---
title: "Continuation prompts — 2026-05-11 PM — push-through-nice-haves cycle"
type: orchestration-doc
status: active
created: 2026-05-11
horizon: 2-3 wall-clock day cycle through 2026-05-15 freeze gate
companion_to: plans/active/work_split_2026_05_11_ikenna.md + plans/active/work_split_2026_05_11_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Continuation prompts — 2026-05-11 PM

> **Why this doc**: Ikenna + Harsh slot agents need paste-ready CONTINUE prompts (not initial spawn prompts) for the
> 2026-05-11 PM → 2026-05-15 freeze-gate push. Operator directive (2026-05-11 PM):
> _"don't stop even at nice-haves; we're moving faster than planned + Harsh leaves in ~3hr."_ 6 slots have outstanding
> work — 4 Ikenna (2/5/7/8) + 3 Harsh (2/4/6). Skipped: Ikenna 1 (main), 3/4/6 (already in flight, no staleness),
> Harsh 1 (main), 3 (defi #5 VM monitoring), 5 (⚪ QUIET, absorbed by Ikenna 7).
>
> Each prompt is paste-ready into the slot's Cursor / Claude Code tab. References the **lean
> `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (10KB)**, not the prior 211KB CLAUDE.md.

## Ikenna slot 2 — `manifest_schema_final_gate` Phase 2 (UTL v8 ManifestWriter) — CRITICAL PATH

```text
You are Tab 2 (Ikenna). Continue your re-task. Worktree: ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/ikennaigboaka/2.

CONTEXT: slot 2's writegate slice (b) primary scope ✅ DONE. Re-tasked 2026-05-11 PM to manifest_schema_final_gate Phase 2 (UTL v8 ManifestWriter). Plan checkboxes show ZERO progress on Phase 2 — you need to actually start + ship.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/ikenna_orchestrator/_agent_pings.md § [main → slot 2]
  3. unified-trading-pm/plans/active/work_split_2026_05_11_ikenna.md § Slot 2 — RE-TASK BRIEF #2
  4. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md:266-285 (Phase 2.A/B/C/D — your scope)

Agent-tag: ikenna-v8-manifestwriter-tab.

CRITICAL PATH for 2026-05-15 freeze gate Phase 2.1 atomic v8 rename. Without Phase 2, the rescan plan can't write rows in v8 shape.

SHIP all 4 sub-phases. Do NOT stop at nice-haves. Sequence:
  Step 0 (~10 min): clear slot 8's Q2 Bug 1 — fix `unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy.py:163-168` 6 keys + docstring `:216` (`"market-data-pipeline-service"` → `"market-data-processing-service"`); update matching test if any. Ack slot 8 via writegate plan body that Q2 fully cleared.
  Step 1 (~3 hr) Phase 2.A: extend UTL `manifest_writer.py` 5 record_* functions with 3 new v8 kwargs (`service_emission_state` / `last_emission_decision_at` / `expected_window_completeness_fraction`, all default None for v7 back-compat).
  Step 2 (~2 hr) Phase 2.B: `emission_publisher.publish_with_policy` integrates Phase 1.B `next_state(...)` resolver (slot 6 shipped UAC@174f401) + passes to ManifestWriter.
  Step 3 (~2 hr) Phase 2.C: `manifest_reader_fallback.py` v7-tolerance for ≤30d + `READER_BACKFILLED_V8_COLUMNS_AS_NULL` event.
  Step 4 (~3 hr) Phase 2.D: NEW `manifest_migrations/v7_to_v8.py` per-VM-shard migration helper. Per-VM shard isolation MANDATORY.

CADENCE per shippable unit (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 1+2+4):
  git add <specific files> && \
    git commit --no-verify -m "..." && \
    git push origin tab/ikennaigboaka/2 --no-verify && \
    git push origin tab/ikennaigboaka/2:live-defi-rollout --no-verify

Plan-flip the `manifest_schema_final_gate_2026_05_09.md:266-285` checkbox in same logical unit as code commit. Done-definition (per plan): UTL@<sha> + 11+ tests + v7 back-compat.

DON'T STOP at nice-haves. If you finish all 4 sub-phases + 11+ tests + QG green, look for adjacent items (Phase 2 codex updates, helper docstrings, integration test extensions) and ship them. Goal: maximum surface coverage before 2026-05-15.

DONE: append DONE-2026-05-12 block in manifest_schema_final_gate plan body. EOD-audit per CLAUDE.md.
```

## Ikenna slot 5 — RE-TASK EXPANSION Tier 1 + Tier 2 (4 plans concurrent)

```text
You are Tab 5 (Ikenna). Continue your re-task expansion. Worktree: ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/ikennaigboaka/5.

CONTEXT: slot 5's primary re-task (DeFi 1.E + hard_schema Phase 1) ✅ DONE. Operator authorized RE-TASK EXPANSION 2026-05-11 PM with Tier 1 + Tier 2 — none of it started yet.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/ikenna_orchestrator/_agent_pings.md § [main → slot 5] RE-TASK EXPANSION
  3. unified-trading-pm/plans/active/work_split_2026_05_11_ikenna.md § Slot 5 RE-TASK → "RE-TASK EXPANSION 2026-05-11 PM"
  4. unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md:3162 (Phase 6.5 — Tier 1 item 2)
  5. unified-trading-pm/plans/active/expected_universe_v2_design_2026_05_08.md (Tier 1 item 3)

Agent-tag: ikenna-multi-track-tab.

SHIP all 6 items. Do NOT stop at nice-haves. Sequence:

TIER 1 (Phase 1 freeze-gate critical-path; ~5-6 AI-days w/ sub-agent fan-out → 2-3 wall-clock):
  1. **Step 5 of P0-2 MDPS (~30min)**: flip `market-data-processing-service/schemas/output_schemas.py:57-66` OHLCV column nullability from `nullable=True` → required for `trades`/`ohlcv`. Closes LAST item of P0-2 surgery.
  2. **Writegate slice (c) Phase 6.5 — Other features-* services bundle (~2-3 days)**: fan out 4 Task blocks in ONE message — one sub-agent per features-svc family (onchain-defi + sports + prediction + microstructure). Each sub-agent: audit emission boundaries → extend UAC `SERVICE_OUTPUT_POLICIES` seed dict → wire `publish_with_manifest_lookup()` per Phase 5.3-5.4 MDPS template → unit + integration tests → flip Phase 6.5 sub-checkboxes.
  3. **Promote `expected_universe_v2_design_2026_05_08.md` → active execution plan (~1 day)**: v8 just shipped at UAC@174f401, prereq cleared. Promote draft to executable phase shape + ship inline UAC additions the v2 enumerator needs.

TIER 2 (carryover from original re-task; ~3-5 AI-days):
  4. **available_at Phase 1 DeFi/TradFi/Predictions per-adapter stamping**: same shape as Harsh slot 4's sports stamping at MTDS@c186ecb. 3 asset_groups, fan out 3 sub-agents.
  5. **PROTOCOL_LAUNCH_DATES research ~30 (chain, protocol) pairs**: fan out 8-10 sub-agents per chunk of 3-4 pairs. Each: WebFetch protocol launch announcement → propose conservative date → add to UAC `PROTOCOL_LAUNCH_DATES` dict. ~6,912 rows reclaimed.
  6. **DeFi Phase 1.E Stream C remainder**: finish the partial archetype enum flips.

CADENCE per shippable unit (per CLAUDE.md Half 1+2+4):
  git push origin tab/ikennaigboaka/5 --no-verify && \
    git push origin tab/ikennaigboaka/5:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Push through all 6 items. Sub-agent fan-out is your force multiplier — use it heavily (4-way for Phase 6.5; 8-10-way for PROTOCOL_LAUNCH_DATES). Operator goal: data-status backfill via expected_universe_v2 + close gate item #3 to ~70% green.

DONE: DONE-2026-05-12 block in each plan touched. Cross-side INFO ping to harsh-main when Phase 6.5 lands.
```

## Ikenna slot 7 — ABSORB Harsh slot 5 live-pipeline carry-forward

```text
You are Tab 7 (Ikenna). Continue with absorbed Harsh-side scope. Worktree: ${WORKSPACE_ROOT}/.tabs/7/ on branch tab/ikennaigboaka/7.

CONTEXT: slot 7's primary scope (alerting + risk + DR Rounds 1-4) ✅ DONE. Operator 2026-05-11 PM: Harsh leaving in ~3hr → ABSORB Harsh slot 5's quiet/queued live-pipeline carry-forward (Harsh slot 5 ⚪ QUIET; no collision). UTL primitives prereq already shipped (Ikenna slot 4 PM@35a79dd4: MDPSStreamingAggregator + AssetScopedFeaturesRunner + CrossCuttingFeaturesRunner real impl, not stubs).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/ikenna_orchestrator/_agent_pings.md § [main → slot 7] absorb brief
  3. unified-trading-pm/plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md § "Deferred work after 2026-05-11 Harsh slot 5 session" + Phases 3, 5, 6, 15
  4. unified-trading-pm/codex/05-infrastructure/live-pipeline-architecture.md (design contract)

Agent-tag: ikenna-livepipeline-absorb-tab.

SHIP all 4 phases. Do NOT stop at nice-haves. Sequence:
  1. **Phase 3 — MTDS websocket `--mode live` + `live_runner.py`** (~2-3 days). MTDS service wiring for live-mode streaming consumption per `MDPSStreamingAggregator` contract.
  2. **Phase 5 — features-svc per-family `live/` runners** (~2-3 days; fan out 5 sub-agents in ONE message — delta-one + volatility + onchain + cross-instrument + multi-timeframe). Each sub-agent wires `AssetScopedFeaturesRunner` for its family.
  3. **Phase 6 — features-svc cross-cutting `live/` runner** (~1-2 days) using `CrossCuttingFeaturesRunner`. Cross-family fan-in per the codex doc's cascade table.
  4. **Phase 15 — QG sweep + smoke** (~1 day). Workspace-wide QG green + integration smoke + per-service consumer-class audit per codex doc emission-policy reference fixtures.

CADENCE per shippable unit (Half 1+2+4):
  git push origin tab/ikennaigboaka/7 --no-verify && \
    git push origin tab/ikennaigboaka/7:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Push through Phase 3 + 5 + 6 + 15. If wall-clock allows, look for adjacent items in `live_pipeline_mtds_mdps_features_2026_05_08.md` § Deferred work (other phase carryover, codex extensions, integration tests) and ship them.

DONE: DONE-2026-05-12 block in `live_pipeline_mtds_mdps_features_2026_05_08.md`. Cross-side ping to harsh-main when Phase 3/5/6/15 land (confirms slot 7 absorption complete).
```

## Ikenna slot 8 — ABSORB Harsh slot 4 bucket-SSOT carry-forward (Phase 0f + 0h)

```text
You are Tab 8 (Ikenna). Continue with absorbed Harsh-side scope. Worktree: ${WORKSPACE_ROOT}/.tabs/8/ on branch tab/ikennaigboaka/8.

CONTEXT: slot 8's primary scope (P0-2 MDPS surgery + writegate Phase 6.2) ✅ DONE. Operator 2026-05-11 PM: Harsh leaving in ~3hr → ABSORB Harsh slot 4's deferred-to-next-session bucket-SSOT items (Phase 0f + Phase 0h; PREREQ for bucket-migration Phase 2.6 cutover 2026-05-15→05-19).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/ikenna_orchestrator/_agent_pings.md § [main → slot 8] absorb brief
  3. unified-trading-pm/plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md Phase 0f + 0h (body ~line 202 + ~line 223)
  4. unified-trading-pm/cursor-configs/CLAUDE.md "Bucket-name SSOT operator decision (b+)" section

Agent-tag: ikenna-bucket-prereq-tab.

SHIP both phases. Do NOT stop at nice-haves. Sequence:
  1. **Phase 0f — VM launcher env-awareness** (~1-2 days; ~30 launcher scripts under `deployment-service/scripts/vm/`). Each launcher reads `DEPLOYMENT_ENV` (env var OR `--env <prod|staging|dev>` CLI flag) + passes to VM via metadata so bucket-resolution targets the right env. Fan out 5-6 sub-agents in ONE message — each handles 5-6 launchers in parallel.
  2. **Phase 0h — sync script** `deployment-service/scripts/sync-buckets-prod-to-{staging,dev}.sh` (~1-2 days). Truncated date window (default 2yr staging / 1yr dev) + same-region copy ($0 egress) + manifest re-sync post-data-sync. Per CLAUDE.md (b+) decision section.

CADENCE per shippable unit (Half 1+2+4):
  git push origin tab/ikennaigboaka/8 --no-verify && \
    git push origin tab/ikennaigboaka/8:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Both are PREREQ for Phase 2.6 cutover — without them, VM launches won't target env-tiered buckets + dev/staging will drift from prod. **AFTER Phase 0f + 0h, pick up Phase 3 (cross-asset rescan) — UNOWNED + closes operator's bad-data cleanup gap** (operator surfaced 2026-05-11 PM: bad parquets — 1440-NaN-bar, partial bundles, schema drift — travel with Phase 2.6 rsync as bad parquets; rescan is the post-migration validation layer that flips them in manifest to `attempted_failed`).

**Tier 2 — Phase 3 cross-asset rescan (~3-5 AI-days; existing plan, no new plan to create)** per `manifest_schema_final_gate_2026_05_09.md:286-301`:
  3. **Phase 3.A** — NEW `deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh` per `manifest_cross_asset_rescan_design_2026_05_08.md:113-127` (singleton-locked, same-region `ap-northeast-1`, per-VM shard isolation envvars, `WORKERS=64` + `HTTP_POOL_SIZE=128`, tarball-default + tarball-from-local flag). Mirror `launch-sfi-forward-poll.sh` precedent. Natural deployment-service continuation of Phase 0f/0h work.
  4. **Phase 3.B** — Add `cross-asset-rescan-` prefix to `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict. Relaunch watchdog VM after dict update (per CLAUDE.md "VM Naming Convention" rule — watchdog only fetches Python at boot).
  5. **Phase 3.C** — Register launcher in `deployment-api/deployment_api/services/deploy_missing.py` `_SERVICE_LAUNCHER_SCRIPTS` registry so Deploy-Missing UI button surfaces it.
  6. **Phase 3.D** — NEW `instruments-service/scripts/cross_asset_rescan.py` per `manifest_cross_asset_rescan_design_2026_05_08.md § "Rescan flip schema"`. Class A mutable auto-flips (capture_status / error_reason / attempted_at / path reconciled to disk truth; bad parquets → `attempted_failed(reason=PARQUET_NAN_RATIO_EXCEEDED|PARTIAL_BUNDLE|SCHEMA_DRIFT|PHANTOM_PATH_MISSING)`) + Class C triage routing to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` for operator review. Per-asset-group rules respect `venue_trading_calendar` / `*_LAUNCH_DATES` / `SOURCE_COVERAGE_START` / market lifecycle. Phantom-audit integration baked in (target 0 phantoms across 5 asset_groups; baseline 354 residual from 2026-05-04). **If slot 3 picks up Phase 3.D in parallel, coordinate via the rescan-design plan body's open-questions section.**
  7. **Promote `manifest_cross_asset_rescan_design_2026_05_08.md` from DRAFT → active execution plan** in same logical unit (frontmatter `status: active` flip + add a Phase 1 (= Phase 3.A-D consumption) section pointing at the work-split brief).

DONE: DONE-2026-05-12 block in `bucket_name_ssot_canonicalisation_2026_05_10.md` (Phase 0f + 0h) + `manifest_schema_final_gate_2026_05_09.md` (Phase 3.A-D if shipped) + `manifest_cross_asset_rescan_design_2026_05_08.md` (status flip + Phase 1 ratification). Cross-side ping to harsh-main: "Phase 0f + 0h shipped — Phase 2.6 cutover prereqs cleared; Phase 3 cross-asset rescan launcher + script shipped — bad-data cleanup mechanism online."
```

## Harsh slot 4 — push through final items before leaving (~3hr window)

```text
You are Harsh Tab 4. Final push before you leave. Worktree: ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/hk/4.

CONTEXT: bucket-SSOT (b+) session 4 in flight. **Phase 0f + 0h ABSORBED by Ikenna slot 8** (operator-directed 2026-05-11 PM, PM@c0d10139) — don't redo those. Your remaining queue: env-less-GCP-entries sub-todo + Done-def #5/#6 + the OUTPUT_BUCKET_TEMPLATE docs + dependency_checker.py sub-todos. Done-def #3 ✅ Q6 RESOLVED = deferred to Phase 2.6 cutover (don't pick that up either).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/_agent_pings.md § ikenna-main → harsh-main (Phase 0f + 0h absorption)
  3. unified-trading-pm/plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md "Deferred work" scoreboard + remaining `- [ ]` items

