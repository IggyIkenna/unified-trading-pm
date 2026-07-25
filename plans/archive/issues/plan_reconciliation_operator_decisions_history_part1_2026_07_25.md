---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — history part 1/4 (Section A, operator decision queue, P0 + P1-partial:
  carry_staked_basis_funding_scan_experiment↔strategy_master through epics/README↔orchestrator_master)"
summary:
  "Verbatim extraction of the FIRST 59 of Section A's 84 operator-decision-queue finding entries (all P0 + the first
  portion of P1) from `plan_reconciliation_operator_decisions_2026_07_11.md`, split for line-cap compliance
  (`plans/active/task_template.md` §3 finding J). Every finding here was ruled on in the parent's §A2 OPERATOR RULINGS
  table (2026-07-12) and dispositioned in the parent's Progress Log — this file is the closed raw finding text only, not
  live tracking. Zero open todos."
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift, history]
related: [/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md]
created: 2026-07-25
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
source: [plan_reconciliation_operator_decisions_2026_07_11]
resolved_by:
  "extracted verbatim from the closed 2026-07-11 contradiction audit; every finding's ruling + disposition lives in the
  parent's §A2 rulings table and Progress Log, not in this file"
locked_by:
drift_direction: advance-code
depends_on: []
---

# Plans-corpus contradiction audit — history part 1/4 (Section A, findings 1-59)

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

> **Extracted verbatim 2026-07-25 →** this file, from
> `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (line-cap remediation,
> `plans/active/task_template.md` §3 finding J — the parent was 3927 lines, over the 1000L hard cap). This is the FIRST
> of 4 history parts covering Section A (operator decision queue, 84 doc-pairs) + Section B (auto-fix queue, 176
> doc-pairs); see the parent doc for the full part index, the §A2 rulings table, Section C (structural gaps), Section D
> (bonus finding), and the Progress Log (which carries every currently-open todo — there are none in this file). Content
> below is byte-for-byte as it appeared in the parent's Section A, unedited.

## A. OPERATOR DECISION QUEUE — 84 doc-pairs (ruling needed)

#### [P0] active/carry_staked_basis_funding_scan_experiment_2026_06_16.md ↔ epics/strategy_master.md

- finding ids: 286,289
- **strategy-service LOGIC FREEZE vs new engine code shipped into engine/strategies/v2/** —
  `epics/strategy_master.md:107-108`: “Only ruff/pyright surface fixes. No changes to `engine/strategies/v2/`,
  `engine/allocator/`, collateral, liquidation, cross-venue transfer. Resume ful” vs
  `active/carry_staked_basis_funding_scan_experiment_2026_06_16.md:1191`: “`staking_simple.py` already exist; ADD
  `funding_dispersion.py` for the $-neutral reversion archetype + the 8 overlays), ... strategy_service/engine/st”
  - why: The epic (hub for this whole cluster) states a standing LOGIC FREEZE forbidding any change to
    strategy-service's `engine/strategies/v2/` until a `STRATEGY-LOGIC UNFREEZE` ping — a rule the sibling
    capability_wizard plan explicitly honors repeatedly (e.g. deferring margin-traceability IMPLEMENT todos and the F27
    collate
- **Epic's auto-populated active-plan index is missing the carry-scan plan from its P0-P3 priority lists** —
  `epics/strategy_master.md:99`: “\_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers
  pick up in priority order (P0 first). Auto-populated by
  `scripts/”  vs  `active/carry_staked_basis_funding_scan_experiment_2026_06_16.md:19`: “parent_epic: strategy_master”
  - why: Same index-drift as the capability_wizard case: the epic's P0-P3 'Assigned active plans' section
    (auto-populated 2026-05-21) does not list carry_staked_basis_funding_scan_experiment_2026_06_16.md anywhere, even
    though it declares parent_epic: strategy_master, is status: active, locked_by: live-defi-rollout, and carries
- **DECISION NEEDED**: strategy_master LOGIC FREEZE (no changes to engine/strategies/v2/ until a formal UNFREEZE ping -
  never posted) vs carry plan shipping funding_dispersion.py into that exact dir citing ad-hoc 'operator permission
  GRANTED 2026-06-18'. A: ratify the shipped file retroactively + post a scoped UNFREEZE note in \_agent_pings.md +
  amend the epic freeze wording to name the carve-out [REC - you did grant it]. B: freeze was violated -> revert
  strategy-service@6b285fad. C: lift the freeze entirely (update epic).

#### [P0] active/cefi_manifest_canonicalisation_2026_06_01.md (intra-doc)

