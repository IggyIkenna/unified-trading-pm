---
doc_type: issue
title:
  "Two self-hosted glue-runner systemd units left INACTIVE on the old orchestrator VM (i-0c9b283b31d6b5ca7) stall UAC
  LDR->main promotion and cascade a Tier-A CI outage across 11 dependent repos (instruments-service main QG-v2 RED is a
  symptom, not a code bug)"
summary: >-
  Slot 11 (agt-152447, BLK-37a5da89, 2026-08-04) fully root-caused instruments-service's main quality-gates-v2 RED as a
  cascading INFRA outage, not a code defect: instruments-service code+tests are GREEN on LDR. Chain: (1) two dedicated
  self-hosted GitHub-Actions glue-runner units are stopped/inactive on the old orchestrator VM (`i-0c9b283b31d6b5ca7`, ip-172-31-5-118) —
  `github-glue-runner-unified-api-contracts@glue-1.service` (inactive) and
  `github-glue-runner-instruments-service@glue-1.service` (externally `systemctl stop`-ped 09:01:57; `Restart=always`
  never fired because an explicit stop suppresses it). (2) UAC's LDR quality-gates-v2 for commit d67a226f (the OKX_SWAP
  venue-registry cleanup already consumed by instruments-service LDR code) has been stuck QUEUED ~1hr (run 30894307404)
  with no runner to pick it up. (3) UAC therefore cannot promote LDR->main (its own ci_status=FAILING), and the fleet
  dep-order/Tier-A gate (bottom-up drain) blocks all 11 dependent repos incl. instruments-service. (4)
  instruments-service's own LDR run (30894282946) is likewise stuck on its stopped runner. Main agt-1756f6 INDEPENDENTLY
  VERIFIED (read-only `systemctl is-active`): both named units are `inactive` while all 11 OTHER repos'
  `github-glue-runner-*@glue-1.service` units are `active/running` — corroborating the two-unit anomaly. **Neither the
  worker nor main can fix it**: `sudo` is blocked by a no-new-privileges flag for both, and neither has AWS SSM
  (`ikenna-worker` lacks `ssm:DescribeInstanceInformation`). Needs someone with host root on the old orchestrator VM (`i-0c9b283b31d6b5ca7`) (or SSM) to
  `systemctl start` the two units. Secondary finding: the glue-runner-crash-loop-watchdog does NOT catch this class — it
  only flags units actively crash-looping (repeated restarts), not a unit sitting cleanly `inactive`/stopped.
status: open # summary below describes the ORIGINAL P1 host-access blocker, which was resolved same-day
  # (2026-08-04) -- corrected 2026-08-16 (plan_reconciler Phase -1). 2 open todos remain, both narrower P2/P3
  # follow-ups (monitoring-gap extension; no automated deploy/sync -- now RESOLVED, see Todos).
nature: issue
asset_group:
  [ci] # corrected 2026-08-16 (/ag-closeout-audit cross-cutting parked finding 6, meta_plan_corpus_hygiene_ao_dispatch_batch1)
  # -- was [cross-cutting]. Content is a fleet-wide self-hosted GitHub-Actions glue-runner systemd-unit outage
  # stalling LDR->main promotion, squarely ci-tranche (CI/CD runner infra).
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [admin, engineer]
tags: [ci-outage, glue-runner, self-hosted-runner, systemd, tier-a-gate, promotion-blocked, monitoring-gap, big-finding]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: 2026-08-04
author: ikennaigboaka [main·planning]
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source: ["slot-11 agt-152447 blocked BLK-37a5da89 (2026-08-04); main agt-1756f6 independent systemctl verification"]
drift_direction: advance-process
estimate_class: infra
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/04-architecture/ci-alerting.md,
    scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
  ]
---

# Fleet CI outage: two stopped glue-runner units block UAC->main + 11 dependent repos

> **🔴 FLEET CI OUTAGE — 11 repos' LDR->main promotion blocked ~1h+ by two stopped self-hosted runners on the planning
> VM. Immediate fix needs host root (`systemctl start` ×2). instruments-service main QG-v2 RED was ALSO a genuine
> test-layer break (now fixed on LDR as `96ea6c4b`, see "Correction" below) — the runner outage still blocks a fresh CI
> reading, but was never the sole cause.**

## Root-cause chain (slot-11-diagnosed, main-verified)

1. `github-glue-runner-unified-api-contracts@glue-1.service` — **inactive** on ip-172-31-5-118 (main verified via
   `systemctl is-active`). No runner => UAC LDR quality-gates-v2 for `d67a226f` stuck **QUEUED ~1h** (run 30894307404,
   `workflow_dispatch`).
2. `github-glue-runner-instruments-service@glue-1.service` — **inactive**; per slot-11, explicitly `systemctl stop`-ped
   at 09:01:57 (external stop => `Restart=always` suppressed), stuck since. instruments-service LDR run 30894282946 has
   no runner.
3. UAC cannot promote LDR->main (own `ci_status=FAILING`); the dep-order / Tier-A bottom-up-drain gate blocks all 11
   dependent repos incl. instruments-service — so instruments-service **main** QG-v2 is RED purely because it resolves
   `unified-api-contracts` against a STALE UAC main (missing `d67a226f`'s OKX_SWAP venue-registry cleanup, already on
   UAC LDR + already consumed by instruments-service LDR). The 4 failing OKX-SWAP venue tests are the visible symptom.
   **Correction (cicd slot-3, agt-0f742e, 2026-08-04, live verification): the "instruments-service code+tests are GREEN
   on LDR" claim above is WRONG for the test layer** — `d67a226f` also removed bare `"OKX"` as a `CEFI_VENUE_FOLD`
   target (OKX-SWAP/OKX-FUTURES became their own declared venues), but instruments-service's own tests were never
   updated to match. This is NOT a runner-outage artifact: the completed (non-stuck) main run 30893378880 actually
   EXECUTED pytest and produced real `AssertionError`s (`assert 'OKX-SWAP' == 'OKX'`, golden-fixture drift, factory
   itype-exchange mismatch, dedup-count pin drift) — an infra/runner failure would abort the workflow, not produce a
   clean pytest diff. Confirmed independently via a local `.venv` install of the exact editable UAC content (same
   `CEFI_VENUE_FOLD` dict, no bare `OKX` key). Fixed + shipped to `instruments-service@live-defi-rollout` as `96ea6c4b`
   (full `quality-gates.sh` green, 5200 passed) — see `cefi_bare_okx_venue_removal_2026_08_04.md`, which shipped the
   UAC+MTDS side of this migration but omitted the instruments-service test update. **Net**: the runner-outage root
   cause (below) is still real and still blocks a FRESH green CI reading from landing, but it is no longer the ONLY
   thing standing between instruments-service and a green LDR — the test-layer fix was also required and is now on LDR.
