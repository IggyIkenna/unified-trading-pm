---
doc_type: codex-ssot
title: Plan Priority — Asset-Group Tier + CI/Audit Precedence + Issue Absorption
summary:
  SSOT for how `priority:` gets assigned/triaged going forward, not just a one-time resort — the asset-group tier
  ordering (cross-cutting > cefi > defi > sports > tradfi, with a billing-critical backfill carve-out for
  sports/tradfi); that CI escalations + daily/on-demand scheduled audit findings ALWAYS outrank the tier ordering (they
  can block the whole fleet, a tier ranking cannot); and that `plans/active/issues/*.md` docs must be actively diagnosed
  and absorbed into AO-dispatchable work, never left as passive undiagnosed prose. Operator ruling 2026-07-28 (Ikenna) —
  apply this to every NEW plan/issue's priority assignment, not only the one-time audit that produced it.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [priority, dispatch, orchestrator, plan-hygiene, ci, escalation]
related:
  [
    /codex/11-project-management/foundation-completion-gate-discipline.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/plan-hygiene.md,
    /codex/04-architecture/ci-alerting.md,
    plans/PLAN_FORMAT.md,
  ]
created: 2026-07-28
authoritative_for:
  [
    asset-group priority tier ordering,
    CI/audit-escalation precedence over tier ordering,
    issue-doc diagnose-and-absorb rule,
  ]
referenced_by: [CLAUDE.md § "Plans — format + authoring discipline", CLAUDE.md § "Governance + safety HARD RULES"]
owner:
last_reviewed: 2026-10-27
code_refs:
---

# Plan Priority — Asset-Group Tier + CI/Audit Precedence + Issue Absorption

> This is a STANDING policy, not a one-time cleanup. Every plan/issue authored, triaged, or re-prioritized from
> 2026-07-28 forward is assessed against this doc — the one-time resort of the then-active ~165-plan corpus that
> prompted this doc was the FIRST application of this rule, not a special exception to it.

## 1. Precedence order (highest first)

1. **CI escalations + daily/on-demand scheduled-audit findings.** A failing required CI check, a paged CI alert, or a
   finding from `/plan-reconcile`, `/ag-closeout-audit`, `/na-eligibility-audit`, `/plan-vintage-audit`, or the
   `run_hygiene_sweep.sh` cron ALWAYS outranks every asset-group tier below — a broken pipeline or an unresolved
   corpus-contradiction can block or misdirect ALL other work, so it is never just "P0 within its tier," it is ahead of
   tier entirely. See `/codex/04-architecture/ci-alerting.md` for the CI-alert routing this feeds from.
2. **Asset-group tier**: `cross-cutting` > `cefi` > `defi` > `sports` > `tradfi`. Rationale (operator ruling
   2026-07-28): cefi carries the funding-rate data that is the basis of the defi-basis carry strategy; defi-basis and
   staked-basis are the current top product priority; sports and tradfi are lower strategic priority EXCEPT —
3. **The sports/tradfi backfill carve-out**: within sports and tradfi specifically, work that is
   data-completion/backfill/manifest-canonicalisation/closeout-critical (the work that finishes the backfill and lets
   the paid vendor subscription be cancelled) stays elevated to P0/P1 despite the tier being deprioritized overall;
   downstream ML/strategy/UX work and plan-hygiene/AO-dispatch-batch satellites in those two tiers drop to P2/P3. This
   is NOT "sports/tradfi = always low" — it's "the specific thing that ends the subscription stays urgent, everything
   built on top of that data can wait."
4. **Within a tier, the granular pipeline-stage sequencing governs WHAT KIND of work ranks first** —
   `/codex/11-project-management/foundation-completion-gate-discipline.md`'s 2026-07-28 refinement: code changes →
   canonical migration/non-canonical-path removal → catalogue-rollup/manifest-consolidator verified working → smoke-test
   skills GREEN → backfill to 100% (zero `attempted_failed`, zero false `empty_confirmed`) → live+T+1 for batch, per
   asset_group; MDPS/features may develop concurrently on already-filled samples but don't reach their own 100%/GREEN
   until MTDS does; then ML (cefi + sports first) → strategy-service (defi-basis/staked-basis, including
   equity-perps/tokenized-stocks + NASDAQ-spot, plus cefi ML) → batch execution → live paper execution → real
   (live-money) execution last. That doc is the SSOT for this axis — this doc doesn't duplicate it, it composes with it:
   tier ordering picks WHICH asset_group, the foundation-gate doc picks WHAT STAGE within it.

## 2. Issues must be diagnosed and absorbed into the AO workflow — never left passive

A doc in `plans/active/issues/*.md` is not "done" by existing. Per this workspace's Findings-triage rule (CLAUDE.md §
"Findings triage"), every issue doc must resolve to one of:

- **Folded into an owning plan** as real `- [ ]` todos (never a prose mention — see
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2's todos-not-prose rule), then archived
  itself once folded, or
- **Its own AO-dispatchable scope** (`assigned_vm: planning`, bounded/deterministic per the dispatch-scope-eligibility
  rule) if it doesn't fit any existing plan, or
- **A genuinely operator-gated decision** (`BLOCKED-OPERATOR-DECISION`/`BLOCKED-CREDENTIALS`), which still needs the
  decision actively sought, not the issue doc left to age silently.

An issue doc that just sits in `plans/active/issues/` with no plan referencing it and no `assigned_vm: planning` scope
of its own is an orphan — exactly what `/ag-closeout-audit` exists to find, and exactly what this rule means to prevent
from accumulating in the first place. Diagnosing an issue means reading it enough to know WHICH of the three outcomes
above applies, not just triaging its severity label.

## 3. Applying this to a NEW plan/issue (not just the one-time resort)

When authoring a plan or triaging an issue: set `priority:` per precedence order § 1 (CI/audit finding first, else
tier + carve-out, else within-tier pipeline stage). When re-triaging an existing plan whose scope has shifted, the same
order applies — a plan doesn't keep an inherited priority once its actual content no longer matches why that priority
was assigned.

**No automated enforcement exists yet** — `regen_backlog_from_plan.py` dispatches strictly off the plan's literal `P<n>`
tag; it does not know this policy and cannot validate a plan's assigned priority against its asset_group/ content. Until
a QG script validates this (tracked as real follow-up work, not left as a prose aside — add it as a todo in whichever
plan owns backlog-tooling QG scripts when someone picks it up), correct application depends on whoever
authors/reprioritizes a plan actually reading this doc.
