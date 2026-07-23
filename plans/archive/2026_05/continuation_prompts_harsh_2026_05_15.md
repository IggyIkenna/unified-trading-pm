---
doc_type: plan
title: Continuation prompts — Harsh side, 2026-05-15 Day-1
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, e2e-testing]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-14
type: orchestration-spec
adopted: 2026-05-15 04:00 UTC
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Continuation Prompts — Harsh side, 2026-05-15 Day-1

> **Status: ADOPTED 🟢** — operator authorized Lever 1+2 pattern @04:00 UTC. Slots execute their queue + self-pivot;
> auto-poll script tracks STARTED/DONE/BLOCKED; main only intervenes on BLOCKED/cross-side/BIG findings.
>
> **Cycle context**: TODAY = Day-4 of 4-day Harsh density-push cycle (2026-05-12 → 2026-05-15). **Phase 1 freeze gate
> fires TODAY**. Slot 6's audit yesterday confirmed all 6 freeze-gate items green ✅ — no gate-blocking work needed
> today. Today's scope = Phase 8 coverage extensions + DeFi paper backtests + B-014 rollout completion +
> cutover-readiness hardening.
>
> **8 days to May-23 live-DeFi cutover.**
>
> **Day-1 deltas from yesterday EOD** (verified against overnight commits + cross-side ledger):
>
> - Slot 4 ✅ shipped B-006 (mtds@504bf34 + instruments@4063e08) overnight
> - Slot 5 ✅ shipped B-009 (risk@ac021a7 + execution@7de7385c) + Phase 3 TradFi migration overnight
> - Slot 6 ✅ self-completed Cluster A+B follow-on + B-012 codex audit overnight
> - Slot 7 ✅ shipped B-018 (36/36 repos snapshot live) + Wave 4 carry-forward overnight
> - Slot 8 ✅ shipped B-014 STEP 5.79-5.82 to base-service.sh + 13/15 service repos QG stub; **2 repos remain + 7
>   stashes in `.tabs/8/<repo>/` (msg `slot-8 B-014-ROLLOUT-COMPLETION`) need RECOVERY + ship**
> - 🚨 **Slot 3 B-016 ACK LANDED YESTERDAY @14:45 UTC** ("APD paper backtest GREENLIT. Proceed with Phase 2 launch") —
>   slot 3 went idle before seeing it; **Phase 2 launch is NOT blocked; slot 3's Day-4 item 1 is "launch now"**. B-016
>   uses CeFi features (different bucket from B-015) → not affected by B-015 phantom-manifest issue per slot 3's own
>   prereq ping
> - Slot 9 🛑 B-015 STILL BLOCKED — Ikenna @02:00 UTC: smoke FAILED SILENTLY (phantom manifest skipped both VMs, ZERO
>   data written); Ikenna slot 8 owns phantom-clear via
>   `reconcile_phantom_manifest_rows_all.py --asset-group DEFI --apply-flips` + re-smoke; HOLD Phase 2 until Ikenna
>   confirms phantom-fix DONE + green smoke
> - Two NEW P0/P1 SECURITY ISSUES filed today by Ikenna slot 6 (GCP SA private key + GitHub PAT in git history across 5
>   repos) — **NOT Harsh-side scope**; Ikenna owns rotation + history rewrite. Awareness only.
>
> See [`harsh_orchestrator/THEMATIC_CLUSTERS.md`](../../harsh_orchestrator/THEMATIC_CLUSTERS.md) for the stable theme
> map this draws from.
>
> **Companion docs**:
>
> - [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md) § "End-of-shift summary 2026-05-14" — what
>   shipped yesterday + open blockers
> - [`harsh_orchestrator/BACKLOG.md`](../../harsh_orchestrator/BACKLOG.md) — full dispatch queue with item details
> - [`plans/active/_agent_pings.md`](_agent_pings.md) — cross-side ping ledger

## How slots use this doc

1. Read **only your slot section** below.
2. Execute items in order. After each item DONE + pushed (commit on `live-defi-rollout`): ping DONE in your slot ping
   file with SHAs.
