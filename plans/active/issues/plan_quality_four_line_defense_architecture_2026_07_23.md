---
doc_type: issue
title: >-
  Plan-quality four-line-of-defense architecture — task_template.md as line 1, plan-hygiene baked into QG as line 2,
  /plan-reconcile as a 24h background AO agent as line 3, /docs-reconcile keeping codex fit-for-agent-consumption as
  line 4
summary: >-
  Operator-directed architecture request (2026-07-23, mid-session on sports_consolidated_closeout_2026_07_19.md's
  hygiene audit): task_template.md should already encode pretty much everything /plan-reconcile checks, so authoring a
  plan correctly is the FIRST line of defense (a local, pre-write check). Plan hygiene (run_hygiene_sweep.sh) should be
  baked into quality-gates.sh as the SECOND line (an automated, every-QG-run check). /plan-reconcile should run as a
  background AO agent every 24h, reporting success and asking operator questions in AO when needed, as the THIRD line.
  /docs-reconcile (codex health) is the FOURTH line, since agents read codex for guidance and bad codex formatting means
  agents don't get the info they need; /plan-reconcile should also ensure plans align with codex content, not just
  plan-internal consistency. Target: never have a plan so badly formatted for AO that it doesn't get completed properly,
  and background checks ensuring plans/issues never conflict with each other in content.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    plan-quality,
    task-template,
    plan-hygiene,
    quality-gates,
    plan-reconcile,
    docs-reconcile,
    ao-dispatch,
    background-agent,
  ]
