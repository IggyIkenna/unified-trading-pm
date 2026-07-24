---
doc_type: issue
title:
  "test_plan_health.py tests that mock add_blocked but not notify_slot_blocked fire REAL Slack posts to
  agent-orchestrator-alerts on every fleet-wide pytest run — confirmed root cause of a live 237-message/3h flood with
  fake, nonexistent blocked_ids"
summary:
  Downloaded the live agent-orchestrator-alerts Slack channel (last 3h, via SLACK_ALERTS_READER_BOT_TOKEN,
  operator-supplied) to root-cause an operator complaint about repeating alerts. Found 237 messages in 3 hours, the top
  signatures being plan_health doc_drift BLOCKED-question pages for CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md with claim
  text — x, already seen, drift Z, rule X contradicted, tab-branch retired, y — that are byte-for-byte the literal test
  fixtures in tests/test_plan_health.py. Confirmed mechanism — 3 tests patch server.plan_health.add_blocked (so no fake
  DB row is written; checked live, zero doc_drift-prefixed rows exist in the real blocked_queue) but do NOT patch
  server.notifications.slack.notify_slot_blocked, which record_result() calls via a fresh in-loop from .notifications
  import slack — bypassing the patch.multiple("server.plan_health", ...) scope entirely. Every real pytest run of these
  3 tests anywhere in the fleet (which happens constantly — quality-gates.sh runs the full suite before every commit)
  fires a real Slack POST referencing a fake blocked_id that answers nothing if clicked.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, test-isolation, slack, plan-health, alerting]
related:
  [
    /plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md,
    /plans/active/ao_remediation_a_independent_fixes_2026_07_23.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P0
parent_epic: orchestrator_master
source:
  "Operator report 'so many repeating alerts' 2026-07-24; root-caused via a live Slack API pull after the GCP
  Secret-Manager read path failed for every available gcloud identity and the operator supplied
  SLACK_ALERTS_READER_BOT_TOKEN directly from .act-secrets"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## Evidence

Downloaded via the Slack API (`conversations.history`, `agent-orchestrator-alerts`, last 3h) — 237 messages total.
Normalizing away timestamps/slot-numbers/shas and grouping by template, the top signatures were:

| n   | Template (claim text)                                            | Span (this pull)    |
| --- | ---------------------------------------------------------------- | ------------------- |
| 70  | `[doc_drift] CLAUDE.md — x`                                      | 08:22–09:13 (51min) |
| 28  | `[doc_drift] CLAUDE.md — drift Z`                                | 08:22–09:13         |
| 14  | `[doc_drift] CLAUDE.md — already seen`                           | 08:22–09:13         |
| 14  | `[doc_drift] CLAUDE.md — rule X contradicted`                    | 08:22–09:13         |
| 14  | `[doc_drift] SUB_AGENT_MANDATORY_RULES.md — y`                   | 08:22–09:13         |
| 14  | `[doc_drift] SUB_AGENT_MANDATORY_RULES.md — tab-branch retired`  | 08:22–09:13         |
| 14  | plan_health dispatch-failed: `tmux unavailable`                  | 08:22–09:13         |
| 14  | plan_health dispatch-failed: `session already exists (raced...)` | 08:22–09:13         |

That's ~168 of the 237 messages in this one pull, still actively firing (last timestamp in the pull was the pull's own
`now`). Grepping the codebase for these exact strings:

```
tests/test_plan_health.py:824:  {"doc": "SUB_AGENT_MANDATORY_RULES.md", "contradicted_by": "live plans", "claim": "tab-branch retired"}
tests/test_plan_health.py:858:  finding = {"doc": "CLAUDE.md", "contradicted_by": "p", "claim": "drift Z"}
tests/test_plan_health.py:876:  "doc_drift": [{"doc": "CLAUDE.md", "claim": "rule X contradicted"}]
tests/test_plan_health.py:995:  finding = {"doc": "CLAUDE.md", "contradicted_by": "p", "claim": "already seen"}
tests/test_plan_health.py:153,251: spawn=(False, "tmux unavailable")
```

Every one of the top 6 doc_drift signatures is a literal test fixture. `notify_slot_blocked`'s actual message format
(`server/notifications/slack.py`) —
`*Agent:* ... | *Time:* ... | *Question:* ... | *Recommendation:* ... | Operator action needed. *Open:* ...fleet-git?slot=0...`
— matches the live Slack content byte-for-byte.

## Confirmed root cause

Three tests in `tests/test_plan_health.py` mock `server.plan_health.add_blocked` (so no fake row lands in the real
`blocked_queue` — **verified live: `SELECT ... FROM blocked_queue WHERE task_id LIKE 'doc_drift:%'` returns 0 rows** on
the orchestrator VM right now) but do **NOT** mock `server.notifications.slack.notify_slot_blocked`:

- `test_record_result_creates_blocked_queue_entry_for_new_doc_drift` (claim `"x"`)
- `test_record_result_logs_doc_drift_blocked_activity` (claim `"x"`)
- `test_record_result_no_blocked_entry_when_drift_not_new` (claim `"already seen"`)
- `test_record_result_resolved_doc_drift_rearms` (claim `"drift Z"`; mocks `notify_plan_health_findings` but not
  `add_blocked` or `notify_slot_blocked` — calls `record_result` twice with the finding present, so it likely
  double-fires per real run)

`record_result()` (`server/plan_health.py`) calls the Slack notify via a **fresh in-loop import**:

```python
for blocked_id, d in new_blocked:
    from .notifications import slack as slack_notify
    slack_notify.notify_slot_blocked("0", "plan_health", f"[doc_drift] {_format_drift_item(d)}", blocked_id, ...)
```

