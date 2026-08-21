---
doc_type: issue
title: 'Fleet-wide mid-task-death sweep — remaining models (Gemini, Claude sub-accounts, GLM, Gemma) root-caused, 3 classification/forensics gaps fixed'
summary:
  'Continuation of ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md after codex-luna and DeepSeek were
  root-caused: swept every OTHER account family for the same mid-task-kill class via a 21-day tmux_session_lost
  DB lookback (Gemini 57 unexplained, Claude sub-accounts 377, GLM 11, gemma-self-hosted 3) followed by a 9-agent
  Workflow investigation (5 cluster deep-dives + 3 adversarial verify passes, one cluster given two independent
  lenses given its size). Headline result: the pkill-guard PATH-wrapper fix already shipped for DeepSeek
  (agent-orchestrator@2fe498b30f) explains 98.6% of the single biggest unexplained population fleet-wide (214
  events across 4 Claude sub-accounts) — it was already working, just not yet confirmed against this population.
  A separate, genuine classification gap was found and fixed: autospawn.py deliberately kills a live worker the
  instant its account falls out of dispatch headroom (working as designed), but tmux_pruner.py never recognized
  the event this kill logs, so every one of these misclassified as "unexplained" and wrongly penalized the
  account''s health tracking. Two more instances of the same gap (orphan_session_reclaim,
  idle_lingering_session_reclaim) and a fleet-wide forensics PATH bug (ausearch has never once successfully run,
  ever, on any death) were found and fixed in the same sweep. A Gemini LiteLLM proxy config bug (dotted vs
  dashed model-name aliases, causing live 400s) was independently found and fixed by a different session
  moments before this one attempted the same fix — discarded in favor of theirs.'
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [multi-agent-safety, agent-orchestrator, dispatch, death-forensics, classification-gap, ao-fleet-death, gemini, claude, glm, gemma]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/pkill_guard_dead_on_exec_into_claude_recurrence4_2026_08_21.md,
    /plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
priority: P1
parent_epic: agent_operating_framework_master
source: "Operator, interactive session (slot 12), 2026-08-21: 'okay now lets go over other models claude and gemini and all models that are remaining to be tested for the mid-task kill issues and update the documents with proper findings. and please look at as many jsonl files or log files of sessions as you have to so we can eliminate this at root for all models and fix this once and for all'"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/death_forensics.py,
    agent-orchestrator/scripts/orchestrator.service,
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
  ]
---

# Fleet-wide mid-task-death sweep — remaining models root-caused (2026-08-21)

## Scoping

21-day `tmux_session_lost` lookback (2026-08-21), grouped by `account_id`/`death_class`, joined against a
`worker_account_unusable_killed`-within-120s check to separate "already explained by the known classification
gap" from genuine residual:

| account | unexplained (21d) | classification-gap matches |
| --- | --- | --- |
| sub-c-ikenna-odum | 79 | 0 |
| sub-g-alpavolt | 50 | 0 |
| sub-d-odum1default | 47 | 0 |
| sub-f-odum2default | 38 | 0 |
| sub-b-iggy2london | 80 | 12 |
| sub-h-igboestates | 36 | 13 |
| sub-e-odum2default | 29 | 3 |
| sub-a-ikenna | 18 | 12 |
| gemini-3-5-flash-lite-proj1 | 25 | 19 |
| gemini-3-7-flash-proj1 | 12 | 4 |
| gemini-3-5-flash-lite-proj2/3, gemini-3-7-flash-proj2/3 | 20 | 11 |
| glm-5-2 | 9 | 0 |
| glm-5-turbo | 2 | 0 |
| gemma-self-hosted | 3 | 0 |

The 4 Claude sub-accounts with ZERO classification-gap matches (sub-c/g/d/f, 214 events combined) are the single
biggest unexplained population fleet-wide — bigger than codex-luna (81) or DeepSeek (53) combined — and became
the highest-priority target.

## Findings

### 1. Classification gap: `worker_account_unusable_killed` (fixed, `agent-orchestrator@dc1d273f89`)

