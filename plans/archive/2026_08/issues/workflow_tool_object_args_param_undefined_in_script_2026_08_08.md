---
doc_type: issue
title:
  Workflow tool's top-level `args` object param arrived as `undefined` inside the script body — one repro, worked around
  by inlining literals
summary: >-
  While running `/ag-closeout-audit sports` (2026-08-08, agt-b4c4ab, slot-13), the first `Workflow` invocation passed a
  well-formed JSON object (`{candidates: [...66 items...], coveringPaths: [...15 items...]}`) via the tool's top-level
  `args` parameter — exactly as documented ("Pass arrays/objects as actual JSON values in the tool call, NOT as a
  JSON-encoded string"). The script failed immediately: `Error: undefined is not an object (evaluating
  'args.coveringPaths.map')` at the script's own line 25, meaning the global `args` binding itself was undefined inside
  the script body, not just missing one key. Root cause NOT diagnosed (single data point, immediately worked around by
  inlining both arrays as JS literals directly in the script body instead of relying on `args`) — could be a
  payload-size threshold (~20KB combined), a param-ordering/shape issue specific to this tool call, or a genuine binding
  bug; not reproduced against a smaller payload to isolate. The workaround (inline literals) succeeded on retry with an
  otherwise identical script. Filed per the pre-compact ritual's "measurement traps / tool answered differently than
  expected" rule — worth a tracked note since several other scheduled skills in this workspace (`na-eligibility-audit`,
  `plan-reconcile`, `docs-reconcile`) document the identical `Workflow` + `args`-object fan-out pattern and could hit
  the same failure blind.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [workflow-tool, tooling, args-binding, ag-closeout-audit, reproducibility-gap]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: ikennaigboaka [slot-13 · ag_closeout_auditor agt-b4c4ab]
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-process
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-08 (agt-b4c4ab, slot-13) — Phase 1 Workflow launch, first attempt.
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /cursor-configs/skills/docs-reconcile/SKILL.md,
  ]
---

# Workflow tool `args` object param undefined inside script (one repro, 2026-08-08)

## What happened

First `Workflow` call this session: `script` (a pipeline-classification script, ~120 lines) + `args` set to a genuine
JSON object (not a stringified blob) shaped `{candidates: [...66 objects...], coveringPaths: [...15 strings...]}`,
combined JSON size ~20.6KB. The script's own line 25 read `const coveringList = args.coveringPaths.map(...)`. The
workflow failed within 8ms of launch:

```
Error: undefined is not an object (evaluating 'args.coveringPaths.map')
    at <anonymous> (workflow.js:25:40)
    at workflow.js:73:1275
    ...
