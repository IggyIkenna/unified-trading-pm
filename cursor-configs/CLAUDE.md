# Unified Trading System — Claude Code Instructions

> **Lean index** of workspace rules. Each rule has a 1-line essence + a pointer to its full SSOT. When a rule applies,
> **read the SSOT pointer** — don't act from memory.
>
> Condensing 2026-06-02 (in progress): grew to ~1180 lines / 84KB; shrinking back toward ~600 by relocating detail to
> codex SSOTs and keeping the sharp directive + 1-line pointer here. These rules are NOT waste — they encode behaviours
> agents were missing; condense, don't drop.
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

- `bash scripts/quickmerge.sh "msg" --agent` not `git push` for promotion-to-main. Always `--agent` in Claude Code.
- Dirty deps → commit + push directly to `live-defi-rollout`. DO NOT quickmerge when dep repos dirty.
- Two-pass: Pass 1 = `bash scripts/quality-gates.sh`. Pass 2 = `quickmerge --agent` (lint/format/typecheck/codex, no
  tests).
- `--dep-branch` is human-only.
- **`git pull` rejected with `(would clobber existing tag)`** (stale local release tag vs semver-agent's canonical
  remote tag, e.g. `v1.0.0`/`v1.2.0`): fix with `git fetch origin --tags --force` (local-only; remote is canonical for
  release tags — never force-push tags the other way), then `git pull --ff-only`. SSOT:
  `codex/05-infrastructure/per-tab-worktrees.md` § "Step 7 — troubleshooting".
- **Full operator deployment flow** (dev → staging → main + paper → live strategy promotion):
  `codex/08-workflows/deployment-flow.md`.
- **agent-orchestrator EXCEPTION (codified 2026-06-01)**: `agent-orchestrator` is the ONE repo whose integration target
  is **`main`, NOT `live-defi-rollout`**. It is operator/agent tooling — NOT production trading code — so it **bypasses
  the production code-hardening path** (`live-defi-rollout` → `staging` → `main`). The slot model still applies: commit
  to the slot branch `tab/<operator>/<N>` to isolate per-agent commits, then **fast-forward the slot branch to `main`**
  (its slot branch tracks `origin/main`; every OTHER repo's slot branch tracks `origin/live-defi-rollout`). Do NOT route
  agent-orchestrator changes through LDR/staging or treat its `main`-behind-LDR as drift to "promote" — `main` is its
  canonical. (Its work may also appear on LDR via the `tab-mirror` GHA; that is harmless mirroring, not the target.)
  SSOT: `codex/04-architecture/agent-orchestrator-overview.md`.

### Imports + types

- `from unified_trading_library.events import setup_events, log_event` — no fallbacks.
- `basedpyright` not `pyright`; always `run_timeout 120 basedpyright <source_dir>/`.
- No `os.getenv()` — use `UnifiedCloudConfig`. No `# type: ignore`. No `try/except ImportError`.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)`.
- No hardcoded `"/tmp"` — use `tempfile.gettempdir()`. SSOT: `codex/06-coding-standards/quality-gates.md`.

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
categories of "missing": (1) expected gap → `record_empty(reason=<typed>)`, (2) unexpected gap →
`DependencyError(fail_fast=True)`, (3) schema-drift bug → RAISE LOUD. Never emit silent placeholders.

**Current canonical manifest schema = v9, workspace-wide (all asset groups, NOT tradfi-only).**
`MANIFEST_SCHEMA_VERSION` 8→9; each asset group's `_index` migrates 8→9 (adds `source`/`asset_group`/`pipeline_mode`
cols) bundled into its single canonicalisation walk. Trust the actual `schema_version` distribution, never the constant.
SSOT: the per-asset-group `*_manifest_canonicalisation_2026_06_01.md` plans coordinated by
`defi_manifest_canonicalisation_2026_06_01.md`.

- 33-member `EmptyConfirmedReason` closed set (29 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` + `NO_INPUT_AVAILABLE` +
  `LEG_ABSENT_LEFT` + `LEG_ABSENT_RIGHT`) in UAC `EMPTY_CONFIRMED_REASONS`. Blank reason →
  `LegacyBlankErrorReasonError`. Enum:
  `unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason`. Per-reason consumer policy table:
  `codex/02-data/honest-absence-downstream-handling.md` § "Per-reason-group → consumer policy".
- Cluster validation MANDATORY at `record_captured()` for bundled data_types. UTL raises `MissingClusterValidationError`
  if kwargs absent.
