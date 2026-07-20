---
doc_type: issue
title:
  "DeFi legacy dex_pools/ + lending_indices/ — the standing DELETE order is STALE and would destroy data (FOLD, not
  delete)"
summary:
  Two live plan docs (defi_consolidated_closeout Track 2, canonical_closeout_open_questions §A6) still order/authorize a
  batch DELETE of the legacy Shape-B `dex_pools/` + `lending_indices/` top-level prefixes. The SAME defi plan's
  later-authored R5 content-verify OVERTURNED that duplicate verdict — PARTIAL-OVERLAP, fold-not-delete, with 32
  legacy-only high-TVL raydium pools absent from canonical. Track 2 and A6 were never updated. A live GCS probe on
  2026-07-20 confirms the legacy objects are still present, that two of the five legacy cells have NO canonical twin at
  all, and that `execution-service` still reads the legacy shape at runtime through an already-broken
  `resolve_bucket_name` call. Executing the standing order as written is an irreversible data-loss event.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    gcs-path,
    delete-safety,
    canonical-twin,
    operator-notify,
    stale-instruction,
    dex-pools,
    lending-indices,
  ]
related:
  [
    defi_consolidated_closeout_2026_07_18,
    canonical_closeout_open_questions_2026_07_18,
    data_pipeline_reconciliation_skill_2026_07_20,
  ]
created: 2026-07-20
priority: P0
parent_epic: defi_master
source:
  "Phase-0 nine-dimension canonicalisation audit 2026-07-20 (contradiction B1), re-verified by independent live GCS
  probe + source read on 2026-07-20"
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# DeFi legacy `dex_pools/` + `lending_indices/` — the standing DELETE order is STALE

> **🔴 OPERATOR-NOTIFY — data-correctness class.** Do not execute `canonical_closeout_open_questions` §A6's GCS-delete
> batch, and do not execute `defi_consolidated_closeout` Track 2's "DELETE the dead top-level Solana `dex_pools/` +
> `lending_indices/` prefixes", as written. A snapshot-first delete is **not** sufficient protection here: the data has
> no complete canonical twin, so the delete would be a real loss of the only live copy of some cells.

## 1. The stale delete order — where it lives

Two live, unchecked P0/P1 items still instruct a delete:

- `plans/active/defi_consolidated_closeout_2026_07_18.md:467-470` — Track 2, first todo: _"**Pin the flat canonical path
  shape** …; DELETE the dead top-level Solana `dex_pools/`+`lending_indices/` prefixes (frozen 2026-04-14, 'Shape-B')…
  **Snapshot-before-delete**"_. Still `- [ ]`.
- `plans/active/issues/canonical_closeout_open_questions_2026_07_18.md` §A6 (pre-amendment `:77-79`) — _"**[P1,
  IRREVERSIBLE — snapshot-first] — GCS deletes**: the dead Shape-B `dex_pools/`+`lending_indices/` top-level prefixes…
  **REC: authorize as a batch with the pre-delete snapshot.**"_ — and §A8 sequences A6 into the start order and asks the
  operator to **authorize** it.

Both rest on a "dead / duplicate" premise that a later verification disproved.

## 2. The R5 overturn — same plan, later authored, opposite verdict

`plans/active/defi_consolidated_closeout_2026_07_18.md:254-262` (R5) carries the corrected verdict verbatim:

> **⚠️ Legacy `dex_pools/`/`lending_indices/` = PARTIAL-OVERLAP, FOLD-not-delete (the verify OVERTURNED the DUP verdict
> — a delete would have LOST real data).** … content-verify found **`dex_pools/raydium/SOLANA/2026-04-14` has 32
> legacy-only high-TVL pools ABSENT from canon** (XMR/USDC $47M, BNB/USDC $18M, USD1/USDC $9.9M, ZEC/USDC $7.5M, …;
> legacy=98 pools, canon=99, intersection only 66). … **DELETE legacy ONLY after the union is content-verified present
> in canon + manifest-registered — NEVER blind-delete.**

