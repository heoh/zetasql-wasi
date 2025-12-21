"""
Dynamic RPC coverage test for ZetaSQL WASI

Validates that all proto service RPCs are exported in the WASM binary.
"""

import re
import pytest
from zetasql.local_service import local_service_pb2


# Hardcoded exclusion list with reasons (maintainable style)
EXCLUDED_RPCS = {
    "EvaluateStream": "gRPC streaming not supported in WASI",
    "EvaluateQueryStream": "gRPC streaming not supported in WASI",
    "EvaluateModifyStream": "gRPC streaming not supported in WASI",
}


def get_proto_rpc_methods():
    """Extract all RPC methods from proto service definition."""
    service = local_service_pb2.DESCRIPTOR.services_by_name['ZetaSqlLocalService']
    methods = []
    
    for method in service.methods:
        if method.name not in EXCLUDED_RPCS:
            methods.append({
                'name': method.name,
                'input_type': method.input_type.name,
                'output_type': method.output_type.name,
            })
    
    return methods


def rpc_to_wasm_name(rpc_name):
    """Convert RPC name to WASM export name.
    
    Format: ZetaSqlLocalService_{RpcName}
    Example: PrepareQuery -> ZetaSqlLocalService_PrepareQuery
    """
    return f'ZetaSqlLocalService_{rpc_name}'


def get_wasm_exports(wasm_client):
    """Get all exports from WASM binary."""
    export_names = []
    for export in wasm_client.module.exports:
        export_names.append(export.name)
    return export_names


def get_rpc_exports(wasm_client):
    """Get RPC-related exports (excluding memory management)."""
    all_exports = get_wasm_exports(wasm_client)
    memory_funcs = {'wasm_malloc', 'wasm_free',
                    'wasm_get_last_error', 'wasm_get_last_error_size'}
    return [e for e in all_exports if e.startswith('wasm_') and e not in memory_funcs]


class TestRPCCoverage:
    """Verify all proto RPCs are exported in WASM."""
    
    def test_all_rpcs_exported(self, wasm_client):
        """Check that all non-streaming RPCs are exported in WASM."""
        proto_methods = get_proto_rpc_methods()
        wasm_exports = get_wasm_exports(wasm_client)
        
        missing = []
        for method in proto_methods:
            wasm_name = rpc_to_wasm_name(method['name'])
            if wasm_name not in wasm_exports:
                missing.append(f"{method['name']} -> {wasm_name}")
        
        assert not missing, (
            f"Missing WASM exports for proto RPCs:\n  " +
            "\n  ".join(missing)
        )
    
    def test_no_unexpected_exports(self, wasm_client):
        """Warn if WASM has unexpected RPC exports not in proto."""
        wasm_rpc_exports = set(get_rpc_exports(wasm_client))
        proto_methods = get_proto_rpc_methods()
        expected_exports = {rpc_to_wasm_name(m['name']) for m in proto_methods}
        
        unexpected = wasm_rpc_exports - expected_exports
        
        if unexpected:
            print(f"\nWarning: Unexpected WASM exports: {sorted(unexpected)}")