- **TradFi `source` column (v9 schema)**: `record_captured(source=...)` REQUIRED for all TradFi writes. UTL raises
  `MissingSourceError` when `asset_group="tradfi"` and `source` omitted. Closed set: `"databento"` / `"massive"`. QG
  STEP 5.64 enforces; use `# QG-allow: tradfi-source-not-applicable` for kwargs-forwarding patterns.
  MANIFEST_SCHEMA_VERSION bumped 8→9. Multi-source union semantics: if ≥1 source is `captured`, downstream treats the
  cell as `captured`. Source priority: `select_primary_available_source()` in
  `unified_api_contracts.canonical.crosscutting.source_priority`. SSOT:
  `codex/02-data/honest-absence-downstream-handling.md` § "Multi-source cell consumer policy". Landed:
  `tradfi_massive_dual_source_2026_05_28.md` Phase 3.
- `available_at` is per-row write-time. UTL `record_captured` asserts presence internally.
- Service-output emission: every publish path through `_resolve_policy_output_data_type` + `_publish_emission_check`.
  SSOT: `codex/02-data/service-output-emission-semantics.md`.
- **Single-walk discipline (HARD RULE — post Phase 2.2)**: The Phase 2.2 GCS bundled migration walks every parquet ONCE.
  Any post-Phase-2 plan proposing another whole-corpus GCS walk is **review-blocking**. New schema columns,
  partition-key changes, or filename renames MUST bundle into the Phase 2 walk or wait for a scheduled next-migration
  window. SSOT: `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`.

SSOT: `codex/02-data/availability-manifest-and-data-status.md` + `codex/02-data/honest-absence-downstream-handling.md`
(§ "Reason taxonomy" — 31-reason table; § "Per-service consumer-class audit" — per-service skip/alert rules; §
"Per-reason-group → consumer policy" — per-reason ML/execution/rolling-window lookup).

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

- **Inherited-dirty-WIP resolution — liveness-gated, role-aware (HARD RULE codified 2026-06-01)**: a slot worktree
  `.tabs/<N>/<repo>` is exclusively that slot's, so dirty content is almost always a previous session of _you_ that is
  now gone → **inherit it** (commit as `chore(orphan-wip)` + push). The discriminator is **LIVENESS, not slot-id
  identity**: a dead/absent/expired `.agent-claim` (or one owned by the session being respawned) → inherit; a DIFFERENT
  live tmux session owning a fresh claim, OR a dirty file with mtime < 120 s (a live interactive operator/Cursor editor)
  → **PROTECT, never stomp**. An agent resolving inherited WIP must first detect whether it is a background autonomous
  worker (tmux `orch-slot-*` / `ORCHESTRATOR_*` env / claim `role`) or an interactive operator session — background:
  `notify_*`-ping the operator + inherit once the prior maker's claim TTL expires; interactive: ASK the operator whether
  other agents are finished, then commit. **Quarantine is never terminal** (a dead maker's WIP must eventually be
  inherited); **never `git add -A` a wiped/mass-delete index** (FM2 guard refuses + quarantines). Slot integration base
  is `live-defi-rollout` for EVERY repo incl. agent-orchestrator (a `main` base reads every slot as diverged —
  2026-05-24 incident). SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Pre-spawn branch-state + liveness-gated
  dirty resolution" + `agent-orchestrator/server/worktree_clean_check.py` +
  `plans/active/orchestrator_autonomy_audit_remediation_2026_06_01.md`.
- **Sports GCS paths**: `unified_api_contracts.sports.candidate_parquet_paths()` in
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Coverage: `clip_dates_to_source_coverage()` +
  `is_in_known_gap()`.
- **VIX 15m**: Barchart preload + Yahoo rolling 60d + honest gap. Massive does NOT cover VIX/VX futures — gap remains
  Barchart+Yahoo post-dual-source (tradfi_massive_dual_source_2026_05_28.md verified 2026-05-30). UAC constants in
  `registry/data_source_continuity.py`.
