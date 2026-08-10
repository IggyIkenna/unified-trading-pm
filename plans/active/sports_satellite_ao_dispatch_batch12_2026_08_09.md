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
  `/plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md` for the full 24-item Deferred ledger with
  taxonomy tags. Two items initially looked batchable but turned out, on a deeper read, to already be live/in-flight
  under a THIRD doc (`sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s odds_api backfill VM chain) — fixed
  as a doc-hygiene note in their source docs instead of drafted here, to avoid racing a live VM.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, features-service, deployment-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-12, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/active/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md,
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
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

- [ ] [DATA] P2. **Execute the actual `--apply-prod --confirm-prod-write` pass of
      `scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py`** (shipped
      `market-tick-data-service@25c7a3f2`) over the 88 2025-era + ~1,210 2018-2020-era `PLAYER_STATS`
      manifest-`captured`-but-no-GCS-object cells, relabeling each to `attempted_failed` with its recorded distinct
      `error_reason` (2025-era: migration artifact from the rescan→migrate→backfill pipeline; 2018-2020-era: the
      already-attributed Defect-3 writer-generation quirk). **Safe/idempotent justification**: this is a manifest-label
      correction, not a GCS object delete — the script follows the established `manifest_swap` safety pattern (dry-run
      default, snapshot-before-write, CAS-filtered index rewrite, post-write verification), and the census already
      confirmed 0 GCS objects exist at any candidate path for this population, so there is nothing to lose.
      `quality-gates.sh --no-fix` green before commit; ship via quickmerge. Source:
      `/plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (## Follow-ups, `[DATA] P3`).
      Done when: a post-write `read_capture_status_counts` (manifest-only, no GCS walk) shows 0
      `captured`-with-no-GCS-object `PLAYER_STATS` cells in the target population, each relabeled with the correct
      `error_reason`, cited by commit + verification output in the source doc.
- [ ] [DATA] P2. **Re-run the features-service `odds_targets` export** (batch handler, idempotent overwrite) over at
      least 1 recent date and confirm `odds_closing_home`/`odds_closing_draw`/`odds_closing_away` actually appear in the
      real GCS parquet — the standing data-side verification for the CLVTargetBuilder repoint that
      `features-service@b4b7ad82` has so far only proven at unit-test level. `quality-gates.sh --no-fix` green before
      commit; ship via quickmerge if any code changes are needed (expected to be a pure re-run, no code change). Source:
      `/plans/active/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` (## Follow-ups,
      `[DATA] P3`). Done when: at least one real GCS parquet for a recent date is cited by path showing non-null
      `odds_closing_{home,draw,away}` columns.
- [ ] [DIAG] P3. **Explain the 23 sentinel-free missing `odds_api` days** (2020-06-06..2026-04-15, dates with neither an
      `odds_api` row nor an `ODDS_API` sentinel row) not accounted for by the already-diagnosed-and-fixed
      sentinel-collision mechanism (`check_shard_freshness` ODDS_API-sentinel collision,
      `market-tick-data-service@362e64e3`, which explains the other 572 of 595 originally-missing days). Investigate and
      document the actual cause (a distinct writer-generation gap, a genuinely-never-attempted day, or something else)
      with file:line/evidence citations — this is an investigation todo, not a data-mutation one. Cross-check the 23
      dates against `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s in-flight full-range odds_api
      backfill first (chunk 26/451 as of 2026-08-09) — if that chain will independently settle some/all of the 23 days
      once it converges, say so and don't duplicate its work; only investigate the residual it won't explain. Source:
      `/plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` (## Follow-ups, `[DATA] P3`).
      Done when: each of the 23 days has a stated, evidenced explanation, or a citation showing the in-flight backfill
      already covers/will cover it.
- [ ] [CODE] P2. **Register a `sports-drop-stale` category in
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
  orphaned-doc items are parked in `/plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md` by taxonomy
  category (operator-gated / time-gated / dependency-gated / too-large-or-risky / not-this-tranche's-write). **Status
  left `draft`** per this skill's autonomous-mode safety rail — flipping to `active` needs explicit operator approval
  before this batch dispatches.
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

## Deferred work after 2026-08-10

| Item                                                               | State / why deferred                                                                                                                                                                   | Blocked on                                                                                                           |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Ship the `_relabel().copy()` + full-index-rescan removal (2nd fix) | In progress. Patch made (uncommitted); `quality-gates.sh` running in the background as of this note (task `bm8lyhs3i`), not yet confirmed green.                                       | Nothing but elapsed QG time — pick this up first in the next session/tick if it wasn't finished before this compact. |
| Todo 1 — `--apply-prod` for 2025 population (~88 rows)             | Not done. Dry-run + the GCS-existence-scan portion of apply both fully validated (88/4,437 confirmed missing) twice now; needs a fresh apply-prod attempt once the 2nd fix is shipped. | The 2nd memory fix above landing + QG passing.                                                                       |
| Todo 1 — `--apply-prod` for 2018-2020 population (~1,210 rows)     | Not done. Dry-run itself has never completed for this population under any code version — confirmed-missing count is still unmeasured.                                                 | The 2nd memory fix above landing + QG passing; run as a plain dry-run first to finally get the count.                |

**Recommended next action**: confirm `quality-gates.sh` (task `bm8lyhs3i`) finished green, ship via
`quickmerge.sh --agent --files 'scripts/sports/reconcile_player_stats_missing_gcs_manifest_2026_08_05.py'`, then re-run
`--population 2025 --apply-prod --confirm-prod-write`. If it STILL dies with a `resource-watchdog` kill (check
`/var/log/syslog` for a new `KILL #` line naming the PID), the cap has proven dynamic-and-low enough that even a
single-copy 17M-row load is unsafe on this host under current conditions — at that point stop patching this script's
internals and instead read the manifest with column projection (`pd.read_parquet(..., columns=[...])`) for the
mask-building step, or move the run to a VM with headroom, rather than attempting a 3rd in-process memory shave. Two
genuinely identical failures at the same fix-version would be the stop-and-escalate signal, not a 3rd blind retry.
