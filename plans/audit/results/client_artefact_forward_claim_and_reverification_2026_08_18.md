---
doc_type: audit-result
title: Client artefact forward-claim basis check + re-verification of first-audit-trusted findings — second-pass audit 2026-08-18
summary: >-
  Two-part second-pass audit. Part (a): searched the full plans corpus for any committed basis for
  platform-external-api-walkthrough.html's "most venues and strategies on the current plan complete over the
  remainder of this year" claim — found none; recommendation is to cut it, per the operator's own stated
  instruction in the stub todo. Part (b): independently re-verified six lower-severity Elysium artefact findings
  the first-pass audit explicitly flagged as sub-agent-sourced and never independently re-checked. Four of six
  are CONFIRMED (targets-not-deltas, cross-client-transfer-impossible — via a different, real production code
  path than the first audit checked — archetype counts 60/32 exact match, and the attestations field claim,
  which is if anything understated relative to current code). Two are materially wrong: the AtomicInstruction
  "schema-level" framing overstates what the Pydantic schema itself guarantees (the real succeed-or-fail-together
  behavior lives in execution-service runtime code, not the schema), and — the most consequential finding —
  "capital budget enforced by construction" is not backed by any wired enforcement path in current code: neither
  a capital_budget_amount guard nor the per-slot TradingWalletConfig mechanism the artefact cites has a single
  production call site in execution-service or strategy-service. A separate, previously-unflagged inaccuracy was
  also found: the deep-dive's description of evidence_router.py (as exposing a per-instruction attestation trail
  queryable by date/venue) does not match what that router's single real endpoint does (incident-evidence
  capture, not attestation query).
status: pass
nature: record
audited_scope: >-
  platform-external-api-walkthrough.html's unsupported forward-looking claim (basis check against plans/active/ and
  plans/epics/), plus independent re-verification of six lower-severity Elysium artefact findings the 2026-08-18
  first-pass audit did not independently check (targets-not-deltas, atomic multi-leg, cross-client-transfer-
  impossible, attestation, archetype counts 60/32, capital budget enforcement).
date: 2026-08-18
auditor: >-
  1 general-purpose sub-agent (sonnet), dispatched as one of 5 parallel agents doing a second-pass audit of
  client-disclosure artefacts, read-only, SUB_AGENT_MANDATORY_RULES.md pasted at spawn.
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi]
stage: [strategy, execution, meta]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
  ]
created: 2026-08-18
tags: [client-disclosure, nick-ai, elysium, audit, forward-claim, re-verification]
---

# Client artefact forward-claim basis check + re-verification of first-audit-trusted findings — 2026-08-18

**Read-only audit. No HTML or plan file was edited.** This is a second-pass, independent verification session
(one of 5 parallel agents) — findings only, for the operator to review before anything reaches a client document.

---

## Part (a) — the forward claim in the platform guide's intro

### The exact quote

`unified-trading-pm/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`, §00 "How to
read this" → callout "Where this is in its life", lines 239-253:

> "Finishing this does not require reinventing design patterns or a long stretch of hypothetical architecture
> work. The patterns are settled and shipped; what remains is **commercially led** — we add venues because someone
> wants to trade them, not to fill a matrix. **We will not build for a market that does not exist.**
>
> So treat what follows as a starting point rather than a finished inventory. **Most of the venues and strategies
> on the current plan complete over the remainder of this year**, and nothing in the architecture stops a new
> venue being added — adding one is a declaration plus an adapter, not a redesign. That is the whole point of the
> normalisation described below."

### Search performed

Grepped, case-insensitively, for any dated commitment that could support "most venues and strategies... complete
over the remainder of this year":
- Patterns tried: `by end of year`, `by end of 2026`, `remainder of 2026`, `complete by december`, `Q4 2026`,
  `2026-12`, `roadmap for the rest of`, `committed to.*venues`, `venue.*roadmap`, `strategy.*roadmap`, `dated
  milestone`.
- Scope: all of `plans/active/*.md` (the full corpus, not just the two owning plans), all of `plans/epics/*.md`
  including `system_readiness_master.md` specifically, and the two owning plans
  (`nick_ai_platform_disclosure_artifact_2026_08_16.md`,
  `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`) plus
  `nick_ai_platform_readiness_remediation_2026_08_16.md`.

### Result

