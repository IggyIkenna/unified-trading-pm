---
doc_type: issue
title:
  Two question docs (client_reporting_pnl_attribution + risk_simulations_limits_alerting) + plans/questions/README.md
  genuinely lost — never committed, 8 active files reference them as canonical SSOTs
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
author: main-orchestrator-agent
source:
  [
    plans/questions/ on-disk vs git-tracked diff,
    git log --diff-filter=D plans/questions/<missing files> (returns empty — never committed),
    git stash list × 20 entries (none contain the docs),
    grep -rln across plans/ + codex/ for the missing slugs (8 hits),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Two question docs + README.md genuinely lost — orphan-referenced as canonical SSOTs from 8 active files

> **Severity**: P0 — May-23 cutover plans cite missing SSOTs for circuit-breaker rule definition + PnL attribution
> decomposition + per-archetype paper-vs-live carve-out **Blast radius**: 8 active files in PM repo reference docs that
> don't exist (1 active plan + 5 question docs + 1 codex doc + 1 spawned execution plan) **Suggested owner**: operator
> triage — pick disposition (re-spawn / fold-in / redirect / accept-loss-and-remove-refs)

## What I found

Three files **never committed to git** AND **gone from disk** as of 2026-05-10:

1. `plans/questions/client_reporting_pnl_attribution_2026_05_08.md`
2. `plans/questions/risk_simulations_limits_alerting_2026_05_08.md`
3. `plans/questions/README.md`

All three existed on disk on 2026-05-08 (read directly via Read tool while drafting
`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`). Verifications:

- `git log --diff-filter=D --oneline -- <each path>` returns nothing — never tracked.
- `git stash list × 20` checked file-by-file — no stash contains them. Stashes are all "foreign-WIP" parks from
  parallel-agent activity 2026-05-08; none captured these.
- `git fsck --lost-found` shows dangling commits/trees but spot-check did not surface the slugs.
- On-disk `ls plans/questions/` (now): 9 docs present (the 3 originally tracked + 5 from 2026-05-08 untracked drafts +
  `wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md` +
  `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`). None of these is a rename of the 2 missing docs
  (different slugs, different scope per body inspection).

**8 active files reference the missing slugs as if they're live canonical SSOTs:**

| File                                                                                                                                         | Line(s)               | What it claims                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md`](../simulation_scenarios_topology_price_shocks_2026_05_09.md)       | 20, 64, 106, 171, 597 | Frontmatter `related_plans:` + body says **`risk_simulations_limits_alerting_2026_05_08` OWNS** real-state risk-limit + circuit-breaker rule definition; this plan **CONSUMES** that taxonomy |
| [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../api_keys_wallets_accounts_readiness_2026_05_10.md)                     | 580–581               | Cites both as siblings; Phase 3.D + Phase 7 explicitly depend on them                                                                                                                         |
| [`plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md`](../../questions/api_keys_wallets_accounts_readiness_2026_05_08.md)     | 568–569               | Sibling-question cross-link; treasury rollup view (C4) is shared dependency                                                                                                                   |
| [`plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md`](../../questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md) | 473, 476              | "Composes with" both — risk + portfolio construction overlap (same data shape) + PnL attribution overlap (same data shape)                                                                    |
| [`plans/questions/batch_live_design_symmetry_2026_05_08.md`](../../questions/batch_live_design_symmetry_2026_05_08.md)                       | 513                   | "PnL reporting must" — references `client_reporting_pnl_attribution`                                                                                                                          |
| [`plans/questions/defi_readiness_catalogue_2026_05_08.md`](../../questions/defi_readiness_catalogue_2026_05_08.md)                           | 937, 939              | "Composes with" both — simulation harness + chain primitives feed risk simulations; PnL attribution decomposition needs DeFi catalogue                                                        |
| [`plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md`](../../questions/paper_vs_live_workflow_maturity_2026_05_08.md)             | 19, 94, 430, 688, 742 | Frontmatter `related_codex:` cite + body says `risk_simulations_limits_alerting` "owns the mock-data-as-stress-test surface"                                                                  |
| [`/codex/04-architecture/paper-vs-live-execution-seam.md`](/codex/04-architecture/paper-vs-live-execution-seam.md)                           | 48                    | Codex SSOT cross-links to it as the canonical risk-simulation doc                                                                                                                             |

Also, **my own `wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md` formerly cross-referenced both**;
re-creation 2026-05-09 dropped those refs since the targets were gone — the new content links to the 3 surviving sibling
drafts instead.

## Why it matters

- **Plans on May-23 critical path are citing ghost SSOTs.** `simulation_scenarios_topology_price_shocks_2026_05_09.md`
  is a fresh 2026-05-09 plan (active, not draft) whose body explicitly delegates circuit-breaker rule taxonomy ownership
  to `risk_simulations_limits_alerting_2026_05_08`. Any agent picking that plan up will look for the upstream doc, not
  find it, and either: (a) re-create it ad-hoc + drift from operator intent, (b) inline a half-baked taxonomy in the
  consumer plan + create the SSOT-divergence Citadel-grade § 7 prohibits, or (c) flag and stall, costing operator triage
  time on the same finding I'm logging now.
- **PnL attribution architecture has no home.** `client_reporting_pnl_attribution` was the canonical question doc for
  per-archetype PnL decomposition (strategy alpha vs execution alpha vs financing vs slippage vs fees vs FX). Multiple
  active plans + question docs assume the decomposition shape exists — when the cross-link bottoms out at a 404, agents
  re-derive in inconsistent ways. The sibling client-reporting question doc had ~80 lines of audit content yesterday;
  reconstructing it from scratch loses that.
- **No `README.md` → no backlog index in `plans/questions/`.** The directory has 10 docs now (3 tracked + 7 untracked
  drafts) with no entry-point document. New question docs land without an explicit registration step. The lifecycle
  process documented in the README (5-phase: drafting → audit → iterating → plan-spawned → closed) is implicit-only.
- **This is the second loss event this week.** `wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md` was also
  lost on 2026-05-08 to the same class of failure — uncommitted question doc + parallel-agent-shared-tree erasure.
  Recovered on 2026-05-09 via re-write because content was preserved in the conversation context. The 2 missing docs
  - README don't have a comparable preservation surface; full content is genuinely gone unless an operator has a local
    copy.

## Recommended decision (operator triage)

Pick one disposition — none of these is destructive, but all need explicit operator direction:

**(a) Re-spawn from operator memory.** Operator drafts new question docs at the same slug + date, audit-pass populates
the Block A-N findings, plan-spawn proceeds. Cost: ~1-2 operator hours of dictation per doc; produces highest-fidelity
content. Recommended IF the operator can recall the original framing — both docs were drafted ~2026-05-08 morning so
recall window is short.

**(b) Fold scope into existing siblings + redirect references.**

- Risk-simulations content folds into `simulation_scenarios_topology_price_shocks_2026_05_09.md` (which already partly
  consumes it) — the consumer becomes the owner.
- PnL-attribution content folds into `wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md` Block D
  (post-trade reporting + fee accrual already overlaps) OR into `api_keys_wallets_accounts_readiness_2026_05_08.md`
  treasury surface (less clean fit).
- All 8 cross-references rewrite to point at the new canonical home.
- Cost: 1 sweep across the 8 files + minor scope expansion in the absorbing docs. Risk: scope-bleed in the absorbing
  doc + loss of the original audit framing.

**(c) Accept loss, strip references.** Remove all 8 cross-references with a brief `# obsolete-ref-removed` annotation.
Implies these question doc bodies of work simply don't exist as canonical question-doc artefacts — risk + PnL
attribution architecture lives directly in master plan + codex SSOTs without a question-doc staging layer. Cost: 1
sweep. Risk: orphaned references signal "we had a plan, then lost it" which is worse than "we never planned that."

**(d) Hybrid.** Re-spawn `risk_simulations_limits_alerting` as a new question doc dated 2026-05-10 (May-23 critical
path; needs explicit framing); fold `client_reporting_pnl_attribution` into the wallet-treasury Block D (PnL surface
already overlaps); README stays gone (the directory has functioned without it for 48h).

**My recommendation: (d).** `risk_simulations_limits_alerting` is on the critical path with a downstream consumer plan
that explicitly cites it as upstream owner — needs a real spawn. `client_reporting_pnl_attribution` overlaps the
wallet-treasury Block D enough that fold-in is honest; only 4 of the 8 references touch it specifically and a reference
sweep is cheap. README is non-load-bearing (docs are findable via `ls`), keeping it gone reduces the parallel-agent
file-collision surface.

## Composes with

- **Findings Triage Discipline** (CLAUDE.md) — case-5 (big) finding routing: operator-notify in chat + issue doc.
- **Plans Run To Actual Completion** HARD RULE — same-class failure as the 2026-05-08 wallet-treasury loss event. The
  underlying systemic gap (uncommitted question docs lost across parallel-agent shared-tree activity) is broader than
  this incident; a separate `plans/active/issues/uncommitted_question_doc_loss_pattern_2026_05_10.md` may be warranted
  if this happens a third time.
- **Capture Discoveries As Plan Todos** (CLAUDE.md) — agents picking up
  `simulation_scenarios_topology_price_shocks_2026_05_09.md` who hit the orphan reference should NOT re-derive the
  taxonomy ad-hoc; they should ping this issue doc.
- **No fire-and-forget question docs** — implicit follow-up: question docs need a `commit-on-creation` discipline
  (already in the workspace as Half-1 of Commit+Push+Flip — this is yet another instance where the rule failed in
  practice).

## Disposition tracking

- [x] Operator picks **disposition (a) — re-spawn all three** per direction "whatever is institutional grade Citadel and
      per claude md" (2026-05-10). Citadel-grade § 7 SSOT bans multi-topic docs (README convention "One topic per doc"),
      so fold-in (b) violates SSOT discipline. Re-spawn at original slug+date means **zero orphan-ref sweep needed**
      (the 8 references resolve as-is).
- [x] Selected disposition executed:
  - PM@b015db97 — `client_reporting_pnl_attribution_2026_05_08.md` re-spawned (high-fidelity from conversation context:
    Block A1-B5 preserved + Block C synthesized).
  - PM@6e504f0b — `risk_simulations_limits_alerting_2026_05_08.md` re-spawned (low-fidelity reconstruction;
    operator-review flag in body + iteration log + operator-note section).
  - PM@6ef6ad4b — `plans/questions/README.md` re-spawned (high-fidelity from conversation context + lifecycle § 1
    - Conventions + Composes-with extended to ban future loss events; backlog table refreshed to current 12 docs).
- [x] All 8 cross-references resolve. **Zero ref-sweep required** because re-spawn preserved slug+date — the 8
      orphan-citing files were already correct; they're just no longer orphans.
- [x] Reconstruction notes in both re-spawned question docs flag operator review for framing-drift before audit pass
      consumes content as canonical (especially `risk_simulations_limits_alerting` which is lower-fidelity).
- [x] **Issue doc closed.** Status flipped to closed; locked_by retained until operator confirms reconstructions are
      acceptable.

**Status: closed** (2026-05-10, executor: main-orchestrator-agent, executor commits PM@b015db97 + PM@6e504f0b +
PM@6ef6ad4b).

**Operator follow-up (non-blocking):**

1. Review `risk_simulations_limits_alerting_2026_05_08.md` body + iteration-log Operator-note section. The 4-surface
   framing (monitor / simulations / alerts / preflight) + the {BLOCK / MONITOR / TEST} action taxonomy are the
   reconstructor's best inference from references — flag any framing drift vs original intent.
2. Spot-check `client_reporting_pnl_attribution_2026_05_08.md` Block C (cross-cutting integration). Block A + B were
   preserved verbatim from yesterday's conversation; Block C was new content synthesized from the original framing line.
3. README backlog statuses for `iterating` / `audit-in-progress` are inferred from commit history — confirm or correct.
