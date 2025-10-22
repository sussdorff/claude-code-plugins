# Security Patterns and Best Practices for Claude Code Hooks

This document outlines security patterns, dangerous command detection, and best practices for implementing secure Claude Code hooks.

## Core Security Principles

### 1. Principle of Least Privilege
Hooks execute with your environment's credentials and full system access. Apply the principle of least privilege:

- Only grant access to necessary files and directories
- Use whitelisting over blacklisting when possible
- Validate all inputs before processing
- Run hooks with minimal required permissions

### 2. Defense in Depth
Implement multiple layers of security:

- PreToolUse validation (first line of defense)
- Path validation (second layer)
- Command sanitization (third layer)
- Logging and monitoring (detection layer)

### 3. Fail Secure
When validation fails or errors occur:

- Block by default (exit code 2)
- Provide clear error messages to Claude
- Log security violations
- Never silently allow dangerous operations

## Dangerous Command Patterns

### Category 1: Destructive File Operations

**Pattern: Recursive Force Deletion**
```python
# Dangerous patterns to block
patterns = [
    r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r|--recursive.*--force|--force.*--recursive)',
    r'rm\s+-[a-z]*r[a-z]*f',  # Matches rm -rf, rm -rfv, etc.
    r'rm\s+-[a-z]*f[a-z]*r',  # Matches rm -fr, rm -frv, etc.
]

# Dangerous paths
dangerous_paths = [
    '/',           # Root directory
    '~',           # Home directory
    '~/',          # Home directory variant
    '*',           # All files wildcard
    '.*',          # Hidden files
    '/*',          # All root files
    '~/.*',        # All home files
    '..',          # Parent directory
    '../..',       # Grandparent directory
    '$HOME',       # Home env variable
]

# Example validation
def is_dangerous_rm(command):
    normalized = command.lower().strip()

    # Check for rm with recursive and force flags
    for pattern in patterns:
        if re.search(pattern, normalized):
            # Check if targeting dangerous paths
            for path in dangerous_paths:
                if path in command:
                    return True
    return False
```

**Block examples**:
- `rm -rf /`
- `rm -rf ~`
- `rm -rf *`
- `rm -fr /var`
- `rm --recursive --force /home`

### Category 2: Permission Modifications

**Pattern: Overly Permissive chmod**
```python
# Dangerous chmod patterns
chmod_patterns = [
    r'chmod\s+777',           # World-writable
    r'chmod\s+-R\s+777',      # Recursive world-writable
    r'chmod\s+666',           # World-writable files
    r'chmod\s+\+x\s+/etc/',   # Making system configs executable
]

def is_dangerous_chmod(command):
    normalized = command.lower().strip()
    return any(re.search(pattern, normalized) for pattern in chmod_patterns)
```

**Block examples**:
- `chmod 777 file.sh`
- `chmod -R 777 /var/www`
- `chmod +x /etc/passwd`

### Category 3: Privilege Escalation

**Pattern: Sudo with Dangerous Operations**
```python
# Dangerous sudo patterns
sudo_patterns = [
    r'sudo\s+rm',             # Sudo deletion
    r'sudo\s+chmod',          # Sudo permission change
    r'sudo\s+chown',          # Sudo ownership change
    r'sudo\s+dd',             # Sudo disk operations
    r'sudo\s+mkfs',           # Sudo filesystem creation
    r'sudo\s+fdisk',          # Sudo disk partitioning
]

def is_dangerous_sudo(command):
    normalized = command.lower().strip()
    return any(re.search(pattern, normalized) for pattern in sudo_patterns)
```

**Block examples**:
- `sudo rm -rf /var`
- `sudo chmod 777 /etc`
- `sudo dd if=/dev/zero of=/dev/sda`

### Category 4: System Directory Modifications

**Pattern: Writing to System Directories**
```python
# Protected system directories
protected_dirs = [
    '/etc/',
    '/bin/',
    '/sbin/',
    '/boot/',
    '/sys/',
    '/proc/',
    '/dev/',
    '/usr/bin/',
    '/usr/sbin/',
    '/var/log/',
    '/lib/',
    '/lib64/',
]

def is_system_path(file_path):
    """Check if path is in protected system directory"""
    normalized = os.path.normpath(file_path)
    return any(normalized.startswith(dir) for dir in protected_dirs)
```

### Category 5: Sensitive File Access

