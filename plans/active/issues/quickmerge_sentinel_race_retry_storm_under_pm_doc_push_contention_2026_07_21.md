---
doc_type: issue
title:
  quickmerge sentinel-race retry-storm under heavy concurrent unified-trading-pm doc-push contention — a
  green-since-attempt-1 single-file fix burned 27 full-QG re-runs losing the push sentinel race
summary: >-
  On 2026-07-21 ~18:07, under sustained heavy fleet contention on unified-trading-pm (many slots concurrently
  quickmerge-ing docs(plans): commits), slot 9 was observed at 27 consecutive QG->quickmerge attempts on a single-file
  fix that had been quality-gates-green since attempt 1. Every attempt re-ran the full multi-minute quality-gates.sh and
  then lost the push sentinel race (STAGE 0.4 behind-remote auto-reconcile -> re-stage -> re-push) to another slot's
  concurrent doc push that landed first. Net effect: ~27x wasted full-QG compute for one already-green single-file
  change, purely due to the retry loop re-running the ENTIRE gate on each lost race rather than fast-pathing an
  already-verified tree. Not a correctness defect and no work lost — flagged by the review role as an
  efficiency/throughput hole worth capturing.
status: open
nature: issue
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, ship-pipeline, sentinel-race, retry-storm, contention, quality-gates, throughput, efficiency, fleet]
related: [/plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md]
created: "2026-07-21"
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [review-role-observation, main-orchestrator-triage]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/issues/quickmerge_sentinel_invalidated_by_its_own_autopull_2026_07_18.md,
    unified-trading-pm/scripts/quickmerge.sh,
  ]
---

# What was observed

Under heavy sustained concurrent doc-push load on `unified-trading-pm` (many fleet slots simultaneously `quickmerge`-ing
`docs(plans):` commits — batch archived-plan triage, checkbox flips, issue docs), the review role observed **slot 9 at
27 consecutive `QG -> quickmerge` attempts** on a **single-file fix that had been `quality-gates.sh`-green since attempt
1**. It kept losing the push sentinel race to other slots' concurrent pushes that landed first, and each retry re-ran
the **full multi-minute `quality-gates.sh`** before attempting the push again.

The tree was green from attempt 1; the 26 subsequent full-QG runs produced no new information — they were pure race-loss
overhead.

# Why it matters

- **Wasted compute + wall-clock**: ~27 full-QG runs (each multi-minute) for one already-verified single-file change.
  Multiply across the fleet during high-contention doc-push windows and it's a meaningful throughput tax on a shared
  host.
- **Amplifies under exactly the load where throughput matters most** — the more slots pushing docs concurrently, the
  more sentinel races are lost, the more full-QG re-runs, which lengthens each slot's ship latency and increases the
  contention window, a mild positive-feedback loop.
- Not a defect: `quickmerge`'s STAGE 0.4 behind-remote auto-reconcile is doing the correct safe thing (never force-push,
  rebase/re-stage on a lost race). The inefficiency is that the **retry re-runs the whole gate** instead of recognizing
  the tree is unchanged-and-already-verified since the last green QG.

# Root cause (hypothesis — verify before fixing)

`quickmerge.sh` runs `quality-gates.sh` then attempts the push; on a lost sentinel race it loops back through the full
sequence including a fresh full QG. There is no "tree content unchanged since last green gate" fast-path, so a pure
rebase-of-remote-doc-commits (which does not touch this slot's staged files) still forces a complete re-gate.

# Candidate fixes (for operator / careful review — do NOT dispatch blind: quickmerge is high-blast-radius shared ship infra)

1. **Content-hash QG cache / green-tree fast-path**: after a green `quality-gates.sh`, record a hash of the staged
   working-tree content; on a retry where the staged content hash is unchanged (only remote doc commits were pulled in
   by STAGE 0.4), skip the full re-gate and go straight to the push. Biggest win, needs care to not skip a gate when the
   rebase actually changed anything relevant.
2. **Backoff + jitter on lost sentinel race**: instead of an immediate tight retry, exponential backoff with jitter so
   concurrent slots de-synchronize and stop colliding on every attempt. Cheap, purely additive, low risk.
3. **Serialized PM-doc-push queue / advisory lock**: a lightweight fleet-level advisory lock (or a short serialization
   window) specifically for `docs(plans):`-only pushes to `unified-trading-pm`, so doc pushes take turns rather than
   racing. Heavier; only worth it if 1+2 don't suffice.

Recommended order: (2) first (cheap, immediate relief), then (1) (the real fix), and consider (3) only if contention
persists.

# Notes

- Filed `assigned_vm: NA` / `execution_scope: local-only`: `quickmerge.sh` is the PM-SSOT ship path symlinked into every
  repo and exercised by every slot on every ship — a careless change here breaks fleet shipping. Operator/careful review
  should sign off on the fast-path predicate (fix 1) before it dispatches, since an over-eager "unchanged tree" skip
  could bypass a genuinely-needed gate.
- No work was lost; this is throughput, not correctness.

# Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` (quickmerge / strict-quickmerge / STAGE 0.4 behind-remote auto-reconcile /
  sentinel-race handling).

