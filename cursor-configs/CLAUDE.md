# Unified Trading System — Claude Code Instructions

> **Lean index** of workspace rules. Each rule has a 1-line essence + a pointer to its full SSOT. When a rule applies,
> **read the SSOT pointer** — don't act from memory.
>
> Reworked 2026-06-02: 1180 → ~900 by relocating detail to codex SSOTs, then → ~955 by **folding in** the 5 former
> per-domain `.claude/rules/*.md` files (their unique rules were missing here + never reached repo-level agents). Net
> agent-loaded context dropped (those root files no longer load). Keep the sharp directive + 1-line pointer; these rules
> are NOT waste — they encode behaviours agents were missing; condense, don't drop.
>
> **Durable facts live HERE (one-liner + codex pointer), NEVER in agent "memory" (HARD RULE codified 2026-06-03)**:
> Claude `memory/` is per-cwd (a different store per tab/slot), local-only (never git-tracked, never reaches a VM or a
> teammate), and NOT inherited by sub-agents — so anything useful to another agent MUST land in this file (one-liner) +
> its codex SSOT (detail), not memory. "Already in codex" is NOT a reason to skip — migrate it as a one-liner + SSOT
> reference. Memory is reserved for session-local / personal (label Ikenna-vs-Harsh or macOS-vs-Linux deltas inline here
> instead) / secrets-adjacent state (procedures + Secret-Manager _names_ may live here; raw key/token VALUES never do).
> Sub-agents reach topic-parity via `SUB_AGENT_MANDATORY_RULES.md` (same topics, one-liner density). This header is the
> SSOT for the rule.
>
> **Size budget**: keep lean (~400–600 lines — not a hard floor). When a section outgrows its essence, push the detail
> to its codex SSOT + leave the directive + pointer here. Hard cap 1500/90KB (review-blocking).

---

## Model Tier Selection — Sonnet 4.6 (default) vs Opus 4.7 (escalation only)

**Default: Sonnet 4.6 / thinking: medium.** Escalate deliberately — not by default.

Three axes declared per slot and per spawn prompt:

- `model_tier: sonnet-doable | opus-required` — Opus only for main orchestrator, cross-repo architecture, >200k context
- `thinking: medium | high | max` — max always requires Opus; medium on Opus is always wrong
- Sub-agent Agent tool calls MUST set `model="sonnet"|"opus"` explicitly — never inherit

**Self-check at every task start (MANDATORY)**: read running model + declared tier + thinking. Sonnet on opus-required →
STOP. Opus on sonnet-doable → flag + proceed. Thinking mismatch → HARD STOP.

SSOT: `codex/06-coding-standards/model-tier-selection.md`.

---

## Environment: Venv Split (SSOT: `cursor-rules/venv-usage-ssot.mdc`)

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source ${WORKSPACE_ROOT}/.venv-workspace/bin/activate`      |

**Never** run `pytest` directly — wrong venv. Always `quality-gates.sh`.

**PYTEST_UNIT_DIR override** (per-family test layouts): some repos organise tests as `tests/<family>/unit/` rather than
the flat `tests/unit/` default. The default will only collect the root-level unit tests, silently skipping per-family
tests. To opt in, set `PYTEST_UNIT_DIR` BEFORE the `source base-service.sh` line in `quality-gates.sh`:

```bash
PYTEST_UNIT_DIR="tests/"   # collect all tests recursively (e.g. features-service)
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
```

Trigger: if `find tests/unit/ -name 'test_*.py' | wc -l` returns <5% of `find tests/ -name 'test_*.py' | wc -l` — the
per-family layout is almost certainly in use and this override is required. SSOT:
`codex/06-coding-standards/quality-gates.md` § "PYTEST_UNIT_DIR per-family override". Landed: PM@c7786b2f.

---

## Master Plan — Live DeFi Trading by 2026-05-23

Two DeFi archetypes (`carry_staked_basis` + `arbitrage_price_dispersion`) live on a real wallet ≥7 days by 2026-05-23.

- **Working plan**: `plans/active/master_to_live_defi_2026_05_23.md`
- **Codex SSOT**: `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`
- **Principle**: doc → plan → code. Drift between any pair is review-blocking. Readiness: 7 groups / 23 items (A-G).
- **Parallel workstreams ACTIVE**: TradFi (`epics/tradfi_master.md`), Sports (`epics/sports_master.md`), Predictions
  (`epics/predictions_master.md`) — separate codepaths, not blocked by DeFi gate. Allocate agent slots to these tracks.

---

## Rules: Read Before Coding

1. `.cursorrules` — workspace standards (uv not pip, quickmerge not git push, etc.)
2. `.cursor/rules/no-empty-fallbacks.mdc` — no try/except fallback imports
3. `.cursor/rules/no-type-any-use-specific.mdc` — no Any types
4. `unified-trading-pm/codex/06-coding-standards/README.md` — coding standards
5. `unified-trading-pm/plans/PLAN_FORMAT.md` — plan format; Cursor checkboxes (`- [x]` / `- [ ]`) required
6. `unified-trading-pm/codex/12-agent-workflow/canonical-plan-flow.md` — end-to-end audit → issue → plan → backlog →
   worker → ship loop (cron timings, silent-failure modes, hygiene scripts)
7. `plans/audit/README.md` — audit lifecycle; every epic has instructions in `plans/audit/instructions/`
8. **Asset-group vocabulary**: `asset_group` (not `category`). CLI `--asset-group`, envs
   `VM_ASSET_GROUP`/`MDPS_ASSET_GROUP`. Keys lowercase: `cefi`/`defi`/`tradfi`/`sports`/`prediction`. GCS hive-key:
   `asset_group=` canonical. Plan: `plans/active/venue_axis_asset_group_vocabulary_2026_04_25.md`.

---

## Key Rules (Quick Reference)

### Dependencies + builds

- Flat deps only — one `[project.dependencies]` per `pyproject.toml`. No extras.
- `uv pip install` not `pip install`.
- Dockerfiles: `ARG PROJECT_ID` +
  `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`

### Git discipline

- **Staging-first (live model 2026-06-02)**: `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` to ship a
  finished unit — quickmerge routes ALL commits → `staging` → SIT → `main`; `--to-staging` is a **no-op**. Never raw
  `git push` for CODE (quickmerge early-exits "nothing to commit" on a clean tree → direct LDR pushes silently pile up
  behind main). Always `--agent` in Claude Code.
- **Commit attribution = slot + host (so CI alerts + triage know WHO did what; codified 2026-06-03)**: every commit's
  author **NAME** carries the slot + host — `ikennaigboaka [slot-<N>·<host>]` (`<host>` = `laptop` / hostname on a
  workstation, the `vm-<id>` on a fleet VM; `<N>` from the `tab/<op>/<N>` branch) AND **email =
  `ikennaigboaka@gmail.com`** (the GitHub-attributed account). **⚠️ The per-repo email is currently WRONG fleet-wide**
  (slot-3 audit 2026-06-03: ~14 of 25 worktrees carry the `semver-rollout[bot]@users.noreply.github.com` email → **agent
  commits there masquerade as the semver bot**; ~7 carry `agent@ci.local` → unattributed) — so this is a STANDARDISE,
  not "leave unchanged". GitHub attribution + semver-agent bot/author checks key off the EMAIL (hence the bot-leak is
  dangerous); fixing name+email per-worktree makes `git log --format=%an` / the GitHub author column / CI
  `head_commit.author.name` correct + slot- aware (the gap that made cross-agent triage guess-work). Set per-worktree by
  `setup-tab-worktrees.sh` (do NOT hand-edit `~/.gitconfig`); manual fallback per slot worktree:
  `git config user.name "ikennaigboaka [slot-3·laptop]" && git config user.email "ikennaigboaka@gmail.com"`. SSOT +
  root-cause hunt: `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution".
- **LDR dual-path**: `live-defi-rollout` is the continuous-integration axis; a finished unit _promotes_ via
  quickmerge→staging. The ONE direct-LDR-push exception: **dirty deps** → commit + push directly to `live-defi-rollout`
  (do NOT quickmerge when dep repos are dirty). The other raw pushes are the ff-pull-in + cross-repo PM plan-flip.
- **PM/codex → `main` directly, NO staging (Option B, 2026-06-03)**: `unified-trading-pm` + `unified-trading-codex` are
  not deployed packages (PM is the SIT _debouncer_, not SIT-covered) → quickmerge routes their PRs to `main` (both docs
  AND scripts/workflows); the main PR's `quality-gates-v2` is the gate. PM has no `staging`; for PM **`main` is the
  reconciliation point** (does for plans what staging does for service repos). Convergence + 3-layer conflict model
  (textual=conflict-resolution-agent / semantic=reviewer+overlap-detector / hygiene=plan-health; **every alert → the
  orchestrator, not Slack-only**) SSOT: `codex/08-workflows/ci-cd-flow.md` § "Convergence + conflict-resolution model".
- **Quality gates BEFORE COMMIT — the commit IS the per-repo quality boundary (HARD RULE; tightened 2026-06-03,
  supersedes "before quickmerge")**: a **code** commit to the integration branch must be made from a
  `quality-gates.sh`-green tree — never on the strength of the light prek hook alone
  (ruff/format/gitleaks/conventional-commit). So `bash scripts/quality-gates.sh` must have exited 0 on HEAD's content
  before you `git commit` code, NOT merely before `quickmerge`. This already held on the quickmerge path (Pass-1 QG →
  Pass-2 commits); it now equally binds the direct **Commit+Push+Flip** path. Realize it cheaply via **QG-sweep
  batching** (run the gate ONCE over a batch → make per-shippable-unit commits from that green tree) — the gate is
  per-batch, not per-commit. **Scope**: binds commits that touch source the gate checks; pure doc / plan-flip / markdown
  commits (e.g. `docs(plans):` flips) take the prek hook only — full QG is a Python/source gate, not a docs gate. The
  sentinel `.qg_last_passed_sha` is written on any COMPLETE green run (fix-mode OR `--no-fix`; NOT gated on fix-mode),
  and quickmerge still verifies it. **Pass-1 MODE is a deliberate choice — AUTO-FIX (`ruff format`/`--fix`) rewrites the
  WHOLE worktree, not just your files (HARD RULE, two cases):**
  1. **Committing only your OWN named files** (the normal `quickmerge --agent --files '<paths>'` ship): format your
     files first (`ruff format <paths>`), then run **`bash scripts/quality-gates.sh --no-fix`** — full gate, writes the
     sentinel, **NO tree reformat**. Ship mode here would reformat unrelated/foreign files → re-dirties the slot, breaks
     FF-sync, risks leaking foreign formatting into your commit.
  2. **You knowingly intend a tree-wide reformat and will own everything AUTO-FIX touches** (a deliberate format pass /
     solo worktree): ship mode `bash scripts/quality-gates.sh` (autofix ON) is correct — that is its purpose.

  Pass 2 = `quickmerge --agent` (verifies sentinel == HEAD, skips redundant QG, opens the auto-merging `staging` PR) —
  it hard-refuses if the sentinel is missing/stale, so skipping Pass 1 means the change never ran tests. SSOT:
  `codex/08-workflows/ci-cd-flow.md` § "Two-Pass Workflow Model (the unit of work)".

