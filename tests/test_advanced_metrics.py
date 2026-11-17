from app.services.advanced_metrics import (
    analyze_advanced_metrics,
    calculate_complexity,
    estimate_technical_debt,
    find_duplicate_blocks,
)
import ast


def test_simple_function_complexity():
    tree = ast.parse("def add(a, b):\n    return a + b")
    function = tree.body[0]

    assert calculate_complexity(function) == 1


def test_conditional_function_complexity():
    code = """
def check(value):
    if value > 10:
        return True
    else:
        return False
"""
    tree = ast.parse(code)

    assert calculate_complexity(tree.body[0]) == 2


def test_maintainability_index_is_in_range():
    code = """
def calculate(a, b):
    result = a + b
    return result
"""
    metrics = analyze_advanced_metrics(code)

    assert 0 <= metrics["maintainability_index"] <= 100


def test_duplicate_code_detection():
    code = """
value = 10
result = value + 5
print(result)

value = 10
result = value + 5
print(result)
"""
    duplicates = find_duplicate_blocks(code)

    assert len(duplicates) > 0
    assert duplicates[0]["occurrences"] > 1


def test_technical_debt_estimation():
    class Finding:
        def __init__(self, severity):
            self.severity = severity

    findings = [
        Finding("critical"),
        Finding("high"),
        Finding("medium"),
        Finding("low"),
    ]

    debt = estimate_technical_debt(findings)

    assert debt["estimated_minutes"] == 65
    assert debt["estimated_hours"] == round(65 / 60, 2)


def test_syntax_error_handling():
    metrics = analyze_advanced_metrics("def broken(")

    assert metrics["analysis_status"] == "syntax_error"
    assert metrics["total_complexity"] is None
    assert metrics["maintainability_index"] is None


def test_empty_code_metrics():
    metrics = analyze_advanced_metrics("")

    assert metrics["analysis_status"] == "success"
    assert metrics["lines_of_code"] == 0
    assert metrics["total_complexity"] == 0
