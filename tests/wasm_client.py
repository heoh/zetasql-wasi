"""
WASM Client for ZetaSQL Local Service

This module provides a Python wrapper around the ZetaSQL WASI binary,
handling memory management and RPC method invocations.
"""

import os
import sys
import re
from enum import IntEnum
from typing import Optional, Any
from wasmtime import Store, Module, Instance, Func, FuncType, ValType, Linker, WasiConfig


class StatusCode(IntEnum):
    """absl::StatusCode enum values.
    
    Matches the C++ absl::StatusCode and gRPC status codes.
    See: https://github.com/abseil/abseil-cpp/blob/master/absl/status/status.h
    """
    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
    UNAUTHENTICATED = 16


class ZetaSQLError(Exception):
    """Base exception for ZetaSQL RPC errors.
    
    Follows the pattern of gRPC's RpcError and database libraries like psycopg2.
    Inherits directly from Exception (not RuntimeError) as this represents
    a specific domain error (SQL analysis/execution), not a generic runtime error.
    
    Attributes:
        code: absl::StatusCode as StatusCode enum or int
        message: Error message from ZetaSQL
        raw_error: Original error string from C++ ("Code: X, Message: Y")
    
    Example:
        try:
            response = client.prepare_query(request)
        except ZetaSQLError as e:
            if e.code == StatusCode.INVALID_ARGUMENT:
                print(f"SQL syntax error: {e.message}")
            elif e.code == StatusCode.NOT_FOUND:
                print(f"Table not found: {e.message}")
    """
    
    def __init__(self, code: int, message: str, raw_error: str):
        self.code = StatusCode(code) if code in StatusCode._value2member_map_ else code
        self.message = message
        self.raw_error = raw_error
        super().__init__(f"[{self.code.name if isinstance(self.code, StatusCode) else f'Code {code}'}] {message}")
    
    @classmethod
    def from_error_string(cls, error_str: str):
        """Parse error string from C++ format: 'Code: X, Message: Y'
        
        Args:
            error_str: Error string in format "Code: X, Message: Y"
            
        Returns:
            ZetaSQLError instance with parsed code and message
        """
        match = re.match(r'Code: (\d+), Message: (.+)', error_str)
        if match:
            code = int(match.group(1))
            message = match.group(2)
            return cls(code, message, error_str)
        # Fallback for unexpected format
        return cls(StatusCode.UNKNOWN, error_str, error_str)


