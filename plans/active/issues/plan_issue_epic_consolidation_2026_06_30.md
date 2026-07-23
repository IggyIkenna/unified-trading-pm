---
doc_type: issue
title: "Plan / Issue / Epic Consolidation — content-verified archive / slim / merge / link + a navigable ordering map"
summary:
  "The instruments-service + MTDS plan/issue set is too large and partly stale/done to navigate or trust. This is the
  consolidation exercise SCOPED TO instruments-service + MTDS ONLY (sports / prediction / defi-exec / features / infra /
  ui / ao kept as-is for now): CONTENT-verify each doc end-to-end (never trust frontmatter status), classify truly-done
  vs bandaid/partial/stale, then archive / SLIM (preferred) / merge / supersede / link-and-track / keep — and produce a
  single ordering map (do-now / parallel / blocked-by-gate) for the remaining IS+MTDS active work. Read-and-verify is
  fanned out to background agents in waves (PILOT first, then ≤6 parallel); agents propose dispositions which I write
  INTO this doc's ledger so the operator decides per-doc without blocking; synthesis + execution stay with the main
  loop. OPERATOR AGREED 2026-06-30 (pilot-first · ≤6 parallel · dispositions-in-doc · issues→plans · IS+MTDS-only)."
status: open
nature: record
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [consolidation, plan-hygiene, issue-triage, archival, ordering-map, ssot-audit]
related:
  [
    ./instruments_service_plan_reconciliation_2026_06_29.md,
    ./mtds_plan_reconciliation_2026_06_29.md,
    ../../PLAN_FORMAT.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-06-30
last_updated: 2026-06-30
assigned_vm: NA
execution_scope: local-only
priority: P1
parent_epic: plan_hygiene_master
source: [operator request 2026-06-30]
drift_direction: advance-code
depends_on: []
locked_by:
locked_since: 2026-06-30
resolved_by:
---

# Plan / Issue / Epic Consolidation (2026-06-30)

> **Goal:** turn the un-navigable **instruments-service + MTDS** plan/issue pile into a lean, trustworthy set + ONE
> ordering map. Every disposition is backed by an **end-to-end content check**, not a frontmatter status.
>
> **Scope (operator 2026-06-30): instruments-service + MTDS ONLY.** Sports, prediction, defi-execution, features/MDPS,
> ml/strategy, infra/cicd, ui, ao/role, pm/meta are **OUT — left exactly as-is** this pass (see §3a IN/OUT inventory).
>
> **Operator AGREED 2026-06-30** with these settings: (1) **pilot first** — one agent on one batch, verify rubric
> quality, then fan out; (2) **≤6 parallel** agents (gentle — avoid rate limits); (3) **dispositions written INTO this
> doc** (§6 ledger) — I do NOT block waiting per-batch; once the operator decides the archive-set we execute it; (4)
> **issues → then plans**; (5) **deliberate same-kind batching** (group docs addressing similar items). Archival (file
> move + `[unlock-plan]`) still waits for the operator's per-doc decision; everything up to that is recorded here.

## 0. Why (operator framing 2026-06-30)

Too many plans/issues/epics, much of it stale or already-done, so: (a) navigation is impossible; (b) there is no clear
"what to do now / what's parallel / what's gated"; (c) it's hard to confirm a plan was _actually_ implemented
end-to-end. This exercise fixes all three.

## 1. The HARD verification rule (the heart of this)

**Frontmatter status (`resolved` / `complete` / `[x]`) is a CLAIM, not proof.** For every doc an agent MUST read the
full content and verify the claim against live reality before any disposition:

1. **Claimed state** — frontmatter `status`, checkbox ratio, any "DONE/RESOLVED/G-gate-complete" banners.
2. **Verified state** — pick the doc's core claims/items and CHECK them against the live tree:
   - cited evidence resolves (commit exists + does what's claimed; `cloudbuild=<id>` is SUCCESS; manifest rows present);
   - the change is in **live code/data** (grep the symbol, read the consumer, query the manifest) — grep-0 ≠ done;
   - **quality gate**: is it a real root-fix or a **bandaid** (shim / `# type: ignore` / disabled test /
     `try/except ImportError` / TODO / "tracked separately")? Did it introduce a **regression**?
   - for an **issue**: is the ROOT CAUSE fixed in live code, or merely patched/worked-around?
3. **Verdict** — `TRULY-DONE` · `DONE-BUT-BANDAID` (works, carries tech-debt) · `PARTIAL` · `STALE` (newer code already
   moved past it) · `SUPERSEDED` (replaced by another doc) · `ACTIVE` (genuine open work).
4. **Evidence** — the agent records the exact checks (files/commands/symbols/build-ids) so the operator can trust the
   verdict without re-doing it. **No verdict without evidence.**

## 2. Disposition vocabulary (operator preference: SLIM > supersede+archive for low-value)

| disposition         | when                                                                       | action                                                                                          |
| ------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **ARCHIVE**         | `TRULY-DONE`, end-to-end verified, little residual reference value         | 5-step ritual → move to archived, done/superseded banner, clear lock (`[unlock-plan]` batch)    |
| **SLIM** _(prefer)_ | done but worth keeping as reference; bloated with completed detail         | trim completed sections to a 1-line summary + durable contract; KEEP active but lean            |
| **MERGE**           | duplicate / overlapping plans                                              | fold into one canonical; archive the merged-away as `superseded_by`                             |
| **SUPERSEDE+arch.** | replaced by a newer/better plan AND a fresh plan is warranted (high value) | new plan carries the open work; old → `superseded_by` + archive                                 |
| **LINK-AND-TRACK**  | OPEN issue whose fix IS covered by an active plan's tasks                  | cross-link issue↔plan + set issue `status: tracked` (or note the covering plan); do NOT archive |
| **KEEP**            | genuine active work, not bloated                                           | leave as-is (± trivial hygiene)                                                                 |

## 3. Phasing + ordering (operator-specified)

**Scope = instruments-service + MTDS plans/issues ONLY** (≈30 issues + ≈30 plans of the 84/124 total — see §3a).
**Issues first, then plans; epics a follow-up.** Everything outside IS+MTDS is untouched this pass.

- **Phase A — IS+MTDS Issues (≈30 docs, see §3a).**
  - **A1** content-verify each: `TRULY-RESOLVED` → ARCHIVE; else → open.
  - **A2** for each still-open issue: does an **active plan already carry tasks** that solve it? **YES** →
    LINK-AND-TRACK (cross-link + status `tracked`); **NO** → KEEP as-is (flag any that need a new task/plan).
- **Phase B — IS+MTDS Active plans (≈30 docs, see §3a).**
  - **B1** content-verify done-ness end-to-end (the §1 rule).
  - **B2** disposition: TRULY-DONE → ARCHIVE; low-value-done → **SLIM** (preferred); duplicates → MERGE; replaced(high
    value) → SUPERSEDE+archive; active → KEEP. Carry the IS/MTDS reconciliation Section-G/F decisions through (e.g.
    `mvp_*_v10` family now that the closeout is verified).
- **Phase C — Epics (follow-up).** Same rubric on the IS+MTDS-relevant epics once A+B land.
- **Phase D — The ORDERING MAP (the navigability deliverable).** From the surviving active IS+MTDS work, produce one
  ranked map: **DO-NOW** (unblocked, high-priority) · **PARALLEL** (independent, safe concurrently) · **BLOCKED/GATED**
  (name the gate + what unblocks it). This is the "what should we do now" the operator asked for.

## 3a. IN/OUT inventory + same-kind batches (operator can correct any boundary call)

**Domain judged by title/content, NOT the `repos:` field** (it is unreliable — many docs have `repos: []` or only
`unified-trading-pm`). **OUT-of-scope this pass** (left exactly as-is): all `sports_*`, `prediction*`/`predictions*`,
defi-execution/strategy (`defi_code_codex_drift`, `e2e_defi_*`, `defi_collateral*`, `defi_pipeline_e2e*`,
`defi_onchain_derivable*`, `defi_manifest_canon*`, `solana_defi*`), features/MDPS (`features_*`, `mdps_*`, `bar_edge*`,
`colocated_feature*`), ml/strategy, all infra/cicd/bucket-IAM/org/ci/devops/uat/ui/ao/role/pm/frontmatter/
doc-index/codex-audit, and personal masters (`harsh_day_master`, `work_split_*`). A `defi`/`features` doc that is really
about shared IS/MTDS **mvp-scope or manifest machinery** is flagged **(borderline)** and kept IN for coherence.

### Phase A — Issues (IS+MTDS), 5 same-kind batches

- **A1 — Manifest / phantom data-correctness (PILOT, 8):** `manifest_hygiene_red_2026_06_22`, `…_06_27`, `…_06_28`,
  `…_06_29` · `phantom_captures_cefi_2026_06_28` · `phantom_captures_tradfi_2026_06_28` ·
  `phantom_captures_defi_2026_06_28` (borderline) · `manifest_index_read_oom_canonical_cache_2026_06_24`. _Tests the
  rubric hard: a dated supersede-chain (4 hygiene snapshots) + content-verify of phantom remediation._
- **A2 — CeFi capture (6):** `cefi_free_venue_historical_refetch_mechanism_2026_06_21` ·
  `cefi_hl_aster_batch_data_gaps_2026_06_22` · `cefi_tardis_historical_blocked_credentials_2026_06_21` ·
  `cefi_universe_capture_rule_2026_06_23` · `live_tardis_machine_and_hl_aster_s3_batch_2026_06_21` ·
  `hyperliquid_rest_pipeline_mode_missed_by_v9_migration_2026_06_17` (status: resolved).
- **A3 — Live pipeline + TradFi capture (7):** `live_mode_event_sink_topic_missing_2026_06_21` ·
  `live_pipeline_persistence_hot_path_decoupling_2026_06_24` (resolved) ·
  `is_tradfi_trades_provenance_massive_vs_databento_skew_2026_06_24` · `krx_equity_twin_no_source_2026_06_28` ·
  `nasdaq_nyse_eu_silent_skip_2026_06_28` · `tradfi_backfill_oom_remediation_2026_06_24` ·
  `tradfi_eu_not_draining_source_axis_drift_2026_06_24`.
- **A4 — Honest-coverage + instrument correctness (6):** `coverage_merge_instrument_id_missing_2026_06_28` ·
  `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29` · `defi_perp_funding_mvp_scope_contradiction_2026_06_29`
  (borderline) · `perp_funding_data_semantics_and_cadence_2026_06_16` ·
  `vm_backfill_data_correctness_findings_2026_06_29` · `empty_reprobe_disagreement_2026_06_22`.
- **A5 — Data-pipeline plumbing (3):** `data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27`
  (borderline) · `gcs_hive_partition_malformed_paths_remediation_2026_06_01` ·
  `macro_micro_econ_data_capture_audit_2026_06_05` (borderline).
- **KEEP (ours, in-flight, not verified by an agent):** `instruments_service_plan_reconciliation_2026_06_29`,
  `mtds_plan_reconciliation_2026_06_29`, this doc.

### Phase B — Plans (IS+MTDS), 5 same-kind batches

- **B1 — MVP backfill / scope / catalogue v10 family (7):** `mvp_backfill_cefi_tick_v10_2026_06_27` ·
  `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27` · `mvp_backfill_defi_onchain_v10_2026_06_27` (borderline) ·
  `mvp_catalogue_finalization_v10_2026_06_27` · `mvp_reconciliation_closeout_v10_2026_06_27` ·
  `mvp_scope_catalogue_tagging_2026_06_08` · `mvp_for_mdps_and_features_universe_uac_2026_06_28` (borderline).
- **B2 — Honest-coverage + instruments catalogue/universe (7):** `honest_coverage_v2_instrument_denominator_2026_06_28`
  · `honest_coverage_v2_opus_checkpoints_2026_06_28` · `honest_coverage_smoke_harness_2026_06_28` ·
  `instruments_catalogue_incremental_rollup_2026_06_29` · `instruments_foundation_completeness_2026_06_24` ·
  `instruments_mtds_subset_consistency_remediation_2026_06_17` ·
  `instrument_universe_registry_consolidation_2026_06_29`.
- **B3 — CeFi + TradFi data (6):** `cefi_deribit_binance_futures_bundle_verification_2026_06_20` ·
  `cefi_manifest_canonicalisation_2026_06_01` · `tradfi_manifest_canonicalisation_2026_06_01` ·
  `tradfi_massive_dual_source_2026_05_28` · `tradfi_multisource_backfill_2026_06_22` ·
  `tradfi_cme_event_contract_backfill_2026_06_20` (borderline).
- **B4 — pipeline_mode / provenance / backfill coordination (7):** `pipeline_mode_partition_migration_2026_06_01` ·
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` ·
  `data_source_provenance_all_asset_groups_2026_06_01` · `path_to_100pct_backfill_mtds_is_2026_06_17` ·
  `data_completion_to_100_all_ag_2026_06_21` · `mtds_file_size_refactor_2026_06_08` (status: deferred) ·
  `macro_econ_adapter_scaffolds_2026_06_09`.
- **B5 — Data master-coordinators (borderline-infra, 4):** `master_data_canonicalisation_migration_catalogue_2026_06_07`
  · `migration_verification_orphan_safety_2026_06_10` · `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`
  (borderline) · `cross_ag_shard_4pillar_validation_harness_2026_06_19` (borderline).

## 4. Background-agent fan-out (read-only verify; synthesis + execution stay here)

Agents VERIFY + PROPOSE; they **never edit/archive**. **Each agent gets `SUB_AGENT_MANDATORY_RULES.md` at spawn top**
(if injection fails, the agent must not proceed). **≤6 parallel** (operator: gentle — avoid rate limits). **One agent
per same-kind batch** (§3a), each agent verifying ~6–8 docs so it holds coherent context.

- **PILOT (1 agent):** batch **A1** only. I inspect the returned verdicts for rubric quality (did it actually open files
  / grep symbols / query manifests, or just restate frontmatter?) **before** fanning out. Bad rubric → tighten the
  prompt + re-pilot; good → proceed.
- **Wave A (issues):** remaining batches A2–A5 → 4 agents, run **≤6 at a time**. Structured per-issue verdict.
- **Wave B (plans):** batches B1–B5 → 5 agents, run **≤6 at a time**. Structured per-plan verdict.
- **Output schema (every agent, per doc):**
  `{slug, claimed_status, verified_verdict, evidence[], disposition, covering_plan, lock, notes}` → I merge into the
  **§6 disposition ledger**.
- **Then (dispositions-in-doc, operator does NOT block):** I synthesize each batch's verdicts straight into §6 with the
  proposed disposition. The operator reviews §6 and says which to archive; I execute ONLY the agreed archive-set
  (archival ritual / slim edits / merges / links) in slot 1. Verdict-writing does not wait; archival waits for the
  per-doc decision.

## 5. Guardrails

- **Verify, don't trust** (§1) — the whole point; a flipped checkbox is not evidence.
- **Locks are boilerplate** (`locked_by: live-defi-rollout` on 98 plans) — per operator, archive only AFTER end-to-end
  verification; clear the lock via a batched `[unlock-plan]` commit (human-gated; I prepare, operator authorizes).
- **SLIM is preferred** over supersede+archive for low-value done plans.
- **Archival = the 5-step ritual** (migrate DEFERRED → banner → codex-alignment check → update CLAUDE.md/codex on a
  changed contract → clear lock). No silent deletes; never `git reset --hard`/`clean`.
- **Dispositions-in-doc (operator 2026-06-30)** — agents propose, I write verdicts+proposed-disposition into §6 without
  blocking; the operator reads §6 and names the archive-set; main loop executes ONLY that set, never auto-archives in
  bulk.
- **Doc edits push** (this is a `docs(plans):` change → direct-push-to-LDR carve-out); **archival file-moves +
  `[unlock-plan]` wait** for the operator's per-doc decision.

## 6. Disposition ledger (filled during execution)

> One row per doc. Agent-verified (content, not frontmatter) + spot-checked by the main loop. **`ARCHIVE` / `SUPERSEDE`
> rows are PROPOSED — they execute only once the operator names the archive-set.** `LINK-AND-TRACK` / `SLIM` / `KEEP`
> are non-destructive and I can apply them on the push the operator already authorized.

### Phase A — Issues

#### Batch A1 — manifest / phantom data-correctness (verified 2026-06-30; pilot + main-loop spot-check)

| #    | slug                                                 | claimed                        | verified verdict     | proposed disposition                                                                       | covering plan / successor                                                                     |
| ---- | ---------------------------------------------------- | ------------------------------ | -------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| A1.1 | `manifest_hygiene_red_2026_06_22`                    | open (no todos)                | STALE→SUPERSEDED     | **SUPERSEDE+archive** → successor `…_06_27` (later defi snapshot)                          | `data_pipeline_hardening_self_monitoring_2026_06_22` (defi DIVERGENT_EMPTY P1 still `[ ]`)    |
| A1.2 | `manifest_hygiene_red_2026_06_27`                    | open (1 `[ ]`)                 | ACTIVE               | **LINK-AND-TRACK** (live defi hygiene ref)                                                 | `data_pipeline_hardening_self_monitoring_2026_06_22`                                          |
| A1.3 | `manifest_hygiene_red_2026_06_28`                    | open (1 `[ ]`)                 | STALE→SUPERSEDED     | **SUPERSEDE+archive** → successor `…_06_29` (later cefi snapshot)                          | `mvp_backfill_cefi_tick_v10_2026_06_27`                                                       |
| A1.4 | `manifest_hygiene_red_2026_06_29`                    | open (1 `[ ]`)                 | ACTIVE               | **LINK-AND-TRACK** (live cefi hygiene ref)                                                 | `mvp_backfill_cefi_tick_v10_2026_06_27` (OKX-SWAP DIVERGENT_EMPTY + 780 HL phantoms, G4 gate) |
| A1.5 | `phantom_captures_cefi_2026_06_28`                   | open (P2✅/P1`[ ]`)            | PARTIAL              | **LINK-AND-TRACK** (P1 HL-phantom apply blocked on VM term)                                | `mvp_backfill_cefi_tick_v10_2026_06_27` (L540-606)                                            |
| A1.6 | `phantom_captures_tradfi_2026_06_28`                 | open (P2✅/P1`[ ]`)            | PARTIAL (apply done) | **SLIM** (apply 0-phantom-confirmed; P1 ICE diag low-impact, billing-blocked)              | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27` (G1 = 0 phantoms)                                |
| A1.7 | `phantom_captures_defi_2026_06_28`                   | open (all `[ ]` — STALE boxes) | PARTIAL              | **LINK-AND-TRACK** (apply DONE 219,632 flipped; writer root-cause + post-fill verify open) | `mvp_backfill_defi_onchain_v10_2026_06_27` (L62/613/1189)                                     |
| A1.8 | `manifest_index_read_oom_canonical_cache_2026_06_24` | open (no todos)                | ACTIVE               | **KEEP** (latent fleet-OOM; Option A/B unimplemented; only config workaround applied)      | none found — needs a `[ ]` task vs UTL `_state.py:149-173`                                    |

**A1 supersede-chain finding (verified):** the four `manifest_hygiene_red` snapshots are **two chains, not one** —
`06_22→06_27` are **defi** (DIVERGENT_EMPTY, 22,140→15,697), `06_28→06_29` are **cefi** (OKX-SWAP empty + HL phantoms).
So only the OLDER of each pair is superseded: **A1.1 + A1.3 → SUPERSEDE+archive**; the newest of each pair (A1.2, A1.4)
stays as the live hygiene reference, link-tracked. The three `phantom_captures` docs are **independent per-AG** (tradfi
apply fully done, cefi apply blocked-on-VM, defi apply done-but-writer-unverified) — not one family.

**A1 spot-check (main loop):** verified verbatim — UTL `_state.py:118` (`_CANONICAL_CACHE: dict[...] = {}`) + `:173`
(`# NOTE: _CANONICAL_CACHE is intentionally NOT popped here`) → OOM root cause genuinely unpatched (A1.8 ACTIVE
confirmed); defi plan `:62`/`:613`/`:1189` (`219,632 phantoms flipped … 2026-06-28T21:35Z`) → A1.7 apply-done confirmed.

**A1 quality flags (fix at execution, not now):** `assigned_vm: vm-cross-cutting` on A1.2/A1.3/A1.4 is an **invalid
frontmatter value** (schema allows only `planning`/`NA`) — correct to `NA` when touching each (A1.3 is archived anyway).

> **PROPOSED A1 ARCHIVE-SET (awaiting operator OK):** `manifest_hygiene_red_2026_06_22` +
> `manifest_hygiene_red_2026_06_28` (both superseded by their later same-AG snapshot; both link-tracked to a still-open
> covering plan, so no information is lost on archive). Everything else in A1 is non-destructive (LINK-AND-TRACK / SLIM
> / KEEP).

#### Batch A2 — CeFi capture (verified 2026-06-30; agent + main-loop spot-check)

| #    | slug                                                               | claimed                    | verified verdict        | proposed disposition                                                                           | covering plan / successor                                                            |
| ---- | ------------------------------------------------------------------ | -------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| A2.1 | `cefi_free_venue_historical_refetch_mechanism_2026_06_21`          | open (no todos)            | SUPERSEDED              | **SUPERSEDE+archive** → `live_tardis_machine_and_hl_aster_s3_batch_2026_06_21`                 | (work absorbed; `mvp_backfill_cefi_tick_v10_2026_06_27`)                             |
| A2.2 | `cefi_hl_aster_batch_data_gaps_2026_06_22`                         | open (P0s open)            | PARTIAL                 | **SLIM + LINK-AND-TRACK** (BUG#1-4 shipped; P0 consolidator-noop + tail open)                  | `mvp_backfill_cefi_tick_v10_2026_06_27`                                              |
| A2.3 | `cefi_tardis_historical_blocked_credentials_2026_06_21`            | open (BLOCKED-CREDENTIALS) | NEEDS-LIVE-CHECK ⚠️     | **KEEP — operator-decision** (see ⚠️ flag below)                                               | `data_completion_to_100_all_ag_2026_06_21` / `mvp_backfill_cefi_tick_v10_2026_06_27` |
| A2.4 | `cefi_universe_capture_rule_2026_06_23`                            | open (2 stale `[ ]` P0)    | PARTIAL                 | **SLIM + LINK-AND-TRACK** (durable capture-rule SSOT; 2 stale P0 boxes — work done in live IS) | `mvp_backfill_cefi_tick_v10_2026_06_27`                                              |
| A2.5 | `live_tardis_machine_and_hl_aster_s3_batch_2026_06_21`             | open                       | PARTIAL (core resolved) | **SLIM + LINK-AND-TRACK** (= the A2.1 successor; tardis-machine + batch-symmetry SSOT)         | `mvp_backfill_cefi_tick_v10_2026_06_27`                                              |
| A2.6 | `hyperliquid_rest_pipeline_mode_missed_by_v9_migration_2026_06_17` | resolved (3 `[ ]` P3)      | TRULY-RESOLVED (core)   | **SLIM** (core migration real; 3 cosmetic P3 read-token cleanups open)                         | `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`                  |

**A2 spot-check (main loop):** verified verbatim — `live_tardis_machine…:81-82` explicitly supersedes A2.1; IS
`parsing.py:433-436` (`FULL-UNIVERSE enumeration … CEFI_BASE_ASSET_UNIVERSE … NO LONGER a gate`) → A2.4's `[ ] P0` is
genuinely stale; the Tardis contradiction below is real (doc2:426 vs doc3:72).

> **⚠️ OPERATOR-DECISION FLAG (A2.3) — Tardis historical billing gate, contradictory state:**
> `cefi_hl_aster_batch_data_gaps_2026_06_22.md:426` says **"Tardis batch billing gate LIFTED — operator paid; access
> confirmed unlimited"** (2026-06-23), but `cefi_tardis_historical_blocked_credentials_2026_06_21.md:72` still reads
> **"BLOCKED-CREDENTIALS — operator has currently EXCLUDED this spend"**, and `data_completion_to_100_all_ag:163` still
> says "Batch Tardis (historical) EXCLUDED". **775.9k attempted_failed cells hinge on this.** If the gate is lifted →
> backfill those cells + flip A2.3 to `tracked`/archive; if still excluded → A2.3 KEEP and doc2:426's "LIFTED" note is
> premature. **Needs your confirmation.**

> **PROPOSED A2 ARCHIVE-SET (awaiting operator OK):** `cefi_free_venue_historical_refetch_mechanism_2026_06_21` (A2.1 —
> superseded same-day by `live_tardis_machine_and_hl_aster_s3_batch`, which explicitly names it; no info loss).
> A2.2/2.4/2.5/2.6 are non-destructive (SLIM/LINK/KEEP); A2.3 is operator-gated.

**Recurring schema flag (A1+A2):** invalid `assigned_vm` values are systemic — `vm-cross-cutting` (A1.2-A1.4) and
**blank** (all 6 A2 docs). Valid set is `{planning, NA}`. Fix to `NA` when touching each (cheap; do at execution).

#### Batch A3 — Live pipeline + TradFi capture (verified 2026-06-30; agent + main-loop spot-check)

| #    | slug                                                               | claimed              | verified verdict | proposed disposition                                                                                                                     | covering plan / successor                                                                              |
| ---- | ------------------------------------------------------------------ | -------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| A3.1 | `live_mode_event_sink_topic_missing_2026_06_21`                    | open (no todos)      | PARTIAL          | **KEEP** (root naming Option A/B undecided; `_sink_factory.py:44` still `{svc}-events`; fleet-wide blast radius — **needs a plan task**) | `data_completion_to_100_all_ag_2026_06_21` (refs only, no `[ ]`)                                       |
| A3.2 | `live_pipeline_persistence_hot_path_decoupling_2026_06_24`         | **resolved (WRONG)** | PARTIAL          | **SLIM + correct status** (`LiveEventFacadeSink` is live, but warm-GCS-parts tier UNBUILT per M-C7 → status:resolved overstates)         | M-C7 (mtds recon) — needs a live-mode build task                                                       |
| A3.3 | `is_tradfi_trades_provenance_massive_vs_databento_skew_2026_06_24` | open (stale)         | TRULY-RESOLVED   | **ARCHIVE** (test renamed → `…databento_batch_rest`, asserts `batch_databento`)                                                          | (tradfi databento-first flip 2026-06-24)                                                               |
| A3.4 | `krx_equity_twin_no_source_2026_06_28`                             | open (2/2 `[x]`)     | TRULY-RESOLVED   | **ARCHIVE** (reclass script applied; eu 378→0; G2 gate met)                                                                              | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27`                                                           |
| A3.5 | `nasdaq_nyse_eu_silent_skip_2026_06_28`                            | open (8/8 `[x]`)     | TRULY-RESOLVED   | **ARCHIVE** (`raw_symbol.upper()` + `EXPECTED_SOURCE_DELIVERY_LAG` in 2 repos; eu=0 G2 gate)                                             | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27`                                                           |
| A3.6 | `tradfi_backfill_oom_remediation_2026_06_24`                       | open (3`[x]`/3`[ ]`) | PARTIAL          | **SLIM + LINK-AND-TRACK** (P0 e2-highmem-4 default landed; 3 cleanup todos open)                                                         | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27`                                                           |
| A3.7 | `tradfi_eu_not_draining_source_axis_drift_2026_06_24`              | open (2 `[ ]`)       | PARTIAL          | **LINK-AND-TRACK** (P1 re-enumerate gated on IS catalogue rebuild; P2 barchart 4,655 rows = operator go/no-go)                           | IS catalogue plan (`instruments_catalogue_incremental_rollup` / `…_foundation_completeness` — confirm) |

> **PROPOSED A3 ARCHIVE-SET (awaiting operator OK):** `is_tradfi_trades_provenance_massive_vs_databento_skew_2026_06_24`
> · `krx_equity_twin_no_source_2026_06_28` · `nasdaq_nyse_eu_silent_skip_2026_06_28` — all three TRULY-RESOLVED, code
> confirmed live in 2 repos, eu=0 proven via the `mvp_backfill_tradfi_ohlcv1m_v10` G2 gate. **Note the inversion:** all
> three carry a stale `status: open` while the fix shipped — exactly the frontmatter-unreliability this pass exists to
> catch.

#### Batch A4 — Honest-coverage + instrument correctness (verified 2026-06-30; agent + main-loop spot-check)

| #    | slug                                                          | claimed              | verified verdict  | proposed disposition                                                                                                                                                                                                                    | covering plan / successor                                                                            |
| ---- | ------------------------------------------------------------- | -------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| A4.1 | `coverage_merge_instrument_id_missing_2026_06_28`             | open (1/1 `[x]`)     | TRULY-RESOLVED    | **ARCHIVE** (fix `f81e339`: `_SHARD_KEY_WITH_IID` live + regression test)                                                                                                                                                               | `honest_coverage_v2_instrument_denominator_2026_06_28`                                               |
| A4.2 | `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29` | open (1`[x]`/4`[ ]`) | PARTIAL           | **LINK-AND-TRACK** (4 CODE todos open; ASTER carve-out = C1/C2 → Ikenna)                                                                                                                                                                | `instrument_universe_registry_consolidation_2026_06_29`                                              |
| A4.3 | `defi_perp_funding_mvp_scope_contradiction_2026_06_29`        | open (4 `[ ]`)       | PARTIAL/ACTIVE ⚠️ | **KEEP — operator-gated** (3-way SSOT contradiction LIVE: `mvp_scope` v12 has no PERPETUAL but `defi_venue_capabilities:139 DRIFT-SOLANA:{perp_funding}` still in registry; P0 ruling pending Ikenna; Harsh provisional = out-of-scope) | `mvp_backfill_defi_onchain_v10_2026_06_27` + `instrument_universe_registry_consolidation_2026_06_29` |
| A4.4 | `perp_funding_data_semantics_and_cadence_2026_06_16`          | open (mixed)         | PARTIAL           | **SLIM** (P1 FUNDING_PERIODS_PER_DAY deletion + Aster legs done; Finding 2/3 + P3 open — **no plan task carries Finding 2/3**)                                                                                                          | none for Finding 2/3 (flag for a task)                                                               |
| A4.5 | `vm_backfill_data_correctness_findings_2026_06_29`            | open (3/6 fixed)     | PARTIAL/ACTIVE    | **KEEP** (F1/F2/F3 fixed w/ SHAs; F4 BLOCKED-CREDENTIALS; F5/F6 verify-first; F7 TradFi-ungated keystone open)                                                                                                                          | per-finding (F5→cefi mvp, F6→IS foundation, F7→none)                                                 |
| A4.6 | `empty_reprobe_disagreement_2026_06_22`                       | open (no todos)      | STALE/PARTIAL     | **LINK-AND-TRACK** (8-day-old snapshot; CURVE row = vm_backfill F4 BLOCKED; reprobe cron self-files)                                                                                                                                    | `data_pipeline_hardening_self_monitoring_2026_06_22`                                                 |

> **PROPOSED A4 ARCHIVE-SET (awaiting operator OK):** `coverage_merge_instrument_id_missing_2026_06_28` (A4.1 —
> TRULY-RESOLVED, fix `f81e339` verified live, regression-tested). Everything else KEEP/LINK/SLIM (non-destructive).

> **⚠️ OPERATOR-DECISION FLAGS (A3/A4) — tie into already-pending items:** (1) **A3.2** = M-C7: the warm-GCS-parts live
> persistence build (already decided, awaiting your greenlight). (2) **A4.3** = `defi_perp_funding` MVP-scope ruling —
> the same C-series Ikenna decision; Harsh's provisional call is "out of MVP scope," UAC code fix deferred until Ikenna
> confirms.

**Open-issue / no-covering-plan gaps surfaced (Phase-A2 "needs a new task"):** A3.1 (event-sink Option A/B convention) ·
A4.4 (funding_timestamp per-settlement offset + historical cadence tracker) · A4.5-F7 (TradFi enumerator not
`is_mvp`-gated) · A3.7-P1 (tradfi re-enumerate, gated on IS catalogue rebuild). I'll collate these into a "needs-task"
list at Phase D.

#### Batch A5 — Data-pipeline plumbing (verified 2026-06-30; agent + main-loop spot-check)

| #    | slug                                                                         | claimed                    | verified verdict | proposed disposition                                                                                                                                      | covering plan / successor                                                             |
| ---- | ---------------------------------------------------------------------------- | -------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| A5.1 | `data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27` | open (4`[x]`/2`[ ]`)       | PARTIAL          | **SLIM** (Finding 1 DP_NOT_V9 + Finding 2 rate-limit shipped w/ regression tests `e2e@21ce846`/`deploy@d36f281`; Finding 3 debounce + IS-handler P3 open) | `data_pipeline_hardening_self_monitoring_2026_06_22` (Finding 3 untracked — flag)     |
| A5.2 | `gcs_hive_partition_malformed_paths_remediation_2026_06_01`                  | open (3`[x]`/2 SUPERSEDED) | PARTIAL          | **SLIM → ARCHIVE-when-successors-apply** (doc-drift + env-tier + QG-guard shipped; 2 GCS remediations SUPERSEDED into B3 plans)                           | `cefi_manifest_canonicalisation` E2 + `tradfi_manifest_canonicalisation` E7 (both B3) |
| A5.3 | `macro_micro_econ_data_capture_audit_2026_06_05`                             | open (audit; Phase 0 done) | ACTIVE           | **LINK-AND-TRACK** (Phase 2 adapters built; Phases 1 FRED-run + 3–6 untracked)                                                                            | `macro_econ_adapter_scaffolds_2026_06_09` (Phase 2 only)                              |

**A5 spot-check (main loop):** verified — `_gcs.py:479-490` rate-limit classifier present;
`scripts/qg/no_malformed_by_date_paths.sh` exists + SUPERSEDED banner routes to cefi/tradfi canon; all 4 macro adapters
exist. No ARCHIVE candidates in A5 (all PARTIAL/ACTIVE).

---

### ✅ PHASE A COMPLETE — 30 IS+MTDS issues content-verified (5 batches, all main-loop spot-checked)

**PROPOSED ARCHIVE-SET (7 docs, awaiting operator OK — execute together with one `[unlock-plan]` batch):**

| slug                                                               | why archivable                                                                      | safety                                                  |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `manifest_hygiene_red_2026_06_22`                                  | superseded by `…_06_27` (later defi snapshot)                                       | link-tracked to still-open `data_pipeline_hardening`    |
| `manifest_hygiene_red_2026_06_28`                                  | superseded by `…_06_29` (later cefi snapshot)                                       | link-tracked to still-open `mvp_backfill_cefi_tick_v10` |
| `cefi_free_venue_historical_refetch_mechanism_2026_06_21`          | superseded same-day by `live_tardis_machine_and_hl_aster_s3_batch` (which names it) | successor carries full resolution                       |
| `is_tradfi_trades_provenance_massive_vs_databento_skew_2026_06_24` | TRULY-RESOLVED — test renamed to databento-first                                    | QG-green; stale `status: open`                          |
| `krx_equity_twin_no_source_2026_06_28`                             | TRULY-RESOLVED — reclass applied, eu=0 via G2 gate                                  | covering plan has G2 evidence                           |
| `nasdaq_nyse_eu_silent_skip_2026_06_28`                            | TRULY-RESOLVED — fixes in 2 repos, eu=0 via G2 gate                                 | covering plan has G2 evidence                           |
| `coverage_merge_instrument_id_missing_2026_06_28`                  | TRULY-RESOLVED — fix `f81e339`, regression-tested                                   | QG-green; stale `status: open`                          |

**+1 deferred-archive:** `gcs_hive_partition_malformed_paths_remediation_2026_06_01` → archive once cefi-canon E2 +
tradfi-canon E7 applies land (verify in Phase B3).

**OPERATOR-DECISION FLAGS (3):** ⚠️ Tardis historical billing gate (A2.3 — 775.9k cells; LIFTED-vs-BLOCKED) · ⚠️
`defi_perp_funding` MVP-scope ruling (A4.3 — Ikenna; Harsh provisional = out-of-scope) · M-C7 warm-GCS-parts build
greenlight (A3.2 — already pending).

**NEEDS-NEW-TASK (open issue, no covering plan):** A3.1 event-sink `{svc}-events` Option A/B convention · A4.4
funding_timestamp per-settlement offset + historical cadence tracker · A4.5-F7 TradFi enumerator not `is_mvp`-gated ·
A3.7-P1 tradfi re-enumerate (gated on IS catalogue rebuild) · A5.1 Finding-3 GONE_NO_CAPTURE debounce · macro Phases
1/3–6.

**SYSTEMIC FRONTMATTER (batch-fix at execution):** invalid `assigned_vm` (blank on ~12 docs, `vm-cross-cutting` on 3) →
set `NA`; stale `locked_since: 2026-05-21` predating `created` on several (template artifact). Non-destructive cleanup.

### Phase B — Plans (31 IS+MTDS plans, 5 batches, all main-loop spot-checked)

#### Batch B1 — MVP backfill / scope / catalogue v10 family

| #    | slug                                                | claimed (status·boxes) | verdict    | disposition                               | notes                                                                                                   |
| ---- | --------------------------------------------------- | ---------------------- | ---------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| B1.1 | `mvp_backfill_cefi_tick_v10_2026_06_27`             | active · 4/5           | ACTIVE     | **KEEP**                                  | G4 gate open (af>0, wave-2 VMs unlaunched); A8/A12/A18 v10→v12 conflicts                                |
| B1.2 | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27`        | active · 4/4 (0 open)  | TRULY-DONE | **ARCHIVE** (needs `[unlock-plan]`)       | G2 GATE MET 2026-06-29 `mtds@a49403e2`; MTDS-recon ALIGNED                                              |
| B1.3 | `mvp_backfill_defi_onchain_v10_2026_06_27`          | active · 7/8           | ACTIVE ⚠️  | **KEEP** (BANDAID-RISK)                   | G2 open, 5 VMs running ETA ~07-01; **gate will MISFIRE on ROCKETPOOL unless re-anchored to v12** (D1)   |
| B1.4 | `mvp_catalogue_finalization_v10_2026_06_27`         | active · 7/7           | TRULY-DONE | **SLIM**                                  | Phase-0 gate record, high reference value; per-AG verdicts referenced by backfill G0s                   |
| B1.5 | `mvp_reconciliation_closeout_v10_2026_06_27`        | active · 7/7           | MOSTLY ⚠️  | **KEEP**                                  | depends_on 2 open plans; standing "v10=ONLY authority" = **agent-safety risk** post-v12 (D1)            |
| B1.6 | `mvp_scope_catalogue_tagging_2026_06_08`            | active · 6/8           | MOSTLY     | **SLIM**                                  | NOT superseded by v10 (owns deploy-api/UI scope toggle); stale illustrative YAML L64 needs `[v12 NOTE]` |
| B1.7 | `mvp_for_mdps_and_features_universe_uac_2026_06_28` | active · 6/6 (0 open)  | TRULY-DONE | **ARCHIVE** (`locked_by: NA` — no unlock) | 6/6 w/ QG+CI green; cleanest archive in batch                                                           |

#### Batch B2 — Honest-coverage + instruments catalogue/universe

| #    | slug                                                         | claimed                | verdict    | disposition                         | notes                                                                                       |
| ---- | ------------------------------------------------------------ | ---------------------- | ---------- | ----------------------------------- | ------------------------------------------------------------------------------------------- |
| B2.1 | `honest_coverage_v2_instrument_denominator_2026_06_28`       | active · 10/12         | MOSTLY     | **SLIM**                            | open `build_expected()` blocked on registry-consolidation Ph2 (C2)                          |
| B2.2 | `honest_coverage_v2_opus_checkpoints_2026_06_28`             | active · 3/3 (0 open)  | TRULY-DONE | **ARCHIVE** (needs `[unlock-plan]`) | 3/3 CK, codex SSOT `honest-coverage-model.md` written (31KB verified)                       |
| B2.3 | `honest_coverage_smoke_harness_2026_06_28`                   | active · 6/6           | MOSTLY     | **SLIM**                            | `locked_by: NA`; add `[ ]` for seasonal-window semantic gap                                 |
| B2.4 | `instruments_catalogue_incremental_rollup_2026_06_29`        | active · 0/14          | ACTIVE     | **KEEP**                            | unstarted; real prod problem (catalogue 38h-stale / Cloud-Run timeout)                      |
| B2.5 | `instruments_foundation_completeness_2026_06_24`             | active · 26/83 (~31%)  | ACTIVE     | **SLIM**                            | 1,463-line living plan; G2–G5 + all Phase-0 open; A12 Phase-0 item needs v2 fix             |
| B2.6 | `instruments_mtds_subset_consistency_remediation_2026_06_17` | active · 50/110 (~45%) | ACTIVE     | **SLIM**                            | 2 stale-open items (A1 venue-dedup `@4da6fe8`, A16 VENUE_FETCH_FAILED) — VERIFY before flip |
| B2.7 | `instrument_universe_registry_consolidation_2026_06_29`      | active · 9/14 (~64%)   | MOSTLY     | **SLIM**                            | `locked_by: NA`; carries A4.2/A4.3 denominator work; Ph2 adapter-routing open               |

#### Batch B3 — CeFi + TradFi data

| #    | slug                                                          | claimed                    | verdict    | disposition                         | notes                                                                                                              |
| ---- | ------------------------------------------------------------- | -------------------------- | ---------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| B3.1 | `cefi_deribit_binance_futures_bundle_verification_2026_06_20` | active · 5/7               | MOSTLY ⚠️  | **KEEP**                            | backfill VMs G4-gated; **C5 Deribit options_chain captured=1 = false-complete** (D3)                               |
| B3.2 | `cefi_manifest_canonicalisation_2026_06_01`                   | active · 56/85 (~66%)      | ACTIVE     | **KEEP**                            | apply-ready since 06-08; **G4 walk NOT run**; E4 orphan-delete pending                                             |
| B3.3 | `tradfi_manifest_canonicalisation_2026_06_01`                 | active · 37/61 (~61%)      | ACTIVE     | **KEEP**                            | **full `--apply` NOT run** (E3/E4/E7 open); **T-OLD-1 `category=` data-loss risk pre-apply**                       |
| B3.4 | `tradfi_massive_dual_source_2026_05_28`                       | active · 41/52 (~79%)      | ACTIVE     | **KEEP**                            | NOT stale (databento-first was a test rename, not priority flip); **consolidator dedup-key missing `source` = P0** |
| B3.5 | `tradfi_multisource_backfill_2026_06_22`                      | active · 8/11              | MOSTLY     | **SLIM**                            | code+manifest shipped; FX drain + ICE-credential + codex-update open                                               |
| B3.6 | `tradfi_cme_event_contract_backfill_2026_06_20`               | active · 4/5 (0 real open) | TRULY-DONE | **ARCHIVE** (needs `[unlock-plan]`) | VM `exit_code=0`, 77,766 rows upgraded, manifest-verified; P3 test-footgun tracked elsewhere                       |

#### Batch B4 — pipeline_mode / provenance / backfill coordination

| #    | slug                                                                | claimed            | verdict        | disposition                                    | notes                                                                                                               |
| ---- | ------------------------------------------------------------------- | ------------------ | -------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| B4.1 | `pipeline_mode_partition_migration_2026_06_01`                      | active · 0/2       | ACTIVE         | **KEEP**                                       | rider-tracker; archives when cefi/tradfi/sports/pred `--apply` complete (distinct from B4.2)                        |
| B4.2 | `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` | active · 8/11      | MOSTLY         | **SLIM**                                       | GATE for all `--apply`; M1-BREAKING landed; stale `[ ]` UI box (M5c/d shipped); extract 2 CICD items; covers A2.6   |
| B4.3 | `data_source_provenance_all_asset_groups_2026_06_01`                | active · ~6/18     | ACTIVE         | **KEEP**                                       | code done; data-backfills + QG-wiring open; **~12 defi handlers missing `assert_defi_catalog_fresh`**               |
| B4.4 | `path_to_100pct_backfill_mtds_is_2026_06_17`                        | active · ~4/26     | ACTIVE         | **MERGE-INTO `data_completion_to_100_all_ag`** | M-1 survivor but Plan 5 is the live coordinator; Step-0 literally duplicated; migrate 22 todos then `superseded_by` |
| B4.5 | `data_completion_to_100_all_ag_2026_06_21`                          | active · ~176/190  | ACTIVE         | **KEEP** (MERGE target)                        | live operational coordinator; covers A3.1; `repos:` missing MTDS/IS (fix)                                           |
| B4.6 | `mtds_file_size_refactor_2026_06_08`                                | **deferred** · 0/3 | TRULY-DEFERRED | **KEEP** (deferred)                            | correctly parked (operator 06-26); polars half shipped separately                                                   |
| B4.7 | `macro_econ_adapter_scaffolds_2026_06_09`                           | active · 5/10      | MOSTLY         | **SLIM**                                       | 4 adapters built; 5 `[ ]` operator-gated (EIA cred / altdata decision); covers A5.3 Phase 2                         |

#### Batch B5 — Data master-coordinators

| #    | slug                                                          | claimed                      | verdict    | disposition                              | notes                                                                                                   |
| ---- | ------------------------------------------------------------- | ---------------------------- | ---------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| B5.1 | `master_data_canonicalisation_migration_catalogue_2026_06_07` | active · 40/72               | ACTIVE ⚠️  | **KEEP + SLIM** (dup G3 banner L805-825) | **STILL the live sequencer**; **TradFi G4 OOM-blocked → operator VM restart**; 4/5 AGs through G4       |
| B5.2 | `migration_verification_orphan_safety_2026_06_10`             | active · 29/45               | MOSTLY     | **SLIM**                                 | core V0–V5 done; 1,293 lines mostly progress-log; V6/A2 tail + wip-branch landing                       |
| B5.3 | `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`   | active · 17/31               | ACTIVE ⚠️  | **KEEP**                                 | L6 decommission + **L2 pause of 10 legacy crons (parallel-SSOT bandaid-risk)** open; 2 stale-open todos |
| B5.4 | `cross_ag_shard_4pillar_validation_harness_2026_06_19`        | active · 5/6 (1 P3-deferred) | TRULY-DONE | **ARCHIVE** (needs `[unlock-plan]`)      | harness built + wired QG STEP 5.88; P3 row migrates to manifest-canon; `locked_since` typo              |

---

### ✅ PHASE B COMPLETE — 31 IS+MTDS plans content-verified (5 batches, all main-loop spot-checked)

**PROPOSED PLAN ARCHIVE-SET (5 TRULY-DONE, awaiting operator OK — all need `[unlock-plan]` except B1.7):**
`mvp_backfill_tradfi_ohlcv1m_v10` · `mvp_for_mdps_and_features_universe_uac` (no lock) ·
`honest_coverage_v2_opus_checkpoints` · `tradfi_cme_event_contract_backfill` ·
`cross_ag_shard_4pillar_validation_harness`.

**PROPOSED MERGE (1):** `path_to_100pct_backfill_mtds_is` → **`data_completion_to_100_all_ag`** (migrate 22 open todos +
the "Definition of 100%" formula → Plan 5/codex, then `superseded_by` + archive). Operator OK + `[unlock-plan]`.

**SLIM (12, non-destructive):** `mvp_catalogue_finalization_v10` · `mvp_scope_catalogue_tagging` ·
`honest_coverage_v2_instrument_denominator` · `honest_coverage_smoke_harness` · `instruments_foundation_completeness` ·
`instruments_mtds_subset_consistency_remediation` · `instrument_universe_registry_consolidation` ·
`tradfi_multisource_backfill` · `pipeline_mode_source_batch_live_replay_standardisation` ·
`macro_econ_adapter_scaffolds` · `migration_verification_orphan_safety` · `master_data_canonicalisation` (drop dup
banner). **KEEP-active (12):** the two cefi/tradfi manifest-canon, cefi_deribit, tradfi_massive, both pipeline_mode,
data_source_provenance, data_completion, master_data_canon (sequencer), bucket_name_ssot,
instruments_catalogue_incremental_rollup, the two open mvp backfills + closeout, mtds_file_size_refactor (deferred).

**⚠️ HIGH-PRIORITY OPERATOR / CRITICAL-PATH ITEMS surfaced by Phase B:**

1. **TradFi G4 migration VM is OOM-blocked** (`master_data_canonicalisation` B5.1 + `tradfi_manifest_canonicalisation`
   B3.3 E3/E4 + `tradfi_backfill_oom` A3.6 all converge here). The 48-scheduler RESUME runbook + G5 backfills are gated
   on it. **Operator action: restart the TradFi G4 migration on a highmem VM.** This is the single biggest blocker.
2. **v10→v12 scope drift (D1 — Ikenna)** — `mvp_backfill_defi_onchain` G2 gate **will misfire on ROCKETPOOL** if run
   before re-anchoring to v12; `mvp_reconciliation_closeout` standing "v10=ONLY authority" is an **agent-safety risk**
   (a background agent could act on stale v10). Decide: update-banners-to-v12-in-place OR archive-v10 +
   open-v12-followup.
3. **C5 Deribit options_chain false-complete (D3 — Ikenna)** — `captured=1` = effectively uncaptured; the cefi G1
   "COMPLETE" banner is false. Decide Deribit options stance before cefi plans proceed.
4. **T-OLD-1 data-loss risk** — `tradfi_manifest_canonicalisation` migrator has no `category=`→`asset_group=` rename;
   running `--apply` as-is orphans NASDAQ/NYSE/ICE/FX paths. **P0 fix before the tradfi apply.**
5. **consolidator dedup-key missing `source`** (`manifest_consolidator.py:278`) — silently collapses dual-source rows
   when Massive lands. P0 (`tradfi_massive`).
6. `gcs_hive_partition` (A5.2) deferred-archive **STILL PENDING** — both cefi E4 orphan-delete + tradfi E7 110k-delete
   unrun.

**Stale-checkbox flips for SLIM (verify-then-flip, don't trust):** pipeline_mode-standardisation M5c/d UI box ·
mtds_subset L1790 venue-dedup + VENUE_FETCH_FAILED · instruments_foundation Phase-0 A12. **No MERGE** beyond B4.4; the
two honest_coverage_v2 plans are model-tier-paired (keep paired); the two pipeline_mode plans are distinct layers (keep
both).

## 7. Ordering map (Phase D output) — the "what to do now" for IS+MTDS

> Synthesised from the surviving KEEP/SLIM/MERGE-target plans + still-open issues (Phases A+B). The whole IS+MTDS data
> layer hangs off **one critical-path spine**: the **TradFi G4 migration VM (OOM-blocked)** and the **cefi/tradfi
> `--apply` walks**. Almost everything "blocked" traces back to those two.

### The critical-path spine (resolve top-down)

```
TradFi G4 migration VM (OOM-blocked, master_data_canon B5.1)
  └─ restart on HIGHMEM  ── gates ──▶ tradfi_manifest_canon E3/E4/E7 (B3.3)
                                        ├─▶ gcs_hive_partition archive (tradfi E7 side, A5.2)
                                        ├─▶ pipeline_mode_partition_migration tradfi rider (B4.1)
                                        └─▶ master_data_canon RESUME runbook (48 schedulers) + G5 backfills (B5.1)
  ⚠ PRE-APPLY BLOCKER: T-OLD-1 — tradfi migrator has no category=→asset_group= rename → MUST fix before --apply (data-loss)

cefi_manifest_canon G4 --apply / E4 orphan-delete (B3.2)
  └─ gates ──▶ gcs_hive_partition archive (cefi E2 side, A5.2)
            ──▶ pipeline_mode_partition_migration cefi rider (B4.1)
            ──▶ mvp_backfill_cefi_tick G4 gate (B1.1) + wave-2 VM relaunch
```

### DO-NOW — unblocked, high-leverage (no gate; mostly small code or the consolidation execution itself)

| #   | action                                                                                                                     | repo / where                                           | why now                                                                |
| --- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------- |
| 1   | **Fix T-OLD-1** — add `category=`→`asset_group=` rename to `migrate_tradfi_to_v9_canonical.py`                             | market-tick-data-service                               | P0; unblocks the entire TradFi `--apply` spine safely (else data-loss) |
| 2   | **Add `source` to consolidator dedup key** (`_BASE_DEDUP_COLS`/`_OPTIONAL_DEDUP_COLS`)                                     | unified-trading-library `manifest_consolidator.py:278` | P0; silent dual-source row-collapse the moment Massive lands           |
| 3   | **Pause the 10 legacy consolidator crons** (`*-legacy-cron`)                                                               | deployment-service / cron (bucket_name B5.3 L2)        | kills the parallel-`_index` SSOT bandaid-risk; highest-value single op |
| 4   | **Wire `assert_defi_catalog_fresh` into the ~12 remaining defi handlers**                                                  | market-tick-data-service (data_source_provenance B4.3) | closes the A12a preflight gap; mechanical                              |
| 5   | **Execute the consolidation archive-set + merge** (once operator OKs) — 7 issues + 5 plans + 1 merge, with `[unlock-plan]` | unified-trading-pm                                     | de-bloats the active set; the point of this exercise                   |
| 6   | **SLIM the 12 plans + flip verified-stale checkboxes** (verify-then-flip)                                                  | unified-trading-pm                                     | navigability; do alongside archives                                    |

### PARALLEL — independent, safe to run concurrently with the spine

- **`instruments_catalogue_incremental_rollup` (B2.4)** — unstarted; fixes the catalogue 38h-stale / Cloud-Run-timeout;
  independent of the migration spine (own repo path).
- **`mvp_backfill_defi_onchain` VM completion (B1.3)** — 5 VMs already running, ETA ~2026-07-01; independent of TradFi.
  _(But its G2 GATE is D1-blocked — see below.)_
- **Honest-coverage SLIMs + smoke-harness (B2.1/2.3)** — doc + the seasonal-window task; independent.
- **`tradfi_multisource_backfill` FX-drain (B3.5)** — operational, independent of the canon `--apply`.

### BLOCKED / GATED — name the gate + what unblocks

| blocked work                                                | gate                                  | unblocked by                                            |
| ----------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------- |
| tradfi `--apply` (E4/E7), 48-scheduler resume, G5 backfills | TradFi G4 VM OOM + T-OLD-1            | DO-NOW #1 + **restart G4 on highmem**                   |
| `gcs_hive_partition` archive (A5.2)                         | cefi E4 + tradfi E7 deletes unrun     | cefi/tradfi `--apply` complete                          |
| `mvp_backfill_cefi_tick` G4 (B1.1)                          | cefi `--apply` + wave-2 VMs + D3      | cefi canon + **D3 Deribit ruling**                      |
| `mvp_backfill_defi_onchain` G2 (B1.3)                       | gate misfires on ROCKETPOOL under v12 | **D1 re-anchor decision** + VM finish                   |
| `honest_coverage build_expected` (B2.1)                     | registry-consolidation Phase 2        | `instrument_universe_registry_consolidation` Ph2 (B2.7) |
| macro Phases 1/3–6 (A5.3)                                   | `altdata` asset_group decision        | operator decision                                       |
| 775.9k cefi Tardis cells (A2.3)                             | Tardis historical billing             | **operator: is it funded?**                             |
| live warm-GCS persistence (A3.2/M-C7)                       | build greenlight                      | **operator greenlight**                                 |

### ⚠️ OPERATOR-DECISION QUEUE (consolidated — these unblock the most downstream work)

1. **Restart the TradFi G4 migration VM on a highmem machine** (infra action, not a question) — unblocks the biggest
   spine.
2. **D1 — v10→v12 scope drift** (Ikenna): update-banners-to-v12-in-place OR archive-v10 + open-v12-followup.
   _Agent-safety: `mvp_reconciliation_closeout` standing "v10=ONLY authority" can misdirect a background agent;
   `mvp_backfill_defi_onchain` G2 misfires on ROCKETPOOL._
3. **D3 — Deribit options_chain stance** (Ikenna): `captured=1` = effectively uncaptured; cefi G1 "COMPLETE" is false.
4. **Tardis historical billing** (operator): funded (doc2) or excluded (doc3)? 775.9k cells hinge on it.
5. **M-C7 warm-GCS-parts build** greenlight (operator) — already decided design, awaiting go.
6. **`altdata` asset_group** decision (operator) — gates macro/econ data entry.
7. **Consolidation execution OK** (operator): approve the archive-set (7 issues + 5 plans), the 1 merge, and
   `[unlock-plan]`.

### Consolidation execution queue (this exercise's output — pending operator OK)

- **ARCHIVE 12** (7 issues §6-PhaseA + 5 plans §6-PhaseB) — all need `[unlock-plan]` except `mvp_for_mdps_*` (no lock).
- **MERGE 1**: `path_to_100pct_backfill_mtds_is` → `data_completion_to_100_all_ag`.
- **SLIM 14** (2 issues + 12 plans) — non-destructive; can do on the already-authorized push.
- **LINK-AND-TRACK / KEEP** — applied in-ledger; non-destructive.
- **Systemic frontmatter cleanup**: invalid `assigned_vm` (blank / `vm-cross-cutting` → `NA`) + stale `locked_since`
  across ~15 docs.
- **NEEDS-NEW-TASK (6)**: event-sink Option A/B · funding_timestamp offset + cadence tracker · TradFi enumerator
  `is_mvp`-gate · tradfi re-enumerate · GONE_NO_CAPTURE debounce · macro Phases 1/3–6.

### Phase C — Epics ✅ DONE 2026-06-30/07-01

Same rubric on the 6 IS+MTDS-relevant epics (2 Opus agents). Result:

- **Repointed 9 dangling child-plan refs** to the consolidation archives/merge — esp. `mtds_mdps_master` +
  `tradfi_master` (the merge `path_to_100pct` → `data_completion_to_100_all_ag`; both archived tradfi plans →
  `../archive/2026_06/`); `features_and_ml_master` `mvp_for_mdps` ref fixed (main loop). **0 dangling `../active/` refs
  remain** in the touched epics.
- **De-contradicted to live SSOT**: `manifest_master` + `cefi_master` "v8/v5 schema" → **v9**
  (`MANIFEST_SCHEMA_VERSION=9`); `tradfi_master` "Databento+Barchart" → **databento-first, Barchart RETIRED** (VIX-15m
  layer survives); de-duplicated a duplicate header; corrected stale child-counts (10→33, 3→6, 9→7). TradFi-G4 migration
  verified **not** falsely "done".
- **Superseded manifest epics** (`manifest_evolution_SUPERSEDED`, `manifest_migration_SUPERSEDED`): genuinely superseded
  (successor `manifest_master`, **0 `parent_epic` dependents**) — **LEFT IN `plans/epics/` per the established
  convention** (all 4 SUPERSEDED epics live there marked; the hygiene check only flags SUPERSEDED filenames in
  `plans/active/`, not `epics/`; moving them would break archaeology refs). Already terminally disposed — no move
  needed.
- **Flagged for a separate codex follow-up** (out of epic scope): `/codex/02-data/mvp-scope-canonical.md` says
  `MVP_SCOPE_CONFIG_VERSION = 11` but code is **12** live; plus pre-existing dangling `../active/` epic links not in the
  consolidation set (frozen-history banners — not safe to auto-edit).

## 8. Summary scoreboard (IS+MTDS pass, 2026-06-30)

| pass             | docs verified | ARCHIVE         | MERGE | SLIM   | LINK/KEEP | operator flags                            |
| ---------------- | ------------- | --------------- | ----- | ------ | --------- | ----------------------------------------- |
| Phase A (issues) | 30            | 7 (+1 deferred) | 0     | 2      | 21        | Tardis billing · defi_perp_funding · M-C7 |
| Phase B (plans)  | 31            | 5               | 1     | 12     | 13        | TradFi-G4-OOM · D1 v10→v12 · D3 Deribit   |
| **total**        | **61**        | **12**          | **1** | **14** | **34**    | 7-item decision queue (§7)                |

Net once executed: **~13 docs leave the active set** (12 archive + 1 merge-away), **14 slimmed**, and the rest are
link-tracked/kept with a single ordering map (§7) replacing the prior un-navigable pile. Nothing destructive has run —
all ARCHIVE/MERGE rows await the operator's OK + `[unlock-plan]`.

## Progress Log

- **2026-06-30** — Doc created as the consolidation plan-of-work (status `draft`, AWAITING AGREEMENT). Inventory taken:
  **123 active plans** (~30 at 100% checkboxes, ~40 at 80–99%), **88 issue docs**, + epics. Lock reality surfaced: **98
  plans `locked_by: live-defi-rollout`** (operator confirms boilerplate — archivable after end-to-end verification via a
  batched `[unlock-plan]`), **22 `NA`**. Methodology (content-verify, not frontmatter), disposition vocabulary
  (SLIM-preferred), phasing (issues → plans → epics → ordering map), and the background-agent fan-out plan drafted.
- **2026-06-30 (agreement + scope narrowing)** — Operator AGREED with mods: **scope narrowed to instruments-service +
  MTDS ONLY** (sports/prediction/defi-exec/features/infra/ui/ao kept as-is); **pilot first**; **≤6 parallel** (gentle);
  **dispositions written into §6** (no per-batch blocking); **issues → plans**; **deliberate same-kind batching**.
  Status → `active`. Built the §3a IN/OUT inventory + 10 same-kind batches (5 issue batches A1–A5 ≈30 docs · 5 plan
  batches B1–B5 ≈30 docs) by title/content domain (the `repos:` field is unreliable — many `[]`/pm-only). PILOT = batch
  A1 (manifest-hygiene supersede-chain + phantom-captures) next. No docs archived/edited yet.
- **2026-06-30 (PILOT complete + validated)** — Batch A1 (8 docs) content-verified by 1 agent, then **main-loop
  spot-checked** (2 load-bearing claims verified verbatim: UTL `_state.py:173` cache-not-popped + defi plan `:62`
  219,632-flip banner). Rubric WORKS — caught a two-chain supersede split (defi 22→27 vs cefi 28→29, not one chain) and
  a reverse-staleness trap (`phantom_captures_defi` boxes all `[ ]` but the apply was DONE). §6 A1 ledger filled.
- **2026-06-30 (PHASE A + B + D COMPLETE)** — Fanned out A2–A5 (4 agents ≤6-parallel) then B1–B5 (5 agents), each
  verifying ~6–8 docs against live code with the friction-tuned rubric; **every ARCHIVE/SUPERSEDE/MERGE claim main-loop
  spot-checked verbatim** before recording. 61 IS+MTDS docs verified (30 issues + 31 plans). Result: **12 ARCHIVE + 1
  MERGE + 14 SLIM + 34 LINK/KEEP** (§8 scoreboard). Surfaced the critical-path spine (TradFi G4 OOM + cefi/tradfi
  `--apply`), a 7-item operator-decision queue, and 6 needs-new-task gaps — all in the §7 ordering map. Recurring
  frontmatter rot (invalid `assigned_vm`, stale `locked_since`) flagged for batch-fix at execution. **Nothing archived
  yet** — all destructive dispositions await operator OK + `[unlock-plan]`. Commits: A1 `991831760`, A2-4 `6102f15e0`,
  A5 `0df47a2f7`, B `0ef55f847`. Phase C (epics) deferred per operator. Proposed A1 archive-set:
  `manifest_hygiene_red_2026_06_22` + `…_06_28` (superseded, link-tracked, no info loss) — **awaiting operator OK**.
  Friction learnings folded into the fan-out prompt (cross-read covering plan both ways · read the CSV artifacts for
  supersede calls · flag invalid `assigned_vm` · "no todos ≠ resolved"). Fanning out A2–A5 (4 agents, ≤6 parallel) next.
- **2026-06-30/07-01 — DISPOSITIONS EXECUTED (operator-authorized, local commits, single push held).** Operator said
  "make the changes, commit locally, push at once." Done on slot-1 worktree:
  - **ARCHIVED 12** (7 issues → `plans/archive/issues/`, 5 plans → `plans/archive/2026_06/`), each with an `✅/🟦`
    verdict banner + status flip. Locked-plan archival used `[unlock-plan]` per operator authorization.
  - **MERGED 1**: `path_to_100pct_backfill_mtds_is` → `data_completion_to_100_all_ag` (no-loss fold-in section +
    both-way `supersedes`/`superseded_by`; full text preserved in archive). `check_superseded_in_active` passes.
  - **LINK-AND-TRACK**: 10 kept-open issues cross-linked via `related:`; invalid `assigned_vm: vm-cross-cutting` → `NA`.
  - **SLIM + DE-CONTRADICT 8 plans** (2 Opus agents, IS+MTDS): v10→v12 banners, foundation Phase-0 → HC-v2, venue-dedup
    flip (`@4da6fe8`), M5c/d UI flip (`@687d4ce`), master_data dup-banner removed, all SSOT-verified vs live UAC/codex;
    open-todo invariant held (only 2 evidenced flips). 4 verified-clean plans left untouched.
  - **STATUS CORRECTION**: `live_pipeline_persistence` `resolved`→`blocked` (warm-GCS tier unbuilt, M-C7).
  - **Inventory regen**: 120→119 plans; the 5 orphans are Harsh's external `ui_pnpm_migration_*` plans, not this work.
  - **Deferred (trivial)**: verbose-trim of the remaining issue-doc SLIMs (phantom_captures_tradfi, live_tardis_machine,
    hyperliquid_rest, tradfi_backfill_oom, gcs_hive_partition, data_pipeline_alerts) — low value on small docs; the §6
    dispositions stand as the record. **Codex follow-up** (out of plan scope): `pipeline-mode-partition.md` still calls
    `live_websocket` a transitional alias (M-C1/M30.5). Operator-decision queue (§7) unchanged — still pending.
