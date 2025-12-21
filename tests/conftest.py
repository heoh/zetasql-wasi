"""
Pytest fixtures for ZetaSQL WASI tests

This module provides common fixtures for test setup and teardown.
"""

import os
import sys
import pytest

# Add generated protobuf code to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_PB_PATH = os.path.join(PROJECT_ROOT, "tests", "generated_pb")
TESTS_PATH = os.path.join(PROJECT_ROOT, "tests")
sys.path.insert(0, GENERATED_PB_PATH)
sys.path.insert(0, TESTS_PATH)

from wasm_client import WasmClient, ZetaSQLError, StatusCode
from zetasql.local_service import local_service_pb2
from zetasql.proto import simple_catalog_pb2
from zetasql.public import options_pb2, type_pb2, value_pb2


@pytest.fixture(scope="session")
def wasm_path():
    """Path to the optimized WASM binary."""
    # Try optimized version first, fall back to regular version
    opt_path = os.path.join(PROJECT_ROOT, "build", "zetasql_local_service_wasi.opt.wasm")
    regular_path = os.path.join(PROJECT_ROOT, "build", "zetasql_local_service_wasi.wasm")
    
    if os.path.exists(regular_path):
        path = regular_path
    elif os.path.exists(opt_path):
        path = opt_path
    else:
        pytest.skip(f"WASM binary not found")
    
    return path


@pytest.fixture(scope="session")
def analyzer_options():
    """Create default analyzer options with all language features enabled."""
    
    # Create a PrepareRequest to access AnalyzerOptionsProto
    request = local_service_pb2.PrepareRequest()
    options = request.options
    
    # Enable all language features to support builtin functions
    # This enables features like arithmetic operators ($add, $subtract, etc.),
    # string functions (UPPER, LOWER, CONCAT), and numeric functions (ABS, CEIL, FLOOR)
    language_options = options.language_options
    language_options.name_resolution_mode = options_pb2.NAME_RESOLUTION_DEFAULT
    language_options.product_mode = options_pb2.PRODUCT_INTERNAL
    
    # Enable all released language features
    # Note: In production, you should enable only the specific features you need
    # For testing purposes, we enable all features to test maximum functionality
    # This is equivalent to calling EnableMaximumLanguageFeatures() in C++
    # EXCEPT: FEATURE_SPANNER_LEGACY_DDL which causes "Spanner DDL statements are not supported" error
    for feature in dir(options_pb2):
        if feature.startswith('FEATURE_'):
            # Skip Spanner-specific DDL feature that causes errors
            if feature == 'FEATURE_SPANNER_LEGACY_DDL':
                continue
            try:
                feature_value = getattr(options_pb2, feature)
                if isinstance(feature_value, int) and feature_value > 0:
                    language_options.enabled_language_features.append(feature_value)
            except:
                pass
    
    return options


@pytest.fixture(scope="session")
def wasm_client(wasm_path):
    """Create a shared WASM client for all tests."""
    return WasmClient(wasm_path)


@pytest.fixture
def simple_catalog():
    """Create a simple catalog with test table."""
    
    catalog = simple_catalog_pb2.SimpleCatalogProto()
    
    # Add a test table
    table = catalog.table.add()
    table.name = "TestTable"
    
    # Add columns with correct type constants
    col1 = table.column.add()
    col1.name = "column_str"
    col1.type.type_kind = type_pb2.TYPE_STRING
    
    col2 = table.column.add()
    col2.name = "column_bool"
    col2.type.type_kind = type_pb2.TYPE_BOOL
    
    col3 = table.column.add()
    col3.name = "column_int"
    col3.type.type_kind = type_pb2.TYPE_INT64
    
    return catalog


@pytest.fixture
def table_data():
    """Create sample table data."""
    
    rows = []
    
    # Row 1: ['string_1', True, 123]
    row1 = []
    v1 = value_pb2.ValueProto()
    v1.string_value = "string_1"
    row1.append(v1)
    
    v2 = value_pb2.ValueProto()
    v2.bool_value = True
    row1.append(v2)
    
    v3 = value_pb2.ValueProto()
    v3.int32_value = 123
    row1.append(v3)
    
    rows.append(row1)
    
    # Row 2: ['string_2', True, 321]
    row2 = []
    v1 = value_pb2.ValueProto()
    v1.string_value = "string_2"
    row2.append(v1)
    
    v2 = value_pb2.ValueProto()
    v2.bool_value = True
    row2.append(v2)
    
    v3 = value_pb2.ValueProto()
    v3.int32_value = 321
    row2.append(v3)
    
    rows.append(row2)
    
    return rows


@pytest.fixture
def prepare_expression_request(analyzer_options):
    """Create a PrepareExpression request factory with builtin functions enabled."""
    
    def factory(sql: str):
        request = local_service_pb2.PrepareRequest()
        request.sql = sql
        request.options.CopyFrom(analyzer_options)
        
        # Create a simple catalog with builtin functions enabled
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        # Include all builtin functions
        builtin_opts.include_function_ids.extend([])  # Empty means include all
        
        request.simple_catalog.CopyFrom(catalog)
        return request
    
    return factory


@pytest.fixture
def prepare_query_request(analyzer_options):
    """Create a PrepareQuery request factory with builtin functions enabled."""
    
    def factory(sql: str, catalog=None):
        request = local_service_pb2.PrepareQueryRequest()
        request.sql = sql
        request.options.CopyFrom(analyzer_options)
        
        # If a specific catalog with tables is provided, use it
        if catalog:
            # Create a copy and ensure it has builtin_function_options
            catalog_copy = simple_catalog_pb2.SimpleCatalogProto()
            catalog_copy.CopyFrom(catalog)
            # Always set builtin_function_options
            builtin_opts = catalog_copy.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
            request.simple_catalog.CopyFrom(catalog_copy)
        else:
            # Create a simple catalog with builtin functions enabled
            new_catalog = simple_catalog_pb2.SimpleCatalogProto()
            builtin_opts = new_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
            request.simple_catalog.CopyFrom(new_catalog)
        
        return request
    
    return factory


@pytest.fixture
def evaluate_request():
    """Create an Evaluate request factory."""
    
    def factory(prepared_id: int):
        request = local_service_pb2.EvaluateRequest()
        request.prepared_expression_id = prepared_id
        return request
    
    return factory
