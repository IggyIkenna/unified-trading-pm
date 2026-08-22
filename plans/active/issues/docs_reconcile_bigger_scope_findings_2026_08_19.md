---
doc_type: issue
title: "docs-reconcile 2026-08-19 — 6 findings needing owner judgment, not a quiet doc edit (2 are BIG findings)"
summary: >-
  Round-up of the /docs-reconcile autonomous run's self-consistency + doctrine sweep findings that could NOT be
  resolved as a mechanical doc fix — each needs either domain-owner judgment, a live-system audit beyond a quick grep,
  or an operator authority ruling. Two are BIG findings per the workspace hard rule (data-correctness /
  SSOT-vs-live-state contradiction) and are called out explicitly for operator attention, not just parked passively.
status: open
nature: issue
asset_group: [meta] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; a docs-reconcile findings digest spanning cefi/ao/ci-tagged items, genuinely process-level not data-pipeline
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service, agent-orchestrator, strategy-service, unified-trading-ci]
scope: [engineer, admin]
tags: [docs-reconcile, self-consistency, big-finding, needs-bigger-scope, cefi, ao, ci, quality-gates]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cefi-batch-live.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/06-coding-standards/adr-qg-offload-self-hosted-runners-2026-06-02.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
  ]
created: 2026-08-19
parent_epic: security_and_cross_cutting_master
source: "/docs-reconcile --autonomous, dispatch agt-4f5336, slot 28, 2026-08-19"
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
priority: P1
milestone: M3
depends_on: []
execution_scope: local-only
drift_direction: advance-code
context_scope:
  [
    /codex/04-architecture/cefi-batch-live.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py,
    /codex/06-coding-standards/adr-qg-offload-self-hosted-runners-2026-06-02.md,
    /plans/epics/ci_master.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
  ]
---

# docs-reconcile 2026-08-19 — bigger-scope findings

All 6 items below surfaced during the daily `/docs-reconcile` autonomous run's Phase 1 "internal self-consistency"
hunter (5 parallel sub-agent reads over the 56 codex docs touched in the prior 24h) and its Phase 2 adversarial
verification pass (5 parallel re-checks against live files + ground-truth greps against actual source code). 17 other
findings from the same sweep were confirmed as low-risk mechanical fixes and already shipped
(`unified-trading-pm@36b1c2771`). These 6 are different: fixing them "right" needs either a domain-owner read, a
live-system audit beyond a 1-2-grep budget, or an operator authority call — applying a quick text edit risked being
confidently wrong. Per CLAUDE.md's findings-triage rule, each below has options with a recommendation marked
(`[REC]`), not an open-ended question.

## 1. 🔴 BIG FINDING — `cefi-batch-live.md` §4/§7 vs §9: `record_empty(EXPECTED_INSTRUMENT_NOT_LISTED)` for CeFi

