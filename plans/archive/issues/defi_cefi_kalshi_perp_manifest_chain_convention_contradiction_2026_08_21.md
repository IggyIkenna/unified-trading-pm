---
doc_type: issue
title: KALSHI-PERP cefi perp_funding manifest chain convention contradicts the current code's own enforced invariant — blocks the 567-row re-emit
summary: >-
  Attempting to execute `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s last open todo (re-emit the 567
  GCS-present/manifest-absent KALSHI_PERP perp_funding (day,symbol) instances into the CEFI manifest, per the
  2026-08-06 operator ruling in `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`) found: (1) both
  prerequisites are genuinely done (the cefi-routing writer fix `market-tick-data-service@2aa23de5` shipped
  2026-07-27, the corpus-wide scope audit landed 2026-07-28), (2) the GCS-object side of the migration may ALREADY be
  partially done (13/13 real-symbol objects for the sample day 2026-07-22 already exist at the correct CEFI path,
  uploaded 2026-08-08 — origin unknown, not found in any plan/issue Progress Log), but (3) EVERY real CEFI
  `(venue=KALSHI-PERP, data_type=perp_funding)` manifest row ever recorded (2026-07-26 through 2026-08-19, the row's
  entire observed history) carries `chain=""`, while the CURRENT code
  (`perp_funding_handler.py::_run_process`, live-verified via `_build_row_key(chain="")` — it raises
  `BlankChainError`) requires a non-blank `chain="KALSHI_PERP"` workaround stamp and would refuse to write a blank-chain
  row at all. Writing the historical re-emit with `chain="KALSHI_PERP"` (matching the code) would create the FIRST-EVER
  divergent-chain row for this shard family; writing `chain=""` (matching every real row) is not achievable through the
  documented production write path (`DefiManifestRecorder`) without bypassing its hard BlankChainError invariant. The
  real writer that has been producing the `chain=""` rows for 3+ weeks was not found despite a real search (not
  `market_tick_data_service/live/` — zero `perp_funding` hits there; not `kalshi_perp_ws.py` — that connector is
  `book_snapshot`-only, unrelated `chain=None` call; no dedicated KALSHI-PERP chain-restamp script exists in
  `scripts/`). Paused before any write — did not execute the historical re-emit, did not flip the plan's todo, did not
  archive the plan.
status: resolved
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [defi, cefi, kalshi-perp, manifest, chain-axis, data-correctness, resolved]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineer
drift_direction: unknown
depends_on: []
resolved_by: market-tick-data-service@f7cdd18b21
locked_by:
source: >-
  Discovered live 2026-08-21 while executing defi_satellite_ao_dispatch_batch2_2026_07_26.md's last open todo
  (line ~307), itself sourced from defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md's
  2026-08-06 operator-ruled [DATA] P1 re-emit todo.
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py,
  ]
---

# KALSHI-PERP cefi perp_funding manifest chain convention contradiction

> **🟢 RESOLVED 2026-08-21** — operator ruled "KALSHI-PERP is not a chain." Fixed + shipped
> `market-tick-data-service@f7cdd18b21` (narrow `_CHAINLESS_VENUES` carve-out); codex updated
> (`/codex/02-data/defi-canonical-naming-ssot.md`); the 567-row historical re-emit this contradiction blocked was
> found already complete via a live full-window query. Full detail in the Resolution section below. Archived per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s 6-step ritual.

## What was measured (live, 2026-08-21)

**Both prerequisites for the re-emit todo are genuinely done** (contrary to the todo sitting untouched for 26 days —
the plan itself is not stale, it just never got picked back up):

- `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s cefi-routing fix shipped
  `market-tick-data-service@2aa23de5` (2026-07-27) — confirmed live in `perp_funding_handler.py`/
  `_perp_funding_kalshi_polymarket.py` at current HEAD.
