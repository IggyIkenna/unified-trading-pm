---
doc_type: issue
title:
  "UAC↔IS DeFi adapter drift — 9 venues declared live with 0 producible instruments (IS quality gate RED, all shipping
  blocked)"
summary:
  uac@3f79489f declared METEORA/LIFINITY/PHOENIX (Solana DEX) + CHAINLINK×5/PYTH (oracles) as live, adapter-backed defi
  venues. MEASURED against live upstreams, only PYTH-SOLANA actually produces instruments (10). METEORA's API 404s,
  LIFINITY's origin is 522, PHOENIX's domain no longer resolves (NXDOMAIN — its own adapter docstring already declared
  the REST API dead 2026-05-15), and CHAINLINK has no IS adapter at all. The 5 IS drift-guard tests are correctly RED
  and block EVERY agent shipping in instruments-service. Registering the dead-upstream adapters would manufacture
  exactly the "expected-but-always-empty" honest-coverage pollution the IS defi builder explicitly forbids.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [drift-guard, honest-coverage, adapter-registry, defi, oracle, dead-upstream, data-correctness, ship-blocker]
related: [defi_consolidated_closeout_2026_07_18]
created: 2026-07-20
priority: P0
parent_epic: infrastructure_master
source: "Live upstream measurement + IS drift-guard triage, slot-1, 2026-07-20"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
assigned_vm:
resolved_by:
---

# UAC↔IS DeFi adapter drift — 9 venues declared live, 1 actually producible

## STATUS UPDATE 2026-07-20 ~15:30 — ship-blocker RESOLVED by T2; a coverage-honesty finding REMAINS

The **gate blocker is cleared**. The owning track landed the lockstep while this issue was being triaged:

| Repo | Commit     | What it did                                                                        |
| ---- | ---------- | ---------------------------------------------------------------------------------- |
| UAC  | `83f17c46` | CHAINLINK-\* → `phase="pipeline"` + **no** `VENUE_TO_ADAPTER_KEY` entry            |
| IS   | `793125ad` | wired meteora/lifinity/phoenix/pyth into `factory._ADAPTERS` + regenerated goldens |
| IS   | `6506b505` | added + registered `ChainlinkOracleReferenceDataAdapter`                           |

Measured at `uac@b6a1d83a` + `is@6506b505`: IS defi producer **93** == UAC defi denominator **93**, and
`{v: k for v, k in VENUE_TO_ADAPTER_KEY.items() if k != NO_ADAPTER_YET and k not in _ADAPTERS}` is now **empty**. All 5
drift guards pass. IS quality gate: **4711 passed / 1 failed**, and the single failure is
`test_expected_matches_golden[sports]` — an unrelated second lockstep (see below), not this issue.

### Correction to Recommendation A below — `NO_ADAPTER_YET` was the WRONG mechanism

