"""Secret scrubbing for capture flags (spec §12).

Two passes: (1) pattern-based for secret-shaped strings, (2) exact-value
redaction of sensitive-named environment variables (Doppler-injected values
land here without needing Doppler awareness). stdlib only.
"""
import os
import re

_PATTERNS = [
    # KEY=value assignments (env-style, ≥3-char upper name, ≥6-char value)
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}=(['\"]?)[^\s'\"]{6,}\1"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._\-]{12,}"),
    # well-known token prefixes
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
               r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}"
               r"|xox[bap]-[A-Za-z0-9\-]{10,}|dp\.st\.[A-Za-z0-9._\-]{8,})\b"),
    # --password foo / --token=foo style CLI args
    re.compile(r"(?i)(--?(password|passwd|token|api-?key|secret)[= ])[^\s]+"),
    # credentials embedded in URLs
    re.compile(r"://[^/\s:@]+:[^/\s@]+@"),
]

_SENSITIVE_KEYWORD = re.compile(
    r"(?i)^(key|keys|apikey|token|tokens|secret|secrets|pass|passwd|password|"
    r"passphrase|cred|creds|credential|credentials|auth|authorization)$"
)


def _is_sensitive_name(name: str) -> bool:
    """Check if a name contains sensitive keywords as distinct name segments.

    Splits on '_' and matches each segment against the explicit keyword list.
    This prevents false positives like COMPASS_HEADING and KEYBOARD_LAYOUT,
    while catching all credential/auth/key inflections: API_KEY, CREDENTIALS,
    AUTHORIZATION, etc.
    """
    segments = name.split('_')
    for segment in segments:
        if _SENSITIVE_KEYWORD.match(segment):
            return True
    return False


def scrub(text: str, env: "dict | None" = None) -> str:
    if not text:
        return text

    # Pattern 1: KEY=value assignments — only redact if KEY is sensitive
    pattern_1 = _PATTERNS[0]
    matches_to_replace = []
    for match in pattern_1.finditer(text):
        full_match = match.group(0)
        # Extract the key part (everything before '=')
        key_part = full_match.split('=')[0]
        if _is_sensitive_name(key_part):
            matches_to_replace.append((match.start(), match.end()))

    # Replace matches from end to start to preserve positions
    for start, end in reversed(matches_to_replace):
        text = text[:start] + "[REDACTED]" + text[end:]

    # Other patterns: apply as-is
    for pat in _PATTERNS[1:]:
        text = pat.sub("[REDACTED]", text)

    env = os.environ if env is None else env
    for name, value in env.items():
        if len(value or "") >= 8 and _is_sensitive_name(name):
            text = text.replace(value, "[REDACTED]")

    return text
