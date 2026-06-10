---
title:
  instruments-service audit findings (download→manifest) — CF-11 swallows, removed-provider still wired, silent excepts
created: 2026-06-08
source:
  - plans/audit/results/instruments_master_audit_2026_06_08.md
locked_by: live-defi-rollout
priority: P2
status: active
---

# instruments-service audit findings — actionable remediation

Surfaced by the 2026-06-08 full-chain audit (`plans/audit/results/instruments_master_audit_2026_06_08.md`). The
production runtime is mostly sound; these are the actionable items, severity-ordered. Repo: `instruments-service` unless
noted.

## What I found / Why it matters / Recommended decision

> **⚠️ CLOSER-LOOK CORRECTION (2026-06-08, traced end-to-end to avoid false positives).** The swallow→manifest chain is:
> adapter swallows + `return []` → `engine/urdi_reference_provider._fetch_one` only appends to `failed[]` on a RAISE, so
> a swallow is **invisible to `failed_venues`** → orchestrator `_non_error_venues` includes it →
> `empty_ok_venues = (_non_error_venues − written_venues) − validation_failed_venues` (`orchestrator.py:2998`) →
> **`expected_venues -= empty_ok_venues` (`:3006`)** → the venue is **silently EXCLUDED from the expected denominator**
> (NOT recorded `attempted_failed`, NOT retried, coverage % inflated). [Earlier wording "records a clean empty" was > >
>
> > imprecise — it's exclusion-from-denominator, same root, slightly different effect.] **Reachability matters**:
> > `_TRADFI_VENUES = [CME, NASDAQ, NYSE, CBOE, ICE, FX]` — neither `polygon` nor `ibkr` is a live venue, so their
> > adapters are **dead-registered (never invoked)** → their swallow is UNREACHABLE today. Only **kalshi** (prediction
> > enumeration) is on a reachable path.

> **STATUS 2026-06-09 — SHIPPED:** kalshi CF-11 fix landed on LDR via quickmerge once staging unlocked
> (`instruments-service@229dcc4`); riding the LDR→staging drain PR #418 to staging → main. The recurring
> version-alignment false-block that delayed it is FIXED (`unified-trading-pm@a428a3515` — `version-alignment-gate.sh`
> now compares like-for-like). The deeper semver-agent `[skip ci]` promotion-block root cause (which kept staging
> re-locking) is written up for review in [[semver_version_bump_skip_ci_promotion_block_2026_06_09]]
> (`plans/active/issues/`).

### 🔴 P0 — fetch error swallowed into not-failed (CF-11) — kalshi (the one REACHABLE case)

- [x] ✅ [MTDS] P0. `prediction/kalshi.py` — `_fetch_markets_page` emits `ADAPTER_FETCH_FAILED` then `return [], None`;
      `get_instruments:130-133` returns `[]` with no raise → not in `failed_venues` → excluded from the expected
      denominator (no `attempted_failed`, no retry). Re-raise when all pages failed (tardis/deribit_combo "raise iff
      `not results and failures`" pattern). Repo: instruments-service. (Caveat: kalshi may be pre-activation as an
      active prediction venue — the fix is correct regardless and prevents a silent gap once it activates.) —
      `instruments-service@229dcc4` | `_fetch_markets_page` raises RuntimeError on 401/transport; `get_instruments`
      re-raises on all-failed | regression: `tests/unit/test_kalshi_adapter.py` (401 + transport-error raise) +
      `tests/unit/test_prediction_adapters_comprehensive.py` (TestKalshiFetchMarketsPage raise) | QG green (sentinel
      79d1acb).

### 🔴 P0 — removed provider dead-registered alongside its replacement → DELETE

- [x] ✅ [MTDS] P0. **Delete `tradfi/polygon.py` + its wiring (dead code, safe).** Polygon.io is a REMOVED TradFi
      provider (CLAUDE.md); its rebrand `tradfi/massive.py` is the live adapter. CLOSER LOOK: `polygon` is registered in
      `factory.py` `ADAPTER_DATA_SOURCES` (`:346`) + the class map (`:314`) but **NOT in `_TRADFI_VENUES`** (which is
      the live tradfi enumeration → databento/massive only) → `polygon.py` is **never invoked** = pure dead
      registration. Delete the adapter + `factory.py:75,130,314,346` + `router.py` import. Deletion is low-risk (nothing
      resolves to it) and moots its (unreachable) swallow + bar-edge-fallback. Repo: instruments-service. — **SHIPPED
      instruments-service@3872848 (wiring + tests: factory/router/6 test files,
      `test_betfair_polygon_polymarket_adapter.py` → `test_betfair_polymarket_adapter.py`) + @effa781 (the 2 file
      deletions — split because quickmerge `--files`'s `[ -e path ]` guard cannot stage deletions; bug filed in
      `quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md` Phase 2). QG green (full suite incl. 3232
      tests); guardrails held: Beefy Polygon-L2 entries + Massive's polygon.io-compatible base URL untouched.
      2026-06-10.**

### 🟡 P2 — ibkr swallow (LATENT — dead-registered) + adapter hardening

- [ ] [MTDS] P2. `tradfi/ibkr.py:337-348` — per-symbol `except Exception: return []` is CORRECT shard-isolation; the gap
      is only the systemic case (`_ib is None` / all-symbols-fail → `get_instruments` returns `[]` with no raise → same
      exclusion-from-denominator). **LATENT**: `IBKR` is not in `_TRADFI_VENUES` → the adapter is not invoked in the
      live tradfi path today. Harden (classify + re-raise on systemic failure) when/if IBKR becomes a live reference
      venue; not urgent. Repo: instruments-service.

### 🟡 P2 — too-broad `except Exception: pass` (DOWNGRADED from 🔴 — low blast radius, not heartbeat)

- [ ] [MTDS] P2. `engine/orchestrator.py:3794, 7821` — narrow the broad excepts: `:3794` swallows all exceptions on a
      canonical-vs-legacy GCS blob-existence probe (Phase-E8 migration read-helper) then silently returns the legacy
      path — catch `NotFound` specifically, let auth/network raise (also fix the `:3791` `# type: ignore[union-attr]`
      possibly-`None` client); `:7821` swallows weather-merge errors then writes new-only (possible merge-skip). **NOTE:
      `:7673` is NOT a bug** — "couldn't read existing weather → fetch everything" is a safe fallback (worst case: a
      redundant fetch), leave it. These are sports/weather-enrichment + a transitional read-helper, not the market-data
      heartbeat. Repo: instruments-service.

### 🟡 P2 — smells / risk

- [ ] [MTDS] P2. Residual bar-edge fallback-to-open: `cefi/hyperliquid.py:257` (`candle.get("T") or candle.get("t")`
      falls to open if `T` is 0/missing); `cefi/ccxt_adapter.py:310-312` + `tradfi/polygon.py:243` fall back to
      `open_ts` for `interval not in BAR_TIMEFRAMES`. Make the close-edge derivation total (raise/skip on unknown
      timeframe rather than silently using the open edge). (Headline IS-refdata edge bugs already FIXED — Ikenna slot-7
      2026-06-08.) Repo: instruments-service. (If polygon.py is deleted per above, drop its part.)
- [ ] [UTL] P2. Confirm UTL `record_captured_from_counts` auto-stamps `default_source` for single-source cells — else
      the 9 IS callsites (`orchestrator.py:1730,1916,2080,2693,3588,6910,7702,7895,8137`) write blank-source captured
      cells (CF-4 RED). If UTL does NOT auto-stamp, thread `source=` at each callsite. Repo: unified-trading-library
      (verify) + instruments-service (thread if needed).
- [ ] [MTDS] P2. `engine/orchestrator.py:4271` `_af_record_empty(reason="")` — make `reason` a required typed
      `EmptyConfirmedReason` (latent `LegacyBlankErrorReasonError` footgun). Repo: instruments-service.
- [ ] [INFRA] P2. Prediction catalogue bucket mismatch:
      `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf:40-44` targets `instruments-store-prediction-…`
      vs SSOT `instruments-store-PRED-…`. Reconcile so the prediction catalogue job hits the SSOT bucket. Repo:
      deployment-service.
- [ ] [MTDS] P2. De-duplicate the IS venue universe: `orchestrator.py:1028 _CEFI_VENUES`/`_TRADFI_VENUES`/`_DEFI_VENUES`
      duplicate UAC `VENUES_BY_ASSET_GROUP` (the enumerator's source) → drift risk. Make the fetch path read the UAC
      registry. Repo: instruments-service.
- [ ] [MTDS] P2. Replace `os.environ["DEPLOYMENT_ENV"]="test"` runtime mutation (`orchestrator.py:8033-8041`,
      `sports_dependency.py:90-98`) with an explicit `env=` param to `resolve_bucket_name` (thread-safety). Repo:
      instruments-service (+ UTL if the param doesn't exist).

### 🟡 P3 — hygiene / systemic

- [ ] [MTDS] P3. Investigate the systemic schema-drift dup the script `scripts/dedupe_manifest_schema_drift.py:1-18`
      documents (16% of shards have >1 manifest row: multi-schema-version + instrument_type casing
      `perpetual`/`PERPETUAL`/`""` + capture_status collisions). Fix the WRITER-side row-key idempotency +
      instrument_type normalization so the dedupe/phantom scripts stop being needed (~76 of 96 scripts are
      manifest-repair). Repo: unified-trading-library (writer) + instruments-service (scripts).
- [ ] [MTDS] P3. Split `engine/orchestrator.py` (8,192 lines, 9× the 900 cap) into focused modules
      (buckets/emission/weather/fixtures/manifest). Repo: instruments-service.
- [ ] [SCRIPT] P3. Script-tier cloud-agnostic sweep: ~60 scripts `from google.cloud import storage`/`boto3` directly →
      `get_storage_client()`; ~30 inline legacy `instruments-store-{ag}-{pid}` (some hardcode `central-element-323112`)
      → `resolve_bucket_name`; `enumerate_expected_universe.py:1381` hardcoded `/tmp/` → `tempfile.gettempdir()`. Repo:
      instruments-service.
- [ ] [PLAN] P3. Delete orphaned static-snapshot catalogue path (`reference_data/catalogue/catalogue_builder.py`
      `CatalogueBuilder` + `orchestrator.py refresh_catalogue`) — superseded by `build_instrument_catalogue.py`, no
      CLI/TF/test caller (parallel old+new). Repo: instruments-service.

### 📝 Doc fixes (PM)

- [ ] [CLAUDE-MD] P2. Correct the over-broad "instruments-service owns all venue URLs via `InstrumentRecord`" line —
      `InstrumentRecord` carries only `source_archive_url_template` + coverage windows; live REST/WS endpoints are UAC
      registries (codex SSOT is accurate). Prevents agents hunting for a nonexistent field.
- [ ] [AUDIT] P2. Fix `instruments_master_audit_instructions.md` item (g): "`rg URDI` → 0 hits" is factually wrong —
      `urdi_reference_provider.py` is the LIVE fetch spine ("URDI" = the folded-in repo's legacy label). Replace with:
      no NEW URDI references / fix the stale error message at `urdi_reference_provider.py:116` (points to deleted repo).