class WasmClient:
    """Client for interacting with ZetaSQL WASM binary."""
    
    def __init__(self, wasm_path: str):
        """
        Initialize the WASM client.
        
        Args:
            wasm_path: Path to the .wasm file
        """
        if not os.path.exists(wasm_path):
            raise FileNotFoundError(f"WASM file not found: {wasm_path}")
        
        # Create WASI config
        wasi = WasiConfig()
        wasi.inherit_stdout()
        wasi.inherit_stderr()
        wasi.inherit_stdin()
        
        # Add tzdata directory as preopen for timezone support
        # ZetaSQL requires access to timezone data files
        try:
            import tzdata
            tzdata_dir = os.path.dirname(tzdata.__file__)
            zoneinfo_dir = os.path.join(tzdata_dir, "zoneinfo")
            if os.path.exists(zoneinfo_dir):
                # Map the zoneinfo directory to /usr/share/zoneinfo 
                # which is the standard location that ZetaSQL expects
                wasi.preopen_dir(zoneinfo_dir, "/usr/share/zoneinfo")
                print(f"[DEBUG] Preopen tzdata: {zoneinfo_dir} -> /usr/share/zoneinfo", file=sys.stderr)
        except ImportError:
            print("[WARNING] tzdata package not installed, timezone features may not work", file=sys.stderr)
        
        # Create store with WASI context
        self.store = Store()
        self.store.set_wasi(wasi)
        
        self.module = Module.from_file(self.store.engine, wasm_path)
        
        # Create a linker and add WASI support
        linker = Linker(self.store.engine)
        linker.define_wasi()
        
        # Instantiate the module with WASI imports
        self.instance = linker.instantiate(self.store, self.module)
        
        # Call _initialize if it exists (WASI initialization)
        try:
            init_func = self.instance.exports(self.store)["_initialize"]
            init_func(self.store)
        except KeyError:
            pass  # _initialize doesn't exist, skip it
        
        # Get exports
        self.memory = self.instance.exports(self.store)["memory"]
        self._wasm_malloc = self.instance.exports(self.store)["wasm_malloc"]
        self._wasm_free = self.instance.exports(self.store)["wasm_free"]
        self._wasm_get_last_error = self.instance.exports(self.store)["wasm_get_last_error"]
        self._wasm_get_last_error_size = self.instance.exports(self.store)["wasm_get_last_error_size"]
        
        # Cache for RPC method exports
        self._rpc_methods = {}
    
    def allocate_bytes(self, size: int) -> int:
        """
        Allocate memory in WASM.
        
        Args:
            size: Number of bytes to allocate
            
        Returns:
            Pointer to allocated memory
        """
        return self._wasm_malloc(self.store, size)
    
    def free_bytes(self, ptr: int) -> None:
        """Free memory in WASM.
        
        Args:
            ptr: Pointer to memory to free
        
        Note:
            C++ wasm_free(void* ptr) does not take size parameter.
            The WASM allocator (malloc/free) tracks block sizes internally.
        """
        self._wasm_free(self.store, ptr)
    
    def write_bytes(self, ptr: int, data: bytes) -> None:
        """
        Write bytes to WASM memory.
        
        Args:
            ptr: Pointer to write to
            data: Bytes to write
        """
        mem_data = self.memory.data_ptr()
        for i, byte in enumerate(data):
            mem_data[ptr + i] = byte
    
    def read_bytes(self, ptr: int, size: int) -> bytes:
        """
        Read bytes from WASM memory.
        
        Args:
            ptr: Pointer to read from
            size: Number of bytes to read
            
        Returns:
            Bytes read from memory
        """
        mem_data = self.memory.data_ptr()
        return bytes([mem_data[ptr + i] for i in range(size)])
    
    def get_last_error(self) -> str:
        """
        Get the last error message from WASM.
        
        Returns:
            Last error message, or empty string if no error
        """
        error_size = self._wasm_get_last_error_size(self.store)
        if error_size == 0:
            return ""
        
        error_ptr = self._wasm_get_last_error(self.store)
        return self.read_bytes(error_ptr, error_size).decode('utf-8')
    
    def call_rpc_method(self, method_name: str, request_data: bytes) -> bytes:
        """
        Call an RPC method with protobuf serialized request.
        
        Args:
            method_name: Name of the RPC method (e.g., "PrepareExpression")
            request_data: Serialized protobuf request
            
        Returns:
            Serialized protobuf response
            
        Raises:
            RuntimeError: If the RPC call fails (returns nullptr)
        """
        # Convert to wasm_ prefixed name
        wasm_method_name = f"wasm_{method_name[0].lower() + method_name[1:]}" if method_name[0].isupper() else f"wasm_{method_name}"
        
        # Get or cache the method export
        if wasm_method_name not in self._rpc_methods:
            try:
                self._rpc_methods[wasm_method_name] = self.instance.exports(self.store)[wasm_method_name]
            except KeyError:
                raise ValueError(f"RPC method not found: {wasm_method_name}")
        
        method = self._rpc_methods[wasm_method_name]
        
        # Allocate memory for request
        request_size = len(request_data)
        request_ptr = self.allocate_bytes(request_size)
        
        # Allocate memory for response_size (output parameter)
        response_size_ptr = self.allocate_bytes(4)  # size_t is 4 bytes in wasm32
        
        try:
            # Write request data
            self.write_bytes(request_ptr, request_data)
            
            # Call the method (returns response_ptr or nullptr on error)
            response_ptr = method(self.store, request_ptr, request_size, response_size_ptr)
            
            # Check for nullptr (error case)
            if response_ptr == 0:  # nullptr in WASM is 0
                error_str = self.get_last_error()
                raise ZetaSQLError.from_error_string(error_str)
            
            # Read response size from output parameter
            response_size_bytes = self.read_bytes(response_size_ptr, 4)
            response_size = int.from_bytes(response_size_bytes, byteorder='little')
            
            # Read response data
            response_data = self.read_bytes(response_ptr, response_size)
            
            # Free response memory (C++ allocated via malloc, we must free)
            self.free_bytes(response_ptr)
            
            return response_data
            
        finally:
            # Always free request memory and response_size_ptr
            self.free_bytes(request_ptr)
            self.free_bytes(response_size_ptr)
    
    def prepare_expression(self, request_proto):
        """Call wasm_prepare RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("prepare", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.PrepareResponse()
        response.ParseFromString(response_data)
        return response
    
    def evaluate_expression(self, request_proto):
        """Call wasm_evaluate RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("evaluate", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.EvaluateResponse()
        response.ParseFromString(response_data)
        return response
    
    def unprepare_expression(self, request_proto):
        """Call wasm_unprepare RPC method (takes only the ID, not a full request)."""
        # wasm_unprepare has signature: int wasm_unprepare(int64_t id)
        # It returns 0 on success or error code on failure
        prepared_id = request_proto.prepared_expression_id
        
        # Get the wasm_unprepare function
        if "wasm_unprepare" not in self._rpc_methods:
            self._rpc_methods["wasm_unprepare"] = self.instance.exports(self.store)["wasm_unprepare"]
        
        unprepare_func = self._rpc_methods["wasm_unprepare"]
        
        # Call with just the ID
        result = unprepare_func(self.store, prepared_id)
        
        # Check for error (0 = success, non-zero = absl::StatusCode)
        if result != 0:
            error_str = self.get_last_error()
            raise ZetaSQLError.from_error_string(error_str)
        
        # Return empty response (unprepare doesn't return data)
        from google.protobuf import empty_pb2
        return empty_pb2.Empty()
    
    def prepare_query(self, request_proto):
        """Call wasm_prepare_query RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("prepare_query", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.PrepareQueryResponse()
        response.ParseFromString(response_data)
        return response
    
    def evaluate_query(self, request_proto):
        """Call wasm_evaluate_query RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("evaluate_query", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.EvaluateQueryResponse()
        response.ParseFromString(response_data)
        return response
    
    def unprepare_query(self, request_proto):
        """Call wasm_unprepare_query RPC method (takes only the ID, not a full request)."""
        # wasm_unprepare_query has signature: int wasm_unprepare_query(int64_t id)
        # It returns 0 on success or error code on failure
        prepared_id = request_proto.prepared_query_id
        
        # Get the wasm_unprepare_query function
        if "wasm_unprepare_query" not in self._rpc_methods:
            self._rpc_methods["wasm_unprepare_query"] = self.instance.exports(self.store)["wasm_unprepare_query"]
        
        unprepare_func = self._rpc_methods["wasm_unprepare_query"]
        
        # Call with just the ID
        result = unprepare_func(self.store, prepared_id)
        
        # Check for error (0 = success, non-zero = absl::StatusCode)
        if result != 0:
            error_str = self.get_last_error()
            raise ZetaSQLError.from_error_string(error_str)
        
        # Return empty response
        from google.protobuf import empty_pb2
        return empty_pb2.Empty()
    
    def prepare_modify(self, request_proto):
        """Call wasm_prepare_modify RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("prepare_modify", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.PrepareModifyResponse()
        response.ParseFromString(response_data)
        return response
    
    def evaluate_modify(self, request_proto):
        """Call wasm_evaluate_modify RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("evaluate_modify", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.EvaluateModifyResponse()
        response.ParseFromString(response_data)
        return response
    
    def unprepare_modify(self, request_proto):
        """Call wasm_unprepare_modify RPC method (takes only the ID, not a full request)."""
        # wasm_unprepare_modify has signature: int wasm_unprepare_modify(int64_t id)
        # It returns 0 on success or error code on failure
        prepared_id = request_proto.prepared_modify_id
        
        # Get the wasm_unprepare_modify function
        if "wasm_unprepare_modify" not in self._rpc_methods:
            self._rpc_methods["wasm_unprepare_modify"] = self.instance.exports(self.store)["wasm_unprepare_modify"]
        
        unprepare_func = self._rpc_methods["wasm_unprepare_modify"]
        
        # Call with just the ID
        result = unprepare_func(self.store, prepared_id)
        
        # Check for error (0 = success, non-zero = absl::StatusCode)
        if result != 0:
            error_str = self.get_last_error()
            raise ZetaSQLError.from_error_string(error_str)
        
        # Return empty response
        from google.protobuf import empty_pb2
        return empty_pb2.Empty()
    
    def analyze(self, request_proto):
        """Call wasm_analyze RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("analyze", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.AnalyzeResponse()
        response.ParseFromString(response_data)
        return response
    
    def parse(self, request_proto):
        """Call wasm_parse RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("parse", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.ParseResponse()
        response.ParseFromString(response_data)
        return response
    
    def build_sql(self, request_proto):
        """Call wasm_build_sql RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("build_sql", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.BuildSqlResponse()
        response.ParseFromString(response_data)
        return response
    
    def extract_table_names_from_statement(self, request_proto):
        """Call wasm_extract_table_names RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("extract_table_names", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.ExtractTableNamesFromStatementResponse()
        response.ParseFromString(response_data)
        return response
    
    def format_sql(self, request_proto):
        """Call wasm_format_sql RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("format_sql", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.FormatSqlResponse()
        response.ParseFromString(response_data)
        return response
    
    def register_catalog(self, request_proto):
        """Call wasm_register_catalog RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("register_catalog", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.RegisterResponse()
        response.ParseFromString(response_data)
        return response
    
    def get_builtin_functions(self, request_proto):
        """Call wasm_get_builtin_functions RPC method."""
        request_data = request_proto.SerializeToString()
        response_data = self.call_rpc_method("get_builtin_functions", request_data)
        
        from zetasql.local_service import local_service_pb2
        response = local_service_pb2.GetBuiltinFunctionsResponse()
        response.ParseFromString(response_data)
        return response
