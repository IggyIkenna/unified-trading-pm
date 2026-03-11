# Unified Trading System — Claude Code Instructions

## Environment: Venv Split (SSOT: venv-usage-ssot.mdc)

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source \${WORKSPACE_ROOT}/.venv-workspace/bin/activate`     |

**Never** run `pytest` directly — uses wrong venv. Always use `quality-gates.sh`.

At session start, for general Python (not tests):

```bash
# WORKSPACE_ROOT = $UNIFIED_TRADING_WORKSPACE_ROOT or first workspace folder
source "\${WORKSPACE_ROOT:-.}/.venv-workspace/bin/activate"
which python  # .venv-workspace/bin/python
```

`.claude/settings.json` may prepend `.venv-workspace/bin` to PATH — if so, checks pass without manual activation.

## Rules: Read Before Coding

Read these before making ANY code changes:

1. `.cursorrules` — workspace standards (uv not pip, quickmerge not git push, etc.)
2. `.cursor/rules/no-empty-fallbacks.mdc` — no try/except fallback imports
3. `.cursor/rules/no-type-any-use-specific.mdc` — no Any types
4. `unified-trading-codex/06-coding-standards/README.md` — coding standards

## Key Rules (Quick Reference)

- `uv pip install` not `pip install`
- `bash scripts/quickmerge.sh "message" --agent` not `git push` — always use `--agent` in Claude Code sessions
- Two-pass model: `bash scripts/quality-gates.sh` first (Pass 1 — full), then `quickmerge --agent` (Pass 2 —
  lint/format/typecheck/codex, no tests, no act)
- **NEVER use `--dep-branch` in agent/Claude Code sessions** — it is a human-only flag. Quickmerge exits(1) if
  `--dep-branch` is combined with `--agent`. Branch is read automatically from `active_feature_branch` in
  `workspace-manifest.json` (currently: `live-defi-rollout`). Dep conflict? Commit dep repo first, then re-run.
- `from unified_events_interface import setup_events, log_event` — no fallbacks
- `basedpyright` not `pyright` (and always with `run_timeout 120 basedpyright <source_dir>/`)
- No `os.getenv()` — use `UnifiedCloudConfig`
- No `# type: ignore` to hide architectural violations — fix the root cause
- No `try/except ImportError` around library imports — fail loud

## Testing Infrastructure (Emulators & Mocks)

All tests run credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). Protocol-faithful emulators and mocks
replace live cloud services (see `unified-trading-pm/plans/archive/cicd_mock_hardening_2026_03_11.plan.md`).

**GCP Emulators** (auto-detected by SDK via env vars):

- Pub/Sub: `PUBSUB_EMULATOR_HOST=localhost:8085`
- GCS: `STORAGE_EMULATOR_HOST=http://localhost:4443` (fsouza/fake-gcs-server)
- BigQuery: `BIGQUERY_EMULATOR_HOST=localhost:9050`

**AWS**: `@mock_aws` decorator (moto) — no credentials, no emulator process needed.

**Network blocking**: `pytest --block-network` blocks all sockets; `@pytest.mark.allow_network` opts out.

**WS tests**: Use `MockWebSocketFeed` from `unified-market-interface/tests/fixtures/mock_ws_server.py`.

**DeFi tests**: Use `responses` library (`@responses.activate`, `passthrough=False`) for Hyperliquid REST.

**Local stack**: `bash unified-trading-pm/scripts/demo-mode.sh --seed` — no credentials required.

**Cassette parity**: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` — runs on every commit.

## This is a Multi-Repo Workspace (NOT a monorepo)

Each subdirectory is an independent git repo. When editing, only commit to the target repo. Never run `basedpyright .`
from workspace root — always run per-repo with timeout.

## Sub-Agents: Full Rules Required (MANDATORY)

Sub-agents (Task tool, mcp_task) start with FRESH context and do NOT inherit your rules. Reduced context makes them miss
rules unless you explicitly provide them.

**When launching ANY sub-agent:**

1. **Paste** the contents of `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the TOP of the prompt,
   OR
2. **If impractical:** Include at TOP: "Before any action, read
   unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
3. **Always include:** WORKSPACE_ROOT path. For tests: `cd <repo> && bash scripts/quality-gates.sh` (per-repo .venv).
   Never .venv-workspace for pytest.

Never rely on sub-agents "inheriting" rules — they cannot. Always pass the full rules.

## Analysis Rules

When analyzing codebase architecture:

- EXCLUDE: .venv*, venv/, node_modules/, build/, dist/, *.egg-info/
- EXCLUDE: Documentation files (\*.md) when counting code usage
- EXCLUDE: Shell scripts when analyzing Python patterns
- FOCUS: Python source files in service directories only
- Use: `--glob '!.venv*' --glob '!**/.venv*/**'` with ripgrep

## Correct search commands for architectural analysis

```bash
rg "pattern" --type py --glob '!.venv*' --glob '!build' --glob '!tests'
grep -r "pattern" --include="*.py" --exclude-dir=".venv*" --exclude-dir="tests"
```

## Workspace Configs (Canonical in PM)

- **Canonical:** `unified-trading-pm/cursor-configs/`
- **Symlink:** `.cursor/workspace-configs` → `unified-trading-pm/cursor-configs`
- **Setup:** `bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh`

**Workspaces:**

- `unified-trading-system-repos.code-workspace` — full (all 59 manifest repos)
- `workspace-libraries` — T0–T2 libraries
- `workspace-uis` — UI repos
- `workspace-trading` — execution, strategy, risk
- `workspace-data-pipeline` — instruments, market data, features
- `workspace-ml` — ML services
- `workspace-features` — feature services
- `workspace-infrastructure` — deployment, infra
- `workspace-complete` / `workspace-full-pipeline` — all repos

All paths use `${workspaceFolder}` — portable across users. Strict basedpyright (reportAny, reportUnknownMemberType,
reportUnknownVariableType = error).