**Zero matches anywhere in the plans corpus.** The only two hits from the broad grep were both false positives on
generic index/dispatch-plan text (`plans/active/INDEX.md`, `defi_satellite_ao_dispatch_batch2_2026_07_26.md`) —
neither contains anything resembling a dated venue/strategy completion commitment; both were read and confirmed
irrelevant. `system_readiness_master.md` — the epic that would be the natural home for any real cross-cutting
roadmap commitment — has no hits at all. Neither owning plan states, implies, or points to a dated "most
venues/strategies complete by end of year" commitment anywhere in their text.

### Verdict

**No cited basis exists.** This confirms the stub P0 todo's own framing verbatim
(`plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md` line 380-382: "It came from operator framing
and has no cited basis in any plan"). I found nothing that basis-checks it, narrower or otherwise — there is no
partial version of this claim ("most venues" alone, or "most strategies" alone, or a specific dated subset) that
any plan supports either. The operator's own instruction in the stub is explicit that the remedy in this case is
to **cut** the claim, not soften it, and this search gives no reason to deviate from that: **recommend cutting
the sentence** "Most of the venues and strategies on the current plan complete over the remainder of this year,"
in full. The surrounding sentences (commercially-led buildout, "we will not build for a market that does not
exist," adding a venue is "a declaration plus an adapter, not a redesign") are architectural/policy statements
that stand on their own and don't depend on the cut sentence — nothing else in the paragraph needs to change.

---

## Part (b) — re-verification of six first-audit-trusted findings

The first-pass audit (`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`, lines 301-307)
listed these six as "sub-agent-sourced, not independently re-verified by the orchestrating session." Each was
independently re-checked against real code below, treated as unconfirmed going in.

| # | Item | First audit's trust | My verdict | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Targets-not-deltas | CONFIRMED clean | **CONFIRMED** | `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py`: `TradeInstruction.target_position_units`, `LendInstruction.target_supplied_amount`, `BorrowInstruction.target_debt_amount`, `StakeInstruction.target_staked_amount` — every position/exposure instruction carries only a `target_*` Decimal field; no delta/increment field exists anywhere in the schema. |
| 2 | Atomic multi-leg (schema-level) | CONFIRMED clean | **PARTIALLY WRONG** | See detail below — the Pydantic schema itself has no validators and enforces nothing; the "must succeed or fail together" property is a real, implemented execution-service runtime behavior, not a schema-level guarantee. |
| 3 | Cross-client-transfer-impossible | CONFIRMED clean | **CONFIRMED** (via a different code path than presumably checked) | `execution-service/execution_service/engine/modes/live/trigger.py` calls `isolation_policy.assert_client_allowed(client_id_str)` on every live instruction before queueing it, catching `CrossClientEventError` and dropping (not executing) the instruction on mismatch. This is real, production, non-test code — see detail below. |
| 4 | Attestation "softened correctly" | CONFIRMED clean (untested assumption) | **PARTIALLY WRONG** | The *field*-population claim is confirmed and, if anything, understated (see detail). But a separate, previously-unflagged inaccuracy was found in the deep-dive's description of `evidence_router.py`. |
| 5 | Archetype counts (60/32) | CONFIRMED clean | **CONFIRMED**, exactly | `StrategyArchetype` enum = 60 members (counted directly); `ARCHETYPE_ENGINE_REGISTRY` (`factory.py`) = 32 entries (counted directly). Both match the artefact's stat-row exactly. |
| 6 | Capital budget "enforced by construction" | Flagged by first audit as "worth a second look... narrower, more defensible" | **WRONG** | Neither of the two plausible enforcement mechanisms is wired into production code. See detail below — this is the most consequential finding in this report. |

### Detail — item 2: Atomic multi-leg

The walkthrough (`strategy-service-walkthrough.html` line 436) shows `AtomicInstruction` in a code listing with
the comment `# multiple legs that must succeed or fail together`. The deep-dive's fuller prose (lines 400-404)
says: "with a declared leader, a deadline on how long the position may sit unhedged, and a compensation policy if
a leg fails... it is handled at the contract level rather than in strategy code."

Checked the real schema — `AtomicLeg`/`AtomicInstruction` in
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py` lines 345-365 — for any
`@field_validator`/`@model_validator` enforcing atomicity or cross-field consistency (e.g. `leader_leg` must
reference a valid `leg_index`, `compensation_policy` required for a given `execution_mode`). **Found none** — the
class is a passive data bag: `legs: list[AtomicLeg]`, `execution_mode: AtomicExecutionMode`,
`leader_leg: int | None`, `hedge_deadline_ms: int | None`, `compensation_policy: CompensationPolicy | None`,
`max_total_slippage_bps: int | None`. The type system enforces nothing about atomicity.

The real "succeed or fail together" behavior is implemented downstream, in execution-service:
`execution-service/execution_service/v2/atomic_leg_executor.py` and
`execution-service/execution_service/algo_library/leveraged_leg_controller.py` both reference
`compensation_policy`/`leader_leg`. **So the substantive claim is true** — this is a real, implemented mechanism,
not vaporware — but it is an execution-service **runtime** guarantee, not a **schema-level** one. The deep-dive's
own phrasing ("handled at the contract level rather than in strategy code") is defensible under a charitable
reading — it correctly locates the responsibility as "not strategy code's problem" without claiming the type
system itself performs the guarantee. The walkthrough's terse in-listing comment is looser and, read literally
next to a Pydantic class definition, could mislead a technical reader into thinking the schema itself enforces
succeed-or-fail-together. **Recommend**: if precision matters here, move or reword the walkthrough's comment to
say the *execution layer* enforces it using these fields, matching the deep-dive's more careful phrasing.

### Detail — item 3: Cross-client-transfer-impossible

The first audit's own §11 finding (line 285 of the first-pass report) noted `TransferCoordinator` — the class
whose `validate_intent()` raises `CrossClientTransferForbiddenError` — **is never instantiated in production
code**. That is still true (I did not find a new instantiation site). This could look like it undermines the
artefact's claim. It does not, because the artefact's actual claim rests on a *different*, independently real
mechanism: **process-level isolation**, not the (unused) `TransferCoordinator` class.

`execution-service/execution_service/isolation_policy.py` implements `assert_client_allowed()`, gated on
`runtime-topology.yaml`'s `isolation_policies.execution-service.default = ISOLATED` and a per-process `CLIENT_ID`
env var (injected by deployment-api's runtime_profile fan-out — i.e., one execution-service process per client).
This function has exactly three non-test call sites, and one of them is a real, live production entry point:
`execution-service/execution_service/engine/modes/live/trigger.py` lines 26-43 — every live instruction is
checked via `assert_client_allowed(client_id_str)` before being queued; on a `CrossClientEventError` the
instruction is logged as `CROSS_CLIENT_INSTRUCTION_REJECTED` and **dropped, not executed**.

This matches the artefact's exact wording (`platform-external-api-walkthrough.html` lines 965-971: "the code
raises rather than executing a cross-client movement"; `strategy-service-walkthrough.html` lines 849-855: "Each
client also runs in its own isolated process — so a cross-client transfer is not merely rejected, it has no path
to be expressed") — the real enforcement is the process-boundary (one `CLIENT_ID`-bound execution-service process
per client) plus this live-path assertion, not the specific `TransferCoordinator` class the first audit centered
its scrutiny on. **CONFIRMED**, on firmer ground than the first audit's own (narrower) check found.

### Detail — item 4: Attestation

The Oct-11 delivery plan (`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`, its own claims
audit) had flagged, as of that date: "'Attestation on every instruction' — **WAS WRONG** — `attestations=`
populated only in MEV modules, not the carry archetypes" (line 113), and recorded the deliberate softening from
"compliance attestation on every instruction" to "the attestation field on every instruction" (lines 216-217),
with an open P1 todo (still `- [ ]`) to decide whether to expand real population.

**Current code is well past that snapshot.** Grepping `attestations=` (non-test) across strategy-service today
shows real population in `vol_trading/*` (14+ files), `carry_and_yield/*` (7 files), `defi_lp/*` (3 files),
`market_making/*` (7 files), `rules_directional/*` (3 files), `ml_directional/*` (2 files),
`arbitrage_structural/*` (5 files), `stat_arb_pairs/*` (2 files), plus the original `mev/*` (3 files) — dozens of
archetype implementations across essentially every family, not "only the MEV modules." So the softened phrasing
("the attestation field on every instruction," rather than an unqualified "compliance attestation on every
instruction") is **CONFIRMED accurate, and now conservative relative to reality** — the field is populated far
more broadly than it was when the softening was written.

**A separate, previously-unflagged inaccuracy**, however: `strategy-service-deep-dive.html` lines 813-815 singles
out `evidence_router` for a "due-diligence conversation": "it exposes the attestation trail, which is how a
decision is evidenced after the fact rather than reconstructed from logs." I read the real file —
`strategy-service/strategy_service/api/evidence_router.py`, 64 lines total, exactly one route:
`POST /evidence/{incident_key}`. Per its own docstring, it is "called by `alerting-service` `EvidenceCollector` at
`AUDIT_REPORT_GENERATED` state transition" and snapshots the position-monitor's `safe_read_only` flag/reason to
GCS as **incident** evidence. It has nothing to do with querying an individual instruction's `attestations` dict,
and there is no filter by date, venue, or instruction anywhere in it. I also checked every other strategy-service
API router (`registry_router.py`, `operational_mode_router.py`, `restriction_profile_router.py`) and found no
route anywhere that queries instructions by attestation/date/venue. The related, stronger claim in
`platform-architecture.html` (lines 1801-1803) — "Every instruction carries its own attestations, so 'why did it
do that, on 14 October, on OKX' is a query rather than an investigation" — implies exactly this kind of query
surface, and I could not find it anywhere in the codebase.

**Verdict for item 4: PARTIALLY WRONG.** The attestations-field claim itself is fine (confirmed, understated even).
But `evidence_router`'s actual function (incident-evidence capture) is materially different from what the deep-dive
describes it as doing (attestation-trail query), and the "query, not investigation" framing in the platform
architecture doc has no backing implementation found. **Recommend**: either build the query surface the copy
implies, or correct both descriptions to describe what `evidence_router` and the attestations field actually do
today (attestations are captured per-instruction in the tape; there is no dedicated cross-instruction query API
yet).

### Detail — item 5: Archetype counts (60/32)

Counted directly rather than trusting the artefact's own stat-row:

- `StrategyArchetype(StrEnum)` in `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py`
  lines 87-182: **60 members** (counted every `= "..."` line). Note, as an aside worth fixing separately (not
  part of this artefact's claim): the enum's own class docstring says "59 archetypes" (line 34) — a minor,
  pre-existing off-by-one in the UAC code's self-description, not in the client artefact. The artefact's "60" is
  the *correct* number against the real enum.
- `ARCHETYPE_ENGINE_REGISTRY` / `_ARCHETYPE_ENGINE_SOURCE` in
  `strategy-service/strategy_service/engine/strategies/v2/factory.py`: **32 entries** (counted directly). Matches
  the artefact's "32 Factory-registered" exactly.
- The artefact's own explanation for the gap ("An archetype is a named idea; it becomes runnable only when a
  catalogue builder emits concrete slots for it") checks out concretely: e.g. the VOL family declares 19 archetype
  enum members but the factory registers only `VOL_TRADING_OPTIONS` — the other 18 VOL engine implementation files
  exist in `engine/strategies/v2/vol_trading/` (confirmed via the `attestations={` grep above) but are not yet
  wired into the factory's static source dict. Same pattern in MARKET_MAKING (10 declared, 2 registered). This is
  a genuine "built but not yet wired for dispatch" gap, not a fabricated distinction.

**Overlap note** (per the task's own instruction to flag, not independently verify): `ARCHETYPE_FEATURE_GROUPS`
(`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py`) is a
genuinely separate registry — feature/data-input requirements per archetype, not engine-runnability — that keys
off the same 60-member `StrategyArchetype` enum but answers a different question than
`ARCHETYPE_ENGINE_REGISTRY`. A different agent in this audit round is independently checking that registry's
own ~40-of-60 count for a different artefact section (the Nick AI platform guide, not this Elysium walkthrough).
The two registries are not interchangeable and my 60/32 finding here does not depend on or corroborate that
other count.

**Verdict: CONFIRMED**, exactly, both numbers.

### Detail — item 6: Capital budget "enforced by construction" — the consequential finding

`strategy-service-walkthrough.html` lines 927-931: "Notional ceilings apply per position and per slot, so a single
archetype cannot consume the book. Combined with per-slot trading wallets (§11), **the cap is enforced by
construction as well as by rule: a slot cannot trade capital it was never given.**"

The first audit flagged this needed "a second look before the repository ships," noting the artefact's
wallet-funding framing is *narrower* than the Oct-11 plan's still-`UNVERIFIED` "capital_budget_amount is
enforced" line, and treated the narrower framing as more defensible. **I checked both mechanisms independently
and neither is wired into production code:**

**Mechanism 1 — `capital_budget_amount` guard** (the thing the Oct-11 plan flagged `UNVERIFIED`, still open as a
`- [ ]` P0 todo there today): grepped every non-test reference to `capital_budget_amount` across strategy-service.
Every hit is pure data-plumbing — the field's declaration on `StrategyInstanceDefinition`/migration specs, the
batch-harness/CLI paper-run setup that passes it through, and the legacy-migration YAML. **Zero raise/reject/guard
logic anywhere** ties an instruction's size to `capital_budget_amount`. `risk_preflight_gate.py` — the actual
pre-trade risk-check module — has no reference to `capital_budget_amount`, `max_position_usd`, or any notional cap
at all; its `apply_risk_preflight()` is a declarative rule evaluator whose fired-rule fields are supplied by
callers, not a hardcoded capital-cap check.

**Mechanism 2 — per-slot trading wallets** (the artefact's actual, narrower claim): `TradingWalletConfig` and
`ShareClassWalletMapping` are real, defined dataclasses —
`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py` lines 408-483 — keyed by
`(client_id, slot_label)`, with a `get_trading_wallet(client_id, slot_label)` lookup method. But grepping every
non-test reference across **both** execution-service and strategy-service turns up: **zero call sites for
`get_trading_wallet()` anywhere**, and the only non-test reference to `TradingWalletConfig` outside the UAC
package itself is a single docstring mention in `execution-service/execution_service/v2/policy_resolver.py` that
explicitly cites it only as an analogy ("per UAC's `TradingWalletConfig` docstring...") — not a usage. This
mechanism is **defined but entirely unwired**: no code path anywhere looks up a slot's wallet, checks its funded
balance, or refuses a trade because a slot "was never given" the capital. It exists only as a UAC schema.

**Verdict: WRONG, not merely "narrower but defensible."** Both plausible readings of "enforced by construction"
were checked against real code and neither has a single production call site. "A slot cannot trade capital it
was never given" describes an architectural intent (and for CEX subaccounts/on-chain wallets, a partial physical
truth — a wallet can't spend a balance it doesn't hold — but that's a custody-layer fact about specific venues,
not something *this* system enforces "by construction" via the `TradingWalletConfig` binding the artefact
explicitly cites). As written, the sentence claims a general, structural guarantee that does not currently exist
in code. **Recommend**: either soften to something like "the design intends per-slot wallet funding to bound
exposure; this is not yet wired to a runtime check" (accurate today), or — better, given this is a capital-safety
claim in a document going to a regulated allocator — treat this as the highest-priority build item among the six
re-verified here and actually wire `capital_budget_amount` (or the wallet lookup) into `risk_preflight_gate.py`
or `allocation_sizer.py` before the claim ships as-is.

---

## What I could not verify

- **Item 2 (atomic multi-leg)**: I confirmed `atomic_leg_executor.py` and `leveraged_leg_controller.py` reference
  `compensation_policy`/`leader_leg`, establishing the mechanism is real and wired, but I did not trace the full
  runtime logic (e.g. whether `RETRY_HEDGE_UNTIL_DEADLINE` actually retries correctly under a real venue failure,
  or whether `hedge_deadline_ms` is enforced with a real timer) — that would need a deeper, execution-service-focused
  read than this task's scope allowed. My finding is scoped to the schema-vs-runtime distinction, which is what
  the task asked me to check.
- **Item 4 (attestation)**: I did not exhaustively check every one of the 60 archetype implementations for
  attestation population — I confirmed broad, multi-family population via grep, which is sufficient to overturn
  the stale "only MEV" framing, but did not verify 100% coverage (some archetype files may still be silent).
- **Item 5 overlap**: I did not independently verify `ARCHETYPE_FEATURE_GROUPS`'s own count — that is explicitly
  another agent's scope per this task's instructions, and I only confirmed the two registries are genuinely
  distinct code artifacts, not that either agent's count on the other registry is right.
- **Part (a)**: I searched `plans/active/` and `plans/epics/` exhaustively via grep plus direct reads of the two
  owning plans and the readiness epic. I did not separately interview the operator about an unwritten verbal
  commitment — if one exists outside the plans corpus, it is by definition not a *cited* basis, which is the
  standard the stub todo itself set ("cite what supports it, or cut it").