- **Manifest phantom audit**:
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group X --dry-run`. Do NOT write empty
  parquets to mask phantoms.
- **Manifest consolidator runtime**: GCP: Cloud Run Jobs + Cloud Scheduler (20 Phase A jobs — 10 env-tiered + 10 legacy
  flat, all `*/1 * * * *`; Phase D 14 Group B jobs TF authored pending `tofu apply`). AWS: Batch Fargate + EventBridge
  Rules (10 Phase C + 16 Phase D Group B both LIVE 2026-06-01 — 26 rules ENABLED, 26 Batch job defs). Terraform:
  `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` (GCP) +
  `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf` (AWS). Legacy GCE VM launcher DELETED 2026-05-20
  (was `launch-manifest-consolidator-vm.sh`). DO NOT relaunch the VM. **Liveness contract (2026-06-01, live)**: the read
  path loud-fails by DEFAULT on a stale/missing consolidated index when per-VM shards exist
  (`ManifestConsolidatorStaleError`; `MANIFEST_ALLOW_STALE_FALLBACK=true` opts back into the recovery merge); a
  `ConsolidatorLivenessMonitor` watchdog (Cloud Run Job `uts-prod-consolidator-liveness-watchdog`, Scheduler `*/2`)
  emits `CONSOLIDATOR_DOWN` on heartbeat absence; `assert_consolidator_healthy(bucket)` is the shared preflight gate.
  SSOT: `codex/05-infrastructure/manifest-consolidator-ssot.md` § "Liveness + health contract".
- **VM tarball**: `bash deployment-service/scripts/vm/create-code-tarballs.sh`. SSOT:
  `codex/05-infrastructure/vm-tarball-deployment.md`.
- **VM launchers**: every `gcloud compute instances create` in `deployment-service/scripts/vm/`. VM naming: first
  segment must be in `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`. **lifecycle_class required (Phase A.2)**: every
  non-`None` entry MUST be
  `VmPrefixSpec(bucket=..., lifecycle_class=LifecycleClass.<EPHEMERAL_BATCH|EPHEMERAL_EXPERIMENT|SCHEDULED_RECURRING|LONG_LIVED_LIVE>)`.
  **Experiment VM name suffix**: `EPHEMERAL_EXPERIMENT` VMs include the run_id: `{prefix}{run_id}-{ts}` (e.g.
  `exp-ml-{uuidv7}-{yyyymmdd}`). Reserved experiment prefixes: `exp-ml-`, `exp-strategy-`, `exp-execution-`. **Zone**:
  default `asia-northeast1-c`. STOCKOUT fallback = `asia-northeast1-b` or `asia-northeast1-a` (same region). NEVER fall
  back to another region (e.g. `us-central1`) — all GCS data is in asia-northeast1; cross-region egress adds cost and
  latency and is caught during T+10min zone audit.
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
- **Agent-orchestrator auth — setup-tokens only (HARD RULE codified 2026-05-28, Phase 4b-cleanup)**: every account in
  `agent-orchestrator/data/config/accounts.json` MUST authenticate via its own `oauth_token_env_file`
  (`~/.claude-accounts/<id>.env`) containing a long-lived setup-token minted via `claude setup-token`. **Never copy
  `~/.claude/.credentials.json` between machines**. The legacy `.credentials.<id>.json` swap path + the
  `swap_claude_account.sh` flow are removed; the runtime refuses to spawn a worker / agent / `/usage` probe for an
  account with no env file. To onboard a new account: (1) run `claude setup-token` on a browser machine, (2) write
  `CLAUDE_CODE_OAUTH_TOKEN=…` + `unset ANTHROPIC_API_KEY` to `~/.claude-accounts/<id>.env` (mode 600), (3) push to the
  creds bucket (`gs://central-element-323112-orchestrator-creds/accounts/` and
  `s3://uts-orchestrator-creds-427895769566/accounts/`), (4) add `oauth_token_env_file` + `setup_token_expires_at` to
  `accounts.json`. SSOT: `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`.
- **Agent-orchestrator backlog is plan-driven (HARD RULE codified 2026-05-28, Phase 6)**: tasks in
  `agent-orchestrator/data/config/backlog.yaml` are auto-derived from `- [ ]` checkboxes in `plans/active/*.md` by
  `server/regen_backlog_from_plan.py`. **Do not hand-edit `backlog.yaml` to add new tasks** — write the todo in the
  relevant active plan file using the canonical format (`- [ ] [CATEGORY] P<0-3>. Description`) and let the next
  `PlanRegenLoop` tick (≤6h, or POST `/api/backlog/regen` for immediate) pull it into the backlog. Idempotency is
  content-based (dedup by raw todo line), so flipping or editing a todo in the plan won't reset the backlog state.
  Hand-edits are still legitimate for _tuning_ derived tasks (priority, repos, target_slot, est_hours, collision_group)
  once they've been auto-created. SSOT: `agent-orchestrator/server/regen_backlog_from_plan.py` +
  `unified-trading-pm/plans/PLAN_FORMAT.md`.
- **Fanning out work = writing tracked plan todos. The plan todo IS the dispatch (HARD RULE codified 2026-06-01)**:
  whenever you decide a unit of work should be done by a slot/worker — "a slot should do X", "this needs a dedicated
  per-repo pass", "fan this out", "assign to slot N", "out of scope for me, hand off" — the decision is **not real until
  it is a `- [ ]` todo in a PM active plan** using the canonical format (`- [ ] [CATEGORY] P<0-3>. Description`) with
  the **target repo named** and **enough self-contained context that a cold sub-agent can act** (it starts fresh + reads
  `SUB_AGENT_MANDATORY_RULES.md`). That plan todo is the ONLY sanctioned dispatch path: `PlanRegenLoop` derives the
  orchestrator backlog from it (per the rule above) and a slot picks it up. **Banned (review-blocking):** punting work
  in chat / a summary only ("X is blocked, needs a slot"), verbally assigning a slot without a plan todo, or marking an
  audit/diagnosis "done" when its follow-ups are only described, not tracked. **Grep-to-verify before ending any session
  that identified fan-out work**: `rg "<the work>" plans/active/` — no `- [ ]` match → STOP, write the todo first. A
  diagnosis that names N repos needing fixes MUST leave N tracked todos behind. Reference incident (2026-06-01): a
  7-repo QG-green remediation surfaced mid-session; per this rule each repo became a tracked todo in
  `cicd_contract_hardening_2026_06_01.md` rather than a verbal "fan it out". Composes with: _Capture Discoveries As Plan
  Todos Immediately_, _Agent-orchestrator backlog is plan-driven_, and _Sub-Agents need full rules_ (the todo carries
  the context the cold worker needs). SSOT: `plans/PLAN_FORMAT.md` + `codex/12-agent-workflow/`.