`patch.multiple("server.plan_health", add_blocked=..., session_scope=..., log_activity=...)` only patches attributes
looked up on the `server.plan_health` module — it does nothing to `server.notifications.slack.notify_slot_blocked`,
which these 4 tests never touch. So every real invocation of these tests posts a REAL Slack message via whatever webhook
URL (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK`) is visible in that shell's environment — and since `quality-gates.sh` runs the
FULL test suite before every commit, and the fleet ships constantly, this fires continuously across every worker that
runs QG on a host where that env var happens to be set.

**Worse than "just noisy": the `blocked_id` in every one of these real Slack pages is the test's MOCKED return value**
(`"BLK-abc123"`, `"BLK-xyz"`, `"BLK-1"`, `"BLK-2"`) — **none of these correspond to a real row.** An operator clicking
through to answer one would find nothing to answer.

## Not yet confirmed (same bug class, needs its own audit pass)

The `tmux unavailable` / `session already exists (raced by another spawn path)` dispatch-failure messages (14 each, same
cadence) are **also** literal test fixtures (`test_plan_health.py:153,251`; `test_escalation.py:375`) for
`notify_plan_health_dispatch_failed`. One relevant test (`test_alert_dispatch_failed_serializes_concurrent_calls`) DOES
correctly patch `server.notifications.slack.notify_plan_health_dispatch_failed` — so the actual leaking call site (if
any) is a **different** test using these same fixture strings, not yet identified. Needs the same audit pass as above
across `test_plan_health.py` AND `test_escalation.py` before concluding this is the same bug (strong circumstantial
match, not yet mechanism-confirmed like the doc_drift case above).

## Open todos

- [ ] [BACKEND] P0. Add the missing `patch("server.notifications.slack.notify_slot_blocked")` (and
      `notify_plan_health_findings` where absent) to the 4 identified doc_drift tests in `test_plan_health.py`.
      **Gate**: running each test with the REAL `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` env var set (or a spy asserting zero
      real HTTP calls) proves no outbound request fires.
- [ ] [BACKEND] P0. Audit `test_plan_health.py` + `test_escalation.py` for every other call into `record_result`,
      `_alert_dispatch_failed`, `dispatch`, or any function that reaches `server.notifications.slack.*`, and confirm
      each test that exercises a real Slack-firing path patches the relevant `notify_*` function. Specifically resolve
      the `tmux unavailable`/`session already exists` open question above.
- [ ] [BACKEND] P1. Add a project-wide `autouse` conftest fixture that blocks real outbound Slack sends by default (e.g.
      patch `server.notifications.slack._post` to a no-op, or assert `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is unset in the
      test environment) — defense-in-depth mirroring the existing `_isolated_state_dir` autouse fixture in
      `tests/conftest.py`, so a future missing per-test mock can't leak into production again. **Gate**: temporarily
      un-mock one of the 4 tests above and confirm the new fixture still prevents a real send.
- [ ] [OPERATOR] P2. Decide whether to also verify why `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is visible inside a worker's
      `quality-gates.sh` pytest run at all (is it exported at the shell/profile level for all subprocesses on the
      central VM, not just the systemd-managed `orchestrator.service`?) — informs whether the fix belongs ONLY in the
      tests, or also in how broadly that env var is scoped on the host.
- [ ] [SCRIPT] P3. Add a `SLACK_ALERTS_READER_BOT_TOKEN` env-var fallback to `scripts/dev/slack-read-channel.py` (gcloud
      ADC stays primary; env var is the degraded path) — every gcloud identity available in this session hit either
      `PERMISSION_DENIED` on `secretmanager.versions.access` or a stale-token reauth prompt that can't run
      non-interactively, and the operator supplied the token directly from `.act-secrets` instead. Attempted 2026-07-24
      (diff written, syntax-validated) but blocked shipping by an UNRELATED pre-existing `quality-gates.sh` failure:
      STEP 5.101 (`no_empty_string_fallback_baseline`) reports 320 sites > baseline 319, citing
      `scripts/sports/migrate_player_mappings_to_canonical.py:63` — a file this todo never touched. Reverted the
      uncommitted diff cleanly rather than force it through; retry once that unrelated ratchet is resolved. **Gate**:
      same as the existing script's own conventions — the fallback is documented as secondary, never touches disk/argv.
- [ ] [BACKEND] P2. **Separately flagged**: `scripts/sports/migrate_player_mappings_to_canonical.py:63` breached the
      `no_empty_string_fallback_baseline` ratchet (320 > 319) — this blocks EVERY future `unified-trading-pm` CODE
      quickmerge (STEP 5.101 scans the whole workspace root, not just the touching diff) until fixed or explicitly
      exempted. Found as a side effect of an unrelated attempted commit 2026-07-24; not investigated further (out of
      scope, unfamiliar file, not touched by this session). SSOT for the ratchet:
      `plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`. **Gate**: rewrite the
      site to fail fast, or add `# noqa: qg-empty-fallback` with a one-line reason per that SSOT's own recipe.

## Progress Log

- **2026-07-24**: Root-caused via a live Slack API pull (operator supplied `SLACK_ALERTS_READER_BOT_TOKEN` from
  `.act-secrets` after the GCP Secret Manager read path failed for every available gcloud identity this session).
  Confirmed the doc_drift mechanism precisely (missing `notify_slot_blocked` mock, verified 0 fake rows in the real
  `blocked_queue`); flagged the dispatch-failed mechanism as same-class-but-unconfirmed. Not fixed yet — filed P0 for
  next pickup, this is an active, ongoing production Slack flood as of filing.
