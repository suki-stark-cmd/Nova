"""Security guardrails for Nova AI.

Reverse-engineered from OpenJarvis `security/` module.
Provides:
- Command blocklist (from shell_exec.py)
- Sensitive file detection (from file_policy.py)
- Injection detection (from injection_scanner.py)
- Input sanitization
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import List, Optional


# ── Dangerous Command Detection ──────────────────────────────

BLOCKED_COMMANDS = [
    "rm -rf /",
    "rm -rf ~",
    "del /s /q c:",
    "format c:",
    "mkfs",
    "dd if=/dev/zero",
    ":(){:|:&};:",       # Fork bomb
    "> /dev/sda",
    "chmod -R 777 /",
    "shutdown",
    "reboot",
    "halt",
    "init 0",
    "init 6",
]


def is_dangerous_command(command: str) -> bool:
    """Check if a command matches any blocked patterns."""
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return True
    # Check for pipe to shell with curl/wget
    if re.search(r"(curl|wget)\s+.*\|\s*(bash|sh|zsh)", cmd_lower):
        return True
    return False


# ── Sensitive File Detection ─────────────────────────────────

SENSITIVE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"id_rsa$",
    r"id_ed25519$",
    r"\.pem$",
    r"\.key$",
    r"\.p12$",
    r"\.pfx$",
    r"authorized_keys$",
    r"known_hosts$",
    r"\.ssh/config$",
    r"\.gnupg/",
    r"\.aws/credentials$",
    r"\.gcloud/",
    r"credentials\.json$",
    r"token\.json$",
    r"secrets?\.(ya?ml|json|toml)$",
    r"\.git/config$",
    r"\.npmrc$",
    r"\.pypirc$",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]


def is_sensitive_file(path: Path) -> bool:
    """Check if a file path matches any sensitive file patterns."""
    path_str = str(path)
    return any(p.search(path_str) for p in _COMPILED_PATTERNS)


# ── Prompt Injection Detection ───────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)",
    r"forget\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)",
    r"you\s+are\s+now\s+(a|an|in)\s+",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*",
    r"<\s*/?system\s*>",
    r"\[system\]",
    r"override\s+instructions?",
    r"jailbreak",
    r"DAN\s+mode",
]

_INJECTION_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_injection(text: str) -> Optional[str]:
    """Check text for prompt injection attempts.

    Returns the matched pattern description or None if clean.
    """
    for pattern in _INJECTION_COMPILED:
        match = pattern.search(text)
        if match:
            return f"Potential prompt injection detected: '{match.group()}'"
    return None


# ── Input Sanitization ───────────────────────────────────────

def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Clean and limit user input."""
    # Strip control characters except newline/tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "...[truncated]"
    return text.strip()


__all__ = [
    "BLOCKED_COMMANDS",
    "detect_injection",
    "is_dangerous_command",
    "is_sensitive_file",
    "sanitize_input",
]
