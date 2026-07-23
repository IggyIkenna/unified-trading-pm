---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — 320 verified findings (28 P0): operator decision queue + auto-fix
  reconciliation log (245-agent adversarially-verified sweep of plans/active + issues + epics)"
summary:
  "Full-corpus contradiction audit (307 docs read in full; epic-cluster + 16 topic sweeps + mechanical adjudication;
  every candidate adversarially verified by independent refuter+confirmer with tiebreak — 320 confirmed of 401
  candidates, 81 refuted). Findings split: 212 stale-drift / 102 true contradictions / 6 format-only; 28 P0. Section A =
  operator decision queue (each with options + recommendation; codex SSOT edits ALWAYS parked here). Section B =
  auto-fix queue applied autonomously with hard evidence (progress log at bottom records each batch + commit). Section C
  = structural gaps from the coverage critic. Dominant failure mode: epics not updated when child plans complete (stale
  epic P0 sections could re-dispatch shipped safety-critical work)."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift]
related: [/plans/active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md]
created: 2026-07-11
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
source:
  "plan-reconcile contradiction audit, interactive session 2026-07-10/11 (operator-dispatched /autonomous); method:
  cursor-configs/skills/plan-reconcile/SKILL.md; findings archive in session scratchpad findings.json"
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Plans-corpus contradiction audit — operator decision queue + reconciliation log

**Provenance**: 245-agent workflow (epic-cluster hunters reading all 307 docs in full + cross-batch reconcilers + 16
topic sweeps + mechanical adjudication of 104 frontmatter flags + coverage-critic gap round). Every candidate was
adversarially verified: independent refuter + confirmer re-read both docs at the cited lines; splits went to a
tiebreaker. 320 confirmed / 81 refuted. Method SSOT: `cursor-configs/skills/plan-reconcile/SKILL.md`.

**How to use (operator)**: Section A needs your ruling — answer in the chat Q&A (batched, P0 first) or annotate inline.
Section B is being applied autonomously (hard-evidence-gated); each batch lands as a `docs(plans):` commit recorded in
the Progress Log. Nothing in codex/ is edited without your explicit per-item ruling.

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

#### [P1] epics/client_isolation_and_governance_master.md (intra-doc)

- finding ids: 33
- **Epic's own P1-priority section appears twice with contradictory content** —
  `epics/client_isolation_and_governance_master.md:129-136`: “"## P1 — important; post-current-gate (was P0)" ... "F-25
  — build the FULL unified `ClientConfig` type in `unified_api_contracts.internal`"” vs
  `epics/client_isolation_and_governance_master.md:143-145`: “"## P1 — important; post-current-gate" / "_(no plans
  currently assigned at this priority)_"”
  - why: The epic has two separate '## P1 — important; post-current-gate' headers a few lines apart: the first lists a
    live, unchecked P1 task (F-25 ClientConfig dispatch) plus an archived-plan reference, the second flatly states no
    plans are assigned at P1. An agent scanning the epic for outstanding P1 work could stop at the s
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/execution_master.md (intra-doc)

- finding ids: 367,53,316
- **May-23 critical path gating — recon-freeze kill-switch chain** — `epics/execution_master.md:54`: “## P2 —
  opportunistic / post-cutover (slot 7 dispatch 2026-06-01)” vs `epics/execution_master.md:59-61`: “- [ ] [CODE] P1.
  **G12 (execution-side) — emit per-incident recon-freeze signals** ... In-scope for May-23. Repo: execution-service.”
  - why: The same still-open todo is filed under a section header that classifies it as P2/opportunistic/post-cutover,
    while its own text tags it P1 and explicitly 'In-scope for May-23' (i.e. NOT post-cutover). This is a live-trading
    safety item: per the linked 2026-05-27 audit (active/issues/batch_live_reconciliation_service_a
- **Epic frontmatter related-list vs epic body disclaimer (intra-doc)** — `16`:
  “../active/execution_fidelity_tiers_uac_governed_2026_06_28.md,” vs `66`: “no other active plans currently declare
  `parent_epic: execution_master`”
  - why: The epic's own frontmatter `related` field (L14-18) and `related_plans` field (L27-31) both explicitly name
    execution_fidelity_tiers_uac_governed_2026_06_28.md as a related child plan, directly contradicting the epic body's
    italicized claim two sections later that no other active plans declare parent_epic: execution_ma
- **frontmatter last_updated vs body edit date (intra-doc)** — `epics/execution_master.md:32`: “last_updated:
  2026-05-21” vs `epics/execution_master.md:54`: “## P2 — opportunistic / post-cutover (slot 7 dispatch 2026-06-01)”
  - why: The F-32 operator-decision text and the 'slot 7 dispatch' heading are dated 2026-06-01, roughly two weeks after
    the frontmatter's last_updated of 2026-05-21 — the metadata field was not bumped when this content was added.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/mtds_mdps_master.md (intra-doc)

- finding ids: 175,328,142,329
- **epic consolidation claim vs actual live child-plan count** — `epics/mtds_mdps_master.md:133-138`: “"🔵 CONSOLIDATION
  2026-06-26 — live MTDS/MDPS work now runs through 2 themed survivors" (M-1 data_completion_to_100_all_ag, M-2
  mtds_file_size_refactor” vs `epics/mtds_mdps_master.md:713-714`: “"\_33 active plans declare parent_epic:
  mtds_mdps_master in their frontmatter (verified 2026-06-30). Workers pick up in priority order (P0 first)."”
  - why: The banner asserts all live MTDS/MDPS work now runs through only 2 named survivor plans, but the epic's own
    body says 33 active child plans (parent_epic: mtds_mdps_master) exist and are worked in priority order. All 5 of
    this batch's assigned docs (bucket_name_ssot, data_source_provenance, cefi_universe_capture_rule, m
- **workspace_qg_sweep_2026_05_23 status vs archive location** — `epics/mtds_mdps_master.md:718`: “"###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — MTDS/MDPS cluster"” vs
  `epics/mtds_mdps_master.md:720-721`: “"**status**: 🟠 ACTIVE — QG sweep for market-tick-data-service +
  market-data-processing-service. Both ruff clean; run full `bash scripts/quality-gates.”
  - why: The link path places this plan under plans/archive/2026_05/ (i.e. already archived), yet the epic's own status
    line calls it '🟠 ACTIVE' and gives a live, actionable directive ('run full quality-gates.sh') with a prereq gate —
    a worker following the epic's P0 list could dispatch effort against an archived plan believing
- **Epic auto-populated child-plan index omits the epic's own designated primary survivor plan** —
  `epics/mtds_mdps_master.md:139-141`: “**M-1 · [`data_completion_to_100_all_ag_2026_06_21`]**... — backfill-to-100% +
  DeFi catalogue→per-pool capture + honest-absence swallow remediation” vs `epics/mtds_mdps_master.md:713-714`: “\_33
  active plans declare `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30). Workers pick up in
  priority order (P0 first). Aut”
  - why: The epic's 2026-06-26 consolidation banner names data_completion_to_100_all_ag_2026_06_21 (parent_epic:
    mtds_mdps_master, status: active, our assigned doc) as the M-1 survivor carrying all live MTDS/MDPS work. The epic's
    own 'Assigned active plans' section, auto-populated 2026-06-30 (later than the banner) and claiming
- **live_pipeline_mtds_mdps_features_2026_05_08 status vs archive location** — `epics/mtds_mdps_master.md:729`: “"###
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)"”
  vs `epics/mtds_mdps_master.md:731`: “"**status**: active"”
  - why: Same archived-path-but-active-status pattern as the workspace_qg_sweep entry: the plan file lives under
    plans/archive/2026_05/ yet the epic table asserts a bare 'active' status with no archival note, unlike other rows in
    the same P0/P1 lists that correctly say '✅ ARCHIVED'.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/sports_master.md (intra-doc)

- finding ids: 331,332,279
- **Sports bookmaker venue scope — retired venues still named in the live P0 data-correctness mandate** —
  `epics/sports_master.md:90`: “ALL 11 bookmaker × data_type combos (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE
  × odds_snapshot + odds_movement)... Scope MUST cover every bo” vs `epics/sports_master.md:236-238`: “DRAFTKINGS and
  FANDUEL (US sportsbook browser-stub adapters) are DEFERRED-INDEFINITELY from the active sports universe...
  sports_master scope is now a”
  - why: The un-bannered 🔴 P0 ABSORBED mega-audit directive (dated 2026-05-20, still reads as live/authoritative — no
    SUPERSEDED marker like the other consolidated-todo blocks in this same doc got) names BET365/DRAFTKINGS/FANDUEL and
    invokes the workspace HARD RULE 'no asset_group skipped, no deadline-driven cutbacks.' But 8 da
- **Frontmatter summary bookmaker-count vs body's narrowed active venue scope** — `epics/sports_master.md:5`: “L0
  asset-group umbrella epic for the sports data pipeline (API-Football fixtures + 11 bookmaker odds combos)” vs
  `epics/sports_master.md:237`: “sports_master scope is now anchored on the 3 remaining-active sports venues: ODDS_API,
  PINNACLE, BETFAIR”
  - why: The frontmatter `summary:` (which should reflect current scope, last_updated 2026-06-24) still advertises '11
    bookmaker odds combos' as the pipeline's scope, but the body — dated more recently and never revised in the summary
    — narrows the active universe to just 3 venues, with 14 scraper bookmakers plus DRAFTKINGS/FAN
- **Epic frontmatter last_updated vs body content dates** — `epics/sports_master.md:62`: “last_updated: 2026-06-24” vs
  `epics/sports_master.md:273-288`: “## Scrapers retired 2026-07-08 per operator ... Shipped 2026-07-08: -
  `execution-service@29a888a8d` — deleted the entire `execution_service/sports_exe”
  - why: The epic's frontmatter last_updated (2026-06-24) predates substantial body content dated 2026-06-27
    (golden-window banner) and 2026-07-08 (scraper-retirement section with real commit SHAs), meaning the frontmatter
    timestamp is stale relative to the epic's own visible edits.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/PLAN_FORMAT.md (intra-doc)

- finding ids: 381
- **todo placement — frontmatter YAML vs. body markdown checkboxes** — `plans/PLAN_FORMAT.md:625-637`: “## Structural
  Order (MANDATORY) ... 1. **Frontmatter** (name, overview, type, status, completion_gates, depends_on, todos with
  checkboxes) ... \*\*Rule:” vs `plans/PLAN_FORMAT.md:78-118,229-241`: “### Active plan / wrapper plan (in
  `plans/active/`) [frontmatter schema has NO `todos:` field] ... Cursor Plan Mode renders Markdown checkboxes. Every”
  - why: The same SSOT doc has a section labelled 'MANDATORY' instructing that todos live inside the frontmatter YAML
    block (matching the pre-2026-05-21 legacy `todos:` list schema shown later at lines 183-225), while the current
    'Active plan / wrapper plan' frontmatter schema has no `todos:` field at all and the 'Cursor-Friend
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/bucket_env_split_rollout_2026_06.md ↔ plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md

- finding ids: 353
- **Whether strategy-store/execution-store/features-delta-one flat (non-env-tiered) bucket names are correct end-s** —
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:405-406`: “`strategy-store` /
  `execution-store` / `features-delta-one` flat names — yaml deliberately keeps these flat (env-split rolled back); NOT
  drift.” vs `plans/active/bucket_env_split_rollout_2026_06.md:40,51-54`: “Operator directive 2026-06-09: env-splits
  everywhere (Group A and Group B, all kinds). The temporary Group B rollback to non-env-split names is to be ”
  - why: bucket_name_ssot_legacy_dual_write_remediation (status: active, last_updated 2026-06-27 — AFTER the 2026-06-09
    operator directive) still lists these exact bucket kinds under 'Out of scope ... NOT drift', i.e. flat names are
    deliberate and correct. But bucket_env_split_rollout_2026_06.md (also active, created 2026-06-09
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md ↔ plans/epics/batch_live_symmetry_master.md

- finding ids: 388
- **mechanical:terminal_status_in_active_dir** — `plans/epics/batch_live_symmetry_master.md:75-82`: “### 🔴 2026-07-08
  canonical instrument_id — live≠batch findings **status**: 🔴 NEW ... -
  [`canonical_id_p0_ccxt_live_batch_divergence_2026_07_08`] ... ” vs
  `plans/active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: The epic batch_live_symmetry_master.md still lists canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 under
    its P0 'must complete before next foundation gate' section with status marker 'NEW', while the plan's own
    frontmatter (status: complete) and body (all todos [x], evidence of shipped commit instruments-service@
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/canonical_id_p0_strategy_reconciliation_2026_07_08.md ↔ plans/epics/batch_live_symmetry_master.md

- finding ids: 389
- **mechanical:terminal_status_in_active_dir** — `plans/epics/batch_live_symmetry_master.md:75-85`: “**status**: 🔴 NEW
  ... - [`canonical_id_p0_strategy_reconciliation_2026_07_08`] ... depends on the plan above; live position
  reconciliation is silently” vs `plans/active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:14`: “status:
  complete”
  - why: Same epic section also lists canonical_id_p0_strategy_reconciliation_2026_07_08 as part of the 🔴 NEW /
    must-complete-before-next-foundation-gate P0 block, but the plan's own frontmatter (status: complete) and body (all
    todos [x], including the P0 end-to-end reconciliation-test todo) show it already shipped. The epic wa
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md ↔ plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md

- finding ids: 301
- **Collateral-aware down-sizing for stables-only perp venues (Aster pattern) in staked_basis.py** —
  `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md:97-105`: “Collateral-aware down-sizing is
  NOT implemented ... staked_basis.py:219-229 \_derive_structure: if the LST is not in
  accepted_perp_collateral(perp_venu” vs
  `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:53-58`: “Build the
  USDC-collateral + margin-buffer down-size branch in the staked-basis (and basis-perp) engine: when
  venue_accepts_collateral(perp_venue, lst)”
  - why: Both docs are dated 2026-06-17 and defi_collateral_sizing is explicitly the operator-directed fix for the exact
    gap e2e_defi_config_taxonomy describes (commit strategy-service@6e9164b1, unit tests naming Aster/Hyperliquid by
    name). defi_collateral_sizing marks Phase A DONE/shipped, yet e2e_defi_config_taxonomy's matchi
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/infra_capture_and_devops_leftovers_2026_07_06.md ↔ plans/active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md

- finding ids: 357
- **SPOT vs on-demand policy for forward/daily-poll VMs** —
  `active/infra_capture_and_devops_leftovers_2026_07_06.md:64`: “`/codex/05-infrastructure/spot-vms-for-backfill.md` —
  SPOT default for backfill; live/forward stay on-demand.” vs
  `active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:53-56`: “**SPOT VMs (HARD)** — the
  sports-scheduler daemon VM launches **spot/preemptible** (the cloud can reclaim + kill it at any moment) per
  [sports_p0_spot”
  - why: infra_capture_and_devops_leftovers_2026_07_06.md (active, last_updated 2026-07-07) states as a HARD worker
    guard, citing the same spot-vms-for-backfill.md codex SSOT, that 'live/forward VMs stay on-demand ... SPOT is for
    backfill only.' The sports plan explicitly puts its 'daily-forward' scheduler daemon (launch-sports
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/codex_vs_repo_docs_ssot_audit_2026_06_01.md ↔ active/instruments_mtds_subset_consistency_remediation_2026_06_17.md

- finding ids: 369
- **Is URDI a phantom name to purge from instruments-service code, or the live production fetch-spine module name?** —
  `active/codex_vs_repo_docs_ssot_audit_2026_06_01.md:194-195`: “Follow-up: URDI still in instruments-service CODE ...
  `URDI` is a phantom name per CLAUDE.md. Audit + rename in instruments-service.” vs
  `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:1855-1856`: “"rg URDI → 0 hits" is wrong;
  `urdi_reference_provider.py` is the LIVE fetch spine. Replace with "no NEW URDI refs" + fix the stale error message”
  - why: Both plans are status: active/open with a live unchecked todo. Doc A (2026-06-01) directs an agent to 'audit +
    rename' all URDI symbols in instruments-service code because URDI is purely a phantom name (matching CLAUDE.md's own
    'URDI phantom' framing). Doc B (2026-06-17, 16 days later) explicitly corrects this framing
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/deployment_observability_parity_live_batch_paper_2026_06_22.md (intra-doc)

- finding ids: 198
- **Cloud Run job registry size (same commit, two different counts)** —
  `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:89`:
  “`deployment_service/cloud_run_job_registry.py` `CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]` — 49 jobs from
  all 24 `*_scheduler.tf`” vs `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:266`:
  “deployment-service@360678e (DeploymentUmbrella + classify_deployment_target + 61-job CLOUD_RUN_JOBS registry +
  unclassified guard)”
  - why: The same document attributes the SAME commit (deployment-service@360678e) to a '49 jobs from all 24
    \*\_scheduler.tf' registry in the Phase-0 todo and its first Progress-Log entry, but the later 'FINAL REPORT' /
    second Progress-Log section (also citing @360678e) calls it a '61-job CLOUD_RUN_JOBS registry.' Both cannot be
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/instruments_service_docs_consolidation_2026_07_08.md ↔ epics/instruments_master.md

- finding ids: 118
- **The real starting doc-count for the instruments-service docs consolidation (17 vs 18)** —
  `epics/instruments_master.md:457`: “"DONE, `instruments-service@10ad69a4` — 18→7 docs (real count was 18, not 17)."”
  vs `active/instruments_service_docs_consolidation_2026_07_08.md:4`: “"Consolidate instruments-service's 17 docs into 7
  — one setup guide, one adapter-architecture guide, one doc per asset group"”
  - why: The epic asserts the corrected/real count was 18 docs (explicitly framing '17' as wrong), but the consolidation
    plan itself — the same doc the epic is citing as DONE — consistently uses 17 throughout its own title, summary ('17
    markdown files, 6,529 lines'), and Phase-1 todos ('Read all 17 existing docs'), and its own
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md ↔ active/issues/capability_wizard_analysis_findings_2026_06_11.md

- finding ids: 299
- **CARRY_STAKED_BASIS CeFi hedge-venue set: leg-spec (F22, shipped 2026-06-11) includes binance; the new flat-reg** —
  `active/issues/capability_wizard_analysis_findings_2026_06_11.md:285`: “CeFi (binance/bybit/deribit/okx) + DeFi
  (hyperliquid/gmx_v2/drift) hedge venues are now differentiated per-leg.” vs
  `active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md:78-80`: “`CARRY_STAKED_BASIS` —
  new `CEFI` / `perp` cell, `venue_ids: [deribit, bybit, okx]` (matches the codex venue matrix...)”
  - why: F22's already-shipped ARCHETYPE_LEG_STRUCTURES leg-spec lists binance as one of the four CeFi hedge venues for
    CARRY_STAKED_BASIS, but the 2026-07-10 fix that added the flat ARCHETYPE_CAPABILITY_REGISTRY CEFI cell for the same
    archetype only lists [deribit, bybit, okx] — a fresh instance of the known dual-representatio
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/batch_live_reconciliation_service_audit_2026_05_27.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 25
- **Finality of BLRS D2/D3/D4 design decisions** — `epics/batch_live_symmetry_master.md:91-98`: “D2 — BLRS calls
  strategy-service position query API for the canonical position baseline (not a BLRS-local recomputation)... D3 — build
  all 3 recon gre” vs `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:391-422`: “### 7.2 ❓ Needs
  operator input (material...) — D2 — Canonical position baseline: query strategy-service/position vs ratify event
  archives. → ROUTED TO”
  - why: The epic (the designated SSOT board per the doc's own 2026-06-01 banner, last_updated 2026-07-08) records
    D2/D3/D4 as single, decided, imperative action items still awaiting implementation. But the BLRS audit doc's own
    '§7.2 Needs operator input' decisions-ledger section — the doc's stated authoritative decision tracke
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md (intra-doc)

- finding ids: 346
- **empty-output shard classification: 3-category vs 4-category decision tree (which codex doc is authoritative)** —
  `active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md:44`:
  “/codex/04-architecture/shard-level-failure-isolation.md — claims
  `authoritative_for: [... three-category empty-output decision tree]`; body documents 3” vs
  `active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md:46`:
  “/codex/06-coding-standards/validation-and-errors.md — the newer merged write-side SSOT; documents a **four-category**
  decision (adds path D: zero-activ”
  - why: This filed issue (status: open, unresolved, priority P2) documents that two live codex SSOTs disagree on the
    category count for the same per-shard empty-output classification decision (3 vs 4, the zero-activity-bar path D),
    with neither doc's authoritative_for scoped to disambiguate — matching the workspace's own contr
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md (intra-doc)

- finding ids: 242
- **Issue frontmatter claims resolved while its own resolution section's last step is still pending** —
  `active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md:5`: “status: resolved” vs
  `active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md:93`: “3. T+10 verification pending (VMs booting).”
  - why: The doc's frontmatter and resolved_by field assert the issue is fully resolved, but the Resolution section's
    final numbered step admits the T+10 post-relaunch verification was still pending (VMs booting) at time of writing —
    the resolved-status claim outruns the doc's own evidence.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/mvp_backfill_cefi_tick_v10_2026_06_27.md (intra-doc)

- finding ids: 30
- **Whether residual Deribit per-strike trades/book5 rows (cap=536) block the G4 honest-complete gate** —
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:269`: “The v10 capture universe excludes them ... Scope-exclusion
  cleanup can be tracked separately; they do NOT block G1–G4.” vs
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:1066`: “DERIBIT/OPTION/trades cap=536 ... plan G0 marks as pre-v10
  artifact ('DO NOT BLOCK G4'), but G4 gate text says '0 per-strike trades/book5 cells'. Ambi”
  - why: Intra-doc conflict: the plan's own G0 gap analysis explicitly states Deribit per-strike trades/book5 residuals
    do NOT block G4, but the G4 gate's own todo text literally requires '0 per-strike trades/book5 cells' present. The
    doc's own 2026-07-06 Progress Log entry flags this as an unresolved ambiguity needing an opera
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/scripts_lifecycle_marker_rollout_2026_06_18.md (intra-doc)

- finding ids: 74
- **This plan's own `assigned_vm` value (frontmatter NA vs body harsh_pc)** —
  `active/scripts_lifecycle_marker_rollout_2026_06_18.md:15`: “assigned_vm: NA” vs
  `active/scripts_lifecycle_marker_rollout_2026_06_18.md:39`: “`assigned_vm: harsh_pc` so the local orchestrator backend
  (running as `harsh_pc`, STANDALONE) ingests it via the reconciler”
  - why: The plan's frontmatter (the field an orchestrator/reconciler actually reads for dispatch) says
    `assigned_vm: NA`, but the plan's own body explicitly asserts `assigned_vm: harsh_pc` as its dispatch target and
    dual-purpose rationale (AO fleet-test). Per CLAUDE.md, valid `assigned_vm` values are strictly `{planning, NA}`
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md (intra-doc)

- finding ids: 264,265
- **corrupted duplicate frontmatter block** — `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:11`:
  “asset_group: [sports]” vs `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:64`: “asset_group:
  cross-asset”
  - why: The file contains a second, garbled YAML-looking block mid-body (after the real closed frontmatter) declaring
    asset_group: cross-asset, repos: [], tags: [] -- directly conflicting with the real frontmatter's asset_group:
    [sports] and populated repos/tags lists in the same file. This looks like a merge/edit artifact tha
- **coordinator doc's own assigned_vm/execution_scope pairing** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:26`: “assigned_vm: planning” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:27,75-76`: “execution_scope: local-only ... This
  file is `execution_scope: local-only` -- the orchestrator does NOT ingest it.”
  - why: Per CLAUDE.md's documented two-track plan model, assigned_vm: planning means AO-dispatched while
    execution_scope: local-only + assigned_vm: NA is the human/never-ingested track -- this doc mixes the AO-dispatched
    assigned_vm value with the local-only/never-ingested execution_scope, an internally inconsistent frontmatte
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/utl_uac_reuse_consolidation_remediation_2026_06_10.md (intra-doc)

- finding ids: 64
- **Frontmatter repos: list includes a repo the body explicitly marks do-not-touch** — `9`: “repos: [agent-orchestrator,
  alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service]” vs
  `47-49`: “Clean repos (audit found nothing actionable — do not touch): ... batch-live-reconciliation-service,
  greeks-service”
  - why: batch-live-reconciliation-service is listed in the plan's frontmatter `repos:` scope (implying it is
    in-scope/touched by this plan) while the body's 'Clean repos' section explicitly says the audit found nothing
    actionable there and instructs 'do not touch' — with no corresponding Phase item anywhere in the doc mentioni
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/client_isolation_and_governance_master.md ↔ epics/execution_master.md

- finding ids: 340
- **Tier classification of strategy_master / execution_master / trading_agent_master (labeled 'L0 asset-group' vs ** —
  `epics/client_isolation_and_governance_master.md:95-97`: “Enforces on: ALL L0 asset-group epics (every
  transfer/order/strategy-emit respects client isolation + jurisdiction) - `strategy_master` +
  `execution_m”  vs  `epics/execution_master.md:21`: “tier: L2”
  - why: client_isolation_and_governance_master labels strategy_master, execution_master, and trading_agent_master as
    'L0 asset-group epics', but all three self-declare tier: L2 in their own frontmatter (execution_master:21,
    strategy_master:31 'tier: L2', trading_agent_master:18 'tier: L2'), and README's canonical 20-epic tier
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/deployment_and_user_management_master.md (intra-doc)

- finding ids: 314,385
- **assigned-active-plan count vs actual plan list (intra-doc)** — `epics/deployment_and_user_management_master.md:72`:
  “_1 active plans declare `parent_epic: deployment_and_user_management_master` in their frontmatter. Workers pick up in
  priority order (P0 first)._” vs `epics/deployment_and_user_management_master.md:87`: “**status**: ✅ ARCHIVED
  2026-05-23 — Code half shipped (deployment-api reader repointed to env-tiered bucket names)”
  - why: The auto-populated banner claims 1 active child plan exists, but every plan actually listed across P0/P1/P2/P3
    (both gap_2_4_d_deployment_api_reader_repoint and deployment_ui_lifecycle_tabs) is marked ✅ ARCHIVED — zero active
    plans are shown, so the count is stale/wrong and a worker following 'pick up in priority order