# Partial progress (2026-07-22)

Fix **2 (backoff + jitter)** shipped as part of `unified-trading-pm@e264b3c9`, landed via the sibling doc
`quickmerge_sentinel_invalidated_by_its_own_autopull_2026_07_18.md` (which already had an operator-decided Option 2 this
doc's fix-2 refines). STAGE 3's AGENT_MODE sentinel-invalid path now auto-retries (re-pull + regate + recheck) up to 3x
with `sleep $((2 + RANDOM % 4 + attempt * 3))` between attempts instead of hard-failing on the first loss — directly
reduces the shape of retry-storm this doc reports (a lost race now self-heals within the SAME quickmerge invocation
instead of needing a fresh agent-initiated regate-and-retry cycle each time). **Not yet measured against THIS doc's
specific 27-consecutive-loss scenario** — that was under sustained heavy multi-slot contention, which 3 bounded retries
may not fully absorb if the push rate stays faster than one regate cycle; re-observe under similarly heavy contention
before closing this doc.

**Fix 1 (content-hash QG cache / green-tree fast-path — "the biggest win", still open)** and **fix 3 (serialized
PM-doc-push queue, still open, only if 1+2 don't suffice)** remain unimplemented. Fix 1 is the harder, real throughput
fix (skip the full multi-minute regate entirely when the only tree delta since the last green gate is remote doc/plan
commits that don't touch this slot's own staged files) — deliberately deferred rather than rushed, per this doc's own
instruction not to dispatch a change to `quickmerge.sh` blind.

## Todos

- [ ] [INFRA] P2. **Implement fix 1 (content-hash QG green-tree fast-path)**, and fix 3 (serialized PM-doc-push queue)
      only if 1+2 prove insufficient — both remain unimplemented; fix 1 is "the biggest win" (skip the full
      `quality-gates.sh` re-run on a lost sentinel race when the staged content is unchanged since the last green gate),
      deliberately deferred pending careful review since `quickmerge.sh` is high-blast-radius shared ship infra.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole remaining todo is
  explicitly gated for operator/careful review on shared, high-blast-radius ship infrastructure (quickmerge.sh) — a
  fast-path predicate error could bypass a genuinely-needed gate.
- **na-eligibility-audit 2026-08-02**: **CONFIRMS KEEP-NA, valid — unchanged** (tranche `ci`, autonomous). Ownership
  moved `infra` → `ci` since the last marker via the 2026-07-31 corpus-sweep `asset_group: [meta]` → `[ci]` retag; the
  content did not move (only post-marker commit is that same sweep). Re-read end-to-end: the sole open todo carries an
  explicit in-doc dispatch prohibition — its own heading reads "for operator / careful review — do NOT dispatch blind:
  quickmerge is high-blast-radius shared ship infra", and the Notes section restates that operator sign-off is required
  on the fast-path predicate because an over-eager "unchanged tree" skip could bypass a genuinely-needed gate. That is a
  standing in-doc gate, confirmed present verbatim, not re-derived.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-03**: **CONFIRMS KEEP-NA, valid — unchanged** (tranche `ci`, autonomous, `agt-4acc10`).
  Re-read end-to-end; the explicit in-doc dispatch prohibition ("for operator / careful review — do NOT dispatch blind:
  quickmerge is high-blast-radius shared ship infra") is still present verbatim. Cross-checked against
  `ci_satellite_ao_dispatch_batch1_2026_07_26.md`, which independently tracks this same item as Deferred D3(5)/D21 under
  "Operator-gated (needs a ruling, not a re-triage)" — consistent, not extracted as a dispatchable todo. A separate
  active plan (`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`) shipped a
  related-but-distinct fix (`scripts/dev/safe-doc-push.sh`) that does not touch this doc's actual fix 1 (content-hash QG
  cache) or fix 3 (serialized PM-doc-push queue) — no duplication. No RECLASSIFY, no ARCHIVE.
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 4 entries resolve on disk (SSOT +
  related issue + archived sibling fix doc + quickmerge.sh) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — in-doc dispatch prohibition, operator sign-off required on shared
ship infra

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply or override the doc's own
explicit, still-present in-doc dispatch prohibition ("for operator / careful review — do NOT dispatch blind: quickmerge
is high-blast-radius shared ship infra") — the AO-dispatch-by-default precedent governs new plans' own `assigned_vm`
default, it does not override an existing, reasoned, high-blast-radius dispatch prohibition already written into a
specific doc. No RECLASSIFY, no satellite-extraction. No ARCHIVE.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:15d1ddb1d1009554]: KEEP-NA,
valid — Fix 2 (backoff+jitter) already shipped and landed via a sibling doc. The sole remaining open todo (implement fix
1: content-hash QG green-tree fast-path, plus fix 3 only if needed) sits under a section explicitly headed 'for operator
/ careful review -- do NOT dispatch blind: quickmerge is high-blast-radius shared ship infra' -- an explicit, verbatim,
still-present DO-NOT-DISPATCH banner in the doc body (confirmed present at read time). The Notes section reiterates
operator sign-off is required on the fast-path predicate because an over-eager 'unchanged tree' skip could bypass a
genuinely-needed gate.
