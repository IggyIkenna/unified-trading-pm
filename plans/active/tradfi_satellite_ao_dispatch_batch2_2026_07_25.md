---
doc_type: plan
title: TradFi satellite AO batch 2 — re-triage clearance from batch1's 33 conflict-gated deferrals
summary: >-
  Second AO-dispatch batch for tradfi, produced by the `/ag-closeout-audit` skill's batchN re-check methodology (never a
  fresh Workflow triage) against `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s own Deferred section — 33
  conflict-gated candidates across 13 docs (the 5th, `tradfi_manifest_content_recovery_completion_2026_07_24.md`, stays
  excluded per batch1's `doc_too_large_or_risky_for_batch` flag and still needs its own dedicated pass). Re-checked
  every named competing claim in `tradfi_consolidated_closeout_2026_07_18.md` against its CURRENT content plus a live
  git-log sweep of the relevant repos since the 2026-07-25 triage: 20 of the 33 candidates cleared (11 shipped, 9 either
  shipped independently between the triage and this re-check or superseded by a resolved sub-question), 4 candidates
  were found to have ALREADY SHIPPED outside AO dispatch during that same window (noted, not re-dispatched), 1 candidate
  is subsumed into another cleared candidate's broader fix, and 8 candidates remain genuinely conflict-gated (competing
  claim still open, unshipped). Same combine-same-file-collision discipline as batch1: 3 groups of same-source-doc
  candidates are bundled into single combined todos (11 dispatchable todos total from the 20 cleared candidates).
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-2, satellite-docs, conflict-recheck]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi re-triage pass, 2026-07-25, per the skill's "batchN methodology" section (added same day).
  Step 1 (re-check prior batch's Deferred section against current state) run against
  `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 33 conflict-gated candidates across 13 docs, using the original
  triage journal `subagents/workflows/wf_92bc129c-2a8/journal.jsonl` (`tradfi_batch1_triage.json` scratch extraction)
  for exact candidate text + conflict quotes, cross-checked against `tradfi_consolidated_closeout_2026_07_18.md`'s live
  content and a `git log --since="2026-07-25 02:00"` sweep across unified-api-contracts, market-tick-data-service,
  instruments-service, deployment-service for anything that shipped between the original triage and this re-check. No
  fresh Workflow triage was run (this is a re-check pass per the skill's explicit guidance).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 2 — re-triage clearance

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 11 todos below are same-priority; same-source-doc collisions were resolved by combining
> candidates into ONE todo per source doc (3 combined groups: data_completion_tradfi,
> instruments_tradfi_g1_g5_gate_execution, tradfi_backfill_throughput_followups) — **one remaining cross-todo file
> collision found and flagged 2026-07-25 (plan-reconcile), not zero**: todos 3 and 9 both write a checkbox flip to
> `tradfi_backfill_throughput_followups_2026_07_24.md` as part of their own Done-when (see each todo's own
> Conflict-check note) — do not dispatch/commit those two concurrently.

## Re-check summary (what changed since batch1's 2026-07-25 triage)

Real, independent progress landed on tradfi between the original triage (~02:14–02:49 UTC) and this re-check (~11:00+
UTC), confirmed via `git log`:

- `unified-api-contracts@32b2879c` — **CME coverage-floor mismatch reconciled** (`coverage_starts.py` now matches
  `venue_mapping.py`'s verified 2020-01-01) — this is the CME-floor ambiguity
  `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`'s candidate flagged as an open risk; it is now
  settled at the SAME value the candidate already planned to use → conflict clears (see Todos).
- `market-tick-data-service@c4f881b1` — **104,623 residual CF-11-origin phantom `attempted_failed` rows retired**
  (matches `tradfi_backfill_throughput_followups_2026_07_24.md`'s own candidate #2 verbatim) → already done, not
  re-dispatched.
- `deployment-service@545ff76` — **`OHLCV_FLEET_CONCURRENCY_CAP` 60→150 + default `TRADFI_OHLCV_MACHINE`
  `e2-highmem-4`→`e2-highmem-16` shipped** (matches `tradfi_backfill_throughput_followups_2026_07_24.md`'s own candidate
  #5 verbatim) → already done, not re-dispatched. This ALSO flips the direction of
  `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s machine-type conflict (that doc wanted to confirm the OLD
  `e2-highmem-4` baked default; the baked default itself moved to `e2-highmem-16`, the value the OTHER side of the
  conflict wanted — both sides now agree; that doc's own P2 checkbox for this was independently re-verified live
  2026-07-25 and is already `[x]`).
- `market-tick-data-service@a23dd8bd` + `instruments-service@52d8b3ef` — chain-bundle content-rewrite executor +
  catalogue Surface-A USD@LIN re-sweep landed; neither is the specific catalogue-rebuild ground any of the 13 docs'
  candidates targeted (MVP-flag promotion / delisted-liveness recheck), so no additional conflict clears from these two.

Beyond the git-log sweep, a large fraction of the 33 candidates turned out to have **no real conflict at all** on closer
per-candidate mapping: batch1's own Deferred section counted several docs' candidates as a single "N items deferred"
block, but the original triage's `conflicts_found` entries frequently named only ONE specific sibling item in a
multi-candidate doc — the other candidates in the same doc were swept along conservatively despite having zero recorded
conflict. Re-mapping each conflict to its actual target candidate (not just its source doc) is what surfaces most of the
20 clearances below — this is a genuine artifact of batch1's conservative whole-doc deferral, not a claim that anything
changed since batch1.

## Todos

- [ ] [DATA] P1. **Re-run the tradfi manifest venue/data_type drift audit (no conflict was ever recorded against this
      candidate — it was grouped under `data_completion_tradfi_2026_07_15.md`'s whole-doc deferral)**, combined with
      **deploying the already-shipped MDPS ohlcv_15m/24h `canonical_writer` fixes** into ONE todo (both edit the SAME
      doc file — `data_completion_tradfi_2026_07_15.md` — and would collide if dispatched as two concurrent AO todos):
      (1) Re-run the drift audit against the live `market-data-tick-tradfi-prd` `_index` (post-v9-walk) to confirm the
      2026-06-04 finding (6,602 rows: 4,130 blank/`UNKNOWN` venue + 2,472 blank data_type) was resolved by the E5
      path-re-derivation walk; diagnose (do NOT bulk-rename) any residual blank/`UNKNOWN` venue or blank data_type rows.
      Flip/update the P1 drift-verify checkbox (line 54) and the E6 CF-7 relabel checkbox (line 177). (2) Rebuild the
      market-data-processing-service tarball from a clean LDR checkout and relaunch `mdps-backfill-tradfi-*` to deploy
      the already-shipped `canonical_writer` fixes (row_key omits `instrument_id` for aggregated shards; `source`
      threaded from the input `pipeline_mode`; both landed, tests green, per this doc's own Progress Log line 640).
      **Conflict-check note**: `tradfi_consolidated_closeout_2026_07_18.md`'s own Phase A2 todo frames "no ohlcv_15m/24h
      aggregation writer exists" as an open, undecided question — this is STALE relative to `data_completion_tradfi`'s
      more detailed, dated Progress Log entry, which shows the writer code already shipped and merely pending a
      tarball-rebuild deploy. Deploying it does NOT itself resolve Phase A2's broader "decision on whether to feed
      `vix_features`" framing (2 residual gaps remain out of scope here: part 3, ~64k old migrated-data
      `instrument_id='ticks_migrated*...'`rows need re-keying; part 4, massive-keyed phantom`expected_unattempted` seeds
      need reconcile-to-databento) — this todo deploys the shipped fix only, it does not close Phase A2. Repos:
      market-tick-data-service (manifest, read-only), instruments-service (audit tooling),
      market-data-processing-service (tarball rebuild), deployment-service (VM relaunch). **Done when**: (a) a fresh
      `\_index` read reports counts for blank/`UNKNOWN`venue, blank data_type, blank`asset_group=None`, plus the total
      captured-cell count vs. the pre-walk baseline (assert no unexplained ~6,602-row shrink); residual drift rows are
      root-caused (not renamed) and written up; the line-54 and line-177 checkboxes in
      `data_completion_tradfi_2026_07_15.md`are flipped/updated with the fresh numbers; AND (b) the relaunched MDPS VM's
      manifest writes for CME/NASDAQ/NYSE ohlcv_15m/24h pass validation (no more `MalformedRowKeyError`/missing-source
      rejection), a fresh manifest read shows non-zero newly-captured ohlcv_15m/24h cells for tradfi, and the line-629
      checkbox's sub-bullet is updated with deploy evidence (tarball sha / VM name / T+10min manifest read). Source:
      `data_completion_tradfi_2026_07_15.md`.

- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review)** — Combined instruments-foundation cleanup pass — 7
      independent, conflict-clear candidates from `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`, bundled into
      ONE todo because all 7 would otherwise edit the SAME doc file concurrently** (mirrors batch1's tradfi_legacy_twin
      combine): (1) Verify instruments-service CME (GLBX.MDP3) instrument-definition catalog manifest coverage for
      2019-01-01 through today in `instruments-store-tradfi`, checking the already-running
      `launch-tradfi-is-defs-sharded.sh` 9-shard fleet's current coverage first; launch a backfill shard for any real
      gap (never copy definitions between dates — CME futures expire daily). (2) Write unit tests for UAC's
      `databento_subscription_allowlist` covering allowed vs blocked dataset, banned OHLCV schema, per-level
      lookback-floor boundaries, batch-ban behavior, break-glass override, and enum-repr normalization (repo:
      unified-api-contracts). (3) Add a grep-based QG ratchet check enforcing no raw `batch.submit_job` call outside the
      guarded `submit_batch_job` wrapper and no off-allowlist Databento dataset string literal in tradfi fetch paths;
      wire into market-tick-data-service's `quality-gates.sh`. (4) Re-fetch a small sample of old tradfi
      instrument-definition dates whose `instrument_count` changed (equity ETFs re-routed XNAS.ITCH→DBEQ.BASIC; CME
      cells now include EC* event contracts) via instruments-service; confirm the re-fetched parquet's instrument set
      matches the current universe, enumerate the remaining un-refetched range. (5) Remove the stale
      post-VIX-INDEX-retirement CBOE `ohlcv_15m` capability registrations: delete the `ohlcv_15m` entry from CBOE's list
      in UAC `expected_coverage.py` (~lines 135/156) and the
      `DataTypeCapability(venue="CBOE", data_type="ohlcv_15m", instrument_type="")` entry in UAC
      `data_type_capability.py`; update the stale `TradfiOhlcv15mAdapter` docstring in MDPS `ohlcv_passthrough.py` —
      this doc's own G1.f.2 post-retirement-cleanup section confirms zero live impact (0 consumers) and that this is
      unrelated to any FUTURE 15m-aggregation-writer decision (a new writer, if built, would add its own new capability
      declaration keyed to the FUTURE type, not resurrect this stale INDEX-type entry). (6) Confirm CI/SIT status for
      UAC commit uac@599acf93 (the G1.f.2 Stage-3 breaking change, now a month old and almost certainly resolved) via
      `gh run list` or git/CI history; update this plan's Deferred-work-table row #2. (7) Fix the stale
      self-contradiction in this plan's own "Gated Phase 2" section: its "Remaining G1 refinements (NOT yet done)"
      bullet (near the top) still frames the cefi-domain equity-perp exclusion and `XCBF.PITCH`→FUTURE/COMMODITY fix as
      undone, even though the SAME document's later G1.b and G1.c entries (dated 2026-06-25) show both already shipped
      with regression tests (`test_g1b_cefi_singles_excluded_from_tradfi_enumeration`,
      `test_g1c_xcbf_outright_only_drops_vx_spreads` / `test_vx_future_asset_group_is_commodity`) — verify live (post
      IS@92084d5c) that `get_instructions` excludes cefi-domain singles and `_DATASET_TO_asset_group["XCBF.PITCH"]`
      resolves FUTURE/COMMODITY, then edit the stale bullet to remove the contradiction. **Conflict-check note**: 2
      OTHER candidates from this same doc (verify/launch ES CME futures ohlcv for 2021-2024, and check/launch the ES_OPT
      lock) are DELIBERATELY EXCLUDED from this todo — `tradfi_consolidated_closeout_2026_07_18.md`'s own
      Phase-C-preceding todo (lines 216-222) still claims broad re-verification of these exact MVP cells via a DIFFERENT
      method (a fresh `data-pipeline-check-is`/`-mtds` run) and remains open/unshipped — that conflict is unresolved and
      stays deferred (see Deferred section). Repos: instruments-service, unified-api-contracts,
      market-tick-data-service, market-data-processing-service, unified-trading-pm (doc). **Done when**: all 7 sub-items
      are individually done per their own criteria (CME defs coverage recorded/gap-closed; new test module covers all 6
      allowlist scenarios and quality-gates.sh green in UAC; the new ratchet check runs green on the current tree and is
      verified to fail on a synthetic violation; a recorded sample-verification result + enumerated un-refetched range
      exists; `expected_coverage.py`/`data_type_capability.py` no longer list CBOE `ohlcv_15m` and the MDPS docstring no
      longer references it, quality-gates.sh green in both repos; uac@599acf93's CI/SIT verdict is recorded and the
      Deferred-work-table row #2 updated; the G1-refinements contradiction bullet is corrected to match the later
      G1.b/G1.c DONE entries) AND `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s corresponding
      checkboxes/table rows for items 1-7 are flipped/updated in the SAME commit. Source:
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`.

      **Evidence**: (1) CME coverage verified against its TRUE declared floor (2020-01-01, not 2019-01-01 — confirmed
                                              live via a SPOT VM finding zero active venues for all of 2019); 1 genuine gap (2024-11-08) backfilled, 2
                                              anomalous Sundays filed as a new P3 finding. (2) `databento_subscription_allowlist` unit tests already existed
                                              (39/39 pass, all 6 scenarios) — no new test needed. (3) The QG grep-ratchet already existed (MTDS STEP
                                              5.92/5.93) — re-verified green. (4) 2 of 3 sample re-fetches succeeded (2020-01-02: 38,669 records; 2023-01-03:
                                              47,810 records), confirming the pre-lockdown universe was far narrower; full 2020-01-01→2026-06-18 re-fetch
                                              range enumerated and filed as a new P2 finding for a dedicated backfill plan. (5) UAC's stale CBOE `ohlcv_15m`
                                              entries were already removed (2026-07-15); fixed the one remaining stale MDPS docstring. (6) uac@599acf93
                                              confirmed live on `main` via merge-ancestry + zero reverts + the removed symbols still absent a month later. (7)
                                              Doc self-contradiction corrected, live-reverified post IS@92084d5c. Shipped:
                                              `market-data-processing-service@aebca177c5` (docstring fix) + `instruments-service@6a54828f84` (script bugfix +
                                              2024-11-08 backfill, no code diff for the manifest write itself). All findings + underlying checkboxes flipped
                                              in `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` in the same commit.

- [ ] [SCRIPT] P1. **Conflict-check (2026-07-25 plan-reconcile): this todo's Done-when flips 3 checkboxes in
      `tradfi_backfill_throughput_followups_2026_07_24.md`; todo 9 below flips a 4th checkbox in that SAME doc. Do not
      dispatch/commit concurrently — run todo 9 (P1) first, then this todo (P2), so the two checkbox-flip commits don't
      race on the same file.** **Combined throughput-followups residual pass — 3 independent, conflict-clear candidates
      from `tradfi_backfill_throughput_followups_2026_07_24.md`, bundled into ONE todo because all 3 would otherwise
      edit the SAME doc file concurrently**: (1) Replace `ohlcv_split_ticker_groups`'s ticker-group fan-out in
      `_tradfi-ohlcv-launcher-lib.sh` (used by `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` and
      `launch-tradfi-bf-nyse-ohlcv-1m.sh`) with N contiguous DATE-range slices per venue (all tickers per VM) — MEASURED
      in this doc's own tick-26 analysis that per-calendar-date cost is ~1.46 min fixed + 7.1e-4 min/cell
      (ticker-count-independent), so the current ticker-group re-shard pays the per-date overhead 5× for ~1.0-1.2× the
      speed; date-slicing collapses equity critical path 7.1h→1.2h and equity compute 231→46 VM-h. Keep the ticker-group
      path reachable behind a flag for the pathological single-VM-memory-ceiling case. (2) Read the existing
      `vm-logs/tradfi-bf-cme-ohlcv-1m-<root>-<year>-*/run.log` files (no new VM launch) for ~6 additional CME roots
      spanning the liquidity spectrum (ES, NQ, GC, 6E, PL, CT) and compute each root's per-calendar-date cost, to narrow
      the current 26× heavy/light spread and tighten the 15-30h backfill ETA band. (3) Fix the stale SSOT header
      reference in `launch-tradfi-bf-cme-ohlcv-1m.sh` (confirmed still present via live grep, 2026-07-25 — cites the
      archived `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`, now at `plans/archive/2026_05/`, and a non-existent
      `tradfi_mvp_set_expansion_2026_07_21.md`) to point at the current live SSOT. Repos: deployment-service,
      unified-trading-pm (doc/Progress Log update). **Done when**: (a) a dry-run of both equity launchers shows
      date-slice fan-out with no date lost/duplicated, the ticker-group path remains reachable via its flag; (b) a
      recorded min/date figure exists for each of the 6 named CME roots and the ETA band in this doc's Progress Log is
      updated/an update recommendation filed; (c) the launcher's header comment no longer references an archived or
      non-existent plan doc; all 3 corresponding checkboxes in `tradfi_backfill_throughput_followups_2026_07_24.md` are
      flipped/updated in the SAME commit. Source: `tradfi_backfill_throughput_followups_2026_07_24.md`.

- [ ] [OPERATOR] P1. **Correct the live tradfi `availability_index` manifest for the ~97,828 combo/chain objects
      quarantined by the 2026-07-20 recovery run** — locate `recover_tradfi_garbage_underlying_2026_07.py --apply`'s
      retained per-shard `--out` TSV / `*.apply_outcomes.json` artifacts (VM launcher convention
      `gs://deployment-scripts-*/vm-logs/<vm>/...`) as the authoritative QUARANTINED-row list, then CAS-update those
      rows' `capture_status` to `attempted_failed` in the live manifest (mirroring
      `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s register/retire whole-index in-place-CAS pattern) so
      the manifest stops silently claiming `captured` at a path that no longer physically exists. **Tagged `[OPERATOR]`
      per `task_template.md` §3's delete-risk rule and `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`**
      (2026-07-25 delete/VM-launch gating pass) — this CAS-updates `capture_status` for ~97,828 live prod manifest rows,
      an overwrite of production state, not a reversible dry-run; per this SAME plan's own "reclassification races the
      consolidator too" near-miss precedent todo below (in-place manifest reclassification racing the live consolidator
      cron), the operator running this must pause the manifest-consolidator cron BEFORE the CAS pass and resume only
      after the post-pass spot-check confirms clean. If the run's per-shard artifacts are not retrievable, STOP and
      report that as the finding rather than launching a new full-corpus GCS walk (single-walk discipline). **No real
      conflict** — the original triage's own conflict note confirmed zero overlap with
      `tradfi_consolidated_closeout_2026_07_18.md`'s own remediation items (grepped, zero hits); the only flagged item
      is a DIFFERENT, reverse-direction problem (`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`) noted
      purely so the operator doesn't conflate the two — same non-blocking pattern as batch1's shipped Deribit combo
      item. Repo: market-tick-data-service. **Done when**: either (a) a CAS pass has run against the live tradfi
      `availability_index` manifest, `capture_status` reads `attempted_failed` for exactly the QUARANTINED-outcome row
      set from the 2026-07-20 recovery run, and a post-pass spot-check confirms 0 of those rows still claim `captured`
      at their pre-quarantine path; or (b) the run's per-shard outcome artifacts are confirmed unrecoverable and the
      todo is reported BLOCKED with that finding. Source:
      `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`.

- [ ] [AUDIT] P1. **Sweep `market-tick-data-service` for the remaining `run_in_executor(None, ...)` network-blocking
      call sites and classify each** — the doc's original "known so far" list is STALE (all 4 `databento_fetch`/
      `databento_batch_jobs` sites already moved to the dedicated `_get_dbn_fetch_executor()` pool, per
      `tradfi_backfill_throughput_followups_2026_07_24.md`'s own already-checked-off [BACKEND] P0). Two sites are NOT
      yet classified: `live/connectors/databento_tradfi_ws.py:482` (`_do_subscribe`) and `:515` (`_do_start`) — both run
      the Databento Live subscribe/start handshake on the default executor, bounded only by `handshake_timeout_s`.
      Classify these two plus confirm no others were missed via a repo-wide `grep -rn "run_in_executor(None"` over
      `market_tick_data_service/` (excluding tests). **Deliberately scoped to NOT touch the doc's [CODE] P1 checkbox or
      `status`/`resolved_by` frontmatter** — that closure is already claimed by
      `tradfi_backfill_throughput_followups_2026_07_24.md`'s own checked-off todo, which explicitly notes the
      doc-hygiene flip on THIS issue doc is still pending; leaving that flip to whichever side the operator wants to
      execute avoids racing it. Repo: market-tick-data-service. **Done when**: the issue doc's [AUDIT] P2 checkbox is
      flipped with a per-site verdict + rationale written inline for every remaining `run_in_executor(None, ...)`
      network-blocking site, explicitly including the 2 newly-identified sites — WITHOUT touching the [CODE] P1 checkbox
      or the doc's status/resolved_by fields. Source:
      `archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`.

- [ ] [TRADFI] P1. **Profile market-tick-data-service's per-date OHLCV fetch/decode path with `memray`** against one
      reproduced heavy chunk (a liquid `GC.OPT ohlcv_1s` expiry day, or a NASDAQ/NYSE many-symbol `ohlcv_1m` week) to
      identify what is holding the ~15 GB transient RSS peak despite ~1.3 MB/date of written output. Capture a memray
      flamegraph + summary and document the top allocation site(s) (e.g. eager DBN decode buffering vs an un-released
      pyarrow frame) as a dated addendum in the issue doc — diagnostic only, no code fix or machine-type revert
      required. **Conflict cleared**: the ONE recorded conflict for this doc targeted the OTHER candidate (verify/drop
      the `TRADFI_OHLCV_MACHINE` Cloud Run env override) — that item is now `[x]` DONE + independently re-verified live
      2026-07-25 (fleet confirmed running the baked `e2-highmem-16` default, no override present), so nothing is left to
      collide with; this memray-profiling candidate was never actually the conflict's target. Repo:
      market-tick-data-service. **Done when**: a memray flamegraph/summary artifact exists for the reproduced heavy
      chunk, the doc addendum names the specific top memory-allocating call site(s) with measured RSS numbers, and the
      `- [ ] [TRADFI] P2. memray...` checkbox is flipped to `[x]` citing that artifact/finding. Source:
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md`.

- [ ] [DATA] P1. **Codify the "reclassification races the consolidator too" near-miss into the manifest-consolidator
      SSOT** — the 2026-07-15 floor-clip run (`correct_tradfi_universe_floor_clip_and_vix_index.py --apply`) mutated the
      canonical tradfi `_index` in-place WITHOUT pausing the consolidator cron, avoiding a lost-update only by observed
      timing luck. Extend `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s existing "Surgical ROW REMOVAL from
      the canonical" pause-first section (or add an adjacent subsection) to state that ANY direct canonical-index
      read-modify-write — not only row-removal, but also in-place `capture_status` reclassification (floor-clip /
      rule-based reclass scripts) — must pause the consolidator cron first, citing this issue's 2026-07-15 Progress Log
      entry as the near-miss precedent. **No real conflict on THIS candidate** — the one recorded conflict for this doc
      targets a DIFFERENT, sibling item in the same source doc (the still-open "4,655 stale barchart rows keep-vs-purge"
      question, which remains a genuinely separate operator-input item, untouched here); this candidate is a pure
      documentation addition unrelated to that question. Repo: unified-trading-pm (doc-only). **Done when**:
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` contains an explicit statement extending the pause-first
      requirement to in-place reclassification/mutation operations (not only removal), cross-referencing this issue doc
      by filename; doc-only change, prek/quality-gates docs pass green. Source:
      `issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`.

- [ ] [INVESTIGATE] P1. **Root-cause the actual `WithinBoundsTradfiSourceZero` trigger for the live, active
      `ohlcv_1s`/`ohlcv_1m` CME/NASDAQ/NYSE population** — grep live logs for the already-shipped
      `DATABENTO_EMPTY_BUT_VALID` structured event (`_emit_empty_but_valid()` in `databento_fetch.py`) on a sample of
      affected (venue, date, instrument) cells, and diff the echoed request args against the 2026-07-13 working
      diagnostic in `tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`. Document whether this is a symbol-mapping
      edge, a per-venue date-window edge, or something else, in a new follow-up issue doc. **No real conflict on THIS
      candidate** — neither of this doc's 2 recorded conflicts targets it; both target the SIBLING candidate in the same
      doc (purge/ reclassify the 1,242 dead CBOE `ohlcv_15m` rows, deliberately left OUT of this batch, see Deferred).
      This candidate investigates the live, ACTIVE population, a different cohort from the dead CBOE rows. Repo:
      market-tick-data-service. **Done when**: a representative sample of affected (venue, date, instrument) cells has
      been diagnosed via the DATABENTO_EMPTY_BUT_VALID event log + request-arg diff, and a follow-up issue doc records
      the findings (root cause identified, or documented as still-open with the specific evidence gathered). Source:
      `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`.

- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): this todo's Done-when ALSO flips a checkbox in
      `tradfi_backfill_throughput_followups_2026_07_24.md` — the SAME doc the P2 todo above (3-item combined pass)
      writes to. Run this todo FIRST (higher priority), then the P2 todo, never concurrently.** **Make TradFi's `todo`
      denominator honest below the vendor discovery floor (4-step ordered sequence, one worker, execute in order)** —
      ALSO closes `tradfi_backfill_throughput_followups_2026_07_24.md`'s own P2 candidate on the SAME 182,407-cell
      cohort (that doc's phrasing pointed at `sentinels.py`, but a live grep confirmed `sentinels.py` has zero
      floor-related logic today; this candidate's more precise, already-verified target is the actual gap). (1)
      Re-measure and break down the 182,407 pre-floor cells by (venue, data_type, year) — extend the doc's own
      2026-07-20 re-verification by adding the YEAR axis and sweeping CBOE (floor 2020-06-01); confirm each counted cell
      is strictly-before its venue's floor (an off-by-one would wrongly reclass a real, fillable day). (2) THEN teach
      `instruments-service/scripts/enumerate_expected_universe.py`'s tradfi path a discovery-floor clip — mirror the
      file's existing `_tradfi_floor_start_for_data_type()` pattern (the BILLING floor) but source the NEW clip from
      `unified_api_contracts.registry.venue_mapping.VenueMapping.get_instrument_discovery_start(venue)`, resolved live
      at runtime — **confirmed via live grep 2026-07-25 that `get_instrument_discovery_start` is NOT currently called
      anywhere in `enumerate_expected_universe.py`, only the separate billing-floor is applied there today, so the gap
      is real.** (3) THEN write and run a one-off writer-side corrective-reclassification script over the exact
      below-floor cells enumerated in step 1, reclassifying `todo`→`expected_unattempted` in the live tradfi manifest;
      verify before/after counts. (4) THEN add a regression-guard test asserting the invariant: no cell below a venue's
      UAC discovery floor may be in state `todo`. **Conflict resolved**: the one recorded conflict flagged the TradFi
      CME floor as unresolved between `coverage_starts.py` (2010-01-01) and `venue_mapping.py` (2020-01-01) —
      `unified-api-contracts@32b2879c` (shipped 2026-07-25, AFTER the original triage) resolved this:
      `coverage_starts.py` now matches `venue_mapping.py`'s verified 2020-01-01, confirmed live against the MTDS
      manifest (earliest CME `captured` row is 2020-01-01). This candidate's own plan to read `venue_mapping.py` as the
      CME-floor SSOT is now correct on BOTH sides, not just self-consistent. Repos: instruments-service;
      unified-api-contracts is a read-only SSOT dependency. **Done when**: full (venue, data_type, year) breakdown
      recorded for NASDAQ/NYSE/CBOE/CME with the strictly-before-floor boundary check confirmed (0 off-by-one cells);
      `enumerate_expected_universe.py`'s tradfi path resolves `get_instrument_discovery_start()` live at runtime and
      materializes new pre-floor cells as `expected_unattempted`, never `todo`; the existing below-floor cells are
      reclassified writer-side with before/after counts recorded; a regression-guard test is added and passing;
      `quality-gates.sh` green in instruments-service; `tradfi_backfill_throughput_followups_2026_07_24.md`'s own P2
      checkbox on the same 182,407-cell cohort is ALSO flipped, citing this todo's commit. Source:
      `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` (also covers
      `tradfi_backfill_throughput_followups_2026_07_24.md`'s duplicate candidate on the same ground).

- [ ] [SCRIPT] P1. **Clean up the historical `corporate_action_confirmed`/`earnings_result` `attempted_failed` orphan
      rows** (807/807 + 799/799 as of the 2026-07-15 alert batch; not independently re-verified against a live manifest
      query since) from the MTDS tradfi tick manifest bucket `market-data-tick-tradfi-prd-central-element-323112`. These
      cells can never be satisfied — the real capture code for both data_types lives entirely in features-service's
      calendar module, never MTDS; the seeding-forward fix already shipped (`instruments-service@03f71c81`); only the
      already-seeded historical rows remain. Follow the exact snapshot / STOP-ON-SURPRISE / predicate-filter /
      write-back / verify-HOLD playbook this same doc already executed for the YAHOO_FINANCE phantom-venue cleanup: (1)
      re-query the live `_index/availability_index.parquet` for current row counts + `capture_status` breakdown (do not
      assume the 807/799 figures still hold); (2) confirm STOP-ON-SURPRISE: zero rows with `capture_status=="captured"`
      for either data_type; (3) snapshot `_index/availability_index.parquet` and
      `_index/expected_universe_ranges.parquet` before any write; (4) delete the matching rows from both files; (5)
      resume/force the consolidator and verify HOLD across ≥5 real merge cycles. **No real conflict on THIS candidate**
      — both of this doc's 2 recorded conflicts target SIBLING human-only items in the same doc (the
      `[DESIGN] P2. ohlcv_15m/24h wanted?` decision and the `[VERIFY] P3. trace the classification layer`
      investigation), neither of which is this candidate's actual scope (a bounded, already-scoped production-data
      cleanup for a fully-diagnosed, code-confirmed-unreachable population). Repo: market-tick-data-service. **Done
      when**: both `_index/availability_index.parquet` and `_index/expected_universe_ranges.parquet` show 0 rows for
      `data_type in {corporate_action_confirmed, earnings_result}`; pre-delete snapshots exist for rollback; ≥5 real
      consolidator merge cycles after resume confirm no resurrection. Source:
      `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`.

- [ ] [TEST] P1. **NICE-TO-HAVE — fix `deployment-service/tests/unit/test_event_logging.py`'s `get_service_name()`
      helper** (currently `Path.cwd().name`, confirmed unchanged via live grep 2026-07-25) to resolve the service
      identity from the repo's own identity (pyproject `name` field or git remote) instead of the checkout directory's
      basename, so `test_required_common_events_exist` correctly `pytest.skip`s deployment-service's
      orchestrator-not-pipeline-service exemption even when the checkout directory is not literally named
      `deployment-service` (e.g. an isolated worktree). **No conflict on THIS candidate** — the doc's one recorded
      conflict targets its SIBLING open item (the FX yahoo-backfill drain, deliberately left OUT of this batch, see
      Deferred); this is an unrelated test-infra fix. Repo: deployment-service. **Done when**: the test still skips as
      expected when run from a worktree directory with a different basename, and continues to pass in the canonical
      `deployment-service`-named checkout; `quality-gates.sh` green. Source:
      `tradfi_multisource_backfill_2026_06_22.md`.

## Already shipped independently since batch1's triage (2026-07-25) — NOT re-dispatched

4 candidates from the original 33 were found, during this re-check, to have shipped OUTSIDE AO dispatch in the window
between the triage (~02:14-02:49 UTC) and this re-check — their own source docs already carry the checked-off `[x]`
evidence, so nothing is drafted here:

- `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s "verify/drop `TRADFI_OHLCV_MACHINE` Cloud Run override"
  candidate — `[x]` DONE, re-independently-verified live 2026-07-25 (job carries no override, fleet runs the baked
  `e2-highmem-16` default).
- `tradfi_backfill_throughput_followups_2026_07_24.md`'s "verify SIGKILL-after-write reproduces" candidate — `[x]` DONE,
  RE-VERIFIED LIVE 2026-07-25 (5 consecutive trading-day runs, all `SUCCEEDED_COUNT=1`, not reproducing).
- `tradfi_backfill_throughput_followups_2026_07_24.md`'s "retire 104,623 residual phantom rows" candidate — `[x]` DONE,
  `market-tick-data-service@ccbac784` (PR #712).
- `tradfi_backfill_throughput_followups_2026_07_24.md`'s "raise `OHLCV_FLEET_CONCURRENCY_CAP` 60→150 + default
  `e2-highmem-16`" candidate — `[x]` DONE, `deployment-service@545ff76`.

## Deferred — still genuinely conflict-gated (re-checked, competing claim still open/unshipped)

8 of the 33 candidates were re-checked against `tradfi_consolidated_closeout_2026_07_18.md`'s CURRENT content and remain
genuinely unresolved (the competing claim has not shipped, been superseded, or been marked stale by any dated section):

- `data_completion_tradfi_2026_07_15.md` — ⑫ FOLLOW `reconcile_phantom_manifest_rows_all.py --dry-run` re-run (conflicts
  with the closeout's own still-open Phase C "Denominator/catalogue-completeness" todo, which cites the SAME
  `phantom_captures_tradfi_2026_06_28.md` ground via a different mechanism); the gate-b
  databento-capture→catalogue-regen→ liveness-recheck chain (conflicts with the closeout's own still-open, still-BLOCKED
  "Certify tradfi Layer-1" P0 — both terminate in a catalogue rebuild for different trigger reasons; a 2026-07-25
  catalogue Surface-A USD@LIN re-sweep DID ship (`instruments-service@52d8b3ef`) but is a DIFFERENT id-shape concern,
  not the MVP-flag-promotion/ delisted-liveness ground this candidate targets — does not clear the conflict).
- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — verify/launch ES CME futures ohlcv coverage 2021-2024;
  check/ launch the ES_OPT lock (both conflict with the closeout's own still-open Phase-C-preceding "re-verify every MVP
  cell via a fresh `data-pipeline-check-is`/`-mtds` run" todo — same ES-futures/options ground, different verification
  method).
- `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` — both candidates (root-cause the ICE/KRX/FX
  source-mislabeling; fix the FX write path + backfill the manifest `instrument_id` column) conflict with the closeout's
  own still-open Phase A2 "NEW 2026-07-24" todo, which directly restates both findings by citing this exact issue doc —
  the master plan has a foothold with a DIFFERENT intended action (evidence-reconciliation against the 99.3%
  canonicality counter-finding, not defect-fixing); still unshipped on the closeout side.
- `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` — purge/reclassify the 1,242 dead CBOE `ohlcv_15m` rows
  (conflicts with the closeout's own still-open Phase C "Denominator/catalogue-completeness" todo, which cites the SAME
  `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md` residual via a weaker "re-verify/explain"
  action vs. this candidate's "purge or reclassify" action — genuine verify-vs-fix ambiguity, unresolved).
- `tradfi_multisource_backfill_2026_06_22.md` — run the FX yahoo backfill to completion (conflicts/sequences against
  `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s still-open source-mislabeling fix — running the
  backfill while the mislabeling root cause is unfixed risks writing MORE mis-stamped rows; genuinely a sequencing
  question for the operator, not resolvable by evidence alone).

## Deferred — operator-gated, not conflict-gated (unchanged, needs a ruling not a re-triage)

`issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` — 0 AO-eligible candidates (the doc IS the undecided
`mvp_mode` design/judgment call); its 1 recorded conflict is against a closeout Phase A2 todo that also just restates
the same undecided question rather than resolving it. This is genuinely operator-gated per the ag-closeout-audit skill's
non-batchable taxonomy — no re-triage will produce a batch3 candidate here until the operator rules "wire a real caller"
vs "remove the dead path."

## Still excluded — too-large-or-risky-for-a-batch (unchanged from batch1)

`tradfi_manifest_content_recovery_completion_2026_07_24.md` (5 AO-eligible candidates found by the original triage, 5
conflicts) remains excluded per batch1's `doc_too_large_or_risky_for_batch` flag — a live, fast-moving, multi-phase
migration doc (dated DELTA sections, an actively-draining VM-backed process); it still needs its own dedicated
triage/design pass as a standalone plan, not a `batchN` slot. Not re-checked this pass (out of scope per the skill's own
taxonomy — re-triage only converts the conflict-gated category, and this doc was never conflict-gated, it was excluded
on a different, non-batchable basis).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`
(`depends_on: [tradfi_satellite_ao_dispatch_batch2_2026_07_25]` — `gate_on_depends: true`), mirroring the batch1
finalize pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc,
except the manifest-consolidator-ssot.md documentation addition (its own todo above), which is itself the codex change.
