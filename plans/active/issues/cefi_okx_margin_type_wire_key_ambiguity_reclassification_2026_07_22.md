---
doc_type: issue
title: >-
  OKX-FUTURES/OKX-SWAP margin_type wire-key ambiguity may be a stale mislabel artifact, not a real ambiguity —
  contradicts the shipped dedup docstring's own classification, needs operator review
summary: >-
  A dispatched workflow investigating the residual ~216 ambiguous CeFi wire-keys (as a side-track of the
  cefi_consolidated_closeout_2026_07_18 migration) found that 75 of the 216 keys (70 OKX-FUTURES dated-future groups +
  all 5 OKX-SWAP perpetual groups) are a linear-vs-inverse margin_type collision on the same bare wire symbol. The
  shipped `_dedup_cefi_expiry_off_by_one()` docstring in `instruments-service/scripts/build_instrument_catalogue.py`
  (commit 9956c36a, 2026-07-22) explicitly classifies this exact shape as "a REAL, different ambiguity ... correctly
  fail the strict checks ... stay excluded exactly as today." The investigating agent found zero-exception evidence
  across all 75 pairs that this is instead a STALE ARTIFACT of a documented, already-fixed historical bug: prior to
  commit dated 2026-07-09 (per `instruments_service/reference_data/adapters/cefi/tardis/parsing.py`'s
  `_infer_margin_type()` docstring), OKX-SWAP/OKX-FUTURES bare (no `_UM`/`_CM` infix) wire symbols were unconditionally
  mislabeled the OPPOSITE of their true margin type. In every one of the 75 groups, the row whose margin_type matches
  TODAY's `_infer_margin_type()` output is also the row whose expiry (where applicable) matches the wire-embedded date —
  a clean double-correlation, not a coincidence. If this reclassification is correct, margin_type is not a genuine
  identity axis for these rows and a corrected dedup rule should collapse them (keeping the row matching today's correct
  classifier); if it is wrong, real distinct linear/inverse products would be silently merged into one, which is a
  substantive economic-field violation, not a housekeeping fix.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, margin-type, wire-key-ambiguity, ssot-contradiction, dedup, operator-review-required]
related: [mtds_rule11_defi_shard_count_stale_baseline_2026_07_22.md]
created: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced by a workflow dispatched from cefi_consolidated_closeout_2026_07_18.md's deferred-work item 4 (residual
    ambiguous CeFi wire-keys); the workflow's OKX investigation + implementation + verify agents all independently
    flagged this as a big finding (SSOT contradiction) rather than silently overriding the shipped docstring or silently
    skipping it",
  ]
resolved_by:
locked_by:
---

# OKX-FUTURES/OKX-SWAP margin_type wire-key collision: real ambiguity, or stale mislabel artifact?

## The contradiction

`instruments-service/scripts/build_instrument_catalogue.py`, function `_dedup_cefi_expiry_off_by_one()` (docstring,
commit `9956c36a`, dated 2026-07-22), explicitly states the linear-vs-inverse OKX-SWAP/OKX-FUTURES/BITGET-FUTURES
perp-clash shape is:

> "a genuinely different margin_type/base_asset under the same wire symbol ... a REAL, different ambiguity ... correctly
> fail the strict checks ... stay excluded exactly as today."

A workflow dispatched 2026-07-22 (this session) to investigate the residual ~216 ambiguous CeFi wire-keys re-examined
this exact shape for OKX-FUTURES/OKX-SWAP specifically (not BITGET-FUTURES — see the separate BITGET-FUTURES finding
below, which is NOT in dispute) and found evidence pointing the other way.

## Evidence for "stale artifact, not real ambiguity"

- `instruments_service/reference_data/adapters/cefi/tardis/parsing.py`'s `_infer_margin_type()` (~lines 439-542) carries
  its own docstring documenting a historical bug: "Previously BACKWARDS ... every real OKX-SWAP/OKX-FUTURES derivative
  was mislabeled the opposite of its true margin type," live-verified 2026-07-09 against OKX's public
  `/api/v5/public/instruments` endpoint (a bare USD-quoted symbol with no `_UM`/`_CM` infix is unconditionally inverse —
  0 of 416 real SWAP rows show a genuine bare-symbol linear product).
- Since margin_type is now a pure deterministic function of `raw_symbol`, two different margin_type values for the
  IDENTICAL raw_symbol in the all-history rolled-up catalogue can only mean one label is a stale pre-fix artifact — not
  two really-different venue products sharing one wire spelling.
