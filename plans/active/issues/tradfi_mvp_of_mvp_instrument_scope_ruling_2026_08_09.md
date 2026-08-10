---
doc_type: issue
title:
  TradFi "MVP-of-the-MVP" instrument scope ruling — narrowed immediate backfill target, rest gated until November 2026
summary: >-
  Operator ruling 2026-08-09: rather than complete all 6 tradfi MVP cells to 100% right now, immediate backfill work is
  narrowed to exactly the instruments needed for the equities-vs-perps basis strategy (Binance-listed equity perps
  launched 2026), **plus the macro/USD-strength backdrop instruments** (CBOE Treasury yield-curve INDEX, FRED macro
  series, KRW/USD, DXY) added by the 2026-08-09 (later same day) follow-up ruling below. Completing the REST of the
  tradfi MVP universe (full-history equities beyond 2026, CME Treasury BOND FUTURES ZN/ZB/ZF/ZT, VIX futures) to 100% is
  explicitly GATED until November 2026 — no plan/todo should drive that broader work before then. This doc is the SSOT
  other tradfi plans point to; it supersedes the "MVP universe" framing in `tradfi_consolidated_closeout_2026_07_18.md`
  for near-term dispatch purposes only (that doc's full 6-cell definition stays valid as the eventual November target,
  it is not rewritten).
status: open
nature: process
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, mvp-scope, instrument-scope, operator-decision, backfill, november-gate]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
  ]
created: 2026-08-09
author: claude-code (interactive session, operator-directed 2026-08-09)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    "Operator chat instruction, 2026-08-09: narrowed scope to (1) MVP equities OHLCV_1m, year 2026 only — Binance listed
    equity perps this year, that is the main strategy being tested (equities-vs-perps basis); (2) Korean stocks —
    OHLCV_24h from Yahoo Finance as a proxy only, no intraday; (3) S&P 500 — the full 6.5-year OHLCV_1m for both futures
    (ES) AND options (ES options); (4) BTC futures, ETH futures (CME), and BTC/ETH spot ETFs (equities). Completing the
    rest of the tradfi MVP universe to 100% is gated until November. Operator: 'to start with, really as a starting
    point we just need the year 2026 ... for korean stocks we just need ohlcv 24h from yahoo finance as a proxy ... for
    s&p 500 year we want the 6.5 year ohlcv_1m futures and options ... we also need btc futures eth futures and btc and
    eth etfs.'",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [/plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
drift_direction: advance-code
depends_on: []
---

# TradFi "MVP-of-the-MVP" instrument scope ruling

## In scope — proceed now

| Cell                                                                                             | Scope                                                | Data type                | Source                   |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ------------------------ | ------------------------ |
| Delta-one single-stock equities                                                                  | **Year 2026 only** (not the full multi-year history) | `ohlcv_1m`               | Databento (`DBEQ.BASIC`) |
| Korean stocks (KRX)                                                                              | Daily proxy only, no intraday                        | `ohlcv_24h`              | Yahoo Finance            |
| S&P 500 futures (ES)                                                                             | Full 6.5-year history (2020-01-01 → now)             | `ohlcv_1m`               | Databento (`GLBX.MDP3`)  |
| S&P 500 options (ES options)                                                                     | Full 6.5-year history (2020-01-01 → now)             | `ohlcv_1m`               | Databento (`GLBX.MDP3`)  |
| CME BTC/ETH futures (BTC, ETH, MBT, MET)                                                         | Full history                                         | `ohlcv_1m`               | Databento (`GLBX.MDP3`)  |
| BTC/ETH spot ETFs (e.g. IBIT, ETHA)                                                              | Full history                                         | `ohlcv_1m`               | Databento (`DBEQ.BASIC`) |
| CBOE Treasury yield-curve INDEX (US3M/US2Y/US5Y/US10Y/US30Y)                                     | Full history                                         | `ohlcv_24h`              | Yahoo Finance            |
| Macro series (UST curve, TIPS, FedFunds/SOFR, CPI, breakevens, GDP, UNRATE, VIXCLS — ~25 series) | Full history from 2018                               | `yield_curve`/`ohlcv_1d` | FRED                     |
| KRW/USD spot (FX)                                                                                | Full history                                         | `ohlcv_24h`              | Yahoo Finance            |
| DXY (US Dollar Index)                                                                            | Full history                                         | `ohlcv_24h`              | Yahoo Finance            |

