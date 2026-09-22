#!/usr/bin/env python3
"""Small catalog metrics dashboard for refinement and staleness review.

Run from the robium repo root:

    uv run scripts/engine/skill_metrics.py [--stale-days 90] [--skills-dir skills]
    uv run scripts/engine/skill_metrics.py --history   # compare historical snapshots
    uv run scripts/engine/skill_metrics.py --dupes     # cross-skill duplicate lines

Default mode prints a per-skill table (body lines, description chars, support
size, examples, and stale facts) plus findings that can seed a refine report.
--history compares the immutable legacy snapshots with the current skill.
--dupes finds identical non-trivial lines appearing in 2+ skills — the
mechanical seed for the duplication pass. Stdlib only.
"""

import argparse
import datetime as dt
import re
import sys
from collections import defaultdict
from pathlib import Path

BODY_WARN_LINES = 90
BODY_MAX_LINES = 120
DESC_WARN_CHARS = 200
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
# Provenance claims with no date can never be aged by the staleness sweep.
UNDATED_RE = re.compile(
    r"\b(this session|as of (now|today|recently)|currently at|at the time of writing)\b",
    re.IGNORECASE)
SKIP_DIRS = {"_TEMPLATE"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    header, body = text[3:end], text[end + 4:]
    meta: dict[str, str] = {}
    key = None
    for line in header.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            meta[key] = "" if val in (">", "|", ">-", "|-") else val
        elif key and (line.startswith("  ") or line.startswith("\t")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, body


def audit_skill(skill_dir: Path, stale_before: dt.date) -> dict:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    body_lines = len(body.splitlines())

    support_bytes = sum(
        f.stat().st_size for f in skill_dir.rglob("*")
        if f.is_file() and f.name not in {"SKILL.md", "evals.yaml"}
    )
    ex_files = [f for f in (skill_dir / "examples").rglob("*") if f.is_file()] \
        if (skill_dir / "examples").is_dir() else []
    unverified = 0
    for f in ex_files:
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:2000]
        except OSError:
            continue
        if "unverified" in head:
            unverified += 1

    stale: list[tuple[str, str]] = []  # (date, context line)
    undated: list[str] = []            # un-sweepable provenance claims
    scan_files = sorted(skill_dir.rglob("*.md"))
    for f in scan_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            for d in DATE_RE.findall(line):
                try:
                    when = dt.date.fromisoformat(d)
                except ValueError:
                    continue
                if when < stale_before:
                    stale.append((d, f"{f.name}: {line.strip()[:90]}"))
            # look one line ahead for the date: provenance phrases wrap
            window = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            if UNDATED_RE.search(line) and not DATE_RE.search(window):
                undated.append(f"{f.name}: {line.strip()[:90]}")

    return {
        "name": meta.get("name", skill_dir.name),
        "desc_chars": len(meta.get("description", "")),
        "body_lines": body_lines,
        "support_kb": support_bytes // 1024,
        "examples": len(ex_files),
        "unverified": unverified,
        "stale": stale,
        "undated": undated,
    }


def semver_key(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)


def dir_stats(d: Path) -> tuple[int, int]:
    """(SKILL.md body lines, total md/py bytes) for a skill directory."""
    skill_md = d / "SKILL.md"
    body_lines = 0
    if skill_md.is_file():
        _, body = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="ignore"))
        body_lines = len(body.splitlines())
    total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    return body_lines, total


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip().lower())


def dupes_report(skills_dir: Path) -> None:
    """Identical non-trivial lines appearing in 2+ skills — duplication-pass seed."""
    seen: dict[str, set[str]] = defaultdict(set)
    sample: dict[str, str] = {}
    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir() or d.name in SKIP_DIRS:
            continue
        for f in d.rglob("*.md"):
            for raw in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                norm = normalize_line(raw)
                if len(norm) < 45 or norm.startswith(("#", "|", "-#", "```", "<!--")):
                    continue
                seen[norm].add(d.name)
                sample.setdefault(norm, raw.strip())
    dupes = sorted(((v, k) for k, v in seen.items() if len(v) > 1),
                   key=lambda t: -len(t[0]))
    if not dupes:
        print("no cross-skill duplicate lines found")
        return
    print(f"{len(dupes)} line(s) duplicated across skills (keep at the lowest owner, cross-ref the rest):")
    for owners, norm in dupes[:40]:
        print(f"  [{', '.join(sorted(owners))}] {sample[norm][:100]}")
    if len(dupes) > 40:
        print(f"  …and {len(dupes) - 40} more")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--dupes", action="store_true",
                    help="identical non-trivial lines appearing in 2+ skills")
    args = ap.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.is_dir():
        print(f"error: {skills_dir}/ not found — run from the robium repo root", file=sys.stderr)
        return 2
    if args.dupes:
        dupes_report(skills_dir)
        return 0
    stale_before = dt.date.today() - dt.timedelta(days=args.stale_days)

    rows = [audit_skill(d, stale_before)
            for d in sorted(skills_dir.iterdir())
            if d.is_dir() and d.name not in SKIP_DIRS and (d / "SKILL.md").is_file()]

    hdr = f"{'skill':<18}{'desc':>5}{'body':>6}{'supportKB':>11}{'ex':>4}{'unver':>7}{'stale':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['name']:<18}{r['desc_chars']:>5}{r['body_lines']:>6}"
              f"{r['support_kb']:>11}{r['examples']:>4}{r['unverified']:>7}{len(r['stale']):>7}")

    warnings: list[str] = []
    for r in rows:
        if r["body_lines"] >= BODY_MAX_LINES:
            warnings.append(f"[{r['name']}] body {r['body_lines']} lines — over the {BODY_MAX_LINES}-line limit")
        elif r["body_lines"] >= BODY_WARN_LINES:
            warnings.append(f"[{r['name']}] body {r['body_lines']} lines — move conditional depth to support files")
        if r["desc_chars"] > DESC_WARN_CHARS:
            warnings.append(f"[{r['name']}] description {r['desc_chars']} chars — tighten the discovery signal")
        if r["unverified"]:
            warnings.append(f"[{r['name']}] {r['unverified']}/{r['examples']} examples unverified — candidates for ✓-promotion or pruning")
        for d, ctx in r["stale"][:5]:
            warnings.append(f"[{r['name']}] dated fact {d} (> {args.stale_days}d) — re-verify: {ctx}")
        if len(r["stale"]) > 5:
            warnings.append(f"[{r['name']}] …and {len(r['stale']) - 5} more stale dated facts")
        for ctx in r["undated"][:3]:
            warnings.append(f"[{r['name']}] un-sweepable provenance claim (no date) — add one: {ctx}")
        if len(r["undated"]) > 3:
            warnings.append(f"[{r['name']}] …and {len(r['undated']) - 3} more undated provenance claims")

    print(f"\n{len(warnings)} warning(s):" if warnings else "\nno warnings — catalog within bars")
    for w in warnings:
        print(f"  - {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
