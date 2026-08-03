"""Recall matcher for the UserPromptSubmit hook (spec §5, "the short loop").

Deterministic keyword matching only — no LLM, no embeddings, fail-open,
millisecond budget. Carries its own minimal observations parser because
installed plugins ship only hooks/ (scripts/engine/observations.py is the
repo-side canonical parser; keep the field semantics in sync with
learnings/observations/README.md).
"""
import glob
import os
import re

MARKER = "[robium-recall]"
_ID_RE = re.compile(r"<!-- id: (obs-[a-z0-9-]+-\d{3}) -->")
_HEAD_RE = re.compile(r"^## (.+?)\s*<!-- id: ")
_FIELD_RE = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")
_STOP = frozenset(
    "the a an and or of to in for with on is are be this that it as at by "
    "from use when not you your how what why can could should".split())


def _tokens(text):
    return {t for t in re.findall(r"[a-z0-9_]+", (text or "").lower())
            if len(t) > 2 and t not in _STOP}


def load_observations(cwd):
    entries = []
    for base in (os.path.join(cwd, "learnings", "observations"),
                 os.path.join(cwd, ".robium", "observations")):
        for path in sorted(glob.glob(os.path.join(base, "*.md"))):
            if os.path.basename(path) == "README.md":
                continue
            try:
                current = None
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line.startswith("## "):
                            m_id = _ID_RE.search(line)
                            m_head = _HEAD_RE.match(line)
                            current = {"id": m_id.group(1) if m_id else "",
                                       "title": m_head.group(1) if m_head else "",
                                       "status": "", "proof": 0, "fields": {}}
                            if current["id"]:
                                entries.append(current)
                        elif current is not None:
                            m = _FIELD_RE.match(line)
                            if m:
                                current["fields"][m.group(1)] = m.group(2).strip()
                                if m.group(1) == "status":
                                    current["status"] = m.group(2).strip()
                                elif m.group(1) == "proof" and m.group(2).strip().isdigit():
                                    current["proof"] = int(m.group(2).strip())
            except (IOError, OSError):
                # Skip unreadable files (permissions, encoding, etc.) silently.
                pass
    return entries


def eligible(entry):
    status = entry.get("status", "")
    if status == "ready":
        return True
    return status == "tentative" and entry.get("proof", 0) >= 2


def match(prompt, entries, top_k=3):
    q = _tokens(prompt)
    if not q:
        return []
    scored = []
    for e in entries:
        skill_stem = e["id"].rsplit("-", 1)[0].replace("obs-", "", 1)
        hay = _tokens(e.get("title", "")) | _tokens(
            e.get("fields", {}).get("target", "")) | {skill_stem}
        s = len(q & hay) / (max(len(q), 1) ** 0.5 * max(len(hay), 1) ** 0.5)
        if s >= 0.15:
            scored.append((e, round(s, 3)))
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


def render(hits, budget_chars=2000):
    if not hits:
        return ""
    lines = [MARKER + " Possibly relevant prior findings (engine recall; "
             "cite the id if one helps or misleads):"]
    for e, _ in hits:
        target = e.get("fields", {}).get("target", "")[:200]
        lines.append(f"- ({e['id']}) {e['title']}: {target}")
    text = "\n".join(lines)
    if len(text) <= budget_chars:
        return text
    return text[:max(budget_chars - 1, 0)].rstrip() + "…"
