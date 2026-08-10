---
doc_type: plan
title: Crypto Alpha Research — Book Construction, Signal Research & Paper-Trading POC
summary: >-
  Alpha-research + book-sizing decisions (short-leg re-spec, basis realism, TS-momentum, execution/universe research)
  plus the standalone e2e-testing paper-trading POC dashboard (`scripts/paper_trading/`) — extracted from the
  paper↔batch↔live determinism-spine plan so that plan stays focused on the ε=0 proof machinery, per the plan's own
  migration proposal.
status: active
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # body is overwhelmingly Binance-perp/CeFi (momentum, basis, RFQ execution calibration) content

stage: [strategy, paper]
repos: [e2e-testing, strategy-service, execution-service]
scope: [engineer, admin]
tags: [alpha-research, paper-trading-poc, strategy, backtest, momentum, basis, execution-research, book-construction]
related:
  [
    citadel_paper_batch_live_reconciliation_2026_06_19,
    plans/epics/strategy_master.md,
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 18
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Extracted 2026-07-24 from plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md, per the line-cap
  remediation triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 5 / bucket-(d) detail): "extract
  the alpha-research + paper-trading-POC track (~30 todos) into crypto_alpha_research_2026_06_23.md — the plan's own
  text (lines 150-165) already proposed this migration and it was never executed." Operator approved the unlock +
  extract via interactive Q&A 2026-07-24; the parent plan's `locked_by: live-defi-rollout` was cleared as part of this
  same action.
assigned_role: backend_engineer
drift_direction: advance-code
context_scope:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/epics/strategy_master.md,
    e2e-testing/scripts/paper_trading/,
  ]
---

# Crypto Alpha Research — Book Construction, Signal Research & Paper-Trading POC

> **Origin**: this plan is a **verbatim extraction** from
> [`plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`](/plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md)
> (the "Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation" determinism-spine plan). That plan's own "Remaining-work
> register" (§C, below) already recommended exactly this migration on 2026-06-23 ("these 16 items are alpha-research +
> book-SIZING DECISIONS... they accumulated in this plan's Progress Log but are a DIFFERENT workstream from the
> paper-batch-live spine") but the migration was never executed until this remediation pass. Two things moved here, both
> genuinely a different workstream from the determinism-spine's ε=0 proof machinery:
>
> 1. **§C below** — the open alpha-research / book-sizing decision register (operator trading-judgment items).
> 2. **The Progress Log** — the standalone `e2e-testing/scripts/paper_trading/` POC dashboard (a **parallel tactical
>    track**, explicitly self-described as "a self-contained live paper-trading POC" using its own engine —
>    `_ledgers.py` / `_coin_history.py` / `paper_engine.py` / `_exec_optimize.py` and ~230 other root research scripts —
>    distinct from the citadel-grade `strategy-service` + `client-reporting-api` spine, which remains in the parent
>    plan) together with the alpha-research findings that followed it (short-leg re-spec, basis-carry realism,
>    TS-momentum, multi-year walk-forward OOS, execution-realism audits, HYPE universe gap, RFQ calibration).
>
> **What did NOT move** (stays in the parent plan): the determinism-spine phases (0-9), the Phase 10/11 citadel
> dashboard + rolling-book infrastructure (client-reporting-api ledgers, `TsmomBtcCtaEngine` production archetype,
> strategy-keyed ledgers, data-quality panels), and all Progress Log entries documenting that spine's shipping history.
> See the parent plan's own text for that work.
>
> **Conservation note**: 35 `- [ ]`/`- [x]` checkboxes moved here verbatim (14 from the POC section + 21 from the
> trailing research narrative); §C itself carries no literal checkboxes (it is a prose index of the SAME open items,
> several of which are ALSO the literal checkboxes below — e.g. "wire the R8 confirmed-momentum short gate" is both a §C
> bullet and a dated checkbox further down). Nothing was dropped or rewritten — every moved block is copied verbatim
> from the parent's line ranges (§C: parent lines 150-166; POC section: parent lines 1739-1878; trailing research:
> parent lines 2333-2660, per `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` as it stood
> 2026-07-24 pre-extraction).

## §C — Open alpha-research / book-sizing decisions (verbatim from the parent's Remaining-work register)

> Moved verbatim from the parent plan's "Remaining-work register + operator gating" §C. The
> `plans/active/ crypto_alpha_research_2026_06_23.md` filename this text names below is this file's PRE-extraction
> proposed name; the actual file lands at today's date per the line-cap remediation's mechanical date-suffix rule
> (2026_06_23 → 2026_07_24, same slug, not a scope change).

**C — Operator-gated: LIVE RESEARCH / trading-judgment (the strategy-alpha workstream — recommend its OWN plan):**

