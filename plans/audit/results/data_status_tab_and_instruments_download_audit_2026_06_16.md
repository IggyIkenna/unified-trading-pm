---
type: analysis
title: Data-status tab + instruments download audit — deployment-api / deployment-ui / instruments universe
epic:
  - instruments_master
  - deployment_and_user_management_master
auditor: ikennaigboaka
date: 2026-06-16
status: complete
source:
  - operator 2026-06-16 (data-status tab walkthrough screenshots:
      CEFI / BINANCE-FUTURES drilldown, instruments-service "out of scope", aave_v3 download failure, missing CeFi
      tokens)
  - parallel read-only investigation 2026-06-16 (deployment-api backend, deployment-ui frontend, instruments-service +
    UAC universe)
locked_by: live-defi-rollout
---

# Data-status tab + instruments download audit (2026-06-16)

> Read-only findings of record. Each item is root-caused with `file:line`. Remediation todos:
> `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`. Migration-owned items (universe + to-100%) are
> cross-linked to `instruments_manifest_canonicalisation_2026_06_01.md`. **Two of these are operator-flagged blockers:
> instruments CSV downloads (finding A) and MTDS/instruments migration-to-100% (finding H).**

## A. DeFi instruments CSV download → "site isn't available" (HTTP 502 path-drift) — BLOCKER (downloads)

Route `GET /download-shard-csv` → `build_instruments_shard_csv_export`
(`deployment-api/deployment_api/routes/data_status/_downloads.py:352,407`).

Root cause: the downloader rebuilds the GCS object path with the **split** manifest venue and **drops chain** —
`deployment_api/services/data_status_drilldown/_csv_export.py:338-339`:
`gs://{bucket}/instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` (e.g. `venue=AAVE_V3`). But
the instruments-service WRITER stores the object under the **combined** DeFi venue token
(`instruments-service/.../engine/orchestrator/writers.py:77-91,181` → `canonicalize_defi_venue_combined()` →
`venue=AAVE_V3-ETHEREUM`), while writing the manifest row split into `venue=AAVE_V3` + `chain=ETHEREUM`
(`writers.py:134-139`). The UI renders the venue from the manifest (`venue=AAVE_V3`, chain separate) and the route
accepts `chain` but never forwards it to the exporter (`_downloads.py:407` omits chain). Result: probe reads 0 rows →
`_path_drift_response` → **HTTP 502** (`_downloads.py:176-204,423`), which the browser shows as "this site can't be
reached". Same `venue={venue}` no-chain shape in the drilldown reader `_instruments.py:62-70`. **Class bug — applies to
every chain-partitioned DeFi shard; needs an all-asset-group download smoke test + a global fix (incl. MTDS DeFi
paths).**

## B. instruments-service drilldown rows all show "out of scope"

`out_of_scope = not scope_in and not dt_is_processed` (`breakdowns_core.py:635,673-674`). `scope_in` =
`is_expected(category,venue,data_type)` against UAC `EXPECTED_COVERAGE_BY_ASSET_GROUP`
(`unified-api-contracts/.../registry/expected_coverage.py:360-368`) and `dt_is_processed` against
`PROCESSED_REQUIRES_RAW` (`registry/processed_data_dependencies.py:92-98`). Both registries enumerate **market-data /
candle** data_types only. instruments-service emits **reference data**, whose data_type tokens are in neither registry →
`scope_in=False ∧ dt_is_processed=False` → `out_of_scope=True` for every row. MTDS venue×data_type pairs ARE listed →
in-scope. The code already knows reference ≠ market data (`breakdowns_core.py:540-543` docstring) but the per-row scope
classification has no instruments-service exemption. Not a data bug — a scope-policy gap.