Root cause of the divergence is recorded at `:1019-1020` — the 32 raydium pools were dropped by the DeFi
catalogue-as-filter (`_catalogue_filter.py`, ~2026-07-09) intersecting raydium's top-100-by-liquidity fetch with the IS
catalogue; and the RCA of whether canon is trustworthy for other raydium/DEX days is still open at `:270-272`.

**Track 2 and A6 were never amended after R5 landed.** The corpus therefore contains an authorize-the-delete
recommendation and a never-blind-delete ruling side by side, with the delete-side item being the one an operator is
being asked to sign off (A8).

## 3. Live GCS probe, 2026-07-20 — and a correction to the audit's own claim

Probed `gs://market-data-tick-defi-prd-central-element-323112` directly (read-only listing).

**Legacy tree — still present, exactly the 8 objects R5 described:**

| Legacy prefix                                             | Objects    |
| --------------------------------------------------------- | ---------- |
| `dex_pools/{kamino,orca,raydium}/SOLANA/date=2026-04-14/` | 6 (2 each) |
| `lending_indices/{kamino,solend}/SOLANA/date=2026-04-14/` | 2 (1 each) |

**Canonical tree on the same day (`raw_tick_data/by_date/day=2026-04-14/…`), by venue:**

| Canonical cell                                                                        | Objects |
| ------------------------------------------------------------------------------------- | ------- |
| `venue=ORCA/chain=SOLANA/instrument_type=solana_amm_pool/data_type=dex_pool_state`    | 14,094  |
| `venue=RAYDIUM/chain=SOLANA/instrument_type=solana_amm_pool/data_type=dex_pool_state` | 100     |
| `venue=KAMINO/chain=SOLANA/instrument_type=lending/data_type=lending_indices`         | 47      |
| `venue=KAMINO/… data_type=dex_pool_state`                                             | **0**   |
| `venue=SOLEND/…` (any data_type)                                                      | **0**   |

**⚠️ Correction to the 2026-07-20 audit synthesis.** That audit's `non_canonical_inventory` entry records the canonical
twin as _"VERIFIED ABSENT (venue={ORCA,RAYDIUM,KAMINO,SOLEND} return zero objects on both day=2026-04-14 and
day=2026-07-15)"_. **That is wrong for day=2026-04-14** — 14,241 canonical objects exist for those venues on the relic's
own day. The zero result is correct only for day=2026-07-15 (DeFi capture is STOPPED, so recent days are empty), and
plausibly arose from probing `instrument_type=pool` when Solana AMM venues actually write
`instrument_type=solana_amm_pool`. This issue doc supersedes that inventory line.

The corrected probe **strengthens rather than weakens** the fold argument, and it independently corroborates R5:

- **RAYDIUM canonical = 100 objects** vs R5's measured `canon=99` pools — the twin exists but is the very
  partial-overlap R5 quantified. The 32 legacy-only pools are missing from a twin that _does_ exist, which is exactly
  why an existence-only check is not a delete proof (the CONTENT-verify precedent).
- **KAMINO `dex_pool_state` = 0** and **SOLEND = 0** — these two legacy cells have **no canonical twin at all**,
  matching R5's "2 known-UNIQUE cells (solend lending, kamino dex_pool)". For these, the legacy objects are the **only**
  copy.

## 4. A live service still READS the legacy shape

`execution-service/execution_service/providers/solana_amm_depth_provider.py:41`:

```python
_DEX_POOLS_PATH_TEMPLATE = "dex_pools/{protocol}/SOLANA/date={date}/"
```

Used at `:258-263` for `protocol in ("raydium", "orca")`, reached from `_load_from_gcs` (`:245`) via the public
`load_date()` (`:190`). Deleting the legacy prefixes breaks this reader's data source outright.

**And the same method is already broken independently** — `:248-254`:

```python
bucket = resolve_bucket_name(
    cloud="gcp",
    kind="market-data-tick-defi",
    asset_group="defi",
    env="prod",
    project_id=self._project_id,
)
```