**Pattern: Credential and Secret Files**
```python
# Sensitive file patterns
sensitive_patterns = [
    r'\.env$',                    # Environment files
    r'\.env\..*$',                # Environment variants (but allow .env.sample)
    r'credentials\.json$',         # Credential files
    r'secrets\.ya?ml$',           # Secret configs
    r'\.aws/credentials$',        # AWS credentials
    r'\.ssh/id_.*$',              # SSH private keys
    r'\.npmrc$',                  # NPM auth
    r'\.pypirc$',                 # PyPI auth
    r'\.netrc$',                  # Generic auth
]

# Whitelist exceptions
whitelist_patterns = [
    r'\.env\.sample$',
    r'\.env\.example$',
    r'\.env\.template$',
]

def is_sensitive_file(file_path):
    """Check if file contains sensitive data"""
    filename = os.path.basename(file_path)

    # Check whitelist first
    if any(re.search(pattern, filename) for pattern in whitelist_patterns):
        return False

    # Check sensitive patterns
    return any(re.search(pattern, filename) for pattern in sensitive_patterns)
```

**Block examples**:
- `.env`
- `credentials.json`
- `secrets.yaml`
- `~/.aws/credentials`
- `~/.ssh/id_rsa`

**Allow examples**:
- `.env.sample`
- `.env.example`
- `.env.template`

## Security Hook Implementation Template

### PreToolUse Security Hook

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import json
import re
import sys
import os

def is_dangerous_rm(command):
    """Detect dangerous rm commands"""
    normalized = command.lower().strip()

    rm_patterns = [
        r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r)',
        r'rm\s+--recursive.*--force',
        r'rm\s+--force.*--recursive',
    ]

    dangerous_paths = ['/', '~', '~/', '*', '.*', '/*', '..']

    for pattern in rm_patterns:
        if re.search(pattern, normalized):
            for path in dangerous_paths:
                if path in command:
                    return True
    return False

def is_sensitive_file(file_path):
    """Check if file is sensitive"""
    if not file_path:
        return False

    filename = os.path.basename(file_path)

    # Allow sample files
    if re.search(r'\.env\.(sample|example|template)$', filename):
        return False

    # Block actual sensitive files
    sensitive = [
        r'\.env$',
        r'credentials\.json$',
        r'secrets\.ya?ml$',
    ]

    return any(re.search(pattern, filename) for pattern in sensitive)

def validate_tool_use(data):
    """Validate tool usage for security issues"""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Validate Bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if is_dangerous_rm(command):
            return False, f"Blocked dangerous rm command: {command}"

    # Validate file operations
    if tool_name in ["Read", "Edit", "Write"]:
        file_path = tool_input.get("file_path", "")
        if is_sensitive_file(file_path):
            return False, f"Blocked access to sensitive file: {file_path}"

    return True, None

