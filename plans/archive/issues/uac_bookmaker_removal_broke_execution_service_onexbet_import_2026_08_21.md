---
doc_type: issue
title:
  unified-api-contracts@cdb8ae8806 (6-bookmaker removal) broke execution-service's import chain --
  caught and fixed same-session
summary: >-
  Deleting unified_api_contracts/external/onexbet/ (operator ruling: remove BETOPENLY/NOVIG/ONEXBET/PROPHETX/
  BETMGM/BETWAY everywhere) broke execution-service/sports_execution/adapters/bookmaker_api/onexbet.py's
  module-level `from unified_api_contracts.external.onexbet.schemas import (...)`, transitively reachable via
  adapters/bookmaker_api/__init__.py -> adapters/__init__.py -> sports_execution/__init__.py -- a real
  ModuleNotFoundError for anything importing sports_execution. Caught by direct reproduction within the same
  session that shipped the UAC change (not by CI), fixed by deleting the dead OneXBetAdapter (already confirmed
  unrouted by a separate investigation before this incident), verified, and shipped. A concurrent session found
  and fixed the identical breakage independently -- the two fixes collided in a rebase and were reconciled
  (kept theirs, plus one genuinely-unique piece: an odds_api.py mapping-alias cleanup theirs didn't cover).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [unified-api-contracts, execution-service]
scope: [engineer]
tags: [cross-repo-break, sports, bookmaker-removal, import-chain, incident, big-finding]
related:
  [/plans/active/issues/sports_bookmaker_roster_classification_2026_08_21.md]
created: "2026-08-21"
author: T1 tranche session
source: >-
  First-hand: this session shipped the UAC deletion, then discovered the break while finalizing the
  sports_bookmaker_roster_classification_2026_08_21.md doc (which documented that a DIFFERENT session had
  already found this exact risk and deliberately avoided it) -- re-verified by direct import reproduction
  before and after the fix, not relayed or assumed.
priority: P1
parent_epic: security_and_cross_cutting_master
resolved_by: execution-service@0c81d75501 (this session, 2026-08-21)
locked_by:
supersedes:
superseded_by:
depends_on: []
---

# UAC bookmaker removal broke execution-service's onexbet import chain

## What happened

1. This session (T1 tranche) shipped `unified-api-contracts@cdb8ae8806`, completing the operator-ruled 6-bookmaker
   removal (BETOPENLY/NOVIG/ONEXBET/PROPHETX/BETMGM/BETWAY) in files a parallel session's own fix
   (`unified-api-contracts@710db834`) had not covered -- including deleting the entire
   `unified_api_contracts/external/onexbet/` adapter package after confirming, via `grep`, zero remaining
   importers **at that point in time**.
2. While updating `sports_bookmaker_roster_classification_2026_08_21.md` with the new SHA, discovered that
   doc already contained the OTHER session's own finding: `execution-service/sports_execution/adapters/
   bookmaker_api/onexbet.py:31` does `BOOKMAKER = BOOKMAKER_REGISTRY["onexbet"]` at module level, and (more
   critically for this incident) `onexbet.py:22` does
   `from unified_api_contracts.external.onexbet.schemas import (...)` -- also module-level. That other session
   had deliberately left `bookmaker_registry.py`'s onexbet entries untouched specifically because of this
   binding, per their own dispatch instructions ("if any live code binds them, STOP and report").
3. This session's own `external/onexbet/` deletion did not cross-check execution-service (a different repo, no
   grep run against it before shipping) -- direct reproduction confirmed the break:
   `ModuleNotFoundError: No module named 'unified_api_contracts.external.onexbet'`, transitively reachable from
   `sports_execution/__init__.py` itself (i.e. anything importing the sports_execution package at all, not just
   the specific adapter).

## Why this happened

The two sessions' scopes were genuinely disjoint at the UAC layer (one covered the registry-constant family, one
covered the `canonical/domain/sports/*` + `external/*` family the first missed) but **neither session's own
cross-repo verification caught the other's blind spot before shipping** -- the OTHER session correctly grepped
execution-service before touching `bookmaker_registry.py` and found the binding; this session grepped
execution-service for `bookmaker_registry` usage but not specifically for `external.onexbet` imports (a narrower,
easier-to-miss binding one file away from the one already known to be risky).

## Resolution

- Confirmed `OneXBetAdapter` was independently already found dead/unrouted (`SportsHandler.BOOKMAKER_VENUES` is
  empty -- `sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md` finding 11) before this incident,
  by the same investigation that flagged the risk. Removing it (not reverting the UAC deletion) is the correct,
  complete fix -- it finishes the operator's "remove everywhere" ruling rather than partially undoing it.
- Removed `onexbet.py` + its dedicated test file, un-wired both `__init__.py` re-export chains, dropped the
  `odds_api.py` aggregator alias, emptied `test_adapter_stubs.py`'s now-empty `BOOKMAKER_API_ADAPTERS` list.
- A concurrent session (`execution-service@f4391ac59`) independently found and fixed the identical breakage
  while this fix was mid-QG -- the two collided in a `git rebase --autostash` push retry; reconciled by taking
  their version for the overlapping files and keeping only the one piece unique to this session's fix (the
  `odds_api.py` mapping-alias line their fix didn't touch). Shipped as `execution-service@0c81d75501`.
- Regenerated `unified-trading-pm`'s `adapter_contract_baseline.yaml` (QG STEP 5.83 ratchet) to drop the now-
  deleted file's stale entry -- verified clean 2-line diff before shipping via the `scripts/quality_gates/`
  direct-push carve-out (CLAUDE.md § git discipline).
- Verified post-fix: `python -c "import execution_service.sports_execution.adapters"` succeeds cleanly on the
  landed origin state.

## Lesson for next time

Before deleting a UAC module/package that's a candidate for cross-repo import, grep **every** consumer repo for
the exact dotted import path being deleted (`unified_api_contracts.external.<pkg>`), not just for the specific
symbol names (`bookmaker_registry`, `CLOUD_RUN_JOBS`, etc.) already flagged as risky by a prior investigation --
a narrower, unflagged binding one file away is exactly the kind of thing that slips through.

## Todos

- [x] ✅ [BACKEND] P1. Fix + ship the execution-service break. — execution-service@0c81d75501.
- [x] ✅ [SCRIPT] P2. Regenerate the adapter-contract-regression baseline. — shipped via direct-push carve-out.
- [ ] [SCRIPT] P3. Consider whether the pre-deletion cross-repo grep step used elsewhere in this session (and
      by the other session, for `bookmaker_registry.py`) should be a documented, mandatory checklist item for
      any UAC package/module deletion — not scoped/authored here, flagging only.

## Progress Log

- **2026-08-21**: Incident found, root-caused, fixed, and shipped within the same session that caused it — see
  "What happened" / "Resolution" above for the full evidence trail.
