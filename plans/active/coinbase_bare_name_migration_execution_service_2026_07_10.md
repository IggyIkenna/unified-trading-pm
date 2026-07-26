---
doc_type: plan
title: COINBASE bare-name execution-service caller migration (follow-on)
summary:
  Follow-on to the UAC + data-plane bare-COINBASE removal — migrates the 12 execution-service callers that were scoped
  OUT of the parent plan, and resolves whether the bare-venue backward-compat resolver in registry.py should be kept
  (Nautilus-driven) or removed.
status: complete
nature: design
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cefi, cross-cutting], a
  # genuine mistag: this is a COINBASE (cefi venue)-specific execution-service caller migration, not cross-AG

stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [venue-canonicalisation, cefi, execution-service, migration, follow-on]
related:
  [/plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md, issues/wsfeedconnector_phase35_gap_2026_07_06.md]
created: 2026-07-10
last_updated: 2026-07-10
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [coinbase_bare_name_migration_2026_07_06]
source: [coinbase_bare_name_migration_2026_07_06.md#2d, coinbase_bare_name_migration_2026_07_06.md#S7]
assigned_role: backend_engineer
drift_direction: advance-code
---

# COINBASE bare-name execution-service caller migration (follow-on)

> **STATUS: draft.** Filed per `coinbase_bare_name_migration_2026_07_06.md` Step S7 ("File a follow-on task for the bare
> COINBASE removal after the 25-caller migration plan is drafted and lands. Owner: `assigned_role: backend-engineer`.
> Depends on THIS plan."). `assigned_vm: NA` / LOCAL track (default per CLAUDE.md "ask the operator before creating an
> AO plan" — this plan defaults to the human/LOCAL track; the operator can flip `assigned_vm: planning` +
> `status: active` if they want the fleet to dispatch it). **Do NOT execute before
> `coinbase_bare_name_migration_2026_07_06.md` S1-S6 have landed** (UAC must drop bare `COINBASE` from
> `VENUES_BY_ASSET_GROUP["cefi"]` first — see `depends_on`).

## 1. Context

`coinbase_bare_name_migration_2026_07_06.md` (S3) removes bare `"COINBASE"` from UAC's cefi venue registries and re-keys
44 UAC + downstream data-plane callers to `COINBASE-SPOT`. That plan explicitly scoped OUT execution-service (§2d, 12
bare-COINBASE call sites across 12 files) — execution-service is a different craft (`backend-engineer`, not
`data_engineering`) and touches order-routing / Nautilus integration, which is out-of-bounds for a data_engineering
worker per the craft-scoping rule in `agents/RULES.md`.

This plan enumerates those 12 call sites (carried over verbatim from the parent plan's §2d) and adds the one open
decision the parent plan flagged: **should `execution_service/instruments/registry.py`'s bare-venue backward-compat
resolver be kept or removed?**

## 2. Open decision — the `registry.py` backward-compat resolver

`execution_service/instruments/registry.py:178-179, 207-208, 310` carries a bare-venue → `COINBASE-SPOT` resolver
(`"COINBASE" → "COINBASE-SPOT"`) plus a Nautilus venue map. Two options:

- **KEEP** — treat it as a resilience shim for external callers (order-routing clients, older integrations) that may
  still pass bare `"COINBASE"` at the API boundary. Nautilus itself uses bare `COINBASE` as its venue name (see
  `execution_service/instruments/utils.py:239` `normalize_venue_for_nautilus` and
  `execution_service/utils/nautilus_compatibility.py:17` `NAUTILUS_SUPPORTED_VENUES`), so a _Nautilus-facing_ resolver
  has a legitimate, permanent reason to keep the bare form on that side of the boundary — this is NOT the same
  bare-COINBASE as the UAC cefi-venue key.
- **REMOVE** — once every internal caller has migrated to `COINBASE-SPOT` (this plan's S1-S3 below), the backward-compat
  branch in `registry.py:178-179` is dead code for the UAC-facing side (only the Nautilus-boundary mapping in
  `utils.py`/`nautilus_compatibility.py` remains necessary).

**Recommendation (non-binding — the executing agent should re-verify against the codebase at execution time, since S1-S6
of the parent plan may have shipped additional context by then):** KEEP the Nautilus-boundary mapping (`utils.py:239`,
`nautilus_compatibility.py:17`, `trade_execution/factory.py:104`, `engine/backtest/preflight.py:90`) — it documents
Nautilus's own bare-venue convention, not UAC drift. REMOVE the `registry.py:178-179` UAC-facing backward-compat branch
only after grepping execution-service's actual external callers (order-routing clients, API request bodies) for any that
still pass bare `"COINBASE"` — if none exist post-migration, the branch is dead and its removal is a straightforward
cleanup (S1 below covers the audit + decision).

## 3. Call sites (carried over from `coinbase_bare_name_migration_2026_07_06.md` §2d)

| File                                                          | Line(s)                | Context                                                                                    | Migration                                                                                                          |
| ------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `execution_service/instruments/registry.py`                   | 178-179, 207-208, 310  | bare-venue backward-compat resolver (`"COINBASE" → "COINBASE-SPOT"`) + Nautilus map        | **DECISION** — see §2. KEEP the resolver OR migrate + delete once external callers are verified clean.             |
| `execution_service/instruments/utils.py`                      | 239                    | `normalize_venue_for_nautilus` — coerces bare/qualified → NautilusTrader's bare `COINBASE` | **KEEP** — Nautilus itself uses bare `COINBASE` as its venue name; intentional.                                    |
| `execution_service/utils/nautilus_compatibility.py`           | 17                     | `NAUTILUS_SUPPORTED_VENUES` frozenset includes `"COINBASE"`                                | **KEEP** — Nautilus support catalogue.                                                                             |
| `execution_service/services/execution_cost_estimator.py`      | 32                     | `_VENUE_FEES_BPS["COINBASE"]`                                                              | **RE-KEY** to `COINBASE-SPOT` (fee schedule per canonical venue) OR keep as a base fallback — audit callers first. |
| `execution_service/trade_execution/factory.py`                | 104                    | `venue_map["coinbase"] = Venue.COINBASE` — Nautilus routing                                | **KEEP** — Nautilus context.                                                                                       |
| `execution_service/algo_library/algorithms/sor.py`            | 27, 29, 34, 153, 169   | SOR algorithm example / cost snapshot / mock venue keys                                    | **RE-KEY** the cost-snapshot dict to `COINBASE-SPOT`; **KEEP** docstring examples (cosmetic).                      |
| `execution_service/custody/pre_trade_pinger.py`               | 15                     | docstring comment                                                                          | **KEEP** or update as documentation.                                                                               |
| `execution_service/engine/backtest/preflight.py`              | 90                     | Nautilus support message                                                                   | **KEEP** — Nautilus context.                                                                                       |
| `execution_service/engine/handlers/trade_handler.py`          | (grep at execute time) | possibly a lookup                                                                          | **AUDIT + RE-KEY** if a lookup.                                                                                    |
| `execution_service/results/serializer.py`                     | (grep at execute time) | possibly a lookup                                                                          | **AUDIT + RE-KEY** if a lookup.                                                                                    |
| `execution_service/trade_execution/adapters/coinbase_ccxt.py` | (grep at execute time) | adapter class                                                                              | **KEEP** file (bare-word CCXT context).                                                                            |
| `execution_service/trade_execution/venue_mapping.py`          | (grep at execute time) | execution-service local venue map                                                          | **AUDIT + RE-KEY**.                                                                                                |
| `configs/expected_start_dates.yaml`                           | (grep at execute time) | YAML config                                                                                | **RE-KEY**.                                                                                                        |

## 4. Sequenced landings

### Step S1 — the `registry.py` decision + audit

- [x] ✅ [BACKEND] P2. Grep execution-service's external-facing surfaces (API route handlers, order-routing request
      schemas) for any caller still passing bare `"COINBASE"` post the parent plan's S1-S6 landing. If none found,
      delete the `registry.py:178-179` UAC-facing backward-compat branch (keep the Nautilus-boundary map at
      `utils.py:239` / `nautilus_compatibility.py:17` / `factory.py:104` untouched — see §2). If any external caller
      still sends bare `"COINBASE"`, KEEP the resolver and document why in a code comment citing this plan. **Gate:**
      `bash scripts/quality-gates.sh` green; decision documented in the Progress Log below with the grep evidence. —
      **DONE (slot-3, 2026-07-26): `execution-service@1267290`, see Progress Log below.**

### Step S2 — re-key the internal lookups

- [x] ✅ [BACKEND] P2. `execution_service/services/execution_cost_estimator.py:32`,
      `execution_service/algo_library/algorithms/sor.py` (cost-snapshot dict only, lines 27/29/34/153/169),
      `execution_service/trade_execution/venue_mapping.py`, `configs/expected_start_dates.yaml`: re-key bare
      `"COINBASE"` → `"COINBASE-SPOT"` per §3. Leave every Nautilus-boundary reference (`utils.py:239`,
      `nautilus_compatibility.py:17`, `factory.py:104`, `engine/backtest/preflight.py:90`,
      `trade_execution/adapters/coinbase_ccxt.py`) untouched. **Gate:** QG green; no runtime string-lookup misses on
      `COINBASE-SPOT`. — **DONE, with one deviation (slot-3, 2026-07-26): `trade_execution/venue_mapping.py` was NOT
      re-keyed** — reading the file confirmed it is itself a full bidirectional Nautilus adapter boundary module (its
      own docstring: "NautilusTrader uses bare venue names... this module provides the mapping layer at the adapter
      boundary"), the SAME class as the already-KEEP-listed files, not UAC-facing drift. Re-keying it would have broken
      the Nautilus integration it exists to serve. See Progress Log for full reasoning.

### Step S3 — audit the remaining grep-only entries

- [x] ✅ [BACKEND] P3. `execution_service/engine/handlers/trade_handler.py`, `execution_service/results/serializer.py`:
      grep for bare `COINBASE` usage; re-key if it's a lookup, leave if it's a label/comment. **Gate:** QG green; audit
      result documented in the Progress Log. — **DONE (slot-3, 2026-07-26): both files already fully `COINBASE-SPOT` — 0
      bare hits, no change needed.**

## 5. Full-execution criterion

- ✅ Every row in §3 marked **RE-KEY** or **DECISION** has landed (KEEP rows are verified, not modified).
- ✅ `grep -rn '"COINBASE"' execution-service/execution_service/ --include='*.py'` (excluding the deliberately-kept
  Nautilus-boundary files) returns 0 hits.
- ✅ execution-service `bash scripts/quality-gates.sh` green on the final commit.

## 6. Codex SSOTs consulted

- `coinbase_bare_name_migration_2026_07_06.md` §2d, §3, §7 (the parent plan this follows on from).
- `/codex/04-architecture/defi-execution-overview.md` (execution-service craft boundary — read on execution, not at
  filing time, since this data_engineering worker does not touch execution-service code).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-26** — S1-S3 executed and landed by slot-3 (backend_engineer), dispatched via
  `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s item -001. `execution-service@1267290`.

  **S1 registry.py decision — REMOVE (external callers verified clean):**

  ```
  $ grep -rn '"COINBASE"' execution_service/api/ --include='*.py'
  (0 hits)
  ```

  No API route handler or order-routing request schema (`api/manual_schemas.py`, `api/preview_schemas.py`) carries a
  bare `"COINBASE"` literal — both use free-form `venue: str` fields with no bare-COINBASE example/default. Deleted the
  UAC-facing backward-compat branches in BOTH `registry.py::convert_to_gcs_format` (178-179) AND
  `convert_to_nautilus_format`'s `venue_lookup_map` (207-208 — same backward-compat class, bundled into the same
  decision). Also found + removed `instruments/utils.py`'s `VENUE_MAP` bare `"COINBASE"` entry (line 28) — the SAME
  UAC-facing-resolver class as `registry.py`'s decision, not named in this plan's original table (a table gap, not a
  scope decision) but required for the §5 grep-0 criterion to actually pass.

  **Deviation from §3's table — `trade_execution/venue_mapping.py` KEPT, not re-keyed.** Reading the file (its own
  docstring: _"NautilusTrader uses bare venue names (e.g. 'BINANCE') internally, while UTS uses qualified VENUE-PRODUCT
  format... This module provides the mapping layer at the adapter boundary"_) confirmed it is a full bidirectional
  Nautilus adapter boundary module — the SAME class as `utils.py:239`/`nautilus_compatibility.py:17`, not UAC-facing
  drift. Re-keying its `NAUTILUS_TO_VENUE["COINBASE"]`/`VENUE_TO_NAUTILUS["COINBASE-SPOT"]` entries would have broken
  the Nautilus integration it exists to serve — Nautilus itself sends/expects bare `"COINBASE"` at this exact boundary.
  §3's table entry for this file was written at filing time without reading the code (per the plan's own "grep at
  execute time" caveat); this is the "re-verify against the codebase at execution time" judgment call §2's
  Recommendation anticipated.

  **S2 re-keys landed:** `execution_cost_estimator.py:32` (`_VENUE_FEES_BPS`), `sor.py` lines 153/169 (the two
  `Example:` docstring dicts inside `update_venue_prices`/`update_venue_liquidity` — the narrative prose at 27/29/34
  stays bare, per §3's own "docstring examples (cosmetic)" instruction), `configs/expected_start_dates.yaml` (4
  occurrences, all `COINBASE:` YAML keys under `instruments-service:` asset-group start-date tables).

  **S3 audit — already clean:** `trade_handler.py`/`serializer.py` grep for bare `COINBASE` returned 0 hits — both
  already fully `COINBASE-SPOT`, no change needed.

  **§5 full-execution criterion, final evidence:**

  ```
  $ grep -rn '"COINBASE"' execution_service/ --include='*.py'
  execution_service/trade_execution/venue_mapping.py:21:    "COINBASE-SPOT": "COINBASE",
  execution_service/trade_execution/venue_mapping.py:32:    "COINBASE": "COINBASE-SPOT",
  execution_service/instruments/utils.py:237:    elif venue_upper in ("COINBASE", "COINBASE-SPOT"):
  execution_service/instruments/utils.py:238:        return "COINBASE"
  execution_service/utils/nautilus_compatibility.py:17:        "COINBASE",
  execution_service/instruments/registry.py:39:    "COINBASE-SPOT": {"gcs_prefix": "COINBASE", "nautilus_code": "COINBASE", "spot_gcs_prefix": "COINBASE"},
  execution_service/instruments/registry.py:307:        "COINBASE-SPOT": "COINBASE",
  ```

  All 7 remaining hits are canonical-keyed (`"COINBASE-SPOT"` as the dict KEY) or genuine Nautilus-boundary conversions
  (`venue_mapping.py`, `normalize_venue_for_nautilus`, `nautilus_compatibility.py`) — zero bare-venue `"COINBASE"` used
  as an INPUT resolver key remain. 117 targeted tests pass (nautilus_compatibility, sor, execution_cost_estimator,
  algorithm_factory, routing_matrix, instruction_convert); `quality-gates.sh` green. Status flipped `complete`.

- **2026-07-10** — Plan filed by slot-8 (data_engineering) per `coinbase_bare_name_migration_2026_07_06.md` Step S7.
  Carried over the 12-file execution-service enumeration from that plan's §2d verbatim and added the `registry.py`
  backward-compat resolver decision (§2) the parent plan flagged as open. Filed as `status: draft`, `assigned_vm: NA`
  (LOCAL track — default per CLAUDE.md; the operator can flip to AO-dispatched later). Depends on the parent plan; do
  not execute before its S1-S6 land.
