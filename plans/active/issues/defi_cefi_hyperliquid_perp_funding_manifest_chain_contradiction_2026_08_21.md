---
doc_type: issue
title: HYPERLIQUID cefi perp_funding manifest rows carry chain="" while the current code hardcodes chain="HYPERLIQUID" — same contradiction class as the resolved KALSHI-PERP finding, HYPERLIQUID side not yet ruled on
summary: >-
  While investigating (and resolving) `issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md`
  (KALSHI-PERP/POLYMARKET-PERP), a live CEFI manifest query for comparison also checked HYPERLIQUID's own
  `perp_funding` rows for the same contradiction pattern. Found it present there too: every one of 979 real
  `captured` `(venue=HYPERLIQUID, data_type=perp_funding)` manifest rows (spanning dates through 2026-08-19, the
  most recent checked) carries `chain=""`, while `perp_funding_handler.py::_run_process`'s `_chain_map` (current
  HEAD, unchanged by `market-tick-data-service@f7cdd18b21` which fixed the KALSHI-PERP/POLYMARKET-PERP side only)
  still hardcodes `chain="HYPERLIQUID"` for the `hyperliquid` protocol — if that code path is really what writes
  these rows, they should show `chain="HYPERLIQUID"`, not blank. This is NOT the same question as "should
  HYPERLIQUID be in `_CHAINLESS_VENUES`" (settled: no — HYPERLIQUID is a real L1, architecturally different from
  KALSHI-PERP/POLYMARKET-PERP's zero-blockchain CFTC-regulated venues, already documented in
  `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi"). It is the SAME
  open empirical question the KALSHI-PERP finding started from, just never answered for this venue: why does live
  production data contradict the code's own enforced value, and which one is actually correct going forward.
status: open
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [defi, cefi, hyperliquid, manifest, chain-axis, data-correctness]
related:
  [
    /plans/archive/issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md,
    /plans/archive/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineer
drift_direction: unknown
depends_on: []
resolved_by:
locked_by:
source: >-
  Discovered live 2026-08-21 as a side-observation while investigating and resolving
  defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md — checked HYPERLIQUID for the same
  pattern out of caution before scoping the fix to only KALSHI-PERP/POLYMARKET-PERP, found it present there too, but
  did not chase it further (out of the operator ruling's scope, and not blocking any open todo at the time). Filed
  properly as its own tracked issue 2026-08-21 after a coordinator review caught that the finding had only been
  left as a code comment + resolved-doc footnote, not a tracked `- [ ]` todo, per this workspace's hard rule against
  prose-only follow-ups.
context_scope:
  [
    /plans/archive/issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
  ]
---

# HYPERLIQUID cefi perp_funding manifest chain contradiction

## What was measured (live, 2026-08-21, re-verified same day after this doc's initial draft)

Current HEAD (`market-tick-data-service@f7cdd18b`, i.e. one commit past the KALSHI-PERP fix
`f7cdd18b21`) still has, in `perp_funding_handler.py::_run_process`:

```python
_chain_map = {
    "hyperliquid": "HYPERLIQUID",
}
chain_for_manifest = _chain_map.get(protocol, "")
```

— meaning every `record_captured`/`record_zero_rows`/`record_failed` call for the `hyperliquid` protocol passes
`chain="HYPERLIQUID"` (non-blank), which `_defi_manifest.py::_build_row_key` accepts unconditionally for this venue
(it's not in `_CHAINLESS_VENUES`, and `"HYPERLIQUID"` is non-blank so `BlankChainError` never fires either way).

A live query of the CEFI manifest (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`)
filtered to `venue="HYPERLIQUID", data_type="perp_funding", capture_status="captured"` found **979 real captured
rows, 100% carrying `chain=""`** — zero rows with `chain="HYPERLIQUID"` — spanning dates through 2026-08-19 (the
most recent sampled). Same shape as the KALSHI-PERP finding before its resolution: the code's own enforced/intended
value and the live data disagree completely, for every row, with no partial/transitional mix.

## Why this is a genuinely open question, not a settled one

`/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi" (updated as part of the
KALSHI-PERP resolution) correctly documents that HYPERLIQUID is architecturally chain-bound (a real L1) and was
deliberately NOT added to `_CHAINLESS_VENUES` — that scoping decision is settled and stays settled here. **This
doc is about a different question**: given the code enforces `chain="HYPERLIQUID"`, why does 100% of live
production data show `chain=""` instead? Candidate explanations (none confirmed):

1. **Deployment drift** — the actually-deployed MTDS build differs from this git checkout's HEAD (the same
   candidate explanation raised, but never confirmed, in the original KALSHI-PERP investigation).
2. **A different writer** — some other, unlocated code path (not `perp_funding_handler.py::_run_process`) is what
   actually produces these rows, using the plain `ManifestWriter` directly rather than `DefiManifestRecorder`
   (bypassing the `_chain_map` entirely). A prior search for a second KALSHI-PERP writer came up empty (checked
   `market_tick_data_service/live/`, `kalshi_perp_ws.py`, and `scripts/` for a restamp script) — not re-run for
   HYPERLIQUID specifically.
3. **The recorded convention itself may need revisiting for THIS handler's perp_funding shard specifically** —
   possible (not confirmed) that `perp_funding_handler.py`'s own perp_funding capture, as distinct from
   HYPERLIQUID's other cefi data (e.g. `derivative_ticker` via `onchain_perp_batch_handler.py`, which the
   `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` precedent already blanked HYPERLIQUID's chain for), was
   never meant to be chain-scoped either — mirroring the exact ruling KALSHI-PERP just received, but for a
   different underlying reason (not "no blockchain," but "this specific shard's chain axis is redundant/wrong for
   this venue too").

Not resolved here. No production write, no code change, no operator ruling requested/assumed — this doc records
the measured contradiction only.

## Recommended next step

- [ ] [DIAG] P2. **Root-cause the HYPERLIQUID `perp_funding` chain contradiction.** Determine which of the three
      candidate explanations above (or another) actually explains why live `chain=""` diverges from the code's
      enforced `chain="HYPERLIQUID"`, then either (a) fix the code to match the correct value (mirroring the
      KALSHI-PERP `_CHAINLESS_VENUES`-carve-out pattern if the ruling comes back the same way, or a different fix if
      it's deployment drift / a second writer), or (b) confirm `chain="HYPERLIQUID"` genuinely is correct and get an
      explicit ruling on restamping the 979 existing `chain=""` rows instead. Repo: market-tick-data-service. Source:
      this doc. **Done when**: the root cause is identified with evidence (not guessed), the correct chain
      convention for this exact shard is confirmed (via code investigation and/or an explicit operator ruling if the
      evidence is ambiguous), any resulting code/data fix ships with `quality-gates.sh` green, and this doc's status
      flips to resolved.

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi" (the settled
  asset_group + `_CHAINLESS_VENUES` scoping — background only, not what this doc is investigating)

## Progress Log

- **2026-08-21**: Filed after a coordinator review of the KALSHI-PERP resolution caught that this side-finding had
  only been left as a code comment + a footnote in the resolved issue doc's Resolution section, not a tracked
  `- [ ]` todo. Re-verified the measurement live before filing (979 captured rows, 100% `chain=""`, current HEAD
  still hardcodes `chain="HYPERLIQUID"`) rather than trusting the earlier same-day observation unchecked.
