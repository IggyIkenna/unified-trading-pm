---
doc_type: plan
title: Commercial-model document set — conflict reconciliation and audience retargeting
summary: >-
  Reconciles the six client-facing documents under codex/14-customer-journeys/commercial-model/ against one another
  and against the codebase, with platform-external-api-walkthrough.html as the source of truth. Retargets the
  carve-out document to POD on the Elysium AM contract basis, tailors the architecture page to a basis and
  staked-basis client, merges the strategy-service walkthrough into the deep dive, and publishes five shareable
  artifacts. Carries the carve-out scope boundary that every downstream edit must respect.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, execution-service, strategy-service, unified-api-contracts, deployment-api]
scope: [engineer]
tags: [client-artefact, commercial-model, carve-out, elysium, pod, conflict-audit, presentation]
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/walkthrough_feedback_checkpoint_2026_08_21.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3
locked_by:
locked_since:
context_scope:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/02-data/honest-coverage-model.md,
  ]
supersedes:
superseded_by:
depends_on:
source: operator request 2026-08-22
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# Commercial-model document set — conflict reconciliation and audience retargeting

> **The single rule this plan exists to enforce**: the six documents may differ in audience, depth and scope. They
> must never state contradictory FACTS about the same thing. `platform-external-api-walkthrough.html` is the source
> of truth between documents; the codebase is the source of truth over all of them.

## The document set and what each one is for

| Document                                | Audience and purpose                                                                |
| --------------------------------------- | ----------------------------------------------------------------------------------- |
| `platform-external-api-walkthrough.html` | **SSOT.** Nick AI and any general deep-dive client. Broadest and most detailed.     |
| `platform-api-reference.html`           | API contracts and drilldown. Compact, endpoint-first.                               |
| `platform-architecture.html`            | Tailored to the basis and staked-basis client.                                      |
| `carveout-engineering.html`             | POD, on the Elysium AM contract basis. A deliberately restricted subset.            |
| `strategy-service-deep-dive.html`       | Contracts, configuration, integration points. Handed to an AI with the codebase.    |
| `ODUM_Elysium_Phase2_Update_2026-07-24.html` | **Frozen historical record.** Excluded from the audit. Leave its contents alone. |

`strategy-service-walkthrough.html` is being merged into the deep dive and then deleted.

## The carve-out boundary

Anchored on three things rather than on preference, because a boundary that follows from the agreement survives
scrutiny in a way that a commercial choice does not.

**Anchor 1, the contract already excludes the fast and clever parts.** Annex A of the Consulting Agreement between
Elysium AM Ltd and IkeNova Ltd, executed 3 March 2025, lists under Scope Exclusions: tokenisation of fund, fund
setup and administration, fund settlement and clearing, prime broker and exchange relationship management, **ultra
low latency execution**, **liquidity provision**, and **post-launch maintenance and upgrades**, the last noted as
arrangeable separately. Excluding smart and fast execution is therefore the agreed scope, not a new restriction.

**Anchor 2, Article 4 sets the ownership test.** All Work Product developed under the engagement is works made for
hire and the exclusive property of the Elysium group, with an irrevocable assignment of anything that cannot be
classified that way. Section 4.6 reserves to the Consultant only generic programming methods and open-sourced
components. So the defensible line is **what was developed under this engagement** versus **independent platform IP
built before and beside it**, not what we would prefer to keep. The basis and staked-basis strategy sits on their
side of that line. The multi-asset-group platform, its smart execution, DART, and the other archetypes sit on ours.

**Anchor 3, POD already owns the excluded layer.** POD is a regulated fund operating system, administered under the
Central Bank of Ireland, running segregated portfolios inside an SPC, with custody through Ceffu, Copper and
Coinbase Prime, venue connectivity through Haruko at 140-plus venues, and NAV, fee calculation and fund accounting
on-chain. POD's own material states that trading IP is owned 100% by the trading teams and PMs. Excluding our
reconciliation, wallet transfers and treasury is therefore declining to duplicate their stack, not withholding.

### In the carve-out

- The basis and staked-basis strategy archetypes.
- An execution service that is stable rather than clever: no smart execution algorithms, no latency optimisation.
- Limit order types only.
- A basic fill algorithm that works orders at market or limit. Its failure mode, that an order may not fill, is
  inherent to that design and should be left implicit rather than dwelt on.

### Out of the carve-out

- Smart execution algorithms, and anything whose value is speed.
- Reconciliation.
- Wallet transfers and treasury movement.
- Every other strategy archetype.
- The parameter surfaces that let a strategy change coins, venues and weights dynamically.
- CI/CD and deployment automation.
- Disaster recovery and kill-switch protocols.
- Hot configuration reloading, and hot reloading of strategy configuration, provided removal is not disproportionate.