3. **Immediately start next item** in your queue — do NOT wait for main dispatch.
4. After your numbered queue is empty, pull from your "Reserve" list.
5. Ping main ONLY on: BLOCKED (genuine gap, ≥30 min investigation), cross-side coordination needed, BIG finding (data
   correctness / multi-repo).
6. EOD: write a brief "🏁 Slot N — Day-1 close" ping summarising what shipped + what's deferred.

## Post-DONE self-poll protocol (ALL slots — mandatory)

After CYCLE-CLOSE or reserve queue exhaustion, do NOT idle. Run this loop until main sends new work:

```bash
while true; do
  sleep 180
  cd /home/hk/unified-trading-system-repos/unified-trading-pm
  git pull --rebase origin live-defi-rollout --quiet
  # Check for a new [main → slot N] direction ping posted AFTER your CYCLE-CLOSE
  head -10 harsh_orchestrator/pings/slot_<N>.md
done
```

- If you see a new `[main → slot N]` direction ping at the top of your ping file → stop the loop, read the direction,
  start immediately.
- If you see `STAND-DOWN` in the direction → stop completely.
- Do NOT ping main to ask for work — just keep polling until the ping arrives.
- Replace `<N>` with your slot number.

## Tomorrow's main-orchestrator tasks (slot 1)

Before slots start, main does:

1. Run `bash scripts/agents/harsh_auto_poll.sh --dry-run` once to verify the auto-poll script reads state correctly.
2. Schedule auto-poll via cron OR run `--watch` in a tmux pane.
3. Triage 2 open cross-side blockers from yesterday EOD:
   - **B-016 (slot 3) Ikenna ACK** — check `plans/active/_agent_pings.md` for response
   - **B-015 (slot 9) BLOCKED** — DeFi features pipeline gap + MTDS lst_rates stale; operator decision on resolution
     path
4. Verify B-014 rollout (slot 8) completed cleanly; flip BACKLOG status if DONE.
5. Run `regenerate_active_plan_inventory.py`.
6. Drop ONE "Day-1 START" ping per slot pointing to their section here. Then stand back.

---

## Slot 2 — Deployment Infra & Lint Sweep

**Theme** (per `THEMATIC_CLUSTERS.md`): deployment-service VM infra + lint sweeps **Status at start of Day-4**: B-011
DONE ✅ (deployment-service@cf6bb83 yesterday) + api_football Phase 3b/3c ✅ + alerting N802 ✅. Standing by.

### Day-4 queue (verified open as of 2026-05-15 morning)

