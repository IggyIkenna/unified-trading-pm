---
doc_type: issue
title: W15 venue-adaptor security audit — close-out gate not met, plan doc at its line-cap
summary: >-
  The W15 plan's close-out todo ("confirm the epic's W15 section reflects this plan's real landed state once
  every todo above is done or explicitly re-scoped") is not yet ripe -- 11 P0/HIGH items remain genuinely open
  with no completion or deferral reasoning. Separately, the plan doc itself is now sitting exactly at the
  1000-line hard cap (check_line_caps.sh), so the NEXT slot that lands a fix + Progress Log entry on this file
  will hit the same pre-commit rejection this session hit.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [unified-trading-pm]
scope: [engineer]
tags: [w15, line-cap, plan-hygiene, close-out-gate]
related:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-21
author: claude-session-2026-08-21-slot-4
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md]
context_scope:
  [
    plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    plans/epics/system_readiness_master.md,
  ]
resolved_by:
locked_by:
---

# W15 venue-adaptor security audit — close-out gate not met, plan doc at its line-cap

## What I found

Dispatched to the W15 plan's close-out todo ("Confirm the epic's own W15 section reflects this plan's real
landed state once every todo above is done or explicitly re-scoped"). A full checkbox inventory
(`grep -n "^- \[" plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`) found the
gate is **not met**: genuinely open with no completion and no explicit deferral reasoning (distinct from the
already-legitimately-deferred Orca/Raydium, Aave/Morpho, Kamino, and staking-wiring P1/P2 follow-ups, which
each carry their own deferral reasoning in their todo text) —

- CCXT order-placement idempotency + fail-closed credential init (2 todos, P0/HIGH).
- Perp/CLOB hardening: order-boundary validation, slippage/expiry bounds, durable idempotency, plus the
  Pacifica live-enablement confirmation (4 todos, P0/HIGH).
- Native-REST hardening: nonce allocator, input validation/bounds, client-order-id preservation, Kraken
  envelope-parsing fail-closed (4 todos, P0/HIGH).
- The sibling close-out todo, "Post-phase codex audit" (1 todo, P0).
- Four full audit phases not yet started: yield-aggregator, TradFi gateway, sports exchange, sports unity
  (P1/P2 by the plan's own original phasing, so plausibly intentional sequencing, but still incomplete).

Synced the epic's W15 section (`/plans/epics/system_readiness_master.md`) to an accurate current summary
(8/12 audit phases done, the above list of what's still open) since it was previously a single stale generic
unchecked line with zero reference to the ~20 completed audit/fix todos already shipped.

Separately: attempting to add a Progress Log entry documenting the above to the plan doc itself hit
`check_line_caps.sh`'s pre-commit hard-fail — the file is at exactly 1000 lines (the plan hard cap), with
zero headroom. This is a real, imminent problem independent of my own edit: this plan has had 12+ slots
landing fixes with detailed Progress Log entries today (2026-08-21) alone, so the next slot to land ANY fix
here (there are 11 open P0 todos actively being worked) will hit the identical rejection.

## Why it matters

The close-out gate-check itself is normal, expected plan-lifecycle behavior — no action needed there beyond
what a future gate-check will re-verify (the exact blocking-item list above makes that re-check fast: grep
those specific items instead of re-reading the whole 1000-line file + full Progress Log again). The line-cap
exhaustion is the more urgent finding: it will block a live-capital-safety security-hardening fix from
shipping via the normal `quality-gates.sh` → `quickmerge`/`safe-doc-push` flow the moment it happens next, and
CLAUDE.md's cap enforcement gives no exception for "in-flight, still needs Progress Log room."

## Recommended decision

Split the plan doc once concurrent-editing activity on it quiets (splitting mid-heavy-contention risks
colliding with the 4+ todo-groups actively in flight right now): move Progress Log entries for already-`[x]`
-checked todos into a new sibling
`w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md` (cross-linked via
`related:` both ways), keeping the Todos section and only the still-open todos' own Progress Log entries in
the main file. Re-verify under the 500-line soft cap afterward, not just the 1000-line hard cap, so there's
real headroom for the 11 open todos' own eventual Progress Log entries.

## Todos

- [ ] [AGENT] P1. Split `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` per the "Recommended
      decision" above once its open-todo count drops (fewer concurrent editors), or immediately if another slot
      hits the same `check_line_caps.sh` rejection first. (repo: unified-trading-pm)
- [ ] [AGENT] P2. Once the 11 items listed under "What I found" are all done or explicitly re-scoped, re-run
      the close-out gate-check (`grep -n "^- \["` against the plan, cross-check the epic's W15 section is still
      accurate) and flip both close-out checkboxes. (repo: unified-trading-pm)
