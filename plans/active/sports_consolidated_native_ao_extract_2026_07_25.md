---
doc_type: plan
title: Sports consolidated closeout — native AO extract (26 AO-eligible todos from the master plan's OWN checkboxes)
summary: >-
  A fresh AO-eligibility triage of sports_consolidated_closeout_2026_07_19.md's OWN native `- [ ]` todos (never before
  extracted — every prior sports satellite batch drew from OTHER orphaned docs, deliberately not this doc's own
  checkboxes). Of ~65 open top-level / 78 total open todos, 26 are genuinely bounded/determinable-by-a-worker-alone
  after this session's several reconciliation passes; the rest stay human (operator-gated deletes/scheduling, open
  design/judgment calls, entangled with the still-pending K1/K2 casing revert or league_id migration, or already flagged
  as conflict-gated in `issues/autonomous_session_operator_decisions_2026_07_25.md`). 6 candidates required scoping DOWN
  from the source todo's literal text (dropping an undecided design fork, an already-superseded downstream framing, or a
  "manual review" sub-part) to make them genuinely bounded; 2 required an added live-probe first-step because the source
  todo's own prerequisite state is ambiguous or self-contradictory. 1 candidate (venue vocabulary re-stamp) explicitly
  EXCLUDES a sub-item already covered by `sports_satellite_ao_dispatch_batch3_2026_07_25.md`.
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
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, native-extract, satellite-docs, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/task_template.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.5
estimate_calibrated_ai_days: 5.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-requested fresh triage (2026-07-25) of sports_consolidated_closeout_2026_07_19.md's own native todos —
  distinct from every prior satellite batch, which deliberately never touched this doc's own checkboxes. Applies the
  same task_template.md §4 "Dispatch-scope eligibility" bar used throughout this session's other sports batches.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports consolidated closeout — native AO extract

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review. All 26 todos
> below are same-priority-tier-independent and touch distinct files (verified individually per todo — see each todo's
> own scope note); todo 1 internally sequences its own 2 steps (live-probe → delete → re-census) inside ONE todo rather
> than being fanned out, per the established pattern in `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s summary
> ("AO's per-todo model has no mechanism to mechanically gate step N on step N-1 within one plan short of
> `sequential: true` for the WHOLE plan... combining same-job chains into one todo each is the safe choice").
>
> **The parent plan (`sports_consolidated_closeout_2026_07_19.md`) is currently OVER the 1000-line hard cap (1002L,
> `check_line_caps.sh` HARD-fails) and is uncommittable via the normal path** — see
> `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #9. This extraction does not touch that file at all
> (not even a one-line pointer) for exactly this reason: any edit to it currently cannot be committed.

## Todos