Two defects, either one fatal:

1. **`env=` and `project_id=` are not parameters.** The signature is keyword-only
   `(cloud, kind, asset_group=None, deployment_env=None)` —
   `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py:366-372`. The call raises
   `TypeError` on unexpected keyword arguments.
2. **`"market-data-tick-defi"` is a bucket-NAME FRAGMENT, not a yaml `kind` key.** The key is `market-data`, a
   per-asset_group dict whose `DEFI` entry is the template
   `market-data-tick-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` — `configs/cloud-providers.yaml:93-97`. There is no
   `market-data-tick-defi` key under `gcp.storage`.

Critically, **line 248 sits OUTSIDE the `try:` at line 262**, whose `except Exception` only wraps
`_load_protocol_from_gcs`. So the raise propagates out of `_load_from_gcs` → `load_date()` → the caller, uncaught. This
is not an honest-absence path; it is an unhandled failure. The correct call is:

```python
resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")
```

(add `deployment_env="prod"` only if a specific tier must be pinned without mutating process env).

**Open sub-question (UNRESOLVED):** because the resolver raises before any read, it is not established whether this
provider currently succeeds in production at all, or whether it has been dead-on-arrival since the call regressed. That
changes the urgency ordering — if it is already dead, the reader is a latent bug rather than an active consumer — but it
does **not** change the delete verdict, which rests on the missing canonical content, not on the reader. Determining
which requires a runtime check that this read-only doc did not perform.

## 5. REQUIRED SAFE ORDER

The delete is not forbidden forever — it is forbidden **until it is proven safe**, in this order:

1. **Content-UNION the legacy cells into the canonical tree.** Per R5 `:259-261`: keep canon's richer 59-col schema on
   the 66-pool intersection, **ADD the 32 legacy-only raydium pools**, keep canon's 33 extras; fold the two
   canonical-twin-less cells (`solend` lending_indices, `kamino` dex_pools) wholesale. Union must be content-verified
   present in canon **and** manifest-registered.
2. **Repoint `execution-service` to canonical, and fix the resolver call in the same change.** Target the canonical
   `…/instrument_type=solana_amm_pool/data_type=dex_pool_state/` path (note: `solana_amm_pool`, not `pool`, per the
   probe in §3), and replace the call with `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`.
   Verify the provider actually returns snapshots at runtime — a green type-check is not evidence here.
3. **ONLY THEN consider deleting the legacy prefixes**, snapshot-first, and only for cells whose union is
   content-verified in canon. Cells failing the content check stay.

Steps 1 and 2 are independent of each other and can proceed in parallel; step 3 gates on **both**.

## 6. Actions taken 2026-07-20

- `defi_consolidated_closeout_2026_07_18.md` Track 2 — annotated in place with a dated `corrected 2026-07-20` block
  flipping the disposition to FOLD-not-delete. Original text preserved, marked superseded.
- `canonical_closeout_open_questions_2026_07_18.md` §A6 — same treatment; the "REC: authorize as a batch" recommendation
  is explicitly withdrawn.
- Neither checkbox was flipped; no code, GCS object, or manifest row was modified.

## 7. Resolution criteria

> Acceptance criteria, **not** dispatchable todos — written as plain bullets so `check_todo_format` does not ingest them
> as priority-less tasks. The dispatchable work lives in `defi_consolidated_closeout_2026_07_18.md` Track 2.

1. Operator acknowledges the withdrawn A6 authorization.
2. Union migration complete + content-verified + manifest-registered (R5 `:254-262`).
3. `execution-service` repointed to canonical and its `resolve_bucket_name` call fixed; runtime-verified.
4. Divergence RCA closed (`defi_consolidated_closeout_2026_07_18.md:270-272`) — is canon `dex_pool_state` trustworthy
   for other raydium/DEX days?
5. Only then: legacy prefixes deleted (snapshot-first) or an explicit decision to retain them.
