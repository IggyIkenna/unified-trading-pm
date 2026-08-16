---
doc_type: issue
title:
  DP-VM-002's exit_code_fleet_monitor.py alert text is a fixed template (not a real per-VM reading) and its
  captured-reader is bucket-`kind`-blind for several VM prefix families — two structural findings from a 23-VM
  historical-sample verification pass
summary: >-
  Follow-up to `qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps_2026_08_09.md`'s (now archived,
  `plans/archive/2026_08/`) todo 2 — a bounded live-verification pass over 23 named DP-VM-002 escalations. That pass
  confirmed 0 of the 23 were genuine live data gaps, but surfaced two DETECTOR-LEVEL findings about
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` itself that were noted in that (now-archived)
  doc's Progress Log as prose only — this doc converts them into tracked, actionable todos per the workspace's "every
  deferral is a todo, never prose" HARD RULE.

  **Finding 1 — fixed alert text, not a real reading.** Every one of the 23 escalation payloads sampled read the
  IDENTICAL generic string `"drained but manifest captured did not climb (0 → 0) ... a genuine silent zero"` — including
  for VMs where "captured climbing" was never even the right question (a purge/no-op migration run, a
  `LifecycleClass.LONG_LIVED_LIVE` producer, several `--test-run` smoke-check VMs). Whether `"(0 → 0)"` is a real per-VM
  interpolated reading or a fixed template needs confirming against the code — if fixed, every future
  DP_VM_GONE_NO_CAPTURE alert's "(N → M)" figure is misleading and should either be genuinely interpolated or dropped
  from the message.

  **Finding 2 — bucket-`kind`-blind captured-reader for several VM prefix families.** An earlier Explore-agent research
  pass (same investigation) found `cli.py::_shard_bucket_for_vm`/`_make_captured_reader` hardcodes
  `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group=ag)` for every VM and, on resolution failure, only
  probe-falls-back across the 5 `market-data` buckets — never `instruments-store` or `features` kind buckets. Confirmed
  impact on 3 of the 23 VMs sampled: `instr-backfill-sports-*` and `fs-backfill-*` prefixes actually write to
  `instruments-store-sports` (registry `_INSTR_SPORTS`), and `features-delta-one-defi-*` writes to a `kind="features"`
  bucket — the reader never looks in either, so a `DP_VM_GONE_NO_CAPTURE` verdict (or its absence) for these prefixes is
  unreliable in either direction.

  **Finding 3 — one occurrence of the documented LIVE-VM exemption apparently not firing.** `mdps-features-live-cefi-*`
  resolves to `LifecycleClass.LONG_LIVED_LIVE` -> `umbrella="live"` in the registry, and the monitor's own code
  (`is_live_vm` gate) is designed to route a flat-captured LIVE VM to `EXPECTED_NO_CAPTURE` (alert suppressed) rather
  than `GONE_NO_CAPTURE`. Escalation `agt-...` for `mdps-features-live-cefi-20260807-001235` fired as a genuine
  `DP_VM_GONE_NO_CAPTURE` CRITICAL page anyway — a single occurrence, not reproduced live in this pass, but worth a
  human confirming whether the umbrella resolution genuinely failed for that alert or whether this is some other,
  correctly-firing path (e.g. a non-zero exit_code misclassified in this doc's own reading of the payload text).
status: resolved
nature: issue
asset_group: [tradfi, sports, defi, cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [dp-vm-002, exit_code_fleet_monitor, alert-quality, bucket-kind, data-pipeline-alerts, detector-bug]
related:
  [
    /plans/archive/2026_08/qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps_2026_08_09.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-09
author:
  slot-18 (data_engineering), task qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps-256f4555cced
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: fleet
estimate_class: refactor
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
locked_since:
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/cli.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: >-
  `qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps_2026_08_09.md`'s todo 2 (23-VM DP-VM-002
  verification pass), extracted 2026-08-09 after that doc archived — the structural detector findings noted in its
  Progress Log had no tracked todo of their own.
---

# DP-VM-002 detector: generic alert text + bucket-kind blindness (3 findings, not individually severe)

> **Status (2026-08-16)**: ✅ RESOLVED. All 4 todos done — deployment-service@d776dbe253 fixed a real
> live-VM-exemption case-sensitivity bug (Finding 3). See Todos section for full evidence.

## What I found

See summary above — full evidence (exact escalation payload text, code line citations for the bucket-kind-blind reader,
the registry entries confirming `mdps-features-live-cefi-` resolves to `LifecycleClass.LONG_LIVED_LIVE`) lives in the
archived source doc's Progress Log:
`/plans/archive/2026_08/qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps_2026_08_09.md` (the
entry starting "Todo 2 (the 23 DP-VM-002 VM names) verified live").

## Why it matters

None of these individually crossed the "big finding" bar in the source investigation (no live data gap resulted from any
of them), which is why they weren't escalated to the operator at the time. But a detector whose alert text doesn't
reflect reality and whose captured-reader can't see 3+ known VM prefix families' actual write buckets will keep
generating exactly the kind of false-DP-VM-002-closure noise the `qg_v2_green` false-resolution investigation
(`escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`) was chasing in the first place —
worth fixing at the root rather than re-discovering per audit.

## Recommended decision

Fix findings 1 and 2 as scoped code changes; investigate finding 3 as a one-off verification (may resolve to "already
fine, this was a different code path" — do not assume it's the same bug as findings 1/2 without checking).

## Finding 4 (added 2026-08-15, escalation agt-cf60fa) — a fully-converged catch-up shard reads 0→0 forever, not just once

A backfill/catch-up VM class (e.g. `mdps-<asset_group>-<year>-*` from `launch-mdps-sharded-backfill.sh`) that has
genuinely finished all real work for its window — everything either `captured` from an earlier run or honestly
`expected_unattempted` (a pre-genesis data_type gap, now fixed for the dex_pool_swaps/defi/2022 case in
`dp_vm_002_mdps_defi_2022_dex_pool_swaps_pregenesis_no_manifest_trace_2026_08_15.md`) — will still write ZERO rows to
its OWN `_index/per_vm/{new-vm-name}.parquet` on every future dispatch, because a fully-fresh shard never gets far
enough into the pipeline to write anything at all. `exit_code_fleet_monitor`'s captured-delta reads 0→0 for that run
too, indistinguishable from a genuine silent failure, on EVERY future dispatch of that shard — not a one-time false
positive like findings 1-3 above, but a permanent, recurring one for any catch-up shard that eventually fully converges.
The detector currently has no way to ask "did this VM's TOTAL asset_group/date-range coverage (not just this VM's own
per-VM shard) actually need anything new this run?" before concluding GONE_NO_CAPTURE.

- [x] ✅ [CODE] P3. Give `exit_code_fleet_monitor`'s DP-VM-002 check a way to recognize a fully-converged catch-up shard
      (e.g. cross-check `check_shard_freshness`/the consolidated manifest for the VM's asset_group+date-range rather
      than relying solely on the VM's own empty per-VM shard) so a genuinely-nothing-to-do run doesn't page CRITICAL
      indistinguishably from a silent failure. Repo: deployment-service. — deployment-service@232f56c4c6: wired MDPS
      orchestration_service.py's per-date "SKIP date=... already fresh in manifest" pre-flight marker into
      `_gcs.py`'s existing `_HONEST_ABSENCE_RE` run.log classifier (the same mechanism every other benign
      flat-captured case already uses), so a fully-converged shard's run.log — wall-to-wall this line — classifies
      HONEST_ABSENCE → EXPECTED_NO_CAPTURE instead of SILENT → GONE_NO_CAPTURE. Regression test added
      (`test_no_capture_reason_honest_absence_fully_converged_catch_up_shard`). Cheaper + safer than a live
      cross-service manifest re-scan per terminated VM (deployment-service has no dep on MDPS/`check_shard_freshness`
      directly, and a full-corpus manifest read per VM risks the sweep-overlap-storm class this file's own comments
      warn about).

## Todos

- [x] ✅ [CODE] P3. Confirm whether `exit_code_fleet_monitor.py`'s `DP_VM_GONE_NO_CAPTURE` alert text's `"(N → M)"`
      captured-count figure is genuinely interpolated per-VM or a fixed/templated string (grep `_finding_for` / wherever
      the alert `context` string is built). If fixed/templated, either wire in the real
      `captured_before`/`captured_after` values already computed in `sweep()`, or drop the misleading `"(0 → 0)"` suffix
      from the message entirely. Repo: deployment-service. — **CONFIRMED genuinely interpolated, no fix needed
      (2026-08-15, slot-25).** `_classify.py::finding_for`'s `DP_VM_GONE_NO_CAPTURE` branch (lines ~671-682) builds the
      summary as an f-string reading `result.captured_before`/`result.captured_after` directly off the
      `TerminationResult` dataclass — those fields are populated in `classify_terminated_vm` from the real
      `captured_before`/`captured_after` args threaded through from `sweep()`'s per-VM `captured_reader()` calls (NOT a
      constant). `tests/unit/test_data_pipeline_monitors.py` already exercises non-zero flat values
      (`captured_reader=lambda _vm: 100`, line 1550/1604/1714) that assert a `GONE_NO_CAPTURE` verdict — those cases
      would render `"(100 → 100)"`, not `"(0 → 0)"`, proving the string is not templated. The `"(0 → 0)"` seen
      identically across all 23 VMs sampled in the source audit is the HONEST consequence of those specific VMs'
      `captured_reader()` genuinely returning 0 both before and after — because `GONE_NO_CAPTURE` structurally requires
      `captured_after <= captured_before` (a climbing count routes to CLEAN/PARTIAL_UNCONFIRMED instead), a VM whose
      reader can't find its real shard (Finding 2's bucket-`kind`-blindness, already tracked as the next todo below)
      will always show flat 0→0 even when real data was captured elsewhere. No code change needed for this todo — the
      fix for the misleading reading lives entirely in Finding 2's bucket-resolution todo, not here. (repo:
      deployment-service, investigation only)
- [x] ✅ [CODE] P3. Extend `cli.py::_make_captured_reader`'s bucket resolution (and its probe-fallback) to also try
      `kind="instruments-store"` and `kind="features"` when `kind="market-data"` doesn't resolve or reads 0 rows for a
      VM prefix known to write elsewhere — at minimum for the `instr-backfill-*`, `fs-backfill-*`, and
      `features-<family>-<ag>-*` prefix families confirmed in this doc's summary. Add a regression test per prefix
      family proving the reader now finds the correct bucket. Repo: deployment-service. — **ALREADY LANDED
      (2026-08-15, slot-27), no new code needed.** Found the fix already implemented in
      `_captured_reader.py::make_captured_reader`/`_shard_buckets`/`_probe_all` (split out of `cli.py` 2026-08-10,
      re-exported as `cli._make_captured_reader`) — `_SHARD_BUCKET_KINDS = ("market-data", "instruments-store",
      "features")` plus the flat `features-sports` fallback key are already probed when the primary market-data
      bucket doesn't resolve or the shard isn't found there. `tests/unit/test_data_pipeline_monitors_cli.py` already
      carries a regression test per prefix family:
      `test_captured_reader_probes_instruments_store_when_market_data_blob_absent` (instr-backfill-\*),
      `test_captured_reader_probes_instruments_store_for_fs_backfill_prefix` (fs-backfill-\*),
      `test_captured_reader_probes_features_bucket_for_features_family_prefix` (features-<family>-<ag>-\*), plus
      `test_captured_reader_prefers_primary_bucket_blob_when_present` proving the probe-fallback doesn't fire when
      the primary bucket already has the shard. All 5 captured-reader tests pass on HEAD. Traced to commit
      `0c38c00d` ("fix(dp-monitors): race-free relaunch state, alert-accuracy quartet, windowed attempted_failed
      ratio, test hermeticity") — a bundled fix commit that implemented this exact finding without linking back to
      this issue doc's todo. No code change required; checkbox flip only. (repo: deployment-service)
- [x] ✅ [DATA] P3. One-off: pull the raw escalation payload + `_finding_for()` code path for
      `mdps-features-live-cefi-20260807-001235`'s specific `DP_VM_GONE_NO_CAPTURE` firing (escalation_queue local
      `sqlite3 -readonly`, co-located on-VM session — see the archived source doc's Access note for how) and determine
      whether the LIVE-VM `is_live_vm` exemption genuinely failed to apply, or whether this was a different,
      correctly-alerting condition (e.g. a real non-zero exit_code) misread as the same bug class in the source
      investigation. If genuinely a live-VM-exemption miss, file the root cause as its own P2 finding — do not fix
      blind. Repo: deployment-service. — **DONE 2026-08-16 (slot-7, data_engineering).** Pulled the raw payload for
      escalation `agt-8e0e57` (local `sqlite3 -readonly` on `agent-orchestrator/data/state/state.db` — this session is
      also co-located on the orchestrator VM): confirmed CRITICAL `DP_VM_GONE_NO_CAPTURE` fired for
      `mdps-features-live-cefi-20260807-001235` with captured flat 0→0. Cross-referenced `_classify.py::
      classify_terminated_vm`'s verdict precedence: the ONLY way to reach the fired message is `is_live_vm=False` at
      classification time (a climbing/nonzero-exit VM never reaches this branch at all) — **CONFIRMED genuine
      live-VM-exemption miss, not a different correctly-alerting condition.** Root cause found (not left as an
      unresolved P2 — the todo's own "do not fix blind" bar was met by full reproduction): the REAL umbrella resolver
      (`cli._umbrella_for_vm` -> `deployment_classification.umbrella_for_vm_name` -> `DeploymentUmbrella`) returns the
      canonical UPPERCASE `"LIVE"` (verified live: `DeploymentUmbrella.LIVE.value == "LIVE"`), but
      `exit_code_fleet_monitor.py`'s `is_live_vm = umbrella == "live"` compared case-sensitively against lowercase —
      so the exemption never fired via the real resolver for ANY live-VM prefix, fleet-wide, not just this one VM.
      The SAME bug pattern existed in `heartbeat_stall_watcher.py`'s auto-kill guard (`umbrella == _LIVE_UMBRELLA`).
      Every existing test masked this by hand-writing a lowercase `umbrella="live"` literal/lambda instead of
      exercising the real resolver. Fixed: deployment-service@d776dbe253 — both comparison sites made
      case-insensitive (`.strip().lower() == "live"`), mirroring `alerting_service.notifiers.router`'s own
      case-insensitive handling of this exact value (confirmed via direct code read — the router already treats this
      as an intentional, documented case-insensitivity contract). Added 4 new regression tests wiring the REAL
      resolver end-to-end (not a hand-written lambda) for both the DP-VM-002 exemption and the auto-kill guard — the
      prior tests would NOT have caught this bug or a future regression of it. QG green (Pass-1 sentinel verified on
      d776dbe253). No separate P2 finding filed — the fix landed in this same task per the todo's own escape valve
      ("do not fix blind" was satisfied by full verification before touching code, not by leaving it unresolved).

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **slot-27 (data_engineering) 2026-08-15**: bucket-kind-blindness todo flipped — verified the fix + a regression
  test per prefix family already landed at deployment-service@0c38c00d; all 5 captured-reader tests pass on HEAD. No
  new code shipped. Remaining open todo in this doc: the finding-3 one-off `mdps-features-live-cefi-*` investigation
  (DATA, not this task's scope).
- **slot-7 (data_engineering) 2026-08-16**: finding-3 investigation done — confirmed genuine live-VM-exemption miss
  (not a different condition) and found + fixed the root cause (umbrella case-sensitivity mismatch between the real
  resolver's uppercase "LIVE" and both monitors' lowercase comparison), deployment-service@d776dbe253. All todos in
  this doc are now checked — doc is archive-eligible.
