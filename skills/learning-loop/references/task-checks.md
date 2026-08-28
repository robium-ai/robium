# Task-check fixtures

Task checks are optional, repository-controlled commands in a skill's
`evals.yaml`. The skill validator, task runner, variant scorer, and deep-verify
lane all use the same schema from `scripts/engine/task_schema.py`.

```yaml
tasks:
  - name: dataset-loads
    command: uv run skills/lerobot/examples/load-dataset-snippet.py
    pass_criteria: "observation\\.image"
    app: robot-navigation
    example: examples/load-dataset-snippet.py
    timeout: 900
```

| Field | Requirement |
|---|---|
| `name` | Required non-empty kebab-case string, unique within the skill. |
| `command` | Required non-empty shell command. Commands are trusted repository content, not user input. |
| `pass_criteria` | Required non-empty regular expression matched against combined stdout and stderr. |
| `app` | Optional repository-root-relative working directory; absolute and parent-traversal paths are rejected. |
| `example` | Optional skill-relative artifact path used by deep verification; absolute and parent-traversal paths are rejected. |
| `timeout` | Optional positive integer seconds; defaults to 300. |

A task passes only when its command exits zero and `pass_criteria` matches.
Timeouts fail the task and terminate the command's complete process group so
children cannot survive the runner. Dry runs print commands without executing
them. A missing task list is a documented skip; a malformed task list, unknown
skill, or requested task name that does not exist is an actionable error.

`example` joins a task to an unverified file under the same skill. A passing
deep-verification run emits an `annotate` delta that promotes the marker; it
never edits the skill directly. A failed fixture remains a reported finding.
