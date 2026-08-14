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
status: open
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

## Todos

- [ ] [CODE] P3. Confirm whether `exit_code_fleet_monitor.py`'s `DP_VM_GONE_NO_CAPTURE` alert text's `"(N → M)"`
      captured-count figure is genuinely interpolated per-VM or a fixed/templated string (grep `_finding_for` / wherever
      the alert `context` string is built). If fixed/templated, either wire in the real
      `captured_before`/`captured_after` values already computed in `sweep()`, or drop the misleading `"(0 → 0)"` suffix
      from the message entirely. Repo: deployment-service.
- [ ] [CODE] P3. Extend `cli.py::_make_captured_reader`'s bucket resolution (and its probe-fallback) to also try
      `kind="instruments-store"` and `kind="features"` when `kind="market-data"` doesn't resolve or reads 0 rows for a
      VM prefix known to write elsewhere — at minimum for the `instr-backfill-*`, `fs-backfill-*`, and
      `features-<family>-<ag>-*` prefix families confirmed in this doc's summary. Add a regression test per prefix
      family proving the reader now finds the correct bucket. Repo: deployment-service.
- [ ] [DATA] P3. One-off: pull the raw escalation payload + `_finding_for()` code path for
      `mdps-features-live-cefi-20260807-001235`'s specific `DP_VM_GONE_NO_CAPTURE` firing (escalation_queue local
      `sqlite3 -readonly`, co-located on-VM session — see the archived source doc's Access note for how) and determine
      whether the LIVE-VM `is_live_vm` exemption genuinely failed to apply, or whether this was a different,
      correctly-alerting condition (e.g. a real non-zero exit_code) misread as the same bug class in the source
      investigation. If genuinely a live-VM-exemption miss, file the root cause as its own P2 finding — do not fix
      blind. Repo: deployment-service.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
