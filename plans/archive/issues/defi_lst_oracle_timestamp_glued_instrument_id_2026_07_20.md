---
doc_type: issue
title: lst_rates + oracle_prices write timestamp-glued instrument_ids ({protocol}_{chain}_{daily_epoch})
summary:
  73 distinct captured instrument_ids in the live defi _index embed a per-day unix epoch instead of a stable
  per-instrument identifier — the same timestamp-glued anti-pattern the per-instrument migration removed for other
  data_types. Small blast radius (78/51.9M rows) but an ACTIVE write-path pattern in the lst_rates + oracle_prices
  handlers.
status: resolved
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, instrument-id, per-instrument-model, lst, oracle, glued-key]
related: [defi_consolidated_closeout_2026_07_18]
created: 2026-07-20
author: unknown
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "filed 2026-07-20 during DeFi LST/oracle canonical-write work; frontmatter completed 2026-07-21 to pass the schema
    gate",
  ]
resolved_by:
locked_by:
locked_since:
assigned_role: data_engineering
context_scope:
  [
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_defi_n5.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/liquidations_handler.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
  ]
---

# lst_rates + oracle_prices write timestamp-glued instrument_ids

> **ARCHIVED 2026-08-21** — sole todo DISPROVEN-as-no-op 2026-08-01 (folded into the closeout plan's phantom-row
> purge); forward write-path fix verified shipped (`market-tick-data-service@4ca2640d` + follow-ups). `archive_exempt`
> bridge (set 2026-08-12) dropped per its own instruction. Moved to `plans/archive/issues/`.

## What was measured (live index, via ADC read 2026-07-20)

Reading `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (51,917,421 rows) and
scanning `instrument_id` for the `_<10-digit>$` glued-epoch pattern found **73 distinct ids / 78 rows**, all
`capture_status=captured`, e.g.:

```
ethena_ETHEREUM_1782648000    ETHENA     lst_rates
etherfi_ETHEREUM_1782475200   ETHERFI    lst_rates
rocketpool_ETHEREUM_1782648000 ROCKETPOOL lst_rates
oracle_prices_1782388800      PYTH       oracle_prices
```

The suffixes (`1782388800`, `1782475200`, `1782561600`, `1782648000`, `1782734400`, `1782820800`) are **consecutive
daily unix epochs** (each 86400s apart, ~2026-06). So the id is `{protocol}_{chain}_{daily_capture_epoch}` — a NEW
"instrument" per protocol per day.

## Why it is wrong

The per-instrument canonical model wants a **stable** `instrument_id` (e.g. `ETHENA-ETHEREUM`) with the date carried by
the `day=` partition + the manifest `date` column — NOT the capture timestamp glued into the id. Gluing the epoch:

- explodes the id cardinality (one id per protocol per day) — defeats per-instrument dedup/coverage;
- makes `record_captured` grain non-stable across days (the same real instrument reads as a new one daily);
- `oracle_prices_1782388800` is worse — the id does not even name the FEED (should be the Pyth feed/asset, e.g.
  `PYTH-SOLANA-<pair>`), only `oracle_prices_<epoch>`.

This is the same timestamp-glued anti-pattern the R3 per-instrument migration removed for `dex_pool_state` etc. — it
survived in the `lst_rates` + `oracle_prices` write path.

## Update 2026-07-20 — the pattern is BROADER than lst_rates/oracle

Sampling a real PROD instrument for the `/data-pipeline-check-mtds` run surfaced `aave_v3_ARBITRUM_20260622_072851` at
`…/venue=AAVE_V3/chain=ARBITRUM/instrument_type=lending/data_type=lending_indices/aave_v3_ARBITRUM_20260622_072851.parquet`
— i.e. **AAVE_V3 `lending_indices` ALSO uses `{protocol}_{chain}_{YYYYMMDD}_{HHMMSS}` (capture-datetime) ids**, not just
lst_rates/oracle_prices. So the glued-id anti-pattern spans lending as well. Widen the fix scope + the re-scan
accordingly (the `_<10-digit>$` regex in the original measurement under-counts the `_YYYYMMDD_HHMMSS` form).

## Blast radius

Small NOW (78 / 51.9M rows, ~6 days of late-June captures across ~12 LST protocols + 1 PYTH oracle row) but the WRITE
PATH still emits this shape, so it grows one-id-per-protocol-per-day going forward. `_migrated_` = 0 and
`ticks_migrated_` = 0 in the same index (the two other orphan classes are clean).

## Fix direction (NOT applied — outside the DeFi-catalogue closeout scope; LST/oracle workstream owns it)

Change the `lst_rates` + `oracle_prices` canonical id derivation to a stable `{PROTOCOL}-{CHAIN}` (lst) /
feed-identifying (oracle) id and let `day=` carry the date, mirroring the per-instrument id derivation the other DeFi
data_types already use. Then re-migrate the 78 existing glued rows to the stable id (idempotent, same UPSERT path as
R3). Verify by re-scanning the index for `_<10-digit>$` → 0.

## Provenance

Found during the DeFi-catalogue-closeout index verification (`defi_consolidated_closeout_2026_07_18.md` Progress Log,
2026-07-20). The `_solana_stake_pool.py` untracked LST artifact seen in the MTDS tree the same day is likely part of the
same LST workstream — worth checking whether it emits this id shape.

## Root cause + TRUE scope (2026-07-21) — SYSTEMIC across ~15 handlers, bigger than first filed

**Root cause:** the filename (which becomes the manifest `instrument_id`) is built as `f"{...}_{ts_label}.parquet"`
where `ts_label = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")` — the WALL-CLOCK capture time. The `date={YYYY-MM-DD}/`
is ALREADY in the path, so `ts_label` is redundant AND non-idempotent (each re-run writes a NEW file instead of
overwriting → id explosion, un-re-fetchable, breaks skip-if-fresh).