- `--dep-branch` is human-only.
- **`git pull` rejected with `(would clobber existing tag)`** (stale local release tag vs semver-agent's canonical
  remote tag, e.g. `v1.0.0`/`v1.2.0`): fix with `git fetch origin --tags --force` (local-only; remote is canonical for
  release tags — never force-push tags the other way), then `git pull --ff-only`. SSOT:
  `codex/05-infrastructure/per-tab-worktrees.md` § "Step 7 — troubleshooting".
- **Quickmerge behind-remote (multi-agent)**: STAGE 0.4 Not-Behind Gate auto-reconciles (ff → rebase-autostash) and, on
  a genuine same-file conflict, `rebase --abort`s (work intact — **never overwrites/blind-merges**) + BLOCKS exit 1
  (`QUICKMERGE_ALLOW_BEHIND=1` emergency-only). On the block, reconcile per the autostash-conflict recipe above
  (preserve peer commits → stash YOUR files by name → `pull --rebase` → reconcile essence → re-QG → re-quickmerge) —
  never blind-overwrite a diverged same-file integration branch. PM-as-a-repo uses the same gate. SSOT:
  `codex/08-workflows/ci-cd-flow.md` § "STAGE 0.4 Not-Behind Gate"; structured `QUICKMERGE_BLOCKED` contract tracked in
  `plans/active/qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md`.
- **Full operator deployment flow** (dev → staging → main + paper → live strategy promotion):
  `codex/08-workflows/deployment-flow.md`.
- **agent-orchestrator branch model — TRANSITIONAL (operator decision 2026-06-02 supersedes the 2026-06-01 `main`-direct
  exception)**: the target is for `agent-orchestrator` to follow the **same** `tab/<op>/<N>` → LDR → `staging` → SIT →
  `main` flow as every other repo. **AO slot branches already track `origin/live-defi-rollout` like every repo** — the
  former `agent-orchestrator`→`main` base override was REMOVED (it made every AO slot read as diverged; do NOT re-add it
  in `workspace-manifest.json`, `setup-tab-worktrees.sh`, or `worktree_clean_check.base_branch_for_repo`). **Still
  mid-migration**: AO has no `staging` branch and no `quickmerge.sh` yet (tracked in
  `plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md` § G6 — BLOCKED-OPERATOR, since
  creating `staging` fires a fleet backend restart). So `main` is the deploy/CICD target reached via the
  LDR→`staging`→SIT→`main` path; until `staging` lands, `main` legitimately lags LDR (do NOT treat `main`-behind-LDR as
  drift; the `tab-mirror` GHA FF's tab→LDR). Once G6 lands `staging` + quickmerge, the path is fully standard. SSOT:
  `codex/04-architecture/agent-orchestrator-overview.md` + the G6 plan above.

### Imports + types

- `from unified_trading_library.events import setup_events, log_event` — no fallbacks.
- `basedpyright` not `pyright`; always `run_timeout 120 basedpyright <source_dir>/`.
- No `os.getenv()` — use `UnifiedCloudConfig`. No `# type: ignore`. No `try/except ImportError`.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)`.
- No hardcoded `"/tmp"` — use `tempfile.gettempdir()`. SSOT: `codex/06-coding-standards/quality-gates.md`.
- **Lazy-import heavy ML deps** (`optuna`/`sklearn`/`lightgbm`) INSIDE the methods that use them, never module-level —
  UTL loads via the `__init__` chain in every service, so a module-level ML import crashes non-ML repos (e.g. the API
  gateway). SSOT: `codex/06-coding-standards/README.md` § imports.
- **`pyrightconfig.json` silently overrides `pyproject.toml`** — when both exist, basedpyright reads ONLY the former's
  excludes/severities; mirror excludes into it or delete it. SSOT: `codex/06-coding-standards/quality-gates.md` § "Type
  Checking Standards".

### Service architecture

- **instruments-service** for reference data, not MTDS. MTDS is market data only.
- **IS→MTDS contract**: instruments-service owns all venue URLs/universe via `InstrumentRecord`; MTDS handlers derive
  URLs from IS, never hardcode. Three QG steps enforce (STEP 5.70): `no_silent_absence_handlers.sh`,
  `no_hardcoded_venue_urls.sh`, `no_hardcoded_venue_universe.sh`. SSOT:
  `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`.
- Shard-level failure isolation — no `raise` inside per-venue/per-shard loops. SSOT:
  `codex/04-architecture/shard-level-failure-isolation.md`.
- Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`.
- Service CLIs: `--operation` (what) `--mode` (batch/live) `--asset-group` (domain). SSOT:
  `codex/06-coding-standards/cli-convention.md`.
- **Feature formula versioning** (delta_one): every parquet in `features-delta-one-{ag}-{pid}` carries
  `feature_group_version` as a (1) HIVE PARTITION KEY in the GCS path
  (`.../feature_group=X/feature_group_version={N}/timeframe=Y/day=Z/instr.parquet`)
  - (2) file-level parquet footer metadata (`feature_group_version` / `feature_column_versions` JSON / `feature_group`).
    NO per-row column (path-partitioning beats per-row at millions-of-files scale — selective reads list paths instead
    of scanning every file). Group version resolves as
    `max(spec.formula_version for spec in get_specs_by_group(group))`. Registry SSOT:
    `features_service/delta_one/app/features/registry.py` (1,382 specs / 34 groups). CLI:
    `features-status [--detailed|--group X|--next N|--export csv|markdown|--check-drift]`. Bump formula_version on MATH
    change only (NOT config — RSI_14 vs RSI_18 is config). SSOT: `codex/02-data/feature-formula-versioning.md`.

### Manifest + honest absence

Manifest v5+: 4-state `capture_status` (`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`). Three
"missing" categories: expected → `record_empty(reason=<typed>)`; unexpected → `DependencyError(fail_fast=True)`;
schema-drift → RAISE LOUD. Never emit silent placeholders. **Canonical schema = v9 workspace-wide** (`_index` 8→9 adds
`source`/`asset_group`/`pipeline_mode`, bundled into each AG's single canonicalisation walk — coordinated by the
`*_manifest_canonicalisation_2026_06_01.md` plans); **trust the actual `schema_version` distribution, never the
constant**.

- `EmptyConfirmedReason` is a closed set (UAC `EMPTY_CONFIRMED_REASONS`); blank reason → `LegacyBlankErrorReasonError`.
- Cluster validation MANDATORY at `record_captured()` for bundled data_types (else `MissingClusterValidationError`).
- **`source=` provenance is CROSSCUTTING — all asset_groups, not TradFi-only** (operator-confirmed 2026-06-01;
  supersedes the prior TradFi-only framing). The same logical metric arrives from >1 source over time, so disambiguate
  with a **row-level `source` column + a per-source manifest row** (NOT a hive path key); `record_captured(source=...)`
  REQUIRED for every captured cell (even single-source today, for swap-resilience); raise `MissingSourceError` when
  blank or not in `SOURCE_PRIORITY[(asset_group, data_type)]`; resolve downstream via
  `select_primary_available_source()` (multi-source union: ≥1 `captured` → cell `captured`). Computed/service-only
  outputs are exempt. Today only `tradfi` is wired (`databento`/`massive`, QG STEP 5.64); cefi/defi/sports are RED gaps;
  prediction N/A. SSOT: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`.
- `available_at` is per-row write-time (UTL asserts). Service-output emission via `_resolve_policy_output_data_type` +
  `_publish_emission_check`.
- **Single-walk discipline (HARD RULE)**: the Phase 2.2 migration walks every parquet ONCE — any new whole-corpus GCS
  walk is review-blocking; bundle schema/partition/rename changes into it.

SSOT: `codex/02-data/availability-manifest-and-data-status.md` + `codex/02-data/honest-absence-downstream-handling.md`
(reason taxonomy + per-service / per-reason consumer policy).

### Shard-granularity SSOT (CRITICAL)

Shard atom MUST be identical across writer atomicity, manifest row key, data-status display, downstream pre-flight gate,
deployment-UI drilldown. Drift = silent correctness bug. 4-pillar validation: row count > 0 OR `record_empty`; NaN ratio
< threshold; schema matches contract; cluster coverage ≥ expected. SSOT: `plans/epics/infrastructure_master.md`.

### Live = batch (CRITICAL)

Live and batch are operational modes of the SAME pipeline. Identical schemas, data_types, fields. Banned: separate
live-only data_types; distinct field sets; deriving `available_at` at read-time. SSOT:
`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`.

### Bucket-name SSOT

Every bucket lookup via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — never inline
`gs://` f-string. `deployment-service/configs/cloud-providers.yaml` is canonical. QG STEP 5.69 enforces. SSOT:
`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`.

### UI changes — playwright gate (HARD RULE — codified 2026-05-23)

Any todo touching `unified-trading-system-ui` or `deployment-ui` MUST NOT be ticked `- [x] ✅` without: (1) tag `[UI]`
appended to role tag; (2) **`pw:L2 ✓`** — `npx playwright test --project=chromium tests/smoke/` exits 0; (3)
**regression guard cited** — spec path in `tests/e2e/`, `tests/playbooks/`, `tests/widgets/`, or `tests/smoke/`
written/updated to catch reverting the change. Evidence format: `— repo@sha | pw:L2 ✓ | regression: tests/path/spec.ts`.
Reviewer rejects ticks without `pw:` + `regression:` evidence. Todos on fleet VMs without a dev server stay
`[BLOCKED-PLAYWRIGHT]` until a UI-capable slot verifies. SSOT: `plans/PLAN_FORMAT.md` § 9 +
`codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement".

### Other key rules

- **Inherited-dirty-WIP — liveness-gated, role-aware (HARD RULE)**: a slot worktree is exclusively that slot's → dirty
  content is usually a dead prior session of you → **inherit** (`chore(orphan-wip)` + push). Discriminator is **LIVENESS
  not identity**: dead/expired `.agent-claim` → inherit; a DIFFERENT live session's fresh claim OR a file with mtime
  <120 s (live editor) → **PROTECT, never stomp**. Background worker → `notify_*` + inherit on TTL expiry; interactive →
  ASK first. Never `git add -A` a wiped/mass-delete index (FM2 guard). Slot base is `live-defi-rollout` for every repo.
  SSOT: `codex/05-infrastructure/per-tab-worktrees.md` + `agent-orchestrator/server/worktree_clean_check.py`.
- **Sports GCS paths**: `unified_api_contracts.sports.candidate_parquet_paths()` in
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Coverage: `clip_dates_to_source_coverage()` +
  `is_in_known_gap()`.
- **VIX 15m**: Barchart preload + Yahoo rolling 60d + honest gap. Massive does NOT cover VIX/VX futures — gap remains
  Barchart+Yahoo post-dual-source (tradfi_massive_dual_source_2026_05_28.md verified 2026-05-30). UAC constants in
  `registry/data_source_continuity.py`.
- **Manifest phantom audit**:
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group X --dry-run`. Do NOT write empty
  parquets to mask phantoms. **After a GCS path migration, large phantom counts are usually false positives** — verify
  `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` covers the new path shape BEFORE any `--apply` (running `--apply` on false
  positives flips real `captured` rows → `attempted_failed`); fix templates + re-run. SSOT:
  `codex/02-data/pipeline-mode-partition.md` § Axis-10.
