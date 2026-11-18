from app.services.security_analyzer import analyze_security


def test_detects_sql_injection():
    code = '''
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
'''
    findings = analyze_security(code)
    assert any("SQL injection" in f.title for f in findings)


def test_detects_pickle_deserialization():
    code = '''
import pickle
data = pickle.loads(user_input)
'''
    findings = analyze_security(code)
    assert any("pickle" in f.title.lower() for f in findings)


def test_detects_unsafe_yaml():
    code = '''
import yaml
data = yaml.load(user_input)
'''
    findings = analyze_security(code)
    assert any("YAML" in f.title for f in findings)


def test_allows_safe_yaml():
    code = '''
import yaml
data = yaml.safe_load(user_input)
'''
    findings = analyze_security(code)
    assert not any("YAML" in f.title for f in findings)


def test_detects_subprocess_shell_true():
    code = '''
import subprocess
subprocess.run(command, shell=True)
'''
    findings = analyze_security(code)
    assert any("Subprocess" in f.title for f in findings)


def test_detects_weak_hash():
    code = '''
import hashlib
digest = hashlib.md5(data)
'''
    findings = analyze_security(code)
    assert any("hash" in f.title.lower() for f in findings)


def test_detects_insecure_random():
    code = '''
import random
token = random.randint(1000, 9999)
'''
    findings = analyze_security(code)
    assert any("random" in f.title.lower() for f in findings)


def test_clean_code_has_no_security_findings():
    code = '''
def add(a, b):
    return a + b
'''
    assert analyze_security(code) == []


def test_invalid_python_returns_no_security_findings():
    code = "def broken(:"
    assert analyze_security(code) == []
