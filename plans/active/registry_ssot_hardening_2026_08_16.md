---
doc_type: plan
title: Registry SSOT hardening — venue capability record, data/instrument types, adapter keys, error-code map
summary: >-
  W2 of the venue-readiness umbrella. Every venue fact should be declared once — capability record, data types,
  instrument types, adapter keys, error-code map — audited for per-service copies across all 7 umbrella repos. A
  same-pattern grep sweep (2026-08-16) found adapter keys, instrument types, and data types already single-SSOT with
  zero redefinitions anywhere, and error-code CLASSIFICATION already routes through classify_venue_error with zero
  local ERROR_CODE_MAP dicts — the actual open work is narrower than the umbrella assumed: a same-repo naming overlap
  on the capability-record concept, and unverified error-code COVERAGE completeness per venue.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [registry-ssot, venue-readiness, carve-out-prerequisite]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
  ]
created: 2026-08-16
source: operator-request-2026-08-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
effort: medium
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/02-data/canonical-cutover-register.md,
    unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors,
  ]
---

# Registry SSOT hardening

> **Parent**: [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
> (workstream W2). Same umbrella as [`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md) (W1).

## Why, in one paragraph

The umbrella's contract step 1 ("Declared") requires every venue fact to live in exactly one place — capability
record, data types, instrument types, adapter keys, error-code map — with per-service copies folded into the SSOT. A
2026-08-16 grep sweep across all 7 umbrella repos (`unified-api-contracts`, `unified-trading-library`,
`instruments-service`, `market-tick-data-service`, `features-service`, `strategy-service`, `execution-service`)
found most of this already true. State the measured baseline plainly rather than assuming the umbrella's "audit and
fold" framing applies uniformly — three of five concerns need no fold, one needs a same-repo naming resolution, one
needs a coverage audit (not a dedup).

## Measured baseline (2026-08-16 sweep)

| Concern | Definitions found | Verdict |
| --- | --- | --- |
| **Adapter keys** | Exactly one: `VENUE_TO_ADAPTER_KEY` dict, `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:78`. Every other hit across all 7 repos is import/usage, not redefinition. | **Clean — no fold needed.** |
| **Instrument types** | Zero `class InstrumentType` redefinitions outside UAC across all 7 repos. | **Clean — no fold needed.** |
| **Data types** | Zero `class DataType` redefinitions outside UAC across all 7 repos. | **Clean — no fold needed.** |
| **Error-code map (classification)** | Zero local `ERROR_CODE_MAP`/`RESPONSE_CODE_MAP`/`_ERROR_CODE_MAP` dict literals anywhere outside UAC; `execution-service/execution_service/trade_execution/error_map.py` imports and aliases `classify_venue_error` rather than reimplementing it. | **Implementation clean.** Coverage (does every venue's actual documented code map to a classified outcome?) is **unverified** — see todo 3. |
| **Capability record** | THREE distinctly-named types, all inside `unified-api-contracts` (not cross-service duplication): `VenueCapability` (StrEnum, `registry/venue_constants.py:593`), `VenueCapabilityRecord` (`registry/market_data_categories.py:2508`), `VenueCapabilityV2` (BaseModel, `internal/architecture_v2/schemas.py:122`). | **Needs a same-repo orthogonality check** — see todo 1. Not a per-service-copy problem; a same-repo naming-overlap one. |

## Todos

- [ ] [BACKEND] P0. **Resolve the three `VenueCapability*`-named types in `unified-api-contracts`.** Read
      `registry/venue_constants.py:593` (`VenueCapability` StrEnum), `registry/market_data_categories.py:2508`
      (`VenueCapabilityRecord`), and `internal/architecture_v2/schemas.py:122` (`VenueCapabilityV2` BaseModel) in full;
      determine whether each is genuinely orthogonal (e.g. an enum of capability *kinds* vs. a data *record* vs. a v2
      *schema* for a different subsystem) or a near-duplicate per the umbrella's canonical-orthogonality ruling. If
      near-duplicate: propose the superset/subset merge, follow
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` (every consumer migrates in the SAME
      change) and record the cutover in `/codex/02-data/canonical-cutover-register.md`; the actual merge/purge stays
      `[OPERATOR]`-gated per that SSOT. If genuinely orthogonal: state why in this plan (one paragraph per type) so
      the next reader doesn't re-ask. Done-when: this plan states a resolved verdict for all three, with either a
      merge proposal or a stated orthogonality justification for each pair.
- [ ] [DOC] P1. **Record the adapter-keys / instrument-type / data-type clean-SSOT verdict as contract-step-1
      evidence.** The umbrella's step 1 ("Declared... one declaration, no per-service copies") needs a citable
      evidence line, not just this plan's own table. Add a one-line pointer from
      `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`'s contract table (or its Progress Log) to
      this plan's Measured Baseline section for these three concerns, so a future venue-readiness check doesn't
      re-run the same sweep. Done-when: the umbrella plan's Progress Log cites this plan + date for the three clean
      verdicts.
- [ ] [DATA] P0. **Audit error-code COVERAGE completeness per in-scope venue** (distinct from the classification
      *implementation*, already confirmed clean above). For each venue currently in the carve-out's contracted scope
      (Bybit, Deribit, Binance, OKX, Lido — per
      `/plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md`'s narrowed scope) plus any other venue
      already `LIVE-READY` or `PAPER-READY`: enumerate that venue's actual documented API response/error codes from
      its own docs, and confirm each maps to a classified outcome via `classify_venue_error` /
      `unified_api_contracts/canonical/crosscutting/errors/`. Report gaps — a code with no classified mapping is a
      real finding, not a style nitpick (silent unclassified-default fallback was already flagged clean at 0/2 in
      execution-service's QG STEP 5.104, but that measures *classifier dispatch*, not *documented-code coverage*).
      Done-when: a table (venue → documented codes → mapped? y/n) exists for all in-scope venues, with every "n"
      resolved to either a new mapping or an explicit declared-unmapped-because-unreachable note.
- [ ] [DOC] P1. **Do not duplicate the umbrella's own granularity-declaration OPERATOR item.** The umbrella
      (`venue_readiness_and_registry_hardening_2026_08_16.md` line ~161) has its own open `[OPERATOR] P0` on "where
      does the granularity declaration live" — likely an extension of whichever capability record survives todo 1
      above. Once todo 1 resolves, add a one-line cross-reference from that operator item to this plan's resolved
      capability-record shape, so the operator answering it sees the current shape rather than a stale one. Done when
      the cross-reference exists (post-todo-1); do not attempt to answer the operator item itself here.

## Definition of done

- [ ] [DOC] P0. **Contract step 1 ("Declared") is evidence-backed for all five concerns** in the venue-readiness
      umbrella — either "already clean, verified `<date>`" or "folded, `<repo>@<sha>`" for each.

## Progress Log

**2026-08-16 — authored.** Forked from the umbrella's W2 item
(`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md` line ~273, "Depends on nothing; can start
immediately"). Grep-swept all 7 umbrella repos for actual redefinitions (not just imports/usage) of
`VENUE_TO_ADAPTER_KEY`, `VenueCapability*`, `ERROR_CODE_MAP`-shaped dicts, `InstrumentType`/`DataType` classes —
found 4 of 5 concerns already single-SSOT with zero cross-service duplication, narrowing the plan's real scope from
"audit and fold" to "verify+document three, resolve one same-repo naming overlap, audit one coverage gap."
