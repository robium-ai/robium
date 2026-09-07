# Testing a skill change

Match the check to the risk. Most prose edits need the validator and manual
scenario review, not a new harness.

## Always

- Run `uv run skills/skill-author/scripts/validate_skills.py`.
- Read the result as a packaging check, not proof that the guidance is useful.
- For description, routing, or behavioral guidance changes, walk through a
  common request, the changed failure or choice, and the nearest request that
  should route elsewhere. Typos and mechanical link fixes do not need a
  ceremonial scenario review.

## Trigger checks

Keep `evals.yaml` only where selection is genuinely ambiguous:

```yaml
triggers:
  positive:
    - phrase: robot will not move to the navigation goal
  negative:
    - phrase: the Gazebo lidar topic is missing
      expect: gazebo
```

Run existing cases with `uv run scripts/engine/run_trigger_evals.py --skills
<name>`. If the semantic judge is unavailable, treat its lexical fallback as a
diagnostic, not a reason to stuff keywords into the description. Do not create
exhaustive synonym lists or assert exact description wording.

## Task checks

Use a task only for a reusable executable artifact or user-visible behavior:

```yaml
tasks:
  - name: example-runs
    command: uv run skills/example/examples/demo.py
    pass_criteria: "completed"
    timeout: 300
```

- `name`, `command`, and `pass_criteria` are required. Names are unique
  kebab-case; pass criteria are regular expressions.
- `app` may set a repository-relative working directory; `example` may point to
  the skill-relative artifact the task verifies.
- Paths cannot be absolute or escape their allowed root. Referenced examples
  and app directories must exist; apps cannot run from inside `skills/`.
  Timeouts must be positive.
- A task passes only when the command exits zero and its output matches.
- Commands are trusted repository content. Never build one from untrusted user
  input.

The validator and `scripts/engine/run_task_checks.py` share this schema.
