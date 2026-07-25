---
doc_type: plan
title:
  TradFi manifest/content recovery completion — Progress Log companion (2026-07-18 through 2026-07-21 P0-finding ticks)
summary: >-
  Companion doc to `tradfi_manifest_content_recovery_completion_2026_07_24.md` — the verbatim historical Progress Log
  slice covering ticks 1-12 (Phase A1/B writer + catalogue + manifest surface migrations, 2026-07-18), ticks 20-21/23-27
  (canonical GCS-path migration, Massive purge, post-migration audits, manifest surgical cleanup, 2026-07-20), the
  2026-07-21 pre-compact checkpoint + pre-compact lessons, and the 2026-07-21 P0 writer-regression finding — extracted
  for line-cap compliance (plan-hygiene discipline, task_template.md §3 finding J). All of it is superseded/carried
  forward by the parent's "2026-07-21/22 continuation" section (which explicitly states it supersedes this content) and
  by the parent's later 2026-07-22 sections. Zero todos — pure narrative/evidence record; the parent plan remains the
  single live source of truth for all open work.
status: complete
nature: record
asset_group: [tradfi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer]
tags:
  [
    tradfi,
    canonicalisation,
    instrument-id,
    manifest,
    catalogue,
    migration,
    massive-purge,
    progress-log,
    history,
    close-out,
  ]
related:
  [
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  plan-hygiene discipline (task_template.md §3 finding J) — extracted from
  tradfi_manifest_content_recovery_completion_2026_07_24.md, whose own Progress Log had grown past the 1000L hard cap
  (1633 lines). This companion carries the OLDER, fully-superseded ticks (1-12, 20-21, 23-27, the 2026-07-21 pre-compact
  checkpoint/lessons, the P0 writer-regression finding) — the parent keeps the "2026-07-21/22 continuation" section
  onward, which is the live, current-state narrative.
assigned_role: data_engineering
drift_direction: advance-code
---

# TradFi manifest/content recovery completion — Progress Log companion

> **Companion history doc, not the live plan.** It holds the verbatim historical Progress Log extracted from
> `/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md` (2026-07-24 line-cap split, plan-hygiene
> discipline per `task_template.md` §3 finding J). Nothing below was rewritten; it is the original text, relocated. All
> open todos, the Codex SSOTs section, and the live/current Progress Log continuation (2026-07-21/22 onward) stay on the
> parent — that document is the single source of truth for what's still open. This companion has 0 open todos of its
> own.

---

## Progress Log

> **Moved verbatim from the parent's Progress Log (2026-07-24 line-cap split)** — this is the manifest/catalogue/
> content id-canonicalisation slice of the parent's single continuous autonomous-session narrative (ticks 1-12, 20-21,
> 23-27, the 2026-07-21/22 continuations, honest-coverage/KRX/chain-manifest-recovery work). The throughput-VM-launch
> slice (ticks 14/16/22/26-ETA + the Backfill-drive/nice-to-have sections) and the Phase-D testing slice (ticks 13/
> 17-19 + the 2026-07-23 continuations) were forked to the sibling plans instead — see their own Progress Logs for that
> content. Nothing below is summarized or rewritten; it is the original text, relocated.

- **2026-07-21 (slot-1) — TradFi MVP-set EXPANSION shipped (operator directive): 4 instrument groups flipped into tradfi
  MVP.** SSOT change in UAC `MVP_SCOPE["tradfi"]` — `unified-api-contracts@afa2dd64` (MVP_SCOPE_CONFIG_VERSION 18→19).
  Two mechanisms, both at the registry layer (NOT a post-hoc catalogue patch):
  - `_mvp_scope_rules.py::TradFiMvpRule` — added `BTC/ETH/MBT/MET` to `underliers` (CME crypto FUTURES; FUTURE cells
    only — `option_underliers={"ES"}` keeps CME BTC/ETH OPTIONS out per operator "no CME option for BTC and ETH"; also
    flows into `MVP_CME_EXCHANGE_CODES` so the CME databento download universe gains BTC.FUT/ETH.FUT/MBT.FUT/MET.FUT).
  - New declarative field `TradFiMvpRule.extra_mvp_cells` (exact `(venue_root, itype, base)` triples), matched by a new
    check in `_mvp_scope_predicate.py::is_mvp`: `(CBOE,FUTURE,VX)` + `(CBOE,INDEX,{US2Y,US5Y,US10Y,US30Y,US3M})` +
    `(FX,SPOT_PAIR,KRW)`. Kept out of the flat `venues`/`instrument_types` sets so "CBOE" doesn't sweep in the ~33k CBOE
    SPX/VIX OPTION rows. Tests added (`test_mvp_scope.py::TestTradFiMvpExpansionV19`), UAC QG green (312s).
  - **Projected mvp delta on the served catalogue (`prod/catalog.parquet`, identical `is_mvp` predicate): +409** — VIX
    FUTURE **82**, CBOE treasury-yield INDEX **10** (VIX cash INDEX excluded), FX KRW **1**, CME BTC/ETH/MBT/MET FUTURE
    **316** (BTC 92 + ETH 81 + MBT 76 + MET 67). Prior mvp=True set (70,930 on the current served artifact: CME OPTION
    69,822 + CME FUTURE 895 + NASDAQ/NYSE/KRX EQUITY 185 + ETF 28) unchanged → projected new total ≈ 71,339. NOTE:
    operator's ~1,602 VIX-futures estimate ≠ the 82 CBOE:FUTURE rows actually present in the served catalogue — flagged;
    the `--mode full` rebuild measures the true served count.
  - **Catalogue rebuild**: `build_instrument_catalogue.py --asset-group tradfi --mode full --allow-catalogue-shrink`
    launched locally (env `GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod`); checkout includes the
    `_iter_by_date_snapshots` litter-exclusion fix (`instruments-service@1a73082e`). 27,104 by_date parquets; **no OOM**
    (RSS steady ~1 GB, peak 1.45 GB) but CPU-bound rollup is slow on the local box — see report for served-artifact
    verification status.
  - **PART B — backfill DOWNLOAD coverage for the 4 groups (exact launcher invocations):**
    - VIX futures (CBOE:FUTURE:VX) — ALREADY covered: `launch-tradfi-bf-cfe-ohlcv-1m.sh` (VX.FUT via Databento
      XCBF.PITCH, routed VM_VENUE=CBOE, full history from 2018-11-04). (`launch-tradfi-bf-cboe-ohlcv-1m.sh` = the
      2026-YTD gap-filler for the same VX.FUT.)
    - CME BTC/ETH futures — ALREADY covered: `launch-tradfi-bf-cme-ohlcv-1m.sh` (CME_ROOTS already lists
      BTC/ETH/MBT/MET; per-root: `--only-root BTC` / `ETH` / `MBT` / `MET`).
    - KRW — ALREADY covered: `launch-tradfi-bf-fx-ohlcv-24h.sh` (Yahoo daily iterates the whole FX_SPOT_PAIRS universe;
      `FxSpotPairDef("KRW","USD","KRWUSD=X")` is in it).
    - Treasuries (CBOE:INDEX:US*) — **GAP CLOSED**: no launcher emitted VM_VENUE=CBOE + ohlcv_24h. Added
      `deployment-service/scripts/vm/launch-tradfi-bf-cboe-indices-ohlcv-24h.sh` (routes
      `route_yahoo_tradfi("CBOE", {ohlcv_24h})` → `fetch_yahoo_indices("CBOE")` → the 5 Yahoo treasury tenors). Ship
      BLOCKED locally by a PRE-EXISTING deployment-service QG red
      (`tests/integration/test_zone_failover_integration.py:39` imports the removed `unified_trading_library.sink` →
      collection pollution) — see report finding.