- **Manifest consolidator runtime**: Cloud Run Jobs + Scheduler (GCP) / Batch Fargate + EventBridge (AWS) — NOT a VM
  (legacy GCE launcher DELETED 2026-05-20; do not relaunch). TF:
  `deployment-service/terraform/{gcp,aws}/manifest_consolidator_scheduler.tf`. **Liveness (live)**: read path loud-fails
  by DEFAULT on a stale/missing index when per-VM shards exist (`ManifestConsolidatorStaleError`;
  `MANIFEST_ALLOW_STALE_FALLBACK=true` to opt into recovery merge); watchdog emits `CONSOLIDATOR_DOWN`;
  `assert_consolidator_healthy(bucket)` is the shared preflight gate. SSOT:
  `codex/05-infrastructure/manifest-consolidator-ssot.md`.
- **VM tarball**: `bash deployment-service/scripts/vm/create-code-tarballs.sh`. SSOT:
  `codex/05-infrastructure/vm-tarball-deployment.md`.
- **VM launchers**: all `gcloud compute instances create` live in `deployment-service/scripts/vm/`; VM name's first
  segment must be in `VM_PREFIX_TO_BUCKET` (`vm_zombie_watchdog.py`) with a `lifecycle_class`
  (`EPHEMERAL_BATCH|EPHEMERAL_EXPERIMENT|SCHEDULED_RECURRING|LONG_LIVED_LIVE`); experiment VMs embed the run_id
  (`exp-{ml,strategy,execution}-{uuidv7}-{ts}`). **Zone** default `asia-northeast1-c`; stockout falls back within-region
  only (`-b`/`-a`), NEVER another region (all GCS data is in asia-northeast1).