- The investigating agent verified this holds with **zero exceptions across all 75 pairs** (70 OKX-FUTURES + 5
  OKX-SWAP): in every case, the row whose margin_type matches today's `_infer_margin_type()` output is _also_ the row
  whose expiry (where applicable) matches the wire-embedded date — an independent double-correlation, not asserted from
  one signal alone.
- Sample (full data in the workflow journal, `wf_2550fc3e-f59`, `investigate:okx` agent result):
  `OKX-SWAP raw_symbol='TRX-USD-SWAP'` → `OKX-SWAP:PERPETUAL:TRX-USD` (margin_type=linear) vs
  `OKX-SWAP:PERPETUAL:TRX-USD@INV` (margin_type=inverse) — even `available_to` matches between the two rows; only
  `margin_type` + `instrument_id` differ.

## Why this is NOT settled and needs operator/team review, not a unilateral fix

- The investigating agent could not independently verify OKX's historical (pre-2026, especially 2019-2020, when most of
  these rows originate) symbol/margin convention beyond `parsing.py`'s 2026-07-09 live evidence, which reflects OKX's
  _current_ API behavior, not a historical audit.
- `margin_type` is a substantive economic/identity field (linear vs. inverse contracts have different settlement
  currencies and risk profiles), unlike `expiry`/`available_to` which are housekeeping timestamps the shipped DERIBIT
  fix already safely ignores.
- A wrong reclassification here would silently merge two real, differently-lifecycled financial instruments into one
  canonical ID — a correctness bug, not a data-hygiene one. (Contrast: BYBIT's superficially similar
  `BTCUSD`/`ETHUSD`/`XRPUSD` PERPETUAL collision, investigated in the same workflow, was confirmed to be **two genuinely
  distinct real products** — a closed 2019-2020 linear market and a separate still-active inverse market — correctly
  excluded. Not every margin_type collision in this dataset is the same root cause.)
- The shipped code was NOT changed to act on this: the same workflow's implementation agent deliberately left OKX-SWAP
  (5/5) and OKX-FUTURES sub-pattern B (70/146) untouched, and updated the docstring to record the open question rather
  than silently overriding or silently skipping it. Verified via
  `git show bf5322bb9:scripts/build_instrument_catalogue.py`.

## What is NOT in dispute (already correctly excluded, do not conflate)

- BITGET-FUTURES's 18 groups (separate investigation, same workflow): confirmed a **different**, but analogous, stale
  pre-fix margin_type mislabel (commit `75bdf02de3741d789be4968f6f08d44f9c31c54d`, 2026-07-14) — but flagged there as
  `fixable: false` too, for the same reason (needs an explicit widen-the-ignore-list decision, not folded silently into
  the existing DERIBIT-shaped helper). This is a closely related but textually distinct finding; treat separately
  if/when picked up.
- BYBIT's 3 PERPETUAL groups (BTCUSD/ETHUSD/XRPUSD): confirmed two genuinely distinct real products, correctly excluded
  — not part of this question.

## Recommended next step

Operator/team decision needed on: is the "REAL, different ambiguity" classification in the current shipped
`_dedup_cefi_expiry_off_by_one()` docstring correct, or should it be corrected to a stale-artifact classification for
OKX-SWAP (5) + OKX-FUTURES sub-pattern B (70) — and, if corrected, should BITGET-FUTURES's analogous 18 be folded into
the same explicit-review decision? If confirmed a stale artifact, the fix is straightforward (widen the ignore-list to
include `margin_type` for this specific shape, tie-break using the already-shipped/live-verified `_infer_margin_type()`
as the authority) and was already sketched by the investigating agent (see workflow journal). Do **not** implement
without explicit sign-off — this is a financial-instrument-identity decision, not a housekeeping fix.

## Provenance

Full investigation, implementation, and adversarial-verify detail: workflow run `wf_2550fc3e-f59`
(`instruments-service/scripts/build_instrument_catalogue.py`), journal at
`~/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/6acb923a-160e-4747-b590-8f035b41ef6c/subagents/workflows/wf_2550fc3e-f59/journal.jsonl`.
The unrelated, already-shipped portion of that same workflow (BINANCE-DELIVERY/BINANCE-FUTURES/KRAKEN-FUTURES fully,
OKX-FUTURES sub-pattern A partially — 84/216 residual keys collapsed) landed at `instruments-service@bf5322bb9`.