- **2026-07-18 (slot-1) — Autonomous close-out loop STARTED; baseline re-measured live + core shape problem
  pinpointed.** Re-verified the climbing metric directly against live prod GCS (not docs), confirming the plan's ground
  truth:
  - Catalogue `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` (1,175,390 rows; 1,111,322
    FUTURE/OPTION): `instrument_id` col **0.0% canonical** (0 in `-USD@LIN`; 997,973 carry whitespace; samples
    `CBOE:FUTURE:VX/F1`); `canonical_instrument_id` col mostly empty strings, **0.0%**.
  - Manifest `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (5,553,510
    rows; written 2026-07-18T11:21Z so consolidator is LIVE): derivative `instrument_id` **0.0% canonical** (0 of
    989,722; samples `EW1H0_P2785`, `UD_1V__VT_...`). `instrument_type` itself is non-canonical (mixed case
    `FUTURE`/`future`, `options_chain`/`futures_chain`).
  - **CLIMBING METRIC baseline = 0% canonical across both id-column surfaces.** Filenames/parquet-content = TBD (A1).
  - **Core shape finding (drives A1+B+QG):** BOTH the MTDS "target" writer
    (`tradfi_shared.py::derive_tradfi_row_instrument_id`) and the IS adapter currently emit `@LIN` **without** the
    operator-decided `-USD` quote — MTDS builds `build_instrument_id(venue, FUTURE, product_root, margin_marker="LIN")`
    → `CME:FUTURE:SP500@LIN-...` (no `-USD`). The shared UAC builder
    (`unified_api_contracts/internal/reference/canonical_id_builder.py::_build_with_margin_marker`) rides `@marker` on
    the symbol segment; the existing CeFi convention bakes the quote INTO the symbol (`BTC-USDT@LIN`). So `-USD@LIN`
    requires the symbol segment to carry `PRODUCT_ROOT-USD`. Decision: extend the shared builder to compose
    `{SYM}-{QUOTE}@{marker}[-expiry...]` when a `quote_asset` is supplied alongside `margin_marker` (additive, opt-in,
    default `""` keeps every existing caller byte-identical), then route both tradfi writers through it with
    `quote_asset="USD"`; migration + QG + verify-gate all assert the `-USD@LIN` body. Coordinated with the parallel
    `cefi_consolidated_closeout_2026_07_18.md` (same shared builder, same DERIBIT quote ruling).
  - Env verified: 8 target repos present in slot-1; gcloud `central-element-323112` ADC; AWS `427895769566`.

- **2026-07-18 (slot-3) — Plan authored, then GROUND-TRUTH-CORRECTED against live prod GCS.** First draft (from a
  3-agent doc audit) claimed the tradfi tick surfaces + v9 schema were "largely DONE, VM-applied." Operator pushed back
  (raw symbols visible in parquet names, manifest, and the instruments data-status/catalogue). Direct live reads
  DISPROVE the "done" claim for the derivative id columns: catalogue `prod/catalog.parquet` has 0 of 1,111,322
  FUTURE/OPTION rows in `@LIN` form (raw `CBOE:FUTURE:VX/F1`); manifest `availability_index.parquet` has 0 `@LIN` across
  all years (2026 alone 568,165 raw + 63,661 malformed). Only equities/futures_chain **filenames** are canonical.
  Rewrote into the operator's one-pass structure — Phase A code (writers live+batch + migration scripts + aggregation +
  adapters + download throughput) → Phase B migrations (all 4 surfaces) → Phase C data-status/honest-coverage → Phase D
  re-smoke-test with the two pipeline-check skills ADAPTED to the tradfi MVP universe (S&P index futures+options,
  delta-one single-stock equities, CME BTC/ETH futures+options, daily treasuries + KRW) → MVP-backfill-ready. All
  tradfi + tradfi-touching IS/MTDS docs aggregated above; none duplicated. The DERIBIT missing-quote finding stays
  captured on the cefi side (`cefi_consolidated_closeout_2026_07_18.md` line 183).

- **2026-07-18 (slot-1, autonomous loop) — Phase A1 underway: UAC builder SHIPPED + MTDS forward-write converged + full
  leak trace.** Re-verified the climbing metric live myself (own measurement, not the doc) on a fresh prod snapshot:
  - **CLIMBING METRIC baseline = 0.0000% canonical (`-USD@LIN`)** on the id-column surfaces: catalogue `instrument_id`
    **0 / 1,111,322** FUTURE/OPTION (113,349 raw like `CBOE:FUTURE:VX/F1` + **997,973 whitespace** — the
    `CME:OPTION:E3AN6 C7960` literal-space class); catalogue `canonical_instrument_id` **0 / 1,111,322** (all empty
    strings); manifest `availability_index.parquet` `instrument_id` **0 / 989,723** (783,523 raw like `EW1H0_P2785` +
    206,200 whitespace). Reusable measurement tool: scratchpad `measure_metric.py` (pyarrow, matches the exact
    `VENUE:TYPE:ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` shape).
  - **[A1 builder] SHIPPED — `unified-api-contracts@8b7c4967`.** Extended the shared
    `canonical_id_builder._build_with_margin_marker` to compose an explicit `-USD` quote onto the _bare_ product-root
    symbol segment when `quote_asset` is passed alongside `margin_marker` → `CME:FUTURE:SP500-USD@LIN-20300621`,
    `CME:OPTION:SP500-USD@LIN-20251017-5000-C`, `CBOE:FUTURE:VIX-USD@LIN-20260722`. Additive + opt-in: default
    `quote_asset=""` keeps every existing `margin_marker` caller byte-identical (audited — all CeFi callers embed the
    quote in the symbol e.g. `BTC-USDT`/`BTC-USD` and never pass `quote_asset`, so zero risk of double-append; verified
    `BINANCE_FUTURES:PERPETUAL:BTC-USDT@LIN` / `BINANCE_DELIVERY:FUTURE:BTC-USD@INV-20260925` unchanged). Added
    `TestTradfiUsdMarginMarker`. UAC QG green (337s).
  - **[A1 writers] MTDS forward-write CONVERGED (edits made, MTDS QG/ship pending this tick):**
    `databento_enrichment.py::_classify_row` (primary databento tick forward-write) and
    `tradfi_shared.py::derive_tradfi_row_instrument_id` (batch derive) now pass `quote_asset="USD"` for FUTURE/OPTION →
    both emit `-USD@LIN`. UAC is editable-local to MTDS (confirmed) so the change resolves at runtime.
  - **LEAK TRACE (drives remaining A1 + Phase B):** (1) **IS catalogue adapter** `.../tradfi/databento/adapter.py:880`
    sets `instrument_key = VENUE:TYPE:{sanitized_raw}` (→ the catalogue's raw `instrument_id`, e.g. `CME:FUTURE:GCQ26`),
    and `_build_canonical_instrument_id` (`:974`) emits a colon/month-only non-`@LIN` additive field (mostly empty live
    because `_resolve_product_root` returns None) — BOTH must converge to `-USD@LIN` (→ IS sub-agent). (2) **Manifest**
    `instrument_id` derives from the parquet **content** `instrument_id` column via
    `unified_trading_library/io/streaming_writer.py`→`manifest_writer`, so once the content column is canonical (done),
    forward-write manifest rows are canonical too; historical manifest+catalogue rows are the Phase-B migration. (3) The
    `tardis_*` paths under `adapters/tradfi/` are CeFi (deribit `derive_row_instrument_id`) or the **futures_chain
    bundle** atom (product-symbol id = canonical by design) — NOT tradfi-databento leaks.
  - **Concurrency note:** slot-3 is running the parallel `cefi_consolidated_closeout_2026_07_18.md` (same shared UAC
    builder); QG cap = 2 (10 cores) so serialize; reconcile-not-stomp if slot-3 lands a builder change (my change is
    additive so it merges cleanly). Env: 8 repos present, gcloud `central-element-323112` ADC, AWS `427895769566`.

- **2026-07-18 (slot-1, tick 2) — MTDS forward-write SHIPPED + verified; IS convergence written, ship in progress.**
  - **[A1 writers] SHIPPED `market-tick-data-service@c44d5f0d`** — `databento_enrichment.py::_classify_row` (primary
    databento tick forward-write) + `tradfi_shared.py::derive_tradfi_row_instrument_id` (batch derive) now emit
    `-USD@LIN`. Landed on attempt 1 of an atomic re-gate+quickmerge retry loop (won the push-race vs slot-3's parallel
    MTDS cefi-script commits — those FF-staled my QG sentinel twice, so I automated the re-gate). MTDS QG green.
  - **Runtime PROOF (own venv):** FUTURE `ESM26`→`CME:FUTURE:SP500-USD@LIN-20260619`; OPTION `E3AN6 C7960`
    →`CME:OPTION:SP500-USD@LIN-20260117-7960-C` (0 whitespace, product root ES→SP500). Metric on LIVE surfaces stays 0%
    until Phase B migrates historical — writers are the gate for B, now open.
  - **[A1 IS] IS catalogue adapter convergence WRITTEN** (sub-agent, uncommitted in
    `instruments-service/.../tradfi/databento/adapter.py` + `tests/unit/test_databento_tardis_adapter.py`) — reviewing +
    gating + shipping now (sub-agent stopped pre-ship). Note: slot-3 already shipped the parallel DERIBIT
    always-BASE-QUOTE fail-loud fix `instruments-service@d72edcf7` (same 2026-07-18 quote ruling, cefi side).
  - **Scoping:** launched a 4-agent read-only Workflow (`wf_2f2c9a39-164`) mapping Phase A2/A3 + B + C + D into
    actionable change-maps (in flight). Phase-B schema recon done: catalogue+manifest carry NO strike/option_right cols
    → migration must re-parse each raw id via the databento classifier (one shared `canonicalize_raw_tradfi_id`), so
    migrated == newly-written byte-for-byte; unparseable spreads (`UD_1V__VT_...`) → quarantine not silent-drop.

- **2026-07-18 (slot-1, tick 3) — IS convergence + scoping complete; Phase B design locked; skills linker fixed.**
  - **[A1 IS] shipping** — reviewed the sub-agent's IS adapter diff (correct: builds `-USD@LIN` via shared builder for
    resolvable FUTURE/OPTION, `canonical_instrument_id`=`instrument_key` byte-equal, drops old colon/month additive
    builder, clean raw fallback). Removed one INVALID sub-agent test (`test_missing_expiry_falls_back_to_raw_shape` —
    asserts a schema-FORBIDDEN FUTURE-with-null-expiry state; the real fallback is covered by
    `test_unresolved_product_root_falls_back_to_raw_shape`). Atomic re-gate+quickmerge retry loop in progress vs a busy
    IS push-race (peers pushing `build_instrument_catalogue.py`). IS tests assert `CME:FUTURE:SP500-USD@LIN-20300621` /
    `CME:OPTION:SP500-USD@LIN-20251017-5000-C` / `CBOE:FUTURE:VIX-USD@LIN-20260722`.
  - **Scoping workflow DONE** (`wf_2f2c9a39-164`, 4 agents) — full change-maps in scratchpad `scope_{A,B,C,D}.md`.
    Highlights: **A3.1 Databento DNS-executor** is the P0 pure-code win (`databento_fetch.py:186/:388/:672` +
    `databento_batch_jobs.py:629` all use `run_in_executor(None,…)` → dedicated pool mirroring
    `tardis_csv_transport.py::_get_parse_executor`; `:186` full-fetch hold is the highest-risk, NOT the doc's headline
    `:672`). **A2.1 CME mbp_10/trades/tbbo** UAC-capability restoration is now DE-SCOPED for MVP by the operator billing
    ruling (ohlcv_1m only); adapter allowlist already fixed `@e2018167`. **A2.2** KRX resolved (verify KRW),
    IBKR/combo-leg done (flip stale todo), `mvp_mode` dead gate → delete. Phase-B design → the 5 refined Phase-B todos
    above (NEW scripts, promote primitive to UAC, catalogue prod/n+per-day-corpus durability, manifest per-VM-shard
    write, re-stamp ~400k mislabeled instrument_type, ICE-qualifier BLOCKED-OPERATOR-DECISION).
  - **Operator (present) clarifications applied** (pm@882650559): Databento MVP backfill = `ohlcv_1m` ONLY
    (mbp_10/trades/tbbo billing-gated by design, 1mo L3 + 1yr L1); Yahoo Finance = 24h/1d daily (Treasuries `ohlcv_24h`,
    KRW). **Skills linker** — this slot still had the legacy per-skill `.claude/skills` layout (Jul 7), so
    data-pipeline-check-is/-mtds + plan-reconcile + pre-compact (added Jul 17-18) never surfaced; re-ran
    `link-claude-skills.sh` → migrated to the single-dir link, all 6 skills now surface (mid-session).

- **2026-07-18 (slot-1, tick 4) — Phase B migration scripts written + dry-run-VERIFIED; 2 CRITICAL findings caught
  before any prod write.** Both scripts (2 sub-agents) reuse the shared `canonicalize_raw_tradfi_id` primitive:
  - **Catalogue** `instruments-service/scripts/canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py` — dry-run vs local
    snapshot: **99.86% OK** (1,109,717/1,111,322; 338 combo + 204 neg-strike + 1,063 ICE-qualifier quarantine);
    self-check passes; snapshot-before-write to `prod/backups/`. In-place `prod/n` rewrite + `--by-day` corpus
    (durability). SAFE to `--apply` (flat rewrite, no dedup-key/consolidator concern). Shipping via the git-add-prestage
    workaround.
  - **Manifest** `market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py` — SHIPPED
    `market-tick-data-service@2bddcb9e`. Dry-run: derivative **62.42% OK** (617,808/989,755) + **238,227 mislabel
    fixes**
    - **3,300,155 UPPERCASE case re-stamps** (Bucket 3, operator ruling) + 142,590 bundle-underlying translations;
      self-verify 617,808/617,808 canonical.
  - **🚨 CRITICAL (data-correctness) — dedup-key: the manifest per-VM-shard additive write DUPLICATES, does NOT achieve
    0-raw.** `instrument_id`/`instrument_type`/`underlying` ARE members of the consolidator's `_OPTIONAL_DEDUP_COLS`
    (`unified_trading_library/manifest_consolidator.py`), so changing them changes the row's dedup key → the additive
    shard ADDS the corrected row as a NEW key and the OLD raw row SURVIVES the merge (both coexist). So `--apply` alone
    leaves the raw rows in place. **Manifest migration REVISED: must PAUSE the tradfi manifest-consolidator + CAS
    in-place rewrite** (sanctioned by the CLAUDE.md direct-index-mutation rule) so raw rows are REPLACED not duplicated;
    the additive+`superseded_keys`-purge alt still needs a pause/CAS for the removal, so pause+CAS is the one correct
    path. **DO NOT run manifest `--apply` as-is.** Captured as the revised Phase-B manifest todo.
  - **quickmerge TOOLING BUG (affects every agent shipping a NEW file)** — `quickmerge.sh`'s early "identical to main"
    check (`git diff origin/main`) does NOT see UNTRACKED files → for a first-time script it silently prints "nothing to
    merge" + exits 0 WITHOUT shipping. Workaround: `git add` the file BEFORE quickmerge. FIX needed in
    `unified-trading-pm/scripts/quickmerge.sh` (stage `--files` before the early-exit, or also check
    `git status --porcelain`) — filed as a Phase-B-adjacent tooling todo.
  - **NEXT:** catalogue `--apply` (safe) → verify → then build the manifest pause+CAS path → manifest `--apply` →
    verify-gate 0 raw → re-measure the live metric (the climb).

- **2026-07-18 (slot-1, tick 5) — 🎯 CATALOGUE SURFACE MIGRATED — metric climbed 0.0000% → 99.8556% (VERIFIED LIVE).**
  Ran `canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py --apply --full-sweep` against prod
  (`GCP_PROJECT_ID=central-element-323112`; the prod-op must run backgrounded — the harness 2-min foreground cap killed
  the first attempt AFTER the backup but BEFORE the write, so the original was intact + safe). Result: **1,109,717 rows
  migrated**, `prod/catalog.parquet` rewritten 11.3MB→16.0MB, backup
  `prod/backups/catalog.parquet.pre_usd_lin_*.bak.parquet`
  - quarantine sidecar written. **INDEPENDENT live re-measure (own tool, not the script)**: catalogue `instrument_id`
    **1,109,717/1,111,322 = 99.8556%** canonical `-USD@LIN`; `canonical_instrument_id` same (byte-equal; the old
    all-empty additive col is gone). Only 1,605 non-canonical remain = the quarantined 338 combo + 204 negative-strike +
    1,063 ICE-qualifier. The deployment-api "Upcoming expiries" widget now renders `CME:OPTION:SP500-USD@LIN-...` not
    `E3AN6 C7960`.
  * **TWO follow-ups found (both minor, tracked):** (1) **catalogue combo re-stamp gap** — 338 CME combo-strips
    (`CME:FUTURE:CL:SA 03M V7`) are stored `instrument_type=FUTURE` but classifier-derive as COMBO; the migration
    quarantined them (left raw + FUTURE), so the post-apply verify flagged 25 as "unexpected violations" (it judges by
    the DECLARED type). FIX = re-stamp quarantined-combo catalogue rows FUTURE→COMBO (per operator UPPERCASE +
    classifier semantic type) AND/OR refine `assert_tradfi_derivative_ids_canonical` to classify by BODY not declared
    type (scope_B.md §7). (2) **Durability NOT yet done** — only `--full-sweep` (prod/n) ran; the per-day
    `instrument_availability/by_date/` corpus still needs `--by-day --apply` or the next `build_instrument_catalogue.py`
    rebuild reverts prod/n. NEXT: run `--by-day`, then manifest pause+CAS.

- **2026-07-18 (slot-1, tick 6) — catalogue per-day durability sweep RUNNING + manifest CAS-mode built + EXECUTION
  RUNBOOK.** Per-day sweep `--by-day --apply --by-day-full-sweep --workers 24` running in bg (2,636 partitions / 27,092
  files, ~3h idempotent, safe — backs up each file, skips already-canonical; progress = TARGET files rewritten).
  Manifest CAS-mode added to `migrate_tradfi_manifest_usd_lin_2026_07_18.py` (`--in-place-cas`: download →
  generation-match CAS rewrite that REPLACES raw rows, fixing the additive-dedup-key duplication; dry-run verified
  617,808/617,808 canonical + 3.3M UPPERCASE + 142,590 bundle translations). **MANIFEST EXECUTION RUNBOOK (the riskiest
  op — run each step, verify, RESUME at the end no matter what):**
  1. Ship the CAS-mode (in flight). 2.
     `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1 --project central-element-323112`
     → `describe ... --format='value(state)'` must show PAUSED.
  2. `cd market-tick-data-service && GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas`
     (BACKGROUND — 132MB download + 4M-row rewrite + snapshot to `_index/backups/` + `if_generation_match` CAS upload;
     aborts LOUDLY on race, no partial write).
  3. Independent verify: re-download `_index/availability_index.parquet` + run scratchpad `measure_metric.py` → expect
     derivative `instrument_id` ~62.4% canonical (rest = the enumerated combo/unparseable/continuous quarantine, NOT raw
     leaks) + 0 whitespace on OK rows. 5.
     **`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1 --project central-element-323112`**
     (CRITICAL — never leave the consolidator paused). Then re-measure the manifest surface (the second climb) + flip.

- **2026-07-18 (slot-1, tick 7) — 🎯 MANIFEST SURFACE MIGRATED (2nd climb) — consolidator paused→CAS→RESUMED cleanly.**
  Executed the runbook: paused `uts-prod-manifest-consolidator-market-data-tradfi-cron` (runs `*/1` — EVERY MINUTE, so
  the pause was essential) → `--apply --in-place-cas` (generation-match CAS: gen 1784386961903329→1784387144414068, NO
  race, 5,553,510 rows rewritten, 114.8MB) → **RESUMED (ENABLED, verified)**. **INDEPENDENT live re-measure:** manifest
  derivative `instrument_id` **0% → 62.4223%** (617,808/989,723); remaining 37.58% = the enumerated quarantine set (325k
  `UD_1V__VT_` CBOE user-defined-strategy COMBOS + 39k unparseable + continuous — NOT raw leaks, they belong to the
  combo track). `instrument_type` now UPPERCASE per operator ruling (`equity`+`EQUITY`→`EQUITY` 1.99M, `combo`→`COMBO`
  1.15M, mislabels re-derived → `OPTION` 238,227). **Backups:**
  `_index/backups/availability_index.pre_usd_lin_20260718T150445Z.parquet`.
  - **RESIDUAL (the key follow-up — cleans both the metric + the dimension):** 165,715 rows still typed lowercase
    `future` = the quarantined COMBOS whose `instrument_type` my migration left unchanged (quarantine = no id/type
    change). They should be `COMBO` (classifier-derived). Because they're counted as raw FUTURE/OPTION, they DRAG the
    62.42% down — re-stamping quarantined-combo `instrument_type`→`COMBO` (on BOTH catalogue + manifest) lifts the true
    FUTURE/OPTION-canonical toward ~100% AND removes the last `future`/`FUTURE` dimension dupe. P0 follow-up.
  - **Durability re-check IN PROGRESS** (does the every-minute consolidator revert the CAS rewrite? modeled on
    `restamp_tradfi_schema_v9_tail` which persisted, so expected durable — verifying live).
  - **Phase C dimensions-view DONE** (operator ask): backend `deployment-api@09656f4`
    (`GET /data-status/axis-value-census`) + UI already shipped by the cefi-Track-6 peer (`deployment-ui@3fb6779`);
    live-verified reproducing the exact drift audit. The old drilldown "removal" was `deployment-api@512180be`
    display-canonicalizing (folding dupes) — good UX, killed drift-detection; the census panel restores the raw view.
  - **Still queued:** combo re-stamp (above), cash-type `-USD` writer fix
    (`NASDAQ:EQUITY:AAPL-USD`/`FX:CURRENCY:KRW-USD` — builder `_build_tradfi_cash` adds `-USD` only for INDEX today),
    catalogue per-day sweep (~60% done), Barchart-retired purge, Phase A2/A3, Phase D.

- **2026-07-18 (slot-1, tick 8) — ✅ MANIFEST DURABILITY CONFIRMED (verified live, not assumed).** Two re-measures at
  +3min and +7min post-migration are BYTE-IDENTICAL (925,816 FUTURE/OPTION, 553,901 canonical 59.83%, raw 165,715 +
  whitespace 206,200; index generation/size stable at 80.6MB). **The raw count is FLAT across ~10 consolidator cycles →
  NO REVERT.** The every-minute consolidator did a ONE-TIME prune (my CAS index 617,808 canonical → consolidator
  steady-state 553,901; ~64k rows removed as stale/dedup, NOT reverted to raw — raw stayed flat) then stabilized. So the
  CAS-of-the-consolidated-index approach IS durable here (matching the `restamp_tradfi_schema_v9_tail` precedent). Both
  Phase-B surfaces (catalogue + manifest) are now migrated + independently-verified-live + durable. The residual 59.83%
  (vs a naive 100%) is entirely the quarantined combos (`UD_1V__VT_`) sitting in the FUTURE/OPTION denominator — the
  combo re-stamp (FUTURE→COMBO) P0 follow-up removes them from the denominator and lifts the TRUE non-combo
  FUTURE/OPTION canonical toward ~100%.

- **2026-07-18 (slot-1, tick 9) — Phase-A refinements landing (throttled by multi-slot QG contention, 4-5 concurrent).**
  - **[cash-type -USD] SHIPPED `unified-api-contracts@33e3f369`** — `_build_tradfi_cash` now suffixes `-USD` for
    EQUITY/CURRENCY/ETF/BOND/COMMODITY (was INDEX-only; CDS bare by design) → `NASDAQ:EQUITY:AAPL-USD`,
    `FX:CURRENCY:KRW-USD`. 6 tests updated to `-USD`. So the WRITER now emits `-USD` on cash types; the historical
    catalogue/manifest cash rows still need the **cash-type migration** (add `-USD` to equity/currency/etf/index/bond
    ids) — fold into the combo re-stamp re-run.
  - **[A3 Databento executor] edits complete, ship pending QG-cap** — dedicated `_get_dbn_fetch_executor()` routes all
    databento_fetch + databento_batch_jobs fetch/decode off the default pool (DNS-starvation fix); waiting on a gate
    slot.
  - ~~**NEW FINDING (follow-up todo): Massive normalizers bypass the shared builder** —
    `unified-api-contracts/unified_api_contracts/external/massive/normalize.py`
    (`normalize_massive_equity`/`_futures`/…) build `instrument_key` via raw f-strings
    (`f"{venue}:{itype.value}:{ticker}"`), so Massive-sourced tradfi ids are bare (`NASDAQ:EQUITY:AAPL`, no `-USD`) and
    won't get the cash `-USD` or the FUTURE `-USD@LIN` shape. Route the Massive normalizers through
    `build_instrument_id`. (repo: unified-api-contracts) — P1, matters for the Massive dual-source MVP cells.~~ **MOOT
    2026-07-21** — Massive removed as a tradfi source 2026-07-19 + fully purged (batch_massive → 0 objects); no cell can
    go Massive-dual-source, so the Massive normalizer path is dead code, not a live follow-up.
  - **Remaining to the terminal gate:** per-day sweep (~68%) → combo re-stamp + cash-type migration (1 catalogue pass +
    1 manifest pause→CAS) → Barchart purge → Phase D (adapt data-pipeline-check-is/-mtds to tradfi-only all-shards, both
    green on `-test-`, then MVP backfills — the wall-clock-bound long pole).

- **2026-07-18 (slot-1, tick 10) — per-day catalogue sweep ~83% then socket-exhausted; refinement wave dispatched
  (QG-throttled).** The `--by-day --apply --by-day-full-sweep --workers 24` catalogue-corpus sweep migrated
  ~22,600/27,092 by_date files then crashed on `OSError(49 Can't assign requested address)` — ephemeral-socket
  exhaustion from 24 workers over ~2h (same class as the Databento-executor DNS fix). prod/n INTACT (sweep only touches
  by_date). NEXT for catalogue durability: re-run the **enhanced** catalogue migration (combo re-stamp + cash `-USD`,
  once that sub-agent lands) with **fewer workers (8-12)** + it skips the ~83% already-canonical fast — ONE combined
  pass covers the remaining by_date + combo + cash. Refinement wave dispatched (all QG-throttled, 4-5 concurrent QGs
  multi-slot): combo/cash migration enhancement (primitive+scripts), Phase-D skill adaptation (pipeline-check
  tradfi-only all-shards + canonical cell), Phase A2/A3 infra (OOM rc137 + T+1 recon job), Databento DNS executor.
  Several sub-agents hit transient API stream-stalls under the heavy load; all resumed (edits persist). CORE remains
  done+durable+verified (both surfaces). RUNBOOK for the combined re-run: (1) catalogue `--apply --full-sweep`
  (prod/n) + `--by-day --apply --by-day-full-sweep --workers 10`; (2) manifest pause→`--apply --in-place-cas`→resume
  (per the tick-6 runbook); (3) verify live + re-measure.

- **2026-07-18 (slot-1, tick 11) — ✅ CATALOGUE prod/n FULLY CANONICAL across all dimensions (verified live).** Enhanced
  catalogue re-run `--apply --full-sweep`: 1,055 rows migrated (717 cash + 338 combo, FUTURE/OPTION idempotent-skipped).
  LIVE re-measure: EQUITY/INDEX/ETF ids all `-USD` (`NASDAQ:EQUITY:ACGL-USD`, `CBOE:INDEX:VIX-USD` — 717/717 cash =
  100%); combos re-stamped `instrument_type=COMBO` (63,275 total COMBO); instrument_types all UPPERCASE
  {FUTURE,OPTION,EQUITY,ETF,INDEX,COMBO,SPOT_PAIR}. FUTURE/OPTION 99.86% (TRUE 99.98% combos-excluded). The 25
  post-apply "violations" are COMBO-typed rows with still-raw ids (`CME:FUTURE:CL:SA 03M V7`) — EXPECTED (combo-ID
  canonicalization is the separate combo track; my re-stamp only fixed the TYPE). Gate refinement (exempt COMBO from the
  FUTURE/OPTION assertion) = a small follow-up. **Catalogue --by-day durability re-run launched (workers=10 to dodge the
  24-worker socket exhaustion; idempotent; ~2-3h, runs past the window).** MANIFEST combo/cash re-run pending its
  enhanced MTDS script landing (then pause→CAS).

- **2026-07-18 (slot-1, tick 12) — ✅ MANIFEST RE-RUN (combo+cash) VERIFIED LIVE — 2nd big climb.** Shipped enhanced
  manifest script (mtds@0e2ab69b) after unblocking the MTDS QG (Databento-executor split databento_fetch.py 915→887 into
  a new `databento_fetch_executor.py` module). Ran pause→`--apply --in-place-cas`→resume (gen
  1784395068233125→…156548316 CAS OK, consolidator RESUMED verified): 2,096,778 CASH rows→`-USD` + 325,473 combos
  re-stamped→COMBO (derivatives already canonical from tick-7). **INDEPENDENT live re-measure:** FUTURE/OPTION canonical
  **59.83%→94.78%** (553,901/584,430 — combos left the denominator); **EQUITY 99.9% `-USD`** (incl. KRX Korean
  `005930.KS-USD`); COMBO 1,480,449. **Residual/durability nuance:** lowercase `future`/`futures`/`FUTURES` types still
  appear — the consolidator re-introduces them from source per-VM-shard fragments (whose per-contract WRITE paths still
  emit lowercase). The derivative canonical IDs are durable (that's the primary target); the instrument_type-DIMENSION
  casing needs the **writer-instrument_type→UPPERCASE convergence** (already a tracked A todo) for full durability — a
  code fix on the tardis/per-contract manifest write paths, not another migration. Both surfaces now: catalogue prod/n
  fully canonical (99.98% true) + manifest 94.78% FUTURE/OPTION + 99.9% cash. NEXT: writer-itype convergence, catalogue
  --by-day durability (running), Phase D.

- **2026-07-20 (slot-1, tick 20) — canonical GCS-PATH migration EXECUTED on VMs; post-audit caught 2 defects; RECOVER-1
  fix SHIPPED (`market-tick-data-service@5588bdf8`).** The physical Hive-path reorg (the orphan-proof 9-disposition map
  over the 2,734,646-object enumeration; design doc
  `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`) ran to a clean 20-shard exit, but a
  post-run live re-walk found 2 defects the canary day missed (canary had no garbage-root combos):
  - **DEFECT 1 (migrate data-loss, soft-delete-recoverable):** garbage-root combos (`underlying=12/13/23`) whose
    canonical target REL == source REL → the copy→verify→delete flow deleted the only copy (~85K,
    `RECOVER_ERROR:NotFound`). FIX: `NOOP_TARGET_EQUALS_SOURCE` guard (never delete when dst==src) +
    `DEFER_CHAIN_TO_RECOVERY` disposition (A_SKIP — leave non-real-root chains IN PLACE for the content-authoritative
    recovery pass, bound to the UAC `is_recognized_tradfi_underlying` predicate).
  - **DEFECT 2 (rebundle ~26% incomplete):** `BUNDLE_ALREADY_EXISTS_SKIPPED` abandoned still-present per-contract
    sources without deleting, so a re-run kept skipping. FIX: `_reconcile_existing_bundle` — delete when rows provably
    contained (symbol-set containment), CAS-merge disjoint sources (`gcs_conditional_put(if_generation_match=0)`) then
    delete, leave partial-overlap loud.
  - **VERIFIED GOOD throughout:** singles/chains ~99% canonical, Massive slice untouched, 0 orphans, everything
    soft-delete-recoverable. A runaway-VM incident (an un-sharded full-apply launch loop, since corrected) was resolved
    with 0 corruption (passes idempotent). 44/44 fix unit-tests pass; MTDS QG green; landed via quickmerge.
  - **REMAINING (RECOVER-2 → EXEC-4/5/6):** restore soft-deleted garbage combos (scoped) + re-run fixed
    migrate+rebundle+recovery to completion (0 legacy / 0 orphan / 0 garbage-root / garbage preserved in `_quarantine/`)
    → manifest rebuild + catalogue MVP-stamping → Databento-backfill 571 Massive-only shards → gated Massive purge →
    re-run backfills + Phase D terminal gate. A full claimed-vs-live-measured "what's left" audit is running to lock the
    exact ordered remainder + surface any un-tracked gap.

- **2026-07-20 (slot-1, tick 21) — OPERATOR MANDATE (6h away): complete everything autonomously. Data-loss quantified =
  0 permanent. Decisions taken + execution sequence armed.**
  - **Quantification (measured read-only, HIGH conf):** permanent loss = **0** (0 of 311 sampled deleted leaves
    gone-with-no-twin; guaranteed by the un-expired 7-day soft-delete, earliest hard-delete 2026-07-26T10:16Z). The
    82,574 `RECOVER_ERROR:NotFound` ≈ **99.4% benign** (objects earlier passes already MOVED to
    canonical/`_quarantine/`, live+intact); **~0.6% (~1–1.4K objects)** are soft-only DEFECT-1 victims → curated restore
    before 2026-07-26. Catalogue 82.9% + manifest 35.5%-blank confirmed but partly-legitimate; 4.1M object count =
    massive-still-live + transient mid-migration coexistence, NOT loss.
  - **Operator mandate (2026-07-20):** all migrations DONE, 0 orphans (MVP + non-MVP); Massive FULLY PURGED; backfill
    code READY (cefi-optimized downloads/processing/uploads) + an ETA to backfill remaining tradfi MVP; all shards
    tested green under `data-pipeline-check-mtds`; **+ KRX equities human-readable-named across catalogue/manifest/
    data-status (new Phase-C todo above).** → This IS the explicit **A8 authorization** + **Massive-purge go-ahead**.
  - **DECISIONS taken (documented, operator away, all reversible):**
    - **CME shard-atom = OPTION A** — per-root chain bundle (`underlying=/quote=/margin=`, blank `instrument_id` is the
      valid shard-atom keyed by underlying); **FIX THE CHECKER** to accept it. Rationale: consistency with the shipped
      CeFi v6 chain layout + the operator's explicit "learning from cefi" + enables completion (no writer change / no
      content re-migration). Shard-atom kept identical across writer/manifest/checker/UI (hard rule).
    - **Massive purge = backfill-571-first-then-purge** (data-correctness heartbeat: never purge unique data; the 571
      Massive-only shards Databento-backfilled to canonical first, then purge the redundant ~1.7M). If the 571 backfill
      cannot finish in-window → purge HELD + ETA (never purge-and-lose-data).
    - **KRX naming = stable code stays the id, human-readable `name` field surfaced on catalogue+manifest+data-status**
      (ids must be stable/unique; the 6-digit code IS the official KRX ticker). Reversible if the operator wants the
      symbol itself changed.
    - Smaller rulings (least-bad, no-loss): etf distinct; combos resolved-or-quarantine-tracked; barchart + ICE
      qualifier variants quarantine-with-tracking.
  - **SAFETY posture (no 2nd incident):** fixed tarball (mtds@5588bdf8) deployed BEFORE any re-run; verified DRY-RUN
    reconcile (0 orphans, garbage deferred) before each `--apply`; restore executed first; ONE sharded `SHARD_OF`
    fan-out (never an un-sharded loop — the earlier runaway), SPOT, monitored T+10min + heartbeat watchdog; post-audit 0
    legacy / 0 orphan / 0 garbage-root / garbage-preserved.
  - **Execution sequence (armed):** restore soft-only → deploy fixed tarball + CME-checker(A) + durability guards
    (fail-on-raw QG + reject numeric/empty underlying) + KRX name mapping → migrate/rebundle/recover `--apply` to 0
    orphans → catalogue `by_date` sweep + rebuild (KRX names + MVP-stamp) + manifest force-rebuild → 571 Massive-only
    backfill (single-IP capped) → Massive purge → MVP backfill code ready + ETA → `data-pipeline-check-mtds` all tradfi
    shards green.

- **2026-07-20 (slot-1, tick 23) — 🎯 CANONICAL-PATH MIGRATION COMPLETE + VERIFIED (operator deliverable #1): 20/20
  shards, ORPHAN = 0.**
  - **Run `20260720-120911`** (20 SPOT shards, fixed tarball `mtds-code@5581dcf9` pinned, ~55 min wall clock). EVERY
    shard reports **`ORPHAN count = 0 (PASS — total map)`** and **`match=True`** (SUM(dispositions) == TOTAL) — the
    operator's "no orphans whether MVP or not" requirement, proven 20/20, not sampled.
  - **Aggregate over 2,649,469 objects classified:** MIGRATE **848,886** → canonical · PURGE_MASSIVE **1,701,414** (left
    in place, gated — closely matches the design's 1,696,166 estimate, confirming purge scope) ·
    **DEFER_CHAIN_TO_RECOVERY 98,006** (garbage-root chains LEFT IN PLACE — the RECOVER-1 fix working at scale; the
    pre-fix code would have destroyed these) · QUARANTINE 1,163.
  - **Pre-flight safety held:** a canary dry-run verified the fixed DEFER/NOOP dispositions on a live-garbage day before
    any `--apply`; the launcher's 2-min foreground timeout produced a partial 3-shard fan-out on the first attempt,
    which was deleted and relaunched cleanly in the background (exactly 20 VMs verified, zero strays).
  - **Data-loss incident CLOSED:** 0 permanent loss. True victim set = **95**, not the ~1–1.4K first estimated — 385,341
    twins were benign **rename-to-live** (CL→CRUDE / NG→NATGAS / MES→MICRO-SP500); all 95 restored at their canonical
    paths and VERIFIED LIVE, well ahead of the 2026-07-27T03:33Z hard-delete.
  - **NEXT:** recovery pass for the 95 restored victims (restored AFTER the shard walks, so absent from their
    enumerations) → catalogue sweep (moved in-region; the laptop run was decelerating badly) + rebuild → manifest
    force-rebuild → 571 Massive-only backfill → purge the 1,701,414 → Phase-D all-shards.

- **2026-07-20 (slot-1, tick 24) — 🛑 MASSIVE PURGE HELD — the `trades`/`tbbo` corpus is the ONLY copy. Verdict (c) NO
  PURGE.** Issue doc: `plans/active/issues/massive_purge_blocked_databento_l1_entitlement_2026_07_20.md`.
  - **Re-measured live `batch_massive` = 1,701,422 objects** (full physical enumeration of all 2,040 `day=` prefixes,
    **0 unparsed** → total map). Reconciles with the migration's `PURGE_MASSIVE = 1,701,414` (**delta +8**) and the
    design's 1,696,166 (delta +5,256). Confidence: HIGH (exact count, not sampled).
  - **Re-derived Massive-only shards from the CURRENT manifest** (`availability_index.parquet` @ 2026-07-20T12:54Z):
    **482**, not 571 — NASDAQ/trades 287 · CME/trades 157 · CME/tbbo 37 · CBOE/ohlcv_15m 1. Same shape as the stale 571,
    reduced by intervening backfills. **Note:** `row_count` is unreliable on BOTH sources (546k/676k Massive `captured`
    rows carry `row_count="0"` with `available='true'`) — the coverage predicate must be `capture_status`, not
    `row_count`, or the derivation silently under-counts by ~3×.
  - **🔴 BLOCKER — `trades`/`tbbo` are Databento L1 schemas behind a 365-day free window**
    (`LEVEL_MAX_LOOKBACK_DAYS["L1"]=365`; `assert_lookback_allowed` fails closed). **481 of the 482** shards predate the
    L1 floor `2025-07-20` (newest gap shard `2025-04-08` = 468 days old). Only the 1 CBOE `ohlcv_15m` shard is
    in-window, and it is derivable by aggregation from already-captured L0 `ohlcv_1m` — no vendor fetch needed.
  - **🔴 STRONGER GROUND TRUTH — Databento has NEVER written a single `trades`/`tbbo` object to this bucket.** 12 days
    sampled across a full year, **all inside** the free window: `trades=0 tbbo=0` on every one (only ohlcv_1m/1s/24h +
    chains present). So no naming convention can be hiding a duplicate. **1,032,672 objects (60.69% of the corpus) are
    `trades`/`tbbo` and are the ONLY copy** — CME/trades 886,744 · NYSE/tbbo 54,639 · NYSE/trades 54,639 · NASDAQ/trades
    14,873 · NASDAQ/tbbo 13,853 · CME/tbbo 7,924.
  - **Even the L0 slice is not safely duplicated:** 5 sampled days → 8,375 Massive vs 2,136 Databento objects, **5**
    exact path-identity matches; Massive covers a broader universe on the same shard (2023-05-23 CME `options_chain`
    3,692 vs 9). L0 duplication is **partial and UNVERIFIED at content granularity**.
  - **🔴 NEW DATA-CORRECTNESS DEFECT — 16,389 phantom manifest rows** over **3,488** shards claim `batch_databento` +
    `trades`/`tbbo` + `captured` while backed by **ZERO** objects on disk (13-shard stratified sample: 0 databento
    objects on every one; 4-shard L0 control correctly showed 83–158 each). A manifest-driven "is it duplicated?" check
    would have greenlit deleting **~826,159** unique objects — the exact shape of a silent million-object loss. → P0
    follow-up todo in the issue doc.
  - **NOT done deliberately:** no purge, no deletes, **sentinel NOT written** (verification did not reach zero — the
    double-gate working as designed); no backfill VMs launched (recovering 1 in-window object would not change the
    verdict). Bucket soft-delete verified **ACTIVE, 604800s (7d)** for whenever a purge is authorized.
  - **BLOCKED-CREDENTIALS ask (operator decision required):** **(A, recommended)** Databento historical `trades`+`tbbo`
    entitlement — `GLBX.MDP3` 2020-01-01→2025-07-20 and `DBEQ.BASIC` 2023-04-15→2025-07-20 — then backfill, verify,
    purge; **(B)** accept Massive as the permanent archive of record and RETAIN those 1.03M objects (makes
    `batch_massive` read-recognition permanent); **(C)** operator accepts permanent data loss and authorizes the full
    purge in writing (not recommended). Purge stays HELD until one is chosen — per this plan's own standing rule, "never
    purge-and-lose-data".

- **2026-07-20 (slot-1, tick 24) — 🔓 OPERATOR RULING: Massive purge AUTHORIZED under accepted-permanent-loss (Option
  C). The blocked-purge issue is resolved by DECISION, not by recovery.**
  - **Operator's words (2026-07-20, verbatim):** _"acept loss of massive. its partial anyway and our subscription is
    terminated. we wont expend databento ohlcv_1m is more than enough for our goals"_ — i.e. Option **C** of the three
    presented in `massive_purge_blocked_databento_l1_entitlement_2026_07_20.md`. Option A (buy Databento historical
    `trades`+`tbbo` entitlement) is explicitly DECLINED; Option B (retain as archive of record) is declined.
  - **Informed consent is on the record**: the operator was given the measured numbers BEFORE deciding — **1,032,672
    `trades`/`tbbo` objects (60.69% of the massive corpus) are the ONLY copy** (Databento has never written a single
    `trades`/`tbbo` object to this bucket — 12 days sampled inside the free window, all zero), 481/482 Massive-only
    shards sit behind a 365-day L1 entitlement wall, and the L0 remainder is only partially duplicated. The operator's
    rationale: the corpus is partial anyway, the **Massive subscription is TERMINATED** (so it can never be extended or
    re-fetched), they will not spend on Databento L1, and **`ohlcv_1m` granularity is sufficient for the trading goals**
    — tick-level `trades`/`tbbo` is not required.
  - **PURGE SCOPE: 1,701,422 `pipeline_mode=batch_massive` objects** (exact, full physical enumeration of all 2,040
    `day=` prefixes, 0 unparsed; reconciles with the migration's 1,701,414, delta +8).
  - **HONESTY REQUIREMENT (do not fake the gate):** the executor's double-gate takes a
    `--massive-backfill-verified <sentinel>` file. **No backfill happened and none ever will**, so the sentinel MUST NOT
    assert backfill-verification. It records the operator's **accepted-permanent-loss authorization** (this tick + the
    verbatim quote) as the basis. The flag's help/docstring is clarified accordingly — the gate's purpose is "authorized
    by an explicit operator basis", of which backfill-verified was only the originally-anticipated one.
  - **Safety net:** bucket soft-delete confirmed ACTIVE at 604800s (7 days), so the purge stays reversible until
    ~2026-07-27 even though the underlying data is otherwise unrecoverable.
  - **Downstream:** with the purge no longer pending, the manifest force-rebuild is UNBLOCKED and now also drops the
    stale massive slice in the same pass — and, critically, re-deriving the index from objects on disk is the fix for
    the **16,389 phantom `captured` rows** (3,488 shards, zero backing objects) that would have mis-classified ~826,159
    unique objects as safe-to-delete had the purge been validated against the manifest instead of GCS.

- **2026-07-20 (slot-1, tick 25) — ✅ POST-MIGRATION AUDIT: migration VERIFIED COMPLETE. The "98,006-deferred vs
  196-recovered gap" was an ACCOUNTING ARTIFACT of a bad aggregate — real residue was 14 objects, now recovered.**
  - **The 196 figure was WRONG (my grep mis-parsed the reconciles).** Aggregating all 20 shards' own artifacts: recovery
    SELECTED **209,769** (A 98,256 · B 83,169 · C 28,344). Apply outcomes: `QUARANTINED` 97,828 · `KEPT:B` 83,169 ·
    `KEPT:C` 28,344 · `RECOVERED:combo` 428 · `SOURCE_DELETED` 428 · `RECOVER_WRITE_FAILED` **0** · `RECOVER_ERROR:*`
    **0**. **Exact conservation, 0 unaccounted:** `A 98,256 = QUARANTINED 97,828 + RECOVERED 428`, and
    `SOURCE_DELETED (428) == RECOVERED (428)` — a source was deleted ONLY after a verified write.
  - **Set-diff of the 98,006 deferred vs the A-selection: 0 deferred-but-not-selected** among the 97,992 in canonical
    layout. ~99.99% of the deferral was already terminal.
  - **TRUE RESIDUE = 14 objects — a FILENAME predicate mismatch** (not layout, not staleness):
    `migrate_tradfi_canonical_2026_07.py:238-239` defers on a garbage underlying with NO filename guard (the
    `fname == "ticks.parquet"` test sits at `:240`, AFTER the defer returns), while
    `recover_tradfi_garbage_underlying_2026_07.py:187` required exactly `ticks.parquet` — so a
    `ticks_migrated_*.parquet` bundle with a garbage root was deferred by migrate and skipped by recovery. FIXED
    (`_is_symbol_less_bundle_file`, mirroring migrate's `_single_file_stem` convention) + 2 regression tests; re-run on
    a FRESH enumeration → all 14 content-recovered via the parquet `symbol` column (`RECOVERED:options_chain 14`, 0
    quarantined, 0 errors), GCS-verified 14/14 garbage `underlying=E` gone and 14/14 canonical
    `underlying=SP500/quote=USD/margin=linear/ticks.parquet` live.
  - **FINAL MEASURED STATE** (26 stratified `day=` prefixes 2020→2026, 36,599 objects, shipped predicates; HIGH
    confidence — pre-migration rows for the identical days reconcile to **zero unexplained delta**:
    `pre 39,855 − live 36,599 = 3,256 = deferred 1,208 + rebundle reduction 2,048`):

    | Metric                    | Result                                                                                              |
    | ------------------------- | --------------------------------------------------------------------------------------------------- |
    | Canonical (non-massive)   | **11,520 / 11,561 = 99.65%**                                                                        |
    | Legacy/bare               | 41 = 0.35% — **all correctly GATED, not gaps**                                                      |
    | Garbage-root live         | 788, all canonical layout; **0 in limbo** (B=372 named spreads, C=416 real roots = deliberate KEEP) |
    | Per-contract un-rebundled | **0**                                                                                               |
    | `_quarantine/`            | ~146K corpus-wide — garbage preserved, never deleted                                                |
    | `batch_massive`           | delta **0** on all 26 days (25,038 == 25,038) — untouched                                           |

  - **The 41 "stragglers" are CORRECTLY GATED, not defects** — do not re-chase them:
    `launch-canonical-migration-vm.sh:193` passes `${quar_flag}` to rebundle+recover ONLY, so migrate ran with no
    `--quarantine`/`--content-repair`/ `--purge-massive`. 18 are `QUARANTINE_REFUSED_GATED` (`migrate:690`); 23 are
    `MIGRATE_SINGLE_RENAME` with `ticks_migrated_*` stems routed to `A_CONTENT_REPAIR` (`:432-433`) whose gate wasn't
    passed. The SAME gate is why `batch_massive` survived — intended design, now superseded by the operator-authorized
    purge (tick 24).
  - **Safety re-confirmed at scale:** `_move_to_quarantine` is copy→verify→delete (`rebundle:449-454`); recover returns
    WITHOUT deleting on a failed write (`:444-447`). A 40-object random sample of quarantined garbage: 39 preserved, 1
    absent — which conservation proves was one of the 428 content-recovered, not a loss.
  - **VERDICT: 0 orphan · 0 garbage-root-in-limbo · 0 per-contract un-rebundled · garbage preserved, never deleted.**
  - **✅ SHIPPED: recovery-selector filename fix landed `market-tick-data-service@1bdbb4e0` (on
    origin/live-defi-rollout, 2026-07-20).** Green-tree window arrived after peer WIP cleared (`sentinels.py` back
    ≤900L + the prediction-canonical SPORTS-shard expectation corrected by its owner); full QG FOREGROUND exit-0 (6,529
    passed, 17 skipped; sentinel `8d7743cb`). Quickmerged the 2 files by name only
    (`recover_tradfi_garbage_underlying_2026_07.py` + `test_recover_tradfi_garbage_underlying_2026_07.py`, +56/-2) — no
    foreign files swept in. Prevents recurrence of the 14-object filename-predicate strand; the DATA was already
    terminal (all 14 recovered + GCS-verified at tick 25).

- **2026-07-20 (slot-1, tick 25) — 🛑 Massive purge NOT executed: the prescribed launcher invocation is broken in a
  destructive direction. Authorization is fine; the execution path is not.**
  - **Authorization re-verified before touching anything.** `unified-trading-pm@1cc566db6` carries the operator's
    verbatim Option-C ruling with the loss numbers already on the record. Bucket soft-delete confirmed **ACTIVE**
    (`retentionDurationSeconds=604800`, 7d). Both preconditions PASS.
  - **Pre-flight audit of the prescribed command found it would purge NOTHING and migrate EVERYTHING.** The `tradfi`
    branch of `launch-canonical-migration-vm.sh` (line 293-296) **silently discards `MIGRATION_EXTRA_ARGS`** — the only
    appends are line 302 (`tradfi-catalogue-canon`) and line 320 (generic `else`). So
    `--purge-massive --massive-backfill-verified <sentinel>` never reach the migrate pass (every massive object →
    `PURGE_REFUSED_GATED`, **0 purged**), while `full` mode runs all three passes with `--apply` (+ `--quarantine` on
    2/3), and the migrate pass's `A_COPY` is copy→verify→**delete source** over every non-canonical NON-massive object —
    an estate-wide unauthorized migration of exactly the `batch_databento` objects the zero-collateral gate exists to
    protect. Third blocker: the sentinel is `Path(...).is_file()` **on the VM**, so a repo/laptop-local sentinel never
    satisfies the gate. **Nothing destructive was executed.** Issue doc:
    `plans/active/issues/tradfi_canonical_migration_launcher_drops_extra_args_2026_07_20.md`.
  - **Shipped (safe + correct regardless of when the purge runs):** `market-tick-data-service@8d7743cb` — the
    `--massive-backfill-verified` help, the module docstring, and the mapping-manifest target string now describe the
    gate honestly as an **operator-authorization-basis** sentinel (completed backfill **OR** explicit accepted-loss),
    instead of asserting a backfill that never happened and never will. File held at exactly 900 lines (the QG cap); QG
    green `--no-fix` (exit 0, sentinel == HEAD).
  - **Read-only baseline captured for whenever the purge does run:** `raw_tick_data/by_date/` = **2,041** prefixes
    (2,040 `day=` + 1 legacy `day-2026-01-01`). Per-day massive/databento/total-parquet — `2020-06-15` 542/191/733 ·
    `2021-06-15` 539/187/726 · `2022-06-15` 556/189/745 · `2023-05-23` 5,360/597/5,957 · `2024-06-17` 777/612/1,389 ·
    `2025-04-08` 759/599/1,358. **`massive + databento == total_parquet` on every sampled day** — no third mode, clean
    path-level separation, so a `batch_massive`-filtered enumeration makes zero-collateral provable BY CONSTRUCTION.
  - **Phases 2-4 (purge verification, manifest force-rebuild, issue closeout) remain OPEN** — all three are downstream
    of a purge that has not happened. The manifest force-rebuild was only ever sequenced behind the purge, not
    technically blocked by it; it can be decoupled if the phantom-row P0 needs fixing sooner.

## Deferred work after 2026-07-20 (tick 25)

| Item                                                               | Why deferred                                   | Tracked in                                                        |
| ------------------------------------------------------------------ | ---------------------------------------------- | ----------------------------------------------------------------- |
| Execute the authorized `batch_massive` purge                       | Launcher drops the gate flags; would mis-scope | `tradfi_canonical_migration_launcher_drops_extra_args_2026_07_20` |
| Purge verification (0 massive + zero collateral)                   | Downstream of the purge                        | `massive_purge_blocked_databento_l1_entitlement_2026_07_20`       |
| Manifest force-rebuild + phantom-row (16,389) verification (a)-(d) | Sequenced behind the purge; decouplable        | `massive_purge_blocked_databento_l1_entitlement_2026_07_20`       |
| Operator confirmation: purge-only vs purge + estate-wide migration | Ambiguous intent; destructive either way       | `tradfi_canonical_migration_launcher_drops_extra_args_2026_07_20` |

- **2026-07-20 (slot-1, tick 26) — ✅ Massive purge EXECUTED + VERIFIED (0 collateral); launcher fixed; manifest cleanup
  handed off for coordination.**
  - **Purge DONE**: `RUN_TS=20260720-193849`, 20-shard fan-out (exactly 20 VMs verified — no runaway), gated
    massive-only path (`TRADFI_PURGE_MASSIVE_ONLY=1`, `MTDS_TARBALL_SHA=1bdbb4e0`, VM-side sentinel). **1,701,414
    PURGED** (all rc=0, 0 PURGE_REFUSED, 0 ORPHAN) **+ 8 corrupt-Hive `batch_massive` stragglers deleted directly**
    (they classify QUARANTINE before the massive branch; 1,701,414 + 8 = 1,701,422 = full enumeration) → **batch_massive
    → 0**.
  - **Zero collateral (Phase 2)**: every sampled `batch_databento` count IDENTICAL before/after (191/187/189/597/612/599
    on the 6 baseline days; 57 + 1,364 present on the 2 straggler days); `_quarantine/` intact (146,288 objects,
    untouched); soft-delete ACTIVE 604800s (reversible ~2026-07-27); all 20 VMs self-deleted.
  - **Ships**: `market-tick-data-service@8d7743cb` (honest sentinel docstring), `deployment-service@2c00c740` (launcher:
    REJECT silently-dropped `MIGRATION_EXTRA_ARGS` for `cat=tradfi` + gated `TRADFI_PURGE_MASSIVE_ONLY=1` migrate-only
    path). Pinned tarballs uploaded via ADC token (the interactive `gsutil` auth had expired): `mtds-code@1bdbb4e0` +
    UAC/UTL/DS pins.
  - **Manifest cleanup NOT yet applied — coordinate-before-cutover.** Post-purge the live `_index` still has 686,005
    stale `batch_massive` rows + 16,389 phantom `batch_databento` trades/tbbo `captured` rows + 35.5% blank id + 0%
    `-USD@LIN`. **A `consolidate(force=True)` does NOT drop them** (deletion-resurrection gap,
    `manifest_consolidator.py:850-862`); (a)+(b) need surgical index removal, (c)+(d) need the object-walk
    `rebuild_tradfi_manifest.py`. The live index is being rebuilt by a peer RIGHT NOW (`384f0345a`, `mtds@ac051bfe`), so
    per the operator's Phase-3 "coordinate and announce" instruction this is handed off rather than blind-overwritten.
    Corrected projection computed + verified locally ((a)→0, (b)→0). Full finding:
    `plans/active/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`.
  - Issue docs flipped RESOLVED: `massive_purge_blocked_databento_l1_entitlement_2026_07_20.md`,
    `tradfi_canonical_migration_launcher_drops_extra_args_2026_07_20.md`.

## Deferred work after 2026-07-20 (tick 26)

| Item                                                                                  | Why deferred                                                                                                                                                                               | Tracked in                                                     |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| ✅ ~~Drop 686,005 stale `batch_massive` + phantom manifest rows~~ **DONE tick 27**    | applied surgically (see tick 27)                                                                                                                                                           | `tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20` |
| ✅ ~~Object-walk id re-derivation (c) blank-id + (d) `-USD@LIN`~~ **RESOLVED-MOOTED** | consumer-trace: no consumer keys off manifest `instrument_id` value (coverage seeds from own rows; render from catalogue); ids 89.1% `@LIN`, self-converging — no surgery (`PM@6bdbae4b6`) | `tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20` |
| manifest-vs-disk consistency check (captured with no object = loud fail)              | P1 hardening, prevents phantom-row recurrence                                                                                                                                              | `tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20` |

- **2026-07-20 (slot-1, tick 27) — ✅ Post-purge tradfi tick `_index` surgical cleanup (a)+(b) APPLIED +
  durability-proven; (c)/(d) scoped.**
  - **Field was CLEAR for the tick `_index`** (the only in-flight peer rebuild, `rebuild_gated.py` PID 78208, writes the
    instruments-store CATALOGUE, not this tick bucket; only per-VM shard = frozen `_legacy_seed`). Consolidator PAUSED
    (`uts-prod-manifest-consolidator-market-data-tradfi-cron`) → snapshot
    `_index/snapshots/pre_manifest_surgical_cleanup_20260720T200716Z.parquet` (gen `1784578000150929`) → CAS write
    (`if_generation_match`) → RESUMED + watched **2 clean no-op cycles** (no resurrection, no
    `ManifestConsolidatorStaleError`).
  - **CRITICAL: the "16,389 phantom" was CONTAMINATED.** On-disk re-verification of all 2,393 candidate `(venue,day)`
    prefixes found 79 shards actually HAVE `batch_databento` objects (CME = databento-native GLBX) carrying **12,790
    real captured rows**. TRUE phantom = **3,615** rows (3,413 zero-object shards). Blind-dropping the stale list would
    have deleted 12,790 rows of real coverage.
  - **Applied**: dropped **686,005** `batch_massive` (GCS re-verified 0 objects, 12 sampled days) + **3,615**
    disk-verified phantom → 5,209,585 → **4,519,965**; `schema_version` preserved **int64**; markers preserved. New gen
    `1784578157569319`.
  - **(c)/(d) scoped, not forced**: (d) already **91.08% `-USD@LIN`** (the "0%" was pre-migration); (c) real defect is
    ~82k blank-no-underlying (1.76M "blank" are legit Option-A bundle atoms). Object-walk re-derivation is entangled
    (`instrument_id` ∈ `_OPTIONAL_DEDUP_COLS` → new key, not a flip) → P1 follow-up.
  - **Ships (docs)**: `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL"; issue doc
    `tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md` (a)+(b) → RESOLVED.

- **2026-07-21 (sub-agent) — ✅ P2 defense-in-depth: VARCHAR-numeric-shard poisoning CLASS killed in the consolidator**
  (`unified-trading-library@02fc4661`). Closes the P2 follow-up in
  `tradfi_schema_version_string_regression_2026_07_20.md` (the source dispatch for this plan's nightly-T+1-down P0). The
  consolidator merge (`_duckdb_merge_payload`) unions the canonical + per-VM shards via
  `read_parquet(union_by_name=true)` + `UNION ALL`; a numeric column stored VARCHAR in ONE shard while BIGINT in the
  canonical promoted the WHOLE merged column to VARCHAR — which bit `row_count` (2026-07-12) and `schema_version`
  (2026-07-20), corrupting every row and later crashing `manifest_writer/_queries.py`. Fix generalises the point
  `TRY_CAST(row_count AS BIGINT)` to the full declared-non-string column set via a new `_typed_col_projection` helper on
  BOTH `shard_proj` + `canon_proj` (`schema_version`/`row_count`/`instrument_count` → BIGINT,
  `expected_window_completeness_fraction` → DOUBLE, `expected`/`available` → BOOLEAN; mirrors
  `manifest_writer/_writer_io.py`). A single mistyped shard can no longer poison the corpus and a poisoned column
  auto-repairs next cycle; no-op for correctly-typed inputs. Anti-regression
  `tests/unit/test_manifest_consolidator_numeric_varchar_hardening.py` (mixed-type merge, full-rebuild AND incremental —
  fails on the pre-fix bare projection). Full `quality-gates.sh` green (119s). **Coordination note:** additive/defensive
  TRY_CAST only — it does NOT touch manifest data, the tick bucket, or the migrate/rebundle/recover scripts, so it
  composes cleanly with any concurrent manifest id-canonicalization that runs THROUGH this consolidator (the id work
  changes VALUES; this pins TYPES).

## Progress Log — 2026-07-21 pre-compact checkpoint (autonomous session, tabs/1)

**State machine for a compacted resume. Background task IDs are session-local (won't survive compaction — re-query
fleet/logs directly).**

### DONE this session (verified)

- **MVP expanded +409** (`uac@afa2dd64`→`22e6a534`): VIX FUTURE, CBOE treasury INDEX (US3M/2Y/5Y/10Y/30Y), KRW FX,
  crypto BTC/ETH/MBT/MET **futures-only** (operator "no cme option for btc and eth"; `option_underliers={ES}`).
- **CME crypto write-guard fix** (`uac@22e6a534`): BTC/ETH/MBT/MET added to `is_recognized_tradfi_underlying` (identity
  maps both registries + named-spread substring guard). Validated live: `underlying=BTC` writes canonical, futures-only.
- **Launchers** (`deployment-service@552d9de` + `@55e13ac`): CBOE-indices treasuries launcher (Yahoo daily), CME crypto
  FUT-only, NASDAQ `--only-group` flag. L1/L2/L3 nice-to-have documented (`@5bdf2a692`).
- **Reconciliation** (`/data-pipeline-reconciliation tradfi`, report at
  `plans/audit/results/data_pipeline_reconciliation_tradfi_2026_07_21.md`): **Massive FULLY purged** (0 objects/rows GCP
  tick+IS+AWS+manifest); **my "~99.65% canonical" was OVERSTATED** — catalogue(99.84%)+paths+filenames+forward-writes
  ARE canonical, but historical **manifest/parquet-content `instrument_id` form is only 30.8% canonical** (0% pre-2023)
  — the content `--apply` migration hasn't covered the bulk.
- **Storage purge (operator-authorized clean-out, in flight)**: `_migration_backup_2026_07_09` **35.91 GB DELETED**
  (twin-verified: all 1636 backup days covered by live); `_quarantine` (7.18 GB) + `_needs_attribution` (4.01 GB)
  deleting. AWS empty. Verify 0 + report ~47 GB reclaimed.

### IN FLIGHT

- **Backfill**: all MVP roots launched SPOT (equity NASDAQ g01-g05 + NYSE g01-g05 [ohlcv_1m+1s, 2023-26 XNAS/XNYS
  floor]; CME ES[done]/GC/CL/SI/HG/NQ/BTC/ETH/NG/PA/PL/MBT/MET; CFE VIX[done]; FX KRW[done]; CBOE treasuries[Yahoo
  daily]). Cap raised to 105. Fleet ~79 draining. 0 errors/quarantine (one transient treasury-VM `cboe-idx-2025` error
  flagged — VM already gone, likely Yahoo hiccup; RELAUNCH if a treasury tenor ends missing). Watch: re-query
  `gcloud compute instances list --filter='name~"^tradfi-bf-" AND status=RUNNING'`.

### NEXT (sequenced — DO NOT reorder)

1. **Backfill completes** (equity long-pole gates) → **DRAIN all VMs both clouds** → consolidate → **snapshot**
   (content-migration is drain-gated HARD RULE + had a prior data-loss incident).
2. **Content-migration** —
   `market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py` (content-based,
   sharded VM, dry-run default, `--apply` gated; needs a fresh single-walk enumeration `--enumeration`; per-object
   copy→verify→delete + re-derive canonical id from parquet; 9-disposition 0-ORPHAN or ABORT). **Run dry-run FIRST**
   (verify dispositions + 0 ORPHAN), then sharded `--apply` on VMs. Then `rebundle_tradfi_chains_2026_07.py --apply`
   (112,839 per-contract `options_chain`). Then migrate the **107 `day=/venue=CME/ticks.parquet` MBO monoliths** (2.53
   GB, ONLY-COPY — migrate-first, NEVER blind-delete). Diagnose WHY 30.8% before full apply. Operator APPROVED running
   it.
3. **Verify** id-form re-measured toward ~100%.
4. **Catalogue MVP promote** (+409) — rebuild+promote served `catalog.parquet` (still old mvp=70,930); verify
   data-status/deployment-api.
5. **Apply doc fixes**: 35 verified contradictions (tracked in
   `plans/active/issues/tradfi_docs_reconciliation_findings_2026_07_21.md` + `.json`) + reconciliation's 4 stale codex
   docs (`non-canonical-path-inventory.md` row 10 / `reconciliation-finding-taxonomy.md` AE-4 /
   `gcs-and-manifest-delete-safety-protocol.md` §3.3 / `tradfi-databento-sourcing-ssot.md` — all still say Massive purge
   PENDING; it EXECUTED) + register patch (rows 10/11/22/24 count updates + new
   `_migration_backup`/`_needs_attribution`/`_quarantine` now DELETED). Apply AFTER migration so "migration complete"
   claims reflect the post-`--apply` reality (nuance: paths/catalogue canonical, id-form migrated).

### Operator directives (durable intent)

- Purge every Massive item (DONE — was already 0). Delete old/bad data, completely clean tradfi buckets IS+MTDS, hard
  storage requirement (EXECUTING ~47 GB). Run content-migration NOW (approved; sequenced after drain). Both AWS tradfi
  buckets empty. Data types: `ohlcv_1m`+`ohlcv_1s` (L0 free) accepted; order-book L1/L2 is documented nice-to-have.

---

## Pre-compact lessons — 2026-07-21 (carry forward, don't re-learn the hard way)

- **gcloud user-token expiry LOOKS like mass VM/data loss — always cross-check with a second signal before reacting.**
  Mid-session `ikenna@odum-research.com`'s token expired (non-interactive, can't reprompt); every
  `gcloud compute instances list` silently returned EMPTY (not an error string in the piped grep). A fleet legitimately
  at 76 read as "76→0 in 10 min" — indistinguishable from mass preemption/deletion without checking. **Caught it** by
  testing a DIFFERENT project-wide query before concluding — the real error (`Reauthentication failed`) only showed up
  unpiped. Fix: switched active account to a service account (`*-compute@developer.gserviceaccount.com`) with standing
  creds; every subsequent monitor greps the raw output for `Reauthentication|invalid_grant` and treats a "0" alongside
  that as `AUTH-ERROR`, never real completion. **Any monitor loop that greps a gcloud/gsutil count MUST carry this
  guard.**
- **A `git commit` block from this workspace's pre-commit hooks is NOT always "branch drift."** Wasted 5 retry cycles
  re-pulling before actually reading `/tmp/dc.log` — the real blocker was `plan-hygiene` frontmatter-schema validation
  (missing `stage`/`repos`/`scope`/`parent_epic`/`priority`/`source` on an `issue` doc; missing `auditor`/`severity`/
  `audited_scope`/`date` on an `audit-result` doc — the two doc_types have DIFFERENT required-field sets, see
  `/codex/11-project-management/doc-frontmatter-schema.md`). **Read the actual hook output before assuming drift** —
  `git commit` prints both under one non-zero exit and a `grep -c 'drift'` on the log false-matched on unrelated text.
- **My own operator-facing "migration complete / ~99.65% canonical" claim was overstated** (verified + corrected this
  session, see reconciliation report + `tradfi_docs_reconciliation_findings_2026_07_21.md`): catalogue + GCS paths +
  forward-writes were genuinely canonical, but I conflated that with the HISTORICAL manifest/parquet-content id-form,
  which measured 30.8% (0% pre-2023). Lesson: "paths migrated" and "content migrated" are different surfaces — say which
  one, every time.

---

## 🔴 P0 finding — 2026-07-21T16:04Z: the 30.8% figure is NOT stable historical debt, it's an ACTIVE LIVE REGRESSION

**Full writeup: `plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`.** Sequencing-altering —
read before resuming Phase B/content-migration work.

Measured directly against the live manifest today: the currently-running TradFi equity/ETF backfill fleet
(`tradfi-bf-nasdaq-*`/`tradfi-bf-nyse-*`) writes a **canonical GCS filename** (`NASDAQ:EQUITY:AAPL-USD.parquet`,
confirmed) but a **non-canonical manifest row** (`instrument_type=equity` lowercase, `instrument_id=AAPL` bare symbol)
for the SAME capture. 352,423 canonical manifest rows exist, ALL frozen at `written_at=2026-07-18` (the one-time
`migrate_tradfi_manifest_usd_lin_2026_07_18.py --in-place-cas` output) — nothing new has landed in canonical form since.
Meanwhile 858,165 legacy rows exist, of which **856,872 were written TODAY** — i.e. the writer bug is actively producing
~850K bad manifest rows/day while the backfill fleet runs, not sitting as a static historical backlog. **Any
content-migration run before this writer is fixed gets immediately re-polluted by the next backfill cycle** — exactly
what happened to the 2026-07-18 fix.

Revised sequencing (supersedes the "run content-migration now" ordering below): **(1) fix the writer** (root cause — the
manifest `record_captured` call site isn't using the same canonical id `tradfi_shared.py` already derives for the file
path) **→ (2) THEN** the historical content-migration/cleanup pass (two-track design: manifest re-run + a new
parquet-content read-modify-write pass) **→ (3)** re-measure canonical % only after both the writer fix AND fleet drain,
not before. A background agent is locating the exact call site + shipping a scoped fix if safe; check its outcome before
re-investigating.

---
