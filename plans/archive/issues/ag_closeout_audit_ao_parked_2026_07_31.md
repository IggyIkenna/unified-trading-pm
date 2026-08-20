---
doc_type: issue
title:
  "ag-closeout-audit ao tranche 2026-07-31 — parked findings (data-correctness contradiction + non-AO-eligible orphans)"
summary: >-
  Durable park for findings surfaced by the `/ag-closeout-audit ao` scheduled run (2026-07-31, dispatch agt-23935a) that
  don't belong in `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s own Deferred section content but still need a
  durable home per the skill's "parked findings always get a durable issue doc" rule. One genuine data-correctness /
  SSOT-adjacent fact contradiction (a doc's own "what's true today" claims proven false by live measurement) plus two
  already-documented non-AO-eligible orphans (cross-referenced from the batch's own Deferred section, restated here for
  the standalone-doc requirement).
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, parked-findings, data-correctness, ssot-contradiction]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/archive/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md,
    /plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-31
last_updated: "2026-07-31"
parent_epic: agent_operating_framework_master
priority: P1
source: >-
  /ag-closeout-audit ao skill run 2026-07-31 (autonomous, scheduled dispatch agt-23935a, role ag_closeout_auditor, slot
  5) — Phase 0-3, per the skill's "Parked findings ALWAYS get a durable issue doc" rule (2026-07-30 addition).
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
resolved_by: "doc-correction shipped 2026-08-01 (context_scope_consumption_enforcement_2026_07_30.md); Finding 2 items require no action"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/context-scout/SKILL.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
drift_direction: advance-code
---

# ag-closeout-audit ao tranche 2026-07-31 — parked findings

> **🟢 RESOLVED 2026-08-02** — Finding 1's doc-correction shipped 2026-08-01 (`context_scope_consumption_enforcement_2026_07_30.md`); Finding 2's items are "no action needed unless the operator lifts the ruling," reconciliation ledger confirms 3/3 findings written and balanced.

## Finding 1 — data-correctness / SSOT-adjacent contradiction (the operator-notify-worthy one)