Agent-tag: harsh-bucket-final-push.

SHIP what's still in scope. Do NOT stop at nice-haves. ~3hr window:
  1. **env-less-GCP-entries sub-todo finish** (DeFi-raw `dex-*`/`*-defi` already partial @fedbbd67; finish + ship remaining GCP entries).
  2. **Done-def #5 — QG STEP 5.68 ratchet** (enforces no inline `f"gs://{bucket}/..."` formatters; AST-walk).
  3. **Done-def #6 — bucket-name SSOT audit table** (which kinds are env-tiered vs env-less, which Group A vs B, etc.).
  4. **dependency_checker.py inline templates → resolve_bucket() migration** (deferred per Done-def #2 split; can pick up if BaseDependencyChecker scope is contained).
  5. **OUTPUT_BUCKET_TEMPLATE docs** (codex/codex-internal explainer).

CADENCE per shippable unit:
  git push origin tab/hk/4 --no-verify && \
    git push origin tab/hk/4:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Push through all 5 items if wall-clock allows. Phase 0c/0d (= Phase 2.6 cutover) is OUTSIDE this window (that's the 2026-05-15→05-19 work).

DONE: DONE-2026-05-12 block in `bucket_name_ssot_canonicalisation_2026_05_10.md`. Final cross-side INFO ping to ikenna-main listing what shipped before you left so we know what remains for the Phase 2.6 cutover.
```

## Harsh slot 2 — features_service_qg_cleanup final push (~3hr window)

```text
You are Harsh Tab 2. Final push before you leave. Worktree: ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/hk/2.

CONTEXT: features_service_qg_cleanup session 4 in flight. Session 3 shipped 28 commits @features-service`e4b10570`; QG 16→9 violation categories. Remaining 7 carry-forward items.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/features_service_qg_cleanup_2026_05_11.md § Phase 1.2 carry-forward + Phase 1.2e + Phase 1.5

Agent-tag: harsh-features-qg-final-push.

SHIP what's still in scope. Do NOT stop at nice-haves. ~3hr window:
  1. **Sports func-decomps**: batch_handler.run (416L), team_form (357L), h2h (272L), player_lineup (219L), feature_builder_registry (389L), `_fetch_runner`/`batch_handler`×3 imports-inside, `_sync_runners` asyncio, broad-except.
  2. **Empty-string/dict/list fallbacks across sports+onchain** + 3 `mock_data_provider.py` `# noqa` markers.
  3. **Phase 1.2e — schema-prov** (group-1 → UAC.internal; group-2 `# CORRECT-LOCAL` + `Dependency*` UTL-root-dedup + `FeatureProcessingResult` double-def collapse + `PubSubMessage`→`DeltaOnePipelineMessage` + new `_`-prefixed helper dataclasses).
  4. **Phase 1.5 — UTL `_get_workspace_root()` lift** (×8 callsites; P2).
  5. **Q4b 1-line import edit** in `scanner_factories.py:43` (if not already shipped).

Fan out 3-4 sub-agents in ONE message per the plan's fan-out spec.

CADENCE per shippable unit:
  git push origin tab/hk/2 --no-verify && \
    git push origin tab/hk/2:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Goal: QG 9→0 violations + Phase 4.6/6 of `features_repo_consolidation_2026_05_08.md` checkbox can flip.

DONE: DONE-2026-05-12 block in `features_service_qg_cleanup_2026_05_11.md` + parent `features_repo_consolidation_2026_05_08.md` Phase 4.6/6 flip if violations cleared. Cross-side INFO ping to ikenna-main with QG final count + Phase 4.6/6 flip status.
```

## Harsh slot 6 — freeze-gate items 8 + 9 final push (~3hr window)

```text
You are Harsh Tab 6. Final push before you leave. Worktree: ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/hk/6.

CONTEXT: workspace QG green sweep + codex audit pass + freeze-gate items 8 + 9 in flight. Track-D P0-1/2/3 ✅; F3 + slot-worktree-QG-bug ✅ RESOLVED (PM@39ab61e5).

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md freeze-gate items 8 + 9
  3. unified-trading-pm/plans/active/issues/codex_audit_2026_05_11.md remaining open items
  4. unified-trading-pm/plans/active/issues/qg_sweep_2026_05_11.md remaining open items

Agent-tag: harsh-qg-codex-final-push.

SHIP what's still in scope. Do NOT stop at nice-haves. ~3hr window:
  1. **Phantom-audit cadence**: run `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|prediction|sports} --dry-run` per asset_group on a same-region GCE VM. Address findings or flip `- [ ]` if zero.
  2. **basedpyright + full quality-gates.sh sweep** workspace-wide (was deferred days 2-4 per qg_sweep doc; ~30-60min per repo for 22 repos — pick the highest-risk repos first).
  3. **Codex doc currency spot-checks** for the 50 present codex docs the Phase 1 plans touch (Phase 1.D alerting/risk/DR + 1.E DeFi + 1.F UI/credentials clusters — slot 7's Round 1-4 just landed; verify codex docs reflect new SSOTs).
  4. **STEP 5.67 baseline maintenance**: if new banned-NaN-placeholder patterns surface during the audit, extend `banned_placeholder_methods_baseline.yaml`.

CADENCE per shippable unit:
  git push origin tab/hk/6 --no-verify && \
    git push origin tab/hk/6:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Goal: freeze-gate item 8 (workspace QG green) + item 9 (codex SSOT currency) BOTH `- [x]` before you leave. These are 2 of the 6 Phase 1 freeze-gate items; closing them removes 2 known-red dependencies for the 2026-05-15 cutoff.

DONE: DONE-2026-05-12 block in `code_freeze_migrate_backfill_sequencing_2026_05_10.md`. Cross-side INFO ping to ikenna-main with freeze-gate items 8 + 9 status + phantom-audit residual counts per asset_group.
```

## Ikenna slot 3 — defi #5 lending-indices VM wrap + Phase 0.4 MDPS reconciler + cross-asset rescan assist

```text
You are Tab 3 (Ikenna). Continue your re-task + absorb 2 adjacent items. Worktree: ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/ikennaigboaka/3.

CONTEXT: slot 3 currently running defi_master Priority #5 lending-indices LINEA/BSC routing config + backfill VM `mtds-lending-indices-20260511-181115` (ETA ~60-90min from launch). When VM hits STOPPED + canonical re-consolidated shows the recent gap (2026-05-07→05-11) captured + checkbox flips `[x]`, primary scope ✅ DONE. Operator-directed 2026-05-11 PM: don't go quiet at done — absorb 2 adjacent items per the "no nice-have skipping" + "consolidate gap-plugging items into existing plans" directives.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/continuation_prompts_2026_05_11_pm.md § Slot 3
  3. unified-trading-pm/plans/active/issues/mdps_canonical_writer_off_by_one_tf_2026_05_11.md (Phase 0.4 scope — reconciler script)
  4. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md:286-301 (Phase 3 — if assisting slot 8)
  5. unified-trading-pm/plans/active/manifest_cross_asset_rescan_design_2026_05_08.md (rescan design spec — if assisting slot 8 on Phase 3.D)

Agent-tag: ikenna-reconciler-tab.

SHIP both items post-lending-VM. Do NOT stop at nice-haves. Sequence:

Step 0 (~5 min) — VM verification: confirm `mtds-lending-indices-20260511-181115` STOPPED cleanly + canonical manifest shows LINEA AAVEV3 + BSC AAVEV3 captured for 2026-05-07→05-11. Flip defi_master Priority #5 `[x]` per slot 3 LEDGER entry. If VM hasn't landed yet, hold + monitor; pick up Step 1 once verified.

Step 1 (~2-3 hr) — **Phase 0.4 MDPS `available_at` off-by-one reconciler** per `mdps_canonical_writer_off_by_one_tf_2026_05_11.md` Phase 0.4. Every MDPS-emitted candle written between Phase 1.2A.1 ship (2026-05-10) and MDPS@f004e12 fix (2026-05-11) carries the over-stamped value (1-timeframe overshoot). NEW script `market-data-processing-service/scripts/reconcile_available_at_off_by_one_tf.py`:
  - Walks `gs://{pid}-mdps/` for candles written in the bad window (filter by manifest `attempted_at` between 2026-05-10 + 2026-05-11)
  - Per-row: re-stamps `available_at = tick_close + latency_delta` (drops the redundant `+ tf_delta`)
  - Per-VM shard isolation MANDATORY (per CLAUDE.md "Per-VM shard isolation for concurrent backfills" rule)
  - Tests + dry-run mode + production verification probe
  - Plan-flip Phase 0.4 `[x]` + DONE block in issue doc

Step 2 (~ASSIST slot 8 OR full ownership if slot 8 saturated) — **Cross-asset rescan Phase 3.D assist**. Slot 8 is primary owner of Phase 3.A/B/C/D per `manifest_schema_final_gate_2026_05_09.md:286-301`. If slot 8 ships Phase 3.A/B/C cleanly but Phase 3.D (`instruments-service/scripts/cross_asset_rescan.py` reconciler logic per the rescan-design spec) is too big for slot 8's remaining capacity, slot 3 absorbs Phase 3.D. Mental model matches lending-indices reconciler work (manifest reconciliation against on-disk truth). Coordinate with slot 8 via `manifest_cross_asset_rescan_design_2026_05_08.md` open-questions section. Don't double-implement — verify slot 8 status first.

CADENCE per shippable unit (CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 1+2+4):
  git push origin tab/ikennaigboaka/3 --no-verify && \
    git push origin tab/ikennaigboaka/3:live-defi-rollout --no-verify

DON'T STOP at nice-haves. Phase 0.4 unblocks honest MDPS metadata for the 2-day bad window; Phase 3.D assist unblocks operator's bad-data flagging mechanism post-Phase-2.6 bucket migration.

DONE: DONE-2026-05-12 block in `mdps_canonical_writer_off_by_one_tf_2026_05_11.md` (Phase 0.4 reconciler) + (if Phase 3.D taken) `manifest_schema_final_gate_2026_05_09.md` + `manifest_cross_asset_rescan_design_2026_05_08.md`. Cross-side INFO ping to harsh-main when reconciler runs to completion + manifest consolidator merges shards.
```

## Skipped (already in flight or absorbed)

- **Ikenna slot 1 (main orchestrator)**: this session.
- **Ikenna slot 4, 6**: already in flight on live-pipeline Phase 14/11 / manifest_schema_final_gate Phase 1 follow-ups respectively. No staleness signal.
- **Harsh slot 1 (main orchestrator)**, **slot 3** (defi #5 VM monitoring — same scope as Ikenna slot 3), **slot 5** (⚪ QUIET, absorbed by Ikenna slot 7).

## Composes with

- CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE (Half 1+2+4 — per-shippable-unit cadence + slot push + LDR FF).
- CLAUDE.md "Capture Discoveries As Plan Todos Immediately" (mid-session findings → plan todos, not chat).
- CLAUDE.md "Findings Triage Discipline" (case-1-to-5 routing for surprises).
- CLAUDE.md "Sub-Agents & Autonomous Agents: Full Rules Required" (paste lean SUB_AGENT_MANDATORY_RULES.md at top of every Task spawn).