**The actual "types":** for cefi/tradfi/defi the writer records each manifest row with `data_type=""` AND
`instrument_type=""` — one bundled `instruments.parquet` per `(asset_group, venue, [chain], date)`
(`instruments-service/.../engine/orchestrator/writers.py:158-181`); the instrument categories (FUTURE/OPTION/SPOT/
PERPETUAL/COMBO) are a COLUMN inside the parquet, not a manifest data_type/axis. The UI surfaces the blank bundle as the
single row "instruments" (sports writes real tokens like `fixtures`). So `is_expected(cat,venue,"")` and
`is_processed_data_type("")` are both `False`. **PROPER FIX (not the `scope_in=True` short-circuit hack — that makes
everything in-scope and kills the ability to flag a venue/day that SHOULD have a catalogue but doesn't):** add a
reference-data expectation registry parallel to the market-data one (`EXPECTED_REFERENCE_COVERAGE_BY_ASSET_GROUP`, or
reuse the IS could-exist universe from `enumerate_expected_universe` + per-venue genesis in
`data-catalogue.instruments-service.yaml`/`expected_start_dates.yaml`); in-scope ⟺
`(asset_group, venue[, instrument_type])` ∈ that set AND `day ≥ genesis`. Branch `_PER_VENUE_DAY_BUNDLE_SERVICES` in
`breakdowns_core._classify_data_type_for_venue:673` onto it. This is the F4 contract (IS owns what-could-exist;
consumers READ it), and depends on finding K (instrument_type in the manifest) to scope per type.

## K. Sharding tailoring per asset class — MTDS is asset-class-aware; instruments-service is NOT instrument_type-aware

§F is "by design" but **only partly tailored**. MTDS flexes per asset class — DeFi adds `chain`, sports
`league_id`/`fixture_id`, prediction `canonical_question_group`/`job_id`, atop `instrument_type × data_type` (caveat:
the generic 5-axis grid OVER-generates expected combos — e.g. Deribit `options_chain` under every instrument_type —
needing the "phantom-expected clamp" `breakdowns_core.py:545+`; so tailored-with-cartesian-overcount).
**instruments-service is NOT instrument_type-aware**: it bundles all instrument_types into one
blank-`data_type`/blank-`instrument_type` row per venue/day, so for derivative-rich venues (CME future+option+combo;
Deribit future+option+perpetual — the §J "only futures+perps, no options" blind spot; Binance spot+perp+future) coverage
can only say "captured SOMETHING for the venue", never "captured CME OPTIONS on day X". **Proper tailoring:** keep the
storage unit (one catalogue parquet per venue/day) but enrich the manifest row with `instrument_type` as a COLUMN
carrying per-type counts (writer currently passes `instrument_type=""` at `writers.py:172`). That one change gives
per-type coverage visibility, makes the §B reference-scope meaningful per type, and fixes the §J Deribit-options blind
spot at the coverage layer.

## C. Venue filter button doesn't filter results — two independent causes

1. **UI**: `selectedVenues` state + toggle is correct (`deployment-ui/src/components/DataStatusTab.tsx:327,2058-2072`)
   and IS passed to the request (`:706,715` → `client.ts:1373-1375`), but **no effect re-runs the fetch when
   `selectedVenues` changes** — `fetchData` only fires from the manifest-mode effect (`:807-814`, deps
   `[manifestFilter]` only), cache-clear (`:822`), and the manual "Check Status" button (`:1872`). Deliberate
   no-auto-fetch (`:1000-1003`), so toggling a venue highlights the button but leaves results stale until "Check Status"
   is re-clicked.
2. **API**: the manifest fast-path that powers the tab (`/api/data-status/manifest` →
   `services/data_status/manifest.py:114-129`) has **no `venue` parameter at all** (only chain/league/fixture/job) — so
   even a re-fetch wouldn't narrow by venue server-side; per-venue breakdown is always computed for all venues
   (`manifest.py:589`). The legacy `/api/data-status` CLI path DOES honour venue (`_status_core.py:60-61` →
   `data_status/cli.py:109-110`).

## D. "available" vs "available dates" are duplicate panels

For a non-DeFi MTDS venue the backend emits both `honest_data_types` and `data_types`; the UI renders **both** — the
honest-coverage panel (`DataStatusTab.tsx:4371-4692`) and the legacy "Data Types" block ("{N} available — click a day"
`:4897-4974`) — keyed by the same data_type names (`:4366-4370` says the honest panel is "additive"). The legacy block
is the redundant/older one; its only unique value is the clickable per-day drill chips.

## E. "+{N} more" pagination is slow / tiny increments

Shared `DateList` component (`DataStatusTab.tsx:245-301`) pages in fixed `DATE_PAGE_SIZE = 60` increments
(`:243,260-261,290-298`). Separately, several `+{N} more` are **static server-truncation labels** (non-interactive:
`:3891,3911,5386`, `VenuePillList` `:230-236`) where the backend never sent the remaining items. A visible-count
selector (50/100/200/1000/2000/All) on `DateList` fixes the in-grid case; the static labels need a backend `limit` bump
to be client-pageable.

## F. instruments-service vs MTDS rollup differs — BY DESIGN, not a bug

Different shard axes: `sharding.instruments-service.yaml` = `asset_group × venue × date` (3 axes; one bundled
`instruments.parquet` per venue/day, `_PER_VENUE_DAY_BUNDLE_SERVICES`); `sharding.market-tick-data-service.yaml` =
`asset_group × venue × instrument_type × data_type × date` (5 axes). So IS has no data_type sub-dimension to nest in the
breakdown while MTDS does. Intrinsic to the sharding contracts — answer only, optional UI clarity note.

## G. CeFi instruments universe is a curated subset — missing EIGEN + 16 coins

The universe is a **hardcoded base-asset allowlist**, not the full exchange listing:
`unified-api-contracts/.../registry/cefi_instrument_universe.py:19` `CEFI_BASE_ASSET_UNIVERSE` (~28 coins) + `:53`
`CEFI_ACCEPTED_QUOTE_ASSETS = {USDT,USDC,USD}`. Applied in tardis (`cefi/tardis/parsing.py:345-355`, the batch path for
binance/bybit/okx/coinbase), hyperliquid (`cefi/hyperliquid.py:124`), aster (`cefi/aster.py:173-175`). **EIGEN is
absent** → EIGENUSDT excluded on binance-spot. Of the operator's list, missing from the allowlist (excluded everywhere):
`AAVE, ALGO, AXS, CHZ, COMP, DASH, ENJ, EOS, FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC`. The rest (ADA/ATOM/AVAX/BNB/
BTC/DOGE/DOT/ETH/LINK/LTC/NEAR/SOL/TRX/UNI/XRP) ARE in the list and should enumerate if the venue/quote are covered. No
size cap, no enumerator omission — purely the two frozensets. Extending = one UAC edit + re-run the IS catalogue.

## H. instruments-service to 100% — migration NOT applied; mix of manifest-reconcile + real capture-freeze gap — BLOCKER (MTDS migration)

Prod instruments-store is **still legacy v8 flat shape** (no `asset_group=`/`pipeline_mode=`); v9 canonicalisation
`--apply` is **🔴 GATED** on `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase-0
(`instruments_manifest_canonicalisation_2026_06_01.md:32`; migrator `migrate_instruments_store_v9.py`, dry-runs green,
apply unchecked E3–E6 `:189-194`). The missing ~5% is **both**: (a) manifest-honesty artifact — ~40% cefi `_index` rows
are null `capture_status` with `instrument_count>0` (real data counted as missing; relabelled honestly by the v9 walk
CF-10, a reconcile not a backfill) + phantom rows (`reconcile_phantom_manifest_rows_all.py`); and (b) a **real
capture-horizon gap** — IS `by_date` definition capture is FROZEN ~2026-05-21 fleet-wide (cefi 05-21, defi 05-07, tradfi
degraded 16K→2/day after 05-04 then stopped 05-22 — anomalous, needs root-cause), per
`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md:194-212`. Path to 100%: land Phase-0 → v9 `--apply` (E4) →
phantom reconcile → un-freeze IS daily capture + fix tradfi break + backfill the genuine post-freeze gap via the IS CLI.

## I. TradFi (CME/Databento) instrument naming is not human-canonical — raw contract codes in base_asset/underlying

For TradFi the adapter emits a RAW venue contract code as `base_asset`/`underlying`, unlike Deribit (BTC/ETH human
roots) and Tardis (canonical base). `instruments-service/.../reference_data/adapters/tradfi/databento/adapter.py:709`
sets `base_asset = underlying or raw_symbol`; `underlying` (`:637-643`) is Databento's raw value, else the longest
registered **exchange-code prefix** via `_extract_underlying_from_symbol` (`symbology.py:121-130`) → best case `"ES"`,
fallback case the full contract-month code (`"ESM0"`) when no prefix matches (CME options with spaced symbols like
`E5AH0 C2510`, calendar combos). `instrument_key` is mechanical (`f"{venue}:{TYPE}:{raw_symbol}"`, `:704`). A
human-canonical mapping **already exists in UAC but is UNUSED**: `tradfi_instrument_universe.py`
`DatabentoInstrumentDef` carries `base_asset="SP500"`/`exchange_code="ES"` (`:40-41,76`) + `EXCHANGE_CODE_TO_NAME`
(`:352`, `CL→CRUDE`, `GC→GOLD`) — the adapter reads the registry only for asset-group resolution, never for the human
name (grep `EXCHANGE_CODE_TO_NAME` = 0 source hits). Because `underlying` is a raw code (or per-contract fallback),
options/futures **bundle by the raw code, fragmenting the option↔underlying-future grouping** (the user's "underlying
path they're bundled with"). Schema gap: UAC `InstrumentRecord`
(`unified-api-contracts/.../internal/reference/instrument.py:90`) has `instrument_key/raw_symbol/ base_asset/underlying`
but **no human-canonical instrument-id and no canonical base/product-root field** — adding them is an additive schema
extension (optional, not in the CeFi-only `model_validator` at `:318`). Fix = in `_parse_row_to_record` resolve
exchange-code → UAC registry, set human root (`ES→SP500`) as canonical base + canonical `underlying`, keep `raw_symbol`
raw, add `canonical_instrument_id` + `product_root`/`canonical_base` schema fields (1:1 into
`INSTRUMENTS_PARQUET_SCHEMA`); also parse the spaced-option root so the fallback stops fragmenting.

## J. Deribit OPTIONS/SPOT in the batch catalogue — spot WRONGLY dropped (operator correction); options BTC/ETH OK

The dedicated live `DeribitOptionsReferenceDataAdapter` (`deribit_options_adapter.py`, fetches `kind=option` for
BTC/ETH/SOL/BNB/XRP) is **NOT wired into the batch run** — `engine/orchestrator/venue_core.py:90-103` `_CEFI_VENUES` has
`DERIBIT` + `DERIBIT-COMBO` but **not `DERIBIT-OPTIONS`**. So batch Deribit options come ONLY via the Tardis `DERIBIT`
adapter (`factory.py:103` routes DERIBIT→tardis), which:

(a) **WRONGLY drops Deribit spot — BUG (operator correction 2026-06-16: Deribit DOES have spot now, launched ~2023;
maybe not in 2019).** `tardis/adapter.py:95-97` hardcodes `"deribit"` in `_DERIVATIVES_ONLY_EXCHANGES`, and `:719-729`
returns `None` for any `SPOT_PAIR` on that venue (comment `:721` "deribit has no spot" is stale). So Deribit spot is
silently excluded fleet-wide. **Fix:** remove `deribit` from `_DERIVATIVES_ONLY_EXCHANGES` (or make it date-aware — spot
only post-launch ~2023), confirm Tardis returns Deribit spot instruments, and validate they pass the universe filter
(BTC/ETH etc. are in `CEFI_BASE_ASSET_UNIVERSE`). The user's "only futures+perps" sample is explained by this drop, not
a date choice.

(b) emits options **filtered to BTC/ETH only** — `tardis/parsing.py:354-355` + UAC `CEFI_OPTIONS_UNDERLYINGS={BTC,ETH}`
(`cefi_instrument_universe.py:59-62`). **Operator 2026-06-16: BTC/ETH underlyings are FINE for now** — do NOT widen
`CEFI_OPTIONS_UNDERLYINGS` or wire the dedicated options adapter yet. BTC/ETH options SHOULD appear via Tardis; if a
sample shows zero, run-verify the Tardis endpoint tier (`adapter.py:564-637`, `/v1/instruments`→401→`/v1/exchanges`
fallback may drop the option metadata `_resolve_option_fields` `parsing.py:358-381` needs).

## Sequencing — migration / data-pipeline / data-status execution tiers (operator 2026-06-16)

Operator ordering: **clean up everything else first → run the actual v9 manifest migration → downloads LAST.** Survey of
the 18 core active plans (read-only, 2026-06-16). No `--apply` has executed anywhere — every vertical is DRY-RUN-only
and operator-gated, double-gated on TIER-0 GATE 0 AND the instrument-catalogue lifecycle gate (both still OPEN).

**TIER 0 — pipeline_mode Phase-0 code foundation (the cross-cutting blocker before ANY `--apply`).**
`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (3/13). OPEN: **M1** full source-aware enum (the
breaking `live_websocket→live_<source>` object migration), **M3** per-shard available-sources registry +
`could_exist(shard,mode)`, **M4** mode-contextual `select_for_mode` read-resolver, **fix #1** (defi rebuild blank
`pipeline_mode`+`source` stamp), **fix #3** (features delta_one reader omits `pipeline_mode=`). DONE: fix #2 (utl), #4
enumerator stamp, #6 write-time cross-check, M2 draft seed. **GATE 0 (every repo QG-green + cross-repo SIT
write→manifest→union-read) NOT MET.** Rider: `pipeline_mode_partition_migration_2026_06_01.md` (promote pipeline_mode to
on-disk hive key) rides each AG walk (0/2).

