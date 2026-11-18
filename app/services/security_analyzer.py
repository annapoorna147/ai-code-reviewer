import ast

from app.models.review import ReviewFinding


def analyze_security(code: str) -> list[ReviewFinding]:
    findings = []

    def add_finding(title, severity, line, explanation, suggestion):
        findings.append(
            ReviewFinding(
                title=title,
                severity=severity,
                line=max(1, line or 1),
                explanation=explanation,
                suggestion=suggestion,
            )
        )

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return findings

    # Track variables assigned dynamically constructed SQL.
    sql_variables = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, (ast.JoinedStr, ast.BinOp)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        sql_variables[target.id] = node.lineno

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        function = node.func

        if isinstance(function, ast.Name):
            name = function.id
            module = None
        elif isinstance(function, ast.Attribute):
            name = function.attr
            module = (
                function.value.id
                if isinstance(function.value, ast.Name)
                else None
            )
        else:
            continue

        # SQL injection detection.
        if name in {"execute", "executemany"} and node.args:
            query = node.args[0]
            vulnerable = (
                isinstance(query, (ast.JoinedStr, ast.BinOp))
                or (
                    isinstance(query, ast.Name)
                    and query.id in sql_variables
                )
            )

            if vulnerable:
                add_finding(
                    "Potential SQL injection",
                    "critical",
                    node.lineno,
                    "An SQL query may contain dynamically constructed input.",
                    "Use parameterized queries instead of formatting SQL strings.",
                )

        # Unsafe pickle deserialization.
        if module == "pickle" and name in {"loads", "load"}:
            add_finding(
                "Unsafe pickle deserialization",
                "high",
                node.lineno,
                "Untrusted pickle data can execute arbitrary code during deserialization.",
                "Avoid unpickling untrusted data. Use a safe format such as JSON.",
            )

        # Unsafe YAML loading.
        if module == "yaml" and name == "load":
            safe_loader = any(
                keyword.arg == "Loader"
                and isinstance(keyword.value, ast.Attribute)
                and keyword.value.attr in {"SafeLoader", "CSafeLoader"}
                for keyword in node.keywords
            )

            if not safe_loader:
                add_finding(
                    "Potentially unsafe YAML loading",
                    "high",
                    node.lineno,
                    "yaml.load() without an explicit safe loader may construct unsafe objects.",
                    "Use yaml.safe_load() or explicitly specify SafeLoader.",
                )

        # Shell command execution.
        if name in {"run", "Popen", "call", "check_call", "check_output"}:
            shell_enabled = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )

            if shell_enabled:
                add_finding(
                    "Subprocess shell execution",
                    "high",
                    node.lineno,
                    "shell=True can allow command injection when input is not trusted.",
                    "Pass commands as argument lists and avoid shell=True.",
                )

        # Weak cryptographic hashes.
        if name in {"md5", "sha1"}:
            add_finding(
                "Weak cryptographic hash",
                "medium",
                node.lineno,
                f"{name.upper()} is not suitable for security-sensitive hashing.",
                "Use SHA-256 or an appropriate password-hashing algorithm.",
            )

        # Insecure random number generation.
        if module == "random" and name in {
            "random", "randint", "choice", "randrange"
        }:
            add_finding(
                "Potentially insecure random generation",
                "medium",
                node.lineno,
                "The random module is not designed for security-sensitive values.",
                "Use the secrets module for tokens and security-sensitive values.",
            )

    return findings
