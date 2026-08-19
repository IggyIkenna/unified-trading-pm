---
doc_type: issue
title:
  Tardis options_chain adapter was genuinely unblocked (credential resolvable) but never wired to any dispatch
  entry — implemented + wired now; separately, the live Deribit options-chain handler had its own unrelated
  bucket-domain bug that would have crashed every write
summary: |
  Operator reported "tardis api key issue is solved" and asked to fix the resulting BLOCKED-CREDENTIALS scaffold
  (`tardis_options_adapter.py`, Phase D P1c Item 3, shipped 2026-06-15, never touched since). Verified the credential
  claim first rather than trusting it: the `tardis-api-key` Secret Manager secret IS genuinely resolvable (confirmed
  live via `get_secret_client()`, 88-char value, `TD.` prefix consistent with a real Tardis key — not the
  `TD.test-key-for-unit-tests` dummy `conftest.py` sets for unit-test config bootstrapping). Implemented
  `TardisOptionsClient.fetch_options_chain` for real (composes `TardisStreamClient` for session/auth/429-5xx-retry,
  downloads Tardis's grouped `OPTIONS.csv.gz` per `docs.tardis.dev/downloadable-csv-files#options_chain`, honest-
  absence on 404/structural-400), removed the credential gate (now resolves via Secret Manager with the raise kept as
  a real empty-resolution safety net), and — per item 4 of the dispatch — found this adapter had ZERO callers
  anywhere in the codebase outside its own module and test file, so built `TardisOptionsChainBackfillHandler` and
  registered `--operation collect-tardis-options-chain` in `cli/main.py`'s dispatcher (the same "handler built, never
  wired" gap class already seen once for `deribit-options-chain` (C5, 2026-07-06) and `collect-governance-proposals`).

  Investigated whether this adapter was actually redundant before touching it (a live hypothesis worth ruling out,
  not assumed): `TardisAdapter`'s own `options_chain`/`futures_chain` `_BULK_DOWNLOAD_SYMBOLS` handling
  (`adapters/tradfi/tardis_adapter.py`) uses `options_chain` purely as a Tardis URL grouping filter to bulk-download
  TRADES for every options instrument (writes `data_type=trades`, `instrument_type=options_chain` — its own code
  comment says so explicitly). That is NOT the same Tardis data channel this adapter implements — the periodic
  mark-price/IV/greeks snapshot channel matching `CanonicalOptionsChainEntry`'s `implied_volatility`/`delta`/`gamma`/
  `theta`/`vega` fields, which the live Deribit handler (`deribit_options_chain_handler.py`) also produces. The two
  are not redundant; before this fix there was genuinely NO working batch path for the snapshot channel.

  Also found (bounded 20-day GCS check, `market-data-tick-cefi-prd-*` bucket, both candidate pipeline_modes) that
  ZERO `options_chain` shards for DERIBIT existed via EITHER path — batch Tardis (this adapter, was unimplemented) OR
  live Deribit (`deribit_options_chain_handler.py`, IS registered/dispatchable but had an unrelated real bug: its
  bucket-domain call used the retired kind-token `"tick-data"` instead of the underscored domain `"market_data"`,
  which `get_write_bucket_name`/`get_bucket_name` raises `BucketNamingError` on — so it would crash on every write
  attempt regardless of being wired). Fixed that 2-line bug in the same pass since it's directly adjacent (same
  feature, same-day discovery, ~5-line fix) and blocks the very capability this task is about.

  Corrected a stale operator-ping claim while at it: `ikenna_orchestrator/pings/slot_1.md`'s 2026-08-08
  round5-cross-cutting-audit line asserted "DERIBIT-COMBO + OKX options_chain Tardis data flowing" — that was
  already incorrect when written (`DERIBIT-COMBO` was deregistered from `VENUES_BY_ASSET_GROUP` 2026-07-23, BEFORE
  that audit ran; bare `OKX` was deregistered 2026-08-04 with no `OKX-OPTIONS` successor — there is no registered
  OKX options venue at all as of 2026-08-16). **CORRECTED 2026-08-18 (plan_reconciler)**: date was previously
  2026-08-05; the actual removal commit is `unified-api-contracts@d67a226f` ("fix(cefi): remove bare OKX from the
  venue registry...", verified via `git log`) timestamped 2026-08-04T08:38:12Z — matches
  `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`'s independently-cited 2026-08-04 date.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tardis, options-chain, credential-unblock, dispatch-gap, bucket-naming-bug, cefi, deribit]
related:
  [
    /plans/active/v2_engine_venue_buildout_2026_06_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-16
priority: P1
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Operator directly confirmed "tardis api key issue is solved! no more blocked credentials for tardis" + "need to
  fix that" mid-session under `/autonomous`; investigated, implemented, tested, and shipped autonomously per operator
  authorization (SUB_AGENT_MANDATORY_RULES.md + AUTONOMOUS_AGENT_RULES.md applied for the duration).
drift_direction: advance-code
context_scope: [market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_options_adapter.py, market-tick-data-service/market_tick_data_service/market_interface/clients/tardis_base_client.py, market-tick-data-service/market_tick_data_service/market_interface/clients/tardis_stream_client.py, market-tick-data-service/market_tick_data_service/cli/handlers/tardis_options_chain_backfill_handler.py, market-tick-data-service/market_tick_data_service/cli/handlers/deribit_options_chain_handler.py, market-tick-data-service/market_tick_data_service/cli/main.py]
---

# Tardis options_chain adapter — credential unblock, real implementation, dispatch wiring

## Credential verification (item 1 — do not trust, verify)

Ran a `.venv` script (no key value ever printed/logged) that called
`get_secret_client().get_secret("tardis-api-key")` — the exact secret name `TardisClientConfig.secret_name` defaults
to and the same one the already-working `TardisBaseClient.api_key` property resolves. Result: **resolvable**, 88
characters, `TD.` prefix — consistent with a real Tardis API key shape and clearly NOT the
`TD.test-key-for-unit-tests` dummy the root `conftest.py` sets via `setdefault` purely to stop module-level config
loading from failing in unit tests. The operator's claim was correct.

## What was implemented

- `TardisOptionsClient.__init__` — no longer unconditionally raises. Resolves `api_key` via an explicit constructor
  arg first, else `_resolve_tardis_api_key()` (module-level helper, mirrors `TardisBaseClient.api_key`'s Secret
  Manager read). `TardisCredentialsNotConfiguredError` is now a REAL safety net (only fires when resolution
  genuinely comes back empty — e.g. a future rotation/revocation), not a standing gate.
- `TardisOptionsClient.fetch_options_chain(exchange, underlying, target_date)` — real implementation. Composes
  `TardisStreamClient` (no bespoke HTTP/auth/retry logic — reuses its proven 429/5xx exponential-backoff
  `async_get_bytes`). Downloads Tardis's grouped `OPTIONS.csv.gz` bulk file
  (`{datasets_base_url}/{exchange}/options_chain/{YYYY}/{MM}/{DD}/OPTIONS.csv.gz` — the same URL shape
  `TardisAdapter._build_tardis_csv_url` uses for its own, DIFFERENT, options bulk-trades download), gzip-decompresses
  + CSV-parses via pandas, filters to the requested `underlying`. HTTP 404 and structural-absence 400 (Tardis code
  140/300, via the already-proven `TardisHTTPError.is_structural_absence`) return `[]` (honest absence); every other
  non-200 raises `TardisHTTPError` for the caller to classify.
- `classify_and_emit_tardis_error` — dropped the hardcoded `"status": "BLOCKED-CREDENTIALS"` detail field (stale
  now that the path is live).
- **New**: `TardisOptionsChainBackfillHandler`
  (`cli/handlers/tardis_options_chain_backfill_handler.py`) — BATCH per-day handler, modeled on
  `DeribitVolatilityIndexHandler`'s proven per-day-dispatch/manifest/bucket pattern and
  `deribit_options_chain_handler.py`'s v6 chain-bundle write path (`build_cefi_partition_path`,
  `derive_settlement_dimensions`, read-merge-write fan-in). `pipeline_mode=BATCH_TARDIS`, `source="tardis"`,
  currencies BTC/ETH (DERIBIT is the only Tardis-registered CeFi venue with a live options market — see the OKX
  finding below). Shard isolation per-currency, no `raise` in the loop, errors routed through
  `classify_and_emit_tardis_error` + `recorder.record_failed`.
- **New CLI operation**: `--operation collect-tardis-options-chain --mode batch --asset-group cefi --start-date
  --end-date`, registered in `cli/main.py`'s `operations` dict (import + entry, alongside the existing
  `deribit-options-chain` / `collect-deribit-volatility-index` entries).

