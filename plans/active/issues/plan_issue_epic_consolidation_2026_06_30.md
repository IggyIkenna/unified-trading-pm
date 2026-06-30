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
status: active
nature: audit
asset_group: cross-asset
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [consolidation, plan-hygiene, issue-triage, archival, ordering-map, ssot-audit]
related:
  [
    ./instruments_service_plan_reconciliation_2026_06_29.md,
    ./mtds_plan_reconciliation_2026_06_29.md,
    ../../PLAN_FORMAT.md,
    ../../../codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-06-30
last_updated: 2026-06-30
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [operator request 2026-06-30]
drift_direction: advance-code
depends_on: []
locked_by: NA
locked_since: 2026-06-30
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
> doc** (§6 ledger) — I do NOT block waiting per-batch; once the operator decides the archive-set we execute it;
> (4) **issues → then plans**; (5) **deliberate same-kind batching** (group docs addressing similar items). Archival
> (file move + `[unlock-plan]`) still waits for the operator's per-doc decision; everything up to that is recorded here.

## 0. Why (operator framing 2026-06-30)

Too many plans/issues/epics, much of it stale or already-done, so: (a) navigation is impossible; (b) there is no clear
"what to do now / what's parallel / what's gated"; (c) it's hard to confirm a plan was *actually* implemented
end-to-end. This exercise fixes all three.

## 1. The HARD verification rule (the heart of this)

**Frontmatter status (`resolved` / `complete` / `[x]`) is a CLAIM, not proof.** For every doc an agent MUST read the
full content and verify the claim against live reality before any disposition:

1. **Claimed state** — frontmatter `status`, checkbox ratio, any "DONE/RESOLVED/G-gate-complete" banners.
2. **Verified state** — pick the doc's core claims/items and CHECK them against the live tree:
   - cited evidence resolves (commit exists + does what's claimed; `cloudbuild=<id>` is SUCCESS; manifest rows present);
   - the change is in **live code/data** (grep the symbol, read the consumer, query the manifest) — grep-0 ≠ done;
   - **quality gate**: is it a real root-fix or a **bandaid** (shim / `# type: ignore` / disabled test / `try/except
     ImportError` / TODO / "tracked separately")? Did it introduce a **regression**?
   - for an **issue**: is the ROOT CAUSE fixed in live code, or merely patched/worked-around?
3. **Verdict** — `TRULY-DONE` · `DONE-BUT-BANDAID` (works, carries tech-debt) · `PARTIAL` · `STALE` (newer code already
   moved past it) · `SUPERSEDED` (replaced by another doc) · `ACTIVE` (genuine open work).
4. **Evidence** — the agent records the exact checks (files/commands/symbols/build-ids) so the operator can trust the
   verdict without re-doing it. **No verdict without evidence.**

## 2. Disposition vocabulary (operator preference: SLIM > supersede+archive for low-value)

| disposition         | when                                                                 | action                                                                                          |
| ------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **ARCHIVE**         | `TRULY-DONE`, end-to-end verified, little residual reference value   | 5-step ritual → move to archived, done/superseded banner, clear lock (`[unlock-plan]` batch)    |
| **SLIM** _(prefer)_ | done but worth keeping as reference; bloated with completed detail   | trim completed sections to a 1-line summary + durable contract; KEEP active but lean            |
| **MERGE**           | duplicate / overlapping plans                                        | fold into one canonical; archive the merged-away as `superseded_by`                             |
| **SUPERSEDE+arch.** | replaced by a newer/better plan AND a fresh plan is warranted (high value) | new plan carries the open work; old → `superseded_by` + archive                            |
| **LINK-AND-TRACK**  | OPEN issue whose fix IS covered by an active plan's tasks            | cross-link issue↔plan + set issue `status: tracked` (or note the covering plan); do NOT archive |
| **KEEP**            | genuine active work, not bloated                                     | leave as-is (± trivial hygiene)                                                                  |

## 3. Phasing + ordering (operator-specified)

**Scope = instruments-service + MTDS plans/issues ONLY** (≈30 issues + ≈30 plans of the 84/124 total — see §3a).
**Issues first, then plans; epics a follow-up.** Everything outside IS+MTDS is untouched this pass.

- **Phase A — IS+MTDS Issues (≈30 docs, see §3a).**
  - **A1** content-verify each: `TRULY-RESOLVED` → ARCHIVE; else → open.
  - **A2** for each still-open issue: does an **active plan already carry tasks** that solve it? **YES** → LINK-AND-TRACK
    (cross-link + status `tracked`); **NO** → KEEP as-is (flag any that need a new task/plan).
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
`defi_onchain_derivable*`, `defi_manifest_canon*`, `solana_defi*`), features/MDPS (`features_*`, `mdps_*`,
`bar_edge*`, `colocated_feature*`), ml/strategy, all infra/cicd/bucket-IAM/org/ci/devops/uat/ui/ao/role/pm/frontmatter/
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
  `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29` ·
  `defi_perp_funding_mvp_scope_contradiction_2026_06_29` (borderline) ·
  `perp_funding_data_semantics_and_cadence_2026_06_16` · `vm_backfill_data_correctness_findings_2026_06_29` ·
  `empty_reprobe_disagreement_2026_06_22`.
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
  `instruments_mtds_subset_consistency_remediation_2026_06_17` · `instrument_universe_registry_consolidation_2026_06_29`.
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
(if injection fails, the agent must not proceed). **≤6 parallel** (operator: gentle — avoid rate limits). **One agent per
same-kind batch** (§3a), each agent verifying ~6–8 docs so it holds coherent context.

- **PILOT (1 agent):** batch **A1** only. I inspect the returned verdicts for rubric quality (did it actually open files
  / grep symbols / query manifests, or just restate frontmatter?) **before** fanning out. Bad rubric → tighten the
  prompt + re-pilot; good → proceed.
- **Wave A (issues):** remaining batches A2–A5 → 4 agents, run **≤6 at a time**. Structured per-issue verdict.
- **Wave B (plans):** batches B1–B5 → 5 agents, run **≤6 at a time**. Structured per-plan verdict.
- **Output schema (every agent, per doc):** `{slug, claimed_status, verified_verdict, evidence[], disposition,
  covering_plan, lock, notes}` → I merge into the **§6 disposition ledger**.
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
  blocking; the operator reads §6 and names the archive-set; main loop executes ONLY that set, never auto-archives in bulk.
- **Doc edits push** (this is a `docs(plans):` change → direct-push-to-LDR carve-out); **archival file-moves +
  `[unlock-plan]` wait** for the operator's per-doc decision.

## 6. Disposition ledger (filled during execution)

> One row per doc. Agent-verified (content, not frontmatter) + spot-checked by the main loop. **`ARCHIVE` / `SUPERSEDE`
> rows are PROPOSED — they execute only once the operator names the archive-set.** `LINK-AND-TRACK` / `SLIM` / `KEEP`
> are non-destructive and I can apply them on the push the operator already authorized.

### Phase A — Issues

#### Batch A1 — manifest / phantom data-correctness (verified 2026-06-30; pilot + main-loop spot-check)

| #   | slug                                       | claimed         | verified verdict | proposed disposition                                       | covering plan / successor                            |
| --- | ------------------------------------------ | --------------- | ---------------- | ---------------------------------------------------------- | ---------------------------------------------------- |
| A1.1 | `manifest_hygiene_red_2026_06_22`         | open (no todos) | STALE→SUPERSEDED | **SUPERSEDE+archive** → successor `…_06_27` (later defi snapshot) | `data_pipeline_hardening_self_monitoring_2026_06_22` (defi DIVERGENT_EMPTY P1 still `[ ]`) |
| A1.2 | `manifest_hygiene_red_2026_06_27`         | open (1 `[ ]`)  | ACTIVE           | **LINK-AND-TRACK** (live defi hygiene ref)                 | `data_pipeline_hardening_self_monitoring_2026_06_22` |
| A1.3 | `manifest_hygiene_red_2026_06_28`         | open (1 `[ ]`)  | STALE→SUPERSEDED | **SUPERSEDE+archive** → successor `…_06_29` (later cefi snapshot) | `mvp_backfill_cefi_tick_v10_2026_06_27`        |
| A1.4 | `manifest_hygiene_red_2026_06_29`         | open (1 `[ ]`)  | ACTIVE           | **LINK-AND-TRACK** (live cefi hygiene ref)                 | `mvp_backfill_cefi_tick_v10_2026_06_27` (OKX-SWAP DIVERGENT_EMPTY + 780 HL phantoms, G4 gate) |
| A1.5 | `phantom_captures_cefi_2026_06_28`        | open (P2✅/P1`[ ]`) | PARTIAL       | **LINK-AND-TRACK** (P1 HL-phantom apply blocked on VM term) | `mvp_backfill_cefi_tick_v10_2026_06_27` (L540-606) |
| A1.6 | `phantom_captures_tradfi_2026_06_28`      | open (P2✅/P1`[ ]`) | PARTIAL (apply done) | **SLIM** (apply 0-phantom-confirmed; P1 ICE diag low-impact, billing-blocked) | `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27` (G1 = 0 phantoms) |
| A1.7 | `phantom_captures_defi_2026_06_28`        | open (all `[ ]` — STALE boxes) | PARTIAL | **LINK-AND-TRACK** (apply DONE 219,632 flipped; writer root-cause + post-fill verify open) | `mvp_backfill_defi_onchain_v10_2026_06_27` (L62/613/1189) |
| A1.8 | `manifest_index_read_oom_canonical_cache_2026_06_24` | open (no todos) | ACTIVE     | **KEEP** (latent fleet-OOM; Option A/B unimplemented; only config workaround applied) | none found — needs a `[ ]` task vs UTL `_state.py:149-173` |

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

> **PROPOSED A1 ARCHIVE-SET (awaiting operator OK):** `manifest_hygiene_red_2026_06_22` + `manifest_hygiene_red_2026_06_28`
> (both superseded by their later same-AG snapshot; both link-tracked to a still-open covering plan, so no information is
> lost on archive). Everything else in A1 is non-destructive (LINK-AND-TRACK / SLIM / KEEP).

#### Batches A2–A5 — _verification in flight (≤6 parallel agents)._

### Phase B — Plans

_(Filled after Phase A; batches B1–B5.)_

## 7. Ordering map (Phase D output)

_(DO-NOW / PARALLEL / BLOCKED-BY-GATE — filled after A+B.)_

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
  Proposed A1 archive-set: `manifest_hygiene_red_2026_06_22` + `…_06_28` (superseded, link-tracked, no info loss) —
  **awaiting operator OK**. Friction learnings folded into the fan-out prompt (cross-read covering plan both ways · read
  the CSV artifacts for supersede calls · flag invalid `assigned_vm` · "no todos ≠ resolved"). Fanning out A2–A5
  (4 agents, ≤6 parallel) next.
