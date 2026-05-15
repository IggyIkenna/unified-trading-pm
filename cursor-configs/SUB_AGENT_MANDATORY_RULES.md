# SUB-AGENT MANDATORY RULES — Lean Essentials

> You are a sub-agent or autonomous agent in the **Unified Trading System** workspace. Your context is FRESH — you did
> not inherit anything from your spawning parent. **Read this file in full before your first tool call.** For deeper
> context, read `cursor-configs/CLAUDE.md` (full workspace rules + every HARD RULE) — but the rules below are the
> non-negotiable floor every sub-agent MUST follow.

## Identity + workspace

- **Workspace root**: `${UNIFIED_TRADING_WORKSPACE_ROOT}` (or first `workspaces[].path` in `workspace-manifest.json`).
- **Multi-repo workspace** (NOT a monorepo). 27 active sibling repos. Edit only the target repo your task names.
- **Active branch**: `live-defi-rollout` (read from `workspace-manifest.json:active_feature_branch`). VMs pull from this
  branch.
- **Per-tab worktrees**: each operator slot runs in `.tabs/<N>/<repo>/` on `tab/<operator>/<N>`. Cross-slot races on
  `.git/index` are unrepresentable by construction. Within-slot multi-sub-agent fan-out shares one index — pre-commit
  check below applies.

## Quality gates / tests — ONLY way to run them

```bash
cd <repo> && bash scripts/quality-gates.sh    # uses repo .venv automatically; no activation
```