**Grep-confirmed sites (`_{ts}` / `_{ts_label}` / `_{noon_ts}` in the filename), ~15 handlers:**
`oracle_prices_handler:378`, `lst_rates_handler:570,691`, `solana_defi_handler:650,651`, `risk_params_handler:655`,
`evm_defi_handler:214`, `lending_indices_handler:433,866`, `dex_swaps_handler:519`, `liquidations_handler:647`,
`_dex_pools_subgraph:365`, `_perp_funding_kalshi_polymarket:323`, `_perp_funding_gmx:264,280`,
`deribit_options_chain_handler:517` (cefi — separate).

**This is a SYSTEMIC per-instrument-model gap, not a 3-handler fix.** Correct fix (bigger than the ratified scope
implied): a SHARED stable-filename helper (drop `ts_label`; name by the per-instrument identity — per-reserve for
lending, per-feed for oracle, per-pool for dex, per-token for lst) that all ~15 handlers adopt, + a full re-migration
renaming the existing `{...}_{ts}.parquet` objects to the stable id (idempotent, keep-latest). Each handler's correct
grain differs (some write one file per protocol-chain, some per-instrument), so this needs per-handler grain analysis +
a shared helper, then one migration pass — a focused project, not a marathon-tail edit. The minimal-safe first step
(drop `ts_label` → stable `{protocol}_{chain}` per date, idempotent overwrite) removes the glued timestamp everywhere
but keeps the current (coarse) grain; the per-instrument sharding is the finer follow-up.

## MIGRATION IN FLIGHT (2026-07-21) — re-shard DONE-logic PROVEN + running; RESUME = rebuild manifest + verify