- **No fire-and-forget VM launches (CRITICAL)**: STARTED within 60s + ≥1 progress/hour + STOPPED/FAILED at exit. Verify
  at T+10min post-launch (deployment registry heartbeat + `gcloud instances describe` = RUNNING). SSOT:
  `codex/05-infrastructure/vm-tarball-deployment.md` § "Post-launch verification — T+10min check".
  - **Pre-migration drain (GCS migration gate — HARD RULE)**: before ANY bucket SSOT cutover or GCS migration, ALL
    running VMs across BOTH GCP + AWS fleets MUST be gracefully stopped and manifest consolidated first. Recipe:
    inventory via `vm_zombie_watchdog.py` + per-prefix SIGTERM + wait for STOPPED event + run manifest consolidator +
    snapshot to `_index/snapshots/pre_migration_<date>.parquet`. SSOT:
    `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0 Stage 0.
- **Per-VM shard isolation**: `VM_NAME=<unique-tag>` + `MANIFEST_PER_VM_SHARDS=true`. QG STEP 5.66 enforces.
- **GCS object ops in migration scripts**: use `unified_trading_library.cloud_interface.gcs_copy_object` /
  `gcs_delete_object` / `gcs_describe_object` — never subprocess `gcloud`/`gsutil` for per-object ops. 250× faster (REST
  API ~100ms vs CLI ~500ms; GIL released → true thread parallelism at workers=32). SSOT:
  `codex/05-infrastructure/gcs-object-operations.md`.
- **Agent-orchestrator auth (HARD RULE; updated 2026-06-01)**: two distinct keys, never collapsed. Operator dashboard
  login JWT = HS256 `ORCHESTRATOR_JWT_SECRET` (central VM only, never on a worker). Internal central↔worker proxy token
  = **ES256 asymmetric** (**HS256 RETIRED 2026-06-01**; all VMs sign ES256, private key via the restricted creds
  bucket). Central terminates the operator JWT at the perimeter + mints a short-lived internal token upstream; operator
  JWT never reaches a worker. Regression symptom: login 200 but `/api/backends` 401s. SSOT:
  `codex/04-architecture/agent-orchestrator-overview.md` §Auth + §"Auth — long-lived setup-tokens";
  `codex/12-agent-workflow/orchestrator-multi-vm-topology.md`.
- **Agent-orchestrator accounts auth via setup-tokens only**: each account in `accounts.json` uses its own
  `oauth_token_env_file` (`~/.claude-accounts/<id>.env`, a `claude setup-token`); **never copy
  `~/.claude/.credentials.json`** (the legacy `.credentials.<id>.json` / `swap_claude_account.sh` path is removed).
  SSOT: `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`.
- **Orchestrator backlog is plan-driven + regen-authoritative (HARD RULE)**: backlog tasks auto-derive from `- [ ]`
  checkboxes in `plans/active/*.md` via `server/regen_backlog_from_plan.py` — **never hand-add to `backlog.yaml`**
  (write the todo in the plan; next `PlanRegenLoop` tick / `POST /api/backlog/regen` pulls it; hand-edits only TUNE
  derived tasks). `yaml`+`state.db` reflect ONLY open plan checkboxes (`ORCHESTRATOR_REGEN_PRUNE_STALE=true` default —
  no zombies; ±5 drift → `verify_fleet_prune_state.sh`). SSOT: `server/regen_backlog_from_plan.py` +
  `agent_orchestrator_backlog_state_alignment_2026_05_29.md`.
- **Fanning out work = a tracked plan todo — the todo IS the dispatch (HARD RULE)**: any "a slot should do X / fan out /
  hand off / out of scope for me" is NOT real until it's a `- [ ] [CATEGORY] P<n>. …` todo in a PM active plan with the
  **target repo named** + cold-start context (worker reads `SUB_AGENT_MANDATORY_RULES.md`). Banned: verbal/chat
  dispatch, or marking an audit "done" with follow-ups only described. **Grep `plans/active/` to verify** before ending
  a session that found fan-out work.
- **Workflow-capable `GH_TOKEN` everywhere** (each slot + operator + every VM worker):
  `source scripts/workspace/load-gh-token.sh` (GH*PAT from SM, carries Workflows:write). The keyring
  `gho*`token lacks the`workflow`scope → silently refuses workflow-file pushes via`gh`-API/HTTPS (SSH `git`push is exempt);`verify-slot-host-symmetry.sh`
  probes + fails a host lacking it.
- **Orchestrator runtime self-heals (defaults ON, fleet-wide)**: **AutoSpawn** wakes an idle slot when queue>0 + no
  active worker + headroom>50% (`ORCHESTRATOR_AUTOSPAWN_ENABLED`; manual `/api/slots/<id>/spawn` only for cold-start);
  **host-offline FAILOVER** (vm-orchestrator ONLY — multi-VM races) reroutes soft-pinned tasks when a host is silent
  > 10 min, hard pins (`failover_allowed: false`) stay, auto-rolls-back on return (`ORCHESTRATOR_FAILOVER_ENABLED`);
  > **WorkerLivenessWatchdog** kills stuck-at-prompt / heartbeat-silent(>900 s) / context-full workers every 60 s then
  > AutoSpawn respawns (`ORCHESTRATOR_WORKER_WATCHDOG_ENABLED`; per-slot 5-min cooldown + 20 kills/day/VM cap; never
  > kills a `blocked` or extended-thinking slot) — **operator must NOT manually kill tmux to restore velocity**. SSOT:
  > `codex/04-architecture/agent-orchestrator-overview.md` §Auto-spawn / §Watchdog / §Failover.
- **Temporary state must have a named successor plan** in `## Temporary states + their canonical follow-up plans`.

### Two teammates × multiple parallel agents (CRITICAL)

**Per-tab worktrees now isolate every worker** (`.tabs/<N>/<repo>` on `tab/<op>/<N>`), and execution runs on the
**orchestrator VMs** — Ikenna + Harsh author/audit plans locally, the orchestrator assigns them to VM workers, and all
code / quality-gates / quickmerge happen there. That isolation has **largely solved** the old shared-tree collision
class: you rarely share a tree with another live agent. The file-ownership discipline + the rare edge-case recoveries
still apply — full step-by-step recipes live in `codex/05-infrastructure/per-tab-worktrees.md` (§ "Step 7 —
troubleshooting", § "Isolated-worktree promotion under shared-worktree ref races", § "Foot-gun mitigations vs.
shared-tree model"). The invariants that must stay in-head:

- **Don't edit unfamiliar files.** Untracked / mid-edit-dirty / recently-pushed = someone else's in-flight work.
  **Untracked file in a dep repo = NOT YOURS.** QG fails on a file you don't own → tell the user.
- **Never** `git checkout origin/<branch> -- .` (dumps remote work) or `git checkout -- <file>` /
  `git checkout HEAD -- <file>` on a dirty file you don't own — UNRECOVERABLE.
- **Verify your work against the stable remote ref, never `FETCH_HEAD`** (it lies under a concurrent session):
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` / `git cat-file -e origin/live-defi-rollout:<path>`.
- **Slot tab branch diverged from LDR → quickmerge re-tangles + the tab→LDR mirror jams (recovery, codified
  2026-06-03)**: if `origin/tab/<op>/N` is NOT an ancestor of `origin/live-defi-rollout`
  (`git merge-base --is-ancestor origin/tab/<op>/N origin/live-defi-rollout` fails), quickmerge's mid-run sync
  re-applies LDR's commits as **patch-id DUPLICATES** on top of yours on every run (symptom: "3 ahead / 2 behind",
  brand-new SHAs each attempt, your changes bounced back to the working tree). Fix:
  `git rebase origin/live-defi-rollout` (drops the duplicates — "skipped previously applied commit"), then
  `git push --force-with-lease origin HEAD:tab/<op>/N` to realign the remote tab branch onto LDR. This is the
  `slot-master-rebase.sh` operation by hand; safe (own slot branch + `--force-with-lease`). Verify with
  `git merge-base --is-ancestor origin/live-defi-rollout HEAD` (true = mirror can FF again).
  - **Align = the MERGED COMBINATION, never "take mine" / "take theirs" (codified 2026-06-03)**: the rebase replays YOUR
    commits onto current LDR; on each conflict keep **BOTH sides' genuine work** (additive plan/doc/code), and where two
    agents independently wrote the **same** rule/fix, MERGE into the single best version (don't keep redundant
    duplicates). **Then VERIFY content survival** — grep your key additions AND the incoming ones in the rebased file
    before pushing (an em-dash / wording mismatch can read as "lost" when it survived; a real drop must be caught here).
  - **`--force-with-lease` is BRANCH-TIP safety, NOT content safety (HARD distinction)**: it only refuses the push if
    the remote `tab/<op>/N` moved since your fetch (catches a concurrent push to YOUR branch) — it does **NOT** inspect
    files or whether anyone had work on them. What actually protects OTHER agents' work is (a) rebasing **onto** current
    LDR so their commits are your BASE (not overwritten), (b) the conflict-merge keeping both, (c) the post-rebase
    verify. Safe here only because the tab branch is yours alone + you rebased onto (not discarded) LDR. **NEVER
    force-push a shared branch (`live-defi-rollout` / `main`).** Caveat: all fleet commits share the `ikennaigboaka`
    identity, so a foreign commit on your tab branch is invisible by author — read the messages (the [slot·host] author
    tag above fixes this).
- **Autostash conflict on rebase** (`Applying autostash resulted in conflicts`) → `git rebase --abort` (state safe,
  autostash intact), stash only YOUR files by name, redo — **NEVER** `git checkout HEAD -- <file>` then `git stash drop`
  (destroys the foreign agent's only WIP copy). § "Step 7" above.
- **Rare — a concurrent session shares your slot's `.git`** → promote your commit via a throwaway worktree off the
  integration branch, never touching the shared tree. § "Isolated-worktree promotion" above.

### Clear context = implement, don't ask

When plan / SSOT name the canonical approach, **ship it**. Don't apply when destructive, foreign files involved, or plan
says "AWAITING USER DIRECTION."

### Promote Workflow Path (May-23 dual-track)

- **PRIMARY = CLI**: operator runs `e2e-testing/scripts/defi/run-paper.sh` → `colocated_engine.py` → `run-live.sh`
  (safety net).
- **SECONDARY = UI**: Promote button → `POST /api/promote/{strategy_id}/{manifest_id}` → `MinimalCandidateManifest` in
  Firestore → paper/live VM auto-launch → DART `ManualTradeGateDialog` for first 3 trading days.
- **DO NOT** enrich `MinimalCandidateManifest` with pinned shas / model refs / features manifest version before May-23 —
  post-cutover scope (named successor: `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`).
- Firebase `execution-full` enforcement is at UI layer for May-23; backend Firebase integration is post-cutover.
- Valid promote targets May-23: `paper_1d` → `live_early` only. `live_full` is post-cutover.
- SSOT: `codex/04-architecture/promote-workflow-architecture.md` + `codex/09-strategy/operational/cli-promote-paths.md`.

---

## Cross-Cutting Rules (docs · code-quality · agent-behavior · Python · UI · PM)

Folded 2026-06-02 from the per-domain `.claude/rules/*.md` files (now tombstoned, operator removes from disk — they were
workspace-root-only + untracked, so these rules never reached repo-level agents; now they propagate via this one SSOT).

### Docs + code quality

- **No summary docs.** Never create `*_SUMMARY.md`/`*_STATUS.md`/`READY_TO_*`/`COMPLETION_*`/`FINAL_*`. Docs only if
  explicitly requested or they're specs (architecture/API/schema). Finish a task → respond with text, not a recap file.
- **Prettier before commit** on `.md`/`.json`/`.yaml`/`.ts`/`.tsx`/`.css`: `npx prettier --write <file>`.
- **Delete deprecated code.** No parallel old+new paths; no backward-compat shims / re-export stubs / `_old.py` /
  `# deprecated` (only exception: `__init__.py` public-API re-exports). Find consumers with `rg`, update all, delete
  old.
- **Never revert local changes** — no `git reset --hard`/`git clean -fd`/`git restore`/`git checkout` that discards
  uncommitted work; `git stash push -u -m` before a branch switch (on feature branches, local dep changes ARE the
  feature).
- **Runtime verification** — never claim "done" without running the code, waiting 8-10s, reading the terminal, grepping
  for errors. "Compiles" ≠ "works".
- **Plans live only under `unified-trading-pm/`** (`plans/active/` working · `plans/ai/` ephemeral · `plans/epics/` ·
  `plans/archive/`) — never in the workspace root, codex root, or a service's `docs/`.
- **Rollout tracking** — "plan complete" = ALL in-scope repos updated, OR scope explicitly limited with a pending list.

### Agent behavior

- **Context7 for external libs** — append "use context7" for React/Next/Tailwind/library/API questions.
- **Parallel agents** max 10 (different repos always safe; same file never). **Sub-agents** are ~10× cheaper + preserve
  context — use for multi-repo / 3+ steps / >100K-token reads; they return ONLY final results (≤400 tokens). (They start
  fresh + don't inherit rules — see § "Sub-Agents & Autonomous Agents" for the mandatory `SUB_AGENT_MANDATORY_RULES.md`
  paste.)
- **Rule-amnesia stop** — halt the session if an agent uses `os.getenv()` / `pip install` / direct `git push` /
  `setup_cloud_logging` / suggests skipping tests.
- **No `python3 << EOF` / inline-Python for file analysis** — catastrophic `re` backtracking caused two 12–22h runaway
  processes; use `rg`/`grep`, and if Python is genuinely needed wrap it in `timeout 30` + read line-by-line.
- **Background-task honesty** — NEVER report a backgrounded task (`run_in_background` Bash / sub-agent / workflow / VM
  launch) as "done" before seeing its actual exit/output; a `| tail`/`| head` pipe buffers → empty until completion, so
  "no output yet" ≠ "finished" (say "still running" + why); let `run_in_background` stream to a file, then read it with
  a SEPARATE call. Harness-tracked tasks auto-re-invoke on exit → rely on that completion signal, do NOT burn credits
  polling them. Poll ONLY genuinely external/untracked work (CI runs, remote VM jobs, deploys) at an interval matched to
  how fast that state changes. Write monitors that watch the RIGHT signal (correct log path + explicit done/terminated
  condition) with a generous fallback timeout, so they don't exit inconclusively and force a re-investigation.
- **Grep codex before asking the operator for committed numbers** — pricing/cost/revenue figures usually already exist
  in `codex/14-customer-journeys/commercial-model/`, plans, or memory; search all three + transcribe, don't block. Ask
  only after all come up empty. Composes with the "harvest from existing" discipline.

### Python service/library specifics

- **No pickle** (joblib/JSON/Parquet instead); no bare `except:`; no creds in repo. **`setup.sh`** mandatory +
  idempotent per repo. **File limits**: 900 lines max (warn 700) / function 200 / method 50 / class 900 / complexity 10
  / imports 30 / params 5 / coverage ≥70%.
- **engine/adapters/cli**: `engine/` has ZERO imports from `adapters/`; adapters <100 lines. **Singleton adapter**
  (`_ADAPTER_CACHE`, one per venue). **Concurrency**: I/O-bound MAX_WORKERS=16, CPU-bound 1-3; RAM 85%→reduce 50%,
  90%→emergency shutdown. **aiohttp** not `requests` in async code.
- **ConfigStore** from `unified_trading_services` for hot-reload runtime config. **IBKR** only via `ibkr-gateway-infra`
  (mock at the `ib_insync` object level — no HTTP VCR).
- **UTC datetimes always** — `datetime.now(timezone.utc)`; never `datetime.now()` / `datetime.utcnow()` /
  `datetime.today()`.
- **Cloud-agnostic I/O** — all storage/secrets via `get_storage_client()` / `get_secret_client()`
  (unified-cloud-interface); never `from google.cloud import *` or `import boto3` directly. Project-id env =
  `GCP_PROJECT_ID` (never `GOOGLE_CLOUD_PROJECT` / `GCP_PROJECT`); API keys from Secret Manager, never `os.environ`.
- **Event metadata** (`setup_events`/`log_event`, 11 lifecycle events) — `correlation_id` on coordination events,
  `duration_ms` on COMPLETED, `stack_trace` on FAILED, `client_order_id` on execution events.
- **Dep tiers** — T0 (no unified deps) → T1 (T0 only) → T2 (T0+T1); no circular imports. **CI test-in-image** — quality
  gates run INSIDE the Docker image; never git-clone source in Cloud Build.

### UI (TypeScript) specifics

- **No Python tools in UI repos** — tsc/ESLint/Vitest/Playwright, never uv/basedpyright/pytest/ruff. **TS strict**:
  `tsc --noEmit`, no `any`, no `@ts-ignore`, zero ESLint warnings.
- **Vitest `pool: "forks"`** (not threads — prevents zombie node procs); `CI=true npm test -- --run`. **Build smoke**:
  `NEXT_PUBLIC_MOCK_API=true pnpm build`. **UI is its own repo** — React/TS never inside a Python service repo.
  (Composes with the playwright gate above.)

### PM repo (`unified-trading-pm`, Level 0)

- SSOT template host (`setup.sh`/`quality-gates.sh`/`quickmerge.sh`/`version-bump.yml` copied to all repos) +
  `workspace-manifest.json` registry. NOT a Python package. `workspace-manifest.json` change → regen DAG SVG
  (`scripts/manifest/generate_workspace_dag.py`). Never push PM unless dependency-alignment passes
  (`check-dependency-alignment.py --json` → `"aligned": true`).

### Migrated operational one-liners (memory→CLAUDE.md SSOT-refs, 2026-06-03)

Cross-domain rules folded out of per-tab session memory; detail lives in the cited SSOT (read it, don't act from this
line):

- **HWM is never raw equity** — three simultaneous methods: TWR HWM (perf %), Notional HWM (transfer-adjusted native
  units), PnL Recovery (USDT for `pnl_based` accounts); never `max(equities)`, never convert a USDT recovery seed to
  BTC. Code: UTL `post_trade/hwm_invariants.py` + client-reporting-api `core/hwm_seeds.py`. SSOT:
  `codex/09-strategy/operational/pnl-attribution.md`.
- **Treasury/wallet hierarchy is keyed by `share_class`, not chain** (USDC/ETH/SOL/BTC) — DeFi 20% treasury / 80%
  hot-per-strategy-per-chain, CeFi 0/100, Sports no split; Copper MPC custody. SSOT:
  `codex/04-architecture/wallet-hierarchy-and-capital-flow.md`.
- **Never copy instrument definitions between dates** — instruments expire/list daily (CME futures/options); always
  re-run the instruments-service CLI for the specific missing date. Only static exception: CBOE VIX index.
- **Server-side Next.js API routes use `firebase-admin`, never the client SDK** — the client SDK reads
  `NEXT_PUBLIC_FIREBASE_*` and silently no-ops on UAT (route returns 200 with no write / empty `submissionId`). SSOT:
  `codex/08-workflows/client-onboarding.md` + `codex/05-infrastructure/firebase-split-topology.md`.
- **GCS canonical batch paths carry `pipeline_mode=batch_*/` LEFT of `asset_group=`** (Phase 3 done) — a prober hitting
  `raw_tick_data/by_date/day=*/asset_group=*/` without `pipeline_mode=` is on the OLD shape; reader-fallback probes both
  until Phase 8 (~2026-06-15) removes it. Sports uses `candidate_parquet_paths()` (unaffected). SSOT:
  `codex/02-data/pipeline-mode-partition.md`.
- **Bump `MAX_DURATION=600` over suppressing the QG `<300s` time check** — when a suite organically outgrows the budget,
  raise it (with a `#` comment on what grew); never deselect/skip slow tests (masks runaway regressions).
  `IGNORE_TIMEOUT=true`/`PYRIGHT_TIMEOUT` stay sanctioned for META-gate-only trips. SSOT:
  `codex/06-coding-standards/quality-gates.md`.
