"""
Optimized parsers with O(n) time complexity and minimal memory overhead.
Uses compiled regex patterns and efficient data structures.
"""
import re
from typing import List, Dict, Set
from functools import lru_cache

# Pre-compile all regex patterns for O(1) lookup - MAJOR PERFORMANCE BOOST
PATTERNS = {
    'flake8': re.compile(r"([^:\n]+):(\d+):\d+: ([EW]\d+) (.+)"),
    'mypy': re.compile(r"([^:\n]+):(\d+): error: (.+)"),
    'pytest': re.compile(r"FAILED ([^:\n]+)::([^\n]+)"),
    'eslint': re.compile(r"([^\n:]+\.[jt]sx?): line (\d+), col \d+, (?:Error|Warning) - (.+?) \((.+?)\)"),
    'tsc': re.compile(r"([^\n(]+)\((\d+),\d+\): error TS\d+: (.+)"),
    'jest_fail': re.compile(r'FAIL\s+(\S+)'),
    'jest_test': re.compile(r"● (.+?) › (.+)"),
    'jest_stack': re.compile(r'at\s+\S+\s+\(([^)]+?):(\d+):\d+\)'),
    'node_syntax': re.compile(r"([^\n:]+):(\d+)\n(.+?)\n\s*\^\s*\n\s*(.+)"),
    'go_error': re.compile(r"\.?/?([^\n:]+\.go):(\d+):\d+: (.+)"),
    'go_test_fail': re.compile(r"--- FAIL: (\w+) \([^)]+\)\s+([^\n:]+\.go):(\d+): (.+)"),
    'go_fail_pkg': re.compile(r"FAIL\s+([^\s]+)\s+\[build failed\]"),
    'java_error': re.compile(r"([^\n:]+\.java):(\d+): error: (.+)"),
    'java_maven': re.compile(r"\[ERROR\]\s+([^\[]+\.java):\[(\d+),\d+\]\s+(.+)"),
    'java_gradle': re.compile(r"([^\n:]+\.java):(\d+): error: (.+)"),
    'rust_error': re.compile(r"error(?:\[E\d+\])?: (.+)\n\s+--> ([^\n:]+):(\d+)"),
    'rust_clippy': re.compile(r"warning: (.+)\n\s+--> ([^\n:]+):(\d+)")
}

# Pre-defined mappings for O(1) lookups
FLAKE8_TYPE_MAP = {
    'F401': 'IMPORT', 'F403': 'IMPORT', 'F811': 'IMPORT',
    'W191': 'INDENTATION', 'W291': 'INDENTATION',
    'E9': 'SYNTAX'  # Prefix match
}

FLAKE8_FIX_MAP = {
    'F401': "remove the import statement",
    'E302': "add blank lines before function",
    'E501': "shorten the line length",
    'W291': "remove trailing whitespace"
}

ESLINT_RULE_MAP = {
    'no-unused-vars': ("LINTING", "remove the unused variable"),
    'no-undef': ("LINTING", "define or import the variable"),
    'indent': ("INDENTATION", "fix indentation to consistent spaces"),
    'semi': ("LINTING", "add missing semicolon"),
    'no-console': ("LINTING", "remove console statement"),
    'eqeqeq': ("LINTING", "use === instead of =="),
    'no-var': ("LINTING", "replace var with let or const"),
}

@lru_cache(maxsize=1024)
def build_fix_id(type_str: str, file: str, line: int) -> str:
    """Cached fix ID generation - O(1) for repeated calls."""
    return f"{type_str}_{file.replace('/', '_')}_{line}"

def build_fix_dict(type_str: str, file: str, line: int, message: str, fix_desc: str) -> Dict:
    """Build fix dictionary with minimal string operations."""
    fix_id = build_fix_id(type_str, file, line)
    
    return {
        "id": fix_id,
        "type": type_str,
        "file": file,
        "line": line,
        "message": message,
        "formatted": f"{type_str} error in {file} line {line} → Fix: {fix_desc}",
        "fix_description": fix_desc,
        "commit_message": f"[AI-AGENT] Fix {type_str} in {file} line {line}",
        "status": "pending"
    }

