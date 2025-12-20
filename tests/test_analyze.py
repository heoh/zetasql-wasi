"""
Test analysis and parsing functionality

Tests for Analyze, Parse, and BuildSql RPC methods.
"""

import pytest
from wasm_client import ZetaSQLError


class TestParseMethod:
    """Test the Parse RPC method."""
    
    def test_parse_simple_query(self, wasm_client):
        """Test parsing a simple query."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.ParseRequest()
        request.sql_statement = "SELECT 1 AS one"
        
        response = wasm_client.parse(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("parsed_statement")
    
    def test_parse_complex_query(self, wasm_client):
        """Test parsing a complex query."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.ParseRequest()
        request.sql_statement = "SELECT a, b FROM table1 WHERE a > 10 ORDER BY b"
        
        response = wasm_client.parse(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("parsed_statement")
    
    def test_parse_join_query(self, wasm_client):
        """Test parsing a query with JOIN."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.ParseRequest()
        request.sql_statement = "SELECT t1.a, t2.b FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id"
        
        response = wasm_client.parse(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("parsed_statement")
    
    def test_parse_syntax_error(self, wasm_client):
        """Test parsing invalid SQL."""
        import pytest
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.ParseRequest()
        request.sql_statement = "SELECT * FORM table1"  # Typo: FORM
        
        # Should raise RuntimeError due to syntax error
        with pytest.raises(ZetaSQLError, match="Syntax error"):
            wasm_client.parse(request)


class TestAnalyzeMethod:
    """Test the Analyze RPC method."""
    
    def test_analyze_simple_select(self, wasm_client):
        """Test analyzing a simple SELECT statement."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_statement = "SELECT 1 AS one"
        
        response = wasm_client.analyze(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.HasField("resolved_statement")
    
    def test_analyze_with_function(self, wasm_client, analyzer_options):
        """Test analyzing statement with function call."""
        from zetasql.local_service import local_service_pb2
        from zetasql.proto import simple_catalog_pb2
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_statement = "SELECT UPPER('hello') AS upper_text"
        request.options.CopyFrom(analyzer_options)
        
        # Create catalog with builtin functions
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(catalog)
        
        response = wasm_client.analyze(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("resolved_statement")
    
    def test_analyze_with_catalog(self, wasm_client, simple_catalog):
        """Test analyzing statement with catalog."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_statement = "SELECT * FROM TestTable"
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.analyze(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("resolved_statement")
    
    def test_analyze_aggregate(self, wasm_client, simple_catalog, analyzer_options):
        """Test analyzing aggregation query."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_statement = "SELECT COUNT(*) AS total FROM TestTable"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.analyze(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("resolved_statement")
    
    def test_analyze_expression(self, wasm_client, analyzer_options):
        """Test analyzing an expression."""
        from zetasql.local_service import local_service_pb2
        from zetasql.proto import simple_catalog_pb2
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_expression = "1 + 2"
        request.options.CopyFrom(analyzer_options)
        
        # Create catalog with builtin functions
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(catalog)
        
        response = wasm_client.analyze(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField("resolved_expression")
    
    def test_analyze_unknown_function(self, wasm_client):
        """Test analyzing with unknown function."""
        from zetasql.local_service import local_service_pb2
        import pytest
        
        request = local_service_pb2.AnalyzeRequest()
        request.sql_statement = "SELECT UNKNOWN_FUNC() AS result"
        
        with pytest.raises(ZetaSQLError):
            wasm_client.analyze(request)


class TestBuildSqlMethod:
    """Test the BuildSql RPC method."""
    
    def test_build_sql_from_analyzed(self, wasm_client):
        """Test building SQL from resolved AST."""
        from zetasql.local_service import local_service_pb2
        
        # First analyze
        analyze_req = local_service_pb2.AnalyzeRequest()
        analyze_req.sql_statement = "SELECT 1 AS one"
        analyze_resp = wasm_client.analyze(analyze_req)
        
        
        # Then build SQL back
        build_req = local_service_pb2.BuildSqlRequest()
        build_req.resolved_statement.CopyFrom(analyze_resp.resolved_statement)
        build_resp = wasm_client.build_sql(build_req)
        
        assert len(build_resp.sql) > 0


class TestAnalyzeParseRoundtrip:
    """Test combinations of Parse and Analyze."""
    
    def test_parse_then_analyze(self, wasm_client, analyzer_options):
        """Test parsing then analyzing the same SQL."""
        from zetasql.local_service import local_service_pb2
        from zetasql.proto import simple_catalog_pb2
        
        sql = "SELECT UPPER('test') AS upper_text"
        
        # Parse
        parse_req = local_service_pb2.ParseRequest()
        parse_req.sql_statement = sql
        parse_resp = wasm_client.parse(parse_req)
        
        
        # Analyze
        analyze_req = local_service_pb2.AnalyzeRequest()
        analyze_req.sql_statement = sql
        analyze_req.options.CopyFrom(analyzer_options)
        
        # Create catalog with builtin functions
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        analyze_req.simple_catalog.CopyFrom(catalog)
        analyze_resp = wasm_client.analyze(analyze_req)
        