- **UTL-on-a-VM crash-cascade checklist** — pip-installing UTL on a VM also needs: (1) `cloud-providers.yaml` on disk +
  its env var, (2) `GCP_PROJECT_ID`/`PROJECT_ID`/`DEPLOYMENT_ENV_SHORT` exported (prod→prd/staging→stg/dev→dev), (3)
  `deployment_service` importable, (4) NO backticks inside the `STARTUP="..."` heredoc (shell command-substitution at
  launch). SSOT: `codex/05-infrastructure/vm-tarball-deployment.md` § "UTL-on-a-VM staging checklist".

---

## Service Infrastructure Requirements (QG-Enforced as ERRORS)

- **STEP 5.61** `ServiceBootstrap(...)` must appear in service source — handles STARTED/STOPPED/FAILED.
- **STEP 5.62** `api/main.py` with `make_health_router` from UTL + `data_freshness` callback.
- **STEP 5.34** `config_reloaders.py` uses typed config class — never `object` or `getattr(service_config, ...)`.
- **Schema provenance** — domain types from UAC (or `unified_api_contracts.internal`) — no local definitions.
- **API key hot-reload** — `ApiKeyReloader` from UTL, not one-shot `validate_api_keys_for_venues()`. SSOT:
  `codex/06-coding-standards/config-reloader-pattern.md`.

---

## DeFi Execution Architecture

Pointer chain. Full specs in codex:

- **Credential convention**: `codex/04-architecture/interface-credential-convention.md`. Trade:
  `get_order_adapter(venue, ...)`. DeFi: `connector.connect(config={...})`. Sports: `adapter(credentials={...})`.
- **RPC URL templates**: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`.
- **Flash loan receiver**: `deployment-service/contracts/FlashLoanReceiver.sol`. SSOT:
  `codex/04-architecture/flash-loan-receiver.md`.
- **Contract registry**: `unified_trading_library/config_interface/testnet_contracts.py` `TestnetContractRegistry` —
  validates `config/testnet_contracts.yaml` at load.
- **Uniswap live swap**: `UniswapConnector.swap_exact_input()` via SwapRouter02
  `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`.
- **DeFi error classification**: 35 codes in UAC
  `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode` (StrEnum; 13 Aave + 7 RECURSIVE*LOOP + 8
  HL*\_ + 2 ORACLE\_\_ + 5 CCTP; updated 2026-05-22). Routes on FAIL/RETRY/SKIP prefix. Full table in
  `codex/04-architecture/defi-execution-overview.md` § "Error Classification".
- **DeFi pipeline**: instruments-service → MTDS → features-onchain → strategy → execution.
- **Removed providers** (do NOT reference): Elysium, Arkham, Bloxroute, Infura, Kaiko, Polygon.io (TradFi data; Polygon
  L2 blockchain intact).
- **Pyth UNBANNED 2026-05-06** for Solana on-chain price feeds. Solana-only; other chains use Chainlink.
- **DeFi + CeFi hybrid (CRITICAL)**: DeFi = long/stake/lend leg (on-chain); hedge/short leg runs on CeFi perp venues.
  SSOT: `codex/09-strategy/architecture-v2/archetypes/`.
- **Custody**: Copper + CEFFU are June-1. May-23 ships on `CLOUD_KMS_ENCRYPTED`. SSOT:
  `codex/04-architecture/custody-providers.md`.

### Client funds isolation (HARD RULE codified 2026-05-20)

**Funds NEVER move between different clients.** Every transfer / withdraw / deposit / bridge / sub-account move /
rebalancing operation is scoped to a single `client_id` on the `TransferIntent`. Enforcement mechanism (2026-05-22
F-36/F-23 reconciliation — corrects prior "3 layers each raises" wording): (1) UAC structural guarantee —
`TransferIntent` carries a single `client_id: str` field (no separate source/dest fields), making same-client intent the
schema default; (2) execution-service `TransferCoordinator.execute()` (`transfer_coordinator.py:241`) raises
`CrossClientTransferForbiddenError` at consume time — the ONLY currently-implemented runtime raise; (3) strategy-service
`IntraClientRebalanceCoordinator` emit-time raise is PLANNED (Phase E.3) but not yet shipped. Full table:
`codex/04-architecture/client-funds-isolation.md`. Custody + legal boundary — each client is a separately-managed
account under its own custody / legal entity (Odum UK vs Cayman vs others). Plan proposals framing "cross-client
rebalancing" as in-scope are **review-blocking** — rewrite as "intra-client multi-portfolio" or "intra-client
multi-wallet" with explicit client_id invariant. **Valid usages of "cross-client"** are isolation-enforcement contexts
ONLY (`isolation_policy.assert_client_allowed()`, `CrossClientEventError` event-bus rejection, supervisor-level
read-only config visibility) — never fund movement. SSOT: `codex/04-architecture/client-funds-isolation.md`. Required
tests in every transfer-related plan: happy intra-client path + structural single-client_id validation +
defence-in-depth coordinator-rejects-cross-client + alert-on-attempt.

### Per-client isolation architecture (strategy-service + execution-service)

One subprocess per client (`multiprocessing.Process` under `StrategySupervisor`). Hard crash isolation
(segfault/OOM/uncaught in one ClientWorker does not affect others). `MarkPriceAggregator` lives in supervisor (single
MTM compute per tick, broadcast via shared memory). Hybrid hot-reload: push events for
`REGISTER`/`DEREGISTER`/`CREDENTIAL_ROTATED` + pull KMS rotation. Per-client preflight: KMS → venue auth ping → balance
fetch → `CLIENT_READY`; failure → `CLIENT_QUARANTINED`. GIL-free parallelism via subprocess boundary. SSOT:
`codex/04-architecture/per-client-isolation-architecture.md`. Composes with:
`codex/04-architecture/client-funds-isolation.md` (HARD RULE) + `codex/04-architecture/client-lifecycle-event-bus.md` +
`codex/05-infrastructure/strategy-shard-vm-topology.md`.

---

## Version / Workflow / Plan Governance

- **Version graduation**: `feat!` on 0.x.x = MINOR. **NEVER bump manually** — semver-agent handles all. Graduate:
  `gh workflow run request-major-bump.yml --repo IggyIkenna/<repo> -f proposed_version="1.0.0"` → comment `/approve`.
  Post-1.0.0: `feat!` = MAJOR.
- **PM/Codex fast-path**: plans/docs/cursor rules (`*.md`, `*.mdc`) → PR targets **main**. Scripts/workflows → PR
  targets **staging**.
- **Plan locking**: `locked_by: live-defi-rollout` + `locked_since: <date>` prevents archival without `[unlock-plan]` in
  commit. Agents may ASK to unlock; never unlock autonomously.
- **Plan archival (HARD RULE)**: Five mandatory steps before moving to `plans/archive/`:
  1. Scan for DEFERRED items; verify operations ran in production; migrate deferred items to active home with
     `**MIGRATED FROM:**`.
  2. Banner archived plan with `## Deferred work — migrated to:` listing each deferred item's destination plan.
  3. **Codex alignment check (added 2026-05-22)**: for every codex doc listed in the plan's `Codex SSOTs:` section, read
     the doc and verify it reflects what actually shipped. Update stale rows/sections in place. If a codex doc was
     promised but never written, write the stub or full doc now. If a codex doc was invalidated, add `SUPERSEDED`
     banner. Plans referencing codex docs that are stale relative to what shipped are **review-blocking until
     corrected**.
  4. Update CLAUDE.md/codex if the archival introduces a new workspace contract (new invariant, new canonical path, new
     tooling pattern).
  5. Remove `locked_by:` frontmatter or add `[unlock-plan]` in commit message if plan was locked.
- **Workflow templates**: SSOT `unified-trading-pm/scripts/workflow-templates/`. Never edit per-repo copies — edit PM
  template + run `rollout-workflow-templates.sh`.
- **Force-sync warning**: `admin-force-sync-all-to-main.sh` overwrites remote main — can revert semver-agent bumps. Run
  `run-version-alignment.sh` first.

---

## Testing + Local Development

**Tests**: credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). GCP emulators: PubSub `localhost:8085`,
Storage `localhost:4443`, BQ `localhost:9050`. AWS: `@mock_aws` (moto). `pytest --block-network`. DeFi integration:
Tenderly fork fixtures in `execution-service/tests/defi_execution/integration/conftest.py`. Cassette parity:
`cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` (every commit).

**Local dev**: deployment-stack (ports 8004/5183):
`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh [--api|--ui|--stop]`. Tier-based:
`cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 0`. Port registry:
`unified-trading-pm/scripts/dev/ui-api-mapping.json`. Full guide: `codex/08-workflows/local-dev.md`.

**Multi-repo**: each subdirectory is independent git repo. Only commit to target repo. Never `basedpyright .` from
workspace root — always per-repo with timeout.

---

## Batch = Live (CRITICAL)

Batch + live use SAME code path. Only difference: execution fills. Never build standalone backtest engines; never
distinguish live/batch strategies; never build asset-group-specific backtest engines. 99% of code path identical.

---

## System-First Architecture

