---
title: "Lending-indices handler bugs (AAVE-V3 ETH silent zero, Compound-V3 schema error, instruments-store metadata gap)"
created: 2026-05-07
author: harsh
source:
  - plans/active/defi_master_2026_05_07.plan.md § "Lending-indices VM run-quality bugs (discovered 2026-05-07 mid-run, VM stopped after diagnosis)"
  - VM `mtds-lending-indices-20260507-140418` (stopped 2026-05-07 ~15:30 IST after diagnosis)
  - gs://lending-indices-central-element-323112/_index/per_vm/mtds-lending-indices-20260507-140418.parquet
  - gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260507-140418/run.log
  - market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py (subgraph routing)
  - instruments-service (DeFi instrument-discovery launch-date floor handling)
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Lending-indices handler bugs (retro-filed per Findings Triage Discipline)

> **Severity**: P0 — Bug 1 silent-zeros AAVE V3 ETHEREUM, the most-relevant chain for `carry_staked_basis` (the
> May-23 lead archetype). Bug 2 produces incorrectly-shaped `empty_confirmed` rows (should be
> `attempted_failed`). Bug 3 underlies bugs 1+2.
> **Blast radius**: defi asset_group lending data; `carry_staked_basis` archetype P&L; `leveraged_funding_arb`
> cross-protocol leg if it touches Compound V3.
> **Suggested owner**: defi_master:Fork 1 (lending-indices handler) + instruments-service DeFi instrument
> discovery.

## Filing rationale

This issue doc is **retroactively filed** per the [Findings Triage Discipline (HARD RULE)](../../cursor-configs/CLAUDE.md)
shipped at PM@`c8e0e0f`. The bugs were discovered + fully documented in
[`defi_master_2026_05_07.plan.md`](../defi_master_2026_05_07.plan.md) earlier today (2026-05-07), but the new rule
requires **big findings to land in BOTH chat AND issues/ folder**, not just plan annotations. This doc points at
the canonical detail in `defi_master` and re-states the severity + blast-radius for the issues triage cycle.

## Summary

VM `mtds-lending-indices-20260507-140418` was launched 2026-05-07 14:04 IST and **stopped 2026-05-07 ~15:30 IST**
after spot-checking the per-VM shard revealed silent data-quality issues. Despite emitting 8,000+
`INSTRUMENT_PROCESSED` events + writing 4,459 manifest rows, only 4 of 8 (venue, chain) pairs were producing
captured rows; the rest were silently writing `empty_confirmed` for dates where data should exist.

### Per-(venue, chain) outcome from per-VM shard

| venue / chain          | captured | empty_confirmed | verdict                              |
| ---------------------- | -------- | --------------- | ------------------------------------ |
| AAVEV3 / ARBITRUM      | 269      | 74              | ✅ working                            |
| AAVEV3 / OPTIMISM      | 270      | 73              | ✅ working                            |
| AAVEV3 / POLYGON       | 272      | 71              | ✅ working                            |
| AAVEV3 / AVALANCHE     | 270      | 73              | ✅ working                            |
| AAVEV3 / **ETHEREUM**  | **0**    | **343**         | ❌ **silent zero — Bug 1**            |
| AAVEV3 / BASE          | 0        | 343             | ⚠️ likely correct (pre-launch in 2022) |
| AAVEV3 / LINEA         | 0        | 343             | ⚠️ likely correct (LINEA mainnet 2023) |
| AAVEV3 / BSC           | 0        | 343             | ⚠️ likely correct                     |
| COMPOUNDV3 / ETHEREUM  | 107      | —               | ✅ working                            |
| COMPOUNDV3 / ARB/BASE/OPT | 0     | 0 (skipped)     | ❌ **subgraph schema error — Bug 2**  |

## Bug 1 — AAVE V3 ETHEREUM silent zero (P0)