4. All 11 OTHER repos' `github-glue-runner-*@glue-1.service` units are `active/running` (main verified) — confirming the
   two named units are the isolated anomaly, not a fleet-wide runner-config problem.
5. **CORRECTION 2026-08-04 (interactive session, `/autonomous` continuation) — a THIRD unit was ALSO stopped, undetected
   by this doc's original sweep**: `github-glue-runner-market-tick-data-service@glue-1.service` was independently found
   `inactive` while investigating an unrelated MTDS workflow stuck QUEUED since 11:09Z. `journalctl` for all three units
   shows the SAME pattern within the SAME ~30s window (08:59:35–09:02:27 UTC): each was mid-job
   (`Running job: Quality Gates ...`) when systemd logged an EXTERNAL `Stopping ...` action, cancelling the in-flight
   job — not a crash, not a `Restart=always` failure. Host `uptime`/`apt` history/process list show NO reboot, NO
   package upgrade, and NO active maintenance process around that window (last boot 2026-07-29, last apt upgrade
   2026-08-01) — nothing found to correlate with a deliberate pause, so this reads as an anomalous/unexplained
   coordinated stop across (at least) 3 units, not confirmed-safe-to-assume-intentional but also not evidence of
   in-flight work to protect. The original "all 11 others active" claim was accurate for what slot-11/main checked at
   the time; it did not cover MTDS.

## Why neither worker nor main can self-serve

`sudo` is blocked by a `no-new-privileges` flag for BOTH the worker session and main agt-1756f6 (verified `sudo -n true`
=> "no new privileges" error). Neither has AWS SSM (`ikenna-worker` lacks `ssm:DescribeInstanceInformation`). Restarting
a systemd unit needs host root / SSM on the old orchestrator VM (`i-0c9b283b31d6b5ca7`) — genuinely operator-gated.

## Todos

