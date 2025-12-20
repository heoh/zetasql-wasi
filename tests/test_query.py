"""
Test query functionality

Tests for PrepareQuery, EvaluateQuery, and UnprepareQuery RPC methods.
"""

import pytest
from wasm_client import ZetaSQLError
from fixtures.sql_samples import (
    TABLE_QUERIES,
    AGGREGATE_QUERIES,
)


class TestBasicQueries:
    """Test basic query preparation and evaluation."""
    
    def test_select_literal(self, wasm_client, prepare_query_request):
        """Test SELECT with literal value (no table)."""
        request = prepare_query_request("SELECT 1 AS one")
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_select_multiple_literals(self, wasm_client, prepare_query_request):
        """Test SELECT with multiple literal values."""
        request = prepare_query_request("SELECT 1 AS one, 'hello' AS greeting, TRUE AS flag")
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_select_with_expression(self, wasm_client, prepare_query_request):
        """Test SELECT with expressions."""
        request = prepare_query_request("SELECT 1 + 2 AS result, UPPER('hello') AS upper_text")
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0


class TestTableQueries:
    """Test queries against tables."""
    
    def test_select_all(self, wasm_client, prepare_query_request, simple_catalog):
        """Test SELECT * FROM table."""
        request = prepare_query_request("SELECT * FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.prepared.prepared_query_id >= 0
    
    def test_select_columns(self, wasm_client, prepare_query_request, simple_catalog):
        """Test SELECT specific columns."""
        request = prepare_query_request("SELECT column_str, column_int FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_where_clause(self, wasm_client, prepare_query_request, simple_catalog):
        """Test SELECT with WHERE clause."""
        request = prepare_query_request("SELECT * FROM TestTable WHERE column_str = 'string_1'", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_where_numeric(self, wasm_client, prepare_query_request, simple_catalog):
        """Test WHERE clause with numeric comparison."""
        request = prepare_query_request("SELECT * FROM TestTable WHERE column_int > 100", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_order_by(self, wasm_client, prepare_query_request, simple_catalog):
        """Test ORDER BY clause."""
        request = prepare_query_request("SELECT * FROM TestTable ORDER BY column_int DESC", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_limit(self, wasm_client, prepare_query_request, simple_catalog):
        """Test LIMIT clause."""
        request = prepare_query_request("SELECT * FROM TestTable LIMIT 1", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0


class TestAggregateQueries:
    """Test aggregate functions in queries."""
    
    def test_count_star(self, wasm_client, prepare_query_request, simple_catalog):
        """Test COUNT(*)."""
        request = prepare_query_request("SELECT COUNT(*) AS total FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_count_column(self, wasm_client, prepare_query_request, simple_catalog):
        """Test COUNT(column)."""
        request = prepare_query_request("SELECT COUNT(column_int) AS count_int FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_sum(self, wasm_client, prepare_query_request, simple_catalog):
        """Test SUM aggregate."""
        request = prepare_query_request("SELECT SUM(column_int) AS sum_int FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_avg(self, wasm_client, prepare_query_request, simple_catalog):
        """Test AVG aggregate."""
        request = prepare_query_request("SELECT AVG(column_int) AS avg_int FROM TestTable", simple_catalog)
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0
    
    def test_min_max(self, wasm_client, prepare_query_request, simple_catalog):
        """Test MIN and MAX aggregates."""
        request = prepare_query_request(
            "SELECT MIN(column_int) AS min_int, MAX(column_int) AS max_int FROM TestTable",
            simple_catalog
        )
        response = wasm_client.prepare_query(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_query_id >= 0


class TestQueryWithTableData:
    """Test query evaluation with actual table data."""
    
    def test_evaluate_with_data(self, wasm_client, analyzer_options, simple_catalog):
        """Test evaluating a query with table data."""
        from zetasql.local_service import local_service_pb2
        from zetasql.public import value_pb2
        
        # Evaluate with SQL + catalog + table data (not using prepared statement)
        eval_req = local_service_pb2.EvaluateQueryRequest()
        eval_req.sql = "SELECT * FROM TestTable"
        eval_req.options.CopyFrom(analyzer_options)
        eval_req.simple_catalog.CopyFrom(simple_catalog)
        
        # Add table content using map access
        table_content = eval_req.table_content["TestTable"]
        
        # Row 1
        row1 = table_content.table_data.row.add()
        val1 = row1.cell.add()
        val1.string_value = "string_1"
        val2 = row1.cell.add()
        val2.bool_value = True
        val3 = row1.cell.add()
        val3.int64_value = 123
        
        # Row 2
        row2 = table_content.table_data.row.add()
        val1 = row2.cell.add()
        val1.string_value = "string_2"
        val2 = row2.cell.add()
        val2.bool_value = True
        val3 = row2.cell.add()
        val3.int64_value = 321
        
        eval_resp = wasm_client.evaluate_query(eval_req)


class TestPrepareEvaluateWorkflow:
    """Test the Prepare -> Evaluate -> Unprepare workflow for queries."""
    
    def test_complete_workflow(self, wasm_client, prepare_query_request):
        """Test complete prepare-evaluate-unprepare workflow."""
        from zetasql.local_service import local_service_pb2
        
        # Prepare
        prepare_req = prepare_query_request("SELECT 1 AS one, 2 AS two")
        prepare_resp = wasm_client.prepare_query(prepare_req)
        
        prepared_id = prepare_resp.prepared.prepared_query_id
        
        # Evaluate
        eval_req = local_service_pb2.EvaluateQueryRequest()
        eval_req.prepared_query_id = prepared_id
        eval_resp = wasm_client.evaluate_query(eval_req)
        
        
        # Unprepare
        unprepare_req = local_service_pb2.UnprepareQueryRequest()
        unprepare_req.prepared_query_id = prepared_id
        unprepare_resp = wasm_client.unprepare_query(unprepare_req)
        


class TestErrorHandling:
    """Test error handling for invalid queries."""
    
    def test_syntax_error(self, wasm_client, prepare_query_request):
        """Test query with syntax error."""
        import pytest
        request = prepare_query_request("SELECT * FORM TestTable")  # Typo: FORM
        
        with pytest.raises(ZetaSQLError, match="Syntax error"):
            wasm_client.prepare_query(request)
    
    def test_unknown_table(self, wasm_client, prepare_query_request):
        """Test query with unknown table."""
        import pytest
        request = prepare_query_request("SELECT * FROM NonExistentTable")
        
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_query(request)
    
    def test_unknown_column(self, wasm_client, prepare_query_request, simple_catalog):
        """Test query with unknown column."""
        import pytest
        request = prepare_query_request("SELECT unknown_column FROM TestTable", simple_catalog)
        
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_query(request)
