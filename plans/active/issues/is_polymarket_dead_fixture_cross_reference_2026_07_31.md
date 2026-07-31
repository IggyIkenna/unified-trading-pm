---
doc_type: issue
title:
  instruments-service's Polymarket adapter carries a dead API-Football fixture cross-reference capability, wired
  end-to-end from factory.py (fetches a real secret) but never invoked
summary: >-
  `PolymarketReferenceDataAdapter.__init__` accepts `api_football_api_key`, stores it as `self._api_football_key`, and
  maintains a `self._fixture_cache` dict — all in service of the single method that reads them,
  `_cross_reference_fixture()` (async, calls `ApiFootballAdapter.get_fixtures`). `instruments_service/reference_data/
  factory.py::get_or_create_adapter` resolves a real `api_football` secret from `extra_api_keys` and threads it into
  the constructor for every Polymarket adapter built via the factory (the only production construction path) — so the
  factory does real work (secret resolution) to feed a capability nothing calls. `_cross_reference_fixture()` has zero
  call sites anywhere outside its own dedicated test file
  (`tests/unit/test_prediction_adapters_comprehensive.py::TestCrossReferenceFixture`); the ONLY other reference to it
  in the codebase is `_build_sports_id()`'s own docstring, which explicitly calls it "the unused, network-dependent
  `_cross_reference_fixture()`" and states it was deliberately left unwired for capture-throughput reasons.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [dead-code, adapters, prediction, polymarket, adapter-dead-code-and-fallback-ban]
related:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: 2026-07-31
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-31 (slot-12, backend_engineer) while executing prediction_consolidated_native_ao_extract_2026_07_25.md
    todo 1's adapter dead-code/fallback audit, per /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# instruments-service: dead Polymarket fixture cross-reference capability

## What I found

`instruments_service/reference_data/adapters/prediction/polymarket/adapter.py::PolymarketReferenceDataAdapter`:

```python
def __init__(self, project_id=None, api_key=None, api_football_api_key=None) -> None:
    ...
    self._api_football_key = api_football_api_key
    self._fixture_cache: dict[str, str] = {}  # "LEAGUE:HOME:AWAY:DATE" → fixture_id
```

`instruments_service/reference_data/adapters/prediction/polymarket/parsing.py::_cross_reference_fixture()` (line 430)
is the only method that reads `self._api_football_key` / `self._fixture_cache`. Grep across the repo (excluding
`tests/`) for `_cross_reference_fixture` returns exactly two hits: its own `async def` and the comment in
`_build_sports_id()` (parsing.py:356-360) that names it:

> "deliberately NOT wired through the unused, network-dependent `_cross_reference_fixture()` (a per-market
> API-Football call in the hot adapter-parsing path would be a real capture-throughput regression); that method
> remains available as a higher-fidelity follow-up for an async, rate-limited pipeline stage."

Yet `instruments_service/reference_data/factory.py:697-704` — the ONLY production adapter-construction path
(`get_or_create_adapter`) — does real work to feed this dead capability:

```python
elif adapter_key == "polymarket" and extra_api_keys:
    af_key = extra_api_keys.get("api_football")
    adapter = PolymarketReferenceDataAdapter(project_id=project_id, api_key=api_key, api_football_api_key=af_key)
```

So a real `api_football` secret is resolved and passed into every live Polymarket adapter instance, purely to sit
unused in `self._api_football_key`.

Per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` rule 1: "a module/class/function that is
defined and registered somewhere... but never actually reached by any live code path is dead code, even though
`vulture` won't flag it... Either delete it or document why it's intentionally kept (e.g. behind a feature flag with a
stated activation path)." The comment here documents WHY it's unwired (throughput), but not a concrete activation
path — "remains available as a higher-fidelity follow-up for an async, rate-limited pipeline stage" is aspirational
future-work framing, not a feature flag or a scheduled follow-up plan item.

(The soccer-fixture join Polymarket DOES ship live — `af_fixture_id`/`home_team_canonical_id`/etc. via
`PredictionFixtureResolver.resolve()` in `fixture_match.py`, called from `_build_sports_id()` — is a SEPARATE,
GCS-parquet-based mechanism with no API-Football network call in the hot path. That one is live and out of scope
here; this finding is specifically about the unused constructor-injected `api_football_api_key` / `_cross_reference_
fixture()` pair.)

## Why it matters

- The factory resolves and threads a real secret for a code path that does nothing with it — dead weight on every
  Polymarket adapter construction, and a red herring for anyone reading `factory.py` trying to understand what
  `api_football_api_key` is actually for.
- `_fixture_cache` / `_cross_reference_fixture()` implement a DIFFERENT team-matching strategy (live per-market
  API-Football lookups with a local cache) than the shipped `PredictionFixtureResolver` (GCS parquet + shared alias
  index) — two divergent, never-reconciled approaches to the same problem living in the same file, one dead. This is
  adjacent to (though not identical to) the codex doc's rule 3 duplicate-implementation concern.

## Recommended decision

Not adjudicated here:

- **(A) Delete** `_cross_reference_fixture()`, the `_fixture_cache` instance attr, the `api_football_api_key`
  constructor param, and the `factory.py` secret-threading that feeds it, plus its dedicated test class — the shipped
  `PredictionFixtureResolver` mechanism already covers Polymarket soccer fixture matching in production.
- **(B) Keep, but give it a real activation path** — if there's an actual planned "async, rate-limited pipeline stage"
  this is meant to feed, name that plan/todo explicitly in the docstring (not just aspirational prose) so the codex
  rule's "stated activation path" bar is genuinely met.

## Todos

- [ ] [BACKEND] P2. Decide (A) vs (B) above with the operator/plan owner, then either delete
      `PolymarketReferenceDataAdapter._cross_reference_fixture()` + `_fixture_cache` + the `api_football_api_key`
      constructor param + `factory.py`'s `af_key` threading + the dedicated test class, or add a concrete named
      activation path (real plan/todo reference) to the code comment. (repo: instruments-service)

## Progress Log
