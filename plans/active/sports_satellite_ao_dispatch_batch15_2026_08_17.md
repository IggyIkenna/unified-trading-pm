---
doc_type: plan
title: Sports satellite AO batch 15 — na-eligibility-audit residual extraction (2026-08-17)
summary: >-
  Fifteenth AO-dispatch batch for sports, drafted by the daily /na-eligibility-audit sports run (dispatch agt-555dfd,
  slot 26). Extracts 11 conflict-clear bounded items from two source docs that could not be whole-doc-reclassified:
  sports_consolidated_closeout_2026_07_19.md (standing 2026-07-23 operator ruling against a direct assigned_vm flip —
  per-item extraction is its established cadence) and sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md
  (mixed bounded + one genuinely [OPERATOR]-gated prod-delete item, split per task_template.md Finding Y, 2026-08-16 —
  an operator-gated item must not share a file with AO-dispatched todos). Every item conflict-checked against batch14
  (2026-08-16, drafted one day prior) and every other active satellite batch before inclusion — none overlap.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-15, satellite-docs, na-eligibility-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md,
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 1.76
assigned_role: data_engineering
effort: high
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit sports (2026-08-17, dispatch agt-555dfd, slot 26) Phase 3, per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §3's shared conflict-check protocol,
  task_template.md's dispatch-scope eligibility test, and task_template.md §3 Finding Y (2026-08-16).
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md,
  ]
---

# Sports satellite AO batch 15 — na-eligibility-audit residual extraction (2026-08-17)

## Conflict-check findings

Both source docs were read end-to-end and checked against `sports_satellite_ao_dispatch_batch14_2026_08_16.md`
(status: draft, drafted 2026-08-16 — one day prior), every other active sports satellite batch (5, 9, 10, 12, and
14's own dependencies), and `sports_consolidated_closeout_2026_07_19.md`'s own Track content, per
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3. Two candidates from the SAME initial
Phase-1 pass were found to already be claimed by batch14 and were correspondingly NOT extracted here (see the
citation-only fixes landed directly in their source docs instead):
`sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md`'s two follow-up todos (batch14 todo 2 already merges
this exact VM-launch action) and `dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md`'s items 2-3
(batch14 todo 9 already covers both). No other overlap found for any of the 11 items below.

## Todos

- [ ] [DIAG] P3. **Re-run the PERPETUAL/football `instrument_type`-axis watch-census.** Two independent read-only
      censuses against `market-data-tick-sports-prd-central-element-323112` (`read_availability_index`, no new GCS
      walk) previously found ZERO rows for both `PERPETUAL` and `football` — re-run once more; if either value
      reappears, trace `written_at`/`service_name` on the specific row before treating it as live; if both remain
      zero, strike the finding as confirmed-dead. Source: `sports_consolidated_closeout_2026_07_19.md` Track C (the
      PERPETUAL/football watch item). Repo: market-tick-data-service. Done when: the census result is cited and the
      source doc's checkbox is flipped either way.
- [ ] [DOC] P2. **Correct the cutover runbook's canonical-is-a-superset premise for raw odds on early dates.**
      `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md` is `status: resolved` (corpus-destroying
      risk already remediated, byte-exact GCS soft-delete restore verified) — the runbook still states the disproven
      premise; correct it and cite that doc. Source: `sports_consolidated_closeout_2026_07_19.md` Track S. Done when:
      the runbook is corrected and cites the resolved doc.
- [ ] [CODE] P2. **Upgrade the sports instrument catalogue's player grain** from `entity=injuries` (injured-only) to
      `entity=fixture_lineups` (full roster, now carries 100% player/coach identity) in
      `build_instrument_catalogue.py`. Source: `sports_consolidated_closeout_2026_07_19.md` Track V. Repo:
      instruments-service. Done when: the catalogue build reads from `fixture_lineups`, verified via a fresh
      row-count/identity spot-check against real data.
- [ ] [DIAG] P2. **Identify which launcher ran the most recent sports features backfill** — serial
      `launch-features-sports-backfill-vm.sh` or parallel `launch-features-sports-parallel-backfill-vm.sh` — via VM
      launch history/logs; if serial, file a follow-up todo requiring the parallel launcher for every future sports
      features backfill. Source: `sports_consolidated_closeout_2026_07_19.md` Track V. Done when: the launcher used
      is named with its citing VM log/dispatch record, and the source doc's checkbox is flipped.
- [x] ✅ [BACKEND] P2. **DUPLICATE — already resolved 2026-07-25 in
      `sports_consolidated_native_ao_extract_2026_07_25.md`** (found 2026-08-17, slot-10). This item's source text
      (`sports_consolidated_closeout_2026_07_19.md` Track K) was independently extracted and completed almost a month
      before this batch drafted the same extraction: confirmed no flag existed (repo-wide grep), then built
      `--fixture-ids` targeting flag on the features-service sports CLI — `features-service@970de3fc`, 9 unit tests.
      Source checkbox flipped in the same session.
