from app.services.code_analyzer import analyze_code


def test_detect_eval():
    code = """
result = eval(user_input)
"""
    findings = analyze_code(code)

    assert any(f.title == "Use of eval()" for f in findings)


def test_detect_exec():
    code = """
exec(user_input)
"""
    findings = analyze_code(code)

    assert any(f.title == "Use of exec()" for f in findings)


def test_detect_hardcoded_secret():
    code = """
password = "mysecret123"
"""
    findings = analyze_code(code)

    assert any(
        f.title == "Possible hardcoded secret"
        for f in findings
    )


def test_detect_bare_except():
    code = """
try:
    print("Hello")
except:
    pass
"""
    findings = analyze_code(code)

    assert any(
        f.title == "Bare exception handler"
        for f in findings
    )


def test_detect_empty_function():
    code = """
def unfinished_function():
    pass
"""
    findings = analyze_code(code)

    assert any(f.title == "Empty function" for f in findings)


def test_valid_code():
    code = """
def add(a, b):
    return a + b

print(add(2, 3))
"""
    findings = analyze_code(code)

    assert findings == []


def test_syntax_error():
    code = """
def broken_function(
    print("Hello")
"""
    findings = analyze_code(code)

    assert any(f.title == "Python syntax error" for f in findings)