The intent behind the exclusions is that POD can run it today and layer their own risk management on top.

## Voice rules, enforced across every document in this set

- Client-facing throughout. No internal audit trail, no changelog framing, no self-narration.
- Never the words fixed, pending, partial, not complete, TODO, or coming soon.
- No em-dashes and no double-hyphens in prose.
- No repo@sha citations, no Source lines, no owner or evidence marker chips, no references to internal plans.
- Module, class and config-file names are appropriate in `strategy-service-deep-dive.html` alone, which is a
  codebase orientation document read alongside the source. They stay out of the other five.
- Built in code counts as built. Only a genuine external dependency, a vendor credential or a missing upstream feed,
  may be qualified, and it is qualified by omission rather than by a caveat.

## Todos

- [ ] [AGENT] P0. **Ground-truth fact base from code, registries and data.** Venue, chain and protocol counts by
      asset group; the `StrategyInstructionV2` member list; family and archetype counts; DeFi execution reality per
      protocol and chain; the external endpoint inventory with auth and real rate limiting; the wired-versus-specified
      status of transfers, reconciliation, breakers, kill switch, hot reload, custody, signals and the batch equals
      paper determinism claim; and the honest data-coverage position. Output is a measured fact sheet with evidence
      inline, plus an explicit list of figures the documents currently get wrong.
- [ ] [AGENT] P0. **Conflict audit across the four stable documents** (walkthrough SSOT, api-reference, architecture,
      carve-out). Classify by contradictory fact, contradictory capability claim, terminology drift, structural
      contradiction. A narrower scope in the carve-out document is not a conflict; a different fact about the platform
      is. Resolve each against the SSOT, and against the codebase where the SSOT is itself wrong.
- [ ] [AGENT] P0. **Merge `strategy-service-walkthrough.html` into `strategy-service-deep-dive.html`** and delete the
      walkthrough, repointing every inbound reference. Add end-to-end code flow for instance startup and config load,
      signal to instruction to execution request, a reconciliation cycle, and a breaker trip into kill switch. The
      document leans on enumerations and payload blocks today and needs narrative flow.
- [ ] [DOC] P0. **Apply the conflict resolutions** across all five live documents, SSOT first then the dependants.
- [ ] [DOC] P0. **Retarget `carveout-engineering.html` to POD** with Elysium AM as the contract basis: retitle, write
      to POD as the operating counterparty, ground the exclusions in Annex A rather than in preference, and state the
      Article 4 ownership test as the reason the boundary falls where it does. Reconcile the existing eleven-component
      package and ten interface contracts against the scope above, and restate the definition of runnable so it
      targets a POD segregated portfolio.
- [ ] [DOC] P0. **Tailor `platform-architecture.html` to the basis and staked-basis client.** Illustrative examples
      become BTC, ETH and SOL basis and its staked variant. Do not position reconciliation, wallet transfers or fund
      accounting as things this reader needs from us, because their fund structure already owns that layer.
- [ ] [AGENT] P1. **Second conflict pass over the merged deep dive** once it lands, against the same SSOT.
- [ ] [DOC] P1. **Publish five artifacts** and cross-link them reciprocally: walkthrough and api-reference refresh at
      their existing URLs, plus new links for carve-out, deep dive and architecture. Record every URL here.
- [ ] [DOC] P2. **Document the isolated-ship stash signature in codex.** `quickmerge --isolated` and `safe-doc-push`
      evacuate the named files into a `qm-iso-evac-<pid>-<timestamp>` stash for the duration of a run, so a file
      legitimately looks reverted mid-ship. The marker string appears only in `scripts/quickmerge.sh` and nowhere in
      codex, which is why this session misdiagnosed it as a peer clobber on 2026-08-22. One line in
      `/codex/05-infrastructure/per-tab-worktrees.md`, next to the existing isolated-mode section. The underlying
      defect is already filed and is worse than the documentation gap: see
      `/plans/active/issues/quickmerge_isolated_stash_evacuation_entangles_concurrent_session_edits_2026_08_22.md`,
      which establishes that the evacuation stash is file-granular rather than session-granular, so a concurrent
      session editing the same file has its hunks swept into the same entry, and that a mid-run STAGE 1 failure
      never restores it. This todo covers only the codex line; the fix belongs to that issue.

## Progress log

**2026-08-22.** Plan opened. Carve-out scope taken from operator direction and cross-checked against the executed
Elysium AM consulting agreement and POD's own positioning material. Operator rulings recorded: carve-out document
addresses POD with Elysium as the contract basis; the Phase 2 update document is frozen history and excluded from
the audit; all five live documents get published artifact links.
