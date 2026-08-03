# Robium Plugin MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the robium Claude Code plugin repo: manifests, skill template, validator, the `robium-architect` subagent, and the 18-skill catalog (9 deep, 9 thin) per the approved spec.

**Architecture:** A single Claude Code plugin whose payload is knowledge, not code: `skills/<name>/SKILL.md` folders (agentskills.io format) with `references/`, `scripts/`, `examples/` one level deep; one subagent; a self-hosted validator script inside the `skill-author` meta-skill that acts as the repo's test suite. Deep skills get full references/examples now; thin skills ship a complete SKILL.md with curated upstream links and deepen later.

**Tech Stack:** Markdown skills (agentskills.io SKILL.md convention), Claude Code plugin manifests (JSON), Python 3.10+ validator run via `uv run` (PEP 723 inline deps), git.

**Spec:** `docs/superpowers/specs/2026-07-10-robium-plugin-design.md` — read it before starting any task. Task content bullets below are binding; the spec is the tie-breaker.

## Global Constraints

- Skill `name` == directory name; lowercase `a-z0-9-`, ≤64 chars (agentskills.io).
- `description` ≤1024 chars, written as trigger surface: capability + "Use when:" phrases + literal keywords + workflow-position marker + "Not for:" negative scope where useful.
- SKILL.md body <500 lines; depth goes to `references/*.md` (single-topic, 5–10 KB, one level deep, never chained).
- Frontmatter: `name` + `description` only, plus `compatibility` only where hardware requirements exist (e.g. isaac-sim). Never `allowed-tools`.
- Required body sections in every skill (validator-enforced): `## When to use this skill`, `## Key directives`, `## Quick start`, `## Platform gotchas`, `## Customization`, `## References` (umbrellas additionally have `## Decision guidance`; tool skills `## Usage patterns`).
- Every skill states its delegation posture (embed / embed+links / delegate) inside "Key directives".
- Every example carries a source link and a `<!-- status: unverified -->` or `<!-- status: verified -->` marker. All MVP examples start `unverified`.
- Helper scripts only when genuinely reusable; `uv run` + PEP 723 header; self-contained.
- No invented syntax or DSL anywhere. Natural language + snippets + configs + Dockerfiles.
- ROS 2 only (ROS 1 is EOL). Modern Gazebo (gz Harmonic/Ionic) only, never Gazebo Classic.
- Research at execution time with current docs (WebFetch/WebSearch/ctx7); do not write upstream API details from memory.
- Commit after every task; push at the end of the last task only.

## File Structure

```
robium/
├── .claude-plugin/plugin.json                    # Task 1
├── .claude-plugin/marketplace.json               # Task 1
├── .gitignore, LICENSE, README.md                # Task 1 (README table finalized in Task 15)
├── skills/_TEMPLATE/SKILL.md                     # Task 2
├── skills/skill-author/{SKILL.md, scripts/validate_skills.py, references/}  # Task 3
├── agents/robium-architect.md                    # Task 4
├── skills/architect/{SKILL.md, references/, examples/}                      # Task 4
├── skills/environments/{SKILL.md, references/, examples/}                   # Task 5
├── skills/integration/{SKILL.md, references/, examples/}                    # Task 6
├── skills/ros2/{SKILL.md, references/, examples/}                           # Task 7
├── skills/nav2/{SKILL.md, references/, examples/}                           # Task 8
├── skills/gazebo/{SKILL.md, references/, examples/}                         # Task 9
├── skills/lerobot/{SKILL.md, references/, examples/}                        # Task 10
├── skills/isaac-sim/{SKILL.md, references/, examples/}                      # Task 11
├── skills/{data,visualization,simulation,testing}/SKILL.md                  # Task 12 (thin umbrellas)
├── skills/{rviz2,foxglove,rerun}/SKILL.md                                   # Task 13 (thin viz tools)
├── skills/{isaac-lab,huggingface}/SKILL.md                                  # Task 14 (thin manip tools)
└── (README skills table + full validation + install smoke test)             # Task 15
```

---

### Task 1: Repo scaffolding and plugin manifests

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.gitignore`
- Create: `LICENSE` (MIT)
- Create: `README.md`

**Interfaces:**
- Produces: installable plugin identity `robium@robium`; marketplace source `./` with default `skills/` + `agents/` discovery. All later tasks drop skills into `skills/<name>/` with no manifest changes needed.

- [ ] **Step 1: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "robium",
  "description": "AI-agent-first robotics dev toolchain: skills for architecting, integrating, simulating, visualizing, testing, and training robotics applications (ROS 2, Nav2, Gazebo, LeRobot, Isaac, HuggingFace)",
  "version": "0.1.0",
  "author": { "name": "robium" },
  "homepage": "https://github.com/robium-ai/robium-docs",
  "repository": "https://github.com/robium-ai/robium-docs",
  "license": "MIT",
  "keywords": ["robotics", "ros2", "nav2", "gazebo", "lerobot", "isaac-sim", "simulation", "physical-ai", "skills"]
}
```

- [ ] **Step 2: Write `.claude-plugin/marketplace.json`**

```json
{
  "name": "robium",
  "owner": { "name": "robium-ai" },
  "metadata": {
    "description": "One-stop robotics plugin for coding agents",
    "version": "0.1.0"
  },
  "plugins": [
    {
      "name": "robium",
      "source": "./",
      "description": "AI-agent-first robotics dev toolchain: stack selection, glue, simulation, visualization, data, testing, and training skills for robotics applications"
    }
  ]
}
```

Single plugin entry with `source: "./"` — Claude Code auto-discovers `skills/` and `agents/` under the plugin root. This is the "enable one plugin" story from the spec.

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.pyc
.DS_Store
.venv/
```

- [ ] **Step 4: Write `LICENSE`** — standard MIT license text, copyright line: `Copyright (c) 2026 robium`.

- [ ] **Step 5: Write `README.md` skeleton**

```markdown
# Robium

