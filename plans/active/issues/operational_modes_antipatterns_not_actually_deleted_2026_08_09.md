---
doc_type: issue
title:
  "operational-modes.md was wrong in 6 ways — 2 'deleted' anti-patterns are still live and decompose()'s documented
  signature never existed"
summary: >-
  A code-verified review of /codex/04-architecture/operational-modes.md (triggered by its 90-day freshness expiry on
  2026-08-09) found the workspace SSOT for the operating-mode taxonomy materially wrong. It declared three anti-patterns
  deleted; only one is. It documented ExecutionTarget/ExecutionTrigger members that do not exist (LIVE_VENUE, MANUAL)
  and omitted one that does (FORK). Worst, it documented decompose() as decompose(mode: OperationalMode) -> (target,
  trigger) when the real signature is decompose(stage: TestingStage) -> (OperationalMode, ExecutionTarget,
  ExecutionTrigger) — code written against the SSOT would not compile. Both docs were corrected in the same pass; the
  underlying CODE cleanup is what this issue tracks.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, execution-service, unified-trading-pm]
scope: [engineer]
tags: [codex-accuracy, ssot, execution, operational-mode, uac, findings-triage]
related:
  [
    /codex/04-architecture/operational-modes.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
  ]
created: 2026-08-09
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
source:
  "slot-3 interactive, 2026-08-09 — codex freshness gate flagged the doc 91d stale; reviewed against code instead of
  date-bumping"
depends_on: []
---

# `operational-modes.md` asserted a cleanup that mostly did not happen

## How this surfaced

The codex freshness gate went red on 2026-08-09 because `operational-modes.md` and `paper-vs-live-execution-seam.md`
crossed 90 days since `last_reviewed: 2026-05-10`. Nobody's commit caused it — the clock did. Rather than bump the date
(which would have been a fabricated review, the same class as a fabricated ruling citation), both docs were checked
against the actual code. Six discrepancies, listed below by severity.

## Findings

### 1. `decompose()`'s documented signature never existed (worst)

The doc — which is `authoritative_for: [operational-mode decompose helper]` — specified:

```
decompose(mode: OperationalMode) -> tuple[ExecutionTarget, ExecutionTrigger]
```

The real function (`unified_api_contracts/internal/modes.py`, ~line 233) is:

```
decompose(stage: TestingStage) -> tuple[OperationalMode, ExecutionTarget, ExecutionTrigger]
```

Different parameter type, different arity, different purpose: it is a **TestingStage migration shim**, not the mode→axes
helper the doc described. The doc's instruction that "routing / recon / UI code uses `decompose(mode)`" would produce
code that does not compile. There is no `OperationalMode → (target, trigger)` helper in UAC at all.

### 2 + 3. Enum members that do not exist, and one that was omitted

| doc said                     | code has                           |
| ---------------------------- | ---------------------------------- |
| `ExecutionTarget.LIVE_VENUE` | `ExecutionTarget.MAINNET`          |
| _(not listed)_               | `ExecutionTarget.FORK`             |
| `ExecutionTrigger.MANUAL`    | `ExecutionTrigger.MANUAL_OPERATOR` |

`FORK` is not cosmetic: `get_paper_target("ethereum")` returns `FORK`, so the EVM/Tenderly paper path is a distinct
target, not a flavour of `TESTNET` as the seam doc's diagram implied.

### 4. `_PAPER_VENUE_KEYS` — CORRECTED: relocated and legitimately reclassified, not an outstanding anti-pattern

**This finding was initially wrong, and the correction is the useful part.**

First read (grep for the symbol): the tuple is alive at `execution-service/execution_service/adapters/sports_factory.py`
(~line 21), moved from the `sports_execution/routing.py` path the doc names and grown 3 → 5 entries — therefore "deleted
by `pvl-p17c`" is false.

A parallel same-day review (slot 2) read the CONSUMER rather than just grepping the symbol, and established the
opposite: `pvl-p17c` genuinely did migrate the mode dispatch — `create_sports_adapter()` branches on
`mode == OperationalMode.PAPER` — and removed the tuple from `routing.py`. What survives in `sports_factory.py` is a
different thing wearing the same name: a per-adapter venue-key **allowlist**, consumed only AFTER the PAPER branch is
already taken, naming the venue keys the single `PaperBettingAdapter` registers itself under. That is a legitimate
permanent lookup, not a parallel mode-detection mechanism. Resolved and archived as
`/plans/archive/issues/operational_modes_paper_venue_keys_anti_pattern_not_deleted_2026_08_09.md`; the codex doc now
carries the reclassification. **No cleanup work remains here** — the `[BACKEND] P2` todo this finding originally spawned
has been withdrawn below.