- [x] ✅ [DATA] P1. **DUPLICATE — already resolved 2026-08-01/08-02 in
      `sports_consolidated_native_ao_extract_2026_07_25.md`** (found 2026-08-17, slot-10). This item's premise
      ("currently ZERO real run-todos exist for any of the 5") was already FALSE at draft time: the same source text
      (`sports_consolidated_closeout_2026_07_19.md` Track K, lines 665-669) was independently extracted into that
      sibling doc and all 5 mechanisms' 3 dated checkpoints (baseline/mid/final) were run and cited with real report
      paths — `plans/audit/results/data_pipeline_e2e_check_{is,mtds,mdps,features}_{2025_12_20,2025_12_24,2025_12_18}.md`
      + `data_pipeline_reconciliation_sports_{2026_07_20,2026_07_22,2026_08_01}.md`. No re-run performed — re-running
      15 pipeline checks to re-answer an already-answered question would waste real VM/agent time. Source doc's
      checkbox flipped in the same session. **Process note**: the na-eligibility-audit conflict-check
      (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) checks a new batch against
      other ACTIVE satellite batches but evidently not against older already-active docs that independently extracted
      the SAME source lines — worth a look by whoever maintains that protocol.
- [x] ✅ [DATA] P1. **Verify no downstream regression for at least one full boundary cycle post-writer-flip** on the
      sports `odds_api` writer cutover (`data_type=trades`→`odds`) — verified 2026-08-17 04:5x UTC (slot-20). Evidence:
      (1) live writer: `gs://central-element-323112-events/live-events/warm/sports/odds/` holds 851 objects (up from 5
      at the Phase-1 15:10 UTC check), most recent object 6s old at check time with ~2-5min inter-arrival cadence — the
      `mtds-live-sports-odds-api-odds-20260816-145019` VM (RUNNING, asia-northeast1-c) is actively and continuously
      writing more than a full boundary cycle after its 2026-08-16 14:50 UTC launch; (2) `DP-LIVE-004` did not
      false-page: scanned the last ~100 `#data-pipeline-alerts` messages spanning the boundary-cycle window — every
      `DP-LIVE-004`/`DP_CRON_DID_NOT_FIRE` hit names an unrelated shard (cefi-consolidated venues, tradfi CME) with
      zero entries for this VM or an `ODDS_API` sports shard; (3) MDPS bucket assignment + features reads: not
      re-verified via a fresh runtime read (module-path friction resolving MDPS's bucket name live) — relying on the
      Phase-0 code-level guarantee already cited in the source plan (`bucket_assignment_adapter.py:705` confirmed
      dual-accepting `odds`/`trades`, and `sports_catalog_reader.py` + the `market-tick-data-service@83a1abbdbf`
      consumer sweep, both already landed with test coverage) — this is a real gap versus a fresh runtime check, noted
      honestly rather than closed with "looks fine." Also noted: a separate CRITICAL `DP_RUN_MOSTLY_EMPTY` fired
      2026-08-17 04:50 UTC for `asset_group=sports data_type=odds_horizon_bucket` (36,303 attempted_failed cells,
      0.6%) — a DIFFERENT data_type (a features-derived horizon bucket, not this writer's raw `odds` shard) and a
      backfill-batch issue, not a live-writer regression; flagged here for visibility, not fixed as part of this item
      (out of scope). Source doc's checkbox flipped in the same session (see
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phase 1).
- [ ] [DIAG] P2. **Confirm with `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`'s owner whether to run its drafted IS-bucket relabel now.** Phase 0/1 of the writer-flip plan have both landed, so per that plan's
      own text ("running before the flip means re-running after"), "run now" is the self-consistent answer. Source:
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phase 2. Done when: the issue doc is updated
      with the decision + evidence, and the source doc's checkbox is flipped.
- [x] ✅ [REVIEW] P2. **Pick up (or confirm claimed by its owner) `sports_taxonomy_p2_migration_2026_08_08.md`'s dangling
      Verification section** (four-surface reconciliation, accepted-exception shrinkage, honest-coverage re-run) — now
      unblocked since the writer has stopped re-accumulating `trades`. Source:
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phase 2. Done when: the section is either
      picked up with progress cited or confirmed already claimed by an active owner, and the source doc's checkbox is
      flipped. — **The premise was stale, not dangling.** Read `sports_taxonomy_p2_migration_2026_08_08.md` directly
      (not just this batch's summary): all 3 Verification todos were already `[x]` done 2026-08-15
      (slot-9/slot-14), predating the source plan's own same-day "still dangling" claim. That verification correctly
      surfaced 2 real findings: one RESOLVED+archived, one
      (`issues/sports_p2_reference_bucket_uppercase_regrowth_2026_08_15.md`, P1 residual restamp) still open but
      actively GATED-monitored across 5 prior sessions (most recently 2026-08-16), waiting on
      `instruments-service@b872799efa`'s promote-to-main — not neglected. Source doc's Phase 2 checkbox flipped in
      the same session; its stale "dangling" prose corrected too.
- [ ] [DATA] P2. **Census every remaining `data_type=trades` GCS object in the sports raw-tick bucket** as of the
      writer-flip Phase 1 completion; split into (a) objects already twinned by the 2026-08-12 restamp (safe to
      delete later — a verified duplicate exists) vs (b) objects written after that restamp that were never relabeled
      (need restamping first). Read-only, no delete. Source:
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phase 3. Repo: market-tick-data-service.
      Done when: the census report cites both population counts, and the source doc's checkbox is flipped.
- [ ] [SCRIPT] P2. **Re-run `restamp_sports_trades_to_odds_2026_08_12.py` + `manifest_swap_trades_to_odds_2026_08_12.py` against census population (b) from the item above**, so 100% of remaining `trades`-labeled content has a
      verified `odds`-labeled twin before any deletion proceeds. Sequenced after the census item above (same-doc
      dependency — both touch the same population, run the census first). Source:
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` Phase 3. Repo: market-tick-data-service.
      Done when: verified-twin coverage reaches 100% for population (b), cited with counts, and the source doc's
      checkbox is flipped.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check
  protocol applied to every item above
- `plans/active/task_template.md` §3 Finding Y — why the writer-flip plan's `[OPERATOR]`-gated delete (items 6-7)
  stays in its own NA source doc rather than being extracted here

## Progress Log

- **2026-08-17 (na-eligibility-audit sports, dispatch agt-555dfd, slot 26)**: authored from 2 source docs' Phase-1
  classification during the sports-tranche `/na-eligibility-audit` run — `sports_consolidated_closeout_2026_07_19.md`
  (6 items, standing 2026-07-23 no-whole-doc-flip ruling, per-item extraction is its established pattern) and
  `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` (5 items, split path per Finding Y — its
  `[OPERATOR]`-gated delete + dependent script-retirement item stay in the source doc). Both source docs' own
  checkboxes annotated with the extraction citation in the same run. **Status set `active`** (not `draft`) per the
  2026-07-30 no-double-gate ruling this skill's own verdict already constitutes the operator decision to apply.

- **2026-08-17 (slot-3, review) — dispatched onto the `[REVIEW] P2` Verification-section todo; found it was a
  stale-premise resolution, not a pickup.** Read `sports_taxonomy_p2_migration_2026_08_08.md` directly (per the
  pre-task conflict-check hard rule, not just this batch's or the source plan's summary text) and found all 3
  Verification todos already `[x]` done 2026-08-15 (slot-9/slot-14) — the source plan's own "still dangling" claim,
  written the same day, simply predated that work and was never re-checked. Flipped both this todo and the source
  doc's Phase 2 checkbox, and corrected the source doc's stale prose claim in the same session. Same pattern as the
  todo-5/6 finding immediately below (a referring doc's premise going stale without anyone re-checking it against
  the actual target doc) — worth folding into the same process-gap note about the na-eligibility-audit conflict-check
  protocol not cross-checking claims against the CURRENT state of cited target docs.
- **2026-08-17 (slot-10, data_engineering) — dispatched onto todo 6 ([DATA] P1, 3-checkpoint pipeline-check sweep);
  found it (and adjacent todo 5) were stale duplicates, not live work.** Before running any of the 15 implied
  pipeline-check dispatches, grepped the corpus for prior sports runs of the same 5 mechanisms per the pre-task
  conflict-check hard rule — found `sports_consolidated_native_ao_extract_2026_07_25.md` already completed this
  EXACT "Track K" item (same source citation, `sports_consolidated_closeout_2026_07_19.md` Track K) on
  2026-08-01/08-02, with all 15 checkpoint reports cited by path. The source doc's checkbox was simply never
  flipped after that sibling doc finished the identical work, so this batch's Phase-1 extraction (which reads the
  source doc's checkbox state, not the sibling doc) picked up a false "ZERO run-todos exist" premise. Same root
  cause affected adjacent todo 5 (fixture-level shard-splitting flag), also already resolved in the same sibling
  doc. Flipped both todos here AND in the source doc (`sports_consolidated_closeout_2026_07_19.md`), citing the
  existing evidence rather than re-running already-answered pipeline checks — 15 VM-backed dispatches to re-confirm
  a known answer would have been pure waste. Flagged as a process gap for the na-eligibility-audit conflict-check
  protocol: it checks a new batch against other ACTIVE satellite batches but not against older already-active docs
  (like `sports_consolidated_native_ao_extract_2026_07_25.md`) that independently extracted the same source lines.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) -- added
  `/plans/active/issues/sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md` on a confirmed evidence
  fingerprint match: both this doc's todo 5 and that issue doc's Part-3 pass independently cite the identical live-VM
  literal `mtds-live-sports-odds-api-odds-20260816-145019` as verification the odds_api writer-flip cutover is clean
  -- same underlying incident, different investigations. Also added `context_scope` (this pair) to that doc.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