- Its corpus-wide KALSHI_PERP scope audit landed 2026-07-28 (batch1 Progress Log): 567 (day,symbol) GCS-present /
  manifest-absent instances, window 2026-05-29..2026-07-25 (55 active days of 58, 13 real symbols), all sitting at
  the stale pre-fix `asset_group=defi`/unhyphenated `venue=KALSHI_PERP` path. Live-reconfirmed today: the sample day
  `day=2026-07-22` has exactly 13 real-symbol objects at that stale path (matches the audit's per-day symbol count).

**Surprise finding #1 — the GCS-object side may already be done, undocumented.** The correct CEFI-classified path for
that same sample day (`.../pipeline_mode=batch_kalshi_perp/asset_group=cefi/venue=KALSHI-PERP/instrument_type=
perpetual/data_type=perp_funding/`) already has all 13 symbol objects, uploaded **2026-08-08** (per GCS object
metadata `last_modified`). Nothing in this plan, the source issue doc, or batch1's Progress Log records this upload —
whoever/whatever did it did not flip any tracking. This needs a scoped check across the FULL 55-day window (not just
the one sample day) before trusting it's complete — not done in this session (paused before further live queries
given finding #2 below made the write side risky regardless).

**Surprise finding #2 — the manifest side contradicts the code, and blocks any new write.** Streamed the full CEFI
`_index/availability_index.parquet` (30,801,085 rows) filtered to `venue="KALSHI-PERP", data_type="perp_funding"`:
every row from **2026-07-26 through 2026-08-19** (the data_type's entire observed history in this manifest, 25
consecutive real captured days, `row_count=39.0` each = 13 symbols × 3 daily funding settlements) carries
**`chain=""`**. Directly invoking the current code's own row-key builder —

```
_build_row_key(target_day=date(2026,8,15), venue="KALSHI-PERP", chain="", data_type="perp_funding")
# -> raises BlankChainError: blank chain for chain-scoped DeFi shard (venue='KALSHI-PERP', ...)
```

— confirms `chain=""` is IMPOSSIBLE to write through the documented, current production path
(`DefiManifestRecorder.record_captured()` → `_emit_captured_add()` → `_write_captured_row()` → `_build_row_key()`,
`_defi_manifest.py`). `perp_funding_handler.py::_run_process` (current HEAD, commit `fb32fb65`, 2026-07-30 — an
"URGENT revert" of a same-day `chain=""` attempt that the commit message says "silently dropped every
kalshi_perp/polymarket_perp/hyperliquid manifest write") hardcodes `chain_for_manifest = "KALSHI_PERP"` (the
non-blank workaround) via `_chain_map`, explicitly documented in an inline comment as "the established, load-bearing
workaround... not drift."

**These two things cannot both be true of the same live system**: the code that supposedly writes these rows raises
on blank chain, yet 100% of the real rows it's supposedly been writing for 3+ weeks are blank-chain. Searched for an
alternative writer and did not find one:

- `market_tick_data_service/live/` — zero files mention `perp_funding` at all (`grep -rl perp_funding live/` empty).
- `market_tick_data_service/live/connectors/kalshi_perp_ws.py` (added `c487a78e`, "Kalshi-perp live WS ... cefi
  book_snapshot") — its one `chain=` reference is `chain=None` for a `book_snapshot` write, unrelated to
  `perp_funding`.
- No `scripts/*restamp*kalshi*chain*` or equivalent cleanup script exists (checked `scripts/` fleet-wide for any
  script combining "KALSHI" + "chain"; the only real precedent, `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`,
  scopes `TARGETS = {"HYPERLIQUID", "ASTER", "EXTENDED-STARKNET", "LIGHTER-ZKSYNC"}` — KALSHI-PERP was never in it).

Not investigated further (would need deployment-artifact inspection, not just git history): whether the ACTUALLY
DEPLOYED MTDS Cloud Run/VM image is behind `fb32fb65` (i.e. still running the reverted `chain=""` code despite the
git revert landing 2026-07-30) — this is the most likely remaining explanation and would itself be a separate,
real deployment-drift finding if confirmed.

## Why this blocks the re-emit todo

The re-emit needs to write ~50-55 new historical manifest rows (one per affected day, `(day, venue)` grain per
`_run_process`'s own recording convention — NOT per-symbol; `instrument_id` is left blank for perp_funding per
`record_captured`'s own docstring) for 2026-05-29..2026-07-25. Whichever chain value is chosen:

- `chain="KALSHI_PERP"` (matches current code's enforced invariant) — creates the FIRST-EVER divergent-chain rows for
  this exact `(venue, data_type)` family, contradicting all 25 real rows on file. A downstream reader that assumes
  one canonical chain value per shard (the exact assumption `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` was
  built to defend for the other 4 venues) would see this as fresh drift needing its own future cleanup.
- `chain=""` (matches every real row) — not writable through `DefiManifestRecorder`, the only production-sanctioned
  manifest-write path this investigation could locate for a batch/historical KALSHI-PERP perp_funding row. Bypassing
  `BlankChainError` (a hard, explicitly-recent, explicitly-documented data-correctness invariant — commit `fb32fb65`
  calls a blank-chain write in this exact shard family a bug, not a style choice) to match unexplained live data is a
  guess, not a resolution.

Per this workspace's stop-condition guidance, this is exactly the "ambiguous scope / touches production data riskily"
case — paused here rather than writing either value into the live 30.8M-row CEFI manifest on a guess.

## Recommended next steps (not a checkbox list — investigation + a decision, not bounded execution)

1. Confirm whether the deployed MTDS Cloud Run/VM image's `perp_funding_handler.py` actually matches this repo's
   current HEAD (`fb32fb65`+) or is running a stale pre-revert build — would fully explain the contradiction if stale.
2. If the deployed code IS current (contradiction persists), find the real writer — check the standard cefi
   orchestrator's sentinel fan-out (`engine.orchestrator.process_ticks`, `_defi_manifest.py`'s own docstring names
   this as the mechanism for "CeFi/TradFi/SPORTS/PREDICTION pipelines") for a KALSHI-PERP perp_funding registration
   this investigation didn't locate.
3. Once the real, currently-authoritative writer + its chain convention is identified, decide (or re-confirm) the
   canonical chain value for this shard family going forward, and whether the 25 real `chain=""` rows need their own
   restamp (if `chain="KALSHI_PERP"` turns out to be the intended standard) or the code comment's "load-bearing
   workaround" framing is simply wrong for this venue now (if `chain=""` is genuinely fine and the current code's
   `_chain_map` entry for `kalshi_perp` is what should be removed).
4. Once resolved, re-verify (fresh, scoped per-day GCS listing — not a whole-corpus walk) whether the CEFI-path GCS
   objects are already fully migrated for the whole 55-day window (surprise finding #1 above, only spot-checked one
   day here) before re-attempting the object copy — the object-copy work may already be entirely done, only the
   manifest-row work may remain.
5. Execute the re-emit (a migration script mirroring `_write_cefi_perp_funding_rows` + `DefiManifestRecorder`,
   feeding each stale object's real captured rows — protocol/coin/symbol/funding_rate/timestamp_ms/timestamp — back
   through the production writer/validator, one manifest row per affected day at `(venue, chain, data_type)` grain
   with the row_count summed across that day's symbols; NOT a live re-fetch, per the operator's "already-written
   objects" phrasing and Kalshi's funding-rates endpoint's uncertain retention window for ~3-month-old dates) was
   designed and dry-run-validated against real production reads this session (confirmed live listing/schema at
   `day=2026-07-22` matches the audit exactly) but was not committed — it hardcoded `chain="KALSHI_PERP"` per the
   pre-discovery understanding and would need re-deriving once step 3 lands.

## Resolution (2026-08-21)

**Operator ruled: KALSHI-PERP is not a chain.** The live manifest's real capture history (`chain=""` on 100% of
every real row) was right; `perp_funding_handler.py`'s hardcoded `chain="KALSHI_PERP"` workaround was wrong. Scope
extended to POLYMARKET-PERP by the identical reasoning already documented in that same module's docstring (both
CFTC-regulated, zero underlying blockchain) — not extended to HYPERLIQUID (a real L1, architecturally different; its
own observed `chain=""` in production is a separate, not-yet-ruled-on finding, noted below).

**Code fix shipped**: `market-tick-data-service@f7cdd18b21`.
- `_defi_manifest.py`: added an explicit `_CHAINLESS_VENUES = frozenset({"KALSHI-PERP", "POLYMARKET-PERP"})`
  allowlist; `_build_row_key` now accepts a blank `chain` for exactly these two venues, raising `BlankChainError`
  for every other (still chain-bound) DeFi-family venue exactly as before — the A4-full invariant is narrowed, not
  weakened.
- `perp_funding_handler.py`: removed the `kalshi_perp`/`polymarket_perp` entries from `_chain_map` (both now fall
  through to `chain=""` via `.get(protocol, "")`); rewrote the misleading 2026-07-30 "load-bearing workaround"
  comment.
- `tests/unit/test_perp_funding_handler.py`: updated the one assertion that hardcoded the old wrong value.
- Full `quality-gates.sh` green (exit 0) both before and after a same-day sports-MVP registry fix (below) had to be
  folded in to get a clean re-gate.
- Codex updated: `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi" now
  documents the chainless-venue pattern and the `_CHAINLESS_VENUES` allowlist as the sanctioned mechanism for any
  future chainless CeFi venue piggy-backing on this recorder.

**Unrelated pre-existing blocker found + fixed in the same ship** (needed for `quickmerge`'s full re-gate to pass at
all, zero relation to the chain question): a same-day, legitimate operator ruling
(`sports_bookmaker_roster_classification_2026_08_21.md`) retired 6 SPORTS venues (BETMGM/BETOPENLY/BETWAY/NOVIG/
ONEXBET/PROPHETX) from UAC's live registry; `market-tick-data-service`'s hand-listed `_SPORTS_MVP_SHARDS` shadow
constant (`scripts/pipeline_e2e_check.py`) and two dependent hardcoded shard-count assertions hadn't been re-pinned
yet. Fixed in the same commit (re-pinned the set + counts 31→25 / 39→33), verified against the live UAC registry
state, not guessed.

**Surprise finding #1 fully resolved — the historical re-emit itself turned out to already be complete.** A live,
full-window (not sample-day) query of the CEFI manifest for `(venue=KALSHI-PERP, data_type=perp_funding)` across the
entire 2026-05-29..2026-07-25 window found **58/58 days present, zero missing, chain="" throughout** (53 `captured` +
5 `empty_confirmed` for the pre-real-data 2026-05-29..2026-06-02 edge; the 3 originally-flagged "zero-object" gap
days 2026-07-17/20/21 are ALSO `captured` with real row_count=39 — some undocumented process, evidently more
thorough than the original stale-DEFI-path-only scope audit, already filled them). The CEFI-path GCS objects are
likewise already fully present for the sample day checked. **The original 567-row re-emit this issue blocked never
needed to run in this session — it was already done, by an unidentified prior process, before this investigation
started.** Origin still unknown; not chased further since the outcome (complete, correct, chain="" throughout) is
independently verified and the code fix now makes that state self-consistent with the codebase going forward too.

**Not investigated / left open (separate, smaller, not blocking)**: the deployment-drift question in the original
"Not investigated further" section below (whether the previously-deployed MTDS build was behind `fb32fb65`) no longer
needs resolving — the code fix supersedes it either way. HYPERLIQUID's own observed `chain=""` in production
(un-ruled-on) was initially left as only a code comment + this note, not a tracked follow-up — a hard-rule violation
(prose-only follow-up) caught in review. **Filed properly 2026-08-21**:
`issues/defi_cefi_hyperliquid_perp_funding_manifest_chain_contradiction_2026_08_21.md`, with a tracked `- [ ]` todo.

## Progress Log

- **2026-08-21**: Discovered while executing `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s last open todo.
  Filed this doc; did not write to production; did not flip the plan todo; did not archive the plan (it still had
  one genuinely-open item, then blocked on this).
- **2026-08-21 (resolution)**: Operator ruled on the chain-convention question. Shipped the code fix
  (`market-tick-data-service@f7cdd18b21`, bundled with an unrelated same-day sports-MVP registry re-pin needed for a
  clean re-gate), updated codex, and found via a full-window live query that the historical re-emit this issue
  blocked was already complete (58/58 days, chain="" throughout) before this session started. Flipped
  `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s last open todo (all 23 now done). Archival of that plan itself
  is owned by its own machine-gated finalize plan, now unblocked — not done in this session. Status: resolved.