**The lesson, which is why this is written up rather than silently deleted**: a surviving symbol name does not mean a
surviving anti-pattern. The anti-pattern was _mode detection via string-set_; the symbol is now an allowlist. A grep for
`_PAPER_VENUE_KEYS` cannot tell those apart, and the wrong reading is the intuitive one — the workspace's grep-then-READ
rule exists for exactly this, and the first read here broke it.

### 5. `TestingStage` — claimed deprecated, actually entangled further

Doc: deprecated 2026-05-09, listed under "Anti-patterns (deleted)". Reality: still a live `StrEnum` (`modes.py`
~line 181) with `LIVE_TESTNET` intact (~line 197) — **and `decompose()` itself now maps every `TestingStage` member to
the canonical 3-tuple** (~line 245). The parallel ladder the deprecation was meant to remove has been wired INTO the
canonical helper. Whether that is a deliberate reversal (TestingStage kept as a migration-era input type) or an
unfinished migration is the open question below; the 3-month-stale deprecation note is the only record of intent.

### 6. `paper_target_registry` is not a real symbol (docs-only, already fixed)

The name appears in 7 PM docs and **zero code**. The real API is `PAPER_EXECUTION_TARGETS` +
`get_paper_target(chain_or_venue)` in `unified_api_contracts/internal/paper_execution_targets.py`. Anyone grepping for
the documented name found nothing and could not tell whether the registry was unbuilt or misnamed. Corrected in both
codex docs in this pass; other docs still carry the old name (todo 3).

Also noted, not a doc error: a separate live `paper_trade: bool` constructor arg survives in
`execution-service/execution_service/defi_execution/protocols/aave_live.py` (~line 122). The doc's claim was scoped to
`service_config.py`, which IS clean — but it is the same competing-surface smell the anti-pattern was about.

## What was already done

Both codex docs were corrected in place (2026-08-09) with the real signatures, real enum members, and the true status of
each anti-pattern, and their `last_reviewed` bumped to reflect a review that actually happened. **No code changed.**

## Todos

- [ ] [DOCS] P2. **RULED 2026-08-09 (operator): `TestingStage` is an unfinished migration, NOT a deliberate permanent
      shim.** The deprecation language in `/codex/04-architecture/operational-modes.md` should describe it as unfinished
      (still the sole input type of `decompose()`, deprecated 2026-05-09, migration never completed) rather than being
      retired as if this were a deliberate keep. This todo's original done-when ("the codex doc states one of the two
      outcomes with a date") is only half-satisfiable from this ruling alone — the outcome is now known, but no owner or
      target date was assigned. **Do not invent an owner or date** — see the placeholder todo below; update the codex
      doc once that placeholder resolves. Repo: unified-trading-pm.
- [ ] [OPERATOR] P3. **Placeholder — assign an owner + target date for finishing the `TestingStage` migration** (per the
      2026-08-09 ruling above: unfinished, not a deliberate keep). Not worker-determinable — stays open until the
      operator names both. **Done when**: `/codex/04-architecture/operational-modes.md` records the owner + target date,
      and the todo above is closed alongside it.
- [x] ✅ WITHDRAWN 2026-08-09 — [BACKEND] P2. ~~Finish the `_PAPER_VENUE_KEYS` deletion `pvl-p17c` claimed.~~ Rests on a
      finding that turned out to be wrong (see Finding 4 above): the migration DID happen and the surviving symbol is a
      legitimate post-branch allowlist, not the anti-pattern. Deleting it would break sports paper routing for all 5
      venues. Resolved by
      `/plans/archive/issues/operational_modes_paper_venue_keys_anti_pattern_not_deleted_2026_08_09.md`.
