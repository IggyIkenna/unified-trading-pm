---
title: Main Agent Ledger — Harsh side
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> Tracks today's slot assignments and live state. Universal mechanics and reading order → [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md). Full task briefs → today's work-split. History → `git log`.

---

## Current shift: 2026-05-13 Wave 2 (Day-4 PM, Harsh-side ONLY)

**Work-split**: [`plans/active/work_split_2026_05_13_harsh.md`](../plans/active/work_split_2026_05_13_harsh.md) § "Wave 2"
**Model**: Sonnet 4.6 / thinking: high (all slots). Wave 1 closed; reset done on 6 of 8 slots; 6 implementor slots active (2, 3, 4, 6, 7, 9); 3 held for cleanup (5, 8, 10).

| Slot | Theme | State | Plan-of-record | Branch |
|------|-------|-------|----------------|--------|
| 1 | Main orchestrator + on-call + LEDGER + ping triage | 🟢 ONLINE | (this LEDGER + work-split) | `tab/hk/1` |
| 2 | data_status_drilldown Phase 7 P1+P2 — venue-detail panel fixes + observability fields | ✅ DONE Wave 4 — Phase 7 P1: manifest_reader pagination + total_instruments_unfiltered (deployment-service@99acc13 + deployment-api@0b853ba); VenueDetailResult top_instruments→instruments rename + "showing N of M" + day??date fix (deployment-ui@a67c32f). Phase 7 P2: missing_dates sample label (deployment-ui@8ce86fa); totals_source rollup/manifest field (deployment-api@b73ce3b + deployment-ui@0529c0a). Plan 31/41 done. Scoreboard in plan body. Shift end called by operator. | `data_status_drilldown_shard_atom_alignment_2026_05_07.md` | `tab/hk/2` |
| 3 | DR Phase 6+9+10 finalisation (AGENT items + SCRIPT prep only; NO VM launch) | ✅ DONE Wave 2 — DR Phase 6.A + 9.A chaos-drill + cutover VM launchers (deployment-service@347d9df); plan flip + DONE ping (PM@08326628). | `disaster_recovery_circuit_breakers_2026_05_10.md` | `tab/hk/3` |
| 4 | 🐛 Script 3 classifier P1 fix (instruments-service ↔ UTL signature) + arbitrage_price_dispersion final 2 items | ✅ DONE Wave 2 — arbitrage 20/20 shipped (strategy-service@33697ce + PM@56b83750); classifier kwarg RESOLVED-AS-STALE (slot 4 RCA: bug doesn't exist on current LDR — was stale VM tarballs pre-UTL@290a415, no code fix needed; PM@a9a6b0d0 issue doc updated). 🟡 RUF002 lint failure on pre-existing foreign files filed as P2 issue. | `issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` + `arbitrage_price_dispersion_finalisation_2026_05_09.md` | `tab/hk/4` |
| 5 | (cleanup done 2026-05-13 — local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5 as historical record) | 🟪 RESERVE (ready) | — | `tab/hk/5` |
| 6 | wave3x_residual_ssots finalisation (73% → 100%) | ✅ DONE Wave 2 — Track D DOCS codex stub shipped (PM@84e29700); scoreboard + DONE block (PM@580176e7); 4 deferred items documented with named owners. All work on LDR. | `wave3x_residual_ssots_2026_05_08.md` | `tab/hk/6` |
| 7 | cross_asset Phase 5A/5B/5C TradFi ETF + futures-roots consolidation | ✅ DONE Wave 2 — Phase 5A/5B/5C VERIFIED already shipped by slot-2-Day-3 (2026-05-12); slot 7 audited membership/consumer-migration clean. Shipped: Phase 5E T-WTI added to TRADFI_ROOTS (UAC@4b97104) + Phase 7G VIX-15m doc-pointer fix (CLAUDE.md + codex). PM@f9f61000 plan annotations. | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 5 | `tab/hk/7` |
| 8 | (cleanup done 2026-05-13 — local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8 as historical record) | 🟪 RESERVE (ready) | — | `tab/hk/8` |
| 9 | 🆕 mock_data Phase 3.D per-reader threading (MTDS Tardis/Databento + ml-inference + strategy) — taken over from slot 5 since slot 5 is held | ✅ DONE Wave 2 — MTDS reader wired (mtds@82639e0 TickDataHandler synthetic-override early-return); PM@33a40116 plan flip; Phase 3.D ALL 3 readers DONE (strategy@a03d12e + ml-inference@0206358 pre-existing + mtds@82639e0 new). DEFERRED: subprocess harness real-VM run (needs operator OK) + slot-8 handshake items. ⚠️ MODEL MISMATCH: LEDGER declared Opus 4.7 but slot ran as Sonnet 4.6 — operator continued. | `mock_data_pipeline_benchmarking_2026_05_10.md` | `tab/hk/9` |
| 10 | dex_perp Phase 2A/2D/2E + 2F P2 + EigenLayer Phase 3A/3B + Phase 4A/4B + codex 5.1/5.2 | ✅ DONE 2026-05-13 — all in-scope shipped (MDPS@c30d8e0 cherry-picked by main to rescue foot-gun #5: MDPS 19-test fix had been left on tab/hk/10 only); worktree reset complete; 4 items DEFERRED with successor refs in plan body | `dex_perp_and_venue_data_expansion_2026_05_12.md` | `tab/hk/10` |

**Wave 1 closeout** (commits on LDR for the record):
- Slot 2 ✅ DONE (PM@3b317e65) — propagation chain Gate 1 fired
- Slot 3 ✅ DONE (PM@3a16656d) — GCP 3 buckets shipped, AWS deferred Phase 2.6
- Slot 4 ✅ DONE (PM@42755747) — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept)
- Slots 5-9 ✅ DONE (PM@3d3d5c14) — batch closure; full per-slot detail in pings/slot_N.md
- Slot 10 ✅ DONE — all in-scope tasks shipped to LDR; 4 items DEFERRED with successor annotations in `dex_perp_and_venue_data_expansion_2026_05_12.md` scoreboard PM@6090e183

**Wave 2 reset status (2026-05-13 09:35-09:40 UTC, PM@7ca204a6)**:
- Slots 2, 3, 4, 6, 7, 9 — reset clean to origin/live-defi-rollout ✅
- Slot 5 — rebase failed (collision casualty cc62f02 in MTDS); deferred to manual cleanup
- Slot 8 — UAC rebase failed (collision casualty 949185c); deferred to manual cleanup
- Slot 10 — skipped per operator (still working at reset time); finished after reset

**Cleanup queue (DONE 2026-05-13 ~11:55 UTC)**:
- ✅ Slot 5 reset: local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5
- ✅ Slot 8 reset: local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8
- ✅ Slot 10 foot-gun #5 intercept: MDPS@0c92b91 (19-test fix) was NOT on LDR despite slot 10's "all work synced" claim. Main cherry-picked to LDR as MDPS@c30d8e0; slot 10 worktree reset clean.

All 10 slots are now in clean known state on LDR (or as ✅ DONE for slot 10).

**Critical-path sequencing (slot 1 monitors during Wave 2)**:
1. Slot 4 ships Script 3 classifier fix → unblocks defi/sports/prediction legacy-blank reclassification (deferred apply-flips still pending post-cutover)
2. Slot 9 ships mock_data Phase 3.D → benchmark report has real 6-stage timings (not extrapolated)
3. Slots 2/3/6/7 fully independent — run in parallel
4. New HARD RULE: LDR-alignment cadence (codified 2026-05-13 PM@f49d5f7d). Slots that boot must rebase ALL owned repos; FF-push per shippable unit, not end-of-session

**Wave 1 audit retrospective**: 3 critical follow-ups pushed PM@7ca204a6 — see `plans/active/issues/audit_wave1_quality_2026_05_13.md` for synthesis. Two impact Wave 2 spawn:
1. Slot 9 Task 3 strategy-paper VM was never actually launched in Wave 1 — re-opened in `promote_workflow_may23_cli_path_2026_05_10.md` Phase 1 as P0. Available for any slot that finishes early to absorb.
2. Sports classifier extension never shipped (slot 9 Wave 1 grep-then-conclude miss) — re-filed as `plans/active/issues/sports_classifier_extension_followup_2026_05_13.md` P1. Available for reserve pickup.

**Operator-pending**: None blocking Wave 2 spawn. Carry-forward (post-cycle operator decisions): slot 8's A/B/C UAC architecture triage (deferred; lives in cross-side `_agent_pings.md`); Telegram OPS chat_id (operator action); AWS bucket creation (Phase 2.6 window, needs GCE VM with aws CLI).

---

## Wave 2 task briefs (slot N agents — read your row)

Each row is a full task brief. After `--reset-slot N` (done 2026-05-13 09:35 UTC), your worktree at `.tabs/N/` is clean on `tab/hk/N` matching `origin/live-defi-rollout`. Just boot + read your row + start.

### Slot 2 — risk_simulations finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `risk-and-exposure-service` + `unified-api-contracts` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](../plans/active/risk_simulations_limits_alerting_2026_05_10.md) (currently 33/40 P0 = 82%)
- **Task**: Ship the 7 open P0 items:
  1. Phase 4.A — risk-and-exposure-service rule migration to UAC registry; rule_evaluator wired
  2. Phase 8.A — Per-rule synthetic-fire test (uses `simulation_scenarios_topology_price_shocks_2026_05_09`)
  3. Phase 8.B — Per-archetype suite: ≥10 rules per archetype fire on schedule + alert routes per archetype
  4. Phase 8.C — Evidence capture
  5. Phase 9.A — Master plan Group F item 20 row gains "risk rule taxonomy + pre-flight + alerting wire"
  6. Phase 9.B — Banners removed
  7. (4 P1 stablecoin items D.2/D.5/D.6/D.7 — only if time after P0s done)
- **Done-def**: 33/40 → 40/40 P0; rule_evaluator wired; per-archetype suite green; Group F item 20 flipped.
- **No big decisions needed.**

### Slot 3 — DR finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`](../plans/active/disaster_recovery_circuit_breakers_2026_05_10.md) (currently 28/42 = 67%)
- **Task**: Write scripts + master-plan rows. **DO NOT LAUNCH ANY VMs** — Ikenna's hold direction on backfill/recon VMs is conservative; treat DR-drill VM launches the same and gate execution on operator OK.
  1. Phase 6.A — Cron VM `disaster-drill-cron-` launcher SCRIPT (writes only; no launch)
  2. Phase 6.B — Drill-report tooling (pass/fail per scenario; alerting rule on red >24h)
  3. Phase 9.A — Per-archetype `dr-drill-cutover-` launcher SCRIPT (arm `KILL_PER_ARCHETYPE`, etc.)
  4. Phase 9.B — Evidence-capture format
  5. Phase 10.A — Master plan rows Group F item 20 + 21 green
  6. Phase 10.B — Banners removed
- **Done-def**: 28/42 → ~38/42; SCRIPT artifacts written + linted + dry-run validated locally; ping `pings/slot_3.md` when scripts ready for operator OK to launch VMs.
- **No big decisions needed.**

### Slot 4 — 🐛 Script 3 classifier P1 + arbitrage final (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-library` + `strategy-service` + `unified-trading-pm`
- **Plans-of-record**:
  - [`plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`](../plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md) (P1 bug, slot 6 Wave-1 filed)
  - [`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md) (18/20 = 90%, 2 P1 items left)
- **Task**:
  1. **Fix `classify_blank_reason_row()` `fixture_manifest` kwarg mismatch**: Read UTL `unified_trading_library.manifest.classify_blank_reason_row` signature; read `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site; align (add `fixture_manifest` handling to reconciler OR drop from UTL — pick per which is canonical intent). FF-push.
  2. **Re-run Script 3 DRY-RUN** for defi/sports/prediction (NO `--apply-flips` — Ikenna's hold direction on manifest reconciliation VMs still applies). Update the issue doc with dry-run upgrade counts. FF-push.
  3. **Arbitrage final 2 items**: canonical BTC/USDT slot entry in strategy-service + tests (per plan-of-record line `^- \[ \]`). FF-push.
- **Done-def**: Script 3 classifier signature aligned + dry-run shows non-zero upgrades for defi/sports/prediction; arbitrage_price_dispersion 18/20 → 20/20.
- **No big decisions needed.**

### Slot 6 — wave3x_residual_ssots finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `unified-trading-library` + per-asset_group services (as items dictate) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/wave3x_residual_ssots_2026_05_08.md`](../plans/active/wave3x_residual_ssots_2026_05_08.md) (currently 16/22 = 73%, 6 items left across Tracks B/C/D/E)
- **Task**: Read the plan. Scan open `- [ ]` todos under Tracks B (sports per-source SSOTs) / C (reconcilers) / D (zero-activity-bar audit) / E (sports availability stamping cascade). Ship in plan order. FF-push per shippable unit.
- **Done-def**: 16/22 → 22/22; all Wave 3.X dimensions covered.
- **No big decisions needed.**

### Slot 7 — cross_asset Phase 5 TradFi consolidation (**Opus 4.7 / thinking: high** ⬆ — multi-callsite refactor)

- **Owned repos**: `unified-api-contracts` + `instruments-service` + `market-tick-data-service` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md) § Phase 5 + reference [`plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md`](../plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md) for TF-1..TF-10 detail
- **Task**:
  1. **Phase 5A — `tradfi_etfs.py`**: Diff-merge 4 ETF universes → single SSOT at `unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py`. Sources: `tradfi_symbology.py:459` `KNOWN_ETFS` + `tradfi_ticker_universe.py:295` `ETF_TICKERS` + `tradfi_instrument_universe.py:151` `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` + `TRADFI_TICKER_COVERAGE_START` ETF subset. **READ each source file body** — do not grep-then-conclude on membership equivalence. Escalate membership conflicts to operator via `pings/slot_7.md`.
  2. **Phase 5B — `tradfi_roots.py`**: Diff-merge 3 futures-roots universes (`TRADFI_INSTRUMENTS` + `TRADFI_DATABENTO_INSTRUMENTS` + `databento_cme_converter.py:57` `SUPPORTED_UNDERLYINGS`) → single SSOT.
  3. **Phase 5C — `asset_group_registry.py`**: TradFi entries point at new SSOTs.
  4. **Phase 7 (small) — VIX-15m doc-pointer fix (TF-7)**: VIX-15m constants live in `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md L535 claims. Fix the doc reference in CLAUDE.md + any codex doc that mirrors the wrong pointer.
- **Done-def**: 4 ETF universes → 1 SSOT (membership diff documented in plan body); 3 futures-roots → 1 SSOT; cross_asset audit Phase 5 checkboxes flipped with evidence; VIX-15m doc-pointer corrected.
- **GREP-THEN-READ warning**: This is multi-callsite refactor. Wave 1 audit found Sonnet had grep-then-conclude failures on this exact shape (3 of 3 slots). Read each source file's actual dict/tuple contents — don't trust the variable name to imply the contents.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

### Slot 9 — mock_data Phase 3.D per-reader threading (**Opus 4.7 / thinking: high** ⬆ — 3-reader bespoke wire-in)

- **Owned repos**: `market-tick-data-service` + `ml-inference-service` + `strategy-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`](../plans/active/mock_data_pipeline_benchmarking_2026_05_10.md) § Phase 3.D (currently 19/29 = 66%)
- **Task**: Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`. For EACH reader, OPEN the function body before deciding the wire-in shape:
  1. **MTDS Tardis/Databento fetch**: External-API non-GCS readers. Needs benchmark-specific instrumentation hook (NOT standard `resolve_bucket_uri` override since these don't go through GCS).
  2. **ml-inference direct feature-vector loader**: Add bespoke `_STAGE_COMMAND_TEMPLATES` entry.
  3. **strategy direct signal+features loader**: Same pattern as (b).
  Then verify with subprocess-pipeline benchmark on 1-day batch.
- **Done-def**: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped with shipped SHAs; benchmark report includes all 6 pipeline stages with REAL timings (currently extrapolated for these 3).
- **GREP-THEN-READ warning**: Slot 9 in Wave 1 had a grep-then-conclude failure on sports classifier. Don't repeat — open each reader's function body before declaring shape.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

---

## Spawned tab — boot

You are slot N. Do this in order, nothing else until done:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — git discipline, LDR-alignment HARD RULE, workspace-drift recognition, communication bus, pre-commit check, sub-agent rules.
2. Find your **Slot N task brief** in this LEDGER § "Wave 2 task briefs" above → that's your full assignment (owned repos + scope items + done-def + model tier).
3. Read your **plan-of-record** (named in your brief) — scan open `- [ ]` todos for your phase.
4. Append boot ack to [`pings/slot_N.md`](pings/) using `date -u` for timestamp, then start work.

**COMPACT-CYCLE GUARD**: Do NOT read repo-level `.claude/CLAUDE.md` files from repos you're working in — the workspace CLAUDE.md (auto-loaded in system context) covers all critical cross-cutting rules. Only read a repo's CLAUDE.md if it's explicitly named in your task brief.

---

## Default agent-spawn workflow (HARD RULE — codified 2026-05-13)

**This is the default for every wave / morning / mid-day relaunch.** Operator should NEVER receive a verbose paste-ready spawn prompt from main unless they explicitly ask for one. Task briefs live in this LEDGER § "Wave N task briefs" — agents read them from there.

**Step 1 (slot 1 main runs, background, parallel)** — reset all 6 slots in one shot:

```bash
cd /home/hk/unified-trading-system-repos
for n in 2 3 4 6 7 9; do
  (
    find ".tabs/$n" -maxdepth 2 -name ".git" 2>/dev/null | while read g; do
      git -C "$(dirname $g)" checkout -- . 2>/dev/null
    done
    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot $n 2>&1 | grep -E "Resetting|complete|ERROR" | sed "s/^/[slot $n] /"
  ) &
done
wait
```

Swap the slot list `2 3 4 6 7 9` for whichever slots the operator wants to spawn this wave. The `git checkout -- .` step silently discards any leftover uncommitted state from the prior agent (usually a STARTED ack — no real work lost). Reset then rebases `tab/hk/N` cleanly onto `origin/live-defi-rollout`.

**Step 2 (operator opens N terminals)** — paste this lean prompt (swap `N`):

```
You are Harsh-side slot N. Pull origin/live-defi-rollout in unified-trading-pm, read harsh_orchestrator/LEDGER.md to find your Slot N task brief, then start working on it. If any owned repo in your worktree at /home/hk/unified-trading-system-repos/.tabs/N/ is behind LDR, fetch + rebase first. Follow harsh_orchestrator/AGENT_ONBOARDING.md for git discipline + ping mechanics + LDR-alignment HARD RULE.
```

That's it. No COMPACT-CYCLE GUARD lectures, no LDR-alignment explanations, no GREP-THEN-READ warnings inline — all that lives in `AGENT_ONBOARDING.md` (universal mechanics) and the LEDGER task brief (per-slot specifics including model tier + grep-then-read warnings on multi-callsite scopes).

**Step 3 (main monitors)** — agent reads LEDGER + plan-of-record + boots. If agent asks clarifying questions, the answer is "the LEDGER brief is the SSOT — re-read it; if still unclear, ping `pings/slot_N.md`". Don't expand the prompt; expand the LEDGER brief.

**Deviation only when operator explicitly says**: "give me a direct prompt for slot N" or "use a custom prompt for X reason". Otherwise: default workflow.

---

## Main orchestrator — fresh boot (slot 1)

Fresh main-agent chat (context window died, new session):

1. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && git -C /home/hk/unified-trading-system-repos/unified-trading-pm log --oneline -5 origin/live-defi-rollout` — see recent origin activity.
2. `cat harsh_orchestrator/pings/slot_{2..10}.md 2>/dev/null` — intra-side pings.
3. `cat plans/active/_agent_pings.md` — cross-side pings.
4. Read this LEDGER § "Current shift" table — note each slot's state; update any SPAWN PENDING → IN FLIGHT based on ping acks.
5. Ack to operator: "Main online. Slots in flight: N. Pings: M intra / K cross. Standing by."
