import re
from typing import List, Dict

def build_fix_dict(type: str, file: str, line: int, message: str, fix_desc: str) -> Dict:
    """Build a complete fix dictionary with all required fields."""
    fix_id = f"{type}_{file.replace('/', '_')}_{line}"
    formatted = f"{type} error in {file} line {line} → Fix: {fix_desc}"
    commit_message = f"[AI-AGENT] Fix {type} in {file} line {line}"
    
    return {
        "id": fix_id,
        "type": type,
        "file": file,
        "line": line,
        "message": message,
        "formatted": formatted,
        "fix_description": fix_desc,
        "commit_message": commit_message,
        "status": "pending"
    }

def parse_flake8(raw: str) -> List[Dict]:
    """Parse flake8 output into structured fix dictionaries."""
    fixes = []
    pattern = r"([^:\n]+):(\d+):\d+: ([EW]\d+) (.+)"
    
    for match in re.finditer(pattern, raw):
        file_path = match.group(1)
        line_num = int(match.group(2))
        code = match.group(3)
        message = match.group(4)
        
        # Determine error type
        if code in ["F401", "F403", "F811"]:
            error_type = "IMPORT"
        elif (code.startswith("E1") and "indent" in message.lower()) or code in ["W191", "W291"]:
            error_type = "INDENTATION"
        elif code.startswith("E9"):
            error_type = "SYNTAX"
        else:
            error_type = "LINTING"
        
        # Determine fix description
        fix_desc_map = {
            "F401": "remove the import statement",
            "E302": "add blank lines before function",
            "E501": "shorten the line length",
            "W291": "remove trailing whitespace"
        }
        fix_desc = fix_desc_map.get(code, "fix the linting issue")
        
        fix = build_fix_dict(error_type, file_path, line_num, message, fix_desc)
        fixes.append(fix)
    
    return fixes

def parse_mypy(raw: str) -> List[Dict]:
    """Parse mypy output into structured fix dictionaries."""
    fixes = []
    pattern = r"([^:\n]+):(\d+): error: (.+)"
    
    for match in re.finditer(pattern, raw):
        file_path = match.group(1)
        line_num = int(match.group(2))
        message = match.group(3)
        
        fix = build_fix_dict("TYPE_ERROR", file_path, line_num, message, "fix the type annotation")
        fixes.append(fix)
    
    return fixes

def parse_pytest(raw: str) -> List[Dict]:
    """Parse pytest output into structured fix dictionaries."""
    fixes = []
    pattern = r"FAILED ([^:\n]+)::([^\n]+)"
    
    for match in re.finditer(pattern, raw):
        file_path = match.group(1)
        test_name = match.group(2)
        message = f"Test failed: {test_name}"
        
        fix = build_fix_dict("LOGIC", file_path, 0, message, "fix the logic error causing test failure")
        fixes.append(fix)
    
    return fixes

def parse_eslint(raw: str) -> List[Dict]:
    """Parse ESLint output into structured fix dictionaries."""
    errors = []
    # Compact format: path/file.js: line X, col Y, Error - message (rule)
    pattern = r"([^\n:]+\.[jt]sx?): line (\d+), col \d+, (?:Error|Warning) - (.+?) \((.+?)\)"
    
    for m in re.finditer(pattern, raw):
        file, line, message, rule = m.groups()
        rule = rule.strip()
        
        if any(x in rule for x in ["import", "require", "module"]):
            btype = "IMPORT"
        elif "indent" in rule:
            btype = "INDENTATION"
        elif any(x in rule for x in ["no-unused", "no-undef", "no-var"]):
            btype = "LINTING"
        elif any(x in rule for x in ["syntax", "parse"]):
            btype = "SYNTAX"
        else:
            btype = "LINTING"
        
        fix_map = {
            "no-unused-vars": "remove the unused variable",
            "no-undef": "define or import the variable",
            "indent": "fix indentation to consistent spaces",
            "semi": "add missing semicolon",
            "no-console": "remove console statement",
            "eqeqeq": "use === instead of ==",
            "no-var": "replace var with let or const",
        }
        fix_desc = next((v for k, v in fix_map.items() if k in rule), f"fix the {rule} issue")
        
        errors.append(build_fix_dict(btype, file.strip(), int(line), message.strip(), fix_desc))
    
    return errors

def parse_tsc(raw: str) -> List[Dict]:
    """Parse TypeScript compiler output."""
    errors = []
    pattern = r"([^\n(]+)\((\d+),\d+\): error TS\d+: (.+)"
    
    for m in re.finditer(pattern, raw):
        file, line, message = m.groups()
        errors.append(build_fix_dict("TYPE_ERROR", file.strip(), int(line), message.strip(), "fix the TypeScript type error"))
    
    return errors