Recommendation A (and this issue's original framing) proposed pointing the venues at the `NO_ADAPTER_YET` sentinel.
**That is not what the contract means by the sentinel, and the owning track independently rejected it in `83f17c46`.**
The sentinel's own registry in `tests/unit/test_venue_adapter_keys.py` scopes it to venues that are adapterless **by
design** (MTDS-owned market-data venues, source-as-venue artifacts, expand-only bare forms) and says in as many words
that it is _"never a shortcut for a missing adapter"_. It is also insufficient on its own:
`VENUES_BY_ASSET_GROUP["defi"]` is derived as `ALL_DEFI_VENUES` filtered by `DEFI_VENUE_PHASE == "live"`, so the
set-equality drift guard would still fail with a sentinel in place.

The correct mechanism — the one `83f17c46` used and the one `JUPITER-SOLANA` has always used — is
**`DEFI_VENUE_PHASE = "pipeline"` + omit the `VENUE_TO_ADAPTER_KEY` entry entirely**. Venue stays declared in
`ALL_DEFI_VENUES` (knowledge

- launch dates preserved), drops out of the live denominator, and no sentinel is spent.

### REMAINING FINDING (P1, data-correctness) — three live venues with measured-dead upstreams

T2 resolved the drift by **widening IS to match UAC** (registering the adapters) rather than narrowing UAC. For PYTH
that is correct — its upstream is healthy (measured 10 real instruments via Hermes, HTTP 200). For the other three it
re-creates the exact failure mode this issue was opened about. Measured at `uac@b6a1d83a`:

| Venue             | `DEFI_VENUE_PHASE` | in `expected_coverage` denominator | upstream (measured 2026-07-20)     |
| ----------------- | ------------------ | ---------------------------------- | ---------------------------------- |
| `METEORA-SOLANA`  | `live`             | **yes**                            | `app.meteora.ag/api/pools` → 404   |
| `LIFINITY-SOLANA` | `live`             | **yes**                            | `api.lifinity.io/pools` → 522      |
| `PHOENIX-SOLANA`  | `live`             | **yes**                            | `api.phoenix.trade` → NXDOMAIN     |
| `PYTH-SOLANA`     | `live`             | yes                                | Hermes 200 — **correct, leave it** |
| `CHAINLINK-*` ×5  | `pipeline`         | **yes** ← leak                     | adapter now exists (`6506b505`)    |

Two distinct problems:

1. **Three venues are `phase="live"` with a populated `expected_coverage` denominator and a permanently unattainable
   numerator** — manufactured coverage, which is precisely what `instruments_service/engine/orchestrator/defi.py`
   forbids in its own words ("they'd emit 0 rows and pollute honest-coverage as expected-but-always-empty"). A
   registered adapter class satisfies the _routing_ guard but says nothing about whether the upstream answers.
2. **`expected_coverage` is not phase-gated.** `get_expected_venues_in_scope("defi")` returns every venue with a
   non-empty list in `_DEFI` **without consulting `DEFI_VENUE_PHASE`**, so the 5 `CHAINLINK-<chain>` rows sit in the
   coverage denominator even though `83f17c46` correctly moved them to `phase="pipeline"`. Flipping a venue to
   `pipeline` therefore does **not** remove it from the honest-coverage denominator — a trap for anyone applying the
   `83f17c46` pattern. Either `_DEFI` rows must be removed in the same commit as the phase flip, or
   `get_expected_venues_in_scope` should intersect with the live set.

Suggested fix (T2 / slot-4's call): re-verify each upstream, and for any that is still dead either flip back to
`phase="pipeline"` **and** delete its `_DEFI` row, or keep it live with a `record_empty`/`empty_confirmed` path so the
numerator is honestly attainable. A ready-made narrowing patch (phase flips + `VENUE_TO_ADAPTER_KEY` removals + `_DEFI`
row removals, with the full evidence in comments) is preserved at
`scratchpad/uac-defi-narrowing-ANALYSIS-slot1-2026-07-20.patch` — **not applied**, since this is T2's lane.

## Blast radius (why this is P0)

`instruments-service`'s quality gate is RED at `instruments-service@367e382b` on 5 drift-guard tests. Because the commit
rule is "commit only from a `quality-gates.sh`-green tree", **every agent trying to ship anything in IS is blocked** —
including finished, verified, unrelated deliverables (the KRX `name`-stamp work is currently stranded in a working
tree).

The 5 RED guards:

| Test                                                    | File                                                  |
| ------------------------------------------------------- | ----------------------------------------------------- |
| `test_every_uac_adapter_key_resolves_to_a_class`        | `tests/unit/test_adapter_routing_uac_invariant.py`    |
| `test_defi_set_equals_uac_denominator_drift_guard`      | `tests/unit/test_orchestrator_helpers.py`             |
| `test_expected_matches_golden[defi]`                    | `tests/unit/scripts/test_expected_universe_golden.py` |
| `test_adapter_data_sources_covers_all_adapters`         | `tests/unit/test_factory_comprehensive.py`            |
| `test_rule11_per_ag_dedup_target_counts_byte_unchanged` | `tests/unit/test_pipeline_e2e_prediction.py`          |

These guards are working exactly as designed. **They must not be weakened, excluded, or baselined.**

## What UAC declared

`uac@3f79489f` ("feat(defi): canonicalize DeFi catalogue venues") added 9 venues to `ALL_DEFI_VENUES`,
`DEFI_VENUE_PHASE="live"`, `MTDS_DEFI_VENUES`, `VENUE_TO_ADAPTER_KEY`, `_DEFI_VENUE_PREFIXES`, capability declarations,
`expected_coverage`, and `PROTOCOL_LAUNCH_DATES`.

Measured drift at HEAD: IS defi producer = **89** venues, UAC defi denominator = **98**. The 9 UAC-only venues are
exactly the ones added by that commit. `VENUE_TO_ADAPTER_KEY` has 9 entries resolving to 5 adapter keys with no class in
`instruments_service.reference_data.factory._ADAPTERS`: `meteora`(1), `lifinity`(1), `phoenix`(1), `chainlink`(5),
`pyth`(1).

## The measurement (this is the load-bearing evidence)

The IS defi builder (`instruments_service/engine/orchestrator/defi.py`) states its own admission criterion explicitly —
a venue is enumerated **only** when its adapter has a populated registry and returns `>=1` real instrument "measured via
the factory". Venues whose adapters would return 0 are deliberately NOT enumerated because they would "emit 0 rows and
pollute honest-coverage as expected-but-always-empty".

Each adapter was instantiated and `get_instruments()` executed against its live upstream on 2026-07-20:

| Venue             | Adapter file       | Instruments | Upstream result                                                 |
| ----------------- | ------------------ | ----------- | --------------------------------------------------------------- |
| `PYTH-SOLANA`     | `pyth.py` ✅       | **10**      | Hermes `200` — real feeds                                       |
| `METEORA-SOLANA`  | `meteora.py`       | **0**       | `app.meteora.ag/api/pools` → **HTTP 404**                       |
| `LIFINITY-SOLANA` | `lifinity.py`      | **0**       | `api.lifinity.io/pools` → **HTTP 522** (Cloudflare origin down) |
| `PHOENIX-SOLANA`  | `phoenix.py`       | **0**       | `api.phoenix.trade` → **NXDOMAIN** (domain gone)                |
| `CHAINLINK-*` ×5  | _(does not exist)_ | **0**       | no adapter in IS at all                                         |

Independently reproduced with `curl` (identical results). **Control:** the Pyth Hermes endpoint returned `200` from the
same host in the same session, so these are genuine upstream failures, not sandbox egress restrictions.

Corroborating: `phoenix.py`'s own docstring already records "Phoenix REST API (api.phoenix.trade) is dead as of
2026-05-15" and documents a Jupiter-based replacement path that was never implemented.

## Determination

**Not mechanical.** Only `PYTH-SOLANA` is genuinely ready. The other 8 venue entries require real provider work:

- **METEORA** — protocol is alive (`amm-v2.meteora.ag` answers `400`, so the host is up) but the adapter's endpoint is
  stale. Needs an endpoint migration **plus** a response-shape remap. Tractable and verifiable, but real work.
- **LIFINITY** — origin returning 522. Needs an availability determination before anything else; may be transient, may
  be dead.
- **PHOENIX** — REST API gone entirely. Needs a rewrite onto the Jupiter `dexes=Phoenix` quote path already sketched in
  the adapter docstring.
- **CHAINLINK** — no IS adapter exists. Needs a curated per-chain aggregator-feed registry + RPC reads across 5 chains.
  **SSOT placement is an open decision**: the only existing copy of this registry is
  `market-tick-data-service/.../cli/handlers/_oracle_prices_constants.py` (383 lines, curated feed addresses per chain),
  and IS **cannot** import it (no service↔service deps). Copying it into IS would create a second, silently drifting
  copy of a correctness-critical registry. Correct home is almost certainly UAC.

**Stubbing any of these is refused.** An adapter that resolves the drift guard while returning nothing would flip these
venues to `phase="live"` with a populated `expected_coverage` denominator and zero attainable numerator — manufacturing
fake coverage and corrupting the honest-coverage model. That is strictly worse than a red gate, which is at least loud.

## Owning workstream

`plans/active/defi_consolidated_closeout_2026_07_18.md`, track **T2 CATALOGUE CODE** (slot-4, in flight). Its scope line
already names this work verbatim: _"CHAINLINK/PYTH + BUILD adapters (IS chainlink.py new; MTDS \_collect_meteora/
\_collect_lifinity new; register orphan pyth/meteora/lifinity/phoenix)"_, sequenced as _"ship UAC first → … → ship
IS+MTDS (drift-guard green)"_.

So the red gate is the **expected intermediate state of a deliberately sequenced cross-repo change** — UAC shipped
first, per plan, and the IS counterpart has not landed. What the plan did not anticipate is that 3 of the 4 "just
register the orphans" adapters have **dead upstreams**, so the IS half is materially larger than "register 4 classes",
and the gap window is blocking unrelated shipping across the whole repo.

## Recommended resolution (operator / T2 owner decision)

**A — UAC narrows to what is producible today [RECOMMENDED].** Keep `PYTH-SOLANA` live; move the other 8 venue entries
back to `phase="pipeline"` and point `VENUE_TO_ADAPTER_KEY` at the `NO_ADAPTER_YET` sentinel until each adapter
measurably produces instruments. This is not a guard weakening — `NO_ADAPTER_YET` is the contract's own designed
mechanism for "venue known, adapter not built yet", and the drift guard explicitly honours it. Unblocks the whole repo
in one small, honest UAC commit; each venue is re-promoted in lockstep as its adapter starts producing. Register `pyth`
in IS `_ADAPTERS` in the same lockstep.

**B — IS builds all 4 adapters before anything else ships.** Correct end-state, but days of work, and LIFINITY/PHOENIX
depend on upstream availability nobody controls. Leaves every agent blocked in IS for the duration.

**C — Revert `uac@3f79489f` wholesale.** Fastest unblock, but discards the genuinely-correct PYTH work and the
force-include/capability changes bundled into the same commit.

**Other:** operator may prefer a different split.

## Notes for whoever picks this up

- The 5 guard tests are correct. Do not edit them, add exclusions, or baseline the failures.
- Re-run the measurement before promoting any venue — upstream status is the admission criterion, not the presence of an
  adapter file. The harness pattern: instantiate the adapter class directly and `await get_instruments()`.
- `KRX_EQUITY_NAMES`-stamping work (unrelated) is stranded behind this gate; it is verified-good and ships the moment
  the tree is green.