- **Workflow-capable GH_TOKEN everywhere — no permission-based work-stoppage (HARD RULE codified 2026-06-01)**: every
  execution context — **each slot, the operator/Harsh main worktree, AND every orchestrator VM worker** — MUST have a
  `GH_TOKEN` that can edit `.github/workflows` (i.e. `GH_PAT` from Secret Manager, which carries fine-grained
  **"Workflows: read/write"**). The gh CLI **keyring login token (`gho_…`) lacks the `workflow` scope**
  (`repo, read:org, gist, admin:public_key` only), so any `gh`-API / HTTPS push that creates or updates a workflow file
  is silently refused — which stalled a CI v1→v2 migration mid-flight (2026-06-01). **Canonical load:**
  `source unified-trading-pm/scripts/workspace/load-gh-token.sh` (fetches `GH_PAT` from GCP SM → AWS SM, exports
  `GH_TOKEN`+`GITHUB_TOKEN`; env beats the keyring for gh + git). It is sourced by `workspace-bootstrap.sh` (local
  hosts) and MUST be exported into orchestrator VM worker envs by `agent-orchestrator/scripts/bootstrap_vm.sh`.
  `verify-slot-host-symmetry.sh` now probes workflow-capability (non-mutating PUT → 409/422 = OK, 403 = blocked) and
  FAILS a host that lacks it. **Note:** git push **over SSH** (a user key) is exempt from the workflow-scope
  restriction, so ssh-protocol slots can already push workflow files via `git`; this rule closes the `gh`-API / HTTPS
  path that is restricted. SSOT: `scripts/workspace/load-gh-token.sh` + `codex/12-agent-workflow/`.
- **Orchestrator regen is authoritative — yaml + state.db must match current plans. No zombies. (HARD RULE codified
  2026-05-30)**: `regen_backlog_from_plan.py` is the single source of truth for backlog state. `backlog.yaml` and
  `state.db` MUST reflect only tasks whose `- [ ]` checkbox is open in an active plan.
  `ORCHESTRATOR_REGEN_PRUNE_STALE=true` is the default on every fleet VM (enabled via
  `/etc/systemd/system/orchestrator.service.d/prune-stale.conf`). If you observe `state.db` queued-row count drifting
  more than ±5 from `backlog.yaml` task count on any VM, run `scripts/orchestrator/verify_fleet_prune_state.sh` to audit
  and `scripts/orchestrator/enable_prune_stale.sh` to re-enable pruning. SSOT:
  `plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md`.
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

Harsh AND Ikenna both run parallel agents. Untracked files / dirty mid-edit / recent remote commits = someone else's
in-flight work. **Do not touch files outside your clear context.**

- Never `git checkout origin/<branch> -- .` (dumps remote work) or `git checkout -- <file>` on foreign-owned dirty files
  (UNRECOVERABLE).
- Right recovery: (a) scope tool to YOUR files; (b) stash foreign files before tool runs; (c) accept you can't auto-fix
  foreign code.
- **Untracked file in a dep repo = NOT YOURS.**
- QG fails on file you don't own → tell the user.
- **Autostash conflict during rebase → `git rebase --abort`, do not patch around.** If `git pull --rebase --autostash`
  (or `git rebase --autostash`) reports `Applying autostash resulted in conflicts. Your changes are safe in the stash.`,
  the autostash holds **foreign-dirty** content that conflicted with the rebased HEAD. Safe recovery:
  `git rebase --abort` returns the repo to its pre-rebase state with the autostash intact. Then explicitly stash only
  YOUR files by name (`git stash push -- path/to/your_file`), redo the rebase, and pop your stash back. **NEVER
  `git checkout HEAD -- <conflicted_file>` to clear markers and then `git stash drop`** — that destroys the foreign
  agent's only copy of their WIP. The dropped-commit hash printed by `git stash drop` is reachable via
  `git stash store <hash>` until next GC, but treat that as a near-miss incident, not a routine path. Incident
  reference: slot-1 2026-05-19 strategy-service autostash drop (recovered via dangling commit, logged in
  `ikenna_orchestrator/pings/slot_1.md`). Full SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Step 7 —
  troubleshooting".
