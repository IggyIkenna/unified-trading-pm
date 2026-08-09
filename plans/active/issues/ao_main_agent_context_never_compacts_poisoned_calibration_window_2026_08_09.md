---
doc_type: issue
title: MAIN ran to 99% context with the compaction safety net silently disarmed — a poisoned learned context window
summary: >-
  orch-agent-main sat at 99% context for hours while every threshold in context_lifecycle stayed silent: a 4.3h
  /api/activity window held 132 context-lifecycle events for role=worker and exactly 1 for role=main. Root cause:
  context_probe.observe() accepts pane_pct as an EXACT calibration source and latches tokens/(pct/100) into
  calibrated_window — monotonic, top-precedence, never re-validated — but its callers passed derive_context_used_pct(),
  whose third branch is a HEURISTIC (a mid-spinner token readout over an ASSUMED 1M window). claude-sonnet-5 ended up
  with calibrated_window=2,614,639 against a ~937K reality, so main's real 99% measured 26% and no threshold fired. It
  hit main and spared the fleet because workers keep a self-reported SlotRow floor and main, having no SlotRow, had only
  the poisoned probe. Code fix shipped; live validation and the codex update remain.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, main-agent, measurement, worker-lifecycle]
related:
  [
    /plans/active/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md,
    /plans/active/issues/ao_learned_context_window_registry_never_revalidates_2026_08_09.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator observation 2026-08-09 ("why is the AO main agent 99% context without getting pre-compact and compact run
  yet"), root-caused in an interactive session (slot 4) against the live VM via read-only SSM.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# MAIN ran to 99% with the compaction safety net silently disarmed

## Live evidence (orchestrator VM, 2026-08-09, read-only SSM)

`GET /api/activity?limit=4000` — a 4.3-hour window (10:49Z → 15:09Z):

| role   | context-lifecycle events                                             |
| ------ | -------------------------------------------------------------------- |
| worker | **132** (`forced_precompact` / `forced_compact` firing at pct=60-65) |
| review | **0**                                                                |
| main   | **1** (a single client-side `context_compact_observed` at 12:31:44Z) |

`proactive_compact_guidance` = **0** across every role for the whole window.

Probing `orch-agent-main` directly:

```
snapshot: ContextSnapshot(model='claude-sonnet-5', tokens=675022, stale_after_compaction=False)
learned window for claude-sonnet-5 = 2614639     <-- true window ~937K
-> computed pct: 26                              <-- AgentRow.context_used_pct = 99
```

## Root cause

`context_probe.observe(model, tokens, pane_pct=...)` treats `pane_pct` as AUTHORITATIVE — the exact denominator the CLI
is dividing by — and writes `tokens / (pane_pct/100)` into `calibrated_window`. That field is monotonic, outranks the
watermark and the `model_tier` prior, and is never re-validated, so a single bad write is permanent and fleet-wide.

Both call sites fed it `derive_context_used_pct()`, which has three branches:

1. `_CONTEXT_USED_RE` — "98% context used", CLI-rendered, authoritative ✅
2. `_AUTO_COMPACT_RE` — "3% until auto-compact", CLI-rendered, authoritative after inversion ✅
3. `_TOKEN_USAGE_RE` — "↑ 250.0k tokens" divided by a hardcoded `_DEFAULT_CONTEXT_WINDOW_K = 1000` ❌ **a guess**

Branch 3 calibrates the window against an assumption about the window. Arithmetic confirms it exactly:
`2,614,639 × 0.26 = 679,806` — a `pane_pct=26` recorded when the session held ~679,806 tokens.

**Why main and not the fleet.** `_read_pct` gave workers `max(SlotRow.context_used_pct, probe)` — their self-reported DB
value still carried the truth, so their forces kept firing at 60% throughout. main is the only target with no `SlotRow`,
and it had no self-reported floor at all: only the poisoned probe. Its `AgentRow.context_used_pct = 99` — the CLI's own
figure, which main reports every tick — was never consulted by the policy.

## Fix (shipped, agent-orchestrator → LDR)

- `worker_liveness`: `derive_calibration_pct()` split out of `derive_context_used_pct()` — CLI-rendered percentages
  ONLY. Both calibration call sites now pass the authoritative value; the heuristic remains a READING.
- `context_probe`: `_calibration_is_plausible()` — a calibration may not exceed 1.5× the larger of the `model_tier`
  prior and the observed watermark. Defense-in-depth that does not depend on every future caller getting the source
  right.
- `context_lifecycle`: `_main_pct()` floors the measured probe on main's own `AgentRow` self-report (mirroring the
  worker ratchet, persisted upward); `_pane_readings()` takes one pane capture per tick instead of two.

Acceptance verified against the PRE-fix arithmetic: it latches 2,614,638 and reports 26% (exactly the live figure);
post-fix reports 68%. Tests: `tests/test_context_probe.py::test_the_measured_poisoning_case_is_rejected` and siblings.

## Remaining todos

- [x] ✅ [BACKEND] P0. Confirm the fix is LIVE on the orchestrator VM, not merely merged: the running uvicorn process
      must be on a revision containing `derive_calibration_pct`. Done-when: `_calibration_is_plausible` is importable
      from the VM's running checkout AND a fresh `/api/activity` window shows `proactive_compact_guidance` or
      `forced_precompact` for `role=main`. — **CONFIRMED LIVE 2026-08-09 (slot 22, backend_engineer)**, verified
      directly on the orchestrator VM (this session's slot host resolves to `i-0c9b283b31d6b5ca7` — no SSM needed). (1)
      The real serving process (`pid=4182514`, `uvicorn server.server:app`, cwd
      `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` — the root clone, NOT a slot worktree) is on HEAD
      `a272e95`, which contains fix commit `bd7ff0a` as an ancestor; process start time 2026-08-09T16:30:30Z is AFTER
      the fix commit's 2026-08-09T15:43:21Z landing. Ran
      `./.venv/bin/python3 -c "from server.context_probe import     _calibration_is_plausible; from server.worker_liveness import derive_calibration_pct"`
      against that exact repo + venv — import succeeded (both symbols resolve). (2) `GET /api/activity?limit=4000`
      (fresh window 2026-08-09T12:41Z → 17:08Z) — filtering on `details.role == "main"` (the role lives inside
      `details`, not a top-level field) found TWO `proactive_compact_guidance` events for `role=main`: one at 15:15:34Z
      (pct=69, before the running process's 16:30:30Z start — from the earlier out-of-band cache purge the Progress Log
      below already records) and, decisively, one AFTER the current process started: **16:47:56Z, pct=60**, each
      followed by a `context_compact_observed` (60→15% at 16:51:53Z; the earlier one 70→7% at 15:21:42Z) proving
      guidance actually drove a real compaction, not just a fired-and-ignored signal. The post-restart 16:47:56Z firing
      is the decisive evidence — it happened 17 minutes into the fixed process's own lifetime, not a leftover from
      before the deploy.
- [x] ✅ [BACKEND] P0. Audit the live `learned_context_windows.json` for any OTHER poisoned entry the same way
      claude-sonnet-5 was poisoned (compare each `calibrated_window` against that model's `model_tier` prior and
      watermark; anything past 1.5x is suspect). The claude-sonnet-5 entry was purged out-of-band on 2026-08-09.
      Done-when: every remaining entry is within the plausibility bound, recorded in the Progress Log. — **AUDITED
      2026-08-09 (slot 18, backend_engineer), no other poisoned entry found.** Full detail in the Progress Log below.
- [x] ✅ [BACKEND] P1. main's true window is ~696K (99% CLI-reported at 689,570 tokens), while the sonnet-5 `model_tier`
      prior is 1M and the corpus watermark is 937,882 — so even post-fix the probe under-reads main by ~30 points and
      only the AgentRow floor makes it accurate. Determine whether the effective window is per-account/per-session
      rather than per-model. Done-when: the finding is recorded and either the model is corrected or the divergence is
      documented as expected in `/codex/04-architecture/agent-orchestrator-worker-liveness.md`. — **DOCUMENTED
      2026-08-09 (slot 19, backend_engineer)**: account tier ruled out for THIS instance (main's account
      `sub-f-odum2default` is `max20`, same tier as most of the fleet that built the 937,882 watermark); `effort`/
      `thinking` depth (main runs `thinking: high` vs workers' `thinking: medium`) is the better-supported per-session
      driver. Documented as expected divergence, not a defect — the per-model registry is a cold-start fallback only,
      already correctly overridden by each target's own self-report floor (`_main_pct` for main, `SlotRow` for workers).
      No registry/model change made. Full detail in `/codex/04-architecture/agent-orchestrator-worker-liveness.md` §
      "Context-window learning is per-model; per-session divergence is expected and already floored".
- [ ] [DOCS] P1. Post-phase codex audit: fold the calibration-source contract (only CLI-rendered percentages may
      calibrate) and main's AgentRow floor into `/codex/04-architecture/agent-orchestrator-worker-liveness.md`.
      Done-when: the SSOT states both rules and cites this incident.

## Progress Log

- 2026-08-09 — Root-caused via read-only SSM against the live VM. Purged the poisoned `claude-sonnet-5`
  `calibrated_window=2,614,639` (the sidecar is documented as safe to lose; it re-converges from transcript reads); main
  immediately re-measured at 69%, above the 60% guidance threshold. Submitted `/compact` to `orch-agent-main` via the
  same verified-submit helper the backend's own forced path uses. Code fix authored, QG-green and shipped.

- **2026-08-09 (slot 22, backend_engineer)** — Closed the "confirm live" todo. This session's slot worktree turned out
  to already be running ON the orchestrator VM (`i-0c9b283b31d6b5ca7`), so verification was direct (no SSM round-trip
  needed): confirmed the real uvicorn process serves from the root `agent-orchestrator` clone at HEAD `a272e95`
  (post-dates fix commit `bd7ff0a`), test-imported `_calibration_is_plausible`/`derive_calibration_pct` against that
  exact process's venv (succeeded), and found a `role=main` `proactive_compact_guidance` firing at 16:47:56Z (pct=60) —
  17 minutes into the current process's own lifetime, so unambiguously post-deploy — followed by a
  `context_compact_observed` showing 60%→15%. Full detail on the todo line above.

- **2026-08-09 (slot 18, backend_engineer)** — Closed the "audit for other poisoned entries" todo. Same as slot 22
  above, this slot's worktree resolves directly onto the orchestrator VM (root `agent-orchestrator` clone at
  `/home/ubuntu/unified-trading-system-repos/agent-orchestrator`, HEAD `a272e95`), so the sidecar was read straight off
  disk — no SSM round-trip needed. Live content of `data/state/learned_context_windows.json`:

  ```json
  {
    "claude-opus-5": { "watermark_hits": 1, "watermark_tokens": 222121 },
    "claude-sonnet-4-6": { "calibrated_window": 173304, "watermark_hits": 4, "watermark_tokens": 165936 },
    "claude-sonnet-5": { "watermark_hits": 1, "watermark_tokens": 933770 }
  }
  ```

  Ran the actual `server.model_tier.context_window()` + the same `reference = max(prior, watermark)` /
  `_MAX_CALIBRATION_OVERSHOOT = 1.5` formula `context_probe._calibration_is_plausible()` uses, against the live venv,
  for every entry carrying a `calibrated_window` (the only field this audit's bound applies to — a watermark-only entry
  has no calibration to validate):
  - `claude-opus-5` — no `calibrated_window` (watermark-only, 222,121 tokens against a 1M prior) — nothing to check.
  - `claude-sonnet-4-6` — `calibrated_window=173,304` vs `reference=max(prior=200,000, watermark=165,936)=200,000` →
    ratio 0.867x — well inside the 1.5x bound. Plausible.
  - `claude-sonnet-5` — no `calibrated_window` (watermark-only, 933,770 tokens against a 1M prior) — confirms the
    poisoned entry from the root-cause section above really was purged out-of-band and nothing has recalibrated it since
    (the code fix now blocks a bad recalibration at write time regardless). **Conclusion: no other poisoned
    `calibrated_window` entry exists in the live registry.** Every entry is within the plausibility bound.

- **2026-08-09 (slot 19, backend_engineer)** — Closed the "per-account/per-session window" todo. This slot also resolves
  directly onto the orchestrator VM (root `agent-orchestrator` clone, HEAD `a272e95`). Read
  `agent-orchestrator/data/config/accounts.json` on disk: 6 anthropic-provider accounts, 5 on tier `max20`
  (`sub-b-iggy2london`, `sub-c-ikenna-odum`, `sub-d-odum1default`, `sub-e-odum2default`, `sub-f-odum2default`) and 1 on
  `pro` (`sub-a-ikenna`). Queried the live `AgentRow` table for `role='main'`: the currently-online main (`agt-222944`)
  runs under `sub-f-odum2default` — `max20`, the same tier as the majority of fleet accounts, ruling out a downgraded
  account tier as the cause of the specific 696K-vs-937,882 gap this todo names. Compared `agents/main.md`
  (`thinking: high`) against `agents/worker.md` (`thinking: medium`) frontmatter — a real, confirmed per-role
  effort/thinking difference between main and the mostly-worker population that built the sonnet-5 corpus watermark, and
  the best-supported explanation for main's own CLI-reported "full" landing at a lower absolute token count than the
  corpus watermark. Recorded the full finding (registry design, account-tier check, effort/thinking hypothesis, and why
  no registry/model change is needed given the existing self-report floor) as a new section in
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md` — done-when satisfied via the "documented as expected"
  branch, not a model correction.