**TIER 1 — cleanup / correctness to land before the migration (most independent of it; can proceed now).**

- `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (P0, ~12/25) — the OTHER hard foundation-gate: IS
  catalogue must be GREEN per-AG before that AG's MTDS `--apply`. Ops tail open (dead daily producer; tradfi
  BLOCKED-CREDENTIALS on Databento).
- `instruments_manifest_canonicalisation_2026_06_01.md` (P0, G1 ROOT, 5/8) — the could-exist-universe SSOT; carries the
  2026-06-16 UAC-denominator callout (this audit).
- `data_source_provenance_all_asset_groups_2026_06_01.md` (P0, write-path DONE; backfills ride each AG's C-source
  rider).
- `mtds_honest_absence_swallow_remediation_2026_06_10.md` (P0, ~14/17 done).
- **This plan's Phases A–D** (scope/venue/UI/universe/naming/Deribit-spot) are TIER-1 cleanup — independent of the
  migration. Universe extension already shipped (UAC@f4f7f8e).

**TIER 2 — the real v9 `--apply` migrations, per asset_group (ALL gated on GATE 0).** Coordinator
`master_data_canonicalisation_migration_catalogue_2026_06_07.md` (G0–G5 gate sequencer, executes nothing). Per-AG
owners, all DRY-RUN-ready / operator-gated: prediction (1.9M moves, closest) · tradfi (5.3M objects) · sports · defi
(re-enumerate 18 new venues first) · cefi (BLOCKED on catalogue bundle-grain) · instruments (5 AGs) · downstream (P1,
G2, dry-run NOT run). MASTER axis: `defi_manifest_canonicalisation_2026_06_01.md`.

**TIER 3 — orphan-safety verification around apply.** `migration_verification_orphan_safety_2026_06_10.md` (P0, 19/37):
G3.5 pre-apply checks HARD-BLOCK G4 `--apply`; G4.5 verified-delete (`cleanup_legacy_twins.py`) runs after, re-sweeping
orphans (must stay 0).

**TIER 4 — data-status tab + downloads (LAST).** This plan's **Phase E** — the download path-fix targets the FINAL
canonical `pipeline_mode=…/venue=…` shape, so it lands after TIER 2. `capability_wizard_and_manifest_2026_06_11.md` is
DECOUPLED (consumes the data-status API as a black box; ~done).

**Watch-item:** the coordinator claims "G0–G3 GREEN / 5-of-5 apply-ready," but TIER-0 GATE 0 is demonstrably NOT met
(M1-breaking / M3 / M4-resolver / fix #3 open) — the coordinator appears to credit only the landed Phase-0.1 subset, not
the full Phase-0 DAG. Reconcile before any `--apply`.