- [x] ✅ [OPERATOR] P1. **RESOLVED 2026-08-04 (interactive session, `/autonomous` continuation) — executed via AWS SSM
      (`admin_od` identity has `ssm:DescribeInstanceInformation` + Run Command reach to i-0c9b283b31d6b5ca7, unlike the
      `ikenna-worker`/main identities that filed this as operator-gated).** Read-only checked all three stopped units
      first (journal history, host uptime, apt history, running processes — see correction above) to rule out
      interrupting genuine in-flight maintenance before touching anything; found none. Ran
      `systemctl start github-glue-runner-{unified-api-contracts,instruments-service,market-tick-data-service}@glue-1.service`
      via SSM `AWS-RunShellScript`; confirmed all three `active` (running) via a follow-up `systemctl is-active`.
      **Live-verified the fix took**: MTDS's queued `update-dependency-version` run (30903608513, queued since 11:09Z)
      moved to `in_progress` within seconds of the restart and completed `success` at 11:27Z; MTDS's `quality-gates-v2`
      run also left QUEUED. Did not independently re-verify the UAC/instruments-service run IDs named above (they were
      slot-11/main's runs, may have timed out/been superseded by now) — whoever next touches this repo should confirm
      UAC's `ci_status` and the Tier-A drain completed, not just that the runners are active again.
- [x] ✅ [DIAG] P1. **Root-cause investigation, 2026-08-04 (same session), inconclusive after exhausting every checkable
      channel — closing a related gap instead of leaving this as a dead end.** Confirmed via `journalctl`
      (`StartLimitIntervalSec=0`/`Restart=always` on every `github-glue-runner-*` unit — "never give up restarting" by
      design) that an EXPLICIT stop request (not a crash, not self-inflicted rate-limiting) is the only thing that can
      explain the outage — `Restart=always` only stands down on a deliberate `systemctl stop`/equivalent. Checked every
      channel that could have issued it, all NEGATIVE: (1) SSH — `last -F` shows no login within 2 weeks of the
      incident; (2) SSM Run Command — `aws ssm list-commands` shows one command that day, ~9h before the incident, none
      in-window (success or failed); (3) SSM Session Manager (interactive) — `aws ssm describe-sessions --state History`
      shows zero sessions that day; (4) host crontab / `/etc/cron.d` — no job resembling a targeted stop; (5) the
      `github-glue-slot-refresh-*` timers (a DIFFERENT, unrelated mechanism — periodic `git pull` of the runner's repo
      mirror, `Type=oneshot`/`Restart=no`, no stop capability) fired ~1min AFTER the incident window, ruled out on both
      mechanism and timing; (6) `systemd-oomd` — confirmed `inactive` on this host; (7) kernel OOM / memory pressure —
      zero `oom`/`killed process` lines in `journalctl -k`/`dmesg` for the window, and `sar -r` shows the host at 15-18%
      memory used at the time (comfortable, not under pressure). No `auditd` was installed, so the actual
      `systemctl stop` invocation's calling UID/process could not be attributed after the fact — that IS the real,
      fixable gap. **Installed `auditd` + `audispd-plugins` on the old orchestrator VM (`i-0c9b283b31d6b5ca7`) via SSM** with a watch rule on
      `/usr/bin/systemctl` execution (`-w /usr/bin/systemctl -p x -k systemctl_exec`), verified `active` + rule loaded
      (`auditctl -l`). This does not explain THIS incident, but any recurrence is now attributable via
      `ausearch -k systemctl_exec`. Leaving this specific incident's trigger formally unknown rather than guessing.
- [ ] [INFRA] P2. **Close the monitoring gap.** The glue-runner-crash-loop-watchdog only flags units actively
      crash-looping (repeated restarts), so a runner sitting cleanly `inactive`/stopped (Restart=always suppressed by an
      explicit stop) evades detection — exactly this incident. Extend the watchdog (or add a sibling check) to alert
      when any expected `github-glue-runner-<repo>@glue-1.service` is `inactive`/`dead`/`failed` for > N minutes while
      peer runners are active, so a stopped runner pages instead of silently stalling promotion for an hour. Repo:
      **unified-trading-pm** (`scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh` — corrected 2026-08-06
      (/plan-reconcile ao); previously mis-pointed at agent-orchestrator, see this doc's context-scout 2026-08-06 note
      below). Target host for this watchdog's own alert logic and any live-state checks: the CI-runner VM
      (`i-042a6332509482556`, the box that actually hosts the glue/writer fleet today — confirmed live below), not the
      old orchestrator VM (`i-0c9b283b31d6b5ca7`), which no longer hosts runners since the 2026-08-05 fleet-split
      migration. Cross-ref `/codex/05-infrastructure/deployment-observability.md`, `/codex/04-architecture/ci-alerting.md`.
      **2026-08-05 addendum: a THIRD failure mode found (see Progress Log) — "active" at the systemd level but hung
      mid-job for hours, then failing to re-register with GitHub even after restart. The watchdog must catch this too,
      not just crash-loop and cleanly-inactive**, e.g. alert on a runner whose `journalctl` shows "Running job" with no
      matching "completed" line for > N minutes, independent of systemd `ACTIVE` state (which stays green throughout
      this failure mode). **Root-cause-of-the-original-stop investigation (2026-08-04/05, interactive session,
      `/autonomous` continuation), operator-requested — inconclusive, documented so the next investigator doesn't
      re-walk the same dead ends.** Confirmed via precise `journalctl` (`-o short-precise`, correctly time-windowed)
      that all three units logged systemd's explicit `Stopping <unit> - <description>...` line within the same ~30s
      window while each was mid-job — this is systemd's own signature for an EXPLICIT stop request, not a self-exit (the
      JIT runner's own clean-exit path logs a distinct "Runner listener exit with 0 return code" message instead, and
      that pattern fires constantly and harmlessly for every other repo's runner throughout the surrounding log — it is
      NOT what happened here). Ruled out, each independently verified live on the host: (1) SSH — `last -F` shows no
      login anywhere near the incident window (most recent prior login was 11 days earlier); (2) AWS SSM —
      `list-commands` against the instance shows zero commands (successful OR failed) in the incident window, from any
      identity; (3) cron/crontab — no job targets these units or fires near that time; (4) systemd self-inflicted
      rate-limiting — ruled out directly, the unit file has `StartLimitIntervalSec=0` with an explicit comment ("Never
      give up restarting — the glue-* pool exits after every single job by design"), so a restart-rate lockout is
      structurally impossible for this unit; (5) the `github-glue-slot-refresh-*` timers — a DIFFERENT, unrelated
      service (git-clone-refresh only, `Restart=no`, oneshot) that happened to run a few minutes later and is a dead
      end; (6) GitHub's own audit log — unavailable via API for this account (`404`, audit-log is an org/enterprise-only
      endpoint, this is a personal-account repo). No `auditd` installed on the host, so there is no OS-level record of
      which process/session issued the stop. **Remaining candidate, unprovable from this host alone**: a GitHub-side
      action (e.g. a runner removed/deregistered via the GitHub API or UI) that the runner's own wrapper script
      propagates into a self-directed `systemctl stop` on clean deregistration — would explain an explicit-stop
      signature with zero local trace, but confirming it needs GitHub's audit log (org/enterprise plan) or the
      operator's own recollection of any action taken around 08:59:35–09:02:27 UTC on 2026-08-04, neither of which this
      session has access to. Genuine root cause: NOT DETERMINED.
