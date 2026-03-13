# Agent Decision Trail

Append-only JSONL log of all automated agent decisions across the system. One file per date: `{YYYY-MM-DD}.jsonl`

## JSONL record schema

Each line is a self-contained JSON object:

```json
{
  "timestamp": "2026-03-13T14:32:01Z",
  "workflow": "semver-agent.yml",
  "repo": "unified-trading-library",
  "agent_type": "claude-haiku",
  "decision": "bump-minor",
  "reasoning_summary": "feat! commit detected on staging, bumped 0.2.3 -> 0.3.0",
  "files_changed": ["pyproject.toml", "CHANGELOG.md"],
  "commit_sha": "abc1234",
  "success": true
}
```

On failure, include `error_message`:

```json
{
  "timestamp": "2026-03-13T14:35:00Z",
  "workflow": "conflict-resolution-agent.yml",
  "repo": "execution-service",
  "agent_type": "claude-sonnet",
  "decision": "resolve-conflict",
  "reasoning_summary": "Attempted 3-way merge of staging_status fields",
  "files_changed": [],
  "commit_sha": "",
  "success": false,
  "error_message": "Conflict markers remain in workspace-manifest.json after resolution"
}
```

## Fields

| Field               | Type     | Required | Description                                       |
| ------------------- | -------- | -------- | ------------------------------------------------- |
| `timestamp`         | string   | yes      | ISO 8601 UTC timestamp                            |
| `workflow`          | string   | yes      | GitHub Actions workflow filename                  |
| `repo`              | string   | yes      | Target repository name                            |
| `agent_type`        | string   | yes      | LLM model or script identifier                    |
| `decision`          | string   | yes      | Short decision label (e.g. bump-minor, skip, fix) |
| `reasoning_summary` | string   | yes      | One-line summary of why                           |
| `files_changed`     | string[] | yes      | List of files modified (empty on failure)         |
| `commit_sha`        | string   | yes      | Resulting commit SHA (empty on failure)           |
| `success`           | boolean  | yes      | Whether the action completed successfully         |
| `error_message`     | string   | no       | Error details (only on failure)                   |

## Produced by

- `scripts/audit/record-agent-decision.sh` -- appends a single record

## Consumed by

- Audit reports (aggregate agent activity per date)
- Post-incident review (trace what agents did)
