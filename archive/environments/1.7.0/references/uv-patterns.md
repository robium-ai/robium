# uv patterns

How to set up and run a pure-Python robium project with
[uv](https://docs.astral.sh/uv/). This is the default for any project that
doesn't need ROS 2 or other system-level dependencies — see the decision tree
in `SKILL.md`. Sources: [uv docs](https://docs.astral.sh/uv/), fetched via the
`ctx7` documentation tool (`astral-sh/uv`) rather than from memory — re-verify
against current docs before relying on exact flag behavior.

## Project setup

```bash
uv init my-project        # scaffolds pyproject.toml, a src/ layout, .gitignore
cd my-project
uv add numpy torch        # adds runtime dependencies, updates pyproject.toml + uv.lock
uv add --dev pytest ruff  # adds a `dev` dependency group
```

`pyproject.toml` after a couple of `uv add` calls looks like:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "torch>=2.3",
]

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6"]
```

See `examples/pyproject-uv.toml` for a complete minimal file.

## Running things: always through `uv run`

```bash
uv run python train.py
uv run pytest
uv run ruff check .
```

`uv run` resolves and syncs the project's `.venv` automatically before
running the command — there is no separate "activate the venv" step to
forget or get wrong. This is why the key directive is "never `pip install`
into system Python": `uv run` (and `uv sync`) already give you an isolated,
reproducible environment for free, so there is no reason to fall back to a
global install.

If you do want an activated shell, `uv venv` creates `.venv` explicitly and
you can `source .venv/bin/activate` as usual — but prefer `uv run` for
scripts and CI since it doesn't depend on shell state.

## `uv sync` vs `uv pip install`

- **`uv sync`** (project-mode) makes the environment match `pyproject.toml` +
  `uv.lock` exactly — installs missing packages *and* removes anything not
  declared. This is the reproducibility guarantee: `uv sync` on two different
  machines with the same lockfile produces the same environment.
- **`uv pip install`** (pip-compatible mode) behaves like `pip install` —
  additive only, no lockfile awareness by default. Reach for it only for
  one-off/ad-hoc installs (e.g. pre-installing a build dependency like
  `torch`/`setuptools` before a package that needs it at build time), not as
  the primary install path for a project.

For robium projects, default to `uv sync` / `uv run` as the primary workflow;
treat `uv pip install` as an escape hatch, not the norm.

## Lockfiles

Commit `uv.lock` to the repository. It pins every resolved dependency
(including transitive ones) to an exact version, which is what makes "works
on my machine" become "works everywhere" — this is the uv half of the
local == remote acceptance test from `SKILL.md`. Re-run `uv lock` (or `uv
sync`, which updates the lock as needed) after changing `pyproject.toml`, and
commit the updated lockfile in the same change.

## Pinning the Python version

```bash
uv python pin 3.11
```

Writes a `.python-version` file; `uv run`/`uv sync` then provision and use
that exact interpreter version (downloading it if needed, unless
`UV_PYTHON_DOWNLOADS=0`). Pin explicitly rather than relying on "whatever
Python happens to be on this machine" — another local/remote parity point.

## When `--system` / `UV_SYSTEM_PYTHON` is acceptable

The "never `pip install` into system Python" directive has exactly one
sanctioned exception: inside a **disposable container build stage**, where
"system Python" means the container's own throwaway Python, not a host
machine's. Two legitimate cases:

- **CI runners that are themselves ephemeral** (a fresh container per job):
  setting `UV_SYSTEM_PYTHON=1` for the whole job lets `uv pip install` target
  the runner's Python directly, since there's no persistent host to pollute.
- **A Docker build stage that installs directly into the image's Python**
  rather than creating a nested venv — acceptable *only* when that stage's
  entire filesystem is the deliverable (i.e., you're not also using that
  Python for anything else). Prefer the multi-stage venv pattern in
  `references/docker-patterns.md` when you have a choice; it keeps the
  Dockerfile identical in spirit to the non-Docker uv workflow.

Never use `--system` on a developer's laptop or on a long-lived server's bare
OS Python — that is exactly the case the directive exists to prevent.

## When to graduate from uv to Docker

Stop trying to make uv alone carry a project once any of these become true:

- The project needs ROS 2 or another apt/system package that isn't
  Python-installable.
- The project depends on a specific OS/kernel feature (e.g. certain GPU
  driver interactions, real-time kernel patches).
- You need the *exact same OS base*, not just the same Python packages,
  reproduced on another machine.

At that point, move to `references/docker-patterns.md` — and keep using uv
*inside* the container for the Python-dependency layer; the two are
complementary, not alternatives, once you're in Docker.
