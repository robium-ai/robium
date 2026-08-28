#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Apply anchor-targeted delta ops to skills (spec §7.2).

Deterministic: archive snapshot → apply ops (no-op fallback) → bump version
→ changelog line → sidecar updates. An unappliable op degrades to a no-op +
report line, never a corrupted file. Refusals (anchor-mismatch content,
existing archive dir, cap breach, protected retire) block without writing.

Ops: update/add/annotate (anchor-targeted body edits, Task 2) plus, added
here:
  - retire: drops an anchor block and its evidence.yaml key. Refused when
    the ledger shows helpful > 0 unless force: true (spec §4.1/§7.2 — a
    block with proven value cannot be silently deleted).
  - move: relocates an anchor block (and its ledger entry) from one skill
    to another. Composition rule: a move is processed inside its SOURCE
    skill's batch (grouped by the `skill` field like any other op). Moves
    sharing a `to_skill` within the same batch are merged into a single
    per-destination buffer (`dest_buffers`, keyed by to_skill) that
    accumulates every moved-in anchor; there is exactly ONE archive-slot
    check, ONE copytree, ONE write, and ONE version bump/changelog line
    per destination no matter how many anchors land there — two
    `shutil.copytree` calls to the same not-yet-existing archive dir would
    otherwise crash the second one and silently drop its content. Nothing
    is committed to disk until the source batch's usual checks (C1
    refusal-blocks-batch, C2 body cap, major-bump guard) all pass — only
    then are the source and every merged destination snapshotted and
    written, and only then do ledger entries move. If a destination
    skill/section is missing, that move degrades to a no-op; if a
    destination's archive slot is already taken (or its merged resulting
    body would breach the cap), the whole move set to that destination —
    and therefore the entire source batch — is refused, nothing written
    anywhere.
  - annotate with file/find/replace (no anchor): a plain find/replace in
    a file elsewhere in the skill directory (e.g. promoting an example's
    `status: unverified` marker). Path is resolved with os.path.realpath
    and must stay inside the skill directory. An annotation counts as a
    build-level change only when it explicitly sets `status_only: true`;
    annotations that add or change user-facing guidance count as minor.