def parse_flake8(raw: str) -> List[Dict]:
    """Optimized flake8 parser - O(n) single pass."""
    if not raw:
        return []
    
    fixes = []
    for match in PATTERNS['flake8'].finditer(raw):
        file_path, line_num, code, message = match.groups()
        line_num = int(line_num)
        
        # O(1) type lookup with fallback
        if code in FLAKE8_TYPE_MAP:
            error_type = FLAKE8_TYPE_MAP[code]
        elif code.startswith('E9'):
            error_type = 'SYNTAX'
        elif code.startswith('E1') and 'indent' in message.lower():
            error_type = 'INDENTATION'
        else:
            error_type = 'LINTING'
        
        # O(1) fix description lookup
        fix_desc = FLAKE8_FIX_MAP.get(code, "fix the linting issue")
        
        fixes.append(build_fix_dict(error_type, file_path, line_num, message, fix_desc))
    
    return fixes

def parse_mypy(raw: str) -> List[Dict]:
    """Optimized mypy parser - O(n) single pass."""
    if not raw:
        return []
    
    return [
        build_fix_dict("TYPE_ERROR", m.group(1), int(m.group(2)), m.group(3), "fix the type annotation")
        for m in PATTERNS['mypy'].finditer(raw)
    ]

def parse_pytest(raw: str) -> List[Dict]:
    """Optimized pytest parser - O(n) single pass."""
    if not raw:
        return []
    
    return [
        build_fix_dict("LOGIC", m.group(1), 0, f"Test failed: {m.group(2)}", "fix the logic error causing test failure")
        for m in PATTERNS['pytest'].finditer(raw)
    ]

def parse_eslint(raw: str) -> List[Dict]:
    """Optimized ESLint parser - O(n) with O(1) rule lookups."""
    if not raw:
        return []
    
    errors = []
    
    # Pattern 1: Standard ESLint format
    for m in PATTERNS['eslint'].finditer(raw):
        file, line, message, rule = m.groups()
        rule = rule.strip()
        line = int(line)
        
        # O(1) rule lookup
        if rule in ESLINT_RULE_MAP:
            btype, fix_desc = ESLINT_RULE_MAP[rule]
        else:
            # Fast categorization
            if 'import' in rule or 'require' in rule or 'module' in rule:
                btype, fix_desc = 'IMPORT', f"fix the {rule} issue"
            elif 'indent' in rule:
                btype, fix_desc = 'INDENTATION', f"fix the {rule} issue"
            elif 'syntax' in rule or 'parse' in rule or 'Parsing error' in message:
                btype, fix_desc = 'SYNTAX', f"fix the syntax error"
            else:
                btype, fix_desc = 'LINTING', f"fix the {rule} issue"
        
        errors.append(build_fix_dict(btype, file.strip(), line, message.strip(), fix_desc))
    
    # Pattern 2: Simple format without rule name (for parsing errors)
    # Format: file.js: line 10, col 21, Error - message
    simple_pattern = re.compile(r"([^\n:]+\.[jt]sx?): line (\d+), col \d+, Error - (.+)")
    for m in simple_pattern.finditer(raw):
        file, line, message = m.groups()
        line = int(line)
        
        if 'Parsing error' in message or 'Unexpected token' in message:
            btype, fix_desc = 'SYNTAX', "fix the syntax error"
        else:
            btype, fix_desc = 'LINTING', "fix the linting issue"
        
        errors.append(build_fix_dict(btype, file.strip(), line, message.strip(), fix_desc))
    
    return errors