**Why this is a BIG finding, not just a doc typo**: this is a same-document contradiction about what PRODUCTION DATA-
WRITING CODE should do, not just prose. §4 (line ~103) and §7 (anti-patterns, line ~163) both explicitly ban
`record_empty(reason=EXPECTED_INSTRUMENT_NOT_LISTED)` for CeFi at instrument-day grain ("cefi is 24/7... Missing =
`record_failed`, not `record_empty`"), backed by an explicit 5-item whitelist that excludes it. §9 (now moved to the
end of the file during this same run's mechanical cleanup — content untouched, dated 2026-05-27, labeled MANDATORY)
gives a live code sample doing exactly that for the same CeFi grain (OKX/Deribit/Kraken dated instruments).

**Live-code evidence is genuinely split** (confirmed by an independent verification sub-agent, not just the original
reader):
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/tardis/tardis_batch_download.py` has a
  real, live "pre-listing filter" using an `EmptyConfirmedReason`-typed parameter — i.e. §9's pattern IS live
  production code, not aspirational pseudocode.
- `instruments-service/tests/unit/scripts/test_enumerate_expected_universe_v2.py`'s docstring states
  `EXPECTED_INSTRUMENT_NOT_LISTED` is a **DeFi**-family reason (cefi/prediction use `EXPECTED_PRE_VENUE_LAUNCH`
  instead) — supporting §4/§7's ban.
- `instruments-service/tests/unit/scripts/test_build_instrument_catalogue.py` (line ~3596) asserts a CeFi-looking
  "before `available_from`" case maps to `EXPECTED_INSTRUMENT_NOT_LISTED` — cutting the other way.

A reconciling explanation MAY exist (e.g. "catalogue construction" vs "manifest empty-marking" are different contexts
that legitimately use the enum differently) but that wasn't confirmable within a verification sub-agent's budget.

**Options:**
- **A. [REC] Assign to the data-pipeline domain owner to read `EmptyConfirmedReason`'s own docstring +
  `tardis_batch_download.py` in full, determine the actually-correct rule, then fix whichever of §4/§7 or §9 is wrong
  (in the live code AND the doc, not just the doc) — this is a data-correctness question, the doc is downstream of it.**
- B. File as a `data_pipeline_failure`-class finding via the normal DP alert path instead of this issue doc, if the
  operator wants it to go through that pipeline's own triage/verification cadence instead.
- C. Leave flagged in-doc only (already done — see the inline note left at the top of §9) until someone with EmptyConfirmedReason context notices.

## 2. `runtime-deployment-topology.md` — position-balance-monitor-service (PBM) described as standalone in 7+ sections

Confirmed pervasive: the 2026-05-20 top-banner consolidation note (PBM merged into `strategy-service`) and a
2026-08-18 operator-ruling addendum in §5 ("deliberate for now, not an oversight... re-evaluate ahead of
`system_readiness_master.md` W7, November 2026") are BOTH current/correct and agree with each other — but Part-1's
mermaid diagram, §6's loop diagram, §7's Data Lineage table, §11's Sharding Dimensions table, §21's Deployment
Targets table, and §22's Async Startup Dependency Chain all still describe/diagram PBM as an independently-deployed
service with its own Cloud Run target. `separation-of-concerns.md`'s matching Layer Model table entry was already
fixed in this run's mechanical batch (same underlying fact) — this doc's fix is bigger because it's not one line, it's
6 separate tables/diagrams that all need to represent "logically separate, physically embedded" consistently.

**Options:**
- **A. [REC] Whoever next does substantive work in `runtime-deployment-topology.md` (or is assigned this doc's
  freshness re-review) reconciles all 6 sections in one pass** — rewrite each to say "PBM (embedded in
  strategy-service's `position/` package as of 2026-05-20, deliberately not extracted per 2026-08-18 operator ruling,
  see §5)" instead of listing it as a standalone deployment target.
- B. A dedicated small plan/todo, since it touches 6 distinct sections and the doc is 1600+ lines (worth tracking as
  its own scoped unit of work rather than an incidental fix).

## 3. 🔴 BIG FINDING — self-hosted-runners ADR (`adr-qg-offload-self-hosted-runners-2026-06-02.md`) may now contradict LIVE fleet state

**Why this is a BIG finding**: this isn't just an ADR's own "Decision" section conflicting with its own "Follow-up
todos" section (that internal contradiction IS confirmed real — Decision: "Keep QG LOCAL... no fleet right-sizing
needed"; Follow-up todos: lists exactly the REJECTED Option B's implementation steps with no caveat). The bigger
concern a verification sub-agent surfaced: **`plans/epics/ci_master.md` contains live entries suggesting Option B (the
rejected central self-hosted-runner pool) may have actually shipped fleet-wide since this ADR was written** — e.g.
"Fleet-wide quality-gates-v2 self-hosted-runner flip already landed on 19/24 repos" and "Fleet-wide QG self-hosted-
runner capacity crisis, day 2." This repo's own `quality-gates-v2.yml` still shows `runs-on: ubuntu-latest`, but the
reusable workflow carries a `self_hosted_runner_labels` fallback parameter consistent with other repos having
already flipped. If true, the ADR's "Decision: Accepted Option A... no fleet right-sizing needed" is now **factually
false relative to live state** — a genuine SSOT-vs-reality contradiction per the workspace hard rule, not an internal
doc-consistency nit.

**Options:**
- **A. [REC] Operator or CI/infra owner reads `ci_master.md`'s full self-hosted-runner history to determine: was this
  ADR ever formally superseded? If yes, mark it `status: superseded` with a pointer to whatever superseded it (its
  Follow-up todos section stops being a live contradiction once the doc is correctly marked historical). If no, this is
  a live architecture decision that silently drifted from its own ADR and needs a real decision: formally ratify the
  Option-B rollout (update the ADR) or roll it back to match the ADR.**
- B. Treat as lower-priority since local QG behavior (the thing that actually affects a developer's daily loop) may be
  unaffected even if CI's `runs-on` target changed — but this still needs someone to confirm that assumption, not just
  assert it.

## 4. `quality-gates.md` Canonical Template vs. `quality-gates-template.sh` / `quality-gates-service-template.sh` drift

Confirmed: `quality-gates.md`'s "Canonical Template (NEW)" section prescribes `--cov-fail-under=70` and unconditional
`pytest -n auto` as required features. A dated HARD RULE elsewhere in the SAME doc (line ~604, "Resolved 2026-06-17")
says `base-service.sh`/`base-library.sh` no longer pass `--cov-fail-under` at all. But `quality-gates-template.sh` (the
file the Canonical Template section actually points at) genuinely still has `--cov-fail-under=$MIN_COVERAGE` on disk,
unmodified — so the doc section isn't merely stale prose, it faithfully describes a real script that itself was never
updated to match the HARD RULE (which only names `base-service.sh`/`base-library.sh`, never this template, as in
scope). A SECOND, differently-named file (`quality-gates-service-template.sh`) is also referenced nearby in the same
doc and contains NEITHER `--cov-fail-under` nor `-n auto` — the two template files themselves disagree, and it's
unclear which (if either) is actually consumed for new-repo bootstrap today.

**Options:**
- **A. [REC] Whoever owns repo-bootstrap tooling audits which template file(s) are actually live-consumed, retires or
  merges the stale one, and brings both the doc's Canonical Template section and the real script(s) into agreement
  with the already-shipped `--cov-fail-under` removal + the LOCAL-vs-CI `-n auto`/`-n 1` split.**
- B. Lower priority if neither template has been used for a new-repo bootstrap recently (worth a quick check of repo
  creation history before investing in the cleanup).

## 5. `agent-orchestrator-scheduled-jobs.md` — an 11th AO timer script exists on disk, undocumented

This run's mechanical fix corrected the doc's internal "9 vs 10 timers" contradiction (frontmatter now says 10,
matching the body's already-correct "The 10 timers" table). But a ground-truth `find` during verification turned up
**11** `install-*-timer.sh` scripts on disk right now — `install-local-ratchet-gate-breach-detector-timer.sh` is
completely absent from this doc's table and `code_refs`. Its own script comment confirms it dispatches via the same
`/api/plan-health/dispatch` mechanism this SSOT catalogs, so it's in-scope, not an intentional exclusion.

**Options:**
- **A. [REC] Next docs-reconcile run (or whoever touches this doc next) reads `install-local-ratchet-gate-breach-
  detector-timer.sh` in full and adds its table row (mode param / job_name / cadence / sharded / timeouts) — the "10"
  fixed today will likely need to become "11" imminently.**
- B. Confirm first whether this timer is actually installed/active on the central VM (a script existing on disk isn't
  proof it's installed) before documenting it as a live timer.

## 6. `launcher-script-ssot.md` — features-service consolidation described two incompatible ways

The "features-service consolidation (2026-05-08)" section says 8 per-family launchers collapsed to "a single"
parameterized launcher. A later "Why per-asset-group launchers" section describes the same named consolidation as
"5-6 features-* repos" collapsing into "one launcher per deployment-cluster shape" (i.e. multiple per-asset-group
launchers, not one). Ground-truth check: `launch-features-vm.sh` DOES exist (matching the first section), but so do
several per-asset-group/family launchers (`launch-features-onchain-backfill-vm.sh`,
`launch-features-sports-backfill-vm.sh`, etc.) — neither section is fully right alone, and the specific example
`launch-features-cefi-vm.sh` cited by the second section does not exist anywhere in the repo. The real current shape
is a hybrid that evolved after both sections were written.

**Options:**
- **A. [REC] Whoever next touches launcher inventory reconciles both sections against the actual current
  `deployment-service/scripts/vm/launch-features-*.sh` file list** (rewrite to describe the real hybrid shape: one
  generic launcher + several family-specific ones) rather than either of the two stale narratives.
- B. Lower priority — doesn't affect correctness of any running system, purely a documentation-accuracy gap.

## Progress Log

- **context-scout 2026-08-19**: populated context_scope (6 entries).
- **2026-08-22 — ruling D6 (Docs-reconcile findings sign-off)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Approve all — each item carries a per-doc recommendation; the two BIG
  findings need named owners now, the rest is bounded cleanup. Note: this doc's 6 findings are framed as prose
  Options (A/B/C), not `- [ ]` todos, so no single checkbox marker exists to retag per-item; each finding's own
  `[REC]`-marked option is hereby approved as the disposition. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