**Rationale**: Binance listed single-stock equity perps in 2026 — the equities-vs-perps basis strategy this is meant to
feed only needs 2026-forward equities data to test against. S&P futures+options get the full window because the
strategy's price-arb/ML backtest (`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`) explicitly runs a
2020-2026 train/test split. BTC/ETH futures+ETFs are the crypto-adjacent legs of the same basis family.

**Rationale — macro/USD-strength backdrop, added 2026-08-09 (same day follow-up)**: operator ruling — the CBOE Treasury
yield-curve INDEX, the FRED macro series, KRW/USD, and DXY are macro/rates/USD-strength context instruments for the same
basis strategy, sourced via Yahoo Finance / FRED (i.e. **not gated by the Databento billing question at all** — see
"Relationship to the Databento billing-suspension issue" below). Treasuries here means **FRED ∪ Yahoo, union of both
sources** (not either/or) — FRED and the CBOE-Yahoo yield-curve index are two distinct, already-real pipelines (see
"Known relaunch gotchas" for the distinction other docs conflate). CME Treasury **bond futures** (ZN/ZB/ZF/ZT) are a
third, separate Treasury surface (same Databento/CME venue as ES) — operator ruling 2026-08-09: **stays deferred to
November**, not part of this in-scope list; do not confuse it with the now-in-scope CBOE yield-curve INDEX above.

## Out of scope — gated until November 2026

Everything else in the 6-cell tradfi MVP universe (`tradfi_consolidated_closeout_2026_07_18.md` § "MVP universe"):

- Delta-one single-stock equities for years **other than 2026** (i.e. completing the full historical equities corpus to
  100%).
- CME Treasury **bond futures** (ZN/ZB/ZF/ZT, Databento `GLBX.MDP3`) — distinct from the now-in-scope CBOE Treasury
  yield-curve INDEX (Yahoo `ohlcv_24h`) above; registered + launcher-ready today (`CME_ROOTS` already has them) but not
  MVP-tagged in `/codex/02-data/mvp-scope-canonical.md`'s underlier set — deferred, operator ruling 2026-08-09.
- VIX FUTURE (CBOE).
- Any FX/commodity futures backfill not named above (the currently-running `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` fleet —
  6A/6B/6C/6E/6J/6L currency futures, 6M/CL/CT/HG commodities — is **entirely out of this scope** and is being killed,
  not relaunched, per this ruling).

