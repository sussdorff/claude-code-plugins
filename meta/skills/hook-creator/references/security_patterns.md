# Security Patterns for Claude Code Hooks

## Core Principles

1. **Least Privilege** — hooks execute with full system access. Validate inputs, whitelist over blacklist.
2. **Defense in Depth** — PreToolUse validation → path validation → command sanitization → logging.
3. **Fail Secure** — block by default on errors (exit 2, never silent pass).

## Dangerous Command Patterns

### Destructive File Operations (rm)

```python
import re

patterns = [
    r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r|--recursive.*--force|--force.*--recursive)',
    r'rm\s+-[a-z]*r[a-z]*f',  # rm -rfv, etc.
]
dangerous_paths = ['/', '~', '~/', '*', '.*', '/*', '~/.*', '..', '../..', '$HOME']

def is_dangerous_rm(command):
    normalized = command.lower().strip()
    for pattern in patterns:
        if re.search(pattern, normalized):
            if any(path in command for path in dangerous_paths):
                return True
    return False
```

Blocks: `rm -rf /`, `rm -rf ~`, `rm -fr /var`, `rm --recursive --force /home`

### Permission Modifications

```python
chmod_patterns = [r'chmod\s+777', r'chmod\s+-R\s+777', r'chmod\s+666', r'chmod\s+\+x\s+/etc/']

def is_dangerous_chmod(command):
    return any(re.search(p, command.lower()) for p in chmod_patterns)
```

### Privilege Escalation

```python
sudo_patterns = [r'sudo\s+rm', r'sudo\s+chmod', r'sudo\s+chown', r'sudo\s+dd', r'sudo\s+mkfs', r'sudo\s+fdisk']
```

### Sensitive File Access

```python
sensitive_patterns = [r'\.env$', r'credentials\.json$', r'secrets\.ya?ml$', r'\.aws/credentials$', r'\.ssh/id_.*$', r'\.npmrc$', r'\.netrc$']
whitelist_patterns = [r'\.env\.(sample|example|template)$']

def is_sensitive_file(file_path):
    filename = os.path.basename(file_path)
    if any(re.search(p, filename) for p in whitelist_patterns): return False
    return any(re.search(p, file_path) for p in sensitive_patterns)
```

### System Directory Protection

```python
protected_dirs = ['/etc/', '/bin/', '/sbin/', '/boot/', '/sys/', '/proc/', '/dev/', '/usr/bin/', '/var/log/']

def is_system_path(file_path):
    return any(os.path.normpath(file_path).startswith(d) for d in protected_dirs)
```

## Path Validation

```python
def normalize_path(path):
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def is_allowed_path(file_path, allowed_dirs):
    normalized = normalize_path(file_path)
    return any(normalized.startswith(normalize_path(d)) for d in allowed_dirs)

def has_path_traversal(path):
    return any(seq in path.lower() for seq in ['../', '..\\', '%2e%2e', '..%2f'])
```

## Common Mistakes

| ❌ Bad | ✅ Better |
|--------|----------|
| `"rm -rf" in cmd` | `re.search(r'rm\s+(-[rf]{2}...)', cmd)` |
| `path == "/etc/passwd"` | `os.path.normpath(path) == "/etc/passwd"` |
| `except: pass` (silent allow) | `except: sys.exit(2)` (fail secure) |
| Blacklist only | Whitelist first, then block |

## Logging Security Events

```python
def log_security_event(event_type, data, allowed=True):
    entry = {"timestamp": datetime.utcnow().isoformat(), "event_type": event_type, "allowed": allowed, "data": data}
    with open(".claude/hooks/logs/security.json", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

## Security Checklist

Before deploying a security hook:

- [ ] Tested against known dangerous patterns
- [ ] Tested with obfuscation (spaces, case, separated flags)
- [ ] Path normalization implemented
- [ ] Whitelist defined for allowed operations
- [ ] Logging captures all security events
- [ ] Error handling fails securely (exit 2 on errors)
- [ ] Regular expressions handle flag variants
- [ ] Edge cases covered with tests
