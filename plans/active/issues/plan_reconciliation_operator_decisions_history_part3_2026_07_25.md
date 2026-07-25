---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — history part 3/4 (Section B auto-fix queue, P1-tail + P2-partial:
  downstream_services_manifest_canonicalisation↔mtds_mdps_master through
  instruments_completion_tracker↔cefi_layer1_denominator_gaps)"
summary:
  "Verbatim extraction of 68 of Section B's 176 auto-fix-queue finding entries (P1 tail + P2 partial) from
  `plan_reconciliation_operator_decisions_2026_07_11.md`, split for line-cap compliance (`plans/active/task_template.md`
  §3 finding J). Every finding here was applied per the parent's Progress Log (2026-07-11 through 2026-07-14 fixer
  waves) — this file is the closed raw finding text only, not live tracking. Zero open todos."
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift, history]
related: [/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md]
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

# Plans-corpus contradiction audit — history part 3/4 (Section B, findings 33-100)

> **Extracted verbatim 2026-07-25 →** this file, from
> `/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (line-cap remediation,
> `plans/active/task_template.md` §3 finding J — the parent was 3927 lines, over the 1000L hard cap). This is the THIRD
> of 4 history parts; see the parent doc for the full part index, the §A2 rulings table, Section C (structural gaps),
> Section D (bonus finding), and the Progress Log (which carries every currently-open todo — there are none in this
> file). Content below is byte-for-byte as it appeared in the parent's Section B, unedited.

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
