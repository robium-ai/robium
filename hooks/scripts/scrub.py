"""Secret scrubbing for capture flags (spec §12).

Two passes: (1) pattern-based for secret-shaped strings, (2) exact-value
and long-line redaction of sensitive-named environment variables
(Doppler-injected values land here without needing Doppler awareness).
stdlib only.
"""
import os
import re

_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (?P<label>(?:[A-Z0-9][A-Z0-9 -]* )?PRIVATE KEY)-----"
    r".*?(?:-----END (?P=label)-----|\Z)",
    re.DOTALL,
)

_PATTERNS = [
    # KEY=value assignments (env-style, ≥3-char upper name, ≥6-char value)
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}=(['\"]?)[^\s'\"]{6,}\1"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._\-]{12,}"),
    # well-known token prefixes
    re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
               r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}"
               r"|hf_[A-Za-z0-9]{20,}|xox[bap]-[A-Za-z0-9\-]{10,}"
               r"|dp\.st\.[A-Za-z0-9._\-]{8,})\b"),
    # --password foo / --token=foo style CLI args
    re.compile(r"(?i)(--?(password|passwd|token|api-?key|secret)[= ])[^\s]+"),
    # credentials embedded in URLs
    re.compile(r"://[^/\s:@]+:[^/\s@]+@"),
]

_MAPPING_ASSIGNMENT = re.compile(
    r"(?P<key_quote>['\"]?)(?P<key>[A-Z][A-Z0-9_]{2,})(?P=key_quote)"
    r"\s*:\s*(?P<value_quote>['\"])(?P<value>[^'\"\r\n]{6,})"
    r"(?P=value_quote)"
)

_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_HOME_PATH = re.compile(
    r"(?:/Users/[^/\s]+|/home/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)"
)

_SENSITIVE_KEYWORD = re.compile(
    r"(?i)^(key|keys|apikey|token|tokens|secret|secrets|pass|passwd|password|"
    r"passphrase|cred|creds|credential|credentials|auth|authorization|"
    r"capability|capabilities)$"
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

    # Redact private-key blocks before KEY=value processing can consume only
    # their BEGIN line and leave the key material behind. Matching through
    # end-of-text also protects truncated or unterminated captured blocks.
    text = _PRIVATE_KEY_BLOCK.sub("[REDACTED]", text)

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

    # JSON / Python-dict / YAML-style quoted assignments occur frequently in
    # tool output embedded inside transcript records. Preserve the key so the
    # evidence remains intelligible, but remove a value whose key is sensitive.
    def redact_mapping(match: re.Match) -> str:
        if not _is_sensitive_name(match.group("key")):
            return match.group(0)
        return (
            f'{match.group("key_quote")}{match.group("key")}'
            f'{match.group("key_quote")}: {match.group("value_quote")}'
            f'[REDACTED]{match.group("value_quote")}'
        )

    text = _MAPPING_ASSIGNMENT.sub(redact_mapping, text)

    # Other patterns: apply as-is
    for pat in _PATTERNS[1:]:
        text = pat.sub("[REDACTED]", text)

    # Captures are local evidence, not a place to retain personal identifiers.
    text = _EMAIL.sub("[REDACTED]", text)
    text = _HOME_PATH.sub("[HOME]", text)

    env = os.environ if env is None else env
    for variable in ("USER", "LOGNAME"):
        account = env.get(variable, "")
        if len(account) >= 4 and account.lower() not in {"root", "runner", "ubuntu"}:
            text = re.sub(
                rf"(?<![A-Za-z0-9]){re.escape(account)}(?![A-Za-z0-9])",
                "[USER]",
                text,
                flags=re.IGNORECASE,
            )
    for name, value in env.items():
        if len(value or "") >= 8 and _is_sensitive_name(name):
            text = text.replace(value, "[REDACTED]")
            # Captured output often contains only one line from a multiline
            # secret, so exact whole-value matching is insufficient. Twenty
            # characters avoids collision-prone fragments while covering PEM
            # payload rows and pretty-printed service-account fields.
            for line in set(value.splitlines()):
                fragment = line.strip()
                if len(fragment) >= 20:
                    text = text.replace(fragment, "[REDACTED]")

    return text
