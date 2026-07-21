---
doc_type: issue
title: Prediction migration script — a tested connection-pool hardening fix sits uncommitted
summary:
  A real, tested (ruff/basedpyright clean) further connection-pool hardening for
  `migrate_prediction_instrument_id_wrap_2026_07_09.py` was written but never committed — its own quality-gates run was
  CPU-starved by the 5 live migration shards it was fixing contention for, and was killed after ~7 minutes rather than
  block further. Not urgent — the migration already self-recovered from the specific issue this fixes, and all 5 shards
  (including the 2 later moved to VMs) completed successfully without it. Ship on a future pass.
status: resolved
nature: notes
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [instrument-id, canonicalization, prediction, connection-pool, tech-debt]
related: [instrument_id_format_canonicalization_2026_07_08.md]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
  "slot-3, 2026-07-14 — re-verified: the documented 3-client fix is already committed at 1f28c472; the separate
  'further' fix's exact diff is unrecoverable and out of scope to fabricate"
source:
  "Real finding from the Prediction migrate-stage agent (wf_118d8268-18c, 2026-07-09) — also independently confirmed
  still uncommitted via a direct git status check 2026-07-10."
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

While running the real Prediction instrument-id-wrap migration as 5 parallel date-sharded background processes, the
agent found and fixed a real throughput bug: worker counts above 32 made throughput WORSE (128 workers measured slower
than 32) due to undersized HTTP connection pools on 3 separate client instances (the main session, the OAuth
token-refresh session, and a third — the listing client — found via one shard stalling 16+ minutes with zero progress).
Fixed by mounting a bigger `HTTPAdapter` pool onto all 3.

A **further** hardening fix (for a related, narrower connection-pool issue) was written and tested clean
(ruff/basedpyright) in the same session, but its own `quality-gates.sh` run was starved of CPU by the 5 live migration
shards still running at the time — the agent killed the QG run after ~7 minutes rather than block further progress on
the actual migration, and did not commit the fix.

**Confirmed still uncommitted** as of 2026-07-10
(`market_tick_data_service/scripts/ migrate_prediction_instrument_id_wrap_2026_07_09.py` shows as a modified,
uncommitted file in the shared working tree).

## Why it matters

Low urgency: the migration itself already self-recovered from the underlying issue (the first fix was sufficient for all
5 shards, including the 2 later moved to dedicated VMs, to complete successfully with 0-8 errors out of tens of millions
of rows each). This is a real robustness improvement sitting ready to ship, not a currently-broken capability.

## Recommended next step

Ship it on a normal pass:
`cd market-tick-data-service && bash scripts/quality-gates.sh --no-fix && bash scripts/quickmerge.sh "fix(prediction): further connection-pool hardening for the instrument-id-wrap migration script" --agent --files 'market_tick_data_service/scripts/migrate_prediction_instrument_id_wrap_2026_07_09.py'`
— no urgency, just needs a quiet window to run its own quality gates without CPU contention from other live migrations.

## Resolution (2026-07-14)

Re-checked: `git status` on this file is clean (no uncommitted changes in this clone) and `git log` shows exactly one
commit for it (`1f28c472`, 2026-07-09). That single committed version already mounts the boosted `HTTPAdapter` onto
**all 3** client instances this doc's "What I found" section names as the root cause: the main `get_storage_client()`
singleton (`_boost_connection_pool()` — main + oauth-token-refresh sessions, lines ~86-131) AND the separate listing
client `main()` constructs directly (lines ~484-490, comment: "applied here to the separate listing client"). So the fix
this doc calls "the first fix" — the one that made all 5 shards self-recover — is fully present and committed.

The SEPARATE "further hardening fix… for a related, narrower connection-pool issue" this doc describes was never
precisely specified beyond that phrase, and its diff was never captured anywhere recoverable (not stashed, not
committed, not in any other doc) — the working tree that held it is gone. Re-deriving and shipping a fix without knowing
its actual intended content would mean fabricating code rather than restoring lost work, which isn't safe to do blind.
Given (a) the migration has already completed successfully across all 5 shards with 0-8 errors out of tens of millions
of rows each, (b) there is no currently-open incident this blocks, and (c) the exact narrower issue is unspecified, this
issue is resolved as: current code already contains the documented fix; the undocumented "further" refinement is not
recoverable and not worth guessing at. If a real narrow connection-pool bottleneck resurfaces on a future large
Prediction/MTDS backfill, profile it fresh rather than trying to reconstruct this one.
