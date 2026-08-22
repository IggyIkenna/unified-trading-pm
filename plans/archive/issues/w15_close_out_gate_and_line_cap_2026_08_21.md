---
doc_type: issue
title: W15 venue-adaptor security audit — close-out gate not met, plan doc at its line-cap
summary: >-
  The W15 plan's close-out todo ("confirm the epic's W15 section reflects this plan's real landed state once
  every todo above is done or explicitly re-scoped") is not yet ripe -- 11 P0/HIGH items remain genuinely open
  with no completion or deferral reasoning. Separately, the plan doc itself is now sitting exactly at the
  1000-line hard cap (check_line_caps.sh), so the NEXT slot that lands a fix + Progress Log entry on this file
  will hit the same pre-commit rejection this session hit.
status: resolved
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
resolved_by: unified-trading-pm@3dfe684715
locked_by:
last_updated: 2026-08-21 # status flipped resolved -- both todos done: the line-cap split landed
  (unified-trading-pm@ba4f18028e), and the gate re-check todo was genuinely performed (still NOT met,
  5 blockers remain down from 11) with ongoing tracking now living solely in the plan's own close-out
  todo per the concurrent slot-21 dedup pass -- archiving per check_archive_candidates.sh (0 open todos).
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

- [x] ✅ [AGENT] P1. Split `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` per the "Recommended
      decision" above once its open-todo count drops (fewer concurrent editors), or immediately if another slot
      hits the same `check_line_caps.sh` rejection first. (repo: unified-trading-pm) — unified-trading-pm@ba4f18028e
      + evidence: relocated the 17 Progress Log entries whose todo(s) were fully `[x]`-checked and had no bearing
      on any open todo, verbatim (mechanical `sed` line-range extraction), to new sibling
      `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md` (cross-linked via
      `related:` both ways); kept every entry still load-bearing for one of the 11 open todos (CCXT-CeFi audit,
      staking-remaining-group audit, perp/CLOB audit, native-REST audit, the slot-24 triage-sweep note, and the
      Orca/Raydium partial-fix entry); fixed all 12 dangling "see Progress Log entry below" pointers on checked
      todos whose target entry moved. Main plan doc: 1000 → 395 lines (well under the 500-line soft cap, not
      just the 1000-line hard cap); zero checkboxes lost (54 before and after); zero content deleted, only
      relocated. Landed while contention on the file was still active (another slot's concurrent edit was
      detected and reconciled mid-session) rather than waiting for it to quiet, since the file was still sitting
      at the hard cap blocking every other slot's fix/evidence entries.
- [x] ✅ [AGENT] P2. Once the 11 items listed under "What I found" are all done or explicitly re-scoped, re-run
      the close-out gate-check (`grep -n "^- \["` against the plan, cross-check the epic's W15 section is still
      accurate) and flip both close-out checkboxes. (repo: unified-trading-pm) — unified-trading-pm@3dfe684715
      + evidence: **Re-checked 2026-08-21 (slot 19), gate still NOT met**: 6 of the original 11 items were already
      done/re-scoped, and the sports-exchange audit phase (one of the 2 remaining unstarted phases) has now been
      completed (see the plan's own Progress Log for the full checklist writeup) — but that audit surfaced 3 new
      genuine P0 findings (tracked as new triage todos in the plan) plus the sports-unity phase is still fully
      unstarted, so the actual close-out checkboxes (this doc previously had none of its own — see the dedup note
      below — and the plan's) correctly stay `[ ]`. Current blocker count: 5 (4 new triage todos + the sports-unity
      audit phase), down from 11.
      **➡️ DUPLICATE OF** `/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`'s own
      close-out todo (2026-08-21 dedup pass, verified `status: active`, its close-out checkbox confirmed still `[ ]`
      per that plan's own 2026-08-21 Progress Log) — the same gate-check + checkbox-flip is tracked there. Checking
      this THIS todo off as resolved: the gate re-check the todo asked for has now genuinely been performed and its
      result recorded, and ongoing tracking of "is the gate met yet" continues in the plan's own close-out todo
      (the non-duplicate SSOT) rather than needing a second parallel tracker here. Re-dispatch a fresh gate-check
      there, not here, once the 5 remaining blockers clear.
