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
    /plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md,
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

## Confirmed + FIXED: dispatch-failure mechanism (was "not yet confirmed")

The `tmux unavailable` / `session already exists (raced by another spawn path)` dispatch-failure messages (14 each) were
confirmed as the SAME bug class, in a different function: `test_dispatch_spawn_failure_raises` and
`test_dispatch_exhausted_retries_drops_benign_label` (`test_plan_health.py`) each drive `dispatch()` into the
`_alert_dispatch_failed()` path without mocking `server.notifications.slack.notify_plan_health_dispatch_failed` — a live
spy proof (real webhook env var set, `_post` spied) caught exactly 2 real posts, matching both templates 1:1.

## Full scope: 11 leaking tests, not 4 — every flood count reconciled exactly

Tracing `record_result()`'s actual control flow (not just the 4 originally suspected tests) showed ANY test passing a
NEW `doc_drift` finding without mocking **both** `notify_plan_health_findings` AND `notify_slot_blocked` leaks — since
`new_blocked` (and therefore the `notify_slot_blocked` call) is populated regardless of whether `add_blocked` itself is
mocked. Reconciling every leaking test's fire-count against the original flood evidence table matches **exactly**: claim
`"x"` = 5 tests × 1 fire = n=70/14 runs; `"y"` = 1 test = n=14; `"already seen"` = 1 test (1 of 2 calls, deduped) =
n=14; `"drift Z"` = 1 test × 2 fires (of 3 calls) = n=28; `"rule X contradicted"` = 1 test = n=14;
`"tab-branch retired"` = 1 test = n=14; `"tmux unavailable"` + `"session already exists"` = 1 test each = n=14 each. All
9 doc_drift tests + 2 dispatch-failure tests fixed in one commit — proof re-run showed 0 real `_post` calls across the
whole suite (1609 passed).

## Open todos

