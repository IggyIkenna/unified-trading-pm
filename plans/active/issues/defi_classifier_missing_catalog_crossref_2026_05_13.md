---
title:
  defi classifier missing instruments-service catalog cross-reference — 604k spurious attempted_failed flips blocked by
  100k cap
created: 2026-05-13
author: ikenna-slot-8
severity: P0
source:
  - unified-trading-library/unified_trading_library/legacy_reason_classifier.py:256-279 (_classify_defi)
  - unified-trading-library/unified_trading_library/legacy_reason_classifier.py:514-524 (classify_blank_reason_row defi
    branch)
  - instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py (reconciler that consumed classifier output)
related:
  - plans/active/expected_unattempted_propagation_chain_2026_05_12.md (Phase 5B apply-flips)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md (Phase 3.D.5 Wave 3)
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

Running `reconcile_legacy_blank_to_typed_reason.py --asset-group defi --apply-flips` (Slot 3 attempt 2026-05-13 ~15:06
UTC) reported:

```
candidates=604951, upgrades=604951
empty_confirmed/EXPECTED_INSTRUMENT_NOT_LISTED -> attempted_failed/LegacyBlankErrorReasonError: 598040
empty_confirmed/SOURCE_RETURNED_ZERO -> attempted_failed/LegacyBlankErrorReasonError: 6911
ERROR Detected 604951 proposed upgrades > --max-flips-per-run=100000; aborting per halt-safety rule.
```

**The 100k cap saved us from 604k spurious flips.** The classifier+reconciler combo is treating defi instrument-day
shards as "should-have-attempted" when the source-of-truth (instruments-service catalog `available_from`/`available_to`)
would indicate `EXPECTED_INSTRUMENT_NOT_LISTED`.

**Root cause** — `_classify_defi` only checks chain-genesis date:

```python
# legacy_reason_classifier.py:256-279
def _classify_defi(row):
    chain = ... ; venue = ... ; day = ...
    if candidate_chain:
        genesis = get_chain_genesis_date(candidate_chain)
        if genesis and day < genesis:
            return "EXPECTED_PRE_GENESIS_CHAIN"
    return "SOURCE_RETURNED_ZERO"  # <-- default for ALL post-genesis defi rows
```

No instruments-service catalog query. The same docstring on `_classify_cefi:296-298` explicitly says:

> **Future enhancement (Wave 3 of writegate Phase 3.D.5)**: cross-reference with instruments-service catalog
> `available_from` / `available_to` per (venue, instrument_id) → emit `EXPECTED_INSTRUMENT_NOT_LISTED` /
> `EXPECTED_INSTRUMENT_DELISTED` for per-instrument lifecycle bounds.

**Wave 3 enhancement was never implemented.** So the 598k existing `EXPECTED_INSTRUMENT_NOT_LISTED` defi rows get
re-classified to `SOURCE_RETURNED_ZERO` (no rule fires) and then flipped by `classify_blank_reason_row:514-524`:

```python
if asset_group in _INSTRUMENT_DAY_EMPTY_ILLEGIT_ASSET_GROUPS:  # {cefi, defi, tradfi}
    if reason == "SOURCE_RETURNED_ZERO":
        return ("attempted_failed", "LegacyBlankErrorReasonError")
```

This is **wrong** for the 598k rows: they were correctly marked `EXPECTED_INSTRUMENT_NOT_LISTED` (instrument doesn't
exist in catalog for that day) and should stay `empty_confirmed`, not flip to `attempted_failed`.

## Why it matters

1. **Data correctness** — 598k defi instrument-day shards would be silently mis-labeled as failures instead of honest
   "instrument not yet listed" gaps. Downstream MTDS retry logic would then trigger 598k pointless re-fetches.

2. **May-23 critical path** — defi is the lead archetype (`carry_staked_basis`). Corrupt defi manifest → wrong
   downstream features → wrong P&L attribution. Group B data-correctness gate.

3. **Cap suggested raise considered HARMFUL** — if anyone raises `--max-flips-per-run` to 1M before Wave 3 ships, they
   will commit 604k bad flips that need a reverse-reconciler to undo.

4. **Same gap exists for cefi/tradfi** — same docstring on `_classify_cefi:296-298` confirms. Tradfi already ran 0
   candidates so no immediate impact, but the gap is structural.

## Recommended decision

**P0 block on defi apply-flips for `reconcile_legacy_blank_to_typed_reason.py` until Wave 3 ships.** Three options:

### Option A — Implement Wave 3 catalog cross-reference (recommended)

Wire `_classify_defi` (and `_classify_cefi`) to query instruments-service catalog per row:

```python
from unified_trading_library.manifest import read_instruments_catalog  # or equivalent
...
inst_id = _row_get(row, "instrument_id")
catalog = read_instruments_catalog(asset_group, venue)
if inst_id and catalog is not None:
    bounds = catalog.get_bounds(inst_id)
    if bounds and day < bounds.available_from:
        return "EXPECTED_INSTRUMENT_NOT_LISTED"
    if bounds and bounds.available_to and day > bounds.available_to:
        return "EXPECTED_INSTRUMENT_DELISTED"
return "SOURCE_RETURNED_ZERO"
```

Scope: ~2-3 cal AI-days. Reads instruments-service catalog (already loaded by MTDS pre-flight per Phase 1), classifies
pre-launch / delisted / unlisted correctly. After implementation, re-run reconciler — expect 598k of 604k candidates to
resolve to legitimate `EXPECTED_INSTRUMENT_NOT_LISTED` (no flip needed) and ~6k legitimate `attempted_failed`.

### Option B — Skip defi reconciler entirely

Don't run `reconcile_legacy_blank_to_typed_reason.py --asset-group defi --apply-flips` until Wave 3 ships. Document in
`expected_unattempted_propagation_chain_2026_05_12.md` Phase 5B that defi is BLOCKED on this issue.

### Option C — Carve-out: classifier returns `EXPECTED_INSTRUMENT_NOT_LISTED` as preserve-current-reason

Patch `classify_blank_reason_row` to NOT flip rows whose CURRENT reason is `EXPECTED_INSTRUMENT_NOT_LISTED` even when
new-classifier returns `SOURCE_RETURNED_ZERO` — i.e. trust the original sweep until we have a better signal. Cleanest
1-line change but doesn't solve the underlying gap.

**Recommendation: Option A** if Wave 3 fits in the cycle; **Option B + Option C as defensive guard** otherwise. Operator
triage on cycle priority.

## Provenance

- Slot 8 (ikenna tab/8) flagged 2026-05-13 ~16:15 UTC after Slot 3 ran into 100k cap on defi
- Slot 3 (ikenna tab/3) executed reconciler, hit cap, paused PART B defi apply-flips
- Earlier context: `_classify_cefi:296-298` docstring TODO explicit; `_classify_defi:256-279` lacks catalog branch
  silently