**No plan/todo should dispatch backfill work for the out-of-scope list before November 2026.** If a worker or an
autonomous session (e.g. `wave_launcher.py`'s gap-driven dispatch) would otherwise pick up one of these cells, treat it
as `BLOCKED-OPERATOR-DECISION` citing this doc, not as ready work.

## Relationship to the Databento billing-suspension issue

`/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` gated several of these same todos
(ES_OPT launch, MVP backfill readiness gate) on 2026-08-09 pending confirmation the vendor account wasn't suspended.
That was independently live-verified the same day — direct calls to Databento's `metadata.list_datasets` and a live
`ES.FUT ohlcv-1m` pull both succeeded — so the billing gate is lifted specifically for the in-scope items above (this
doc's scope list). The billing issue doc itself stays open as a standing awareness record; it no longer blocks the
in-scope relaunch this doc authorizes.

## Known relaunch gotchas (carry forward, don't re-discover)

- `wave_launcher.py`'s dedup check (`running_cell_keys`) parses live VM names for a `root` group label and never matches
  the per-single-root dispatch candidate keys it computes internally for CME — this is why the FX/commodity fleet
  duplicated 3-13x per shard. Any relaunch of the in-scope CME cells (ES, BTC/ETH futures) must not reuse
  `wave_launcher.py` blind — either fix the key mismatch first, or launch directly via
  `launch-tradfi-bf-cme-ohlcv-1m.sh` / `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` per-shard with a manual "is a VM already
  running for this shard" check.
- ES ohlcv_1m capture has a real, confirmed (not vendor-side) gap May-December every year 2020-2026 — live-verified
  against Databento directly. Relaunching ES needs `--force`/`VM_FORCE=true` semantics that don't just skip on a false
  "already captured" read for those months, since the manifest's own `NO_INPUT_AVAILABLE` classification there is wrong.
- **DXY has no backfill launcher today** — `launch-tradfi-bf-ice-ohlcv-1m.sh` is unrelated dead Databento scaffolding
  (Brent/Gasoil/Sugar futures, `ICE_ROOTS=()` deliberately empty). A new small launcher is needed, templated off
  `launch-tradfi-bf-fx-ohlcv-24h.sh` / `launch-tradfi-bf-cboe-indices-ohlcv-24h.sh` (source
  `_tradfi-ohlcv-launcher-lib.sh`, `VM_VENUE=ICE`, `ohlcv_24h`, no `--source` needed — Yahoo, not Databento).
- **None of the 4 new cells are `wave_launcher.py`-auto-dispatched.** `LAUNCHER_FOR_VENUE` only drives
  CME/CBOE/NASDAQ/NYSE (FX/ICE/KRX excluded by design, `wave_launcher.py:19-40` docstring), and `VENUE_DATA_TYPES` is
  empty so `ohlcv_24h` is never addressable regardless of venue (FX entry removed 2026-06-30, commit `b38dbff8`,
  "descope FX from tradfi wave-launcher" — reason not re-investigated here). The Treasury-INDEX, FRED, KRW/USD, and
  (once it exists) DXY backfills all need **manual** launcher invocation, same as the existing FX pattern — do not
  assume registering an instrument makes it auto-dispatch.
- **FRED backfill likely already ran** — `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` records
  the FRED macro backfill launched and verified 2026-07-30 (`tradfi-bf-fred-full-*`). Check the manifest for actual
  coverage before re-launching; this may already be a completeness-verify task, not a fresh backfill.

## Disposition of currently-running infra (2026-08-09)

167 `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` VMs were running at the time of this ruling, 100% out of the scope above
(FX/commodity futures) and massively duplicated (up to 13 concurrent VMs per shard, see above). Disposition: killed, not
resumed. See Progress Log below for the kill + scoped-relaunch record.

## Todos

- [x] ✅ [SCRIPT] P1. **RECURRENCE CONFIRMED LIVE A SECOND TIME (2026-08-09, later same day)** — was not fixed as of
      that check. Fix `wave_launcher.py`'s `running_cell_keys` dedup check so it matches the per-single-root CME
      dispatch candidate keys it computes internally, instead of only matching a VM-name-parsed "root group" label —
      currently causes CME launches to duplicate 3-13x per shard (measured: 167 stray VMs from one erroneous wave, per
      "Disposition of currently-running infra" above). **Confirmed AGAIN live** (instrument-scope-diff session,
      2026-08-09): `-eth-eth-     2022-*` and `-met-met-2023-*` were each observed running as TWO separate VMs ~3h apart
      for the identical shard — killed the newer (redundant) instance of each pair as a stopgap
      (`gcloud compute instances delete`, `asia-northeast1-c`), keeping the earlier-started original. **FIXED 2026-08-09
      (round-9 combined RECLASSIFY + satellite-extraction sweep, found already-shipped by a concurrent session)**:
      `deployment-service@bcf55c781f98f3834298252c443ed5ffa6f42a35` ("fix(tradfi): CME --only-root VMs get a plain
      single-root name, closing the wave-launcher dedup gap", slot-4·laptop, 2026-08-09T10:24:07+01:00) — the fix is on
      the LAUNCHER side, not `wave_launcher.py` itself: `launch-tradfi-bf-cme-ohlcv-1m.sh`'s single-root mode now names
      the VM `tradfi-bf-cme-ohlcv-1m-${root}-${year}-${run_ts}` (no `g${idx}-${first}-${last}` bundling artifact) so
      `wave_launcher.py`'s existing `_VM_NAME_RE`/`running_cell_keys` regex parses the clean root string correctly and
      recognizes a running single-root VM as covering its candidate — closing the gap without needing to touch
      `wave_launcher.py` itself. Verified `git merge-base --is-ancestor bcf55c781... origin/live-defi-rollout` = YES
      (real ancestor, not a local-only peer commit).
- [ ] [SCRIPT] P1. **NEW (2026-08-09)** — confirm `wave_launcher.py`'s ACTUAL production deployment mechanism and that
      it has picked up `deployment-service@bcf55c781` (the dedup fix above). The module's own docstring says it runs as
      a "Cloud Run Job + Scheduler (every 2-3h)" (implying a built container image, needing an explicit rebuild to pick
      up new code), but `_write_last_run_sentinel`'s comment says it runs as a "HOST cron... on the monitor host"
      (implying a live git checkout that would pick up the fix on its next `git pull`) — these two descriptions of the
      SAME script are in tension and were not reconciled this session. Done when: the actual invocation mechanism is
      confirmed (Cloud Build/Cloud Run Job config vs. a host crontab entry), and — if it's an image-based Cloud Run Job
      — either a redeploy has run or one is explicitly triggered. Until confirmed, do not assume the CME duplicate-VM
      recurrence has actually stopped in production, only that the code fix is correct and shipped.
- [x] ✅ [DATA] P1. **NEW FINDING (2026-08-09)** — `tradfi-bf-nyse-ohlcv-1m-2023-d01-*` was observed RUNNING live,
      violating the "equities = 2026 ONLY" scope. **Resolved itself** — by the instrument-scope-diff session
      (2026-08-09, several hours later), this VM was no longer running (self-deleted on completion or reaped; not
      independently confirmed which). No action needed on this specific instance, but the underlying gap —
      `wave_launcher.py`'s gap-driven scan is scope-blind, it only reads "is this cell a manifest gap," not this doc's
      ruling — is UNCHANGED and will produce the same class of violation again on the next scan. Repo:
      deployment-service (`scripts/wave_launcher.py`).
- [x] ✅ [SCRIPT] P1. **NEW (2026-08-09 macro/USD backdrop addition)** — write a new DXY backfill launcher script,
      templated off `launch-tradfi-bf-fx-ohlcv-24h.sh` / `launch-tradfi-bf-cboe-indices-ohlcv-24h.sh`: source
      `_tradfi-ohlcv-launcher-lib.sh`, `VM_VENUE=ICE`, `ohlcv_24h`, no `--source` flag (Yahoo, not Databento). **Shipped
      `deployment-service@bd561d917`** — `scripts/vm/launch-tradfi-bf-ice-ohlcv-24h.sh` + registry entries in
      `launcher_registry.py`/`vm_prefix_registry.py` (preemption relaunch + bucket classification) + regression test in
      `test_launcher_registry.py`. Dry-run verified. QG green.
- [x] ✅ [SCRIPT] P2. **NEW (2026-08-09)** — add `("ICE", "INDEX", "DXY")` to `extra_mvp_cells` in UAC's
      `unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py` so DXY counts toward the tradfi MVP
      completeness denominator. **Shipped `unified-api-contracts@e6c66c382`** — `MVP_SCOPE_CONFIG_VERSION` bumped to 23,
      3 new/updated tests in `test_mvp_scope.py` (`test_ice_index_dxy_is_mvp`, `test_ice_other_cells_not_swept_in`,
      `test_extra_mvp_cells_exact_membership` updated to 8-triple). QG green.
- [x] ✅ [DATA] P1. **NEW (2026-08-09)** — before launching anything: check the manifest for actual FRED coverage (the
      FRED macro backfill reportedly ran 2026-07-30 per
      `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` — this may already be a verify-only task).
      Then launch/verify full-history backfills for the CBOE Treasury yield-curve INDEX and KRW/USD (existing launchers,
      manual invocation per "Known relaunch gotchas"), and DXY once its launcher exists (todo above). **EXTRACTED
      2026-08-09 (round-9 combined RECLASSIFY + satellite-extraction sweep) →
      `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 (now `[x]` ✅, archived)** —
      all 4 cells are Yahoo/FRED-sourced, not gated by the open Databento billing-suspension issue; the DXY launcher
      shipped same-day (see todo above, now `[x]`). Completion recorded there. **(na-eligibility-audit 2026-08-10,
      tradfi tranche, dispatch agt-a70469): closing here too — this doc's own Progress Log (round-9 entry below) already
      confirmed this exact item done/archived elsewhere; the checkbox itself was never flipped to match.)**
- [x] ✅ [DOCS] P2. **NEW (2026-08-09)** — propagate this scope update to `/codex/02-data/mvp-scope-canonical.md`,
      `/codex/02-data/cross-asset-canonical-target-ssot.md`, and `/codex/09-strategy/mvp-universe-per-asset-group.md`.
      **Shipped `unified-trading-pm@d5d0b75cc` / `@22d0a07d0` / `@ecddf76ad`**. The closeout doc
      (`tradfi_consolidated_closeout_2026_07_18.md`) was deliberately NOT touched further — already over its 1000L hard
      cap from prior growth, no scoped-append exception applies to a content addition; its existing banner pointing at
      this doc is sufficient.
- [x] ✅ [SCRIPT] P2. **NEW (2026-08-09)** — add `("ICE", "ohlcv_24h")` to `_TRADFI_MVP_SHARDS` in
      `market-tick-data-service/scripts/pipeline_e2e_check.py:330-338` so the MTDS `--mvp-only` smoke test exercises DXY
      (Treasury-INDEX/CME and KRWUSD/FX cells are already covered in that hand-listed set). Repo:
      market-tick-data-service. **(na-eligibility-audit 2026-08-10, tradfi tranche, dispatch agt-a70469): confirmed
      LANDED — independently read `market-tick-data-service/scripts/pipeline_e2e_check.py` line 337 live on
      `origin/live-defi-rollout`:
      `("ICE", "ohlcv_24h"),  # daily DXY (US Dollar Index, Yahoo-sourced) -- added 2026-08-09 scope ruling` is present
      in the `_TRADFI_MVP_SHARDS` frozenset. Missed flip, closing.)**
- [x] ✅ [SCRIPT] P3. **NEW (2026-08-09)** — add `IBIT`/`ETHA` to `_DEFAULT_TICKERS` in
      `features-service/features_service/calendar/cli/handlers/corporate_actions_handler.py:52-75` so the
      corporate-actions (dividends/splits/earnings) sweep covers the newly-in-scope BTC/ETH spot ETFs — the production
      sharding config doesn't pass `--tickers`, so it silently falls through to this hardcoded default today. Repo:
      features-service. **(na-eligibility-audit 2026-08-10, tradfi tranche, dispatch agt-a70469): confirmed LANDED —
      independently read `features-service/features_service/calendar/cli/handlers/corporate_actions_handler.py` lines
      77-78 live on `origin/live-defi-rollout`: both `"IBIT"` and `"ETHA"` are present in `_DEFAULT_TICKERS`. Missed
      flip, closing.)**

## Progress Log

- 2026-08-09: doc created, scope ruling recorded. Sweep of tradfi plans/issues for regression risk against this scope in
  progress — see this doc's `related` list and the per-doc scope notes added to each.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:6648d0c11c478b7d]: **KEEP-NA,
  valid -- first audit, functioning correctly as an SSOT ruling doc.** A dedicated sub-agent hunter read this doc
  end-to-end plus cross-referenced its live consumers (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` -- both confirmed already citing this ruling correctly, same day).
  Converted the "Known relaunch gotchas" wave_launcher.py dedup-bug prose into a tracked `- [ ]` checkbox above (same
  finding, not new scope) -- kept KEEP-NA rather than RECLASSIFY despite it reading as a bounded code fix, because it
  touches live-dispatch-critical-path machinery (`wave_launcher.py`'s VM-launch dedup) that this pass did not itself
  directly read the code for; flagging as a RECLASSIFY candidate for a follow-up pass that reads `wave_launcher.py`
  directly rather than promoting on secondhand evidence alone. Separately noted (not this doc's to verdict):
  `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` reports a live, unresolved possible
  violation of this doc's "year 2026 only" scope contending for the same account-wide Databento lock as the authorized
  ES_OPT launch -- worth a prompt look by whoever owns tradfi triage today.
- **2026-08-09 (same day, follow-up ruling)**: operator asked for a canonical-vs-conflicting instrument-scope audit (4
  parallel research agents: doc landscape, backfill-script capability, instruments-service/UAC registry,
  MTDS/MDPS/features/reconciliation-skill dynamism). Findings: (1) DXY has a near-total documentation gap — shipped in
  code/features/one prior ruling (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`, 2026-06-25 operator ruling:
  "DXY canonical along with KRWUSD... not one-offs") but absent from this doc, the code-level `mvp-scope-canonical.md`,
  and the canonical-id SSOT. (2) This doc's own "Daily Treasuries (ohlcv_24h, FRED)" out-of-scope line conflated two
  distinct real pipelines — the Yahoo-sourced CBOE yield-curve INDEX and the separate FRED macro-series adapter —
  corrected below. (3) Operator ruling: Treasuries in scope = the yield-curve INDEX (FRED ∪ Yahoo, union of both), NOT
  the CME Treasury bond futures (ZN/ZB/ZF/ZT), which stay deferred to November. (4) KRWUSD and the yield-curve INDEX
  need zero new code (registered, MVP-tagged, launcher-ready) but are NOT `wave_launcher.py`-auto-dispatched (manual
  launch only, FX/ICE/`ohlcv_24h` excluded by design). DXY needs one new launcher script (genuine gap) + one UAC MVP-tag
  line. Added these 4 cells to "In scope", corrected the out-of-scope section, and filed 6 new tracked todos (launcher
  script, UAC MVP-tag, backfill launch/verify, codex doc propagation, MTDS smoke-test entry, features-service
  corp-actions ticker list).
- **2026-08-09 (same session, follow-through — shipped)**: 4 of the 6 todos filed above shipped this session:
  `deployment-service@bd561d917` (new DXY launcher + registry entries + test), `unified-api-contracts@e6c66c382` (DXY
  MVP-tag, config v23), `unified-trading-pm@d5d0b75cc`/`@22d0a07d0`/`@ecddf76ad` (3 codex docs), and the
  `data-pipeline-check-mtds` skill doc's own duplicate hand-list (`unified-trading-pm@86f6618df`) — a 4th mirror of the
  same `_TRADFI_MVP_SHARDS` hand-list found while checking whether MTDS/MDPS/features/reconciliation track scope
  dynamically (most do; this skill doc and MTDS's own smoke test are the two genuine hand-lists that needed the same
  edit). The MTDS `_TRADFI_MVP_SHARDS` code change and the features-service `_DEFAULT_TICKERS` change are written and
  QG'd; their quickmerges were in flight when this entry was written — check their own commits for final SHAs before
  assuming undone. Also converted the FRED backfill's day-by-day API-call-waste finding from prose to a tracked todo
  (`unified-trading-pm@5f813f854`) per operator pushback that "harmless duplication" undersold it. Separately,
  live-fleet-reconcile found the wave_launcher.py dedup bug recurring a SECOND time (killed the 2 redundant duplicate
  VMs as a stopgap, root cause still unfixed — see that todo above) and confirmed the out-of-scope NYSE-2023 VM had
  already resolved itself. ForexFactory econ-calendar scraper
  (`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`) checked per operator question: still
  `status: draft`, not in the catalogue, blocked on an unresolved Cloudflare-bypass design decision — left as-is,
  already correctly tracked.
- **round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09)**: re-read this doc end to end (2 remaining
  open todos). The `wave_launcher.py` CME dedup fix (todo 1, flagged by this doc's own earlier na-eligibility-audit
  entry as "a RECLASSIFY candidate for a follow-up pass that reads `wave_launcher.py` directly") was found ALREADY
  SHIPPED by a concurrent session (`deployment-service@bcf55c781`, confirmed ancestor of `origin/live-defi-rollout`) —
  flipped `[x]` with evidence above; the fix landed on the VM-naming side, not `wave_launcher.py` itself. The
  FRED/CBOE/KRW/DXY backfill-verify todo (todo 2) extracted into
  `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 (Yahoo/FRED-sourced, not
  Databento-billing-gated; now `[x]` ✅, archived). This doc stays `assigned_vm: NA` as an SSOT ruling doc — both
  remaining action items are now tracked/closed elsewhere.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:ac4c223a308148ee]: **KEEP-NA,
  stale-items fixed.** Fresh full read, 4 open items. Closed 3 this pass: todo "check FRED coverage, launch/verify
  CBOE/KRW/DXY" (this doc's own round-9 Progress Log entry above already confirmed it EXTRACTED + archived, checkbox
  simply never flipped to match); todo "add (ICE, ohlcv_24h) to `_TRADFI_MVP_SHARDS`" (independently confirmed LANDED
  via direct read of `market-tick-data-service/scripts/pipeline_e2e_check.py` line 337 live); todo "add IBIT/ETHA to
  `_DEFAULT_TICKERS`" (independently confirmed LANDED via direct read of
  `features-service/.../corporate_actions_handler.py` lines 77-78 live). Sole remaining open item (`wave_launcher.py`
  production-deployment-mechanism confirmation) is GENUINE_WORK, not promoted — matches this doc's established pattern
  of staying NA as an SSOT ruling doc, extract rather than self-dispatch. `assigned_vm` unchanged.