- [x] [BACKEND] P0. Add the missing `notify_slot_blocked`/`notify_plan_health_findings` mocks — scope widened from the
      original 4 to all 9 leaking doc_drift tests once the full `record_result()` control flow was traced. —
      `agent-orchestrator@a545800`. **Gate met**: scoped spy run (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK` set + `_post`
      spied) across `test_plan_health.py` + `test_escalation.py` → 129 passed, 0 real `_post` calls.
- [x] [BACKEND] P0. Audited both files for every other Slack-reaching call; found + fixed the 2 dispatch-failure tests
      (`test_dispatch_spawn_failure_raises`, `test_dispatch_exhausted_retries_drops_benign_label`) missing
      `notify_plan_health_dispatch_failed` mocks — resolves the "not yet confirmed" section above. —
      `agent-orchestrator@a545800`.
- [x] [BACKEND] P1. Added `_no_real_slack_webhook` autouse fixture to `tests/conftest.py` — defaults
      `server.notifications.slack._WEBHOOK_URL` to `""` for every test (mirrors `_isolated_state_dir`); a test that
      exercises `_post`'s real retry/backoff logic (`test_slack_notifications.py`) overrides it itself, unaffected. —
      `agent-orchestrator@a545800`. **Gate met**: a throwaway test with a live-looking webhook URL AND zero notify
      mocking (the exact "forgot the mock" scenario) still made 0 real `httpx.Client` calls — the fixture alone blocks
      it, independent of the per-test mock. Full suite (1609 passed, 1 skipped) unaffected.
- [x] [DIAG] P2. **Answered 2026-07-27 (classification sweep, read-only SSM against the orchestrator VM,
      `i-0c9b283b31d6b5ca7`)** — `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is **NOT** exported at the shell/profile level:
      `grep -rl AGENT_ORCHESTRATOR_SLACK_WEBHOOK /etc/environment /etc/profile.d /etc/systemd/system /home/*/.bashrc     /home/*/.profile /home/*/.bash_profile`
      matched only 3 systemd drop-ins (`orchestrator.service.d/slack-alerts.conf` + 2
      `audit-*.service.d/slack-alerts.conf` — no shell dotfile). It IS, however, present in the live tmux SERVER
      process's own environment (`/proc/<tmux-server-pid>/environ`, confirmed via `sudo` read) — meaning every worker
      pane spawned on that shared tmux server inherits it, because the tmux server itself was started as a descendant of
      `orchestrator.service` (which correctly needs the var) and never had it stripped before spawning worker sessions.
      **This explains the observed flood exactly**: not a careless broad export, but env-inheritance through the
      AutoSpawn → tmux-server → worker-pane process chain. **No further host-level fix is required** — the already-
      shipped `_no_real_slack_webhook` autouse conftest fixture (P1 todo above) defaults the webhook to `""` inside
      every test regardless of what the surrounding shell/tmux environment exports, so this mechanism is fully closed at
      the test layer independent of the host-level env-var chain. Optional future hardening (not required, not actioned
      here): `AutoSpawn`'s tmux-spawn call could explicitly `unset AGENT_ORCHESTRATOR_SLACK_WEBHOOK` before launching a
      new slot session, so a FUTURE test class that forgets to mock Slack doesn't inherit a working webhook either — but
      the current fix already prevents the concrete flood this issue was filed for.
- [ ] [SCRIPT] P3. Add a `SLACK_ALERTS_READER_BOT_TOKEN` env-var fallback to `scripts/dev/slack-read-channel.py` (gcloud
      ADC stays primary; env var is the degraded path) — every gcloud identity available in this session hit either
      `PERMISSION_DENIED` on `secretmanager.versions.access` or a stale-token reauth prompt that can't run
      non-interactively, and the operator supplied the token directly from `.act-secrets` instead. Attempted 2026-07-24
      (diff written, syntax-validated) but blocked shipping by an UNRELATED pre-existing `quality-gates.sh` failure:
      STEP 5.101 (`no_empty_string_fallback_baseline`) reports 320 sites > baseline 319, citing
      `scripts/sports/migrate_player_mappings_to_canonical.py:63` — a file this todo never touched. Reverted the
      uncommitted diff cleanly rather than force it through; retry once that unrelated ratchet is resolved. **Gate**:
      same as the existing script's own conventions — the fallback is documented as secondary, never touches disk/argv.
- [x] [BACKEND] P2. **Separately flagged**: `scripts/sports/migrate_player_mappings_to_canonical.py:63` breached the
      `no_empty_string_fallback_baseline` ratchet (320 > 319) — this blocks EVERY future `unified-trading-pm` CODE
      quickmerge (STEP 5.101 scans the whole workspace root, not just the touching diff) until fixed or explicitly
      exempted. Found as a side effect of an unrelated attempted commit 2026-07-24; not investigated further (out of
      scope, unfamiliar file, not touched by this session). SSOT for the ratchet:
      `plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`. **Gate**: rewrite the
      site to fail fast, or add `# noqa: qg-empty-fallback` with a one-line reason per that SSOT's own recipe. — already
      covered by plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (measured 2026-07-26:
      check_no_empty_string_fallback.py --scope unified-trading-pm reports 319 == baseline) (see that doc for
      execution).

## Progress Log

- **2026-07-24**: Root-caused via a live Slack API pull (operator supplied `SLACK_ALERTS_READER_BOT_TOKEN` from
  `.act-secrets` after the GCP Secret Manager read path failed for every available gcloud identity this session).
  Confirmed the doc_drift mechanism precisely (missing `notify_slot_blocked` mock, verified 0 fake rows in the real
  `blocked_queue`); flagged the dispatch-failed mechanism as same-class-but-unconfirmed. Not fixed yet — filed P0 for
  next pickup, this is an active, ongoing production Slack flood as of filing.
- **2026-07-24 (later same day)**: Re-pulled the channel — the original 51-minute burst (168 messages) had already gone
  quiet ~41 minutes before this pass (last flood message 09:13:36 UTC; re-pull at 09:55 UTC clean), confirming the flood
  is bursty (tracks fleet-wide QG sweeps) rather than continuous, but guaranteed to recur on the next full-suite run
  anywhere the webhook env var is visible. Traced `record_result()`'s full control flow (not just the 4 originally
  suspected tests) and found the true leaking set was **11 tests**: every count in the original evidence table (70, 28,
  14×6) reconciles EXACTLY against a specific leaking test once all of them are accounted for — see "Full scope" above.
  Fixed all 11 (the 9 doc_drift tests in `test_plan_health.py` + the 2 `_alert_dispatch_failed` dispatch-failure tests),
  added the P1 autouse `_no_real_slack_webhook` conftest fixture as defense-in-depth, and proved both with a real spy
  (fake `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` set, `_post`/`httpx.Client` spied — 0 real calls, 1609/1609 passed full
  suite). Shipped `agent-orchestrator@a545800` via quickmerge (landed on LDR). 3 todos remain open (operator env-
  var-scope decision, the deferred script fallback, and the unrelated ratchet breach) — none block the production fix.