Look at the existing system before implementing. Key repo map: events → UTL · schemas → UAC · cloud →
unified-cloud-interface · market data → MTDS · execution → execution-service · reference data → instruments-service
(`URDI` is a phantom name — does NOT exist) · UI → `unified-trading-system-ui` (consolidated, includes user-management
functionality) + `deployment-ui` (`user-management-ui` repo is ARCHIVED 2026-05 — folded into unified-trading-system-ui;
do NOT reference) · **orchestration → `agent-orchestrator`** (FastAPI + Vite dashboard; port 8026 locally;
`agent-orchestrator.odum-research.com` prod; dashboard is authoritative work-split surface. `ikenna_orchestrator/`
LEDGER.md remains as offline fallback only; the `harsh_orchestrator/` LEDGER + dispatch files were retired 2026-05-25 →
`plans/archive/orchestrator_legacy/` (only `harsh_orchestrator/_agent_pings.md` stays in place — still read by the live
plan-hygiene + orphan-ping crons). SSOT: `codex/04-architecture/agent-orchestrator-overview.md`.

**UAC import rule**: `from unified_api_contracts.{domain} import ...` only. Never `canonical.*` or `normalize_utils.*`.
SSOT: `imports/uac-import-surface-enforcement.mdc`. Full decision tree: `SUB_AGENT_MANDATORY_RULES.md` §0.

---

## Plan Format + Filename Convention

Every todo: `- [x] [SCRIPT] P0. Description...`. SSOT: `plans/PLAN_FORMAT.md`.

Epic-foundation model (codified 2026-05-21): **epics in `plans/epics/<slug>.md` are everlasting** — no date suffix, no
`estimate_*` fields, required `assigned_vm` + `tier` + `priority` frontmatter + P0/P1/P2/P3 priority blocks. Active
plans + wrapper plans in `plans/active/<slug>_YYYY_MM_DD.md` MUST carry `parent_epic:` + `estimate_class` /
`estimate_baseline_ai_days` / `estimate_calibrated_ai_days`. **Orphan active plans (no `parent_epic:`) are
review-blocking.** Audit docs land in `plans/audit/results/<slug>_YYYY_MM_DD.md`. Archive:
`plans/archive/<slug>.plan.md` (DO NOT rename). Full epic-flow SSOT: `plans/epics/README.md` (19 epics × 5 tiers × 10-VM
topology + audit→plan→epic flow + lifecycle).

**`assigned_vm:` frontmatter (MANDATORY — orchestrator v0.7+)**: Every master plan and epic plan MUST declare
`assigned_vm: <vm-id>` in frontmatter. Valid ids are in `orchestrator_vm_registry.yaml`. PM `quality-gates.sh` runs
`scripts/orchestrator/regen_vm_registry.py --check` as a post-gates step — exits 1 if any plan's `assigned_vm` is not in
the registry. Missing or unknown `assigned_vm` is review-blocking. SSOT:
`plans/active/orchestrator_v07_multi_vm_topology_2026_05_21.md` § Phase 1.

---

## Capture Discoveries As Plan Todos Immediately (HARD RULE)

Every side-discovery MUST go into a plan todo at the moment it surfaces. Tag P0-P3 + `**DEFERRED**`/`**NICE-TO-HAVE**` +
provenance. **Never auto-memory. Never chat summary.**

End-of-cycle: every deferral in your summary MUST already be a `- [ ]` plan todo. Grep to verify — no match → STOP, add
todo first. Reviewers reject summaries with grep-miss deferrals.

---

## Active Plan Inventory + Done-vs-Left Dashboard

Run: `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`. Cadence: morning + EOD + before
planning decisions (slot 1 main, both sides). Writes between `<!-- AUTO-INVENTORY-START -->` /
`<!-- AUTO-INVENTORY-END -->` in `master_to_live_defi_2026_05_23.md`. **Orphan check**: any active plan without
`parent_epic:` in frontmatter shows as **ORPHAN** in the dashboard. Orphan count > 0 is review-blocking at PR time —
assign the right epic OR file the plan in `plans/active/issues/` if scope unclear. Do NOT mass-sweep (collision risk per
Findings Triage). Full SSOT: `codex/11-project-management/active-plan-inventory-tracker.md`. Epic registry:
`plans/epics/README.md`.

---

## Local slot host = VM slot host — symmetric worker model (HARD RULE codified 2026-05-20)

**Every host owning slot worktrees follows the SAME contract** — VM, operator laptop, Harsh laptop alike: per-slot
worktree on `tab/<operator>/<N>`, `slot-cron-ff-pull.sh` + `slot-git-status-report.sh` every 5 min, and Commit + Push +
Flip same-turn. **An interactive Claude Code session IS slot N** (same branch, same Commit+Push+Flip, same FF-pull +
status-report); the orchestrator doesn't differentiate it from a spawned worker (only `paused` vs `working` differs). So
a 9-hour uncommitted local WIP is the same anti-pattern as a stale worker — both block FF-pulls + create the "stale
code" the worktree model prevents. **Verify every host**: `bash scripts/verify-slot-host-symmetry.sh` (exit 0 = both
crons installed + ran <10 min + report posted). SSOTs: `codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md` ·
`agent-orchestrator/agents/worker.md` · `scripts/dev/slot-cron-ff-pull.sh` · `slot-git-status-report.sh` ·
`scripts/verify-slot-host-symmetry.sh`.

## Plan Hygiene — Frontmatter, Line Caps, Archive Candidates

Run: `bash unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh`. Auto-fix:
`python3 unified-trading-pm/scripts/plan-hygiene/fix_frontmatter.py`. Daily cron on planning VM at `0 5 * * *` UTC pings
orchestrator inboxes on failure. Full SSOT: `codex/11-project-management/plan-hygiene.md`.

---

## Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)

> **#1 source of wasted reallocation + false-progress** (2026-05-14/15: slots shipped 15+ items unflipped; dashboard
> showed ~14% vs ~70% actual). Half-1 without Half-2 in the SAME agent turn is a violation — not "later".

**Half 1 — commit + push at every shippable unit** (pushed = real; per-unit, not per-hour/session). Pre-commit
(MANDATORY): `git status && git diff --cached --stat` (NO path arg — see the whole index); `git restore --staged <file>`
anything not yours; stage by name, never `git add .`/`-A`. Bundle Edit→stage→commit→push in ONE Bash call; `--no-verify`
authorized only on prek auto-restore symptoms ("Restored working tree changes from .../prek/patches/").
`quickmerge --agent --files '<paths>'` **re-asserts `--files` scope on the prek commit-retry** (when a hook reformats
files and the first commit fails, it re-stages ONLY your `--files`, never `git add -A`) so a hook can't bundle FOREIGN
modified files (another agent's WIP, an inventory regen) into your scoped commit — but for a hand `git commit` the
discipline is yours. SSOT: `codex/08-workflows/ci-cd-flow.md` § "Two-Pass Workflow Model".

### Half 2 — flip the plan checkbox in the SAME AGENT TURN as Half-1 (the most-violated half)

The next Bash call after the code push, before any new item — NOT next session / EOD. Flip `N. [item]` →
`N. ✅ [item] — <repo>@<sha> + evidence`; commit with the **MANDATORY `docs(plans):` prefix** (`plan(...)` is
hook-rejected) + push. **Self-check before the next item**: `git log --oneline -5` should alternate code-commit ↔
`docs(plans): flip`; two consecutive code commits with no flip between → STOP + flip first. Found unflipped items
(recovery/audit) → stop new work, walk the branch log, ship one
`docs(plans): backfill plan-flips for items X/Y/Z — <repos>@<shas>`, then resume.

**Why**: an unflipped item is invisible to the orchestrator → it re-dispatches to another slot that re-implements
(wasted hours + conflicts) — a flipped checkbox is the orchestrator's done-signal, not "bookkeeping".

**Half 3 — session-end**: multi-item sessions with non-final state get a `## Deferred work after <date>` table before
`## Temporary states`. Half-2 ALWAYS matters when an item is final; Half-3 when non-final. Full treatment + the
2026-05-14/15 incident: `codex/12-agent-workflow/commit-push-flip-rule.md`.

---

## Post-Plan-Phase Codex Audit (HARD RULE)

After every major phase: (1) phase changed a codex contract? update the doc. (2) new pattern not in codex? write stub.
(3) invalidated codex doc? add SUPERSEDED banner. Codex doc paths MUST be enumerated in plan's "Codex SSOT updates"
phase — plans omitting this are review-blocking.

---

## CI Verification After Every Push (HARD RULE)

- Pushes to `main` / PRs → CI runs. **Always verify** via
  `gh run list --branch <branch> --repo <owner>/<repo> --limit 5`.
- **Required check name (all repos)**: `quality-gates-v2` (v1 `quality-gates`/`workspace-qg` retired 2026-05-29 — see
  `codex/08-workflows/ci-cd-flow.md` § quality-gates-v2).
- **Branch protection = ruleset + classic, BOTH** (must agree or merges silently dead-lock); ruleset context is derived
  from the workflow's job `name:`; `enforce_admins` only ON when v2 is green. SSOT: `codex/08-workflows/ci-cd-flow.md` §
  "Branch-protection mechanism".
- **Force-push vs let-CI/CD (HARD RULE)**: admin force (relax → do → RE-ENABLE, guaranteed) is for the **initial
  clean-slate only** where the gate can't run/be-satisfied by a PR (missing/wrong-named v2 workflow; FF a default branch
  strictly behind its integration branch; landing the fix that unblocks the branch). **Everything else goes through the
  normal PR → quickmerge auto-merge** (a green gate merges it). NEVER leave a ruleset `enforcement=disabled` /
  `enforce_admins` off; resolve conflicts ON `live-defi-rollout`, never a throwaway branch. SSOT:
  `codex/08-workflows/ci-cd-flow.md` § "Force-push vs let-CI/CD".
