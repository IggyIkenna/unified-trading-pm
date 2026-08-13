# CeFi Canonical-Completeness — FINAL EXECUTION BLUEPRINT (2026-07-17)

> **🟢 RESOLVED-BY-REFERENCE 2026-07-29 (retag) — corrected 2026-08-12 (/plan-reconcile).** This blueprint's execution
> DID start and finish via the forked plan `cefi_migration_cutover_and_track8_completion_2026_07_25.md` (archived,
> status: complete, all 5 apply/verify todos closed, residual gap CLOSED 2026-07-28 with cited live-verified proof). The
> banner below is kept only as historical context for what the blueprint originally specified — it is NOT an
> in-flight/must-read-first warning anymore; see the archived successor plan for the actual execution record.
>
> <details><summary>Original 2026-07-17 banner (historical)</summary>
>
> **🟡 In-flight refactor + drain-gated GCS cutover.** This blueprint is the settled execution plan for the
> canonical-completeness program (parent: `cefi_residual_followups_after_honest_done_2026_07_17.md`
> §"Canonical-completeness program"). It makes cefi tick data canonical across ALL FOUR surfaces — (A) GCS filename, (B)
> parquet `instrument_id` column, (C) manifest `instrument_id` key, (D) reader resolution — by keying every surface off
> the instruments-service catalogue map read as DATA. Any agent touching cefi MTDS write/read paths, the cefi manifest,
> features/MDPS cefi reads, or launching cefi VMs must read this first.
>
> </details>

**Verdict of the adversarial review: `NEEDS-REDESIGN`.** This blueprint is that redesign. It supersedes the raw D1–D4
specs wherever they conflict with the review. The single largest change: **every surface keys off ONE 3-tuple map
`(venue, instrument_type, raw_symbol) → instrument_id` built by ONE shared builder** — the D1/D3 2-tuple key is deleted
(it silently under-resolved exactly the BYBIT/OKX/BINANCE-FUTURES majors the program exists to fix).

---

## 1. Execution summary + strict ordering

**Summary.** The instruments-service catalogue
(`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`) already decomposes every venue as
`(venue, raw_symbol) → instrument_id`. We make the writer (parquet column), the filename, the manifest key, and the
reader all resolve identity through the SAME catalogue map — read as parquet DATA, never via a service↔service import.
Because the review proved `(venue, raw_symbol)` is ambiguous for spot/perp wire-symbol clashes (`(BYBIT, BTCUSDT)` →
both `BYBIT:SPOT_PAIR:BTC-USDT` and `BYBIT:PERPETUAL:BTC-USDT@LIN`), the whole program is re-keyed to the **3-tuple
`(venue, instrument_type, raw_symbol)`**, single-sourced in one builder and one UAC map. New writes are canonicalized in
Phase-0 code (Tardis lane **and** the live/on-chain `PartitionedTickWriter` column path); the reader bridge makes a
canonical id resolve to on-disk objects during the MIXED window; then four one-time, snapshot-first, dry-run-first
migration scripts canonicalize the historical corpus (content bytes, Tardis filenames, manifest keys, eu-twins). All GCS
mutation happens **behind a writer drain**; readers must already carry the bridge.

**STRICT ORDERING (do not reorder — each gate protects the next):**

1. **Phase -1 — Catalogue REBUILD + verify gate (prerequisite of everything, incl. D1 deploy).** Re-run
   `build_instrument_catalogue.py` after the already-shipped catalogue-canonicalization adapter fixes. **Verify gate
   (hard):** `0` cefi rows where `instrument_id` contains `:PERP:`; `0` cefi rows where
   `instrument_id != canonical_instrument_id`; re-measure the ambiguous-key count on the **pinned 3-tuple** key. Nothing
   downstream keys off the catalogue until this is green (BLOCKER-A/B). Owner + evidence recorded in the Progress Log.
2. **Phase 0a — Pin the two contracts (design lock, before any code).**
   - **Filename-stem form:** the single-instrument cefi filename stem is the **FULL canonical `instrument_id`**
     (`VENUE:TYPE:BASE-QUOTE[@MARKER]`), matching the live on-chain objects. NOT the bare symbol segment. Correct the
     contradicting docs (Phase 2) but lock the form now so writer/migration/reader agree byte-for-byte.
   - **Shard atom:** `[date, venue, data_type, instrument_type, instrument_id, pipeline_mode]` — **WITH
     `pipeline_mode`**. Identical across writer / manifest / status / gate / UI and across all four migration scripts.