## Adjacent bug fixed in the same pass: live Deribit handler's bucket domain

`deribit_options_chain_handler.py::process` called `get_write_bucket_name("tick-data", "cefi")`. `"tick-data"` is a
retired yaml KIND token, not a valid underscored DOMAIN key — `get_bucket_name` raises `BucketNamingError: unknown
bucket domain 'tick-data'` (confirmed live). This handler IS registered in the dispatcher (`"deribit-options-chain"`)
so it's reachable, but every real invocation would crash on the first write, meaning options_chain could never have
been captured via the live path either. Fixed to `get_write_bucket_name("market_data", "cefi")` — the correct
domain, verified live to resolve to `market-data-tick-cefi-{env}-central-element-323112`, matching
`DeribitVolatilityIndexHandler`'s already-correct `resolve_bucket_name(kind="market-data", ...)` call. Only 2 files
in the whole repo used the stale `"tick-data"` string with `get_write_bucket_name`/`get_bucket_name`; the other one,
`adapters/tradfi/yahoo_finance_adapter.py`, is unrelated (TradFi, not CeFi/Tardis) and out of this task's scope —
flagged as a follow-up below rather than fixed here.

## Production data-flow check (proves the gap was real, not hypothetical)

Bounded GCS check (NOT a full-corpus walk — 20 specific recent days x 2 pipeline_modes x DERIBIT, single API call
each) against the prod bucket `market-data-tick-cefi-prd-central-element-323112`: **zero** `options_chain` shards
found for DERIBIT via `pipeline_mode=batch_tardis` or `pipeline_mode=live_deribit` in the last 20 days. Confirms
neither path had ever successfully written data — consistent with (a) this adapter never being implemented/wired
and (b) the live handler's bucket bug making it a permanent no-op even though registered.