- **Concurrent agent in your shared `.tabs/<N>/` worktree (refs move under you) → isolated-worktree promotion, NOT
  `FETCH_HEAD`.** When another session OR an orchestrator-spawned worker shares your slot's `.git`, it rewrites `HEAD` /
  `FETCH_HEAD` / the slot branch mid-task: your push to `live-defi-rollout` is rejected and `FETCH_HEAD`-based
  diagnostics LIE (you may wrongly conclude "my work is already on LDR" — the moving `FETCH_HEAD` briefly pointed at the
  worker's local tip that contained your own commit). (1) Verify ONLY against the stable remote-tracking ref:
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` / `git cat-file -e origin/live-defi-rollout:<path>` —
  never `FETCH_HEAD`. (2) Do NOT autostash-rebase the shared dirty tree (same foreign-WIP foot-gun as above). (3)
  Promote YOUR work via a throwaway worktree off the integration branch — never touches the shared `.tabs/<N>/` tree, so
  the concurrent worker is undisturbed: `git worktree add --detach /tmp/promote-$$ origin/live-defi-rollout` →
  cherry-pick your commit → on conflict KEEP LDR's side for the other agent's hunks + trim any of their snapshot that
  auto-merged in but isn't on LDR (`git checkout origin/live-defi-rollout -- <file>` then re-add only your hunk) → gate
  on `git diff --cached origin/live-defi-rollout` showing YOURS-ONLY lines → push → `git worktree remove --force`. Full
  SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Isolated-worktree promotion under shared-worktree ref races".
  Incident: slot-1 2026-06-01 data-source-provenance promotion.

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

> **The #1 source of wasted reallocation + false-progress reporting.** Repeated violation observed 2026-05-14/15: slots
> 5+7 each shipped 15+ items without flipping work-split checkboxes; daily analysis reported ~14% progress when actual
> was ~70%. **Half-1 without Half-2 in the same agent turn is a rule violation — NOT "I'll do it later".**

**Half 1 — Commit + push at every shippable unit.** Pushed = real. Per-shippable-unit cadence, NOT per-hour, NOT
per-session.

Pre-commit check (MANDATORY — catches accidental bundling):

```bash
git status && git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything not yours: `git restore --staged <file>` before commit.

**Foot-gun #4** (prek auto-restore): bundle Edit→stage→commit→push into ONE Bash call. `--no-verify` IS authorized when
auto-restore symptoms observed (diagnostic: "Restored working tree changes from .../prek/patches/" in output). Stage
explicitly by name; never `git add .` / `-A`.

### Half 2 — Flip the checkbox IN THE SAME AGENT TURN as Half-1 (the most-violated half — read carefully)

**"Same logical unit"** = the next Bash invocation after the code push, in the same agent turn, before starting any new
item. NOT next session. NOT end of day. NOT "when I remember". If you committed code at 14:32 and the flip commit lands
at 17:50, you violated this rule for 3h18m.

**The compliance pattern (memorize)**:

```bash
# Step 1: ship code
cd <service-repo> && git add <my-files> && git commit -m "feat: ..." && git push origin HEAD:live-defi-rollout
SHA=$(git rev-parse --short HEAD)

# Step 2: IMMEDIATELY flip the plan checkbox (next Bash call, same turn)
cd ${WORKSPACE_ROOT}/unified-trading-pm
# Edit work_split or plan-of-record:
#   N. [item description]
# becomes
#   N. ✅ [item description] — <repo>@<SHA> + brief evidence
git add plans/active/<plan>.md
git commit -m "docs(plans): flip item N — <one-line evidence>" && git push origin HEAD:live-defi-rollout
```

**`docs(plans):` prefix is MANDATORY** for flip commits (`plan(...)` is rejected by the conventional-commits hook).

**Self-check before starting the NEXT item** (MANDATORY):

```bash
git log --oneline -5
# Expected: alternating "feat/fix/refactor: ..." and "docs(plans): flip ..." commits.
# Two consecutive code commits with no docs(plans) flip in between → STOP, flip before next item.
```

**Rule violations** (review-blocking; agent should self-correct before proceeding):

- ❌ "I'll flip at end of session" — other slots are reading the work-split RIGHT NOW for reallocation.
- ❌ "One batch flip commit at the end" — the next reallocation sweep may re-dispatch items 3+4 during the gap.
- ❌ "The code is on LDR, the flip is bookkeeping" — a flipped checkbox is the ORCHESTRATOR'S done-signal. Without it,
  the item is functionally unfinished from dispatch's view.
- ❌ "I forgot which item this commit closed" — you committed too many items in one push. Split next commit per
  shippable unit.
- ❌ Plan-flip commit lands hours/days after code commit — window is the SAME AGENT TURN.

**If you find unflipped items** (during recovery / audit / reassignment):

1. STOP picking up new work.
2. Walk your tab branch's git log since last known flip; for each code commit that closed an item, flip its checkbox
   with `- [x] ✅ ... — <repo>@<sha> (backfilled <date>)`.
3. Ship as one `docs(plans): backfill plan-flips for items X/Y/Z — <repos>@<shas>` commit. Push.
4. THEN resume normal work.

**Why this is THE wasted-reallocation source**: orchestrator reallocates based on work-split table state. Unflipped item
→ orchestrator may re-dispatch to another slot. Other slot reads the plan, doesn't see the LDR code (it reads the
checkbox, not a workspace grep), and re-implements. Net: wasted slot-hours + merge conflicts.

