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

- [x] [BACKEND] P0. **Resolve the three `VenueCapability*`-named types in `unified-api-contracts`.** ✅ Resolved
      2026-08-16 — read `registry/venue_constants.py:593`, `registry/market_data_categories.py:2508`, and
      `internal/architecture_v2/schemas.py:122` in full, plus grep-verified every consumer of each. **Verdict: all
      three are genuinely orthogonal — no merge needed.**
      - **`VenueCapability`** (StrEnum, `venue_constants.py:593`) is a vocabulary of execution *operation kinds*
        (`spot_trade`, `perp_trade`, `lend`, `stake`, `sports_exchange`, ...), keyed into
        `VENUE_CAPABILITIES: dict[str, set[VenueCapability]]` and consumed by execution-facing code
        (`defi_pricing_fidelity.py`, `iv_surface_fidelity.py`, venue-capability tests). It answers "what operations
        can this venue execute."
      - **`VenueCapabilityRecord`** (dataclass, `market_data_categories.py:2508`) is a per-venue *market-data
        availability* record (route + per-data_type batch/live coverage) — a different domain entirely (data
        coverage, not execution capability). The author already disambiguated this in the class's own docstring
        ("Named `VenueCapabilityRecord` (not `VenueCapability`) to avoid colliding with the unrelated
        execution-capability `VenueCapability` StrEnum"), and its consumers (`market_data_categories.py` + 2 data-
        coverage test files) confirm the domain split holds in practice. It answers "what data does this venue have,
        and since when."
      - **`VenueCapabilityV2`** (Pydantic `BaseModel`, `internal/architecture_v2/schemas.py:122`) has **zero
        instantiations anywhere in the codebase** (grep-confirmed) — it is a schema-only stub for a v2
        strategy-architecture subsystem, not yet populated for any real venue. Its `supported_operations: list[str]`
        field is untyped and has zero producers/consumers outside its own declaration. It is orthogonal to
        `VenueCapability` **today** only because nothing has been built on it yet — not because the design avoided
        the overlap.
      - **Adjacent finding, not a duplicate of the three named types**: `VenueCapabilityV2.features:
        list[VenueFeature]` references a *fourth* enum (`VenueFeature`, `architecture_v2/enums.py:563`) whose
        vocabulary substantially overlaps `VenueCapability`'s under inconsistent casing/naming conventions —
        `FLASH_LOAN` (both, identical), `SPOT_TRADE`↔`SPOT_TRADING`, `PERP_TRADE`↔`PERPS_TRADING`,
        `OPTIONS_TRADE`↔`OPTIONS_TRADING`, `STAKE`↔`NATIVE_STAKING`, `PROVIDE_LIQUIDITY`↔`LP_PROVISION`. See new
        todo below — tracked separately since it's a fourth type, out of this todo's named scope, and not yet
        live (no `VenueCapabilityV2` instances exist to make it an active bug).
- [x] [DOC] P1. **Record the adapter-keys / instrument-type / data-type clean-SSOT verdict as contract-step-1
      evidence.** ✅ Done 2026-08-16 — added a Progress Log entry to
      `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md` citing this plan's Measured Baseline
      (2026-08-16 sweep) for the three clean verdicts (adapter keys, instrument types, data types), plus a pointer to
      this plan's todos 1 and 3 for the capability-record and error-code-map concerns.
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
- [x] [DOC] P1. **Do not duplicate the umbrella's own granularity-declaration OPERATOR item.** ✅ Done 2026-08-16 —
      added a cross-reference from the umbrella's `[OPERATOR] P0` "where does the granularity declaration live" item
      (`venue_readiness_and_registry_hardening_2026_08_16.md` line ~161) to this plan's resolved verdict: all three
      `VenueCapability*` types survive orthogonally (todo 1), and of the three, `VenueCapabilityRecord` is the
      closest-fit shape (already keyed per-venue × per-data_type) for the operator to evaluate — evidence only, the
      operator decision itself is untouched.