`VENUES_BY_ASSET_GROUP` check: `OKX` (bare) has no options-capable successor venue (`OKX-FUTURES`/`OKX-SPOT`/
`OKX-SWAP` only) — DERIBIT is the only Tardis-registered CeFi options venue right now.

## Test evidence

- `tests/market_interface/adapters/cefi/test_tardis_options_adapter.py` — updated credential-guard tests (now
  monkeypatch `_resolve_tardis_api_key` instead of asserting an unconditional raise); new `TestFetchOptionsChain`
  class covering: parse + underlying filter, 404 → `[]`, structural-absence 400 → `[]`, genuine 5xx → raises
  `TardisHTTPError`, empty-payload → `[]`. All mocked (`_FakeStreamClient`), no network.
- `tests/unit/test_tardis_options_chain_backfill_handler.py` — new file, mirrors
  `test_deribit_options_chain_handler.py`'s `_StubStorage`/`_write_shard` pattern (v6 canonical path + chain fan-in)
  plus `_collect_currency_day`'s three routing branches (captured / zero-rows / failed) against a fake client.
- **Real integration run** (by hand, not wired into default QG — `@pytest.mark.requires_credentials` skip preserved):
  constructed a real `TardisOptionsClient()` (genuine Secret Manager resolution, no explicit key) and called
  `fetch_options_chain("deribit", "BTC", date(2026, 8, 10))` against the live Tardis API. Result: **inconclusive, not
  a code-contract failure**. `TardisStreamClient`'s warmup (small auth'd GET to `api.tardis.dev/exchanges`) succeeded
  immediately, proving the credential + auth-header path works end-to-end. The actual `OPTIONS.csv.gz` bulk download
  then timed out on all 3 retry attempts (`aiohttp` `TimeoutError`, zero bytes ever received, ~5 min per attempt —
  `TardisClientConfig.read_timeout=300s` — over a ~15-minute total wall-clock window) and `fetch_options_chain`
  correctly propagated the exhausted-retries `TimeoutError` (no silent swallow). This file is genuinely large
  (codebase's own comments cite 300 MB+ for a heavy DERIBIT options day) and this attempt ran from an interactive
  dev sandbox, not a properly-provisioned backfill VM — the same URL shape, auth pattern, and
  `TardisStreamClient.async_get_bytes` retry machinery this call reuses are already proven in production by
  `TardisAdapter`'s own (different) bulk options/futures downloads, so a code-level contract mismatch is unlikely.
  Treat this as **unverified against a real large download in this environment** — recommend one real attempt from
  an actual backfill VM (not a dev sandbox) before trusting this at scale; do not read the mocked unit-test pass as
  proof the live download completes.
- Full `bash scripts/quality-gates.sh` (repo `.venv`) run for market-tick-data-service: **PASSED** — "✅ ALL QUALITY
  GATES PASSED" (5 iterations to get there: import-order lint auto-fixed via `ruff --fix`; a 55-line
  `fetch_options_chain` method over the 50-line method-size cap fixed by extracting `_build_options_chain_url`/
  `_options_chain_rows_or_raise` helpers; the cross-repo `adapter_contract_baseline.yaml` ratchet — see below — one
  genuine host-contention timeout retried clean). Shipped
  `market-tick-data-service@3105f17711` (6 files: adapter, new handler, `deribit_options_chain_handler.py` bucket
  fix, `cli/main.py` dispatch wiring, both test files).