AI-agent-first robotics dev toolchain, delivered as a skills-heavy Claude Code plugin.
Enable robium and your coding agent knows which robotics libraries/frameworks/tools fit,
how to glue them together, which patterns actually work, how to test, and where to get data.

## Install

/plugin marketplace add robium-ai/robium-docs
/plugin install robium@robium

## Skills

<!-- SKILLS TABLE — updated in the final task -->

## Design

See `docs/superpowers/specs/2026-07-10-robium-plugin-design.md`.
```

- [ ] **Step 6: Verify manifests parse**

Run: `python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin .gitignore LICENSE README.md
git commit -m "feat: plugin manifests and repo scaffolding"
```

---

### Task 2: Skill template (`skills/_TEMPLATE/`)

**Files:**
- Create: `skills/_TEMPLATE/SKILL.md`

**Interfaces:**
- Produces: the canonical skeleton every skill task (3–14) copies from. Section headings here are exactly what the validator (Task 3) enforces.

- [ ] **Step 1: Write `skills/_TEMPLATE/SKILL.md`**

```markdown
---
name: REPLACE-must-equal-directory-name
description: >
  CAPABILITY SUMMARY in one sentence. Use when: explicit trigger phrase 1;
  trigger phrase 2; literal keywords the user might type ('foo', 'bar').
  WORKFLOW-POSITION MARKER, e.g. "Load after architect selects the stack."
  Not for: adjacent things this skill should NOT fire on (name the sibling skill instead).
---

# Skill Title

One-paragraph orientation: what this skill covers and the outcome it produces.

## When to use this skill

- Expanded triggers beyond the description.
- Cross-references: "for X, use the `sibling` skill instead."

## Key directives

- Delegation posture: one of — **embed** (knowledge lives here) / **embed + links** / **delegate to <upstream skill/plugin>**.
- The guardrails: "never X", "always Y", ordered by importance.

## Quick start

Exact commands / snippets for the most common path. Copy-pasteable.

## Decision guidance   <!-- umbrellas; tool skills use "## Usage patterns" instead -->

The decision tree or the 3-5 most common usage patterns, each with a snippet.

## Platform gotchas

- macOS / Linux / GPU / remote-server notes. Only real ones — delete if none known yet.

## Customization

How to adapt the examples and configs to a different robot/task/env.

## References

