---
doc_type: issue
title:
  instruments-service's Polymarket reference-data adapter is broken (import-time, blocks the ENTIRE test suite) by
  unified-api-contracts@4f25d5f0's deletion of PredictionMarketMapper — needs a scoped design decision, not (yet)
  confirmed mechanical
summary: >-
  unified-api-contracts@4f25d5f0 (`feat!: delete deprecated PredictionMarketCategory axis, migrate consumers to
  CanonicalQuestionGroup/two_axis`, tracked as [x] done in walkthrough_feedback_remediation_2026_08_21.md's
  "Manifest supersession flagged to T2 (no-migration scope here)" todo) deleted `unified_api_contracts/prediction.py`
  and `canonical/domain/prediction/{__init__.py,prediction_mapping.py}` entirely, including `PredictionMarketMapper`,
  with no successor of the same shape anywhere in UAC. That todo's own self-audit (`rg
  'PredictionMarketCategory|canonical/domain/prediction[^s]'`) was scoped to UAC's own repo and claimed "no production
  consumer" for the deleted symbols — false: `instruments-service/instruments_service/reference_data/adapters/
  prediction/polymarket/{markets.py,parsing.py}` imports `PredictionMarketMapper` from the now-deleted
  `unified_api_contracts.prediction` module at PACKAGE-INIT time (`markets.py:23`,
  `_MAPPER = PredictionMarketMapper()` at module level). Because this package is imported by
  `instruments_service/reference_data/factory.py` (the adapter registry every service/test touches), the
  `ModuleNotFoundError` fires at pytest COLLECTION time and fails the ENTIRE instruments-service test suite —
  measured 2026-08-21: `quality-gates.sh --no-fix` produced "3 skipped, 5 xfailed, 2 warnings, 4079 errors" with ZERO
  tests passing (previously 5390 passed on the same tree before this commit landed). Same root cause + same shape as
  the sibling `deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md` issue (also found
  2026-08-21, also a downstream consumer the UAC-side self-audit missed) — but the actual blast radius here, traced
  to the real call site, is NARROWER than that sibling issue's: `_MAPPER.map_market(...).category` (parsing.py:73-80)
  feeds exactly ONE branch of `_build_instrument_id()` (parsing.py:230-276) — the residual "not sports, not a
  keyword-matched crypto asset, not a keyword-matched macro index" fallback, where `category` only labels the
  `instrument_type` string suffix (`prediction::{category}`, e.g. `prediction::politics`/`prediction::weather`/
  `prediction::other`) and `canonical_instrument_id` is already `None` regardless (populated separately by the
  cross-venue mapping rollup step per that method's own docstring). Sports/crypto/macro markets never reach this
  branch (they resolve via independent matchers earlier in the same function) — but the coarse-bucket vocabulary
  (`politics`/`financial`/`sports`/`crypto`/`weather`/`entertainment`/`other`) `PredictionMarketMapper` produced has
  no replacement anywhere in UAC post-4f25d5f0 (mirrors the sibling issue's finding exactly), so even this narrower
  fix isn't a mechanical symbol swap — it needs either a locally-owned coarse-bucket mapping (re-introducing, in this
  one repo, the axis UAC just deleted workspace-wide) or a redesign of this one fallback branch around the two-axis
  model (`classify_polymarket_to_canonical_group()` + `CANONICAL_GROUP_METADATA`, both already imported in the same
  file for the SEPARATE `canonical_question_group` field one method away) — genuinely a design call given real,
  already-captured Polymarket `instrument_type` values would change, not attempted blind by a session whose actual
  task was an unrelated Kalshi-perp data repoint and who could not even run the full test suite to verify a fix's
  blast radius (collection itself is broken).
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [prediction, breaking-change, cross-repo-consumer-migration, instruments-service, quality-gates]
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
    /plans/active/issues/deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-21
author: claude-code (T2 session, code_readiness_t2_refdata_marketdata_2026_08_19.md — Kalshi perp data-only repoint)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P0
resolved_by:
source: >-
  Hit live 2026-08-21 re-gating instruments-service after a coordinator signal that unified-api-contracts was clean
  at 4f25d5f0 and it was safe to retry an unrelated Kalshi-perp quickmerge. `quality-gates.sh --no-fix` failed at
  pytest collection with 4079 errors and zero passed (vs. 5390 passed on the same tree pre-4f25d5f0). Traced via
  `grep -rln "PredictionMarketMapper" instruments-service/` (3 files: markets.py, parsing.py, polymarket/__init__.py)
  and `git show 4f25d5f0 -- unified_api_contracts/prediction.py` (confirms the module was deleted outright, not
  moved) and a direct grep of live UAC for any surviving `PredictionMarketMapper` definition (zero hits — no
  successor exists). Read `parsing.py`'s actual call site (`_parse_market` → `_build_instrument_id`) to scope the
  real blast radius rather than guessing from the import alone.
context_scope:
  [
    instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/markets.py,
    instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/parsing.py,
    instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/__init__.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/predictions/two_axis.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py,
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/issues/deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md,
  ]
depends_on: []
locked_by:
locked_since:
---

## What's broken

`instruments_service/reference_data/adapters/prediction/polymarket/markets.py:23` and
`__init__.py:57` both import a name deleted outright by `unified-api-contracts@4f25d5f0`:

```python
from unified_api_contracts.prediction import PredictionMarketMapper   # module deleted entirely
...
_MAPPER = PredictionMarketMapper()   # module-level construction, markets.py:367
```

`unified_api_contracts/prediction.py` (the facade module) and the package it re-exported
(`canonical/domain/prediction/`) were both deleted in the breaking commit — not moved, not
aliased. `PredictionMarketMapper` has no successor anywhere in the current UAC tree (confirmed
via grep — zero hits).

Since `polymarket/__init__.py` (which does the import) is loaded by
`instruments_service/reference_data/factory.py` (the adapter registry), the resulting
`ModuleNotFoundError` fires at **pytest collection time** — it fails the entire test suite, not
just prediction-specific tests. Measured 2026-08-21: `quality-gates.sh --no-fix` → "3 skipped, 5
xfailed, 2 warnings, 4079 errors" with **zero tests passing** (the same tree passed 5390 tests
immediately before this commit landed upstream).

## The real (narrower than it first looks) blast radius

`parsing.py::_parse_market()` line 73-80:

```python
mapped = _pm._MAPPER.map_market(
    venue="POLYMARKET", market_id=condition_id, question=question,
    resolution_date=expiry, outcomes=tuple(market.outcomes) if market.outcomes else ("Yes", "No"),
)
category = mapped.category.value  # crypto, financial, sports, politics, etc.
```

`category` is passed into `_build_instrument_id()` (line 230), which branches:
1. **Sports** — resolved via `market.sports_market_type` (structural field), `category` unused.
2. **Crypto** — resolved via `_pm._match_crypto_asset(question)` (keyword matcher), `category`
   unused.
3. **Macro** — resolved via `_pm._match_macro_index(question)` (keyword matcher), `category`
   unused.
4. **Fallback** (everything else) — `label = "other" if category == "sports" else category`,
   then `instrument_type = f"prediction::{label}"`, `canonical_instrument_id = None` (populated
   separately downstream regardless, per the method's own docstring).

So `category` only matters in branch 4, and only to label the `instrument_type` string suffix —
it does NOT drive `canonical_instrument_id` (already `None` in this branch either way). This is
a real, live production field (written into every captured Polymarket `InstrumentRecord` that
falls through to this branch), but a narrower surface than the sibling deployment-api issue's
external-facing API/UX contract.

## Why this still isn't a confirmed-mechanical fix

`PredictionMarketMapper`'s coarse-bucket vocabulary (`politics`/`financial`/`sports`/`crypto`/
`weather`/`entertainment`/`other`) has no drop-in successor — `PredictionUnderlying` (the new
Axis-1 replacement) is fine-grained (`BTC`, `CRUDE_OIL`, `TRUMP`, `SPORTS_MLB`, ...), not a
7-value bucket, mirroring exactly what the sibling deployment-api issue found. A same-shape local
mapping would have to be either:

1. **Resurrected locally** — instruments-service builds and owns a small
   `PredictionUnderlying -> {bucket}` table, re-introducing (in this one repo) the exact axis UAC
   just deleted workspace-wide.
2. **Redesigned** — branch 4's fallback instrument_type label is rebuilt around
   `classify_polymarket_to_canonical_group()` / `CANONICAL_GROUP_METADATA` (both already imported
   in this same file, already used one method away for the separate `canonical_question_group`
   field) — needs deciding what bucket-equivalent (if any) those expose, and whether reordering
   `_parse_market()` (currently computes `group` AFTER calling `_build_instrument_id`) is
   required.

Either option changes a real, already-captured production field
(`InstrumentRecord.instrument_type`) for existing Polymarket markets — this session could not
even run the full test suite to verify a candidate fix's blast radius, since collection itself is
broken. Not attempted blind under an unrelated task's time budget.

## Impact right now

`quality-gates.sh` is red for the ENTIRE instruments-service repo — blocks ANY ship to this repo,
not just prediction-catalogue changes. Confirmed blocking
`code_readiness_t2_refdata_marketdata_2026_08_19.md`'s Kalshi-perp data-only repoint ship (code
complete + unit-tested + previously gate-green on everything except this pre-existing, unrelated
import break that landed between QG runs).

- [ ] [BACKEND] P0. Pick one of the two options above (or a third, better one) for
      `parsing.py::_build_instrument_id()`'s fallback-branch `category` derivation, apply it to
      `markets.py`/`parsing.py`/`__init__.py`, then confirm `quality-gates.sh --no-fix` collects +
      passes in instruments-service again (was 5390 passed before 4f25d5f0 landed — that is the
      bar, not just "collects"). Check whether any existing instruments-service test asserts the
      OLD coarse-bucket `instrument_type` values (e.g. `prediction::politics`) and update
      deliberately, not incidentally.