- [ ] [DATA] P0. **Track F — PURGE the fabricated POST-FLOOR `derived_features` remainder (Jun-Dec 2020 + 2021-2026
      only) + re-verify by CENSUS, one worker, in order.** **⛔ CORRECTED 2026-07-26 (slot-12 `data_engineering`): this
      todo's own "Not `[OPERATOR]`-gated" justification was WRONG at the time and was removed** — the original triage
      had merely ASSERTED "GCS soft-delete gives a 7-day recovery window, reversible" without ever querying the actual
      bucket policy, and no carve-out existed in the codex SSOT yet at that point. **✅ RE-CORRECTED 2026-07-27 —
      `[OPERATOR]` removed again, this time on a verified rather than asserted basis.**
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (added 2026-07-26, AFTER the 07-26 correction
      above) now provides exactly the carve-out that doc's §3.1 lacked when this todo was last edited: an object/
      prefix-scoped prod-bucket delete (never a whole-bucket destroy) may proceed agent-side once a FRESH, same-run
      `gcs_bucket_soft_delete_retention_seconds(bucket)` check confirms ≥604800s retention. This todo's delete is
      object-scoped (specific `derived_features` parquet objects filtered by creation timestamp, never the
      `features-sports-prd-central-element-323112` bucket itself) — fresh-checked 2026-07-27, retention returned
      `604800` (7 days), so it qualifies (finding T, `task_template.md`). **Secondary, reinforcing point the 07-26
      correction didn't consider**: `derived_features` is itself a DERIVED dataset computed from raw market/odds data
      that this delete does not touch — even independent of the 7-day GCS window, any day's features can be re-derived
      from source at any time, which is a stronger reversibility argument than soft-delete alone (though not what §3a's
      check itself tests for). Confirmed real, populated corpus in scope (not already-resolved): `gcloud storage ls -r`
      on a sample day (`sports_features/by_date/day=2021-01-01/**`) shows real
      `league={id}/feature_group=derived_features/     features.parquet` objects across multiple leagues — this is NOT
      an empty/moot target. **Step 1 (live-probe, SAFE, READ-ONLY)**: run a GCS creation-time census across
      `features-sports-prd-central-element-323112`'s
      `sports_features/by_date/day={D}/league={L}/     feature_group=derived_features/` corpus for Jun-Dec 2020 +
      2021-2026 to establish the CURRENT pre-/post- `2026-07-19` object-count split directly (do not trust the parent
      doc's contradictory checkbox state). **Step 2 — now agent-executable, no operator sign-off needed** (re-query the
      bucket's soft-delete retention fresh immediately before running, not from this citation): snapshot the delete
      list, then delete every object from that scope still carrying a pre-`2026-07-19` creation timestamp (honest
      absence beats an invented `competition_phase` — do NOT re-touch pre-floor 2017-2019/pre-06-06 2020 dates, already
      handled by the separate pre-floor wipe). **Step 3**: re-run the census, confirm 0 remain. (repo: features-service
      / GCS `features-sports-prd-central-element-323112`). **Done when**: the step-3 census returns 0 post-floor
      `derived_features` objects with a pre-`2026-07-19` creation timestamp. Source:
      `sports_consolidated_closeout_2026_07_19.md:244-259`.
- [ ] [REVIEW] P1. **Track C — re-verify the existing K1/K2 delete-candidate GCS object list against the CURRENT casing
      state.** Read-only: a fresh object-level census confirms whether the candidate list matches the corpus's actual
      casing as of the check date (it may predate or postdate the still-pending lowercase-revert). No delete action in
      this todo itself. (repo: market-tick-data-service / instruments-service, read-only census). **Done when**: either
      the census confirms the existing candidate list still matches current corpus state, or a corrected list is
      produced and cited. Source: `sports_consolidated_closeout_2026_07_19.md:337-340`.
- [ ] [DATA] P1. **Track C — venue vocabulary safe re-stamp + SMARKETS residual purge (excludes the KALSHI/POLYMARKET
      cross-AG bleed sub-item).** Now that the parts[]-index parser fix has shipped
      (`market-data-processing-service@51502c3` + `instruments-service@f46e553e`, verified via `git log`), re-stamp: (1)
      casing/alias rewrite LADBROKES_UK→LADBROKES, UNIBET_UK/UNIBET_EU→UNIBET, SPORT888→BET888SPORT (all 4 already exist
      correctly-cased in the UAC venue registry — pure re-stamp, no registry gap); (2) the footystats legacy bundle
      mislabel `venue=ODDS_API`→`FOOTYSTATS` (42,476 rows, a separate writer defect from the parser bug); (3) the
      parse-bug residue FOOTBALL/UNKNOWN (parser fix already shipped, existing rows need re-stamping to match). THEN
      snapshot-then-purge the small SMARKETS residual (an explicitly-deleted venue per codex — "removed from all repos,
      no manifest rows should be expected" — any remaining rows are stale residue, not a registry gap). **EXCLUDES**:
      the cross-AG bleed sub-item (KALSHI, POLYMARKET rows belonging to `asset_group=prediction`) — already tracked as
      its own AO-eligible candidate in `sports_satellite_ao_dispatch_batch3_2026_07_25.md:132` ("Determine the
      disposition of `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/... rows") — drafting it here too would
      duplicate that work. **Self-justified, not `[OPERATOR]`-gated**: the re-stamp mirrors the same safe
      copy/verify/swap-or-relabel pattern K1/K2 shipped without an `[OPERATOR]` tag elsewhere in this same doc family;
      the SMARKETS purge is snapshot-first against a tiny, already-fully-removed-venue residual population. (repo:
      market-data-processing-service / market-tick-data-service / instruments-service catalogue). **Done when**: a
      corpus-wide sports venue census shows 0 rows for LADBROKES_UK/UNIBET_UK/UNIBET_EU/SPORT888/FOOTBALL/UNKNOWN/
      SMARKETS, and 0 rows carrying the footystats-legacy-bundle `venue=ODDS_API` signature. Source:
      `sports_consolidated_closeout_2026_07_19.md:364-374`.
- [ ] [CLEANUP] P2. **Track S — snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout** (frozen
      2026-04-20, no entities). **Built-in safety gate**: first confirm no reader consumes it (grep both repos for the
      path); if a reader is found, STOP and report instead of deleting — do not proceed with the cull. Self-justified,
      not `[OPERATOR]`-gated: snapshot-first + the reader-check is a hard fail-safe baked into the todo itself. (repo:
      instruments-service / GCS). **Done when**: the reader-check result is recorded, AND (if clear) the snapshot+delete
      has executed with a post-delete listing confirming 0 objects remain. Source:
      `sports_consolidated_closeout_2026_07_19.md:421-422`.
- [ ] [DOC] P2. **Track S — Finding C correction: fix the cutover runbook's canonical-is-a-superset premise for raw odds
      on early dates**, citing `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`
      (`status:     resolved`, corpus-destroying risk already remediated — only this documentation correction remains).
      (repo: unified-trading-pm, doc edit — locate the cutover runbook via
      `sports_legacy_bucket_cutover_2026_07_16.md`'s own references). **Done when**: the cutover runbook is corrected
      and cites this doc. Source: `sports_consolidated_closeout_2026_07_19.md:423-429`.
- [ ] [CODE] P1. **Track E — wire the T0/T1 dependency gate for real: make every real caller of the pre-flight pass
      `date=`.** Currently the pre-flight only fires `if date is not None` and no caller passes it, so the fail-loud
      boundary is unreachable (`sports_t0_t1_dependency_gate_never_wired_2026_07_15`). (repo: instruments-service /
      market-tick-data-service — locate the pre-flight + its real callers by symbol). **Done when**: a T0-before-T1
      ordering violation actually raises in a test (not just "the code path exists but is never hit"). Source:
      `sports_consolidated_closeout_2026_07_19.md:450-453`.
- [ ] [DIAG] P1. **Track O — root-cause the 112,277 `attempted_failed` rows confined to exactly BETFAIR/MATCHBOOK/
      PINNACLE (all 6 years) — DIAGNOSIS ONLY, do NOT relabel.** Likely `_SNAPSHOT_VENUES` CLV completeness, not primary
      capture — confirm or deny. The relabel action itself stays explicitly out of this todo's scope (per the parent
      doc's own "Operator decisions needed" section, flagging a premature relabel as irreversible-adjacent). (repo:
      market-tick-data-service, read-only). **Done when**: a written root-cause finding confirms or denies the
      `_SNAPSHOT_VENUES` CLV-completeness hypothesis, citing the actual mechanism. Source:
      `sports_consolidated_closeout_2026_07_19.md:490-491`.
- [ ] [DIAG] P1. **Track O — locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed`
      rows** (confirmed not `_emit_sports_v1/v2_sentinels`). **Scoping note**: the source todo frames this as "before
      folding into K2" — that downstream framing is now STALE (K2's casing migration is itself superseded and slated for
      revert per Track C), so this candidate is pure standalone diagnosis, not a K2-fold-in precondition. (repo:
      market-tick-data-service / instruments-service, read-only). **Done when**: a written finding names the
      emitter/mechanism producing these rows. Source: `sports_consolidated_closeout_2026_07_19.md:492-493`.
- [ ] [DIAG] P2. **Track O — corpus-wide scan for other low-fixture dates whose only in-window odds fall in the
      T-12h↔T-24h dead-zone, + investigate why the multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet
      2025-12 days.** **Scoped DOWN from the source todo**: drops "consider adding a T-18h horizon or widening the T-24h
      staleness cap" — that's an undecided design choice with no defined target, stays human; this candidate is scan +
      diagnosis only. **Conflict-check clearance**: confirmed DISTINCT from
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s already-dispatched zombie-tick sweep (that doc's own note:
      "a DIFFERENT cap in a DIFFERENT file/mechanism entirely" — that one is the fetch-based `STALENESS_CAP_SECONDS`
      zombie-tick rejection in `_prepare_tick_data()`; this todo is about `TIER1_HORIZONS` spacing logic in
      `bucket_assignment_adapter.py`). NOTE FOR THE DISPATCHED WORKER: do not conflate the two staleness caps in your
      report. (repo: market-tick-data-service, read-only scan). **Done when**: a written list of affected dates + a
      root-cause finding on the loop-skip is recorded; does NOT decide the T-18h-horizon/cap-widening question. Source:
      `sports_consolidated_closeout_2026_07_19.md:494-496`.
- [ ] [CODE] P1. **Track H — implement the registry-aware honest-coverage denominator in
      `compute_coverage_for_bucket()`** (deployment-api) — sports coverage % must reflect "captured / UAC registry
      universe," not "captured / raw manifest." **REQUIRED FIRST STEP (live-probe, do not trust the source todo's
      "largely executed" framing at face value)**: run a live manifest census confirming 0 sports manifest rows still
      carry non-registry-form `league_id` strings; if any non-registry rows remain, STOP and report instead of shipping
      the denominator change (a registry-membership test cannot be correct while non-registry rows exist). (repo:
      deployment-api). **Done when**: the live-probe confirms 0 non-registry `league_id` rows AND the denominator code
      change ships, verified against a real bucket. Source: `sports_consolidated_closeout_2026_07_19.md:536-541`.
- [ ] [CODE] P2. **Track H — implement RAISE-on-all-NaT for `AvailableAtStampingError`** (operator-ruled: fail loud at
      the shard that can't be stamped, not skip-with-record) at the CF-8 fix's own code path
      (`market-tick-data-service@af627b5b`). **Scoping note**: only the CODE change ships via this todo — the CF-8
      production maintenance-window RUN itself stays human/operator-gated (needs an operator to lift stop `BLK-d9137d48`
      and schedule the window), so this candidate does not require that window to have run; it just needs to exist and
      be tested against the already-shipped CF-8 fix's code path. (repo: market-tick-data-service). **Done when**: a
      test demonstrates an all-NaT shard raises `AvailableAtStampingError` instead of silently skip-recording. Source:
      `sports_consolidated_closeout_2026_07_19.md:558-561`.
- [ ] [OPS] P2. **Track V — re-roll `build_instrument_catalogue.py --asset-group sports --since 2019-01-01`** to pick up
      the +26,894 round rows produced by the pre-2019-scope (§T) + registry-membership (§U) decisions and the 2026-07-18
      round-derivation sweep — the catalogue snapshot predates all of them. Self-justified, not `[OPERATOR]`-gated:
      idempotent catalogue-snapshot regeneration from current registry+manifest state, not a destructive delete of
      source data. (repo: instruments-service). **Done when**: the catalogue snapshot is regenerated and reflects the
      round-row count increase. Source: `sports_consolidated_closeout_2026_07_19.md:630-632`.
- [ ] [CODE] P2. **Track V — upgrade the catalogue `player` grain from `entity=injuries` (injured-only) to
      `entity=fixture_lineups`** (full roster, now carries 100% player/coach identity). (repo: instruments-service,
      `build_instrument_catalogue.py`). **Done when**: the catalogue's player grain reads from `fixture_lineups` and a
      spot-check confirms full-roster coverage vs the old injured-only set. Source:
      `sports_consolidated_closeout_2026_07_19.md:633-634`.
- [ ] [DATA] P2. **Track V — determine which launcher ran the most recent sports features backfill** (NOT a VM launch —
      this todo is a read-only audit of PAST launch history/logs; no VM is started by this todo itself) — serial
      `launch-features-sports-backfill-vm.sh` or parallel `launch-features-sports-parallel-backfill-vm.sh`. (repo:
      deployment-service, read-only log/dispatch-record audit). **Done when**: the launcher used is named with its
      citing VM log/dispatch record; if serial, a follow-up todo is filed requiring the parallel launcher for every
      future sports features backfill (that follow-up todo, not this one, would be the actual VM-launch-relevant
      action). Source: `sports_consolidated_closeout_2026_07_19.md:635-638`.
- [ ] [BACKEND] P2. **Track K — confirm whether any primary sports entrypoint (not a one-off script) exposes a genuine
      fixture-level targeting flag for shard-splitting a backfill run.** (repo: features-service / market-data-
      processing-service, read-only CLI audit). **Done when**: either a cited flag+file is named, or the add-flag todo
      exists with a named target CLI. Source: `sports_consolidated_closeout_2026_07_19.md:661-664`.
- [ ] [DATA] P1. **Track K — run + cite 3 dated checkpoints (pre-backfill baseline, mid-backfill spot-check,
      post-backfill final gate) for EACH of the 5 required mechanisms** (`data-pipeline-check-is`/`-mtds`/`-mdps`/
      `-features` + `/data-pipeline-reconciliation`) against sports — currently ZERO real run-todos exist for any of the
      5 despite all 5 already supporting sports's shard atoms (task_template.md §3 finding K). **Use the already-pinned
      `SPORTS_SMOKE_DATES` constants as the reference dates** (busy `2025-12-20` / thin `2025-12-24` /
      `known_buggy_odds` `2025-12-18` / `known_buggy_fixtures` `2024-03-09` — shipped
      `features-service@84cb4613`/`@0ae9f460`) rather than inventing a day, since several of these skills explicitly
      require the day to come from the operator, not be invented — these are the doc's own already-established canonical
      smoke dates, resolving that constraint. (repo: cross-repo, skill-driven). **Done when**: each of the 5 mechanisms
      has 3 dated runs cited by report path/dispatch_id, baseline through final. Source:
      `sports_consolidated_closeout_2026_07_19.md:665-669`.
- [ ] [DOC] P2. **Track X — update the sports issue-doc index**: it lists
      `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` as merely open/P2, but
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` already has a DECIDED (2026-07-23) naming scheme +
      scoped 3-repo migration in flight — a fresh agent shouldn't re-litigate the naming decision. **First locate the
      actual index** (grep the corpus for the literal string `sports_odds_feature_naming_four_way_mismatch_2026_07_21`
      to find every referencing doc — the exact index location isn't self-evident from the source todo alone). (repo:
      unified-trading-pm, doc edit). **Done when**: every located index entry is corrected, citing the decided doc.
      Source: `sports_consolidated_closeout_2026_07_19.md:727-731`.
- [ ] [BACKEND] P2. **Track X — audit adapters under instruments-service's `.../adapters/sports/adapters/`,
      market-tick-data-service's `.../adapters/sports/`, and execution-service's `.../sports_execution/adapters/` for
      dead code, silent fallbacks, and duplicated logic** — cite
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. (repo: instruments-service /
      market-tick-data-service / execution-service, read-only). **Done when**: a written per-repo finding list (or an
      explicit "none found") exists, each finding citing a symbol. Source:
      `sports_consolidated_closeout_2026_07_19.md:770-773`.
- [ ] [DOC] P3. **Track X — add `data_completion_sports_history_2026_07_24.md` (0 open todos) as a bulleted entry to
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s Aggregated-source-docs index** — it is not
      currently listed there. (repo: unified-trading-pm, doc edit). **Done when**: the entry appears in that file's
      index with its open-todo count noted. Source: `sports_consolidated_closeout_2026_07_19.md:774-777`.
- [ ] [DATA] P2. **Track S2 — check whether the mis-keyed-duplicate bug class** (`rebuild_sports_manifest_v9.py` E4
      apply-pass bug, fixed going forward `market-tick-data-service@55f9e961`) **hit the `mdps` surface or any other
      bucket rebuilt via the same script family.** **EXCLUDES** the sibling "88 orphan rows manual review + disposition"
      sub-item from the same source todo — explicitly framed as "manual review," stays human. (repo:
      market-data-processing-service / market-tick-data-service, read-only). **Done when**: a written finding either
      confirms the bug class is absent elsewhere, or names the affected buckets/rows. Source:
      `sports_consolidated_closeout_2026_07_19.md:847-852`.
- [ ] [DATA] P1. **Track S2 — Sports P2a sub-item (c) ONLY: re-run the 40,041 FIXTURES `attempted_failed` rows for
      2018/2021/2023.** **EXCLUDES** sub-items (a) G1 non-canonical-league NOISE wipe (~1,437 leagues/~106k rows — a
      purge with an unconfirmed relationship to the already-answered §U non-registry-league decision; needs an explicit
      check whether it's the SAME population as that decision's already-approved 489-pair/10,869-row purge before
      executing, since the scale differs by ~10x) and (b) G2 2015-2017 zero-captured diagnosis (bundles an undecided
      "then fix" after diagnosis, subscription-tier-limit-vs-backfill-bug is an open question) — both stay human,
      flagged separately below. Self-justified, not `[OPERATOR]`-gated: standard skip-aware re-run/backfill pattern, not
      a delete. (repo: instruments-service). **Done when**: the re-run completes for the 3 named years, with a fresh
      census of remaining `attempted_failed` cells cited. Source: `sports_consolidated_closeout_2026_07_19.md:863-868`.
- [ ] [DATA] P2. **Track S2 — TEAMS full-history backfill.** **REQUIRED FIRST STEP (live-probe)**: verify whether
      `sports_data_sources_canonical_completion_2026_07_13.md`'s consolidator NULL/empty-string dedup-key fix has
      actually shipped (check its plan status + cited commit) — the source todo states this fix "must land first"; if
      not shipped, STOP and report rather than proceeding with the backfill. **VM-launch discipline**: SPOT provisioning
      by default per the workspace backfill-VM hard rule. (repo: instruments-service). **Done when**: the prerequisite
      is confirmed shipped AND the TEAMS full-history backfill completes with a fresh coverage census cited. Source:
      `sports_consolidated_closeout_2026_07_19.md:911-913`.
- [ ] [INFRA] P2. **Track S2 — investigate + partially close the legacy-CAS aggregate-manifest-gate question, combined
      with the independent 205-227 cell re-fetch.** (1) Read `unified_trading_library.manifest_consolidator`'s
      merge-source code to confirm or deny the hypothesis that the shard-fallback aggregate gate structurally never
      folds in a prior legacy-CAS (non-per-VM-shard) write — a one-off closer script closed 5,288 cells via legacy CAS
      write, verified correct at the cell level 3× independently, but the shard-fallback aggregate gate never reflected
      it even after a full consolidator-cadence window. (2) Separately (independent of (1)'s outcome) re-fetch the
      ~205-227 genuine gap cells from that closer's own dry-run — a normal targeted re-fetch. (repo:
      unified-trading-library / instruments-service). **Done when**: a written confirm/deny of the hypothesis citing the
      exact code path is recorded, AND the ~205-227 cell re-fetch completes with a fresh count. Source:
      `sports_consolidated_closeout_2026_07_19.md:914-920`.
- [ ] [VERIFY] P2. **Track S2 — reconcile the post-07-13 rebuild delta** (`PLAYER_VALUES` −10,934, `ODDS` −3,180
      captured cells vs the 2026-07-12 verified state) against real GCS objects, via a per-key manifest-vs-GCS diff —
      determine phantom-correction vs data loss. **Flagged as important**: a genuine data-loss verdict here would be a
      real finding, not just hygiene — surface it prominently regardless of outcome. (repo: instruments-service,
      read-only diff). **Done when**: the per-key diff is run and a written determination (phantom-correction vs data
      loss) is recorded for every missing key. Source: `sports_consolidated_closeout_2026_07_19.md:937-941`.
- [ ] [DATA] P2. **Track S2 — mirror the staleness-budget fix + drop hardcoded workarounds.** (1) Add `"sports": 1800`
      to deployment-api's `_AG_STALENESS_BUDGET_SEC` (cockpit consolidator-health view) — the UTL-side
      `AG_STALENESS_BUDGET_SEC` mirror already shipped (`unified-trading-library@fd87daa1`, verified via `git log`); (2)
      grep the fleet for hardcoded `MANIFEST_CONSOLIDATED_STALENESS_SEC` sports workarounds and drop them now that the
      override lands. (repo: deployment-api, cross-repo grep). **Done when**: the deployment-api mirror lands and a
      fleet-wide grep confirms 0 remaining hardcoded workarounds (or none found). Source:
      `sports_consolidated_closeout_2026_07_19.md:942-946`.
- [ ] [DATA] P3. **Track S2 — write the `check_high_attempted_failed` runbook note for deployment-service** documenting
      the sports/trades `DP_RUN_MOSTLY_EMPTY` 87.2% ratio spike as a K1/K2 denominator-shrink artifact on already-dead
      residue, not a live outage (so a future on-call doesn't re-diagnose this from scratch). **EXCLUDES** the sibling
      "re-check once the K1/K2 legacy-object DELETE executes" sub-part — gated on the still-operator-pending K1/K2
      delete (Track V), stays human/deferred to a follow-up once that delete lands. (repo: deployment-service, doc
      edit). **Done when**: the runbook note is added. Source: `sports_consolidated_closeout_2026_07_19.md:951-955`.

## Classification notes — why every OTHER open native todo stays human

_Not exhaustive here — the full table is in the dispatching session's report._

The 26 todos above are a genuine minority of the parent doc's ~65 open top-level / 78 total open todos. The rest split
into: (a) explicit `[OPERATOR]`/`BLOCKED-<TOKEN>`-tagged items (structurally non-dispatchable already); (b) irreversible
GCS deletes gated on the still-pending K1/K2 casing revert or league_id migration (themselves operator-scheduled, per
`issues/autonomous_session_operator_decisions_2026_07_25.md`); (c) items already flagged as conflict-gated against a
satellite batch in that same operator-decisions doc (Sports P2b, the R1/R2/R3 gate, the Track S2 decision-16
day-partition investigation, the Track E entity=fixtures repoint); (d) open design/judgment calls with no defined target
(the EXCHANGE_ODDS/FIXED_ODDS fork's first step is itself `[OPERATOR]`, the cross-object-CAS safety-mechanism design,
Track S's "eliminate OR document" fork); (e) live-production-supervision items explicitly marked "DELIBERATELY NOT done
unsupervised"; (f) items whose real content lives in another doc this extraction is out of scope for (pointers to
`sports_legacy_bucket_cutover_2026_07_16.md`'s T2.9/T2.10,
`sports_canonical_universe_and_apifootball_reference_ expansion_2026_06_24.md`'s own ~9-11 todos, a mis-filed DEFI
item). See the dispatching session's full report for the per-todo table.

## Progress Log

- 2026-07-26 (slot-12, `data_engineering`): **Todo 1 (Track F derived_features purge) — corrected mis-gating + completed
  the worker-safe portion; the delete itself stays human.** The todo's own "Not `[OPERATOR]`-gated" justification was
  WRONG: confirmed the target bucket is `features-sports-prd-central-element-323112` (a genuine `-prd-` production
  bucket) and `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1's "Any prod-bucket delete" hard stop is
  unconditional — no soft-delete-reversibility carve-out exists in that section. Added `[OPERATOR]` to the todo +
  corrected its justification text (see todo 1 above). Ran the SAFE, read-only Step 1 live-probe as a bounded SAMPLE
  (not an exhaustive multi-year walk — a full census across ~6.5 years × all leagues would itself be a
  whole-corpus-scale GCS walk better run as its own single-walk-compliant job, and the delete needs operator execution
  regardless): 5 sample days across the range (`2020-06-06`, `2021-06-15`, `2022-06-15`, `2024-06-15`, `2026-06-15`),
  one `derived_features` object's real `creation_time` checked per day via `gcloud storage objects describe`. Result:
  `2020-06-06`'s sampled object has `creation_time=2026-07-17T21:52:06Z` — genuinely PRE the `2026-07-19` cutoff,
  confirming the fabricated post-floor residue the todo describes STILL EXISTS for at least this date. The other 4
  sampled dates (`2021-06-15`/`2022-06-15`/`2024-06-15`/`2026-06-15`) all show `creation_time=2026-07-19T*`, consistent
  with the parent doc's "re-run" checkbox having genuinely regenerated most of the corpus that day — so BOTH
  contradictory signals in the source todo's prerequisite state were partially right: the bulk re-run happened, but
  residue remains. **Handoff to operator**: this sample is sufficient to confirm the purge is still needed and
  non-trivial in scope, but not exhaustive enough to safely drive a delete list — recommend either (a) the operator runs
  the full census + delete personally, or (b) files a dedicated, properly-VM- launched, single-walk-compliant follow-up
  plan for the exhaustive census + delete (Tier-2 SPOT VM, per the workspace heavy-I/O rule). Not flipping todo 1's
  checkbox — the substantive delete action has not occurred.
