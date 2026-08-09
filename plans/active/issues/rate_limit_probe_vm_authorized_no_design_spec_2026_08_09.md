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
related: [infra_capture_and_devops_leftovers_2026_07_06]
created: 2026-08-09
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
author: slot-9 (infra)
source: ["plans/active/infra_capture_and_devops_leftovers_2026_07_06.md"]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
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

- [ ] [OPERATOR] P2. Supply the missing rate-limit-probe design spec (target vendor/endpoint, request pattern,
      disposable-IP VM provisioning mechanism, success/stop criteria, teardown) — see "Recommended decision" above. Once
      supplied, the parent todo in `infra_capture_and_devops_leftovers_2026_07_06.md` can be re-scoped and dispatched.
      (repo: unified-trading-pm)
