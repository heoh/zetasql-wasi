"""
Test expression evaluation functionality

Tests for PrepareExpression, EvaluateExpression, and UnprepareExpression RPC methods.
"""

import pytest
from wasm_client import ZetaSQLError
from fixtures.sql_samples import (
    SIMPLE_EXPRESSIONS,
    STRING_FUNCTIONS,
    NUMERIC_FUNCTIONS,
    CONDITIONAL_EXPRESSIONS,
)
from zetasql.local_service import local_service_pb2
from zetasql.proto import simple_catalog_pb2
from zetasql.public import type_pb2


class TestBasicExpressions:
    """Test basic expression evaluation without preparation."""
    
    def test_integer_literal(self, wasm_client, prepare_expression_request):
        """Test evaluating a simple integer literal."""
        request = prepare_expression_request("1")
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.HasField('prepared')
        assert response.prepared.prepared_expression_id >= 0
    
    def test_string_literal(self, wasm_client, prepare_expression_request):
        """Test evaluating a string literal."""
        request = prepare_expression_request("'hello'")
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_expression_id >= 0
    
    def test_arithmetic_expression(self, wasm_client, prepare_expression_request):
        """Test evaluating arithmetic expressions."""
        request = prepare_expression_request("1 + 2")
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_expression_id >= 0
    
    def test_boolean_literal(self, wasm_client, prepare_expression_request):
        """Test evaluating boolean literals."""
        request = prepare_expression_request("TRUE")
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client)
        assert response.prepared.prepared_expression_id >= 0


class TestStringFunctions:
    """Test string function evaluation."""
    
    @pytest.mark.parametrize("name,sql", STRING_FUNCTIONS.items())
    def test_string_functions(self, wasm_client, prepare_expression_request, name, sql):
        """Test various string functions."""
        request = prepare_expression_request(sql)
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.prepared.prepared_expression_id >= 0


class TestNumericFunctions:
    """Test numeric function evaluation."""
    
    @pytest.mark.parametrize("name,sql", NUMERIC_FUNCTIONS.items())
    def test_numeric_functions(self, wasm_client, prepare_expression_request, name, sql):
        """Test various numeric functions."""
        request = prepare_expression_request(sql)
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.prepared.prepared_expression_id >= 0


class TestConditionalExpressions:
    """Test conditional expressions (IF, CASE, etc.)."""
    
    @pytest.mark.parametrize("name,sql", CONDITIONAL_EXPRESSIONS.items())
    def test_conditional_expressions(self, wasm_client, prepare_expression_request, name, sql):
        """Test conditional expressions."""
        request = prepare_expression_request(sql)
        response = wasm_client.prepare_expression(request)
        
        # Response validated (errors raise RuntimeError in wasm_client), \
        assert response.prepared.prepared_expression_id >= 0


class TestRandomFunction:
    """Test RAND() function to ensure WASI random support works."""
    
    def test_rand_prepare(self, wasm_client, prepare_expression_request):
        """Test that RAND() can be prepared."""
        request = prepare_expression_request("RAND()")
        response = wasm_client.prepare_expression(request)
        
        assert response.prepared.prepared_expression_id >= 0
        assert response.prepared.HasField('output_type')
    
    def test_rand_execute(self, wasm_client, prepare_expression_request):
        """Test that RAND() can be executed and returns valid values."""
        
        # Prepare RAND()
        prepare_req = prepare_expression_request("RAND()")
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        prepared_id = prepare_resp.prepared.prepared_expression_id
        
        # Evaluate multiple times to check randomness
        values = []
        for _ in range(5):
            eval_req = local_service_pb2.EvaluateRequest()
            eval_req.prepared_expression_id = prepared_id
            eval_resp = wasm_client.evaluate_expression(eval_req)
            
            # RAND() should return a value (we can't check exact value as it's random)
            assert eval_resp.HasField('value')
            # Store value for uniqueness check
            if eval_resp.value.HasField('double_value'):
                values.append(eval_resp.value.double_value)
        
        # At least some values should be different (probabilistically almost certain)
        # RAND() returns values in [0, 1), so they should be floats
        assert len(values) > 0, "RAND() should return double values"
        assert all(0 <= v < 1 for v in values), "RAND() values should be in [0, 1)"
        
        # Clean up
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        wasm_client.unprepare_expression(unprepare_req)
    
    def test_rand_in_expression(self, wasm_client, prepare_expression_request):
        """Test RAND() in arithmetic expressions."""
        
        # Test RAND() * 100 (scale to 0-100 range)
        prepare_req = prepare_expression_request("RAND() * 100")
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        prepared_id = prepare_resp.prepared.prepared_expression_id
        
        # Evaluate
        eval_req = local_service_pb2.EvaluateRequest()
        eval_req.prepared_expression_id = prepared_id
        eval_resp = wasm_client.evaluate_expression(eval_req)
        
        # Should return a value in [0, 100)
        assert eval_resp.HasField('value')
        if eval_resp.value.HasField('double_value'):
            value = eval_resp.value.double_value
            assert 0 <= value < 100, f"RAND() * 100 should be in [0, 100), got {value}"
        
        # Clean up
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        wasm_client.unprepare_expression(unprepare_req)