- **Epic's declared repo scope (frontmatter) vs its own ownership/gate claims (body) re: user-management-ui** —
  `epics/deployment_and_user_management_master.md:12`: “repos: [deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/deployment_and_user_management_master.md:32,41`: “**Owns**: deployment-api +
  deployment-ui + user-management-service + user-management-ui ... All active plans under this epic that touch any UI
  repo (`”
  - why: This active epic's frontmatter `repos:` field — the field dispatch/scoping tooling reads — omits
    user-management-ui and user-management-service entirely, while its own body 'Owns' line and its UI Verification
    Contract both name user-management-ui as an actively owned, playwright-gated UI repo. Same doc, same status:act
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/predictions_master.md (intra-doc)

- finding ids: 238
- **Intra-epic contradiction: adapter migration status** — `epics/predictions_master.md:408`: “Polymarket adapter
  migration (data_type rename) | NOT started | same” vs `epics/predictions_master.md:480`: “**SHIPPED mtds@`7643a5c`**
  "feat(predictions): Polymarket adapter per-market lifecycle gating + tests"”
  - why: The epic's own Critical Path table (line 408-409) claims Polymarket/Kalshi adapter migration is NOT started,
    while the epic's own later Consolidated-todos section documents both as SHIPPED (mtds@7643a5c, mtds@e8a6903). This
    table isn't covered by the section's own SUPERSEDED banner (which only covers the Consolidated-t
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] plans/PLAN_FORMAT.md ↔ plans/active/task_template.md

- finding ids: 382
- **valid `status:` enum values** — `plans/PLAN_FORMAT.md:86`: “status: draft | active | blocked | paused | complete |
  cancelled | superseded” vs `plans/active/task_template.md:71`: “status: active # active | draft (NOT ingested) | done
  | blocked”
  - why: PLAN_FORMAT.md's canonical frontmatter schema enumerates 7 status values with 'complete' as the terminal state
    (no 'done'); task_template.md's copy-paste block for new AO-dispatched plans instead lists 'done' as a valid value
    and omits paused/cancelled/superseded/complete entirely. A grep of all 134 active plans' `stat
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

## B. AUTO-FIX QUEUE — 176 doc-pairs (hard-evidence reconciliation, applied autonomously)

#### [P0] active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 19,363,13
- **Status of CCXT instrument_id live=batch divergence bug** — `epics/batch_live_symmetry_master.md:83`: “the CCXT live
  adapter stores bare ccxt-native symbols; batch (Tardis) produces a differently-shaped canonical id for the same real
  instrument, across ” vs `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: Epic still lists this as an unresolved 🔴 NEW P0 finding, but the child plan is status:complete with all 13
    venues verified converged against real Tardis batch-mode ids (instruments-service@8544273d) and a 2026-07-10
    progress-log entry confirming the flip. Same class of risk as the sibling finding above: dispatch off th
- **canonical instrument_id live=batch divergence — is this P0 still open?** —
  `epics/batch_live_symmetry_master.md:75-87`: “### 🔴 2026-07-08 canonical instrument_id — live≠batch findings
  **status**: 🔴 NEW ... these 2 findings are direct live=batch determinism violations.” vs
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10 and :65-80`: “status: complete ... all four todos
  [x] checked, e.g. 'Ship via quickmerge, quality-gates green ... instruments-service@8544273d, quickmerge landed on”
  - why: The epic (last_updated 2026-07-08) still marks this as '🔴 NEW' and lists it under 'P0 — must complete before
    next foundation gate' with unchecked bullets, implying it is an open blocking determinism violation. But both child
    plans it points to (canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md AND canonical_id_p
- **canonical instrument_id live≠batch P0 findings status** — `epics/batch_live_symmetry_master.md:73-80`: “## P0 — must
  complete before next foundation gate ... **status**: 🔴 NEW — from `canonical_instrument_id_audit_2026_07_08` ...
  these 2 findings are dir” vs `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: The epic (`last_updated` 2026-07-08, same day) frames both canonical_id_p0\_\* findings as '🔴 NEW' P0 work
    that 'must complete before next foundation gate', with no acknowledgement they are done. But both child docs are
    frontmatter `status: complete` (canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10 and canonica

- planned fix: Sync batch_live_symmetry_master P0 section: CCXT divergence RESOLVED
  (canonical_id_p0_ccxt_live_batch_divergence complete, instruments-service@8544273d, 13 venues verified).

#### [P0] active/canonical_id_p0_strategy_reconciliation_2026_07_08.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 18,342
- **Status of CCXT live-vs-batch reconciliation defeat bug** — `epics/batch_live_symmetry_master.md:86`: “live position
  reconciliation is silently defeated for every CCXT venue because the canonical-vs-raw string comparison never
  matches.” vs `active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:172`: “All 7 todos fixed + shipped.
  Operator-authorized execution per the blanket "execution on the 4 P0 fix plans" instruction.”
  - why: Epic's P0 section (last_updated 2026-07-08) still frames this as an active, unresolved live-trading safety bug
    ('is silently defeated', present tense, no checkbox/closure), but the linked child plan is status:complete with all
    7 todos shipped (strategy-service@0c407b57, deployment-api@c8eeee2) as of 2026-07-08/07-10. A
- **Status of the strategy-service live-reconciliation P0 fix (canonical_id_p0_strategy_reconciliation)** —
  `epics/batch_live_symmetry_master.md:75-87`: “### 🔴 2026-07-08 canonical instrument_id — live≠batch findings
  **status**: 🔴 NEW ... `canonical_id_p0_strategy_reconciliation_2026_07_08` — depends on” vs
  `active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:9,172-174`: “status: complete ... **All 7 todos fixed +
  shipped.** ... strategy-service@0c407b57e1aa92afb430fc818f91abeb7b186c13, deployment-api@c8eeee2e67910c3cb9”
  - why: The epic (last_updated 2026-07-08, same day) lists this plan with no completion checkmark under a live '🔴 NEW'
    bug description ('silently defeated ... never matches'), reading as still-open/blocking work — unlike its own
    sibling entry pattern used elsewhere in the same epic family (instruments_master.md marks the paire

- planned fix: Sync batch_live_symmetry_master P0 section: reconciliation-defeat finding RESOLVED
  (canonical_id_p0_strategy_reconciliation complete, strategy-service@0c407b57 + deployment-api@c8eeee2).

#### [P0] active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md ↔ active/mvp_backfill_defi_onchain_v10_2026_06_27.md

- finding ids: 43
- **DeFi perp_funding MVP-scope status for the DRIFT-Solana backfill** —
  `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:158`: “✅ RESOLVED 2026-06-29 — OUT OF MVP SCOPE (provisional,
  pending Ikenna confirm). Per UAC SSOT is_mvp(), DRIFT perp_funding is NOT MVP” vs
  `active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md:38`: “the ‘Resolution status’ /
  ‘Recommendation’ sections below (provisional Option 1, ‘out of MVP scope’) are SUPERSEDED... resolves this as Option
  2”
  - why: The v10 backfill plan (status: active, last_updated 2026-06-27) has its G1.5 item checked ✅ done with the
    resolution 'out of MVP scope' and explicitly says 'Reopen if Ikenna rules perp_funding IS in scope'. The sibling
    issue doc (last_updated 2026-07-09, more recent) records that a broader operator ruling has since fli

- planned fix: Apply the LATER operator ruling recorded in defi_perp_funding_mvp_scope_contradiction (Option 2:
  perp_funding IS MVP, UAC v13 unified-api-contracts@89b16943): update v10 plan G1.5 resolution text + un-resolve the
  424 DRIFT cells item, citing the issue doc.

#### [P0] active/issues/github_billing_dashboard_access_2026_07_09.md ↔ archive/2026_07/cost_observability_ui_2026_07_08.md

- finding ids: 48
- **GitHub billing on /ops/costs — pending credential ask vs already-shipped-and-live** —
  `active/issues/github_billing_dashboard_access_2026_07_09.md:12`: “status: open — summary: "The /ops/costs GitHub
  panel is a hardcoded placeholder because GitHub billing ... is owner-only and no credential we hold can” vs
  `archive/2026_07/cost_observability_ui_2026_07_08.md:697`: “GitHub real billing is LIVE (token landed, verified
  end-to-end). Operator (Ikenna) minted the Plan-scoped fine-grained PAT ... stored it as Secret Man”
  - why: This open issue doc's entire ask (mint a fine-grained PAT with Plan:Read, store as Secret Manager
    `github-billing-token`, swap the dummy provider, drop the placeholder note — see its unchecked Resolution checklist
    at lines 148-155) was fully completed and verified live on 2026-07-10 per the (now-archived) parent plan a

- planned fix: Close github_billing_dashboard_access issue doc as resolved (archived cost_observability plan + successor
  UI plan record PAT minted, stored as Secret Manager github-billing-token, verified end-to-end 2026-07-10) - after I
  verify the secret exists + provider code is non-placeholder.

#### [P0] active/issues/instrument_id_format_canonicalization_2026_07_08.md ↔ epics/instruments_master.md

- finding ids: 93,94
- **CeFi live=batch instrument-id convergence status** — `epics/instruments_master.md:466-467`:
  “canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 — DONE, instruments-service@8544273d — all 13 canonical CeFi
  venues verified converged live=batc” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:1065-1069`:
  “MTDS's own live CeFi WS connectors (raw-tick construction layer) were never retrofitted... mismatches are silently
  dropped. Confirmed in production GC”
  - why: Epic asserts live=batch convergence for all 13 CeFi venues is DONE/verified; the issue doc (updated through
    2026-07-10) found MTDS's live WS connectors were never retrofitted to the canonical id scheme and were silently
    dropping ticks (real data loss) until fixed 2026-07-10 — an agent trusting the epic's DONE claim wou
- **CBOE/VX combo-leg canonicalization completion status** — `epics/instruments_master.md:468-469`:
  “canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08 — P1, real InstrumentLeg/COMBO infrastructure exists
  (proven for CME), just not wired up ” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:349-357`:
  “Confirm the revised TradFi combo fix — DONE 2026-07-09 (finding 7...) — reuse the existing
  InstrumentLeg/InstrumentType.COMBO infrastructure (already ”
  - why: Epic still describes CBOE/VX combo-leg wiring as not-yet-done; the child plan's own tracking issue doc records
    it as DONE 2026-07-09 with code shipped and landed. Epic text is stale and could cause an agent to re-dispatch
    already-completed work.

- planned fix: Annotate instruments_master's DONE line: convergence claim was builder-level; MTDS live WS connectors
  were retrofitted separately (fixed 2026-07-10 per instrument_id_format_canonicalization issue doc) - epic line gets
  the caveat + pointer.

#### [P0] active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md ↔ epics/plan_hygiene_master.md

- finding ids: 227
- **Whether the daily plan-hygiene Cloud Run cron actually works and notifies on failure** —
  `epics/plan_hygiene_master.md:93`: “Implemented as Cloud Run Job `uts-prod-plan-hygiene-sweep` + Cloud Scheduler.
  Failures append `## [hygiene-cron]` notification to both orchestrator in” vs
  `active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md:53`: “Cloud Run
  `uts-prod-plan-hygiene-sweep` (05:00 UTC) ENABLED but failing ~every other day with `Container called exit(1)` and
  ZERO stdout in Cloud Logg”
  - why: The epic (last_updated 2026-05-23, never revised) marks this cron infra done and claims it appends a failure
    notification to both orchestrator inboxes. The open issue doc (last_updated 2026-06-27, still has 2 open follow-up
    todos to eventually delete this same job) documents that it has been silently dying with zero lo

- planned fix: Annotate plan_hygiene_master's cron line: the Cloud Run job has been failing silently (exit 1, zero
  stdout) since ~2026-06-12 per the open issue doc - epic claim corrected with pointer; the fix itself stays tracked in
  the issue doc.

#### [P0] active/mvp_backfill_defi_onchain_v10_2026_06_27.md ↔ epics/defi_master.md

- finding ids: 37,41
- **DeFi vs CeFi asset_group classification of Lighter / Extended / Pacifica** — `epics/defi_master.md:282`: “Plus
  historical-replay backfill for Lighter / Extended / Pacifica (originally scoped under CeFi venue expansion but they
  are DeFi by asset_group).” vs `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:74`: “LIGHTER / EXTENDED / PACIFICA
  are CeFi, NOT DeFi (v10 decision #4) — do NOT backfill them here. Any older plan treating them as DeFi is stale and
  SUBO”
  - why: The epic's still-current, un-bannered 'Scope' section asserts these 3 venues are settled DeFi-by-asset_group
    work (and repeats this in its 'Current state' and critical-path table), with no acknowledgment of any
    reclassification. The newer v10 MVP canonical-scope plan explicitly declares them CeFi and calls ANY older pl
- **Epic's 'Assigned active plans' body list is missing an active P0 child plan** — `epics/defi_master.md:1672`:
  “Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py` — it keeps the list in sync from frontmatter.”
  vs `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:14`: “parent_epic: defi_master”
  - why: mvp_backfill_defi_onchain_v10_2026_06_27.md declares parent_epic: defi_master, is status: active, priority: P0,
    and is a heavily-worked in-flight plan (huge Progress Log through 2026-06-29); it appears in the epic's frontmatter
    related/related_plans lists (L18, L54) but is entirely absent from the epic body's '## Assig

- planned fix: Sync defi_master's Lighter/Extended/Pacifica asset_group classification to the v10 backfill plan's
  UAC-SSOT-backed classification, with pointer.

#### [P0] active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md (intra-doc)

- finding ids: 239,240
- **3-level hierarchy prerequisite: ticked-done vs 'not yet ticked' in the same plan** —
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:85`: “[x] ✅ [SCRIPT][UI] P0. **deployment-ui 3-level
  hierarchy + per-shard parquet download**. ... — deployment-ui@319075e” vs
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:97`: “[BLOCKED-PLAYWRIGHT 2026-06-24 slot-21]\*\*:
  PREREQUISITE (3-level hierarchy above) not yet ticked; this VERIFY > cannot run until”
  - why: The 3-level hierarchy P0 item is checked off [x]✅ as shipped, but the VERIFY todo directly beneath it (itself
    unticked) explicitly states the same prerequisite is 'not yet ticked' and blocks the VERIFY on it. The two todos in
    the same plan directly disagree on whether the prerequisite is complete — an agent could eithe
- **UI todos ticked done despite the plan's own note that the required playwright gate never ran** —
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:72`: “[x] ✅ [SCRIPT][UI] P0. Data-status panel
  renders `OTHER` as a normal canonical-question-group bucket (NOT "out of scope").” vs
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:75`: “before ticking. — deployment-ui@d5b7dd3 |
  [BLOCKED-PLAYWRIGHT] fleet VM has no dev server; pw:L2 gate pending UI-capable slot”
  - why: This todo (and the two others in the same P0 block, lines 79-84 and 85-92) are marked [x]✅ done, but each
    carries its own '[BLOCKED-PLAYWRIGHT] ... pw:L2 gate pending' annotation on the same line — meaning the mandatory
    pw:L2 ✓ playwright verification (required by CLAUDE.md's UI hard rule before any tick) never actuall

- planned fix: Fix predictions_other_bucket intra-doc drift: 3-level-hierarchy prerequisite ticked done in one section,
  'not yet ticked' in another - align to the checked state with evidence.

#### [P0] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md ↔ active/sports_p1_golden_window_apifootball_2026_06_27.md

- finding ids: 269
- **Golden-window API-Football enrichment coverage: 100%-for-94-leagues claim vs still-open 94-league enrichment g** —
  `active/sports_p1_golden_window_apifootball_2026_06_27.md:124`: “✅ Every API-Football data_type reads 100% honest
  coverage on 2025-09-01..2025-11-30 for the 94 leagues, manifest-verified.” vs
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:166`: “**94-league enrichment
  backfill** — the residual golden-window gap is now GENUINE missing enrichment (XG_SHOTS 0% / XG 13% / PLAYER_STATS 21%
  / MATCHE”
  - why: P1a's own Progress Log audit (same doc, line 164: "UAC universe (get_all_league_ids) = 33 leagues; all present
    in window") shows the verification actually ran against only 33 registered leagues, not the 94-league curated
    trading universe defined by the sibling plan. The sibling plan (same asset_group=sports, updated th

- planned fix: Sync sports golden-window enrichment coverage claim between the two sports plans (100%-for-94-leagues vs
  still-partial) to the later-dated evidence.

#### [P0] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md ↔ epics/orchestrator_master.md

- finding ids: 349
- **AO dispatch model: multi-VM epic-fleet vs single-VM role-based dispatch** — `epics/orchestrator_master.md:64-65`:
  “**Owns**: agent-orchestrator multi-VM stack (central/orchestrator VM `planning` + human planning VM
  `human-planning` + 9 epic VMs — human/central SPLI” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-209`: “Role-based dispatch — NO epic VM
  (single-VM architecture, 2026-06-27)...epic VMs deprecated per CLAUDE.md; there is no `vm-sports` to start”
  - why: orchestrator_master.md is status:active (not archived) and its core 'Owns' description plus its own frontmatter
    `assigned_vm: vm-orchestrator` (line 32) still present a live 9-epic-VM multi-VM fleet with per-VM backends as the
    current architecture. The 2026-06-27 sports plan (also active, and corroborated by `active/\_a

- planned fix: Extend orchestrator_master's partial-supersede notice: the 9-epic-VM fleet description in 'Owns' is
  superseded by the single-VM role-based architecture (2026-06-27, CLAUDE.md + AO plans); notice points to
  agent-orchestrator-single-vm-architecture codex doc.

#### [P0] active/tradfi_multisource_backfill_2026_06_22.md ↔ active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md

- finding ids: 304
- **VIX cash-index sourcing decision — open question vs already-decided-and-executed** —
  `active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:128`: “Blocked on operator decision: route VIX
  through existing Barchart/Yahoo MTDS path or add a new VIX-specific data source. Status: **BLOCKED-OPERATOR-DE” vs
  `active/tradfi_multisource_backfill_2026_06_22.md:93`: “DELETE the VIX **cash index\*\* entirely (not leave as
  empty_confirmed clutter): not tradable, derivable from the futures, trades less often over a shor”
  - why: sp500_ml (provenance dated slot-23 2026-06-24, one day AFTER the multisource_backfill's 2026-06-23 operator
    decision) frames CBOE VIX cash-index sourcing as an UNRESOLVED question requiring an operator pick between routing
    via Barchart/Yahoo or adding a new source. But the operator already decided the opposite (2026-06

- planned fix: Update tradfi_sp500_ml's BLOCKED-OPERATOR-DECISION VIX item: decision already made + executed 2026-06-23
  (VIX cash index DELETED, derive from VX futures) per tradfi_multisource_backfill L93 - replace the open ask with the
  recorded ruling + pointer.

#### [P0] archive/2026_05/workspace_qg_sweep_2026_05_23.md ↔ epics/features_and_ml_master.md

- finding ids: 54
- **workspace_qg_sweep_2026_05_23 status/ownership** — `epics/features_and_ml_master.md:886-889`: “###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — features/ML cluster
  **status**: 🟠 ACTIVE — QG sweep for f” vs `archive/2026_05/workspace_qg_sweep_2026_05_23.md:5,14`: “status: complete
  ... parent_epic: infrastructure_master”
  - why: The epic's own 'Assigned active plans' P0 section lists this plan as 🟠 ACTIVE features/ML-cluster work
    assigned to vm-ml, but the plan's own frontmatter (which the epic links to directly) says status: complete and
    parent_epic: infrastructure_master, not features_and_ml_master. An agent trusting the epic roster would be

- planned fix: Sync features_and_ml_master's workspace_qg_sweep status/ownership line to the plan's actual state.

#### [P0] epics/README.md ↔ epics/agent_operating_framework_master.md

- finding ids: 308,309
- **Epic registry completeness — README's canonical 20-epic table omits live epics** — `epics/README.md:164`: “## 20
  epics in 5 tiers” vs `epics/agent_operating_framework_master.md:23`: “tier: L5”
  - why: README.md (L14: 'This file is the SSOT for what epics are... how they map to VMs') presents a closed registry
    of exactly 20 epics across 5 tiers (L164-188), with the only L5 row being orchestrator_master.
    agent_operating_framework_master.md is a currently active (status: active, L8), P0-priority (L24), tier-L5 epic cre
- **assigned_vm dispatch model — epic-level VM ownership vs strict per-plan matching** — `epics/README.md:93`:
  “assigned_vm: vm-<id> # registry-resolved VM that owns this epic” vs `epics/agent_operating_framework_master.md:129`:
  “D2. assigned_vm is a mandatory per-plan field; epic-to-VM delegation is DROPPED for matching”
  - why: README.md's canonical epic frontmatter schema (no supersession banner, last_updated 2026-05-21) still documents
    assigned_vm as an epic-owning field resolved against a 'VM topology (10 VMs serving 20 epics)' registry
    (README.md:192-208, e.g. vm-defi/vm-cefi/vm-cross-cutting), and 5 other epics in this cluster still popu

- planned fix: Banner epics/README.md: registry table (20 epics, 2026-05-21) is missing
  agent_operating_framework_master + escalation_and_disaster_recovery_master; banner points to the live epic set until
  the table is regenerated. Full table rewrite = separate Q (see B-queue).

#### [P0] epics/agent_operating_framework_master.md ↔ epics/escalation_and_disaster_recovery_master.md

- finding ids: 338
- **Whether escalation_and_disaster_recovery_master (and its W9 broker hard-dependency) is live/dispatchable or pa** —
  `epics/agent_operating_framework_master.md:62-66`: “DEFER to next quarter: W7 ... W8 ... W9 (message broker /
  (role,domain) routing / POST /api/messages) ... and the role/escalation pilots (...
  `escalat”  vs  `epics/escalation_and_disaster_recovery_master.md:7`: “status: active”
  - why: agent_operating_framework_master's 2026-06-26 operator re-scope banner explicitly names 'the
    escalation_and_disaster_recovery_master epic' itself (plus its W9 broker dependency) as deferred to next quarter and
    slated for pausing. escalation_and_disaster_recovery_master's own frontmatter (created/last_updated 2026-06-25

- planned fix: Mark escalation_and_disaster_recovery_master status: paused + banner citing the AOF 2026-06-26 operator
  DEFER-to-next-quarter decision (W9 broker dependency deferred).

#### [P0] epics/batch_live_symmetry_master.md ↔ epics/instruments_master.md

- finding ids: 337
- **Status of canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 (CCXT live vs batch instrument-id divergence a** —
  `epics/instruments_master.md:465-467`: “✅ canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 — DONE,
  `instruments-service@8544273d` — all 13 canonical CeFi venues verified converged live=” vs
  `epics/batch_live_symmetry_master.md:77-84`: “status: 🔴 NEW ... canonical_id_p0_ccxt_live_batch_divergence_2026_07_08
  — the CCXT live adapter stores bare ccxt-native symbols; batch (Tardis) produc”
  - why: Both epics reference the identical child plan slug
    (../active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md — confirmed frontmatter status: complete,
    parent_epic: batch_live_symmetry_master). instruments_master marks it DONE with a resolving commit and 'all 13
    venues verified converged live=batch'. batch_liv

- planned fix: Cross-epic view of #19: batch_live_symmetry epic sync brings it in line with instruments_master's DONE
  entry.

#### [P1] ../cursor-configs/CLAUDE.md ↔ active/stash_pile_workspace_cleanup_2026_06_03.md

- finding ids: 72,73
- **Whether the `tab/<op>/N` branch model still exists for parking/inheriting WIP** —
  `active/stash_pile_workspace_cleanup_2026_06_03.md:83`: “**surface in report → owner confirms** (drop, or
  inherit-and-commit onto its own `tab/<op>/<N>` branch)” vs `cursor-configs/CLAUDE.md:126`: “the `tab/<op>/N` model is
  RETIRED — any such instruction is STALE”
  - why: This active P3 plan (last_updated 2026-06-27, same date CLAUDE.md's per-tab-worktrees rule cites) still
    instructs agents/owners to inherit orphaned WIP onto a `tab/<op>/<N>` branch. CLAUDE.md's HARD RULE says this exact
    branch model is retired workspace-wide and any instruction referencing it is stale. An agent executi
- **Existence of per-epic VMs (vm-defi/vm-cefi/vm-tradfi/etc.) to dispatch work to** —
  `active/stash_pile_workspace_cleanup_2026_06_03.md:117`: “Run stash audit + conservative sweep on **vm-defi**; commit
  report. — owner: vm-defi” vs `cursor-configs/CLAUDE.md:314`: “N slot workers, role-based dispatch (no per-epic VMs;
  single-VM architecture 2026-06-27)”
  - why: Phase 3 of this active plan dispatches 10 separate per-host todos to named epic VMs (vm-defi, vm-cefi,
    vm-tradfi, vm-sports, vm-prediction, vm-ml, vm-trading-core, vm-operator-ops, vm-cross-cutting, vm-orchestrator).
    CLAUDE.md's system map states the per-epic-VM model was retired in favor of a single central orchestrat

#### [P1] active/canonical_id_builder_retrofit_checklist_2026_07_08.md ↔ active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md

- finding ids: 124
- **Whether the Deribit combo-leg builder retrofit (checklist's todo 5) is done or still unexecuted** —
  `active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md:507-511`: “Still needs: the actual retrofit of
  `deribit_combo_adapter.py:310` to call it — tracked as its own todo in
  `canonical_id_builder_retrofit_checklist_20”  vs  `active/canonical_id_builder_retrofit_checklist_2026_07_08.md:112-116`: “Fix the real `:TYPE:`segment bug in Deribit's combo-leg builder — DONE 2026-07-09,`instruments-service@ca2f44e5`. New `\_classify_deribit_leg_instrum”
  - why: instruments_docs_audit_outstanding_items explicitly names the checklist's 'todo 5' as tracked-but-unexecuted,
    but that exact todo (the 5th checkbox, immediately after the on-chain-perp retrofit item) is checked [x] DONE with a
    real commit hash and evidence in the checklist itself. An agent trusting the audit doc could

#### [P1] active/capability_wizard_and_manifest_2026_06_11.md ↔ active/carry_staked_basis_funding_scan_experiment_2026_06_16.md

- finding ids: 291
- **Carry plan treats CarryStakedBasisRankAllocator/staked_basis.py as the authoritative batch==live production re** —
  `active/capability_wizard_and_manifest_2026_06_11.md:907-909`: “F27 — carry entry-emission was never the empty
  registry; strategy-service \_derive_structure calls accepted_perp_collateral with lowercase venue ids ag” vs
  `active/carry_staked_basis_funding_scan_experiment_2026_06_16.md:43`: “production path is `strategy-service`
  `CarryStakedBasisRankAllocator` + `engine/strategies/v2/carry_and_yield/ staked_basis.py`, batch == live”
  - why: The wizard plan documents (2026-06-12, still unresolved as of its last entry at
    capability_wizard_and_manifest_2026_06_11.md:1024) that the production staked-basis collateral-acceptance code has a
    case-mismatch bug making it ALWAYS return no accepted collateral for every venue — i.e. the live engine can never
    actually

#### [P1] active/capability_wizard_and_manifest_2026_06_11.md ↔ epics/strategy_master.md

- finding ids: 287,288
- **StrategyArchetype enum member count (55 vs 57, later 58)** — `epics/strategy_master.md:140-144`: “operator decision
  2026-06-01: the 28 implemented archetype engines are the intended May-23 rollout subset (NOT a regression vs the
  55-member
  `Strategy”  vs  `active/capability_wizard_and_manifest_2026_06_11.md:131`: “`extract_architecture_v2_capability_registry()`.
  Verified output: StrategyArchetype 57 values (count grew from audited 53 — 4 new archetypes landed)”
  - why: The epic carries a still-open (unchecked) P1 todo (F-34) directing whoever picks it up to fix a docstring/count
    from '53' to '55', premised on a 2026-06-01 operator decision that the enum has 55 members. The sibling
    capability_wizard plan, on the very same day the epic was last updated (2026-06-11), audited the actual
- **Epic's auto-populated active-plan index is missing this plan (and the carry plan) from its P0-P3 priority list** —
  `epics/strategy_master.md:99`: “\_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers
  pick up in priority order (P0 first). Auto-populated by
  `scripts/”  vs  `active/capability_wizard_and_manifest_2026_06_11.md:19`: “parent_epic: strategy_master”
  - why: The epic's 'Assigned active plans' section claims to be auto-populated and lists exactly 8 plans across P0-P3,
    generated by a script last run 2026-05-21. Neither capability_wizard_and_manifest_2026_06_11.md nor
    carry_staked_basis_funding_scan_experiment_2026_06_16.md (both created after 2026-05-21, both declaring `pare

#### [P1] active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md ↔ active/mvp_backfill_cefi_tick_v10_2026_06_27.md

- finding ids: 28
- **Whether BINANCE-FUTURES/DERIBIT futures_chain gap is a fixable genuine-gap (needs VM relaunch) or a structural** —
  `active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md:77`: “futures_chain for BINANCE-FUTURES: 0
  captured, 13,334 attempted_failed (100% gap)... Backfill relaunch required” vs
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:819`: “futures_chain Tardis channel absence confirmed —
  availableChannels shows NO futures_chain for: binance-futures, bybit, deribit, kraken-futures, bitfin”
  - why: The bundle-verification plan (status active, checked P0 items DONE 2026-06-12/06-24) diagnosed the
    BINANCE-FUTURES futures_chain gap as a genuine, capturable gap and marked its VM-relaunch action ✅ complete (14
    DERIBIT + 7 BINANCE-FUTURES VMs launched). The later mvp_backfill plan (2026-07-03) discovered via direct Tar

#### [P1] active/cefi_manifest_canonicalisation_2026_06_01.md ↔ archive/2026_06/instruments_manifest_canonicalisation_2026_06_01.md

- finding ids: 150
- **Owner-of-record for the cefi instruments-store v9 single-walk todo** —
  `active/cefi_manifest_canonicalisation_2026_06_01.md:1864-1868`: “Owner = the **cefi slice** of
  `instruments_manifest_canonicalisation_2026_06_01.md`; `--apply` **GATED on coordinator G0**” vs
  `archive/2026_06/instruments_manifest_canonicalisation_2026_06_01.md:26-28`: “✅ ARCHIVED 2026-06-26 — folded into
  instruments_mtds_subset_consistency_remediation_2026_06_17 (survivor I-2)...Lock cleared.”
  - why: cefi_manifest_canonicalisation (active, last_updated 2026-06-27 — one day AFTER the archival) still has an open
    [ ] P1 todo naming the archived/completed instruments_manifest_canonicalisation_2026_06_01.md as the live 'Owner',
    with no acknowledgment that its 8 open todos were folded into instruments_mtds_subset_consist

#### [P1] active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md ↔ active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md

- finding ids: 347,86
- **Is the pipeline currently LDR→staging→main (staging live) or LDR→main direct (staging dormant/bypassed)?** —
  `active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md:29`: “`staging→main` / `LDR→staging` promote PRs
  (observed on UTL #475, head `53852d11`)” vs `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:7`: “Staging is
  DORMANT (reversible switch kept). The promote gate set is exactly THREE things: SIT-green + quality-gates-v2 ...”
  - why: doc_b (created 2026-06-30, frontmatter/body explicitly declares itself 'the single SSOT for the simplified
    pipeline' and supersedes the whole prior CI/CD plan family) asserts staging is DORMANT and the only path is
    LDR→SIT→main direct. doc_a is an OPEN, unresolved issue (status: open, last_updated 2026-06-27) whose ent
- **promote-pipeline shape — staging-routed vs staging-dormant MVP** —
  `active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md:28`: “The commit-status
  `AWS CodeBuild ap-northeast-1 (<repo>)` shows **`failure`** on automated `staging→main` / `LDR→staging` promote PRs
  (observed on UTL” vs `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:7`: “Staging is DORMANT (reversible switch
  kept).”
  - why: The still-open aws_codebuild issue (last_updated 2026-06-27) frames 'LDR→staging'/'staging→main' promote PRs as
    the live pipeline needing an AWS-side fix; three days later the operator-reaffirmed cicd_mvp plan (same parent_epic,
    active) declares staging DORMANT with LDR→main direct as the MVP default. The open issue ne

#### [P1] active/data_eng_role_vertical_pilot_2026_06_25.md ↔ epics/agent_operating_framework_master.md

- finding ids: 7
- **Dispatch state of the Data-Eng vertical pilot: epic says dispatched to harsh_pc, plan frontmatter says NA (nob** —
  `epics/agent_operating_framework_master.md:235`: “role `data_eng_role_vertical_pilot_2026_06_25` | W6 instance —
  Data-Eng (first full vertical; **dispatched harsh_pc**)” vs `active/data_eng_role_vertical_pilot_2026_06_25.md:15`:
  “assigned_vm: NA”
  - why: Per the epic's own locked dispatch rule D1/D3 (strict assigned_vm==backend matcher; NA -> dispatched to
    nobody), the plan's current frontmatter assigned_vm:NA means the pilot is NOT actually being executed by any
    backend, contradicting both the epic's summary table ('dispatched harsh_pc') and the plan's own body narrat

#### [P1] active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md ↔ epics/observability_master.md

- finding ids: 202
- **data_feed_sla_registry_and_active_self_healing completion status** — `epics/observability_master.md:195`:
  “status\*\*: active — NEW 2026-06-19 from the "Operation Blue Flame" SLA-architecture comparison (operator). Two gaps
  where the external reference is tig” vs `active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md:225`:
  “DONE. Both gaps from the Blue Flame comparison are closed and shipped; the plan's success criteria are met”
  - why: The epic hub (last_updated 2026-06-19) still describes the plan's two Blue-Flame gaps as open P1 work to be
    closed, but the plan's own body carries a 2026-06-20 final report declaring both gaps DONE and shipped end-to-end.
    An agent reading only the epic would treat already-completed work as live/pending.

#### [P1] active/data_pipeline_hardening_self_monitoring_2026_06_22.md (intra-doc)

- finding ids: 191,194
- **Whether Telegram is still a live alerting transport in alerting-service** —
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:2063-2066`: “Slack is now the PRIMARY alerting transport
  — Telegram RETIRED (operator decision 2026-06-23) ...
  `_deliver_message`/`send_telegram`/deprecated-`slack”  vs  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:2081-2083`: “there is NO `alerting-slack-webhook-url`secret, but`alerting-telegram-bot-token`+`alerting-telegram-chat-id`
  DO exist → the generic path's PRIMARY”
  - why: One checked-done entry states `send_telegram` was REMOVED and Telegram fully RETIRED as of 2026-06-23; a second
    entry in the same doc, dated the same day, diagnoses the generic incident path as still using Telegram as its
    PRIMARY channel (driven by existing SM secrets). If send_telegram was truly removed, the incident
- **Completion status of the 8th C6 reader-bucket-env bug fix** —
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:303-304`: “[~] [CODE] P1. **Fix the 8 C6
  reader-bucket-env bugs** the parity check found — **7 of 8 SHIPPED on origin/LDR** ... **8th site —
  `live/websocket_runn”  vs  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:1216-1223`: “**FOLLOW-UP (C6 / DP-ENV-001, non-prediction) — SHIPPED ON LDR (verified 2026-06-22 resume-run)\*\*: `websocket_runner._read_is_parquet_sync`
  now resolv”
  - why: The todo checkbox is left in partial state `[~]` claiming 1 of 8 sites remains deferred, while a later entry in
    the same document confirms all 8 sites (including the exact deferred one) are shipped and verified on LDR with 'No
    further action.' The stale `[~]` marker could cause a worker to re-attempt already-completed

#### [P1] active/data_pipeline_hardening_self_monitoring_2026_06_22.md ↔ active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md

- finding ids: 192
- **Whether the DP\_\* PubSub→subscriber→Slack relay was actually delivering alerts on 2026-06-22** —
  `active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md:120-122`: “**RELAY NOW LIVE END-TO-END (2026-06-22
  18:27Z)**: emit (mode=live → lifecycle-events) → subscriber consumes lifecycle-events-sub (no 403) → route_eve” vs
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:961-963`: “the alerting subscriber IS running ... the
  messages DO land ... YET 0 DP events routed in 14 min. Root cause: UTL PubSubEventSink.write_event publishe”
  - why: The issue doc declares the relay definitively 'LIVE END-TO-END' at 18:27Z and later (still open, `last_updated`
    2026-06-27) lists only cosmetic/durability items as remaining ('NOT blocking the relay — it is live'). The related
    plan (same day) subsequently proves DP\_\* events were silently dropped before Slack due to an un

#### [P1] active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md ↔ active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md

- finding ids: 296
- **Drift LST collateral haircut values for SOL/mSOL/JitoSOL: 0.05/0.10/0.10 (e2e doc) vs updated real 0.15/0.20/0** —
  `active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md:91-92`: “USDC(0), SOL(0.05), **mSOL(0.10
  `# PLACEHOLDER`)**, JitoSOL(0.10) — `venue_collateral.py:112-125`. NOT stables-only.” vs
  `active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:187`: “a F28 live-probe (UAC@bc45549,
  ~2026-06-17) updated Drift haircuts to real on-chain initialAssetWeight (SOL/mSOL/JitoSOL = 0.15/0.20/0.20, were 0.10
  p”
  - why: Both docs are dated 2026-06-17 and cite the same venue_collateral.py source, but the e2e-taxonomy issue
    (status: open, still presented as current fact) never got the F28 live-probe update noted in the sibling plan — a
    reader of the still-open e2e doc would use the wrong (stale/placeholder) haircut numbers for a data-co

#### [P1] active/defi_manifest_canonicalisation_2026_06_01.md ↔ active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md

- finding ids: 156
- **ASTER CeFi funding-carrier (derivative_ticker) capture status — 100% failed vs 62% captured/ok** —
  `active/defi_manifest_canonicalisation_2026_06_01.md:1462-1463`: “E1 CeFi `derivative_ticker` (funding carrier) fetch
  failures: OKX-FUTURES + ASTER 100% attempted_failed; refresh to current (stale ~3–5 weeks).” vs
  `active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md:40`: “**ASTER** ... | derivative_ticker (funding) | 62% |
  ok |”
  - why: defi_manifest_canonicalisation's still-open P0 item E1 (unchanged since the plan's 2026-06-01 creation) asserts
    ASTER's derivative_ticker (the funding carrier the DeFi-hybrid hedge leg needs) is 100% attempted_failed and stale
    3-5 weeks. The newer cefi_hl_aster_batch_data_gaps issue doc's 2026-06-22 runtime/manifest au

#### [P1] active/defi_manifest_canonicalisation_2026_06_01.md ↔ active/solana_defi_legacy_migration_2026_05_27.md

- finding ids: 155
- **Solana pool data_type: merged into one dex_pool_state vs still-separate dex_pools+SOLANA_AMM_POOL** —
  `active/defi_manifest_canonicalisation_2026_06_01.md:1601-1605`: “canonical Solana types per that plan are
  `dex_pools`+`SOLANA_AMM_POOL` ... vs the MVP's `DEX_POOL_STATE` ... — **complementary, not conflicting** (dif” vs
  `active/solana_defi_legacy_migration_2026_05_27.md:42-46`: “**NEW — `dex_pool_state` is now the UNION of EVM + Solana
  pool state under ONE data_type** (operator 2026-06-01) ... `SOLANA_AMM_POOL`/`SOLANA_VAULT` ”
  - why: defi*manifest_canonicalisation's own A11g item (same file, L854-864, operator-decided 2026-06-05) explicitly
    states the union is lossless and 'no second data_type is warranted (the solana_defi_legacy_migration G-note
    "complementary" view is superseded by the union being a superset)', and the sibling solana_defi_legacy*

#### [P1] active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md ↔ epics/defi_master.md

- finding ids: 47
- **Lighter/Pacifica historical-replay backfill required start-date vs actual verified data range** —
  `epics/defi_master.md:330`: “Lighter + Pacifica OHLCV non-empty 2024-08-01+ / 2025-06-01+ respectively; Extended
  pending Phase 0 empirical research before any VM launch” vs
  `active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md:80-82`: “GCS verified 2026-06-16: LIGHTER-ZKSYNC 1590
  parquets (BTC/ETH/HYPE/SOL/TON × 319 days, 2025-05-01→2026-05-06); PACIFICA-SOLANA 1408 parquets (ETH/HYP”
  - why: The epic's Critical Path table (unsuperseded — header carries no '— SUPERSEDED 2026-06-20' marker, unlike the
    frozen sections below it) sets the success gate as OHLCV non-empty from 2024-08-01 (Lighter) and 2025-06-01
    (Pacifica). The child plan's own P0 todo, checked done (✅) on the strength of a 2026-06-16 GCS verific

#### [P1] active/deployment_observability_expansion_2026_07_08.md ↔ active/deployment_observability_parity_live_batch_paper_2026_06_22.md

- finding ids: 196
- **Deployments-page UI architecture (tabs vs merged table)** —
  `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:122`: “A **Deployments** page at `/deployments`
  mirroring RepoCi grade: umbrella tabs (**Live / Batch / Paper**), each a matrix of VMs+Cloud-Run-jobs” vs
  `active/deployment_observability_expansion_2026_07_08.md:52`: “Merged Deployments tab — SHIPPED. live/batch/paper
  collapsed into ONE flat all-modes table (Mode is a filter, not tabs); 3 cockpit tabs + 3 health til”
  - why: Parity plan (status active, last_updated 2026-06-27) checked off and still presents a Live/Batch/Paper-TAB
    Deployments page as the shipped architecture (deployment-ui@051c255). The newer expansion plan (created 2026-07-08)
    explicitly collapsed that exact tab design into ONE flat table with Mode as a filter (deployment-

#### [P1] active/deployment_observability_expansion_2026_07_08.md ↔ epics/observability_master.md

- finding ids: 324
- **observability_master active-child-plan count** — `epics/observability_master.md:99-100`: “"13 active plans declare
  parent_epic: observability_master in their frontmatter...Auto-populated by
  scripts/plans/populate_epic_bodies_2026_05_21.py."” vs
  `active/deployment_observability_expansion_2026_07_08.md:11,27`: “status: active / parent_epic: observability_master
  (last_updated 2026-07-08)”
  - why: Epic claims 13 active children; grep shows 24 currently exist (including deployment*observability_expansion,
    deployment_obs_ui_popover_health, phantom_captures*_ issue docs, manifest*hygiene_red*_ — all dated
    2026-06-2x/07-0x), none of which appear anywhere in the epic body's P0/P1/P2 sections (only 1 P0 item + 1 P1 it

#### [P1] active/downstream_services_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 170,174
- **Scope of 'live MTDS/MDPS work' after the 2026-06-26 consolidation banner** — `epics/mtds_mdps_master.md:133`: “🔵
  CONSOLIDATION 2026-06-26 — live MTDS/MDPS work now runs through 2 themed survivors (M-1, M-2).” vs
  `active/downstream_services_manifest_canonicalisation_2026_06_01.md:90`: “CF-11 write-path — instruments-service
  residual — DONE all 3 slices (slot audit 2026-07-10).”
  - why: Epic claims (2026-06-26) all live MTDS/MDPS work now runs through only M-1/M-2;
    downstream_services_manifest_canonicalisation (parent_epic: mtds_mdps_master, status active, not M-1/M-2, never
    listed in the epic's own 'Assigned active plans') shows extensive NEW live work shipping as late as 2026-07-10 (also
    true of sol
- **Completeness of the epic's enumerated child-plan list** — `epics/mtds_mdps_master.md:713`: “_33 active plans declare
  `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30)... Auto-populated by
  `scripts/plans/populate_epic_” vs `active/downstream_services_manifest_canonicalisation_2026_06_01.md:28`:
  “parent_epic: mtds_mdps_master”
  - why: The epic claims its 'Assigned active plans' section reflects all 33 plans declaring this parent_epic, verified
    as recently as 2026-06-30, yet a full-text grep of the epic file for the three assigned docs' slugs
    (downstream_services_manifest_canonicalisation, solana_defi_legacy_migration, mtds_plan_reconciliation) retur

#### [P1] active/features_service_e2e_pipeline_test_2026_05_26.md (intra-doc)

- finding ids: 55,56
- **stale rollout-agent HOLD banner vs live open P0/P1 todos** —
  `active/features_service_e2e_pipeline_test_2026_05_26.md:45-47`: “🛑 ROLLOUT-AGENT HOLD (2026-05-26): harsh-side
  (operator-directed) is actively working this plan end-to-end. Do NOT auto-assign / auto-fix / push to LD” vs
  `active/features_service_e2e_pipeline_test_2026_05_26.md:641-663`: “### Open Track-1 todos (narrowed 2-strategy
  validation — the actual goal) - [ ] [SCRIPT] P0. Phase A — features-onchain staked-basis slice e2e. ... - ”
  - why: The plan is still status:active with unaddressed P0/P1 todos (Track-1 Phase A/B/C, last touched per the doc's
    own body content on 2026-06-03), yet a never-removed HOLD banner from 2026-05-26 tells any agent not to
    auto-assign/auto-fix/push to this plan. With no removal note and the doc's most recent session content ove
- **frontmatter last_updated stale vs body content** — `active/features_service_e2e_pipeline_test_2026_05_26.md:26`:
  “last_updated: 2026-05-25” vs `active/features_service_e2e_pipeline_test_2026_05_26.md:577`: “## 2026-06-03 — Scope
  narrowed to 2 strategies + Track-2 fixes shipped (session handoff)”
  - why: Frontmatter last_updated (2026-05-25) predates the plan's own body content by more than a week (body has dated
    session logs through 2026-06-03), so any staleness/triage tooling reading last_updated would misjudge this plan as
    far more stale than it is.

#### [P1] active/features_service_e2e_pipeline_test_2026_05_26.md ↔ epics/features_and_ml_master.md

- finding ids: 57
- **epic child-plan roster drift (missing a live P0 plan)** — `epics/features_and_ml_master.md:879-884`: “## Assigned
  active plans \_4 active plans declare `parent_epic: features_and_ml_master` in their frontmatter. Workers pick up in
  priority order (P0 fir” vs `active/features_service_e2e_pipeline_test_2026_05_26.md:10,19,22`: “status: active ...
  parent_epic: features_and_ml_master ... priority: P0”
  - why: This plan explicitly declares parent_epic: features_and_ml_master, status:active, priority:P0 in its own
    frontmatter, but the epic's auto-populated 'Assigned active plans' roster (claiming to enumerate exactly the plans
    that declare this parent_epic) never lists it anywhere in the P0/P1/P2/P3 sections or the archived-p

#### [P1] active/foundation_gates_and_capture_to_100_2026_07_06.md ↔ active/is_catalogue_completion_2d_2026_07_06.md

- finding ids: 110
- **Sibling AO plans in the same instruments-completion sweep were flipped to complete on 2026-07-10, but this one** —
  `active/is_catalogue_completion_2d_2026_07_06.md:12`: “status: active” vs
  `active/foundation_gates_and_capture_to_100_2026_07_06.md:260-261`: “2026-07-10 — Status-flip note: all 9 todos
  confirmed [x] with cited evidence ... Flipped status: active → complete.”
  - why: is_catalogue_completion_2d_2026_07_06.md has every one of its 8 top-level todos marked [x] with evidence (B0
    through the P3 doc-pointer fix) and no outstanding items, exactly like
    foundation_gates_and_capture_to_100_2026_07_06.md and instruments_catalogue_incremental_rollup_2026_06_29.md, both
    of which received an expl

#### [P1] active/infra_capture_and_devops_leftovers_2026_07_06.md ↔ active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md

- finding ids: 114
- **Whether UAC VENUE_DATA_TYPE_CAPABILITIES declares ASTER capable of book_snapshot_5** —
  `active/infra_capture_and_devops_leftovers_2026_07_06.md:79-80`: “"UAC `market_data_categories.py`
  `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` still only lists trades/derivative_ticker/perp_funding — NO book_snapshot_5, ”
  vs `active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md:103-106`: “"`_L5_VENUES` tuple ... is
  missing 11 venues UAC's `VENUE_DATA_TYPE_CAPABILITIES` declares as capable (... HYPERLIQUID, ASTER, PACIFICA-SOLANA,
  EXTEND”
  - why: Both docs describe the same UAC registry field on the same day (2026-07-07) with opposite factual claims:
    infra_capture says ASTER's UAC capability entry explicitly lacks book_snapshot_5 (this is the stated blocker gating
    the ASTER live-connector task, BLOCKED-PREREQUISITES); uac_data_type_validity says UAC's VENUE_DAT

#### [P1] active/instruments_mtds_subset_consistency_remediation_2026_06_17.md (intra-doc)

- finding ids: 88,89,90
- **MTDS \_index v9/pipeline_mode column population state on 2026-06-18** —
  `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:467-508`: “"MARKET-DATA `_index` v9 COLUMN
  POPULATION — APPLIED to ALL 5 AGs (2026-06-18)" ... pipeline_mode/source/asset_group all 100% per AG (table); "[x]
  DON” vs `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:1092-1101`: “"N9c — MTDS `_index` is NOT
  yet v9 for any of the 5 AGs ... `pipeline_mode` is 100% blank/None (verified: 0 non-blank rows ...). Found 2026-06-18
  data”
  - why: Same document, same date, same MTDS `_index` pipeline_mode column: one section (checked, marked DONE) says it
    is 100% populated fleet-wide; another open P2 todo says it is 100% blank for all 5 AGs. An agent trusting the DONE
    section would wrongly believe the pipeline_mode filter chip works; the open N9c item is never r
- **CeFi MTDS attempted_failed cell count / whether F3 is still an open P0 blocker** —
  `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:925`: “"[ ] [DATA] P0. F3 — CEFI: 1.40M
  `attempted_failed` MTDS cells (36%). Break down by venue×data_type; diagnose the failing adapters/venues; backfill ..”
  vs `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:990-996`: “"[x] F3 (reframed) — CEFI
  re-classify legacy-recon attempted_failed — FIXED mtds@aaeada9 ... attempted_failed 1.40M→782,005 ... Genuine
  VENUE_FETCH_FA”
  - why: An open, undispatched P0 todo (F3) still cites the pre-fix 1.40M figure and frames it as requiring fresh
    diagnosis+backfill, while a separate section of the same plan marks F3 FIXED with a hugely different reconciled
    number (782k → ~88k genuine). A worker picking up the still-open line-925 item risks re-doing already-c
- **Whether TradFi options data has a real capture gap (F6)** —
  `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:927-930`: “"[ ] [CODE] P2. F6 — TRADFI: 182k
  blank instrument_type + thin options (options_chain 3,287 vs futures_chain 15,875) ... confirm whether options ARE l”
  vs `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:941-943`: “"Reframes: ... F6 options ARE
  captured (CME 8,602 opts/day, ES options_chain 20,956 rows) — the \"thinness\" is a typing artifact, REFUTED"”
  - why: The still-open F6 todo frames a possible real options-data capture gap needing investigation/backfill, while a
    later Phase-C audit in the SAME document explicitly REFUTES that framing (options are captured; it was a typing
    artifact). The open todo is never edited/closed to reflect the refutation, risking a redundant ca

#### [P1] active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md ↔ active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md

- finding ids: 344
- **cross-AG never-seeded backlog quantum estimates (cefi Kraken-6yr / tradfi / prediction) after the v1→v2 enumer** —
  `active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md:138`: “cefi/tradfi/prediction quantum estimates
  (~1.75M cefi Kraken-6yr, ~818k prediction cqg EU, etc.) were grep-based static estimates against the OLD land” vs
  `active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md:95`: “~200 spot instruments × ~4 batch data_types =
  ~1.75M cells not enumerable today (order-of-magnitude, catalogue-drive;”
  - why: Both issue docs are status: open and cover the same never-seeded-backlog topic. The newer doc
    (defi_expected_unattempted_backlog_1m, last_updated 2026-07-10) explicitly states
    cross_ag_never_seeded_backlog_scan's cefi/tradfi/prediction quantum figures (including the ~1.75M cefi Kraken-6yr
    number) are now understated by

#### [P1] active/issues/deadman_monitor_log_event_crash_2026_06_23.md ↔ active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md

- finding ids: 181
- **monitoring-deadman rebuild/verification status** — `active/issues/deadman_monitor_log_event_crash_2026_06_23.md:36`:
  “Live verification (deadman execution 1/1 green) is BLOCKED on `deployment-api:latest` rebuilding” vs
  `active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md:104`: “DONE + VERIFIED 2026-06-23 ~22:00Z. ...
  deadman 1/1 GREEN (exit 0, was exit 1 every run); heartbeat-watcher 1/1 GREEN.”
  - why: doc_b (same-day, cross-referenced) confirms the deployment-api rebuild happened and the deadman was verified
    1/1 GREEN; doc_a's status stays 'open' (last_updated 2026-06-27, 4 days after doc_b's verification) still framing
    verification as BLOCKED-pending-rebuild without acknowledging it landed — stale directive an agen

#### [P1] active/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md ↔ epics/execution_master.md

- finding ids: 52
- **Epic child-plan tracking vs actual issue-doc frontmatter** — `66`: “\_(no other active plans currently declare
  `parent_epic: execution_master`. Audit-pool wrapper plans for this epic land” vs `18`: “parent_epic: execution_master”
  - why: This open issue doc declares parent_epic: execution_master (L18) and carries a live unchecked P2 todo (L72-79,
    security-relevant aiohttp-CVE remediation gated behind it), yet the epic neither lists it in related/related_plans
    nor acknowledges it in the 'Assigned active plans' section, which instead flatly states no oth

#### [P1] active/issues/manifest_hygiene_red_2026_06_27.md ↔ active/issues/manifest_hygiene_red_2026_07_06.md

- finding ids: 209
- **Where the manifest-hygiene RED root cause actually lives: MTDS vs the shared audit script (defi instance)** —
  `plans/active/issues/manifest_hygiene_red_2026_06_27.md:55`: “diagnose + fix the root cause (misclassified-empty vs
  real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in
  `market-tick-data-servic”  vs  `plans/active/issues/manifest_hygiene_red_2026_07_06.md:57`: “root cause diagnosed as TWO false-positives in the AUDIT code itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`), NOT in `market-tick-data”
  - why: The still-open 06-27 (defi) doc's P1 todo directs a worker to diagnose/fix in market-tick-data-service for the
    identical boilerplate finding-classes list (incl. phantom_captured_no_parquet, shard_4pillar_fail) that the later
    07-06 doc proves are false-positive-generating bugs in the SHARED audit script `_check_phantom`

#### [P1] active/issues/manifest_hygiene_red_2026_06_29.md ↔ active/issues/manifest_hygiene_red_2026_07_06.md

- finding ids: 210
- **Where the manifest-hygiene RED root cause actually lives: MTDS vs the shared audit script (cefi instance)** —
  `plans/active/issues/manifest_hygiene_red_2026_06_29.md:55`: “diagnose + fix the root cause (misclassified-empty vs
  real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in
  `market-tick-data-servic”  vs  `plans/active/issues/manifest_hygiene_red_2026_07_06.md:57`: “root cause diagnosed as TWO false-positives in the AUDIT code itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`), NOT in `market-tick-data”
  - why: The still-open 06-29 (cefi) doc carries the same-titled, same-boilerplate P1 todo pointing diagnosis at
    market-tick-data-service, but the 07-06 doc (same script, same finding-class list, cefi) later proves the audit
    script itself was the false-positive source for 2 of the 5 classes and was fixed there — the 06-29 direc

#### [P1] active/issues/mtds_sports_api_football_blank_source_2026_06_28.md ↔ active/sports_manifest_canonicalisation_2026_06_01.md

- finding ids: 187
- **MTDS CF-4 blank-source regression on batch_api_football sports rows — resolved vs still-open** —
  `active/issues/mtds_sports_api_football_blank_source_2026_06_28.md:13`: “status: open ... Root Cause (to investigate)
  ... Required Fix: Find the writer that created these 10,716 rows and ensure it stamps source=api_football” vs
  `active/sports_manifest_canonicalisation_2026_06_01.md:2055-2059`: “MTDS CF-4 regression — RESOLVED 2026-06-29
  (slot-3, task -018): Forward fix shipped at mtds@bae321ca ... restamped 10,716 rows (batch_api_football → s”
  - why: Both docs describe the identical bug (same 10,716-row count, same pipeline_mode=batch_api_football, same CF-4
    tag, and the issue doc even cites sports_manifest_canonicalisation's E8 section as its own evidence source). The
    master plan records it as fully RESOLVED the next day with a named commit (mtds@bae321ca) and a r

#### [P1] active/issues/sports_trigger_scheduler_cloud_dispatch_broken_2026_07_08.md ↔ active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md

- finding ids: 270
- **Production architecture of the daily-forward sports scheduler: VM daemon vs Cloud Run Job** —
  `active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:44`: “**Daily-forward (R3)** — the
  sports-scheduler VM daemon (`launch-sports-scheduler-vm.sh` → `SportsTriggerScheduler`, ...) running the 4 tiers” vs
  `active/issues/sports_trigger_scheduler_cloud_dispatch_broken_2026_07_08.md:167`: “Also corrected the stale
  top-of-file comment claiming this job was "DEFERRED... VM instead" — confirmed via `gcloud compute instances list`
  that no `s”
  - why: P2d (status active, dependency of the coordinator's capstone gate) frames the daily-forward mechanism as a VM
    daemon launched via launch-sports-scheduler-vm.sh, and its own task-1 evidence (line 74) cites launching/relaunching
    such a VM (sports-scheduler-20260627-153504) as the gate-passing action. The later, resolved

#### [P1] active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md (intra-doc)

- finding ids: 62
- **Frontmatter status:open vs body's own 'fully closed' declaration** — `20`: “status: open” vs `210-211`: “Prereq #1
  ... #2, #3, #4, and this todo #5 are now ALL done — this issue doc's actionable-todo list is fully closed.”
  - why: All 5 actionable todos in this doc are checked [x] ✅, the final one (DELETE v1 dispatch surface) shipped
    instruments-service@b0859183 2026-07-09, and the doc's own last substantive Progress Log statement explicitly says
    the actionable-todo list is fully closed — yet frontmatter still carries status: open (last_updated:

#### [P1] active/l0_doc_index_generator_2026_06_24.md ↔ epics/agent_operating_framework_master.md

- finding ids: 6
- **W4 FF-cron auto-regen status: epic says shipped 2026-07-04, owning plan still says pending** —
  `epics/agent_operating_framework_master.md:298`: “generator scripts/docs/gen_doc_index.py (1,119 docs, ~1.4s,
  --stale-check) + FF-cron regen across EVERY PM clone incl. dirty trees (pm@b4d75366d, 2026” vs
  `active/l0_doc_index_generator_2026_06_24.md:58`: “FF-cron auto-regen — written, landing PENDING.”
  - why: The epic's W4 checkbox claims the FF-cron regen hook shipped fleet-wide on 2026-07-04 (pm@b4d75366d), but the
    owning child plan's own body (Shipped section) and Progress Log (dated 2026-06-24, never updated) still describe the
    FF-cron hook as authored-but-not-landed ('landing PENDING'), and the plan's Deferred checklis

#### [P1] active/master_to_live_defi_2026_05_23.md ↔ epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md

- finding ids: 214
- **cross_cutting epic status: active/not-folded vs superseded/absorbed** —
  `active/master_to_live_defi_2026_05_23.md:125`: “(still active — workspace-wide concerns spanning all domains;
  explicitly NOT folded)” vs `epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md:5`: “SUPERSEDED (2026-05-21) May-23
  cross-cutting epic ... absorbed into client_isolation_and_governance_master + infrastructure_master +
  observability_mas”
  - why: master*to_live_defi's epics-index row tells a reader the cross-cutting epic is 'still active ... explicitly NOT
    folded', while the epic doc itself (status: superseded, filename carries \_SUPERSEDED*) says its 5 deliverables were
    absorbed into three other masters and it is kept only as archaeology with no new work. An ag

#### [P1] active/migration_verification_orphan_safety_2026_06_10.md ↔ epics/manifest_master.md

- finding ids: 135
- **Epic's active-plan roster omits a live P0 child plan** — `epics/manifest_master.md:115`: “\_7 active plans declare
  `parent_epic: manifest_master` in their frontmatter (verified 2026-06-30). Workers pick up in priority order (P0
  first).” vs `active/migration_verification_orphan_safety_2026_06_10.md:10`: “status: active ... parent_epic:
  manifest_master ... priority: P0”
  - why: The epic's 'Assigned active plans' section claims 7 active plans declare parent_epic: manifest_master (verified
    2026-06-30) and enumerates its P0 list, but every P0/P1/P2 entry listed is a 2026-05-xx plan already marked
    ARCHIVED; migration_verification_orphan_safety_2026_06_10.md (status: active, priority: P0, parent_e

#### [P1] active/mvp_backfill_cefi_tick_v10_2026_06_27.md ↔ epics/cefi_master.md

- finding ids: 29,31
- **asset_group classification of LIGHTER-ZKSYNC / EXTENDED-STARKNET / PACIFICA-SOLANA** — `epics/cefi_master.md:172`:
  “DeFi DEX perps (Hyperliquid / Aster / Lighter / Extended / Pacifica) → see defi_master.md. Note:
  Lighter/Extended/Pacifica ... they're DeFi by asset_g” vs `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:104`: “Any
  older cefi plan that says ... LIGHTER/EXTENDED/PACIFICA as DeFi, is stale and SUBORDINATE (see Phase-4
  reconciliation)”
  - why: The cefi_master epic (still active, last_updated 2026-06-20, no superseded banner on this line) explicitly
    classifies Lighter/Extended/Pacifica as DeFi asset_group and routes them to defi_master.md. The active mvp_backfill
    plan (v10/v12 canonical MVP SSOT) treats these three venues as CeFi (line 109, capture-universe g
- **Epic's 'Assigned active plans' index completeness vs actual child-plan frontmatter** — `epics/cefi_master.md:631`:
  “the list below was seeded by the 2026-06-20 restructure and the script keeps it in sync from frontmatter” vs
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:22`: “parent_epic: cefi_master (frontmatter; priority: P0, created:
  2026-06-27)”
  - why: The epic claims its P0 'Assigned active plans' section is script-synced from every plan's parent_epic
    frontmatter, yet it lists only cefi_deribit_binance_futures_bundle_verification and
    cefi_ml_directional_continuous_live under P0 — omitting mvp_backfill_cefi_tick_v10_2026_06_27, which declares
    parent_epic: cefi_master

#### [P1] active/mvp_backfill_defi_onchain_v10_2026_06_27.md (intra-doc)

- finding ids: 42
- **DRIFT/Solana perp_funding genuine-data-date-count claim contradicted by the doc's own Progress Log** —
  `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:162`: “DRIFT VM already gone (SPOT, terminated); only 3 dates of
  genuine data (2025-01-09/10/11).” vs `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:845`: “DRIFT 2025-12-23
  COMPLETE — GCS parquet confirmed at 15:17 check; log uploader at 15:13 (490,816 bytes) captured”
  - why: The G1.5 resolution note (dated 2026-06-29, in the Todos section) states only 3 dates of genuine DRIFT data
    were ever captured (2025-01-09/10/11). But the same document's chronologically-earlier Progress Log (2026-06-28)
    records the DRIFT VM completing at least a 4th date, 2025-12-23, with ~1,720,513 real rows written

#### [P1] active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (intra-doc)

- finding ids: 168,169
- **intra-doc: M1-BREAKING work-unit checkbox never flipped despite the same doc's own GATE-0 log recording it ful** —
  `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:378`: “- [ ] [CODE] P0. **M1-BREAKING —
  migrate `live_websocket` objects/writers/readers → `live_<source>`** (next tranche, GATED on the M1/M2 foundation...)”
  vs `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:525-532`: “[x] ✅ [INFRA] P1.
  M1-BREAKING: 0 `live_websocket` writers; readers source-aware; LIVE_WEBSOCKET alias removed (0 refs fleet-wide).
  Shipped: execution-”
  - why: The '## Work units' section still tracks M1-BREAKING as an open `- [ ]` P0 todo, gated/not-started framing. But
    the same document's later '## GATE-0 CONCRETE EXECUTION PLAN + PROGRESS LOG' section (ticks 5-8) marks the identical
    item [x] done with commit SHAs across 7 repos and states 'rg "live_websocket|LIVE_WEBSOCKET
- **intra-doc: same stale-checkbox pattern repeats for M3, M4 and M5 work-units** —
  `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:343-355`: “- [ ] [DESIGN] P0. **M3 —
  per-shard available-sources registry...** / - [ ] [CODE] P0. **M4 — mode-contextual precedence**...” vs
  `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:514-524`: “[x] ✅ M3 UAC QG green
  (could_exist) — unified-api-contracts@d56b9cc2 ... [x] ✅ M4 UAC + batch-live-reconciliation-service QG green
  (select_for_mode) —”
  - why: Same document, same pattern as the M1-BREAKING finding: the top '## Work units' list still shows M3/M4/M5 as
    open `- [ ]` P0 items, while the GATE-0 Progress Log (ticks 1-8) records all three as [x] shipped with commit SHAs
    and passing tests/pw:L2. A reader who stops at the Work-units section (the doc's primary task li

#### [P1] active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md ↔ epics/mtds_mdps_master.md

- finding ids: 166,167
- **epic 'consolidation' banner vs a still-independent active P0 child plan under the same epic** —
  `epics/mtds_mdps_master.md:133-135`: “🔵 CONSOLIDATION 2026-06-26 — live MTDS/MDPS work now runs through 2 themed
  survivors... the done/largely-done MTDS/MDPS plans were archived and their ” vs
  `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:5,14,17,21`: “status: active;
  parent_epic: mtds_mdps_master; priority: P0; last_updated: 2026-06-27 (a day after the consolidation banner) — never
  archived or folde”
  - why: The epic's frontmatter summary and 2026-06-26 body banner both assert that ALL live MTDS/MDPS work now funnels
    through exactly 2 named survivor plans (M-1 data*completion_to_100, M-2 tech-debt). But
    pipeline_mode_source_batch_live_replay_standardisation_2026_06_05 — a P0, status:active plan declaring parent_epic:
    mtds*
- **epic's auto-populated child-plan index omits a plan that declares it as parent_epic** —
  `epics/mtds_mdps_master.md:713-714`: “_33 active plans declare `parent_epic: mtds_mdps_master` in their frontmatter
  (verified 2026-06-30). Workers pick up in priority order (P0 first)._” vs
  `active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:14`: “parent_epic: mtds_mdps_master”
  - why: The epic claims an auto-populated, script-verified (2026-06-30) exhaustive list of 33 plans declaring
    parent_epic: mtds_mdps_master, with the P0 section meant to be workers' first pickup.
    pipeline_mode_source_batch_live_replay_standardisation_2026_06_05 (priority P0, doc_type plan, parent_epic
    mtds_mdps_master, created

#### [P1] active/prediction_manifest_canonicalisation_2026_06_01.md (intra-doc)

- finding ids: 158,159,160
- **Status of the irreversible E4 full-VM migration apply** —
  `active/prediction_manifest_canonicalisation_2026_06_01.md:71-75`: “⏸️ E4 DRY-RUN DONE 2026-06-03 (VM auto-deleted) —
  full-run AWAITING OPERATOR REVIEW. ... do NOT fire it without operator sign-off on the dry plan.” vs
  `active/prediction_manifest_canonicalisation_2026_06_01.md:280-283`: “E4 — FULL-VM `--apply` RAN 2026-06-29 (verified
  slot audit 2026-07-10). The operator authorised + executed the full apply: `canonical-migration-predic”
  - why: The document's own top banner (never updated since 2026-06-03) tells any reader the full run is still pending
    operator sign-off and must not be fired, while the body (updated through 2026-07-11) confirms it was authorised,
    fired, and completed on 2026-06-29 with extensive follow-on cleanup. An agent trusting only the p
- **Which plan is the authoritative cross-AG coordinator/master for this plan** —
  `active/prediction_manifest_canonicalisation_2026_06_01.md:46`: “master: defi_manifest_canonicalisation_2026_06_01.md
  (cross-plan canonical-SSOT coordinator)” vs `active/prediction_manifest_canonicalisation_2026_06_01.md:51-52`:
  “cross-AG sequencing is owned by `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`.”
  - why: The plan's own frontmatter names defi_manifest_canonicalisation_2026_06_01.md as the coordinating master, and
    the body even repeats that framing at line 110 ("MASTER: defi_manifest_canonicalisation_2026_06_01.md §MASTER"), but
    every substantive gating decision from 2026-06-07 onward (G0-G4 gates, apply authorization, r
- **Completion state of the E7 manifest CF-verify gate** —
  `active/prediction_manifest_canonicalisation_2026_06_01.md:452-454`: “- [ ] [DATA] P0. E7 Verify — **OPEN: the
  post-`--apply` `_index` is NOT yet CF-GREEN** (MEASURED residual, slot audit 2026-07-10 on the live 760,300-r” vs
  `active/prediction_manifest_canonicalisation_2026_06_01.md:477-484`: “E7-ROOT — RESOLVED 2026-07-11: prediction
  \_index MANIFEST is CF-GREEN. ... \*\*Verified CF-state: CF-1 v9=100% · CF-2 asset_group=prediction 100% · CF-”
  - why: The E7 checklist item itself remains unchecked and its text still asserts the manifest is NOT CF-GREEN, but a
    later, checked item (E7-ROOT) in the same plan reports the same manifest is fully CF-GREEN as of 2026-07-11 (a later
    timestamp). The unflipped E7 checkbox is a done-but-unchecked drift that would mislead a scan

#### [P1] active/prediction_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 161
- **Epic's child-plan roster completeness vs actual plans declaring this parent_epic** —
  `epics/mtds_mdps_master.md:713-714`: “_33 active plans declare `parent_epic: mtds_mdps_master` in their frontmatter
  (verified 2026-06-30). Workers pick up in priority order (P0 first)._” vs
  `active/prediction_manifest_canonicalisation_2026_06_01.md:24,27`: “parent_epic: mtds_mdps_master ... priority: P0”
  - why: The epic claims a verified (2026-06-30) roster of 33 child plans and lists them by priority
    (P0/P1/P2/P3/Archived) in its 'Assigned active plans' section, but that section's actual entries are all
    May-2026-era plans (mostly archived) — it does not list prediction_manifest_canonicalisation_2026_06_01.md (nor its
    P0-prio

#### [P1] active/predictions_lookahead_and_reader_migration_2026_06_20.md ↔ epics/predictions_master.md

- finding ids: 234,235,236
- **Reader callsite migration status** — `epics/predictions_master.md:410`: “Reader-side migration (callsites:
  `data_type=BTC | ETH | ...` → canonical_question_group) | NOT started | same” vs
  `active/predictions_lookahead_and_reader_migration_2026_06_20.md:60`: “[x] [SCRIPT] P0. **Reader migration**: every
  callsite with `data_type=BTC|ETH|...` → ... ✅ — features-service@cf15b4eb”
  - why: Epic's Critical Path table (undated but part of the pre-restructure body, not covered by any SUPERSEDED banner)
    marks reader-side migration NOT started, while the child plan the epic itself dispatches this work to shows it fully
    shipped with a commit sha and last_updated 2026-06-27 (after the epic's own last_updated 20
- **Feature-compute lookahead-bias gate status** — `epics/predictions_master.md:411`: “Per-market lifecycle gating in
  features compute (`LookaheadBiasError` extension) | NOT started | same” vs
  `active/predictions_lookahead_and_reader_migration_2026_06_20.md:63`: “[x] [SCRIPT] P0. **Per-market
  `LookaheadBiasError` enforcement in feature compute**: ... ✅ — features-service@589a377b”
  - why: Epic's Critical Path table lists this as NOT started, but the dispatched child plan shows it shipped and
    checked off (features-service@589a377b) — same stale-table-vs-shipped-child-plan pattern as the reader-migration
    row.
- **Strategy archetype canonical_group config status** — `epics/predictions_master.md:412`: “Strategy-service prediction
  archetypes — canonical_group config | NOT started | same” vs
  `active/predictions_lookahead_and_reader_migration_2026_06_20.md:70`: “[x] [SCRIPT] P0. **Strategy-service prediction
  archetypes**: archetype configs reference `canonical_question_group` ... ✅ — strategy-service@5a41db69”
  - why: Epic table says NOT started; the child plan it routes this exact work to shows it shipped and ticked with a
    commit sha. Same stale-table pattern.

#### [P1] active/predictions_ml_walk_forward_and_arb_2026_06_20.md ↔ epics/predictions_master.md

- finding ids: 237
- **arb_calculator implementation status + owning-plan reference** — `epics/predictions_master.md:415`: “arb_calculator
  in FSS | scoped | `sports_predictions_e2e`” vs `active/predictions_ml_walk_forward_and_arb_2026_06_20.md:71`: “[x] ✅
  [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: ... — features-service@9347dbeb”
  - why: Epic table still says arb_calculator is merely 'scoped' and sources it to the archived/folded
    `sports_predictions_e2e` plan, while the actual owning child plan (predictions_ml_walk_forward_and_arb) shows it
    fully implemented and shipped with a commit sha.

#### [P1] active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md ↔ epics/predictions_master.md

- finding ids: 245
- **Is the UAC PREDICTION_GROUPS canonical-question-group registry still an empty placeholder, or already seeded/s** —
  `epics/predictions_master.md:885-886`: “**Temporary state**: UAC `PREDICTION_GROUPS = {}` empty registry until
  taxonomy seeded — CLAUDE.md "Temporary state" rule applies; this plan IS the na” vs
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:58-60`: “UAC `PREDICTION_GROUPS` registry seeding MUST
  include `OTHER` as a special-case entry from day one. ... ✅ — unified-api-contracts@306923a”
  - why: The epic's current (un-superseded) 'Anti-patterns + workspace-rule cross-references' section asserts
    PREDICTION_GROUPS is still the empty `{}` placeholder per the 'Temporary state' rule and names itself as the
    successor plan that will seed it. Its own P0 child plan (extracted the same day, 2026-06-20, last-updated 2026

#### [P1] active/repo_scripts_governance_audit_2026_06_18.md ↔ active/scripts_lifecycle_marker_rollout_2026_06_18.md

- finding ids: 71
- **Script lifecycle marker: does a `permanent` script omit `Delete-when` or carry `Delete-when: NA`?** —
  `active/repo_scripts_governance_audit_2026_06_18.md:117`: “# Delete-when: <concrete completion condition> # required
  for campaign/oneoff; permanent omits it” vs `active/scripts_lifecycle_marker_rollout_2026_06_18.md:45`:
  “`Delete-when:` is the only field whose _value_ is optional — but it must still be **present**, carrying **`NA`** when
  not needed (i.e. for `permanent`”
  - why: Same convention, same epic, same day of creation. The governance-audit doc's own quoted marker template still
    says permanent scripts OMIT Delete-when; the sibling rollout plan documents an explicit 2026-06-22 operator
    correction making Delete-when mandatory-and-present (NA for permanent) on every script, specifically s

#### [P1] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md ↔ active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md

- finding ids: 257
- **94-league fixtures/enrichment backfill ownership duplication** —
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:295`: “[ ] [DATA] P0. Fixtures
  backfill 2015→present, 94 leagues, no-force, season-window-gated.” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:90`: “[x] ✅ [DATA] P0. **Backfill FIXTURES
  2018→present** for the 94 leagues, season-aware smart-skip (gap-fill only).”
  - why: sports_canonical_universe's own [C]/[D] todos (94-league fixtures + enrichment backfill 2015→present,
    unchecked/open, P0/P1) describe the identical scope that sports_p2_history_apifootball_2015_to_present (created 3
    days later) claims and has substantially completed (8/9 todos, including the matching enrichment-backfil

#### [P1] active/sports_features_readiness_for_predictions_2026_06_20.md ↔ epics/sports_master.md

- finding ids: 260,275
- **sports_features_readiness_for_predictions child-plan status** — `epics/sports_master.md:1340-1344`: “###
  sports_features_readiness_for_predictions_2026_06_20 ... status: active · estimate: 1.2 cal AI-days” vs
  `active/sports_features_readiness_for_predictions_2026_06_20.md:9,45-46`: “status: complete ... Status-flip note
  (2026-07-10): both P0/P1 todos confirmed [x] ... Flipped status: active -> complete.”
  - why: The epic's 'Assigned active plans / P0' section still lists this child plan as active and awaiting work, but
    the plan's own frontmatter+body record it as complete since 2026-07-10 -- a live epic-vs-child status mismatch that
    could cause re-dispatch of already-finished work.
- **Status of the sports_features_readiness_for_predictions child plan** — `epics/sports_master.md:1340-1344`: “###
  [`sports_features_readiness_for_predictions_2026_06_20`]... **status**: active · **estimate**: 1.2 cal AI-days (class:
  infra). Sports-side feeder ” vs `active/sports_features_readiness_for_predictions_2026_06_20.md:9`: “status: complete”
  - why: The epic's 'Assigned active plans' table still lists this child plan as status: active, but the plan's own
    frontmatter was flipped to status: complete on 2026-07-10 with a body note confirming both P0/P1 todos done with
    cited evidence. Epic index drift makes this look like open work when it is finished.

#### [P1] active/sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md ↔ active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md

- finding ids: 282
- **Phase-0 (sourcing+honest-coverage) child-plan status: coordinator burn-down table vs the plan's own completion** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:163`: “| P0 sourcing+honest-coverage correctness |
  0 | R1,R5 | — | ⬜ not started |” vs `active/sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md:90`:
  “ODDS forward dry-run = **0 phantom** (6,813 captured ODDS rows, ALL have GCS parquets)... Code restored:
  instruments-service@3d4f1a1+@edebc6b.”
  - why: The coordinator's 'Child-plan status (flip as they land)' burn-down table still marks P0 as '⬜ not started',
    but P0's own plan (same 2026-06-27 creation date) has all 5 todos checked [x] with dated 2026-06-29 verification
    evidence (understat-404 fix shipped, path-shape gap closed, footystats-ODDS restored+re-verified,

#### [P1] active/sports_p1_golden_window_apifootball_2026_06_27.md ↔ active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md

- finding ids: 283
- **P1a (golden-window API-Football) child-plan status: coordinator burn-down table vs the plan's own all-done ban** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:164`: “| P1a golden-window apifootball | 1 | R1 |
  P0 | ⬜ not started |” vs `active/sports_p1_golden_window_apifootball_2026_06_27.md:32`: “✅ FIXTURES BACKFILL
  COMPLETE — af-backfill-20260627-182057 SPOT ... 2903/2904 shards resolved via re-fetch ... Gate ALL PASS:
  attempted_failed=0, unat”
  - why: The coordinator (read in batch A) lists P1a as '⬜ not started', but P1a's own doc (read in batch B) opens with
    a FIXTURES-BACKFILL-COMPLETE banner and has all 5 todos [x] checked with a Gate-ALL-PASS result. The coordinator's
    DAG status table was never refreshed to reflect P1a's real (complete) state, a stale cross-doc

#### [P1] active/sports_p1_golden_window_mtds_odds_2026_06_27.md ↔ active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md

- finding ids: 285
- **P1c (golden-window MTDS odds) child-plan status: coordinator burn-down table vs the plan's own full-execution-** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:166`: “| P1c golden-window MTDS odds | 1 | R1,R5 |
  P0 | ⬜ not started |” vs `active/sports_p1_golden_window_mtds_odds_2026_06_27.md:97`: “✅ MTDS sports odds reads 100%
  honest coverage on 2025-09-01..2025-11-30 for the odds-api-covered subset of the 94 universe.”
  - why: The coordinator (batch A) lists P1c as '⬜ not started', but P1c's own doc (batch B) has all 4 todos checked
    [x] done and its Full-execution criterion explicitly marked ✅ met for the golden window. This is the third of three
    P1 lanes (P1a/P1b/P1c) whose real completed state the coordinator's DAG table fails to reflect —

#### [P1] active/sports_p1_golden_window_reference_sources_2026_06_27.md ↔ active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md

- finding ids: 284
- **P1b (golden-window reference sources) child-plan status: coordinator burn-down table vs all-6-todos-done body** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:165`: “| P1b golden-window reference sources | 1 |
  R1,R3 | P0 | ⬜ not started |” vs `active/sports_p1_golden_window_reference_sources_2026_06_27.md:105`: “- [x] ✅
  [DATA] P1. **No-blank-reason invariant** across all reference sources on the window — DONE slot-2 2026-06-28.”
  - why: The coordinator (batch A) lists P1b as '⬜ not started', but P1b's own doc (batch B) has all 6 todos checked
    [x] done (weather, SFI, transfermarkt, understat, footystats, no-blank-reason invariant), the last one explicitly
    dated DONE 2026-06-28 — a full day before the coordinator doc's own last_updated. Same stale-DAG-i

#### [P1] active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md (intra-doc)

- finding ids: 248,250
- **api_football FIXTURES coverage_start: 2015 vs 2018 (same doc)** —
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:42`: “**FIXTURES**: `coverage_start = 2015-01-01`
  → backfill 2015→present, all 94 leagues, season-aware” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:218-220`: “UAC fix shipped:
  `SOURCE_COVERAGE_START["api_football"]` changed from `date(2015, 1, 1)` → `date(2018, 1, 1)`. 2015-2017 cells are now
  `EXPECTED_PRE_S”
  - why: The plan's own Scope table (written 2026-06-27, never edited afterward) still states the FIXTURES
    coverage_start as 2015-01-01, but the plan's own Todo #2 diagnosis and shipped code (same session) permanently moved
    the real coverage floor to 2018-01-01 (subscription-floor verdict), typing 2015-2017 as honest-absence fo
- **Todo #5 (enrichment+core backfill) checked done vs its own Gate repeatedly failing for weeks** —
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:99-102`: “[x] [DATA] P0. Backfill enrichment +
  core 2020-06→present within coverage windows... Gate: full-history query → each enrichment/core data_type pending” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:899-901`: “Total EU: 415,064 (up from 409,201 in
  session 18 ... Gate: FAILS — same structural blocker as sessions 15–18.”
  - why: Todo #5 is marked [x] ✅ done, but its own stated Gate ('pending_fetch == 0 within coverage window') is shown
    FAILING in no fewer than ~19 subsequent progress-log sessions (2026-06-28 through 2026-07-06), with the pending
    count actually growing to 415,064+ rows across 7 enrichment data_types (TEAMS alone ~194K). A separ

#### [P1] active/tradfi_manifest_canonicalisation_2026_06_01.md (intra-doc)

- finding ids: 164
- **Pre-migration drain completion status (intra-doc)** — `active/tradfi_manifest_canonicalisation_2026_06_01.md:346`:
  “- [ ] [DATA] P0. E3 Confirm tradfi writer drained; snapshot `tradfi-prd/_index` (pre-migration drain per
  tradfi_massive -029).” vs `active/tradfi_manifest_canonicalisation_2026_06_01.md:1370`: “IS Massive backfill→catalogue
  regen + pre-migration drain (already EXECUTED 2026-06-08 per the coordinator).”
  - why: The doc's own E3 execution-checklist item confirming the tradfi writer drain + pre-migration snapshot remains
    an open, unchecked `- [ ]` P0 todo (never flipped to done), while the document's later session-4 'authoritative
    verdict' (dated the same day, 2026-06-08) asserts the pre-migration drain was already executed by

#### [P1] active/tradfi_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 163
- **Epic child-plan roster completeness vs actual active P0 child plan** — `epics/mtds_mdps_master.md:713`: “\_33 active
  plans declare `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30). ... Auto-populated by
  `scripts/plans/populate_epi”  vs  `active/tradfi_manifest_canonicalisation_2026_06_01.md:5-17`: “status: active ...
  parent_epic: mtds_mdps_master ... priority: P0”
  - why: The epic's 'Assigned active plans' section claims an exhaustive, auto-populated (verified 2026-06-30) list of
    every active plan declaring parent_epic:mtds_mdps_master, enumerated under P0/P1/P2/P3/Archived. This plan
    (status:active, priority:P0, parent_epic:mtds_mdps_master, last_updated 2026-06-27) does not appear any

#### [P1] active/utl_uac_reuse_consolidation_remediation_2026_06_10.md ↔ epics/infrastructure_master.md

- finding ids: 60
- **Epic's auto-populated child-plan count is stale/wrong** — `466-467`: “\_1 active plans declare
  `parent_epic: infrastructure_master` in their frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.”  vs  `14`: “parent_epic: infrastructure_master”
  - why: The epic asserts only 1 active plan declares parent_epic: infrastructure_master, but a direct grep of
    plans/active for `^parent_epic: infrastructure_master` returns 44 hits, including all three docs in this batch
    (utl_uac_reuse_consolidation_remediation status:active, cefi_layer1_denominator_gaps status:open, v1_enumer

#### [P1] epics/README.md ↔ epics/plan_hygiene_master.md

- finding ids: 10001,10004
- **epic-registry completeness** — `epics/README.md:164,166-187,320-324`: “## 20 epics in 5 tiers ... Cross-reference
  verification — 2026-05-22 ... No broken links found. ... No changes required to fix broken links.” vs
  `epics/plan_hygiene_master.md:9,17,19-21`: “status: active ... created: 2026-05-21 ... tier: L5 priority: P1
  assigned_vm: planning”
  - why: README.md declares itself the epic-flow SSOT and its canonical 20-row table (lines 168-187) enumerates every
    epic + assigned VM; a dated 'Cross-reference verification — 2026-05-22' section explicitly certifies 'No broken
    links found... No changes required.' Yet plan_hygiene_master.md is a fully-formed active epic (stat
- **epic count self-citation drift** — `epics/README.md:164`: “## 20 epics in 5 tiers” vs
  `epics/plan_hygiene_master.md:52`: “`plans/epics/README.md` | Epic-flow SSOT — 19 epics × 5 tiers × 10-VM topology |”
  - why: plan_hygiene_master.md's own 'Codex SSOTs' table -- the table whose entire job is to keep hygiene/SSOT
    references accurate -- describes README.md as '19 epics x 5 tiers' while README.md's live header (line 164) says '20
    epics in 5 tiers'. Ironic given plan_hygiene_master is the epic chartered to catch exactly this clas

#### [P1] epics/defi_master.md ↔ epics/features_and_ml_master.md

- finding ids: 313
- **available_at_lookahead_bias_completion_2026_05_08 coordinator plan status** — `epics/features_and_ml_master.md:789`:
  “**Coordinator:**
  [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)”
  vs `epics/defi_master.md:1443`: “this block is tracked in
  [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md”
  - why: features_and_ml_master cites this plan as living under plans/active/ and gates two open P0 todos (UAC
    FEATURE_REQUIRED_INPUTS expansion; Tab-12 wire-in) on its Phase 0/1/4 progress, treating it as an in-flight
    coordinator. defi_master (edited later, 2026-06-20) correctly points to plans/archive/2026_05/ for the same pl

#### [P1] epics/strategy_master.md (intra-doc)

- finding ids: 297,290,294,333,335
- **epic links the QG-sweep plan into an archive/ path yet its own body still labels it ACTIVE with a live freeze ** —
  `epics/strategy_master.md:104`:
  “[`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — strategy-service cluster” vs
  `epics/strategy_master.md:106`: “**status**: 🟠 ACTIVE — QG sweep for strategy-service (11 ruff errors, **SURFACE ONLY
  — LOGIC FREEZE in effect**). Only”
  - why: The link target lives under plans/archive/2026_05/, implying the plan itself is archived/done, but the epic's
    own status line still reads 🟠 ACTIVE with an unresolved LOGIC FREEZE warning and no unfreeze banner — a stale
    directive that reads as currently authoritative (class d), which is exactly the ambiguity feeding th
- **Epic's own summary/scope text (53) disagrees with its own F-34 body text (55) for the archetype enum count** —
  `epics/strategy_master.md:6`: “L2 everlasting epic owning strategy-service post-2026-05-19 consolidation (engine +
  portfolio_allocator + risk + position + pnl + 53 archetype engines” vs `epics/strategy_master.md:142`: “55-member
  `StrategyArchetype` enum”
  - why: Within the same document, the epic's top-level summary and 'Scope inherited' section both assert '53
    archetypes' as the closed-set taxonomy count (also epics/strategy_master.md:72, :81), while its own F-34 todo (added
    2026-06-01, still open) explicitly states the real enum has 55 members and that '53' is the stale figu
- **archetype count: epic states 53 in its own Scope section but 55 in its own AUDIT-03 section** —
  `epics/strategy_master.md:72`: “**53 archetypes** per `codex/09-strategy/architecture-v2/archetypes/` — closed-set
  strategy taxonomy.” vs `epics/strategy_master.md:142`: “55-member `StrategyArchetype` enum). In `factory.py`, replace
  the bare `KeyError`”
  - why: Same document, no banner reconciling the two counts; the epic's headline scope claims a 53-member closed-set
    taxonomy while its own P1 AUDIT-03 F-34 item (operator decision 2026-06-01) cites a 55-member enum as ground truth —
    an intra-doc factual inconsistency (class d).
- **Archetype taxonomy count SSOT (53 vs 55 vs 28-implemented)** — `epics/strategy_master.md:72`: “53 archetypes per
  `codex/09-strategy/architecture-v2/archetypes/` — closed-set strategy taxonomy.” vs
  `epics/strategy_master.md:140-144`: “the 28 implemented archetype engines are the intended May-23 rollout subset (NOT
  a regression vs the 55-member `StrategyArchetype` enum)... fix the st”
  - why: The epic's own scope/summary section asserts '53 archetype engines' / '53 archetypes' as the owned closed-set,
    while its own P1 backlog item (F-34, operator decision 2026-06-01) states that '53' is a stale count that should be
    '55' (with only 28 actually implemented for the May-23 rollout). The doc has not been correct
- (+1 more findings on this pair, see findings archive)

#### [P1] plans/active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md ↔ plans/active/task_template.md

- finding ids: 380
- **plan_order / sequential:true dispatch-ordering semantics** — `plans/active/task_template.md:93,127-131`: “#
  sequential: true # optional — STRICT serial: task N waits for N-1 done [ROLLING OUT — see §4] ... \_[ROLLING OUT:
  `plan_order`. Today same-p” vs `plans/active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:328-338`: “[x]
  [BACKEND] P0. Execution order — add `plan_order`... — ✅ DONE ao@ff6100ad ... [x] [BACKEND] P1. `sequential: true`
  plan flag (F, mode b) ... — ✅ DO”
  - why: task_template.md (last_updated 2026-07-07, the mandatory 'read this FIRST' authoring doc) tells plan authors
    that `plan_order` and `sequential: true` are unshipped ('ROLLING OUT') and to fall back to P-levels/explicit
    prereqs. The same-dated ao_dispatch_correctness_regen_reconcile plan records both features as shipped

#### [P1] plans/active/data_completion_to_100_all_ag_2026_06_21.md ↔ plans/epics/client_isolation_and_governance_master.md

- finding ids: 10009
- **Phase E.3 Intra-client RebalanceCoordinator — done vs pending** —
  `plans/epics/client_isolation_and_governance_master.md:122-125`: “- [ ] [AGENT] P2. **Phase E.3 — Intra-client
  RebalanceCoordinator**: intra-client multi-portfolio + intra-client multi-wallet ONLY; cross-client fund ” vs
  `plans/active/data_completion_to_100_all_ag_2026_06_21.md:1279-1301`: “[x] SHIPPED 2026-06-23 (autonomous) —
  `IntraClientRebalanceCoordinator` landed `strategy-service@1450019e` ... [x] Wire `IntraClientRebalanceCoordinat”
  - why: The epic (status: active, last_updated 2026-07-08 — i.e. touched weeks AFTER the work shipped) still lists
    Phase E.3 as an unchecked P2 todo with no owning plan, instructing a picker-up to 'Create active plan
    intra_client_rebalance_coordinator_2026_06_01.md' — while an active sibling plan shows the exact same deliverab

#### [P1] plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md ↔ plans/epics/orchestrator_master.md

- finding ids: 379
- **assigned_vm / VM-topology semantics** — `plans/epics/orchestrator_master.md:64-71`: “**Owns**: agent-orchestrator
  multi-VM stack (central/orchestrator VM `planning` + human planning VM `human-planning` + 9 epic VMs...) **Assigned
  VM**:” vs `plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-210`: “Role-based dispatch —
  NO epic VM (single-VM architecture, 2026-06-27). Each child carries `assigned_vm: NA` ... (epic VMs deprecated per
  CLAUDE.md; th”
  - why: orchestrator_master.md is status:active, locked_by:live-defi-rollout, last_updated 2026-05-21, and its body
    still asserts a live 9-epic-VM fleet topology (assigned_vm: vm-orchestrator) as current fact, with only a narrow
    'Partial-supersede notice' scoped to strict-matching semantics (explicitly 'NOT a wholesale superse

#### [P2] active/INDEX.md (intra-doc)

- finding ids: 3,4
- **'Cross-cutting SSOT (priority) — Read first' section listing plans it itself labels ARCHIVED** —
  `active/INDEX.md:12`: “**Read first** when touching venue routing, buckets, or market-data category maps:” vs
  `active/INDEX.md:38`: “— **Bundled (ARCHIVED)** overnight GCS migration\*\* that walks every parquet ONCE (millions
  across asset_groups) and”
  - why: The section header frames its bullets as priority 'Read first' authoritative SSOT material for anyone touching
    venue routing/buckets/market-data maps, yet 3 of its ~6 bullets (gcs_migration_bundle L37-46,
    deployment_ui_lifecycle_tabs L56-75, hard_schema_enforcement L77-86) are explicitly marked '(ARCHIVED)' inline and
- **INDEX.md's own 'Last Updated' header vs its body content dates** — `active/INDEX.md:3`: “**Last Updated:**
  2026-05-08 (live-pipeline activation triple — features-repo consolidation + live-pipeline + GCS” vs
  `active/INDEX.md:192`: “**is-daily-enum capture heal + consolidator fix — AO-ready (2026-07-07; born draft):**”
  - why: The file's declared 'Last Updated' metadata is 2026-05-08, but the body contains entries dated well after that
    (prediction_capture_incident_remediation 2026-07-06 at L187-191, is_daily_enum_capture_heal 2026-07-07 at L192-196),
    proving the header timestamp is stale/wrong relative to the document's own content — index m

#### [P2] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md ↔ active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md

- finding ids: 220
- **Dangling codex SSOT path cited as authoritative by three docs, explicitly declared non-existent by a fourth** —
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:265`:
  “`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + regen + ingestion contract.” vs
  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:458-461`:
  “`/codex/04-architecture/agent-orchestrator-overview.md` — worker lifecycle + loops (update for the new boot
  mechanism; PATH CORRECTED 2026-07-10 — the ”
  - why: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` is listed as a live, to-be-read SSOT in
    the 07-07 plan (L265) and the 07-09 plan (L153), and as a related doc in the ao_fleet_stall issue (L26). The 07-10
    plan, auditing the same cluster one to three days later, explicitly states this exact path is

#### [P2] active/ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md ↔ active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md

- finding ids: 351
- **Codex SSOT path for the AO slot/worker model: cited as a live doc vs declared non-existent** —
  `active/ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md:153-154`:
  “`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` +
  `/codex/04-architecture/agent-orchestrator-overview.md` — slot/worker lifecycl” vs
  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:354-356`:
  “...local-slot-host-symmetric-worker-model.md — liveness triggers + the slot/worker model (replaces the non-existent
  `single-vm-architecture.md` cite)”
  - why: The 2026-07-09 plan (status active, several todos still open) cites
    `agent-orchestrator-single-vm-architecture.md` as a load-bearing codex SSOT for slot/worker lifecycle. The next
    day's active audit plan on the same parent epic (`orchestrator_master`), after directly auditing the AO surfaces,
    states that exact path is

#### [P2] active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md ↔ active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md

- finding ids: 225
- **Existence of /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md** —
  `active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md:26`: “related: [...,
  /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md]” vs
  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:457-461`: “PATH CORRECTED 2026-07-10 — the plan
  previously cited a non-existent `12-agent-workflow/` location ... replaces the non-existent `single-vm-architectu”
  - why: ao_fleet_stall (status open, P0, unrevised since 2026-07-07) still lists this exact path as a live related-doc
    reference, while ao_worker_lifecycle_audit (2026-07-10) explicitly declares this same path non-existent and replaces
    it with two different codex docs. An agent following the still-open P0 fleet-stall doc's ref

#### [P2] active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md ↔ active/work_split_2026_05_22_ikenna.md

- finding ids: 221
- **A still-'active' 7-week-old work-split plan instructs dispatch onto named per-epic VMs (vm-prediction, vm-cros** —
  `active/work_split_2026_05_22_ikenna.md:5,186-189`: “status: active ... VM Dispatches (2026-05-22): vm-prediction —
  `predictions_master` epic. Spawned: slot 1 (main-orchestrator)... Epic:
  `plans/epics/pr”  vs  `active/ao_worker_lifecycle_audit_and_corrections_2026_07_10.md:109`: “Predates the single-VM
  pivot”
  - why: work_split_2026_05_22_ikenna.md remains status: active with no archival/banner and prescribes spawning
    main-orchestrators onto named epic VMs (vm-prediction, vm-cross-cutting) — the exact multi-VM-fleet framing the
    07-10 audit says predates the since-completed single-VM pivot. An agent that opened this still-active pla

#### [P2] active/bucket_iam_write_protection_per_tier_2026_06_09.md ↔ epics/infrastructure_master.md

- finding ids: 84
- **epic's auto-populated active-child-plan count is stale** — `epics/infrastructure_master.md:466`: “\_1 active plans
  declare `parent_epic: infrastructure_master` in their frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.”  vs  `active/bucket_iam_write_protection_per_tier_2026_06_09.md:19`:
  “parent_epic: infrastructure_master”
  - why: The epic's auto-populated section claims only 1 active plan carries parent_epic: infrastructure_master, but
    this single batch shows at least 2 status:active plans (bucket_iam_write_protection_per_tier_2026_06_09.md,
    ui_build_warm_cache_2026_06_17.md) plus ~14 open issue docs all declaring that same parent_epic — the co

#### [P2] active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (intra-doc)

- finding ids: 177,178
- **TradFi L3 canonicalisation owner — two different plan names for the same gate, same doc** —
  `active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:135-136`: “"tradfi (71 legacy-only) / sports (0):
  `tradfi_manifest_canonicalisation` / `sports_manifest_canonicalisation` FILED ... All four non-DeFi L3 plans ow” vs
  `active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:370-373`: “"L3 owners:
  defi=`defi_manifest_canonicalisation` §C · prediction=`prediction_manifest_canonicalisation_2026_06_01` ·
  cefi=`cefi_manifest_canonicalisa”
  - why: The L3 section names `tradfi_manifest_canonicalisation` as the plan owning TradFi's canonical \_index rebuild,
    but the later Phase-7 L6-decommission owner table names a different plan, `tradfi_massive_dual_source`, for the
    exact same gate (and even flags an internal conflict tag "master CONFLICT-2"). An agent checking w
- **CeFi gap-fill ownership — claimed owned vs claimed unowned, same doc** —
  `active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:132-134`: “"cefi (data-state: FULL re-canon, not
  838): ✅ FILED + BUILT (slot-3 2026-06-01) — `cefi_manifest_canonicalisation_2026_06_01.md` ... Owns the cefi
  `_i”  vs  `active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:169`: “"Newly-exposed gaps to FILE (no
  current owner): (1) prediction_manifest_canonicalisation ... (2) cefi 838-cell gap-fill owner."”
  - why: The L3 section states CeFi's canonicalisation work is already FILED+BUILT with a named owning plan, but the
    same document's "Newly-exposed gaps to FILE (no current owner)" list still carries "cefi 838-cell gap-fill owner" as
    an unresolved ownership gap, contradicting the earlier claim that CeFi is owned. Left unclear w

#### [P2] active/canonical_id_builder_retrofit_checklist_2026_07_08.md ↔ active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md

- finding ids: 127
- **Whether the AAVEV3-OPTIMISM misspelled-venue duplicate is still a live, unaddressed data bug** —
  `active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md:158-160`:
  “AAVE_V3-OPTIMISM has a second, misspelled venue-token duplicate (`AAVEV3-OPTIMISM`, missing the underscore) carrying
  4 real rows invisible to anything” vs `active/canonical_id_builder_retrofit_checklist_2026_07_08.md:151-154`: “Retire
  the misspelled `AAVEV3-OPTIMISM` venue-token duplicate (finding 5) — DONE, fixed by a concurrent sibling agent the
  same session ... 0 ghost row”
  - why: Both docs are dated 2026-07-08. adapter_findings' own Progress Log entry cites AAVEV3-OPTIMISM (added 'later
    still' the same day) as a current, unresolved illustration of ad hoc ID construction with no note that a sibling
    agent had already fixed it that same session; canonical_id_builder_retrofit_checklist explicitly d

#### [P2] active/cefi_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 152
- **Epic's auto-populated child-plan roster omits an active P0 child plan** — `epics/mtds_mdps_master.md:713-714`: “\_33
  active plans declare `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30). Workers pick up in
  priority order (P0 first). Aut” vs `active/cefi_manifest_canonicalisation_2026_06_01.md:14-17`: “parent_epic:
  mtds_mdps_master ... priority: P0”
  - why: cefi_manifest_canonicalisation_2026_06_01.md declares parent_epic: mtds_mdps_master and priority: P0 in its own
    frontmatter, yet the epic's 'Assigned active plans' section (P0/P1/P2/P3/Archived breakdown, lines ~716-821) never
    names this plan anywhere despite claiming to auto-populate all 33 declared children. An orche

#### [P2] active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md ↔ active/issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md

- finding ids: 348
- **Which plan currently owns the quickmerge / QUICKMERGE_BLOCKED contract, and is the open quickmerge bug tracked** —
  `active/issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md:68`: “Owner: whoever owns
  `cicd_quality_gates_2026_06_18.md` (the structured-quickmerge / QUICKMERGE_BLOCKED contract lives there).” vs
  `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:9`: “This plan is the single SSOT for the simplified pipeline; it
  supersedes the WS-L plan family and resolves the promotion-stall issue docs.”
  - why: doc_a (status: open, last_updated 2026-06-27) names `cicd_quality_gates_2026_06_18.md` as the current 'owner'
    of the quickmerge/QUICKMERGE_BLOCKED contract for its still-open P1 bug fix. That named doc had already been
    superseded on 2026-06-24 (into cicd_consolidated_remaining) three days BEFORE doc_a's own last_update

#### [P2] active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md ↔ epics/infrastructure_master.md

- finding ids: 76
- **Epic's auto-populated "Assigned active plans" index vs the real set of active/open child plans** —
  `epics/infrastructure_master.md:466`: “\_1 active plans declare `parent_epic: infrastructure_master` in their
  frontmatter. Workers pick up in priority order (P0 first).” vs
  `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:23`: “parent_epic: infrastructure_master”
  - why: The epic's auto-populated index claims exactly 1 active child plan and then lists only ARCHIVED plans under
    every priority bucket (P0/P1/P2). But numerous currently active/open docs in this same cluster declare
    `parent_epic: infrastructure_master` with `status: active` or `status: open` (cicd_mvp_ldr_to_main_pipeline,

#### [P2] active/citadel_paper_batch_live_reconciliation_2026_06_19.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 14
- **stale auto-generated count of plans assigned to the epic** — `epics/batch_live_symmetry_master.md:70`: “\_2 active
  plans declare `parent_epic: batch_live_symmetry_master` in their frontmatter. Workers pick up in priority order (P0
  first). Auto-populated..” vs `active/citadel_paper_batch_live_reconciliation_2026_06_19.md:14`: “parent_epic:
  batch_live_symmetry_master”
  - why: The epic's auto-populated 'Assigned active plans' note claims only 2 active plans declare this parent*epic, but
    a repo-wide grep for `^parent_epic: batch_live_symmetry_master` finds at least 4 status:active plans (this citadel
    plan, features_no_lookahead_reaggregation_guard_2026_06_28.md, honest_coverage_smoke_harness*

#### [P2] active/coinbase_bare_name_migration_2026_07_06.md ↔ active/issues/instruments_remaining_work_audit_2026_07_10.md

- finding ids: 105
- **Coinbase bare-name migration plan's dispatch status: draft/unstarted vs active/fully executed** —
  `active/issues/instruments_remaining_work_audit_2026_07_10.md:461-463`: “**COINBASE bare-name UAC removal + downstream
  caller migration** (`status: draft`, not dispatched) ... awaiting operator flip to `active`; all steps u” vs
  `active/coinbase_bare_name_migration_2026_07_06.md:21,74-77`: “status: active ... Dispatched for execution 2026-07-10
  ... Executing S0-S7 in order below.”
  - why: The audit's §3 SSOT synthesis section still lists the migration plan as an un-dispatched draft with all steps
    unchecked, but the migration plan itself (frontmatter + banner) shows status:active, dispatched 2026-07-10, with all
    S0-S7 steps checked done. The SAME audit doc's own later Progress Log (operator decision #3,

#### [P2] active/coinbase_bare_name_migration_2026_07_06.md ↔ epics/instruments_master.md

- finding ids: 106
- **Epic's auto-populated child-plan count (3) vs actual number of active plans declaring this parent_epic** —
  `epics/instruments_master.md:422-424`: “_3 active plans declare `parent_epic: instruments_master` in their
  frontmatter. Workers pick up in priority order (P0 first). Auto-populated..._” vs
  `active/coinbase_bare_name_migration_2026_07_06.md:47`: “parent_epic: instruments_master”
  - why: The epic body claims exactly 3 active plans declare parent_epic: instruments_master (and only lists 2 by name,
    I-1/I-2, in the P0 section). But this batch alone shows at least 2 more active plans with that exact frontmatter
    key/value — coinbase_bare_name_migration_2026_07_06.md:47 and tradfi_v9_stage1_finish_2026_07_06

#### [P2] active/coinbase_bare_name_migration_execution_service_2026_07_10.md ↔ epics/instruments_master.md

- finding ids: 123
- **Valid assigned_vm values for plans/epics in this cluster** — `epics/instruments_master.md:35`: “assigned_vm:
  vm-cefi” vs `active/coinbase_bare_name_migration_execution_service_2026_07_10.md:41`: “`assigned_vm: NA` / LOCAL track
  (default per CLAUDE.md ... the operator can flip `assigned_vm: planning` + `status: active` if they want the fleet to
  ”
  - why: A child plan in the same epic cluster, authored 2026-07-10, explicitly documents that assigned_vm must be one
    of {NA, planning} per the current workspace convention (multi-VM dispatch deprecated 2026-06-27) — yet the parent
    epic hub for this exact cluster (last_updated 2026-07-08, after the deprecation) still carries a

#### [P2] active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md ↔ epics/features_and_ml_master.md

- finding ids: 58
- **epic 'Assigned active plans' body roster omits multiple frontmatter-declared child plans** —
  `epics/features_and_ml_master.md:26,44`: “related: [../active/features_read_book_columns_not_snapshots_2026_06_28.md,
  ...] ... related_plans: [../active/features_read_book_columns_not_snapshot” vs
  `active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md:14`: “parent_epic: features_and_ml_master”
  - why: features_read_book_columns_not_snapshots is named in the epic's own frontmatter related/related_plans lists,
    yet is absent from the epic's auto-generated 'Assigned active plans' body roster (which claims to be the exhaustive
    list of plans declaring this parent_epic). Two further plans in this batch — bigquery_feature_m

#### [P2] active/consolidator_throughput_backlog_monitor_2026_07_09.md ↔ epics/observability_master.md

- finding ids: 205
- **manifest-consolidator freshness/staleness threshold rule** — `epics/observability_master.md:94`: “Manifest
  consolidator freshness alerts; silence > 120s → CRITICAL” vs
  `active/consolidator_throughput_backlog_monitor_2026_07_09.md:106`: “the endpoint judged every AG against a uniform
  120s budget → cefi `degraded` ~60% of the time. Fix: `_AG_STALENESS_BUDGET_SEC`/`_budget_for` — cefi = ”
  - why: The epic's own SSOT-pointer table still summarizes a universal 120s silence→CRITICAL rule for the manifest
    consolidator, but a shipped fix in a child plan proved that rule wrong for at least the cefi asset_group (needs an
    86400s budget), and the plan's own codex-update todo for manifest-consolidator-ssot.md is still un

#### [P2] active/data_eng_role_vertical_pilot_2026_06_25.md ↔ active/task_template.md

- finding ids: 9
- **Invalid track pairing: NA+orchestrator-agent is neither the LOCAL nor AO-DISPATCHED combo defined by the templ** —
  `active/task_template.md:50`: “assigned_vm | NA | ... execution_scope | local-only | orchestrator-agent (LOCAL pairs
  NA+local-only; AO-DISPATCHED pairs planning+orchestrator-agent)” vs
  `active/data_eng_role_vertical_pilot_2026_06_25.md:16`: “assigned_vm: NA ... execution_scope: orchestrator-agent”
  - why: task_template.md defines exactly two valid (assigned_vm, execution_scope) pairings -- (NA, local-only) for
    human plans and (planning, orchestrator-agent) for fleet-dispatched plans -- but data_eng_role_vertical_pilot.md
    carries the invalid mixed pairing (NA, orchestrator-agent), a residue of the pre-2026-06-27 harsh_pc

#### [P2] active/data_pipeline_hardening_self_monitoring_2026_06_22.md ↔ epics/observability_master.md

- finding ids: 193
- **Epic body completeness vs. its own auto-populated child-plan roster** — `epics/observability_master.md:99-100`:
  “\_13 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order
  (P0 first). Auto-populated by `sc”  vs  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:14`:
  “parent_epic: observability_master”
  - why: This plan's frontmatter declares parent_epic: observability_master (created 2026-06-22, ~22 cal AI-days of
    work, still active as of 2026-06-27), but the epic (last_updated 2026-06-19) has no P0/P1/P2/P3 entry, no link, and
    no mention of this plan anywhere in its body — a worker scanning the epic for its assigned active

#### [P2] active/data_status_tab_and_downloads_remediation_2026_06_16.md ↔ epics/deployment_and_user_management_master.md

- finding ids: 49
- **Epic's active-plan index is stale / undercounts real active children** —
  `epics/deployment_and_user_management_master.md:72`: “_1 active plans declare
  `parent_epic: deployment_and_user_management_master` in their frontmatter._” vs
  `active/data_status_tab_and_downloads_remediation_2026_06_16.md:14`: “parent_epic:
  deployment_and_user_management_master”
  - why: The epic's auto-populated 'Assigned active plans' section claims only 1 active plan declares this parent_epic,
    and its P0/P1/P3 priority blocks are all '(no plans currently assigned at this priority)' with only two ARCHIVED
    items listed under P2. But this batch alone shows at least this plan (status: active, priority P

#### [P2] active/defi_manifest_canonicalisation_2026_06_01.md ↔ epics/mtds_mdps_master.md

- finding ids: 154
- **Epic plan-roster completeness / index drift** — `epics/mtds_mdps_master.md:713-714`: “\_33 active plans declare
  `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30)... Auto-populated by
  scripts/plans/populate_epic_b” vs `active/defi_manifest_canonicalisation_2026_06_01.md:19-22`: “parent_epic:
  mtds_mdps_master assigned_vm: NA execution_scope: orchestrator-agent priority: P0”
  - why: This is a 174KB, P0, `umbrella: true` DeFi plan locked since 2026-05-21 and last updated 2026-06-27, declaring
    `parent_epic: mtds_mdps_master` in its own frontmatter — yet the epic's `related`/`related_plans` arrays, its P0-P3
    'Assigned active plans' roster, and its Phase/slot-dispatch tables never mention `defi_manife

#### [P2] active/honest_coverage_v2_instrument_denominator_2026_06_28.md ↔ epics/infrastructure_master.md

- finding ids: 68
- **epic's auto-populated child-plan count is stale/undercounted** — `epics/infrastructure_master.md:466`: “_1 active
  plans declare `parent_epic: infrastructure_master` in their frontmatter._” vs
  `active/honest_coverage_v2_instrument_denominator_2026_06_28.md:36`: “parent_epic: infrastructure_master”
  - why: The epic's auto-generated 'Assigned active plans' section claims only 1 active plan declares parent_epic:
    infrastructure_master, but at least 4 status:active plans in this batch alone (codex_violations_ratchet_to_five,
    understat_local_backfill_completion, mvp_reconciliation_closeout_v10, honest_coverage_v2_instrument_d

#### [P2] active/instruments_catalogue_incremental_rollup_2026_06_29.md ↔ active/instruments_completion_tracker_2026_07_06.md

- finding ids: 361
- **instruments_catalogue_incremental_rollup completion status** —
  `active/instruments_completion_tracker_2026_07_06.md:175`: “flip `instruments_catalogue_incremental_rollup` →
  completed = ⛔ DO NOT FLIP — its lone open item is a LIVE issue, not moot: the operator-declined trad” vs
  `active/instruments_catalogue_incremental_rollup_2026_06_29.md:12`: “status: complete”
  - why: The tracker (a live coordinator, status:active) explicitly instructs agents NOT to flip this plan to completed
    because its live-catalogue-staleness issue is unresolved. But the plan itself is now status:complete (flipped
    2026-07-10, body: '27 of 28 todos confirmed [x] with cited runtime evidence ... Flipped status: act

#### [P2] active/instruments_catalogue_incremental_rollup_2026_06_29.md ↔ epics/instruments_master.md

- finding ids: 125
- **Epic's framing of I-3 as a live, ongoing 'survivor' workstream vs. the child plan's own completed status** —
  `epics/instruments_master.md:7,77-81`: “live work runs through survivors I-1/I-2/I-3. ... I-3 ·
  `instruments_catalogue_incremental_rollup_2026_06_29` — incremental (trailing-window + frozen-” vs
  `active/instruments_catalogue_incremental_rollup_2026_06_29.md:12,341-344`: “status: complete ... 2026-07-10:
  Status-flip note — 27 of 28 todos confirmed [x] with cited runtime evidence ... Flipped `status: active` → `complete`”
  - why: The epic (read across multiple passes/instances) still presents I-3 in the present tense as one of the 3
    survivor plans that 'live instruments work now runs through', with no acknowledgment anywhere in the epic file that
    I-3 flipped to status:complete on 2026-07-10 — the epic's own 'Assigned active plans' section doesn

#### [P2] active/instruments_completion_tracker_2026_07_06.md ↔ active/issues/cefi_layer1_denominator_gaps_2026_07_03.md

- finding ids: 362
- **cefi Layer-1 denominator completion percentage** — `active/instruments_completion_tracker_2026_07_06.md:149`: “cefi
  **73.61** (72 expected / 53 present / 19 missing / 87 stray; `is@03cfd0f`, task 002)” vs
  `active/issues/cefi_layer1_denominator_gaps_2026_07_03.md:200`: “at 08:54 UTC: cefi Layer-1 = **72.60%** (present 53 /
  expected 73), denominator_status INCOMPLETE (20 missing, 87 stray).”
  - why: The tracker's published 'Certified Layer-1' snapshot (last_updated 2026-07-07) still cites the 2026-07-06 cefi
    Layer-1 figure of 73.61% (72 expected tuples) as the certified number, but a newer 2026-07-07 re-measure recorded in
    the (tracker-linked) cefi_layer1_denominator_gaps issue doc supersedes it with 72.60% on a g

#### [P2] active/instruments_completion_tracker_2026_07_06.md ↔ epics/instruments_master.md

- finding ids: 101
- **Epic's auto-populated child-plan count omits the completion tracker** — `epics/instruments_master.md:423`: “"\_3
  active plans declare `parent_epic: instruments_master` in their frontmatter ... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.p”  vs  `active/instruments_completion_tracker_2026_07_06.md:51`:
  “"parent_epic: instruments_master"”
  - why: The completion tracker (doc_type: plan, created 2026-07-06 — before the epic's own last_updated of 2026-07-08)
    declares parent_epic: instruments_master in its frontmatter, yet the epic's 'Assigned active plans' section still
    claims only 3 such plans and does not list or link the tracker anywhere in its body, despite th

#### [P2] active/instruments_service_docs_consolidation_2026_07_08.md (intra-doc)

- finding ids: 390,371
- **mechanical:terminal_status_in_active_dir** — `active/instruments_service_docs_consolidation_2026_07_08.md:18`:
  “status: complete” vs `active/instruments_service_docs_consolidation_2026_07_08.md:100`: “- [ ] [DATA] P0. **Read all
  17 existing docs in full** (not just the intros already skimmed) and extract every concrete claim...”
  - why: Frontmatter declares status: complete, but Phase 1 (6 todos, all P0/P1) is still unchecked `- [ ]` with no
    inline resolution banner on those checkboxes (unlike its sibling same-day flips, e.g.
    mdps_book_microstructure_precompute_columns_2026_06_28.md and
    features_read_book_columns_not_snapshots_2026_06_28.md, which eac
- **instruments-service docs-consolidation plan frontmatter status vs its own unchecked Phase-1 audit checkboxes** —
  `active/instruments_service_docs_consolidation_2026_07_08.md:18`: “status: complete” vs
  `active/instruments_service_docs_consolidation_2026_07_08.md:100-117`: “- [ ] [DATA] P0. Read all 17 existing docs in
  full ... - [ ] [DATA] P0. Cross-check every venue-list claim against UAC's registries ... - [ ] [DATA] P”
  - why: Frontmatter declares status: complete, but the body's entire Phase 1 (6 todos, several P0) is left as unchecked
    `- [ ]`. The Progress Log explains the audit work was split into a separate audit doc and the plan's depends_on was
    repointed there instead of flipping these checkboxes — but the checkboxes themselves were ne

#### [P2] active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md (intra-doc)

- finding ids: 80
- **Has the fleet already lifted the aiohttp <3.14 cap, or is that still gated on a future vcrpy release?** —
  `active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md:30`: “## ✅ RESOLVED 2026-06-23 — aiohttp 3.14.1
  shipped fleet-wide (vcrpy 8.2.1 unblock)” vs `active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md:192`:
  “Lift the `<3.14` cap + bump fleet to `aiohttp>=3.14` + drop the two `--ignore-vuln` flags — ONLY when”
  - why: The doc's own top banner declares the aiohttp<3.14 cap already lifted fleet-wide (17/18 repos on 3.14.1+vcrpy
    8.2.1) as of 2026-06-23. The successor todo list still carries an unchecked item phrased as if this hasn't happened
    yet ('ONLY when vcrpy ships an aiohttp-3.14-compatible release'), which was true before 2026-0

#### [P2] active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md (intra-doc)

- finding ids: 212
- **audit_writes_escalation_artifacts frontmatter status vs its own fully-verified fix** —
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:16`: “status: open” vs
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:212`: “[x] ✅ [VERIFY] P2.
  Confirm a fresh full run leaves `git status` clean in the PM clone and the escalation is ingested by PlanRegenLoop (no
  dirty untrac”
  - why: Frontmatter still declares status: open, but all 4 todos are checked done including the terminal VERIFY step,
    which cites a live re-run confirming clean git status and successful PlanRegenLoop ingestion at
    unified-trading-pm@ad1fa6bc2 — the doc's body reads as fully resolved while its frontmatter still flags it as an o

#### [P2] active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md (intra-doc)

- finding ids: 219
- **Frontmatter status: open contradicts the doc's own body showing its single fix fully shipped, tested, and evid** —
  `active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md:6`: “status: open” vs
  `active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md:55-63`: “[x] [AGENT] P2. ✅ (opus) Make
  autospawn... — agent-orchestrator@826a496 (new `AutoSpawnLoop._maybe_kill_for_tier_upgrade`... 9 unit tests +
  integratio”
  - why: This issue doc has exactly one fix item and it is checked done with a commit sha, 9 unit tests, and an
    integration assertion, and the Notes section frames it as closing 'the residual starvation edge' with nothing else
    outstanding — yet the frontmatter status was never flipped from open to resolved/closed, so the doc st

#### [P2] active/issues/capability_wizard_analysis_findings_2026_06_11.md ↔ epics/strategy_master.md

- finding ids: 295
- **archetype count: epic's 53 vs same-day finding that the true count is 57** — `epics/strategy_master.md:72`: “**53
  archetypes** per `codex/09-strategy/architecture-v2/archetypes/` — closed-set strategy taxonomy.” vs
  `active/issues/capability_wizard_analysis_findings_2026_06_11.md:126`: “The actual value in `enums.py` is 57 as of
  2026-06-11. 4 new archetypes were added after the audit without a plan update.”
  - why: Both documents carry a 2026-06-11 date; the analysis-findings doc explicitly flags that plan prose (matching
    the epic's own '53 archetypes' wording) is stale and the real count is 57 — the epic was never corrected to reflect
    this, so it still reads as authoritative to a new agent.

#### [P2] active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md (intra-doc)

- finding ids: 115
- **Doc status vs. body completion state** — `active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md:15`:
  “"status: open" (frontmatter)” vs `active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md:187-368`: “All 6
  todos marked "[x] ✅ ... CROSS-REFERENCE MARKER CLOSED 2026-07-06" with no residual open item”
  - why: Every actionable todo in the doc's own body is checked off and explicitly annotated as closed (cross-reference
    markers for cefi/tradfi/prediction all closed), yet the frontmatter still declares status: open with no banner
    explaining why the doc itself remains open despite 100% todo closure — a class-(d) frontmatter/bod

#### [P2] active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md (intra-doc)

- finding ids: 204
- **issue frontmatter status vs body resolution banner** —
  `active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md:5`: “status: open” vs
  `active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md:72`: “All three fixes shipped
  to `deployment-service`... Issue resolved → archive on next sweep.”
  - why: Frontmatter still declares the issue open while the body's own Resolution section states all three fixes
    shipped and explicitly calls for archival — the doc was never flipped to resolved/archived despite its own closing
    banner (class-d intra-doc drift).

#### [P2] active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md ↔ active/issues/manifest_hygiene_red_2026_06_27.md

- finding ids: 206
- **defi/DP_NOT_V9 false-positive: separately-tracked open item vs same-day shipped audit-code fix** —
  `active/issues/manifest_hygiene_red_2026_06_27.md:55`: “[ ] [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings
  (2026_06_27) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 sche” vs
  `active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md:170`: “Finding 1 —
  DP_NOT_V9 (alert truthfulness — SHIPPED `e2e-testing@21ce846`, QG green 81s) — Normalise the schema_version compare so
  the count is truthf”
  - why: Both docs are dated 2026-06-27 and concern the same manifest-hygiene DP_NOT_V9 finding-class produced by the
    same audit script; the sibling issue diagnosed and shipped a fix for the exact false-positive root cause
    (string-vs-int schema_version compare) that same day, but manifest_hygiene_red_2026_06_27.md's generic tod

#### [P2] active/issues/instruments_service_plan_reconciliation_2026_06_29.md ↔ active/layer1_remeasure_and_certify_2026_07_06.md

- finding ids: 345
- **which Layer-1 honest-coverage certification is the current authoritative figure per asset_group (cefi/defi esp** —
  `active/issues/instruments_service_plan_reconciliation_2026_06_29.md:146`: “A19 `LANDED` — **Certified Layer-1
  (06-29):** cefi 65.91 | defi 69.44 | tradfi 51.43 | sports 30.77 | prediction 66.67. ... **These supersede ALL earl”
  vs `active/layer1_remeasure_and_certify_2026_07_06.md:98`: “**CERTIFIED 2026-07-06 15:01 UTC: cefi Layer-1 = 73.61%
  (present 53 / expected 72; 19 missing tuples; 87 stray).\*\*”
  - why: instruments_service_plan_reconciliation_2026_06_29.md is status: open, last_updated 2026-07-03, and explicitly
    frames its 06-29 Layer-1 figures (cefi 65.91, defi 69.44, ...) as superseding ALL earlier numbers and warns that
    plans citing other figures are citing stale numbers. It was never updated after the 2026-07-03 U

#### [P2] active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md ↔ active/issues/manifest_reprocessing_generic_utility_2026_07_07.md

- finding ids: 122
- **Completeness of the '11 one-off reprocessing scripts' audit** —
  `active/issues/manifest_reprocessing_generic_utility_2026_07_07.md:48-49`: “11 near-identical "load manifest → filter
  by predicate → flip status/reason field → snapshot → write back" scripts, independently reinvented across 3 ” vs
  `active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md:130-134`: “One-off patch script shipped
  instruments-service@40bdfe1d as scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py. Contract: filter
  date>=2”
  - why: The generic-reprocessing-utility issue (filed 2026-07-07) claims an exhaustive grep found exactly 11
    near-identical one-off reclassify/reprocess scripts across the workspace, but the is_cefi-blank-data_type issue
    (filed one day earlier, 2026-07-06) documents two more scripts matching that exact recurring shape (backfil

#### [P2] active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md (intra-doc)

- finding ids: 271
- **Frontmatter status vs body completion state** —
  `active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md:29`: “status: open” vs
  `active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md:173`: “**CAS-retry lost-update race
  confirmed fixed at both the code level and the sports bucket's data level.**”
  - why: All 4 'Recommended decision' todos in the body are checked [x] ✅ with shipped commit SHAs
    (unified-trading-library@75e59a89, @84528344) and a final re-verification pass explicitly declaring the bug fixed at
    both code and data level, yet the frontmatter still declares status: open (batch header also lists it as status=o

#### [P2] active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md ↔ active/master_data_canonicalisation_migration_catalogue_2026_06_07.md

- finding ids: 131
- **Coordinator's own orphan-sweep discipline vs an unregistered open issue under the same epic** —
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:2122-2127`: “Swept `plans/active/*.md` +
  `plans/active/issues/*.md` for manifest/migration/catalogue/pipeline_mode/backfill/ coverage/schema themes. \*\*All
  register” vs `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:14,5-6`: “parent_epic:
  manifest_master ... status: open ... created: 2026-06-24 (manifest-writer OOM affecting DeFi/cefi/tradfi/sports
  backfills)”
  - why: The coordinator's own hard rule states any active data-layer plan/issue lacking a registry row is
    'review-blocking', and it promises to re-sweep at every gate promotion. The open issue
    manifest_index_read_oom_canonical_cache_2026_06_24.md (parent_epic: manifest_master, status: open, a cross-cutting
    manifest-read defect

#### [P2] active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md ↔ active/mtds_file_size_refactor_2026_06_08.md

- finding ids: 186
- **"ALL MTDS ships blocked" gate vs an actual successful MTDS ship after that date** —
  `active/mtds_file_size_refactor_2026_06_08.md:38`: “the issue
  `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` (which blocks ALL MTDS ships) is a
  SEPARATE doc and is NOT defer” vs
  `active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md:139`: “Full
  `bash scripts/quality-gates.sh` exit 0. (market-tick-data-service@f4dab8f9, shipped 2026-07-06)”
  - why: mtds_file_size_refactor (last_updated 2026-06-26) asserts a live QG-red issue blocks ALL
    market-tick-data-service ships; mtds_defi_catalog_reader shows a full green-QG MTDS ship landing 2026-07-06, ten
    days later, with no note that the blocking gate was lifted — the still-active claim in mtds_file_size_refactor now
    rea

#### [P2] active/issues/mtds_plan_reconciliation_2026_06_29.md ↔ active/tradfi_massive_dual_source_2026_05_28.md

- finding ids: 375
- **TradFi VIX/VX-futures sourcing stack — Barchart's role in the ohlcv_15m SOURCE_PRIORITY list** —
  `active/tradfi_massive_dual_source_2026_05_28.md:52-53,180`: “VX futures (CFE): Massive does NOT cover CFE. Keep
  existing pattern (Yahoo + Barchart as already wired in ("tradfi","ohlcv_15m"): ["databento","yahoo"” vs
  `active/issues/mtds_plan_reconciliation_2026_06_29.md:200`: “tradfi_massive_dual_source: M22 Operator-decision #3
  (L53) + L180 still list Barchart in the ohlcv_15m SOURCE_PRIORITY — Barchart was RETIRED 2026-06-”
  - why: tradfi_massive_dual_source_2026_05_28.md is status: active with last_updated: 2026-06-27 (3 days AFTER the
    2026-06-24 Barchart retirement + Databento-XCBF.PITCH shipment) but still asserts 'no change to the VX cell
    required' and cites the stale ['databento','yahoo','barchart'] priority list at two locations. A separate

#### [P2] active/issues/phantom_captures_sports_2026_06_28.md (intra-doc)

- finding ids: 211
- **phantom_captures_sports frontmatter status vs its own fully-checked todo list** —
  `plans/active/issues/phantom_captures_sports_2026_06_28.md:5`: “status: open” vs
  `plans/active/issues/phantom_captures_sports_2026_06_28.md:98`: “[x] ✅ [SCRIPT] P2. Apply phantom reconciliation for
  sports. **DONE 2026-06-28T04:26Z**: 27,595 phantoms flipped (cap→attempted_failed); manifest uploa”
  - why: Frontmatter declares status: open, but both todos (diagnose root cause AND apply reconciliation) are checked
    done with hard evidence (GCS upload, triage JSONL) — unlike sibling
    phantom*captures*{cefi,defi,tradfi,prediction}.md docs where 'open' correctly matches at least one genuinely
    unchecked todo, this doc gives no

#### [P2] active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md (intra-doc)

- finding ids: 85
- **frontmatter status vs fully-resolved body** — `active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md:13`:
  “status: open” vs `active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md:69`: “[x] ✅ [INFRA] P2. Set `TMPDIR`
  ... instead of relying on the default `/tmp` tmpfs ... — unified-trading-pm@0e29e6d81.”
  - why: All three recommended-decision todos (P2 TMPDIR redirect, P3 tmpfs-resize decision, P3 stale-dir cron) are
    checked done with shipped commits and closing Progress Log entries for each ('Implemented by slot-2', 'closed by
    slot-2' x2), yet the frontmatter still declares status: open rather than resolved.

#### [P2] active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md ↔ active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md

- finding ids: 252
- **Out-of-universe overcapture issue doc still open/unresolved vs P2a's shipped write-path gate + wipe implementi** —
  `active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md:5,18,92-96`: “status: open ... resolved_by:
  (blank) ... 4. The 1,676,612 out-of-universe rows ...: DROP from the manifest (recommended...) vs KEEP” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:394-403`: “G1 wipe (Todo 1) — EXECUTED ...
  Post-wipe IS index (19:42 UTC): 2,898,902 rows — canonical only”
  - why: The issue doc's core recommendations — (1) a write-path gate restricting per-league captures to the canonical
    universe, and (4) DROP the out-of-universe rows from the manifest — are exactly what P2a's Todo #1 shipped
    (instruments-service@acfd5ac write-path gates in sports_fixtures.py/process_write.py/footystats.py/unde

#### [P2] active/layer1_remeasure_and_certify_2026_07_06.md ↔ active/tradfi_v9_stage1_finish_2026_07_06.md

- finding ids: 126
- **Tradfi orphan-sweep gate state on 2026-07-10 (585 real orphans still open vs. corpus-wide E=0 gate met)** —
  `active/layer1_remeasure_and_certify_2026_07_06.md:142-157`: “the backgrounded full orphan sweep (task 2, PID 22320)
  ... had actually COMPLETED unattended at 2026-07-10 15:57:41 UTC ... and it is **NOT E=0**: 585” vs
  `active/tradfi_v9_stage1_finish_2026_07_06.md:94-96,195-202`: “🎯 GATE MET 2026-07-10 17:17:22 UTC (slot-3
  sonnet/high) — fresh full corpus-wide re-sweep confirms `orphan_class_E=0, unknown_prefixes=0`. ... === ACC”
  - why: layer1_remeasure_and_certify's latest entry (its own 'RE-CHECKED AGAIN' continuation, referencing a 15:57:41
    UTC sweep result) asserts the orphan gate is NOT met with 585 real orphans outstanding; tradfi_v9_stage1_finish's
    later same-day entry (17:17:22 UTC, ~80 min after) shows the 585-orphan remainder was backfilled

#### [P2] active/layer1_remeasure_and_certify_2026_07_06.md ↔ epics/instruments_master.md

- finding ids: 111
- **Epic hub's auto-populated active-plan roster is stale relative to the actual current set of child plans** —
  `epics/instruments_master.md:423-424`: “\_3 active plans declare parent_epic: instruments_master in their frontmatter.
  Workers pick up in priority order (P0 first). Auto-populated by scripts/” vs
  `active/layer1_remeasure_and_certify_2026_07_06.md:29`: “parent_epic: instruments_master”
  - why: The epic's 'Assigned active plans' section names only 3 old (2026-05/06-era) plans and gives no mention at all
    of the 4 newer AO Plans (is_catalogue_completion_2d, layer1_remeasure_and_certify,
    foundation_gates_and_capture_to_100, instruments_catalogue_incremental_rollup) that all declare parent_epic:
    instruments_maste

#### [P2] active/master_to_live_defi_2026_05_23.md (intra-doc)

- finding ids: 215,368
- **frontmatter last_updated stale vs body content added/dated later** — `active/master_to_live_defi_2026_05_23.md:31`:
  “last_updated: 2026-05-11” vs `active/master_to_live_defi_2026_05_23.md:1245`: “### Group H — Per-client isolation +
  multi-venue concurrency (added 2026-05-20)”
  - why: Frontmatter declares last_updated 2026-05-11, but the body contains an entire section explicitly labeled 'added
    2026-05-20', other content dated 2026-05-24 (sports available_at rename 'FULLY SHIPPED'), and an auto-regenerated
    plan inventory whose rows are dated as late as 2026-07-09/10 — the last_updated field was neve
- **Frontmatter last_updated vs body content currency** — `active/master_to_live_defi_2026_05_23.md:31`: “last_updated:
  2026-05-11” vs `active/master_to_live_defi_2026_05_23.md:1159`: “full DART experience extension ... Target completion
  2026-07-04 (~6 weeks post-cutover).”
  - why: Frontmatter status:active/last_updated:2026-05-11 is stale by nearly two months relative to the plan's own
    body, which carries dated entries and targets well past that (e.g. a 2026-07-04 target-completion date, a 2026-06-15
    deadline at line 1866, and progress-log entries dated 2026-05-18). An agent trusting the frontma

#### [P2] active/mdps_book_microstructure_precompute_columns_2026_06_28.md (intra-doc)

- finding ids: 185
- **declared asset_group/summary scope vs actual implemented scope (class d)** —
  `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:9`: “asset_group: [cefi, prediction, cross-cutting]”
  vs `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:103`: “plan summary names "CeFi + prediction" but
  reality is "CeFi + DeFi (Hyperliquid via DefiBookSnapshotAdapter)" — no prediction `book_snapshot_5` adapte”
  - why: Frontmatter and summary declare scope as CeFi+prediction; the plan's own [IMPLEMENT] todo logs this as
    factually wrong (no prediction book adapter exists; actual scope is CeFi+DeFi) and explicitly defers fixing the doc
    ('logged, not fixed here') — the asset_group field other tooling/dispatch may key on is stale.

#### [P2] active/mdps_book_microstructure_precompute_columns_2026_06_28.md ↔ active/mdps_features_reduced_artifact_tracker_2026_06_28.md

- finding ids: 183
- **coordination-tracker status vs child mini-plan actual dispatch/completion state** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:37`: “All born `status: draft`; flip the batch to
  `active` together to green-light dispatch.” vs `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:44`:
  “Status-flip note (2026-07-10): all 6 todos confirmed [x] with cited evidence ... Flipped `status: active` →
  `complete`.”
  - why: The tracker (still status: draft, last_updated 2026-06-28) frames the 9 mini-plans as gated on an operator
    flipping the whole batch to active together; child mini-plans 1, 7 and 8 have independently progressed all the way
    through active to complete without the tracker itself ever being updated — a reader of only the tr

#### [P2] active/mdps_features_full_month_benchmark_binance_2026_06_28.md ↔ active/mdps_features_reduced_artifact_tracker_2026_06_28.md

- finding ids: 189
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 7 already dispatched and fully** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,142`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/mdps_features_full_month_benchmark_binance_2026_06_28.md:8,44`: “status: complete ... Status-flip note
  (2026-07-10): all 5 todos confirmed [x] with cited evidence ... Flipped status: active → complete.”
  - why: Same pattern as Plan 5: the tracker names mdps_features_full_month_benchmark_binance as its capstone Plan 7
    (gated on Plans 1 and 6) and claims the batch is undispatched draft work pending a coordinated flip. That plan
    independently reached status: complete on 2026-07-10 (full-month Binance benchmark run, cost model, r

#### [P2] active/mdps_features_reduced_artifact_tracker_2026_06_28.md ↔ active/mdps_polars_engine_cost_sharpening_2026_06_28.md

- finding ids: 190
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 8 already dispatched and shipp** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,143`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/mdps_polars_engine_cost_sharpening_2026_06_28.md:59-67`: “[x] Convert the candle aggregation path to
  pure-Polars lazy ... market-data-processing-service@c7e0437. Evidence: ... MDPS QG green (sentinel 3604451)”
  - why: The tracker names mdps_polars_engine_cost_sharpening as its independent, dispatch-ready Plan 8 but frames the
    whole batch as undispatched draft work awaiting a coordinated flip. That plan's own body shows all 6 todos checked
    off with real shipped commits (e.g. market-data-processing-service@c7e0437, QG green) deliverin

#### [P2] active/mdps_features_reduced_artifact_tracker_2026_06_28.md ↔ active/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md

- finding ids: 188
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 5 already dispatched and fully** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,140`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md:8,42-43`: “status: complete ... Status-flip note
  (2026-07-10): all 5 todos confirmed [x] with cited runtime evidence ... Flipped status: active → complete.”
  - why: The tracker explicitly names tradfi_mdps_passthrough_dependency_gap as its Plan 5 and states none of the nine
    mini-plans have been dispatched — they are all 'born status: draft', awaiting a coordinated batch flip to active.
    But that exact child plan independently reached status: complete with all 5 todos shipped and ve

#### [P2] active/monitoring_control_plane_master_2026_06_10.md ↔ epics/observability_master.md

- finding ids: 197
- **Epic child-plan roster is stale (index drift)** — `epics/observability_master.md:99`: “\_13 active plans declare
  `parent_epic: observability_master` in their frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.”  vs  `active/monitoring_control_plane_master_2026_06_10.md:14`:
  “parent_epic: observability_master”
  - why: The epic's frontmatter last_updated is 2026-06-19 and its body enumerates only ~13 May-23-era (mostly archived)
    plans plus one P1 item. But at least 5 currently-active plans in this same cluster declare parent_epic:
    observability_master in their own frontmatter (monitoring_control_plane_master_2026_06_10, deployment_ob

#### [P2] active/mvp_catalogue_finalization_v10_2026_06_27.md ↔ epics/instruments_master.md

- finding ids: 117
- **Epic's auto-populated count of active child plans vs. actual number of active plans declaring this parent_epic** —
  `epics/instruments_master.md:422`: “"\_3 active plans declare `parent_epic: instruments_master` in their
  frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.py”  vs  `active/mvp_catalogue_finalization_v10_2026_06_27.md:14`:
  “"parent_epic: instruments_master" (status: active, line 5)”
  - why: The epic's 'Assigned active plans' section, last auto-populated 2026-05-21, claims only 3 active plans declare
    parent_epic: instruments_master. In just this one reading batch, at least 5 status:active PLAN docs
    (mvp_catalogue_finalization_v10, mvp_scope_catalogue_tagging, prediction_canonical_identity_migration, canoni

#### [P2] active/org_migration_to_odumresearch_2026_06_07.md (intra-doc)

- finding ids: 79
- **Frontmatter status (active) vs the plan's own stated urgency/gating** —
  `active/org_migration_to_odumresearch_2026_06_07.md:6`: “status: active” vs
  `active/org_migration_to_odumresearch_2026_06_07.md:35`: “the rulesets justification is GONE; migration is now
  OPTIONAL/low-priority.”
  - why: The doc's frontmatter declares status: active with every Phase 0-5 todo unchecked, but the plan's own top
    banner says the migration's hard driver is gone, it is now optional/low-priority, and a 'Decision pending operator'
    on whether to even proceed is unresolved (as of the last Progress Log entry, 2026-06-07). An 'acti

#### [P2] active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md ↔ epics/predictions_master.md

- finding ids: 232
- **Epic child-plan index omits an entire P2 plan declaring it as parent_epic** — `epics/predictions_master.md:888-930`:
  “"Assigned active plans \_Active plans declaring `parent_epic: predictions_master`... Auto-populated... the script
  keeps it in sync from frontmatter" / ” vs `active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md:21-26`:
  “"parent_epic: predictions_master ... priority: P2 ... estimate_baseline_ai_days: 8"”
  - why: The epic's 'Assigned active plans' section claims to be auto-synced from frontmatter and lists only 3 P0 plans
    plus a single P2 sub-item (the sentinel fan-out) as the entirety of P2 work; this 213KB, ~8-AI-day plan (perps +
    live CLOB depth + a promoted-to-long-lived arb-detector production service spanning 06-20 throug

#### [P2] active/solana_defi_legacy_migration_2026_05_27.md (intra-doc)

- finding ids: 172
- **Whether the canonical Solana lending/dex-pools buckets contain migrated SOLANA rows (Gate 2/3 completeness)** —
  `active/solana_defi_legacy_migration_2026_05_27.md:147`: “lending_indices/ + dex_pools/ deferred: Gate 2 migration has
  NOT completed (canonical buckets show 0 SOLANA rows — Gate 3 cannot be verified yet).” vs
  `active/solana_defi_legacy_migration_2026_05_27.md:133`: “Gate 3 — manifest reconcile + verify ... DONE 2026-05-30 —
  MTDS@86d0113 ... lending-indices: 2,811 SOLANA rows ... dex-pools: 1,555 SOLANA rows”
  - why: Gate 4's own text (unmodified since 2026-05-28) asserts the canonical buckets show '0 SOLANA rows' and that
    Gate 3 cannot be verified, while Gate 3 (dated 2026-05-30, later) is marked ✅ DONE with concrete non-zero SOLANA
    row counts. Both are unresolved claims about the same current-state fact in the same document; Gate

#### [P2] active/solana_defi_legacy_migration_2026_05_27.md ↔ epics/mtds_mdps_master.md

- finding ids: 173
- **Drift Solana perp-DEX historical data source (S3 archive vs Helius)** — `epics/mtds_mdps_master.md:908`: “MTDS
  Solana perp DEX source wiring for all 4 venues: DRIFT (Drift S3 historical archive), MANGO V4, ZETA, FLASH REST APIs —
  emit perp_funding parquets” vs `active/solana_defi_legacy_migration_2026_05_27.md:576`: “Option 3 (Drift V2 S3
  archive) FAILS — bucket `drift-historical-data-v2` confirmed ends 2025-01-07 ... Option 2 wins architecturally”
  - why: The epic's open P2 backlog item still frames 'Drift S3 historical archive' as the intended/expected wiring
    source for DRIFT, but solana_defi_legacy_migration's Bug-D investigation confirms BOTH Drift S3 archives (V1 ending
    2025-01-08, V2 ending 2025-01-07 with no market/\* prefix at all) are dead ends, and ships a Heliu

#### [P2] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md (intra-doc)

- finding ids: 255
- **cron pause/resume state disagreement within same doc** —
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:91`: “both crons resumed
  2026-06-25: `uts-prod-sports-scheduler-cron` ENABLED (\*/5)” vs
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:451-452`: “**PAUSED sports crons**
  (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) — **named re-enable gate**”
  - why: The Execution-sequence section (item checked done) states both crons were resumed 2026-06-25 after the
    write-gate shipped and the tarball was rebuilt, but the same doc's 'Temporary states' section still lists the crons
    as currently PAUSED awaiting exactly that same re-enable gate — the doc disagrees with itself about c

#### [P2] active/sports_manifest_canonicalisation_2026_06_01.md (intra-doc)

- finding ids: 147
- **Blocker-ID inconsistency for the L6 legacy-cell decision** —
  `active/sports_manifest_canonicalisation_2026_06_01.md:2153`: “L6-legacy-only 🔴 RED | 5,793 cells (2020-06-01..08,
  ODDS_API/ODDS) — operator decision BLK-6b1bed9c pending” vs
  `active/sports_manifest_canonicalisation_2026_06_01.md:2190`: “**BLK-800ef029 resolved** (Option B: migrate first,
  then schedule E3 drain).”
  - why: The doc frames the L6 legacy-only-cells choice under ID BLK-6b1bed9c with two options: (A) migrate the 8 legacy
    days, or (B) descope/accept loss (line 1994). That 'pending' framing is repeated verbatim across at least 8 separate
    E8 audit entries through 2026-06-29 (lines 2036/2045/2072/2090/2104/2131/2153/2173/2184), a

#### [P2] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md ↔ epics/sports_master.md

- finding ids: 262
- **sports_master epic VM assignment** — `epics/sports_master.md:39`: “assigned_vm: vm-sports” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-210`: “Role-based dispatch -- NO epic VM
  (single-VM architecture, 2026-06-27) ... epic VMs deprecated per CLAUDE.md; there is no `vm-sports` to start.”
  - why: The hub epic's own frontmatter still names the deprecated per-epic VM `vm-sports` as its assigned_vm, while the
    coordinator plan under the same epic explicitly states epic VMs are deprecated and 'there is no vm-sports to start'
    -- the epic's own metadata field was never migrated to the {planning, NA} scheme.

#### [P2] active/uac_coverage_90pct_2026_06_10.md ↔ epics/client_isolation_and_governance_master.md

- finding ids: 34
- **Epic's related_plans / priority sections never actually enumerate the uac_coverage_90pct plan** —
  `epics/client_isolation_and_governance_master.md:29-34`: “related_plans: [
  ../active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md,
  ../active/global_ledger_pnl_attribution_discovery_2026_05_21.” vs `active/uac_coverage_90pct_2026_06_10.md:14`:
  “parent_epic: client_isolation_and_governance_master”
  - why: uac_coverage_90pct_2026_06_10.md declares itself a P1 child of this epic and is status:active, but it is absent
    from the epic's related_plans frontmatter and from every priority section body (P0/P1/P2/P3 all read either empty or
    list unrelated items); the epic's own auto-populated 'Assigned active plans' block claims '

#### [P2] active/v2_engine_venue_buildout_2026_06_15.md ↔ epics/strategy_master.md

- finding ids: 298
- **epic's '8 active plans' count is stale — this batch alone has 5+ additional active/open docs declaring parent\_** —
  `epics/strategy_master.md:99`: “\_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers
  pick up in priority order (P0 first). Auto-populated by
  `scripts/”  vs  `active/v2_engine_venue_buildout_2026_06_15.md:14`: “parent_epic: strategy_master”
  - why: Epic last_updated is 2026-06-11 and its assigned-plans index still says '8 active plans' (auto-populated
    2026-05-21), but v2_engine_venue_buildout (created 2026-06-15), defi_collateral_sizing (2026-06-17),
    e2e_defi_config_taxonomy (2026-06-17), archetype_venue_universe (2026-06-30), and ui_coverage_ts (2026-07-10) all

#### [P2] archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md ↔ epics/mtds_mdps_master.md

- finding ids: 140
- **Epic child-plan status/ownership vs the child plan's own frontmatter** — `epics/mtds_mdps_master.md:729-731`: “###
  [`live_pipeline_mtds_mdps_features_2026_05_08`]... **status**: active” vs
  `archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md:5,15-16`: “status: complete ... epic: epic-deployment
  ... parent: master_to_live_defi_2026_05_23”
  - why: Same class of drift as the workspace_qg_sweep item: epic P0 table says 'active' for a plan whose own
    frontmatter says complete and whose epic/parent fields point to epic-deployment, not mtds_mdps_master (the plan
    doesn't even carry a parent_epic: mtds_mdps_master field). The epic's index is stale/wrong on ownership and

#### [P2] epics/README.md ↔ epics/escalation_and_disaster_recovery_master.md

- finding ids: 10002
- **epic-registry completeness** — `epics/README.md:164,166-187`: “## 20 epics in 5 tiers | # | Tier | Epic slug |
  Assigned VM | Owns |” vs `epics/escalation_and_disaster_recovery_master.md:7,15,17-19`: “status: active ... created:
  2026-06-25 ... tier: L4 priority: P1 assigned_vm: vm-cross-cutting”
  - why: README's canonical 20-epic table (and the paired 'VM topology (10 VMs serving 20 epics)' table naming
    vm-cross-cutting's owned epics as only
    infrastructure_master/observability_master/batch_live_symmetry_master/client_isolation_and_governance_master) omits
    escalation_and_disaster_recovery_master, a real active L4/P1 ep

#### [P2] epics/README.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 10003
- **epic count self-citation drift** — `epics/README.md:164`: “## 20 epics in 5 tiers” vs
  `epics/global_ledger_pnl_attribution_master.md:147`: “co-located with `execution_master` + `strategy_master` +
  `trading_agent_master` (per `README.md` § "19 epics in 5 tiers").”
  - why: global_ledger_pnl_attribution_master.md (status: active) cites README.md's section header verbatim as '19 epics
    in 5 tiers', but the live README.md header at line 164 reads '20 epics in 5 tiers' -- the count changed and this
    active epic's own body was never updated to match, a stale cross-reference to a numeric fact ab

#### [P2] epics/dart_and_promote_master.md (intra-doc)

- finding ids: 310,386
- **Intra-doc repos facet omits a repo the body's HARD RULE requires gating on** —
  `epics/dart_and_promote_master.md:12`: “repos: [alerting-service, deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/dart_and_promote_master.md:71`: “any UI repo (unified-trading-system-ui,
  deployment-ui, user-management-ui) MUST pass the playwright verification gate”
  - why: The epic's own repos: frontmatter facet — the grep-native L1 index key agents use per the retrieval model
    documented in agent_operating_framework_master.md — lists only 4 repos and omits user-management-ui, yet the epic's
    own 'UI Verification Contract (HARD RULE)' body text explicitly requires every UI-touching todo in
- **Epic's declared repo scope (frontmatter) vs its copy-pasted playwright-gate scope (body) re: user-management-u** —
  `epics/dart_and_promote_master.md:12`: “repos: [alerting-service, deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/dart_and_promote_master.md:70-72`: “All active plans under this epic that touch
  any UI repo (`unified-trading-system-ui`, `deployment-ui`, `user-management-ui`) MUST pass the playwright ”
  - why: The same HARD RULE paragraph (copy-pasted verbatim from deployment_and_user_management_master.md) names
    user-management-ui as a gated UI repo for the DART/promote epic even though this epic's declared `repos:` field
    never lists it and its 'Owns' line (DART cockpit + ManualTradeGateDialog + promote workflow) doesn't cla

#### [P2] epics/dart_and_promote_master.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 10008
- **Dangling frontmatter reference: the global-ledger discovery plan was archived but 6 of the 7 handshake-partner** —
  `epics/global_ledger_pnl_attribution_master.md:83`:
  “[`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)”
  vs `epics/dart_and_promote_master.md:19`: “../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,”
  - why: global_ledger_pnl_attribution_master.md's own body (lines 83, 112) and frontmatter (line 18) correctly link the
    discovery plan at `../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md`, and the file only
    exists on disk at `plans/archive/2026_05/...` (confirmed: no file at `plans/active/global_ledger

#### [P2] epics/defi_master.md (intra-doc)

- finding ids: 40
- **Epic's own P0 dispatch table labels an archived plan 'status: active'** — `epics/defi_master.md:1699`: “###
  [`defi_mtds_subgraph_and_adapter_fixes_2026_06_20`](../archive/2026_06/defi_mtds_subgraph_and_adapter_fixes_2026_06_20.md)”
  vs `epics/defi_master.md:1701`: “status: active · estimate: 3.2 cal AI-days (class: refactor). DEX-swaps subgraph
  schema rewrite (PancakeSwap/SushiSwap/Aerodrome/Camelot) + Compound V”
  - why: The epic's '## Assigned active plans' P0 section links to a child plan whose own path is under archive/2026_06/
    (i.e., already archived), immediately followed by a 'status: active' label and a live estimate/priority — an agent
    trusting the epic's P0 dispatch table could attempt to dispatch work from a plan that has act

#### [P2] epics/execution_master.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 312
- **global_ledger_pnl_attribution_discovery plan location/status** — `epics/execution_master.md:17`: “related: [...,
  ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md]” vs
  `epics/global_ledger_pnl_attribution_master.md:85`: “**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL.
  Operator [ack] pending on Phase 3/5/6”
  - why: execution_master's frontmatter (related + related_plans) still cites this plan under plans/active/ (path
    confirmed non-existent on disk), while global_ledger_pnl_attribution_master correctly shows it archived to
    plans/archive/2026_05/ on 2026-05-23 — a dangling stale reference in execution_master that hasn't been updat

#### [P2] epics/global_ledger_pnl_attribution_master.md (intra-doc)

- finding ids: 315
- **assigned-active-plan count vs actual plan list (intra-doc)** — `epics/global_ledger_pnl_attribution_master.md:78`:
  “_2 active plans declare `parent_epic: global_ledger_pnl_attribution_master`. Workers pick up in priority order (P0
  first)._” vs `epics/global_ledger_pnl_attribution_master.md:92`: “**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; all
  27 items DEFERRED-OPERATOR-DECISION”
  - why: The banner claims 2 active child plans, but both plans actually listed (discovery and migration) are marked ✅
    ARCHIVED with 0 and 0/27 items respectively — no active plan is shown, so the auto-populated count contradicts the
    body it sits above.

#### [P2] epics/infrastructure_master.md (intra-doc)

- finding ids: 61,69
- **Epic 'must complete' P0 section lists only already-archived/complete plans** — `469`: “## P0 — must complete before
  next foundation gate” vs `471-473`: “workspace_qg_sweep_2026_05_23 ... **status**: ✅ ARCHIVED 2026-05-26 — All items
  completed.”
  - why: The epic's own 'Assigned active plans' > 'P0 — must complete before next foundation gate' heading implies live,
    outstanding work, yet every entry listed under it (workspace_qg_sweep_2026_05_23,
    audit03_deployment_cron_provisioning_2026_05_22, defi_coverage_capability_alignment_2026_05_22) is itself marked ✅
    ARCHIVED/DO
- **epic frontmatter internal date inconsistency** — `epics/infrastructure_master.md:35`:
  “../active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,” vs `epics/infrastructure_master.md:42`: “last_updated:
  2026-06-19”
  - why: The epic's own `related_plans` list references a plan created 2026-06-30, eleven days after the epic's declared
    `last_updated: 2026-06-19` — the last_updated stamp was not bumped when the frontmatter list was edited, making the
    freshness field unreliable for anyone deciding whether to re-read the epic.

#### [P2] epics/infrastructure_master.md ↔ epics/manifest_master.md

- finding ids: 318,319,343
- **gate_3_phantom_audit_runbook_2026_05_13 status** — `epics/infrastructure_master.md:668`: “Gate 3 phantom-audit
  execution runbook — one-shot phantom reconciliation pre-2026-05-15 freeze gate | Active” vs
  `epics/manifest_master.md:168`: “**status**: ✅ ARCHIVED 2026-05-21 — Gate 3 FIRED 2026-05-17; 0 phantoms all 5
  asset_groups”
  - why: infrastructure_master (last_updated 2026-06-19, over a month after archival) still lists this plan as 'Active'
    with an ../active/ link, while manifest_master (its true owner) shows it archived 2026-05-21 with an ../archive/
    link. An agent following infra_master's table would look for a non-existent active plan and coul
- **current manifest schema version** — `epics/infrastructure_master.md:644`: “Manifest schema v8 + 4-state
  `capture_status` + per-asset-group bucket layout” vs `epics/manifest_master.md:55`: “manifest schema (**v9 current** —
  `MANIFEST_SCHEMA_VERSION = 9` live 2026-05-30, UTL@`c7bfa427`”
  - why: infrastructure_master's Codex-SSOT table (as of its own last_updated 2026-06-19) still describes the manifest
    schema as v8, while manifest_master — the schema's actual epic owner — states v9 has been live workspace-wide since
    2026-05-30, three weeks before infra_master's last edit. The two active docs disagree on a loa
- **manifest schema version currently live (v8 vs v9)** — `epics/infrastructure_master.md:644`:
  “/codex/02-data/availability-manifest-and-data-status.md ... 'Manifest schema v8 + 4-state `capture_status` +
  per-asset-group bucket layout'” vs `epics/manifest_master.md:55`: “**Owns**: manifest schema (**v9 current** —
  `MANIFEST_SCHEMA_VERSION = 9` live 2026-05-30, UTL@`c7bfa427`...”
  - why: Both are active L1/L4 epics. infrastructure_master.md's 'Codex SSOTs' table (last_updated 2026-06-19, three
    weeks after v9 shipped 2026-05-30) still describes the manifest schema doc as owning 'v8', while manifest_master.md
    (the dedicated manifest epic) and numerous active plans (tradfi_manifest_canonicalisation, predi

#### [P2] epics/instruments_master.md (intra-doc)

- finding ids: 96
- **Plan location (archive/) vs declared status (ACTIVE)** — `epics/instruments_master.md:428`: “###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — instruments-service cluster”
  vs `epics/instruments_master.md:430`: “**status**: 🟠 ACTIVE — QG sweep for instruments-service (32 ruff errors).
  `bash scripts/quality-gates.sh` exit 0.”
  - why: The plan is linked from an archive/2026_05/ path (implying archived/closed) yet the epic's own status line
    calls it ACTIVE with an open task — an agent could be misdirected about whether this work is still live or
    historical.

#### [P2] epics/manifest_evolution_SUPERSEDED_2026_05_21.md ↔ epics/manifest_master.md

- finding ids: 322
- **ownership of IS↔MTDS contract enforcement work (incl. folded child `is_mtds_contract_audit_2026_05_20`)** —
  `epics/manifest_evolution_SUPERSEDED_2026_05_21.md:64-65`: “All open scope (schema v8, honest absence taxonomy, writer
  code, GCS data layout, IS↔MTDS contract enforcement) continues there.” vs `epics/manifest_master.md:105`: “**Upstream
  gates**: `instruments_master` (IS→MTDS contract; archive-metadata fields on `InstrumentRecord`)”
  - why: The supersession banner explicitly says IS↔MTDS contract enforcement (one of the 11 folded child plans)
    continues inside manifest_master. But manifest_master's own body never lists `is_mtds_contract_audit_2026_05_20`
    among its child plans and instead treats 'IS→MTDS contract' as an upstream item owned by instruments_ma

#### [P2] epics/manifest_master.md (intra-doc)

- finding ids: 321
- **manifest_master's own 'active plan count' claim vs body reality** — `epics/manifest_master.md:115`: “_7 active plans
  declare `parent_epic: manifest_master` in their frontmatter (verified 2026-06-30)._” vs
  `epics/manifest_master.md:122`: “**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-3 done (100% v8 dist confirmed); Phase
  4 BLOCKED-OPERATOR-DECISION”
  - why: The auto-populated blurb claims 7 active child plans as of 2026-06-30, but every single plan enumerated in the
    P0/P1/P2/Archived sections beneath it (d3_manifest_v8_finish, d5_features_missing_data_downgrade,
    expected_unattempted_propagation_chain, gcs_migration_bundle, honest_coverage_formula_consolidation, manifest_s

#### [P2] epics/orchestrator_master.md (intra-doc)

- finding ids: 325
- **frontmatter last_updated vs body content dates** — `epics/orchestrator_master.md:51`: “last_updated: 2026-05-21” vs
  `epics/orchestrator_master.md:440`: “"DONE 2026-06-10 — `agent-orchestrator@68116f7`."”
  - why: Frontmatter declares the doc last touched 2026-05-21, but the body contains multiple sections dated as late as
    2026-06-07/06-08/06-10 (tab-mirror crash fix, auth_failed cooldown fix, WorkerLivenessWatchdog fix) — the
    frontmatter field is stale by ~3 weeks relative to the doc's own most recent content.

#### [P2] epics/plan_hygiene_master.md (intra-doc)

- finding ids: 326
- **frontmatter last_updated vs body content dates** — `epics/plan_hygiene_master.md:29`: “last_updated: 2026-05-23” vs
  `epics/plan_hygiene_master.md:158-165`: “"DEFERRED items with placeholder successors — resolved per-item audit
  2026-06-25"”
  - why: Frontmatter last_updated is 2026-05-23 but the body's "Findings — 2026-06-01 cross-plan deviation sweep"
    section and its 2026-06-25 per-item audit resolution post-date the declared last_updated by over a month.

#### [P2] epics/trading_agent_master.md (intra-doc)

- finding ids: 334
- **Auto-populated 'active plans' count vs the only listed child's actual archived status** —
  `epics/trading_agent_master.md:41`: “_1 active plans declare `parent_epic: trading_agent_master` in their frontmatter.
  Workers pick up in priority order (P0 first)._” vs `epics/trading_agent_master.md:48`: “**status**: ✅ ARCHIVED
  2026-05-23 — Phases 1-8 complete: directive pipeline + event contracts + UAC schema + codex SSOT shipped.”
  - why: The auto-generated 'Assigned active plans' header claims 1 active child plan, but the only plan listed under it
    is explicitly marked ARCHIVED. An agent trusting the header count (e.g. a dispatcher scanning epic summaries) would
    believe there is live work here when the sole child is closed; the epic's P1-P3 sections are

#### [P2] manifest_hygiene_red_2026_07_03.md ↔ plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md

- finding ids: 391
- **mechanical:dangling_ref** —
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:23`: “related:
  [../data_pipeline_hardening_self_monitoring_2026_06_22.md, manifest_hygiene_red_2026_07_03.md]” vs `-`: “file not
  found anywhere under plans/ (no manifest_hygiene_red_2026_07_03.md exists in active/issues, archive/issues, or
  archive; nearest matches are d”
  - why: The related field cites a specific issue doc by filename that does not exist anywhere in the plans corpus. The
    referencing doc's own body explains this is because the 2026-07-03 escalation artifact was left dirty/untracked and
    later wiped by a tree-clean before being committed (illustrating the very bug the issue descr

#### [P2] plans/PLAN_FORMAT.md ↔ plans/active/mvp_reconciliation_closeout_v10_2026_06_27.md

- finding ids: 383
- **SSOT location for the plan-archival '5-step ritual'** —
  `plans/active/mvp_reconciliation_closeout_v10_2026_06_27.md:47`: “`plans/PLAN_FORMAT.md` + `plans/epics/README.md` —
  archival 5-step ritual; plan-hygiene QG.” vs `plans/PLAN_FORMAT.md:57-69`: “## Archive Criteria by Plan Type ...
  **Archive eligibility rule:** A plan is eligible for archive when ALL repos in `repo_gates` have reached the gate”
  - why: Multiple active docs (this one and active/issues/plan_issue_epic_consolidation_2026_06_30.md:191) cite
    PLAN_FORMAT.md + epics/README.md as the SSOT housing the 'archival 5-step ritual' (migrate DEFERRED → banner →
    codex-alignment check → update CLAUDE.md/codex → clear lock). PLAN_FORMAT.md's actual archival content is

#### [P2] plans/active/bucket_env_split_rollout_2026_06.md ↔ plans/epics/infrastructure_master.md

- finding ids: 356
- **Epic's related_plans list vs. child plans' declared parent_epic** — `plans/epics/infrastructure_master.md:26-40`:
  “related_plans: [mvp_reconciliation_closeout_v10_2026_06_27.md, cicd_mvp_ldr_to_main_pipeline_2026_06_30.md, ...] (no
  mention of bucket_env_split_rollo” vs `plans/active/bucket_env_split_rollout_2026_06.md:18`: “parent_epic:
  infrastructure_master”
  - why: Both bucket_env_split_rollout_2026_06.md and bucket_iam_write_protection_per_tier_2026_06_09.md (both status:
    active, P1, locked_by live-defi-rollout since 2026-06-09) declare parent_epic: infrastructure_master, but
    infrastructure_master.md's related_plans/related frontmatter list (lines 15-21, 26-33) does not include

#### [P2] plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md ↔ plans/epics/infrastructure_master.md

- finding ids: 354
- **Current SSOT location/owner for bucket naming (which doc 'owns' the bucket-naming SSOT)** —
  `plans/epics/infrastructure_master.md:645`: “`plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` |
  Bucket naming SSOT (`resolve_bucket_name()` only; never inline `gs://` f-str” vs
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:427-428`: “UAC is now named the canonical
  SSOT in `cursor-configs/CLAUDE.md` § Bucket-name SSOT + `/codex/02-data/bucket-naming-and-config.md`
  (deployment-service”
  - why: infrastructure_master's own 'Codex SSOTs' table (a list of docs that supposedly still 'own' live conventions)
    lists an ARCHIVED plan as the thing that 'Owns' the bucket-naming SSOT, with no pointer to the actual current SSOT
    location. bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (active, P0, same corpus

#### [P2] plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md ↔ plans/epics/mtds_mdps_master.md

- finding ids: 355
- **Epic's child-plan tracking vs. an active plan's declared parent_epic** — `plans/epics/mtds_mdps_master.md:37`:
  “related: [..., bucket_name_ssot_canonicalisation_2026_05_10.md, ...]” vs
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:19`: “parent_epic: mtds_mdps_master”
  - why: bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md is a P0, actively-locked (locked_since
    2026-06-01), 557-line plan that declares mtds_mdps_master as its parent_epic and explicitly 'reopens' the archived
    plan the epic still lists in its related/frontmatter. Yet mtds_mdps_master.md never references bucket_nam

#### [P3] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md (intra-doc)

- finding ids: 352
- **Doc's own '## Codex SSOTs' header list left uncorrected against its own later self-correction** —
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:265`:
  “`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + regen + ingestion contract.” vs
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:709-711`: “real doc is
  `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, not the stale
  `12-agent-workflow/...single-vm-architecture.md` in t”
  - why: This still-active plan's Progress Log entry explicitly flags its own Codex-SSOTs section's citation as stale
    and names the real replacement doc, but the '## Codex SSOTs' header block itself (line 265) was never edited to drop
    or replace the flagged citation — a self-acknowledged drift left live and uncorrected in the s

#### [P3] active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md (intra-doc)

- finding ids: 24
- **last_updated frontmatter vs progress-log status-flip date (intra-doc)** —
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:24`: “last_updated: 2026-07-08” vs
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:84`: “**2026-07-10** — **Status-flip note**: all 4
  todos confirmed `[x]` with cited evidence ... Flipped `status: active` → `complete`.”
  - why: The frontmatter `last_updated` field still reads 2026-07-08 even though the doc's own Progress Log records a
    status change (active→complete) two days later on 2026-07-10 — the frontmatter timestamp wasn't bumped alongside the
    status flip.

#### [P3] active/is_catalogue_completion_2d_2026_07_06.md (intra-doc)

- finding ids: 112
- **Frontmatter last_updated predates the doc's own newest Progress Log entries** —
  `active/is_catalogue_completion_2d_2026_07_06.md:28`: “last_updated: 2026-07-06” vs
  `active/is_catalogue_completion_2d_2026_07_06.md:314`: “- **2026-07-07** — **B2 downstream FLIPPED (slot-2
  opus/max).** Wired enumerate_expected_universe.py to the shipped UAC SSOT”
  - why: The frontmatter declares last_updated: 2026-07-06, but the body's Progress Log contains multiple entries dated
    2026-07-07 (B2 downstream flip, MVP-tagging-verify fix) that are chronologically after the declared last-updated
    date — a stale metadata field on the doc's own record of its latest edits.

#### [P3] active/issues/cefi_layer1_denominator_gaps_2026_07_03.md (intra-doc)

- finding ids: 63
- **Frontmatter last_updated predates a body entry dated after it** — `43`: “last_updated: 2026-07-06” vs `208`:
  “COINBASE / DERIBIT-COMBO MVP_SCOPE membership — RESOLVED 2026-07-10 (operator decision #6: "keep both declared")”
  - why: The frontmatter's last_updated field (2026-07-06) is earlier than a body todo explicitly dated 2026-07-10
    (operator decision #6 resolving the COINBASE/DERIBIT-COMBO MVP_SCOPE question), meaning the doc was substantively
    edited after the recorded last_updated timestamp without the field being bumped. Any tooling that us

#### [P3] active/issues/fleet_data_acquisition_health_2026_06_21.md (intra-doc)

- finding ids: 81
- **Frontmatter last_updated date vs a later dated body revision** —
  `active/issues/fleet_data_acquisition_health_2026_06_21.md:30`: “last_updated: 2026-06-27” vs
  `active/issues/fleet_data_acquisition_health_2026_06_21.md:56`: “REVISED 2026-07-10 (operator): fix properly, don't
  paper over the inconsistency with a tolerant fallback.”
  - why: The frontmatter claims the doc was last touched 2026-06-27, but the body contains a revision explicitly dated
    2026-07-10 (13 days later) revising the recommended fix for bug #2. The last_updated field was not bumped when the
    body was edited, so any staleness/triage tooling keying off last_updated would under-count this

#### [P3] active/issues/instrument_id_format_canonicalization_2026_07_08.md (intra-doc)

- finding ids: 97
- **Section header claims 6 findings; body enumerates 8** —
  `active/issues/instrument_id_format_canonicalization_2026_07_08.md:73`: “## The 6 real divergences found, and their
  target canonical format” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:219`: “8. **RESOLVED
  2026-07-08 (was: "Prediction's per-market instrument_id is genuinely opaque, and its enrichment columns are 100%
  empty").**”
  - why: The doc's section header still says '6 real divergences' but findings 7 and 8 were added later per this doc's
    own Progress Log — cosmetic count drift that could make a skimming reader underestimate scope.

#### [P3] active/issues/instruments_remaining_work_audit_2026_07_10.md ↔ active/tradfi_v9_stage1_finish_2026_07_06.md

- finding ids: 107
- **tradfi_v9_stage1_finish open-task count (6 of 11) and orphan-sweep blocking-reason vs the plan's own current c** —
  `active/issues/instruments_remaining_work_audit_2026_07_10.md:347-350`: “tradfi_v9_stage1_finish — AO Plan 2 ... 6 of
  11 unchecked ... orphan sweep (blocked on manifest rebuild ordering), straggler VM re-run ...” vs
  `active/tradfi_v9_stage1_finish_2026_07_06.md:94-215`: “🎯 GATE MET 2026-07-10 17:17:22 UTC ... orphan_class_E=0 ...
  Checkbox FLIPPED — the literal gate is genuinely, corpus-wide met”
  - why: By the time task 2 (orphan sweep) checkbox is flipped done, only 5 of 11 tasks remain unchecked (3,4,6,10,11),
    not 6, and the sweep is no longer 'blocked on manifest rebuild ordering' (that ordering block was resolved back on
    2026-07-07 per the plan's own history). This may simply reflect the audit doc being authored e

#### [P3] active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md (intra-doc)

- finding ids: 231
- **Self-contradictory 'stale path' description within Finding 1** —
  `active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md:66`: “Rewrite all four referrers
  `architecture-v2/cross-cutting/pnl-attribution.md` → `architecture-v2/cross-cutting/pnl-attribution.md`.” vs
  `active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md:43`: “The actual doc lives at
  **`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`** (64 KB, the canonical PnL-attribution SSOT)”
  - why: The doc's own recommended-decision line instructs rewriting a path into the identical path (X → X), and the
    sentence introducing the 'correct' target repeats the exact same path string used earlier as 'does not exist'. The
    described stale path was almost certainly `operational/pnl-attribution.md` but an edit pass appea

#### [P3] active/issues/sports_data_capture_gap_2026_06_29.md (intra-doc)

- finding ids: 280
- **Frontmatter date ordering (last_updated / locked_since predate created)** —
  `active/issues/sports_data_capture_gap_2026_06_29.md:13`: “created: 2026-06-29” vs
  `active/issues/sports_data_capture_gap_2026_06_29.md:23-24`: “last_updated: 2026-06-27 locked_since: 2026-05-21”
  - why: The doc's own frontmatter has last_updated (2026-06-27) and locked_since (2026-05-21) both before its created
    date (2026-06-29), which is internally impossible and indicates copy-pasted/unmaintained frontmatter dates.

#### [P3] active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md (intra-doc)

- finding ids: 266
- **impossible frontmatter date ordering** —
  `active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md:20`: “created: 2026-06-29” vs
  `active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md:30-31`: “last_updated: 2026-06-27
  locked_since: 2026-05-21”
  - why: last_updated (2026-06-27) and locked_since (2026-05-21) both predate the doc's own created date (2026-06-29),
    which is logically impossible -- a copy-paste frontmatter error that would mislead any date-based sorting/staleness
    tooling.

#### [P3] active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md (intra-doc)

- finding ids: 307
- **Frontmatter/lede summary stale vs. body's own resolution progress** —
  `active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md:4`: “The tradfi `expected_unattempted` (EU) is
  dead-flat at **1,084,542** while a multi-VM CME/NYSE/NASDAQ databento backfill campaign burns compute.” vs
  `active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md:140`: “EU journey: 1,084,542 → 336,061 (massive)
  → 1,349 (MVP).”
  - why: The doc's frontmatter `summary:` and opening line still describe the EU as 'dead-flat at 1,084,542', but the
    doc's own later Progress Log records that the same session drove EU down to 336,061 and then to a durable 1,349 via
    an executed operator decision + code fixes. The headline framing (still the first thing a reade

#### [P3] active/prediction_capture_incident_remediation_2026_07_06.md (intra-doc)

- finding ids: 373
- **Freshness of the plan's own frontmatter metadata vs. its Progress Log** —
  `active/prediction_capture_incident_remediation_2026_07_06.md:52 (frontmatter last_updated)`: “last_updated:
  2026-07-06” vs `active/prediction_capture_incident_remediation_2026_07_06.md:264-272`: “2026-07-10 — Phase 0 CLOSED
  for real (sub-agent verification pass, part of the instruments-completion-tracker sweep). ... read
  gs://market-data-tick-c”
  - why: The plan's frontmatter last_updated field (2026-07-06) disagrees with its own body, which carries a substantive
    Progress Log entry dated 2026-07-10 (a Phase-0 closure verification with new evidence). A doc-freshness/index
    consumer (e.g. the L0 doc index or a staleness check) reading only the frontmatter would treat thi

#### [P3] active/sports_p1_golden_window_features_2026_06_27.md (intra-doc)

- finding ids: 263
- **P1d frontmatter last_updated vs body Progress Log** — `active/sports_p1_golden_window_features_2026_06_27.md:21`:
  “last_updated: 2026-06-27” vs `active/sports_p1_golden_window_features_2026_06_27.md:459`: “### 2026-07-03 -- slot 5:
  Todo 4 (feature manifest clean) COMPLETE”
  - why: Frontmatter claims the doc was last updated 2026-06-27, but the body's own Progress Log contains dated entries
    through 2026-07-03 (and several 2026-06-29 entries) -- the last_updated field was never refreshed despite
    substantial later edits, which is misleading to any tooling or reviewer sorting/trusting that field.

#### [P3] active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md (intra-doc)

- finding ids: 253
- **Item #7's stale un-block-sequence text vs item #4 now being flipped done** —
  `active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:176-178`: “BLOCKED-PREREQUISITES
  (2026-07-08, slot-7)... item #4 and #5 must both reach pending_fetch=0 before this item can flip” vs
  `active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:1140`: “Gate MET — flipped item #4's
  checkbox ✅.”
  - why: Item #7's bullet text (last edited 2026-07-08) still frames itself as blocked on BOTH item #4 (understat) and
    item #5 (footystats), but the 2026-07-09 progress-log entry flipped item #4 to done — the item #7 checkbox/bullet
    was never rewritten to reflect that only item #5 now blocks it. Cosmetic/staleness rather than a

#### [P3] active/sports_reference_backfill_oom_2026_06_22.md (intra-doc)

- finding ids: 281
- **Plan status vs all-todos-done body** — `active/sports_reference_backfill_oom_2026_06_22.md:9`: “status: active” vs
  `active/sports_reference_backfill_oom_2026_06_22.md:63-80`: “[x] [SCRIPT] P1. Fix per-league skip-check to single
  index read... [x] [SCRIPT] P2. **DONE** Column-prune slim reads via `read_availability_index(colu”
  - why: Every todo in the plan body (including the follow-up marked 'DONE') is checked with shipped commit evidence and
    no remaining open item, but the frontmatter status is still 'active' rather than 'complete' — plan-hygiene drift
    that could cause the item to look like open work.

#### [P3] archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md ↔ epics/mtds_mdps_master.md

- finding ids: 141
- **Epic child-plan status vs the child plan's own frontmatter** — `epics/mtds_mdps_master.md:799-801`: “###
  [`mtds_per_instrument_download_api_2026_04_24`]... **status**: active” vs
  `archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md:5`: “status: complete”
  - why: A third instance of the same systemic pattern: the epic's index still marks this archived/complete plan
    'active', confirming the epic's child-status table is stale across multiple entries, not a one-off typo.

#### [P3] epics/batch_live_symmetry_master.md (intra-doc)

- finding ids: 311
- **Stale 'stub, not yet filled' banner left in place on a heavily-populated, recently-updated epic** —
  `epics/batch_live_symmetry_master.md:49`: “Status: stub created 2026-05-21 by migrate_epics_2026_05_21.py. Operator
  fills body with P0/P1/P2/P3 priority blocks listing all assigned active plans” vs
  `epics/batch_live_symmetry_master.md:75`: “2026-07-08 canonical instrument_id — live!=batch findings”
  - why: The doc still carries its original 2026-05-21 auto-generated 'stub created... Operator fills body' placeholder
    line as if the body were still empty, but the same document (last_updated 2026-07-08 per frontmatter) already
    contains detailed P0 findings, P1 BLRS recon-gate todos, and multiple archived-plan summaries below

#### [P3] epics/features_and_ml_master.md (intra-doc)

- finding ids: 317
- **frontmatter last_updated vs body edit date (intra-doc)** — `epics/features_and_ml_master.md:52`: “last_updated:
  2026-05-21” vs `epics/features_and_ml_master.md:211`: “## Tier-violation cleanup (slot 7, 2026-06-01 — surfaced during
  dependency-alignment)”
  - why: Two whole sections (Tier-violation cleanup; DeFi data-loading dispatch) are dated 2026-06-01, after the
    frontmatter's last_updated of 2026-05-21 — stale metadata that understates how recently the doc was actually edited.

## C. Structural gaps (coverage critic)

1. **Epic-registry completeness never enforced**: `epics/README.md` declares itself SSOT with a closed 20-epic table
   (2026-05-21) but live epics (agent_operating_framework_master, escalation_and_disaster_recovery_master) are absent —
   nothing regenerates or validates the table.
2. **Cross-epic handshake tables are asymmetric**: 'Composition with other epics' sections disagree between epic pairs.
3. **Client-funds-isolation HARD RULE** has no in-corpus contradiction but also no plans-corpus coverage tying it to the
   transfer plans — worth an explicit cross-reference pass.
4. **Several CLAUDE.md HARD RULES have no dedicated codex SSOT doc** (named inline only) — codex additions need operator
   sign-off (Section A applies).

## D. Bonus finding (outside plans corpus)

`cursor-configs/skills/git-commit/SKILL.md` instructs the `plan(<plan-name>):` commit prefix for plan flips, while
CLAUDE.md + SUB_AGENT_MANDATORY_RULES.md mandate `docs(plans):` and state `plan(...)` is hook-rejected. One of the three
is wrong; recommend updating git-commit SKILL.md to `docs(plans):` (matches the enforcing hook).

## A2. OPERATOR RULINGS — 2026-07-12 interactive Q&A (ALL 84 parked pairs ruled)

Recorded verbatim from the chat Q&A session; each ruling is binding for the reconciliation edits below. Execution status
tracked in the Progress Log.

| Finding(s)      | Ruling                                                                       | Execution                                                                                                                                |
| --------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 228 (+27)       | Tardis billing IS LIFTED (unlimited access confirmed)                        | close cefi_tardis_historical_blocked_credentials as resolved; correct blocked framings; 775.9k-cell backfill dispatchable                |
| 66              | instrument_type canonical casing = UPPERCASE                                 | corrective todo: fix BYBIT-SPOT mapping + relabel script to SPOT_PAIR BEFORE the -003 relabel runs                                       |
| 144             | Sports gate breach: RATIFY + VERIFY                                          | verify launched VMs wrote v9-canonical; if clean record waiver in both docs; if not escalate                                             |
| 171             | M-C2 DOWNGRADE stands (latent, not active bug)                               | fix mtds_plan_reconciliation Progress Log reversal                                                                                       |
| 246/247         | VERIFY P1d first                                                             | check P1d features status; then set P1e gate verdict accordingly                                                                         |
| 286/292         | LOGIC FREEZE LIFTED ENTIRELY                                                 | strategy_master freeze removed (lifted 2026-07-12 per operator); post green UNFREEZE ping; F27 + frozen fixes dispatchable               |
| 376             | Fireblocks OUT of June-1 scope                                               | fix defi_master custody section; close Fireblocks todo as descoped-per-POD                                                               |
| 128             | TradFi G4: MANIFEST SPOT-CHECK decides                                       | run tradfi raw-tick v9 coverage check; correct losing banner; split RESUME-runbook sub-part                                              |
| 149             | cefi F2: VERIFY CODE + collapse losing passage                               | read \_rollup_bundle_grain in instruments-service HEAD                                                                                   |
| 367             | G12 recon-freeze subscriber -> P0                                            | move to execution_master P0 must-complete section                                                                                        |
| 87              | Narrow 'can never red' claim + bump off P3                                   | pm_scripts_typecheck_debt edit incl. zero-warning-policy caveat                                                                          |
| 46              | Phase-D gate checkbox REOPENED                                               | revert to [ ] + dependent real-data re-run todo                                                                                          |
| 254             | Sports-scheduler: VERIFY live write-target first                             | read-only check on running scheduler; docs follow reality; legacy-writes => escalate                                                     |
| 113             | EULER_V2: VERIFY code first                                                  | read defi_venues.py + capture path; reconcile both docs to ground truth                                                                  |
| 15/365/17       | Correct headline; scope epsilon=0 PROVEN to paper<->batch                    | Phase 2 stays open                                                                                                                       |
| 95              | G1: FINISH G1.2 FIRST, then stamp                                            | dispatched to separate operator-run agent (prompt delivered in chat)                                                                     |
| 30              | DELETE Deribit per-strike artifacts + ensure chain-level capture grain       | snapshot-first purge todo + grain regression check                                                                                       |
| 77              | REMOVE aster/hyperliquid book/liq SOURCE_PRIORITY registration               | UAC corrective todo                                                                                                                      |
| 305             | Massive Phase-4b DOWNGRADE to P2 + annotate                                  | databento-primary SSOT cited                                                                                                             |
| 353             | Env-split WINS                                                               | bucket_name_ssot repointed at bucket_env_split_rollout as authority                                                                      |
| 339             | REGENERATE epic registry (true count 23)                                     | rebuild README table + orchestrator count + regeneration-script todo                                                                     |
| 216/323         | REGENERATE orchestrator census                                               | run/replicate the census script                                                                                                          |
| 175/142/146     | ENFORCE 2 survivors                                                          | fold-in/archive mapping authored as HUMAN plan for operator approval; sports_manifest stays mtds_mdps child, sports_master wording fixed |
| 10010           | CODIFY /autonomous model-tier carve-out                                      | codex model-tier-selection.md + CLAUDE.md one-liner (authorized codex edit)                                                              |
| 357             | DOCUMENT sports-scheduler SPOT carve-out                                     | codex spot-vms-for-backfill.md (authorized codex edit)                                                                                   |
| 341             | FORMALISE '/' as Betfair native convention                                   | checklist P2 closes by-design                                                                                                            |
| 78              | MAKE SIT BLOCKING                                                            | P1 todo: wire SIT-green as required check on promote PR; claim restored only after                                                       |
| 224             | VERIFY AO deploy path on the VM first                                        | then correct todo/notes to reality                                                                                                       |
| 218             | FLIP the 3 evidenced prevention todos                                        | issue stays open on remaining 3                                                                                                          |
| 366             | FULL RE-AUDIT of global_ledger epic                                          | authored as HUMAN plan (assigned_vm: NA)                                                                                                 |
| 83              | ADD --dry-run cross-ref to watchdog relaunch item                            |                                                                                                                                          |
| 74              | RETIRE harsh_pc framing (frontmatter NA correct)                             |                                                                                                                                          |
| 134/132         | parent_epic = manifest_master; fix body line                                 |                                                                                                                                          |
| D               | FIX git-commit SKILL.md to docs(plans):                                      | cursor-configs edit                                                                                                                      |
| codex-gap       | CREATE /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md | + SUPERSEDED-banner the stale multi-vm doc (authorized)                                                                                  |
| schema          | ADD 'paused' epic status                                                     | schema doc + validator; then flip escalation epic to paused                                                                              |
| 50 reclassified | APPLY ALL 50 evidence-resolved autofixes                                     | fixer wave, refusal contract applies                                                                                                     |
| B-queue         | PROCEED P1->P2->P3 original auto-fix waves (163 remaining pairs)             |                                                                                                                                          |
| new plans       | BOTH new work items = HUMAN plans (assigned_vm: NA)                          | global-ledger re-audit + MTDS fold-in mapping                                                                                            |

## Progress Log (append-only)

- 2026-07-14 (verify-rerun-2 CLOSE-OUT — all 163 confirmed findings dispositioned): the 2026-07-13 verification re-run
  (163 confirmed: 10 P0 / 66 P1 / 59 P2 / 28 P3; 57 refuted; 10 plausible-unverified; coverage caveats — re-hunts
  partially failed under session limits, 4 tiebreaks + completeness critic never ran, so 163 undercounts) is now fully
  worked: P0s 63/53/113 inline (PM@432a0c71a); P0 pair 215+127 (footystats-reversal sync + row-loss issue resolved,
  PM@f3321cbc4-rebased); P0 pair 197+220 (catalogue G2 registry + PLAN_FORMAT epic assigned_vm, PM@697ad61e3); P0s
  152/154/196 adjudicated per-claim against post-dating events (cross-cutting doc corrected — relabel/rebuild claims
  STALE for sports/tradfi/defi, cefi NOT adjudicated (no fresh CF-audit), E8/legacy-deletes STILL-LIVE, PM@98555eb99).
  153 P1-P3 findings union-find-chunked into 15 disjoint fixer waves, all applied + pushed: chunk 0
  (e217ade9b/269153dc2/67f59b944), 1 (5fe1e98d9), 2+3 (10a704cd8 — chunk 3's commit absorbed, content verified), 4
  (3872662ef/717cfcd47/3219c10d6/378f89b6f/ea26e1644/63e8b11f7/8025a34d0/01e12b3d6), 5 (89f00fde9), 6 (70adff9d1), 7
  (c40143447/cfbde900a), 8 (13d29f946), 9 (eef15a1d5 — incl. an honesty UN-flip of a wrongly-[x] P0 config-grid run,
  finding 36), 10 (2460d4bc0), 11 (b9556edc8), 12 (c934a7ed0), 13 (7fcc70b70), 14 (932ffcf8e). Incidents during the
  wave, all resolved: (a) a stale-tree index race produced commit 0e5f533b6 carrying 3 foreign files' PRE-fix content —
  its revert b7da88fbf was CORRECT (restored the fixes); the orchestrator's own re-apply false-alarm was caught and
  reversed with zero residue; (b) deterministic prettier emphasis-mangling root-caused (code span split across a line
  break + unbackticked underscore identifiers → underscores rewritten as asterisks, paragraphs collapsed): repaired +
  made prettier-stable in instruments_foundation_completeness (PM@169a8c8cd), propagated copies in 2 active plans + 4
  audit-instruction docs dispatched to a fixer (archive copies left as historical record). Operator-gated leftovers
  parked (see session report): STEP 5.91 + STEP 5.86 QG-step collisions (228/227, renumbering needs a ruling),
  tradfi-databento codex SSOT stale VIX-15m sourcing rows (217, CODEX-GATED), wsfeedconnector ownership routing (126),
  mvp_catalogue archival (130, locked_by), G3 homeless-consolidator re-scope-vs-close (182), [UI] tick with [BACKEND]
  evidence (56), instruments_completion_tracker D6 still ⏳ (residual). Separately during close-out: the 2026-07-13
  BITGET-FUTURES 6-VM wave was found FAILED on Tardis concurrent-IP lockout (launched without the lease) — correction +
  recurrence entries shipped PM@c31cdb81c.
- 2026-07-13 (§A2 findings 175/142/146 — MTDS/MDPS 2-survivor consolidation EXECUTED): the fold-in/archive mapping
  authored in `mtds_consolidation_foldin_mapping_2026_07_12.md` (per the "ENFORCE 2 survivors" ruling) received its HARD
  GATE approval — operator ruling verbatim: "Approve all + unlock" (blanket `[unlock-plan]` for every locked candidate);
  todo-5 judgment call (`defi_manifest_canonicalisation_2026_06_01`) = "FOLD → M-1";
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` = "KEEP standalone";
  `mdps_features_reduced_artifact_tracker_2026_06_28` = "Keep as tracker"; `sports_manifest_canonicalisation_2026_06_01`
  = KEEP per this same ruling's original 175/142/146 text (unchanged). Executed in full: **9 plans folded into M-1**
  (`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`, `data_source_provenance_all_asset_groups_2026_06_01`,
  `macro_econ_adapter_scaffolds_2026_06_09`, `cefi_manifest_canonicalisation_2026_06_01`,
  `tradfi_manifest_canonicalisation_2026_06_01`, `prediction_manifest_canonicalisation_2026_06_01`,
  `downstream_services_manifest_canonicalisation_2026_06_01`, `defi_manifest_canonicalisation_2026_06_01`,
  `bar_edge_left_vs_right_remediation_2026_06_08` — 130 open todos migrated verbatim with provenance into M-1's new
  "Folded-in scope 2026-07-13" section, each archived to `plans/archive/2026_07/` — unified-trading-pm@e4dd7871e); **1
  plan credited into M-2** (`mdps_polars_engine_cost_sharpening_2026_06_28`) + **4 plan-hygiene-debt plans
  simple-archived** (`mdps_book_microstructure_precompute_columns_2026_06_28`,
  `mdps_features_full_month_benchmark_binance_2026_06_28`, `tradfi_mdps_passthrough_dependency_gap_2026_06_28`,
  `solana_defi_legacy_migration_2026_05_27` — stale `status: active` corrected to `complete` + unlocked —
  unified-trading-pm@4336c38f6); 10 codex docs repointed off the now-archived paths +
  `pipeline_mode_source_batch_live_replay_standardisation` banner + tracker rows + `epics/mtds_mdps_master.md`
  consolidation-executed banner (unified-trading-pm@8eb5293b3). **"sports_master wording fixed" pointer** (the paired
  item from the original 175/142/146 ruling, not executed by the foldin-mapping plan per its own scope note):
  `sports_manifest_canonicalisation_2026_06_01.md` itself was confirmed untouched (correct — KEEP-WITH-JUSTIFICATION);
  the `sports_master` epic-body wording fix referenced by the original ruling still needs a direct edit to
  `plans/epics/sports_master.md` by whoever next touches that epic — filed here as the pointer since this plan's scope
  explicitly excluded executing it directly. Full mapping + per-plan justification:
  `mtds_consolidation_foldin_mapping_2026_07_12.md` (now `status: complete`).
- 2026-07-12 (dev sports-fixtures OOM todo CLOSED — mirrored, not descoped): confirmed dev is genuinely consumed, not
  dead weight — `uts-dev-{sports,features,instruments,cefi}-*-t1-schedule` Cloud Scheduler entries (4x/day: midnight,
  6am, noon, 6pm, matching prod's cadence exactly) are ENABLED and firing every 6h in the SAME `central-element-323112`
  project as prod (dev is a same-project `uts-dev-` prefix tier for pre-prod batch/cron validation, not a
  separate-GCP-project tier like deployment-ui's dev/staging/prod split).
  `gcloud run jobs executions list --job=uts-dev-instruments-service-sports-fixtures`: 338/338 executions failed since
  job creation (2026-04-19), 100% failure rate, never once succeeded. **Root-caused past the operator's OOM framing**:
  Cloud Logging showed `Container called exit(2)` (a clean argparse exit), never `Container terminated on signal 9`
  (prod's actual pre-fix OOM signature) — so the dev job was NOT OOM-killed at all. `gcloud run jobs describe` diff vs
  `uts-prod-instruments-service-sports-fixtures` showed dev's baked-in container args used a stale `--category=SPORTS`
  flag; grepped `instruments-service` CLI (`unified_trading_library/service_cli.py:347` calls strict
  `parser.parse_args()`, and `--asset-group` — not `--category` — is the only registered filter flag,
  `unified_trading_library/service_framework/... `) confirms an unrecognized flag under strict `parse_args()` always
  hits argparse's `sys.exit(2)` path before any app code (incl. the memory-heavy fetch loop) ever runs — matching the
  observed exit(2) signature exactly and explaining why raw cpu/mem alone would not have fixed it. Also
  `instruments_service/cli/instruments_handler.py:126-128`: `asset_groups = cli_asset_groups or ["ALL"]` — even if the
  stale flag hadn't crashed the parse, dropping `--asset-group=SPORTS` would have silently widened the run to ALL asset
  groups (CEFI+DEFI+TRADFI+SPORTS+PREDICTION), which IS a real OOM risk at small cpu/mem (the exact all-AG workload
  `terraform/gcp/t1_batch_scheduler.tf:41-45` documents as having OOM'd prod at 8cpu/32Gi previously). Env var also
  drifted (dev: `ENVIRONMENT=dev`, prod: `DEPLOYMENT_ENV=prod`) but was inert — `bucket_naming.py:128-140` falls back
  `DEPLOYMENT_ENV` → `ENVIRONMENT` → `prod` default, so dev was already resolving `dev` correctly via the fallback;
  fixed anyway for exact prod-shape parity. **Fix applied**
  (`gcloud run jobs update uts-dev-instruments-service-sports-fixtures --region=asia-northeast1`): cpu 2→8, memory
  4Gi→32Gi, args `--category=SPORTS`→`--asset-group=SPORTS` (mirrors prod's exact 5-arg list), env `ENVIRONMENT=dev`→
  `DEPLOYMENT_ENV=dev` (mirrors prod's exact 4-var set, same GCP_PROJECT_ID/GCS_LOCATION/PYTHONUNBUFFERED).
  **Verified**: `gcloud run jobs execute uts-dev-instruments-service-sports-fixtures --region=asia-northeast1 --wait` →
  execution `uts-dev-instruments-service-sports-fixtures-xchgv` completed successfully in 3m26.46s, `succeededCount: 1`,
  `status.conditions[].type=Completed status=True` — first success in the job's history (post-fix spec re-`describe`d to
  confirm args/env/resources landed as intended). Evidence: gcp_project=central-element-323112,
  execution=uts-dev-instruments-service-sports-fixtures-xchgv, region=asia-northeast1.

- 2026-07-12 (finding 366 — global-ledger epic full re-audit COMPLETE): executed per §A2 ruling ("FULL RE-AUDIT of
  global_ledger epic... authored as HUMAN plan") via `plans/active/global_ledger_epic_reaudit_2026_07_12.md`.
  Claim-by-claim re-audit of `plans/epics/global_ledger_pnl_attribution_master.md` (10 claims + 2
  epic-internal-consistency bugs; full verdict table in that plan's Progress Log). Headline: the epic's claimed
  "Migration plan 0/27, Phase 7/8 DEFERRED-POST-CUTOVER" is CONTRADICTED-BY-CODE — real, tested
  InstructionLedger/PricingLedger/TransferLedger GCS writers + a paper-mode PassiveLedger synthesiser have SHIPPED, but
  through a SEPARATE plan (`plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`, parented under
  `batch_live_symmetry_master`, not this epic), not through the frozen migration plan (which correctly stays 0/27
  untouched). The live (non-paper) PassiveLedger per-event divergence-check listener is genuinely still unshipped
  (forward-carried as a new epic P3 todo). `EventType` enum is now 39 (not 37) at HEAD. VM-prefix claims BACKED (1
  cosmetic naming correction: `batch-live-recon-`, not `batch-live-recon-cron-`). greeks-service@b0b702d P2 item
  re-verified BACKED, no regression. All 4 codex SSOT docs exist/current (contradicts the epic's "DEFERRED-POST-CUTOVER"
  framing); one codex-internal stale sub-claim found (`global-ledger-architecture.md` still calls
  `build_attribution_rows()` a "stub") and flagged CODEX-GATED (not edited — operator-gated, new todo filed in the
  re-audit plan for a follow-up session). **GOVERNANCE-GATE: NO BREACH (initial suspicion overturned on deeper
  verification)**: the audit's first pass found no operator-ack record for the discovery plan's 3 gated decisions (Phase
  3 late-arriving-data / Phase 5 greeks-home / Phase 6 TreasuryLedger split) and provisionally escalated; a
  PM-git-history search then FOUND the ack — `unified-trading-pm@351a47b61` (2026-05-23 20:42 +0100, "6 operator-ACK'd
  decisions"), recorded in `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § "Operator decisions
  (ACK'd 2026-05-23)". Gate properly cleared ~4 weeks before any Phase 7/8 code shipped; shipped code CONSISTENT with
  the acks; escalation WITHDRAWN. Real finding = doc-sync: the ack lived only in the MTDS plan while the epic +
  discovery archival banner said "[ack] pending" for 7 weeks (now fixed in the epic with citations). Bonus discovery
  from the ack record: the acked `ledger_type=treasury/` partition (fund-administration-service writer) is itself still
  unimplemented at HEAD — forward-carried as a second epic P3 todo. Epic synced in place (`last_updated` bumped to
  2026-07-12, all STALE/CONTRADICTED-BY-CODE claims corrected with "(was: …)" + evidence citations) — commit pending via
  the orchestrator (this agent runs no git commands per its instructions).

- 2026-07-12 (LEFTOVER QUEUE CLOSED, final Q&A round): operator ruled all 4 remaining items. (1) codex finding 346 FIXED
  — shard-level-failure-isolation.md synced to the 4-category taxonomy, validation-and-errors.md §1 named SSOT. (2)
  Three sync edits applied: CLAUDE.md URDI "phantom" label RETIRED (module verified load-bearing in 6+ adapters);
  manifest-consolidator-ssot.md 120s-blanket corrected to per-AG budgets (cefi=86400s per deployment-api@90ace9f);
  ao-self-pull.sh documented in both AO codex docs. (3) Template-gap ruled two-track-stands: data_eng_role_vertical
  pilot execution_scope corrected to local-only (validated). (4) E8 re-run EXECUTED live: stale-snapshot hypothesis
  CONFIRMED for the 2026-06-27 claims (rows ~5x understated; CF-1 GREEN live both surfaces) but walk NOT C-GREEN — real
  remaining gaps (CF-8, IS CF-3 19,274/CF-4 796,523 blanks, L6 legacy-only MTDS 140 + IS 1,855 NEW) pinned on the
  never-run E3 drain + E4 apply; full verdict tables appended to the sports canonicalisation plan. RECONCILIATION
  DISPATCH COMPLETE — no open items remain in this issue doc's queue beyond the tracked [ ] todos above.

- 2026-07-12 (FINAL WAVE COMPLETE): all 17 afix2 chunks processed — 191 findings across 161 original-auto-fix pairs:
  applied or verified-already-done in full; every edit evidence-re-verified (git shas, artifact reads, live manifest
  probes); notable closes: 8 stale-open issue docs flipped resolved with verified shas; 4 impossible-date-ordering
  frontmatter bugs; epic rosters regenerated/corrected across execution/infrastructure/mtds_mdps/observability/
  features/cefi/predictions/trading_agent epics; DRIFT perp_funding "3 dates" claim corrected via LIVE manifest read (8
  captured dates, 7.4M rows); Barchart ohlcv_15m retirement synced; INDEX.md header + caveat fixed. Sports prod deploy
  VERIFIED end-to-end (scheduler state unfroze; fixtures 3 consecutive successes; docs synced; dev-fixtures OOM
  side-finding filed as todo above). Corpus validators GREEN (frontmatter yaml + schema exit 0; 2 residual todo-format
  hits are pre-existing debt, untouched). NOTE for the record: during a mid-wave session-wide permission outage, the
  chunk 8/9-retry/11 fixers applied edits via Bash workarounds instead of halting (transparently flagged in their
  reports); operator said "continue" — their edits were retained and are content-verified, but the workaround behavior
  is logged here as a process deviation.

- 2026-07-12 (sports prod deploy, escalation ii COMPLETE): scheduler args fix tofu-applied (gen 2, state unfroze 10:40Z;
  discovery dispatched 16:45Z); prod fixtures job created 8cpu/32Gi, 3 consecutive successes incl. 2 unattended cron
  ticks; NEW side-finding: DEV fixtures job OOM-failing every run (~336 execs) at 2cpu/4Gi.
- [x] [INFRA] P2. Fix uts-dev-instruments-service-sports-fixtures OOM (mirror the prod 8cpu/32Gi bump or descope the dev
      cron) — side-finding from the 2026-07-12 prod deploy. — gcloud@central-element-323112 2026-07-12 + evidence below
      (MIRRORED, not descoped: real consumed dev tier, not dead weight — root cause was a stale `--category=SPORTS` arg,
      not raw OOM; both fixed).
- 2026-07-12 (rulings batch 4): P1e gate formally GREEN (re-audit PASS 0/0/0/0; gate doc + coordinator table + P2a/P2b
  ran-ahead notes applied — 246/247). Registry regenerated: 23 epics / 6 tiers, 4 superseded excluded, regen-script todo
  filed (339). Orchestrator census regenerated: 8 live children, was 'zero active' (216/323; NB the named populator
  script has a hardcoded stale macOS path — documented inline). Watchdog: 3 evidenced prevention todos flipped in
  ao_fleet_stall (218 — NB corrected pair mapping), dry-run safety xref added (83). AO deploy-model claims corrected in
  BOTH AO plans per VM-verified AUTO-PULL-LIVE verdict; DEPLOY todo split (224). git-commit skill prefix fixed to
  docs(plans): (finding D). Codex edits (authorized): /autonomous model-tier carve-out (10010), sports-scheduler SPOT
  carve-out (357), NEW agent-orchestrator-single-vm-architecture.md SSOT + SUPERSEDED banner on the multi-vm doc
  (codex-gap). Epic 'paused' status added to docspec + schema doc; escalation epic flipped to paused, validator-verified
  corpus-wide (schema ruling). AO repo: ao-self-pull allowlist + combined -u stash fix SHIPPED
  agent-orchestrator@5bf8ce5 (incident i interim fix; latent stash-orphan bug also fixed).
- 2026-07-12 (rulings batch 3 + LIVE INCIDENTS): TradFi G4 3-file correction applied (128: catalogue banner ->
  DONE-with-cleanup-tracked; migration_verification L719 split; RESUME-runbook owning todo added to
  tradfi_v9_stage1_finish, sequenced after fleet-drain). SIT-blocking P1 todo + gate caveat in cicd_mvp (78). BYBIT-SPOT
  UPPERCASE corrective todo, must land before -003 relabel (66). Recon plan headline corrected: Phases 0-1,3-11; eps=0
  scoped to paper<->batch (15/365/17). EULER_V2 two-doc reconciliation applied per code verification (113). Deribit
  purge + chain-grain todos filed in mvp_backfill_cefi_tick (30). P1e features re-audit EXECUTED: PASS 0/0/0/0 -> gate
  GREEN application in flight (246/247). TWO LIVE INCIDENTS found + operator-ruled: (i) AO ao-self-pull
  dirty-gate-jammed ~37h (regen-ldr-plans-\* dir written into repo tree); orchestrator was 4 commits stale -> service
  RESTARTED 2026-07-12 10:30:27Z (HTTP 200, HEAD fd9c002 loaded); interim allowlist + generator fix + wedge-alert
  hardening = open todos below; (ii) BOTH prod sports crons silently inert (fixtures job NOT_FOUND in prod; scheduler
  job generation-1 container, fix bb880b6 never applied) -> operator authorized deploy, infra agent dispatched.
- [x] [CODE] P1. AO: fix the regen-ldr-plans-\* generator to write under tempfile.gettempdir() (it litters the AO repo
      tree AND /tmp — same class as the 2026-07-10 /tmp-full incident); interim: add the dir pattern to ao-self-pull.sh
      AO_RUNTIME_CHURN_PATHS allowlist. Repo: agent-orchestrator. (Incident i above.) — agent-orchestrator@fc9ac53b.
      Root cause: `tempfile.mkdtemp(prefix=...)` (no explicit `dir=`) inherits `tempfile.gettempdir()`'s OWN fallback
      chain, which silently substitutes the process CWD (== the systemd service's repo checkout) when every real temp
      location is full/unwritable — exactly the observed incident. Added `_safe_tempdir_base()` (refuses the
      CWD-fallback, degrades to the PM working tree instead), `_sweep_orphan_snapshots()` (reclaims dirs orphaned by a
      hard-killed process — the /tmp-littering half), and a `try/finally` around snapshot creation (immediate cleanup on
      a mid-failure, not deferred to the next call). 5 new regression tests added
      (tests/test_regen_backlog_from_plan.py); quality-gates.sh green (1204 passed, ruff+basedpyright clean). The
      interim ao-self-pull.sh allowlist entry (5bf8ce5) STAYS as defense-in-depth; comment updated to note the root fix
      landed.
- [x] [CODE] P2. AO: harden ao-self-pull.sh wedge alert to also fire when the RUNNING process is stale N ticks while the
      checkout is current (today it only alerts on checkout behind>=10). Repo: agent-orchestrator. (Incident i.) —
      agent-orchestrator@fc9ac53b. Added a per-tick counter (state file, same /tmp convention as `AO_WEDGE_STATE`) that
      fires a deduped Slack alert (shared `_post_wedge_slack_alert` — same webhook path, separate dedup statefile so it
      never suppresses/is suppressed by the drift-based alert) once the stale-process self-heal hasn't resolved the
      process<->HEAD gap for >=3 consecutive ticks (`AO_STALE_PROCESS_ALERT_TICKS`, default 3). Verified via `bash -n` +
      a scratch-repo dry run (fake `systemctl`/`curl`): no alert on ticks 1-2, alert fires at tick 3, dedup suppresses
      tick 4, tick-counter clears once the self-heal actually resolves the staleness, and the pre-existing drift-based
      `_alert_wedge` still fires independently on a separate dirty+12-behind scenario (no cross-suppression).
- [ ] [DOCS] P2. Codex stub: ao-self-pull.sh is the production AO deploy mechanism but is absent from
      agent-orchestrator-overview.md / runtime-deployment-topology.md (codex edit — operator-gated, queue for next Q&A).
- 2026-07-12 (rulings batch 2): applied per §A2 — LOGIC FREEZE lifted in strategy_master (286/292; NB the freeze's
  UNFREEZE-ping channel \_agent_pings.md was retired 2026-07-04, so the epic banner + this ledger ARE the lift record);
  G12 -> P0 in execution_master (367); Fireblocks OUT in defi_master (376); Tardis pair closed/unblocked (228+27); cefi
  F2 Change-B collapsed after code verification PROVED fix live at is@4f5faae8 (149); M-C2 Progress Log corrected to the
  DOWNGRADE verdict (171); pm_scripts_typecheck claim narrowed + todo bumped P3->P1 (87); Betfair '/' formalised
  by-design (341); Massive Phase-4b P0->P2 (305); bucket flat-names defer to env-split authority (353); harsh_pc framing
  retired (74); manifest-cache parent epic fixed to manifest_master (134/132); Phase-D gate checkbox REOPENED +
  real-data re-run todo (46). Verifications completed: P1d COMPLETE but P1e formal re-audit missing -> re-audit
  dispatched (246/247); TradFi G4 apply DONE (GCS re-verified) but Stage-1 close-out open + RESUME runbook untracked ->
  corrections + owning todo in flight (128); EULER_V2 'never polled' CONFIRMED + NEW stalled-upstream blocker (~38 days
  behind) -> doc reconciliation in flight (113).
- 2026-07-11 (P0 batch): all 13 P0 auto-fix pairs applied + committed (this commit). Highlights: batch_live_symmetry P0
  section synced to complete child plans (18/19/337/363); epics/README registry+VM-model banner (308/309); orchestrator
  single-VM supersede notice (349); escalation epic PAUSED per 2026-06-26 deferral (338); plan_hygiene cron claim
  corrected to HISTORICAL outage + current-green per live gcloud check (227 — fixer refused the original stale wording,
  re-verified); instruments MTDS-WS caveat (93); defi Lighter/Extended/Pacifica -> CeFi per UAC mvp_scope.py decision
  log (37 — direction flip vs the planned fix, evidence-backed); features qg-sweep synced (54); v10 perp_funding IN-MVP
  ruling applied + 424 DRIFT cells reopened (43); sp500_ml VIX ruling applied (304); predictions intra-doc note fixed
  (239); sports P1a honest-coverage claim clarified as classification-not-presence (269); github_billing issue CLOSED
  with evidence chain (48 — secret-describe IAM-blocked, cent-exact reconciliation
  - code-read accepted as hard evidence).
- 2026-07-11: audit workflow completed (245 agents, 23.2M tokens; survived one /tmp-full kill + three host-process exits
  via journal resume). Findings archive: session scratchpad `findings.json` (+ backup in session dir). This doc created
  with full decision queue + auto-fix queue.
