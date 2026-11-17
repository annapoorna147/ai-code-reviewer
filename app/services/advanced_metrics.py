import ast
import math
from collections import Counter


def calculate_complexity(node):
    """Calculate cyclomatic complexity for one function."""
    complexity = 1

    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            complexity += 1

        elif isinstance(child, ast.ExceptHandler):
            complexity += 1

        elif isinstance(child, ast.IfExp):
            complexity += 1

        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1

        elif isinstance(child, (ast.comprehension,)):
            complexity += 1

    return complexity


def find_function_complexities(tree):
    """Return complexity measurements for all functions."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results.append({
                "name": node.name,
                "line": node.lineno,
                "complexity": calculate_complexity(node),
            })

    return results


def calculate_maintainability_index(code, tree, total_complexity):
    """
    Calculate an approximate Maintainability Index.

    Uses a Halstead-volume estimate based on Python AST operators
    and operands, with the commonly used MI formula.
    """
    operators = []
    operands = []

    for node in ast.walk(tree):
        if isinstance(node, ast.operator):
            operators.append(type(node).__name__)

        elif isinstance(node, ast.unaryop):
            operators.append(type(node).__name__)

        elif isinstance(node, ast.boolop):
            operators.append(type(node).__name__)

        elif isinstance(node, ast.cmpop):
            operators.append(type(node).__name__)

        elif isinstance(node, ast.Name):
            operands.append(node.id)

        elif isinstance(node, ast.Constant):
            operands.append(repr(node.value))

    unique_operators = len(set(operators))
    unique_operands = len(set(operands))
    total_operators = len(operators)
    total_operands = len(operands)

    vocabulary = unique_operators + unique_operands
    length = total_operators + total_operands

    if vocabulary == 0 or length == 0:
        halstead_volume = 0
    else:
        halstead_volume = length * math.log2(vocabulary)

    loc = max(1, len(code.splitlines()))
    volume_term = math.log(max(halstead_volume, 1))
    loc_term = math.log(loc)

    maintainability = (
        171
        - 5.2 * volume_term
        - 0.23 * total_complexity
        - 16.2 * loc_term
    ) * 100 / 171

    return round(max(0, min(100, maintainability)), 2)


def find_duplicate_blocks(code, minimum_lines=3):
    """Find repeated sequences of normalized source lines."""
    normalized = [
        " ".join(line.strip().split())
        for line in code.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    occurrences = Counter()

    for size in range(minimum_lines, len(normalized) + 1):
        for index in range(len(normalized) - size + 1):
            block = tuple(normalized[index:index + size])
            occurrences[block] += 1

    duplicate_blocks = []

    for block, count in occurrences.items():
        if count > 1:
            duplicate_blocks.append({
                "lines": len(block),
                "occurrences": count,
                "code": list(block),
            })

    # Keep the longest repeated blocks to avoid excessive overlap.
    duplicate_blocks.sort(
        key=lambda item: (
            item["lines"],
            item["occurrences"],
        ),
        reverse=True,
    )

    return duplicate_blocks[:10]


def estimate_technical_debt(findings):
    """Estimate remediation time using severity-based effort."""
    effort_minutes = {
        "critical": 30,
        "high": 20,
        "medium": 10,
        "low": 5,
    }

    total_minutes = sum(
        effort_minutes.get(finding.severity, 0)
        for finding in findings
    )

    return {
        "estimated_minutes": total_minutes,
        "estimated_hours": round(total_minutes / 60, 2),
    }


def analyze_advanced_metrics(code, findings=None):
    """Generate advanced code quality metrics."""
    findings = findings or []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "lines_of_code": len([
                line for line in code.splitlines() if line.strip()
            ]),
            "total_complexity": None,
            "function_complexities": [],
            "maintainability_index": None,
            "duplicate_blocks": [],
            "technical_debt": estimate_technical_debt(findings),
            "analysis_status": "syntax_error",
        }

    function_metrics = find_function_complexities(tree)

    total_complexity = sum(
        item["complexity"] for item in function_metrics
    )

    maintainability = calculate_maintainability_index(
        code,
        tree,
        total_complexity,
    )

    duplicates = find_duplicate_blocks(code)

    return {
        "lines_of_code": len([
            line for line in code.splitlines() if line.strip()
        ]),
        "total_complexity": total_complexity,
        "function_complexities": function_metrics,
        "maintainability_index": maintainability,
        "duplicate_blocks": duplicates,
        "technical_debt": estimate_technical_debt(findings),
        "analysis_status": "success",
    }