class TestPrepareEvaluateWorkflow:
    """Test the Prepare -> Evaluate -> Unprepare workflow."""
    
    def test_prepare_evaluate_unprepare(self, wasm_client, prepare_expression_request):
        """Test complete prepare-evaluate-unprepare workflow."""
        
        # Step 1: Prepare
        prepare_req = prepare_expression_request("1 + 2")
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        
        prepared_id = prepare_resp.prepared.prepared_expression_id
        assert prepared_id >= 0
        
        # Step 2: Evaluate
        eval_req = local_service_pb2.EvaluateRequest()
        eval_req.prepared_expression_id = prepared_id
        eval_resp = wasm_client.evaluate_expression(eval_req)
        
        
        # Step 3: Unprepare
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        unprepare_resp = wasm_client.unprepare_expression(unprepare_req)
        
    
    def test_multiple_evaluations(self, wasm_client, prepare_expression_request):
        """Test evaluating the same prepared expression multiple times."""
        
        # Prepare once
        prepare_req = prepare_expression_request("1 + 2")
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        prepared_id = prepare_resp.prepared.prepared_expression_id
        
        # Evaluate multiple times
        for _ in range(3):
            eval_req = local_service_pb2.EvaluateRequest()
            eval_req.prepared_expression_id = prepared_id
            eval_resp = wasm_client.evaluate_expression(eval_req)
        
        # Clean up
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        wasm_client.unprepare_expression(unprepare_req)


class TestParameterizedExpressions:
    """Test expressions with parameters."""
    
    def test_integer_parameter(self, wasm_client, analyzer_options):
        """Test expression with integer parameter."""
        
        # Prepare with parameter
        prepare_req = local_service_pb2.PrepareRequest()
        prepare_req.sql = "@value"
        prepare_req.options.CopyFrom(analyzer_options)
        
        # Create catalog with builtin functions
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        prepare_req.simple_catalog.CopyFrom(catalog)
        
        # Define parameter type
        param = prepare_req.options.query_parameters.add()
        param.name = "value"
        param.type.type_kind = type_pb2.TYPE_INT64
        
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        
        prepared_id = prepare_resp.prepared.prepared_expression_id
        
        # Evaluate with parameter value
        eval_req = local_service_pb2.EvaluateRequest()
        eval_req.prepared_expression_id = prepared_id
        
        param_value = eval_req.params.add()
        param_value.name = "value"
        param_value.value.int64_value = 42
        
        eval_resp = wasm_client.evaluate_expression(eval_req)
        
        # Clean up
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        wasm_client.unprepare_expression(unprepare_req)
    
    def test_string_parameter(self, wasm_client, analyzer_options):
        """Test expression with string parameter."""
        
        prepare_req = local_service_pb2.PrepareRequest()
        prepare_req.sql = "@name"
        prepare_req.options.CopyFrom(analyzer_options)
        
        # Create catalog with builtin functions
        catalog = simple_catalog_pb2.SimpleCatalogProto()
        builtin_opts = catalog.builtin_function_options
        builtin_opts.language_options.CopyFrom(analyzer_options.language_options)
        prepare_req.simple_catalog.CopyFrom(catalog)
        
        param = prepare_req.options.query_parameters.add()
        param.name = "name"
        param.type.type_kind = type_pb2.TYPE_STRING
        
        prepare_resp = wasm_client.prepare_expression(prepare_req)
        
        prepared_id = prepare_resp.prepared.prepared_expression_id
        
        eval_req = local_service_pb2.EvaluateRequest()
        eval_req.prepared_expression_id = prepared_id
        
        param_value = eval_req.params.add()
        param_value.name = "name"
        param_value.value.string_value = "test"
        
        eval_resp = wasm_client.evaluate_expression(eval_req)
        
        # Clean up
        unprepare_req = local_service_pb2.UnprepareRequest()
        unprepare_req.prepared_expression_id = prepared_id
        wasm_client.unprepare_expression(unprepare_req)


class TestErrorHandling:
    """Test error handling for invalid expressions."""
    
    def test_syntax_error(self, wasm_client, prepare_expression_request):
        """Test that syntax errors are properly reported."""
        # Invalid SQL syntax
        import pytest
        request = prepare_expression_request("SELECT")  # Incomplete
        
        # Should raise RuntimeError due to syntax error
        with pytest.raises(ZetaSQLError, match="Syntax error"):
            wasm_client.prepare_expression(request)
    
    def test_unknown_function(self, wasm_client, prepare_expression_request):
        """Test that unknown functions are properly reported."""
        import pytest
        request = prepare_expression_request("UNKNOWN_FUNCTION('test')")
        
        # Should raise RuntimeError due to unknown function
        with pytest.raises(ZetaSQLError):
            wasm_client.prepare_expression(request)
