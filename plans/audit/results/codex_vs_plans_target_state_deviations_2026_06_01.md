---
type: analysis
title: Codex-vs-active-plans target-state deviation audit
epic: plan_hygiene_master
auditor: ikenna + claude (opus-1m, 6-worker fan-out split by codex dir)
date: "2026-06-01"
status: in-progress
source:
  - plans/active/*.md (46 active plans; ~36 reference codex)
  - codex/ (801 docs)
scope:
  "Where an active plan's TARGET END-STATE conflicts with / is missing from the codex doc it claims as SSOT. Goal:
  update codex AHEAD of archival so archival is mechanical."
method:
  6 read-only sonnet workers, one per codex-dir cluster (02-data; 04-architecture; 05-infrastructure;
  06-coding-standards+08-workflows; 12-agent-workflow+governance; 09-strategy+security+master). Each given the focused
  plan set referencing its dir. Opus consolidation + contradiction verification.
---

# Codex-vs-plans target-state deviation audit (2026-06-01)

> **Direction of truth**: codex = eventual SSOT; plans = declared target state. A deviation means codex does not yet
> reflect a target the plan declares shipped/canonical. Fix codex first → archival becomes a no-op.

## 0. HEADLINE — conflict requiring OPERATOR resolution (do NOT auto-fix)

**Agent-orchestrator integration branch: `main` vs `live-defi-rollout`.** Two 2026-06-01 operator-codified statements
directly contradict:

- Plan `cicd_contract_hardening_2026_06_01.md:136`: _"agent-orchestrator EXCEPTION — `main` is its target, NOT LDR
  (codified 2026-06-01, operator)."_
- Codex `codex/05-infrastructure/per-tab-worktrees.md:665-666`: _"FM6 per-repo base: every repo — INCLUDING
  agent-orchestrator — integrates via `live-defi-rollout`. Do NOT special-case agent-orchestrator to `main`."_

These may be reconcilable (deploy/promotion branch = `main` for Cloud Run; slot-worktree rebase base = LDR for spawn
hygiene) but as written they read as opposites, both citing the operator on the same day. **Resolve before editing
either side.** Until resolved, do NOT apply worker-recommended edits that touch this rule (04-architecture #13, 06/08
#4). Once resolved, the _losing_ side (plan or codex) must be corrected to match.

---

## 1. HIGH-CONFIDENCE codex-stale fixes (safe to apply — codex is behind shipped target state)

Grouped by theme; multiple workers corroborated several. Each row: codex doc → what to change.

### Theme A — Manifest schema version v8 → v9

- `codex/02-data/shard-granularity-cefi.md` + `codex/02-data/pipeline-coverage-matrix.md`: both say "Target: 100% of
  rows at **v8**". Plans (cefi/defi manifest_canonicalisation) target **v9**, and actual live schema rolled to v9
  2026-05-30. → update both to v9.
- `codex/02-data/data-lineage-MTDS-features-ml.md` "Features input discovery": says "v8 manifest" throughout → v9.

### Theme B — `source` column is now UNIVERSAL (not TradFi-only)

- `codex/02-data/availability-manifest-and-data-status.md` Column Rules (~L436), `AvailabilityRecord` code comments
  (L393/419), and the "TradFi `source` column — v9" section (~L1615): all still say _"source field (v9, TradFi only)"_ /
  `category=="tradfi"`. Shipped state (uac@aab101ad / utl@0f7198f2): `source` covers every external-vendor cell across
  all 5 asset groups; registry-driven auto-stamp single-source, `MissingSourceError` on multi-source blank. → strip
  "TradFi only"; rename section to "Universal `source` column — v9"; cross-link the already-correct
  `contracts-scope-and-layout.md` § "Generalised beyond TradFi".

### Theme C — `pipeline_mode=` on-disk partition no longer DEFERRED

- `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` status banner says "Phase 5 — DEFERRED". Plan
  `pipeline_mode_partition_migration_2026_06_01.md` re-scopes it as a named **rider** inside each AG's L3 single-walk. →
  update banner to "IN PROGRESS as named rider per AG L3 walk"; add the plan's per-bucket rider-coverage table (note
  instruments bucket still pending).

### Theme D — Manifest-reader fail-fast contract self-contradicts inside one doc

- `codex/02-data/availability-manifest-and-data-status.md`: the 2026-06-01 "liveness contract" section (L1399) already
  describes the inverted/default-RAISE behaviour (`MANIFEST_ALLOW_STALE_FALLBACK=true` escape-hatch), but the older
  2026-05-28 "opt-in" subsection (L1533) still describes default-OFF with `MANIFEST_FAIL_ON_STALE_FALLBACK`. → mark the
  2026-05-28 subsection "superseded 2026-06-01; raise is now default".

### Theme E — Venue-name underscore canonicalisation

- `codex/02-data/availability-manifest-and-data-status.md` protocol-coverage table (L1435/1436) shows `TRADER_JOEV2`
  (AVALANCHE) and `VELODROMEV2` (OPTIMISM); L431 calls `TRADER_JOEV2` an "intentional canonical underscore". Plan
  `defi_manifest_canonicalisation` §C12-UAC ships `TRADER_JOE_V2` / `VELODROME_V2` (uac@6261bea2) as the canonical form.
  → fix the two table rows + remove the L431 "intentional" claim.

### Theme F — EmptyConfirmedReason count 31 → 33 _(verified against UAC source)_

- `codex/02-data/honest-absence-downstream-handling.md` says "31-member `EmptyConfirmedReason` closed set" / "31-reason
  taxonomy". Verified actual enum in `unified-api-contracts/.../honest_coverage.py` = **33 members** (incl.
  `LEG_ABSENT_LEFT/RIGHT`, `SOURCE_RETURNED_ZERO`, `NO_INPUT_AVAILABLE`). CLAUDE.md (33) is correct; codex is stale. →
  update count to 33 + add the 2 LEG_ABSENT rows to the taxonomy table.

### Theme G — Orchestrator internal auth HS256 → ES256 _(corroborated by 3 workers, 4 docs)_

Shipped 2026-06-01 (`orchestrator_asymmetric_auth`): internal proxy token now ES256 (central holds private key in GCP
SM; workers verify with public key from GCS `internal-public.pem`; HS256 dual-accept during 48h soak). Stale docs:

- `codex/04-architecture/agent-orchestrator-overview.md` (two-secret/HS256 section + Tech-stack Auth row + "seam for
  later" language + "Auth flip rationale" HS256 provisioning recipe).
- `codex/12-agent-workflow/orchestrator-multi-vm-topology.md` (two-secret HS256 section; add
  `ORCHESTRATOR_INTERNAL_ALG`, `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS`). → update both to ES256 + asymmetric key
  distribution + soak note.

### Theme H — Fleet topology 10 → 11 VMs

- `codex/04-architecture/agent-orchestrator-overview.md` "Fleet topology": says "1 central + 10 epic VMs, 82 slots".
  Plans reference **11 VMs** (10 epic + 1 api-host). → update to 11 VMs / recomputed slot total.

### Theme I — WorkerLivenessWatchdog absent from overview

- `codex/04-architecture/agent-orchestrator-overview.md`: has its own final-status doc
  `agent-orchestrator-worker-liveness.md` but the overview has no section/mention. → add a "Worker liveness watchdog"
  section (3 triggers: stuck-at-prompt 180s / heartbeat-silent 900s / context-full immediate; anti-thrash gates;
  debounce vs `WorkerLivenessKicker`) + a row in the AutoSpawnLoop failure-modes table for "tmux alive but
  stuck/silent/context-full".

### Theme J — Watchdog enabled default true/false

- `codex/04-architecture/agent-orchestrator-worker-liveness.md` env table: default `false`. CLAUDE.md HARD RULE + plan
  Phase 4: enabled `true` on every fleet VM via systemd drop-in. → clarify: code default `false`; systemd-deployed
  default `true` on 10/11 VMs (vm-ml SSM-broken, watchdog not yet installed — add as known gap).

### Theme K — PlanRegen interval 6h → 30 min

- `codex/04-architecture/agent-orchestrator-overview.md` (L238) and
  `codex/12-agent-workflow/orchestrator-multi-vm-topology.md`: both say
  `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS default 21600 (6h)` / "≤6h latency". Plan
  `plan_hygiene_silent_failure_capture` Phase 6 shipped 1800s (30 min) fleet-wide + `pm-pull.timer` 5-min cadence. →
  update default to 1800 + note pm-pull 5-min cadence (≤35 min push-to-pickup).

### Theme L — Slack notify\_\* inventory stale in safety-mechanisms doc

- `codex/12-agent-workflow/orchestrator-safety-mechanisms.md` §C lists 11 funcs ("verified 2026-05-28"); 4 new ones
  shipped (`notify_unpushed_plans`, `notify_autospawn_flap`, `notify_watchdog_kill`, `notify_sync`). The authoritative
  `codex/05-infrastructure/agent-orchestrator-slack-notifications.md` IS already correct (13 Slack/9 Telegram). → add
  the 4 rows + cross-link the SSOT to stop the two drifting.

### Theme M — Spawn hygiene / liveness-gated dirty resolution

- `codex/12-agent-workflow/orchestrator-safety-mechanisms.md` §E + mirror in overview: still describe the OLD
  unconditional `git add -A` orphan-wip commit. Shipped (`orchestrator_autonomy_audit_remediation` Phase 4):
  liveness-gated `resolve_dirty_state` + `check_slot_branch_state` across all 3 spawn paths (9-FM coverage). The new
  model is documented in `per-tab-worktrees.md` but §E is stale. → replace §E with pointer + 3-outcome summary (dead
  predecessor→inherit; live peer→protect; wiped-index→quarantine).

### Theme N — CI v2 stale counts + template name + dep_repos rule

`codex/08-workflows/ci-cd-flow.md`:

- "all 10 repos rotated" / "21 Python repos" → fleet is **17 repos** (main+staging) all on `quality-gates-v2`.
- `workspace-qg.yml.tmpl` → **`quality-gates-v2.yml.tmpl`** (template renamed; v1 `python-quality-gates.yml` kept only
  as ghost-target).
- "dep_repos from `workspace-manifest.json` (canonical)" → now **BFS-transitive closure over pyproject
  `path="../<repo>"` editable deps**; manifest is fallback only.
- semver-agent: mark SHIPPED 2026-06-01 (24 repos, trigger `quality-gates-v2`); document `timeout-minutes: 135` +
  `if: failure()||cancelled()` as v2-callee contract. `codex/05-infrastructure/cicd-setup.md` Quick-Reference: "Fix a CI
  step → python-quality-gates.yml" → **v2** callee.

### Theme O — Workflow-capable GH_TOKEN HARD RULE missing

- `codex/08-workflows/ci-cd-flow.md` is silent on the 2026-06-01 HARD RULE: `source load-gh-token.sh` (SM-backed,
  `Workflows: write` scope) required before any `.github/workflows/*.yml` edit; default keyring token 403s. → add a
  "Workflow-file editing — GH_TOKEN scope" section.

### Theme Q — Bucket-name resolver domain-string contract (RC1 bug class)

- No codex doc names the rule behind the 2026-06-01 dual-write bug: a service domain string passed to
  `resolve_bucket_name` must match `_DOMAIN_TO_YAML_KIND` exactly (`market_data`, not `market-data-tick-{ag}`) or it
  silently falls through to the legacy flat name. → add a "Resolver domain-string contract" subsection to
  `codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md` (+ addendum noting the resolver was canonical but
  writers bypassed it via malformed domain; fix at market-tick-data-service@0b575651).

### Theme R — Manifest-consolidator legacy crons pending decommission

- `codex/05-infrastructure/manifest-consolidator-ssot.md` lists 20 GCP crons "all ENABLED" as canonical; 10 `*-legacy`
  flat crons are actually pending pause + TF removal once per-AG L3 reaches C-GREEN. → add "Pending decommission"
  callout; fix the stale "expect 10, target 5" verification comment (actual: 20 → 10 env-tiered).

### Theme S — Tarball SHA-pin prune incident

- `codex/05-infrastructure/vm-tarball-deployment.md` `cleanup_old_tarballs.py` section: add warning that a freshly
  uploaded `<repo>@<sha>.tar.gz` can be pruned within seconds (2026-06-01 20-shard launch all failed exit-2). Use a
  no-prune bucket / tune `--keep-n` before relying on SHA-pins for fan-out.

### Theme T — Quickmerge sentinel integration undocumented

- `codex/05-infrastructure/quickmerge-architecture.md` is silent on the `.qg_last_passed_sha` two-pass model. → add a
  "Sentinel integration" subsection (written by base-service.sh on full QG pass; read by quickmerge.sh:819 in --agent;
  partial runs don't write it → can't unblock).

### Theme U — Custody CEFFU June-1 (today IS 2026-06-01)

- `codex/04-architecture/custody-providers.md` §2.4: CEFFU still `<TBD-OPERATOR-PROVIDES-API-SPEC>` with "DEFERRED to
  June-1+". The June-1 target has arrived. → confirm flip landed (populate endpoints) or record revised timeline; the
  `<TBD>` markers block the implementation gate.

### Theme V — PnLFactor enum self-contradiction + duplicate vocabularies

`codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`:

- Ledger→attribution mapping (L745) uses `CARRY_FUNDING/CARRY_DIVIDEND/REALIZED_PNL/LOSS_LIQUIDATION` but the
  `PnLFactor` enum block (L538) lacks them → doc is self-contradictory. Reconcile (add members or remap).
- §"Reward P&L Factors" introduces a parallel `PNL_FACTOR_*` naming system for events already covered by `CARRY_*` →
  pick one vocabulary; map or formally add.
- Cross-reference `global_ledger_pnl_attribution_migration` Phase 8 as the trigger for the UAC enum PR (instead of
  leaving the ⚠ proposed sub-factors open-ended).

### Theme W — `unrealized_pnl` "always 0" now stale

- `pnl-attribution.md` Implementation-status (L785): "unrealized_pnl always returns 0 — MarkPrice not bridged". Shipped
  2026-05-30 (strategy-service@8deaf28): `_session_pnl_realized/_unrealized` wired into `BaseArchetypeEngineV2`. →
  update.

### Theme X — Regime-clustering ownership + algorithm

`codex/04-architecture/regime-clustering-structure-allocator.md`:

- "Service ownership" row: "features-service (fit); strategy-service (assign)" → plan ships `assign_clusters()` +
  `compute_proximity()` in **features-service** (features-service@68817bfb). Fix to "features-service (fit + assign)".
- Step 2: "GMM or k-means" → plan uses "GMM (soft) / **HDBSCAN**". Replace k-means with HDBSCAN.

### Theme Y — carry_staked_basis venue_universe includes excluded venue

- `codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` frontmatter `venue_universe` includes
  `HYPERLIQUID`, but the master plan (Q&A #2) and the doc body (`accepted=False`, 0 rows) exclude it (no ETH-LST
  margin). → remove HYPERLIQUID from the frontmatter list (or annotate `accepted=False`).

### Theme Z — Global-ledger DELTA note mis-describes enforcement

- `codex/04-architecture/global-ledger-architecture.md` DELTA note: "cross-client enforced by `@model_validator`".
  `client-funds-isolation.md` is authoritative: enforcement is **structural single-`client_id` field +
  `TransferCoordinator.execute()` runtime gate** (no model_validator). → correct the DELTA note to match.

### Theme AB — FeatureSpec fields missing from formula-versioning _(verified: codex lacks them)_

- `codex/02-data/feature-formula-versioning.md`: plan `features_registry_status_versioning` Phase 1 ships
  `custom_or_third_party: Literal["custom","ta_lib","pandas_std","numpy_std"]` + `formula_hash` on `FeatureSpec`.
  Verified absent from codex. → add both fields to the FeatureSpec narrative. (One worker mis-reported this as aligned;
  grep confirms missing.)

---

## 2. Non-codex staleness surfaced (CLAUDE.md / plan side — fix separately, not via codex)

- **Model tier "Opus 4.7" → "Opus 4.8"**: `codex/06-coding-standards/model-tier-selection.md` is already at 4.8
  (correct). CLAUDE.md header ("Sonnet 4.6 vs Opus 4.7") + `human_work_backlog_2026_05_20.md` slot table still say 4.7.
  Fix CLAUDE.md + the plan, NOT codex.
- **EmptyConfirmedReason 33**: CLAUDE.md correct; only codex needs the bump (Theme F).

---

## 3. Verified ALIGNED (workers checked, no action)

api-host auto-reboot/ceiling (15-min, SSM ceiling) · slack-notifications.md (15-row refresh) · per-tab-worktrees
`.code-workspace` path-style + FF-starvation watchdog · data-engine-selection (pure-Polars lock) ·
estimation-calibration multipliers · PYTEST_UNIT_DIR override · cli-promote-paths `LIVE_FULL` post-cutover · S3-snapshot
overview row · plan-hygiene.md / stale-blocker-reaper.md / claude-cli-multi-account-headless-auth.md (setup-token +
cross-operator pool).

---

## 4. Do-NOT-apply (worker recommendations contradicted by verification)

- 04-arch #13 / 06+08 #4 "add agent-orchestrator `main` exception note to codex": **blocked** by §0 conflict — codex
  per-tab-worktrees explicitly says LDR. Resolve §0 first.