**Reference 2026-05-14/15 incident**: slots 5+7 each shipped 15+ items without Half-2. Three slots looked idle in
dashboard view when they were the workspace's top performers — operator nearly reallocated load away from them. Backfill
operation required to repair.

**Half 3 — Session-end deferred-work scoreboard.** Multi-item sessions with non-final state →
`## Deferred work after <date> <session-tag>` table in plan body before `## Temporary states`.

**The 3 halves compose**: Half-1 alone = "shipped but invisible"; Half-1+2 alone = "shipped + visible, missing context
for next agent"; Half-1+2+3 = full handoff. Half-3 matters when item is non-final; Half-2 ALWAYS matters when item is
final.

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

**Premise**: for every asset_group and every MVP archetype, **data exists**. If the public/free path is exhausted, the
unblock is a credential / subscription / account-provisioning ask to the operator — NOT a license to defer or descope
the adapter. Applies workspace-wide; primary targets are `instruments-service` and `market-tick-data-service` (MTDS)
adapters/handlers/clients, but the rule generalises (DeFi protocol-rate readers, sports/prediction feed adapters, tradfi
vendor SDKs, on-chain RPC providers).

**Banned reasoning patterns** (every one of these is a violation if it leads to scope removal):

- "No public API for X" → there's a paid tier (Helius for Solana, Alchemy paid for high-rate,
  Glassnode/Kaiko/IntoTheBlock for on-chain analytics, Tardis for historical CEX ticks, Databento/Polygon.io for tradfi,
  Sportradar/Footystats/The-Odds-API for sports).
- "Free tier exhausted" → upgrade the tier; this is a sub-1-hour operator credential swap, not a multi-week scope cut.
- "No test data" → mock the API contract from public docs + integration-test against the live endpoint once credentials
  land.
- "Subscription required" → that's the unblock, not the blocker. Ping operator.
- "Couldn't reproduce in sandbox" → ship the adapter, gate the integration test behind a `requires_credentials` mark.

**Required action when an agent hits this wall**:

1. **Build the adapter scaffold anyway.** Schema + UAC contract + auth shape + retry/backoff/rate-limit semantics +
   error classification (`classify_venue_error()`) + manifest emission per writegate Phase 6.x. Unit tests against mocks
   (per docs). Integration tests marked `@pytest.mark.requires_credentials` + skipped by default.
2. **File a `pings/slot_<N>.md` operator-credential request** with exact shape:
   ```
   CREDENTIAL APPROVAL REQUEST — <adapter_name>
   Vendor: <name + tier + cost estimate>
   What I need: <API key | OAuth flow | account email + signup | hardware-2FA setup>
   Account to use: <existing operator email | new account needed>
   Unblocks: <list of asset_group × archetype combos + which May-23 gate>
   Without it: integration tests skip; unit + scaffold ship + adapter is dormant
   ```
3. **Adapter stays ON the live list.** Status = `BLOCKED-CREDENTIALS`, NOT `DEFERRED` and NOT `POST-CUTOVER`. Plan-flip
   is `- [ ] [BLOCKED-CREDENTIALS — pinging operator]` not a checkbox flip.
4. **Cross-link in master plan.** Add row to `master_to_live_defi_2026_05_23.md` § "Credential asks awaiting operator"
   so it's visible in the daily inventory regenerator. (Section auto-created if absent.)
5. **Never move the adapter to a post-cutover plan without explicit operator [ack]** on the slot ping. Silent deferral =
   blocked PR.

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

**Enforcement**:

- Plan reviewer rejects any plan that contains "DEFERRED — no data" / "no API access" / "post-cutover — credentials"
  without an operator [ack] ping link.
- Inventory regenerator surfaces `BLOCKED-CREDENTIALS` count as a master plan column.
- PM `quality-gates.sh` runs `scripts/quality_gates/check_credential_ask_orphans.py` — baselined ratchet that fails on
  any `BLOCKED-CREDENTIALS` plan line lacking a ping reference (±5-line context: `*orchestrator/pings/slot_N.md` path,
  `CREDENTIAL APPROVAL REQUEST`, `[ack]`, named SM secret, or `CONFIRMED-STATUS`). Re-baseline only with
  `--baseline-write` after intentional debt.