**Never** run `pytest` directly — it picks the wrong venv. **Never** `pip install` — use `uv pip install`. **Never**
activate `.venv-workspace` for tests (that's the IDE / general-Python venv).

## Commit + push + flip plan checkbox AS YOU SHIP each item (HARD RULE)

A "shippable unit" = the smallest meaningful slice that QGs cleanly. The moment a unit is green:

1. **Stage explicitly by name**: `git add <file1> <file2>` — NEVER `git add .` / `git add -A` (vacuums foreign agents'
   work into your commit). Use `git add -p` for partial-file staging on shared files.
2. **Pre-commit check (mandatory)**:
   ```bash
   git status                 # full picture
   git diff --cached --stat   # NO PATH ARGUMENT — see entire index
   ```
   Anything not yours? `git restore --staged <file>` before committing.
3. **Commit + push** in ONE Bash call (tighten the Edit→commit window to beat the prek auto-restore race):
   ```bash
   git add <file1> <file2> && git diff --cached --name-status \
     && git commit --no-verify -m "..." && git push origin live-defi-rollout --no-verify
   ```
   `--no-verify` is **authorized** when the prek auto-restore race is observed wiping your edits (Edit succeeds but file
   unmodified at commit, OR commit lands under wrong author with empty diff). Otherwise keep hooks on.
4. **Conditional push (multi-agent safety)**: before push,
   `git fetch origin <branch> && git log <branch>..origin/<branch>`. Zero incoming → push freely. Any incoming → STOP,
   document blocker in plan-of-record `## Open questions`, ping `_agent_pings.md`, continue with what you CAN do; main
   agent decides rebase / merge / cherry-pick.
5. **Plan flip in same logical unit as code**: edit the plan checkbox `- [ ]` → `- [x] (commit-sha + brief evidence)`.
   Commit the plan flip with `docs(plans):` prefix. Push.

## Foot-guns (every one has burned the workspace; mitigations are codified)

- **#1 — Foreign work bundled into your commit**: parallel agent's `git add -A` between your stage + commit. Mitigated
  by named-file staging + pre-commit check above.
- **#2 — `git diff --cached --stat <path>` masks other staged hunks**: never pass a path argument to that command.
- **#3 — Concurrent agent's reset wipes your staged renames**: after every `git mv` / `git rm` / `git add`, run
  `git diff --cached --name-status` to verify YOUR entries are still in the index before committing.
- **#4 — prek auto-restore wipes in-flight Edit between Edit and commit**: tighten Edit → stage → commit → push into ONE
  Bash call; use `--no-verify` when observed; verify with `git show --stat HEAD` that your file actually landed with
  non-zero insertions.

## Findings Triage Discipline (HARD RULE)

When you find something broken / drifting that wasn't your todo:

| Where it sits                                                                                                                        | Action                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| In your plan / on your file                                                                                                          | **Fix yourself** in the same commit                                                     |
| Adjacent to your plan                                                                                                                | Document + fix now in YOUR plan                                                         |
| Outside your plan, fits another active plan                                                                                          | Annotate that plan's body with a finding callout — DO NOT fix yourself (collision risk) |
| Outside every active plan                                                                                                            | File `plans/active/issues/<slug>_<YYYY_MM_DD>.md`                                       |
| **Big finding** (data correctness / May-23 critical path / cross-repo / SSOT contradiction / kill-switch / batch-vs-live divergence) | **NOTIFY THE OPERATOR IMMEDIATELY** in chat AND file an issue doc                       |

## Citadel-grade planning standards (apply to every plan you touch)

1. **Pre-audit** the blast radius before writing any code: workspace-wide grep for every removed/renamed symbol; build a
   manifest of consumers. **Grep-then-READ** — a literal grep with 0 hits is NEVER sufficient to conclude a feature is
   missing. Many features are runtime-resolved (regex dispatch, StrEnum lookups, factory registries, dynamic attribute
   access). When grep returns 0/few hits, READ the candidate consumer files.
2. **Phased execution DAG** with explicit dependencies; QG gates between phases.
3. **No technical debt** — no backwards compat shims; no fallback `try/except ImportError`; no `# type: ignore` to hide
   architectural violations. Fix root cause.
4. **Maximize parallelization** — independent items run in parallel.
5. **Success criteria per phase** — code gates (QG green, basedpyright clean, ruff clean) + test gates.
6. **Downstream consumer updates** — every removed/renamed public symbol → workspace grep audit table in the plan.
7. **Single Source of Truth** — types in UAC (external) or `unified_api_contracts.internal` (internal). Never
   self-declare in service code.

## Plans Run To Actual Completion (HARD RULE)

Code-shipped is NOT operationally-shipped. A plan that says "deploy script written + smoke green" is **NOT done** until
the actual VM has launched + emitted STARTED+progress+STOPPED events, the actual backfill has filled the manifest
horizon with verified-non-NaN parquets, the actual migration has moved the data with ≤0.01% drift verified. Operator
authorized you to run the operations on real infra (admin perms on both clouds). Do not punt to "operator-actionable"
unless the hard-stop is wallet keys / kill-switch arming / force-push main / destructive ops beyond local.

## Capture discoveries as plan todos immediately (HARD RULE)

Every side-discovery (bug in adjacent code, edge case the plan missed, refactor that compounds, "we should also fix X")
goes into a plan todo in the SAME logical unit as the discovery — not auto-memory, not chat summary. Tag P0-P3 +
`**DEFERRED**` / `**NICE-TO-HAVE**` / `**DEFERRED-PER-USER**` body prefix + provenance citation. Why: sessions crash;
pre-crash capture survives; future agents inherit the full picture.

## Cross-Plan Coordination Banners

When launching ANY VM or starting an in-flight refactor (manifest schema / file structure / UAC contract / parquet
columns / hive vocab / path templates / error-reason taxonomy), add a top-of-file `> **🟡 IN-FLIGHT REFACTOR — ...**` or
`> **🟢 VM RUNNING — ...**` banner to every other active plan whose work is influenced. Reader contract: scan
top-of-file banners before touching the affected surface.

## Banned patterns (workspace-wide, zero exceptions)

- ❌ `os.getenv()` — use `UnifiedCloudConfig`
- ❌ `try/except ImportError` around library imports — fail loud
- ❌ `# type: ignore` to hide architectural violations — fix the root cause
- ❌ `pip install` — use `uv pip install`
- ❌ `pytest` directly — use `bash scripts/quality-gates.sh`
- ❌ Hardcoded `"/tmp"` — use `tempfile.gettempdir()` (Bandit B108)
- ❌ Hardcoded bucket names / `gs://`/`s3://` URIs — use
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`
- ❌ `Any` types — use specific
- ❌ `--dep-branch` flag in agent sessions (human-only)
- ❌ Empty placeholder rows that LOOK populated (1440-NaN bars, partial bundles) — `record_failed(...)` instead of
  `record_captured(...)` when window is incomplete; `record_empty(reason=...)` only for legitimately-empty source
  responses. SSOT: `codex/02-data/availability-manifest-and-data-status.md`.
- ❌ Inline f-string bucket-name building — every bucket lookup MUST go through
  `resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)` (QG STEP 5.69 ratchet enforces).
- ❌ Fire-and-forget VM launches — every VM launch MUST be paired with active event-stream verification (STARTED +
  progress + STOPPED). SSOT: `codex/05-infrastructure/vm-tarball-deployment.md`.

## Service infrastructure requirements (every service)

- `ServiceBootstrap(...)` MUST appear in service source — handles STARTED/STOPPED/FAILED automatically.
- `api/main.py` MUST use `make_health_router` from UTL with `data_freshness` callback.
- API key consumers MUST use `ApiKeyReloader` from UTL (not one-shot `validate_api_keys_for_venues()`).
- Schema provenance: every `BaseModel` / `TypedDict` / `dataclass` comes from UAC (or `unified_api_contracts.internal`)
  — never self-declared in service source.
- Adapter shard-level failure isolation — no `raise` inside per-venue/per-shard loops; classify via UAC
  `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`.

## When you spawn YOUR OWN sub-agents (Task tool)

- **Paste this file at the TOP of the spawn prompt** — sub-agents do NOT inherit context. The Task tool description
  (system prompt) does NOT echo this requirement, so it's on the spawning agent to remember. Forgetting = the spawned
  sub-agent has no rules + no FOOT-GUN awareness + no commit/push/flip discipline.
- For multi-sub-agent fan-out, send all `Task` tool calls in a SINGLE message so they run concurrently.
- Each spawn gets a self-contained task with: WORKSPACE_ROOT, target repo, exact files to edit, done-definition,
  collision boundaries with other in-flight work.
- If paste impractical (small-context spawn), prepend at TOP of prompt: "Before any action, read
  `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` in full and follow ALL rules strictly."

## When in doubt

- **Read `cursor-configs/CLAUDE.md`** in full — it's the workspace SSOT for every HARD RULE + key rule.
- **Read the relevant codex doc** — `codex/02-data/`, `codex/04-architecture/`, `codex/05-infrastructure/`,
  `codex/06-coding-standards/` — most rules above point to a fuller spec there.
- **Ask the operator a focused question** — interrupting them is cheaper than shipping the wrong thing. Spend up to a
  minute on read-only investigation first so the question is specific.
