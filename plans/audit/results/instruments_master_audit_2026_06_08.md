---
type: audit-result
epic: instruments_master
instructions_ref: plans/audit/instructions/instruments_master_audit_instructions.md (items a–h, CF-1…CF-14)
auditor: harsh (interactive, hk laptop)
date: 2026-06-08
status: complete
method:
  code-state — 4 parallel read-only sub-agents (adapters/download · manifest+schema · catalogue/universe/contract ·
  standards/hygiene) + first-hand verification of the top findings + git-log reconciliation. Data-state reads deferred
  (laptop host; flagged where they'd confirm).
---

# instruments-service audit — full chain (download → manifest versions) — 2026-06-08

Operator (Harsh) asked for a broad "anything suspicious" sweep across every angle from data download to manifest
versions. Audited against the existing `instruments_master_audit_instructions.md` (instruments is the canonical-form
ROOT, owns CF-1…CF-14). Four read-only sub-agents + first-hand verification of the load-bearing findings.

## Verdict

**The production runtime is mostly sound** — the canonical-form core (schema_version, expected_unattempted, multi-source
FIXTURES, validity-matrix, Era-B bundle-grain, daily-listing) is well-engineered and the bar-edge bugs from this
morning's sweep were already fixed by a teammate. The real issues are **(1) three adapters still swallow fetch errors
into honest-empty** (CF-11 gap a prior pass missed), **(2) a removed provider (`polygon.py`) is still wired alongside
its replacement (`massive.py`)**, **(3) silent `except: pass` in the orchestrator masks GCS errors as absence**, and a
broad tail of **hygiene debt concentrated in one 8,192-line god-module + a 96-script repair sprawl**. Nothing here is a
live trading-data-corruption incident; the CF-11 swallows are the highest-priority correctness items.

## Angle coverage + verdict

| Angle                                                       | Verdict                                                                                                                   |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Download / adapters (error handling, auth, edge, isolation) | 🟡 — 3 CF-11 swallows remain; bar-edge FIXED; auth/isolation clean                                                        |
| Manifest + schema versions                                  | 🟢 core clean (v9 migrator + schema_version read actual distribution) / 🟡 script sprawl + systemic schema-drift band-aid |
| Catalogue / universe / IS→MTDS contract                     | 🟢 catalogue+enumerate correct / 🟡 URDI naming, dead duplicate catalogue, hardcoded universe dup, CLAUDE.md over-claim   |
| Standards / hygiene / bucket naming                         | 🟡 — one 8,192-line god-module + 3 silent excepts; scripts carry the cloud-SDK/`/tmp` tail                                |

---

## 🔴 Findings (correctness — fix first)

1. **CF-11 swallow — `prediction/kalshi.py` (verified).** `_fetch_markets_page` emits `ADAPTER_FETCH_FAILED` on 401 /
   `aiohttp.ClientError` but `return [], None`; `get_instruments` (`:130-133`) just `extend([])` + breaks → returns `[]`
   with **NO raise**. A Kalshi outage/auth-fail records a **clean empty** in the IS manifest → MTDS trusts it as
   `expected_unattempted`/skip. Kalshi is the one prediction/cefi adapter the 2026-06-03 CF-11 pass missed. Fix:
   re-raise when all pages failed (the tardis/deribit_combo "raise iff `not results and failures`" pattern).
2. **CF-11 swallow — `tradfi/ibkr.py:337-348` (per-agent).** `except Exception: … return []` per symbol — no
   classify/event/raise; a mid-batch IB socket death silently shrinks the equity universe with zero failure signal.
3. **CF-11 swallow + REMOVED-PROVIDER — `tradfi/polygon.py:286-354` (verified wired).**
   `aiohttp.ClientError → return []`/`None` with no classify, no event, no raise. **AND** `polygon.py` is a **removed
   TradFi provider** (CLAUDE.md: "Polygon.io REMOVED, do NOT reference") yet is **still wired** — `factory.py:75`
   imports `PolygonReferenceDataAdapter`, `:314` registers `"polygon"`, `:130` maps `"POLYGON"`, `router.py` imports it
   — and its rebrand replacement **`massive.py` exists alongside it** (parallel old+new path, banned). The 2026-05-22
   commit _patched_ polygon.py ("replace deleted UAC external/polygon types with local models") instead of deleting it.
   Fix: **delete `polygon.py` + its factory/router wiring** (massive.py supersedes it); this also moots the swallow.
4. **Silent `except Exception: pass` — `engine/orchestrator.py:3794, 7673, 7821` (per-agent).** `:3794` swallows ALL
   exceptions while probing canonical-vs-legacy GCS blob existence then silently returns the legacy path; `:7673/:7821`
   swallow on weather merge. Masks real GCS/auth/schema errors as absence (counter to honest-absence +
   no-silent-failure). Fix: catch `NotFound` specifically, let unexpected raise. (`:3791` has a related
   `# type: ignore[union-attr]` hiding a possibly-`None` storage client.)

## 🟡 Findings (smells / risk)

5. **Residual bar-edge fallback-to-open holes** (the 4 headline cases were FIXED by Ikenna slot-7 @2026-06-08 21:28 —
   `fix(bar-edge): stamp close/right edge … IS refdata adapters`; see § Reconciliation). Remaining: `hyperliquid.py:257`
   `candle.get("T") or candle.get("t")` falls to the OPEN edge if `T` is 0/missing; `ccxt_adapter.py:310-312` +
   `polygon.py:243` fall back to `open_ts` for any `interval not in BAR_TIMEFRAMES`. Look-ahead leakage on a
   nonstandard/zero-close timeframe.
6. **Systemic schema-drift band-aid — `scripts/dedupe_manifest_schema_drift.py:1-18`.** Documents "138% coverage / 16%
   of shards have >1 manifest row" from one shard under multiple schema versions + instrument_type casing
   (`perpetual`/`PERPETUAL`/`""`) + capture_status collisions. The phantom/dedup/canonicalize **script sprawl (~76 of 96
   scripts are manifest-repair)** is the symptom; the real fix is writer-side row-key idempotency + instrument_type
   normalization. (Target bucket is MTDS-written, but the repair tooling + smell live in IS.)
7. **`record_captured_from_counts` × 9 omit `source=`**
   (`orchestrator.py:1730,1916,2080,2693,3588,6910,7702,7895,8137`). Correct ONLY if UTL auto-stamps `default_source`
   for single-source sports-reference cells. Confirm the UTL contract — else these are blank-source captured cells (CF-4
   RED). (Multi-source FIXTURES correctly passes explicit `source` — `:2467` / `sports_fixtures_daily_repoll.py:419`.)
8. **`_af_record_empty` default `reason=""`** (`orchestrator.py:4271`) — latent blank-reason footgun
   (`LegacyBlankErrorReasonError`); one caller safe today. Make `reason` a required typed param.
9. **`available_at` flat-constant approximation** — injuries `date+12h` (`:4466`), fixture-stats/events `date+17h`
   (`:4917`, comment admits "approximate"). Per-row precision gap (a 22:00-KO fixture mis-stamped available at 17:00).
10. **Hardcoded venue universe duplicated** — `orchestrator.py:1028 _CEFI_VENUES`/`_TRADFI_VENUES`/`_DEFI_VENUES`
    duplicate UAC `VENUES_BY_ASSET_GROUP` (used by `enumerate_expected_universe.py`). A venue added to one but not the
    other silently desyncs the fetched universe from the could-exist denominator.
11. **Prediction catalogue bucket mismatch** — `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf:40-44`
    grants/targets `instruments-store-prediction-…` while the SSOT maps prediction → `instruments-store-PRED-…`
    (self-flagged in the TF). A live scheduler reading/writing a non-SSOT bucket → wrong/empty prediction could-exist
    seed.
12. **`os.environ["DEPLOYMENT_ENV"]="test"` mutation in a prod hot path** (`orchestrator.py:8033-8041`,
    `sports_dependency.py:90-98`) to steer `resolve_bucket_name` to the test bucket — not thread-safe (races other
    slots). `resolve_bucket_name` should take an explicit `env=` param.
13. **God-module + script tail** — `engine/orchestrator.py` is **8,192 lines (9× the 900 cap)**; tardis.py 1348,
    databento.py 1207, polymarket.py 1184, `_solana_utils.py` 1016 over cap. ~60 scripts import
    `from google.cloud import storage`/`boto3` directly + ~30 inline legacy `instruments-store-{ag}-{pid}` bucket names
    (some hardcode `central-element-323112`) → a repair script can silently target the wrong (legacy) bucket.
    `enumerate_expected_universe.py:1381` hardcodes `/tmp/`.

## ℹ️ Notes / resolved

- **URDI is NOT a phantom/dead — naming only.** `engine/urdi_reference_provider.py` is the LIVE sole external-fetch
  spine (`orchestrator.py:111` + `catalogue_builder.py`). "URDI" is the legacy label of the
  `unified-reference-data-interface` repo folded into IS. So the audit-instruction item (g) "`rg URDI` → 0 hits"
  expectation is **factually wrong for this repo** (~30 hits, all legitimate). Real defect:
  `urdi_reference_provider.py:116` error message still points operators to the deleted repo
  `unified-reference-data-interface/factory.py` (real path: `reference_data/factory.py`). **Recommend fixing
  audit-instruction item (g).**
- **Dead duplicate catalogue path** — `reference_data/catalogue/catalogue_builder.py` (`CatalogueBuilder`) +
  `orchestrator.py refresh_catalogue` write a static `date=None` snapshot, superseded by the
  `build_instrument_catalogue.py` lifecycle roll-up; no CLI/TF/test caller → orphaned, delete-candidate (parallel
  old+new).
- **CLAUDE.md over-claim** — "instruments-service owns all venue URLs via `InstrumentRecord`" overstates it:
  `InstrumentRecord` has NO venue-URL field (only `source_archive_url_template` + coverage windows); live REST/WS
  endpoints are UAC registries. The codex SSOT is accurate; the lean-index summary drifts → recommend correcting the
  CLAUDE.md one-liner so agents don't hunt for a nonexistent field.

## ✅ Verified clean (the good news)

- **schema_version (CF-1)**: IS does not hardcode/trust a write constant — `ManifestWriter` owns it; the v9 migrator
  (`migrate_instruments_store_v9.py`) reads the ACTUAL distribution (`v8_before`/`v9_before`), is idempotent
  (`pipeline_mode=` no-op guard), single-walk, snapshot-before-write. (The v8-incident lesson is applied.)
- **expected_unattempted (CF-6)**: `enumerate_expected_universe.py` materializes the 4th state with only closed-set
  typed `EXPECTED_*` reasons; no silent placeholders.
- **validity-matrix + Era-B bundle-grain**: rejects impossible `(instrument_type × data_type)` cells; options/futures
  chains enumerate ONE candidate per underlying (not per-leaf — fixes the ~563K tradfi false-candidate over-fan).
- **daily-listing**: fetch-once-then-filter-per-date via lifecycle bounds (`available_from/to`), inclusive, UAC-sourced
  genesis/launch — NOT a cross-date copy. VIX static exception handled.
- **auth + isolation**: no direct `google.cloud`/`boto3` in `reference_data/`; credentials via constructor `api_key`
  (SM-injected); per-venue/shard loops isolate (no aborting re-raise); `base_adapter._get_with_retry` does exp-backoff
  on 429/5xx. ~26 DeFi adapters are static no-I/O lists (correctly CF-11-exempt).
- **bar-edge (IS refdata)**: hyperliquid/aster/ccxt/polygon now stamp the close edge (fixed today — § Reconciliation).

## Reconciliation with the bar-edge issue docs

This morning's sweep flagged the IS reference adapters (hyperliquid/aster/ccxt/polygon) as left-edge. Git log confirms
they were **FIXED 2026-06-08 21:28 by Ikenna (slot-7)** —
`fix(bar-edge): stamp close/right edge on pre-agg OHLCV ingestion in IS refdata adapters`. So the finding was correct
and is now resolved (residual fallback-to-open holes per finding 5). The
`hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md` + the systemic doc's IS-refdata rows are updated to FIXED.

## Remediation todos filed

The 🔴 items (kalshi/ibkr CF-11 swallow, polygon removed-provider deletion, orchestrator silent-excepts) + top 🟡s are
filed in `plans/active/issues/instruments_service_audit_findings_2026_06_08.md`.

## Reproduce

```
rg -U "except\b[^\n]*:\s*\n(\s*[^\n]*\n)?\s*return (\[\]|None)" instruments-service/ -t py -g '!*test*'   # CF-11 swallows
rg -n "polygon" instruments-service/instruments_service/reference_data/factory.py                          # removed-provider still wired
rg -n "except Exception:\s*$" instruments-service/instruments_service/engine/orchestrator.py               # silent excepts
wc -l instruments-service/instruments_service/engine/orchestrator.py                                       # 8192-line god-module
```