- [ ] [BACKEND] P2. **Adjacent finding: `VenueFeature` enum vocabulary overlaps `VenueCapability`'s.** Surfaced while
      resolving todo 1 — `VenueCapabilityV2.features: list[VenueFeature]`
      (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:563`) and `VenueCapability`
      (`registry/venue_constants.py:593`) encode overlapping operation concepts under inconsistent
      casing/naming: `FLASH_LOAN` (both, identical), `SPOT_TRADE`↔`SPOT_TRADING`, `PERP_TRADE`↔`PERPS_TRADING`,
      `OPTIONS_TRADE`↔`OPTIONS_TRADING`, `STAKE`↔`NATIVE_STAKING`, `PROVIDE_LIQUIDITY`↔`LP_PROVISION`. Not urgent —
      `VenueCapabilityV2` has zero live instances today, so this is not yet an active duplication, only a design gap
      that will become one the first time `VenueCapabilityV2` is populated. P2 (not P0/P1) because nothing consumes
      it yet. Done-when: either `VenueCapabilityV2.supported_operations`/`.features` is retyped to reuse
      `VenueCapability` directly (dropping `VenueFeature` as a separate vocabulary), or a stated reason `VenueFeature`
      must stay distinct (e.g. it mixes execution ops with account-structure features like `SUBACCOUNT`/`DARK_POOL`
      that `VenueCapability` doesn't cover) is recorded here — resolve before or at the point `VenueCapabilityV2`
      gets its first real instance, not before.

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

**2026-08-16 — todo 1 resolved.** Read all three `VenueCapability*` types in full plus every consumer of each
(grep-verified). Verdict: genuinely orthogonal, no merge — `VenueCapability` (execution operation-kind vocabulary),
`VenueCapabilityRecord` (per-venue market-data availability, already self-disambiguated by its own docstring), and
`VenueCapabilityV2` (zero live instances anywhere — unpopulated v2 schema stub). Surfaced one adjacent, out-of-scope
finding in the process: `VenueCapabilityV2.features: list[VenueFeature]` uses a fourth enum whose vocabulary
overlaps `VenueCapability`'s under inconsistent casing — tracked as a new P2 todo since it isn't yet an active bug
(nothing instantiates `VenueCapabilityV2` today). Also closed todo 4 (cross-referenced the umbrella's granularity
`[OPERATOR]` item to `VenueCapabilityRecord` as the closest-fit shape — evidence only, not a decision).

**2026-08-16 — todo (contract-step-1 evidence) resolved.** Added a Progress Log entry to the umbrella plan citing
this plan's Measured Baseline for the three clean verdicts (adapter keys, instrument types, data types) plus a
pointer to todos 1 and 3 here for the capability-record and error-code-map concerns — closes the umbrella's
contract-step-1 "Declared" citable-evidence requirement for these three concerns.

**2026-08-16 — error-code coverage audit (`[DATA] P0` todo) — RESEARCH COMPLETE, 5/5 venues; consolidation + code
changes still pending.** Per CLAIM≤MEASUREMENT, dispatched 5 parallel WebSearch/WebFetch research agents (one per
in-scope venue) against each venue's real official docs rather than recalling "documented codes" from training
memory. Baseline diffed against:
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/{cefi.py,defi.py}` via
`classify_venue_error()`/`VENUE_ERROR_MAP`. All 5 (Binance, Bybit, OKX, Deribit, Lido) now complete. Findings below
(full agent outputs are in this session's transcript, not yet re-verified/applied to code — capturing the substance
here so it survives compaction; **the remaining work is to build the required table + apply mapping changes**, not
more research):

- **Binance** (Spot REST/WS scope, 3 independent official sources cross-checked): mapped today = -1000, -1003,
  -1006, -1013, -1021, 429/500 (400/401 are not in Binance's own enumerated HTTP list — generic/inferred). Biggest
  gap: **-2010 NEW_ORDER_REJECTED** (generic order-placement rejection — the single most common live outcome,
  currently unmapped) → FAIL. Also worth adding: 418 (IP auto-ban after ignoring 429 — needs long/escalating
  backoff, not a normal retry) → RECONNECT; 409 (cancelReplace ambiguous partial success — needs order-state
  reconciliation, not blind retry/fail); -1007 TIMEOUT (exec status unknown, same hazard class as -1006) →
  RECONNECT/reconcile; -1002/-1022/-2014/-2015 (auth/signature/key failures) → FAIL; -2013 NO_SUCH_ORDER → FAIL;
  -1015/403 (distinct rate-limit surfaces from -1003/429) → RETRY-with-backoff. Explicitly could NOT verify several
  older third-party-cited margin codes (-2018→-2020, -2025, -2027→-2034, -2037/-2038, -2040/-2041) exist in the
  current official Spot `errors.md` — do not add on memory, they may be Margin-API-only or deprecated.
- **OKX**: mapped today = 50011, 50026, 51008, plus 50004 (labeled WS-close, but OKX's own docs define 50004 as a
  REST timeout — **50004 is a mismatch**; the code that actually matches our WS-close intent is **64008**, itself
  unmapped). Docs page is a JS SPA (WebFetch got fragments only) — cross-verified via ccxt's actively-maintained OKX
  adapter as a secondary source, high confidence on codes/messages, lower confidence on completeness of the very
  newest additions. Reachable gaps worth adding: 64008 (WS closing soon) → RECONNECT; 60015 (WS idle 30s
  disconnect) → RECONNECT; 50001 (matching engine upgrading, routine at funding settlement) → RETRY; 50013 (system
  busy, near-dup of mapped 50026) → RETRY; 60009 (WS login failed) → FAIL; 60014 (WS rate limit, WS analog of
  mapped 50011) → RETRY; 51009 (order blocked, account suspended) → FAIL; 51119/51127/51131/51736/51764
  (insufficient-balance variants distinct from mapped 51008) → FAIL; 51400/51401/51402 (cancel-target
  not-found/already-canceled/already-completed — reachable on cancel-fill races, should be treated as no-op
  success, not default-fail) → FAIL-as-noop; 51002 (instrument/index mismatch, config-bug signal) → FAIL+alert;
  50102 (timestamp >30s skew) → FAIL+alert.
- **Deribit** (docs.deribit.com/articles/errors, cross-checked vs ccxt): mapped today = 10028, 10040, 11044, 13009,
  13010, plus 400/401/429/500 (which aren't Deribit JSON-RPC codes at all — separate HTTP transport layer). **Two
  EXISTING mappings appear mislabeled, not just gaps** — higher-risk than an unmapped code since it drives wrong
  retry behavior silently: **13010** is labeled "token revoked→RECONNECT" but Deribit's own docs define it as
  `value_required` (generic bad-request/missing-param, not auth-related — reconnecting won't fix a malformed
  request; recommend FAIL). **11044** is labeled "not enough funds→FAIL" but is actually `not_open_order` (order-
  state error); the real not-enough-funds code, **10009**, is unmapped entirely. Recommend: reclassify 13010→FAIL,
  add 10009→FAIL as the real insufficient-funds code (leave 11044→FAIL, just fix its semantic label if downstream
  logic ever branches on description text). Other reachable gaps: 10004 order_not_found → FAIL; 10047
  matching_engine_queue_full → RETRY; 10066 too_many_concurrent_requests → RETRY; 11051/13028
  system_maintenance/temporarily_unavailable → RETRY-with-backoff; 13000-13008 credential errors → FAIL; 10041
  settlement_in_progress → RETRY-with-backoff; 11052 subscribe_error_unsubscribed → RECONNECT (WS-specific, our
  current 4-code set has zero WS-subscription coverage); 13888 timed_out → RETRY; -32602/-32600/-32601/-32700/-32000
  standard JSON-RPC protocol errors → FAIL (client-side malformation, retry won't help).
- **Lido**: real error surface is two unrelated layers — (a) off-chain REST APIs (docs.lido.fi), read-only,
  no documented Lido-specific error-code table beyond generic HTTP convention; (b) on-chain JSON-RPC + Lido
  contract custom errors (verified from `lidofinance/core` GitHub source: `WithdrawalQueueBase.sol`, `Lido.sol`).
  Mapped today = 400/401/429/500, -32603, `"WITHDRAWAL_NOT_FOUND"` (our internal label — **does not literally match
  any real Lido contract error name**; closest real analogs are `InvalidRequestId`/`RequestNotFoundOrNotFinalized`,
  both currently unmapped, worth noting as a naming caveat not a bug). Reachable gaps (assuming withdrawal
  status/claim checks are in scope, staking-submit is not): `InvalidRequestId`/`InvalidRequestIdRange` → FAIL;
  `RequestNotFoundOrNotFinalized` → FAIL (reachable on every pre-finalization claim-eligibility check);
  `RequestAlreadyClaimed` → FAIL; JSON-RPC -32000 (generic revert catch-all when a provider doesn't decode the
  custom error) → FAIL; -32005 (Infura/Alchemy rate-limit code, RPC analog of the already-mapped REST 429) →
  RETRY. If staking-submit (not just withdrawal) is ever in scope, also add `STAKE_LIMIT`→RETRY-with-backoff and
  `STAKING_PAUSED`/`ZERO_DEPOSIT`→FAIL. Oracle/finalizer-only and admin/governance-only contract errors are
  correctly out of reach for a normal client — not gaps.
- **Bybit** (V5 API, bybit-exchange.github.io/docs/v5/error, full fetch succeeded, ~700+ codes across 20
  categories): mapped today is entirely transport/session/auth-level (400, 401, 429, 10000, 10001, 10006, 10019,
  33004). **Genuine doc-level ambiguity found, not our bug**: Bybit itself overloads code **10003** (REST/UTA =
  "API key invalid/wrong domain" vs WS-OE = "too many sessions under same UID") and **10016** (REST/UTA = "server
  error" vs WS-OE = "internal error/service restarting") — any classifier keying purely off the integer without
  tagging REST-vs-WS origin will misclassify one of the two meanings; worth a namespace-tagged key, not just an
  added mapping. Reachable transport-level gaps worth adding: 403 → FAIL (or RETRY only if cause is IP-rate-limit,
  else FAIL — distinct from 429); 404 → FAIL (client-side routing bug, never transient); 10429 (WS analog of REST
  429) → RETRY; 10018 (IP rate limit, distinct surface from key-based 10006) → RETRY-with-backoff; 10002/-1
  (timestamp outside recv window / request expired) → FAIL-then-resync-clock; 10014 (duplicate
  request/idempotency collision on a reused clientOrderId) → FAIL; 10404 (WS op type not found — schema drift, a
  code bug not transient) → FAIL; 20003 (WS too-frequent-same-session, distinct from 10429/10006) → RETRY; 20006
  (WS duplicate reqId, client bug) → FAIL. Plus a handful of explicitly-transient business-layer codes worth
  special-casing despite the general rule below: 110079 (order processing, try again) → RETRY; 170007 (spot
  backend timeout) → RETRY; 170032 (spot network error) → RETRY; 170149/170150 (generic create/cancel failure) →
  RETRY-once-then-FAIL. Agent's explicit recommendation: the other ~600 business-rejection codes (110xxx
  order/position, 170xxx spot, 176xxx/182xxx margin, loan/earn/reward/RFQ/prediction) are deterministic per-request
  rejections (insufficient balance, invalid leverage, KYC blocks, etc.) that belong in order-response handling, not
  this transport retry/reconnect/fail map — blindly retrying them would either loop pointlessly or risk duplicate
  submission, so deliberately NOT itemized/added. Also flagged as a bigger structural gap than any single missing
  code: **if the classifier has no explicit default-fallback for an unrecognized numeric code, that should be
  added** (`FAIL` + log-unknown-code) so a genuinely novel documented code doesn't silently mis-route.

**Next step**: consolidate all 5 audits above into the required "venue → documented codes → mapped? y/n" table,
apply the recommended additions/relabels to `unified-api-contracts/.../errors/{cefi.py,defi.py}` (incl. the two
Deribit relabels — 13010→FAIL, add 10009 as real insufficient-funds — and the OKX 50004-vs-64008 fix), decide on a
namespace-tagged key for Bybit's 10003/10016 REST-vs-WS collision, ship code via `quickmerge.sh --agent --files
'unified_api_contracts/canonical/crosscutting/errors/cefi.py unified_api_contracts/canonical/crosscutting/errors/defi.py'`
scoped to the `unified-api-contracts` repo, then flip this plan's `[DATA] P0` error-code-coverage todo to `[x]`
with evidence (table + sha) and ship this doc via `safe-doc-push.sh`.