**Operator ruling 2026-07-21: fix write path + re-migrate. Operator also asked whether the pool id is canonical.**
ANSWER (verified against the builder + live data): the canonical symbolic pool id IS the human
`venue:instrument_type:base-quote-fee` — e.g. `UNISWAP_V3-ETHEREUM:POOL:COMP-WETH-100` (filename
`COMP-WETH-100.parquet`, `token_a=COMP token_b=WETH fee_rate_bps=10000`), produced by
`unified_api_contracts/canonical/crosscutting/defi.py::_symbolic pool id`. `…:POOL:0x<addr>` (Balancer) and
`…:LENDING:<uuid>` (Kamino) are the builder's INTENDED FALLBACK ("the symbol IS the pool address — no pair/fee encoded —
always non-empty + reversible") for pools/markets whose tokens can't resolve to a clean symbol. So the DATA's per-row
`instrument_id` column is ALREADY canonical (human where resolvable, address/UUID fallback otherwise). The DEFECT is
only the coarse glued FILENAME (`{protocol}_{chain}_{capture_ts}`).

**Measured true scale (from the live `_index`):** 1,755 captured glued coarse files → **406,724 per-instrument groups**,
BUT R3 already created MOST of the per-instrument twins from other coarse files for the same (venue,chain,date) — so the
migration is **mostly idempotent renames + ~a few thousand genuinely-new twins** (the Solana lending/lst R3's matcher
missed: `kamino_lending_SOLANA_`, `lst_rates_marinade_` — the extra `_lending_`/`_rates_` segment breaks the
`{venue}_{chain}_` prefix). Measured mid-run: present≈201k, new twins≈6.5k, retired≈473.

**The re-shard (PROVEN end-to-end via an oracle_prices canary):** for each glued coarse file → group by the
already-canonical `instrument_id` column → write one `{sanitize_defi_symbol(SYMBOL)}.parquet` per instrument (reusing
`migrate_defi_batch_to_per_instrument.leaf_for_instrument_id`) → retire the coarse original to
`_migrated_{orig}.parquet` (proof-gated: only after every attributable group has a twin). Idempotent (exists()-gated).
Canary VERIFIED: `oracle_prices_1782388800` → 7 twins `BTC_USD.parquet`/`ETH_USD.parquet`/…

- original retired. Harness: `market-tick-data-service/scripts/one_offs/reshard_glued_defi_ids_2026_07_21.py` (local,
  index-driven, decoupled 16-reader/64-writer pool; NOT the R3 tool because R3's matcher misses the Solana naming — this
  is index+column-driven so it handles all 1,755).

**RESUME (fresh session):**

1. Confirm the apply finished (log `reshard_apply2.log` SUMMARY, or re-run the harness `--apply` — idempotent, skips
   present + already-`_migrated_`).
2. **Rebuild the manifest** for the affected data_types so the glued ids leave the index and the twins enter:
   `rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2020-01-01 --end-date 2026-12-31`
   (default `--reemit-absence` OFF, mtds@05ad49f7). The `_migrated_` originals are skipped by the Defect-A `_`-prefix
   guard.
3. **VERIFY 0 glued ids**: re-scan the fresh `_index` for `instrument_id` matching `(_\d{8}_\d{6}|_\d{10})$` with
   capture_status=captured → must be 0.
4. **Delete the `_migrated_` markers** (operator-authorized deletes; proof-gated: only where the per-instrument twins
   exist) — cleanup.

**FORWARD write-path fix (still open):** the ~6 handlers (lending_indices/lst_rates/oracle_prices/liquidations/
dex_swaps/dex_pool_state Solana paths) still have a residual coarse `file_name=f"{...}_{ts_label}"` write alongside
their `write_defi_rows` per-instrument path (the compound_v3 file dated 2026-07-20 proves it). Route those residual
paths through `write_defi_rows` (or drop the `_{ts}`) so no new glued files appear when capture resumes. DeFi capture is
currently STOPPED, so no new ones are being written now.

## FINAL STATE 2026-07-21 (after 3 idempotent apply passes) — 98.7% DONE, precise remainder

