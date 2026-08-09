---
doc_type: plan
title: DeFi venue hygiene + lst-rates aggregation residual — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  2 small residual todos forked verbatim out of the archived migration-verification/orphan-safety harness plan
  (2026-07-24 plan line-cap remediation split): folding the `lst-rates` corpus into the DeFi could-exist / data-status
  view, and reconciling orphan/junk DeFi venue spellings (`VAULT`, `SUSHISWAP` classic-vs-V3 ambiguity).
status: active
nature: process
asset_group:
  [defi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # lst-rates + DeFi venue spellings (VAULT/SUSHISWAP) are DeFi-only content, inherited the parent harness's
  # cross-cutting tag on fork instead of being corrected to its real single-AG scope
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [defi, lst-rates, venue-canonicalisation, manifest, migration, plan-split, residual]
related:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (its own Progress Log, entry
  dated 2026-06-16) as part of the 2026-07-24 plan line-cap remediation
  (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's durable
  protocol (CF-15…CF-21) had already migrated to codex; these were the last genuinely-open items in its defi-venue
  thread and are tracked here going forward.
context_scope:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py,
  ]
---

# DeFi venue hygiene + lst-rates aggregation residual

> **Origin.** Both todos below are moved **verbatim** from
> `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; full historical Progress
> Log archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an Appendix).
> Neither is a data gap — both are data-status aggregation / venue-spelling hygiene items, explicitly NICE-TO-HAVE / P3
> in the source.

## Todos

- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-2) — stale premise, root cause found + fixed elsewhere.** The dedicated
      `lst-rates-central-element-323112` bucket this todo names no longer exists — verified live
      (`gcloud storage buckets describe` → 404) — it was migrated into the shared `market-data-tick-defi` bucket and
      deleted 2026-07-13/ 14 (`defi_dedicated_bucket_shared_migration_2026_07_13.md`, all todos `[x]`), and the 5 LST
      venues' `lst_rates` capability-registry entries were fixed 2026-07-07/10
      (`defi_turbo_api_hides_real_captured_data_2026_07_07.md`) — verified live: `ANKR-ETHEREUM`/`MANTLE-ETHEREUM`/
      `STADER-ETHEREUM`/`STAKEWISE-ETHEREUM`/`SWELL-ETHEREUM` all carry `lst_rates` entries in
      `unified_api_contracts/registry/defi_venue_capabilities.py`. deployment-api's own DeFi sub-bucket-fold machinery
      (`_BUCKET_CATEGORY_OVERRIDES`/`_MTDS_DEFI_SUB_DIMENSIONS` in `services/data_status/defi.py`) is now empty — every
      DeFi sub-bucket that ever existed (incl. `lst-rates`) has been consolidated into the single shared bucket, not
      permanently multi-bucket-folded; there is nothing left to fold. **Found + fixed the actual live residual bug
      instead**: `DEFI_NON_PROTOCOL_VENUE_PREFIXES` in
      `deployment-api/services/data_status/{rollup_cache, breakdowns_domain}.py` matched on venue PREFIX
      (`v.split("-",1)[0]`), which silently stripped `ANKR-ETHEREUM` (a real, capability-registered LST protocol with
      genuinely captured data) — plus every `ALCHEMY-<chain>` venue and `COINBASE-ETHEREUM` — from the rollup venue
      list + per-chain breakdown, just for sharing a prefix with the bare noise strings
      `"ANKR"`/`"ALCHEMY"`/`"COINBASE"` (confirmed real: `token_transfers_handler.py` reads a chainless
      `venue="ALCHEMY"` instruments lookup). Fixed both call sites to match on the full venue string; regression test
      added (`test_strip_defi_ghost_venues_keeps_real_prefix_sharing_venues`). Shipped: `deployment-api@f919c87`.
- [x] ✅ [DATA] P3 (VAULT half only). **DONE 2026-07-26 (slot-2) — `VAULT` half of this todo was already resolved,
      SUSHISWAP half stays open.** `VAULT` is NOT present in `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` (grep-
      verified 0 matches) — already excluded, guarded by a passing regression test
      (`unified-api-contracts/tests/unit/test_mtds_venue_coverage.py::TestNewlyCapabilitiedDefiVenues:: test_vault_is_not_in_all_defi_venues`,
      live-run confirmed green). The residual 1,113 `VAULT`-labeled captured rows (pre-attribution-window
      `vault_share_price` rows the writer's per-vault `_VAULTS` protocol lookup never covered) are correctly
      uncounted/invisible today, not incorrectly excluded — reattributing them to a real protocol would need a new
      one-off manifest/GCS migration script (writer-side work, out of scope for a registry edit). **`SUSHISWAP`
      classic-vs-`SUSHISWAP_V3` alias question stays explicitly open** — genuinely undecided data-semantics call, was
      also explicitly out of scope for the dispatched todo that closed this
      (`defi_satellite_ao_dispatch_batch2_2026_07_26.md` item 4: "Do NOT touch the bare-`SUSHISWAP` classic-vs-V3 alias
      question in the same registries — that is explicitly out of scope here (conflict-gated)").
- [x] ✅ [DATA] P3. **Decide the SUSHISWAP classic-vs-V3 alias question** — the bare-`SUSHISWAP` venue attribution
      (classic vs `SUSHISWAP_V3`) is a genuinely undecided data-semantics call, explicitly left open when the rest of
      this doc's VAULT/SUSHISWAP todo closed 2026-07-26. **RULED (operator, 2026-08-08)**: fold bare `SUSHISWAP` into
      `SUSHISWAP_V3` going forward, AND migrate + purge the historical GCS object filenames/paths and manifest rows to
      the canonical venue name — not a forward-only labeling default. This is explicitly the same standard the operator
      set for the sibling factory-address decision below: two sources of truth (a non-canonical `SUSHISWAP` label
      sitting alongside `SUSHISWAP_V3` in real GCS paths + manifest rows) is the actual defect being fixed, not just the
      registry/label going forward.
- [ ] [SCRIPT] P2. **BLOCKED-OPERATOR-DECISION 2026-08-08 (slot 16) — scoping revealed the premise doesn't hold as
      literally worded; see the finding + queued question below before any migration executes.** Original text preserved
      for the audit trail: "Migrate + purge bare-`SUSHISWAP` historical objects/manifest rows to `SUSHISWAP_V3` — per
      the 2026-08-08 ruling above: (1) enumerate every GCS object under the DeFi bucket whose path/filename carries the
      bare `SUSHISWAP` venue token (not `SUSHISWAP_V2`/`SUSHISWAP_V3`), (2) for each, resolve/rewrite to the canonical
      `SUSHISWAP_V3` path (venue + chain, matching the canonical naming convention this same epic already established
      for the composite-venue-objects fold), (3) re-register the corrected paths in the manifest, (4) purge the original
      non-canonical objects/rows once the canonical twin is verified present — a fresh
      `gcs_bucket_soft_delete_retention_seconds()` reversibility check on the target bucket qualifies this for
      agent-execution without operator sign-off per `gcs-and-manifest-delete-safety-protocol.md` §3a (same pattern as
      the sibling `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` migration, archived 2026-08-08). No
      backfill needed — this is a rename/relabel of already-captured data, not new capture. Scope this against the live
      row count for bare `SUSHISWAP` first (a fresh availability_index read) before estimating size."

## Finding (2026-08-08, slot 16) — the scoping step surfaced a genuine data-correctness ambiguity, not a simple rename

Ran the todo's own required first step (a fresh, filtered `read_availability_index` read — never a corpus walk) before
writing any migration code, per this doc's + the sibling `_2026_08_04` precedent scripts' established idiom:

```python
read_availability_index(bucket, columns=["date","venue","chain","data_type","capture_status","instrument_type"],
                         filters=[("venue", "==", "SUSHISWAP")])   # then repeated for venue == "SUSHISWAP_V3"
```

**Bare `venue=SUSHISWAP` (613,628 rows, 483,751 `captured`, 1,761 dates, 2021-08-31..2026-08-02) is 100%
`chain=ARBITRUM` — ZERO rows on `chain=ETHEREUM` or blank/null chain.** Cross-checked against GCS directly (bounded,
prefix-scoped listings, 5 sampled dates 2022-2026, never a corpus walk): `venue=SUSHISWAP/chain=ETHEREUM/` matches NO
objects on any sampled date; `venue=SUSHISWAP/chain=ARBITRUM/` (under a `pipeline_mode=` prefix) DOES have real objects.
`SUSHISWAP` + `ARBITRUM` is exactly how the registry's own already-canonical `SUSHISWAP-ARBITRUM` venue
(`unified_api_contracts.registry.defi_venues.ALL_DEFI_VENUES`) is represented in this manifest (venue/chain stored as
separate columns, joined at display time) — **this is real, live, actively-growing canonical data, not a legacy
artifact.** The "classic-`SUSHISWAP`-vs-`SUSHISWAP_V3` on Ethereum" ambiguity this todo was written to resolve has NO
corresponding population anywhere in the current bucket — the premise the 2026-08-08 ruling was made against does not
hold; there is nothing on Ethereum to migrate.

**A separate, more dangerous ambiguity turned up while checking the sibling bare `venue=SUSHISWAP_V3` population**
(2,273,083 rows, 1,325,155 `captured`, spanning `chain ∈ {ETHEREUM, BASE, AVALANCHE, ARBITRUM}`). The ETHEREUM/BASE/
AVALANCHE chains all match already-registered `SUSHISWAP_V3-{CHAIN}` venues (consistent, not a defect) — but
**`chain=ARBITRUM` (701,982 rows, `captured` through 2026-08-06 — actively growing) has NO registered
`SUSHISWAP_V3-ARBITRUM` venue in `ALL_DEFI_VENUES` at all.** Confirmed via
`instruments-service/instruments_service/reference_data/adapters/defi/_dex_factory_registry.py` (lines 106-140, sourced
from Etherscan/Arbiscan/DefiLlama contract name-tags): SushiSwap V2 and V3 have **genuinely different,
independently-sourced factory addresses on Arbitrum** (`0xc35DADB6...bc74C4` for V2 vs `0x1af415a1E...82231e` for V3) —
this is real, distinct on-chain DEX data, not a duplicate/mislabel of the V2 `SUSHISWAP-ARBITRUM` data found above. The
same file's own docstring (line 52-54) already flags this exact registry gap as a known, still-open item
(`issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`).

**Consequence for the dispatched todo**: neither literal reading of "fold bare SUSHISWAP into SUSHISWAP_V3" is safe to
execute as-is. Forcing bare `SUSHISWAP` (→ Ethereum-default alias target `SUSHISWAP_V3-ETHEREUM`) would mislabel 613,628
real Arbitrum-V2 rows as Ethereum data. Renaming bare `SUSHISWAP_V3`+`ARBITRUM` to any existing registered venue would
either collide with unrelated `SUSHISWAP_V3-{other chain}` data (if chain is dropped) or requires a canonical venue name
(`SUSHISWAP_V3-ARBITRUM`) that does not exist yet in UAC. No GCS object, manifest row, or code was touched — this is a
read-only scoping finding.

> **🟡 OPERATOR QUESTION QUEUED (not blocking other work — answer whenever convenient)**: the 2026-08-08 ruling above
> assumed a single Ethereum-only classic-vs-V3 ambiguity; live data shows the real picture is multi-chain and the
> literal "fold bare SUSHISWAP into SUSHISWAP_V3" instruction has no safe execution as worded. Options: **(a) close this
> todo as a verified no-op** — there is no bare-SUSHISWAP-Ethereum population to migrate; the only real open item is the
> separately-tracked `SUSHISWAP_V3-ARBITRUM` registry gap
> (`defi_sushiswap_uniswap_bare_version_factory_gap_ 2026_07_21.md`), which should absorb this todo's remaining scope
> instead of a fresh migration script; **(b) register `SUSHISWAP_V3-ARBITRUM` as a new canonical UAC venue** (it's real,
> distinct, actively-growing data per the factory- address evidence above) and THEN dispatch a proper venue-relabel
> migration for the 701,982-row population currently mislabeled bare; **(c) operator inspects further** before deciding.
> **Recommendation: (a)** — the original todo's premise doesn't hold, and (b)'s registry decision is exactly the open,
> already-tracked sibling issue's job, not a reason to duplicate scope here. This todo stays open pending that answer;
> not re-attempting the migration until then.

## Success criteria

1. ✅ `lst-rates` captured rows are credited in the DeFi could-exist / data-status view — closed 2026-07-26 (stale
   dedicated-bucket premise + capability-registry gap both already fixed elsewhere; the actual live residual, a
   venue-prefix-exclusion bug, found + fixed this pass).
2. ✅ `VAULT` resolved (already excluded, test-guarded) — closed 2026-07-26. `SUSHISWAP` classic-vs-V3 ambiguity
   **remains open** — genuinely undecided data-semantics call, explicitly out of scope for the todo that closed the rest
   of this criterion.

## Progress Log

- **2026-08-08 (slot 16)**: dispatched the `[SCRIPT] P2` migrate+purge todo. Its own first step (a fresh, filtered
  `read_availability_index` scoping read) surfaced that the premise doesn't hold: bare `venue=SUSHISWAP` is 100%
  `chain=ARBITRUM` (already-canonical `SUSHISWAP-ARBITRUM` data, not an Ethereum legacy artifact — zero
  bare-SUSHISWAP-Ethereum rows exist, cross-verified against GCS directly on 5 sampled dates). Found a separate, more
  consequential issue while checking the sibling bare `venue=SUSHISWAP_V3` population: 701,982 `ARBITRUM`-chain rows
  have no registered `SUSHISWAP_V3-ARBITRUM` canonical venue, and are confirmed (via the dex-factory-address registry)
  to be genuinely distinct SushiSwap V3 data, not a V2 duplicate. No GCS object, manifest row, or code touched —
  read-only scoping only. Queued an operator question (see Finding above) rather than force a migration that risks
  mislabeling/corrupting real, actively-growing multi-chain data; skipping this task back to the queue.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole residual is the SUSHISWAP classic-vs-V3 alias question,
  explicitly a genuinely undecided data-semantics call

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  further work done yet beyond what the parent's archived Progress Log already recorded.
- 2026-07-26 (slot-2) — both todos closed per the per-todo detail above. `deployment-api@f919c87` (venue-prefix-
  exclusion fix). `SUSHISWAP` classic-vs-V3 remains the one genuinely open item in this doc.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no content change (3 entries — the 2026-08-01 marker
  undercounted; list already carries the origin plan, the batch2 doc that scoped SUSHISWAP out, and the real
  `defi_venue_capabilities.py` registry source).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA, valid — re-read end to end; both P3
  todos remain closed with hard evidence, the sole open checkbox (SUSHISWAP classic-vs-V3 venue-attribution) is still an
  undecided data-semantics call per the doc's own text and `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s explicit
  out-of-scope carve-out. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: refreshed context_scope (3 entries) -- fixed a dead path (the
  `defi_venue_capabilities.py` entry was missing the `unified-api-contracts/` sibling-repo prefix, resolved to nothing).
- **na-corpus-digest-closeout 2026-08-08**: operator ruled the SUSHISWAP classic-vs-V3 question interactively — fold
  into `SUSHISWAP_V3`, AND migrate + purge the historical GCS objects/manifest rows to canonical naming (not a
  forward-only label default; explicitly the same standard as the factory-address ruling in
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — avoid two sources of truth, not just relabel going
  forward). Flipped `assigned_vm: NA` → `planning`; filed the migration+purge as a new `[SCRIPT] P2` todo.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — sole open item (bare-SUSHISWAP alias) remains an
  undecided data-semantics call; other 2 items closed 2026-07-26 with hard evidence.