3. **Phase 0b — Code fixes land + deploy (in this sub-order):**
   - **Shared builder** `CeFiCatalogReader.build_raw_symbol_map()` (3-tuple) + UAC `CeFiWireCanonicalMap` (3-tuple). ONE
     builder.
   - **D1 writer** (Tardis column + manifest) keyed off the shared builder; **fail-loud** on empty/unreachable catalogue
     in the registered prod path.
   - **D1-live** column decomposition in `PartitionedTickWriter` (live consolidated + on-chain write paths).
   - **D2 filename** stem = full instrument_id (Tardis + live paths).
   - **D3 reader bridge** (MTDS `reader.py`, MDPS `path_parsing.py` + `canonical_writer_shaping.py`) — 3-tuple.
   - **D-features** `raw_data_loader.py` bridge + column-name reconciliation.
   - Deploy all of the above (tarball live on every writer box + every narrow-read consumer). **This deploy is itself a
     drain-gate prerequisite (blocking-risk #2): the writers must be re-enabled only onto the fixed 3-tuple code, or the
     migrated corpus regrows the raw remainder.**
4. **Phase 1 dry-runs (no drain needed, read-only):** run all 4 migration scripts `--dry-run` against `-prd`; confirm
   counts within STOP-ON-SURPRISE bounds; confirm the active majors now resolve via the 3-tuple key.
5. **Phase 1 DRAIN (GATES every `--apply`).** Stop **ALL** cefi writers both clouds (Tardis `cefi-queue-*` + on-chain
   `cefi-*` + forward/cron/live). Run the manifest consolidator to a stable index. **Snapshot** the cefi bucket
   `_index/`
   - a listing manifest to `_index/snapshots/pre_d4_<ts>/`. HARD RULE: **no GCS cutover with writers live; no writer
     re-enable until Phase-0 tarball confirmed live AND `--apply` verified.**
6. **Phase 1 `--apply` (ordered 0→1→2→(3,4)):** content backfill → filename rename → manifest completion + eu-twin drop.
   Each is snapshot-first, idempotent, before/after row-count verified.
7. **Phase 1 verify:** re-consolidate the manifest; run each script's `_verify_gate`; re-run every `--dry-run` and
   assert `0` further changes (idempotency proof). Record measured deltas in the Progress Log.
8. **Re-enable writers** (both clouds) — only after step 7 green and Phase-0 tarball confirmed live.
9. **Phase 2 — Docs/codex reconciliation:** correct the stale "filename is the bare symbol" docs and pin the
   four-surface contract in codex.

**Drain gate, called out explicitly:** the `--apply` of D4 scripts 1 & 2 (content rewrite + GCS rename) is the ONLY step
that mutates prod objects. It runs strictly inside the Phase-1 drain window, strictly after (a) the catalogue rebuild is
green, (b) the Phase-0 3-tuple code is deployed to every writer, and (c) the D3 reader bridge is deployed to **every**
narrow-read consumer (MTDS reader, MDPS, features-service, and any strategy/ml cefi reader). Renaming objects while a
consumer runs old reader code = silent ShardNotFound / 0-row reads. This is a review ordering-issue and is now a hard
gate.

---

## 2. Code fixes (Phase 0) — diff-level, with reviewer-required changes folded in

### Contract changes that touch every fix (READ FIRST)

- **THE KEY IS A 3-TUPLE.** `(venue.upper(), instrument_type.upper(), raw_symbol.upper()) → instrument_id`. This
  replaces the D1/D3 2-tuple key everywhere. Rationale (review blocking-risk #1): `(BYBIT, BTCUSDT)` is
  2-tuple-ambiguous → the 2-tuple builder EXCLUDES it → writer falls through to wrapped-wire `BYBIT:SPOT_PAIR:BTCUSDT`
  while the 3-tuple migration produces `BYBIT:SPOT_PAIR:BTC-USDT` → the two DO NOT JOIN, breaking the
  shard-atom-identical HARD RULE for the marquee majors. `instrument_type` is in scope at every insertion point (writer
  `derive_row_instrument_id`, `venue_fetch.py:386`, reader per-shard read, MDPS path axis).
- **ONE BUILDER.** Exactly one map builder exists: `CeFiCatalogReader.build_raw_symbol_map()` (3-tuple). The D1 spec's
  `raw_symbol_to_instrument_key_map()` (2-tuple) and the D4 spec's separately-named builder are **collapsed into this
  one method** (deletes the duplicate; satisfies single-source / delete-deprecated-code). UAC's `CeFiWireCanonicalMap`
  consumes the same 3 columns + type.
- **ONE HONEST-UNRESOLVED SET.** The ambiguous/excluded set is measured ONCE, off the pinned 3-tuple key against the
  REBUILT catalogue, and reported as a single number everywhere (writer WARNING, reader honest-fallback, migration
  report). The spec's divergent figures (297 / 439 / 777 / 781) are all pre-rebuild, pre-pinned-key measurements and are
  superseded by the single post-rebuild measurement. Reader and writer must honest-drop the SAME set.
- **READ `instrument_id`, NEVER `canonical_instrument_id`.** The `canonical_instrument_id` column is a trap (511 rows
  carry the raw-glued form, e.g. `BINANCE-DELIVERY:FUTURE:ADAUSD_200925`). Every builder + script reads `instrument_id`.
- **FAIL-LOUD, not silent-degrade.** A registered prod resolver whose catalogue is unreachable or whose built map is
  EMPTY must raise / loud-error (data-correctness heartbeat), NOT silently return `{}` and disable decomposition
  corpus-wide (review blocking-risk #4). Disabled-by-default for tests is achieved by NOT registering a builder — a
  registered-but-empty map is the danger signal and halts.

---

### FIX 0 — Shared 3-tuple builder (NEW, single source) + UAC map

**Repo: market-tick-data-service** — `market_tick_data_service/engine/cefi_catalog_reader.py`

- **:281** add instance memo:
  ```
  self._raw_symbol_map: tuple[dict[tuple[str, str, str], str], set[tuple[str, str, str]]] | None = None
  ```
- **~:316 / ~:412** add the ONE shared builder (replaces both spec builders):
  ```python
  def build_raw_symbol_map(
      self, *, venues: set[str] | None = None
  ) -> tuple[dict[tuple[str, str, str], str], set[tuple[str, str, str]]]:
      """Single shared (venue, instrument_type, raw_symbol) -> instrument_id map.
      Reads the parquet columns directly off the cached full-lifecycle catalogue
      (CatalogRow drops raw_symbol, so the row API cannot build it). Reads
      instrument_id ONLY (canonical_instrument_id is a raw-glued trap). Excludes any
      3-tuple resolving to >1 distinct instrument_id (honest-unresolved, reported,
      never guessed). Returns (resolve_map, excluded_keys)."""
      if self._raw_symbol_map is not None:
          return self._raw_symbol_map
      out: dict[tuple[str, str, str], str] = {}
      conflicted: set[tuple[str, str, str]] = set()
      df = self._load_latest_catalog()
      required = {"venue", "instrument_type", "raw_symbol", "instrument_id"}
      if df is None or df.empty or not required.issubset(df.columns):
          # FAIL-LOUD: a registered prod resolver must never silently disable.
          msg = f"cefi catalogue unusable for raw_symbol map (df empty/missing {required})"
          raise ValueError(msg)
      for v, t, r, k in zip(df["venue"], df["instrument_type"], df["raw_symbol"], df["instrument_id"], strict=True):
          kv, kt, kr, kk = _safe_str(v).upper(), _safe_str(t).upper(), _safe_str(r).upper(), _safe_str(k)
          if not (kv and kt and kr and kk):
              continue
          if venues is not None and kv not in venues:
              continue
          key = (kv, kt, kr)
          if key in conflicted:
              continue
          if key in out and out[key] != kk:
              conflicted.add(key); del out[key]; continue
          out[key] = kk
      logger.info("cefi_catalog_reader: 3-tuple raw_symbol map built: %d keys, %d ambiguous excluded", len(out), len(conflicted))
      self._raw_symbol_map = (out, conflicted)
      return self._raw_symbol_map
  ```
- **Why:** one builder = one map key across writer, migrations, and (via UAC) reader = "shard atom identical". Full
  cached frame (no MVP gate / no active-date filter) so a delisted instrument still resolves at backfill write time.
  Reuses `_load_latest_catalog()` — no second GCS download. Reuses module-local `_safe_str`.
- **Test:** `tests/unit/test_cefi_catalog_reader.py` — feed a tiny frame with `(BYBIT, SPOT_PAIR, BTCUSDT)`,
  `(BYBIT, PERPETUAL, BTCUSDT)`, an ambiguous dated-future 3-tuple, and one `:PERP:` row; assert (a) the two BYBIT rows
  disambiguate by itype (both present, neither excluded), (b) the ambiguous key is in the excluded set and absent from
  the map, (c) reads `instrument_id` not `canonical_instrument_id`, (d) idempotent memoisation, (e) **raises** on an
  empty/column-missing frame (fail-loud).

**Repo: unified-api-contracts** — NEW `unified_api_contracts/canonical/domain/cefi_wire_canonical.py` (pandas-free)

- `@dataclass(frozen=True) class CeFiWireCanonicalMap` with `_canonical_by_wire: dict[tuple[str, str, str], str]` (fwd,
  keyed `(venue, itype, raw_symbol)`), `_wire_by_canonical: dict[tuple[str, str], str]` (rev, keyed
  `(venue, instrument_key)` — injective by construction), `ambiguous_wire_keys: frozenset[tuple[str, str, str]]`.
- `@classmethod from_triples(rows: Iterable[tuple[str, str, str, str]])` — takes
  `(venue, instrument_type, raw_symbol, instrument_key)` quads (name kept `from_triples` per spec but arity is 4; or
  rename `from_rows` — pick one and export it). Build fwd
  `(venue.upper(), itype.upper(), raw.upper()) → set(instrument_key)`; rev
  `(venue.upper(), instrument_key) → raw_symbol`; `ambiguous = frozenset(k for k, ids in fwd if len(ids) > 1)`;
  `canonical_by_wire = {k: one for k, ids in fwd if len(ids) == 1}`; skip any blank field.
- `canonical_for(venue, instrument_type, raw_symbol) -> str | None`;
  `raw_symbol_for(venue, instrument_key) -> str | None`.
- Export from `unified_api_contracts/__init__.py` `__all__`.
- **Why:** single-sourced canonicalization contract shared by the D3 reader, MDPS, and (semantically) the D1 writer, so
  writer/reader symmetry is byte-identical → paper==batch, shard-atom identical. Pure/no-I/O keeps UAC pandas-free and
  keeps both services depending on UAC, never on each other. Ambiguous-exclusion enforces "never guess" at the type
  level.
- **Test:** `tests/.../test_cefi_wire_canonical_map.py` — quads incl.
  `(BITFINEX-FUTURES, PERPETUAL, ADAF0:USTF0, BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN)`, both BYBIT BTCUSDT rows, one
  synthetic ambiguous 3-tuple; assert forward disambiguation by itype, reverse `raw_symbol_for` round-trips, ambiguous
  key → `canonical_for(...) is None` and is in `ambiguous_wire_keys`.

---

### FIX D1 — Writer: decompose ALL cefi venues (Tardis column + manifest key)

**Repo: market-tick-data-service.** New leaf module + one insertion point + one registration.

- **NEW `market_tick_data_service/market_interface/adapters/cefi/catalog_id_resolver.py`** (pure, no engine import):
  process-global `register_cefi_id_resolver_builder(builder)` /
  `resolve_cefi_instrument_id(venue, instrument_type, symbol) -> str | None` + bounded per-venue miss accounting
  (`_SAMPLE_CAP = 32`, instrument-granular, dedups per-tick repeats) + `log_and_reset_cefi_resolver_misses(day)`.
  - **Signature change vs spec:** resolver takes `instrument_type` (3-tuple). Builder returns the shared
    `(map, excluded)` tuple; resolver uses `map` for hits and MAY consult `excluded` to classify a miss as
    ambiguous-honest vs unknown for the WARNING.
  - **Fail-loud:** if a builder is registered but `_builder()` raises or yields an empty map, `resolve_*` re-raises
    (does not swallow to None). Disabled-by-default = no builder registered → returns None → existing behaviour (tests
    green).
- **`engine/cefi_catalog_reader.py:281`** — memo already added in FIX 0.
- **`market_interface/adapters/cefi/tardis_shared.py:53`** —
  `from .catalog_id_resolver import resolve_cefi_instrument_id`.
- **`tardis_shared.py:455`** — ONE insertion point, before the type branches, inside `derive_row_instrument_id`:
  ```python
  symbol = str(symbol_raw)

  # Decompose ALL cefi venues off the catalogue map (DATA, 3-tuple keyed). Catalogue
  # is SSOT; miss -> fall through to the existing per-venue logic (honest wrapped-wire
  # / margin-marker degrade). instrument_type is already in scope here.
  _catalog_id = resolve_cefi_instrument_id(venue, str(instrument_type), symbol)
  if _catalog_id:
      return _catalog_id

  if instrument_type is InstrumentType.OPTION:
      ...
  ```
  - **Why one insertion point covers everything:** the parquet column (`tardis_shared.py:792`, bulk
    `tardis_bulk_download.py:166/174`) AND the manifest key (`venue_fetch.py:386 _canonicalize_manifest_instrument_id`,
    which calls this SAME function with the SAME `instrument_type`) both flow through `derive_row_instrument_id` →
    identical id in column + manifest by construction, ZERO change to `venue_fetch.py` (898/900 lines, cap-critical).
    For the 6 margin-marker venues the catalogue now supersedes the 2026-07-09 heuristic for resolvable symbols
    (intended convergence; heuristic stays as the degrade). OPTION/FUTURE/PERPETUAL/SPOT_PAIR and DERIBIT-COMBO
    passthrough all remain as the fallthrough.
- **`engine/orchestrator/catalog_registration.py:85`** — register the lazy builder once per process:
  ```python
  _cefi_reader = CeFiCatalogReader(get_storage_client(), _cefi_instr_bucket)
  register_catalog_reader("cefi", _cefi_reader)
  register_cefi_id_resolver_builder(lambda: _cefi_reader.build_raw_symbol_map()[0])
  ```
  (+ top import of `register_cefi_id_resolver_builder`). Lazy: the map builds on the first `resolve()` (first write),
  reusing the sentinel-path frame.
- **`engine/orchestrator/manifest_finalize.py:623`** — after the existing `cefi_manifest_id_unresolved` WARNING, call
  `log_and_reset_cefi_resolver_misses(date)` (+ import). Emits the bounded per-venue catalogue-miss WARNING once per
  run; `venue_fetch.py` stays untouched.
- **Test:** `tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py` (new):
  - register a synthetic 3-tuple map incl. `(BYBIT, SPOT_PAIR, BTCUSDT) → BYBIT:SPOT_PAIR:BTC-USDT`,
    `(BYBIT, PERPETUAL, BTCUSDT) → BYBIT:PERPETUAL:BTC-USDT@LIN`,
    `(BITFINEX-FUTURES, PERPETUAL, AMPF0:USTF0) → BITFINEX-FUTURES:PERPETUAL:AMP-USDT`.
  - assert
    `derive_row_instrument_id({'symbol':'BTCUSDT'}, venue='BYBIT', instrument_type=SPOT_PAIR) == 'BYBIT:SPOT_PAIR:BTC-USDT'`
    and the PERPETUAL variant resolves to the `@LIN` id (proves the 2-tuple ambiguity is resolved — review blocking-risk
    #1).
  - **SHARD-ATOM identity:** `_canonicalize_manifest_instrument_id('BYBIT','SPOT_PAIR','BTCUSDT') ==` the same string.
  - case-insensitivity (BINANCE lowercase wire), miss→wrapped-wire fallthrough + one recorded miss.
  - **disabled-by-default regression guard:** with NO builder registered, every existing `derive_row_instrument_id`
    output is byte-identical (protects the ~30 assertions in `test_tardis_canonical_output.py` +
    `test_venue_fetch_cefi_manifest_canonicalization.py`).
  - **fail-loud:** a builder that yields `{}` → `resolve_*` raises (not silent None).

---

### FIX D1-live — Live + on-chain COLUMN decomposition (NEW; closes review blocking-risk #3 / missed surface)

**Repo: market-tick-data-service** — `engine/orchestrator/partitioned_writer.py`.

- **Problem (verified by review):** `derive_row_instrument_id` is reachable ONLY from the Tardis lane
  (`tardis_cefi_shards.py:137/455`). The live consolidated path and the on-chain lane (`onchain_perp_batch_handler` /
  `hyperliquid_s3` / `_umi_aster`) write via `PartitionedTickWriter.write_chunk`, which never calls
  `derive_row_instrument_id` → their parquet `instrument_id` COLUMN is only as canonical as the upstream adapter
  stamped. Left as-is, live cefi writes carry wrapped-wire/raw ids while batch is decomposed → **batch != live** (breaks
  the paper(W)==batch-rerun(W) ε=0 spine) and non-joining. D2 change-2 fixes only the live FILENAME, not the column.
- **Change:** in the cefi branch of `write_chunk` / group-shaping, before the file_symbol/stem is computed, normalize
  the `instrument_id` COLUMN via the SAME shared 3-tuple map (a new module-level `get_cefi_wire_map()` bridge — see FIX
  D3 — reused here so writer and reader share one map). For each row,
  `canonical_for(venue, instrument_type, raw_symbol)`; hit → overwrite the column cell; miss → leave honest + count.
  Gate on `asset_group == "cefi"`. Fail-loud consistent with FIX 0 when the registered map is empty in a prod write.
- **Why:** the live/on-chain COLUMN must be decomposed by the same map as the Tardis lane, or D2's live filename
  override reads a non-canonical column and the four surfaces split-brain on the live path. This is the surface the raw
  D1 spec missed.
- **Test:** `tests/unit/engine/test_partitioned_writer_cefi_column.py` — a cefi live chunk with raw `instrument_id`
  column `BTC-PERP` (on-chain) / `ADAF0:USTF0` (wrapped) + a synthetic map → out column canonical; ambiguous/unknown →
  unchanged; non-cefi asset_group → untouched.

---

### FIX D2 — Writer: canonical FILENAME stem = FULL instrument_id

**Repo: market-tick-data-service.** Filename stem is the FULL canonical `instrument_id` (locked in Phase 0a). Reuses the
column value D1/D1-live already made canonical — no catalogue re-resolution.

- **`market_interface/adapters/cefi/tardis_shared.py:704-715`** (`_file_stem_for`, PRIMARY) — single-instrument branch
  names the object by the row's FULL canonical `instrument_id` instead of the raw wire `symbol`:
  ```python
  ids: set[str] = set()
  for row in rows:
      raw = row.get("instrument_id")
      if raw is None or raw == "":
          msg = f"{instrument_type} row missing canonical 'instrument_id' for filename stem"
          raise ValueError(msg)
      ids.add(str(raw))
  if len(ids) != 1:
      msg = f"{instrument_type} per-symbol shard must contain exactly one instrument_id, got {sorted(ids)}"
      raise ValueError(msg)
  return next(iter(ids))
  ```
  - `instrument_id` is attached at `:792` BEFORE this helper is called at `:798` → filename == column == manifest by
    construction. `build_partition_path` writes the stem VERBATIM (never through `_sanitize_symbol`); `:` and `@` are
    legal GCS object-name chars (proven by live on-chain objects `HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet`,
    `ASTER:PERPETUAL:0G-USDT@LIN.parquet`). cefi-scoped (tradfi has its own `_file_stem_for` at `tradfi_shared.py:413`).
    Fail-loud on missing id (no silent placeholder). Update the helper docstring (`:675-683`).
  - CHAIN branch (`CHAIN_INSTRUMENT_TYPES` → underlying) and the `is_derivative` `underlying=…/ticks.parquet` branch are
    UNCHANGED (operator bundle→underlying rule).
- **`engine/orchestrator/partitioned_writer.py:257`** (`_resolve_file_symbol`, SECONDARY / batch=live parity) — extend
  the existing verbatim `file_symbol` filename-override from prediction-only to cefi:
  ```python
  if self._asset_group in ("prediction", "cefi") and "instrument_id" in group_df.columns:
  ```
  `file_symbol` affects ONLY the on-disk filename; the writer KEY / row-count / manifest bookkeeping stay on the bare
  `symbol` (`partitioned_writer.py:186-191`) → **shard atom unchanged**, identical to how prediction already behaves.
  cefi CHAIN types get `file_symbol=''` (→ `ticks.parquet`). Requires the live cefi df to carry the canonical
  `instrument_id` column — guaranteed by FIX D1-live. Update the `_resolve_file_symbol` docstring (currently claims cefi
  "untouched").
- **Tests:**
  1. `_file_stem_for` (cefi): enriched rows `instrument_id='BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN'`,
     `symbol='ADAF0:USTF0'` → stem `'BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN'`; ValueError when id missing/empty; CHAIN
     branch unchanged; `:`/`@` survive (not sanitized).
  2. `finalise_rows_and_path`: cefi PERPETUAL shard → `shard.path` endswith
     `/BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN.parquet` AND stem == `shard.df['instrument_id'].iloc[0]` (four-surface
     identity). Margin-marker standalone (BINANCE-FUTURES `BTCUSDT`) → `/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet`
     (D2 stands alone for the 6 margin venues).
  3. `_resolve_file_symbol` + `_resolve_writer_file_name`: cefi with instrument_id column → returns the id;
     `is_derivative=False, symbol='ADAF0:USTF0', file_symbol='BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN'` →
     `'…@LIN.parquet'` verbatim; `_get_writer` KEY still uses `_sanitize_symbol(bare symbol)` (bookkeeping unchanged);
     cefi CHAIN → `file_symbol=''`.
  4. tradfi isolation: `tradfi_shared._file_stem_for` unchanged.

---

### FIX D3 — Reader wire↔canonical bridge (fixes the audited silent data-loss), 3-tuple

**Repos: unified-api-contracts (map SSOT — done in FIX 0), market-tick-data-service (reader),
market-data-processing-service.**

**Per-service thin loaders (process-cached, fail-loud in prod / fail-soft only where the catalogue is legitimately
absent, e.g. test env):**

- **MTDS — NEW `engine/cefi_wire_bridge.py`:** module-level `get_cefi_wire_map() -> CeFiWireCanonicalMap | None`.
  Resolve `resolve_bucket_name(cloud="gcp" if is_gcp() else "aws", kind="instruments-store", asset_group="cefi")` +
  `get_storage_client()`; probe `prod/staging/dev/catalog.parquet` (mirror
  `CeFiCatalogReader._CATALOG_OBJECT_CANDIDATES`); read only `venue,instrument_type,raw_symbol,instrument_id`; build the
  UAC 3-tuple map; cache at module scope with a loaded-flag so a `None` isn't re-probed. Process cache is REQUIRED
  (`CanonicalParquetReader()` is constructed per-read in `book_microstructure_handler`; the ~424,699-row catalogue must
  not re-download per read). Reader+writer share this ONE map (also imported by FIX D1-live) so writer/reader symmetry
  holds.
- **MDPS — NEW `app/utils/cefi_wire_bridge.py`:** same shape, using the
  `resolve_bucket_name(kind="instruments-store", asset_group="cefi")` pattern already in MDPS `dependency_checker.py`.

**MTDS `reader.py` (scoped to `asset_group=="cefi"` AND `instrument_id is not None`):**

- **`:333-341` `_blob_paths_non_derivative`** — candidate stems (ordered, deduped):
  `[full canonical id, reverse-map raw_symbol, raw_symbol.upper()]`. New helper
  `_cefi_candidate_stems(venue, instrument_type, instrument_id)` uses `m.raw_symbol_for(venue, instrument_id)` (reverse
  map is injective — instrument_key is unique, so no 3-tuple needed on the reverse). `_read_first_existing_blob`
  (already chosen when `len>1`) returns the first that exists → canonical preferred, wire fallback → MIXED corpus
  resolves either way (fixes break #1: canonical `…ADA-USDT@LIN.parquet` absent, on disk `ADAF0:USTF0.parquet`).
- **`:382-391` `_build_row_filters`** — DROP the `("symbol","==",id)` pushdown for cefi (add `"cefi"` to the existing
  `not in ("prediction",…)` guard). Justification: the writer guarantees one symbol per per-symbol cefi file
  (`_file_stem_for` raises on >1) and stem-resolution already selects the exact instrument's file → no row filter is
  needed, and no single filter is correct across wire/wrapped/on-chain content classes (fixes break #2:
  `symbol == canonical` matched 0 rows against the wire `symbol` col; also would drop on-chain `BTC-PERP` content). Keep
  the filter for non-cefi; keep the prediction `canonical_question_group` filter.
- **`:470-489` `read_shard` post-read** — after the read, for cefi call new
  `_normalize_cefi_instrument_id(df, venue, instrument_type)`: rewrite the `instrument_id` column via the FORWARD
  3-tuple map `canonical_for(venue, instrument_type, symbol)`; leave rows unresolved/ambiguous unchanged (honest).
  **3-tuple is load-bearing here** (review blocking-risk #5): the 2-tuple forward map returns None for the BYBIT/OKX
  majors, so a narrow read would FIND the file but return rows whose column is still wire/wrapped → downstream joins
  silently miss. The reader knows `instrument_type` per shard read, so the 3-tuple lookup resolves the majors. Gated on
  `instrument_id` given + cefi → the default full-shard path (`instrument_ids=None`) is UNTOUCHED.

**MDPS:**

- **`app/utils/path_parsing.py:178-247`** (`blob_matches_any_instrument_id`) — for a parsed cefi id
  (`VENUE_TO_ASSET_GROUP.get(venue)=="cefi"`): after the `venue=`/`instrument_type=` axis checks, accept when the
  filename stem ∈ `{ canonical_symbol, full iid, raw_symbol, raw_symbol.upper() }` where
  `raw_symbol = get_cefi_wire_map().raw_symbol_for(venue, iid)` (reverse map). Refactor
  `blob_matches_canonical_instrument_id` to take an accepted-stems set (or add `_stems` variant). Non-cefi keeps the
  single `/{symbol}.parquet` rule (fixes break #3: wire `ADAF0:USTF0.parquet` failed `/{AMP-USDT}.parquet` substring →
  silently dropped from the scan). Fail-soft to today's behavior when the map is None (test env).
- **`app/core/canonical_writer_shaping.py:236-314`** (`_renormalize_legacy_tradfi_instrument_ids`) — RENAME to
  `_renormalize_legacy_instrument_ids` (update `__all__` at `:606` + the call site; no shim — delete-deprecated-code).
  Keep the tradfi branch. Add a cefi branch: for each unique in-file id, recover raw_symbol = `id.split(":",2)[2]` if
  `id.count(":")>=2` else `id` (covers wrapped-wire `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0 → ADAF0:USTF0`, and bare
  on-chain `BTC-PERP` by trying both the split tail and the whole string), then
  `canonical_for(venue, instrument_type, raw_symbol)` (instrument_type recovered from the path/df) → rewrite via
  `replace_strict`; unresolved/ambiguous unchanged (honest). Rename justified — the function is no longer
  tradfi-specific.

**Tests (D3):**

1. UAC map — covered in FIX 0 (3-tuple, ambiguous exclusion, reverse round-trip).
2. MTDS reader — extend `tests/market_interface/unit/test_canonical_parquet_reader.py`: monkeypatch
   `cefi_wire_bridge.get_cefi_wire_map`. (a) WIRE case: only `.../ADAF0:USTF0.parquet` exists, `symbol=[ADAF0:USTF0]*N`,
   `instrument_id=[BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0]*N`;
   `read_shard(venue='BITFINEX-FUTURES', data_type='trades', instrument_type='PERPETUAL', instrument_id='BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN')`
   → N rows (breaks #1+#2 closed) AND `df['instrument_id'].unique()==['…ADA-USDT@LIN']` (normalize-on-read). (b)
   CANONICAL-filename case: only `HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet` exists, content `symbol=[BTC-PERP]`;
   canonical id → rows returned (break #2 alone). (c) map==None → falls back to canonical-stem-only, existing tests
   pass; `instrument_ids=None` full-shard path asserted unchanged. (d) **3-tuple majors:** BYBIT SPOT_PAIR vs PERPETUAL
   BTCUSDT read returns the correctly-typed canonical column (proves review blocking-risk #5 closed).
3. MDPS `path_parsing` —
   `blob_matches_any_instrument_id('.../venue=BITFINEX-FUTURES/instrument_type=perpetual/data_type=trades/ADAF0:USTF0.parquet', ['BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN']) is True`
   (break #3); wrong-venue/itype blob → False.
4. MDPS renormalizer — cefi candles_df `instrument_id=[BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0]`, venue=BITFINEX-FUTURES,
   itype=perpetual, CEFI → out `…ADA-USDT@LIN`; ambiguous/unknown → unchanged; tradfi + already-canonical → no-op.
5. Optional ADC single-object integration: real
   `gs://market-data-tick-cefi-prd-…/…/venue=BITFINEX-FUTURES/instrument_type=perpetual/data_type=trades/ADAF0:USTF0.parquet`
   via `read_shard(instrument_id='BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN')` → non-empty (end-to-end proof the audited
   silent data-loss is closed).

---

### FIX D-features — features-service narrow cefi reads (Phase-0 P1; review missed-surface)

**Repo: features-service** — `raw_data_loader.py:126-179`.

- **Problem:** the plan flags a latent `instrument_id` (raw_tick) vs `instrument_key` (loader) column-name mismatch, and
  the loader does narrow per-instrument cefi reads with no wire→canonical bridge → after the filename migration these
  keep silently dropping (review missed-surface). This is NOT optional — it is a narrow-read consumer that must carry
  the bridge before the D4 GCS cutover (ordering gate).
- **Change:** route features' cefi narrow reads through the same MTDS reader path (which now carries the D3 bridge) OR,
  if features reads GCS directly, add the same `get_cefi_wire_map()` candidate-stem + normalize-on-read logic (features
  must read the catalogue as DATA — no service↔service import). Reconcile the `instrument_id`↔`instrument_key` column
  name on the real (non-mock) read path so the join key matches the canonicalized column.
- **Test:** extend the features raw-loader unit test with a cefi wire-filename fixture → asserts non-empty rows +
  canonical join key; a `map==None` fallback path leaves current behavior unchanged.
- **Flag:** confirm whether features reads via MTDS `reader.py` (then it inherits D3 for free — verify) or via its own
  GCS path (then it needs its own bridge). This determines the size of the change; verify before coding.

---

## 3. Migration scripts (Phase 1) + drain runbook

**All four scripts:** key off the ONE shared 3-tuple map (FIX 0 builder for MTDS scripts; IS scripts re-read their own
catalogue directly with the identical key + exclusion rule — no service↔service import); read `instrument_id` NOT
`canonical_instrument_id`; dry-run is the default; `--apply` only inside the drain; snapshot-first; idempotent (re-run →
0 changes); before/after row counts verified and recorded in the Progress Log; **precondition guard that refuses
`--apply` if the Phase -1 catalogue verify gate is not green** (encodes BLOCKER-A so it cannot be skipped).

### SCRIPT 1 — Parquet CONTENT backfill (MTDS)

`scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` (fork of
`migrate_cefi_dated_perps_margin_marker_2026_07_09.py`)

- **Inputs:** cefi tick bucket, day×venue prefixes (ALL cefi venues, widened from the 6 margin-marker). Reuses the
  fork's ThreadPoolExecutor + wedged-worker hard-deadline + backup-first `_backup_and_write` + re-read `_verify` +
  force-exit-on-wedge verbatim.
- **Logic change:** `patch_instrument_id_column` stops calling `derive_row_instrument_id` (only decomposes the 6 margin
  venues) and does a two-stage resolve of the frozen `instrument_id` column: (stage 1)
  `map[(venue, itype_upper, upper(df['symbol']))]`; (stage 2, on-chain lanes where the bundle `ticks.parquet` has a
  `coin` column / symbol doesn't match) fall back to `canonical_instrument_id()` / `legacy_bare_symbol_canonical_id()`
  imported from `migrate_onchain_perp_perpetual_canonical_2026_07_08.py` applied to the CURRENT content value.
  Unresolved-by-both → left as-is + counted (honest). Replace `_verify(expect_marker=True)` with "resampled written id
  == catalogue canonical". Do NOT re-fetch. Unifies the 3 non-canonical content classes (a) undecomposed margin-marker,
  (b) wrapped-wire non-margin, (c) on-chain `BTC-PERP` in ONE pass.
- **Snapshot target:** `_migration_backups/cefi_content_catalogue_2026_07_17/`.
- **Dry-run expectation:** per-class `would_patch` counts + `0` read_errors.
- **STOP-ON-SURPRISE:** bound `would_patch` against the audit's non-canonical population; halt if the resolvable
  fraction diverges materially from the dry-run measurement (re-measured post-rebuild).
- **Idempotency:** `--apply` one day → re-read sample → column == catalogue canonical; re-run `--dry-run` → `0`
  would_patch.
- **Before/after evidence:** per-class patched counts; sample row column value before vs after.

### SCRIPT 2 — Filename rename, Tardis lane (MTDS)

`scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py` (fork of
`migrate_onchain_perp_perpetual_canonical_2026_07_08.py`)

- **Inputs:** cefi tick bucket, **per-day-prefix iterator** (day×venue) — NOT the template's
  whole-`raw_tick_data/by_date/` walk (single-walk discipline: a new whole-corpus walk is review-blocking). Keeps
  `do_rename`'s idempotent GCS server-side copy+delete + `gcs_describe_object` dup-source handling + the PAIRED manifest
  key rewrite (rename + manifest together).
- **Logic change:** `plan_rename` resolves the new stem via the shared 3-tuple map keyed on
  `(venue, itype-from-path, raw stem)`; new stem = the FULL canonical `instrument_id` (Phase-0a pinned form — MUST
  byte-match `_file_stem_for`). Scope: single-instrument shards only (perpetual/spot_pair/future/option); SKIP chain
  bundles (`_BUNDLED_LEGACY_STEMS`, `ticks.parquet`/underlying-named).
- **Snapshot target:** relies on Script-1's content backup + the drain `_index/snapshots/` bucket-listing snapshot; the
  rename is reversible via the recorded old→new plan.
- **Dry-run expectation:** planned renames map raw stem → catalogue id; chain `ticks.parquet` skipped.
- **STOP-ON-SURPRISE:** halt if the planned-rename count for a prefix exceeds the object count (impossible-plan guard)
  or if a target stem collides with an existing distinct object.
- **Idempotency:** `--apply` one prefix → object renamed AND manifest key updated together; re-run →
  `already_canonical`.
- **Before/after evidence:** old→new object paths for a sampled prefix; matching manifest key delta.

### SCRIPT 3 — Manifest completion + de-dup (instruments-service)

`scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py` (fork of
`relabel_cefi_tardis_raw_symbol_to_canonical_2026_07_15.py`)

- **Inputs:** main `_index/availability_index.parquet` + every `_index/per_vm/*.parquet`. Reuses the snapshot to
  `_index/snapshots/`, STOP-ON-SURPRISE candidate bound, post-apply `_verify_gate`.
- **Three deltas:** (i) map from the rolled-up `prod/catalog.parquet` `instrument_id` column keyed on **(venue,
  instrument_type, upper(raw_symbol))**, excluding conflicts — recovers the active majors (BYBIT/OKX/BINANCE-FUTURES
  perps) the 2-tuple relabel left raw; (ii) rolled-up catalogue (all lifecycle) resolves delisted contracts the by_date
  snapshot missed; (iii) NEW de-dup pass: normalize coexisting `…@LIN` / `…:BASE-QUOTE` (no marker) / bare-wire
  spellings of ONE instrument onto the catalogue `instrument_id`, then `drop_duplicates` on the PINNED shard atom
  `[date, venue, data_type, instrument_type, instrument_id, pipeline_mode]` keeping the best `capture_status` via
  `_STATUS_RANK` (captured>empty_confirmed>attempted_failed>expected_unattempted). Retain the eu-duplicate reconcile
  pass.
- **Snapshot target:** `_index/snapshots/pre_d4_<ts>/` (shared drain snapshot).
- **Dry-run expectation:** total candidates within STOP-ON-SURPRISE; print relabeled / honest-unresolved /
  de-dup-collapsed / eu-dropped; confirm BYBIT/BINANCE-FUTURES majors now RESOLVE.
- **STOP-ON-SURPRISE:** re-measure bounds against the REBUILT catalogue (the pre-rebuild ~490k raw remainder is the
  upper bound); halt on candidate count outside the re-measured band.
- **Idempotency:** `--apply` → `_verify_gate` returns 0 (0 resolvable-raw captured rows, 0 eu/captured collisions);
  re-run `--dry-run` → 0 relabels.
- **Before/after evidence:** canonical-fraction before (84.44%) → after; per-major-venue resolved counts; de-dup
  collapse count.

### SCRIPT 4 — eu-twin drop, native-canonical on-chain lane (instruments-service)

`scripts/drop_cefi_eu_twins_native_canonical_2026_07_17.py` (derivative of Script-3's reconcile pass)

- **Inputs:** MAIN index only (per-VM shards carry no eu skeleton). Drop `expected_unattempted` rows keyed on
  `(venue, data_type, day)` where a canonical `captured` twin exists for the native-canonical venues (EXTENDED-STARKNET,
  PACIFICA-SOLANA, +~33). Exact-match join only (never fuzzy — under-reconcile is the safe direction).
- **Snapshot target:** `_index/snapshots/pre_d4_<ts>/`.
- **Dry-run expectation:** ~10,368 within bound, split 9,817 EXTENDED-STARKNET / 518 PACIFICA-SOLANA / ~33.
- **STOP-ON-SURPRISE:** bound ~[8000, 15000]; halt outside.
- **Idempotency:** `--apply` → re-run → 0.
- **Before/after evidence:** eu-twin count dropped per venue; residual-#3 gate RED→GREEN.

### DRAIN RUNBOOK (INFRA P0 — GATES all `--apply`)

- **Writers to stop (verified `bucket=_TICK_CEFI` in `deployment_service/vm_prefix_registry.py`):** Tardis lane
  `cefi-queue-*` (`launch-cefi-sharded-backfill.sh`); on-chain lane `cefi-hyperliquid-*` / `cefi-extended-*` /
  `cefi-lighter-*` (`launch-cefi-sharded-backfill.sh` + `launch-cefi-hl-aster-historical-backfill.sh`) + `aster-fwd-*`
  (`launch-aster-forward-poll.sh`); forward/cron/live (`launch-cefi-onchain-forward-poll.sh`,
  `launch-cefi-forward-poll.sh`, `launch-cefi-fwd-daily-cron-vm.sh`, `launch-mtds-live-cefi-consolidated.sh`).
- **Sequence:** stop ALL (both clouds) → run the manifest consolidator to a stable index → snapshot the cefi bucket
  `_index/` + a listing manifest to `_index/snapshots/pre_d4_<ts>/` → run scripts in order **0→1→2→(3,4)** →
  re-consolidate + verify → **re-enable writers ONLY after the Phase-0 tarball is confirmed live** (else re-launched
  writers re-corrupt with pre-fix ids — review blocking-risk #2).
- **HARD RULE:** no GCS cutover with writers live; no writer re-enable before the Phase-0 3-tuple code is deployed to
  every writer AND the D3 bridge is deployed to every narrow-read consumer (MTDS reader, MDPS, features, strategy, ml).
- **Box sizing:** Script-3's full-index de-dup groupby loads ~207MB / ~11.3M rows into pandas (~3-5GB — fits a normal
  box, proven by the relabel dry-run). No D4 script needs the 32-64GB box; only the SEPARATE phantom re-census (residual
  #2, out of this scope) does.

---

## 4. OPEN QUESTIONS / must-resolve-before-`--apply`

Merged from all four specs' `open_questions` + the reviewer's NEEDS-DECISION / ordering items. Ranked; the first five
are `--apply` blockers.

1. **[BLOCKER — key arity] Confirm the 3-tuple key `(venue, instrument_type, raw_symbol)` is adopted by D1, D3, and D4
   uniformly** (this blueprint mandates it; the raw D1/D3 specs used a 2-tuple). Without it the
   BYBIT/OKX/BINANCE-FUTURES majors get non-joining ids (writer wrapped-wire vs migration decomposed) — the exact
   instruments the program exists to fix. Verify every insertion point threads `instrument_type` (writer,
   `venue_fetch.py:386`, reader per-shard, MDPS axis).
2. **[BLOCKER — catalogue rebuild] Who owns the Phase -1 rebuild + verify gate, and when?** D1's DEPLOY (not just D4's
   `--apply`) requires a clean `prod/catalog.parquet`: `0` cefi `:PERP:` ids, `instrument_id == canonical_instrument_id`
   for cefi, re-measured ambiguity. Deploying D1 against the dirty catalogue keys the writer off rebuild-debris. Must be
   an explicit Phase-0 deliverable with a named owner and cited evidence.
3. **[BLOCKER — filename form] Lock the single-instrument filename stem = FULL `instrument_id`**
   (`VENUE:TYPE:BASE-QUOTE[@MARKER]`). The plan Phase-0 text + codex (`chart-candle-delivery-flow.md:274`,
   `canonical-write-conventions.md:128-134`, `per-asset-group-bucket-layouts.md:135`) say "canonical symbol segment"; D2
   / D4-script-2 / the on-chain precedent say FULL id. Writer, migration, and reader candidate-stems MUST agree
   byte-for-byte. Correct the contradicting docs (Phase 2) but lock the form before coding.
4. **[BLOCKER — reader deploy ordering] The D3 bridge must be deployed to EVERY narrow-read consumer** (MTDS reader,
   MDPS, features-service, and any strategy/ml/batch-live-reconciliation cefi reader) BEFORE D4 scripts 1/2 `--apply`.
   Enumerate the full consumer set and confirm each carries the bridge; the drain stops writers only, so a consumer on
   old reader code breaks on renamed/rewritten objects.
5. **[BLOCKER — live/on-chain column] Confirm FIX D1-live lands** so the live consolidated + on-chain
   `PartitionedTickWriter` write paths decompose the `instrument_id` COLUMN (not just the Tardis lane / not just the
   filename). Otherwise live cefi writes carry non-canonical columns → batch != live (ε=0 spine broken) and D2's live
   filename override reads a non-canonical column.
6. **[shard atom] Ratify `[date, venue, data_type, instrument_type, instrument_id, pipeline_mode]` (WITH
   `pipeline_mode`)** as the one true atom. The 2026-07-15 relabel omitted `pipeline_mode`; the on-chain rewrite
   included it. Script-3's de-dup groupby must include `pipeline_mode` or it can collapse two genuinely different
   pipeline_mode shards.
7. **[single honest-unresolved set] Re-measure the ambiguous/excluded count ONCE** off the pinned 3-tuple key against
   the REBUILT catalogue, and use that single number everywhere. The spec figures (297 snapshot / 439 3-tuple / 777
   / 781) are all pre-rebuild/pre-pinned-key and diverge per surface — a reader must honest-drop the same set the writer
   does.
8. **[margin-marker convergence] Confirm the operator wants NEW writes to match the CATALOGUE, not the 2026-07-09
   heuristic.** Catalogue-first changes the 6 margin venues' output for resolvable symbols (e.g. BINANCE
   `btcusdt_210326` → catalogue `@LIN-20210327` vs heuristic `20210326`, a settlement-date +1). Intended (catalogue is
   SSOT), not a blocker.
9. **[features read path] Determine whether features-service reads via MTDS `reader.py` (inherits D3 for free) or its
   own GCS path (needs its own bridge)** — sizes the D-features change; verify before coding.
10. **[HL/ASTER catalogue freshness] Does the instruments-service rebuild refresh HL/ASTER to `PERPETUAL@LIN`?** The
    live catalogue still carries `HYPERLIQUID:PERP:ARK` / mixed `ASTER:PERP:*` + `ASTER:PERPETUAL:*@LIN`.
    Reader/renormalizer canonicalize only as far as the catalogue goes. Recommend D3/D4 HL-ASTER canonical identity
    `depends_on` the catalogue-refresh todo (does not block the rest of D3).
11. **[ambiguous dated-futures] The residual ambiguous set (genuine expiry collisions vs rebuild-debris
    double-spellings, e.g. OKX-FUTURES `BTC-USD-200103` → 2 ids)** stays honest-unresolved, but re-measure
    genuine-vs-debris post-rebuild before committing STOP-ON-SURPRISE bounds; the doc's "resolve the 297 / resolve BYBIT
    majors" framing is only partly achievable (perps disambiguate by itype; dated-futures collisions do not).
12. **[777 vs 297] Confirm accepting the larger honest-unresolved superset** the full-lifecycle rolled-up catalogue
    excludes (vs the active-day relabel's 297). Not a blocker — it is the honest superset.
13. **[DERIBIT-COMBO] Combo symbols never resolve via the (venue, raw) map** (writer label DERIBIT-COMBO, catalogue
    stores venue=DERIBIT itype=COMBO) → stay on the existing passthrough `DERIBIT-COMBO:OPTION:<raw>` (already
    canonical-by-construction). Confirm acceptable (yes — not a regression).
14. **[OPTION / dated-FUTURE coverage] The "decompose ALL types" claim is unproven for per-option and per-expiry-future
    chains** — D1 inserts before the type branches, but catalogue `raw_symbol` coverage for those rows is unverified; on
    a miss they fall through honestly. Verify catalogue coverage for a sample OPTION + dated FUTURE before claiming
    full-type decomposition.
15. **[peak RSS] Measure peak RSS on the smallest cefi backfill box** (~353k-entry map ~100-150MB coexisting with the
    ~360k-row cached frame). If tight, drop the reader's frame cache after the map + sentinel enumeration (optimisation,
    not correctness).
16. **[MDPS scan cost] Confirm the orchestration_scanner is a long-lived worker** (it is, per
    `orchestration_workers.py`) so the one-time ~424,699-row catalogue download amortizes; a short-lived CLI would pay
    it per-run.
17. **[rename symbol vs `_renormalize_legacy_tradfi_instrument_ids`] Confirm no external importer** of the renamed MDPS
    symbol beyond in-repo tests before renaming to `_renormalize_legacy_instrument_ids` (grep showed only tests). If
    external, keep the name and just widen the branch.
18. **[full-shard normalize] Should the full-shard cefi read (`instrument_ids=None`) also normalize its column to
    canonical during the mixed window?** Left OUT (task says keep the default path untouched); flag as an optional
    follow-up once the D-content backfill lands (after which the on-disk column is already canonical).
19. **[catalogue data-quality gap] 16 of 89 BITFINEX-FUTURES catalogue rows carry a PERPETUAL id with no `@marker`**
    (e.g. `AMP-USDT`) while others do (`ADA-USDT@LIN`). The writer faithfully mirrors the catalogue (honest, correct),
    so filenames are mixed-marker for that venue — surface to the instruments-service catalogue-completeness workstream.

---

## 5. Reviewer verdict + blocking risks that MUST be closed first

**Verdict: `NEEDS-REDESIGN`.** This blueprint IS the redesign. The five reviewer blocking risks and their resolutions:

1. **Key-arity split producing non-joining ids for the marquee majors** → CLOSED by the mandated single 3-tuple key +
   single builder (FIX 0), adopted by D1/D3/D4 uniformly. (Open question #1 tracks the confirmation.)
2. **Re-enabling writers after the manifest migration re-corrupts** → CLOSED by making the Phase-0 code the 3-tuple
   writer AND gating writer re-enable on the Phase-0 tarball being live (drain runbook + ordering step 8).
3. **Live + on-chain cefi write paths not decomposed by D1** → CLOSED by the NEW FIX D1-live (column decomposition in
   `PartitionedTickWriter` for the live consolidated + on-chain paths). (Open question #5.)
4. **Silent corpus-wide degrade on catalogue schema-drift / empty map** → CLOSED by fail-loud: a registered prod
   resolver raises on empty/unreachable catalogue instead of silently returning `{}` (FIX 0 + FIX D1).
   Disabled-by-default for tests is achieved by not registering a builder, not by swallowing errors.
5. **Reader normalize-on-read leaving the ambiguous majors' column non-canonical** → CLOSED by the 3-tuple forward map
   in `_normalize_cefi_instrument_id` (reader has `instrument_type` per shard read). (Open question #1/#7.)

**Ordering issues** (all folded into §1's strict ordering): reader-bridge-before-cutover gate (open #4); filename-form
lock before coding (open #3); catalogue rebuild as a D1-deploy prerequisite (open #2); 3-tuple writer fixed before the
drain snapshot (blocking #2).

**Rule violations** (all resolved): shard-atom-identical → one 3-tuple atom WITH `pipeline_mode` (open #6);
single-source builder → exactly one `build_raw_symbol_map()` (FIX 0); one honest-unresolved set → single post-rebuild
measurement (open #7).

**Missed surfaces** now covered: features-service (FIX D-features); live/on-chain COLUMN (FIX D1-live); strategy/ml/
batch-live consumers (enumerated in the reader-deploy gate, open #4); OPTION/dated-FUTURE decomposition (verify gate,
open #14); SPOT_PAIR on ambiguous venues (resolved by 3-tuple, FIX 0/D1).

**Do not proceed to any `--apply` until open questions #1–#5 (the blockers) are confirmed closed and the Phase -1
catalogue verify gate is green.**

## 6. Todos

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_consolidated_closeout_2026_07_18.md` ("Phase A (code on `main`) ✅ · Phase B (deploy) ✅ ·
      Phase C (4 scripts dry-run-clean) ✅ · Phase D/E (drain + `--apply`) tracked in the forked child plan") and
      `plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (forked child plan, all 5
      apply/verify todos ran to completion — `status: complete`, "verified all 5 todos [x], residual gap explicitly
      CLOSED 2026-07-28 with cited live-verified proof," archived).** This blueprint's execution DID start and finish
      via that forked plan; the sign-off this todo asked for is superseded by that plan's own completed apply/verify
      chain, not merely promised. **CORRECTED 2026-08-12 (/plan-reconcile)**: the sentence that followed here through
      2026-08-12 read "this blueprint's execution has not started; every Phase 0/1 code fix and Phase 1 migration script
      above is still unshipped pending that sign-off" — directly contradicting the resolved-by-reference clause
      immediately above it. That was unedited leftover boilerplate from before the 2026-07-29 retag and is struck as
      stale/wrong; the forked-plan completion record is the current truth.
