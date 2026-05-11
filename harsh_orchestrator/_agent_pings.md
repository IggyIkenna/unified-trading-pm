<!--
Lightweight ping ledger — the doorbell.

Sub-agents append a one-liner here when they need attention from the main agent.
The main agent polls this file every ~10 min via /loop, reads the referenced plan
doc, answers in the plan doc's `## Open questions` section, then removes the line
from this file.

Format (one line per active ping):
  [YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>

Examples:
  [2026-05-08 09:14 UTC] phase2-routes-tab — Q on subprocess.run timeout default; see deployment_api_work_stream_a_2026_05_07.md
  [2026-05-08 09:32 UTC] dart-playwright-tab — done with personas 1-3, blocked on persona 4 fixture; see strategy_and_dart_master_2026_05_07.md
  [2026-05-08 10:01 UTC] manifest-rescan-tab — silent-zero finding for prediction asset_group; see issues/prediction_silent_zero_2026_05_08.md

This file is EPHEMERAL — entries are removed when handled. Full Q&A history lives
in the referenced plan doc's `## Open questions` section (status badges 🟡 BLOCKED
→ ✅ RESOLVED).

When this ledger consistently has 15-20+ active pings, signal Harsh to spawn a
SECOND main agent in another tab; two main agents can divide the ledger using a
[CLAIMED-BY: main-1] / [CLAIMED-BY: main-2] marker on each ping.

Full lifecycle + format spec: cursor-configs/CLAUDE.md § "Daily Work-Split Process" — Plan-of-record + Q&A bus / Ping ledger / Polling cadence subsections.
-->

# Active pings

[2026-05-11 06:52 UTC] harsh-workspace-qg-tab — STARTED slot 6 (plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)
[2026-05-11 06:55 UTC] harsh-bucket-and-adapter-tab — STARTED slot 4 (plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
[2026-05-11 07:05 UTC] harsh-wave3x-tab — Track D audit COMPLETE; anti-seq verdict = NO new schema dim, 1 candidate new reason EXPECTED_KNOWN_SOURCE_GAP (Ikenna slot 5 decision); + P0 bugs surfaced (MTDS blank-reason sentinel-abort, MDPS dead write-gate + 1440-NaN TradFi passthrough, commodity phantom-row) → owners writegate Phase 2.A/2.E + Harsh slots 5+6; see plans/active/issues/wave3x_track_d_findings_2026_05_11.md