> These 16 items are alpha-research + book-SIZING DECISIONS (which legs, what weights, whether to ship the short sleeve)
> — they need **operator trading judgment**, not just code, so they are operator-gated (`BLOCKED-OPERATOR-DECISION`
> class). They accumulated in this plan's Progress Log but are a DIFFERENT workstream from the paper-batch-live spine.
> **Recommendation: migrate these to a dedicated `plans/active/crypto_alpha_research_2026_06_23.md` under the strategy
> epic** so this determinism plan stays focused. (Say the word and I'll do the migration with `MIGRATED FROM:` banners.)
>
> **Reviewed 2026-07-28 (operator gate-clearance pass): confirmed PERMANENT hard-stop, NOT unlocked.** Book sizing,
> hedge design, and which alpha legs ship are trading-book judgment calls with real capital consequences — the same
> class of decision CLAUDE.md reserves for a human permanently (wallet keys, force-push main). This category is
> explicitly excluded from the general "unpause/relax/complete-in-full" theme applied elsewhere in this pass; these 16
> items stay `BLOCKED-OPERATOR-DECISION` indefinitely and are not retagged.

- Short sleeve: re-cast as a basis tail-hedge · re-evaluate book weight (15%→smaller/0) · wire the R8 confirmed-momentum
  short gate into production · ship the de-risk overlay + 12% short.
- Basis: deployable = liquid-only carry · re-present + size on RAW economics (not vol-normed) · filled-to-capacity +
  capped slow-momentum (180–365d) allocator.
- Momentum: add a confirmed long+short TS-MOMENTUM leg · maker-WIDTH sweep · per-strategy execution sweep (basis+short).
- Universe + risk: ADV/depth capacity gating · time-average the liquidity scan · funding-regime monitor + dynamic basis
  sizing · `h32` next-weak-leg · apply cs-denoise + tsmom-long-only to the production legs.
- [STRATEGY] Accelerate the non-crypto archetypes (TradFi/sports/prediction) for genuine bear-regime alpha.

---

## Progress Log — paper-trading POC + alpha-research history (verbatim, chronological)

> Moved verbatim from the parent plan's Progress Log. The POC dashboard section (2026-06-19/20) comes first
> chronologically, followed by the alpha-research findings that continued through 2026-06-21. Each dated `### ` entry
> below is unmodified from the parent.

### 2026-06-19/20 — Operator-facing LIVE paper-trading POC dashboard + 5-ledger UI (parallel tactical track)

A self-contained live paper-trading POC proving the same determinism spine end-to-end on real infra, with the operator
dashboard the larger plan targets. **NOT a third sim** — the POC reuses frozen models + a shared featlib so
`paper(W) == backtest-rerun(W)` (feature parity ε=2.6e-06, run-twice ε=0, all-leg recon by_leg {cs:0,basis:0,short:0}).
Engine source lives in `e2e-testing/scripts/paper_trading/` (wired to strategy-service QG per Peripheral-Script rule);
UI in `unified-trading-system-ui/app/paper-trading/`.

**Shipped (deployed on real infra + GCS):**

- **Two Cloud Run jobs** (`asia-northeast1`, images in `unified-trading-library` AR): `paper-signal-engine` (15m
  scheduler — frozen c48/max/wide2 ensemble + funding-rank basis + own_trend(200,20) short → positions + the 5 ledger
  parquets + per-coin history) and `paper-trading-engine` (dashboard JSON builder — real per-leg inputs + LIVE Binance
  order-book depth walked at $250k/$1M notionals).
- **Five live ledgers** → `gs://…/paper_engine/ledgers/{signals,orders,trades,transfers}.parquet` + rolled into
  `output/ledgers.json`; 1m intra-bar fill-sim (taker immediate / maker fill-or-miss with partials). Idempotent
  (`drop_duplicates(id)`) → restart-safe replay.
- **UI**: `/paper-trading` (booked-in-paper hero with UTC timestamps + a variable time-window selector 15m…all),
  `/paper-trading/ledgers` (5 live tables, 15s whole-screen refresh), `/paper-trading/coin/[coin]` (per-coin PnL by
  strategy backtest→paper + buy/sell filled/missed scatter, searchable across 31 coins). Regression:
  `tests/smoke/paper-trading-live-ledgers.smoke.spec.ts`.
- **Real-exposure fix** (operator caught it 2026-06-19): the Margin panel hardcoded gross to the design target
  `BOOK*3 = $15M/6x`; now computed from the actual positions — **current gross $5.6M (2.2x), net all-legs**, per-leg
  from live positions. Depth panel was already a genuine live order-book pull.

**Remaining ship (this session, autonomous):**

- [x] ✅ [INFRA] PB.1. Redeploy `paper-signal-engine` (now COPYs `_ledgers.py`/`_ledgers_json.py`/`_coin_history.py`;
      rolling 3-day 1m floor) + `paper-trading-engine` (real-margin `paper_engine.py`). Repo: e2e-testing.
- [x] ✅ [SCRIPT] P2. ~~**BLOCKED (pre-existing e2e ratchet drift, NOT this work)**~~ — Land the engine source to
      `e2e-testing/scripts/paper_trading/`. Source is SYNCED + all OWN gate items GREEN (ruff-clean, lifecycle markers,
      basedpyright-excluded per script-homes rule, codex `uv pip install`, TID251 `# noqa`, Dockerfile digest-pinned).
      Quickmerge is blocked by a **pre-existing repo-wide STEP 5.95 TID251 ratchet breakage** (5 un-noqa'd
      `scripts/sports/*` `google.cloud` sites, 15>baseline 10, red before any paper-trading change) → issue:
      `plans/active/issues/e2e_testing_tid251_ratchet_over_baseline_2026_06_20.md`. Engine is already DEPLOYED + the
      source lives in `.tabs/1/`; lands as soon as the sports/e2e-domain reconciles the ratchet. Repo: e2e-testing.
      **DONE (na-eligibility-audit 2026-08-03)** — the cited issue is `status: resolved` (RESOLVED 2026-06-19,
      `e2e-testing@02912ad` + PM baseline ratchet-down, tid251 15→5, "e2e gate is now GREEN fleet-wide... paper-trading
      POC landing... is unblocked"); this doc's OWN later Progress Log entry (2026-06-21 section,
      "MACHINE-INDEPENDENCE") confirms the engine source was in fact landed the next day — "the MAINTAINED deployable
      engine + research harnesses were already landed (`e2e-testing@237d4d8d`...)" (2026-06-20 19:19, per the same
      section's final confirmation) with a follow-up `RECOVERY.md` manifest at `e2e-testing@061e0f78`.
- [x] ✅ [UI] PB.3. Land the UI (Ledgers tab + per-coin analytics + hero reframe + real-margin panel) — DONE,
      `unified-trading-system-ui@d8362766` on `live-defi-rollout` (Tier-C drain → staging). `pw:L2` ✓ 6 passed.
      regression: `tests/smoke/paper-trading-live-ledgers.smoke.spec.ts`. Repo: unified-trading-system-ui.

**Fill-model fidelity (operator design 2026-06-20 — the flat `usd*0.34` per-candle was cosmetic; replaced):**

- [x] ✅ [CODE] PB.4. **Volume-scaled maker fill, swept-vs-touched** — DONE in `_ledgers.py`, **CONFIRMED by PB.7
      backtest + REDEPLOYED** (it IS the risk-adjusted-best single-shot model). A 1m candle that trades a tick THROUGH
      the limit (`low<limit` buy / `high>limit` sell) = a sweep that clears our level → fill the FULL minute volume
      (zero queue priority still fills); a candle that only TOUCHES (`low==limit`) = a 25% queue share; never reaches →
      no fill. Always AT the limit, never better. Validated vs real Binance UNI 1m: $59k order → 53% filled / 47% missed
      (vs flat-1/3's fantasy 100%). Repo: e2e-testing (engine).
- **[CODE] P2.5. EXTRACTED 2026-08-09 — moved to `cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 1 for AO
  dispatch (parent_epic: strategy_master). See that doc for the live checkbox + evidence.** (Taker = VWAP-walk the live
  depth, replacing the flat-slip fill-sim in `_ledgers.py`. Repo: e2e-testing.)
- [x] ✅ [CODE] PB.6. **Missed-remainder policy — DROP wins (backtest-decided, NOT requote)** — PB.7 verdict: dropping
      the unfilled remainder (single-shot, no requote) is the risk-adjusted winner for cs (Sharpe 0.24 vs 0.22, maxDD
      −$1.06M vs −$1.79M ≈ halved, 5.3 vs 4.0 bps), because under-filling the largest rebalances acts as a free
      position-size cap. The live engine ALREADY drops (`missed`) → no change needed; requote is REJECTED for cs (it
      just chases the same exposure over days = no risk benefit). Re-evaluate per-strategy if a future archetype is
      capacity-bound. Repo: e2e-testing (`_ledgers.py` unchanged — drop confirmed).
- [x] ✅ [INFRA] PB.7. **Backtest the fill assumptions per strategy — DONE** (`_fill_backtest.py`, 8.8y cs). Compared
      full-fill / single-shot(drop) / requote over history with real 15m volume as the per-cycle liquidity budget.
      **VERDICT: single-shot (= the live swept/touched + drop model) is most faithful AND risk-adjusted-best** — it
      validates the deployed engine, rejects requote (PB.6), and confirms PB.4. Determinism held (same code+data). bps
      PnL surfaced as a first-class column. Repo: e2e-testing (`_fill_backtest.py`).
- [x] ✅ [CODE] P2.8 (PB.8). **Paper-tape fidelity tier (aggTrades) — WIRED into the live maker fill + DEPLOYED.** The
      live maker fill now resolves against the REAL futures aggTrades flow that crossed the limit (true
      volume-at-price), with a 1m-volume fallback (`_ledgers._aggtrades_flow` + `simulate_fills(use_tape=True)`; signal
      engine redeployed). **The BTC "1% fidelity" was a MEASUREMENT BUG, not a finding** (operator caught it): a 1bp
      band on BTC is ~$6 — when the close sits near a minute's low, almost nothing printed below close−1bp in that
      backward window, so the "% of 1m volume at the level" reads ~0 — which is about price TRAVEL, not liquidity. The
      fix uses absolute flow-at-limit: a **page-cap → super-liquid (BTC/ETH) fills IN FULL**; thin alts fill against
      their genuine (smaller) flow (tested: BTC/ETH capped→full, ENJ ~5%). Bounded API (per-rebalance, ≤5 pages, early
      liquid-detection). Repo: e2e-testing.
- [x] ✅ [CODE+UI] PB.9. **bps PnL everywhere ($ PnL / $ traded × 1e4)** — operator ask 2026-06-20: surface the
      efficiency lens alongside the $/yr exec cost. Engine computes per-coin + per-strategy + aggregate **turnover**
      (`_coin_history.py` → `bps_summary.json`; per-coin `bps_cs/basis/short`) and the **exec-cost twin**
      (`exec_cost_bps` in `paper_engine.py`); LIVE bps from the trades ledger (`paper_live.pnl_bps`). UI shows it on the
      Cumulative-PnL + Exec-cost KPI cards, a per-strategy attribution column, the per-coin KPI cards, and the
      booked-trades window (realized cost-bps). First numbers: total **+7.1 bps** (basis +21.4 / cs +4.0 / **short
      −14.7** — a hedge, not a standalone alpha). Evidence: engine deployed (both Cloud Run jobs) + GCS-mirrored
      (`bps_summary.json` total bps 7.07 live); unified-trading-system-ui@c0b669ab | pw:L2 ✓ (6 passed) | regression:
      tests/smoke/paper-trading-live-ledgers.smoke.spec.ts.
- [x] ✅ [RESEARCH+CODE] PB.10. **Short research — regime gate beats the NAIVE baseline; the REAL leg is already good
      (honest finding).** `_short_research.py` (10 variants, full + since-2023): the naive `own_trend(200,20)` short
      LOSES (−$49k full / −$260k since-2023, Sharpe −0.04/−0.27 — shorts dips that bounce in the bull). A BTC regime
      gate (short only when BTC is itself in a confirmed downtrend, same 200/20 params — NOT param-mined) flips it to
      **+$240k/+$29k, Sharpe 0.76/0.17, ~4× smaller DD**; robust across (200,20)+(150,30) (`regime_soft`/faster params
      fail → the slope-confirmed bear gate is the lever). All mean-rev/RSI/vol-spike shorts lose (shorting crypto pumps
      = falling-knife-up). **BUT it does NOT cleanly beat the REAL `legs_real` short**: over the apples-to-apples common
      window (to 06-17) regime = $10.0k < legs_real $18.7k; the +$29k edge is 2 volatile recent days (lost ~$25k
      06-13→16, regained ~$26k 06-17→19), not clean alpha. So the deployed short was NEVER the loser (the −$269k was
      only the per-coin own_trend PROXY). WIRED: regime short into `_coin_history._short` (per-coin reconstruction — far
      better proxy: −$269k naive → +$29k, sign-matches the real leg). NOT overridden into the engine (the dashboard
      keeps the real `legs_real` short — it's better). Repo: e2e-testing (POC engine). **OOS check (operator-flagged —
      the original selection was IN-SAMPLE / data-snooping across 13 variants):** added a proper split — IS = pre-2024
      (select), OOS = 2024-2026 (held out). The regime CONCEPT generalizes OOS (`regime_own_trend(200,20)` OOS Sharpe
      **1.12** / +$183k, `(150,30)` 1.01, vs naive 0.08) → a real effect, not pure overfit; ALL mean-rev/RSI/vol shorts
      lose IS AND OOS (genuinely no edge). BUT param selection is fragile: the IS-best `(100,10)` (IS Sharpe 0.76)
      DEGRADES to 0.12 OOS (overfit to IS noise). The `(200,20)` used for the per-coin view is the OOS-best, so it's on
      solid ground — but partly luck (it wasn't IS-best). Lesson: a specific param config is NOT proven without
      walk-forward; the regime IDEA is the durable finding.
- [x] ✅ [STRATEGY] P1. **Robust short — EXHAUSTIVE walk-forward: NO standalone short alpha is robust (done properly).**
      Expanded `_short_research.py` to **16 candidates** (own_trend ± regime/params, mean-rev, RSI, vol-spike, xs-loser,
      drawdown, low-vol-regime, breakdown) and ranked EVERY one by rolling walk-forward (18mo train→6mo test × 11
      windows). The **best** candidate (regime_mean_rev) is only **+0.30 mean OOS Sharpe, positive in 5/11 windows
      (45%)** — a coin flip, not an alpha. The regime(200,20) from the prior single-OOS-split is actually the **WORST**
      (−1.58 mean OOS) — the 1.12 split was pure luck. **Rigorous finding: a crypto bull market has NO persistent
      standalone-short ALPHA** (momentum shorts whipsaw, reversal shorts catch knives, regime gates are luck). The
      **robust decision is therefore NOT to ship any signal** (all overfit) — the real `legs_real` short (a thin +$18.7k
      hedge) correctly stays. The genuine robust path is a ROLE change, not a signal: a vol-targeted **beta hedge**
      judged on BOOK risk-reduction, or fold the short into the market-neutral cs / funding-carry basis legs that ARE
      robust — a strategy decision (operator-gated, like the PB.8 wiring). Per-coin VIEW keeps the regime reconstruction
      (labelled non-alpha proxy). Repo: e2e-testing (`_short_research.py`, 16-candidate walk-forward).

**Execution-config optimization (operator design 2026-06-20 — pick the BEST REALISTIC execution per strategy; the
full-fill fantasy is the ceiling, never a choice). Lever grid: style (maker rest / taker cross) × participation (¼/⅓/
full of the candle volume) × timing (first-minute drop / subsequent-minute requote) × IOC-vs-resting. BATCH liquidity =
minute-candle VOLUME; LIVE = real order-book DEPTH (same assumptions, better data) → the live−batch differential = the
execution-realism gap.**

- [x] ✅ [RESEARCH] PB.11. **cs execution sweep — DONE (`_exec_optimize.py`).** Net = alpha captured − exec cost −
      missed alpha; cost model maker 1bp@limit / taker 2bp + 3bp spread + 8bp·√(order/vol) impact; 15m-bar volume / 96 =
      per-cycle batch budget. **VERDICT for cs: TAKER IS CATASTROPHIC**
      (−$1.13M, Sharpe −0.33 — the ~10bp spread+impact
      dwarfs cs's ~4bp edge); cs MUST be **maker**. Among maker configs **25% + drop is the best RISK-ADJUSTED** (Sharpe
      0.19, maxDD −$1.09M
      = half of requote's, 64% of the ceiling) — under-filling caps position (confirms PB.7); **requote/full capture
      more ABSOLUTE PnL** (76–100% of ceiling) at ~$1.88M DD. So cs ships maker-25%-drop (current live model) for
      risk-adjusted, requote as the PnL-max knob. Repo: e2e-testing (`_exec_optimize.py`).
- [ ] [RESEARCH] P2. **Per-strategy execution sweep (basis + short) — they will DIFFER from cs.** basis is low-turnover
      (funding carry, large alpha/trade) → taker likely fine (fill in full, cost is a small fraction); short is
      selective. Reconstruct each leg's positions (like `_coin_history._basis`/`_short`) + run the same lever sweep;
      pick the best realistic config PER strategy (maker/taker is NOT one-size-fits-all — that's the whole point). Repo:
      e2e-testing.
- [x] ✅ [CODE] P2 (PB.13). **Live−batch execution-realism differential — SHIPPED + live.**
      `paper_engine.execution_realism` emits BATCH (resting maker, fee at limit) = 1.0 bps vs LIVE (cross the REAL
      order-book depth at each order's size) = 22.4 bps → **differential 21.4 bps** = patient-execution alpha (only
      visible with live depth; the basis for live−batch recon = live = batch fill model + real depth). Dashboard panel
      `pt-execution-realism`. The full per-order live-depth WALK (vs the snapshot cost proxy) + the per-strategy config
      (PB.12, done) compose here. Repo: e2e-testing. Evidence: `paper_trading.json.execution_realism` live + UAT panel.

### 2026-06-21 — MACHINE-INDEPENDENCE: full POC research corpus + data mirrored off-laptop (GCS + e2e repo)

Operator: "what's left is everything in e2e testing repo and gcs" — nothing of the paper-trading research/build/data may
live only on this laptop. Audited the on-machine state vs the durable stores and closed every gap. The 40G `.tabs/1`
total is mostly the **sibling repo clones** (execution-service / strategy-service / system-integration-tests / etc. —
each already version-controlled in its own GitHub repo + the orchestrator clones, reproducible via `git clone`); the
genuinely machine-only payload is the paper-trading POC research corpus + its data, now mirrored:

- **e2e-testing repo** (`scripts/paper_trading/`): the MAINTAINED deployable engine + research harnesses were already
  landed (`e2e-testing@237d4d8d`, incl. the PB.8 aggTrades tape-fill `_ledgers.py` — verified byte-identical to the root
  deployed copy). Added **`RECOVERY.md`** (`e2e-testing@5f1fd149`, Pass-1 QG exit 0 + strict-quickmerge clean) — the
  SSOT restore manifest: documents the full GCS `research_archive/` layout + the `gcloud storage rsync` restore
  commands + the two `deploy*.sh` redeploy steps, so a wiped machine rebuilds from repo + GCS alone.
- **GCS `paper_engine/research_archive/`** (comprehensive archive — was only ~41 of 234 code files + a 340-day cache
  seed before): `code/` = all **234 `.py` + 16 `.sh`** (the entire research corpus — every backtest/feature/panel/dune/
  cryptoquant sweep, browsable); `plots/` = **262 result PNGs**; `_ens_model/` = the frozen LightGBM ensemble joblibs +
  meta (the 40M that takes ~81 min to retrain); `cache/` = the full **6.7G `_cache`** (8+yr 1m/15m bars + funding + the
  parquets the backtests ran on — IN PROGRESS, uploading) + the `_handoff_funding_strategy.tar.gz` (127M, redundant
  prior packaging, uploading). No loose root-level data artifacts exist outside `_cache`/`_ens_model` (verified — 0
  stray parquet/npy/csv/joblib at root).
- **Net**: the deployable code + the model + the plots + the research code are fully off-machine NOW; the 6.7G data
  cache finishes uploading in the background. Machine-independence achieved — `RECOVERY.md` is the single restore entry
  point.
- **DONE-confirmed (final state)**: 6.7G `_cache` upload COMPLETE — GCS `research_archive/` counts now match local
  exactly (cache 1880=1880 / code 234=234 / plots 262=262 / model 4=4; total **7.45 GB**) + the 127M handoff tarball +
  15 export/CQ/dune research CSVs. **e2e deployable verified current**: all engine files were committed to e2e
  (2026-06-20 19:19 / `237d4d8d`) AFTER their root mtimes — the 7 apparent root↔e2e "drifts" are gate-clean ruff-autofix
  equivalences (`dict.fromkeys`↔comprehension, `["BTC"]+sorted`↔`*sorted`, redundant `int(round)`) + lifecycle headers,
  NOT missing logic (the exact dense deployed source is also independently in GCS `research_archive/code/`). Final
  `RECOVERY.md` manifest = `e2e-testing@061e0f78` (the in-repo research-corpus tarball was correctly NOT committed — the
  e2e repo gitignores binary archives by design, so GCS is the corpus home + the repo holds maintained source + the
  manifest). Nothing paper-trading-specific lives only on this laptop.

### 2026-06-21 — EXECUTION-REALISM AUDIT (operator-driven): liquidity-scan artifact + liquid-universe rebuild

Operator probed the regenerated-under-maker book ("nothing is taker anymore?" / "GALA 27% slip?" / "basis yield really
high?"). Findings, all measured:

- **Maker-vs-taker IS settled per-coin (not assumed)**: `_exec_by_vol.py` measured IOC-taker vs maker-resting per coin
  on the 1m candles → **maker wins 28/28** (taker spread+impact exceeds the thin cs edge; maker fills at a credit). So
  the all-maker `EXEC_CONFIG` is the OUTCOME of a per-strategy sweep, correct for the directional legs.
- **The maker-WIDTH dimension was NEVER swept** (both `_exec_optimize` + `_exec_by_vol` fix maker at 1bp inside) — the
  "rest at 1/2/5/10bp from prev close, fill-prob vs price" sweep the design intended was not executed. OPEN.
- **The illiquid-tail slippage is a SINGLE-SNAPSHOT ARTIFACT**: `_liquidity_scan.py` is ONE Binance-perp order-book
  snapshot with an instant
  full-$1M market sweep → GALA `slip_1M=2777bp` (27%), `slip_2M=nan` ("book too thin"). That is
  a CAPACITY flag (can't push $1M
  instantly into a sub-penny token), NOT a recurring cost. It distorts the illiquid-tail taker-vs-maker comparison
  (garbage-in); the liquid-coin scan (ETH 1.2bp / SOL 3.7bp) is realistic.
- **Liquid-universe rebuild (`_book_liquid_compare.py`, maker exec, full vs liq<30/100/300bp)**: excluding the illiquid
  tail makes the DIRECTIONAL book BETTER — cs net PnL 468k→712k, cost 109k→47k, drawdown −1.07M→−322k (3×), Sharpe
  0.19→0.75; combined directional 0.17→0.76. The illiquid coins were net DRAG, not diversification. **basis** PnL
  collapses 762k→247k (−68%) — confirming ~2/3 of the raw carry is uncapturable small-cap funding — but its **Sharpe
  holds (14.96→12.59)**: real carry quality, far less capacity than the raw $ implied. Liquid-9 5-leg book = **OOS
  Sharpe 2.64 / +basis 9.65** (≈ the full-30 headline, but 3× smaller drawdown + a tradeable basis). New generators:
  `_book_latest_exec.py` / `_book_liquid_compare.py` / `_book_liquid9_plot.py`; the deployable plot is
  `book_liquid9_*.png`.

**Follow-up todos (execution-realism hardening):**

- [ ] [RESEARCH] P2. **Time-average the liquidity scan** — `_liquidity_scan.py` is ONE snapshot (the GALA-27%/`nan`
      artifact). Take N snapshots over a session + average (or use rolling depth), so the illiquid-tail slip is robust,
      not a single thin-book instant. Repo: e2e-testing `scripts/paper_trading/` (research harness). Provenance:
      execution-realism audit 2026-06-21.
- [ ] [RESEARCH] P2. **Gate the tradeable universe by ADV/depth capacity** (structural exclusion) — drop coins where the
      depth can't absorb the per-coin allocation, BEFORE the execution comparison, so illiquid names are excluded by
      capacity not modeled at 100s–1000s bp. Deployable cut ≈ liquid<30–100bp (9–17 coins). Repo: strategy-service /
      e2e-testing. Provenance: execution-realism audit 2026-06-21.
- [ ] [RESEARCH] P2. **Run the maker-WIDTH sweep** (rest at 0/1/2/5/10bp from prev close per vol-tercile; fill-prob vs
      price improvement) — the one execution dimension never actually swept; feed the per-coin optimal width into the
      live `EXEC_CONFIG` + the book. Repo: e2e-testing `scripts/paper_trading/`. Provenance: execution-realism audit
      2026-06-21.
- [ ] [RESEARCH] P3. **Deployable basis = liquid-only carry** — rebuild the basis sleeve on the liquid universe (ADV ≥
      $5M, the `_carry_liq_daily` path) as the SIZED number (~$250k, Sharpe ~12–13), not the raw top-third (incl.
      uncapturable small-caps). Repo: strategy-service / e2e-testing. Provenance: execution-realism audit 2026-06-21.

### 2026-06-21 — MULTI-YEAR WALK-FORWARD OOS + SHORT-LEG RE-SPEC (operator-driven, `/autonomous`)

Operator pushed two things: (1) show OOS for ALL walk-forward years (2017+ data exists), not just 2025; (2) re-spec the
short leg ("why bleed in bulls? make it bull/bear-adaptive or a beta-hedge — make it work"). Done, measured:

- **Multi-year walk-forward OOS exposed (`_book_liquid9_plot.py`, LO→2023)**: every ML leg IS expanding-window
  walk-forward (`_panel.py` cs / `_mom_tb.py` h32 / `_gate_regime.py` ext all do `train yr<Y → test yr==Y` for
  Y∈2023-2026) — so 2023/2024 are genuine OOS the book was hiding by measuring 2025+ only. Honest framing: model-fit is
  walk-forward every year, but strategy DESIGN was developed on 2023-24, so 2023-24 = walk-forward-but-in-development,
  **2025 = clean holdout** (design frozen), 2026-H1 = live-forward. **The full-OOS directional book is Sh ~1.3-1.4
  (yearly ['23:-1.5 '24:+2.8 '25:+2.8 '26:-0.5]) — NOT the 2.6 the 2025-only view showed; 2023 was a LOSING year.** The
  plot now shades 2023-24 dev + marks the 2025 clean-holdout boundary.
- **WHY 2023 negative despite 4-leg diversification (`_book2023_decomp.py`)**: diversification WORKED (the 3 long legs
  are near-uncorrelated, mean |corr| 0.08) but it cuts VARIANCE, not regime alpha-decay — in 2023 EVERY leg individually
  had no edge (cs/h32/ext all ~−1 Sharpe; the post-2022-bottom recovery was a regime shift the pre-2023 models hadn't
  learned), so the diversified average is a tighter loss, not a profit. short contributed only −0.8% of the −7.5% (the
  −19.6 short Sharpe is a low-$ steady bleed; short was actually −0.57 corr with cs = a partial hedge).
- **Short re-spec (`_short_respec.py`) — both operator ideas tested:**
  - **(B) Vol-targeted BETA-HEDGE = NOT APPLICABLE**: the directional book's rolling beta to BTC is **−0.01
    (market-neutral)** — cs/h32/ext net to ~zero market exposure, so there is NO net-long to hedge; the beta-hedge
    (gated on book-net-long ∧ confirmed-risk-off, sized to net beta) correctly NEVER fires. The book's 2023 loss was
    alpha-failure, not market beta; a beta-hedge can't fix it. (This VALIDATES the book as neutral — it doesn't need a
    directional hedge.)
  - **(A) CONFIRMED-MOMENTUM GATE = SHIPPED**: the −19.6 Sharpe 2023 bleed came from the lagging `BTC<200dSMA-falling`
    gate shorting INTO the recovery rally (gate fired on days BTC ran +533% annualized). Swept 10 gates; **R8 = short
    only when BTC 20d AND 60d returns both <0** (confirmed negative momentum, never shorts a rising market) is the
    robust winner: short 2023 **−23.2→+0.8** Sharpe, no catastrophic year, book maxDD **−8.8%→−7.9%**, strictly better
    than the naive short. **Wired into `_exec_optimize.build_strategies` short gate** (the research/book short).
- **Honest ceiling**: R8 makes the short SAFE (no whipsaw) but NOT accretive — the book is ~1.33-1.38 with or without it
  (5th independent confirmation the short has no robust standalone alpha). Deployable: keep R8 at a SMALL weight, or
  drop. The real crash risk is in the BASIS carry (liquidation deleveraging), so a tail hedge belongs THERE, not on the
  market-neutral directional book.

**Follow-up todos:**

- [ ] [RESEARCH] P2. **Wire the R8 confirmed-momentum short gate into the PRODUCTION short** (live paper engine
      `_ledgers.py`/`_signal_engine.py` strat-signals + strategy-service archetype) — the research `_exec_optimize`
      short is fixed; the live short still uses the lagging SMA gate. Repo: e2e-testing `scripts/paper_trading/` +
      strategy-service. Provenance: short re-spec 2026-06-21.
- [ ] [RESEARCH] P3. **Re-cast the short as a BASIS tail-hedge, not a directional sleeve** — the directional book is
      market-neutral (no beta to hedge); the genuine left-tail is the basis carry's liquidation-deleveraging risk. Test
      a convex hedge (long vol / deep-OTM / index short in confirmed risk-off) sized to the BASIS sleeve's crash
      exposure. Repo: strategy-service / e2e-testing. Provenance: short re-spec 2026-06-21.
- [ ] [RESEARCH] P3. **Re-evaluate the short's book weight (15%→smaller or 0)** — at 15% it's net-neutral-to-slightly-
      negative for the book (1.33 w/ R8 vs 1.38 no-short). Size it by its marginal Sharpe contribution, not a fixed 15%.
      Repo: strategy-service. Provenance: short re-spec 2026-06-21.

### 2026-06-21 — WHY ALL-STRATEGY 2023 PnL SUCKS: structural (not data); regime shift; funding risk; TS-momentum fix

Operator: "why does everything lose in 2023 across all strategies — do we not have data for 2017-2023?" then "before
dropping the training cutoff, see if it improves PnL — 2021 regime shift (institutionals/ETFs) means old data may be
less useful." Investigated end-to-end:

- **2023 is STRUCTURAL, not a data/model bug (`_dispersion_diag.py`)**: 2023 had the **lowest cross-sectional dispersion
  of any year (2.28%)** + was the **regime-transition year** (2022 capitulation → 2023 V-recovery; every walk-forward
  model was trained on data ending in the bear) + a **melt-up** (BTC +154%) the market-neutral book deliberately doesn't
  capture. Cross-sectional alpha needs coins to DIVERGE; in 2023 everything pumped together → no XS spread to exploit.
  All XS legs failed simultaneously because it's the MARKET, not the models.
- **The 2021 institutional/ETF regime break is REAL and the operator's instinct is dead-on**: avg pairwise correlation
  jumped **0.14-0.26 (2018-2021, retail/idiosyncratic) → 0.56-0.71 (2022+, institutional/macro-correlated)**; XS
  dispersion halved (3.8-6.5% → 2.3-3.0%). Cross-sectional crypto alpha is STRUCTURALLY thinner post-2021.
- **TRAINCUT verdict — pre-2021 data does NOT help (empirically tested before changing anything)**: ext walk-forward
  full-history (incl. 2017-2020) vs 2021-cut → 2023 **−0.7 vs −0.6 (marginally WORSE)**, 2024-26 unchanged, and the
  pre-2021 OOS itself is **−3.2/−3.0** (model forced to learn the dead retail regime). h32 full-history aggregate
  dropped to 0.43. **KEEP the cutoff** — more history dilutes with a defunct regime. (Data DOES exist to 2017-2020 in
  `altfull_*`; the cs ensemble `_panel.py` even reads the 2022+ `alt_*` instead — a real plumbing gap — but the regime
  analysis says using the deeper history would hurt, so it's moot for now.)
- **The XS legs are a 2024-25-favorable OVERLAY, not a foundation**: multi-cycle walk-forward (WFSTART=2020) shows ext
  is positive ONLY in 2024-2025 across the whole 2020-2026 record (2020:−3.2 2021:−3.0 2022:−0.3 2023:−0.7 2024:+3.0
  2025:+2.9 2026:−0.1). We had been viewing a window that happened to include its two good years.
- **Operator: "basis can't be the only thing — others must contribute in low-funding years." CONFIRMED + quantified
  (`_robustness_addons.py`)**: funding compressed **+12.0% (2024) → +0.9% (2025) → −0.4% (2026)** — basis carry is
  structurally shrinking. 2026 is the danger case: basis thin AND XS weak. **The fix is a confirmed long+short
  TS-MOMENTUM leg** (funding-independent, regime-adaptive): yearly `'23:+0.4 '24:+0.4 '25:+1.7 '26:−0.2` — positive-to-
  flat in EVERY regime (long captures the 2023/24/25 melt-up beta the neutral book misses; short is the R8 selloff
  function for 2026). The robust book = **XS (dispersion) + basis (funding) + TS-momentum (beta)** so something always
  fires; the R8 short folds into the TS-momentum's short side.

**Follow-up todos:**

- [ ] [RESEARCH] P2. **Add a confirmed long+short TS-MOMENTUM leg** to `build_strategies` + the production book — the
      missing regime-adaptive beta sleeve (funding-independent; long confirmed-uptrend coins, short confirmed-downtrend,
      20d&60d momentum confirmation). Folds the R8 short into its short side. Repo: e2e-testing
      `scripts/paper_trading/` + strategy-service. Provenance: robustness analysis 2026-06-21.
- [ ] [RESEARCH] P3. **Funding-regime monitor + dynamic basis sizing** — funding compressed +12%→−0.4%; size the basis
      sleeve by the prevailing funding level (down-weight as it compresses) so the book doesn't silently over-rely on a
      shrinking carry. Repo: strategy-service. Provenance: robustness analysis 2026-06-21.
- [ ] [BUG] P3. **`_mom_tb.py` daily-PnL save is skipped under `OOSLO`/`WFSTART`<2023** — the `MOMDAILY_TAG` parquet
      never wrote for the multi-cycle run (the `ext` `WFSTART` path saved fine). Gate the daily-save on the predicted
      range, not a hardcoded 2023+ window. Repo: e2e-testing `scripts/paper_trading/`. Provenance: multi-cycle run
      2026-06-21.
- [ ] [DATA] P3. **cs ensemble (`_panel.py`) reads `alt_*` (2022+) not `altfull_*` (2017+)** — a plumbing gap (the deep
      history exists but isn't used). Low priority since the regime analysis says pre-2021 hurts, but the inconsistency
      should be reconciled (use `altfull_*` + an explicit TRAINCUT, not a silent 2022 floor). Repo: e2e-testing. Prov:
      data-extent audit 2026-06-21.

### 2026-06-21 — SIGNAL-vs-EXECUTION, walk-forward COIN/STRATEGY allocation, basis CAPACITY, HYPE universe gap

Operator pushed on coin-pick / gross-vs-net / lookahead, then walk-forward allocation, then the basis capital
constraint, then HYPE. Findings (all walk-forward, IS=2023-24 / OOS=2025-26):

- **2023 is a SIGNAL problem, not execution (`_gross_net_decomp.py`)**: cs GROSS PnL (perfect-fill, zero-cost) was
  **−$116k (Sharpe −0.55) in 2023** — there was no alpha to capture, execution didn't eat it. 2024/25 gross strongly
  positive, exec drag only 7-22% (maker captures the spread: total cost $47k
  on $944k gross; the bigger exec piece is
  $185k missed-alpha from partial fills). Per-coin: the bad names are bad
  because the **SIGNAL** loses on them (SOL −$107k, LTC −$114k GROSS) not because they're expensive (SOL is the CHEAPEST
  at 4bp); ZEC is the best (+$596k) despite the highest slip (26bp). So coin-pick = signal quality, not execution cost.
- **Walk-forward COIN allocator (`_wf_coin_select.py`) — "drop SOL/LTC" was LOOKAHEAD BIAS**: a causal trailing-Sharpe
  allocator (monthly, floor-kept-alive) correctly down-weights LTC (1.2% vs 3.3%) using only past data, BUT does NOT
  beat equal-weight (+0.13 vs +0.21) — it chases the prior regime's winners into rotation years. **Coin-selection is not
  a free edge; equal-weight + keep-every-coin-alive is the honest baseline** (operator's instinct vindicated).
- **Comprehensive IS/OOS allocation study (`_alloc_comprehensive.py`) — scaling into WINNERS works, into LOSERS does
  not**: slow momentum (180-365d, into winners) beats equal OOS for coins (1.00 vs 0.77) and **directional strategies
  (1.63 vs 1.03)**; mean-reversion (into losers) FAILS OOS; fast (90d) momentum ≈ equal (chases rotation). The
  directional-strategy edge is REAL (not a basis artifact).
- **Basis is CAPACITY-BOUNDED, not "scaled into" (operator correction)**: you cannot deploy more than your capital ×
  funding-coin liquidity into a delta-neutral long-spot/short-perp carry. So basis is a **fixed-capacity sleeve filled
  first**; the momentum allocator distributes only the **directional** legs (cs/h32/ext/short/tsmom). With basis
  excluded, capped slow-momentum lifts the directional book OOS **1.03→1.63** (full-window 0.42→0.70). Plot:
  `book_updated_*.png`. The naive "momentum over all 6 legs → OOS 10.7" was just over-concentrating the capacity-bounded
  basis — fixed by treating basis as a sleeve + a per-leg weight cap.
- **HYPE universe gap (operator: "we should trade HYPE everywhere")**: the universe is FROZEN to 30 Binance-spot coins;
  the entire post-2024 cohort (HYPE, SUI, …) is missing because the pipeline only pulls Binance spot, and **HYPE isn't
  on Binance spot** (it's on Hyperliquid — the venue we trade — + Bybit). Fetched HYPE full history from **Bybit** (54k
  15m bars, 2024-12-05→now → `altfull_HYPE_15m`); Hyperliquid `candleSnapshot` is recent-only (~52d). Adding HYPE
  exposed + FIXED a latent `build_strategies` bug (basis leg crashed on a fundingless coin → now reindexes funding to
  0). HYPE needs the cs-ensemble re-run to actually trade.

**Follow-up todos:**

- [ ] [DATA] P2. **Add HYPE + the post-2024 cohort (SUI, etc.) to the trading universe** — fetch from Bybit/Hyperliquid
      (`_fetch_bybit.py`/`_fetch_hyperliquid.py`), fetch their funding, **re-run the cs ensemble (`_panel.py`) with them
      in the universe** so they actually trade; the WF allocator then weights a new coin from the floor up as it earns a
      trailing Sharpe. Repo: e2e-testing `scripts/paper_trading/` + strategy-service. Prov: HYPE gap 2026-06-21.
- [ ] [RESEARCH] P2. **Implement the deployable allocator: basis filled-to-capacity + capped slow-momentum (180-365d)
      over the directional legs** (cs/h32/ext/short/tsmom), monthly, lagged, per-leg cap so no sleeve dominates; coins
      stay ~equal-weight (selection isn't a reliable edge). Repo: strategy-service. Prov: allocation study 2026-06-21.
- [ ] [BUG] P3. **Combined-book vol-normalization uses full-period vol (mild in-sample scaling)** — does not affect
      per-leg Sharpe but a strictly-OOS combined number should weight legs by TRAILING vol. Repo: e2e-testing. Prov:
      walk-forward audit 2026-06-21.

**CORRECTION (2026-06-21, operator caught a −1.49 TS-momentum line on the plot)**: the TS-momentum leg was being
normalized by the UNSHIFTED signal count (`tsig.abs().sum`) while the numerator was the shifted signal — a 1-day
misalignment that CORRUPTED the leg to a fake −1.49 Sharpe in `_updated_book_plot.py` + `_alloc_comprehensive.py`. The
TRUE leg is **+0.75 (OOS +1.13, '25 +1.75)** — a positive trend-follower. Fixed both (normalize by the shifted signal).
**Two consequences**: (1) the directional book ~tripled — equal-weight **full +0.42→+1.37, OOS +1.03→+2.18** (the bug
was dragging it ~1 Sharpe); (2) the "capped slow-momentum beats equal (1.03→1.63)" claim above was **partly the buggy
baseline** — with the leg fixed, all directional allocation rules land ~2.0–2.3 OOS and equal-weight (+2.18) is
competitive, so **the allocation tilt is marginal (~+0.1), not ~+0.6**. Net: equal-weight directional +
basis-to-capacity is the robust deployable; the clever tilt is a rounding error. Lesson: a losing backtest line is more
often a BUG or overfit than free inverse-alpha — fix/verify it, don't reflexively flip it (flip is in-sample by
construction).

**SHORT-LEG FINAL VERDICT (2026-06-21, operator: "short still needs fixing in 2023")**: the book short's GROSS signal is
NEGATIVE in 2023 (−0.72) AND 2024 (−4.01) — it shorts INTO the bull; SIGNAL problem, not execution (net −0.52/−3.24 ≈
gross). NO gate fix works — every stronger gate shorts deeper into the rally/bottom (drawdown-gate −18 in 2023).
**Decisive test: the directional book is STRICTLY BETTER without the standalone short — full +1.37→+1.54, 2024
+2.19→+2.66, 2025 +3.19→+3.31, only 2026 −0.22→−0.52 (covered by basis + tsmom's short side).** 6th independent
confirmation the short has no standalone edge; first DECISIVE one. **Action: RETIRE the standalone short as a leg** (the
R8 gate from earlier today made it less-catastrophic but the right answer is removal). **Deployable directional book =
cs + h32 + ext + TS-momentum (no standalone short) + basis-to-capacity.** Scripts: `_short_2023_fix.py` /
`_short_net_book.py`.

### 2026-06-21 — cs/tsmom UNDERPERFORM THE 2-BAR: diagnosed + fixed (IS-chosen, no-lookahead, robust)

Operator: "each strategy going in is supposed to be Sharpe 2 even with realistic fills" — then "make sure robust OOS +
no lookahead". Per-leg audit (realistic maker, liquid-9): the legs HIT ~2-3 in the clean years (ext 2.7-3.1, h32 2.6
in 2025) but the FULL walk-forward drags them (cs 0.75, h32 0.54, ext 1.39, tsmom 0.75) — the 2023 structural drought,
NOT the fills (gross is also ~1 full). cs and tsmom are the genuinely weak ones. Dug in (`_cs_tsmom_audit.py` /
`_honest_optimize.py`):

- **cs was OVER-TRADING a noisy 15m next-bar signal (turnover ~1873x)**. Smoothing the ML book (EWMA span, trailing →
  lookahead-free) DENOISES it — robust across EVERY span 3-40 (OOS 0.84→1.05-1.33; longer spans overfit IS so kept a
  short denoise). **Wired span-7 into `build_strategies` (`bk.ewm(span=7).mean()`) → OOS 1.26 (from 0.84).** Proper fix
  is a longer-horizon TARGET retrain in `_panel.py`; this is the easy 80%.
- **tsmom's SHORT side was the whole drag** — LONG-ONLY beats long+short across ALL 18 sweep configs (mean OOS 1.48 vs
  0.81). HONEST: the IS-chosen config (MA20 10/30 long-only) → **OOS 1.38** (my first pass cherry-picked the OOS-best
  2.36 — overfit, corrected). Make tsmom long-only.
- **DISCIPLINE (operator demand)**: every hyperparameter chosen on IS(2023-24), reported on OOS(2025-26) untouched; all
  smoothers/signals are trailing+shifted (no lookahead); robustness shown by the whole-grid spread, not a tuned point.
- **Result (honest)**: the DIVERSIFIED directional book = **full +2.26 / OOS +2.72 — CLEARS the 2-bar via
  diversification** (legs individually 1.3-1.8; four near-uncorrelated legs combine above any one). + basis = +8.28.
  2023 (−0.6) / 2026 (−1.1) still negative (drought/compression) — basis carries those. Plot `book_improved_*.png`.

**Follow-up todos:**

- [ ] [RESEARCH] P2. **Apply the cs denoise + tsmom-long-only to the production legs** — cs: `ewm(span≈7)` on the ML
      book (or a longer-horizon target retrain in `_panel.py`); tsmom: ship LONG-ONLY (drop the short side). Both
      IS-chosen, OOS-validated, lookahead-free. Repo: e2e-testing `scripts/paper_trading/` + strategy-service. Prov:
      leg-quality audit 2026-06-21.
- [ ] [RESEARCH] P3. **h32 is the next weak leg (0.54 full)** — give it the same denoise/horizon treatment (it's a
      momentum leg; likely over-trading like cs). Repo: e2e-testing. Prov: leg-quality audit 2026-06-21.

### 2026-06-21 — BASIS-CARRY REALISM AUDIT (operator: "basis seems crazy high — yield? execution? $2.5M unleveraged? not super-illiquid?")

`_basis_audit.py` answers all four empirically: (1) **NOT illiquid** — the liquid-9 basis holds only liquid majors
(LINK/LTC/ZEC/DOGE/XRP/ETH/ADA/SOL/BNB), zero illiquid-tail. (2) **Unleveraged + UNDER-deployed** — mean gross notional
$804k (max $2.0M) vs the
$2.5M CAP, delta-neutral, uses CAP not the 2x BOOK. (3) **Yield realistic** — held-coin funding
+9.8%/yr mean (real Binance funding on liquid perps), NOT the 50%+ illiquid-small-cap funding. (4) **Sharpe real but
OPTIMISTIC** — funding-only 13.6 → 11.7 (2-leg maker) → 7.8 (+3%/yr financing) → 7.1 (+basis-dislocation MTM). **The
deployable basis Sharpe is ~7-12, not 13.** TWO clarifications: (a) the raw $
is MODEST — $264k cum over 3.5yr on ~$800k = ~10%/yr, sane low-vol carry, NOT crazy; (b) the "400%+ cum" on the leg
plots is a PRESENTATION ARTIFACT — every leg is vol-normalized to 10% vol, which LEVERS the low-vol carry up for
Sharpe-comparability. The one unmodeled risk is the rare basis-blowout TAIL (deleveraging events) a funding-only
backtest can't capture.

- [ ] [RESEARCH] P2. **Re-present + size basis on RAW economics, not vol-normed** — the deployable carry is ~10%/yr on
      ~$800k liquid-majors capital (Sharpe ~7-12 after 2-leg exec + financing), with an unmodeled deleveraging-tail
      risk; stop showing the 10%-vol-normed 400%-cum line as the headline. Add a basis-dislocation/borrow cost model + a
      tail reserve. Repo: strategy-service. Prov: basis realism audit 2026-06-21.

### 2026-06-21 — 2026 ALPHA DEATH: no clean crypto bear-alpha; de-risk + small short MITIGATE (operator-validated)

2026-H1 is a SELLOFF (BTC −29%); the book is long-biased/market-neutral with NO bear-alpha (we retired the short; basis
funding compresses to ~0/−0.4%). Two grounded bear-ALPHA candidates BOTH FAIL (`_2026_alpha*.py`): funding-gated short
WHIPSAWS (−8 in 2023, transition), and bidirectional/reverse-carry has NOTHING to harvest (even in 2026 only ~1 coin
funded < −5%/yr). **No clean crypto bear-alpha for a mild selloff with ~0 funding.** BUT de-risk + a SMALL short
MITIGATE (`_2026_derisk_short.py`): de-risk (gross 0.5× in confirmed risk-off = BTC 60d-mom<0 ∧ funding compressing,
lagged) fires 60%/2026, 0%/2024; + a 12% R8 short. **Combined: 2026 Sh −1.10→−0.42 (loss cut ~60%), maxDD −6.3%→−5.4%,
full 2.26→2.21 (negligible), no lookahead.** HONEST: 2026 still −0.42 = risk MITIGATION not alpha; genuine bear-alpha is
CROSS-ASSET.

- [ ] [RESEARCH] P2. **Ship de-risk overlay + 12% short to the deployable book** — gross 0.5× in confirmed risk-off (BTC
      60d-mom<0 ∧ funding compressing, lagged) + R8 short at ~12%. Cuts 2026 loss ~60% + drawdown, negligible cost, no
      lookahead. Repo: strategy-service. Prov: 2026 audit 2026-06-21.
- [ ] [STRATEGY] P1. **Accelerate non-crypto archetypes (TradFi/sports/prediction) for genuine bear-regime alpha** —
      2026 proves the crypto carry+directional book is flat-to-negative in a crypto selloff; cross-asset is the only
      real diversifier. Repo: epics. Prov: 2026 audit 2026-06-21.

### 2026-06-21 — EXECUTION CALIBRATION vs Binance RFQ/screen (operator: "are we too aggressive on ourselves?")

Operator gave indicative Binance RFQ widths vs screen costs (BTC/ETH ~0.5-2bp, SOL/BNB/XRP ~1-6bp, DOGE/ADA/LINK
~3-15bp)

- flagged RFQ can execute the BASIS as one combo. `_rfq_calibrate.py`: **at the REAL
  ~$250k trade size our liquidity
  scan matches the operator table almost exactly** (ETH 0.2 vs ~0.5-2, SOL 1.8 vs ~1-6, ADA 8.4 / LINK 6.2 / LTC 9.3 vs
  ~3-15). The apparent over-charge was a SIZE error — we'd read the **$1M**
  column (3-4× wider) when we trade
  ~$65-270k/coin. **The deployable book was already fine** (`simulate` uses the maker model, never the $1M scan; only
  audit scripts read the wrong column). The **maker-25%+missed model is CHEAPER than RFQ full-fill** for our
  low-turnover smoothed legs ($23k vs $54k on cs → keep the maker method). RFQ is a genuine upgrade ONLY for (a) the
  **basis combo** (one ticket → my earlier basis 2nd-leg haircut was too harsh) + (b) high-turnover legs. NOT
  over-aggressive at the right size; maker model is slightly conservative if anything.

* [ ] [BUG] P3. **Audit scripts read the $1M slip column; use the size-correct $250k column** —
      `_exec_by_vol`/`_exec_bps` over-state cost 3-4×; deployable `simulate` unaffected. Repo: e2e-testing. Prov: RFQ
      calibration 2026-06-21.
* [ ] [RESEARCH] P3. **Model basis execution as a Binance RFQ combo** (one ~0.5-5bp width for long-spot+short-perp) not
      two-leg taker — removes the 2nd-leg haircut. Repo: strategy-service. Prov: RFQ calibration 2026-06-21.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - 24 open items are almost entirely
  `[RESEARCH]` strategy work (execution sweeps, allocator design, leg re-specs, universe construction); the archetypal
  judgment corpus NA exists for.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries) --
  `e2e-testing/scripts/paper_trading/` (the standalone paper-trading POC dashboard named in the doc's own summary) + its
  `RECOVERY.md` remain the correct source targets alongside the parent plan + line-cap-remediation issue +
  strategy_master epic.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-confirmed against today's 9
  cheat-sheet rulings; none apply to a corpus of alpha-research strategy-desk judgment calls (execution-config sweeps,
  leg re-specs, allocator design, universe construction, all `[RESEARCH]`/`[STRATEGY]`). This is the archetypal
  trading-judgment content the NA classification exists for — reaffirms the 2026-07-30 verdict, no change.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms 2026-08-08 round7 verdict;
  16/22 open items map onto the doc's own operator-gated §C register (PERMANENT hard-stop, 2026-07-28), remaining 6 are
  RESEARCH refinements. 3 lower-confidence MISCLASSIFIED_LIKELY_AO_ELIGIBLE items noted, not enough to flip the doc.