- finding ids: 149,151,153
- **cefi F2 FUTURE bundle-grain rollup — is the enumerate venue-aware fix actually shipped/wired?** —
  `active/cefi_manifest_canonicalisation_2026_06_01.md:420-421`: “F2 venue-aware FUTURE bundle — CLOSED +
  VERIFIED...code shipped on LDR (`uac@e3dcd868` + `is@4f5faae8`) (enumerate `_rollup_bundle_grain` threads
  `ins”  vs  `active/cefi_manifest_canonicalisation_2026_06_01.md:1883-1885`: “`\_rollup_bundle_grain`(~:1162-1166) calls`bundle_instrument_type_for_leaf(...)`and`grain_for_instrument_type(...)`**without`venue=`\*\*
  → defaults”
  - why: Same doc, same function (`_rollup_bundle_grain`), both dated 2026-06-08. One passage (with checked-off todo +
    concrete before/after enumerate numbers) says the venue-aware fix landed via is@4f5faae8 and is verified GREEN on
    real prod. A later section in the same doc, titled 'Proposed fixes for the deferred-with-reason
- **Which plan is the authoritative cross-plan coordinator for cefi's canonicalisation work** —
  `active/cefi_manifest_canonicalisation_2026_06_01.md:31`: “master: defi_manifest_canonicalisation_2026_06_01.md
  (cross-plan canonical-SSOT coordinator)” vs `active/cefi_manifest_canonicalisation_2026_06_01.md:44-45`: “⛔
  COORDINATED + APPLY-GATED (2026-06-07) — cross-AG sequencing is owned by
  `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.m”
  - why: The doc's own machine-readable frontmatter `master:` field still names
    defi_manifest_canonicalisation_2026_06_01.md as coordinator, but the body's own banner (and
    defi_manifest_canonicalisation's own explicit '⬆️ DEMOTED 2026-06-07' banner) both say coordination moved to
    master_data_canonicalisation_migration_catalogue
- **True scope of the plan: narrow gap-fill vs whole-corpus re-canonicalisation** —
  `active/cefi_manifest_canonicalisation_2026_06_01.md:4`: “summary: Canonicalise the CeFi manifest via single-walk
  migration to v9 schema, closing legacy-only captured cells and unblocking the CeFi apply gate.” vs
  `active/cefi_manifest_canonicalisation_2026_06_01.md:78-82`: “🔴 DATA-STATE FINDING...cefi is a FULL
  re-canonicalisation, NOT an 838-cell gap-fill...the data-state is the truth and the scope is the whole corpus.”
  - why: The frontmatter `summary:` (what an L0/L1 doc-index grep surfaces first) frames this as closing a small
    legacy-only cell gap, but the plan's own body explicitly and repeatedly states the real, much larger scope is a full
    corpus-wide re-canonicalisation (100% of rows non-v9, no source/asset_group columns, blank pipeline
- **DECISION NEEDED**: cefi F2 FUTURE bundle-grain: same doc says CLOSED+VERIFIED (is@4f5faae8 threads venue=) AND
  still-broken (call site lacks venue=). Resolvable by reading instruments-service \_rollup_bundle_grain today. A:
  authorize me to verify the code + collapse the losing passage [REC - pure fact check]. B: you know the answer -> tell
  me which passage wins.

#### [P0] active/data_completion_to_100_all_ag_2026_06_21.md ↔ active/sports_manifest_canonicalisation_2026_06_01.md

- finding ids: 144
- **Sports backfill/scheduler-relaunch sequencing gate** —
  `active/sports_manifest_canonicalisation_2026_06_01.md:243-244`: “No sports backfill / relaunch of `sports-scheduler`
  until this walk is C-GREEN (master L3-gates-L5 + `bucket_name_ssot…` Phase 4 — the drained
  `sports”  vs  `active/data_completion_to_100_all_ag_2026_06_21.md:104-109`: “sports —
  launch-mtds-sports-odds-backfill-vm.sh + launch-sports-is-gap-fill.sh / launch-sports-full-sweep-vm.sh (IS sports
  15.9%→100%) ... VMs RUNNING”
  - why: The sports master plan hard-gates ALL sports backfill / sports-scheduler relaunch behind the canonical v9 walk
    reaching C-GREEN. The sports plan's own E8 verify audits (dated 2026-06-27 through 2026-06-29, i.e. AFTER the
    2026-06-21 launches below) repeatedly report BOTH sports surfaces still RED/BLOCKED (E4 VM apply no
- **DECISION NEEDED**: Sports master hard-gated ALL sports backfills behind canonical-walk C-GREEN;
  data_completion_to_100 launched 8+ sports VMs on 2026-06-21 while the gate doc's own E8 audits show BLOCKED through
  2026-06-29. A: ratify retroactively (backfills were canonical-path, no damage) + record waiver in both docs [REC if
  writes were v9-canonical]. B: order a verification audit of what those VMs wrote before ratifying. C: treat as process
  breach -> add gate-check to VM launch protocol.

#### [P0] active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md ↔ active/issues/capability_wizard_analysis_findings_2026_06_11.md

- finding ids: 292
- **strategy-service LOGIC FREEZE scope vs a shipped collateral-logic change in the same engine file family** —
  `active/issues/capability_wizard_analysis_findings_2026_06_11.md:645-646`: “F27 — carry-staked-basis venue-id CASE
  MISMATCH (`deribit`≠`DERIBIT`) blocks emission. LOGIC-FREEZE. Target: strategy-service.” vs
  `active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:53-56`: “(strategy-service@6e9164b1)
  Build the USDC-collateral + margin-buffer down-size branch in the staked-basis (and basis-perp) engine ... Replaces
  the ha”
  - why: The epic's still-current freeze (epics/strategy_master.md:106-108) bans changes to 'collateral' and
    'engine/strategies/v2/', and the analysis-findings doc explicitly gates F27 (a collateral/perp_venue bug in the SAME
    staked_basis.py engine) on that freeze, unresolved as of the doc's own 2026-06-27 last_updated. Yet the
- **DECISION NEEDED**: Second LOGIC FREEZE conflict: defi_collateral_sizing shipped a collateral-decision change
  (strategy-service@6e9164b1, 2026-06-17) while capability_wizard findings still gate F27 on the freeze. Same ruling
  options as #286 - one decision should settle the freeze's real scope + status, then both docs get aligned.

#### [P0] active/honest_coverage_v2_instrument_denominator_2026_06_28.md ↔ active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md

- finding ids: 66
- **instrument_type canonical casing (shard-atom SSOT)** —
  `active/honest_coverage_v2_instrument_denominator_2026_06_28.md:123`: “`perpetual`, `SPOT_PAIR`/`spot_pair`/`spot`,
  `FUTURE` vs `futures_chain`, `OPTION` vs `options_chain` — data_type [leaking]” vs
  `active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md:244`:
  “(`_VENUE_INSTRUMENT_TYPE["BYBIT-SPOT"] = "spot"`), the captured-row path stamps SPOT_PAIR correctly.”
  - why: honest_coverage_v2's shipped P0 fix (mtds@b989284c, 2026-06-28) explicitly lists `SPOT_PAIR`/`spot_pair`/`spot`
    as a casing-dupe BUG class to collapse into ONE canonical UPPERCASE value ('Fix the WRITER to emit
    canonical-uppercase instrument_type', L125). The later bybit_spot fix (mtds@c4df8ae0 + 9d21b133, 2026-07-07,
- **DECISION NEEDED**: instrument_type canonical casing SSOT conflict: honest_coverage_v2 shipped UPPERCASE canonical
  (SPOT_PAIR) while the later bybit fix maps BYBIT-SPOT to lowercase 'spot' and its relabel script targets lowercase -
  shard-atom identity risk. A: UPPERCASE is canonical; fix bybit mapping + relabel script [REC - matches UAC enum +
  honest-coverage P0]. B: lowercase is canonical; supersede honest_coverage_v2's fix. Needs one ruling then a
  code+relabel pass.

#### [P0] active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md ↔ active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md

- finding ids: 228
- **Whether Tardis historical-data billing has been approved/lifted or is still excluded** —
  `active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md:426`: “(Tardis batch billing gate LIFTED — operator paid;
  access confirmed unlimited.)” vs `active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md:72`: “Status:
  `BLOCKED-CREDENTIALS` — operator has currently EXCLUDED this spend”
  - why: Two open issue docs make opposite factual claims about the same operator billing decision, gating 775.9k
    attempted_failed CeFi cells. This is independently confirmed by direct read (not just via the third doc that flags
    it) and remains unresolved 8+ days later: plan_issue_epic_consolidation_2026_06_30.md:251-257 flags
- **DECISION NEEDED**: Two open issue docs claim opposite states of YOUR Tardis billing decision (LIFTED-paid vs
  BLOCKED-CREDENTIALS-excluded), gating 775.9k attempted_failed CeFi cells. A: billing IS lifted -> close
  cefi_tardis_historical_blocked_credentials + unblock the backfill [REC if you did pay]. B: billing still excluded ->
  correct cefi_hl_aster_batch_data_gaps L426. C: partial (paid once, not standing) -> document exact scope in both.

#### [P0] active/issues/mtds_plan_reconciliation_2026_06_29.md (intra-doc)

- finding ids: 171
- **Whether the manifest-consolidator dual-source dedup bug (M36/M-C2) is an active data-correctness issue** —
  `active/issues/mtds_plan_reconciliation_2026_06_29.md:458`: “Verdict — LATENT fragility, well-mitigated by the
  idempotent-backfill design; NOT an active data-correctness bug.” vs
  `active/issues/mtds_plan_reconciliation_2026_06_29.md:634`: “CONFIRMED unchanged: M-C2 (M36) consolidator
  `_BASE/_OPTIONAL_DEDUP_COLS` both omit `source` → silent dual-source drop (⚠️ NOTIFY, the headline)”
  - why: Same document, same finding, two directly opposed verdicts: Section F's detailed re-verification (with operator
    Harsh's reasoning about idempotent skip-captured backfill) explicitly DOWNGRADES M-C2 to 'latent, NOT an active bug,
    optional low-pri hardening' — but the doc's own final Progress Log entry (dated the same 20
- **DECISION NEEDED**: mtds_plan_reconciliation contradicts ITSELF on consolidator dual-source dedup bug M-C2: body says
  DOWNGRADED to latent (Harsh's idempotent-backfill reasoning), final Progress Log says CONFIRMED unchanged / NOTIFY
  headline. A: accept the DOWNGRADE verdict, fix the Progress Log [REC - the downgrade is the detailed, later-reasoned
  analysis]. B: keep NOTIFY/P0 -> dispatch the dedup-cols hardening fix now.

#### [P0] active/master_data_canonicalisation_migration_catalogue_2026_06_07.md ↔ active/migration_verification_orphan_safety_2026_06_10.md

- finding ids: 128
- **TradFi G4 --apply completion status as of 2026-07-06** —
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:52-55`: “🟡 VM IN FLIGHT (2026-07-06) — slot-6
  TradFi G4 restart. The OOM-blocked TradFi MTDS raw-tick v9 --apply ... is RESTARTED per D3: 2025 smoke VM canonic” vs
  `active/migration_verification_orphan_safety_2026_06_10.md:64-68`: “🟢 V6 CLOSED (2026-07-06). TradFi G4 --apply DONE
  for 2020-2025 + 2026 (7 VMs total...). 2026 year landed 15:14 UTC ... All 5 AGs now canonical (5/5).”
  - why: Both docs carry a live top-of-file banner dated the SAME day (2026-07-06) about the SAME work item (TradFi G4
    raw-tick migration) and reach opposite conclusions: the master coordinator (the operator's 'single pane of glass'
    for this exact gate) says the migration was JUST RESTARTED via a smoke VM with a per-year fan-ou
- **DECISION NEEDED**: TradFi G4 --apply: master catalogue banner (2026-07-06) says RESTARTED via smoke VM with per-year
  fan-out ahead; migration_verification (same day) says DONE 2020-2026, all 5 AGs canonical. Timestamps inside conflict
  (done 15:14 vs restarted 17:01). A: trust migration_verification V6-CLOSED + fix catalogue banner - but ONLY after a
  manifest spot-check confirms tradfi raw-tick v9 coverage [REC: I can run the check on your go]. B: catalogue is right
  (restart superseded a partial run) -> fix migration_verification.

#### [P0] active/master_to_live_defi_2026_05_23.md ↔ epics/defi_master.md

- finding ids: 376
- **Custody provider scope for the June-1 flip (Fireblocks in vs out of scope)** — `epics/defi_master.md:900`: “cutover
  ships on `CLOUD_KMS_ENCRYPTED` (HSM-backed CMK); June-1 flips per-wallet to `COPPER_MPC` / `FIREBLOCKS_MPC` on
  client-provided creds.” vs `active/master_to_live_defi_2026_05_23.md:1417`: “CLOUD_KMS_ENCRYPTED for May-23 cutover →
  COPPER + CEFFU per POD June-1 (POD scope: Copper + CEFFU only; Fireblocks OUT OF SCOPE)... Fireblocks OUT OF ”
  - why: epics/defi_master.md's own custody section header and its R9-resolution banner state June-1 custody flips to
    COPPER_MPC AND FIREBLOCKS_MPC, and the epic still carries an open/deferred FireblocksCustodyProvider todo pointing
    at a successor plan. master_to_live_defi_2026_05_23.md, sourced from the same R9 resolution + a
- **DECISION NEEDED**: Custody June-1 scope: defi_master says flip to COPPER_MPC/FIREBLOCKS_MPC; master_to_live_defi
  says POD scope = Copper + CEFFU only, Fireblocks OUT. A: Fireblocks OUT per POD codification (later + corroborated by
  capability_wizard findings) -> fix defi_master custody section + close its Fireblocks todo as descoped [REC]. B:
  Fireblocks back in scope -> update master_to_live_defi POD scope.

#### [P0] active/sports_p1_golden_window_e2e_gate_2026_06_27.md ↔ active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md

- finding ids: 246
- **P1e golden-window gate status vs Phase-2 (P2a) prerequisite claim** —
  `active/sports_p1_golden_window_e2e_gate_2026_06_27.md:96-101`: “VERDICT = PARTIAL GREEN — blocked on P1d (features)
  ... PHASE-2: BLOCKED — Phase-2 gate opens ONLY when P1d completes and features manifest re-audit r” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:34`: “PREREQ: P1e GREEN (window proven).”
  - why: P1e's own gate doc (which explicitly 'Blocks: P2a, P2b' at its own line 123) recorded its verdict as PARTIAL
    GREEN with Phase-2 explicitly BLOCKED pending P1d completion, and was never updated afterward (last_updated
    2026-06-27, only 128 lines, no later verdict). Yet P2a's banner asserts the prereq is met as fact and t
- **DECISION NEEDED**: P1e golden-window gate recorded PARTIAL GREEN / 'PHASE-2: BLOCKED' but P2a proceeded with weeks
  of backfills claiming 'PREREQ: P1e GREEN'. A: ratify - declare P1e retroactively GREEN (P1d features since
  completed?) + update the gate doc [REC if P1d is in fact done]. B: P1e still partial -> P2a/P2b work is at-risk, order
  re-verify of the golden window before further Phase-2 work.

#### [P0] active/sports_p1_golden_window_e2e_gate_2026_06_27.md ↔ active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md

- finding ids: 247
- **P1e golden-window gate status vs Phase-2 (P2b) prerequisite claim** —
  `active/sports_p1_golden_window_e2e_gate_2026_06_27.md:101,123`: “PHASE-2: BLOCKED — Phase-2 gate opens ONLY when P1d
  completes ... Blocks: P2a, P2b (the expansion does not start until the window is proven).” vs
  `active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:73`: “PREREQ: P1e GREEN. One agent,
  `data_engineering` (Sonnet/high).”
  - why: Same conflict as the P2a candidate, applied to P2b: the plan's banner treats P1e as satisfied fact and dozens
    of agent-sessions ran extensive backfills (weather/SFI/TM/understat/footystats/odds-api, 2026-06-27→2026-07-09)
    under that assumption, while P1e's own recorded verdict is PARTIAL GREEN with Phase-2 explicitly B
- **DECISION NEEDED**: Same as #246 for P2b (reference+odds backfill). Same ruling should cover both.

#### [P1] CLAUDE.md ↔ plans/active/gcs_bucket_estate_cleanup_2026_07_10.md

- finding ids: 10010
- **model-tier self-check** — `plans/active/gcs_bucket_estate_cleanup_2026_07_10.md:35-40`: “model_tier_note: "Flagged
  per AUTONOMOUS_AGENT_RULES self-check — this is a long cross-repo autonomous loop, which CLAUDE.md's
  model-tier-selection no” vs `CLAUDE.md:42`: “Self-check every task start: Sonnet on opus-required → STOP; thinking
  mismatch → HARD STOP.”
  - why: CLAUDE.md states the model-tier self-check as an unconditional HARD RULE ("Sonnet on opus-required → STOP")
    with no documented carve-out. This plan (status: complete, still live in the active corpus with no reconciling
    banner) explicitly identifies itself as an opus-required-shaped task, admits it ran on Sonnet, and —
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/INDEX.md ↔ active/prediction_capture_incident_remediation_2026_07_06.md

- finding ids: 2
- **KALSHI/POLYMARKET-PERP demo-first repoint gating condition** — `active/INDEX.md:190`: “DONE; demo-first repoint
  gated on the pre-existing `prediction_venue_perps_and_live_clob_depth` plan's ownership; prod” vs
  `active/prediction_capture_incident_remediation_2026_07_06.md:148`: “## Workstream B — KALSHI-PERP / POLYMARKET-PERP
  adapter correction (demo-first; prod gated on access)”
  - why: INDEX.md claims the demo-first repoint itself is gated on another plan's
    ('prediction_venue_perps_and_live_clob_depth') ownership. The actual plan (its own SSOT) states in its Workstream B
    header and body (lines 95, 148) that ONLY the prod cutover is gated (on access/operator decision); Phase 1 is
    explicitly labeled '(
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md ↔ active/ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md

- finding ids: 224
- **Whether the live AO backend needs a manual multi-step deploy runbook or auto-deploys via FF-pull+reload** —
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:493-497`: “The live server was deliberately NEVER
  restarted during development, so this is the FIRST deploy of all of it at once (deploy runbook: disable service” vs
  `active/ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md:471-473`: “Deploy mechanism confirmed:
  uvicorn runs under systemd with `--reload --reload-dir server`, so the 5-min FF-pull cron IS the deploy — the reloader
  res”
  - why: Doc A's still-open P1 DEPLOY todo (disable service/stop backend/pull/manually restart) is premised on code
    sitting inert on LDR until an operator runs the manual VM-agent runbook. Two days later Doc B proves the opposite
    for the same live service: the systemd uvicorn process auto-reloads on every 5-min FF-pull cron tic
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md ↔ active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md

- finding ids: 218
- **Fleet-stall issue doc still 'open' with unchecked P0 prevention todos that the sibling plan (which explicitly ** —
  `active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md:121-127`: “[ ] [CODE] P0. regen must propagate
  tier/role changes to existing queued tasks... [ ] [CODE] P0. Add an `assigned_role` craft filter to
  `pick_next_tas”  vs  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:684`: “🎯 ALL 3 ROOT CAUSES FIXED
  (RC-1/RC-2/RC-3) — the incident is resolved in code.”
  - why: The dispatch-correctness plan explicitly states it 'Records the incident in
    issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md' and ships exactly RC-1 (regen propagate), RC-2
    (craft filter/roles), RC-3 (slot_skips hygiene) with commit shas. The issue doc itself, however, still carries
    status: open and every
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md ↔ epics/orchestrator_master.md

- finding ids: 216
- **Epic asserts zero active child plans while multiple P0 active/open docs cite it as parent_epic** —
  `epics/orchestrator_master.md:183-186`: “All originally-assigned sub-plans are now archived...Remaining non-archived
  orchestrator work lives in the Phase 6/9/11 rows...next regeneration will ” vs
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:14,44`: “status: active ... parent_epic:
  orchestrator_master”
  - why: The epic hub (parent to this whole cluster) claims all sub-plans archived and expects the next regen to show
    zero active plans, yet this batch alone has at least 6 status:active/open docs (07-07, 07-09, 07-10 plans + 3 issue
    docs) all declaring parent_epic: orchestrator_master and carrying live P0/P1 work. An agent or
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md ↔ active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md

- finding ids: 82
- **tab-branch model retirement vs live remediation guidance** —
  `active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md:60`: “cherry-pick / rebase onto a current
  `tab/<vm>/<N>` slot branch, QG-green, quickmerge → LDR (inherit the orphan work), then delete the rootm branch.” vs
  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:96`: “HIGH — `agents/RULES.md:26-29` teaches the
  RETIRED tab-branch model as current fact.”
  - why: orphan_rootm (status open, last_updated 2026-06-27) instructs a future worker to rebase orphaned work onto 'a
    current tab/<vm>/<N> slot branch' — but the tab-branch model was RETIRED workspace-wide since 2026-06-08
    (/codex/05-infrastructure/per-tab-worktrees.md: 'tab/<op>/N tab-branch model RETIRED'); a sibling 2026-07-
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md ↔ epics/orchestrator_master.md

- finding ids: 217,323
- **Epic still frames current architecture as a 9-epic-VM fleet; corpus confirms a single-VM pivot happened and tr** —
  `epics/orchestrator_master.md:64-70`: “Owns: agent-orchestrator multi-VM stack (central/orchestrator VM `planning` +
  human planning VM `human-planning` + 9 epic VMs...) ... Assigned VM:
  `vm”  vs  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:109`: “Predates the single-VM pivot ("VM
  fleet" plural framing, fixed per-phase slot ownership).”
  - why: The epic (no banner, status active) presents the 9-VM fleet + per-VM assignment as the current, live topology
    owned by this epic. The sibling 07-10 audit plan (same epic cluster) explicitly labels 'VM fleet' plural framing as
    something that PREDATES a since-completed 'single-VM pivot' and treats it as dead content to b
- **orchestrator_master active-child-plan count** — `epics/orchestrator_master.md:183-186`: “"All originally-assigned
  sub-plans are now archived...Auto-populated by scripts/plans/populate_epic_bodies_2026_05_21.py (next regeneration
  will surfa” vs `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:17,40`: “status: active / parent_epic:
  orchestrator_master (last_updated 2026-07-10)”
  - why: The epic explicitly predicts zero active children going forward, but grep of plans/active/\*.md shows 8 plans
    currently declare parent_epic: orchestrator_master, including one last-updated the day before this audit
    (2026-07-10) and none of them are surfaced anywhere in the epic body — an agent trusting the epic's own cl
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/canonical_id_builder_retrofit_checklist_2026_07_08.md ↔ active/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md

- finding ids: 341
- **Betfair `/`-delimited instrument_id fix scope** —
  `active/canonical_id_builder_retrofit_checklist_2026_07_08.md:117-123`: “Sports keeps its own ID scheme (not forced
  into VENUE:TYPE:SYMBOL — operator decision), so this does NOT route through build_canonical_instrument_id; ” vs
  `active/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md:139,155`: “Two real options, either is
  legitimate — this needs a decision, not more investigation... No code changed in this session for this finding.”
  - why: Same-day (2026-07-08), same file:line (betfair.py:279) target: the retrofit checklist plan (not
    cross-referencing the issue doc at all) frames this as a simple, isolated single-repo delimiter swap plus a
    downstream-consumer check. The issue doc (open, filed same session) found the `/`-shape is independently built/parse
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md ↔ active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md

- finding ids: 78
- **Whether "SIT-green" is a meaningful validation gate for cross-repo correctness** —
  `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:67`: “**SIT-green** — the cross-repo SIT suite validated this
  repo's LDR tree (`full-workspace-sit` on the promoted content).” vs
  `active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:74`: “Nightly/dispatch
  `full-workspace-sit` runs **green** (coverage gap; also does not gate promotes).”
  - why: The CI/CD MVP plan names SIT-green as one of only three gates on LDR→main promotion, presenting it as
    validating the promoted tree. The later breaking-change-differ issue doc documents a real incident where a
    consumer-breaking UAC registry change reached main because SIT (a) never gated the promote at all (fires only o
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/citadel_paper_batch_live_reconciliation_2026_06_19.md (intra-doc)

- finding ids: 15,365,17
- **foundation-completion-gate ordering vs harness declared PROVEN while Phase 2 is still open** —
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:77`: “Phases 1–3 are the foundation; the harness (4) is
  meaningless until the fill model is unified (1) and trades are identified (2) and the ledger exists ” vs
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:346`: “**T+1 reconcile ε=0 on real data**:
  `reconcile_day(paper, batch)` → `is_deterministic=True`, bug_class=NONE, mean_fill_price_delta_bps=0.”
  - why: The plan's own Citadel-standard §8 ordering rule says the reconciliation harness (Phase 4) is 'meaningless'
    without Phase 2 (per-trade identity) being done first, yet Phase 2's two items (P2.1 line 203, P2.2 line 205) remain
    unchecked `[ ]` throughout the document while Phase 4/7/9/10/11 repeatedly declare the harness
- **Is the paper↔batch determinism spine (Phases 0-11) fully DONE, including Phase 2 per-trade identity (G2)?** —
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:84-89`: “The paper↔batch determinism + monitoring SPINE
  (Phases 0–11) is DONE. Phase 11 is the last phase (no P12). ... all shipped.” vs
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:201-206`: “## Phase 2 — Per-trade identity in execution
  events (G2) - [ ] [CODE] P2.1. Execution events gain trade_key + side/qty/price/fees ... - [ ] [CODE] P2.”
  - why: The plan's 'Remaining-work register' banner declares the full Phases 0-11 spine DONE/shipped, but Phase 2 (one
    of those numbered phases, covering gap G2 'per-trade identity in execution events') has both its todos still
    unchecked '[ ]' with no shipped commit cited. The doc partially self-qualifies ('89 boxes done / rem
- **"the GroupCRunner LINCHPIN" labeled both DONE (P1.4) and REMAINING (P11.6 hand-off item)** —
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:1183`: “(5) **P11.6** — the GroupCRunner LINCHPIN (batch
  runs the SAME execution-service matching engine as paper, ε=0).” vs
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:187`: “P1.4. **Complete `GroupCRunner` — THE LINCHPIN**
  — DONE (`execution-service@d36b751f`, QG green, 17 tests...).”
  - why: The 2026-06-22 hand-off-brief Progress Log entry lists item (5) 'P11.6 — the GroupCRunner LINCHPIN ... ε=0' as
    REMAINING work to drive to done, reusing the exact 'LINCHPIN' label the plan already assigned to P1.4, which is
    marked ✅ DONE far earlier in the same document. The two items are meant to be different sub-piece
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/citadel_paper_batch_live_reconciliation_2026_06_19.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 366
- **PassiveLedger synthesiser — gated on operator [ack] and deferred, or already shipped?** —
  `epics/global_ledger_pnl_attribution_master.md:139-140`: “Phase 8 — strategy-service PassiveLedger synthesiser:
  Per-event divergence check path. DEFERRED-POST-CUTOVER (gate: Phase 3/4/5 ack).” vs
  `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:216-221`: “P3.2. PassiveLedger synthesiser — DONE
  (unified-trading-library@09885861, 16 tests): ledger/materialize.py::passive_ledger_row() builds LedgerRow(...)”
  - why: The epic (last_updated 2026-05-23, status active) still lists the PassiveLedger synthesiser as
    DEFERRED-POST-CUTOVER pending operator [ack] on Phase 3/4/5 decisions from an archived discovery plan. But the
    citadel determinism-spine plan (created 2026-06-19, active) already shipped a PassiveLedger synthesiser (unified-t
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/data_completion_to_100_all_ag_2026_06_21.md (intra-doc)

- finding ids: 138
- **Definition-of-100%/honest-coverage denominator formula (SSOT)** —
  `active/data_completion_to_100_all_ag_2026_06_21.md:3242`: “Honest-empty is EXCLUDED from the denominator
  (pre-genesis, pre-launch, no-fixture, weekend/holiday, not-listed, documented structural gaps).” vs
  `active/data_completion_to_100_all_ag_2026_06_21.md:3244`: “% = captured / (captured + empty_confirmed +
  attempted_failed + expected_unattempted)”
  - why: The doc's own 'Durable contract — Definition of 100% (SSOT)' asserts empty_confirmed is excluded from the
    denominator, then in the very next sentence gives the canonical formula with empty_confirmed explicitly summed INTO
    the denominator. An agent computing honest-coverage % from this SSOT paragraph could apply either
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/data_eng_role_vertical_pilot_2026_06_25.md (intra-doc)

- finding ids: 8
- **Intra-doc frontmatter vs body disagreement on assigned_vm** —
  `active/data_eng_role_vertical_pilot_2026_06_25.md:15`: “assigned_vm: NA” vs
  `active/data_eng_role_vertical_pilot_2026_06_25.md:39`: “**Dispatch note**: `assigned_vm: harsh_pc` (the standalone
  fleet-dispatch test host ... **Operator chose to dispatch this plan**”
  - why: The frontmatter states assigned_vm:NA (not dispatched to any backend under strict matching) while the body's
    Dispatch note asserts the operator chose assigned_vm:harsh_pc for this exact plan -- the two fields of the same
    document disagree on whether this plan is currently dispatched, and neither the frontmatter nor the
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md (intra-doc)

- finding ids: 38
- **Duplicate 'Phase 4' todo, same doc, contradictory checkbox states** —
  `active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md:148`: “[ ] [SCRIPT] P1. Phase 4 — Cat-C
  test-fixture modernization. ... (2) market-tick-data-service (215) ... (3) features-service (13), strategy-service (9”
  vs `active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md:161`: “[x] ✅ [SCRIPT] P1. Phase 4 — Cat-C
  test-fixture modernization. ... refresh quarterly via a cron VM that probes the recent finalized block per chain. .”
  - why: Two todos both titled 'Phase 4 — Cat-C test-fixture modernization' appear in the same plan: one unchecked
    describing an address-citation backfill across
    MTDS(215)/features-service(13)/strategy-service(9)/deployment-service(3)/alerting/e2e/ui(1 each) — exactly the same
    counts already shipped and checked-done in Phase 5.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md (intra-doc)

- finding ids: 46
- **Phase-D historical carry tracer checked ✅ done without meeting the plan's own stated success criterion** —
  `active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md:66`: “[x] [VERIFY] P0. Phase-D gate … ✅ —
  strategy-service@971b7217 … run with --seed 42 shows 10/10 SKIP_NO_DATA (backfill not yet reached — expected per p” vs
  `active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md:99`: “The Phase-D historical carry tracer passes the
  10-sample-day intent test (≥5/7 archetypes non-empty, no silent NaN-only days) over 2022→today.”
  - why: The P0 todo is checked done, but its own cited evidence is 10/10 SKIP_NO_DATA (zero of the required ≥5/7
    archetypes were non-empty on any sampled day) because the backfill hadn't reached that window — the gate-LOGIC was
    verified (unit tests + rc=0) but the actual over-2022→today data outcome the plan's Success Criteria
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/escalation_pipeline_mvp_2026_06_25.md ↔ epics/escalation_and_disaster_recovery_master.md

- finding ids: 50
- **E1 child-plan status (proposed vs active)** — `epics/escalation_and_disaster_recovery_master.md:84`: “| E1 |
  `escalation_pipeline_mvp_2026_06_25` | Generalize `/blocked` → role-agnostic escalation record ... | P1 | proposed |”
  vs `active/escalation_pipeline_mvp_2026_06_25.md:5`: “status: active”
  - why: The epic's workstream registry table lists E1 (escalation_pipeline_mvp_2026_06_25) with status "proposed" —
    implying it is not yet greenlit/started — while the child plan's own frontmatter declares itself "status: active"
    (in-flight, dispatchable). An agent reading only the epic table would treat E1 as not-yet-started
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/execution_fidelity_tiers_uac_governed_2026_06_28.md ↔ epics/execution_master.md

- finding ids: 51
- **Epic child-plan tracking vs actual plan frontmatter** — `66`: “\_(no other active plans currently declare
  `parent_epic: execution_master`. Audit-pool wrapper plans for this epic land” vs `14`: “parent_epic: execution_master”
  - why: The epic's own 'Assigned active plans' body section (L64-67) asserts no active plan declares parent_epic:
    execution_master, but this plan's frontmatter does declare exactly that, and the epic's own
    'related'/'related_plans' frontmatter fields (L16, L29) even list this same file by path — so the epic body claim is
    stale
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/foundation_gates_and_capture_to_100_2026_07_06.md ↔ active/instruments_completion_tracker_2026_07_06.md

- finding ids: 358,359,360
- **instruments foundation gate sign-offs (cefi G2-G5)** — `active/instruments_completion_tracker_2026_07_06.md:283`: “-
  [ ] [VERIFY] P0. Reconcile checkbox drift; take the formal **G2 → G5** sign-offs (cefi)” vs
  `active/foundation_gates_and_capture_to_100_2026_07_06.md:146`: “[x] ✅ [SCRIPT] P0. **G2 → G5 reconcile + sign-off
  (cefi) — DONE 2026-07-06**. Reconciled the checkbox-vs-reality drift...”
  - why: The coordinator tracker (status:active, last_updated 2026-07-07) still lists the G2→G5 cefi sign-off
    reconciliation as an open Stage-4 todo, while AO Plan 5 (foundation_gates_and_capture_to_100, status:complete) shows
    this exact task done and signed off 2026-07-06. Tracker's own Progress Log acknowledges other Plan-5 i
- **systemic unregistered-handler audit completion status** — `active/instruments_completion_tracker_2026_07_06.md:306`:
  “- [ ] [SCRIPT] P1. **Systemic unregistered-handler audit** (generalizes the Deribit C5 bug — do BEFORE the Stage-3
  re-measure).” vs `active/foundation_gates_and_capture_to_100_2026_07_06.md:77`: “- [x] ✅ [SCRIPT] P0. **Systemic
  unregistered-handler audit** (generalizes the Deribit C5 bug). Diff every handler class...”
  - why: Same task, described in near-identical wording in both docs. The tracker (coordinator, active) still lists it
    unchecked in Stage 5, but the executing plan (status:complete) shows it done 2026-07-06 with shipped SHAs. The
    tracker's own Progress Log (line ~479) even cites this exact Plan-5 line as '✓ done' elsewhere, yet
- **DeFi risk_params MTDS handler capture item** — `active/instruments_completion_tracker_2026_07_06.md:296`: “- [ ]
  [CODE] P1. DeFi `risk_params` MTDS handler (193,042 EU, no handler today)” vs
  `active/foundation_gates_and_capture_to_100_2026_07_06.md:176`: “- [x] ✅ [CODE] P1. **DeFi `risk_params` MTDS
  handler** — 193,042 `expected_unattempted` cells with no handler today. ... DRIFT RECONCILED + C5-avoidan”
  - why: The coordinator tracker lists the risk_params handler as an open Stage-5 capture todo, while the completed AO
    Plan 5 shows it already built, registered, tested and shipped (mts@90cd3975), with the handler in fact originally
    shipped even earlier (2026-06-24). Same pattern of tracker not reflecting Plan-5's completion.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/instruments_foundation_completeness_2026_06_24.md (intra-doc)

- finding ids: 95
- **Gate-sequencing discipline (G1 sign-off never recorded before G2-G5)** —
  `active/instruments_foundation_completeness_2026_06_24.md:608`: “No gate is crossed without operator sign-off. No
  parallel-up across gates within an AG.” vs `active/instruments_foundation_completeness_2026_06_24.md:430-431`: “🚦
  GATE G1 — sign-off. / [x] ✅ ... G2 — backfill cefi all venues × all days × all years — SIGNED OFF 2026-07-06
  (RECONCILE: already-run, not a redo).”
  - why: The plan's own hard rule bans crossing a gate without sign-off and bans parallel-up across gates, yet the G1
    gate line carries no recorded sign-off evidence (unlike G2/G3/G4 which are each explicitly 'SIGNED OFF 2026-07-06')
    while G1 sub-item G1.2 is still marked partial/REMAINING — a live gate-discipline violation an
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/batch_live_reconciliation_service_audit_2026_05_27.md (intra-doc)

- finding ids: 21,364,20
- **D2/D3/D4 decision finality (intra-doc)** — `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:33`:
  “D1 already DECIDED=A. The three routed items are now ruled (FINAL). Execution: slot 7 records each into
  batch_live_symmetry_master (SSOT) and ships th” vs
  `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:408`: “D2 — Canonical position baseline: query
  strategy-service/position vs ratify event archives. → ROUTED TO IKENNA.”
  - why: The top-of-doc banner (dated 2026-06-01) declares D2/D3/D4 'now ruled (FINAL)' with concrete rulings spelled
    out, but the § 7.2 decisions ledger further down (dated 2026-05-27, never updated) still frames the same three items
    as open '❓ Needs operator input... ROUTED TO IKENNA' questions with multiple unresolved option
- **BLRS D2/D3/D4 recon decisions — already ruled FINAL, or still open operator questions?** —
  `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:33-42`: “OPERATOR DECISION LEDGER — 2026-06-01
  ... D1 already DECIDED=A. The three routed items are now ruled (FINAL) ... D2 — BLRS calls strategy-service/posi” vs
  `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:408-422`: “D2 — Canonical position baseline:
  query strategy-service/position vs ratify event archives. → ROUTED TO IKENNA. ... Either: (A) ... (B) ... D3 — ... →”
  - why: The doc's own top banner (dated 2026-06-01, presumably added after the original 2026-05-27 pass-2 audit) states
    D2/D3/D4 are 'already DECIDED=A'/'now ruled (FINAL)' with concrete resolutions. But §7.2 of the same document, never
    updated to match, still frames D2/D3/D4 as open '❓ NEEDS-OPERATOR' questions with multiple
- **stage1 ml_recon latency_delta_ms implementation status (intra-doc)** —
  `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:269`: “hardcoded `0.0` (TODO: timestamp compare)
  ... **CODE stub**” vs `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:342`: “G2 ✅ DONE
  (BLRS@07222f6) `stage1` `latency_delta_ms` now a real median |batch−live| `metadata.inference_duration_ms` over
  matched keys”
  - why: The main § 4 Codex↔Code drift table (and § 7.1 item 5) still describes stage1 latency delta as an unimplemented
    hardcoded 0.0 stub needing action, while § 6's G2 entry (added later in the same doc) says it was already fixed and
    shipped with tests. The two sections of the same audit disagree on current implementation st
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md ↔ active/mvp_backfill_cefi_tick_v10_2026_06_27.md

- finding ids: 27
- **Whether CeFi batch-Tardis historical backfill spend is operator-excluded** —
  `active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md:57`: “"batch Tardis (cefi historical) is
  BILLING-GATED — do NOT launch cefi batch backfills" ... Status: BLOCKED-CREDENTIALS, no agent action until operator”
  vs `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:189`: “Backfill trades + book_snapshot_5 for the perp-gated MVP
  universe, MAJORS FIRST — WAVE-1 LAUNCHED 2026-06-28T03:47Z across 8 venues, all RUNNING”
  - why: The open (status=open, last_updated 2026-06-27) issue doc quotes an explicit operator directive excluding ALL
    batch-Tardis CeFi historical backfills as billing-gated, requiring operator ack before any agent action. The active
    mvp_backfill plan (created the same week, 2026-06-27) proceeds to launch and run exactly this
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md ↔ active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md

- finding ids: 113
- **EULER_V2 production-capture wiring status** —
  `active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md:324-329`: “"Wire VENUS/BENQI/RADIANT/EULER_V2
  into the production orchestrator — fixed... 7 venues flipped pipeline→live: ... EULER_V2-ETHEREUM" (instruments-ser”
  vs `active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md:216-223`: “"Decide whether to actually wire
  EULER_V2 capture given real subgraph infra now exists (verified working 2026-06-02, never actually polled)" — open P2”
  - why: One doc (mtds_is_full_adapter) records EULER_V2-ETHEREUM as already flipped pipeline→live in the production
    orchestrator on 2026-07-10 with a cited commit SHA; the other doc (defi_turbo_api), also touched 2026-07-10, treats
    EULER_V2 capture as still undecided/never-polled and asks for a decision on whether to wire it a
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/fleet_data_acquisition_health_2026_06_21.md ↔ active/issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md

- finding ids: 77
- **Does the ASTER venue produce `liquidations` (and `book_snapshot`) data at all?** —
  `active/issues/fleet_data_acquisition_health_2026_06_21.md:121`: “registered `hyperliquid` + `aster` as cefi sources
  on the 5 cefi perp market-data types they produce —
  `(cefi, trades|ohlcv_1m|book_snapshot|liquidati”  vs  `active/issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md:152`: “violating `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]`
  (trades/derivative_ticker/perp_funding only — ASTER is a perp DEX with no orderbook-snapshot or liqu”
  - why: The 2026-06-21 fix registers ASTER as a valid source for cefi `liquidations` (and `book_snapshot`) data types,
    i.e. asserting ASTER produces them. The 2026-07-03 resolved reconciliation doc directly states ASTER is 'a perp DEX
    with no orderbook-snapshot or liquidation feed', confirms zero real ASTER liquidations/book5
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md (intra-doc)

- finding ids: 256
- **issue doc completion state overclaimed** —
  `active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md:251`: “This was the last open todo in this
  doc** — all 7 todos are now `- [x]`.” vs `active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md:165`:
  “[ ] [DATA] P2. **BLOCKED-PREREQUISITES (2026-07-08, slot-8).\*\* \*\*Re-verify + re-dispatch footystats backfill VM”
  - why: The Progress Log's narrative claims all 7 todos in this doc are now checked/done, but the Actionable-todos
    checklist in the same doc still shows todo #4 (the actual pending_fetch==0 re-verify/re-dispatch gate that flips the
    upstream sports_p2 item #5/#7 gates) unchecked and explicitly BLOCKED-PREREQUISITES. Frontmatter
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md (intra-doc)

- finding ids: 104
- **DERIBIT-COMBO's target instrument_type label: FUTURE_COMBO vs COMBO** —
  `active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:390-392`: “DERIBIT-COMBO should
  become instrument_type=FUTURE_COMBO under the single DERIBIT venue instead of a separate venue identity” vs
  `active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:464-467`: “DERIBIT-COMBO's
  instrument_type was invented as "FUTURE_COMBO" without verification — the real adapter stamps a single generic COMBO”
  - why: The still-open (unchecked) todo instructing engineers to retire DERIBIT-COMBO into
    'instrument_type=FUTURE_COMBO' was never edited after this same doc's own later (round-3) investigation found that
    label was fabricated and the real, production-confirmed value is the generic 'COMBO' (375 real rows,
    deribit_combo_adapter
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/instruments_service_plan_reconciliation_2026_06_29.md ↔ active/issues/wsfeedconnector_phase35_gap_2026_07_06.md

- finding ids: 98
- **Open task plans to eventually drop bare COINBASE from UAC, contradicting a LANDED anti-removal decision** —
  `active/issues/wsfeedconnector_phase35_gap_2026_07_06.md:150`: “"(3) land the migration; THEN drop bare `COINBASE`
  from UAC. Original gate remains: ... entry removed from `VENUES_BY_ASSET_GROUP[\"cefi\"]`"” vs
  `active/issues/instruments_service_plan_reconciliation_2026_06_29.md:92`: “"The 'push the split INTO UAC / drop bare
  forms' approach was REJECTED ... Conflicts: plans proposing to ... drop bare `OKX`/`COINBASE`."”
  - why: wsfeedconnector's still-open CODE task (title: 'COINBASE bare-name UAC removal + downstream migration')
    explicitly sequences toward dropping bare COINBASE from UAC once prerequisites land, while the reconciliation doc's
    SSOT assertion ledger (A3, status LANDED) records that dropping bare OKX/COINBASE was already REJECT
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/instruments_service_plan_reconciliation_2026_06_29.md ↔ epics/sports_master.md

- finding ids: 372
- **Which venues are currently members of UAC's sports (odds) venue universe** — `epics/sports_master.md:243-244`:
  “`uac@56d941e` — removed `DRAFTKINGS`, `FANDUEL`, `BET365` from `VENUES_BY_ASSET_GROUP["sports"]` +
  `VENUE_DATA_TYPE_CAPABILITIES`; sports universe =
  `”  vs  `active/issues/instruments_service_plan_reconciliation_2026_06_29.md:94-97,930-931,939`: “A4 `LANDED` — ...
  UAC sports = MTDS odds venues (ODDS_API/PINNACLE/BETFAIR\*/DRAFTKINGS/FANDUEL). ... sports 8 odds venues ... sports A4
  two-registry i”
  - why: sports_master (status: active, updated through 2026-07-08 with a further 'Scrapers retired 2026-07-08' section)
    documents that DRAFTKINGS and FANDUEL were REMOVED from VENUES_BY_ASSET_GROUP["sports"] on 2026-05-12 (commit
    uac@56d941e), leaving only [ODDS_API, PINNACLE, BETFAIR] as the active sports venue universe (a de
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md ↔ active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md

- finding ids: 116
- **Whether getting the UTL dtype-coercion fix into the deployed Cloud Run image resolves is-daily-enum-{predictio** —
  `active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md:91`: “"The fix (fixed-UTL→image) heals both
  and is escalated to P0 in the plan's Workstream A."” vs
  `active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md:75-78`: “"The image was rebuilt
  with the coercion... docker-inspected it... UTL version 1.6.0. Yet the enum still fails. So the coercion is present
  and is NOT ”
  - why: prediction_universe_capture_dead (open, filed 2026-07-06) asserts as a still-standing claim that shipping the
    fixed UTL to the deployed image 'heals both' jobs, framing the remaining work as purely a rollout/deploy step. The
    same-day sibling handoff doc (also open, re-confirmed failing through 2026-07-09 in its own 202
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md (intra-doc)

- finding ids: 134,132
- **Which epic owns this open P2 manifest-OOM issue doc** —
  `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:14`: “parent_epic: manifest_master” vs
  `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:71`: “Owner: a UTL/manifest slot. parent epic:
  mtds_mdps_master.”
  - why: The doc's own frontmatter declares parent_epic: manifest_master, but its body's closing line declares a
    different parent epic (mtds_mdps_master). An agent routing/dispatching this open issue would get two different
    answers depending on whether it reads frontmatter or body text — a direct intra-doc ownership contradicti
- **Intra-doc epic-ownership disagreement (frontmatter vs body)** —
  `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:14`: “parent_epic: manifest_master” vs
  `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:71`: “Cross-cutting (touches the LIVE
  cefi/sports/tradfi manifest path) → validate carefully; NOT blocking the DeFi backfill (highmem unblocks it). Owner:
  a”
  - why: The issue doc's frontmatter declares parent_epic: manifest_master, but the body's closing line assigns it to a
    DIFFERENT epic, 'parent epic: mtds_mdps_master'. An epic-rollup query keyed on either field would attribute this
    open P2 issue inconsistently, and it's unclear which epic's owner is actually accountable for cl
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md ↔ active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md

- finding ids: 121
- **book_microstructure_handler.py deletion status** —
  `active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md:38-63`: “book_microstructure_handler.py: 0
  contract calls < baseline 8 (file missing or renamed)... needs the same diagnose-before-fix treatment... confirm whe”
  vs `active/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md:141-150`: “Retired MTDS's
  order_flow_imbalance entirely — deleted book_microstructure_handler.py... Evidence: market-tick-data-service@a4fb3d13,
  quality-gates.sh”
  - why: The baseline-regression issue (filed 2026-07-09, still open) treats book_microstructure_handler.py's
    disappearance as an undiagnosed mystery that might need 'restoring' the missing contract calls, without
    acknowledging that a separate issue doc (filed 2026-07-07, two days earlier, same repo) already confirms this file
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md (intra-doc)

- finding ids: 176
- **Deribit funding cadence — stale evidence table vs later correction, same doc** —
  `active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md:50`: “"Deribit | ... hourly rows w/ interest_1h |
  1h (24/day) | 1h ✅ | 3.0 ❌ (8× under)" — table marks UAC perp_funding_cadence deribit=1h as CORRECT” vs
  `active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md:107-110`: “"CONFIRMED 2026-06-17 ... it is the 8h
  FIGURE ... Resolution: UAC FUNDING_CADENCE_SECONDS["deribit"] corrected 1h → 8h so annualise(rate,"deribit") ma”
  - why: Finding-1's comparison table (top of doc) still displays UAC's deribit value as 1h with a ✅ (correct) mark,
    but the doc's own later resolution changes UAC's actual shipped value to 8h and explicitly says the prior 1h was
    wrong for the stored figure. The table was never updated to reflect the fix, so a reader/agent usin
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/pm_scripts_typecheck_debt_2026_06_11.md ↔ active/issues/uv_pin_fleet_drift_2026_06_22.md

- finding ids: 87
- **Whether PM scripts/ basedpyright errors can still block (red) the LDR→main promotion PR** —
  `active/issues/pm_scripts_typecheck_debt_2026_06_11.md:76-79`: “Recurring-ratchet trap RESOLVED — basedpyright is
  WARN-ONLY for PM `scripts/` ... Removed `BASEDPYRIGHT_MAX_ERRORS=1555` ... base-service runs basedpy” vs
  `active/issues/uv_pin_fleet_drift_2026_06_22.md:221-230`: “RESIDUAL BLOCKER (separate, pre-existing CI-infra incident)
  — PR #498's v2 still RED on `QG slice (typecheck)`: ~3082 `reportAny`/`reportUnknown*` err”
  - why: pm_scripts_typecheck_debt (fix shipped unified-trading-pm@22b2f89d7 PR #523, 2026-06-24) unconditionally
    asserts the WARN-ONLY change 'can never red the LDR→main PR / starve the fleet' and downgrades itself to priority P3
    'no urgency (the gate no longer blocks anything)'. uv_pin_fleet_drift's residual-blocker entry (do
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/terminated_vm_disk_orphan_no_reaper_2026_06_30.md ↔ active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md

- finding ids: 83
- **watchdog relaunch guidance risks repeating the live-VM-kill incident** —
  `active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md:89`: “Keep the watchdog in `--dry-run` for
  the duration of the manual-backfill campaign (`launch-vm-zombie-watchdog.sh --dry-run`). Only re-enable reaping o” vs
  `active/issues/terminated_vm_disk_orphan_no_reaper_2026_06_30.md:101`: “The currently-running
  `vm-zombie-watchdog-20260623` is on the pre-`738637c` code. The reaper activates only once the watchdog runs fresh
  code: ... oth”
  - why: The still-open zombie_watchdog doc mandates the watchdog stay `--dry-run` while any manual-backfill campaign is
    live, after the launcher's recorded DEFAULT `dry_run=false` caused it to kill 9 live campaign VMs on 2026-06-23. The
    terminated_vm_disk_orphan doc's open P3 follow-up recommends relaunching that same watchdog
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md ↔ active/tradfi_massive_dual_source_2026_05_28.md

- finding ids: 305
- **Continued Massive dual-source integration vs. operator's databento-primary simplification/purge** —
  `active/tradfi_massive_dual_source_2026_05_28.md:270`: “This defeats the operator's core requirement (consumers can't
  tell the source). **Must land BEFORE the paid backfill.**” vs
  `active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md:122`: “OPERATOR DECISION: purge `massive`
  entirely from the tradfi manifest (databento primary everywhere → simpler). EXECUTED.”
  - why: tradfi_massive_dual_source (status active, last_updated 2026-06-27 — three days AFTER the purge) still carries
    open P0 Phase-4b todos directing agents to rebuild/wire the MassiveTradfiRestConnector into the canonical write path
    before a 'paid backfill', with no acknowledgment of the EU-drift issue doc's 2026-06-24 oper
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/master_data_canonicalisation_migration_catalogue_2026_06_07.md (intra-doc)

- finding ids: 129
- **Gate-State Board vs WAVE checklist: G4 apply status per asset_group** —
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:158-184`: “As of 2026-06-16 ... G4 🟡 (gated) —
  every per-AG G4 --apply checkbox is open [ ]; ... Recomputed from the registered plans' checkboxes ... NOT hand-ma” vs
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:244-261`: “slot 2 (DeFi) — G4 --apply ... ✅
  COMPLETE. / slot 3 (CeFi) — G4 --apply ... ✅ COMPLETE. / slot 4 (Sports) — G4 --apply ... ✅ COMPLETE. / slot 5
  (Predi”
  - why: The Gate-State Board table explicitly claims to be the authoritative, non-hand-maintained summary ('Recomputed
    ... NOT hand-maintained divergent state', 'Refresh at each gate promotion') and states every AG's G4 checkbox is
    still open as of 2026-06-16. But the same document's own WAVE dispatch checklist shows 4 of 5 AG
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/master_data_canonicalisation_migration_catalogue_2026_06_07.md ↔ epics/manifest_master.md

- finding ids: 137,130
- **Is ManifestWriter.add() dead/soft-deprecated code awaiting deletion, or a live production write path being act** —
  `epics/manifest_master.md:194-198`: “"Design and land a successor plan for full `ManifestWriter.add` deletion: that
  method was soft-deprecated in the wave-2 plan (Phase 3 swapped all call” vs
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:2194-2197`: “"M-COORD-5 (DeFi slice, slot-2) —
  DONE mtds@f80c50f1: rebuild_defi_manifest.py writer.add(...) now passes asset_group=defi + the source-aware pipeline”
  - why: The epic's still-open P2 deferred todo (created 2026-05-21, unaddressed as of the epic's last_updated
    2026-05-21) frames `ManifestWriter.add` as effectively dead — all call sites already swapped to
    record_captured/record_empty in wave-2 — such that the only remaining work is to grep-confirm zero callers and
    delete the
- **Epic registry does not list its own active P0 child plan** — `epics/manifest_master.md:115`: “_7 active plans
  declare `parent_epic: manifest_master` in their frontmatter (verified 2026-06-30). Workers pick up in priority order
  (P0 first)._” vs `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:9,26`: “status: active ...
  parent_epic: manifest_master ... priority: P0”
  - why: The epic asserts 7 active plans currently declare parent_epic: manifest_master, and its P0/P1/P2 body sections
    should surface them, but every single entry listed under P0-P2 is marked '✅ ARCHIVED' (2026-05-21/23) and the P3
    section explicitly says 'no plans currently assigned at this priority' (line 173). This master c
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/mdps_polars_engine_cost_sharpening_2026_06_28.md (intra-doc)

- finding ids: 182
- **frontmatter status vs 100%-complete body (class d)** — `active/mdps_polars_engine_cost_sharpening_2026_06_28.md:5`:
  “status: active” vs `active/mdps_polars_engine_cost_sharpening_2026_06_28.md:104`: “[x] ✅ [AGENT] P2. MDPS QG green;
  quickmerge `--agent --files`; update M-2 `mtds_file_size_refactor` to mark the Polars seam done ... Gate: QG green; C”
  - why: All 6 todos in this plan are checked [x] with cited shipped commits/evidence (including the final cross-plan
    annotation), yet frontmatter still reads status: active. Its sibling mini-plans from the same 2026-06-28 tracker
    batch (mdps_book_microstructure_precompute_columns, mdps_features_full_month_benchmark_binance, tr
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/migration_verification_orphan_safety_2026_06_10.md (intra-doc)

- finding ids: 136
- **Stale unchecked TradFi G4 todo vs the doc's own top-of-file closure banner** —
  `active/migration_verification_orphan_safety_2026_06_10.md:719`: “[ ] [DATA] P1. **G4 — TradFi apply REMAINS + RESUME
  runbook** ... **TradFi OOM-blocked** — restart with lower concurrency / larger VM). ... Still open” vs
  `active/migration_verification_orphan_safety_2026_06_10.md:64`: “**🟢 V6 CLOSED (2026-07-06).** TradFi G4 `--apply`
  DONE for 2020-2025 + 2026 (7 VMs total, e2-standard-16 · SPOT · workers 24 · per-year; ... \*\*All 5 A”
  - why: A `- [ ]` (unchecked/open) P1 todo still frames TradFi G4 --apply as OOM-blocked and 'still open', but the same
    document's own top banner (most recent, 2026-07-06) declares TradFi G4 --apply DONE and all 5 asset groups now
    canonical. The unflipped checkbox violates the commit-push-flip discipline and could cause an age
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/predictions_ml_walk_forward_and_arb_2026_06_20.md (intra-doc)

- finding ids: 241
- **Acceptance-metrics todo ticked done while its own text says it is blocked on the (still unticked) walk-forward** —
  `active/predictions_ml_walk_forward_and_arb_2026_06_20.md:53`: “[ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward
  against the Group-D-validated feature matrix. (BLOCKED-ON `sports_master:Group E` gate” vs
  `active/predictions_ml_walk_forward_and_arb_2026_06_20.md:55`: “[x] ✅ [ANALYSIS] P0. Acceptance metrics — log-loss,
  calibration, AUC for win/draw/loss; threshold per the consolidated plan bar. (BLOCKED-ON the walk-”
  - why: The walk-forward run itself is unticked and explicitly gated on sports*master:Group E, yet the very next todo
    (acceptance metrics, which by its own parenthetical is 'BLOCKED-ON the walk-forward run above') is ticked ✅ done —
    only the acceptance-metrics \_code* was shipped/unit-tested, not run against real walk-forward o
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md ↔ epics/sports_master.md

- finding ids: 254
- **sports-scheduler cron relaunch gate** — `epics/sports_master.md:452`: “Do NOT relaunch the sports-scheduler before
  those gates.” vs `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:91-92`: “both
  crons resumed 2026-06-25: `uts-prod-sports-scheduler-cron` ENABLED (\*/5) +
  `uts-prod-sports-fixtures-noon-t1-schedule` ENABLED (noon daily).”
  - why: Epic's 2026-06-01 banner explicitly forbids relaunching sports-scheduler until the sports L3 canonicalisation
    plan hits C-GREEN and legacy buckets are decommissioned, with no epic update acknowledging those specific gates were
    met. The sibling plan instead reports the cron already resumed 2026-06-25 on a different name
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/sports_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 146
- **Epic consolidation claim vs an un-folded, still-active third child plan** — `epics/mtds_mdps_master.md:133-144`: “🔵
  CONSOLIDATION 2026-06-26 — live MTDS/MDPS work now runs through 2 themed survivors ... the done/largely-done MTDS/MDPS
  plans were archived and their” vs `active/sports_manifest_canonicalisation_2026_06_01.md:5-23`: “status: active ...
  parent_epic: mtds_mdps_master ... last_updated: 2026-06-27 ... locked_by: live-defi-rollout (with Progress Log entries
  continuing t”
  - why: The epic's 2026-06-26 banner asserts live MTDS/MDPS work was reduced to exactly 2 survivors (M-1, M-2) after
    archiving done/largely-done plans. sports_manifest_canonicalisation_2026_06_01.md declares parent_epic:
    mtds_mdps_master, remains status: active, and is neither M-1 nor M-2, nor archived, nor mentioned anywhere
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/sports_p1_golden_window_features_2026_06_27.md ↔ active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md

- finding ids: 259,261
- **P1e gate readiness / P1d features-manifest state** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:168`: “P1e golden-window e2e gate ... BLOCKED on
  P1d (features manifest empty; re-audit when P1d done)” vs
  `active/sports_p1_golden_window_features_2026_06_27.md:478-485`: “derived_features 91/91, fixture_features 91/91,
  odds_features 91/91 ... 0 blank-reason + 0 un-evidenced attempted_failed”
  - why: Coordinator's burn-down table asserts the features manifest is empty and blocks P1e on that basis, but P1d's
    own 2026-07-03 progress log shows the manifest fully populated (91/91 across all three feature groups) and clean --
    the coordinator's blocker reason is stale and could cause someone to skip re-auditing P1e or mi
- **child-plan assigned_vm value** — `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-211`: “Each
  child carries `assigned_vm: NA` + `assigned_role` ... `execution_scope: orchestrator-agent` -- the central
  orchestrator dispatches them by ROLE, ” vs `active/sports_p1_golden_window_features_2026_06_27.md:15-16`:
  “assigned_vm: planning execution_scope: orchestrator-agent”
  - why: The coordinator plan explicitly asserts every child carries `assigned_vm: NA`, but the actual child plan (in
    this same DAG) carries `assigned_vm: planning` -- the coordinator's description of its own children's dispatch
    metadata is factually wrong, which could mislead anyone reading only the coordinator about how/wheth
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/tradfi_multisource_backfill_2026_06_22.md ↔ epics/tradfi_master.md

- finding ids: 303,306
- **VIX cash-index / Barchart-Yahoo 15m layering status** — `epics/tradfi_master.md:765`: “**VIX 15m source layering**
  (CLAUDE.md): Barchart preload + Yahoo rolling + honest gap. MTDS routing in `umi_tick_provider.py` MUST short-circuit
  Barc” vs `active/tradfi_multisource_backfill_2026_06_22.md:93`: “DELETE the VIX **cash index** entirely (not leave as
  empty_confirmed clutter): not tradable, derivable from the futures, trades less often over a shor”
  - why: The epic's Anti-patterns section (last_updated 2026-06-20, and also its Scope section citing 'Barchart survives
    ONLY as the VIX-15m cash-index layering') still asserts the Barchart+Yahoo VIX-15m cash-index pipeline is the active
    workspace rule an agent MUST follow. But tradfi_multisource_backfill records an executed op
- **Epic child-plan roster completeness (index drift)** — `epics/tradfi_master.md:774`: “6 active plans declare
  `parent_epic: tradfi_master` in their frontmatter (verified 2026-06-30... the live set has grown)” vs
  `active/tradfi_multisource_backfill_2026_06_22.md:14`: “parent_epic: tradfi_master”
  - why: The epic's auto-populated 'Assigned active plans' section claims a verified (2026-06-30) census of children but
    its P0/P1/P2 tables only enumerate tradfi_sp500_ml_and_arb (P0) + tradfi_massive_dual_source (P1) plus archived
    plans — it never lists tradfi_multisource_backfill_2026_06_22 (active, created 2026-06-22, preda
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/tradfi_v9_stage1_finish_2026_07_06.md (intra-doc)

- finding ids: 103
- **Task 3 (straggler re-run) checkbox state vs Progress Log claim of completion** —
  `active/tradfi_v9_stage1_finish_2026_07_06.md:216`: “- [ ] [DATA] P0. **BLOCKED-STRAGGLER-VM-RUNNING · Idempotent
  straggler re-run** (checkbox unchecked)” vs `active/tradfi_v9_stage1_finish_2026_07_06.md:459-461`: “**Task 3
  (straggler re-run) VERIFIED DONE + FLIPPED** — the already-launched VM ... had actually completed cleanly”
  - why: The Progress Log entry explicitly says the task was 'VERIFIED DONE + FLIPPED', but the actual todo checkbox at
    line 216 is still '[ ]' unchecked and its in-checkbox status text is still the stale 2026-07-06 'PARKED, verify +
    flip after VM terminates' note — the flip narrated in prose never happened in the checklist its
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] active/uac_coverage_90pct_2026_06_10.md (intra-doc)

- finding ids: 32
- **UAC final combined test-coverage number vs the locked fail_under=90 gate** —
  `active/uac_coverage_90pct_2026_06_10.md:37-38`: “"Fresh measurement (2026-06-10): **89.82% combined** (statement
  92.53%, branch 56.63%) after Phase 2 + Phase 3 tests + Phase 4 omit expansion. Gate ra” vs
  `active/uac_coverage_90pct_2026_06_10.md:129-130`: “"Final combined branch coverage: **56.63%** ...; statement:
  **92.53%** ...; combined: **≥90%** — `unified-api-contracts`"”
  - why: Same document reports two different final 'combined coverage' figures built from the identical statement
    (92.53%) and branch (56.63%) components: the Context section says the post-all-phases measurement is 89.82% combined
    (which is below the newly-locked fail_under=90 threshold), while the Phase 3 checkbox and the clos
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] archive/2026_05/workspace_qg_sweep_2026_05_23.md ↔ epics/mtds_mdps_master.md

- finding ids: 139
- **Epic child-plan status/ownership vs the child plan's own frontmatter** — `epics/mtds_mdps_master.md:718-720`: “###
  [`workspace_qg_sweep_2026_05_23`]... **status**: 🟠 ACTIVE — QG sweep for market-tick-data-service +
  market-data-processing-service.” vs `archive/2026_05/workspace_qg_sweep_2026_05_23.md:5,14`: “status: complete ...
  parent_epic: infrastructure_master”
  - why: The epic's 'Assigned active plans → P0' section lists workspace_qg_sweep_2026_05_23 as ACTIVE work still owed
    under mtds_mdps_master, but the linked file's own frontmatter says status=complete AND declares a totally different
    parent_epic (infrastructure_master), not mtds_mdps_master at all. An orchestrator reading the
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] archive/2026_06/sports_phantom_recon_and_coverage_windows_2026_06_20.md ↔ epics/sports_master.md

- finding ids: 251
- **Epic lists a P0 foundation-gate plan as active with a link into active/, but the plan is archived+complete** —
  `epics/sports_master.md:1333,1335-1338`: “###
  [`sports_phantom_recon_and_coverage_windows_2026_06_20`](../active/sports_phantom_recon_and_coverage_windows_2026_06_20.md)\n\n**status**:
  active ” vs `archive/2026_06/sports_phantom_recon_and_coverage_windows_2026_06_20.md:6`: “status: complete”
  - why: The epic's 'P0 — must complete before next foundation gate' section (claims the auto-populate script 'keeps it
    in sync from frontmatter', L1300-1302) still shows sports_phantom_recon_and_coverage_windows_2026_06_20 as
    status:active linking to plans/active/..., but that file has moved to plans/archive/2026_06/ with fron
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/README.md ↔ epics/orchestrator_master.md

- finding ids: 339
- **Canonical total epic count in the shared VM/epic registry (20 vs 19)** — `epics/README.md:164`: “## 20 epics in 5
  tiers” vs `epics/orchestrator_master.md:116-117`: “Registry SSOT: [`../../orchestrator_vm_registry.yaml`] ... — 10 VMs
  × 19 epics × 4 accounts.”
  - why: README enumerates its epic table with exactly 20 numbered rows (L166-187) and reaffirms 'all 20 epics' (L190)
    and 'VM topology (10 VMs serving 20 epics)' (L192), declaring itself SSOT for VM mapping. orchestrator_master cites
    the same underlying orchestrator_vm_registry.yaml as describing '10 VMs × 19 epics × 4 account
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)
