---
doc_type: issue
title:
  market-tick-data-service quality-gates.sh background runs killed near-instantly, including setsid-detached — not fully
  explained by known RAM-exhaustion class
summary: >-
  Shipping a verified, committed fix (market-tick-data-service@eeade63b) required a fresh quality-gates.sh run to mint a
  HEAD-matching --agent sentinel. 20+ consecutive attempts across ~4h were killed — most within seconds, one even a
  trivial `sleep 180` diagnostic died within ~11s. This resembles the archived
  shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md class but main's live investigation ruled out the
  resource-watchdog.sh RAM/CPU/swap kill path specifically (MIN_AGE_SEC=30s exempts anything younger, several kills were
  both near-instant AND at healthy measured host RAM/load) — main's working theory (background invocation not fully
  detached from the invoking shell/tool-call) was tested via setsid+nohup+disown and got further (one run reached the
  pytest TESTS stage, 10889 items collected, several dozen passing) but still died before completion, without an
  EXIT_CODE marker — so the shell-detach theory is not fully confirmed either. Filed to hand off the
  now-safely-committed-but-unshipped code + the accumulated diagnostic evidence rather than keep burning session hours
  on further blind retries (main's own explicit instruction after ~18 attempts).
status: open
nature: issue
asset_group: [infrastructure, defi]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [infra, quality-gates, qg-governor, shared-host, background-task, kill, defi]
related:
  [
    /plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
    /plans/archive/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md,
    /plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md,
  ]
created: 2026-08-15
last_updated: 2026-08-21
author: slot-15 (infra)
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
drift_direction: advance-code
depends_on: []
source: ["BLK-ff9ec1b7 (blocked-question on slot 15, 2026-08-15, answered by main)"]
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
    /plans/archive/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md,
    /plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md,
    unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.sh,
    unified-trading-pm/scripts/hooks/pkill-guard.sh,
  ]
---

# market-tick-data-service quality-gates.sh background runs killed near-instantly

## What I found

