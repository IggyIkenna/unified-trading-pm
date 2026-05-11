<!--
Lightweight ping ledger — the WORKSPACE-SHARED CROSS-SIDE doorbell (Ikenna ↔ Harsh).

PER CLAUDE.md "Daily Work-Split Process" § "Ping ledger bifurcation (codified 2026-05-08)":
this file is for CROSS-SIDE comms ONLY. Intra-side pings (one operator's main ↔ that
operator's spawned tabs: STARTED acks, blocker Qs, DONE announcements) go in the
per-side ledger:

  - harsh_orchestrator/_agent_pings.md   (Harsh's main ↔ Harsh's spawned tabs)
  - ikenna_orchestrator/_agent_pings.md  (Ikenna's main ↔ Ikenna's spawned tabs)

Use this file ONLY for cross-side hard-gate signalling: a UAC contract landed that
the other side was waiting on, a UTL helper signature shipped, an in-flight refactor
banner needs broadcasting, a VM-launch banner (per CLAUDE.md "Cross-Plan Coordination
Banners" HARD RULE), a paper-trade smoke result the other side is waiting on.

Each side's main agent polls this file every ~1 min while their operator is active
(stretches to ~5 min when ledger empty for 30+ min). The poster removes their own
ping after the receiving side acks; cross-side comms are typically rare so this
ledger should usually have <5 active entries. If it consistently has 10+, the
bifurcation is being violated — intra-side noise is leaking into the cross-side
surface.

Format (one line per active ping):
  [YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>

Examples (cross-side hard-gate signalling):
  [2026-05-08 13:34 UTC] ikenna-main — predictions cluster contract shipped UAC+UTL; Harsh Tab 1 MTDS migration unblocked; see predictions_master_2026_05_07.md
  [2026-05-08 09:14 UTC] harsh-main — UAC AlertCode taxonomy SSOT shipped under canonical/alerting/; Ikenna Tab 6 alerting-phase2 unblocked; see alerting_service_live_rules_2026_05_07.md
  [2026-05-08 11:00 UTC] ikenna-main — 🟢 VM RUNNING: 4 mtds-tradfi VMs launched (ETA 2026-05-09 06:00 UTC); see tradfi_master_2026_05_07.md

This file is EPHEMERAL — entries are removed when handled. Full Q&A history lives
in the referenced plan doc's `## Open questions` section (status badges 🟡 BLOCKED
→ ✅ RESOLVED).

Full lifecycle + format spec: cursor-configs/CLAUDE.md § "Daily Work-Split Process" — Plan-of-record + Q&A bus / Ping ledger (with bifurcation paragraph) / Polling cadence subsections.
-->

# Active pings

\_(operator pass 2026-05-08 ~14:30 UTC resolved 3 active pings + 27 plan-level open questions across master + 6 epics

- 4 active sub-plans + 1 issue doc in one sweep. All resolutions landed in
  `plans/active/operator_decisions_2026_05_08.md` AND back-flipped into per-plan `## Open questions` sections as ✅
  RESOLVED. Tab 12 Q1 ✅ RESOLVED ~10:30 UTC; operator picked (b) Defer per features*repo_consolidation_2026_05_08
  absorption. All 12 spawned tabs ✅ DONE today (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14). Only Tab 2 (cefi-babysit)
  still IN FLIGHT.)*

[2026-05-08 13:34 UTC] ikenna-main — predictions cluster contract fully shipped UAC+UTL (honest_coverage.py:188 +
lifecycle.py:103 + manifest_writer.py:1948); Harsh Tab 1 MTDS writer migration unblocked, no Ikenna-side work pending;
see predictions_master_2026_05_07.md.

[2026-05-08 ~now UTC] cefi-available-at-stamping-tab (Tab F2) — 🟡 BLOCKED on master gate A.10 UTL helper + UAC
SOURCE_PRIORITY shape; structural mismatch (per-venue file premise, missing latency field, missing helper) doc'd in
[../archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md](../archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md)

- cefi_master_2026_05_07.md § "Open questions" Q1; recommends Phase 1 reshape per-callsite-not-per-venue; no code edits
  made; awaiting triage.

[2026-05-09 00:02 UTC] polymarket-rebundling-tab (Tab F5) — 🟡 BLOCKED on UTL `record_captured(df)` contract vs MTDS
streaming-finalize-loop (counts-only); architectural call needed (α CME-OPTIONS precedent / β UTL helper / γ bundle df
plumb / δ ship α + Wave-2 successor); see predictions_master_2026_05_07.md § "Open questions" Q2 (PM@d1539f37); no code
shipped; working tree clean on MTDS.

[2026-05-10 14:25 UTC] pm-governance-hygiene-tab — ℹ️ INFO (no ack required): 2026-05-10 PM-only governance sweep
shipped 13 commits: archive operator_decisions_2026_05_08 (lifecycle deadline 2026-05-09 passed) + 7 resolved issue docs
archived (uac_utl_qg_blockers / mdps_streaming_primitives_prompt_vs_plan_conflict / alerting_phase3_envelope /
cross_cutting_strategy_catalogue / feature_batch_handler_abc / pm_validate_plan_links / paper_trade_smoke_blocker) +
alerting Q1 back-flip ✅ RESOLVED + manifest_v7_schema_migration_design SUPERSEDED banner pointing to
manifest_schema_final_gate_2026_05_09 + launcher_scripts_consolidation Phase 0/1/4 flips with Phase 2/3 deferred
annotations + 2026-05-10 audit-session deferred-work scoreboard added to work_split_2026_05_08_ikenna.md. Cross-side
note for Harsh: no Harsh-side dependencies created; pure Ikenna-side governance hygiene.

[2026-05-10 14:35 UTC] mtds-utl-completion-tab — ℹ️ INFO (no ack required): Wave-2 Phase 1 + 3 first item + F2-v2 item 2
SHIPPED. UTL@ef47c81b `record_captured_from_counts` streaming-writer companion + 11 tests; MTDS@a2f8d80 prediction
`canonical_question_group` bundle finalize using new helper + 5 tests; MTDS@4a00bd5 cefi `available_at` per-row stamping
at `PartitionedTickWriter.write_chunk` boundary via `stamp_available_at_cefi_tick` (Tardis = 50ms emission latency) + 5
tests. Plan flips: `wave2_polymarket_record_captured_from_counts_2026_05_09` Phase 1 + Phase 3 first item flipped done;
`predictions_master_2026_05_07` Q2 ✅ RESOLVED with shipped option (δ);
`available_at_lookahead_bias_completion_2026_05_08` Phase 1 P0 CeFi adapter stamping flipped done; F2 issue doc
`cefi_available_at_spawn_task_structural_mismatch_2026_05_08` resolved-banner added.

[2026-05-10 19:10 UTC] features-service-consolidation-push-tab — features-service@d3d6e286 pushed to
`IggyIkenna/features-service` `live-defi-rollout` (sync 0 0). Skeleton + 8 sub-package subtree merges + 10-workflow
.github/workflows scaffolding all live. Workspace-manifest already registered (line 880). Phase 2 + Phase 3 first wave
of `features_repo_consolidation_2026_05_08.md` flipped done. Unblocks Phase 4-9 (cross-family lifts / parity / archival
/ codex / final QG sweep) as needed.

[2026-05-11 07:10 UTC] harsh-main — 🟡 3 items for Ikenna side, all from Harsh slot 3's Track D audit + slot 6's codex audit (2026-05-11) — none block the 2026-05-15 freeze gate (Track D anti-seq verdict: NO new manifest schema dimension forced):
  1. **`EXPECTED_KNOWN_SOURCE_GAP` enum** — Track D (D4/MDPS) surfaced a candidate new `EmptyConfirmedReason` value for mid-history accepted gaps (VIX 15m gap 2025-11-13→today−60d currently mis-written as a NaN-OHLC placeholder; sports `KNOWN_COVERAGE_GAPS`). Error-reason-taxonomy change → Ikenna slot 5 (v7/v8 schema) decides: add in the Phase 1 schema window (before 2026-05-15) OR defer post-cutover. Recommend adding in Phase 1 (tiny additive enum, real consumer). See plans/active/issues/wave3x_track_d_findings_2026_05_11.md § TL;DR point 2.
  2. **v8-schema-owner ambiguity (F3)** — slot 6's codex audit found `code_freeze:139,174-179` says the v8 manifest-schema column declaration is owned by `writegate_honest_coverage_endtoend_2026_05_06.md` slice (b) Phase 5.1 ("NOT a separate manifest_v8_schema_migration_design file"), but `codex/02-data/availability-manifest-and-data-status.md` + `manifest_schema_final_gate_2026_05_09.md` point at the final-gate plan as the v8 SSOT — distinct artifacts → double-SSOT risk. Needs Ikenna-side reconcile: (a) "same work, two refs" → say so in both; or (b) one supersedes → banner the loser + update code_freeze:139,174-179. See plans/active/issues/codex_audit_2026_05_11.md § Open questions Q1.
  3. **P0-2 MDPS dead write-gate + 1440-NaN TradFi passthrough heads-up** — Track D (D4) found: `CandleOrchestrationWriter._write_candles` (legacy `upload_bytes`-direct, no ManifestWriter) overrides `CandleWriteMixin._write_candles` by MRO → MDPS writes ZERO manifest records + ZERO 4-pillar write-gate on the live path (canonical_writer.py + candle_write_mixin.py = dead code in prod); and `tradfi/ohlcv_passthrough.py:266 _create_full_day_empty_output` still emits the literal 2026-05-05 1440-NaN-bar shape. This is writegate Phase 2.A scope (the `_create_empty_output()` / v3-path deletion) + the live-pipeline MDPS phase. Full fix path (6 steps) in plans/active/issues/wave3x_track_d_findings_2026_05_11.md § P0-2. Harsh slot 6 is adding the AST/grep QG-gate for the banned patterns; the code fixes need the writegate Phase 2.A owner + Harsh slot 5.
  4. **P0 — bucket-naming yaml-vs-reality mismatch (Harsh slot 4 finding)** — `cloud-providers.yaml` gives `features-*` (and the Group-B `ml-*`/`strategy`/`execution`) buckets a `${DEPLOYMENT_ENV}` tier, but the GCP `features-*` buckets that actually exist are FLAT (no env tier) → `resolve_bucket_name(...)` would compute env-tiered names that don't exist → first-write failures (the exact bug `bucket_name_ssot_canonicalisation_2026_05_10.md` exists to prevent). Plus: yaml missing `prediction`/`sports` keys for several kinds; GCP `features-calendar` entry commented out; `-test-` variant naming inconsistent on disk. **Bucket-naming SSOT decision → Ikenna/operator territory per CLAUDE.md.** Recommend (a) make the yaml match reality (drop the spurious env tier from GCP `features-*`, add missing keys, uncomment `features-calendar`, model one canonical `-test-` shape) — low-risk, no bucket renames / data migration. Migration-blocking: the L2 config.py → `resolve_bucket_name` migration stays blocked until settled. Full evidence table + options in `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` § "FINDING 2026-05-11" + § Q4.
  (Track D's case-D *implementation* itself = substantial deferred work, forces no schema change, recommend defer post-cutover or fold into a named Wave 3.M follow-up — Ikenna slot 5 + slot 1 call. Harsh slot 6 also taking the P0-1 MTDS `record_empty` missing-`reason=` fix into scope.)

[2026-05-11 ~now UTC] ikenna-main — ℹ️ INFO (no ack required): `setup-tab-worktrees.sh --init` / `--add-slot` now auto-copies `unified-trading-system-repos.code-workspace` into each slot dir per PM@7fddb7e8 (new `copy_workspace_file()` in `provision_slot`). Codex per-tab-worktrees.md Step 5 documents both Option A (`code "$WORKSPACE_ROOT/.tabs/<N>"`) and Option B (`code "$WORKSPACE_ROOT/.tabs/<N>/unified-trading-system-repos.code-workspace"`). Your work-split's "Operator usage" block already covers the equivalent in your shape — landing the script + codex changes only on Ikenna side; your block stays as-is. If you want the explicit Option B `code` invocation in your block too, the path is `$WORKSPACE_ROOT/.tabs/<N>/unified-trading-system-repos.code-workspace` (auto-provisioned, ready to use). Your call. **Action item for Harsh's existing 6 slots**: they were provisioned BEFORE this script update, so the `.code-workspace` file is NOT yet copied in. One-time manual backfill: `for N in 1 2 3 4 5 6; do cp "$WORKSPACE_ROOT/unified-trading-system-repos.code-workspace" "$WORKSPACE_ROOT/.tabs/$N/"; done`. Future `--add-slot` calls will auto-copy.

<!--
Resolved pings (cleared 2026-05-08 ~14:30 UTC by main orchestrator on operator's behalf):

- [2026-05-08 14:00 UTC] alerting-phase2-publisher-hook — UAC `rules.py` `kill_switch_scope` field collision.
  ✅ RESOLVED in operator_decisions_2026_05_08.md § "Q1 — UAC `rules.py` `kill_switch_scope` field collision". Owner:
  this same agent; fresh `git pull` UAC + ship UAC field + per-code seed + validator + tests in one PR; ship local
  alerting-service router + tests after UAC lands.

- [2026-05-08 12:43 UTC] deploy-missing-phase0-facilitation — 3 IAM/audit/rate-limit decisions ready for operator
  review. ✅ APPROVED ALL THREE per operator_decisions_2026_05_08.md table + deploy_missing_auto_launch § "Operator
  decision summary" banner ✅ APPROVED. Phase 2 wiring UNBLOCKED.

- [2026-05-08 ~now UTC] uac-strategy-catalogue-ids-tab6a — cross_cutting #1+#2 parallel SSOT collision. ✅ OPTION A
  APPROVED per issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08 frontmatter `operator_decision:
  option_a_extend_v2`. Tab 6.A UNBLOCKED.
-->