related: [plans/active/task_template.md, plans/PLAN_FORMAT.md, plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-07-23"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [operator request, sports_consolidated_closeout hygiene audit session 2026-07-23]
resolved_by:
locked_by:
depends_on: []
---

# Plan-quality four-line-of-defense architecture

## Why this exists

While auditing `sports_consolidated_closeout_2026_07_19.md` for AO-dispatch-readiness (2026-07-23), two things surfaced
in the same session: (1) a hygiene sweep + several quality-gate scripts caught real, fixable defects (missing
frontmatter fields, a stale line-cap exemption with no ceiling, a model-tier heuristic that no longer matched the
operator's actual policy) — but only because a human/agent happened to run them manually; (2) a second, independent
adversarial review of the SAME plan's content found 7 more classes of AO-dispatch-breaking defects
(first-line-truncation gutting instructions, contradictory ordering rules, stale checkboxes, undefined section
shorthand, ambiguous "absorb" instructions, inconsistent delete-risk tagging, missing definitions-of-done) that none of
the existing automated checks catch at all — `/plan-reconcile` is the tool built to catch exactly that class, but
nothing runs it automatically.

**The operator's ruling**: this should not depend on someone remembering to run the right tool at the right time. Four
layers, each catching what the previous layer misses, each backing up the one before it failing:

## The four lines of defense

1. **`plans/active/task_template.md` — LOCAL, pre-write check (line 1).** The template an author reads BEFORE writing a
   plan should already encode, as directly-followable rules, pretty much everything `/plan-reconcile` checks for after
   the fact — line-1-truncation discipline (§3 already has this — audit whether it's followed in practice),
   ordering-dependency encoding (`sequential:`/`depends_on`+`gate_on_depends`, not prose — §4 already has this too),
   stale-checkbox discipline, section-shorthand-must-be-spelled-out, ambiguous-instruction bans, delete-risk tagging
   consistency, and a definition-of-done convention. **Todo**: audit `task_template.md` against the 2026-07-23
   adversarial-review findings (see `sports_consolidated_closeout_2026_07_19.md`'s new "Track Y — PLAN-QUALITY
   REMEDIATION" section for the concrete finding list, findings A/B/D/E/F/G) and add/tighten any rule that isn't already
   there in a form an author would actually apply while writing, not just retrospectively.
2. **Plan hygiene baked into quality gates — automated, every-QG-run check (line 2).** `run_hygiene_sweep.sh` currently
   runs manually (a documented "morning step") or via the `--precommit` staged-files gate. **Todo**: wire the FULL sweep
   (not just `--precommit`'s 3 local checks) into `quality-gates.sh` for the `unified-trading-pm` repo specifically (or
   a dedicated PM-repo QG slice) so a plan/codex-touching change cannot land without the full hygiene sweep passing —
   not just the fast pre-commit subset. Needs a decision on whether this should be `--ci` mode (hard-fails the QG run)
   or advisory-only for the soft checks (matches the sweep's own hard/soft split). **Todo**: decide + implement.
3. **`/plan-reconcile` as a 24h background AO agent — content-level cross-doc check (line 3).** Hygiene (line 2) checks
   structure/format; `/plan-reconcile` checks CONTENT — cross-doc contradictions, done-but-unchecked todos, stale claims
   a later section of the same doc already superseded (exactly what the adversarial review's finding C caught).
   **Todo**: wire `/plan-reconcile` into a scheduled background AO agent (cron-style, every 24h — see the `schedule`
   skill / `CronCreate` tool) that runs the skill's own audit → adversarially-verify → auto-fix-mechanical →
   batch-operator-Q&A flow, reports success/failure to the operator (Slack or the AO alerts channel, per
   `/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only convention — a clean run is a digest item,
   a genuine operator-decision-needed batch is an actionable page), and asks operator questions IN AO (the dashboard Q&A
   mechanism, not a chat message) when a finding needs an authority call rather than a mechanical fix. **Open question
   for the operator**: which AO mechanism should own the schedule — a literal cron
   (`CronCreate`/`scripts/self-hosted-runners/hosted-baseline/plan-health-agent.yml` already exists as a candidate home,
   check it first) vs. a role-dispatched recurring task the orchestrator's role registry owns. **Todo**: research the
   existing `plan-health-agent.yml` (found during this session's script search, never inspected) — it may already be
   exactly this, just unwired/unverified-live, before building a new mechanism from scratch.
4. **`/docs-reconcile` — codex fitness-for-agent-consumption (line 4).** Agents read codex for guidance; if codex
   frontmatter/summary/`authoritative_for` is malformed or a doc's body drifted from what its own banner claims (the
   EXACT failure class this session found on 6 sports codex docs before fixing them), agents get bad guidance even when
   the PLAN itself is perfect. **Todo**: `/plan-reconcile` should explicitly check plan↔codex CONTENT alignment as part
   of its own scope (its own description already says "Plan↔codex drift is in scope"), not just defer entirely to
   `/docs-reconcile`'s codex-internal-health scope — clarify/confirm the boundary: `/docs-reconcile` owns codex-internal
   structural health (schema/generator drift, authoritative_for collisions, placeholder summaries); `/plan-reconcile`
   owns whether a PLAN's claims about what codex says are still true. Both should run on the same 24h background cadence
   (line 3) so drift in either direction gets caught within a day, not whenever someone happens to invoke either skill
   manually.

## Target state

- No plan can be authored so badly-formatted-for-AO that it silently fails to complete (line 1 catches it at write-time;
  line 2 catches it mechanically at commit-time as a backstop).
- No plan/issue-doc pair can silently drift into contradiction for more than 24h (line 3's background cadence).
- No codex doc can silently drift from what plans claim it says for more than 24h (line 4, paired with line 3).
- All 4 lines report clearly enough that a human never has to manually remember to run any of them.

## Key clarification (2026-07-23): line 2 vs line 3 catch different defect classes, by design

Findings A/D/E/F/G (first-line truncation, bare section-shorthand, ambiguous verbs, delete-tagging inconsistency,
missing definition-of-done) are **content-judgment defects** — there is no deterministic script that can grep for "does
line 1 contain the complete instruction," since that requires understanding what the instruction actually means. Do NOT
try to add these to `run_hygiene_sweep.sh` (line 2) — that line is for mechanically-checkable structure (frontmatter,
todo format, line caps, `depends_on` cycles), and belongs there because it IS deterministic. Findings A/D/E/F/G are
correctly line 3's job (`/plan-reconcile`, LLM-based) — `plan-reconcile/SKILL.md` now has an explicit "AO-dispatch-
readiness hunters" pass (added 2026-07-23) checking every open todo against `task_template.md` §3's rules for exactly
these 5 classes, closing the loop between line 1 (author-time prevention) and line 3 (catch what slipped through)
without inventing a second spec. Finding C (stale checkboxes) was already Phase 2's job, unchanged.

## Todos

- [x] [DOC] P1. ✅ **DONE 2026-07-23** — `task_template.md` §3 now has explicit rules for findings D (no bare cross-doc
      §-shorthand), E (literal-action verbs, ban "absorb"/"incorporate"), F (delete-risk tagging consistency), G (stated
      definition-of-done), and C (check-before-adding a stale-checkbox pre-write habit); A and B were already
      well-covered (line-1-truncation §3, `sequential:`/`depends_on` ordering §4) — verified by re-reading both before
      editing, not assumed. `pm@<commit-pending>`.
- [x] [DOC] P1. ✅ **DONE 2026-07-24 (2 new findings, H/I) — surfaced by manually building + then AO-flip-safety-
      auditing the 5 asset-group consolidated close-outs (tradfi/defi/cefi/prediction/sports), a pattern §3/§4 didn't
      yet cover.** `task_template.md` §3 now also has: **finding H** — a digest of ANOTHER plan's todos (the
      "referenced, not duplicated" discoverability pattern an umbrella coordinator plan uses) must NEVER use real
      `- [ ]` checkbox syntax, verified via direct code read of `regen_backlog_from_plan.py`'s `_UNCHECKED_RE`
      (indentation-agnostic — a nested digest checkbox parses exactly like a real dispatchable one, risking double-
      dispatch + cap-busting + drift the moment the plan is flipped to `assigned_vm: planning`); use a bold
      `- **[TAG] P<n>.**` marker instead. **finding I** — forking a section out of an over-cap plan into a child plan
      (the `umbrella: true` split pattern) must encode the real ordering constraint as `depends_on:` +
      `gate_on_depends: true` in the SAME edit, not leave it as header prose ("gated on T1→T3") that's invisible to the
      dispatcher. Both found live (unencoded) in 3 of the 5 consolidated close-outs during this session's audit and
      fixed directly: tradfi/defi got real `depends_on`+`gate_on_depends` wiring; cefi's Track 7 delete-after- verify
      todo (a genuine prod-GCS permanent-data-loss risk if it raced ahead of its own verify step under AO's
      same-priority concurrent-dispatch default) got tagged `[OPERATOR]` per finding F. `pm@<commit-pending>`.
- [ ] [SCRIPT] P1. **Operator ruling 2026-07-23: hard-fail on EVERY check (not the hard/soft split), gated on a
      prerequisite** — wire the full `run_hygiene_sweep.sh` into `quality-gates.sh` for `unified-trading-pm` with ALL
      checks (including the currently-"soft" ones: line caps, estimate sanity, superseded-in-active, codex refs,
      parent-epic alignment, CLAUDE↔SUB_AGENT parity) blocking the commit, matching the sweep's `--ci` exit-1 behavior
      but extended past just the 7 currently-hard checks. **Prerequisite, NOT done here**: the sweep scans the WHOLE
      `plans/active/` corpus, not just a commit's touched files — measured 2026-07-23, 30 pre-existing plans already
      violate `check_line_caps.sh`'s own internal hard threshold (23 non-umbrella >1000L, 7 umbrella >2000L, e.g.
      `sports_manifest_canonicalisation_2026_06_01.md` at 4733L; full list via
      `bash scripts/plan-hygiene/check_line_caps.sh`), plus 19 more in the 500-1000L soft range — a blanket flip today
      would immediately block every future plan-touching commit workspace-wide on debt nobody just created. **Operator
      chose to fix all 30 first, then flip** (not the ratchet-baseline alternative, and not scoping the gate to
      touched-files-only) — this prerequisite is its own separate body of work (each of the 7 umbrella plans has 100+
      todos and needs a real split, not a trim) and should be tracked as its own plan before this todo can ship. All 6
      other currently-soft checks are already at 0 corpus-wide violations (verified 2026-07-23,
      `run_hygiene_sweep.sh --ci --no-regen`) and can flip to hard-fail immediately, independent of the line-caps
      prerequisite. **Progress check 2026-07-24 (slot 2)**: re-ran `bash scripts/plan-hygiene/check_line_caps.sh` — down
      to **13 plans still HARD** (from 30), so `plan_line_cap_remediation_2026_07_23.md` (still `status: open`) has made
      real progress but the prerequisite is not yet clear. This todo still cannot ship. **Progress check 2026-07-24
      (later same day, tradfi/defi/cefi/prediction/sports consolidated-closeout remediation session)**:
      `bash scripts/plan-hygiene/check_line_caps.sh` now shows **10 plans still HARD** (down from 13) — this session
      trimmed/umbrella-exempted the 5 asset-group consolidated close-outs, which were among the over-cap set. Still not
      zero; `plan_line_cap_remediation_2026_07_23.md` remains the tracked owner of the remaining 10. Also found and
      fixed a real blind spot in `check_estimate_sanity.sh` while re-running the full sweep: it silently skipped a plan
      whose `estimate_class` was set but one of `estimate_baseline_ai_days` / `estimate_calibrated_ai_days` was
      genuinely blank (only ever compared two numbers that were both already present) — now reports these as a `MISSING`
      finding (still soft/exit-0, matching this check's own documented behavior; corpus-wide re-run after the fix: 0
      missing, 2 pre-existing >20% drift, unrelated to this session's files) — `pm@<commit-pending>`.
- [x] [INFRA] P0. ✅ **Research DONE 2026-07-23 — line 3 is MOSTLY ALREADY BUILT; extend, do not rebuild.** Found:
      `scripts/self-hosted-runners/hosted-baseline/plan-health-agent.yml` (+ its rollout-committed twin
      `.github/workflows/plan-health-agent.yml`) is a GHA workflow (daily cron `0 2 * * *` + PR gate) whose own header
      says its Haiku-based drift-detection step is a placeholder — the REAL migration already shipped:
      `agent-orchestrator/server/plan_health.py`'s `dispatch(mode="reconcile")` spawns `agents/plan_reconciler.md`
      (opus/max/thinking-on), fired by a genuine **systemd timer**
      (`agent-orchestrator/scripts/install-plan-reconciler-timer.sh` → `plan-reconciler.timer`,
      `OnCalendar=*-*-* 01:00:00 UTC`) hitting `POST /api/plan-health/dispatch`, watched by a dedicated
      `plan_reconciler_liveness_canary.py` that pages if the timer goes inactive or no successful run lands in >26h.
      **This IS the 24h background `/plan-reconcile`-class agent line 3 asked for — it already runs daily.** The one
      real gap: `plan_health.py::record_result()` routes `doc_drift` (the operator-decision-needed half) to a plain
      Slack message (`slack_notify.notify_plan_health_findings`, deduped by a `_drift_key` seen-set) rather than AO's
      structured dashboard BLOCKED-question surface (`notify_slot_blocked`, which renders question+options+
      recommendation and gets an explicit ✅-close bookend) — `contradictions` findings already route silently to a
      `reconciler_candidate` feed correctly (no page, consumed by the next reconcile run), matching the actionable-only
      convention. AO has no separate generic cron/`CronCreate` registry — recurring work is done via per-purpose systemd
      timers hitting dedicated dispatch endpoints, supervised by the daemon-thread `LoopSupervisor`
      (`server/loop_supervisor.py`); that's the pattern to extend, not a new scheduler.
- [x] [INFRA] P1. ✅ **DONE (agent-orchestrator@18f262e, confirmed live 2026-07-24 slot 2)** — routed
      `plan_health.py::record_result()`'s `doc_drift` findings through the AO dashboard's `notify_slot_blocked`
      BLOCKED-question surface. Each NEW `doc_drift` key now also gets a synthetic `BlockedRow` (`slot_id=0`, the same
      "plan-level, no worker slot" sentinel `bootstrap.py` uses for operator-gated todos) via `state_store.add_blocked`,
      visible through `blocked_queue` (`GET /api/state` / `/api/blocked/*`), plus a `notify_slot_blocked` Slack ping —
      additive, the existing `notify_plan_health_findings` Slack path is unchanged. Verified present in the current
      `live-defi-rollout` checkout (`.tabs/2/agent-orchestrator/server/plan_health.py` lines ~552-628). No NEW doc_drift
      finding has fired since this shipped (all recent `doc_drift_open` activity predates 18f262e), so the live
      blocked-queue path itself hasn't been end-to-end exercised by a fresh finding yet — the code path is confirmed
      present and reachable, not yet observed firing on real drift.
- [x] [INFRA] P2. ✅ **DONE (agent-orchestrator@329571e + interactive SSM install, confirmed live 2026-07-24 slot 2)** —
      `/docs-reconcile` is wired onto the same 24h cadence as line 3. `docs-reconciler.timer` confirmed
      `active (waiting)`, `enabled`, `Trigger: Sat 2026-07-25 02:04:22 UTC` via `systemctl status docs-reconciler.timer`
      on the orchestrator VM this session; a manual proof-dispatch already fired successfully today
      (`plan_health_dispatched` slot 2, `dispatch_id=agt-763781`, 07:25:09 UTC, `agent_kind=docs_reconciler`). The
      timer's own first natural (cron-triggered, not manually dispatched) elapse hasn't happened yet — that's expected,
      it isn't due until 2026-07-25 02:04 UTC. Plan↔codex-content-alignment boundary is documented in this doc's § "The
      four lines of defense" item 4 (`/docs-reconcile` = codex-internal structural health; `/plan-reconcile` = whether a
      plan's claims about codex are still true) — no further clarification needed.
- [ ] [REVIEW] P2. Once lines 2-4 are live, re-run the sports closeout hygiene audit end-to-end and confirm all 4 lines
      would have caught what the two manual/adversarial passes caught this session, as the acceptance test for this
      whole initiative. **RE-CHECKED 2026-07-24 (slot 2), verdict = 3/4 LIVE, line 2 NOT live — precondition still
      unmet.** Lines 1, 3, 4 confirmed live this session (see their todos above +
      `/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md` item 14's parallel check). Line 2
      (hygiene-sweep hard-fail wired into `quality-gates.sh`) is confirmed NOT wired —
      `grep -n run_hygiene_sweep scripts/quality-gates.sh` returns nothing — and its own prerequisite (fix the over-cap
      plans) is still open: a fresh `bash scripts/plan-hygiene/check_line_caps.sh` run today shows **13 plans still
      HARD-violating** the 1000L/2000L-umbrella cap (down from 30 at this todo's authoring, but not zero — see
      `plan_line_cap_remediation_2026_07_23.md`, still `status: open`). A full `run_hygiene_sweep.sh --ci --no-regen`
      run today confirms the current state: 0 hard failures / 1 soft warning (line caps), matching the prerequisite's
      own "0 corpus violations on the other 6 currently-soft checks, line-caps is the sole blocker" framing. Since the
      Gate requires **all four** lines producing their expected signal and line 2 structurally cannot fire while
      unwired, this item stays open rather than being force-closed on 3/4 — **re-open this exact check once
      `plan_line_cap_remediation_2026_07_23.md` finishes and this SCRIPT todo ships.**

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/11-project-management/doc-frontmatter-schema.md`. No
existing codex SSOT names this 4-line architecture itself — once lines 2-4 are actually wired, add one (likely under
`codex/11-project-management/` or `codex/12-agent-workflow/`).