def parse_jest(raw: str) -> List[Dict]:
    """Parse Jest test output - extract actual file paths and line numbers."""
    errors = []
    
    # Match FAIL lines: FAIL src/path/to/file.test.js
    fail_files = re.findall(r'FAIL\s+(\S+)', raw)
    
    # Match actual Jest test failure format: ● TestSuite › TestName
    pattern = r"● (.+?) › (.+)"
    
    for m in re.finditer(pattern, raw):
        suite = m.group(1).strip()
        test = m.group(2).strip()
        
        # Try to extract file and line from stack trace after the failure
        context = raw[m.end():m.end()+500]
        
        # Look for "at Object.<anonymous> (src/file.js:10:5)" or similar
        file_match = re.search(r'at\s+\S+\s+\(([^)]+?):(\d+):\d+\)', context)
        if not file_match:
            # Try simpler pattern: "at src/file.js:10:5"
            file_match = re.search(r'at\s+([^:\s]+?):(\d+):\d+', context)
        
        if file_match:
            file = file_match.group(1)
            line = int(file_match.group(2))
        else:
            # Fall back to the FAIL file for this test suite
            file = None
            for f in fail_files:
                if suite.lower().replace(' ', '') in f.lower().replace('/', '').replace('.', ''):
                    file = f
                    break
            if not file:
                file = fail_files[0] if fail_files else f"test/{suite}"
            line = 0
        
        # Clean up file path — remove absolute path noise
        file = re.sub(r'^.*?/(src/|packages/|lib/)', r'\1', file)
        
        errors.append(build_fix_dict(
            "LOGIC", file, line,
            f"Test failed: {suite} › {test}",
            f"fix the failing test: {test}"
        ))
    
    return errors

def parse_go(raw: str) -> List[Dict]:
    """Parse Go vet, test, and gofmt output."""
    errors = []
    
    # Pattern 1: go vet/compile errors: ./file.go:10:5: message OR file.go:10:5: message
    pattern1 = r"\.?/?([^\n:]+\.go):(\d+):\d+: (.+)"
    for m in re.finditer(pattern1, raw):
        file, line, message = m.groups()
        file = file.strip().lstrip('./')
        message = message.strip()
        
        # Determine error type
        if "undefined:" in message or "not declared" in message or "cannot find" in message:
            error_type = "IMPORT"
        elif "syntax error" in message.lower() or "expected" in message.lower():
            error_type = "SYNTAX"
        elif "type" in message.lower() and ("mismatch" in message.lower() or "cannot use" in message.lower()):
            error_type = "TYPE_ERROR"
        else:
            error_type = "LINTING"
        
        errors.append(build_fix_dict(error_type, file, int(line), message, f"fix the {error_type.lower()} error"))
    
    # Pattern 2: go test failures with file paths
    # Example: --- FAIL: TestFunction (0.00s)
    #          file_test.go:15: Error message
    test_fail_pattern = r"--- FAIL: (\w+) \([^)]+\)\s+([^\n:]+\.go):(\d+): (.+)"
    for m in re.finditer(test_fail_pattern, raw):
        test_name, file, line, message = m.groups()
        file = file.strip().lstrip('./')
        errors.append(build_fix_dict("LOGIC", file, int(line), f"Test {test_name} failed: {message.strip()}", "fix the failing test logic"))
    
    # Pattern 3: FAIL package lines
    fail_pattern = r"FAIL\s+([^\s]+)\s+\[build failed\]"
    for m in re.finditer(fail_pattern, raw):
        pkg = m.group(1)
        # Try to find the actual file from the package name
        pkg_file = pkg.replace("/", "/") + ".go"
        errors.append(build_fix_dict("SYNTAX", pkg_file, 0, "Build failed for package", "fix the build errors"))
    
    # Pattern 4: gofmt output (files that need formatting)
    # gofmt -l outputs filenames that need formatting
    if "=GOFMT=" in raw:
        gofmt_section = raw.split("=GOFMT=")[1] if "=GOFMT=" in raw else ""
        for line in gofmt_section.split('\n'):
            line = line.strip()
            if line.endswith('.go') and not line.startswith('='):
                errors.append(build_fix_dict("INDENTATION", line, 0, "File needs formatting", "run gofmt to fix formatting"))
    
    return errors

def parse_java(raw: str) -> List[Dict]:
    """Parse Java compiler and Maven output."""
    errors = []
    # javac: file.java:10: error: message
    pattern = r"([^\n:]+\.java):(\d+): error: (.+)"
    
    for m in re.finditer(pattern, raw):
        file, line, message = m.groups()
        btype = "IMPORT" if "cannot find symbol" in message else "SYNTAX"
        errors.append(build_fix_dict(btype, file.strip(), int(line), message.strip(), "fix the Java compile error"))
    
    return errors

def parse_rust(raw: str) -> List[Dict]:
    """Parse Rust compiler output."""
    errors = []
    pattern = r"error(?:\[E\d+\])?: (.+)\n\s+--> ([^\n:]+):(\d+)"
    
    for m in re.finditer(pattern, raw):
        message, file, line = m.groups()
        errors.append(build_fix_dict("SYNTAX", file.strip(), int(line), message.strip(), "fix the Rust compile error"))
    
    return errors

def deduplicate(fixes: List[Dict]) -> List[Dict]:
    """Remove duplicate fixes by id field."""
    seen_ids = set()
    unique_fixes = []
    
    for fix in fixes:
        if fix["id"] not in seen_ids:
            seen_ids.add(fix["id"])
            unique_fixes.append(fix)
    
    return unique_fixes