## Cross-repo shipping notes (unified-trading-pm)

- `scripts/quality_gates/adapter_contract_baseline.yaml`: this file's `tardis_options_adapter.py` entry (count: 10)
  predated this session and was already stale relative to the pre-fix scaffold — regenerating after the real
  implementation legitimately dropped the count to 8 (the reduction is entirely in trimmed docstring text, not a
  dropped `classify_venue_error`/`ADAPTER_FETCH_FAILED` call — both real call sites are still present and exercised
  by the mocked unit tests). Fixed via a full-workspace `--regenerate-baseline` run, verified only 2 other files'
  counts moved (both increases, safe for a shrink-only ratchet) before shipping. Shipped
  `unified-trading-pm@fc1ff3612a`.
- `scripts/quality_gates/reachability_gate_baseline.json`: unrelated pre-existing drift hit while shipping —
  `execution-service:defi_protocols`'s `SymbioticConnector` had become reachable (good — something wired it up) but
  the shrink-only baseline still listed it, hard-failing quickmerge's post-gate re-validation for ANY PM commit.
  Removed the single stale entry per the checker's own remedy text. Shipped `unified-trading-pm@bb6faddbf7`.
- **A real data-loss near-miss worth recording**: an earlier `--isolated` quickmerge attempt for this doc's own
  `adapter_contract_baseline.yaml` + `slot_1.md` edits reported `✅ Landed` but the landed commit
  (`unified-trading-pm@bb6faddbf7`) only actually contained 2 of the 4 named `--files` — the baseline fix and the
  slot_1 ping silently never made it into that commit despite a clean exit. Recovered from a leftover
  `qm-iso-evac-<pid>-*` stash entry from that same attempt (confirmed mine via the PID, confirmed content via `git
  stash show -p` before popping), re-verified, and re-shipped successfully as
  `unified-trading-pm@fc1ff3612a`. Exactly the "`ahead=0` + clean tree ≠ landed" failure mode CLAUDE.md's ship-
  discipline section warns about — worth a broader audit of `--isolated` + multi-file `--files` interaction if this
  recurs.

## Recommended next step — NOT executed here (explicitly out of scope)

A real historical backfill for `(cefi, DERIBIT, options_chain, source=tardis)` is now dispatchable
(`--operation collect-tardis-options-chain --mode batch --asset-group cefi --venues DERIBIT --start-date <D>
--end-date <D>`) but has NOT been launched. Rough scope: 2 currencies (BTC, ETH) x however many days back the
operator wants covered (Deribit options history goes back to ~2016; a reasonable first pass mirrors the DVOL
handler's "connectivity-test only" precedent — a bounded trailing window, not the full history, as a separate
operator-authorized VM launch). Per `/codex/05-infrastructure/vm-launcher-runbook.md`, this is a genuine backfill
(heavy I/O, real cost) and should be a deliberate, separately-authorized dispatch, not a side effect of shipping the
adapter fix.

## Follow-ups (not fixed in this pass)

- [ ] [AGENT] P3. `adapters/tradfi/yahoo_finance_adapter.py` has the same `get_write_bucket_name("tick-data", ...)` stale-
      domain bug found in `deribit_options_chain_handler.py` — unrelated to CeFi/Tardis, needs its own verification
      of Yahoo-adapter behavior before fixing. market-tick-data-service.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
