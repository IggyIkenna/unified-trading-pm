---
title: "batch_live_symmetry Tab 2 BE-AWARE banners not landed on 4 downstream plans"
created: 2026-05-14
author: harsh-main-review
status: RESOLVED — harsh-main landed all 4 banners + flipped checkbox (2026-05-14)
resolved_by: harsh-main (2026-05-14); verified by slot-8-ikenna (2026-05-14)
source:
  - plans/active/batch_live_symmetry_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

> **✅ RESOLVED** — All 4 banners verified present (gcs_migration_bundle L541, manifest_schema_final_gate L97,
> live_pipeline_mtds_mdps_features L1051, defi_master L34). Checkbox at `batch_live_symmetry_2026_05_10.md:117`
> already `[x]` (PM@harsh-main 2026-05-14). Issue CLOSED.

## What I found

`batch_live_symmetry_2026_05_10.md` line 117 has an open `- [ ]` P0 checkbox:

> "Land BE-AWARE / RE-VERIFY banners from Tab 2 onto:
> `gcs_migration_bundle_pipeline_mode_2026_05_08.md` ·
> `manifest_schema_final_gate_2026_05_09.md` ·
> `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
> `defi_master_2026_05_07.md`."

Tab 2's DONE condition explicitly requires these 4 banners. Slot 5 shipped all Tab 2 code
(UAC@01c1b59 — BatchExecutionMode + RECON_GREEN_THRESHOLDS; exec@b30167e2+7df685d8 — node_builder
migration; PM@88093918+2c547d64 — L7 fix-list + scoreboard) but the banner landing step was
skipped. Grep confirms none of those 4 plans have a batch_live_symmetry BE-AWARE banner.

The Tab 1 banners (line 114, `[x]`) were landed correctly. Only the Tab 2 set at line 117 is missing.

## Why it matters

The Cross-Plan Coordination Banners rule (CLAUDE.md) requires BE-AWARE banners when a UAC contract
ships that changes downstream consumer behaviour. The `BatchExecutionMode` enum and
`RECON_GREEN_THRESHOLDS` dict are new UAC contracts that affect gcs_migration_bundle (pipeline_mode
column consumers), manifest_schema_final_gate (reconciler thresholds), live_pipeline (runtime mode
routing), and defi_master (batch vs live execution mode). Without the banners, agents working those
plans may miss re-verification steps and build against stale assumptions.

## Recommended decision

Add the BE-AWARE banner text to the top section of each of the 4 plans:

> **🟡 IN-FLIGHT REFACTOR — batch_live_symmetry 2026-05-14** (BE-AWARE)
> `BatchExecutionMode` enum + `RECON_GREEN_THRESHOLDS` shipped at UAC@01c1b59.
> Re-verify any archetype-keyed batch/live routing code before touching pipeline_mode / reconciler
> threshold / mode-routing logic.

Then flip the checkbox `[x]` at `batch_live_symmetry_2026_05_10.md:117`.

execution:
  owner: slot 5
  cadence: one-shot
  verifier: grep "batch_live_symmetry" on all 4 plan files returns BE-AWARE banner; line 117 checkbox is [x]
  last_executed: NEVER