Composes with: Findings Triage (this rule is the per-data-source case of "fix now if you have context"); Capture
Discoveries As Plan Todos (the ping IS the discovery capture); Commit + Push + Flip (the `BLOCKED-CREDENTIALS` status is
the plan-flip equivalent); Plans Run To Actual Completion (the adapter doesn't run to completion without credentials →
credentials are the operationally-shipped definition).

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

> Operator directive 2026-05-20: the data pipeline is the heartbeat of everything (paper-trade, strategy, execution).
> When a data audit surfaces issues, **every issue is fixed in full** — every missing venue × data_type × time range
> backfilled, every silent empty diagnosed, every schema-version row migrated, every batch adapter paired with a live
> equivalent. **No deferrals to hit a calendar deadline. No asset_group skipped.**

**The only legitimate deferral path** (closed set, agent never decides autonomously — operator-only):

- `BLOCKED-CREDENTIALS` — credential ask filed + operator-acked (per `External Data Is Always Available`).
- `BLOCKED-OPERATOR-DECISION` — operator explicitly articulates why a specific (venue, data_type, time-range) is removed
  from scope. Agent surfaces the gap + proposes options; operator decides scope.
- `BLOCKED-UPSTREAM-OUTAGE` — third-party degraded; ping logged; auto-resumes on health check.

**Banned reasoning patterns** (review-blocking):

- "We'll skip this for the deadline" — deadline ≠ license to ship broken data.
- "This asset_group is post-cutover" — every asset_group is in scope unless operator explicitly removes it.
- "Most cells captured, backfill the rest later" — every cell is in scope unless operator explicitly removes it.
- "The constant says v8, that's good enough" — code-constant ≠ data-state. Read the actual `schema_version` column
  distribution per bucket (incident 2026-05-20: 0% of 7.4M prod rows at v8 despite constant bump).
- "We'll do A5 / A6 later" — when a data audit names sub-audits (dependency-fail propagation, batch-live parity), those
  are part of the same gate, not optional extensions.

**Operational consequences**:

1. **Layer-N+1 work freezes when a data audit is RED for affected asset_groups** (foundation-completion-gate expansion —
   see `codex/11-project-management/foundation-completion-gate-discipline.md`).
2. **Slot reassignment is mandatory**: slot 1 main reassigns slots from layer-N+1 to data-fix work until the audit is
   GREEN. Slots that "double down on bad code" (build paper-trade / strategy / execution on top of unaudited data) are
   blocked, not deprioritised.
3. **Plan reviewer rejects** any plan proposing layer-N+1 changes while the relevant data audit has open P0 items
   without an operator-acked `BLOCKED-*` status.
4. **Every data audit MUST surface** (a) where it sampled vs walked exhaustively, (b) what coverage gaps remain. Audits
   without this transparency section are review-blocked.

**Composes with**: `Foundation-Completion-Gate Discipline` (data-correctness expansion of that gate);
`External Data Is Always Available` (per-data-source case — credentials unblock, not scope removal);
`Plans Run To Actual Completion` (operationally-shipped = every cell, not "most cells"); `Manifest + Honest Absence`
(per-cell expression — every cell either `captured` or `empty_confirmed[reason=<typed>]` with operator-acked reason).

**Reference incident (2026-05-20)**: Mega-audit Phase A surfaced 765 `DIVERGENT_EMPTY` + 236,892 `MISSING_EXPECTED`
cells across MTDS buckets + **0% of 7.4M prod manifest rows at v8** + 1.3M NULL-schema-version rows. Operator codifying
this rule: "I'm tired of doing this same thing a million times. We're on version eight for a reason. It's because you
keep being sloppy and keep missing out stuff."

**Full SSOT**: `codex/02-data/data-pipeline-correctness-hard-rule.md`.

**Operator-handoff entry point for migration coordination**: `plans/epics/mtds_mdps_master.md` — sequences (Phase -2)
strategy/ml/features repo consolidation finish → (Phase -1) workspace-wide QG green → (Phases 0-10) data-pipeline
migration as previously sequenced → (Phases 11-14) backfill-to-100% + live-data + batch-live-symmetry +
strategy/execution deployment-topology cleanup. Slot-1 main owns broadcast + ACK tracking; phase ordering is HARD (do
not reorder). Per-phase plan-of-record + owner slot + verification criterion in the coordinator plan.

**Quality Gates Are A Merge Prerequisite (HARD RULE — codified 2026-05-20 round 5)**: no code change merges to
`live-defi-rollout` (any service repo) without `bash scripts/quality-gates.sh` exit 0 for the touched repo + any
cross-repo consumers. Plan reviewers reject PRs that lack a QG-green evidence line. Harsh-side slots own the
workspace-wide QG-green sweep as a prerequisite for any ikenna-side migration work. Operator-tunable exemption only via
`BLOCKED-OPERATOR-DECISION` with explicit articulation. Composes with `Plans Run To Actual Completion` +
`Data Pipeline Correctness Is The Heartbeat`.