- [x] ✅ [DOCS] P3. **Rename the remaining `paper_target_registry` references corpus-wide.** Five PM docs still use the
      non-existent name: `/plans/epics/defi_master.md`,
      `/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`, and three archived plans (leave
      archived ones alone — they are historical record). **Done when**: no ACTIVE plan or codex doc references
      `paper_target_registry`; each points at `PAPER_EXECUTION_TARGETS` / `get_paper_target()`. Repo:
      unified-trading-pm. — Done via `ao_satellite_ao_dispatch_batch15_2026_08_09.md` todo 1:
      `unified-trading-pm@6390acba57` (both active docs fixed: `/plans/epics/defi_master.md:107,110` —
      `paper_target_registry` SSOT/indexing renamed to `PAPER_EXECUTION_TARGETS` / `get_paper_target(chain)`;
      `/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md:84,261` — renamed to
      `get_paper_target()` / `PAPER_EXECUTION_TARGETS`. The 3 archived plans left untouched per this todo's own
      instruction. `/codex/04-architecture/operational-modes.md` and
      `/codex/04-architecture/paper-vs-live-execution-seam.md` were NOT touched — both already carry an explicit prior
      correction note self-referencing the old name to explain the naming issue, not a stale usage; re-grepped
      corpus-wide post-edit and confirmed zero remaining ACTIVE-plan/codex stale-usage hits outside those two
      intentional correction notes + this todo's own source/tracking docs). Independently re-verified 2026-08-10 via
      `ao_satellite_ao_dispatch_batch15_finalize_2026_08_09.md` todo 1 (fresh corpus-wide grep, zero unexpected hits).
- [ ] [BACKEND] P3. **Decide the `aave_live.py` `paper_trade: bool` constructor arg.** Either fold it into
      `OperationalMode`/`ExecutionTarget` like `service_config.py`'s was, or document why a protocol-level flag is
      legitimately different. **Done when**: the arg is gone, or the codex doc records the exemption with a reason.
      Repo: execution-service.

## Progress Log

- **2026-08-09 (slot 3, interactive)** — Found while unblocking a codex-freshness red during an unrelated ship. The gate
  did its job precisely as designed: a 90-day timer forced a re-read of an SSOT that had drifted badly from the code it
  governs, and the drift was invisible from the doc alone. Worth noting the failure mode — every one of these six errors
  would have been caught the moment anyone tried to USE the doc, which suggests nobody had, for three months, despite it
  being `authoritative_for` four separate contracts.
- **2026-08-09 (operator ruling)**: RULED — `TestingStage` is an unfinished migration, not a deliberate permanent shim;
  needs an owner + target date assigned (not invented here). Retagged `[OPERATOR]` → `[DOCS]` for the disposition record
  and filed a new `[OPERATOR]` P3 placeholder todo for the actual owner/date assignment. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09 (round9)**: satellite-extraction, not whole-doc RECLASSIFY — first audit pass on
  this doc (never previously touched by na-eligibility-audit). Of the 4 open items: the `paper_target_registry` rename
  is a pure mechanical corpus-wide rename with a code-verified real symbol name, no judgment call — extracted to
  `ao_satellite_ao_dispatch_batch15_2026_08_09.md`. The other 3 stay KEEP-NA, valid: the `TestingStage` codex-doc update
  is downstream of the operator-only owner/date placeholder (self-declared "not worker-determinable"), and the
  `aave_live.py` constructor-arg item is an explicit "decide" design call. Whole-doc RECLASSIFY bar not cleared.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **4**, matching. Re-affirms the round9 (2026-08-09) satellite-extraction verdict: the sole mechanical item
  (`paper_target_registry` corpus-wide rename) is already correctly
  `➡️ EXTRACTED 2026-08-09 to ao_satellite_ao_dispatch_batch15_2026_08_09.md`. The 3 survivors remain genuinely gated —
  the `TestingStage` codex update is downstream of an explicit `[OPERATOR]` placeholder (owner + target date, "not
  worker-determinable" per its own text, not invented here), and the `aave_live.py` constructor-arg item is an explicit
  "decide" design call. No new bounded item found on independent re-read.
- **ao_satellite_ao_dispatch_batch15_finalize 2026-08-10**: reconciled real completion evidence for the
  `paper_target_registry` rename todo back into this doc (was a bare `➡️ EXTRACTED` redirect pointer, now carries the
  actual `unified-trading-pm@6390acba57` evidence + the finalize plan's own independent re-verification). The doc's
  other 3 open items are untouched — still genuinely NA per the na-eligibility-audit history below.
- **docs-reconcile 2026-08-10**: this doc's own "What was already done" (line ~126, "Both codex docs were corrected in
  place") was itself incomplete — independently re-verified via adversarial dual-agent read (not just trusting the
  claim) and found TWO of this issue's own findings never actually landed in the cited docs: (a) Finding 5's
  `TestingStage.LIVE_TESTNET` "not deleted" correction was applied to the Anti-patterns section of
  `operational-modes.md` but never propagated to that same doc's TL;DR (line ~68) or frontmatter `summary:` (line ~7),
  which both still asserted "deleted" — self-contradicting the doc's own later section; (b) Finding 2+3's `FORK` enum
  member was documented in prose (paper-vs-live-execution-seam.md's Review note, line ~177) but the seam diagram two
  sections above it was never redrawn — still nested "EVM: Tenderly fork" under the `TESTNET` branch, exactly the wrong
  grouping the review note itself flags. Fixed both today (doc-internal-only, no code/design change, same class of fix
  as this doc's own already-applied corrections) — TL;DR/summary now say "NOT deleted... still live", diagram now has a
  separate `target == FORK` branch. Not re-opening any todo above; this was a docs-reconcile self-consistency finding,
  not new design work.