`autospawn.py`'s `_drain_worker_account_failover` deliberately kills a live worker the instant its bound account
falls out of dispatch headroom (disabled/rate-limited/auth-failed/over its pct ceiling — for Gemini, over its
RPM/RPD ceiling) — a genuine, working-as-designed failover, not a bug. It logs `worker_account_unusable_killed`
to `activity_log` right before the kill. But `tmux_pruner.py`'s `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS` tuple —
the list of event types that make the death classifier read `intentional_teardown` instead of `unexplained` —
never included it. Every one of these kills therefore misclassified as `unexplained`, wasting OOM/external-kill
forensics AND (via `tmux_pruner.py`'s existing `record_spawn_outcome` hook on unexplained deaths) wrongly
recording a spawn FAILURE against the account's in-memory health ring — penalizing an account for a failover
that was never its fault.

Measured match rate (deaths preceded by `worker_account_unusable_killed` within 120s, same slot): 100% for
`gemini-3-7-flash-proj2`, 76% for `gemini-3-5-flash-lite-proj1`, 15-67% for several Claude sub-accounts — but
ZERO for codex-luna, DeepSeek, GLM, Gemma, and (critically) the sub-c/g/d/f mystery cluster below.

**Fix**: added `worker_account_unusable_killed` to `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`, auto-covered by the
existing parametrized regression suite (`tests/test_tmux_pruner_death_class_signals.py`).

### 2. The sub-c/g/d/f mystery cluster (214 events) — substantially explained, not a new bug

Two independent investigation lenses (transcript-reading + host/infra-correlation) sampled this cluster:

- **211/214 (98.6%) occurred BEFORE the pkill-guard PATH-wrapper fix landed**
  (`agent-orchestrator@2fe498b30f`, 2026-08-21 13:55:20 UTC — see
  `pkill_guard_dead_on_exec_into_claude_recurrence4_2026_08_21.md`); only 4 isolated (non-clustered) events
  occurred after. This is the SAME cross-slot pkill-guard mechanism already root-caused for DeepSeek — a bare
  `pkill -f "<name>"` from any slot's Bash tool call, unguarded due to the dead sourced-shell-function guard,
  killing every slot running that same-named process simultaneously. The fix already shipped applies fleet-wide
  (a PATH-prepended executable wrapper, not account-specific), and this population's post-fix data confirms it
  is working — no further code change needed here.
- Adversarial verification REFUTED a competing theory from this investigation (that `ao-self-pull.sh`'s
  `systemctl restart orchestrator` cycle directly kills tmux worker panes): `orchestrator.service`'s
  `KillMode=process` (root-caused + fixed 2026-05-20, per the unit's own comment) specifically prevents this —
  a restart SIGTERMs only the uvicorn main PID, and `tmux_spawn.py` decouples worker sessions via `setsid`. The
  measured correlation (5/123 residual rows near a restart) was statistically consistent with chance
  (~3.6 expected), not causation.
- **Residual sibling classification gap found, not yet fixed**: an account-wide Claude session-limit hit
  freezes every slot bound to that account near-simultaneously. AO's own `_handle_account_blocked_pane` is
  deliberately alert-only (a 2026-08-14 incident is the reason it never force-kills), so the frozen slots
  instead each independently breach the GENERIC heartbeat-staleness threshold and get a legitimate watchdog
  force-kill — but because they froze together, these land within seconds of each other, and none of the
  events this specific watchdog path emits are in `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`, so every one
  misclassifies as unexplained. Affects `sub-d-odum1default`/`sub-f-odum2default` per the sample. See Todo.

### 3. Two more classification-gap event types (fixed, `agent-orchestrator@0704ed0a47`)

`worker_liveness_watchdog.py`'s orphan-session and idle-lingering-session reclaimers (both legitimate,
working-as-designed teardowns, confirmed live via matching `journalctl` lines to specific Gemini deaths within
the classifier's 90s lookback window) had NO distinctly-named `activity_log` event at all before this fix —
`kill_session()`'s `reason=` kwarg only ever reached a plain `logger.warning` line, invisible to the classifier
(unlike `worker_account_unusable_killed`, which at least had its own `log_activity()` call). Added the
companion `log_activity()` call at both call sites (`orphan_session_reclaim`, `idle_lingering_session_reclaim`)
and wired both into the classifier tuple. Factored the kill+log logic into two small helper methods
(`_kill_orphan_session_and_log`, `_log_reclaim_teardown_event`) to keep `_tick_once` under the ruff C901
complexity ceiling (inlining pushed it to 27 > 26). New regression tests confirm both the event fires and its
`slot_id`/`account_id` payload is correct; `tests/test_worker_liveness_watchdog.py::_make_slot` gained an
explicit `account_id` parameter (previously an unconfigured `MagicMock` attribute there would have raised
`TypeError` on JSON-serialization once a real caller started passing it through).

### 4. Fleet-wide forensics blind spot: `ausearch` has never once successfully run (fixed, same commit as #3)

`orchestrator.service`'s `Environment="PATH=...` omitted `/usr/sbin` (and `/sbin`) — but `ausearch` lives at
`/usr/sbin/ausearch`. Every `subprocess.run(['ausearch', ...])` inside `death_forensics.py`'s
`check_external_kill` raised `FileNotFoundError`, caught by its best-effort wrapper and reported as
`external_kill.checked=false`. Measured: **578/578** `unexplained_death_forensics` rows fleet-wide show this —
meaning every prior "external kill not suspected" verdict, across every investigation this session and before,
carried ZERO evidentiary weight for this leg. It was never checked, not checked-and-clean. (The OOM leg was
unaffected — `journalctl` sits on `/usr/bin`, already on the old PATH — so OOM-ruling-out conclusions from
earlier in this sweep stand.) Fixed by adding `/usr/sbin:/sbin` to the systemd unit TEMPLATE
(`scripts/orchestrator.service`) — self-heals onto the live unit via `ao-self-pull.sh`'s idempotent
`install-orchestrator-service.sh` re-run (every ~2 min), no separate deploy action needed.

**Structural gap noted, not fixed**: even with the PATH bug fixed, `ausearch`'s EXECVE-based audit search can
never see AO's OWN `kill_session()` calls — they fire via direct `os.kill(pid, SIGTERM/SIGKILL)` syscalls from
within the long-running orchestrator process, never an execve'd subprocess. auditd's EXECVE record type is
structurally blind to this entire class (~20 call sites). Closing this needs a different audit rule type
(SIGNAL records, not EXECVE) — not attempted this session, tracked as a todo.

### 5. Gemini LiteLLM proxy model-name mismatch — found here, fixed independently elsewhere

`config/litellm/grok_gemini_proxy.yaml`'s `model_name` aliases used dots (`gemini-3.5-flash-lite-proj1`) while
every real request's `ANTHROPIC_MODEL` (confirmed via the live per-account `~/.claude-accounts/<id>.env`) uses
dashes (`gemini-3-5-flash-lite-proj1`) — every affected request immediately 400'd with
`litellm.proxy.route_llm_request.ProxyModelNotFoundError`, 650 occurrences in one day (journalctl-confirmed),
steadily from ~11:00 UTC onward. **Independently fixed by a different session (slot-15) as
`agent-orchestrator@bee25ba8`, 2026-08-21 16:09:38 UTC — minutes before this investigation's own fix attempt.**
Discovered via quickmerge's not-behind gate blocking on a real working-tree overlap (both sessions edited the
same file, same direction) when this session tried to ship its own copy. Their fix is more thorough (a
dedicated new test file, `tests/test_gemini_proxy_alias_account_id_alignment.py`, plus a fix to
`gemini_translation_smoke.py`'s own same-source-of-truth gap this investigation didn't catch: the smoke test
resolved its model name by reading the same yaml file production reads, so a bug in the yaml never showed up as
a test failure). This session's own copy was discarded in favor of theirs after pulling and comparing — not
duplicated.

### 6. Lower-priority / not yet acted on

- **GLM shared-key blind quota estimator**: `glm-5-2`/`glm-5-turbo` share ONE physical Zhipu "Coding Plan" API
  key (both accounts' env files fetch the same GSM secret). Z.ai's API exposes no real quota/rate-limit signal
  at all (confirmed via `glm_quota_poller.py`'s own docstring), so its count-based usage estimate under-reports,
  and a real 429 (`[1308][Usage limit reached for 5 hour...]`, confirmed byte-for-byte in 3 separate jsonl
  transcripts) shows in `account_snapshot` as `account_status=healthy`. 11 unexplained deaths over 21 days. No
  clean fix without a real upstream quota endpoint.
- **`sub-f-odum2default`-specific residual pattern**: its slots run a `cicd`/monitoring role
  (cloud-build-failure-watcher, ldr-ci-monitor, escalation dispatch) whose background Monitor/task-notification
  watches sometimes conclude right at the moment of an "unexplained" death (not a mid-turn crash) — 3 samples,
  not yet confirmed as a real pattern vs. coincidence.
- **Possibly-stale `context_activity_silence_detected` reading**: one sampled slot showed
  `minutes_silent=1791` against a 14400s window just 9 minutes before its death, while `slot_progress` events
  showed it actively working at that exact time — flagged, not investigated further.
- **gemma-self-hosted**: all 3 unexplained deaths were the SAME single incident (a litellm/Ollama
  `reasoning_effort`-mapping bug, `"gemma3:27b" does not support thinking"`), already root-caused and fixed
  2026-08-20 (`config/litellm/ollama_thinking_monkeypatch.py`) — zero recurrences since. No action needed.

## Todo

- [x] ✅ [BACKEND] P0. Add `worker_account_unusable_killed` to `tmux_pruner.py`'s
      `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`. Shipped `agent-orchestrator@dc1d273f89`, auto-covered by the
      existing parametrized regression suite.
- [x] ✅ [BACKEND] P1. Add companion `log_activity()` calls for `orphan_session_reclaim` and
      `idle_lingering_session_reclaim` in `worker_liveness_watchdog.py`, wire both into the classifier tuple,
      new regression tests. Shipped `agent-orchestrator@0704ed0a47`.
- [x] ✅ [INFRA] P1. Fix `orchestrator.service`'s PATH to include `/usr/sbin:/sbin` so `ausearch` can actually
      run. Shipped in the same commit as above.
- [x] ✅ [INFO] P2. Gemini proxy model-name mismatch — confirmed already fixed independently
      (`agent-orchestrator@bee25ba8`); no action needed here.
- [ ] [INFRA] P2. Identify the exact event type AO's generic heartbeat-staleness watchdog emits when it
      force-kills a slot whose account is frozen by an account-wide Claude session-limit hit (distinct from
      `worker_account_unusable_killed` — the generic staleness path, not the headroom-failover one), and add it
      to `_INTENTIONAL_TEARDOWN_SIGNAL_EVENTS`. Affects `sub-d-odum1default`/`sub-f-odum2default` per this
      investigation's sample.
- [ ] [INFRA] P3. `death_forensics.check_external_kill`'s EXECVE-based search is structurally blind to AO's own
      `kill_session()` calls (direct `os.kill()` syscalls, not an execve'd subprocess) — needs a different audit
      rule type (auditd SIGNAL records) to close, not attempted this session.
- [ ] [DATA] P3. GLM shared-key blind quota estimator — no clean fix without a real upstream quota endpoint;
      consider pattern-matching the literal `[1308][Usage limit reached...]` 429 body as a stopgap
      classification signal if this recurs at volume.
- [ ] [DATA] P3. `sub-f-odum2default`'s cicd/monitoring-role residual pattern and the possibly-stale
      `context_activity_silence_detected` reading — both need more samples/investigation before a fix can be
      designed.
- [ ] [DOC] P3. Monitor for recurrence: confirm no new cross-slot broad-pkill-style mass-death bursts appear
      now that the pkill-guard-bin fix is live, and confirm the classification-gap fixes correctly reduce the
      "unexplained" share of new deaths (re-run this doc's scoping query in a week+).

## Progress Log

- 2026-08-21 (slot 12, interactive session): operator asked to sweep every remaining model for the same
  mid-task-death class already root-caused for codex-luna/DeepSeek, reading real jsonl/log evidence rather than
  aggregate correlation alone. Scoped via a 21-day DB lookback, then ran a 9-agent Workflow (5 cluster
  investigations in parallel + 3 adversarial verify passes). While waiting on the workflow, independently found
  and confirmed the `worker_account_unusable_killed` classification gap directly in the code (not from the
  workflow) — implemented, tested, shipped as `agent-orchestrator@dc1d273f89` before the workflow even
  completed. Workflow findings then folded in: the sub-c/g/d/f mystery cluster substantially explained by the
  already-shipped pkill-guard fix; 2 more classification-gap events plus the ausearch PATH bug found and fixed
  as `agent-orchestrator@0704ed0a47`; the Gemini proxy bug found but discovered already independently fixed
  elsewhere (`bee25ba8`) via a quickmerge working-tree-overlap block, resolved by pulling theirs in rather than
  duplicating. One real mid-session mistake, caught before it caused harm: briefly edited `tmux_pruner.py`
  directly in the SHARED top-level `agent-orchestrator` checkout (used by the live server + other sessions)
  instead of this slot's own `.tabs/12` worktree — caught, reverted cleanly there via `git checkout --`
  (confirmed nothing else was touched, since it was purely my own uncommitted diff), redone correctly in
  `.tabs/12`. Filed this as a new, dedicated doc (split from `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
  to keep that doc under its 1000-line hard cap) rather than merged, matching the precedent that doc's own
  Cluster-B finding already set.