def parse_node_syntax(raw: str) -> List[Dict]:
    """Parse Node.js --check syntax errors."""
    if not raw or '=NODE_SYNTAX=' not in raw:
        return []
    
    errors = []
    # Extract NODE_SYNTAX section
    if '=NODE_SYNTAX=' in raw:
        section_start = raw.find('=NODE_SYNTAX=') + len('=NODE_SYNTAX=')
        section_end = raw.find('=ESLINT=', section_start)
        if section_end == -1:
            section_end = len(raw)
        section = raw[section_start:section_end]
        
        # Parse each file's errors - format: file.js:\n/full/path/file.js:line\ncode\n^\nSyntaxError: message
        lines = section.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for file path with line number: /path/file.js:10
            if '.js:' in line and '/' in line and line[0] == '/':
                try:
                    # Extract file and line number
                    parts = line.split(':')
                    if len(parts) >= 2:
                        full_path = parts[0]
                        line_num = int(parts[1]) if parts[1].isdigit() else 0
                        
                        # Get filename only
                        file_name = full_path.split('/')[-1]
                        
                        # Look ahead for SyntaxError message
                        error_msg = "Syntax error"
                        for j in range(i+1, min(i+10, len(lines))):
                            if 'SyntaxError:' in lines[j] or 'Error:' in lines[j]:
                                error_msg = lines[j].strip()
                                break
                        
                        errors.append(build_fix_dict("SYNTAX", file_name, line_num, error_msg, "fix the syntax error"))
                except (ValueError, IndexError):
                    pass
            i += 1
    
    return errors

def parse_tsc(raw: str) -> List[Dict]:
    """Optimized TypeScript parser - O(n) single pass."""
    if not raw:
        return []
    
    return [
        build_fix_dict("TYPE_ERROR", m.group(1).strip(), int(m.group(2)), m.group(3).strip(), "fix the TypeScript type error")
        for m in PATTERNS['tsc'].finditer(raw)
    ]

def parse_jest(raw: str) -> List[Dict]:
    """Optimized Jest parser - O(n) with minimal string operations."""
    if not raw:
        return []
    
    errors = []
    fail_files = [m.group(1) for m in PATTERNS['jest_fail'].finditer(raw)]
    
    for m in PATTERNS['jest_test'].finditer(raw):
        suite, test = m.group(1).strip(), m.group(2).strip()
        
        # Extract file and line from stack trace (limited context search)
        context = raw[m.end():m.end()+500]
        file_match = PATTERNS['jest_stack'].search(context)
        
        if file_match:
            file, line = file_match.group(1), int(file_match.group(2))
            # Clean path efficiently
            if '/(src/' in file or '/(packages/' in file or '/(lib/' in file:
                file = file[file.rfind('/(') + 2:]
        else:
            # Fast fallback
            file = next((f for f in fail_files if suite.lower().replace(' ', '') in f.lower().replace('/', '').replace('.', '')), 
                       fail_files[0] if fail_files else f"test/{suite}")
            line = 0
        
        errors.append(build_fix_dict("LOGIC", file, line, f"Test failed: {suite} › {test}", f"fix the failing test: {test}"))
    
    return errors

