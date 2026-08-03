# Robium — Brainstorm Seed

*Input for `superpowers:brainstorming`. This is a draft, not a spec — continue brainstorming from here. Raw source notes live in `raw-drafts.md`.*

## One-liner

Robium is an **AI-agent-first robotics dev toolchain**, delivered as a skills-heavy coding-agent plugin (Claude Code / Cursor style). When anyone builds a robotics application with a coding agent, they enable Robium and their agent gets a large capability boost: it knows which libraries/frameworks/tools fit, how to glue them together, which patterns actually work, how to test, and where to get data.

## What it is (and isn't)

- **Is:** a plugin repo of skills (`SKILL.md` format per agentskills.io, mirroring `huggingface/skills` as the closest real-world precedent), plus battle-tested examples, helper scripts, reference material, and possibly agents.
- **Isn't:** a framework, a codegen product, or a new syntax/DSL. No invented abstractions — natural language + example snippets + Dockerfiles + config samples + a few genuinely reusable helper scripts.

## Skill catalog (initial flavors)

1. **Architect** — scaffolding decisions: which libraries, how they fit together, how to generate the system, what data to use. Carries higher-level examples (scaffolding layouts, Docker compositions).
2. **Integration / glue** — wiring modules together, inter-module communication choices, writing solid Dockerfiles/containers.
3. **Data strategy** — where data comes from: generate from real scenarios vs. offline datasets vs. other sources.
4. **ROS** — ROS domain knowledge, gluing ROS packages together.
5. **Hugging Face** — HF ecosystem usage; more generally, every skill should know about and *delegate to* existing plugins/skills from its libraries instead of reinventing.
6. **NVIDIA robotics ecosystem** — Isaac and friends: usage and integration.
7. **LeRobot** — LeRobot-specific skills.
8. **Visualization** — umbrella skill (best practices, tool selection) + per-tool skills: RViz, Rerun, Foxglove, …
9. **Simulation** — simulator selection, simulating sensors correctly.

Each skill folder ships samples scoped to its altitude (architect = high-level scaffolding/Docker; tool skills = module-in-context usage), and consistently includes: example snippets, customization guidance, example configs, platform gotchas, and links to upstream samples/repos/plugins/official docs. Good generalization is a standing requirement.

## MVP verticals

1. **Classical robotics:** ROS mobile-robot navigation.
2. **Physical AI / ML:** hand manipulation via LeRobot, Google robotics libraries, or NVIDIA.

## Cross-cutting principles

- **Virtual-environment-first:** Docker when a full env is needed, otherwise uv/uvx/venv — identical repro local vs. remote server.
- **Delegate, don't reimplement:** prefer upstream plugins/skills/docs; Robium curates and glues.
- **Test-driven:** sample applications are built test-driven and kept maintained and running.
- **No invented syntax:** the deliverable is knowledge + examples, not code.

## The skill development loop (first-class concern)

- Companion repo **`robium-applications`**: real apps generated *using* Robium skills — serving as (a) the proving ground that hardens skills, (b) a living, always-running, test-driven regression suite, and (c) the canonical samples the skills reference.
- Reverse direction too: build some apps *without* skills, then distill skills from what worked.
- Skill authoring uses Claude's own skill-generation tooling (`skill-creator`, `superpowers:writing-skills`) plus mining existing repos (real ROS apps, etc.) for reusable patterns.

## Open questions to brainstorm

- Repo layout specifics: what exactly do we mirror from `huggingface/skills` (needs the detailed investigation of their format/structure)?
- Skill granularity: one umbrella per domain vs. many narrow skills — where's the line (e.g. visualization umbrella + per-tool)?
- How does the plugin get distributed/installed (marketplace? single repo? versioning)?
- Does Robium need its own CLI (HF pairs skills with `hf`), or is it pure skills for MVP?
- What are the acceptance criteria for a skill being "battle-tested"?
- How do the two MVP verticals prioritize the skill catalog — which skills are needed first?
- What exactly does the feedback loop from robium-applications back into skills look like operationally?