- `references/<topic>.md` — one line on what it covers
- `examples/<file>` — one line, with status marker
- Upstream: [official docs](URL), [examples repo](URL), related plugins/skills

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->
```

- [ ] **Step 2: Commit**

```bash
git add skills/_TEMPLATE
git commit -m "feat: skill template skeleton"
```

---

### Task 3: `skill-author` meta-skill + validator (the repo's test suite)

**Files:**
- Create: `skills/skill-author/SKILL.md`
- Create: `skills/skill-author/scripts/validate_skills.py`
- Create: `skills/skill-author/references/quality-bar.md`
- Create: `skills/skill-author/references/learnings-loop.md`
- Create: `skills/skill-author/references/mining-guide.md`

**Interfaces:**
- Consumes: `skills/_TEMPLATE/SKILL.md` (Task 2).
- Produces: `uv run skills/skill-author/scripts/validate_skills.py` → exits 0 with `PASS`, 1 with `FAIL:` lines. Every later task runs this as its test step.

- [ ] **Step 1: Write the validator `skills/skill-author/scripts/validate_skills.py`**

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Validate every skill in skills/ against the robium quality bar.

Checks (per spec section 6): name==dirname, name charset/length, description
present and <=1024 chars, body <500 lines, required sections present,
referenced local files exist. _TEMPLATE is excluded (skeleton, not a skill).
"""
import re
import sys
from pathlib import Path

import yaml

REQUIRED_SECTIONS = [
    "## when to use this skill",
    "## key directives",
    "## quick start",
    "## platform gotchas",
    "## customization",
    "## references",
]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LOCAL_REF_RE = re.compile(r"`((?:references|scripts|examples)/[^`\s]+)`")


def check_skill(skill_dir: Path) -> list[str]:
    errs: list[str] = []
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return [f"{skill_dir.name}: missing or malformed frontmatter"]
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        return [f"{skill_dir.name}: frontmatter YAML error: {exc}"]
    body = m.group(2)

    name = fm.get("name", "")
    desc = (fm.get("description") or "").strip()
    if name != skill_dir.name:
        errs.append(f"{skill_dir.name}: frontmatter name {name!r} != directory name")
    if not NAME_RE.match(name or "") or len(name) > 64:
        errs.append(f"{skill_dir.name}: name violates agentskills.io constraints")
    if not desc:
        errs.append(f"{skill_dir.name}: description missing")
    elif len(desc) > 1024:
        errs.append(f"{skill_dir.name}: description {len(desc)} chars (>1024)")

    n_lines = body.count("\n") + 1
    if n_lines >= 500:
        errs.append(f"{skill_dir.name}: body {n_lines} lines (must be <500)")

    lower = body.lower()
    for section in REQUIRED_SECTIONS:
        if section not in lower:
            errs.append(f"{skill_dir.name}: missing required section '{section}'")

    for ref in LOCAL_REF_RE.findall(body):
        if not (skill_dir / ref).exists():
            errs.append(f"{skill_dir.name}: referenced file missing: {ref}")
    return errs


def main() -> None:
    skills_root = Path(__file__).resolve().parents[2]
    skill_dirs = sorted(
        p for p in skills_root.iterdir() if p.is_dir() and p.name != "_TEMPLATE"
    )
    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(check_skill(skill_dir))
    for err in errors:
        print(f"FAIL: {err}")
    print(f"Checked {len(skill_dirs)} skills: {'FAIL' if errors else 'PASS'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the validator — expect failure (no SKILL.md for skill-author yet)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `FAIL: skill-author: missing SKILL.md` then `Checked 1 skills: FAIL`, exit 1.

- [ ] **Step 3: Write `skills/skill-author/SKILL.md`**

Copy `_TEMPLATE`, then fill. Frontmatter description (verbatim):

> Author and improve robium skills. Three modes: fresh authoring from skills/_TEMPLATE, mining skills out of existing repos and apps, and hardening skills from learnings/ notes after trial runs. Enforces the robium quality bar (template compliance, trigger-surface descriptions, <500-line bodies, stated delegation posture, upstream links, no invented syntax) and runs scripts/validate_skills.py. Use when: 'write a new robium skill', 'improve robium skills', 'absorb learnings', 'harden skills', after building an app produced learnings files, or when distilling patterns from an existing robotics repo into a skill. Wraps Claude's skill-creator skill for evals and description tuning instead of reinventing it. Not for: building robot applications (use architect and the domain skills).

Body content requirements (all template sections present; this is a **deep** skill):
- **Key directives:** delegation posture = embed; knowledge goes to the lowest skill that can hold it; anything appearing twice in learnings becomes a skill edit; every absorbed learning adds a Changelog line to the edited skill; always run the validator before committing skill changes; use Claude's `skill-creator` for eval/description work.
- **Quick start:** the three modes as numbered workflows — fresh (copy _TEMPLATE → research upstream → fill sections → validate → commit), mine (read target repo → list candidate patterns → map each to lowest skill → edit/create → validate), harden (read `learnings/*.md` in the app repo → group by skill → edit skills → add changelog lines → mark learnings absorbed by appending `<!-- absorbed: YYYY-MM-DD -->`).
- **Decision guidance:** when to create a new skill vs deepen an existing one vs add a reference file; when a snippet belongs in the body vs `examples/`.
- **References index** pointing at the three references files and the validator script.

- [ ] **Step 4: Write the three references files**

- `references/quality-bar.md` — the full checklist from spec section 5 (template compliance, description-as-trigger-surface with the 5 ingredients, <500-line body, delegation posture stated, upstream links present, examples carry status markers, no invented syntax), each item with a one-line "how to check".
- `references/learnings-loop.md` — the operational loop from spec section 5: app sessions write `learnings/YYYY-MM-DD.md` (what to capture: wrong/missing guidance, stale samples, no-skill-fired gaps, figured-out-from-scratch moments); hardening sessions consume → edit → changelog → mark absorbed; placement + recurrence rules.
- `references/mining-guide.md` — how to mine a repo: what counts as a reusable pattern (appears in ≥2 places or is a hard-won config), how to trim an upstream example (minimal, runnable, source-linked, status-marked), where mined knowledge lands (lowest skill).

- [ ] **Step 5: Run validator — expect PASS**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 1 skills: PASS`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add skills/skill-author
git commit -m "feat: skill-author meta-skill with repo validator"
```

---

### Task 4: `architect` skill (deep) + `robium-architect` subagent

**Files:**
- Create: `skills/architect/SKILL.md`
- Create: `skills/architect/references/stack-selection.md`
- Create: `skills/architect/references/scaffold-patterns.md`
- Create: `skills/architect/references/brief-template.md`
- Create: `skills/architect/examples/architecture-brief-example.md`
- Create: `agents/robium-architect.md`

**Interfaces:**
- Consumes: `_TEMPLATE`, validator.
- Produces: the routing map all other skills are referenced from; the brief contract `docs/architecture-brief.md` (in app repos) that the subagent writes and the main agent refines.

- [ ] **Step 1: Research** — WebSearch/WebFetch current landscape enough to write honest decision guidance: ROS 2 distro status (current LTS), Nav2/Gazebo pairing, LeRobot maturity, Isaac Sim/Lab requirements. Keep notes; do not trust memory for version facts.

- [ ] **Step 2: Write `skills/architect/SKILL.md`**

Frontmatter description (verbatim):

> Entry-point skill for designing robotics applications with AI agents. Turns requirements (robot type, task, hardware, sim-vs-real, GPU/budget) into a full stack decision — middleware, simulation, data, visualization, training frameworks — plus a scaffold plan and a written architecture brief. Use when: starting any new robotics app; 'build a robot app', 'which robotics stack', 'scaffold a robotics project', 'mobile robot', 'robot arm', 'manipulation policy', 'navigation stack'; or when requirements exist but the stack is unchosen. This is the entry-point skill of the robium plugin: load it first; it routes to every other robium skill per build phase. Not for: debugging an existing stack (use the matching tool skill) or authoring robium skills (skill-author).

Body content requirements (**deep**; umbrella → `## Decision guidance`):
- **Key directives:** embed posture; always produce/update `docs/architecture-brief.md` in the app repo — it is the living architecture contract; virtual-environment-first (route to `environments`); never invent syntax — recommend real, current tools only; state open risks explicitly in the brief.
- **Quick start:** requirement checklist to collect (robot type, task, hw, sim/real, GPU, local/remote), then the two MVP golden paths: nav → `ros2`+`nav2`+`gazebo`+`visualization`; manipulation → `lerobot`(+`isaac-sim`/`isaac-lab` if GPU)+`huggingface`+`data`.
- **Decision guidance:** the routing table — every robium skill with one line on when architect hands off to it (the only skill that knows the whole catalog, per spec).
- **References:** `stack-selection.md` (decision trees: middleware yes/no ROS 2, simulator gazebo-vs-isaac, training framework), `scaffold-patterns.md` (repo layouts for a ROS 2 app and a LeRobot app: directory trees + what each dir holds), `brief-template.md` (the brief's required sections: chosen stack + reasoning, module breakdown, comms plan, env strategy, data plan, robium skills per phase, open risks), `examples/architecture-brief-example.md` (a filled example for a hypothetical diff-drive warehouse robot, `<!-- status: unverified -->`).

- [ ] **Step 3: Write the three references + example brief** per the content lists above. Each references file single-topic, 5–10 KB.

- [ ] **Step 4: Write `agents/robium-architect.md`**

```markdown
---
name: robium-architect
description: Robotics application architect. Use PROACTIVELY at the start of any new robotics application to run the heavy stack-selection research and produce the architecture brief. Takes requirements (robot type, task, hardware, sim-vs-real, GPU/budget, local/remote); returns a concise summary and writes the full brief to docs/architecture-brief.md in the application repo. One-shot: after the brief exists, refine it in the main conversation with the architect skill instead of relaunching; relaunch only for genuine re-architecture pivots.
tools: Read, Glob, Grep, WebFetch, WebSearch, Write
---

You are the robium application architect. Your job is the research burst at the
start of a robotics project — comparing stacks, reading upstream docs, weighing
trade-offs — so the main conversation stays clean.

Playbook: read the robium `architect` skill (skills/architect/SKILL.md and its
references/) and follow its decision guidance. Research with current docs; never
answer version/API questions from memory.

Process:
1. Extract requirements from your prompt. If something critical is missing
   (robot type, sim-vs-real, GPU availability), state your assumption explicitly
   in the brief rather than guessing silently.
2. Decide the stack using the architect skill's decision trees.
3. Write the full architecture brief to docs/architecture-brief.md in the
   application repo, following references/brief-template.md exactly: chosen
   stack with reasoning, module breakdown, comms plan, env strategy (uv vs
   Docker), data plan, which robium skills to load per build phase, open risks.

Hard boundaries:
- Write ONLY docs/architecture-brief.md. No scaffolding, no code, no other files.
- Your final message is a short summary of the decision + the brief's location +
  the top 3 risks. The brief file carries the detail.
```

- [ ] **Step 5: Run validator — expect PASS (2 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 2 skills: PASS`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add skills/architect agents
git commit -m "feat: architect skill and robium-architect subagent"
```

---

### Task 5: `environments` skill (deep)

**Files:**
- Create: `skills/environments/SKILL.md`
- Create: `skills/environments/references/uv-patterns.md`
- Create: `skills/environments/references/docker-patterns.md`
- Create: `skills/environments/references/gpu-and-remote.md`
- Create: `skills/environments/examples/pyproject-uv.toml`
- Create: `skills/environments/examples/Dockerfile.ros2`
- Create: `skills/environments/examples/Dockerfile.gpu-ml`

**Interfaces:**
- Consumes: `_TEMPLATE`, validator.
- Produces: env decision logic that `architect` routes to and `integration` builds on.

- [ ] **Step 1: Research** — current uv docs (ctx7: `uv`), ROS 2 Docker official images, NVIDIA container toolkit basics. Verify image tags/current versions before writing them into examples.

- [ ] **Step 2: Write `skills/environments/SKILL.md`**

Frontmatter description (verbatim):

> Virtual-environment-first setup for robotics projects: decide uv/venv vs Docker, make local and remote-server runs reproduce identically, handle GPU passthrough and headless/display forwarding. Use when: setting up any new robotics project environment; 'uv', 'venv', 'virtualenv', 'docker for this project', 'reproducible environment', 'works locally but not on the server', 'GPU in container'. Load early in any robium build, right after architect. Decision rule of thumb: pure-Python ML stacks → uv; anything needing ROS 2 or system deps → Docker. Not for: multi-module application Dockerfiles and compose wiring (integration skill).

Body content requirements (**deep**; umbrella):
- **Key directives:** embed posture; environment before code — no `pip install` into system Python ever; every project must state its env strategy in the architecture brief; identical env local and remote is the acceptance test.
- **Decision guidance:** uv vs venv vs Docker tree (Python-only → uv; ROS 2/system deps → Docker; mixed → Docker with uv inside); local vs remote parity checklist.
- **Platform gotchas:** macOS has no native ROS 2 → Docker; GPU containers need nvidia-container-toolkit (Linux only); X11/Wayland forwarding vs headless + web viz (route to `foxglove`).
- **References/examples** per the file list; Dockerfiles minimal and source-linked, `<!-- status: unverified -->` (as comments compatible with each file format: `# status: unverified` in Dockerfiles/TOML).

- [ ] **Step 3: Write references + examples** per lists above.

- [ ] **Step 4: Run validator — expect PASS (3 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 3 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/environments
git commit -m "feat: environments skill (deep)"
```

---

### Task 6: `integration` skill (deep)

**Files:**
- Create: `skills/integration/SKILL.md`
- Create: `skills/integration/references/comms-selection.md`
- Create: `skills/integration/references/dockerfile-guide.md`
- Create: `skills/integration/references/compose-patterns.md`
- Create: `skills/integration/examples/docker-compose.ros2-app.yml`
- Create: `skills/integration/examples/Dockerfile.multistage-ros2`

**Interfaces:**
- Consumes: `environments` (env strategy decided first — cross-reference it).
- Produces: glue guidance `architect` routes to for the "wire it together" phase.

- [ ] **Step 1: Research** — ROS 2 comms patterns (topics/services/actions), zenoh bridge status, docker compose for ROS 2 (network modes, DDS discovery across containers). Verify current recommendations.

- [ ] **Step 2: Write `skills/integration/SKILL.md`**

Frontmatter description (verbatim):

> Glue robotics modules into one running system: choose module boundaries, pick inter-module communication (ROS 2 topics/services/actions, zenoh, gRPC, REST, shared memory), and write solid Dockerfiles and docker-compose for robotics workloads. Use when: wiring components together; 'containerize this', 'dockerfile', 'docker compose', 'how should these modules talk', 'connect the planner to the controller', multi-process or multi-container robotics systems. Load after architect chose the stack and environments set the env strategy. Not for: choosing the overall stack (architect) or single-project env setup (environments).

Body content requirements (**deep**; umbrella):
- **Key directives:** embed posture; prefer ROS 2 native comms inside a ROS system — add non-ROS transports only across system boundaries; one process per container unless there's a stated reason; DDS discovery across containers must be configured explicitly, never assumed.
- **Decision guidance:** comms-choice table (same-process / same-host ROS / cross-host / non-ROS peer), module-boundary heuristics (split by rate + failure domain).
- **References/examples** per file list; compose example = minimal two-service ROS 2 app (sim + app) with DDS config, source-linked, status-marked.

- [ ] **Step 3: Write references + examples.**

- [ ] **Step 4: Run validator — expect PASS (4 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 4 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/integration
git commit -m "feat: integration skill (deep)"
```

---

### Task 7: `ros2` skill (deep)

**Files:**
- Create: `skills/ros2/SKILL.md`
- Create: `skills/ros2/references/workspace-and-packages.md`
- Create: `skills/ros2/references/launch-patterns.md`
- Create: `skills/ros2/references/interfaces-and-qos.md`
- Create: `skills/ros2/references/debugging.md`
- Create: `skills/ros2/examples/package-ament-python/` (minimal package: `package.xml`, `setup.py`, one node file, one launch file — each source-linked, status-marked)

**Interfaces:**
- Consumes: `_TEMPLATE`, validator.
- Produces: the foundation skill `nav2`, `gazebo`, `rviz2` cross-reference.

- [ ] **Step 1: Research** — current ROS 2 LTS distro docs (ctx7 or docs.ros.org): colcon, ament_python package anatomy, launch, QoS matrix, rosdep. Pin the distro name used throughout the skill to the current LTS.

- [ ] **Step 2: Write `skills/ros2/SKILL.md`**

Frontmatter description (verbatim):

> Core ROS 2 usage: workspaces, colcon builds, packages (ament_python/ament_cmake), nodes, topics/services/actions, QoS, launch files, parameters, TF2, rosdep, and gluing third-party packages together. Use when: any ROS 2 development or debugging; 'ros2', 'colcon', 'launch file', 'package.xml', 'QoS mismatch', 'TF', 'node not receiving messages', 'rosdep'. Foundation skill for the ROS vertical — load alongside nav2, gazebo, rviz2. ROS 2 only; ROS 1 is EOL and out of scope. Not for: navigation specifics (nav2), simulation (gazebo), or visualization (rviz2/foxglove).

Body content requirements (**deep**; tool skill → `## Usage patterns`):
- **Key directives:** embed posture (no good upstream skill exists); always rosdep-install before building; QoS compatibility is the first suspect for silent topic failures; workspace overlays over source edits of third-party packages.
- **Usage patterns:** create package → build → run; add a dependency; write a launch file; bridge two third-party packages (remap + relay); parameterize a node.
- **Platform gotchas:** macOS → Docker only (cross-ref `environments`); DDS env vars (`ROS_DOMAIN_ID`); shell sourcing order.
- **References/examples** per file list.

- [ ] **Step 3: Write references + example package files.**

- [ ] **Step 4: Run validator — expect PASS (5 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 5 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/ros2
git commit -m "feat: ros2 skill (deep)"
```

---

### Task 8: `nav2` skill (deep)

**Files:**
- Create: `skills/nav2/SKILL.md`
- Create: `skills/nav2/references/nav2-architecture.md`
- Create: `skills/nav2/references/tuning-guide.md`
- Create: `skills/nav2/references/common-failures.md`
- Create: `skills/nav2/examples/nav2-params-diffdrive.yaml`
- Create: `skills/nav2/examples/bringup-launch-snippet.py`

**Interfaces:**
- Consumes: cross-refs `ros2`, `gazebo`, `visualization`.
- Produces: the nav-vertical core skill the trial run exercises.

- [ ] **Step 1: Research** — current Nav2 docs (docs.nav2.org): bringup, BT navigator, costmap layers, planner/controller servers, AMCL vs slam_toolbox. Base the params example on the official minimal diff-drive config.

- [ ] **Step 2: Write `skills/nav2/SKILL.md`**

Frontmatter description (verbatim):

> Nav2 mobile-robot navigation for ROS 2: bringup, behavior trees, costmaps, planner/controller servers, localization (AMCL, slam_toolbox), waypoint following, and tuning. Use when: 'navigation', 'nav2', 'costmap', 'path planning', 'robot won't move to goal', 'localization', 'SLAM', 'AMCL', 'waypoint', or any autonomous mobile robot task. Load after architect selects the ROS nav stack; pairs with ros2 (foundation), gazebo (sim), and visualization (debugging). Not for: manipulation (lerobot) or generic ROS 2 issues (ros2).

Body content requirements (**deep**; tool skill):
- **Key directives:** embed + links posture; start from the official minimal config and change one subsystem at a time; sim time consistency (`use_sim_time`) everywhere; verify TF tree + map→odom→base_link before tuning anything else.
- **Usage patterns:** bringup with an existing map; SLAM-then-navigate; send goals programmatically; tune for a new robot footprint/speed.
- **References/examples** per file list; `common-failures.md` = the "robot won't move" diagnostic checklist.

- [ ] **Step 3: Write references + examples.**

- [ ] **Step 4: Run validator — expect PASS (6 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 6 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/nav2
git commit -m "feat: nav2 skill (deep)"
```

---

### Task 9: `gazebo` skill (deep)

**Files:**
- Create: `skills/gazebo/SKILL.md`
- Create: `skills/gazebo/references/worlds-and-models.md`
- Create: `skills/gazebo/references/sensors.md`
- Create: `skills/gazebo/references/ros2-bridge.md`
- Create: `skills/gazebo/examples/diffdrive-world-snippet.sdf`
- Create: `skills/gazebo/examples/ros-gz-bridge-config.yaml`

**Interfaces:**
- Consumes: cross-refs `ros2`, `nav2`, `simulation`.
- Produces: the sim half of the nav-vertical trial run.

- [ ] **Step 1: Research** — current gz release docs (gazebosim.org): SDF worlds, sensor plugins (lidar/camera/IMU), ros_gz bridge syntax, headless mode. Confirm the current LTS pairing with the chosen ROS 2 distro.

- [ ] **Step 2: Write `skills/gazebo/SKILL.md`**

Frontmatter description (verbatim):

> Modern Gazebo (gz — Harmonic/Ionic line) simulation: SDF worlds and models, sensors (lidar, camera, IMU, contact), the ros_gz bridge, spawning robots, and headless/server operation. Use when: 'gazebo', 'gz sim', 'ros_gz', 'simulate the robot', 'add a lidar to the sim', simulating mobile robots or sensors in the ROS ecosystem. Pairs with ros2 and nav2; simulator SELECTION lives in the simulation skill. Gazebo Classic (11) is EOL — this skill covers modern gz only and must never recommend Classic. Not for: Isaac Sim (isaac-sim) or non-ROS simulation.

Body content requirements (**deep**; tool skill):
- **Key directives:** embed + links posture; never Gazebo Classic; bridge every topic explicitly (config file over ad-hoc CLI bridges); sensor rates/frames must match the real target robot (cross-ref `simulation` correctness guidance).
- **Usage patterns:** run a world headless; spawn a robot from SDF/URDF; bridge sensor topics to ROS 2; add sensor noise.
- **Platform gotchas:** GPU vs software rendering; running gz in Docker (cross-ref `environments`); macOS status.
- **References/examples** per file list.

- [ ] **Step 3: Write references + examples.**

- [ ] **Step 4: Run validator — expect PASS (7 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 7 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/gazebo
git commit -m "feat: gazebo skill (deep)"
```

---

### Task 10: `lerobot` skill (deep)

**Files:**
- Create: `skills/lerobot/SKILL.md`
- Create: `skills/lerobot/references/datasets.md`
- Create: `skills/lerobot/references/policies-and-training.md`
- Create: `skills/lerobot/references/eval-and-sim.md`
- Create: `skills/lerobot/examples/train-act-command.md`
- Create: `skills/lerobot/examples/load-dataset-snippet.py`

**Interfaces:**
- Consumes: cross-refs `huggingface` (hub mechanics), `environments` (uv), `data` (sourcing strategy).
- Produces: the manipulation-vertical core skill the trial run exercises.

- [ ] **Step 1: Research** — current LeRobot repo/docs (github.com/huggingface/lerobot, ctx7): install (uv), LeRobotDataset format, available policies (ACT, diffusion, pi0, …), train/eval CLI, sim envs shipped. Verify current CLI shapes — LeRobot moves fast; do not write commands from memory.

- [ ] **Step 2: Write `skills/lerobot/SKILL.md`**

Frontmatter description (verbatim):

> HuggingFace LeRobot for physical-AI manipulation: the LeRobotDataset format, loading and recording episodes, training policies (ACT, diffusion, pi0), evaluating in simulation, and teleoperation. Use when: 'lerobot', 'manipulation policy', 'imitation learning', 'train a robot arm policy', 'ACT', 'diffusion policy', physical-AI dataset/training/eval tasks. Core skill of the manipulation vertical; pairs with huggingface (hub mechanics), environments (uv-first install), and data (sourcing strategy). Not for: classical motion planning or the NVIDIA RL stack (isaac-lab).

Body content requirements (**deep**; tool skill):
- **Key directives:** embed robotics glue + point to HF ecosystem for hub mechanics (delegation posture); uv-first install per `environments`; start from a pretrained/hub policy or official example config before training from scratch; small-scale fine-tune before long runs.
- **Usage patterns:** browse/load a hub dataset; visualize episodes (cross-ref `rerun`); train a policy on an existing dataset; evaluate in a sim env; record new episodes.
- **Platform gotchas:** GPU vs Apple Silicon (MPS) vs CPU training expectations; headless eval on remote servers.
- **References/examples** per file list; commands copied from current official docs with source links, status-marked.

- [ ] **Step 3: Write references + examples.**

- [ ] **Step 4: Run validator — expect PASS (8 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 8 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/lerobot
git commit -m "feat: lerobot skill (deep)"
```

---

### Task 11: `isaac-sim` skill (deep)

**Files:**
- Create: `skills/isaac-sim/SKILL.md`
- Create: `skills/isaac-sim/references/setup-and-requirements.md`
- Create: `skills/isaac-sim/references/ros2-integration.md`
- Create: `skills/isaac-sim/references/scenes-and-sensors.md`
- Create: `skills/isaac-sim/examples/docker-run-command.md`

**Interfaces:**
- Consumes: cross-refs `simulation`, `isaac-lab`, `environments`.
- Produces: the NVIDIA-ecosystem entry point.

- [ ] **Step 1: Research** — current Isaac Sim docs (NVIDIA): version, GPU/driver requirements, container images, ROS 2 bridge, headless/livestream. Verify requirements — they change per release.

- [ ] **Step 2: Write `skills/isaac-sim/SKILL.md`**

Frontmatter — include a `compatibility` field (the one skill that needs it): `Requires NVIDIA RTX-class GPU and recent drivers; Linux or Windows; no macOS support.` Description (verbatim):

> NVIDIA Isaac Sim: installation and container setup, GPU/driver requirements, USD scenes, robots and sensors, the ROS 2 bridge, and headless/livestream operation for remote servers. Use when: 'isaac sim', 'omniverse', GPU photorealistic simulation, synthetic data generation, or NVIDIA robotics ecosystem work. State the GPU requirement BEFORE recommending Isaac Sim — if the user lacks an RTX-class NVIDIA GPU, route to gazebo instead. Simulator selection lives in the simulation skill. Not for: RL training workflows (isaac-lab) or lightweight simulation needs (gazebo).

Body content requirements (**deep**; tool skill):
- **Key directives:** embed + links posture (no upstream skill exists); check GPU/driver compatibility first, always; prefer the official container for reproducibility (cross-ref `environments`); headless + livestream for remote work.
- **Usage patterns:** run the container; load a scene; add a robot + sensors; enable the ROS 2 bridge; generate synthetic data.
- **References/examples** per file list.

- [ ] **Step 3: Write references + example.**

- [ ] **Step 4: Run validator — expect PASS (9 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 9 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/isaac-sim
git commit -m "feat: isaac-sim skill (deep)"
```

---

### Task 12: Thin umbrellas — `data`, `visualization`, `simulation`, `testing`

**Files:**
- Create: `skills/data/SKILL.md`
- Create: `skills/visualization/SKILL.md`
- Create: `skills/simulation/SKILL.md`
- Create: `skills/testing/SKILL.md`

**Interfaces:**
- Consumes: cross-refs to their tool skills (visualization → rviz2/foxglove/rerun; simulation → gazebo/isaac-sim).
- Produces: complete selection-level guidance; deepened later via the learnings loop.

Thin = complete SKILL.md with all required sections and curated upstream links; no references/ or examples/ yet. Each still passes the validator.

- [ ] **Step 1: Write `skills/data/SKILL.md`** — description (verbatim):

> Data sourcing strategy for robotics and physical-AI: choose between offline datasets (HuggingFace hub, Open X-Embodiment and similar), simulation-generated data, and teleop/real-robot collection; plan storage formats, episode structure, and dataset versioning. Use when: 'where do we get data', 'training data for the robot', 'dataset for manipulation', 'generate data in sim', 'collect demonstrations', planning any data pipeline for robot learning. Umbrella skill — mechanics live downstream: hub operations in huggingface, LeRobot formats in lerobot, synthetic generation in isaac-sim/gazebo. Not for: model training itself (lerobot, isaac-lab).

Decision guidance: offline-first rule (search existing datasets before collecting); sim-generation vs teleop cost trade-offs; verify embodiment match before committing to a dataset.

- [ ] **Step 2: Write `skills/visualization/SKILL.md`** — description (verbatim):

> Choose and apply robotics visualization: selection guidance for rviz2 vs Foxglove vs Rerun, plus best practices — what to visualize at each dev stage, live vs recorded, local vs remote. Use when: 'visualize', 'see what the robot sees', 'debug visually', 'plot the trajectory', 'dashboard for the robot', choosing a viz tool, or recording data for later inspection. Umbrella skill — after selecting, load the matching tool skill: rviz2 (ROS-native debugging), foxglove (remote/web + MCAP recording), rerun (ML/data-centric logging). Not for: tool-specific how-to (the per-tool skills).

Decision guidance: selection table by context (ROS desktop debugging → rviz2; remote/server or sharing → foxglove; ML rollouts/custom pipelines → rerun); always-visualize checklist (TF, sensor rates, costmaps/policy actions).

- [ ] **Step 3: Write `skills/simulation/SKILL.md`** — description (verbatim):

> Choose and set up robotics simulators, and simulate sensors correctly: Gazebo vs Isaac Sim selection, sensor fidelity (rates, noise models, frames matching the real robot), determinism, and sim-to-real considerations. Use when: 'simulate', 'which simulator', 'test without hardware', 'sensor simulation', 'sim-to-real', or any simulation-strategy question. Umbrella skill — after selection, load gazebo or isaac-sim for mechanics. Selection rule of thumb: ROS-centric mobile robotics or no NVIDIA GPU → gazebo; photorealism, synthetic data at scale, or NVIDIA RL stack → isaac-sim. Not for: simulator-specific how-to (gazebo, isaac-sim).

Decision guidance: the selection tree + sensor-correctness checklist (rate, noise, frame names, timestamps, `use_sim_time`).

- [ ] **Step 4: Write `skills/testing/SKILL.md`** — description (verbatim):

> Test-driven robotics development: smoke tests for launch files, sim-based regression tests, node-level unit tests, policy eval as a test, and CI patterns for robotics repos. Use when: 'test the robot app', 'how do I test this node', 'smoke test', 'regression test in sim', setting up tests for a new robotics project, or before claiming any robotics app works. Applies to both verticals: launch_testing and pytest for ROS 2 apps; deterministic small-scale eval runs for ML policies. Load alongside whatever skill is building the thing under test. Not for: general (non-robotics) testing practices.

Decision guidance: the test pyramid for robotics (unit → node/launch smoke → sim scenario → policy eval); "a sample app is not done until its smoke test passes" (feeds the trial-run bar).

- [ ] **Step 5: Run validator — expect PASS (13 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 13 skills: PASS`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add skills/data skills/visualization skills/simulation skills/testing
git commit -m "feat: thin umbrella skills (data, visualization, simulation, testing)"
```

---

### Task 13: Thin viz tool skills — `rviz2`, `foxglove`, `rerun`

**Files:**
- Create: `skills/rviz2/SKILL.md`
- Create: `skills/foxglove/SKILL.md`
- Create: `skills/rerun/SKILL.md`

- [ ] **Step 1: Write `skills/rviz2/SKILL.md`** — description (verbatim):

> RViz2 visualization for ROS 2: displays, TF frame debugging, markers, saved config files, and the common 'nothing shows up' fixes (fixed frame, QoS, sim time). Use when: 'rviz', 'rviz2', visualizing ROS topics, TF trees, costmaps, or robot models during development. ROS-native desktop debugging tool — for remote/web visualization use foxglove; for ML/data-centric logging use rerun. Pairs with ros2 and nav2.

Usage patterns: launch with a saved config; the nothing-shows-up checklist; nav2 debugging display set. Embed posture (small domain).

- [ ] **Step 2: Write `skills/foxglove/SKILL.md`** — description (verbatim):

> Foxglove for robotics visualization: foxglove_bridge setup for live ROS 2 robots, layouts, MCAP recording and playback, and remote/web visualization of robots running on servers. Use when: 'foxglove', 'mcap', visualizing a robot running on a remote server, sharing visualization with others, or recording sessions for later analysis. The remote-viz answer in the robium stack — key to the local-vs-remote workflow (cross-ref environments). Not for: ROS desktop debugging (rviz2) or ML logging (rerun).

Usage patterns: bridge a live robot; record MCAP; view remotely in the web app. Embed + links posture.

- [ ] **Step 3: Write `skills/rerun/SKILL.md`** — description (verbatim):

> Rerun for data-centric robotics and ML visualization: logging APIs (Python), timelines, entity paths, and viewing policy rollouts, episode data, and sensor streams. Use when: 'rerun', visualizing ML training/eval rollouts, LeRobot episode data, or custom sensor pipelines outside ROS tooling. Defers heavily to Rerun's official examples and docs — check them before writing logging code. Pairs with lerobot and data. Not for: live ROS topic debugging (rviz2, foxglove).

Usage patterns: log a simple stream; visualize a LeRobot episode; remote viewer. Point-upstream posture (delegate-leaning: link Rerun's examples as primary).

- [ ] **Step 4: Run validator — expect PASS (16 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 16 skills: PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/rviz2 skills/foxglove skills/rerun
git commit -m "feat: thin viz tool skills (rviz2, foxglove, rerun)"
```

---

### Task 14: Thin manipulation tool skills — `isaac-lab`, `huggingface`

**Files:**
- Create: `skills/isaac-lab/SKILL.md`
- Create: `skills/huggingface/SKILL.md`

- [ ] **Step 1: Write `skills/isaac-lab/SKILL.md`** — description (verbatim):

> NVIDIA Isaac Lab: reinforcement-learning and imitation-learning workflows on top of Isaac Sim — prebuilt environments and tasks, training runs, and exporting policies. Use when: 'isaac lab', 'GPU RL for robots', 'train in isaac', sim-to-real policy training in the NVIDIA stack. Load after isaac-sim basics are settled (same GPU requirements apply — RTX-class NVIDIA GPU, no macOS). Alternative ML path to lerobot; the architect skill decides between them. Not for: Isaac Sim setup itself (isaac-sim) or imitation learning on real-robot datasets (lerobot).

Embed + links posture; usage patterns: install on top of Isaac Sim; run a prebuilt task; train + monitor.

- [ ] **Step 2: Write `skills/huggingface/SKILL.md`** — description (verbatim):

> HuggingFace ecosystem for robotics projects: hub datasets and models for robot learning, and demo Spaces. DELEGATES: for hub mechanics (download/upload/auth/jobs), install HuggingFace's own skills — /plugin marketplace add huggingface/skills, then /plugin install hf-cli@huggingface-skills — and defer to them; this skill adds only the robotics-specific layer (which datasets and models matter for manipulation and navigation, robotics dataset conventions on the hub). Use when: HF hub operations inside a robotics project, 'huggingface dataset for robots', 'upload the policy to the hub', and the HF skills aren't installed yet. Pairs with lerobot and data.

Delegate posture — this is the delegation showcase: Key directives instruct installing/deferring to upstream HF skills; body stays short and robotics-specific.

- [ ] **Step 3: Run validator — expect PASS (18 skills)**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 18 skills: PASS`, exit 0.

- [ ] **Step 4: Commit**

```bash
git add skills/isaac-lab skills/huggingface
git commit -m "feat: thin manipulation tool skills (isaac-lab, huggingface)"
```

---

### Task 15: README skills table, full validation, install smoke test

**Files:**
- Modify: `README.md` (replace `<!-- SKILLS TABLE ... -->` marker)

- [ ] **Step 1: Update README** — replace the marker with a hand-maintained table: one row per skill (18 rows): name, layer (umbrella/tool), depth (deep/thin), one-line purpose taken from each description's first sentence. Note the architect subagent under a short `## Agents` section.

- [ ] **Step 2: Full validation**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 18 skills: PASS`, exit 0.

Run: `python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Install smoke test (manual, with the user)** — in a Claude Code session: `/plugin marketplace add /Users/robium-ai/repos/robium` then `/plugin install robium@robium`; confirm the 18 skills and the robium-architect agent appear. Ask the user to run this and confirm.

- [ ] **Step 4: Commit and push**

```bash
git add README.md
git commit -m "feat: README skills table; MVP catalog complete"
git push origin main
```

---

## Verification (whole plan)

1. `uv run skills/skill-author/scripts/validate_skills.py` → `Checked 18 skills: PASS`.
2. Both manifests parse; local marketplace install shows the plugin, 18 skills, 1 agent.
3. Spot-check 3 skills (one deep umbrella, one deep tool, one thin) against the quality bar in `skills/skill-author/references/quality-bar.md`.
4. **Out of plan scope (next effort):** the two trial runs in a new `robium-applications` repo — nav app and manipulation app — which are the spec's real MVP gate.

## Self-review notes

- Spec coverage: repo structure (T1), template (T2), skill-author + validator (T3), architect + subagent (T4), all 9 deep skills (T3–T11), all 9 thin skills (T12–T14), routing rules (architect body, T4), validation (T3, T15). Trial runs are explicitly deferred to robium-applications per spec scope.
- Deep-skill bodies are research-authored at execution time by design (content-authoring project); the binding parts — file lists, verbatim descriptions, required directives, section structure, validator checks — are fully specified above with no placeholders.
- Type/name consistency: skill names in descriptions' cross-references match directory names throughout (architect, integration, environments, data, visualization, simulation, testing, skill-author, ros2, nav2, gazebo, rviz2, foxglove, rerun, lerobot, isaac-sim, isaac-lab, huggingface).
