---
doc_type: issue
title: "TradFi /autonomous session (2026-07-25) — queued operator decisions"
summary: >-
  Operator dispatched an 8-hour /autonomous session to resume tradfi_consolidated_closeout_2026_07_18.md and its 3
  children, with explicit instruction to queue genuine operator-decision items in writing rather than block on them
  (operator was leaving the desk). This doc is that queue. Each item below is something this session found that is
  either an explicit pre-existing BLOCKED-OPERATOR-DECISION in the source plans, or a new judgment call this session
  surfaced but did not decide unilaterally. Everything else the session COULD decide from documented intent, it did —
  see the 3 tradfi plan docs' Progress Log sections for the executed work.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, operator-decision, autonomous-session, canonicalisation, ice, chain-bundle]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_manifest_content_recovery_completion_2026_07_24,
    tradfi_backfill_throughput_followups_2026_07_24,
    tradfi_phase_d_terminal_gate_2026_07_24,
    tradfi_chain_bundle_sampler_root_mismatch_2026_07_23,
  ]
created: 2026-07-25
parent_epic: tradfi_master
priority: P1
source:
  "Operator, 2026-07-25 — dispatched /autonomous with an explicit instruction to keep working for up to 8 hours and
  queue any genuinely operator-owned decisions in writing (structured, answerable async) rather than block waiting for a
  synchronous answer, since the operator was stepping away from the desk."
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
drift_direction: none
depends_on: []
---

# TradFi /autonomous session (2026-07-25) — queued operator decisions

> Read this doc top-to-bottom when you're back. Nothing below blocked the session's other work — everything unblocked
> kept moving in parallel (see the 3 tradfi plan docs' Progress Logs for what shipped). These are the items that are
> genuinely yours to decide.

## 1. ICE qualifier variants — population is much bigger than previously known [RECOMMEND OPTION A]

**Pre-existing decision, not new** — this was already flagged `BLOCKED-OPERATOR-DECISION` in
`tradfi_manifest_content_recovery_completion_2026_07_24.md` before this session started. What's new: this session's live
catalogue + by-day-corpus full-sweep (2026-07-25) measured the REAL scale for the first time, and it is much larger than
the catalogue-only estimate the plan had been citing.

- Catalogue (`prod/catalog.parquet`): 1,063 ICE-qualifier-variant rows.
- Per-day corpus (`instrument_availability/by_date/`, 27,142 files, full sweep): **269,520 ICE-qualifier-variant rows**
  — 254x the catalogue-only figure, and the dominant share (99%) of that surface's entire 272,616-row quarantine
  population.

The defect: the classifier + current writer emit `ICE:FUTURE:BRN_Z-USD@LIN-...` with banned characters (`_`, `!`)
because Databento's ICE symbols carry a qualifier suffix (`BRN_Z`/`BRN!`/`BRN_MD1`) that `EXCHANGE_CODE_TO_NAME` only
maps for the bare root. ICE is NOT in the tradfi MVP universe, so none of this blocks MVP backfill readiness — but
269,520 rows is a real, now-quantified data-quality gap worth a decision rather than indefinite quarantine.

**Options:**

- **A (recommended — matches the existing plan's own recommendation): qualifier-normalize + map the base root.** Strip
  the qualifier suffix, resolve via the existing base-root map, keep the qualifier as separate metadata if needed. Fixes
  the defect at the source; largest population addressed.
- B: Accept `_qualifier` as a permitted id-shape exception for ICE only, relax the canonical-shape gate for this one
  venue.
- C: Leave ICE permanently quarantined (defer indefinitely) — cheapest, but leaves 269,520 rows honestly-absent from
  every canonical read/count for a venue that's a real (if non-MVP) part of the data estate.
- Other: your call.

## 2. Chain-manifest recovery — retire-phase 50,520-row `--apply` still needs your review

**Pre-existing, unchanged since 2026-07-22/23** — `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s
P1-OPERATOR-REVIEW todo. The register phase (1,545 rows) is done and durability-reverified by this session (still
`captured` in a fresh live read). The retire phase — dropping 50,520 now-superseded raw `futures_chain`/ `options_chain`
manifest rows via a single in-place-CAS whole-index REPLACE — was deliberately never `--apply`'d, per direct prior
operator instruction ("do NOT --apply retire without further review").

**This session did NOT re-run the retire dry-run** (out of scope for what was actioned this pass — the session focused
on the casing/catalogue/phantom items instead). The plan's own text already warns the candidate list goes stale after "a
day or two" — **whoever applies this must re-run the `--retire` dry-run first** to get a fresh candidate list before
deciding.

**Options:** A: review + approve as-is once re-dry-run confirms the list is materially unchanged. B: review + request
changes. C: defer further. Other.

## 3. Chain-bundle canonical-root → raw-Databento-symbol reverse translation — `EXCHANGE_CODE_TO_NAME` SSOT contradiction

**Pre-existing, blocking the Phase-D MVP backfill readiness gate** —
`tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` §4. The chain-bundle sampler passes a now-canonical
`underlying` (e.g. `"AUD"`) to CME/GLBX.MDP3, whose curated symbol list expects the raw exchange code (`"6A"`) — fixing
this needs resolving a contradiction between two UAC files over what `EXCHANGE_CODE_TO_NAME` should say. This session
did not touch it (not re-investigated this pass; no new information beyond what's already in that issue doc). It remains
the sole named blocker on `tradfi_phase_d_terminal_gate_2026_07_24.md`'s P0 MVP backfill readiness todo — until it's
resolved (or you explicitly accept current evidence as sufficient), that gate stays blocked.

**Options:** A: resolve the SSOT contradiction (read the issue doc §4 for the two conflicting files, pick one). B:
explicitly accept the current Phase-D evidence as sufficient and unblock the MVP backfill gate without fixing this.
Other.

## 4. Legacy-twin bucket deletes — still a hard stop, not re-raised, just confirming it's still parked correctly

`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` — `BLOCKED-OPERATOR-DECISION`, Ikenna's migration sign-off
gates this. Untouched this session, correctly (never autonomous per the workspace HARD RULE). No action needed from you
unless you want to move on it; just confirming this session didn't touch it.

## What this session DID decide from documented intent (informational, not asking)

- The manifest `instrument_type` casing residual (45,681 rows re-drifted post-2026-07-22 CAS run) was fixed per the
  already-RULED D1/casing-directive UPPERCASE target — no new decision needed, just execution.
- The catalogue Surface-A re-sweep (both `prod/catalog.parquet` and the by-day corpus) was executed per the
  already-decided `-USD@LIN` target shape from the 2026-07-18 operator ruling.
- The CF-11 phantom `attempted_failed` retirement routed rows to `EXPECTED_INSTRUMENT_NOT_LISTED` /
  `EXPECTED_SOURCE_DELIVERY_LAG` per the already-fixed live emitter's own convention (BLK-d385496b answer B, 2026-06-28)
  — no new taxonomy decision, just applying the existing one to historical residue.

## Open todo

- [ ] [PM] P2. Once you've answered items 1-3 above, record the decision inline in this doc (flip to resolved) and
      propagate into the relevant plan doc(s)' todos per the standing "plan references, doesn't duplicate" rule.