- **Promotion automation (staging→main: semver / SIT / staging-to-main) REPAIRED 2026-06-02** — semver-agent now watches
  `quality-gates-v2` (was watching a dead `Quality Gates` check; cicd #504), so the LDR→staging→SIT→main→image pipeline
  flows again. **Ship every unit via `quickmerge --agent --files '<paths>'`** (Pass 1 local `quality-gates.sh` writes
  the sentinel → Pass 2 quickmerge commits + opens the staging PR + auto-merges). **Do NOT
  `git push HEAD:live-defi-rollout` directly** — quickmerge **early-exits "nothing to commit" on a clean tree**, so
  direct-pushed commits never open a staging PR and silently pile up on LDR behind main (slot-7 2026-06-02: PM was level
  but mtds +131 / deployment +92 / alerting +22 behind main from direct LDR pushes). Existing committed-LDR backlog
  drains via the staging→main automation or a per-repo staging PR — NOT a retroactive quickmerge. Residual hardening +
  backlog-drain status: `plans/active/cicd_contract_hardening_2026_06_01.md` § "Phase 6 — CONSOLIDATED HAND-OFF".
- Pushes to `live-defi-rollout` / `feat/*` → NO remote CI. Quality enforced locally via `quality-gates.sh`.
- On CI fail: `gh run view <run-id> --log-failed`. Fix root cause. Push again.
- CI failures are NOT issues to flag — fix in real time.

---

## Grep-Then-Read, Not Grep-Then-Conclude (HARD RULE)

0 grep hits ≠ feature missing. Many features are runtime-resolved (regex dispatch, StrEnum lookups, factory registries,
dynamic `getattr`, config-driven wiring). After 0 hits: escalate to READ — open candidate consumer + factory/dispatcher
files. When uncertain, ASK rather than CONCLUDE. For >50KB plans, read past executive summary.

---

## Findings Triage Discipline (HARD RULE)

| Where it sits                  | Action                                                                                                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| In your code / file you own    | Fix in same commit                                                                                                       |
| Adjacent to your plan          | Document + fix in YOUR plan                                                                                              |
| Outside plan, small + clear    | Fix if ≤30 min                                                                                                           |
| Outside plan, ambiguous        | Diagnose first — read both sides (caller + callee). Fix the side that's wrong. If genuinely can't tell → file issue doc. |
| Audit finding with clear scope | Wrapper plan in `plans/active/<slug>_remediation_<date>.md` with `parent_epic:` + `assigned_vm:` → dispatch to epic VM   |
| Outside every plan             | `plans/active/issues/<name>_<YYYY_MM_DD>.md`                                                                             |
| **Big finding**                | NOTIFY OPERATOR + file issue doc                                                                                         |

**"Pre-existing" is NOT a triage criterion** — fix now if you can. **Diagnose before fix** — is the code wrong or the
test wrong? Read both sides.

"Big" = data correctness ≥1 asset_group / May-23 critical path / cross-repo / contradicts workspace SSOT. Issue-doc
frontmatter: `title`/`created`/`author`/`source[]`/`locked_by`. Body: `## What I found` / `## Why it matters` /
`## Recommended decision`.

---

## External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified 2026-05-14)

**Premise**: for every asset_group × MVP archetype, **data exists** — if the public/free path is exhausted, the unblock
is a credential/subscription **ask to the operator, NOT** a license to defer/descope (paid tiers exist: Helius/Alchemy,
Glassnode/Kaiko, Tardis, Databento, Sportradar/The-Odds-API…). Banned: "no public API / free tier exhausted / no test
data / subscription required / can't repro in sandbox" used to drop scope.

**Required when you hit the wall**: (1) build the adapter scaffold anyway (schema + UAC contract + auth/retry +
`classify_venue_error()` + manifest emission; unit tests on mocks; integration tests
`@pytest.mark.requires_credentials`, skipped by default); (2) file a `CREDENTIAL APPROVAL REQUEST` in
`pings/slot_<N>.md` (vendor+tier+cost / what's needed / account / what it unblocks); (3) status =
**`BLOCKED-CREDENTIALS`** (NOT `DEFERRED`/`POST-CUTOVER`); (4) cross-link the master plan's "Credential asks awaiting
operator"; (5) never move to post-cutover without operator `[ack]`.

**Status taxonomy** (closed set; replaces ad-hoc "deferred" language):

- `BLOCKED-CREDENTIALS` — has named operator ask; waits for [ack]; adapter scaffold + unit tests still ship in same
  logical unit
- `BLOCKED-OPERATOR-DECISION` — closed-set design call needed (e.g. which vendor among 3 candidates); waits on operator
  pick
- `BLOCKED-UPSTREAM-OUTAGE` — third-party degraded; ping logged; auto-resumes on health check
- `DEFERRED` — only valid with NAMED successor plan in `plans/active/` + operator-acked migration line in current plan

**MVP archetype × asset-group coverage target** (May-23 gate): every cell in this matrix has a working batch adapter
(either green or `BLOCKED-CREDENTIALS` with named ask):

|                              | DeFi                                                                                                       | CeFi (perp + spot)                                                             | TradFi                     | Sports                                  | Prediction                              |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------- | --------------------------------------- | --------------------------------------- |
| `carry_staked_basis`         | LST APRs (Lido stETH / RocketPool rETH / Coinbase cbETH / Solana JitoSOL / mSOL); Aave/Compound base rates | Perp funding (Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken); spot prices | n/a                        | n/a                                     | n/a                                     |
| `arbitrage_price_dispersion` | DEX prices (Uniswap V3 / Curve / Balancer / Sushi / PancakeSwap / Phoenix / Orca / Raydium / Drift)        | CEX spot + perp marks (all 7+ venues)                                          | (optional) Databento ticks | (optional) odds dispersion across books | (optional) Polymarket vs Kalshi spreads |

Sports + Prediction tracks have parallel coverage targets independent of the DeFi archetypes.

**Enforcement**: PM `quality-gates.sh` runs `scripts/quality_gates/check_credential_ask_orphans.py` (baselined ratchet —
fails on a `BLOCKED-CREDENTIALS` plan line with no ping reference). Full rule + credential-request template +
composes-with (Findings-Triage / Capture-Discoveries / Commit+Push+Flip / Plans-Run-To-Completion):
`codex/02-data/external-data-always-available-rule.md`.

---

## Plans Run To Actual Completion, Not Smoke-Test Green (HARD RULE)

Code-shipped ≠ operationally-shipped. Backfills/migrations/reconcilers run to completion on real infra with
manifest-verified rows + sample-inspected parquets. ADC admin perms on GCP (`central-element-323112`) + AWS
(`427895769566`) — do NOT pause for operator approval on infra ops.

Hard-stop list (human-only): wallet keys, force-push to main, version 1.0.0 graduation. **Kill-switch / trading-halt is
direction- + scope-aware, NOT a blanket gate (codified 2026-06-02):** (a) **protective/fail-safe = always autonomous** —
agents + the runtime may arm the kill-switch / `STOP_NEW_ONLY` / firm-wide halt + relaunch crashed safety/monitoring VMs
(alerting/watchdog/consolidator); fail toward safety without a human. (b) **resume / un-kill / disarm = autonomous WHEN
within the defined disaster-recovery + auto-recovery scope** (`auto_cooldown` breakers self-recovering on the
`autonomous-recovery-matrix.md` timelines + the DR-plan runbook); **human-only ONLY when OUTSIDE that scope** — a
`manual_unkill` destructive breaker (`KILL_ALL` / `CANCEL_OPEN`, operator sign-off by design) or a novel situation the
DR/auto-recovery matrix doesn't cover. Within scope an agent resumes; outside scope a human does. SSOT:
`codex/04-architecture/autonomous-recovery-matrix.md` § "Hard-stop scope: agent vs human".

Every Tab in daily work-split MUST declare Full-Execution Criterion. SSOT: `plans/PLAN_FORMAT.md` § 8.

---

## Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified 2026-05-20)

> Operator 2026-05-20: the data pipeline is the heartbeat — when an audit surfaces issues, **every** issue is fixed in
> full (every venue × data_type × time-range backfilled, every silent-empty diagnosed, every schema row migrated, every
> batch adapter paired with live). **No deferrals for a deadline. No asset_group skipped.**

**Only legitimate deferral** (operator-only — agent never decides): `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION`
/ `BLOCKED-UPSTREAM-OUTAGE`. **Banned**: "skip for the deadline" · "post-cutover" · "most cells captured, rest later" ·
"the constant says v8 so good enough" (read the actual `schema_version` distribution — incident: 0% of 7.4M rows at v8
despite the bump) · "do A5/A6 later". **Consequences**: layer-N+1 work FREEZES while a data audit is RED for affected
asset_groups (foundation-completion-gate); slot-1 reassigns slots to data-fix until GREEN; reviewer rejects layer-N+1
plans with open audit P0s; every audit must state where it sampled vs walked + remaining gaps. Composes with
Foundation-Completion-Gate / External-Data / Plans-Run-To-Completion / Manifest-Honest-Absence. Full SSOT:
`codex/02-data/data-pipeline-correctness-hard-rule.md`; migration sequencing (Phase ordering HARD, slot-1 owns
broadcast/ACK): `plans/epics/mtds_mdps_master.md`.

**Quality Gates Are A Commit + Merge Prerequisite (HARD RULE)**: no code is **committed** toward / merged to
`live-defi-rollout` without `bash scripts/quality-gates.sh` exit 0 for the touched repo + cross-repo consumers
(commit-as-boundary, see § "Quality gates BEFORE COMMIT"); reviewers reject PRs lacking a QG-green evidence line.
Exemption only via operator `BLOCKED-OPERATOR-DECISION`. **This is the LOCAL / agent pre-flight (an agent +
commit/quickmerge requirement — fail-fast so you never put un-QG'd code on the integration branch or waste a doomed
CI/PR cycle), NOT a server gate. `live-defi-rollout` carries NO required-check ruleset — it is the unprotected
integration axis by design (`codex/08-workflows/ci-cd-flow.md`). The SERVER-ENFORCED required check (`quality-gates-v2`)
fires at the staging/main PR — the promotion boundary. The `require-quality-gates` ruleset targets `~DEFAULT_BRANCH`, so
every repo's default branch MUST be `main` (a non-main default mislocates the required check onto LDR and blocks pushes
to the integration axis — incident 2026-06-03 uta+greeks; `verify_branch_protection_check_names.py` now asserts it).**

**Batch the GATE, not the commits — QG-sweep (2026-06-02)**: for a batch of related edits, make ALL edits (code-only
agents verify with `basedpyright` on touched files), run `quality-gates.sh` ONCE per repo over the batch, THEN make
per-shippable-unit commits + flips from that green tree (Commit+Push+Flip intact — only GATE RUNS batch). **Shared-host
(HARD)**: ≤1–2 full QGs at once host-wide (they serialize; exceeding OOM-kills, exit 144); **NEVER bulk-kill `pytest` /
`quality-gates.sh` / `basedpyright`** (may be another slot's). When only the `<300s` META-gate trips (substantive gates
green): `IGNORE_TIMEOUT=true` / `PYRIGHT_TIMEOUT=<n>` are sanctioned. SSOT: `codex/06-coding-standards/quality-gates.md`
§ "QG-sweep batching".

**Generated artifacts + QG sentinels are gitignored, NEVER committed; generators MUST be deterministic (HARD RULE,
codified 2026-06-03)**: every file `quality-gates.sh`/`quickmerge` regenerates from a tracked SSOT is `.gitignore`'d +
`git rm --cached`'d — tracking it only churns the worktree → jams `slot-cron-ff-pull.sh` → drift (the root cause of the
chronic dirty-pull toil). Canonical ignore set (PM): `docs/repo-management/CI-CD-PIPELINE.svg`/`.html` (←
`cicd-pipeline-definition.yaml`), `WORKSPACE_MANIFEST_DAG.svg` + `DATA_FLOW_DAG.svg` (← `workspace-manifest.json`),
`derived-dependency-manifest.json` (← all `pyproject.toml`), `coverage.xml`, and the QG sentinels `.qg_last_passed_sha`

- `.qg_content_sentinel` (local-only caches). Every consumer regenerates from the SSOT before reading, so a committed
  copy is always a stale cache; nothing imports an SVG (zero logic blast radius). **Generators MUST emit
  deterministically** — `sorted()` any set/map before rendering (incident: `generate-cicd-diagram.py` iterated a `set()`
  of marker colours → byte-churned the SVG every run with no real change). **If you see a generated artifact dirty/`??`
  after a QG run, do NOT stage it** — it is regen churn; gitignore + `git rm --cached` it (and add the pattern to the
  canonical template `scripts/propagation/templates/gitignore-python.txt` for fleet rollout). SSOT:
  `cicd_contract_hardening_2026_06_01.md` item H + `qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md`.

