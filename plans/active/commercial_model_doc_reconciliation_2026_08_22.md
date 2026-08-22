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

`strategy-service-walkthrough.html` was merged into the deep dive and deleted; the deep dive now carries its unique
material and every inbound reference points at the deep dive.

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

- [x] ✅ [AGENT] P0. **Ground-truth fact base from code, registries and data.** Venue, chain and protocol counts by
      asset group; the `StrategyInstructionV2` member list; family and archetype counts; DeFi execution reality per
      protocol and chain; the external endpoint inventory with auth and real rate limiting; the wired-versus-specified
      status of transfers, reconciliation, breakers, kill switch, hot reload, custody, signals and the batch equals
      paper determinism claim; and the honest data-coverage position. Output is a measured fact sheet with evidence
      inline, plus an explicit list of figures the documents currently get wrong.
- [x] ✅ [AGENT] P0. **Conflict audit across the four stable documents** (walkthrough SSOT, api-reference, architecture,
      carve-out). Classify by contradictory fact, contradictory capability claim, terminology drift, structural
      contradiction. A narrower scope in the carve-out document is not a conflict; a different fact about the platform
      is. Resolve each against the SSOT, and against the codebase where the SSOT is itself wrong.
- [x] [AGENT] P0. ✅ **Merge `strategy-service-walkthrough.html` into `strategy-service-deep-dive.html`** and delete
      the walkthrough, repointing every inbound reference. Deep dive is now 19 sections: the walkthrough's unique
      material lands as §02 strategy identity, §05 the mode axis with testnet as a paper sub-mode, §07 coin/venue/
      funding selection, §08 reconciliation engines and the four scenarios, §10 risk, §12 the execution seam and its
      config loop, §19 signal leasing, plus transfer/custody/treasury detail folded into §11, the read-only position
      adapter contract into §13, and fill fidelity into §16. New §06 carries the four traced code paths: instance
      startup and config load, signal to instruction to published execution request, a reconciliation cycle, and a
      breaker trip into the kill switch, each naming real modules and callables verified against
      `strategy-service`. Status/evidence/owner chips, internal plan links and em-dashes removed throughout; venue,
      chain, protocol, archetype, module and router counts re-measured from the live registries and corrected.
- [ ] [DOC] P2. `plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md` still lists the deleted
      `strategy-service-walkthrough.html` in its artefact reading list, and still says "four client-sendable
      documents" where the sibling tranche plans now say three. It could not be edited in the same pass because the
      file sits at 1,001 lines against a 1,000-line hard cap, so every commit touching it is rejected until it is
      split. Split it, then apply both corrections.
- [ ] [SCRIPT] P3. Drop the deleted `strategy-service-walkthrough.html` from
      `scripts/plan-hygiene/allocate_code_readiness_tranches.py`'s `SPINE_SOURCES` tuple and reword the historical
      example naming it in `scripts/plan-hygiene/check_artefact_enum_drift.py`'s module docstring. Neither breaks
      today (`load_spine_text()` guards on `fp.exists()`, and the drift checker globs the directory rather than
      naming files), so this is tidy-up that belongs in a gated code push rather than a doc push.
- [ ] [DOC] P3. `plans/epics/html/system_readiness_master.html` still names `strategy-service-walkthrough.html` as
      lane A's owned file. It is a rendered dashboard for the archived
      `client_artefact_remediation_elysium_2026_08_18.md`, so repointing it at the deep dive would misstate what that
      plan owned. Regenerate or retire the dashboard instead.
- [x] ✅ [DOC] P0. **Apply the conflict resolutions** to the walkthrough and api-reference — unified-trading-pm@6ef0b73c7e.
      Stale SSE access-control disclosure replaced, route-module count re-measured to 34 with its counting rule stated
      inline, transfer-rails table rebuilt around `TransferHandler`, rotting line citations deleted in favour of bare
      file names, 633 versus 683 reconciled with each basis named and the noun settled on shard, envelope versus V2
      union disambiguated. Architecture and carve-out resolutions ship with their own retargeting passes.
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

**2026-08-22, second entry.** The ground-truth pass confirmed every headline breadth figure (171 live, 194 declared,
24 chains, 59 protocols, 16 instruction types) and found one flatly wrong number, 59 archetypes where the registry
holds 60, originating in a stale docstring in the enum itself. It also surfaced several correct-but-misleading
figures now carried as qualifiers: only 10 of 24 chains carry a live DeFi venue, only 3 protocols have end-to-end
live execution wiring, and real custody integrations number 2 rather than 4. Uniswap V4 LP turns out not to be
callable at all, since `LpMintInstruction` carries no field for the pool price the V4 path requires, which
retrospectively validates keeping V4 out of the LP lists. The signals surface is wired on origin but its registry
holds two suspended stubs, so it dispatches to zero recipients.

Two authentication defects were found incidentally and verified directly rather than taken on report, then filed
as `/plans/active/issues/unauthenticated_manual_execution_surface_and_unresolved_rbac_identity_2026_08_22.md`
(unified-trading-pm@77faa65ca6): execution-service mounts `/manual/*` with no auth dependency while both sibling
routers on adjacent lines carry one, and deployment-api's RBAC reads a request-state identity that only its tests
ever write. The first carries an operator todo, since its severity depends on Cloud Run ingress configuration that
is not set by any file in these repositories.

The coverage section was built for real rather than scaffolded: 3,725 shard rows at venue by instrument-type by
data-type grain with completion bars, read from the daily `coverage.json` the honest-coverage measurement writes,
so it regenerates rather than rotting. Note this introduces a third universe size alongside the 633 readiness-dump
and 683 declared-registry counts; the section names its own basis, but all three side by side is a follow-up.

**2026-08-22.** Plan opened. Carve-out scope taken from operator direction and cross-checked against the executed
Elysium AM consulting agreement and POD's own positioning material. Operator rulings recorded: carve-out document
addresses POD with Elysium as the contract basis; the Phase 2 update document is frozen history and excluded from
the audit; all five live documents get published artifact links.
