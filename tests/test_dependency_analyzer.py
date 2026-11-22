from app.services.dependency_analyzer import analyze_dependencies


def test_detects_imported_packages():
    code = """
import os
import requests
import json
"""

    result = analyze_dependencies(code)

    assert result["analysis_status"] == "success"
    assert "os" in result["imports"]
    assert "requests" in result["imports"]
    assert "json" in result["imports"]


def test_detects_unused_imports():
    code = """
import os
import json

print(json.dumps({"hello": "world"}))
"""

    result = analyze_dependencies(code)

    assert "os" in result["unused_imports"]
    assert "json" not in result["unused_imports"]


def test_detects_duplicate_imports():
    code = """
import os
import json
import os
"""

    result = analyze_dependencies(code)

    assert "os" in result["duplicate_imports"]


def test_detects_from_imports():
    code = """
from pathlib import Path
from collections import Counter

path = Path("test.txt")
"""

    result = analyze_dependencies(code)

    assert "pathlib" in result["imports"]
    assert "collections" in result["imports"]


def test_detects_risky_package_patterns():
    code = """
import pickle

data = pickle.loads(user_data)
"""

    result = analyze_dependencies(code)

    assert len(result["risky_patterns"]) >= 1


def test_handles_syntax_errors():
    result = analyze_dependencies("import os\nif (")

    assert result["analysis_status"] == "syntax_error"
    assert result["imports"] == []
    assert result["unused_imports"] == []


def test_empty_code():
    result = analyze_dependencies("")

    assert result["analysis_status"] == "success"
    assert result["imports"] == []
    assert result["unused_imports"] == []
    assert result["duplicate_imports"] == []