**Every active ping references a plan item (HARD RULE)**: no orphan pings in the `_agent_pings.md` ledgers — every entry
cites a plan-of-record (`plans/active|epics|audit|active/issues/<slug>.md`, incl date-suffixed). References nothing →
file/extend a plan first or remove the ping. A 4-hourly cron (`scripts/agents/audit_ping_orphans.sh` local + GCP
`uts-prod-orphan-ping-audit`) appends `## [orphan-ping-cron]` notices to both orchestrator inboxes; slot-1 + harsh-main
clear them within a cycle. SSOT: `scripts/agents/audit_ping_orphans.sh` +
`deployment-service/terraform/gcp/orphan_ping_audit_scheduler.tf`.

---

## Estimate Calibration (HARD RULE)

Apply class multipliers at plan-write time. Claude's estimates run 1.5-3× conservative for this workspace's fan-out
pattern:

| Class       | Multiplier |
| ----------- | ---------- |
| `refactor`  | 0.4×       |
| `design`    | 0.6×       |
| `infra`     | 0.8×       |
| `brand-new` | 1.0×       |
| `research`  | 1.2×       |

Frontmatter (every active plan + wrapper plan after 2026-05-11): `estimate_class` / `estimate_baseline_ai_days` /
`estimate_calibrated_ai_days`. **Epics in `plans/epics/` are EXEMPT** — they are everlasting and do not carry estimate
fields (estimation lives on the active plans they reference). Audit wrapper plans count as active plans → MUST carry all
three estimate fields. Legacy plans: retrofit on next substantive touch — do NOT mass-sweep. Retrospective ledger:
`codex/08-workflows/estimation-retrospective-ledger.md`. Full SSOT: `codex/08-workflows/estimation-calibration.md`.

---

## Citadel-Grade Planning Standards

Every plan MUST: (1) Pre-Audit Before Execution — workspace-wide grep for every removed/renamed symbol; embed manifest.
(2) Phased Execution DAG with explicit deps + QG gates between phases. (3) No Technical Debt — clean breaks, no shims.
(4) Parallelization — independent items marked PARALLEL. (5) Success Criteria per phase — QG/basedpyright/ruff + test +
deployment gates. (6) Downstream Consumer Updates — pre-audit EVERY workspace consumer for removed/renamed public
symbols. (7) Single Source of Truth — types in UAC or `unified_api_contracts.internal`. (8) Foundation-Completion-Gate
Discipline — no plan ships items in layer N+1 before layer N is GREEN-audited + manifest-divergence = 0 for affected
asset_groups; parallel-up across asset_groups within a layer is encouraged, parallel-up across layers is
review-blocking. Full layer table + application rules + anti-patterns:
`codex/11-project-management/foundation-completion-gate-discipline.md`. Master tracker:
`plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`. (9) Issue-Doc Lifecycle Discipline — issue
docs in `plans/active/issues/` exist to surface UNACKED work; once acked (into a plan / shipped code / out-of-scope with
named successor), they archive immediately. Banner-marked-in-`active/issues/` is a transitional convenience, NOT a
permanent state. "Stays until parent closes" lifecycles are dual-tracking and review-blocking. State machine + audit
recipe + anti-patterns: `codex/11-project-management/issue-doc-lifecycle.md`.

---

## Runbook Execution-Owner SSOT (HARD RULE)

Every runbook MUST declare 4 fields: `owner` / `cadence` / `verifier` / `last_executed`. No exceptions — missing fields
= review-blocking. Closed set of execution paths: (1) Cron VM, (2) Daily Tab assignment, (3) QG-wired smoke, (4) Cron
ScheduleWakeup. Reference: `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`.

---

## Peripheral Script Directories Under Primary-Consumer QG (HARD RULE)

Every peripheral script directory importing from a service MUST be wired into THAT service's `quality-gates.sh`. Key
mapping: `e2e-testing/scripts/defi/` → strategy-service QG; `e2e-testing/scripts/sports/` → features-service QG;
`e2e-testing/scripts/prediction/` → mtds QG; `*_service/scripts/migration_*.py` → own service QG.

---

## Master Plan Continuous-Verification Column (HARD RULE)

Every success criterion (Groups A-G, 23 items) MUST declare continuous-verification path. Column:
`| Group | Item | Cutover Criterion | Continuous Verification | Last verified |`. PRs without `Last verified` updates
are review-blocked.

---

## Per-Tab Worktrees — 3-tier parallel-agent isolation

3 tiers: Operator (separate machines) → Slot (`.tabs/<N>/<repo>/` on `tab/<operator>/<N>`) → Sub-agent (within slot,
shares index).

Bootstrap: `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8` (also: `--add-slot N`,
`--reset-slot N`, `--list`). Reconciliation: `bash unified-trading-pm/scripts/dev/slot-master-rebase.sh`.

SSOTs: `codex/05-infrastructure/per-tab-worktrees.md` + `plans/active/per_agent_worktrees_2026_05_10.md`.

### Respawn working-tree hygiene (background agents) — liveness-gated, not identity-gated

On spawn/respawn/restart an agent MUST come up on a good tree. The discriminator for inherited dirty WIP is **liveness,
not identity**: the slot worktree `.tabs/<N>/<repo>` is exclusively that slot's, so dirty content left by a dead
predecessor (expired `.agent-claim` TTL / no tmux session / stale heartbeat) is _you-in-a-prior-session_ → **inherit +
commit**. **Quarantine is NEVER terminal** — a dead maker must not leave the slot infinitely dirty. Only a provably-LIVE
peer (realistically the operator's own interactive session on the slot, per the "operator session counts as a slot"
rule) is protected: a **background** worker `notify_*`-pings the operator + inherits once the maker's claim TTL expires;
an **interactive** session ASKS the operator whether other agents are finished, then commits. Forbidden: per-file
foreign attribution (`in_flight_files` is a refinement, never a gate); pushing a wiped-index mass-delete
(`git reset --mixed HEAD` first, quarantine if files truly gone); spawning without asserting `HEAD == tab/<op>/N` +
upstream == the repo's correct base (per-repo: `main` for agent-orchestrator, `live-defi-rollout` else). SSOT:
`plans/active/orchestrator_autonomy_audit_remediation_2026_06_01.md` § Phase 4.

---

## Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)

**Main orchestrator bootstrap**: Ikenna reads `ikenna_orchestrator/LEDGER.md` first (offline fallback); the Harsh-side
LEDGER was retired 2026-05-25 (→ `plans/archive/orchestrator_legacy/`) — use the agent-orchestrator dashboard. Boot:
`git status` + `git fetch` + ledger/dashboard read + ack state.

**Sizing**: ~250-400 cal AI-days per side per 4-day cycle. **Ikenna**: cross-cutting design (3+ repos),
trading-judgment, governance, large migrations. **Harsh**: implement-from-spec, run-script-and-verify, single-repo
edits, test execution.

**Models**: A = fixed 5-tab clustering. B = 1-main + dynamic spawned tabs. \*\*C = Planning VM (Ikenna + Harsh
interactive, Opus 4.7 1M) → audit pool → wrapper plans with `parent_epic:` + `assigned_vm:` → Epic VMs (Sonnet 4.6 main

- review + workers per epic).\*\* Epic flow SSOT: `plans/epics/README.md`. VM topology spec:
  `plans/active/orchestrator_master.md`.

**Universal mechanics**:

- **Conditional push**: `git fetch` first → 0 incoming → push freely; any incoming → STOP, document 🟡 BLOCKED in
  plan-of-record, append ping.
- **Ping ledger bifurcation**: workspace-shared `plans/active/_agent_pings.md` (cross-side only) + per-side
  `<side>_orchestrator/pings/slot_<N>.md` (intra-side). Per-slot files reset on re-theme via `--reset-slot <N>`.
  Cross-side commit-sha entries persist until both sides ack.
- **Slot precedence**: slot 1 main owns master-plan refresh + daily inventory regenerator. Other slots do NOT edit
  `master_to_live_defi_2026_05_23.md` directly.
- Sub-agent fan-out: send all `Task` calls in SINGLE message. Paste `SUB_AGENT_MANDATORY_RULES.md` at top.

Full SSOT: `codex/12-agent-workflow/` + `ikenna_orchestrator/LEDGER.md`.

---

## Cross-Plan Coordination Banners

When launching VM or starting in-flight refactor, add `> **🟢 VM RUNNING — ...**` / `> **🟡 IN-FLIGHT REFACTOR — ...**`
banner to every affected active plan. Scan banners before touching affected surface. Banner-remove owned by launcher at
completion.

---

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents start FRESH. Paste `SUB_AGENT_MANDATORY_RULES.md` (10KB lean file) at TOP of every Task spawn.

- Local: `RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")`.
- GHA: load via `GITHUB_ENV` heredoc.
- If paste impractical: include "Before any action, read SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
- **If rules injection fails, agent MUST NOT proceed.**

SSOTs: `unified-trading-pm/scripts/agents/inject-mandatory-rules.sh` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`.

---

## Analysis Rules

EXCLUDE `.venv*`, `node_modules/`, `build/`, `dist/`. FOCUS Python source in service dirs.

```bash
rg "pattern" --type py --glob '!.venv*' --glob '!build' --glob '!tests'
```

---

## Workspace Configs (Canonical in PM)

Canonical: `unified-trading-pm/cursor-configs/`. Setup:
`bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh`. Strict basedpyright
(`reportAny`/`reportUnknownMemberType`/`reportUnknownVariableType` = error).

---

## UAC Citadel Architecture

Layout: `canonical/domain/` · `canonical/crosscutting/` · `external/{source}/` (80+ dirs) · `normalize_utils/` ·
`registry/` · root facades.

**Deleted dirs** (do NOT reference): `canonical/normalize/` · `external/sports/` · `external/cloud_sdks/` ·
`external/onchain/` · `external/macro/` · `schemas/` · `shared/` · `external/kaiko/` · `external/polygon/` (TradFi data
provider; Polygon L2 chain in `canonical/crosscutting/defi.py` intact).

Import: `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`. Deep paths are
UAC-internal. SSOT: `codex/02-data/contracts-scope-and-layout.md`.

**Global ledger SSOT** (Phase 2 shipped 2026-05-23): `unified_api_contracts.canonical.crosscutting.ledger` —
`LedgerRow` + 4 aliases (Instruction/Passive/Treasury/Pricing) + 5 StrEnums + `CrossClientTransferForbiddenError`.
Architecture: `codex/04-architecture/global-ledger-architecture.md`. Taxonomy: `codex/02-data/ledger-event-taxonomy.md`.