`/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today (2026-07-30)" section
(lines 46-51) asserts, as established fact:

> "Every `plans/active/*.md` + `plans/active/issues/*.md` doc carries a `context_scope` frontmatter field... The field
> is now REQUIRED (`docspec.py`, `plan`/`issue` doc_types) and `check_frontmatter_schema.py` fails PM QG on a missing
> one — so the corpus stays covered going forward, and the `context-scout` skill keeps it fresh as docs are
> authored/edited."

**Both claims are measurably false as of this run (2026-07-31):**

1. **"now REQUIRED"** — `scripts/docs/docspec.py:136` (doc_type `plan`) and `:160` (doc_type `issue`) both still read
   `FieldSpec("context_scope", Req.E, "free_list")` — `Req.E` (elective), not `Req.R` (required). Verified by direct
   read, not grep-and-assume.
2. **"backfilled the corpus"** — a live run of `generate_context_scope_inventory.py --json` this session reports **626
   in-scope docs, 616 `NEVER_SCOUTED`, 10 `STALE`, 0 `UP_TO_DATE`**. This is the opposite of "backfilled" — the
   corpus-wide sweep has barely started. This matches
   `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`'s own still-open `[SCRIPT] P0` todo (now
   dispatched as `ao_satellite_ao_dispatch_batch3_2026_07_31.md` todo 1), which independently confirms the backfill is
   real, uncovered, remaining work — not a completed fact.

**Why this matters beyond one wrong sentence**: `/na-eligibility-audit` reviewed
`context_scope_consumption_enforcement_2026_07_30.md` on 2026-07-31 (dispatch `agt-676f1e`) and verdicted "KEEP-NA,
valid" — a correct verdict on ITS OWN terms (that doc's two open todos are genuinely a judgment call, unaffected by
whether the premise is true), but the review did not catch that the doc's stated justification for why its scope is
narrow ("the backfill work... is a bounded, already-complete unit") rests on a false premise. Downstream, anyone reading
this doc to understand corpus state (not just its own todos) would be misled into believing the field is both complete
and enforced. This is exactly the class of drift `/plan-reconcile`'s corpus-wide contradiction sweep exists to catch —
it just hadn't reached this doc yet.

**Not fixed by this audit** (out of `/ag-closeout-audit`'s scope — this skill classifies AO-tranche coverage, it does
not correct prose-level factual drift in a sibling doc; that is `/plan-reconcile`'s job, or a small bounded direct edit
by whoever picks this up next).

- [x] [DOCS] P1. **Correct `context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today" section to match
      measured reality** — replace the false "REQUIRED"/"backfilled" claims with the actual state (`Req.E`, 616/626
      `NEVER_SCOUTED`), citing this doc + the live inventory command output as evidence. Re-run
      `generate_context_scope_inventory.py --json` fresh at fix time (the count will have moved once
      `ao_satellite_ao_dispatch_batch3_2026_07_31.md` todo 1 starts landing) rather than copying this doc's numbers
      verbatim. **Done when**: the corrected section cites a freshly-run inventory count + the direct `docspec.py` line
      read, and no longer claims the backfill/hardening is done. This is a small, bounded, single-doc prose correction —
      AO-eligible in isolation, but held here rather than folded into batch3 because it touches a DIFFERENT doc than any
      of batch3's 3 todos and doesn't need to block on them landing first. ✅ 2026-08-01 — corrected in
      `context_scope_consumption_enforcement_2026_07_30.md` (fresh docspec.py read: `Req.E` at lines 139/163; fresh
      inventory run: 647 total / 410 `NEVER_SCOUTED` / 15 `STALE` / 222 `UP_TO_DATE`) — unified-trading-pm@pending.

## Finding 2 — orphaned, genuinely not AO-eligible (restated per the standalone-doc requirement; full reasoning lives in `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Deferred section)

- `/plans/archive/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`'s sole open `[REVIEW] P3`
  item (host-resource dashboard/alerting surfacing `MemoryAvailable`/cgroup-vs-host RAM mismatch) is self-assessed real
  feature-sized, cross-repo work (new agent-orchestrator backend reader + new deployment-ui dashboard tile with its own
  `pw:L2` regression spec) — not a bounded AO todo. Candidate for `/plan-brainstorm` to scope properly.
- `/plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md` — 7 open todos that individually read AO-dispatch
  grade, but the doc carries an explicit, session-fresh operator ruling to stay `assigned_vm: NA`/human-only. Drafting a
  batch todo would override a recorded operator decision. No action needed unless the operator lifts the ruling.

## Reconciliation ledger

`parked_findings = 3` (the data-correctness contradiction + the 2 non-AO-eligible orphans) `==`
`entries_actually_written_to_this_doc = 3`. Balanced.

## Progress Log

- **2026-07-31** — Filed by `/ag-closeout-audit ao` (autonomous mode, scheduled dispatch agt-23935a, slot 5) per the
  skill's "Parked findings ALWAYS get a durable issue doc" rule, since this run reached Phase 3 (batch3 drafted) but
  Finding 1 doesn't belong inside the batch's own Deferred section (it's not AO-batch material touching batch3's files,
  it's a standalone factual correction to a different doc).
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): RECLASSIFY
  `NA -> planning`. The sole open item (line 92, single-file prose correction to
  `context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today" section) is fully worker-determinable —
  grep/read two facts, rewrite one paragraph, cite evidence; no design/judgment fork, no `[OPERATOR]` tag, no
  live-VM/host/credential access needed. Phase 2 conflict-check clear:
  `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md` (active `assigned_vm: planning`) references this doc's
  finding only as a "confirm whether it has been corrected, escalate again if not" verification checkpoint — not a
  competing claim on the same fix, and this reclassification is what lets that checkpoint actually resolve.
  `assigned_role` left unset (no clean match in the live `agents/*.md` registry for a single prose-fix todo; per-task
  `[DOCS]` tag routing applies instead per RULES.md).
- **context-scout 2026-08-01**: verified pre-existing context_scope (3 entries) — all 3 paths confirmed resolving on
  disk, left unchanged.
