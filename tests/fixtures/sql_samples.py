"""
Common SQL samples for testing ZetaSQL WASI

This module contains reusable SQL queries and expressions for testing.
"""

# Simple expressions
SIMPLE_EXPRESSIONS = {
    "integer_literal": "1",
    "string_literal": "'hello'",
    "addition": "1 + 2",
    "multiplication": "3 * 4",
    "string_concat": "CONCAT('hello', ' ', 'world')",
    "boolean": "TRUE",
}

# String function tests
STRING_FUNCTIONS = {
    "upper": "UPPER('hello')",
    "lower": "LOWER('WORLD')",
    "concat": "CONCAT('a', 'b', 'c')",
    "substring": "SUBSTRING('hello', 1, 3)",
    "length": "LENGTH('test')",
    "trim": "TRIM('  hello  ')",
    "replace": "REPLACE('hello', 'l', 'L')",
}

# Numeric function tests
NUMERIC_FUNCTIONS = {
    "abs": "ABS(-5)",
    "ceil": "CEIL(3.14)",
    "floor": "FLOOR(3.14)",
    "round": "ROUND(3.14159, 2)",
    "mod": "MOD(10, 3)",
    "rand": "RAND()",
}

# Conditional expressions
CONDITIONAL_EXPRESSIONS = {
    "if_true": "IF(TRUE, 'yes', 'no')",
    "if_false": "IF(FALSE, 'yes', 'no')",
    "case_when": "CASE WHEN 1 > 0 THEN 'positive' ELSE 'negative' END",
    "coalesce": "COALESCE(NULL, 'default')",
}

# Table queries
TABLE_QUERIES = {
    "select_all": "SELECT * FROM TestTable",
    "select_columns": "SELECT column_str, column_int FROM TestTable",
    "where_clause": "SELECT * FROM TestTable WHERE column_str = 'string_1'",
    "where_int": "SELECT * FROM TestTable WHERE column_int > 200",
    "order_by": "SELECT * FROM TestTable ORDER BY column_int DESC",
    "limit": "SELECT * FROM TestTable LIMIT 1",
}

# Aggregate queries
AGGREGATE_QUERIES = {
    "count": "SELECT COUNT(*) FROM TestTable",
    "count_column": "SELECT COUNT(column_int) FROM TestTable",
    "sum": "SELECT SUM(column_int) FROM TestTable",
    "avg": "SELECT AVG(column_int) FROM TestTable",
    "min": "SELECT MIN(column_int) FROM TestTable",
    "max": "SELECT MAX(column_int) FROM TestTable",
    "any_value": "SELECT ANY_VALUE(column_str) FROM TestTable",
}

# DML statements
DML_STATEMENTS = {
    "insert": "INSERT INTO TestTable VALUES ('string_3', FALSE, 456)",
    "update": "UPDATE TestTable SET column_int = 999 WHERE column_str = 'string_1'",
    "delete": "DELETE FROM TestTable WHERE column_bool = FALSE",
}

# Parameterized queries
PARAMETERIZED_QUERIES = {
    "param_int": "SELECT @value AS result",
    "param_string": "SELECT @name AS name",
    "param_bool": "SELECT @flag AS flag",
    "param_in_where": "SELECT * FROM TestTable WHERE column_str = @str_value",
}

# Error cases
ERROR_CASES = {
    "syntax_error": "SELECT * FORM TestTable",  # Typo: FORM instead of FROM
    "unknown_column": "SELECT unknown_column FROM TestTable",
    "unknown_table": "SELECT * FROM NonExistentTable",
    "type_mismatch": "SELECT 'string' + 123",  # Type error
    "division_by_zero": "SELECT 1 / 0",
}

# Format test cases
FORMAT_TEST_CASES = {
    "messy_query": "seLect   foo,bar from some_table where   something  limit 10",
    "nested_query": "SELECT * FROM (SELECT a, b FROM t1) WHERE a > 10",
    "complex_join": "select t1.a,t2.b from table1 t1 join table2 t2 on t1.id=t2.id where t1.active=true",
}

# Extract table names test cases
EXTRACT_TABLE_CASES = {
    "single_table": "SELECT * FROM users",
    "multiple_tables": "SELECT * FROM users, orders WHERE users.id = orders.user_id",
    "join": "SELECT * FROM users JOIN orders ON users.id = orders.user_id",
    "subquery": "SELECT * FROM (SELECT * FROM users) AS u",
    "qualified_name": "SELECT * FROM mydb.myschema.users",
}

# Analysis test cases
ANALYZE_CASES = {
    "simple_select": "SELECT 1 AS one",
    "function_call": "SELECT UPPER('hello') AS upper_text",
    "table_scan": "SELECT * FROM TestTable",
    "aggregation": "SELECT COUNT(*) AS total FROM TestTable",
}
