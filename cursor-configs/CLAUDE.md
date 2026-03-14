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
5. `unified-trading-pm/plans/PLAN_FORMAT.md` — plan format; **Cursor checkboxes** (`- [x]` / `- [ ]`) required on every
   todo

## Key Rules (Quick Reference)

- **Flat deps only** — every `pyproject.toml` has ONE list: `[project.dependencies]`. No
  `[project.optional-dependencies]` ever — not `dev`, not `test`, not any group. Never use `.[dev]` extras (e.g.
  `uv pip install -e .` not `uv pip install -e ".[dev]"`). Tests run locally, Cloud Build, Code Build, and GHA — all
  need all deps. Optional groups are pointless and create conflicts.
- `uv pip install` not `pip install`
- `ARG PROJECT_ID` +
  `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
  in Dockerfiles — never `python:3.13-slim` or `pip install uv`
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

## Local Development

Start the full stack locally with mock mode (no credentials needed):

```bash
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock    # start all UIs + APIs
bash unified-trading-pm/scripts/dev/dev-stop.sh                       # stop all
bash unified-trading-pm/scripts/dev/dev-status.sh                     # check status
```

### 5 Mode Axes

| Axis       | Env Var           | Mock value    | Real value      | Controls                           |
| ---------- | ----------------- | ------------- | --------------- | ---------------------------------- |
| UI data    | `VITE_MOCK_API`   | `true`        | `false`         | Client-side mock data vs API calls |
| UI auth    | `VITE_SKIP_AUTH`  | `true`        | `false`         | OAuth login requirement            |
| API data   | `CLOUD_MOCK_MODE` | `true`        | `false`         | Sample data vs real cloud          |
| API auth   | `DISABLE_AUTH`    | `true`        | unset           | Token validation                   |
| Mock state | `MOCK_STATE_MODE` | `interactive` | `deterministic` | Stateful vs stateless              |

### Presets

| Preset       | Flag              | Use case                                                                   |
| ------------ | ----------------- | -------------------------------------------------------------------------- |
| **ci**       | `--mode ci`       | CI smoke tests, deterministic (no cache persistence)                       |
| **mock**     | `--mode mock`     | Local dev/UAT (default), interactive state persists in `.local-dev-cache/` |
| **api-real** | `--mode api-real` | Test APIs against real cloud data                                          |
| **real**     | `--mode real`     | Staging-like, needs credentials + OAuth                                    |

### Cache Cleanup

```bash
bash unified-trading-pm/scripts/dev/dev-stop.sh --clean     # stop + wipe .local-dev-cache/
bash unified-trading-pm/scripts/dev/dev-start.sh --reset     # wipe cache + start fresh
```

### Quick Test Reference

| What                 | Command                                             |
| -------------------- | --------------------------------------------------- |
| Python quality gates | `cd <repo> && bash scripts/quality-gates.sh`        |
| UI tests (headless)  | `cd <ui-repo> && CI=true npm test -- --run`         |
| UI smoke build       | `cd <ui-repo> && VITE_MOCK_API=true npx vite build` |

UIs on ports 5173-5183, APIs on 8004-8016. Port registry SSOT: `unified-trading-pm/scripts/dev/ui-api-mapping.json`.
Vitest must use `pool: "forks"` (not threads) to prevent zombie node processes.

Full guide: `unified-trading-codex/08-workflows/local-dev.md`

## This is a Multi-Repo Workspace (NOT a monorepo)

Each subdirectory is an independent git repo. When editing, only commit to the target repo. Never run `basedpyright .`
from workspace root — always run per-repo with timeout.

## System-First Architecture (No Ad-Hoc Solutions)

The 67-repo Unified Trading System already covers every domain. Before implementing anything — feature, fix, refactor,
new capability — **look at the existing system first**. Do NOT build ad-hoc solutions, duplicate sources of truth, or
create unnecessary repos/files. If a library is missing a feature, ADD the feature to the library. If the library's
approach is wrong, FIX it. Never work around it.

Key repo mapping: events → `unified-events-interface`, schemas → `unified-internal-contracts` / `unified-api-contracts`,
cloud → `unified-cloud-interface`, config → `unified-config-interface`, market data → `unified-market-interface`,
execution → `unified-trade-execution-interface`, domain utils → `unified-domain-client` / `unified-trading-library`, UI
→ check existing 13 UIs first.

Full decision tree: `SUB_AGENT_MANDATORY_RULES.md` §0.

## Plan Format (Cursor Checkboxes)

When creating or editing plans in `plans/active/` or `plans/ai/`, every todo's first content line MUST start with a
Markdown checkbox: `- [x]` for done, `- [ ]` for pending. Format: `- [x] [SCRIPT] P0. Description...` or
`- [ ] [AGENT] P0. Fix...`. This ensures Cursor Plan Mode renders filled vs hollow circles correctly. See
`plans/PLAN_FORMAT.md` § Cursor-Friendly Todo Checkboxes.

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents (Task tool, mcp_task) and autonomous agents (GHA workflows, Claude Code `--print`, Cursor background agents)
start with FRESH context and do NOT inherit your rules. Reduced context makes them miss rules unless you explicitly
provide them.

**CRITICAL: Agents in `--print` mode CANNOT read files from disk.** Telling them "read .cursorrules" is useless — they
never see it. Rules MUST be pasted directly into the prompt text.

**When launching ANY sub-agent or autonomous agent:**

1. **For local scripts:** Use `inject-mandatory-rules.sh`:
   ```bash
   RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")
   ```
2. **For GHA workflows:** Load rules via `GITHUB_ENV` heredoc in a prior step, then prepend `${MANDATORY_RULES}` to the
   prompt.
3. **For Cursor/Claude Code sub-agents (Task tool):** Paste contents of
   `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the TOP of the prompt.
4. **If paste is impractical:** Include at TOP: "Before any action, read
   unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
5. **Always include:** WORKSPACE_ROOT path. For tests: `cd <repo> && bash scripts/quality-gates.sh` (per-repo .venv).
   Never .venv-workspace for pytest.
6. **If rules injection fails, the agent MUST NOT proceed.** Exit with error.

Never rely on sub-agents "inheriting" rules — they cannot. Always inject the full rules. **SSOT:**
`unified-trading-pm/scripts/agents/inject-mandatory-rules.sh`

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
