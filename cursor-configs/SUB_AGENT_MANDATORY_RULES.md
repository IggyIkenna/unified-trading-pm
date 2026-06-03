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
cd <repo> && bash scripts/quality-gates.sh             # SHIP mode (default): autofix + check
cd <repo> && bash scripts/quality-gates.sh --no-fix    # DIAGNOSTIC mode: check-only, zero file modifications
```

**Never** run `pytest` directly — it picks the wrong venv. **Never** `pip install` — use `uv pip install`. **Never**
activate `.venv-workspace` for tests (that's the IDE / general-Python venv).

### Ship mode vs diagnostic mode (HARD RULE — choose intentionally)

| Intent                                                                                                                                                    | Command                                  | Behavior                                                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Deliberate tree-wide reformat** (you own everything AUTO-FIX touches)                                                                                   | `bash scripts/quality-gates.sh`          | `FIX_MODE=true` (default) → `[1/6] AUTO-FIX` runs `ruff format` + `ruff check --fix` **in-place across the WHOLE worktree** (not just your files), then LINT + TYPECHECK + TESTS. |
| **Diagnostic / observation** (memory profiling, exploring failures, "what would CI see")                                                                  | `bash scripts/quality-gates.sh --no-fix` | AUTO-FIX block **skipped**. Drift = fail. **Identical to CI behavior.**                                                                                                           |
| **CI** (`.github/workflows/quality-gates-v2.yml` — required check `quality-gates-v2`; v1 `python-quality-gates.yml` / `quality-gates` RETIRED 2026-05-29) | `bash scripts/quality-gates.sh --no-fix` | Same as diagnostic. Zero autofix. Drift = build fail.                                                                                                                             |

**Why this matters** — incident 2026-05-15: an agent ran `bash scripts/quality-gates.sh` (ship mode) for a
memory-diagnostic measurement. The AUTO-FIX block reformatted **350 unrelated files** in the worktree. The agent had to
manually `git restore .` to avoid leaking foreign formatting changes into a commit (which would have collided with
parallel agents editing the same files).

**The rule — decide by WHAT you will commit, not merely "am I committing" (AUTO-FIX rewrites the WHOLE tree, not just
your files):**

1. **You are only going to commit your OWN named files** (the normal per-unit ship —
   `quickmerge --agent --files '<paths>'`): **use `--no-fix`.** Ship mode would reformat unrelated / foreign files
   across the worktree → re-dirties the slot (breaks FF-sync) and risks leaking foreign formatting. Verify your files
   with `ruff check` + `basedpyright` + `pytest` on the touched paths; quickmerge then runs the gate it needs (Pass 1).
2. **You knowingly intend to "ruff up" other files and will own/commit whatever AUTO-FIX touches** (a deliberate
   tree-wide format pass, or a solo worktree where re-dirtying is fine): **ship mode is allowed**
   (`bash scripts/quality-gates.sh`, autofix ON) — that IS its purpose.

Anything else (measuring memory, reproducing a failure, exploring `pytest` output, verifying CI parity, ad-hoc gate
runs) → `--no-fix`.

(Note: `basedpyright` and `pytest` are check-only at all times — they don't have an autofix mode, so `--no-fix` only
affects `ruff`. The semantic match still holds: locally autofix drift, in CI prove zero drift.)

## Commit + ship + flip plan checkbox AS YOU SHIP each item (HARD RULE)

A "shippable unit" = the smallest meaningful slice that QGs cleanly. **Shipping CODE is a TWO-PASS model (staging-first,
live model 2026-06-02) — NEVER a raw `git push` of code:**

1. **Pass 1 — full quality gate writes the sentinel.** `cd <repo> && bash scripts/quality-gates.sh` MUST exit 0 on your
   current HEAD. On exit 0 it writes `.qg_last_passed_sha` (== HEAD). Skipping Pass 1 means the change never ran tests,
   and Pass 2 hard-refuses on the missing/stale sentinel.
2. **Pass 2 — `quickmerge` commits + opens the auto-merging staging PR.**
   ```bash
   bash scripts/quickmerge.sh "feat: ..." --agent --files '<path1> <path2>'
   ```
   ALWAYS `--agent` in Claude Code; ALWAYS scope with `--files` (named paths — NEVER the whole tree; that vacuums
   foreign agents' work). quickmerge verifies sentinel == HEAD, stages ONLY your `--files`, commits, and routes the unit
   `live-defi-rollout` → `staging` → SIT → `main` (→ Cloud Build image on `main`). It **early-exits "nothing to commit"
   on a clean tree**, so a forgotten `--files` ships NOTHING — and a raw `git push origin live-defi-rollout` of code
   silently piles up on LDR _behind_ main (it never opens a staging PR). `--dep-branch` is human-only.
   - **Pre-`--files` hygiene (mandatory)**: `git status && git diff --cached --stat` (NO path argument — see the WHOLE
     index) so you pass only YOUR paths. Foreign dirty files left out of `--files` stay untouched.
   - **prek auto-restore race**: if you must hand-commit (Edit succeeds but file unmodified at commit, OR commit lands
     under wrong author with empty diff), bundle Edit → stage-by-name → commit → push in ONE Bash call with
     `--no-verify`, then verify with `git show --stat HEAD` that your file landed with non-zero insertions.
3. **The ONLY sanctioned raw `git push origin live-defi-rollout` = dirty deps.** When a dep repo is dirty mid-edit,
   commit + push the dep directly to `live-defi-rollout` (do NOT quickmerge with dirty deps). The other sanctioned raw
   pushes are the ff-pull-in and the cross-repo PM plan-flip in step 5. **Everything else ships via quickmerge.**
4. **Conditional push (multi-agent safety)**: before any push,
   `git fetch origin <branch> && git log <branch>..origin/<branch>`. Zero incoming → push freely. Any incoming → STOP,
   document blocker in plan-of-record `## Open questions`, ping `_agent_pings.md`, continue with what you CAN do; main
   agent decides rebase / merge / cherry-pick. **Shared `.tabs/<N>/` worktree (a concurrent agent moves `HEAD` /
   `FETCH_HEAD` under you)**: verify ONLY against the stable remote ref
   (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`), never `FETCH_HEAD`, and promote YOUR commit via a
   throwaway worktree off `origin/live-defi-rollout` so the other agent is undisturbed. SSOT: `cursor-configs/CLAUDE.md`
   § "Concurrent agent in your shared `.tabs/<N>/` worktree".
5. **Plan flip in same logical unit as code**: edit the plan checkbox `- [ ]` → `- [x] (commit-sha + brief evidence)`.
   Commit the plan flip with the **MANDATORY `docs(plans):` prefix** (`plan(...)` is hook-rejected) + push. A plan-flip
   on a PM `*.md`/`*.mdc` is docs fast-path (PR targets `main`); the PM staging→main bypass + main-backmerge keep PM
   synced with no manual reconcile.

## Foot-guns (every one has burned the workspace; mitigations are codified)

- **#1 — Foreign work bundled into your commit**: parallel agent's `git add -A` between your stage + commit. Mitigated
  by named-file staging + pre-commit check above.
- **#2 — `git diff --cached --stat <path>` masks other staged hunks**: never pass a path argument to that command.
- **#3 — Concurrent agent's reset wipes your staged renames**: after every `git mv` / `git rm` / `git add`, run
  `git diff --cached --name-status` to verify YOUR entries are still in the index before committing.
- **#4 — prek auto-restore wipes in-flight Edit between Edit and commit**: tighten Edit → stage → commit → push into ONE
  Bash call; use `--no-verify` when observed; verify with `git show --stat HEAD` that your file actually landed with
  non-zero insertions.
- **#5 — Staging a QG-regenerated artifact**: `quality-gates.sh`/`quickmerge` regenerate gitignored artifacts every run
  (`*_DAG.svg`, `CI-CD-PIPELINE.svg/html`, `derived-dependency-manifest.json`, `coverage.xml`) + write the
  `.qg_last_passed_sha` / `.qg_content_sentinel` caches. These are gitignored — if one shows dirty/`??`, it is regen
  churn: **NEVER `git add` it** (named-file `--files` already protects you). If a generated artifact or sentinel is
  somehow tracked in your repo, `git rm --cached` + gitignore it. Generators must emit deterministically (`sorted()`
  sets before rendering) — a non-deterministic generator byte-churns its output every run.

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

**Declare your plan's TARGET SURFACE + check for overlapping open claims before you start (HARD RULE 2026-06-03).** In
your plan/todo, name the repo + file/symbol surface your work touches. Before starting, grep `plans/active/` for another
open todo claiming the same surface — if one exists you likely have a **semantic conflict** (two valid plans, work
collides) that no textual merge will catch; coordinate/reconcile or flag it first. Conflicts resolve in 3 layers (SSOT
`codex/08-workflows/ci-cd-flow.md` § "Convergence + conflict-resolution model"): **textual merge** →
conflict-resolution-agent; **semantic** → the per-VM review agent + the scripted cross-plan overlap detector → owning
epic-VM orchestrator; **hygiene** → plan-health-agent. You author on **LDR (fast, may be temporarily inconsistent)**;
reconciliation happens at the gated PR boundary (`staging` for service repos, the `main` PR for PM/codex) then
back-merges to LDR — so a `quality-gates.sh`-green commit is the per-repo boundary, not the final word.

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
