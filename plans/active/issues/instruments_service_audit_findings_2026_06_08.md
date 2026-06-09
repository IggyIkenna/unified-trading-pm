---
title:
  instruments-service audit findings (download→manifest) — CF-11 swallows, removed-provider still wired, silent excepts
created: 2026-06-08
author: harsh
source:
  - plans/audit/results/instruments_master_audit_2026_06_08.md
locked_by: live-defi-rollout
---

# instruments-service audit findings — actionable remediation

Surfaced by the 2026-06-08 full-chain audit (`plans/audit/results/instruments_master_audit_2026_06_08.md`). The
production runtime is mostly sound; these are the actionable items, severity-ordered. Repo: `instruments-service` unless
noted.

## What I found / Why it matters / Recommended decision

### 🔴 P0 — fetch errors swallowed into honest-empty (CF-11 gap a prior pass missed)

A swallowed fetch error mislabeled as `empty_confirmed` pollutes the IS manifest → MTDS reads it and wrongly treats the
cell as `expected_unattempted`/skip. The 2026-06-03 cross-AG CF-11 pass fixed cefi/sports/defi but missed these:

- [ ] [MTDS] P0. `prediction/kalshi.py` — `_fetch_markets_page` emits `ADAPTER_FETCH_FAILED` then `return [], None`;
      `get_instruments:130-133` returns `[]` with no raise. Re-raise when all pages failed (tardis/deribit_combo "raise
      iff `not results and failures`" pattern) so an outage/auth-fail writes `attempted_failed`, not empty. Repo:
      instruments-service.
- [ ] [MTDS] P0. `tradfi/ibkr.py:337-348` — `except Exception: … return []` per symbol with no classify/event/raise.
      Classify via `classify_venue_error`, emit `ADAPTER_FETCH_FAILED`, re-raise on all-failed so a mid-batch IB socket
      death surfaces as `attempted_failed` not a silently-shrunk universe. Repo: instruments-service.

### 🔴 P0 — removed provider still wired alongside its replacement

- [ ] [MTDS] P0. **Delete `tradfi/polygon.py` + its wiring.** Polygon.io is a REMOVED TradFi provider (CLAUDE.md) and
      its rebrand `tradfi/massive.py` exists alongside it (parallel old+new path, banned). `polygon.py` is still
      imported + registered in `reference_data/factory.py:75,130,314,346` + `router.py`, and it ALSO swallows fetch
      errors (`:286-354` `aiohttp.ClientError → return []`/`None`, no classify/event/raise). Remove the adapter +
      factory/router entries; confirm no consumer resolves `"polygon"`/`"POLYGON"` (massive is the replacement). Repo:
      instruments-service. (Deleting it moots the swallow.)

### 🔴 P1 — silent `except: pass` masks GCS errors as absence

- [ ] [MTDS] P1. `engine/orchestrator.py:3794, 7673, 7821` — `except Exception: pass` swallows ALL exceptions on the
      canonical-vs-legacy GCS blob-existence probe (`:3794` then silently returns the legacy path) + weather merge.
      Catch `NotFound` specifically; let unexpected raise (honest-absence / no-silent-failure). Also resolve the related
      `:3791` `# type: ignore[union-attr]` hiding a possibly-`None` storage client. Repo: instruments-service.

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

- [ ] [CLAUDE.md] P2. Correct the over-broad "instruments-service owns all venue URLs via `InstrumentRecord`" line —
      `InstrumentRecord` carries only `source_archive_url_template` + coverage windows; live REST/WS endpoints are UAC
      registries (codex SSOT is accurate). Prevents agents hunting for a nonexistent field.
- [ ] [AUDIT] P2. Fix `instruments_master_audit_instructions.md` item (g): "`rg URDI` → 0 hits" is factually wrong —
      `urdi_reference_provider.py` is the LIVE fetch spine ("URDI" = the folded-in repo's legacy label). Replace with:
      no NEW URDI references / fix the stale error message at `urdi_reference_provider.py:116` (points to deleted repo).