Session goal: ship `market-tick-data-service` commit `9a21fe0c` (3-handler `ParallelPerSymbolRunner` conversion, already
independently verified correct — see the source issue doc's own evidence trail) via the standard
Pass-1-QG-then-quickmerge flow. The pre-rebase diff got a full, clean `✅ ALL QUALITY GATES PASSED (2042s)`. After a
mandatory `git pull --rebase --autostash` (someone else landed 2 commits on `live-defi-rollout` first) + a `ruff-format`
auto-fix + re-commit, a fresh sentinel-minting run was needed for the new HEAD SHA — and every attempt to get one died:

| # attempts | Method                                                                                                                | Typical death point                                                                                                                                                                                                                                                                            | Host state at death (when captured)                                                                                                                                |
| ---------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ~12        | `run_in_background: true` (harness Bash tool)                                                                         | Most: printed only the `[quality-gates] market-tick-data-service @ ...` header line, then gone. A few got further (governor token wait, `[0/6] ENVIRONMENT`, one reached 75% through `[3/6] TESTS`).                                                                                           | Ranged from genuinely contended (load 8-13, <2Gi free) to completely healthy (load 3.5-4.8, 20Gi+ available) — NOT consistently correlated with resource pressure. |
| 1          | `bash -c 'sleep 180; echo end'` (trivial, no QG at all)                                                               | Killed within ~11s (measured via embedded `date +%s` timestamps)                                                                                                                                                                                                                               | N/A — a bare sleep cannot be RAM/CPU-contended                                                                                                                     |
| 2          | `setsid nohup bash -c '... > log 2>&1; echo EXIT_CODE=$? >> log' < /dev/null & disown` (operator-directed diagnostic) | Attempt 1: died before any real QG output. Attempt 2: got MUCH further — governor token acquired after 15s wait, environment checks passed, TESTS stage started, `10889 items` collected, several dozen dots (passing tests) printed — then died anyway, no `EXIT_CODE=` marker ever appeared. | Not captured at exact death moment for either.                                                                                                                     |

**What this rules out**: `scripts/dev/resource-watchdog.sh` (the RAM/CPU/swap-triggered kill path documented in
`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s cross-check addendum) explicitly exempts any process
younger than `MIN_AGE_SEC=30s` from every one of its checks (`resource-watchdog.sh:392-394`, "Skip young processes
(startup spikes)") — main confirmed this by reading the script live. The 11s-old trivial `sleep` death is **structurally
impossible** to be that watchdog. Genuine fleet-wide qg-governor contention (the documented, already-known, separate
issue — `[qg-governor] total-instance tokens busy ... queued Ns`) is real and was observed independently (governor wait
times up to 60s+ seen in some runs), but does not explain an 11s bare-sleep death either.

**What is NOT yet confirmed**: main's working theory — that the background invocation (via the harness's
`run_in_background: true` Bash tool) is not fully detached from the invoking shell/tool-call, so it dies on a turn/shell
boundary the way a bare `&` job would on shell exit without `nohup`+`disown` — predicts that a FULLY detached
`setsid`+`nohup`+`disown` run should survive indefinitely. It got meaningfully further (real QG stages, governor
admission, deep into pytest) but STILL died without a clean exit marker on both of the 2 attempts made. This either
means (a) the detach theory is only partially right (detachment helps but something else still kills it later), or (b)
the _checking_ mechanism (polling the log file via a fresh `until grep -q ... ; do sleep 5; done` Bash
`run_in_background` call) is itself part of the problem — that poller was ALSO still running via the harness's own
background-task tracking when compaction interrupted this session, so its own fate (whether it ever detected an
`EXIT_CODE=` line) is unknown as of this doc being filed.

## Why it matters

- **Blocks shipping verified, correct code.** The 3-handler DeFi concurrency fix is done and independently confirmed
  sound (a full clean pre-rebase QG pass, plus zero test failures across 2 different partial post-rebase runs that each
  got well into the TESTS stage) — only the mechanical "get one clean run to mint a sentinel" step is blocked. This is a
  landing-only blocker, not a correctness question.
- **~4 hours of session wall-clock** spent on this single shipping step across ~20 attempts, following (and eventually
  exceeding) the established "don't blind-retry past 2 consecutive kills" precedent from the archived RAM doc — flagging
  because that precedent assumes RAM-exhaustion is the mechanism, and this session's evidence suggests it may not fully
  explain what's happening here, which is itself worth someone with host-level access confirming.
- **A future worker on ANY repo could hit the same wall** if the actual mechanism is a harness/session-level
  background-task issue rather than genuinely host-specific RAM pressure — worth root-causing once rather than every
  future worker independently rediscovering "it's the RAM doc" and burning hours on retries that were never going to
  work for a different reason.

## Recommended decision

Needs someone with either host-level process/journal access (to see what actually sends the kill signal — a per-process
CPU/wall-time budget enforced by something OTHER than `resource-watchdog.sh`? a harness-side background-task timeout
independent of host state? an actual OOM-kill that `dmesg`/journalctl access — unavailable to this unprivileged session
— could confirm or rule out?) or harness/tooling-level visibility into how `run_in_background` tracks and potentially
reaps its own child processes.

## Todos

- [ ] [INFRA] P2. ATTEMPT-THEN-ASK (per D102, 2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md ledger):
      attempt the host/journal-level root-cause investigation via SSM on the shared host with existing access —
      confirm or rule out a genuine kernel OOM-kill (`dmesg | grep -i oom` / `journalctl -k | grep -i "killed
      process"` around the death timestamps logged in this doc's evidence table) vs. a harness-side background-task
      timeout/reaper unrelated to host memory; if a genuine wall (no root/`adm`-group access reachable via SSM
      either), escalate with >=2 options (e.g. request a scoped SSM document granting read-only dmesg/journalctl
      access, or accept the mechanism stays unconfirmed and rely on the cross-repo intermittent-kill evidence already
      gathered). Source: this doc.
- [ ] [INFRA] P3. If the root cause turns out to be harness/session-level (not host RAM), file the correction against
      `plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` (it stays substantially
      correct for most of ITS OWN evidence per its own 2026-08-14 cross-check addendum, but this doc's evidence suggests
      a second, distinct near-instant-kill mechanism may also be riding alongside it — mirrors that same addendum's own
      slot-8/`orphan_reap` misattribution finding). Repo: unified-trading-pm. Source: this doc.
- [x] [CODE] P1. Once quality-gates.sh can complete cleanly for market-tick-data-service, ship the already-committed
      `market-tick-data-service@eeade63b` (3-handler `ParallelPerSymbolRunner` conversion) via the standard Pass-1 QG →
      `quickmerge --agent --files <the 3 handler files>` flow, then flip BOTH
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`'s item-1 checkbox AND
      `plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`'s corresponding todo (line ~849) with the
      shipped SHA. Repo: market-tick-data-service + unified-trading-pm. Source: this doc + the source issue doc's own
      Progress Log entry. — **market-tick-data-service@eeade63b0c**, landed on live-defi-rollout, ancestry verified,
      2026-08-15.

## Progress Log

- 2026-08-15 (slot-15, infra): Filed after BLK-ff9ec1b7 (main's diagnosis: ruled out `resource-watchdog.sh`'s
  RAM/CPU/swap path via `MIN_AGE_SEC=30s` exemption; recommended `setsid`+`nohup`+`disown` as a shell-detach test). Both
  setsid attempts got further than any prior `run_in_background` attempt but still died without a clean exit — evidence
  captured above. Following main's explicit instruction ("if it doesn't complete within ~2 more attempts, stash and
  release GATED") rather than continuing to retry blind. Code stays safely committed locally at
  `market-tick-data-service@eeade63b` (not a stash — an actual local commit, strictly safer); not pushed.
- 2026-08-15 (slot-15, infra): A later `run_in_background` quickmerge attempt (task `bgre3k8hi`) acquired its
  qg-governor token after a 521s queue wait and then ran cleanly end-to-end — full Pass-1 QG green, sentinel verified,
  pushed as `market-tick-data-service@eeade63b0c` to `live-defi-rollout` (ancestry-verified). The near-instant-kill
  mechanism did not recur on this run; todo 3 closed. Todos 1-2 (host-level root-cause investigation) remain open — the
  mechanism itself is still unexplained, this is just evidence it isn't 100% reproducible.
- 2026-08-15 (slot-14, infra): **Cross-repo confirmation — not MTDS-specific.** Hit the identical near-instant-kill
  pattern shipping an unrelated `deployment-service` fix (bumped `launch-measure-honest-coverage-vm.sh`'s default
  MACHINE_TYPE, committed `65248727`). Attempt 1: `bash scripts/quality-gates.sh` via `run_in_background: true` produced
  zero stdout before dying (same shape as this doc's `sleep 180` control). Attempt 2 (retried once per RULES.md, not
  blind-looped): got further — governor token acquired after 3s wait, dep-content gate PASSED, then `Terminated` + the
  script's own SIGTERM-trap fired
  (`❌ [quality-gates] received SIGTERM — wrote kill marker .../qg-governor/killed.<pid>`), confirming an external
  SIGTERM, not a crash/OOM inside the QG process itself. Stopped after 2 consecutive kills per the established precedent
  rather than continuing to retry blind. This strengthens todo 1: whatever sends the kill is repo-agnostic (hit
  `market-tick-data-service` AND `deployment-service` on the same host/session type) and intermittent (both repos have
  ALSO had clean runs), consistent with a host/session-level reaper racing the QG process rather than something specific
  to either repo's QG content. Code stays safely committed locally at `deployment-service@65248727` (not a stash — an
  actual local commit); not pushed. Releasing this task GATED rather than continuing to retry.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-21 — ruling D102 (Near-instant QG kill root-cause)**: ATTEMPT-THEN-ASK — run dmesg/journalctl via SSM on
  the shared host; if no root path exists, record and move on. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
