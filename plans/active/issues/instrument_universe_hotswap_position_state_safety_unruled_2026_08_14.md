---
doc_type: issue
title:
  Live instrument-universe hot-swap position-state safety is still unruled — split off from the now-resolved
  strategy-config-hot-reload guard doc
summary: >-
  `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` (archived 2026-08-14, `strategy-service@c688512912`) closed
  the STRATEGY-CONFIG half of its original A/B/C decision — a safe-field allow-list + `UnsafeConfigChangeError` now
  guards `enabled_strategies` changes. That guard is strategies-only. The doc's OTHER, separate concern — "Underlying
  instruments = NO (position-state continuity is broken; restart required)" in
  `/codex/04-architecture/live-strategy-config-hot-reload.md`'s table, contradicted by `_on_instruments_reload()`
  hot-swapping `_active_instruments` and fanning out `INSTRUMENT_UNIVERSE_CHANGED` live, no restart, no error — was
  never covered by that ruling and has no guard today. The codex doc's own "Underlying instruments" row is still marked
  `⚠️ CONTRADICTED, unenforced`. Split into its own doc so this genuine judgment call (is the live hot-swap actually
  position-state-safe, or does it need the same enforced/restart-required treatment) does not silently evaporate now
  that the parent doc is archived — this doc exists specifically to keep it a tracked `- [ ]` todo per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [strategy, live-trading, hot-reload, config, ssot-contradiction, safety, instrument-universe]
related:
  [
    /plans/archive/2026_08/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
  ]
created: "2026-08-14"
author: claude-agent
parent_epic: security_and_cross_cutting_master
priority: P2
source: >-
  Split off during the cross-cutting satellite AO batch13b finalize plan's todo-2 archival pass (review, slot 20,
  2026-08-14) — the parent doc's own instrument-universe concern was prose-only after its sole tracked todo (the
  strategy-config guard) closed, which would have left the concern untracked once the parent archived.
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: needs-decision
depends_on: []
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    strategy-service/strategy_service/config_reloaders.py,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
  ]
---

# Live instrument-universe hot-swap position-state safety — still unruled

## What I found

`strategy-service/strategy_service/config_reloaders.py`'s `_on_instruments_reload()` atomically swaps
`_active_instruments`, computes an added/removed delta, and notifies strategy engines via `INSTRUMENT_UNIVERSE_CHANGED`
— an unconditional live hot-swap with no restart and no error path. The codex SSOT
(`/codex/04-architecture/live-strategy-config-hot-reload.md`) documents this row as **⚠️ CONTRADICTED, unenforced**: the
design historically called this unsafe for position-state continuity ("restart required"), but the shipped code does it
live. The 2026-08-12 operator ruling (option A) that closed the sibling strategy-config guard question did not address
this — it scoped explicitly to `enabled_strategies`/strategy-archetype changes (`SAFE_STRATEGY_RELOAD_FIELDS`), not the
instruments domain.

## Why it matters

Same two readings as the parent doc originally posed, now narrowed to just the instruments question:

1. The hot-swap is a genuine live-trading position-state-continuity hazard and needs the same enforced/restart-required
   guard the strategies domain just got.
2. The hot-swap is intentional and safe (the delta-callback machinery reads as deliberately built for it), and the codex
   doc's "restart required" row is simply stale and should be corrected to match shipped behavior.

Left unruled, the codex SSOT keeps contradicting the shipped code on a live-trading-safety-relevant claim.

## Decision needed

- **A** — Extend the safe-field-allow-list pattern to the instruments domain: gate `_on_instruments_reload()` so an
  unsafe instrument-universe change is rejected (mirrors `strategy-service@c688512912`'s strategies-domain shape).
- **B** — Confirm the hot-swap is intentional/safe and correct the codex "Underlying instruments" row from
  `NO`/`restart required` to `Yes` with a note on why continuity isn't actually broken.

## Follow-ups

- [ ] [OPERATOR] P2. Rule A vs B above for live instrument-universe hot-swap position-state safety. Once ruled, either
      implement the guard in `strategy-service/strategy_service/config_reloaders.py` (option A) or correct
      `/codex/04-architecture/live-strategy-config-hot-reload.md`'s "Underlying instruments" row (option B).

## Progress Log

- **2026-08-14 (slot-20, review, `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13_finalize.md` todo 2)**: split
  off from `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` at archival time so this genuine unresolved
  judgment call stays a tracked todo instead of evaporating as prose in the archived parent.
- **context-scout 2026-08-17**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:5e6b7fed4d4c0336]: KEEP-NA, valid -- 1 open todo confirmed via grep, matches inventory. Sole item is explicitly [OPERATOR]-tagged: rule A (extend the strategy-config safe-field-allow-list guard pattern to the instruments domain) vs B (confirm the live hot-swap is intentional/safe and correct the codex SSOT's stale 'restart required' row) for live instrument-universe hot-swap position-state continuity safety. This is a genuine, unresolved, live-trading-safety judgment call the doc's own frontmatter frames as drift_direction: needs-decision, split off deliberately from an archived parent doc specifically so it would not silently evaporate. No prior ruling exists in this doc's own text to cite -- the question is live and open.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).