def main():
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        # Log the attempt (append to log file)
        with open(".claude/hooks/logs/pre_tool_use.json", "a") as log:
            log.write(json.dumps(input_data) + "\n")

        # Validate
        is_valid, error_msg = validate_tool_use(input_data)

        if not is_valid:
            # Block the operation
            print(error_msg, file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks and feeds stderr to Claude

        # Allow the operation
        sys.exit(0)

    except Exception as e:
        # On error, log but don't block
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## Path Validation Best Practices

### 1. Normalize Paths
```python
import os

def normalize_path(path):
    """Normalize path for consistent validation"""
    # Expand user directory
    expanded = os.path.expanduser(path)
    # Get absolute path
    absolute = os.path.abspath(expanded)
    # Normalize (remove .., etc.)
    normalized = os.path.normpath(absolute)
    return normalized
```

### 2. Validate Against Whitelist
```python
def is_allowed_path(file_path, allowed_dirs):
    """Check if path is within allowed directories"""
    normalized = normalize_path(file_path)
    return any(normalized.startswith(normalize_path(dir)) for dir in allowed_dirs)

# Example usage
allowed_dirs = [
    os.getcwd(),  # Current project directory
    "/tmp",       # Temp directory
]

if not is_allowed_path(user_file, allowed_dirs):
    print("Access denied: Path outside allowed directories", file=sys.stderr)
    sys.exit(2)
```

### 3. Prevent Path Traversal
```python
def has_path_traversal(path):
    """Check for path traversal attempts"""
    dangerous_sequences = ['../', '..\\', '%2e%2e', '..%2f', '..%5c']
    normalized = path.lower()
    return any(seq in normalized for seq in dangerous_sequences)
```

## Command Sanitization

### 1. Strip Dangerous Characters
```python
def sanitize_command(command):
    """Remove dangerous shell characters"""
    # Characters that enable command injection
    dangerous_chars = [';', '|', '&', '$', '`', '\n', '\r']

    sanitized = command
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    return sanitized
```

### 2. Validate Against Allowed Commands
```python
def is_allowed_command(command, whitelist):
    """Check if command is in whitelist"""
    cmd_name = command.strip().split()[0]
    return cmd_name in whitelist

# Example usage
allowed_commands = ['git', 'npm', 'python', 'node']
if not is_allowed_command(user_command, allowed_commands):
    print(f"Command not allowed: {user_command}", file=sys.stderr)
    sys.exit(2)
```

## Logging and Monitoring

### 1. Comprehensive Logging
```python
import json
from datetime import datetime

def log_security_event(event_type, data, allowed=True):
    """Log security-relevant events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "allowed": allowed,
        "data": data
    }

    log_file = ".claude/hooks/logs/security.json"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

### 2. Alert on Security Violations
```python
def alert_security_violation(violation_type, details):
    """Send alert for security violations"""
    # Could integrate with:
    # - Email notifications
    # - Slack webhooks
    # - Security monitoring systems

    message = f"SECURITY ALERT: {violation_type}\nDetails: {details}"

    # Example: Desktop notification
    os.system(f'notify-send "Security Alert" "{message}"')

    # Example: Log to syslog
    # syslog.syslog(syslog.LOG_WARNING, message)
```

## Testing Security Hooks

### 1. Test Dangerous Patterns
```python
# test_security.py
def test_dangerous_rm():
    assert is_dangerous_rm("rm -rf /") == True
    assert is_dangerous_rm("rm -rf ~") == True
    assert is_dangerous_rm("rm file.txt") == False
    assert is_dangerous_rm("rm -r temp/") == False  # Not force
```

### 2. Test Edge Cases
```python
def test_obfuscation():
    # Test various obfuscation attempts
    assert is_dangerous_rm("rm  -rf  /") == True  # Extra spaces
    assert is_dangerous_rm("RM -RF /") == True    # Uppercase
    assert is_dangerous_rm("rm -r -f /") == True  # Separated flags
```

## Common Security Mistakes to Avoid

### ❌ Mistake 1: Blacklist-Only Approach
```python
# BAD: Easy to bypass
def is_dangerous(cmd):
    return "rm -rf" in cmd  # Misses "rm -fr", "rm -r -f", etc.
```

### ✅ Better: Pattern Matching
```python
# GOOD: Catches variations
def is_dangerous(cmd):
    pattern = r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r)'
    return re.search(pattern, cmd.lower()) is not None
```

### ❌ Mistake 2: Insufficient Path Validation
```python
# BAD: Can be bypassed with relative paths
def is_protected(path):
    return path == "/etc/passwd"
```

### ✅ Better: Normalized Path Checking
```python
# GOOD: Normalizes before comparing
def is_protected(path):
    normalized = os.path.normpath(os.path.abspath(path))
    return normalized == "/etc/passwd"
```

### ❌ Mistake 3: Silent Failures
```python
# BAD: Allows dangerous operation silently
try:
    validate(command)
except:
    pass  # Silently allows
```

### ✅ Better: Fail Secure
```python
# GOOD: Blocks on error
try:
    validate(command)
except Exception as e:
    print(f"Validation error: {e}", file=sys.stderr)
    sys.exit(2)  # Block operation
```

## Security Checklist

Before deploying a security hook:

- [ ] Tested against known dangerous patterns
- [ ] Tested with obfuscation attempts (spaces, case, etc.)
- [ ] Path normalization implemented
- [ ] Whitelist for allowed operations defined
- [ ] Logging captures all security events
- [ ] Error handling fails securely (blocks by default)
- [ ] Regular expressions anchored properly
- [ ] Edge cases covered with tests
- [ ] Documentation includes security rationale
- [ ] Code reviewed by another developer

## Additional Resources

- OWASP Command Injection Prevention Cheat Sheet
- CWE-78: OS Command Injection
- NIST Guidelines on Secure Configuration
