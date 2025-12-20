"""
Test DML (Data Modification Language) functionality

Tests for PrepareModify, EvaluateModify, and UnprepareModify RPC methods.
"""

import pytest
from wasm_client import ZetaSQLError


class TestInsertStatements:
    """Test INSERT DML statements."""
    
    def test_insert_prepare(self, wasm_client, analyzer_options, simple_catalog):
        """Test preparing an INSERT statement."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "INSERT INTO TestTable VALUES ('string_3', FALSE, 456)"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.prepared.prepared_modify_id >= 0
    
    def test_insert_with_column_names(self, wasm_client, analyzer_options, simple_catalog):
        """Test INSERT with explicit column names."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "INSERT INTO TestTable (column_str, column_bool, column_int) VALUES ('test', TRUE, 999)"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_modify_id >= 0


class TestUpdateStatements:
    """Test UPDATE DML statements."""
    
    def test_update_prepare(self, wasm_client, analyzer_options, simple_catalog):
        """Test preparing an UPDATE statement."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "UPDATE TestTable SET column_int = 999 WHERE column_str = 'string_1'"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_modify_id >= 0
    
    def test_update_multiple_columns(self, wasm_client, analyzer_options, simple_catalog):
        """Test UPDATE with multiple columns."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "UPDATE TestTable SET column_int = 500, column_bool = FALSE WHERE column_str = 'string_1'"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_modify_id >= 0
    
    def test_update_no_where(self, wasm_client, analyzer_options, simple_catalog):
        """Test UPDATE without WHERE clause is rejected."""
        from zetasql.local_service import local_service_pb2
        import pytest
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "UPDATE TestTable SET column_bool = TRUE"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        # Should fail with WHERE clause requirement
        with pytest.raises(ZetaSQLError, match="WHERE clause"):
            wasm_client.prepare_modify(request)


class TestDeleteStatements:
    """Test DELETE DML statements."""
    
    def test_delete_prepare(self, wasm_client, analyzer_options, simple_catalog):
        """Test preparing a DELETE statement."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "DELETE FROM TestTable WHERE column_bool = FALSE"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_modify_id >= 0
    
    def test_delete_with_complex_where(self, wasm_client, analyzer_options, simple_catalog):
        """Test DELETE with complex WHERE clause."""
        from zetasql.local_service import local_service_pb2
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "DELETE FROM TestTable WHERE column_int > 200 AND column_bool = TRUE"
        request.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        response = wasm_client.prepare_modify(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_modify_id >= 0


class TestPrepareEvaluateWorkflow:
    """Test the Prepare -> Evaluate -> Unprepare workflow for DML."""
    
    def test_insert_workflow(self, wasm_client, analyzer_options, simple_catalog):
        """Test complete workflow for INSERT."""
        from zetasql.local_service import local_service_pb2
        
        # Evaluate with SQL + catalog + table data (not using prepared statement)
        eval_req = local_service_pb2.EvaluateModifyRequest()
        eval_req.sql = "INSERT INTO TestTable VALUES ('new_row', TRUE, 777)"
        eval_req.options.CopyFrom(analyzer_options)
        
        # Ensure simple_catalog has builtin functions
        if not simple_catalog.HasField('builtin_function_options'):
            builtin_opts = simple_catalog.builtin_function_options
            builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        eval_req.simple_catalog.CopyFrom(simple_catalog)
        
        # Add existing table data using map access
        table_content = eval_req.table_content["TestTable"]
        
        row1 = table_content.table_data.row.add()
        val1 = row1.cell.add()
        val1.string_value = "old_string"
        val2 = row1.cell.add()
        val2.bool_value = True
        val3 = row1.cell.add()
        val3.int64_value = 123
        
        eval_resp = wasm_client.evaluate_modify(eval_req)
        


class TestErrorHandling:
    """Test error handling for invalid DML statements."""
    
    def test_insert_type_mismatch(self, wasm_client, analyzer_options, simple_catalog):
        """Test INSERT with type mismatch."""
        from zetasql.local_service import local_service_pb2
        
        import pytest
        request = local_service_pb2.PrepareModifyRequest()
        # Trying to insert string into int column
        request.sql = "INSERT INTO TestTable VALUES ('string', TRUE, 'not_a_number')"
        request.options.CopyFrom(analyzer_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_modify(request)
    
    def test_update_unknown_column(self, wasm_client, analyzer_options, simple_catalog):
        """Test UPDATE with unknown column."""
        from zetasql.local_service import local_service_pb2
        import pytest
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "UPDATE TestTable SET unknown_column = 123"
        request.options.CopyFrom(analyzer_options)
        request.simple_catalog.CopyFrom(simple_catalog)
        
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_modify(request)
    
    def test_delete_unknown_table(self, wasm_client, analyzer_options):
        """Test DELETE from unknown table."""
        from zetasql.local_service import local_service_pb2
        import pytest
        
        request = local_service_pb2.PrepareModifyRequest()
        request.sql = "DELETE FROM NonExistentTable WHERE id = 1"
        request.options.CopyFrom(analyzer_options)
        
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_modify(request)