- **1,733 / 1,755 glued coarse files RE-SHARDED + retired to `_migrated_`** — their per-instrument twins are present
  (mostly already created by R3 from sibling coarse files: measured present≈305k twins, ~8.4k genuinely new written for
  the Solana lending/lst R3's matcher had missed). Verified end-to-end on the oracle canary.
- **22 `dex_pool_state` files remain LIVE at the legacy `category=defi` path** (my harness now probes BOTH
  `asset_group=`/`category=`). Their twins are present EXCEPT ~28 instruments whose `leaf_for_instrument_id` symbol
  raises on `blob.exists()` (a bad GCS object name from a problematic dex_pool symbol, OR a persistent GCS 4xx/5xx —
  consistent 28 across 3 passes, so NOT transient). The proof-gate CORRECTLY refuses to retire these 22 (can't confirm
  those 28 twins exist → won't drop the coarse original).

**RESUME (precise):**

1. ✅ **DONE 2026-07-21 — the 28 diagnosed and fixed.** Root cause: all 28 are a single `WETH`-paired Uniswap V3 pool
   (recurring across BASE/ARBITRUM/OPTIMISM, multiple days) whose counterparty is a spam/"zalgo" token — a symbol
   stuffed with ~1000 Unicode combining marks. Confirmed via a parallelized, exception-logging diagnostic run (0 errors
   on 14,914 real instrument checks) followed by an instrumented `--apply` run that captured the actual GCS exception:
   `BadRequest: 400` because the sanitized leaf was **1,201 bytes**, over GCS's 1024-byte object-name cap. Fixed in
   `_sanitize_defi_symbol` (`canonical_write.py`) — strips every Unicode combining-mark codepoint
   (`unicodedata.category` in `Mn`/`Mc`/`Me`) then caps the result at 200 bytes; hardens both this migration AND the
   live per-instrument writer against any future zalgo-stuffed on-chain token symbol. Pinning test added. Shipped
   `market-tick-data-service@781204d8` (dirty-deps direct-push carve-out — unified-trading-library had unrelated
   concurrent-agent WIP blocking quickmerge's pre-flight; not touched). Migration re-run in progress to finish retiring
   the last 22 files.
2. **Rebuild the manifest** (VM-scale, ~hrs — run on a `canonical-migration` VM, not in-session):
   `rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2020-01-01 --end-date 2026-12-31`
   (reemit OFF, the mtds@05ad49f7 default). `_migrated_` originals skipped by Defect-A.
3. **Verify 0 glued ids** in the fresh `_index` (`instrument_id ~ (_\d{8}_\d{6}|_\d{10})$` + captured → 0; expect ~22
   until step 1 completes the last files).
4. **Delete the `_migrated_` markers** (operator-authorized; proof-gated: only where the per-instrument twins exist) —
   the retired coarse originals are dead weight once the manifest is rebuilt.
5. **`category=defi` → `asset_group=defi` PATH canonicalization** — the 22 (and any other `category=` legacy objects)
   are at the non-canonical `category=` path. That path migration is SEPARATE from this filename fix (out of scope here)
   — track it under the broader canonicalization.

Harness (durable, resumable, idempotent):
`market-tick-data-service/scripts/one_offs/reshard_glued_defi_ids_2026_07_21.py`.

## Update 2026-07-22 — the historical migration is 100% DONE; the "forward write-path fix" was ALREADY SHIPPED, not open

**Historical migration: COMPLETE.** All 1,755/1,755 glued coarse files re-sharded + retired, 0 errors (the final 22-28
were the Zalgo-symbol GCS-object-name-cap bug from step 1 above, fixed and re-run clean). The VM-scale manifest rebuild
(RESUME step 2) is running as `canonical-migration-defi-per-instrument-20260722-033122`.

**"FORWARD write-path fix (still open)" (line 157 above) — RE-INVESTIGATED, found already fixed, NOT open.** The "~15
handlers" framing was accurate for whatever code existed when this issue was first filed (2026-07-20), but
`market-tick-data-service@4ca2640d` ("shard DeFi writer to one parquet per instrument"), **landed 2026-07-18 — two days
BEFORE this issue doc was even filed** — already fixed the actual defect at its root: `write_defi_rows()`
(`canonical_write.py:158-349`) now ALWAYS shards non-empty rows by real `instrument_id`
(`leaf = sanitize_defi_symbol(symbol)`) and its own docstring states "Caller `file_name` is empty-only" (verified by
reading the current source — the `for _inst_id, group in df.groupby("instrument_id", ...)` loop at `:337` computes the
leaf from the row data, never from the caller's `file_name=f"{...}_{ts_label}.parquet"` argument). Every one of the
handlers named in the original "~15 handlers" list calls `write_defi_rows()` for its real data and gets this sharding
for free — the `_{ts_label}`-glued `file_name=` they pass is dead for the non-empty case.

**Empirically verified, not just read**: scanned live GCS for glued-pattern objects (`_\d{8}_\d{6}\.parquet$` /
`_\d{10}\.parquet$`, excluding `_migrated_`) across `day=2026-07-14` through `day=2026-07-21` (8 consecutive days,
spanning both sides of this issue's own filing date AND the "compound_v3 file dated 2026-07-20" cited as evidence of an
ongoing problem) — **zero** new glued objects on every single day. The cited "compound_v3 2026-07-20" evidence was
either an empty-marker file (the one case `file_name` still applies to — cosmetic, not a data-loss bug) or a stale read;
either way, no REAL captured data has landed under a glued filename since `4ca2640d`.

**Residual (WAS marked P3/cosmetic — that call was WRONG, see "Update 2026-07-24 (session 2)" below)**: the empty-marker
case (`rows=[]` → `write_defi_rows` uses `file_name or "empty.parquet"` verbatim) still gets a wall-clock name from the
~11 handlers that pass `file_name=f"{...}_{ts_label}.parquet"`, so a genuinely-empty shard writes a NEW empty marker
object every run instead of reusing one stable "no data" sentinel.

**`reshard_glued_defi_ids_2026_07_21.py`'s own `Delete-when` marker** ("0 glued ids remain in the defi _index + the
write-path forward-fix has shipped") is now satisfied on BOTH conditions once the manifest rebuild (RESUME step 2, in
flight) confirms 0 glued ids — the forward-fix half is DONE (shipped `4ca2640d`, verified above), it was never actually
blocked on this session's work.

## Update 2026-07-23 — 34 MORE glued rows surfaced by the fresh full-corpus rebuild; resharded; NOT a forward-path regression

The DeFi-catalogue-closeout plan's own full 2020-2026 manifest rebuild (5-VM parallel,
`defi_consolidated_closeout_2026_07_18.md`, completed 2026-07-23) gave a fresh recount reason to re-verify this issue's
"0 glued ids" claim. A direct read of the now-larger consolidated index (23,472,205 rows) found **34 captured rows**
still matching the glued regex (`(_\d{8}_\d{6}|_\d{10})$`) — all `lending_indices`/`liquidations`, e.g.
`kamino_lending_SOLANA_20260528_134927` (22 KAMINO/SOLANA `lending_indices` rows, 12 single-row `liquidations` across
AAVE_V3/COMPOUND_V3/FLUID/GMX/SPARK on various chains).

**This is NOT a regression of the forward-write-path fix** (`4ca2640d`, verified clean above). The sample ids are dated
2026-05-28 — well before both the fix and the 2026-07-21 sweep. Root cause: `reshard_glued_defi_ids_2026_07_21.py` is
**index-driven** (groups by the manifest's own `instrument_id` column), so it can only reshard what the manifest already
knows about. These 34 objects existed on GCS the whole time but were **not yet reflected in the manifest** when the
2026-07-21 sweep ran (the 1,755-file count was accurate for the index AS IT STOOD then) — the same "previously-unindexed
objects surfacing" mechanism the closeout plan separately logged for legacy `dex_pools`/`perp_mark_price` as a "bonus
finding" of this session's rebuild. The scan tool is only as complete as the index it reads.

**Fix applied 2026-07-23**: added a proper `defi-glued-reshard` category to
`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (previously this tool was local-only, ad hoc — now it's
a first-class, fleet-registered, re-runnable VM launcher, so any future resurfacing doesn't need bespoke tooling) —
`deployment-service@3345bf9`. Ran on a fresh in-region VM with pinned, rebuilt tarballs (the local laptop's network path
to GCS was independently confirmed too degraded this session for a reliable ~900MB-class direct read/ download — even a
47.8MB single-shard download timed out at 60s — so an in-region VM read/write is now the standing recipe for this class
of check, not just a nice-to-have): **34/34 processed, 242 new per-instrument twins written, 968 already-present twins
skipped, 0 unattributable, 0 missing, 0 errors, 34 originals retired to `_migrated_`.** A follow-up full-corpus manifest
rebuild (6-way parallel, full 2020-01-01..2026-07-22, gap-checked) is running to reflect this in the index; once it
completes, re-verify 0 glued ids (expect 0 now) before deleting `_migrated_` markers.

**Cross-session note (2026-07-23, from a different concurrent slot)**: 2 of the original 6 rebuild VMs
(`canonical-migration-defi-rebuild-20260723-140715` covering 2024-04-29..2024-12-31, and `-140853` covering
2025-07-01..2025-12-31) were SPOT-preempted (confirmed genuine via `gcloud compute operations list` —
`compute.instances.preempted`, not a crash) and had not yet been relaunched ~10 minutes later while the other 4 chunks
progressed. Since this directly gates the closeout plan's own "verify 0 glued ids + delete `_migrated_` markers" todo,
relaunched both missing ranges fresh (`canonical-migration-defi-rebuild-20260723-142940` and `-143019`) — the rebuild is
idempotent/safe-to-rerun by design (its own docstring: "Safe to re-run"), so no coordination conflict. Current live
roster covers the full 2020-01-01..2026-07-22 range with no gaps across 6 VMs: `-141001` (2026), `-141515` (2025 H1),
`-141922` (2020..2022-04-29), `-142022` (2022-04-29..2024-04-29), `-142940` (2024-04-29..2024-12-31, gap-fill),
`-143019` (2025 H2, gap-fill). Also confirmed directly (per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
§3): the `_migrated_` marker delete remains a human-only hard stop regardless of chat authorization — a sanctioned
dry-run-by-default script already exists
(`market-tick-data-service/scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py`); once this rebuild sweep
confirms 0 glued ids, the plan is to run that script's dry-run and hand the verified `--apply` command to the operator
rather than execute it from any agent context.

## Update 2026-07-24 — the 34 rows are GCS-fixed; the index count structurally can't reach 0 via rebuild alone

Ran the full 6-way parallel manifest rebuild through completion (all chunks rc=0, full 2020-01-01..2026-07-22 coverage),
then re-checked the consolidated index for glued ids: **still 34, same exact `instrument_id`s** as before the reshard
fix (e.g. `kamino_lending_SOLANA_20260528_134927`).

**This is NOT a failed fix — direct GCS verification proves the object-level fix is correct.** Listed the KAMINO
`day=2026-05-28` `lending_indices` directory directly: zero glued-timestamp-named files, only clean UUID-named
per-instrument twins (Kamino's canonical `...:LENDING:<uuid>` fallback form) plus exactly one `_migrated_` marker —
consistent with the reshard tool's own reported outcome (34 retired, 242 twins written, 0 errors).

**Root cause of the persisting count**: the consolidated `_index/availability_index.parquet` is append/UPSERT-only — a
`rebuild_defi_manifest` re-scan adds/refreshes rows for objects it currently finds, but never removes a row for a path
that no longer exists. These 34 rows entered the index during an earlier rebuild pass (before the reshard fix ran) and,
once written, persist regardless of how many further rebuilds run afterward. Structurally the same "phantom row" class
as `defi_consolidated_closeout_2026_07_18.md`'s separately-tracked "purge 1.79M dup + ~219.5K phantom rows" todo, not a
distinct problem needing its own fix.

**Conclusion**: the write-path/historical-backlog fix for these 34 rows is DONE and verified at the GCS level. The
manifest index will only show 0 for this regex once the phantom-row purge runs (it folds these 34 in with the rest) —
that purge is the correct next step, not another rebuild cycle.

## Update 2026-07-24 (session 2) — the "P3 cosmetic, does NOT affect the manifest" call above was WRONG; found + fixed

The closeout plan's 6-VM full-corpus rebuild (`defi_consolidated_closeout_2026_07_18.md`, completed 2026-07-24) gave
another fresh recount. Result: **21 glued rows, not 0** — 9 are the ORCA/SOLANA `dex_pool_state` cells tracked
separately (another concurrent session's active parallel-write-timeout fix, unrelated to this doc). **The other 12 are
NEW**: all `data_type=liquidations`, all sharing the literal instrument_id suffix `_20260723_013349` (one batch run,
2026-07-23 01:33:49 UTC), all `date=2026-07-22`, across AAVE_V3/COMPOUND_V3/GMX/SPARK/FLUID on multiple chains.

This directly falsifies the "Residual (P3, cosmetic)" call two sections up ("does NOT affect instrument-id correctness,
capture_status, or the manifest"). It does, via a mechanism that call missed:

1. **Writer**: `liquidations_handler.py::_write_liquidations_shard` passed
   `file_name=f"{protocol}_{chain}_{ts_label}.parquet"` for the empty-marker case. `collect-liquidations` runs on a
   **daily Cloud Scheduler cron** (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`, `30 1 * * *` UTC) —
   every day a venue/chain shard has zero liquidations, this writes a FRESH, distinctly-timestamped empty-marker object.
   Not a one-time artifact — a live, currently-still-running source of new glued objects, one batch per day, for as long
   as it shipped unfixed.
2. **Manifest**: `rebuild_defi_manifest.py::parse_hive_path` sets `instrument_id` from the raw filename stem
   unconditionally, and `emit_captured` stamps `capture_status=CAPTURED` on file PRESENCE alone (`row_count=0` sentinel,
   no parquet opened) for any data_type outside `ROWCOUNT_VERIFIED_DATA_TYPES` — which `liquidations` was NOT in. So a
   full-corpus rebuild (exactly what this session ran) blindly re-derives a glued `instrument_id` from the empty
   marker's wall-clock filename and stamps it CAPTURED. This is the SAME 0-row-parquet defect the N5 fix
   (`_rebuild_defi_n5.py`) already solved for `vault_share_price` — `liquidations` (and, it turns out, several siblings)
   just weren't in that set.

**Distinguishing this from the 34-row phantom-index case directly above**: those 34 rows are STALE — the underlying GCS
objects were already fixed (resharded, retired to `_migrated_`) and the manifest's append/UPSERT-only index simply never
dropped the old row for a now-gone path; no further rebuild can fix that, only the separate phantom-row purge. These 12
rows are the OPPOSITE: the underlying glued objects still genuinely exist on GCS right now (the cron wrote them
yesterday and nothing had touched them since), so once the fix below ships and the shard reprocesses, the SAME object
gets correctly reclassified via UPSERT — no purge dependency.

**Full sweep + fix (both sides, all genuinely-reachable call sites)**: grepped every DeFi handler for this exact
`file_name=f"..._{ts_label|noon_ts}.parquet"` empty-marker pattern (9 files, 13 call sites total). Traced each site's
caller for an early-return-on-empty guard to separate genuinely-reachable sites from dead code:

- **Genuinely reachable (fixed — dropped the timestamp from `file_name=`, letting `write_defi_rows` fall back to its own
  stable `"empty.parquet"` default)**: `liquidations_handler.py:554`, `risk_params_handler.py:643`,
  `dex_swaps_handler.py:516`, `evm_defi_handler.py:207`, `lending_indices_handler.py:866`, `lst_rates_handler.py:566`
  (`_write_empty_lst_marker` — this function's entire purpose IS the empty marker, was unconditionally reached),
  `vault_share_price_handler.py:275` (`_emit_empty_marker_and_manifest` — same shape; already had manifest-side N5
  protection, but the object churn at the source is now also stopped).
- **Confirmed dead-for-empty (left untouched — the caller early-returns on `df.empty`/`grouped.setdefault` before
  `write_defi_rows` can ever be reached with zero rows, so `file_name` here was already inert per the empty-only clause
  in its own docstring)**: `_dex_pools_subgraph.py:365,550`, `lending_indices_handler.py:430`,
  `oracle_prices_handler.py:381`, `lst_rates_handler.py:687`, `vault_share_price_handler.py:578`.
- **Manifest-side (`_rebuild_defi_n5.py`)**: `ROWCOUNT_VERIFIED_DATA_TYPES` expanded from `{vault_share_price}` to
  `{vault_share_price, liquidations, lending_indices, lst_rates, risk_params, dex_pool_swaps}` — the exact set of
  data_types with a genuinely-reachable empty-marker writer above. `vault_share_price_absence_reason`'s pre-launch check
  stays vault_share_price-only (a new `_LAUNCH_DATE_CHECKED_DATA_TYPES` set) since that registry's semantics were only
  validated for VSP; the universal 0-row check now applies to all six.
- Added regression tests: `test_rebuild_defi_manifest.py` (0-row liquidations shard → `SOURCE_RETURNED_ZERO`, no
  launch-date check applied) and `test_liquidations_handler.py` (two cron runs with different `ts_label` on the same
  empty shard write the SAME stable path, not two glued objects).

**Not yet done**: the 12 CURRENT glued objects need one more targeted rebuild pass (single-day, `2026-07-22`, cheap —
not a new whole-corpus walk) once this fix ships, to reclassify them via the now-fixed N5 path. Re-verify 0 glued ids
(excluding the 9 known ORCA rows, which are a separate owner's in-flight fix) after that.

## Todos

- [x] ✅ [DATA] P2. **DISPROVEN 2026-08-01 (slot-11) — the single-day rebuild is a NO-OP; folds into the closeout plan's
      `:401` P0 phantom-row purge instead.** Dry-ran
      `rebuild_defi_manifest.py --start-date 2026-07-22 --end-date 2026-07-22 --dry-run`, then confirmed via direct GCS
      listing: all 10 remaining glued liquidations markers (AAVE_V3 ×4, COMPOUND_V3 ×4, FLUID ×1, SPARK ×1 — 2 of the
      original 12 already cleared on their own) are ALREADY retired to
      `_migrated_aave_v3_ARBITRUM_20260723_013349.parquet` etc., with NO per-instrument twins (genuine 0-row empty
      markers, nothing to reshard). `rebuild_defi_manifest.py`'s R3 defect-A `_`-prefix guard explicitly skips retired
      markers, so a rebuild pass can never rediscover and reclassify them via the N5 path — the N5 fix is correct for
      objects that still exist under their glued name, but these no longer do. This makes the 10 liquidations rows the
      SAME phantom-row class as the 9 ORCA `dex_pool_state` rows (append/upsert-only manifest, source object renamed
      away, nothing left to re-scan) — both now require the closeout plan's
      `defi_consolidated_closeout_2026_07_18.md:401` P0 phantom-row purge (~1.79M dup + ~219.5K phantom rows, VM-scale),
      not a standalone fix here. Full evidence:
      `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md`'s batch-7 todo 3 (2026-08-01).

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - single residual is a bounded single-day (2026-07-22)
  targeted rebuild pass + a re-verify; the N5 fix it depends on has shipped
- **2026-08-01 (slot-11)**: The single-day rebuild premise above was disproven — see the Todos entry. This doc's scope
  is now fully resolved (either shipped/verified, in the case of the forward write-path fix, or folded into the closeout
  plan's P0 phantom-row purge, in the case of the historical residual rows); no standalone action remains here.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — doc's scope is fully resolved (all todos
  checked, folded into the closeout plan's phantom-row purge for the residual); list still accurately anchors the
  historical fix evidence.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