1. **🚀 `honest_coverage` cron VM scheduling** — slot 7 filed
   `plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md` yesterday:
   `GET /api/data-status/honest-coverage` returns 404 because no cron VM is currently writing daily
   `gs://central-element-323112-honest-coverage/{date}/coverage.json`. **Build the cron VM launcher + Cloud Scheduler
   trigger** (same pattern as B-018 QG snapshot cron). Done-def: (a)
   `deployment-service/scripts/vm/launch-honest-coverage-vm.sh` exists + registered in `VM_PREFIX_TO_BUCKET`; (b) Cloud
   Scheduler trigger created for daily 00:30 UTC; (c) smoke run produces first `coverage.json` to GCS; (d) endpoint
   `/api/data-status/honest-coverage` returns 200 with current date payload. Coordinate with slot 7 on UI badge ("last
   honest-coverage update age").
2. **VM_PREFIX_TO_BUCKET watchdog blindspot audit** — B-011 noted 8 blindspot prefixes. Investigate each: (a) is VM type
   still active? (b) which bucket maps? (c) update `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict; (d) relaunch
   watchdog VM per CLAUDE.md. Done-def: 0 unknown prefixes; watchdog re-deployed.
3. **Codex audit on deployment-and-qg-strategy** — Phase 8.A surfaces (B-006/B-007/B-008/B-009/B-010/B-012/B-013/B-018)
   shipped yesterday need codex reflection. Verify `/codex/05-infrastructure/deployment-and-qg-strategy.md` +
   `/codex/05-infrastructure/vm-tarball-deployment.md` reflect: new VM_PREFIX entries (qg-snapshot, honest-coverage),
   B-018 cron VM pattern, Phase 8.A coverage targets. Done-def: codex doc updated OR confirmed already current.
4. **alerting-service codex violations follow-up** —
   `plans/active/issues/alerting_service_codex_violations_d5_d7_2026_05_14.md` (4 D.5+D.7 codex violations filed by slot
   6). Triage: fix where mechanical, escalate to operator if not.

### Reserve queue

- Cross-repo shellcheck sweep on launchers in `deployment-service/scripts/vm/` (any post-B-011 additions)
- ml-training-service `catboost_info/` gitignore hygiene (training artifacts polluting worktree)
- deployment-service VM launcher template consolidation (DRY common patterns across launch-\*.sh)

### Coordination

- deployment-service overlap with slot 7 (Phase 4 cron VM + Phase 4.B downstream) — coordinate file-level; slot 7 owns
  the UI half of honest-coverage badge
- **DO NOT touch `deployment-service/scripts/base-service.sh` template** — slot 8's B-014 rollout work in flight

---

## Slot 3 — Strategy Service & DeFi Paper Backtests

**Theme**: archetype coverage + DeFi paper backtests (APD half) **Status at start of Day-4**: B-010 DONE ✅ + B-016
Phase 1 DONE ✅ + critical APD alias bug fix shipped (strategy@0ca3fac + e2e@d55e7eb). **🚀 B-016 ACK LANDED** from
Ikenna @14:45 UTC 2026-05-14: "B-016 APD paper backtest GREENLIT. Proceed with Phase 2 launch." (see cross-side ledger).
Slot 3 went idle before seeing it.

### Day-4 queue (verified open as of 2026-05-15 morning)

1. **🚀 B-016 PHASE 2 LAUNCH (priority 1; was blocked, NOW UNBLOCKED)** — Ikenna ACKed yesterday afternoon. Slot 3
   missed it overnight. **Sanity-check first**: read `plans/active/_agent_pings.md` for the full Ikenna response
   (start_date, bankroll, hedge venue list confirmations); B-016 uses `features-cefi-central-element-323112` bucket (NOT
   the empty `features-onchain-*` bucket from B-015 phantom issue) — verify CeFi bucket has data for your target window.
   Then **LAUNCH**:
   ```bash
   python e2e-testing/scripts/defi/colocated_engine.py \
     --strategy arbitrage_price_dispersion --mode paper \
     --start-date <Ikenna-confirmed> --end-date <Ikenna-confirmed>
   ```
   Capture VM name + correlation_id. Ping STARTED-Phase-2 immediately on VM-up. Phase 3 = autonomous 30-day monitor
   (survives session shutdown). Done-def: VM running + STARTED event in
   `gs://central-element-323112-events/events/strategy-service/.../*.jsonl`.
2. **archetype_slot_resolver test coverage** — yesterday's APD alias fix (`strategy@0ca3fac`) shipped without tests. Add
   unit tests: (a) `resolve("arbitrage_price_dispersion")` returns slot ID; (b) `resolve("APD")` uppercase alias returns
   same; (c) unknown string raises helpful error; (d) regression test for the bug you caught (sys.exit(1) on missing
   alias). Done-def: 4+ tests + QG green.
3. **execution alpha smoke test extensions** — yesterday slot 3 added smokes (`strategy@fc634e3`). Extend: (a) APD
   multi-venue slippage scenarios across 6 perp venues; (b) carry archetype hedge leg fill simulation; (c) edge cases
   (zero-volume venue, paused league, single-leg-only). Done-def: 5+ new scenarios + QG green.
4. **DeFi paper backtest report template refinement** —
   `e2e-testing/reports/defi_paper_runs/arbitrage_price_dispersion_template.md` (slot 3@aa336ed). Pre-populate with
   Phase 2 launch SHA + VM name fields so Phase 3 monitor day-30 report has skeleton ready.

### Reserve queue

- batch_live symmetry strategy-service items (any remaining from Tab 3)
- V2BatchHarness GCS mock conftest extensions (`@8e478de` baseline)
- carry_staked_basis archetype validation test coverage (mirrors slot 9 B-015 if B-015 still BLOCKED)

### Coordination

- Pair with slot 9 on cross-side DeFi prereqs — share Phase 1 verification patterns
- strategy-service overlaps with slot 4 (general tests) — coordinate file-level
- **Once VM launched, ping cross-side ledger** so Ikenna knows Harsh's APD half is in flight

### Open questions

#### Q1 — [slot-3, 2026-05-15 05:18 UTC] — B-016 DEFERRED: MTDS CeFi tick coverage insufficient for any 7-day window

**Status**: 🔴 DEFERRED — upstream CeFi MTDS tick data has no continuous 7-day window with ≥4 APD venues

**Finding (updated 2026-05-15, post operator option-B decision)**:

Operator approved option B (7-day smoke window). Scanned
`gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/` for APD target venues:
BINANCE-FUTURES, BYBIT, DERIBIT, OKX-FUTURES/SPOT/SWAP. Coverage is highly sporadic:

- Mar 30, 31, Apr 1: 6 venues each (BINANCE, BYBIT, DERIBIT, OKX all present) — best 3-day run
- Apr 2-5: 1-2 venues only
- Apr 13-14: 4-6 venues briefly
- No 7-day window anywhere with ≥4 venue families present on every day

**Conclusion**: Option B cannot be satisfied — upstream MTDS tick data does not have any valid 7-day window. Per
operator deferred fallback (07:38 UTC): **B-016 is DEFERRED**.

**Also confirmed (issue #1 from Q1 original, fixed)**:

- `colocated_engine.py` `_FEATURE_BUCKETS["CEFI"]` hardcoded wrong bucket name → fixed to use `resolve_bucket_name()`
  (committed in e2e-testing@3ee6177).

**Re-activation condition**: B-016 re-activates automatically when CeFi delta_one features land in GCS (i.e., after
`features_service --operation batch --asset-group cefi --feature-family delta_one` runs over a continuous 7-day window
with ≥4 venues). At that point BACKLOG status flips from DEFERRED to DISPATCHED.

**Status**:
`DEFERRED — no valid smoke window; re-activates when CeFi features-service batch completes over 7d continuous window`

---

## Slot 4 — Test Failures Absorption & Service Lifecycle Coverage

**Theme**: Phase 0 test failure absorption + ServiceBootstrap lifecycle coverage **Status at start of Day-1**: B-006
DONE ✅ (mtds + instruments lifecycle tests). ml-inference Phase 0 DONE ✅.

### Day-1 queue

1. **B-006 extension — features-service ServiceBootstrap** — yesterday's note: "features-service top-level is a pure
   dispatcher (no ServiceBootstrap), per-family CLIs have it + static scan tests verify markers". Verify: does each
   per-family CLI (delta_one, volatility, sports, etc.) have lifecycle test coverage? If any family CLI is missing, add
   it. Done-def: every per-family CLI in features-service has STARTED/STOPPED/FAILED test OR a documented exemption with
   rationale.
2. **B-006 verification — risk + execution lifecycle re-validation** — yesterday's claim: "execution + risk already had
   full lifecycle tests". Verify by reading: `risk-and-exposure-service/tests/unit/test_lifecycle_events.py` (or
   equivalent) + `execution-service/tests/unit/test_lifecycle_events.py`. Confirm coverage matches B-006 spec. If gaps,
   fix.
3. **ml-inference-service Phase 6.6 emission policy coverage extensions** — yesterday's
   `b43da70 fix(qg): ml-inference-service` got QG green. Look for coverage gaps in `publish_with_policy`
   per-strategy-signal path. Add tests for: WARN_ONLY, NAN_FILL, STRICT_FAIL policy outcomes for ml-inference. Done-def:
   ml-inference-service coverage ≥ pre-existing + new lines covered.

### Reserve queue

- Cross-repo test diagnostic backlog (any remaining pre-existing failures filed as issue docs)
- features-service Phase 6 emission policy parity check (delta_one + cross_instrument + onchain)
- instruments-service test extensions on Phase 3 migration script

### Coordination

- execution-service overlap with slot 5 (kill switch) + slot 6 (custody) — coordinate file-level
- features-service overlap with slot 9 (peripheral) — usually distinct concerns

---

## Slot 5 — Risk Engine + Execution Alpha + Kill-Switch

**Theme**: risk + execution coverage + kill switch + circuit breaker **Status at start of Day-1**: B-009 DONE ✅
(risk@ac021a7 + execution@7de7385c). Phase 3 TradFi migration shipped (instruments@db070da + @e1ca983).

### Day-1 queue

1. **B-009 extension — UTL 3-tier kill-switch coverage** — yesterday's DONE ping noted "DEFERRED: UTL 3-tier coverage is
   separate scope". Ship that now: add tests in `unified-trading-library/tests/` for the 3-tier kill switch helpers (if
   separate from service-side). Done-def: UTL QG green + coverage target met.
