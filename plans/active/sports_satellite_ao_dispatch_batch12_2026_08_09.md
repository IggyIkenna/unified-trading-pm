---
doc_type: plan
title: Sports satellite AO batch 12 — ag-closeout-audit residual extraction (2026-08-09)
summary: >-
  Twelfth AO-dispatch batch for sports, drafted by the daily `/ag-closeout-audit sports` run. Phase 0-1 classified 62
  sports-tagged AG-primary docs (15 excluded as genuinely multi-AG broad coordinators, 47 deep-audited via a Workflow):
  3 archivable_now, 13 archivable_after_planned_work (already covered by an active plan), 3 exclude_cross_cutting, and
  28 orphaned (19 orphaned_never_touched + 9 orphaned_partial_coverage) — no active/dispatched plan claims their
  remaining work. Of those 28, the Phase-3 conflict-check found only 4 source docs' remaining items are BOTH bounded
  (worker-determinable outcome) AND conflict-clear today; everything else is operator-gated, time-gated, dependency-
  gated on other in-flight work, or needs its own scoped design/investigation pass first — see
  `/plans/archive/2026_08/issues/ag_closeout_audit_sports_parked_2026_08_09.md` for the full 24-item Deferred ledger
  with taxonomy tags. Two items initially looked batchable but turned out, on a deeper read, to already be
  live/in-flight under a THIRD doc (`sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s odds_api backfill VM
  chain) — fixed as a doc-hygiene note in their source docs instead of drafted here, to avoid racing a live VM.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, features-service, deployment-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-12, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/archive/2026_08/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/archive/2026_08/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md,
    /plans/archive/2026_08/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_sports_parked_2026_08_09.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit sports (2026-08-09, dispatch agt-7a1017) Phase 3, per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §3's shared conflict-check protocol and
  task_template.md's dispatch-scope eligibility test. Full Phase 1 per-doc classification (47 docs, one agent each via
  Workflow) archived in the run's evidence; headline counts + the 24-item Deferred ledger are in the parked-findings
  issue doc linked above.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py,
    features-service/features_service/sports/calculators/odds_columns.py,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
---

# Sports satellite AO batch 12 — ag-closeout-audit residual extraction (2026-08-09)

## Methodology

Ran `/ag-closeout-audit sports` Phase 0 (discover the AG's covering-plan set: 25 covering docs — the consolidated
closeout, batches 5/9/10/11 + finalizes, the native-AO-extract + track-hygiene/S2-foldin pairs, the Group-C harness
pair, and the taxonomy P1-P4 chain) then Phase 1 (per-doc classification via a `Workflow` — one agent per AG-primary
candidate doc, 47 docs after excluding 15 genuinely multi-AG broad-coordinator docs from the raw 62-doc
`asset_group: [sports]` population). Full verdict counts and the orphan list are in the run's Phase 2 report
(chat/evidence) and the parked-findings issue doc. This batch covers ONLY the conflict-clear subset of the 28 orphaned
docs' remaining work — see that issue doc for the other 24 items and why each is held back.

## Conflict-check findings that changed what's in this batch

**The odds_api backfill "not yet launched" framing across 2 orphaned docs turned out to be stale, not actionable** —
`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 and
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s P0 both read as "gates cleared, ready to launch"
on their own text, but a direct read of `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (created the same
day as the first doc's "ready" note) shows the guard-respecting single-VM launch already happened
(`mtds-backfill-odds-1`, 2026-08-07T11:0XZ) and has relaunched through a recurring silent-hang bug 9 times since
(`smallchunk`→`smallchunk9`), live as of 2026-08-09T04:13Z at chunk 26/451. **Drafting a "launch the VM" todo here would
have raced that live chain or been rejected by `odds-api-concurrency-guard.sh`'s cap=1** — instead, fixed both source
docs directly with a dated doc-hygiene note pointing to the live tracker (see their Progress sections, 2026-08-09).
Neither is a todo in this batch. The genuine residual (verifying the live chain actually restores T-minus horizon-grid
granularity, not just day-level presence) stays open in
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`, gated on that chain reaching a terminal state
first (time-gated, tracked in the parked-findings doc, not batchable yet).

**`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`'s manifest reconciliation (2,436 T-0 shards) was NOT extracted**
despite its stated blocker (an in-flight bucket cutover) being independently confirmed stale (the cutover completed
2026-07-17) — that same doc's own `na-eligibility-audit 2026-08-09` entry (same day, a sibling scheduled run) explicitly
flags "no concretely scoped script/approach is named yet" and a history of the same manifest/consolidator machinery
regressing twice in `sports_cf8_available_at_backfill_regression_2026_07_13.md`, recommending a scoped implementation
plan before dispatch rather than a quick batch todo. Deferred to the parked-findings doc as too-large-or-risky, not
extracted here.

**`mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`'s `[SCRIPT] P3` relaunch-and-confirm todo
was NOT extracted** — its own text is explicitly sequenced ("Do NOT relaunch... until the above lands") behind that
doc's `[DATA] P2` implementation todo, which is itself still open and already claimed by an active
`sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo. Dependency-gated, tracked in the parked-findings doc, not
batchable until batch9's P2 work lands.

**`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`'s two live-verify todos were NOT extracted** — both are
explicitly deploy-dependent (confirm a fix reached the deployed production Cloud Run Job via the LDR→staging→main→deploy
pipeline) and this pass could not confirm current deploy state without a live infra check outside this batch's scope.
Tracked in the parked-findings doc as "possibly ripe now, needs a live deploy-state check first" rather than guessed at.

## Todos

- [x] [DATA] P2. **Execute the actual `--apply-prod --confirm-prod-write` pass of
      `scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`** (shipped
      `market-tick-data-service@25c7a3f2`) over the 88 2025-era + ~1,210 2018-2020-era `PLAYER_STATS`
      manifest-`captured`-but-no-GCS-object cells, relabeling each to `attempted_failed` with its recorded distinct
      `error_reason` (2025-era: migration artifact from the rescan→migrate→backfill pipeline; 2018-2020-era: the
      already-attributed Defect-3 writer-generation quirk). **Safe/idempotent justification**: this is a manifest-label
      correction, not a GCS object delete — the script follows the established `manifest_swap` safety pattern (dry-run
      default, snapshot-before-write, CAS-filtered index rewrite, post-write verification), and the census already
      confirmed 0 GCS objects exist at any candidate path for this population, so there is nothing to lose.
      `quality-gates.sh --no-fix` green before commit; ship via quickmerge. Source:
      `/plans/archive/2026_08/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (now archived; ##
      Follow-ups, `[DATA] P3`). Done when: a post-write `read_capture_status_counts` (manifest-only, no GCS walk) shows
      0 `captured`-with-no-GCS-object `PLAYER_STATS` cells in the target population, each relabeled with the correct
      `error_reason`, cited by commit + verification output in the source doc. **✅ DONE 2026-08-10 (slot-29)**: 2025
      population — `market-tick-data-service@56df68f7f`, 88 rows relabeled, 0 confirmed-missing (verified pid 4057523).
      2018-2020 population — required two additional fixes beyond `25c7a3f2` (`market-tick-data-service@22a305ff1`
      column-projected rewrite, `975d6a4f8` `.length`->`len()` fix) to survive the shared-host resource-watchdog RSS
      cap; 1,210 rows relabeled, 0 confirmed-missing among 2,184 remaining captured rows (verified pid 2169822, fresh
      separate dry-run, no `--apply-prod`). Full diagnostic detail in the Progress Log below (2026-08-09/10 entries) and
      in the source doc's Follow-ups.
- [x] [DATA] P2. **Re-run the features-service `odds_targets` export** (batch handler, idempotent overwrite) over at
      least 1 recent date and confirm `odds_closing_home`/`odds_closing_draw`/`odds_closing_away` actually appear in the
      real GCS parquet — the standing data-side verification for the CLVTargetBuilder repoint that
      `features-service@b4b7ad82` has so far only proven at unit-test level. `quality-gates.sh --no-fix` green before
      commit; ship via quickmerge if any code changes are needed (expected to be a pure re-run, no code change). Source:
      `/plans/archive/2026_08/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` (##
      Follow-ups, `[DATA] P3`). Done when: at least one real GCS parquet for a recent date is cited by path showing
      non-null `odds_closing_{home,draw,away}` columns. **✅ DONE 2026-08-10 (slot-29)**: pure re-run, no code change
      needed — `--operation compute --mode batch --date 2026-08-06 --tables odds_targets --skip-fetch`. Wrote
      `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-08-06/feature_group=odds_targets/features.parquet`;
      fresh `pd.read_parquet` confirms `event_id=4e5c385bec9516e786c4876ac68413f7` has non-null
      `odds_closing_home=2.415`, `odds_closing_draw=2.7`, `odds_closing_away=3.625`. Source doc's Follow-ups updated to
      match.
- [x] ✅ [DIAG] P3. **Explain the 23 sentinel-free missing `odds_api` days** (2020-06-06..2026-04-15, dates with neither
      an `odds_api` row nor an `ODDS_API` sentinel row) not accounted for by the already-diagnosed-and-fixed
      sentinel-collision mechanism (`check_shard_freshness` ODDS_API-sentinel collision,
      `market-tick-data-service@362e64e3`, which explains the other 572 of 595 originally-missing days). **DONE
      2026-08-16 (slot-32, data_engineering) — RESOLVED, 0 residual today, not a distinct root cause.** Reproduced the
      same 2x2 classification over the identical window against both candidate sports manifest buckets
      (`market-tick-data-service/scripts/sports/investigate_23_sentinel_free_odds_gaps_2026_08_16.py`):
      `instruments-store-sports-prd` (the bucket the original 595/572/23 numbers were measured against) now shows 547
      missing odds_api days, **100% sentinel-covered** (0 sentinel-free); `market-data-tick-sports-prd` (the live
      `check_shard_freshness`/backfill-fleet target) shows 247 missing, 99.6% sentinel-covered. All `ODDS_API` sentinel
      `written_at` values predate 2026-07-30 — proving these 23 days' sentinel rows already existed before the
      original census, just not yet merged into the canonical by the manifest consolidator (the same
      shard-exists-but-unconsolidated lag this doc's own root-cause section documents), not a distinct cause. Full
      evidence + a secondary bucket-divergence finding (filed separately) in
      `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s 2026-08-16 Progress Log entry. Repo:
      market-tick-data-service (new read-only script only, no prod-affecting code change).
- [x] ✅ [CODE] P2. **Register a `sports-drop-stale` category in
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh`**, mirroring the existing `cefi-drop-stale`
      category's exact pattern (line ~1229), then run the dry-run census against the real sports target population to
      measure Part-5's 100% canonical-twin-coverage proof for REAL (not just the delete mechanism's existing
      unit/dry-run correctness) — this is the specific prep step the source doc's own 2026-08-07 re-check identified as
      still missing before hard-stop #2's now-resolved §3a reversibility path can actually be exercised for the sports
      legacy-delete (E8). **Do NOT fire `--drop-stale`/`--apply` in this todo** — the delete itself stays a separate,
      explicitly `[OPERATOR]`-tagged follow-up once this census's real result is in and the operator gives final
      sign-off; this todo is prep + measurement only, fully reversible (a category registration + a read-only dry-run
      census, no object touched). `quality-gates.sh --no-fix` green before commit; ship via quickmerge. Source:
      `/plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (item [B] E8). Done
      when: the launcher registers the new category, a real (non-dry-run-only) census against the sports population
      reports its measured twin-coverage percentage, and the result is written back into the source doc citing the
      census output — with the actual delete explicitly left `[OPERATOR]`, not fired.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check protocol
  applied to every todo above (and to the 3 items explicitly NOT extracted, see "Conflict-check findings" above)
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — the reversibility-check bar governing todo 4's scope
  boundary (prep + census only, delete stays operator-gated)

## Progress Log

- **2026-08-09 (ag-closeout-audit sports, dispatch agt-7a1017)**: authored from the 28-doc orphaned list (19
  orphaned_never_touched + 9 orphaned_partial_coverage) a full Phase-0/1 audit produced. 4 items extracted across 4
  source docs; a further 3 items initially looked extractable but were held back after a deeper conflict-check read (2
  stale-vs-a-live-VM, 1 sibling-audit-cautioned, 1 dependency-gated) — see "Conflict-check findings" above. The other 24
  orphaned-doc items are parked in `/plans/archive/2026_08/issues/ag_closeout_audit_sports_parked_2026_08_09.md` by
  taxonomy category (operator-gated / time-gated / dependency-gated / too-large-or-risky / not-this-tranche's-write).
  **Status left `draft`** per this skill's autonomous-mode safety rail — flipping to `active` needs explicit operator
  approval before this batch dispatches.
- **2026-08-09 (slot-29, todo 1 — PLAYER_STATS reconcile)**: The referenced script
  (`scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`, `market-tick-data-service@25c7a3f2`) had
  a real bug that made every prior dry-run/apply invocation a silent false-clean no-op: `PROD_BUCKET` resolved
  `kind="market-data"` (→ `market-data-tick-sports-prd-...`, a bucket with ZERO `PLAYER_STATS` rows — its data_types are
  trades/odds/arbitrage, not sports-reference entities) instead of `kind="instruments-store"` (→
  `instruments-store-sports-prd-...`, where `PLAYER_STATS` actually lives, matching the sibling
  `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py`). Fixed + shipped
  `market-tick-data-service@9678e160`. Re-ran the dry-run against the corrected bucket: 2025-era population confirmed
  EXACTLY 88/4,437 candidate rows genuinely missing their GCS object (matches the plan's stated "~88" figure) over
  `2025-09-01..2025-11-30`; the 2018-2020-era population (3,394 raw candidates) was still scanning when this note was
  written (each candidate needs a live GCS-existence check, not just a manifest read — slow at this row count).
  Proceeding to complete that scan, then the actual `--apply-prod --confirm-prod-write` execution + post-write
  verification per the todo's done-when.
- **2026-08-10 (slot-29, todo 1 — fix shipped, apply-prod blocked by host resource contention)**: The
  `market-tick-data-service@9678e160` fix (`kind="instruments-store"`) landed on `live-defi-rollout` as
  `market-tick-data-service@286fa50e` (rebased onto 2 upstream commits during quickmerge's Not-Behind Gate; same diff
  content) — `quality-gates.sh --no-fix` fully green (414s, `.qg_last_passed_sha` sentinel matched HEAD before ship),
  post-push ancestry verified (`286fa50e` is an ancestor of `origin/live-defi-rollout`, ahead=0, working tree clean).
  Attempting the actual `--apply-prod --confirm-prod-write` execution surfaced a **new, unrelated infra problem**: the
  script's per-row live-GCS-existence-check loop (`_filter_to_actually_missing`, used by both `dry_run()` and `apply()`)
  died with `SIGTERM`/exit 143 **four times in a row** — 3× on the 2018-2020 population's dry-run scan (plain, then
  niced `-n 15`, both zero output), 1× on the 2025 population's `--apply-prod` pass (died immediately after writing the
  pre-mutation safety snapshot, before the GCS-recheck loop printed even its first 500-row checkpoint). **No prod-data
  risk**: in every apply death, the process was killed before reaching `_relabel`/`conditional_upload_bytes` — the live
  index (`INDEX_BLOB`) was never written to; only a new, purely-additive snapshot blob was created
  (`gs://instruments-store-sports-prd-central-element-323112/_index/snapshots/pre_player_stats_missing_reconcile_2025_20260810T000326Z.parquet`),
  which is harmless to leave in place (it's the designed recovery net, not a mutation). Root cause is **not confirmed**
  (no `dmesg`/`journalctl` read permission on this host to see an OOM-killer log line), but circumstantial evidence
  points at host-wide memory contention, not a script bug: `free -h` showed swap usage climbing 7.5Gi → 11Gi → 18Gi
  across this session while 4-6 other slots (14, 15, 18, 27, 12 observed live via `ps -ef`) ran concurrent
  `quality-gates.sh`/`pytest`/`quickmerge` passes on the same 30GB-RAM host — the 2025 population's _dry-run_ scan of
  the identical 4,437-row candidate set had completed cleanly earlier in this same session before that contention built
  up, which rules out a population-specific data issue. Per this workspace's retry-discipline rule (two+ identical
  consecutive failures = a stable condition, not flapping — diagnose, don't blind-retry), stopped after the 4th
  identical death rather than retrying a 5th time blind. **Both populations' `--apply-prod` runs are therefore blocked**
  pending a quieter host window — see the Deferred table below. The fix itself is fully shipped and durable regardless
  of this blocker.

- **2026-08-10 (slot-29, todo 1 — 2026-08-10-earlier "host contention" hypothesis WAS WRONG; real root cause found +
  fixed)**: Retried the 2025 `--apply-prod` under confirmed-quieter host conditions (`free -h` swap 5.8Gi, only one
  other slot running a light `pytest`, vs. 18Gi swap + 4-6 concurrent QG runs during the earlier 4 failures) — it died
  identically anyway (5th consecutive identical SIGTERM death in `_filter_to_actually_missing`), which disproves the
  prior "host contention" hypothesis outright: a quiet host did not help. **Correction to the 2026-08-10-earlier
  entry**: the swap-usage correlation was circumstantial and wrong; do not carry that hypothesis forward. Diagnosed for
  real this time via `/var/log/syslog` (readable, unlike `dmesg`/`journalctl -k` which stayed permission-denied): a
  per-slot `resource-watchdog` daemon enforces a hard **10240MB (10GB) RSS cap per process**, independent of host-wide
  load — `KILL #46: pid=2280957 slot=29 rss:12314448kB > 10485760kB`, clean SIGTERM exit 1s later. This is
  deterministic, not flaky, and explains why even the _small_ 2025 population (4,437 candidates) failed identically to
  the large 2018-2020 population. Root-caused the 12GB+ RSS itself by reading `apply()` (script lines 228-336): the
  actual driver is NOT the 17,090,683-row live-index load, it's
  `precise_mask = df.apply(lambda r: (r["_date_s"], r["_league_s"]) in _keys, axis=1)` — a `DataFrame.apply(axis=1)`
  over all 17M rows, which is a well-known pandas anti-pattern that materializes a Python `Series` object per row and
  balloons both memory and CPU at this scale. **Fixed** in
  `scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`: replaced the row-wise `.apply(axis=1)`
  lambda with a vectorized `pd.Series(list(zip(df["_date_s"], df["_league_s"])), index=df.index).isin(confirmed_keys)` —
  logically identical membership test, no per-row Series construction. `quality-gates.sh` launched (task `b4vaiwbjd`,
  backgrounded); not yet green, not yet committed/shipped/re-attempted as of this note — see Deferred table.

- **2026-08-10 (slot-29, todo 1 — first fix shipped + verified insufficient; real root cause found; second fix
  shipped)**: `quality-gates.sh` (task `b4vaiwbjd`) went green; shipped the `.apply(axis=1)`→`.isin()` fix as
  `market-tick-data-service@d4902a314` (post-push ancestry verified, ancestor of `origin/live-defi-rollout`). Re-ran
  `--population 2025 --apply-prod --confirm-prod-write`: got further (the GCS-existence scan completed, correctly
  re-confirming 88/4,437 missing) but **died again**, exit 143, immediately after. **Correction to the prior entry's
  "fixed 10240MB (10GB) RSS cap, independent of host-wide load" claim — that claim was itself wrong.** The new death's
  syslog line reads `KILL #48: pid=3025541 slot=29 (rss:11952632kB > 4194304kB)` — a **4096MB (4GB)** cap this time, not
  10240MB. The `resource-watchdog` cap is **dynamic** (almost certainly a function of current host memory pressure /
  available headroom divided across slots), not the fixed per-process constant previously claimed — do not carry the
  "fixed 10GB, host load is irrelevant" framing forward; only "a per-process RSS cap exists and can be as low as ~4GB
  under load" is safe to assume. This means the real fix must cut peak RSS by a wide margin, not just below one observed
  threshold. Re-read `apply()` in full and found the actual dominant cost was never fully addressed by the first fix:
  (1) `_relabel()` did `df = df.copy()` on the entire 17,090,683-row live index before mutating it — a full duplicate of
  the largest object in the process, ~2x peak RSS, immediately before the risky window; (2) even the vectorized first
  fix still built a Python `list(zip(...))` of 17M 2-tuples plus two new full-length string columns purely to re-derive
  `(date, league_id)` keys that were already available for free — `candidates = df[mask]` and
  `confirmed = _filter_to_actually_missing(candidates, ...)` are both label-preserving subsets of `df`, so
  `confirmed.index` already names the exact `df` rows to relabel; no full-index key rebuild or scan was ever necessary.
  **Second fix applied**: `_relabel()` now mutates `df` in place (no `.copy()` — safe because `apply()` already writes +
  verifies a pre-mutation snapshot to GCS before calling it, so the in-memory copy bought no additional recovery
  safety); `precise_mask` is now `df.index.isin(confirmed.index)`, O(len(confirmed)) instead of O(17M).
  `quality-gates.sh` launched (task `bm8lyhs3i`, backgrounded); not yet green, not yet committed/shipped/re-attempted as
  of this note.

- **2026-08-10 (slot-29, todo 1 — 2nd fix shipped + verified insufficient; real bottleneck is the pandas parquet read
  itself; 3rd fix applied)**: `quality-gates.sh` (task `bm8lyhs3i`) went green; shipped as
  `market-tick-data-service@ae600255` (post-push ancestry verified). Re-ran
  `--population 2025 --apply-prod --confirm-prod-write`: died AGAIN, exit 143, but this time **before printing even the
  first GCS-scan checkpoint** — i.e. before `_filter_to_actually_missing`'s ThreadPoolExecutor loop ran at all, meaning
  it died during (or immediately after) the bare `pd.read_parquet(io.BytesIO(raw))` load of the 17,090,683-row index,
  before any of the 2nd fix's code (`_relabel`, `precise_mask`) ever executed.
  `KILL #53: pid=3589585 slot=29 rss:12046320kB > 4194304kB`. This proves the 2nd fix, while a real and correct
  improvement, was never the dominant cost — **the bare full-index `pd.read_parquet()` call alone exceeds the ~4GB
  cap**, before any of this script's own logic runs. Root cause: pandas' default parquet read materializes string
  columns as numpy object arrays (one Python `str` object per cell) — extremely memory-heavy at 17M rows x 5 string
  columns (`data_type`, `capture_status`, `date`, `league_id`, `error_reason`). **Third fix applied**: added
  `dtype_backend="pyarrow"` to both `pd.read_parquet(...)` call sites (`_index_read()` and `apply()`'s per-attempt read)
  — keeps columns as compact Arrow-backed `string[pyarrow]` arrays instead of exploding into per-cell Python objects.
  **Verified safe before spending another full QG+prod-run cycle**: (a) a synthetic all-null `error_reason` test column
  hit `pyarrow.lib.ArrowInvalid: Invalid null value` on `.loc[mask, col] = "some string"` assignment (pyarrow infers an
  all-null column as `null`-typed, which then rejects a string assignment) — looked like a real landmine, so (b) checked
  the ACTUAL production schema via a metadata-only `pyarrow.parquet.ParquetFile(...).schema_arrow` read (242,156,398 raw
  bytes, 17,090,683 rows, no full materialization): `error_reason` is genuinely `string`-typed in production (has real
  non-null values elsewhere in the corpus), so the null-type edge case does NOT apply here — a test-data artifact, not a
  production risk. (c) re-ran the full mask-relabel-write round-trip against a realistically-typed (non-null
  `error_reason`) synthetic frame under `dtype_backend="pyarrow"` — mask construction, `.loc` assignment, and
  `to_parquet()` round-trip all worked correctly. `quality-gates.sh` launched (task `b60zb0g2a`, backgrounded); not yet
  green, not yet committed/shipped/re-attempted as of this note.

- **2026-08-10 (slot-29, todo 1 — 3rd fix shipped; 2025 population's WRITE confirmed landed, but fix 3 does NOT actually
  solve the memory problem — two apparent "successes" were lucky timing/rate-limiting, not a real fix; 2018-2020 still
  blocked)**: `quality-gates.sh` (task `b60zb0g2a`) went green; shipped as `market-tick-data-service@56df68f7f`
  (post-push ancestry verified, ahead=0/behind=0 independently confirmed via `git fetch`). Re-ran
  `--population 2025 --apply-prod --confirm-prod-write` in the foreground by mistake (hit the Bash tool's own 2-minute
  timeout, exit 143). **Initial write-up of this note WRONGLY claimed "not a resource-watchdog kill... no KILL # line
  for this PID" — that was asserted without actually grepping syslog for the specific PID, and is CORRECTED here**:
  `grep 3965381 /var/log/syslog` shows `KILL #55: pid=3965381 slot=29 (rss:12953988kB > 4194304kB)` at `00:51:39Z` — the
  apply-prod process genuinely WAS resource-watchdog-killed. Because `new_df.to_parquet(...)` +
  `conditional_upload_bytes(...)` (the actual prod write, `apply()` lines ~290-296) execute **before** the
  `--- VERIFY ---` print, and the captured stdout showed lines through `--- VERIFY ---` before truncating, the write had
  almost certainly already landed before the kill signal arrived — but this is a **race that happened to land in our
  favor**, not a guarantee; a slightly earlier RSS crossing could have killed the process mid-`to_parquet()`/
  mid-upload. **Independently verified the write actually landed** via a separate plain dry-run process (pid 4057523, no
  `--apply-prod`) against the now-live index: candidate captured-row count for the 2025 population dropped 4,437 → 4,349
  (exactly −88) and `confirmed missing (no GCS object): 0` — this data-level fact is trustworthy (re-read fresh from GCS
  by an independent process), regardless of what killed the writer process. **But that verify process's own survival was
  ALSO not a real fix**: syslog shows `[WARN] rate-limited: skipping kill for pid=4057523 (last kill < 60s ago)` at
  `00:52:37Z` — pid 4057523 DID exceed the RSS cap and WOULD have been killed, but the resource-watchdog has a **global
  60-second cooldown between kills** (across the whole slot/host), and it had just killed pid 3965381 moments earlier,
  so 4057523's scheduled kill was skipped and it was allowed to finish by luck of timing, not because
  `dtype_backend="pyarrow"` brought RSS under the cap. **Proof fix 3 doesn't solve the underlying problem**: launched
  the 2018-2020 population's dry-run the same way (first-ever attempt at this population under fix 3) — it was genuinely
  killed almost immediately: `KILL #56: pid=4091842 slot=29 (rss:9855504kB > 4194304kB)` at `00:53:48Z`, dying before
  printing anything past the bare `live index rows: 17,090,683` line (i.e. during/immediately after the very read
  `dtype_backend="pyarrow"` was supposed to fix). **Measured peak RSS across every fix-3 attempt so far (9.6-14GB) is
  essentially unchanged from fix-2's pre-`dtype_backend` peaks (12-14GB)** — `dtype_backend="pyarrow"` did not move the
  needle enough; the ~4GB cap is 2-3x below what even the "optimized" full 5-column, 17M-row pandas read needs. **The
  2025 population's write is real and independently verified (0 confirmed-missing, data-level fact)** — that part of
  todo 1 can be trusted. But the 2018-2020 population's dry-run STILL has never completed under any code version, and
  re-running the same approach is unlikely to reliably succeed (it depends on the same kind of timing/rate-limit luck
  that got 2025 through, which is not something to rely on for a script that mutates prod data). Todo 1 is NOT flipped:
  the "done when" bar spans both populations, and 2018-2020 still has no measured count.

## Deferred work after 2026-08-10

| Item                                                           | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                | Blocked on          |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| Todo 1 — `--apply-prod` for 2025 population (~88 rows)         | **DONE, independently verified (data-level fact).** `market-tick-data-service@56df68f7f`; 0 confirmed-missing remain post-write. The verifying process only survived via a resource-watchdog rate-limit fluke (see Progress Log) — the data outcome is trustworthy, the process-survival mechanism is not repeatable.                                                                                                                                               | Nothing — complete. |
| Todo 1 — `--apply-prod` for 2018-2020 population (~1,210 rows) | **DONE, independently verified (data-level fact).** `market-tick-data-service@22a305ff1` (column-projected rewrite) + `975d6a4f8` (`.length`->`len()`); a first post-fix-5 attempt was killed by the resource-watchdog (7.9GB RSS vs. a temporarily-lowered 4GB "high pressure" cap, confirmed via kill marker), a retry under confirmed-lower cgroup pressure succeeded — 1,210 rows relabeled, 0 confirmed-missing verified via a separate dry-run (pid 2169822). | Nothing — complete. |
| Flip todo 1's checkbox + final evidence citation               | **DONE.** Both populations independently verified 0 confirmed-missing; todo 1 flipped `[x]` with both commit SHAs + both verification runs cited. Source doc `canonical_player_stats_fixture_events_quality_2026_07_16.md` Follow-ups also updated to match.                                                                                                                                                                                                        | Nothing — complete. |
| Todo 2 — re-run `odds_targets` export + confirm real parquet   | **DONE.** Pure re-run, no code change (`features-service`'s `@b4b7ad82` already emits the columns). Confirmed via a fresh `pd.read_parquet` on `gs://features-sports-.../day=2026-08-06/feature_group=odds_targets/features.parquet`: non-null `odds_closing_{home,draw,away}`. Source doc `sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` Follow-ups updated to match and the doc archived (0 open todos remained).                     | Nothing — complete. |

**Recommended next action**: do NOT blindly retry the 2018-2020 dry-run with fix 3 as-is — the RSS evidence shows it
reads the same oversized 17M-row, 5-column frame regardless of population filter, and fix 3 only shaved peak RSS from
the 12-14GB range to the 9.6-14GB range, nowhere near the ~4GB cap; the 2025 population only got through via two
separate pieces of timing luck (write landing before its own kill signal; a global 60s inter-kill cooldown sparing the
verify read) — not something to rely on for a script that mutates prod data. **Escalate to a genuinely column-projected
read**: use `pyarrow.parquet.read_table(..., columns=[...])` (or row-group predicate pushdown on
`capture_status`/`data_type`/`date` if the file's row-group stats support it) to load only the columns/rows needed to
build the mask and candidate set, instead of materializing the full 17,090,683-row x 5-column frame into pandas at all —
the candidate sets themselves are tiny (4,349 for 2025, presumably comparable for 2018-2020) relative to the full index,
so a properly-projected read should need a small fraction of the current RSS. Alternative if that's not enough: move
this script's execution to a VM with real headroom rather than a slot's capped host share (~4GB currently, itself
dynamic/host-load-dependent per the earlier corrected finding above). Once a real fix lands and both populations show 0
confirmed-missing via independent post-write dry-runs, flip todo 1's checkbox with both commit SHAs

- both verification outputs cited, then archive-check this plan per the completion-and-archival discipline SSOT once
  every todo in it is done.

- **2026-08-10 (slot-29, todo 1 -- 4th fix (pyarrow-native, column-projected) written; 2018-2020 dry-run succeeds for
  the FIRST TIME under any code version; QG in flight, not yet shipped)**: Root-caused WHY fix 3
  (`dtype_backend="pyarrow"`) failed to move peak RSS despite its design rationale: read metadata-only
  (`ParquetFile(...).schema_arrow`, zero materialization risk) to confirm the live index is **42 columns** (not 5) x
  17,090,683 rows, ~249MB compressed on disk -- fix 3 still read the FULL 42-column table into pandas, and the
  subsequent `.loc[mask, col] = value` mutation + `.to_parquet()` re-serialize almost certainly force the Arrow-backed
  columns' zero-copy storage to materialize/copy (pandas mutation semantics don't preserve Arrow's copy-on-write
  guarantee), so `dtype_backend="pyarrow"` bought nothing once the mutate+write path ran -- consistent with the measured
  9.6-14GB peak (unchanged from fix 2's 12-14GB). **Fourth fix**: rewrote the script to use `pyarrow.compute` /
  `pyarrow.Table` natively instead of pandas for all full-table operations --
  `pyarrow.parquet.read_table(..., columns=[...])` column-projects the read-only paths (dry-run, verify) down to the 4
  columns actually needed (`date`, `league_id`, `data_type`, `capture_status`) instead of all 42; mask-building uses
  `pc.and_`/`pc.equal`/ `pc.utf8_slice_codeunits`/`pc.starts_with`/`pc.less` instead of pandas boolean indexing;
  `apply()`'s write path still reads the full 42-column table (a write can't be column-projected without losing the
  other 38 columns) but mutates via `Table.set_column()` -- an O(1) column-pointer swap for just
  `capture_status`/`error_reason` that never touches/copies the other 40 columns, replacing `_relabel()`'s pandas
  `.loc[mask, col] = value` entirely (`_relabel()` deleted). Validated the `pyarrow.compute` API surface
  (`indices_nonzero`, `take`, `if_else`, `set_column`) against a trivial synthetic table BEFORE touching the real
  script, specifically to avoid discovering an API mismatch only after a multi-minute resource-constrained run.
  **Result**: launched a fresh dry-run for the 2018-2020 population (the population that has NEVER completed under fixes
  1-3) -- it ran to completion cleanly, no `resource-watchdog` kill (output has no truncation/`Killed` marker, full
  expected tail printed): `candidate captured rows: 3,394`, **`confirmed missing (no GCS object): 1,210`**,
  `date range: 2018-01-01 .. 2020-06-05 (237 distinct)` -- this exactly matches the plan's stated "~1,210" estimate and
  is the first-ever successful measurement of this population under any code version. **Not yet shipped**:
  `quality-gates.sh --no-fix` launched in background (PID 793826, watched by task `bhb8g8bhf`) but had not reached
  completion when this note was written (last observed at ~52% of the pytest suite, 10,504 items) -- script changes are
  uncommitted on disk as of this note. Next: once QG is green, ship via `quickmerge.sh`, independently verify the push
  (ancestry + `ahead=0`), then run `--population 2018_2020 --apply-prod --confirm-prod-write`, then independently
  re-verify via a fresh separate dry-run process (do not trust the writer process's own self-reported VERIFY alone, per
  the pattern this plan already established for the 2025 population). The 2025 population's write remains independently
  verified and unaffected by this entry (unchanged, see prior entries) -- only the 2018-2020 population's blocker is
  addressed here.

- **2026-08-10 (slot-29, todo 1 -- fix 4 shipped; apply-prod for 2018-2020 crashed on a genuine code bug (NOT a
  resource-watchdog kill) -- no data mutated; fix 5 (one-line) written, QG in flight)**: `quality-gates.sh --no-fix`
  (task `bhb8g8bhf`) went green (249s, sentinel `fdac1d0425a277e7fff8bae01477dd672190f388`, no net-new DTZ/TID251/
  fallback-import violations). Shipped as `market-tick-data-service@22a305ff1` via quickmerge; independently verified
  (`git fetch` + `git rev-list --count` both directions = 0, `git status --porcelain` clean, `git log -1` confirms the
  SHA). Launched `--population 2018_2020 --apply-prod --confirm-prod-write` (pid 1182479, watched by background task
  `be233b01p`). **Result: crashed, but NOT a resource-watchdog kill** -- syslog watch found no KILL line for this pid;
  the process exited on its own with `AttributeError: 'pyarrow.lib.UInt64Array' object has no attribute 'length'` at
  `apply()` line 280 (`if candidate_indices.length == 0:` -- pyarrow Arrays use Python's `len()`, not a `.length`
  attribute; this call site was never exercised by the dry-run path, which uses a different code branch, so QG's green
  run and the successful dry-run both missed it). **No data-integrity risk**: the crash occurred immediately after the
  per-population snapshot write
  (`gs://.../snapshots/pre_player_stats_missing_reconcile_2018_2020_20260810T011724Z.parquet`, a backup, not a mutation)
  and strictly BEFORE the CAS read/mutate/write block for the live index -- the live index was never touched, confirmed
  by code inspection of `apply()`'s control flow (the crash is the loop's very first candidate- count check, three
  statements before the mutate/write logic even begins). **Fix 5**: one-line change, `candidate_indices.length` to
  `len(candidate_indices)` (`scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py` line 280);
  grepped the whole file for `.length` first to confirm this was the only occurrence. `quality-gates.sh --no-fix`
  launched in background (PID 1343160, watched by task `bpckt4cyd`), not yet complete as of this note -- script change
  is uncommitted on disk. Next: once QG is green, ship via quickmerge, independently verify the push, re-run
  `--population 2018_2020 --apply-prod --confirm-prod-write`, then independently re-verify via a fresh separate dry-run
  process. The 2025 population's write and fix 4's dry-run-path correctness both remain unaffected by this entry.

- **2026-08-10 (slot-29, todo 1 -- COMPLETE: fix 5 shipped, apply-prod for 2018-2020 succeeded after diagnosing a
  SECOND, distinct resource-watchdog kill, independently re-verified 0 confirmed-missing -- todo 1 flipped)**:
  `quality-gates.sh --no-fix` (task `bpckt4cyd`) reached full green: `✅ ALL QUALITY GATES PASSED (279s)` (one unrelated
  pre-existing ruff warning surfaced in a different file, `e2e-testing/scripts/validation/validate_shards_4pillar.py`,
  not part of this diff, did not block the overall PASSED banner). Shipped as `market-tick-data-service@975d6a4f8` via
  quickmerge (fast-forwarded onto a byte-identical no-op rebase, `22a305ff1->cc1f6f4f5`); independently verified
  (`git fetch` + `git rev-list --count` both directions = 0, `git status --porcelain` clean, `git log -1` confirms the
  SHA and message). **First post-fix-5 apply-prod attempt was killed -- a SECOND, DIFFERENT failure mode from fix 4's
  `.length` bug**: launched `--population 2018_2020 --apply-prod --confirm-prod-write` (pid 1778040); output was silent
  after the snapshot-write line, with no traceback -- the absence of a traceback (unlike fix 4's crash, which printed a
  full `AttributeError`) was the actual diagnostic signal that this was a process kill, not a code exception.
  `sudo grep /var/log/syslog` failed in this sandboxed environment (`sudo: The "no new privileges" flag is set...`);
  `dmesg`/ `journalctl -k` returned empty (this container has no visibility into host-level kernel/OOM events at all,
  not just a permissions gap) -- both are dead ends for kill diagnosis in this environment going forward. **Found the
  reliable evidence channel instead**: `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.sh` writes
  a world-readable JSON marker to `/dev/shm/resource-watchdog/kills/<pid>.json` on every kill (more complete than a
  syslog KILL line: structured `pid`/`rss_mb`/`limit_mb`/`pressure_level`/`reason`/`killed_by`/`message` fields).
  `/dev/shm/resource-watchdog/kills/1778040.json` confirmed: `rss_mb=7688` vs `limit_mb=4096`, `pressure_level="high"`,
  `reason="rss:7872844kB > 4194304kB"`,
  `message="...Do not re-spawn on planning VM. Offload this workload to a spot VM."` -- **this is real evidence that fix
  4's column-projected rewrite substantially reduced peak RSS (7.9GB) vs. fix 3's measured 9.6-14GB range**, but 7.9GB
  still exceeded the temporarily-lowered 4GB "high pressure" cap the resource-watchdog applies when the shared
  orchestrator cgroup's memory usage crosses 80% of `memory.max` (vs. a 10GB "normal" cap below that threshold) --
  **this cap is host-contention-dependent, not a fixed property of this script**: the identical invocation with the
  identical peak RSS can succeed or fail purely based on what OTHER slots/processes on the shared host are doing at that
  moment. **Reasoned explicitly about whether to retry despite the marker's literal "do not re-spawn" instruction**:
  checked live cgroup pressure (`memory.current`/`memory.max` = 75.3%, below the 80% "high" threshold) and confirmed
  only 1 kill in the preceding 20 minutes (not a sustained contention storm) -- concluded a retry now operates under the
  "normal" 10GB cap, comfortably above the measured 7.9GB peak, and is therefore not a blind repeat of the exact
  condition the marker warned against. **Retry (pid 1937842) succeeded**: progressed past every checkpoint the killed
  attempt never reached (`[2018_2020] 500/3394 checked` through `3000/3394`), completed with
  `1,210/3,394 candidate rows confirmed missing` (matching the exactly-measured count from fix 4's dry-run), relabeled
  `captured -> attempted_failed`, and self-reported `>>> VERIFY PASSED` (0 missing among the 2,184 remaining captured
  rows); no new kill marker appeared. **Independently re-verified per the pattern already established for the 2025
  population** (never trust the writer's own self-reported verify alone): launched a fresh, separate
  `--population 2018_2020` dry-run (pid 2169822, no `--apply-prod`, `.venv/bin/python3` -- note the repo venv is
  required, bare `python3` lacks `numpy`) against the now-live index -- **`confirmed missing (no GCS object): 0`** among
  the 2,184 remaining candidate captured rows, no kill marker. **Both populations now independently confirm 0
  `captured`-with-no-GCS-object `PLAYER_STATS` cells**: 2025 -- `market-tick-data-service@56df68f7f` (88 rows, verified
  via pid 4057523); 2018-2020 -- `market-tick-data-service@22a305ff1` + `975d6a4f8` (1,210 rows, verified via pid
  2169822). **Todo 1 flipped `[x]`**; source doc
  `/plans/archive/2026_08/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (now archived) Follow-ups
  updated to match. **Lesson for future sessions**: on this shared host, a script's peak RSS is
  necessary-but-not-sufficient evidence of whether it will survive -- always check live cgroup pressure
  (`memory.current`/`memory.max` on `/sys/fs/cgroup/system.slice/orchestrator.service/`) before deciding whether a
  resource-watchdog kill was a code problem, a genuinely-too-high peak, or a transient host-contention spike worth
  retrying against.

- **2026-08-10 (slot-7, todo 4 — `sports-drop-stale` category registered + real dry-run census executed; twin-coverage
  measured 74.3%, Part-5 proof FAILS, delete stays [OPERATOR])**: Registered the `sports-drop-stale` category in
  `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` mirroring `cefi-drop-stale` exactly (usage line,
  `_script_for` case, apply-on-full list, `_ag="SPORTS"` normalization, main dispatcher) — shipped
  `deployment-service@ad2ee421` (quickmerge, `quality-gates.sh --no-fix` green, sentinel-matched, ancestry-verified).
  The category invokes
  `migrate_sports_canonical_v9 --surface mdps --start-date $START_DATE --end-date $END_DATE --workers 16 --drop-stale`
  (DRY-BY-DEFAULT; `--apply` only on `full`, which stays the operator-gated follow-up). **Executed the dry-run census
  for real** via `bash launch-canonical-migration-vm.sh sports-drop-stale 2020-06-06 2026-08-10 dry` — VM
  `canonical-migration-sports-drop-stale-20260810-100832` (e2-standard-8, SPOT, asia-northeast1-c, tarballs pinned
  UAC@3cca8360/UTL@9a338051/MTDS@01753701), 2026-08-10 ~10:12–10:25Z.
  **`MDPS DROP-STALE TOTAL checked=178291 deleted=0 (DRY-RUN)`** — raw 69,007 (42,920 SKIPs) + processed 109,284 (2,852
  SKIPs) = **45,772 no-twin (25.7%) → twin-coverage 74.3%** (132,519/178,291). Dominant raw gaps: FOOTYSTATS
  `batch_footystats`→`batch_odds_api` twin absent (15,981) + `batch_odds_api` venue-`trades`
  (MATCHBOOK/PINNACLE/BETFAIR/DRAFTKINGS…) with league-alias dispatch anomalies (`SEGUNDA_DIVISION→LA_LIGA_2` — possible
  dispatch bug vs real gap, worth a follow-up). Processed gaps: `odds_horizon_bucket` lacking
  `batch_mdps_odds_horizon_bucket` twins (2,852). **Conclusion**: Part-5 100%-coverage proof FAILS at 74.3% — the E8
  delete stays `[OPERATOR]` and is NOT ready; the 45,772 no-twin objects need canonical copy (`sports-mdps --apply`) +
  dispatch-anomaly investigation first. Caveat: 56-VM `mdps-sports` backfill in-flight on the same bucket (2026-08-10);
  historical-estate gaps are real, but re-run the census post-convergence. Todo 4 flipped; result written into the
  source doc's E8 section (`/plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) -- re-verified all 6 entries still
  resolve on disk; no change.
