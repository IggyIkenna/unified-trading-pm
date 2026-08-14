---
doc_type: issue
title: Rate-limit-probe VM — operator authorized the risk call, but no engineering spec was ever produced
summary:
  "The operator's 2026-08-06 ruling authorized the rate-limit-probe VM's risk-tolerance question (go ahead), but the
  todo's claim that a probe design already exists is false — no target vendor/endpoint, request pattern, disposable-IP
  provisioning mechanism, or success/stop/teardown criteria were found anywhere in the corpus. Escalated via /blocked
  (BLK-04a2a05a); operator ruling (relayed by main, 2026-08-09): file this gap, leave the parent checkbox open, do not
  invent a probe design. Standing pointer for whoever supplies the missing spec."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [infra, blocked, rate-limit-probe, disposable-ip, operator-decision]
related:
  [infra_capture_and_devops_leftovers_2026_07_06, /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-09
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
author: slot-9 (infra)
source: ["plans/active/infra_capture_and_devops_leftovers_2026_07_06.md"]
resolved_by:
locked_by:
archive_exempt: true
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/infra_capture_and_devops_leftovers_2026_07_06.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

## What I found

`plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`'s `[INFRA] P1` "rate-limit probe VM" todo carries a
2026-08-06 operator ruling — **"AUTHORIZED — proceed with the disposable-IP probe"** — resolving the reputational/ToS
risk-tolerance question the todo had been gated on since it was written. The todo's own text asserts "the probe design
is already stated as ready in this todo's own text; no further sign-off needed."

That claim does not hold up. I read the full todo plus every doc in the corpus that references this item
(`instruments_completion_tracker_2026_07_06.md`, `infra_capture_and_devops_leftovers_finalize_2026_07_25.md`,
`cross_cutting_consolidated_closeout_2026_07_25.md`, `issues/instruments_remaining_work_audit_2026_07_10.md`) and a
repo-wide grep for `rate_limit_probe`/`rate-limit-probe`. None of them name:

- Which vendor/endpoint the probe targets.
- What request pattern/rate the probe should drive (how aggressive, for how long).
- How the "disposable IP" is provisioned (new VM in a fresh region? ephemeral external IP flow? which cloud?).
- Success/stop criteria (what result answers the underlying question — e.g. "the vendor's stated per-IP rate limit is X
  req/s" — and when to abort).
- A teardown/cleanup step for the disposable resources afterward.

What exists is only the risk-tolerance ANSWER ("go ahead"), not an engineering SPEC to execute against.

## Why it matters

This todo describes deliberately, adversarially stress-testing a live third-party vendor's infrastructure from a
disposable IP — real reputational/ToS/abuse-detection exposure per the todo's own `why_operator_only` reasoning. The
infra craft's north-star is "never launch blind" (`unified-trading-pm/agents/infra.md`): launching a VM to execute an
unscoped adversarial probe — inventing the target vendor, request pattern, and stop criteria myself — would be worse
than declining, since a wrong guess here has external consequences (a vendor could rate-limit/ban a shared or
production-adjacent IP range, or read the traffic as abuse) that aren't easily reversible.

Escalated via `/blocked` (`BLK-04a2a05a`); operator ruling recorded 2026-08-09 (relayed via main): **option B — file
this issue doc, leave the todo's checkbox open pointing here, do not invent a probe design.** Confirmed this is not a
defer-to-avoid-work call — the missing spec is genuine, and if the probe is still wanted the operator can supply the
missing design specifics later, at which point it re-dispatches as concretely scoped work (option A stays available).

## Recommended decision

No further AO action on this todo until the operator (or main, on the operator's behalf) supplies:

1. Target vendor + endpoint.
2. Request pattern / rate / duration to drive.
3. Disposable-IP provisioning mechanism (cloud + region + teardown).
4. Success/stop criteria.

Once supplied, re-file as a normal `[INFRA]` execution todo (or update this doc + flip its status) and it can be
dispatched normally under the standard VM-launch observability rules (`vm-launcher-runbook.md` — no fire-and-forget,
STARTED <60s + progress + terminal state).

## Todos

- [x] ✅ [OPERATOR] P2. **RETIRED 2026-08-11** — operator confirmed the original motivating incident (Tardis
      rate-limiting) was already solved via a different mechanism: the 1-concurrent-VM hard cap
      (`tardis-concurrency-guard.sh`, 2026-07-16) plus larger boot disk to fix the burst-write bottleneck
      (`deployment-service@ac5d1660`, 2026-07-18). No probe design spec is needed — closed the parent todo in
      `infra_capture_and_devops_leftovers_2026_07_06.md` as won't-do rather than continuing to carry this ask. (repo:
      unified-trading-pm)

## Progress Log

- **2026-08-11** (operator decision, via main): retired — see the todo above. Marked `archive_exempt: true` rather than
  running the full corpus-wide archival ritual in the same pass; this doc has ~3 corpus referrers, genuinely
  0-open-todos/done, intentional terminal state. Revisit for a proper archive (banner + git mv + referrer fix) in a
  dedicated plan-hygiene pass.
- **context-scout 2026-08-14**: populated context_scope (2 entries).