Run.log shows `instruments-store-defi parquet missing for aave_v3/ETHEREUM/2022-12-08; falling back to subgraph
discovery` then `Wrote 0 rows`. The instruments-store-defi metadata is missing for ETHEREUM (404s for early 2022
dates) AND the subgraph fallback is misconfigured for ETHEREUM specifically — other chains (Arbitrum, Optimism,
Polygon, Avalanche) have working subgraph fallbacks with the same code.

**Investigation target**: `market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py`
(or equivalent) + the per-chain subgraph endpoint config. Likely a chain→subgraph URL mapping bug or a missing
schema mapping for the Ethereum subgraph response shape.

## Bug 2 — COMPOUND V3 multi-chain Messari subgraph schema error (P0)

Run.log shows:

```
Subgraph query errors for Ff7ha9ELmpmg81D6nYxy4t8aGP26dPztqD1LDJNPqjLS:
  [{'message': "Type 'Query' has no field 'marketDailySnapshots'"}]
```

…for COMPOUND_V3 on ARBITRUM/BASE/OPTIMISM. The Messari subgraph schema has been updated upstream + the MTDS
GraphQL query is stale. The field is likely renamed (e.g. `marketHourlySnapshots` or `marketSnapshots`) or moved
into a different entity.

**Side effect — also a writegate violation**: VM records these as `empty_confirmed` per the writegate three-category
model (subgraph returned 0 rows, no exception) — but per writegate Phase 2.A spirit this should be
`attempted_failed` because the GraphQL error means we DIDN'T actually probe the data. This is a 3-category
empty-output decision-tree mis-routing: this is case C (downstream calc dropped all rows due to malformed source
fields → `record_failed(MalformedTickFieldError(...))`), not case A (source returned 0 rows).

## Bug 3 — `instruments-store-defi` metadata missing for early 2022 dates

Affects all (venue, chain) pairs equally for early 2022 dates. The fallback to subgraph discovery works for some
chains and not others (see Bugs 1+2). The deeper question is whether instruments-service's lookback covers early
DeFi protocol launch dates — `instruments-store-defi-{pid}/instrument_availability/by_date/day=2022-12-08/...`
returns 404 for AAVEV3/COMPOUNDV3/etc. across all chains.

**Investigation target**: `instruments-service` DeFi instrument-discovery script + its launch-date floor
handling.

## Verification recipe

Use this WITHIN 10-15 MIN of any backfill VM launch (per the durable rule from this incident — see memory entry
`feedback_verify_vm_data_quality_at_launch.md` and the CLAUDE.md "no fire-and-forget VM launches" reference
incident extension):

```bash
PID=central-element-323112
VM=mtds-lending-indices-{ts}  # the actual VM name
gcloud storage cp gs://lending-indices-${PID}/_index/per_vm/${VM}.parquet /tmp/per_vm.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('/tmp/per_vm.parquet')
print(f'Total rows: {len(df):,}')
m = df.groupby(['venue','chain','capture_status']).size().unstack(fill_value=0)
print(m)
silent_zeros = m[(m.get('captured', 0) == 0) & (m.get('empty_confirmed', 0) > 100)]
if len(silent_zeros) > 0:
    print(f'\\n⚠️ Silent-zero candidates (captured=0 but empty_confirmed>100):')
    print(silent_zeros)
"
gcloud storage cat gs://deployment-scripts-${PID}/vm-logs/${VM}/run.log | grep -E "Subgraph query error|metadata unavailable|Wrote 0 rows" | head -20
```

Trigger pattern: any (venue, chain) row with `captured=0` AND `empty_confirmed>100` is a silent-zero candidate.

## Recommended decision

Owner: defi_master Fork 1 (lending-indices handler) + instruments-service DeFi instrument discovery. Sequence:

1. Fix Bug 3 first (instruments-service launch-date floor) — unblocks the fallback path for all chains.
2. Fix Bug 1 (AAVE V3 Ethereum subgraph routing) — unblocks `carry_staked_basis` Ethereum leg.
3. Fix Bug 2 (Compound V3 Messari schema) — re-issue queries against current schema; route the GraphQL error
   through `record_failed(MalformedTickFieldError(...))` per writegate Phase 2.A rather than swallowing as
   empty_confirmed.
4. Re-launch the VM with `--apply-write` after fixes shipped + tarballs refreshed.

Detailed bug descriptions + per-(venue, chain) evidence + verification recipe live in
[`defi_master_2026_05_07.plan.md`](../defi_master_2026_05_07.plan.md) § "Lending-indices VM run-quality bugs"
(authoritative source — this issue doc is a triage-pointer, not the canonical detail).

---

## DONE-2026-05-08 — Tab 5 (lending-indices-bugfix-tab)

All three bugs resolved. Status: ✅ RESOLVED.

**Bug 3 — instruments-service launch-date floor handling**
- `instruments-service@1a90185` — `get_protocol_floor_date()` now consults UAC `PROTOCOL_LAUNCH_DATES` via
  `get_protocol_launch_date(chain, venue_prefix)` as the canonical SSOT first, then falls back to local
  `LENDING_PROTOCOL_DEPLOY_DATES` for protocols UAC does not yet track (spark, morpho, fluid, euler_v2, radiant,
  venus, benqi). AAVE V3 ETHEREUM floor corrected from 2023-01-27 (legacy fallback) to 2022-03-14 (mainnet
  deploy per UAC). Tests assert UAC-derived floors AND local-fallback path for non-UAC protocols.

**Bug 1 — AAVE V3 ETHEREUM silent zero**
- `market-tick-data-service@d2f365e` (Bugs 1+2 combined) — `_query_and_parse` cascade for `aave_v3` extended to
  native (`reserveParamsHistoryItems`) → Messari (`marketDailySnapshots`) so a Messari-shaped Aave V3 deployment
  still yields rows. AAVE V3 + Spark + Compound V3 now share the same cascade pattern.

**Bug 2 — Compound V3 multi-chain Messari schema error + record_empty mis-routing**
- `market-tick-data-service@d2f365e` — new `SubgraphSchemaError` exception raised by `_execute_subgraph_query`
  when the GraphQL response carries the schema-drift fingerprint (`has no field` / `Cannot query field`).
  `_query_and_parse` cascade catches the error per-variant and tries the next schema; if EVERY variant raises
  (no schema applied), the last error is re-raised. `_collect_protocol_chain` re-raises `SubgraphSchemaError`
  so `process()` routes to `record_failed` (writegate Phase 2.A: `attempted_failed` not `empty_confirmed`).
  Pre-fix the broad `except Exception: return 0` masked schema errors as legitimate empty.
- `market-tick-data-service@de9d5cf` — ruff format spacing follow-up.

**Verification**
- 7 instruments-service tests pass: `tests/unit/test_evm_creation_resolver.py::TestGetProtocolFloorDate` —
  asserts UAC SSOT precedence, fallback to local dict, generic 2020-01-01 floor.
- 13 MTDS tests pass: `tests/unit/test_lending_indices_handler.py` — original 3 + 10 new covering
  schema-drift detection (6 cases), AAVE V3 native→Messari cascade fallthrough, all-schemas-drift re-raises,
  all-schemas-empty returns empty df, schema-error propagation through `_collect_protocol_chain`.
- Per-file basedpyright + ruff clean on all my edited files. Workspace QG fails at IMPORT_PATTERNS gate (5
  scripts authored by `semver-rollout[bot]`) and at LINT on `tests/unit/test_databento_path_streaming.py`
  (Tab 7's untracked WIP) — both exempt under CLAUDE.md QG-failure exception 2026-05-07 → ~2026-05-09.

**Re-launch readiness**
- After tarball refresh (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI`)
  the lending-indices VM can be re-launched. Operator-owned step.
