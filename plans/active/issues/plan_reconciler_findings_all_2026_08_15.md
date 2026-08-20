---
doc_type: issue
title: "plan_reconciler fresh full-corpus sweep — all 10 tranches, 2026-08-15"
summary: >-
  Fresh `/plan-reconcile all` sweep run interactively 2026-08-15, AFTER reconciling every prior tranche's residual
  findings doc first (see `operator_ruling_record_plan_reconcile_session_2026_08_15.md` for that pass's rulings). Covers
  all 10 tranches (ao, ci, tradfi, cefi, defi, cross-cutting, infra, prediction, sports, ui) via ~35 parallel read-only
  hunter sub-agents (several tranches self-partitioned into their own nested sub-batches given corpus size). Surfaced 1
  P0, ~45 P1s, and a long tail of P2/P3 hygiene findings. This doc is the durable home for that output — promoted from
  session scratchpad before a context compaction, per the workspace's own "durable = committed" rule. Findings were NOT
  yet applied at authoring time — this doc IS the backlog for that work. **STALE as of 2026-08-16 (plan_reconciler
  cross-cutting correction)**: the body has since accumulated 30+ dated DONE/APPLIED/RESOLVED entries with real
  shipped-commit citations from subsequent sessions (measured via grep 2026-08-16) — this doc is no longer a purely
  unapplied backlog; check each item's own body entry for its current status rather than trusting this summary line.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, all-tranches, fresh-sweep]
related:
  [
    /plans/active/issues/operator_ruling_record_plan_reconcile_session_2026_08_15.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-15"
parent_epic: plan_hygiene_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "Interactive session, operator-directed full-corpus /plan-reconcile fresh sweep, 2026-08-15 — 35+ parallel read-only
  sub-agents, several tranches self-partitioned (ao 5, tradfi 5, cefi 5, defi 5, cross-cutting 6, sports 5, infra 5+,
  prediction 3, ui 3+)."
drift_direction: fix
depends_on: []
context_scope:
  [
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/plans/active/issues/operator_ruling_record_plan_reconcile_session_2026_08_15.md,
  ]
---

# plan_reconciler — fresh full-corpus sweep, 2026-08-15

**How to use this doc**: every finding below is READ-ONLY discovery — nothing has been applied yet. Work items are
`- [ ]` todos, one per finding, tagged with the fix class in the text. RESOLVED-on-discovery items (rare — the sweep
found the issue already fixed by the time it read) are pre-flipped `[x]`. Everything else needs one of: a mechanical
auto-fix (apply directly, evidence already cited), or an operator ruling (judgment call, options should be presented).

## ⚠️ P0 — checkbox contradicts an explicit operator instruction not to flip it

- [x] ✅ [DATA] P0. **`plans/active/lst_rate_honest_coverage_2026_07_21.md:116`** — todo "Regenerate catalogue +
      expected universe" is checked `[x]`, but the SAME item's own body (lines 127-130) carries a later, dated
      correction: "RULED 2026-08-12 (/plan-reconcile, operator interactive): a literal regen-script run IS required
      before this closes — invariant-test confirmation alone is not sufficient. Do NOT flip this todo `[x]` until
      `build_instrument_catalogue.py` + `enumerate_expected_universe.py` (v2) have actually been executed against real
      infra and the new AAVE/CHAINLINK cells confirmed `expected_unattempted`." NOT auto-fixable — a worker must verify
      against real infra whether the regen script has run since, then either supply the missing evidence or flip the
      checkbox back to `[ ]` per the doc's own instruction. This is the single highest-severity finding of the whole
      sweep: a live mis-route risk on a data-correctness gate. **RESOLVED (2026-08-15, /plan-reconcile defi verification
      pass)**: re-read the live doc — the checkbox is already `[ ]`, not `[x]`. A prior 2026-08-15 pass had already
      live-checked `gcs_describe_object` on both script outputs (catalogue regenerated 04:34:25Z with the new AAVE/
      CHAINLINK cells present, but `enumerate_expected_universe.py`'s output still stale from 2026-07-03) and reverted
      the checkbox back to `[ ]` per the doc's own instruction — see `lst_rate_honest_coverage_2026_07_21.md`'s own
      "REVERTED to `[ ]` (2026-08-15, /plan-reconcile, operator interactive)" entry. The contradiction this finding
      flagged no longer exists; the todo stays genuinely open (enumerator still needs to run) but the mis-route risk is
      gone.

## P1 — live operational/data-correctness risks

- [x] ✅ [DATA] P1. **Sports taxonomy path-key contradiction, active migration — RESOLVED 2026-08-15.**
      `sports_taxonomy_p2_consumer_inventory_2026_08_12.md:386-409` — re-confirmed live: UAC
      `canonical/domain/sports/gcs_paths.py` (`league_id` param, lines 233/351-352/360/365/377/380) unambiguously writes
      only `league=` — that part of the finding was correct and stands. But this is a DIFFERENT path builder from the
      actual migration-sweep target: MTDS's raw-tick odds pipeline
      (`market-tick-data-service/scripts/merge_migrated_odds_into_canonical_2026_07_17.py`), which canonicalizes on
      `league_id=` instead (confirmed via the sibling migration plan's exhaustive 2026-08-15 census,
      `sports_taxonomy_p2_migration_2026_08_08.md:576-594`, + an already-executed purge of 15,154/16,968 legacy
      `league=` raw-tick objects, `market-tick-data-service@8a772b3180`). No remaining contradiction — the two docs were
      describing two different path builders for two different data domains; corrected both the §12 text and the
      "Cross-cutting findings" bullet 3 in the consumer-inventory doc to state the domain-scoped truth explicitly.
      `unified-trading-pm` (doc-only, this session).
- [x] ✅ [DATA] P1. **Databento billing gate stale-"lifted" claim, live risk of wasted VM spend.**
      `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` claims the billing gate is "lifted" for in-scope items
      (CME/ES futures/options, BTC/ETH CME futures), last touched 2026-08-10. But
      `tradfi_databento_account_billing_suspended_2026_08_09.md` shows status flipped back to `blocked` 2026-08-14, with
      2026-08-15 entries confirming the SAME unpaid-invoice wall (402 `account_delinquent_invoice`) on CME/GLBX.MDP3 —
      exactly the MVP-of-MVP doc's in-scope cells. A worker trusting the stale framing would relaunch CME/ES backfills
      that fail immediately. Needs: update the MVP-of-MVP doc's billing-relationship section with a
      recheck-live-billing-doc caveat. **DONE 2026-08-15** — re-verified billing doc still `blocked` as of 2026-08-15;
      added a dated caveat to the MVP-of-MVP doc pointing to the billing doc as live source of truth.
      `unified-trading-pm@f6d90162b4`.
- [x] ✅ [CODE] P1. **UAC sports odds registry contradicts the 2026-08-08 operator-ruled canonical `data_type`, no
      tracked todo.** `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1565-1591`'s
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports","odds")]` still declares `data_type="trades"` as canonical.
      Contradicts the 2026-08-08 operator ruling + 2026-08-12/13/14 executed migration that standardized on `"odds"`
      (see `sports_odds_api_data_type_casing_standardization_2026_08_15.md`, shipped
      `market-tick-data-service@28e2eb36d8`). Self-flagged in
      `sports_p2_raw_tick_live_writer_still_emits_trades_2026_08_15.md:145-153` but the finder explicitly declined to
      create a tracked todo ("small enough to fold in") — itself a HARD RULE violation (every follow-up must be a
      `- [ ] todo, never prose"). Needs: (a) update the UAC registry entry, (b) this todo IS the tracked instance now. **DONE 2026-08-15**: `("sports","odds")`matrix entry flipped from`frozenset({"trades",
      "odds_horizon_bucket"})`to`frozenset({"odds",
      "odds_horizon_bucket"})`; 2 tests in `tests/internal/unit/test_sports_prediction_contracts.py`that asserted the old`"trades"`canonical value updated to assert`"odds"`; the legacy `CONTRACT_REGISTRY[("sports","odds","trades")]`schema intentionally retained (documented as no-longer-matrix-reachable, backs pre-migration prod rows) — full`quality-gates.sh`green. `unified-api-contracts@0bc2fc7c14`.
- [x] ✅ [DOCS] P1. **AWS-vs-GCP epic contradiction — infrastructure_master.md still frames DeFi compute as
      AWS-primary.** `plans/epics/infrastructure_master.md:869,875` carries 2 open todos ("Operator sign-off on
      dual-cloud parity", "GCP bucket decommission" post-AWS-parity) that are opposite-direction from
      `defi_compute_gcp_migration_2026_08_08.md`, which is ~72% executed (13/18 todos) moving compute OFF AWS ONTO GCP.
      That migration plan's own todo 16 (still open) already knows it needs to resolve/supersede these 2 epic todos but
      hasn't executed. NOT auto-fixable — needs the citing/superseding edit (todo 16's own job). **DONE 2026-08-15**:
      confirmed todo 16 is still open (not force-resolving); added a cross-reference banner to the epic pointing at the
      migration plan's todo 16 as the pending resolution, per its own explicit instruction not to hand-edit the 2 epic
      todos myself. `unified-trading-pm@01cf658dc9`.
- [x] ✅ [DATA] P1. **Zero-checkbox doc with real P1 data-correctness work, structurally undispatchable despite
      assigned_vm:planning.**
      `plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md`
      — priority:P1, assigned_vm:planning, but body's "Recommended decision" section has 3 numbered action items with NO
      checkbox syntax anywhere, no Todos section. Same class as an already-fixed instance elsewhere in this same
      original findings doc. Auto-fixable: convert the 3 numbered items to `- [ ]` todos. **DONE 2026-08-15**: converted
      all 3 to `- [ ] [OPERATOR]/[CODE]/[CODE] P1.` todos, exact content preserved. `unified-trading-pm@1c3fef9ea5`.
- [x] ✅ [DOCS] P1. **Zero-checkbox doc, real orphaned follow-up.**
      `dp_manifest_hygiene_defi_index_scale_oom_2026_08_15.md` — zero checkboxes, Option C (defi manifest granularity)
      explicitly self-flagged as "NOT yet tracked" — corpus-grep confirms no home anywhere. Found independently by both
      the defi-tranche AND cross-cutting-tranche sweeps (cross-validated). Auto-fixable: add a `- [ ] [DIAG] P3` todo
      for the Option-C investigation. **DONE 2026-08-15**: added the `- [ ] [DIAG] P3` todo under a new "Follow-up"
      section. `unified-trading-pm@1c3fef9ea5`.
- [x] ✅ [DOCS] P1. **Dangling reference to a nonexistent OPERATOR todo blocks a real CODE todo.**
      `ibkr_gateway_infra_release_tag_stall_2026_08_11.md:97-98,152` — a `[CODE] P2` todo is BLOCKED on "the OPERATOR
      audit todo below" but NO such `[OPERATOR]` todo exists anywhere in the doc (corroborated:
      `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md:401-403` references the same missing todo). Corpus-wide
      grep confirms zero actual checkbox exists for "breaking_scan_dir completeness". Auto-fixable: add the missing
      `- [ ] [OPERATOR] P2` todo to the ibkr doc (natural owner). **DONE 2026-08-15**: added the missing
      `- [ ] [OPERATOR] P2` todo, content inferred from the batch13 doc's own diagnosis of the same missing item.
      `unified-trading-pm@1c3fef9ea5`.
- [x] ✅ [BACKEND] P1. **QG-red commit claim — RESOLVED, claim was accurate, gate doc was stale.** Live re-run of the
      actual scanner (`check_adapter_contract_regression.py`) against the current checkout:
      `OK — 363 baselined file(s) at or above minimum` — NOT currently red. `4844b6286b`'s api_football refactor
      legitimately split `sports_reference_core.py` (extracting `sports_reference_fixture_existence_gate.py`, confirmed
      real `record_empty()` calls, not a stub); the baseline was correctly regenerated same-day
      (`unified-trading-pm@438838ae72`, on `origin/live-defi-rollout`, 14+6=20 ≥ original 19 — call count went UP).
      `sports_honest_coverage_gap_closure_2026_08_14.md:213-232`'s "FIXED, shipped, tested" claim already cited that
      same baseline-bump commit and was accurate — no correction needed there. Flipped
      `mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`'s adapter-contract todo `[x]` with this
      evidence (its unrelated morpho-URL todo stays open — still genuinely red, separate finding). `unified-trading-pm`
      (doc-only, this session).
- [x] [DOCS] P1. **CLAIM≤MEASUREMENT violation — 2 docs falsely claim archival ritual completed.**
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` and
      `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` both have na-eligibility-audit entries claiming "ran
      the 6-step archival ritual... status:resolved... archived" — FALSE on both: frontmatter still active/open, files
      still physically in `plans/active/`, no archive copy exists. Underlying engineering work IS genuinely done (all
      todos `[x]` with real commit citations). Fix: either finish actual archival (flip + `git mv` both) or correct the
      false claims. — **APPLIED 2026-08-15**: finished the actual archival for both — status flipped
      (`complete`/`resolved`), banner added, `git mv`'d to `plans/archive/2026_08/` (+ `issues/` for the four-way-
      mismatch doc), `archive_exempt` dropped, and all real active-corpus referrers (frontmatter `related:` links +
      markdown links) fixed to the new paths.
- [x] ✅ [CODE] P1. **Done-but-unchecked, 4 items in one doc.**
      `plans/active/artifact_pipeline_observability_2026_07_17.md` — 4 of 7 cross-referenced items from batch4 are
      done-but-unchecked with hard evidence: `:646-647` port manual-trigger action/retire CloudBuildsTab
      (deployment-ui@9d5ad0d105), `:648` retire superseded deployment-api routes (deployment-api@3f13e4435e), `:688-689`
      build→deploy latency join (deployment-api@764db37c33), `:702-703` deploy-churn/crash-loop health condition
      (deployment-api@ec80509550). All 4 auto-fixable: flip citing the shas. **DONE 2026-08-15**: all 4 shas
      independently re-verified reachable (ancestor of `origin/live-defi-rollout`); for item 1, the real citation is
      `deployment-ui@b3300a71a7` ("port manual-trigger build action..., retire CloudBuildsTab") — `9d5ad0d105` was a
      same-topic follow-up bugfix, not the port itself; flipped all 4 citing the correct shas, trimmed prose to keep the
      doc under its 1000L cap. `unified-trading-pm@5196dfcafc`.
- [x] ✅ [CODE] P1. **Done-but-unchecked, 3 more items, mechanism exists but hasn't run.**
      `data_status_tab_and_downloads_remediation_2026_06_16.md` — 3 of 4 batch4-claimed fixes still open despite hard
      evidence: `:186-188` rollup-difference-clarity tooltip (deployment-ui@8033b83651), `:238-247` Yahoo/Kalshi
      market-tick-view scope check (confirmed correct-by-design), `:338-347` per-service coverage BucketNamingError
      root-fix (already root-fixed, deployment-api@c1aab6e/@b014ae9). Root cause:
      `ui_satellite_ao_dispatch_batch4_2026_08_13_finalize.md`'s reconciliation todo hasn't run yet (machine-gated
      mechanism exists, just not executed). **DONE 2026-08-15**: sha flipped citing `deployment-ui@8033b83651`;
      correct-by-design item verified via direct read of UAC `expected_coverage.py` (YAHOO_FINANCE removed as a venue
      2026-07-15, KALSHI's expected data_types list deliberately excludes `ohlcv_1m`) and flipped; BucketNamingError
      item flipped citing both `deployment-api@c1aab6e` (root-fixed) and `@b014ae9` (SHARED pseudo-key honest-empty by
      design, tracked separately). `unified-trading-pm@5196dfcafc`.
- [x] [DOCS] P1. **Predictions_master epic missing batch11.** `plans/epics/predictions_master.md` `related_plans:`
      (lines 35-51) and "Assigned active plans" section (says "16 active plans", actual 18) both omit
      `prediction_satellite_ao_dispatch_batch11_2026_08_13.md` + its finalize (both declare
      `parent_epic: predictions_master`, created before the epic's own last_updated). Auto-fixable: add 2 entries,
      correct 16→18. — **APPLIED 2026-08-15**: added both entries to `related_plans:` and the P2 body section, 16→18.
- [x] ✅ [CODE] P1. **cefi_enumeration_audit doc — 2 issues.**
      `cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`: (a) frontmatter
      self-contradiction `assigned_vm: planning` + `execution_scope: local-only` (schema requires `orchestrator-agent`
      pairing) — Progress Log records the reclassification but execution_scope was never updated, auto-fixable; (b)
      doc's last line says "a SEPARATE, still-open question (**new todo below**)" but no such todo exists anywhere in
      the doc — needs human check: author the missing todo or correct the sentence. **DONE 2026-08-15** — (a) flipped
      `execution_scope` to `orchestrator-agent`; (b) confirmed no such todo exists anywhere, corrected the false
      forward-reference sentence instead of guessing at scope. `unified-trading-pm@f6d90162b4`.
- [x] ✅ [DOCS] P1. **cefi batch10_finalize stale lock-ask premise.**
      `cefi_satellite_ao_dispatch_batch10_2026_08_08_finalize.md` todo 2 (still open) asks the operator to unlock
      `cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` as "locked" — but that doc's own Progress Log shows
      `locked_by` was already cleared 2026-08-12 (corpus-wide placeholder fix), now bridged via `archive_exempt:true`
      awaiting follow-on archival, not actually locked. Needs a human/next-toucher edit to narrow the ask to the other
      named doc (`cefi_universe_capture_rule_2026_06_23.md`, unverified) since the finalize is `sequential:true`/gated —
      don't blind-flip. **DONE 2026-08-15** — verified BOTH named docs have `locked_by` cleared already (not just the
      one), rewrote the todo to reflect the corpus-wide 2026-08-12 clearing and point at running the archival ritual
      instead of an operator unlock-ask; did not flip any other todo in this `sequential:true` doc.
      `unified-trading-pm@f6d90162b4`.
- [x] [DOCS] P1. **Predictions consolidated closeout per-child open-todo snapshot 20 days stale.**
      `prediction_consolidated_closeout_2026_07_18.md`: phase_ab says 13 open (actual 6), phase_c says 4 (actual 2),
      phase_d says 6 (actual 5), capture_incident_remediation says 9 (actual 7). Not dispatch-blocking (real gate is
      `depends_on`) but misleads readers. Re-run counts, update both citation points (snapshot table + digest). —
      **APPLIED 2026-08-15**: re-counted fresh (`grep -c`), same figures confirmed still accurate; updated both citation
      points (snapshot table + digest index).
- [x] ✅ [TERRAFORM] P1. **tradfi_master epic stale active-plans list.** `plans/epics/tradfi_master.md:817-888` lists
      batch6+finalize as "status: active" but they're archived; list stops at batch8, missing batch9-batch12 entirely
      (epic's own frontmatter `related_plans` cites batch12, `ag_closeout_audit_tradfi_parked_2026_08_10.md` confirms
      batch11+12 flipped active 2026-08-12). Needs `populate_epic_bodies_2026_05_21.py` re-run. **DONE 2026-08-15** —
      ran `populate_epic_bodies_2026_05_21.py --apply` (derived, full-corpus tool); only committed the resulting
      `tradfi_master.md` diff (correctly now lists batch11/12/13+finalize, drops archived batch6), reverted the tool's
      incidental regen of the other 18 epics as out-of-scope for this pass. `unified-trading-pm@f6d90162b4`.
- [x] ✅ [SCRIPT] P1. **Checkbox-counting tooling may have a `*`-bullet blind spot causing a false archive candidate.**
      `tradfi_backfill_oom_remediation_2026_06_24.md:428` has a genuinely open `* [ ]` item (asterisk bullet, not dash)
      but `ag_closeout_audit_tradfi_parked_2026_08_10.md:95` claims "0 open, 12 done" and lists it as an archive
      candidate. Same false-negative class already known for na-eligibility-audit's own star-bullet gap. REAL RISK: doc
      could be archived while carrying genuine open work. Fix: normalize bullet to `-`, AND check whether
      `check_archive_candidates.sh`/`count_open_tasks.py` has this same regex gap. **DONE 2026-08-15** — normalized the
      bullet (content unchanged). Confirmed the tooling gap by reading source: `count_open_tasks.py`'s
      `OPEN_RE = re.compile(r"^\s*- \[ \]")` and `check_archive_candidates.sh`'s `grep -cE '^[[:space:]]*- \[.\]'` both
      require a dash bullet — neither counts `* [ ]`. Reported here for a human to fix in the tooling itself (out of
      scope for this docs-only pass). `unified-trading-pm@f6d90162b4`.

## P2 — done-but-unchecked (auto-fixable, hard evidence)

- [x] ✅ [SCRIPT] P2. `ff_pull_fleet_drift_rca_2026_08_11.md` 2 of 4 open todos already shipped 2026-08-13 (code
      self-cites the doc by name) — `unified-trading-pm@c89e109ea7` (slot/clone log tagging),
      `unified-trading-pm@bb75f3d5ce` (ff-starvation-detect.sh detached-HEAD verdict). Flip both citing the shas. **DONE
      2026-08-15** — both shas re-verified reachable, both flipped. `unified-trading-pm@f6d90162b4`.
- [x] ✅ [DATA] P2. `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md:125-131` Phase A2 todo1 still `[ ]` but
      `tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md:7-9` shows the verify already done with live
      code quoted. Flip citing the drift doc. **DONE 2026-08-15.** `unified-trading-pm@f6d90162b4`.
- [x] ✅ [DATA] P2. `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md:92-105` "converge GCS chain-bundle onto registry
      values" still `[ ]`, but batch13 (`:76-113`) already did the identical work with full evidence. Flip batch11
      citing batch13's shas. **DONE 2026-08-15.** `unified-trading-pm@f6d90162b4`.
- [x] ✅ [DOCS] P2. `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` action item1 has a
      stale "option 2 still NOT shipped" note but `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md:191-198` shows it
      DONE (deploy@48f55e934b). Auto-fixable. **DONE 2026-08-15.** `unified-trading-pm@f6d90162b4`.
- [x] [CODE] P2. `sports_consolidated_closeout_2026_07_19.md:745` Track H RAISE-on-all-NaT todo still `[ ]`, but
      identical work shipped per `sports_consolidated_native_ao_extract_2026_07_25.md:346-350`
      (market-tick-data-service@84ee34f2, 2 named tests, QG green). Flip citing that sha. — **APPLIED 2026-08-15**:
      re-verified the citation, flipped.
- [x] [DOCS] P2. `sports_satellite_ao_dispatch_batch11_2026_08_09_finalize.md:64-69` todo2 still `[ ]` but target
      (canonicalization doc's parity-test todo) is `[x]` with features-service@36fb7b88, independently corroborated
      (10/10 tests passing). Flip citing evidence (entangled with the P1 archival-claim finding above — fix both
      together). — **APPLIED 2026-08-15**: flipped alongside the P1 archival fix above.
- [x] ✅ [DOCS] P2. `bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27.md` sole todo not flipped even
      though the source plan was already archived 2026-08-15 (this session's own batch3). Flip citing the archive
      commit, then archive this finalize doc too (no lock on it). **DONE 2026-08-15**: flipped citing
      `unified-trading-pm@5ee2edd598` (the archive commit); confirmed no lock, 0 open todos, `git mv`'d to
      `plans/archive/2026_08/`. `unified-trading-pm@01cf658dc9`.
- [x] ✅ [DOCS] P2. `strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` — all 10 todos `[x]`,
      archive_exempt bridge same pattern as bucket_iam (already fixed this session) but this doc was missed. Standard
      6-step archival (paired execution plan has real open work, don't touch that one). **DONE 2026-08-15**: confirmed
      all 10 `[x]`, no lock; ran the 6-step ritual (banner, `archive_exempt` dropped, `git mv` to
      `plans/archive/2026_08/`, every corpus referrer's path fixed — the paired execution plan +
      `RUNTIME_TOPOLOGY_DECISIONS.md` + 3 family docs); the paired execution plan itself left `active` (real open work
      confirmed, untouched). `unified-trading-pm@01cf658dc9`.
- [x] ✅ [DATA] P2. `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` — possible (not confirmed) that the
      [OPERATOR] P1 "decide immediate unblock" todo is already satisfied (08-10 00:37 success referenced as established
      fact in a later entry) but no citable sha/GCS check exists. **DONE (verified 2026-08-16, /plan-reconcile Phase
      -1)**: re-read the target doc directly — the `[OPERATOR] P1` todo is itself already `[x]` with its own dated
      entry ("Resolved as of 2026-08-15 — moot. The daily cron has been writing fresh `coverage.json` successfully
      with the default machine type for several days now (bucket shows 08-01, 08-02, 08-04, 08-05, 08-09, 08-10,
      08-12, 08-14, 08-15 — no gap since 08-12)"), and the doc carries `archive_exempt: true` deliberately (0 open
      todos, kept for 9 live cross-referrers' link stability per its own 2026-08-15 Progress Log entry) — confirmed
      genuinely resolved, not just claimed.

## P2 — needs operator ruling / judgment call (not mechanically resolvable)

- [x] ✅ [OPERATOR] P2. `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:470-473` — todo asks to
      move `market_metadata` off an axis (2 named options), but current code has evolved to a THIRD resolution
      (`expected_count_per_day: "indeterminate"`) matching neither literal option. Needs re-wording or
      closure-by-citation. **RESOLVED (2026-08-15, /plan-reconcile defi verification pass)**: the requested action
      already happened — the source todo carries an **"INVESTIGATED (2026-08-15, /plan-reconcile, operator interactive)
      — stays open, reworded framing only"** entry documenting the 3rd resolution
      (`deployment_api/services/data_status/mtds_meta.py:162-176`'s `indeterminate` marker mitigates the symptom but
      doesn't resolve either of the todo's 2 named options) and explicitly noting the todo "stays open and unchanged in
      intent." The re-wording/closure-by-citation this finding asked for is done; the underlying todo intentionally
      stays open (operator-gated design choice, not a hygiene gap).
- [x] ✅ [OPERATOR] P2. `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md:178-190` open P1 todo's
      premise was invalidated by the SAME doc's own later Progress Log — but a same-day sibling doc gives a MORE
      PRECISE, partially-contradicting correction. Two docs not fully reconciled. Needs human to re-scope/close.
      **RESOLVED 2026-08-15 (sports-tranche plan-reconcile pass)**: re-checked the source doc directly — the todo
      already carries a **"CLOSED (2026-08-15, /plan-reconcile, operator interactive)"** note redirecting to the 2
      sibling plans that now own the split (`sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` for the
      raw-tick GCS path surface, `sports_odds_api_data_type_casing_standardization_2026_08_15.md` for the manifest
      capture-record surface), and the checkbox itself is already `[x]`. No further reconciliation needed.
- [x] ✅ [OPERATOR] P2. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` — 2 blocks of literal unresolved git
      conflict markers were found in the WORKING TREE by an independent sweep agent; already resolved by this session
      directly (confirmed HEAD was always clean — working-tree-only artifact, not corpus corruption). No further action
      needed, noted for completeness. **Flipped 2026-08-16 (plan_reconciler cross-cutting)** — the item's own text
      already stated resolution with no further action needed; the checkbox was simply never flipped to match.
- [x] ✅ [OPERATOR] P2. `prediction_phase_e_football_arb_live_2026_07_24.md` — E1 (open) says Kalshi "has none today"
      for af_fixture_id resolution, but E2 (done, same doc) already shipped exactly that. E1's framing is stale; a
      narrower 3-way-identity-match verification may still be genuinely open. Needs doc-owner call on scope. **RESOLVED
      2026-08-15 (same-session operator interactive)**: E1 flipped `[x]` citing E2's shipment directly in the source doc
      ("CLOSED (2026-08-15, /plan-reconcile, operator interactive)... Closing citing E2's shipment rather than
      duplicating it as separately-open"). Doc now shows 2 open (E3's P1 + P2 only); the parent closeout's per-child
      snapshot line was stale at "3 open" and has been corrected in this pass (see
      `prediction_consolidated_closeout_2026_07_18.md`).
- [x] ✅ [OPERATOR] P2. `sports_predictions_live_mode_activation_readiness_2026_07_21.md:214` — todo checked `[x]` but
      its own body says "Checkbox NOT flipped... per operator's explicit instruction" YET the doc's Progress Log shows a
      DIFFERENT same-day audit pass overrode this and flipped it anyway. Two same-day passes, opposite conclusions.
      Needs human ruling: re-verify a live poll cycle, resolve explicitly. **RESOLVED 2026-08-15 (same-session operator
      interactive)**: live poll cycle re-verified directly against infra (no `mtds-live-sports-*` VM running; warm-sink
      prefix >4h stale against a 300s max-batch-duration sink) — settles the tension: parent checkbox stays `[x]`
      (connector code/launcher claim is true), part (b)'s "fresh poll cycle succeeding" condition is NOT met today.
      Documented in the source doc's body at the cited location.

## P3 — cosmetic / hygiene (low priority, batch when convenient)

- [x] ✅ [DOCS] P3. Stale `last_updated` frontmatter, systemic across dozens of docs corpus-wide (body content weeks ahead
      of frontmatter date) — worth a corpus-wide script fix rather than per-doc edits. Named instances:
      `prediction_capture_incident_remediation_2026_07_06.md`, `consolidator_throughput_backlog_monitor_2026_07_09.md`,
      `data_status_catalogue_true_source_phase2_2026_07_24.md`, `data_status_cell_grid_rearchitecture_2026_07_18.md`, 8
      named docs from tradfi batch1, `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`.
      **DONE 2026-08-20**: added `scripts/plan-hygiene/check_last_updated.py`, which derives each live plan/epic's
      date from its newest Git commit and preserves quote/comment formatting when applying corrections. Applied the
      mechanical fix across the corpus; a fresh read-only scan reports no stale live dates (0 paths skipped).
- [x] ✅ [DOCS] P3. 3 cross-cutting docs mistagged with `prediction` in `asset_group` with zero real prediction-market
      content: `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`,
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`,
      `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`. Drop `prediction` from all 3.
      **DONE 2026-08-15**: `adapter_findings...` fixed directly (`unified-trading-pm@e83ca342dd`); the other two were
      mid-archival by a concurrent session at the time — landed the `asset_group` fix woven into that session's own
      archival commit (see the P1 CLAIM≤MEASUREMENT item above, same 2 docs).
- [x] ✅ [DOCS] P3. 4 cross-cutting docs carry identical stale `archive_exempt` BRIDGE markers from 2026-08-12, all
      0-open-todos, 3+ days past the promised follow-on: `backfill_vm_slack_alert_e2e_verification_2026_06_23.md`,
      `batch_live_reconciliation_service_audit_2026_05_27.md`, `capability_wizard_gap_discovery_2026_06_11.md`,
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`. Route to `/archive-candidates-audit`.
      **Flipped 2026-08-16 (plan_reconciler cross-cutting)** — verified all 4 now physically live under
      `plans/archive/2026_08/issues/` (filesystem-confirmed); the requested archival already happened.
- [x] ✅ [DOCS] P3. `reference_path_convention_2026_07_23.md:144-150` todo assumed a file would be split (it's exactly
      1000L) then its dangling ref fixed — file was instead ARCHIVED whole, archived copy still carries the unfixed
      reference. Todo as worded is unexecutable; needs re-scoping. **DONE 2026-08-15**: re-scoped the todo (split-first
      premise moot, `check_line_caps.sh` is scoped to `plans/active/`+`plans/epics/` only) and fixed the reference
      directly in the archived copy + 4 more pre-existing dangling refs the same archived doc carried.
      `unified-trading-pm@e83ca342dd`.
- [x] ✅ [DOCS] P3. `safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md:185-195` — 2 of 3 ag_closeout_audit
      slug-collision pairs (cefi, prediction) already resolved via `_r2` split; only tradfi pair remained. Bonus:
      `check_create_only_archive_commits.py`'s `ALLOWED_DUPLICATE_STEMS` still listed all 3, 2 were vestigial. **DONE
      2026-08-15** (tradfi-tranche `/plan-reconcile` pass): archived tradfi's active Round-2 doc to
      `/plans/archive/2026_08/issues/ag_closeout_audit_tradfi_parked_2026_08_10_r2.md`, repointed its 4 frontmatter
      referrers, and removed the `tradfi` stem from `ALLOWED_DUPLICATE_STEMS` — only `INDEX.md` remains on the list.
      `unified-trading-pm` (this commit).
- [x] ✅ [DOCS] P3. `deployment_registry_firestore_migration_2026_07_14.md:66-69,126` still frames the P3 halt as
      operator-gated, contradicting the sibling doc's 2026-08-15 fix (this session) that corrected the SAME framing
      elsewhere. Reword to match, fix a stale banner-color reference too. **DONE 2026-08-15**: reworded both spots to
      match the sibling p3_cutover doc's corrected framing (HALTED on an unmet data precondition, not an
      operator-approval gate) and fixed the stale 🔴→🟡 banner-color reference. `unified-trading-pm@e83ca342dd`.

## Zero-checkbox docs found (flagged, not all confirmed violations — several route to sibling plans)

- `dp_manifest_hygiene_defi_index_scale_oom_2026_08_15.md` — real orphaned follow-up, see P1 above.
- `path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md` — real
  P1 work, see above.
- `defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md` — real judgment-work deferral never tracked, HARD
  RULE violation.
- `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` — record-type audit doc, findings routed to sibling plans (not a
  violation).
- `instruments_docs_audit_outstanding_items_2026_07_08.md` — known/accepted state, 7+ prior audits ruled KEEP-NA (not
  worker-bounded).

## Coverage note

~35 sub-agents covered all 10 tranches; several tranches self-partitioned given corpus size (ao 5 batches, tradfi 5,
cefi 5, defi 5, cross-cutting 6, sports 5, infra 5+, prediction 3, ui 3+). Every tranche reported "unusually
well-audited" overall — the bulk of what a fresh sweep would normally find had already been caught by this workspace's
own standing na-eligibility-audit/context-scout/plan_reconciler cadence. The findings above are the genuine residual on
top of that.

## Not yet done (see the sibling `## Deferred work` table in this session's `/pre-compact` note for full detail)

- **STALE (corrected 2026-08-16, plan_reconciler cross-cutting)**: accurate when written, but 30+ items in the body
  above now carry dated DONE/APPLIED entries with commit citations from subsequent sessions — check each item's own
  body text for current status rather than trusting this line.
- **2026-08-16 (/plan-reconcile Phase -1, dedicated pass)**: re-checked every remaining open item. Flipped the
  `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` P2 item (confirmed resolved with hard evidence, see
  its own entry above). One item remains genuinely open: the systemic stale-`last_updated` P3 hygiene finding (real,
  low-priority, needs a corpus-wide script fix rather than a per-doc edit — out of scope for this pass). Doc NOT
  archived (1 item still open).
- Historical-reconcile batches 5-10 (from the SEPARATE earlier pass this same session, reconciling prior dated findings
  docs) were partially committed (batches 1-4 landed) — batches 5-10 (prediction/sports/ui/08-08-archive/
  meta-docs/locked_by-sweep) still need their commits, IF the edits from that earlier apply-agent pass survived the
  session's repeated autostash cycles (confirmed at least the infra doc's edits did NOT survive and had to be redone —
  verify each remaining batch's target files before assuming the content is still there).
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **plan-reconcile 2026-08-20**: implemented and applied the corpus-wide `last_updated` synchronizer; verification
  reports `✅ check_last_updated: no stale live dates (0 path(s) skipped)`.

## Progress Log

- **na-eligibility-audit 2026-08-17** [body-hash:54d6e4cc04ce637b]: RECLASSIFY (whole-doc) -- assigned_vm flipped NA -> planning; execution_scope -> orchestrator-agent; assigned_role: review (already set). The sole open item (a corpus-wide stale-last_updated-frontmatter script fix, named instances enumerated) is bounded/mechanical, conflict-check CLEAR. doc_type: issue, structurally exempt from a finalize-plan companion. Cross-cutting tranche audit.
