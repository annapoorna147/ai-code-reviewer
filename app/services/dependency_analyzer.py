import ast
from collections import Counter


class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.imported_names = []
        self.used_names = set()
        self.risky_patterns = []

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split(".")[0]
            self.imports.append(module)

            bound_name = alias.asname or alias.name.split(".")[0]
            self.imported_names.append((bound_name, module))

    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module.split(".")[0]
            self.imports.append(module)

            for alias in node.names:
                if alias.name == "*":
                    continue

                bound_name = alias.asname or alias.name
                self.imported_names.append((bound_name, module))

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "pickle"
                and node.func.attr in {"load", "loads"}
            ):
                self.risky_patterns.append(
                    "Unsafe pickle deserialization detected."
                )

            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "yaml"
                and node.func.attr == "load"
            ):
                safe_loader = any(
                    keyword.arg == "Loader"
                    and isinstance(keyword.value, ast.Attribute)
                    and keyword.value.attr == "SafeLoader"
                    for keyword in node.keywords
                )

                if not safe_loader:
                    self.risky_patterns.append(
                        "Potentially unsafe YAML loading detected."
                    )

        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.risky_patterns.append(
                "Dynamic eval execution detected."
            )

        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr in {
                    "run", "Popen", "call", "check_call", "check_output"
                }
            ):
                if any(
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                ):
                    self.risky_patterns.append(
                        "Subprocess execution with shell=True detected."
                    )

        self.generic_visit(node)


def analyze_dependencies(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "analysis_status": "syntax_error",
            "imports": [],
            "unused_imports": [],
            "duplicate_imports": [],
            "risky_patterns": [],
            "recommendations": [],
        }

    visitor = DependencyVisitor()
    visitor.visit(tree)

    import_counts = Counter(visitor.imports)

    duplicate_imports = sorted(
        module
        for module, count in import_counts.items()
        if count > 1
    )

    unused_imports = sorted({
        module
        for name, module in visitor.imported_names
        if name not in visitor.used_names
    })

    recommendations = []

    if unused_imports:
        recommendations.append(
            "Remove unused imports: " + ", ".join(unused_imports)
        )

    if duplicate_imports:
        recommendations.append(
            "Consolidate duplicate imports: " + ", ".join(duplicate_imports)
        )

    if visitor.risky_patterns:
        recommendations.append(
            "Review potentially unsafe package usage before deployment."
        )

    return {
        "analysis_status": "success",
        "imports": sorted(import_counts.keys()),
        "unused_imports": unused_imports,
        "duplicate_imports": duplicate_imports,
        "risky_patterns": sorted(set(visitor.risky_patterns)),
        "recommendations": recommendations,
    }