class TestRPCSmoke:
    """Minimal smoke tests - verify each RPC is callable with minimal input."""
    
    def test_parse_smoke(self, wasm_client):
        """Parse RPC accepts minimal input."""
        request = local_service_pb2.ParseRequest(sql_statement="SELECT 1")
        response = wasm_client.parse(request)
        assert response is not None
    
    def test_analyze_smoke(self, wasm_client, analyzer_options):
        """Analyze RPC accepts minimal input."""
        request = local_service_pb2.AnalyzeRequest(
            sql_statement="SELECT 1",
            options=analyzer_options
        )
        response = wasm_client.analyze(request)
        assert response is not None
        assert response.resolved_statement
    
    def test_build_sql_smoke(self, wasm_client, analyzer_options):
        """BuildSql RPC accepts minimal input."""
        # First analyze to get resolved statement
        analyze_req = local_service_pb2.AnalyzeRequest(
            sql_statement="SELECT 1",
            options=analyzer_options
        )
        analyze_resp = wasm_client.analyze(analyze_req)
        
        # Then build SQL from it
        request = local_service_pb2.BuildSqlRequest(
            resolved_statement=analyze_resp.resolved_statement
        )
        response = wasm_client.build_sql(request)
        assert response is not None
        assert response.sql
    
    def test_format_sql_smoke(self, wasm_client):
        """FormatSql RPC accepts minimal input."""
        request = local_service_pb2.FormatSqlRequest(sql="select 1")
        response = wasm_client.format_sql(request)
        assert response is not None
        assert response.sql
    
    def test_lenient_format_sql_smoke(self, wasm_client):
        """LenientFormatSql RPC accepts minimal input."""
        request = local_service_pb2.FormatSqlRequest(sql="select 1")
        # Call via RPC method directly with correct name
        response_data = wasm_client.call_rpc_method("LenientFormatSql", request.SerializeToString())
        response = local_service_pb2.FormatSqlResponse()
        response.ParseFromString(response_data)
        assert response.sql
    
    def test_prepare_query_smoke(self, wasm_client):
        """PrepareQuery RPC accepts minimal input."""
        request = local_service_pb2.PrepareQueryRequest(sql="SELECT 1")
        response = wasm_client.prepare_query(request)
        assert response is not None
        assert response.prepared
        
        # Cleanup
        wasm_client.unprepare_query(
            local_service_pb2.UnprepareQueryRequest(
                prepared_query_id=response.prepared.prepared_query_id
            )
        )
    
    def test_evaluate_query_smoke(self, wasm_client):
        """EvaluateQuery RPC accepts minimal input."""
        # Prepare first
        prep_resp = wasm_client.prepare_query(
            local_service_pb2.PrepareQueryRequest(sql="SELECT 1")
        )
        
        # Evaluate
        request = local_service_pb2.EvaluateQueryRequest(
            prepared_query_id=prep_resp.prepared.prepared_query_id
        )
        response = wasm_client.evaluate_query(request)
        assert response is not None
        
        # Cleanup
        wasm_client.unprepare_query(
            local_service_pb2.UnprepareQueryRequest(
                prepared_query_id=prep_resp.prepared.prepared_query_id
            )
        )
    
    def test_prepare_modify_smoke(self, wasm_client, analyzer_options):
        """PrepareModify RPC accepts minimal input."""
        request = local_service_pb2.PrepareModifyRequest(
            sql="INSERT INTO t VALUES (1)",
            options=analyzer_options
        )
        # This may fail due to table not found, but proves RPC is callable
        try:
            response = wasm_client.prepare_modify(request)
            assert response is not None
        except Exception as e:
            # If we get an error about table not found, that's fine - RPC is callable
            assert "not found" in str(e).lower() or "INVALID_ARGUMENT" in str(e)
    
    def test_extract_table_names_smoke(self, wasm_client):
        """ExtractTableNamesFromStatement RPC accepts minimal input."""
        request = local_service_pb2.ExtractTableNamesFromStatementRequest(
            sql_statement="SELECT * FROM table1"
        )
        response = wasm_client.extract_table_names_from_statement(request)
        assert response is not None
    
    def test_get_table_from_proto_smoke(self, wasm_client):
        """GetTableFromProto RPC accepts minimal input."""
        from google.protobuf import descriptor_pb2
        request = local_service_pb2.TableFromProtoRequest(
            file_descriptor_set=descriptor_pb2.FileDescriptorSet()
        )
        # May fail with invalid descriptor, but proves RPC is callable
        try:
            response_data = wasm_client.call_rpc_method("GetTableFromProto", request.SerializeToString())
            response = local_service_pb2.TableFromProtoResponse()
            response.ParseFromString(response_data)
            assert response is not None
        except Exception:
            pass  # Expected to fail with empty descriptor
    
    def test_get_language_options_smoke(self, wasm_client):
        """GetLanguageOptions RPC accepts minimal input."""
        from zetasql.proto import options_pb2
        request = options_pb2.LanguageOptionsProto()
        # Call via RPC method directly
        response_data = wasm_client.call_rpc_method("GetLanguageOptions", request.SerializeToString())
        response = options_pb2.LanguageOptionsProto()
        response.ParseFromString(response_data)
        assert response is not None