def parse_go(raw: str) -> List[Dict]:
    """Optimized Go parser - O(n) single pass with minimal allocations."""
    if not raw:
        return []
    
    errors = []
    
    # Pattern 1: Compile/vet errors
    for m in PATTERNS['go_error'].finditer(raw):
        file, line, message = m.group(1).strip().lstrip('./'), int(m.group(2)), m.group(3).strip()
        
        # Fast type detection
        if "undefined:" in message or "not declared" in message or "cannot find" in message:
            error_type = "IMPORT"
        elif "syntax error" in message or "expected" in message:
            error_type = "SYNTAX"
        elif "type" in message and ("mismatch" in message or "cannot use" in message):
            error_type = "TYPE_ERROR"
        else:
            error_type = "LINTING"
        
        errors.append(build_fix_dict(error_type, file, line, message, f"fix the {error_type.lower()} error"))
    
    # Pattern 2: Test failures
    for m in PATTERNS['go_test_fail'].finditer(raw):
        test_name, file, line, message = m.groups()
        errors.append(build_fix_dict("LOGIC", file.strip().lstrip('./'), int(line), 
                                     f"Test {test_name} failed: {message.strip()}", "fix the failing test logic"))
    
    # Pattern 3: Build failures
    for m in PATTERNS['go_fail_pkg'].finditer(raw):
        pkg_file = m.group(1).replace("/", "/") + ".go"
        errors.append(build_fix_dict("SYNTAX", pkg_file, 0, "Build failed for package", "fix the build errors"))
    
    # Pattern 4: gofmt (fast line-by-line check)
    if "=GOFMT=" in raw:
        gofmt_start = raw.find("=GOFMT=") + 8
        gofmt_end = raw.find("=", gofmt_start)
        gofmt_section = raw[gofmt_start:gofmt_end] if gofmt_end != -1 else raw[gofmt_start:]
        
        for line in gofmt_section.split('\n'):
            line = line.strip()
            if line.endswith('.go') and not line.startswith('='):
                errors.append(build_fix_dict("INDENTATION", line, 0, "File needs formatting", "run gofmt to fix formatting"))
    
    return errors

def parse_java(raw: str) -> List[Dict]:
    """Optimized Java parser - O(n) single pass. Handles javac, Maven, and Gradle."""
    if not raw:
        return []
    
    errors = []
    
    # Pattern 1: Maven errors [ERROR] path/File.java:[line,col] message
    for m in PATTERNS['java_maven'].finditer(raw):
        file, line, message = m.group(1).strip(), int(m.group(2)), m.group(3).strip()
        
        if "cannot find symbol" in message or "package does not exist" in message:
            error_type = "IMPORT"
        elif "class, interface, or enum expected" in message:
            error_type = "SYNTAX"
        else:
            error_type = "SYNTAX"
        
        errors.append(build_fix_dict(error_type, file, line, message, f"fix the {error_type.lower()} error"))
    
    # Pattern 2: Standard javac/Gradle errors path/File.java:line: error: message
    for m in PATTERNS['java_error'].finditer(raw):
        file, line, message = m.group(1).strip(), int(m.group(2)), m.group(3).strip()
        
        if "cannot find symbol" in message or "package does not exist" in message:
            error_type = "IMPORT"
        elif "class, interface, or enum expected" in message:
            error_type = "SYNTAX"
        else:
            error_type = "SYNTAX"
        
        errors.append(build_fix_dict(error_type, file, line, message, f"fix the {error_type.lower()} error"))
    
    return errors

def parse_rust(raw: str) -> List[Dict]:
    """Optimized Rust parser - O(n) single pass. Handles cargo errors and clippy warnings."""
    if not raw:
        return []
    
    errors = []
    
    # Pattern 1: Cargo compile errors
    for m in PATTERNS['rust_error'].finditer(raw):
        message, file, line = m.group(1).strip(), m.group(2).strip(), int(m.group(3))
        
        if "cannot find" in message or "unresolved import" in message:
            error_type = "IMPORT"
        elif "expected" in message and "found" in message:
            error_type = "TYPE_ERROR"
        else:
            error_type = "SYNTAX"
        
        errors.append(build_fix_dict(error_type, file, line, message, f"fix the {error_type.lower()} error"))
    
    # Pattern 2: Clippy warnings (treat as linting)
    for m in PATTERNS['rust_clippy'].finditer(raw):
        message, file, line = m.group(1).strip(), m.group(2).strip(), int(m.group(3))
        errors.append(build_fix_dict("LINTING", file, line, message, "fix the clippy warning"))
    
    return errors

def deduplicate(fixes: List[Dict]) -> List[Dict]:
    """Optimized deduplication using set - O(n) time, O(n) space."""
    if not fixes:
        return []
    
    seen: Set[str] = set()
    unique_fixes = []
    
    for fix in fixes:
        fix_id = fix["id"]
        if fix_id not in seen:
            seen.add(fix_id)
            unique_fixes.append(fix)
    
    return unique_fixes