```

`args` itself was `undefined` in the script's execution scope — not merely missing the `coveringPaths` key. The tool's
own auto-generated recovery hint for resuming showed the args value re-serialized as a JSON-_encoded string_ rather than
a live object, which may or may not be related to the actual binding failure (the recovery-hint serialization could just
be a display artifact, not evidence about what the running script actually received).

## Workaround (worked, same session)

Re-issued an otherwise-identical `Workflow` call with `CANDIDATES` and `COVERING_PATHS` written as JS literal `const`s
directly in the script body (no top-level `args` reliance at all). Launched successfully — no immediate error, ran to
completion in the background. This is consistent with the tool's own documented constraint that the `meta` object must
be a pure literal, but `args` is documented as safe to use for exactly this kind of payload, so the literal-inlining
requirement (if that is in fact the real constraint) is broader than documented.

## Not established

- Whether the failure is a payload-size threshold, a one-off transient issue, or a genuine args-binding bug — only one
  data point exists (this run). Not re-tested against a minimal repro (e.g. a 1-key, 50-byte `args` object) to isolate
  size vs. shape vs. transience.
- Whether `resumeFromRunId` + a supplied `args` (as the recovery hint suggested) would have also failed or succeeded —
  not attempted, since inlining was faster and this run wasn't blocking on isolating the tool bug.

## Why this is worth tracking

`na-eligibility-audit`, `plan-reconcile`, and `docs-reconcile`'s own SKILL.md files document the same `Workflow` +
object-`args` fan-out pattern this hit. If the root cause is payload-size-related (all of those skills routinely fan out
over 50-90+ docs' worth of metadata), a future worker following the documented pattern verbatim could hit the identical
immediate failure with no obvious cause, burn a turn diagnosing it cold, and only discover the inline-literal workaround
by accident — exactly the kind of trap this ritual exists to pre-empt for the next reader.

- [x] ✅ [DIAG] P3. Reproduce with a minimal `Workflow` call (a trivial script + a small object `args`, e.g.
      `{a: 1, b: [1,2,3]}`) and a large one (mirror this run's ~20KB payload) to isolate whether the failure is
      size-gated, shape-gated, or transient. If a real threshold or bug is confirmed, add a one-line caution to this
      workspace's `Workflow`-using skills (`ag-closeout-audit`, `na-eligibility-audit`, `plan-reconcile`,
      `docs-reconcile`) recommending inline literals over `args` for large candidate-list payloads, OR file it as a
      product bug if it's outside this repo's control. Source: this issue doc. Done when: root cause is
      confirmed/ruled-out with a minimal repro, and (if confirmed) the affected skill docs carry the caution. —
      unified-trading-pm@ROOT_CAUSE_CONFIRMED (see Progress Log 2026-08-16)

## Progress Log

- **slot-13 (ag_closeout_auditor agt-b4c4ab) 2026-08-08**: Filed during the pre-compact ritual, per the workspace HARD
  RULE that findings become `- [ ]` todos, not chat-only prose. Not blocking this session's sports audit — the
  workaround (inline literals) let Phase 1 classification proceed normally.
- **na-eligibility-audit 2026-08-08** (ao tranche): RECLASSIFY — the sole `[DIAG] P3` todo is bounded/deterministic (run
  a minimal + a large `Workflow` `args` call, observe pass/fail, done-when is an objective repro-confirmed-or-ruled-out
  outcome; the follow-on doc-caution edit is a one-line addition to 4 named skill files, not a design call).
  Conflict-check cleared: 0 hits for `assigned_vm: planning` docs in `parent_epic: orchestrator_master` mentioning
  Workflow args/reproduction; 0 hits for a sibling batch/finalize doc claiming it; 0 overlap in
  `ao_open_issues_consolidated_close_out_2026_07_17.md`. Flipped `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`; corrected `assigned_role: data_engineering -> infra` (this
  touches no manifest/capture_status/GCS-writer code at all — data_engineering's stated scope — and is closer to general
  tooling/observability than any other craft role, matching the precedent `634dabc01` set for an analogous
  not-data-pipeline-work retag). Issue doc under `plans/active/issues/` — exempt from the finalize-plan-coverage rule,
  no companion finalize doc needed.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **slot-6 (data_engineering worker, adopted infra craft) 2026-08-16**: Reproduced with two live `Workflow` calls — a
  44-byte object `{a: 1, b: [1, 2, 3]}` and a 16.3KB object mirroring the original shape (66 `candidates` + 15
  `coveringPaths`). **Root cause confirmed, NOT size-gated**: in both calls `typeof args` was `"string"` inside the
  script body — the object passed via the tool's top-level `args` parameter arrives as a JSON-encoded STRING, never a
  parsed/live object, regardless of payload size (44B and 16.3KB both stringified identically). The large-payload repro
  threw the byte-for-byte SAME error as the original report:
  `TypeError: undefined is not an object (evaluating 'args.coveringPaths.map')` — because a string has no
  `coveringPaths` property, `.map` throws exactly this way. This contradicts the `Workflow` tool's own documented
  contract ("Pass arrays/objects as actual JSON values in the tool call, NOT as a JSON-encoded string") — the tool
  claims live-object binding but this harness's tool-call transport in fact always stringifies an object/array `args`
  value; the fix at the call site is `JSON.parse(args)` as the script's first line, or skip `args` and inline the data
  as JS literals (the original workaround). **Correction to this todo's own premise**: only `ag-closeout-audit`
  actually invokes the `Workflow` tool today (`SKILL.md` § "Phase 1") — `na-eligibility-audit`, `plan-reconcile`, and
  `docs-reconcile` use plain `Agent`/sub-agent fan-out, not `Workflow`+`args` at all (grepped all four SKILL.md files,
  0 hits for "Workflow" in the latter three), so the "several other scheduled skills... document the identical pattern"
  claim in this doc's `## Why this is worth tracking` section was stale/inaccurate — no caution added to those three.
  Added the caution to `ag-closeout-audit/SKILL.md` § "Phase 1" (unified-trading-pm). This is a harness/tool-level
  defect outside this repo's control to fix directly (no product-bug channel available from this session), so the
  actionable within-repo deliverable — the caution on the one skill that actually uses the pattern — is the closure.
  Archiving this issue doc same-commit (single-repo case, sanctioned per RULES.md § 2).
