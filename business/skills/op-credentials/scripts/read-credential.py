#!/usr/bin/env python3
"""
Helper function for reading a credential from 1Password in Python code.
Copy this function into your Python project as needed.
"""
import subprocess


def read_op_credential(service: str, field: str) -> str | None:
    try:
        result = subprocess.run(
            ["op", "read", f"op://API Keys/{service}/{field}"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
