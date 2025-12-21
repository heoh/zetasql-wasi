"""
Test SQL formatting and utility functions

Tests for FormatSql, ExtractTableNames, and related utility RPC methods.
"""

import pytest
from wasm_client import ZetaSQLError
from fixtures.sql_samples import FORMAT_TEST_CASES, EXTRACT_TABLE_CASES
from zetasql.local_service import local_service_pb2
from zetasql.proto import options_pb2


class TestFormatSql:
    """Test the FormatSql RPC method."""
    
    def test_format_simple_query(self, wasm_client):
        """Test formatting a simple query."""
        
        request = local_service_pb2.FormatSqlRequest()
        request.sql = "select   foo,bar from some_table"
        
        response = wasm_client.format_sql(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert len(response.sql) > 0
        # Formatted SQL should be different (properly formatted)
        assert response.sql != request.sql
    
    def test_format_messy_whitespace(self, wasm_client):
        """Test formatting SQL with messy whitespace."""
        
        request = local_service_pb2.FormatSqlRequest()
        request.sql = "SELECT    *    FROM    table1    WHERE    a   >   10"
        
        response = wasm_client.format_sql(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert len(response.sql) > 0
    
    def test_format_complex_query(self, wasm_client):
        """Test formatting a complex query."""
        
        request = local_service_pb2.FormatSqlRequest()
        request.sql = "select t1.a,t2.b from table1 t1 join table2 t2 on t1.id=t2.id where t1.active=true"
        
        response = wasm_client.format_sql(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert len(response.sql) > 0
    
    @pytest.mark.parametrize("name,sql", FORMAT_TEST_CASES.items())
    def test_format_various_cases(self, wasm_client, name, sql):
        """Test formatting various SQL cases."""
        
        request = local_service_pb2.FormatSqlRequest()
        request.sql = sql
        
        response = wasm_client.format_sql(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert len(response.sql) > 0
    
    def test_format_invalid_sql(self, wasm_client):
        """Test formatting invalid SQL."""
        
        request = local_service_pb2.FormatSqlRequest()
        request.sql = "SELECT * FORM table1"  # Syntax error
        
        # FormatSql may or may not accept invalid SQL depending on implementation
        # Just check it doesn't crash
        try:
            response = wasm_client.format_sql(request)
            # If it succeeds, check for result
            assert isinstance(response, local_service_pb2.FormatSqlResponse)
        except ZetaSQLError:
            # If it fails with error, that's also acceptable
            pass


class TestExtractTableNames:
    """Test the ExtractTableNamesFromStatement RPC method."""
    
    def test_extract_single_table(self, wasm_client):
        """Test extracting table name from simple query."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = "SELECT * FROM users"
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert len(response.table_name) > 0
    
    def test_extract_multiple_tables(self, wasm_client):
        """Test extracting multiple table names."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = "SELECT * FROM users, orders WHERE users.id = orders.user_id"
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        # Should have at least 2 tables
        assert len(response.table_name) >= 2
    
    def test_extract_from_join(self, wasm_client):
        """Test extracting table names from JOIN query."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert len(response.table_name) >= 2
    
    def test_extract_qualified_name(self, wasm_client):
        """Test extracting qualified table name."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = "SELECT * FROM mydb.myschema.users"
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert len(response.table_name) > 0
    
    def test_extract_from_subquery(self, wasm_client):
        """Test extracting table names from subquery."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = "SELECT * FROM (SELECT * FROM users) AS u"
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        # Should find the inner table
        assert len(response.table_name) > 0
    
    @pytest.mark.parametrize("name,sql", EXTRACT_TABLE_CASES.items())
    def test_extract_various_cases(self, wasm_client, name, sql):
        """Test extracting table names from various SQL patterns."""
        
        request = local_service_pb2.ExtractTableNamesFromStatementRequest()
        request.sql_statement = sql
        
        response = wasm_client.extract_table_names_from_statement(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert len(response.table_name) > 0


class TestGetBuiltinFunctions:
    """Test the GetBuiltinFunctions RPC method."""
    
    def test_get_builtin_functions(self, wasm_client, analyzer_options):
        """Test retrieving builtin functions."""
        
        # Use ZetaSQLBuiltinFunctionOptionsProto as request
        request = options_pb2.ZetaSQLBuiltinFunctionOptionsProto()
        request.language_options.CopyFrom(analyzer_options.language_options)
        
        response = wasm_client.get_builtin_functions(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        # Should have many builtin functions
        assert len(response.function) > 0
        
        # Check for some common functions (name_path is repeated string, lowercase)
        function_names = ['/'.join(f.name_path) for f in response.function]
        assert any('upper' in name.lower() for name in function_names)
        assert any('count' in name.lower() for name in function_names)
