from app.services.architecture_analyzer import analyze_architecture


def test_detects_classes_and_methods():
    code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
"""

    result = analyze_architecture(code)

    assert result["analysis_status"] == "success"
    assert len(result["classes"]) == 1
    assert result["classes"][0]["name"] == "Calculator"
    assert result["classes"][0]["methods"] == ["add", "multiply"]


def test_detects_function_calls():
    code = """
def calculate():
    return add(10, 20)

def add(a, b):
    return a + b
"""

    result = analyze_architecture(code)

    assert {
        "caller": "calculate",
        "callee": "add",
    } in result["call_graph"]


def test_detects_import_dependencies():
    code = """
import os
import json
from pathlib import Path
"""

    result = analyze_architecture(code)

    assert "os" in result["dependencies"]
    assert "json" in result["dependencies"]
    assert "pathlib" in result["dependencies"]


def test_detects_class_inheritance():
    code = """
class Animal:
    pass

class Dog(Animal):
    pass
"""

    result = analyze_architecture(code)

    dog = next(
        item for item in result["classes"]
        if item["name"] == "Dog"
    )

    assert dog["bases"] == ["Animal"]


def test_handles_syntax_errors():
    result = analyze_architecture("class Broken(")

    assert result["analysis_status"] == "syntax_error"
    assert result["classes"] == []
    assert result["functions"] == []
    assert result["call_graph"] == []


def test_empty_code():
    result = analyze_architecture("")

    assert result["analysis_status"] == "success"
    assert result["classes"] == []
    assert result["functions"] == []
    assert result["dependencies"] == []
    assert result["call_graph"] == []
