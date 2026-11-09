import ast
import re

from app.models.review import ReviewFinding


SECRET_PATTERN = re.compile(
    r"""(?i)\b(password|passwd|api_key|secret_key)\b\s*[:=]\s*["'][^"']+["']"""
)


def analyze_code(code: str) -> list[ReviewFinding]:
    findings = []

    def add_finding(title, severity, line, explanation, suggestion):
        findings.append(
            ReviewFinding(
                title=title,
                severity=severity,
                line=max(1, line),
                explanation=explanation,
                suggestion=suggestion
            )
        )

    lines = code.splitlines()

    # Check for hardcoded secrets.
    for line_number, line in enumerate(lines, start=1):
        if SECRET_PATTERN.search(line):
            add_finding(
                "Possible hardcoded secret",
                "high",
                line_number,
                "A password, API key, or secret may be hardcoded.",
                "Load secrets from environment variables or a secret manager."
            )

    # Parse Python source code.
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        add_finding(
            "Python syntax error",
            "high",
            error.lineno or 1,
            error.msg,
            "Fix the syntax error before running this code."
        )
        return findings

    for node in ast.walk(tree):

        # Detect eval() and exec().
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    add_finding(
                        "Use of eval()",
                        "high",
                        node.lineno,
                        "eval() executes dynamically supplied expressions.",
                        "Use safer alternatives such as ast.literal_eval() when appropriate."
                    )

                elif node.func.id == "exec":
                    add_finding(
                        "Use of exec()",
                        "high",
                        node.lineno,
                        "exec() dynamically executes Python statements.",
                        "Avoid dynamic execution or use a restricted, explicit design."
                    )

        # Detect broad exception handling.
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                add_finding(
                    "Bare exception handler",
                    "medium",
                    node.lineno,
                    "Catching every exception can hide unexpected failures.",
                    "Catch specific exception types."
                )

            elif isinstance(node.type, ast.Name):
                if node.type.id == "Exception":
                    add_finding(
                        "Broad exception handling",
                        "low",
                        node.lineno,
                        "Catching Exception may hide errors that should be handled separately.",
                        "Catch only the exceptions your application expects."
                    )

        # Detect empty functions.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body

            if len(body) == 1 and isinstance(body[0], ast.Pass):
                add_finding(
                    "Empty function",
                    "low",
                    node.lineno,
                    f"Function '{node.name}' currently contains only pass.",
                    "Implement the function or remove it if it is unnecessary."
                )

    return findings