**Batch the GATE, not the commits — QG-sweep technique (codified 2026-06-02)**: `quality-gates.sh` is expensive
(~100–500s/run, worse under host contention), so when shipping MANY related code items (esp. across repos and/or via
parallel code-only sub-agents) do NOT run a full QG before every small edit. Instead: (1) make ALL the code edits for
the batch (code-only agents verify with `basedpyright` on touched files, NOT full QG); (2) run `quality-gates.sh` ONCE
per repo over the whole batch — a single green sweep validates all of that repo's edits; (3) THEN make
**per-shippable-unit commits + plan-flips** from that green tree (Commit + Push + Flip stays fully intact — only the
GATE RUNS are batched, never the commits). **Shared-host QG concurrency (HARD)**: the dev host is shared across ALL
slots — `quality-gates.sh`'s "keep parallel QGs to 1–2" warning is HOST-WIDE, not per-slot. Run **≤1–2 full QGs at
once** (full QGs serialize; code-only `basedpyright`-only agents parallelize safely); exceeding it OOM-kills gates (exit
144 mid-TESTS). **NEVER bulk-kill `pytest`/`quality-gates.sh`/`basedpyright` processes** (by pattern or PPID=1) — they
may belong to another slot's session (the process-space form of "don't touch outside your context"); stop only your own
tracked background tasks. When only the `<300s` (or inner `run_timeout`) META-gate trips under contention — all
substantive gates green — `IGNORE_TIMEOUT=true` / `PYRIGHT_TIMEOUT=<n>` are the sanctioned overrides (the gate prints
"ALL QUALITY GATES PASSED" + writes the sentinel). Full SSOT: `codex/06-coding-standards/quality-gates.md` § "QG-sweep
batching + shared-host concurrency". Composes with `Commit + Push + Flip` + `Quality Gates Are A Merge Prerequisite`.

**Every Active Ping Must Reference A Plan Item (HARD RULE — codified 2026-05-20 round 5; cadence tightened round 6)**:
no orphan pings in `plans/active/_agent_pings.md` / `ikenna_orchestrator/_agent_pings.md` /
`harsh_orchestrator/_agent_pings.md`. Every active entry MUST cite a plan-of-record (`plans/active/<slug>.md`,
`plans/epics/<slug>.md`, `plans/audit/<slug>.md`, or `plans/active/issues/<slug>.md`). Bare slug links to date-suffixed
plan files (`<slug>_YYYY_MM_DD.md`) inside the same ping-ledger directory also count.

**If an agent's ping references nothing**, the agent MUST EITHER (a) file a new plan / extend an existing one before
posting (preferred), OR (b) remove the ping. **Forcing agents to make plans or issues around their pings is the point**
— pings without plan-state get lost; plans persist + propagate via the inventory regenerator.

**Cadence**: every 4 hours (6×/day), NOT weekly. Cron stack:

- **Local** (Ikenna's machine, `crontab -e`):
  ```
  0 */4 * * * cd ${WORKSPACE_ROOT}/unified-trading-pm && bash scripts/agents/audit_ping_orphans.sh >> /tmp/orphan_pings_audit.log 2>&1
  ```
- **GCP Cloud Run Job + Cloud Scheduler** (`central-element-323112` / `asia-northeast1`, offset by 2h so passes don't
  collide): `15 2,6,10,14,18,22 * * *` UTC. Job name `uts-prod-orphan-ping-audit` clones unified-trading-pm @
  live-defi-rollout, runs the audit script, commits + pushes orphan notifications back to LDR. Image:
  `gcr.io/google.com/cloudsdktool/google-cloud-cli:slim`. GH PAT sourced from Secret Manager `GH_PAT`. Terraform SSOT:
  `deployment-service/terraform/gcp/orphan_ping_audit_scheduler.tf`. Entrypoint:
  `scripts/agents/cron_orphan_ping_audit_entrypoint.sh`. (AWS-VM path NOT used — agent-orchestrator's prod backend is
  Cloud Run; reusing the existing GCP cron stack avoids a new infra surface.)

When orphans are detected: the script appends a `## [orphan-ping-cron]` notification to BOTH orchestrator inboxes
(`ikenna_orchestrator/_agent_pings.md` + `harsh_orchestrator/_agent_pings.md`) listing every orphan + remediation steps.
Slot-1 main + harsh main are responsible for clearing the notification within one cron cycle (4h).

**Audit script SSOT**: `unified-trading-pm/scripts/agents/audit_ping_orphans.sh`. Composes with
`Capture Discoveries As Plan Todos Immediately` (every discovery is already a plan todo — pings just point at the todo).

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
