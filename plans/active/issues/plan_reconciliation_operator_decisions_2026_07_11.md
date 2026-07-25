---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — 320 verified findings (28 P0): operator decision queue + auto-fix
  reconciliation log (245-agent adversarially-verified sweep of plans/active + issues + epics)"
summary:
  "Full-corpus contradiction audit (307 docs read in full; epic-cluster + 16 topic sweeps + mechanical adjudication;
  every candidate adversarially verified by independent refuter+confirmer with tiebreak — 320 confirmed of 401
  candidates, 81 refuted). Findings split: 212 stale-drift / 102 true contradictions / 6 format-only; 28 P0. Section A =
  operator decision queue (each with options + recommendation; codex SSOT edits ALWAYS parked here) — ALL 84 pairs ruled
  (§A2). Section B = auto-fix queue applied autonomously with hard evidence (Progress Log records each batch + commit) —
  ALL 176 pairs applied. Section C = structural gaps from the coverage critic (still open, untracked elsewhere). Raw
  finding text for Sections A+B (3606 lines) extracted verbatim 2026-07-25 into 4 history-part companion docs for
  line-cap compliance; this parent keeps the frontmatter, provenance, §A2 rulings table, Sections C/D, and the Progress
  Log (which carries the one still-open todo)."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift]
related:
  [
    /plans/active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md,
    /plans/active/issues/plan_reconciliation_operator_decisions_history_part1_2026_07_25.md,
    /plans/active/issues/plan_reconciliation_operator_decisions_history_part2_2026_07_25.md,
    /plans/active/issues/plan_reconciliation_operator_decisions_history_part3_2026_07_25.md,
    /plans/active/issues/plan_reconciliation_operator_decisions_history_part4_2026_07_25.md,
  ]
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

**How to use (operator)**: Section A's 84 pairs are ALL ruled — see §A2 below. Section B's 176 pairs are ALL applied —
see the Progress Log below. Nothing in codex/ is edited without an explicit per-item ruling (recorded in §A2). This
parent is now a lean pointer + current-state doc; the raw finding text lives in the 4 history parts (below).

## History parts index (line-cap split, 2026-07-25)

> **Why this exists**: this doc was 3927 lines — massively over the `plans/active/issues/*.md` 1000L hard cap
> (`scripts/plan-hygiene/check_line_caps.sh`). The audit itself is closed (Section A 84/84 ruled, Section B 176/176
> applied — see §A2 + Progress Log); only Section C (4 structural-gap observations) and one Progress-Log todo are still
> genuinely open. Per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s FINAL RESOLUTION pattern, the
> closed raw finding text (Sections A + B, 3606 lines, 260 finding entries, ZERO checkbox todos) was extracted verbatim
> into 4 companion history docs. Conservation verified: `git show HEAD:<this path> | grep -c '^- \[[ xX~]\]'` = 4 (3
> done + 1 open); all 4 remain in THIS parent's Progress Log below — the history parts carry 0.

| Part                                                                                                                      | Covers                                                                                                                                                        | Findings | Lines |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------: | ----: |
| [`_history_part1_2026_07_25.md`](/plans/active/issues/plan_reconciliation_operator_decisions_history_part1_2026_07_25.md) | Section A, P0 + P1-partial (carry_staked_basis_funding_scan_experiment↔strategy_master → epics/README↔orchestrator_master)                                    |       59 |   941 |
| [`_history_part2_2026_07_25.md`](/plans/active/issues/plan_reconciliation_operator_decisions_history_part2_2026_07_25.md) | Section A tail (P1/P2/P3) + '## B.' heading + Section B P0/P1-partial (epics/client_isolation… → deployment_observability_expansion↔observability_master)     |       57 |   925 |
| [`_history_part3_2026_07_25.md`](/plans/active/issues/plan_reconciliation_operator_decisions_history_part3_2026_07_25.md) | Section B P1-tail + P2-partial (downstream_services_manifest_canonicalisation↔mtds_mdps_master → instruments_completion_tracker↔cefi_layer1_denominator_gaps) |       68 |   970 |
| [`_history_part4_2026_07_25.md`](/plans/active/issues/plan_reconciliation_operator_decisions_history_part4_2026_07_25.md) | Section B P2-tail + all of P3, end of Section B (instruments_completion_tracker↔instruments_master → epics/features_and_ml_master intra-doc)                  |       76 |   940 |

## A. OPERATOR DECISION QUEUE — 84 doc-pairs — ALL RULED (§A2, 2026-07-12)

> Raw finding text extracted verbatim 2026-07-25 → history parts 1-2 (table above). Every pair's ruling is in §A2 below;
> execution is tracked in the Progress Log below.

## B. AUTO-FIX QUEUE — 176 doc-pairs — ALL APPLIED (Progress Log)

> Raw finding text extracted verbatim 2026-07-25 → history parts 2 (tail)-4 (table above). Application batches +
> evidence (commit shas) are recorded in the Progress Log below.

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

- 2026-07-25 (LINE-CAP REMEDIATION — split, not archival): this doc was 3927 lines, over the `plans/active/issues/*.md`
  1000L hard cap (`scripts/plan-hygiene/check_line_caps.sh`). Read in full first to judge split-vs-archive per
  `plan_line_cap_remediation_2026_07_23.md`'s precedent: Section A (84/84 ruled, §A2) and Section B (176/176 applied,
  Progress Log above) are fully closed, but this doc is NOT a pure closed record — Section C's 4 structural-gap
  observations are still genuinely open/untracked, and the 2026-07-12 Progress Log carried one still-open todo
  (`[ ] [DOCS] P2. Codex stub: ao-self-pull.sh...`, below). That current-state kernel means archival (moving the whole
  doc to `plans/archive/`) would be wrong — a still-open todo would go dark. Chose SPLIT: extracted Sections A + B
  verbatim (3606 lines, 260 finding entries, 0 checkbox todos) into 4 companion history docs
  (`plan_reconciliation_operator_decisions_history_part{1-4}_2026_07_25.md`, all under 1000L — see "History parts index"
  above), leaving this parent with the frontmatter, provenance, §A2 rulings table, Section C, Section D, and the full
  Progress Log (all 4 of this doc's checkbox todos — 3 done, 1 open — stay here; conservation verified: original
  `git show HEAD:<path> | grep -c '^- \[[ xX~]\]'` = 4, history parts carry 0, parent carries 4, sum = 4). Result:
  parent 370L, all 5 files pass `check_line_caps.sh`.
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
