---
doc_type: issue
title: MTDS quickmerge RED — hardcoded blue-api.morpho.org URL in oracle_prices handler
summary: >-
  quickmerge's no_hardcoded_venue_urls.sh pre-push gate is RED for
  market-tick-data-service, blocking ALL pushes (not just this session's),
  because of a pre-existing hardcoded URL literal in
  market_tick_data_service/cli/handlers/_oracle_prices_constants.py, unrelated
  to the diff that hit it.
status: open
archive_exempt: true
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
assigned_vm: planning
execution_scope: orchestrator-agent
tags: [ci, quickmerge, mtds, morpho, hardcoded-url, repo-blocker]
priority: P1
source: pacifica_solana_canonical_mechanism_unconfirmed_2026_08_15_task_ecf1bbeb8527
parent_epic: defi_master
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# MTDS quickmerge RED — hardcoded blue-api.morpho.org URL

## What I found

Shipping an unrelated one-line docstring change to
`market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py`
via `quickmerge.sh --agent` failed at the post-QG pre-push gate
(`unified-trading-pm/scripts/qg/no_hardcoded_venue_urls.sh`, invoked by
quickmerge as part of its cross-repo checks — this is a SEPARATE gate from
`quality-gates.sh`, which had already passed green with a sentinel written
for the same commit):

```
ERROR: blue-api.morpho.org bare literal in market_tick_data_service/cli/handlers
       (use get_evm_protocol_rest_url("morpho") from unified_api_contracts.registry)
ERROR: 1 hardcoded-URL violation(s) in MTDS handlers
```

Confirmed PRE-EXISTING and unrelated to the shipped diff: my commit only
touched `scripts/reconcile_pacifica_quarantine_2026_08_15.py` (`git show
--stat HEAD`). The violation is
`market_tick_data_service/cli/handlers/_oracle_prices_constants.py:556`:

```python
_MORPHO_BLUE_API_URL = "https://blue-api.morpho.org/graphql"  # DERIVED 2026-08-14 from docs.morpho.org (same endpoint morpho_adapter.py/lending_indices_morpho.py already use)
```

— dated 2026-08-14 in its own comment, landed well before this session. This
is a genuine repo-wide RED gate: it will block EVERY quickmerge push to
`market-tick-data-service` until fixed, not just this task's.

## Why it matters

Per `CLAUDE.md` "Commit + Push + Flip" HARD RULE, code reaches the
integration branch only via quickmerge — a red pre-push gate on this scale
stalls the whole repo's shippable-unit throughput. `no_hardcoded_venue_urls.sh`
exists (`is_mtds_contract_audit_2026_05_20`) specifically to force handler
URLs through IS's `InstrumentRecord.source_archive_url_template` / UAC's
`get_evm_protocol_rest_url()` registry rather than hardcoded literals.

## Recommended decision

Fix the violation directly: replace the hardcoded
`_MORPHO_BLUE_API_URL = "https://blue-api.morpho.org/graphql"` literal in
`market_tick_data_service/cli/handlers/_oracle_prices_constants.py` with
`get_evm_protocol_rest_url("morpho")` from `unified_api_contracts.registry`,
per the gate's own error message. Verify `unified_api_contracts.registry`
actually has a "morpho" entry resolving to this same URL before swapping (if
it doesn't, register it there first — do not hand-roll a second literal).

- [x] ✅ [DATA] P1. Replace the hardcoded `_MORPHO_BLUE_API_URL` literal in
      `market_tick_data_service/cli/handlers/_oracle_prices_constants.py`
      with `get_evm_protocol_rest_url("morpho")` from
      `unified_api_contracts.registry` (registering the "morpho" entry in UAC
      first if it doesn't already exist) so `no_hardcoded_venue_urls.sh`
      passes and quickmerge pushes to market-tick-data-service unblock.
      (repos: market-tick-data-service, unified-api-contracts) —
      market-tick-data-service@8b0cedce63. The "morpho" entry already existed
      in `unified_api_contracts.registry.capability_declarations._defi`
      (`EVM_DEFI_REST_URLS["morpho"]["api_url"] = "https://blue-api.morpho.org"`,
      exposed via `get_evm_protocol_rest_url`) — no UAC registration needed.
      `_MORPHO_BLUE_API_URL` now derives as
      `f"{get_evm_protocol_rest_url('morpho')}/graphql"`, the same pattern
      `morpho_adapter.py`'s `MORPHO_API_URL` already used.
      `scripts/qg/no_hardcoded_venue_urls.sh` verified passing +
      `quality-gates.sh` green on the shipped SHA.