Also here: the co-evolving-evals rule (a `major` bump — reachable only via
an explicit `bump:` override — is refused unless the skill is listed in
`evals_confirmed`), and `mark_absorbed`, which flips `status:` to
`absorbed <date>` in learnings/observations/<stem>.md for every reason id
(`obs-<stem>-NNN`) attached to an op that actually applied.
"""
import argparse
import datetime
import os
import re
import shutil
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ledger

_ANCHOR = "<!-- id: {} -->"
_ANCHOR_ID_RE = re.compile(r"<!-- id: ([a-z0-9][a-z0-9-]*) -->")
_VER_RE = re.compile(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$")
_OBS_ID_RE = re.compile(r"^obs-(.+)-\d{3}$")
BODY_CAP = 500
_BUMP_RANK = {"build": 0, "minor": 1, "major": 2}


def find_anchor_block(lines, anchor):
    marker = _ANCHOR.format(anchor)
    for i, line in enumerate(lines):
        if marker in line:
            stripped = line.lstrip()
            # Check for list items: unordered (- *) or ordered (1. 2. etc.)
            if re.match(r"([-*]|\d+\.)\s", stripped):
                indent = len(line) - len(line.lstrip())
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        break
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent <= indent:
                        break
                    j += 1
                return (i, j)
            # table-row anchor: marker lands inside a `| cell | cell |` row
            # (e.g. skills/live-demo/SKILL.md:122-124). Always a single line —
            # never scan into sibling rows.
            if stripped.startswith("|"):
                return (i, i + 1)
            # wrapped-bullet continuation anchor: the marker sits on an
            # INDENTED continuation line of a bullet whose bold lead-in
            # wrapped (e.g. skills/nav2/SKILL.md:250-252 "behavior.** <!--
            # id: ... --> ..."). Scan UP through contiguous non-blank lines
            # for the enclosing list-item line (smaller indent) and resolve
            # the block as THAT bullet's block via the same indent-scan used
            # above. No enclosing bullet found before a blank line/heading →
            # fall back to a conservative single-line block.
            indent = len(line) - len(stripped)
            if indent > 0:
                k = i - 1
                bullet_line = None
                while k >= 0:
                    cur = lines[k]
                    if not cur.strip() or cur.startswith("#"):
                        break
                    cur_stripped = cur.lstrip()
                    cur_indent = len(cur) - len(cur_stripped)
                    if cur_indent < indent and re.match(r"([-*]|\d+\.)\s", cur_stripped):
                        bullet_line = k
                        break
                    k -= 1
                if bullet_line is None:
                    return (i, i + 1)
                bullet_indent = len(lines[bullet_line]) - len(lines[bullet_line].lstrip())
                j = bullet_line + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        break
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent <= bullet_indent:
                        break
                    j += 1
                return (bullet_line, j)
            # paragraph anchor (bold-paragraph or plain-prose item, indent 0):
            # block runs to the first blank line or heading (exclusive),
            # with fence awareness (don't break on # or blank lines inside fences)
            j = i + 1
            in_fence = False
            while j < len(lines):
                nxt = lines[j]
                nxt_stripped = nxt.lstrip()
                # Toggle fence state on lines starting with ```
                if nxt_stripped.startswith("```"):
                    in_fence = not in_fence
                    j += 1
                    continue
                # Only apply blank-line and heading stops outside of fences
                if not in_fence:
                    if not nxt.strip() or nxt.startswith("#"):
                        break
                j += 1
            return (i, j)
    return None


def _find_section(lines, section):
    heading = f"## {section}"
    for i, line in enumerate(lines):
        if line.strip() == heading:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            return (i, j)
    return None


def _version(lines):
    for i, line in enumerate(lines):
        m = _VER_RE.match(line)
        if m:
            return ".".join(m.groups()), i
    raise ValueError("no version: line in frontmatter")


def bump_version(ver, kind):
    major, minor, build = (int(x) for x in ver.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{build + 1}"


def _infer_bump_kind(ops):
    """Return the highest bump required by the applied operations.

    Status-only annotations are verification markers or evidence metadata
    that do not change instructions. Every other operation, including an
    unclassified annotation, changes or may change user-facing guidance and
    therefore requires a minor bump. Defaulting ambiguity upward prevents a
    substantive edit from being mislabeled as a build-only correction.
    """
    return "build" if all(
        op.get("op") == "annotate" and op.get("status_only") is True
        for op in ops
    ) else "minor"


def _select_bump_kind(ops, override=None):
    """Select the higher of the inferred requirement and an override."""
    inferred = _infer_bump_kind(ops)
    if override is None:
        return inferred
    return max((inferred, override), key=_BUMP_RANK.__getitem__)


def _body_line_count(lines):
    seen = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            seen += 1
            if seen == 2:
                return len(lines) - i - 1
    return len(lines)


def _content_lines(content):
    lines = content.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _block_kind(line):
    stripped = line.lstrip()
    if re.match(r"([-*]|\d+\.)\s", stripped):
        return "list"
    if stripped.startswith("|"):
        return "table"
    return "paragraph"


def _needs_blank(left, right):
    if not left or not right:
        return False
    return not (_block_kind(left) == _block_kind(right) == "list"
               or _block_kind(left) == _block_kind(right) == "table")


def _splice_block(lines, start, end, block_lines):
    """Replace a Markdown block while canonicalizing only its boundaries."""
    block = list(block_lines)
    while block and not block[0].strip():
        block.pop(0)
    while block and not block[-1].strip():
        block.pop()

    prefix = lines[:start]
    suffix = lines[end:]
    while prefix and not prefix[-1].strip():
        prefix.pop()
    while suffix and not suffix[0].strip():
        suffix.pop(0)

    out = prefix
    if block:
        if _needs_blank(out[-1] if out else "", block[0]):
            out.append("")
        out.extend(block)
    if suffix:
        left = out[-1] if out else ""
        if _needs_blank(left, suffix[0]):
            out.append("")
        out.extend(suffix)
    return out


def _inside_frontmatter(lines, index):
    delimiters = [i for i, line in enumerate(lines) if line.strip() == "---"]
    return len(delimiters) >= 2 and delimiters[0] < index < delimiters[1]


def _insert_at_section_bottom(lines, sec, block_lines):
    s, e = sec
    insert_at = e
    while insert_at > s + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    return _splice_block(lines, insert_at, insert_at, block_lines)


def _apply_one(lines, op, report):
    """Return new lines or None (no change). Appends to report."""
    kind = op["op"]
    if kind in ("update", "annotate") and "anchor" in op:
        loc = find_anchor_block(lines, op["anchor"])
        if loc is None:
            report["noop"].append(_item(op, "anchor not found"))
            return None
        if _ANCHOR.format(op["anchor"]) not in op.get("content", ""):
            report["refused"].append(_item(op, "content drops the anchor id"))
            return None
        start, end = loc
        if _inside_frontmatter(lines, start):
            return lines[:start] + _content_lines(op["content"]) + lines[end:]
        return _splice_block(lines, start, end, _content_lines(op["content"]))
    if kind == "update" or kind == "annotate":
        report["refused"].append(_item(op, f"op {kind} missing required field 'anchor'"))
        return None
    if kind == "add":
        sec = _find_section(lines, op.get("section", ""))
        if sec is None:
            report["noop"].append(_item(op, "section not found"))
            return None
        s, e = sec
        insert_at = s + 1 if op.get("position") == "top" else e
        while insert_at > s + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        return _splice_block(lines, insert_at, insert_at, _content_lines(op["content"]))
    report["refused"].append(_item(op, f"unknown op {kind!r} (core)"))
    return None


def _apply_retire(working, op, skill_dir):
    """Return ("noop"|"refused"|"applied", note, new_lines_or_None)."""
    anchor = op.get("anchor")
    if not anchor:
        return ("refused", "op retire missing required field 'anchor'", None)
    loc = find_anchor_block(working, anchor)
    if loc is None:
        return ("noop", "anchor not found", None)
    entry = ledger.load(skill_dir).get(anchor, {})
    if int(entry.get("helpful", 0)) > 0 and not op.get("force"):
        return ("refused", "anchor has helpful>0 — retire needs force: true", None)
    start, end = loc
    return ("applied", "applied", _splice_block(working, start, end, []))


def _apply_annotate_file(skill_dir, op):
    """Return ("noop"|"refused"|"applied", note, path_or_None, content_or_None)."""
    rel = op.get("file", "")
    skill_real = os.path.realpath(skill_dir)
    target_real = os.path.realpath(os.path.join(skill_dir, rel))
    if not (target_real == skill_real or target_real.startswith(skill_real + os.sep)):
        return ("refused", "file escapes skill dir", None, None)
    if not os.path.exists(target_real):
        return ("noop", "file not found", None, None)
    content = open(target_real, encoding="utf-8").read()
    find = op.get("find", "")
    if find not in content:
        return ("noop", "find text not present", None, None)
    new_content = content.replace(find, op.get("replace", ""), 1)
    return ("applied", "applied", target_real, new_content)


def _apply_annotate_working(lines, op):
    """annotate+file targeting the skill's OWN SKILL.md: same find/replace
    semantics as _apply_annotate_file, but applied to the in-memory
    `working` lines instead of a fresh disk read.

    Bug this works around: the batch's only unconditional disk write for
    `md` happens twice — once from `working` (which carries the version
    bump/changelog), then unconditionally again from `file_effects` for
    any file-targeted annotate. When the annotated file IS the skill's own
    SKILL.md, both writes target the same path and the second (a stale
    pre-batch disk read + a single substitution, computed before any bump
    happened) always wins, silently discarding the version bump, the
    changelog line, and any other op's `working`-based edit from the same
    batch. Routing the SKILL.md-target case through `working` instead
    keeps it in the one write path that composes correctly with bump/
    changelog and with sibling ops. Auxiliary-file targets (examples/*,
    references/*) are unaffected and keep using _apply_annotate_file.
    Return ("noop"|"applied", note, new_lines_or_None).
    """
    text = "\n".join(lines)
    find = op.get("find", "")
    if find not in text:
        return ("noop", "find text not present", None)
    new_text = text.replace(find, op.get("replace", ""), 1)
    return ("applied", "applied", new_text.split("\n"))


def _item(op, note):
    return {"skill": op.get("skill", "?"), "op": op.get("op", "?"),
            "anchor": op.get("anchor", op.get("section", op.get("file", "-"))),
            "note": note}


def mark_absorbed(reasons, observations_dir, date):
    notes = []
    for rid in sorted(set(reasons)):
        m = _OBS_ID_RE.match(rid or "")
        if not m:
            continue
        path = os.path.join(observations_dir, f"{m.group(1)}.md")
        if not os.path.exists(path):
            notes.append(f"{rid}: observations file not found")
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        hit = None
        for i, line in enumerate(lines):
            if f"<!-- id: {rid} -->" in line:
                hit = i
                break
        if hit is None:
            notes.append(f"{rid}: entry not found")
            continue
        for j in range(hit + 1, min(hit + 12, len(lines))):
            if lines[j].startswith("status:"):
                lines[j] = f"status: absorbed {date}"
                break
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return notes


def apply_file(deltas_path, skills_dir="skills", archive_dir="archive",
               dry_run=False, date=None, observations_dir=None):
    with open(deltas_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    date = date or spec.get("date") or datetime.date.today().isoformat()
    overrides = spec.get("bump") or {}
    evals_confirmed = spec.get("evals_confirmed") or []
    observations_dir = observations_dir or os.path.join(
        os.path.dirname(os.path.abspath(skills_dir)), "learnings", "observations")
    report = {"applied": [], "noop": [], "refused": [], "skills_bumped": {}, "notes": []}

    # Branch guard: refuse to apply on main/master (merge is the gate)
    if not dry_run:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "-C", os.path.dirname(os.path.abspath(skills_dir)),
                 "branch", "--show-current"],
                capture_output=True, text=True, timeout=5
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else ""
            if current_branch in ("main", "master"):
                report["refused"].append({
                    "skill": "apply_deltas",
                    "op": "guard",
                    "anchor": "-",
                    "note": f"refusing to apply on branch '{current_branch}' — absorb runs on loop/* branches (merge is the gate)"
                })
                return report
        except Exception:
            pass  # Fail-open: if git command fails, proceed
    applied_reasons = []

    by_skill = {}
    for op in spec.get("deltas", []):
        by_skill.setdefault(op["skill"], []).append(op)

    for skill, ops in by_skill.items():
        skill_dir = os.path.join(skills_dir, skill)
        md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(md):
            for op in ops:
                report["refused"].append(_item(op, "skill not found"))
            continue
        lines = open(md, encoding="utf-8").read().splitlines()
        old_ver, _ = _version(lines)
        snap = os.path.join(archive_dir, skill, old_ver)
        if os.path.exists(snap):
            for op in ops:
                report["refused"].append(_item(op, f"archive {snap} exists — bump upstream first"))
            continue

        working, applied_here = lines, []
        log_ops = []  # parallel to applied_here; changelog-safe op descriptions
        pending = {"applied": [], "noop": [], "refused": []}
        retire_anchors = []
        dest_buffers = {}  # to_skill -> merged destination buffer for this batch
        file_effects = []

        for op in ops:
            kind = op["op"]

            if kind == "retire":
                status, note, new_lines = _apply_retire(working, op, skill_dir)
                if status == "noop":
                    pending["noop"].append(_item(op, note))
                elif status == "refused":
                    pending["refused"].append(_item(op, note))
                else:
                    working = new_lines
                    applied_here.append(op)
                    pending["applied"].append(_item(op, "applied"))
                    retire_anchors.append(op["anchor"])
                    log_ops.append(op)
                continue

            if kind == "move":
                anchor = op.get("anchor")
                to_skill = op.get("to_skill")
                to_section = op.get("to_section")
                if not (anchor and to_skill and to_section):
                    pending["noop"].append(
                        _item(op, "move op missing to_skill/to_section/anchor"))
                    continue
                loc = find_anchor_block(working, anchor)
                if loc is None:
                    pending["noop"].append(_item(op, "anchor not found"))
                    continue
                buf = dest_buffers.get(to_skill)
                if buf is None:
                    dest_dir = os.path.join(skills_dir, to_skill)
                    dest_md = os.path.join(dest_dir, "SKILL.md")
                    if not os.path.exists(dest_md):
                        pending["noop"].append(_item(op, "to_skill not found"))
                        continue
                    dest_lines = open(dest_md, encoding="utf-8").read().splitlines()
                    dest_old_ver, _ = _version(dest_lines)
                    dest_snap = os.path.join(archive_dir, to_skill, dest_old_ver)
                    if os.path.exists(dest_snap):
                        pending["refused"].append(
                            _item(op, f"archive {dest_snap} exists — bump upstream first"))
                        continue
                    buf = {"dir": dest_dir, "md": dest_md, "old_ver": dest_old_ver,
                           "snap": dest_snap, "working": dest_lines, "moves": []}
                    # Not registered in dest_buffers yet: only a move that
                    # actually stages content (passes the to_section check
                    # below) may create a commit-time destination write. A
                    # bad-section move must leave the destination completely
                    # untouched, even if a sibling op elsewhere in this same
                    # batch applies (would otherwise phantom-bump a skill
                    # that received nothing).
                sec = _find_section(buf["working"], to_section)
                if sec is None:
                    pending["noop"].append(_item(op, "to_section not found"))
                    continue
                start, end = loc
                block = working[start:end]
                working = _splice_block(working, start, end, [])
                buf["working"] = _insert_at_section_bottom(buf["working"], sec, block)
                buf["moves"].append({"anchor": anchor, "reason": op.get("reason")})
                dest_buffers[to_skill] = buf
                applied_here.append(op)
                pending["applied"].append(_item(op, "applied"))
                log_ops.append({"op": "move-out", "anchor": f"{anchor} to {to_skill}",
                                "reason": op.get("reason")})
                continue

            if kind == "annotate" and "file" in op:
                target_real = os.path.realpath(os.path.join(skill_dir, op.get("file", "")))
                if target_real == os.path.realpath(md):
                    # Same-file case: route through `working` (see
                    # _apply_annotate_working docstring) instead of the
                    # disk-read/file_effects path, so this composes
                    # correctly with the version bump/changelog and any
                    # sibling op in the same batch.
                    status, note, new_lines = _apply_annotate_working(working, op)
                    if status == "noop":
                        pending["noop"].append(_item(op, note))
                    else:
                        working = new_lines
                        applied_here.append(op)
                        pending["applied"].append(_item(op, "applied"))
                        log_ops.append(op)
                    continue
                status, note, path, content = _apply_annotate_file(skill_dir, op)
                if status == "noop":
                    pending["noop"].append(_item(op, note))
                elif status == "refused":
                    pending["refused"].append(_item(op, note))
                else:
                    applied_here.append(op)
                    pending["applied"].append(_item(op, "applied"))
                    file_effects.append({"path": path, "content": content})
                    log_ops.append(op)
                continue

            new = _apply_one(working, op, pending)
            if new is not None:
                working = new
                applied_here.append(op)
                pending["applied"].append(_item(op, "applied"))
                log_ops.append(op)

        # C1: If any op is refused, block the entire batch (no-ops never block)
        if pending["refused"]:
            for item in pending["applied"]:
                report["refused"].append({**item, "note": "blocked: batch contains a refused op"})
            report["refused"].extend(pending["refused"])
            report["noop"].extend(pending["noop"])
            continue

        if not applied_here:
            for k in ("applied", "noop", "refused"):
                report[k].extend(pending[k])
            continue

        bump_kind = _select_bump_kind(applied_here, overrides.get(skill))

        # Co-evolving-evals rule: a major bump requires the skill to be
        # listed in evals_confirmed, checked after bump-kind resolution.
        if bump_kind == "major" and skill not in evals_confirmed:
            report["refused"].extend(
                _item(op, "major bump without evals_confirmed (co-evolving-evals rule)")
                for op in applied_here)
            report["noop"].extend(pending["noop"])
            continue

        new_ver = bump_version(old_ver, bump_kind)
        working = _bump_and_log(working, old_ver, new_ver, date, log_ops)

        # C2: Check body cap AFTER adding changelog lines
        if _body_line_count(working) >= BODY_CAP:
            report["refused"].extend(
                _item(op, "would breach 500-line body cap: split to references/")
                for op in applied_here)
            report["noop"].extend(pending["noop"])
            continue

        # Bump+changelog+cap-check each merged destination buffer exactly
        # ONCE — every anchor moving into the same skill in this batch
        # shares a single snapshot/version/changelog line. A destination
        # problem refuses the WHOLE source batch — a move is atomic across
        # both skills, so nothing (source or any destination) is written
        # unless every side is clean.
        dest_breach = None
        for to_skill, buf in dest_buffers.items():
            dest_bump_kind = _select_bump_kind(
                [{"op": "move"}], overrides.get(to_skill))
            if dest_bump_kind == "major" and to_skill not in evals_confirmed:
                dest_breach = "major bump without evals_confirmed (co-evolving-evals rule)"
                break
            dest_new_ver = bump_version(buf["old_ver"], dest_bump_kind)
            log_ops_dest = [{"op": "move-in", "anchor": f"{m['anchor']} from {skill}",
                            "reason": m.get("reason")} for m in buf["moves"]]
            dest_final = _bump_and_log(buf["working"], buf["old_ver"], dest_new_ver,
                                       date, log_ops_dest)
            if _body_line_count(dest_final) >= BODY_CAP:
                dest_breach = "would breach 500-line body cap: split to references/"
                break
            buf["new_ver"] = dest_new_ver
            buf["final_lines"] = dest_final

        if dest_breach is not None:
            report["refused"].extend(_item(op, dest_breach) for op in applied_here)
            report["noop"].extend(pending["noop"])
            continue

        if not dry_run:
            shutil.copytree(skill_dir, snap)
            with open(md, "w", encoding="utf-8") as f:
                f.write("\n".join(working) + "\n")
            for buf in dest_buffers.values():
                shutil.copytree(buf["dir"], buf["snap"])
                with open(buf["md"], "w", encoding="utf-8") as f:
                    f.write("\n".join(buf["final_lines"]) + "\n")
            for fe in file_effects:
                with open(fe["path"], "w", encoding="utf-8") as f:
                    f.write(fe["content"])

            # Ledger writes happen only now, after every copytree above, so
            # the archive snapshots still carry the pre-op evidence.yaml.
            if retire_anchors or dest_buffers:
                sdata = ledger.load(skill_dir)
                for anchor in retire_anchors:
                    sdata.pop(anchor, None)
                for to_skill, buf in dest_buffers.items():
                    moved_entries = {}
                    for m in buf["moves"]:
                        moved = sdata.pop(m["anchor"], None)
                        if moved is not None:
                            moved_entries[m["anchor"]] = moved
                    if moved_entries:
                        dest_dir = os.path.join(skills_dir, to_skill)
                        ddata = ledger.load(dest_dir)
                        ddata.update(moved_entries)
                        ledger.save(dest_dir, ddata)
                ledger.save(skill_dir, sdata)

        report["skills_bumped"][skill] = (old_ver, new_ver)
        for to_skill, buf in dest_buffers.items():
            report["skills_bumped"][to_skill] = (buf["old_ver"], buf["new_ver"])
        applied_reasons.extend(op.get("reason") for op in applied_here if op.get("reason"))
        for k in ("applied", "noop", "refused"):
            report[k].extend(pending[k])

    if not dry_run:
        report["notes"] = mark_absorbed(applied_reasons, observations_dir, date)
    return report


def _op_summary(op):
    """Changelog summary for one applied op. `add` names the new anchor id
    extracted from its content (`add <anchor-id> (<section>)`), falling
    back to the current `add <section>` form when the content carries no
    anchor id. Every other op keeps its existing anchor/section/file form."""
    kind = op.get("op", "?")
    if kind == "add":
        section = op.get("section", "")
        m = _ANCHOR_ID_RE.search(op.get("content", "") or "")
        if m:
            return f"add {m.group(1)} ({section})"
        return f"add {section}"
    return f"{kind} {op.get('anchor', op.get('section', op.get('file', '')))}"


def _bump_and_log(lines, old_ver, new_ver, date, applied_ops):
    out = []
    ver_done = False
    for line in lines:
        if not ver_done and _VER_RE.match(line):
            out.append(f"version: {new_ver}")
            ver_done = True
        else:
            out.append(line)
    reasons = ", ".join(sorted({str(op.get("reason") or "?") for op in applied_ops}))
    summary = "; ".join(_op_summary(op) for op in applied_ops)
    entry = f"- {new_ver} ({date}): {summary} [reasons: {reasons}] (applied by apply_deltas)"
    final = []
    inserted = False
    i = 0
    while i < len(out):
        line = out[i]
        final.append(line)
        if not inserted and line.strip() == "## Changelog":
            # Skip blank lines and HTML-comment lines after heading
            i += 1
            while i < len(out):
                nxt = out[i]
                if nxt.strip() == "":
                    final.append(nxt)
                    i += 1
                elif nxt.strip().startswith("<!--"):
                    final.append(nxt)
                    i += 1
                else:
                    break
            # Consume exactly one pre-existing blank line right at the
            # insert point (if the scan above just left one) so the new
            # blank line we add below doesn't accrete on repeated bumps —
            # any blank line earlier (e.g. between the heading and a
            # convention comment) stays untouched.
            if final and final[-1].strip() == "":
                final.pop()
            final.append("")
            final.append(entry)
            inserted = True
            i -= 1  # Back up to process this line normally in next iteration
        i += 1
    return final


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("deltas")
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--archive-dir", default="archive")
    ap.add_argument("--observations-dir", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    rep = apply_file(args.deltas, args.skills_dir, args.archive_dir, args.dry_run,
                     observations_dir=args.observations_dir)
    print("| skill | op | anchor | status | note |")
    print("|---|---|---|---|---|")
    for status in ("applied", "noop", "refused"):
        for item in rep[status]:
            print(f"| {item['skill']} | {item['op']} | {item['anchor']} "
                  f"| {status} | {item['note']} |")
    for skill, (old, new) in rep["skills_bumped"].items():
        print(f"\nbumped {skill}: {old} -> {new}"
              + (" (dry-run: not written)" if args.dry_run else ""))
    if rep.get("notes"):
        print("\nabsorption notes:")
        for n in rep["notes"]:
            print(f"- {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
