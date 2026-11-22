import ast
from collections import Counter


class ArchitectureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.dependencies = set()
        self.call_graph = []
        self.function_stack = []
        self.defined_functions = set()

    def visit_ClassDef(self, node):
        bases = [
            base.id if isinstance(base, ast.Name)
            else base.attr if isinstance(base, ast.Attribute)
            else ast.unparse(base)
            for base in node.bases
        ]

        methods = [
            item.name
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        self.classes.append({
            "name": node.name,
            "line": node.lineno,
            "bases": bases,
            "methods": methods,
        })

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        name = node.name

        if self.function_stack:
            qualified_name = f"{self.function_stack[-1]}.{name}"
        else:
            qualified_name = name

        self.functions.append({
            "name": qualified_name,
            "line": node.lineno,
        })

        self.defined_functions.add(name)
        self.function_stack.append(qualified_name)

        for child in node.body:
            self.visit(child)

        self.function_stack.pop()

    def visit_Call(self, node):
        caller = self.function_stack[-1] if self.function_stack else "<module>"

        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        else:
            callee = None

        if callee:
            self.call_graph.append({
                "caller": caller,
                "callee": callee,
            })

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.dependencies.add(alias.name.split(".")[0])

    def visit_ImportFrom(self, node):
        if node.module:
            self.dependencies.add(node.module.split(".")[0])


def analyze_architecture(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "classes": [],
            "functions": [],
            "dependencies": [],
            "call_graph": [],
            "coupling_metrics": [],
            "analysis_status": "syntax_error",
        }

    visitor = ArchitectureVisitor()
    visitor.visit(tree)

    internal_calls = [
        edge for edge in visitor.call_graph
        if edge["callee"] in visitor.defined_functions
    ]

    incoming = Counter(
        edge["callee"] for edge in internal_calls
    )

    outgoing = Counter(
        edge["caller"] for edge in internal_calls
    )

    coupling_metrics = [
        {
            "function": function["name"],
            "incoming_calls": incoming[
                function["name"].split(".")[-1]
            ],
            "outgoing_calls": outgoing[function["name"]],
        }
        for function in visitor.functions
    ]

    recommendations = []

    for cls in visitor.classes:
        if len(cls["methods"]) > 10:
            recommendations.append(
                f"Consider splitting class '{cls['name']}' "
                "because it contains more than 10 methods."
            )

    for metric in coupling_metrics:
        if metric["outgoing_calls"] > 5:
            recommendations.append(
                f"Review function '{metric['function']}' "
                "because it has more than 5 internal function calls."
            )

    if len(visitor.dependencies) > 10:
        recommendations.append(
            "Review imported dependencies to reduce unnecessary dependency complexity."
        )

    return {
        "classes": visitor.classes,
        "functions": visitor.functions,
        "dependencies": sorted(visitor.dependencies),
        "call_graph": internal_calls,
        "coupling_metrics": coupling_metrics,
        "recommendations": recommendations,
        "analysis_status": "success",
    }