- [x] ✅ [INFRA] P1. **RESOLVED 2026-08-05 (same session, later).** `writer-1/2/3` on the CI-runner VM
      (`ip-172-31-3-59`, instance `i-042a6332509482556` — a DIFFERENT box from the old orchestrator VM
      `i-0c9b283b31d6b5ca7` named above, despite this entry's original "SAME planning VM" framing at the time;
      unified-trading-pm's own writer pool) — root cause was a
      **diagnostic miss, not a genuinely unfixable hang**: my earlier "root cause NOT found" checks
      (`systemctl status actions.runner.*`, `journalctl -u actions.runner.*`) matched ZERO units, because these runners
      are NOT self-registered `actions.runner.*` services — they're custom systemd TEMPLATE units,
      `github-glue-runner@writer-N.service` (unified-trading-pm) and `github-glue-runner-ao@writer-1.service`
      (agent-orchestrator, a SEPARATE registration + a SEPARATE `/opt/github-glue-runners-ao/` directory tree on the
      same host — do not confuse the two pools). Every earlier "restart"/"check" against the wrong unit name silently
      no-op'd. With the real names: `systemctl status`/`journalctl -u github-glue-runner@writer-N.service` showed two
      DIFFERENT genuine failure shapes, not one — (a) agent-orchestrator's `writer-1` had never actually been restarted
      this incident at all (`Active: since Aug 04 09:43`) and was looping
      `TaskCanceledException`/`SocketException(125) Operation canceled` on stale TLS reads against the Actions broker
      (`pipelinesghubeus3.actions.githubusercontent.com`) — a long-lived HTTP/2 connection that died without the client
      detecting it, a known self-hosted-runner failure class; (b) unified-trading-pm's `writer-1/2/3`, already
      `systemctl restart`-ed earlier this session via the correct unit name, were genuinely stuck silently at init
      (`_diag` log frozen at exactly 4 startup lines for 30+ min despite the process actively consuming CPU) — DNS,
      disk, and `curl https://api.github.com` all confirmed healthy, ruling out host-level network/infra causes.
      **Fix**: `sudo systemctl restart` on the correct 4 unit names (`github-glue-runner-ao@writer-1.service` +
      `github-glue-runner@writer-{1,2,3}.service`) via SSM. Verified via the GitHub API (not just systemd `is-active`,
      which was misleadingly green throughout): all 4 `online` within ~15s of restart; the 3 unified-trading-pm writers
      immediately went `busy: true` on real queued work. Confirmed materially fixed, not cosmetic:
      `ldr-to-main-promote-fleet.yml`'s two prior manual dispatches had each sat queued then been auto-cancelled after
      12-15min with no runner ever attaching — the run dispatched immediately after this fix stayed
      `pending`/progressing past that same window instead of being cancelled.
- [x] ✅ [OPERATOR] P1. **RETRACTED — diagnosed against the WRONG box; closing as MOOT (corrected 2026-08-06
      (/plan-reconcile ao), citing this doc's own `[DIAG] P1` correction entry below).** The correction re-verified via
      read-only SSM on BOTH real instances: the "0 loaded units for every per-repo pool" / "ENTIRE glue/writer pool ...
      is down" finding below was measured against `i-0c9b283b31d6b5ca7` — the OLD orchestrator VM, whose runner fleet
      was CORRECTLY, deliberately migrated off per
      `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` (complete 2026-08-05) — not a real
      outage. The actual dedicated runner VM (`i-042a6332509482556`) was healthy the entire time (17/17 units active, 0
      failed): there was nothing to `systemctl start` or reinstall. **No operator action remains from this todo** — its
      own actual dispatch reason (unified-api-contracts main QG-v2 RED) was already independently fixed within this same
      entry (see below), and that fix stands regardless of the wrong-box misdiagnosis. Original diagnosis + shipped fix
      preserved verbatim below for the audit trail. **4th recurrence, 2026-08-06 (cicd slot-4, agt-80cfec, `main_ci_red`
      for unified-api-contracts) — worse than every prior occurrence: the ENTIRE glue/writer pool on the old orchestrator VM
      (`i-0c9b283b31d6b5ca7`, ip-172-31-5-118) is down, not just 2-4 units.** `systemctl list-units 'github-glue-runner@*' --all` shows the
      base unified-trading-pm pool (`glue-1..5`, `writer-1..3`) all `inactive (dead)`/`disabled`;
      `github-glue-runner-<repo>@*` shows **0 loaded units for every per-repo pool** (unified-api-contracts included) —
      not "stopped", never even registered/loaded on this box. `setup-glue-runners.sh status` independently confirms: 0
      systemd units, only token/slot-refresh timers ticking. `glue-runner-crash-loop-watchdog` reports "0/0
      crash-looping" every 5min (expected per the P2 todo above — it only catches an ACTIVE unit crash-looping, not a
      fleet with nothing loaded at all, so it never paged). Same access wall as every prior entry: `sudo` blocked by
      `no-new-privileges` in this slot's sandbox, no SSM identity available to this role. **Did not attempt the infra
      fix** (operator-gated, same as always) — instead found + shipped a real, narrower, independently-useful fix for
      the SPECIFIC symptom this escalation was dispatched for: main's copy of unified-api-contracts'
      `.github/workflows/quality-gates-v2.yml` was stale, still requiring
      `self_hosted_runner_labels: ["self-hosted","glue"]`, even though
      `unified-trading-pm/scripts/workflow-templates/ self-hosted-qg-repos.txt` removed unified-api-contracts on
      2026-08-05 (public repo, GitHub-hosted is unmetered) and `live-defi-rollout`'s copy already carries the correct
      `ubuntu-latest` default — main just never got that specific promotion. Re-rolled main's copy directly (commit
      `5acc9859`, `.github/**`-only carve-out) — confirmed GREEN afterward (run `31069093947`, all legs on
      `ubuntu-latest`, no dependency on the dead pool at all). This is a **workaround for one repo's one symptom, not a
      fix for the underlying outage** — every other repo still on `self-hosted-qg-repos.txt` (`agent-orchestrator`,
      `unified-trading-pm`, `strategy-service`, `e2e-testing`, `features-service`, `market-tick-data-service`,
      `execution-service`, `ml-service`) was believed still fully blocked at filing time; **per the correction, that
      "still fully blocked" claim is ALSO wrong-box-derived and should not be trusted without a fresh per-repo check.**
      ~~Needs the same operator/host-root action as every prior entry: SSH or SSM onto the old orchestrator VM (`i-0c9b283b31d6b5ca7`) and either
      `systemctl start` the existing units or re-run `setup-glue-runners.sh install` per
      `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` if this was a central-VM relaunch~~ —
      **superseded by the correction: no such action is needed, the real runner VM was never down.**