2. **pnl-attribution-service Cluster B follow-up audit** — slot 6 shipped pnl-attribution-service@9f3379f yesterday
   (C901 noqa + extract). Verify QG green + audit for any remaining Cluster B items. If clean: stand down on this item.
3. **Phase 6.7 risk_state BLOCK_CRITICAL gate coverage** — risk-and-exposure-service@df4849f shipped earlier this week.
   Add coverage tests: (a) state transitions trigger BLOCK_CRITICAL, (b) emission policy STRICT_FAIL fires correctly,
   (c) deactivation re-arms. Done-def: BLOCK_CRITICAL paths 100% covered.

### Reserve queue

- execution-service DeFi error classification taxonomy (13 DefiErrorCode entries — slot 6 mentioned as optional in their
  Final Wave; pick up if they didn't)
- pnl-attribution-service ARBITRAGE_PRICE_DISPERSION archetype bucket extensions (slot earlier added; may need test
  extensions)
- deployment-api SHARD_AXIS_MATRIX drift (if not closed by Ikenna slot 8)

### Coordination

- execution-service overlap with slot 4 (lifecycle) + slot 6 (custody) — coordinate file-level
- Phase 6.7 work overlaps with slot 8 (UTL emission publisher coverage)

---

## Slot 6 — Custody, Signing, UTL Coverage, Codex Audits

**Theme**: execution-service custody + UTL helpers + codex audits **Status at start of Day-1**: B-012 DONE ✅ + Cluster
A+B follow-on DONE ✅ + B-012 codex audit DONE ✅ (yesterday's full close-out).

### Day-1 queue

1. **codex audit — verify execution-service custody patterns are documented** — yesterday's codex audit was on
   `/codex/04-architecture/custody-providers.md` + `interface-credential-convention.md`. Extend: verify
   `/codex/04-architecture/flash-loan-receiver.md` + DeFi error classification taxonomy in codex are current vs shipped
   code. Done-def: codex docs reflect current code OR gaps filed as TODO.
2. **DeFi error classification coverage extension** — if slot 5 didn't take this from reserve: 13 DefiErrorCode entries
   (`unified_api_contracts.canonical.crosscutting.errors.defi`). Verify each has test coverage in execution-service
   consumers (aave.py, etc.). Done-def: each DefiErrorCode has a test exercising FAIL/RETRY/SKIP routing.
3. **UTL legacy_reason_classifier extension** — yesterday's UTL work shipped `e75bb0d` (PLAYER_VALUES cadence). Audit:
   are all `EmptyConfirmedReason` taxonomy entries handled in legacy_reason_classifier? Done-def: every reason in the
   enum has classifier coverage.

### Reserve queue

- UAC ×→x cleanup (if any new RUF003 occurrences crept in — slot 6 shipped UAC@046f9d6 for 2 remaining yesterday)
- codex/06-coding-standards/ doc currency (any new pattern from Phase 8 work)
- UTL test coverage for new helpers (signing helpers if not at parity with execution-service custody)

### Coordination

- execution-service overlap with slot 4 + slot 5 — coordinate file-level
- UAC overlap with Ikenna side primary — check `_agent_pings.md` before touching UAC

---

## Slot 7 — Deployment API + UI + Phase 4 Cron Infra

**Theme**: deploy-readiness + Phase 4 snapshot infra **Status at start of Day-4**: B-018 ✅ (Phase 4.A snapshot live;
36/36 repos in `quality_gates_snapshot/`) + B-013 ✅ + Wave 4 carry-forward ✅ + SHARD_AXIS_MATRIX shipped
(`deployment-api@40f7769`).

### Day-4 queue (verified open as of 2026-05-15 morning)

1. **B-018 Phase 4.A monitoring + alerting hook** — alerting hook if `snapshot.sh` fails for N consecutive days. Wire
   into `alerting-service` (use existing emission policy). Done-def: ALERT_CODE for stale-snapshot defined in UAC;
   integration test fires; ping flowing through alerting-service.
2. **deployment-ui "last snapshot age" badge** — UI badge per repo showing freshness of QG snapshot. Reads from parquet
   metadata in `gs://central-element-323112-deployment-events/quality_gates_snapshot/`. Done-def: badge renders + pnpm
   build green + vitest green.
3. **honest_coverage UI badge** (paired with slot 2's cron VM work) — once slot 2 ships the cron VM, deployment-ui needs
   the matching "last honest-coverage update" badge in data-status view. Read from
   `gs://central-element-323112-honest-coverage/{date}/coverage.json`. Done-def: badge in data-status UI + smoke green
   via deployment-stack.
4. **Phase 4.B downstream items** — `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 4.B.
   Check plan for unflipped checkboxes. Done-def: Phase 4.B items shipped OR explicit DEFERRED annotation.

### Reserve queue

- deployment-ui vitest coverage extensions (cross_asset filter buttons, DeployMissingButton edge cases)
- client-reporting-api coverage (DEFERRED until client data backfill lands; no action today)
- Cloud Scheduler trigger SSOT consolidation (audit drift between `deployment-service/scripts/vm/` triggers + PM
  scripts)

### Coordination

- **Slot 2 pairs on honest_coverage cron VM** — slot 2 owns the VM launcher half; you own UI badge + endpoint
  integration
- deployment-service overlap with slot 2 (VM infra) — coordinate launcher file-level
- deployment-api/ui pair almost always yours

---

## Slot 8 — UTL Coverage + QG Ratchet Rollout + Meta-QG

**Theme**: UTL + base-service.sh + STEP rollouts **Status at start of Day-4**: B-007+B-008 ✅ (UTL manifest writer +
emission publisher 100% coverage @e6877d2) + Tab 3 L2 fix-batch ✅. **B-014 partial**: STEP 5.79-5.82 added to
base-service.sh + 13/15 service repos QG stub pushed to LDR. **7 stashes uncommitted in `.tabs/8/<repo>/`** for final 2
repos + 5 more that took newer template version.

### Day-4 queue (verified open as of 2026-05-15 morning)

1. **🚨 B-014 STASH RECOVERY (priority 1)** — 7 stashes preserved during this morning's worktree reset, all tagged
   `pre-reset-2026-05-15 slot-8 B-014-ROLLOUT-COMPLETION`. Affected repos: `features-service` · `ibkr-gateway-infra` ·
   `market-data-processing-service` · `ml-inference-service` · `ml-training-service` · `system-integration-tests` ·
   `unified-trading-system-ui`. For each:
   ```bash
   cd /home/hk/unified-trading-system-repos/.tabs/8/<repo>
   git stash list | grep "B-014-ROLLOUT-COMPLETION"   # confirm stash present
   git stash pop                                       # restore changes
   git diff scripts/quality-gates.sh                   # verify: MIN_COVERAGE=70 + new SSOT path + instruction block
   bash scripts/quality-gates.sh                       # confirm QG green with new template
   bash scripts/quickmerge.sh "feat(qg): B-014 rollout completion to <repo>" --agent
   ```
   Done-def: all 7 repos shipped quality-gates.sh template upgrade + QG green + stashes dropped.
2. **B-014 final 2-of-15 verification** — yesterday's rollout left 2 repos un-propagated. After stash recovery (above),
   audit which service repos still don't have the new template version. Use:
   ```bash
   for repo in /home/hk/unified-trading-system-repos/*/scripts/quality-gates.sh; do
     grep -L "MIN_COVERAGE=70" "$repo" 2>/dev/null
   done
   ```
   Propagate via `bash unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py` to any remaining.
   Done-def: all 15 service repos at template version with `MIN_COVERAGE=70` + `SSOT: unified-trading-pm/codex/...`
   path; full workspace QG green; `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` Phase 3
   checkbox flipped with final SHAs.
3. **codex_vs_citadel audit follow-up** — Ikenna slot 8 owns the audit umbrella, Harsh-side surfaces need verification.
   Read `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`. Verify Harsh-side codex sections (UTL,
   deployment-service template, Phase 8 surfaces) are aligned with shipped code. File issue doc for any drift.
4. **UTL emission publisher consumer-side coverage audit** — yesterday's B-008 hit 100% on `emission_publisher.py`.
   Audit `publish_with_policy` callsites across consumer services (execution, risk, strategy, features). Are all
   consumer-side patterns tested? Done-def: callsite map filed OR gaps fixed.

### Reserve queue

- /codex/06-coding-standards/quality-gates.md updates (document new STEP 5.79-5.82 + UAC carveouts)
- batch_live_symmetry follow-on (L4/L5/L6 sweeps if Ikenna slot 5 punted)
- base-service.sh template DRY (consolidate common patterns)

### Coordination

- **CRITICAL**: B-014 stash recovery touches 7 different repos. Coordinate via ping ledger if any conflict arises (e.g.,
  Ikenna's slot 8 also touching system-integration-tests or features-service)
- UTL overlap with slot 4 (test utils) + slot 6 (helpers) — coordinate file-level
- **DO NOT use `git stash drop` until quickmerge ships** — preserve recovery path

---

## Slot 9 — MTDS + PBM + DeFi Carry Backtest

**Theme**: MTDS + PBM + DeFi carry paper backtest (B-015 half) **Status at start of Day-4**: 🛑 B-015 STILL BLOCKED —
Ikenna posted update @02:00 UTC 2026-05-15: smoke VMs from yesterday FAILED SILENTLY (phantom manifest rows skipped both
write paths; ZERO data written to GCS). Issue doc:
`plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md`. Ikenna slot 8 owns phantom-clear
(`reconcile_phantom_manifest_rows_all.py --asset-group DEFI --apply-flips`) + re-smoke.

### Day-4 queue (verified open as of 2026-05-15 morning)

1. **🛑 HOLD B-015 Phase 2 launch** — DO NOT re-launch VMs until Ikenna slot 8 pings phantom-fix DONE + green re-smoke.
   Poll `plans/active/_agent_pings.md` every ~30 min for Ikenna's resolution ping; auto-poll will alert when it lands.
   **Until then, your primary work is items 2-4 below**. When phantom-fix DONE pings → immediately verify smoke green
   via event stream → launch Phase 2 → ping STARTED-Phase-2.
2. **MTDS UAC facade migration audit** — yesterday's `mtds@1b62d0f` + `@05aaeaa` shipped UAC facade migration. Audit for
   any remaining deep-imports across all MTDS handlers (grep for `from market_tick_data_service.unified_api_contracts`
   deep paths). Done-def: 0 deep-imports + MTDS QG green.
3. **MTDS Solana Helius RPC integration tests** — `mtds@05b705a` shipped Helius wiring as part of Ikenna slot 3's perp
   venue adapters work. Add Harsh-side integration tests: (a) Helius adapter happy-path; (b) rate-limit handling (429
   response); (c) fallback to alternative provider; (d) `SOLANA_RPC_PROVIDER` env var toggle. Done-def: 4+ tests + MTDS
   QG green.
4. **MTDS handler readiness audit for DeFi backtests** — given B-015 phantom issue surfaced lst*rates data-correctness
   gap, audit \_all* MTDS DeFi handlers for similar phantom risk: lst_rates, evm_defi, gas_fee, solana_defi,
   eigenlayer_rewards. For each: verify (a) latest write date matches expectation, (b) manifest rows match parquet rows
   (no phantoms). Done-def: audit report ping with findings; new issue docs if phantoms found beyond lst_rates.

### Reserve queue

- PBM Phase 8 coverage extensions
- MTDS handler additions for new venues (post-Solana plan progression by Ikenna slot 3)
- DeFi data-pipeline gap reporting (you're the natural slot for this — keep monitoring)

### Coordination

- **CRITICAL handoff**: when Ikenna slot 8 pings phantom-fix DONE, drop everything else, verify re-smoke green, launch
  B-015 Phase 2
- B-015 directly paired with slot 3's B-016 — but B-016 NOT BLOCKED by phantom issue (CeFi features bucket); coordinate
  timing differences
- MTDS overlap with slot 4 (test failures) — coordinate if slot 4 picks up MTDS items

---

## Today's high-level priorities (cycle Day-4 closeout)

In order of importance for the May-23 cutover:

1. **Slot 3 launches B-016 Phase 2** (DeFi APD paper backtest) — has been blocked, now unblocked; this is the FIRST DeFi
   paper backtest to go live, critical-path for cutover validation.
2. **Slot 8 completes B-014 rollout** (stash recovery + final 2 repos + QG green workspace-wide) — Phase 3 ratchet is
   the last cross-cutting deployment infra item before cutover.
3. **Slot 2 ships honest_coverage cron VM** — closes the 404 endpoint gap slot 7 found yesterday; needed for cutover-day
   data-status visibility.
4. **Slot 9 holds B-015 + audits DeFi handlers for phantom risk** — preemptively check other MTDS DeFi handlers (not
   just lst_rates) for the same phantom-manifest issue.
5. **Slots 4, 5, 6, 7 ship Phase 8 coverage extensions** — kill-switch UTL, DeFi error classification, lifecycle
   coverage, Phase 4.B + alerting hooks.

## EOD pattern (Day-4 = cycle close)

Today is Day-4 of the 4-day Harsh density-push cycle. EOD action:

1. Each slot writes a "🏁 Slot N Day-4 CYCLE-CLOSE" ping summarising the full 4-day cycle:
   - Items shipped (per day, with SHAs)
   - Items deferred (with reason + successor — if no successor, escalate to operator)
   - Open BLOCKERs at cycle close
2. Main writes ONE cycle-close scoreboard block in LEDGER + ARCHIVES this `continuation_prompts_harsh_2026_05_15.md` to
   `plans/archive/` with cycle-close annotations.
3. Main + Ikenna cross-side close coordination (Ikenna's cycle also closes today): align next-cycle scope via cross-side
   ping.
4. Auto-poll continues overnight to catch any late commits.
5. Next cycle (Day-1) starts 2026-05-16 — new `continuation_prompts_harsh_2026_05_16.md` will be written by main from
   refreshed BACKLOG + cycle-close findings.

## Status at adoption (2026-05-15 04:00 UTC)

- [x] THEMATIC_CLUSTERS.md reviewed — slot themes match expectation
- [x] continuation_prompts (this doc) verified against current LDR + cross-side ledger
- [x] `bash scripts/agents/harsh_auto_poll.sh --watch` running in background (PID 80423, log: /tmp/harsh_auto_poll.log)
- [x] All 8 slot worktrees `--reset-slot` clean to LDR; B-014 work preserved in 7 stashes (slot 8 recovers)
- [x] Day-4 START pings dropped to all 8 slot ping files (this morning @04:18 UTC, then refreshed @04:26)
- [x] ✅ Operator opens 8 Claude Code tabs in `.tabs/<N>/unified-trading-pm/` + pastes 1-line spawn prompt (backfilled
      2026-05-19 — workers are actively running as evidenced by slot-2 session executing plan closes)