- [x] ✅ [DIAG] P1. **CORRECTION to the "4th recurrence" todo above, 2026-08-06 (interactive session) — the "0 loaded
      units anywhere" finding was a diagnosis performed against the WRONG box, not a real fleet-wide outage.**
      Independently re-verified via read-only SSM `systemctl list-units 'github-glue-runner*' --all` on BOTH real
      instances: (1) the OLD orchestrator VM (`i-0c9b283b31d6b5ca7`, private IP `172.31.5.118` — confirmed via
      `hostname -I`, matching this doc's "planning VM (ip-172-31-5-118)" references) genuinely shows 0 loaded
      `@glue-N`/`@writer-N` job-runner units (only `.slice` cgroup caps and `@github-glue-token-refresh-*` oneshot
      timers, both cosmetic/expected) — **but this is CORRECT and BY DESIGN**, not a fault: the entire runner fleet was
      deliberately migrated off this box per
      `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`, confirmed complete as of
      2026-08-05. (2) The actual dedicated escalation-runner VM (`i-042a6332509482556`, private IP `172.31.3.59`, the
      SAME instance this doc's own 2026-08-05 entry calls "writer-pool host" and separately warns "the planning VM and
      this writer-pool host are DIFFERENT instances despite the similar naming") is **healthy right now**: 17 active
      `@glue-N`/`@writer-N` units, 0 failed, covering `agent-orchestrator`, `unified-trading-pm`,
      `market-tick-data-service`, `execution-service`, `features-service`, `ml-service`, `strategy-service`,
      `e2e-testing`. Practical consequence: the live `main_ci_red` escalations at the time of writing (deployment-api,
      deployment-service, ibkr-gateway-infra, market-tick-data-service) are almost certainly genuine app/test-level CI
      failures, NOT infra — MTDS's own runner is confirmed healthy, and
      deployment-api/deployment-service/ibkr-gateway-infra have no units registered on the new VM at all (consistent
      with being on the GitHub-hosted `self_hosted_runner_public_repo_revert` list, so this outage class was never even
      applicable to them). **Does not retract the unified-api-contracts fix in the entry below** (that one correctly
      diagnosed a stuck/unclaimed run and the `ubuntu-latest` re-roll fixed it regardless of root-cause attribution) —
      only the "ENTIRE glue/writer pool ... is down" / "0 loaded units for every per-repo pool" framing in the
      `[OPERATOR] P1` todo above, which conflated the correctly-decommissioned old VM with a real outage.
- [x] ✅ [INFRA] P3. **DONE 2026-08-15 (slot-15·infra).** This doc's own history called at least 3 different real EC2
      instances "the planning VM" at different points (`i-0c9b283b31d6b5ca7` old orchestrator box, `i-042a6332509482556`
      dedicated CI-runner VM, `i-0dd9812a96cdda5dc` human-planning VM) — the ambiguity directly caused the misdiagnosis
      corrected above (an agent checked the old, correctly-empty box instead of the new dedicated runner VM). Fixed:
      replaced every ambiguous "the planning VM" reference in this doc's Root-cause chain / Why-neither-can-self-serve /
      Todos / Progress Log sections with the specific instance ID (+ stable label — "old orchestrator VM" for
      `i-0c9b283b31d6b5ca7`, "CI-runner VM" for `i-042a6332509482556`); `i-0dd9812a96cdda5dc` (human-planning VM, itself
      terminated 2026-08-03 per CLAUDE.md) was never actually implicated in any finding here, named only to close the
      ambiguity. Also added an explicit host pointer to the P2 monitoring-gap todo above, naming `i-042a6332509482556` as
      the watchdog's target host, not `i-0c9b283b31d6b5ca7`. Fleet-wide grep confirmed no other codex/monitoring doc in
      this corpus (`deployment-observability.md`, `ci-alerting.md`, the watchdog script itself) uses the ambiguous
      "planning VM" phrase — this doc was the sole source. The remaining quoted uses of "planning VM" in this doc (the
      2026-08-06 correction entries + the final Progress Log entry) are deliberately left as verbatim quotes of the
      original ambiguous language, since they're the narrative record of the confusion this fix closes, not fresh
      ambiguous references.
- [x] ✅ [INFRA] P1. **RESOLVED 2026-08-06 (same session, shipped `879e3e109`).** A THIRD distinct monitoring-gap
      dimension found 2026-08-06: the crash-loop watchdog was structurally false-positiving on every healthy `@glue-N`
      unit, independent of the cleanly-inactive/wedged gaps above.** `is_crash_looping()` only checked
      `SubState=auto-restart` + `NRestarts>=5`, but per `github-glue-runner@.service`'s own design comment ("glue-*: one
      job per process, restart to re-register"), `Restart=always` fires on EVERY exit including a clean job-completion
      (`Runner listener exit with 0 return code, stop the service, no retry needed`), and `NRestarts` is a lifetime
      counter that never resets. A healthy glue-N unit crosses the threshold within its first few jobs, then sits above
      it FOREVER — any 5-min poll landing in the ~5s restart window between two clean job cycles pages a false
      `CRITICAL "runner process is DOWN"` alert on a unit that was never down. Live-caught in real time (see Progress
      Log): this exact bug produced the operator-visible alert that opened the session
      (`github-glue-runner@glue-2.service`, `NRestarts=968`) plus two more mid-session (`glue-3`/`glue-5`), each
      independently confirmed via `journalctl` to be clean `Result=success` exits with zero actual failures — `glue-3`/
      `glue-5` even self-"recovered" ~6 minutes later purely from poll-timing luck, the exact false-alert-then-bookend
      flap this fix eliminates structurally rather than by chance. **Fix**: gate `is_crash_looping()` on
      `Result != success` (systemd's verdict on the unit's last completed run) in addition to the existing checks — the
      original 2026-07-28 GCP_PROJECT-missing incident this watchdog was built for exited non-zero every time, so real
      crash-loop detection is unaffected. **Deployed live** to `i-042a6332509482556` (`/usr/local/sbin/`, plus the
      `/opt/github-glue-runners/repo/` and `/opt/glue-deploy/unified-trading-pm/` mirrors — all three previously
      divergent, now matching one hash) and verified via a manual trigger (`0/17 crash-looping`, empty `alerted-units`
      state file) BEFORE the repo commit — host QG capacity was critical at diagnosis time (load avg ~168, ~60MB free
      RAM, ~91% swap used, 8-9 concurrent `quality-gates.sh` runs from other slots) and quickmerge's full QG has no skip
      path, so committing then risked tipping a shared, already memory-constrained host into an OOM cascade that could
      kill other slots' legitimate runs (the exact class in
      `/plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`). Host load dropped (~10
      within the hour) and the fix shipped to `live-defi-rollout` as `879e3e109` (quickmerge's SHA-sentinel skipped a
      redundant Pass-2 QG re-run, so this added no extra host load) — draining to `main` via `ldr-to-main-promote.yml`
      on the normal ~15-30min SLA, not yet independently re-verified on `main`.
- [x] ✅ [INFRA] P3. **RESOLVED — DONE 2026-08-16 (plan_reconciler Phase -1).** `unified-trading-pm@572addd34f` adds
      `scripts/self-hosted-runners/deploy-sbin-scripts.sh` (header comment cites this exact todo) +
      `github-glue-deploy-sync.{service,timer}`, wired into `setup-glue-runners.sh`'s base-pool install path (verified
      `systemctl enable --now github-glue-deploy-sync.timer` at lines 587-601) — a real ~10-min sync, verified ancestor
      of HEAD. Was: **No automated deploy/sync exists for this watchdog script at all — found while fixing the item
      above.** The live host's executed copy (`/usr/local/sbin/glue-runner-crash-loop-watchdog.sh`) was already stale
      before today's fix, missing the 2026-08-05 unit-enumeration pattern-match fix documented in this same script's own
      header comment (bare `grep glue` vs. the `github-glue-runner*` glob). No workflow, cron, or install script
      references `/usr/local/sbin/glue-runner-crash-loop-watchdog.sh` (`setup-glue-runners.sh`, the closest candidate,
      doesn't touch it) — every prior fix needed a manual SSM copy that evidently didn't happen consistently. Wire an
      automated sync (e.g. a step in `setup-glue-runners.sh`, or a small `git pull`-and-diff timer) so a future repo fix
      actually reaches the host instead of silently sitting uncommitted-to-production indefinitely.

## Progress Log

- **2026-08-04 (main agt-1756f6)** — Filed on slot-11's BLK-37a5da89. Independently verified (read-only `systemctl`):
  both named units `inactive`; all 11 peer `@glue-1` runners `active/running`; main also lacks sudo (no-new-privileges)
  so cannot self-serve. Answered the blocked question (Option A — operator host restart; disposition partial, the fix is
  operator-executed) and told slot-11 to stand down (fully diagnosed, nothing more it can do). This is a big finding
  (fleet CI outage, 11 repos, CI-critical path) — routed to the operator via this P1 issue doc's `[OPERATOR]` todo.
- **2026-08-04 (cicd slot-3, agt-0f742e, escalation `main_ci_red`)** — Dispatched to fix instruments-service main
  quality-gates-v2 RED. Found the "GREEN on LDR" claim above was incomplete: the completed (non-stuck) main run
  30893378880 shows real pytest `AssertionError`s from `d67a226f`'s bare-`OKX` fold removal never being reflected in
  instruments-service's own tests (`_canon_venue` fold assertions, the cefi expected-universe golden, the bare-OKX
  itype-exchange gather, a dedup'd-target-count pin). Fixed all 4, regenerated the golden fixture, verified full
  `quality-gates.sh` green locally (5200 passed, 6 skipped), shipped to `live-defi-rollout` as `96ea6c4b` (verified
  ancestor-of-origin). Added the "Correction" note above rather than leaving the incomplete diagnosis to stand. Did NOT
  touch the glue-runner infra (operator-gated, out of scope for this role, already correctly filed as the P1
  `[OPERATOR]` todo below).
- **2026-08-04 (interactive session, `/autonomous` continuation)** — Hit this same outage independently while chasing an
  unrelated stuck MTDS workflow (`update-dependency-version`, queued 10+ min). Found a THIRD stopped unit
  (`market-tick-data-service`) this doc's original sweep missed. Had SSM reach to the old orchestrator VM (`i-0c9b283b31d6b5ca7`) via the interactive
  session's own `admin_od` AWS identity — a capability the filing identities explicitly lacked — so executed the P1 fix
  directly rather than re-escalating: read-only diagnosis (journal, uptime, apt history, `ps`) found no evidence of
  legitimate in-flight maintenance around the 09:01-09:02Z stop window, then `systemctl start` on all three units,
  confirmed `active`, confirmed the MTDS workflow immediately picked up a runner and completed. **P1 done. P2
  (monitoring-gap hardening in agent-orchestrator) is NOT done** — left open as the genuine remaining follow-up; this
  doc's `status` stays `open` until that lands. Also note for whoever picks up P2: three units stopping within the same
  ~30s window, each cancelling an in-flight job, is a pattern worth alerting on directly (not just "any one unit
  inactive too long") — a coordinated multi-unit stop is a stronger signal than an isolated one.
- **2026-08-04 (interactive session, same continuation, on operator direction "fix the root of these blockages too")** —
  Spent 7 SSM round-trips trying to attribute the actual stop trigger; came up empty on every channel (see the new
  `[DIAG] P1` todo above for the full checklist). Converted the dead end into a real hardening: installed `auditd` on
  the old orchestrator VM (`i-0c9b283b31d6b5ca7`) with a watch on `systemctl` exec, so a repeat incident is attributable
  within minutes instead of
  requiring this kind of after-the-fact archaeology. P2 (extending the crash-loop watchdog to catch a cleanly-`inactive`
  unit, not just a crash-looping one) remains the one open item — still correctly scoped to `agent-orchestrator`, not
  something to bolt onto this session's host-level access.
- **2026-08-05 (interactive session, unrelated token-usage-tracking work, hit this class of outage a third time)** —
  While trying to speed up an agent-orchestrator quickmerge's LDR->main promotion, found `writer-1/2/3` (a DIFFERENT
  pool than this doc's original 3 units — unified-trading-pm's own writer runners, same host) all showed GH-API
  `offline`+`busy` simultaneously. `journalctl` showed all three stuck on `Running job: update-ci-status` since ~10:20
  with no completion line ~2h later — a THIRD distinct failure shape (hung mid-job, not crash-looping, not cleanly
  stopped). Restarted via SSM (`i-042a6332509482556`, correcting an initial wrong-instance-ID mistake — the old
  orchestrator VM (`i-0c9b283b31d6b5ca7`) and this writer-pool host (`i-042a6332509482556`) are DIFFERENT instances
  despite the similar naming) after confirming host disk/memory were
  healthy and it wasn't a resource-exhaustion crash-loop. Restart cleared the hang (old PID SIGKILLed) but did NOT
  restore GitHub connectivity — added as the new `[INFRA] P1` todo above, left genuinely unresolved (not a "someone
  else's problem, wait" case — I could not find the root cause with the access/tools available in this session). Also
  extended the existing `[INFRA] P2` watchdog todo to explicitly cover this "active-but-hung" shape, since the current
  framing (crash-loop vs. cleanly-inactive) would miss it too.
- **2026-08-05 (same session, later) — root-caused and RESOLVED, closing the `[INFRA] P1` todo above.** The earlier
  "root cause not found" was a diagnostic miss: `systemctl status actions.runner.*` (GitHub's own default self-install
  naming convention) matched nothing, because this fleet's runners are custom systemd template units named
  `github-glue-runner@writer-N.service` (found by `find /etc/systemd/system -iname '*glue*'`, then confirmed against
  `glue-runner-run.sh`'s own header comment). With the real unit names, `journalctl -u` showed real, readable state for
  the first time: agent-orchestrator's `writer-1` (a separate registration + directory tree,
  `/opt/github-glue-runners-ao/`, from unified-trading-pm's `/opt/github-glue-runners/`) had silently stopped
  long-polling GitHub's broker after a stale TLS connection, never actually restarted this incident despite being named
  in the earlier todo; unified-trading-pm's `writer-1/2/3`, already restarted once via the correct unit name earlier
  this session, were separately stuck silently at process init. `sudo systemctl restart` on all 4 correct unit names via
  SSM fixed both: GitHub API confirmed all 4 `online` within 15s, the 3 unified-trading-pm writers went `busy` on real
  queued work immediately, and a `ldr-to-main-promote-fleet.yml` run dispatched right after stayed progressing past the
  12-15min mark where the two prior attempts had been auto-cancelled. **Lesson for next time**: when a self-hosted
  runner investigation on this host comes up empty, verify the unit name against `glue-runner-run.sh`'s header comment
  or `find /etc/systemd/system -iname '*glue*'` FIRST — `actions.runner.*` is the wrong pattern fleet-wide here, and a
  `systemctl`/`journalctl` query against a non-existent unit name fails silently (empty output, not an error), which
  reads exactly like "nothing to report" instead of "you queried the wrong thing."
- **context-scout 2026-08-06**: populated context_scope (4 entries). Note: the P2 todo's "Repo: agent-orchestrator
  (deployment/monitoring)" pointer is STALE — the actual glue-runner-crash-loop-watchdog lives in THIS repo
  (`scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh`), not agent-orchestrator; no such path exists there.
- **2026-08-06 (cicd slot-4, agt-80cfec, `main_ci_red` escalation for unified-api-contracts)** — Dispatched to fix
  `quality-gates-v2` RED on unified-api-contracts' main. Diagnosis: main's most recent push-triggered run had a `tests`
  leg that sat 38min mid-run then got force-cancelled (`##[error]The operation was canceled.`) — not a code failure (the
  `checks` leg had already passed clean). Re-triggering via `workflow_dispatch` reproduced worse: both `tests` and
  `checks` legs sat `queued` with `runner_name: ""` for 20+ minutes, never claimed by anything. Traced to this doc's
  exact outage class, but at full-fleet scale this time (see the new `[OPERATOR] P1` todo above for the systemctl/
  setup-glue-runners.sh evidence — 0 loaded runner units anywhere, not just 2-4 stopped ones). Could not self-serve the
  infra fix (same `no-new-privileges`/no-SSM wall as every prior entry in this doc). Shipped a scoped, independently-
  correct workaround instead: main's `.github/workflows/quality-gates-v2.yml` was stale (still pinned to
  `self_hosted_runner_labels: ["self-hosted","glue"]` from before unified-api-contracts was removed from
  `self-hosted-qg-repos.txt` on 2026-08-05), so re-rolled it to match `live-defi-rollout`'s already-correct
  `ubuntu-latest` copy (commit `5acc9859`, direct push to main under the `.github/**`-unblock-the-pipeline carve-out).
  Confirmed GREEN: run `31069093947` completed successfully entirely on GitHub-hosted runners. Cancelled the
  now-permanently-stuck `workflow_dispatch` run `31067911291` first so it didn't linger queued forever. This closes MY
  wall (`quality-gates-v2` on unified-api-contracts main) but does **not** touch the underlying pool outage — added a
  fresh `[OPERATOR] P1` todo above since this doc's `status: open` correctly reflects that the root cause is back again,
  now at a larger blast radius than any prior entry.
- **2026-08-06 (interactive session, operator-triggered CI audit)** — Operator asked why the "hundreds of AO
  escalations" they were seeing didn't square with a 25-repo fleet; while investigating live `main_ci_red` escalations
  (deployment-api, deployment-service, ibkr-gateway-infra, market-tick-data-service), re-checked this doc's "4th
  recurrence" claim directly via SSM on both real instances rather than trusting the doc's prior framing. Found the "0
  loaded units anywhere" evidence was gathered against `i-0c9b283b31d6b5ca7` — the OLD orchestrator VM, which is
  SUPPOSED to be runner-free per the fleet-split plan — while the actual current runner VM (`i-042a6332509482556`) is
  healthy (17/17 units active, 0 failed). Added the correction todo above rather than editing the original entry
  (preserving the audit trail) plus a new P3 hardening todo to stop this recurring, since the "planning VM" naming
  ambiguity has now caused at least one real misdiagnosis. Did not change `status` — the doc's other open items (P2
  monitoring gap, P1 operator systemctl-start-or-reinstall action for the OLD claim, root-cause-of-original-stop) are
  unaffected by this correction and stay open.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — sole [OPERATOR] P1 item (4th recurrence, whole runner pool down)
  independently confirmed 6x since 2026-08-04 that AO-worker/main identities structurally lack the needed SSM reach;
  whole doc stays NA despite 2 more-bounded-looking sibling items.
- **2026-08-06 (interactive session, operator flagged a live CRITICAL alert: `github-glue-runner@glue-2.service`
  crash-looping on `i-042a6332509482556`, `NRestarts=968`)** — Diagnosed via read-only SSM before touching anything:
  `systemctl show` returned `Result=success`/`ExecMainStatus=0` and `journalctl` showed the unit's last exit was a clean
  `Runner listener exit with 0 return code, stop the service, no retry needed` immediately following a completed job —
  not a crash. Root-caused to a structural false-positive bug in `is_crash_looping()` affecting the entire `@glue-N`
  pool (full mechanism + fix in the new `[INFRA] P1` todo above), confirmed live a second way when `glue-3`/`glue-5`
  independently false-paged mid-session (journal 13:07:51Z) and self-"recovered" ~6 minutes later (13:13:11Z) purely
  from poll-timing luck — the exact noisy flap this fix eliminates structurally. Fixed `is_crash_looping()` to require
  `Result != success`, verified `shellcheck`-clean (exit 0) and `bash -n`-clean. While preparing to deploy, also found
  the live host's executed copy (`/usr/local/sbin/glue-runner-crash-loop-watchdog.sh`) had a DIFFERENT hash than both
  repo-tracked mirrors on the same host (`/opt/github-glue-runners/repo/`, `/opt/glue-deploy/unified-trading-pm/`) —
  missing the 2026-08-05 unit-enumeration fix, because no automated deploy path exists for this file (new `[INFRA] P3`
  todo above). Deployed the fully-current script to all three on-host locations via SSM (backed up the prior
  `/usr/local/sbin/` copy first), then manually triggered `glue-runner-crash-loop-watchdog.service`: clean
  `OK -- 0/17 glue-runner units crash-looping` reading, `alerted-units` state file empty afterward — confirmed fixed and
  verified live. Held the repo commit initially — host QG capacity was in a critical state at diagnosis time (load avg
  ~168 dropping to ~17 over ~10min, free RAM as low as ~60MB, swap ~91% used, 8-9 concurrent `quality-gates.sh --no-fix`
  runs from other slots observed throughout) and quickmerge's full QG has no skip path.
- **2026-08-06 (same session, operator asked to retry shipping)** — Rechecked host load: dropped to ~10 (1-min avg), 1
  other QG running, still tight on swap (~93% used) but no longer in the acute range from the earlier reading. Shipped
  `scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh` via quickmerge as `879e3e109` — landed on
  `live-defi-rollout` (quickmerge's SHA-sentinel skipped a redundant Pass-2 QG re-run since Pass 1 had already verified
  this exact tree, so the ship itself added no additional host load). Closed the `[INFRA] P1` todo above with the SHA.
  Not yet independently re-verified on `main` (drains via `ldr-to-main-promote.yml`, ~15-30min SLA) — the live fix on
  `i-042a6332509482556` predates and is independent of this commit landing anywhere.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — CORRECTED rationale (the prior
  2026-08-06 na-eligibility-audit marker cited the `[OPERATOR] P1` item as the sole reason to stay NA; that item is now
  RESOLVED/MOOT per this doc's own later entries, so that rationale is stale). Fresh read of the 3 remaining open items:
  the P2 monitoring-gap extension needs host-deploy access + judgment about alert conditions (same class of work the
  shipped `is_crash_looping()` fix required); the 2 P3 items (VM-naming disambiguation, automated watchdog-script sync)
  are lower-confidence AO-eligible candidates — flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` in this audit's report rather
  than reclassified here, given this doc's history of misdiagnosis from ambiguous instance naming.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged.

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- 458-line doc tracking a P1 fleet CI outage (2 then 3 stopped glue-runner systemd units blocking UAC->main + 11 dependent repos). Every P1 host-access, root-cause, writer-pool-fix, VM-naming-disambiguation, and deploy-sync-automation todo is resolved with SHA/verification evidence (last closed 2026-08-16). The sole open todo (line 147, INFRA P2) bundles a real watchdog-extension implementation task — extend/sibling-check `glue-runner-crash-loop-watchdog.sh` to catch cleanly-inactive AND...
- **context-scout 2026-08-20**: re-verified context_scope (4 entries), unchanged.

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — erring toward caution per this pass's own
ambiguity rule. Sole open todo (line ~147, `[INFRA] P2`, close the monitoring gap) bundles 2 distinct
watchdog-extension asks: (a) alert when a `github-glue-runner-<repo>@glue-1.service` sits cleanly `inactive`/`dead`/
`failed` for >N minutes while peers are active, (b) alert on a runner whose `journalctl` shows "Running job" with no
matching "completed" line for >N minutes. Both are plausibly implementable (the doc even names the target script
and host), but neither states N, and this exact doc's own history includes a real prior misdiagnosis from ambiguous
VM naming — the 2026-08-07 and 2026-08-18 audits both tagged this `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` rather than
extract it, and re-reading it fresh this pass I did not find a stronger basis to override that judgment than they
had. Not extracting this round either — flagging the ambiguity again rather than force a RECLASSIFY, consistent
with "when genuinely unsure, err toward KEEP-NA." No `assigned_vm` change.
