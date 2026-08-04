---
doc_type: issue
title:
  "Two self-hosted glue-runner systemd units left INACTIVE on the planning VM stall UAC LDR->main promotion and cascade
  a Tier-A CI outage across 11 dependent repos (instruments-service main QG-v2 RED is a symptom, not a code bug)"
summary: >-
  Slot 11 (agt-152447, BLK-37a5da89, 2026-08-04) fully root-caused instruments-service's main quality-gates-v2 RED as a
  cascading INFRA outage, not a code defect: instruments-service code+tests are GREEN on LDR. Chain: (1) two dedicated
  self-hosted GitHub-Actions glue-runner units are stopped/inactive on the planning VM (ip-172-31-5-118) —
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
  (`ikenna-worker` lacks `ssm:DescribeInstanceInformation`). Needs someone with host root on the planning VM (or SSM) to
  `systemctl start` the two units. Secondary finding: the glue-runner-crash-loop-watchdog does NOT catch this class — it
  only flags units actively crash-looping (repeated restarts), not a unit sitting cleanly `inactive`/stopped.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts, instruments-service]
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

## Why neither worker nor main can self-serve

`sudo` is blocked by a `no-new-privileges` flag for BOTH the worker session and main agt-1756f6 (verified `sudo -n true`
=> "no new privileges" error). Neither has AWS SSM (`ikenna-worker` lacks `ssm:DescribeInstanceInformation`). Restarting
a systemd unit needs host root / SSM on the planning VM — genuinely operator-gated.

## Todos

- [ ] [OPERATOR] P1. **Immediate host action (unblocks 11 repos).** On the planning VM (ip-172-31-5-118), with root:
      `sudo systemctl start github-glue-runner-unified-api-contracts@glue-1.service` and
      `sudo systemctl start github-glue-runner-instruments-service@glue-1.service`; confirm both go `active (running)`
      (`systemctl is-active …`). Then re-verify UAC LDR run 30894307404 (and instruments-service 30894282946) leave
      QUEUED and go green, and the `ldr-to-main-promote-fleet` job picks UAC up on its next ~5-15min tick, draining the
      Tier-A gate for the 11 dependent repos. If the instruments-service unit was stopped deliberately (external
      `systemctl stop` 09:01:57), confirm no in-flight maintenance conflicts before starting. (planning VM — operator
      host action)
- [ ] [INFRA] P2. **Close the monitoring gap.** The glue-runner-crash-loop-watchdog only flags units actively
      crash-looping (repeated restarts), so a runner sitting cleanly `inactive`/stopped (Restart=always suppressed by an
      explicit stop) evades detection — exactly this incident. Extend the watchdog (or add a sibling check) to alert
      when any expected `github-glue-runner-<repo>@glue-1.service` is `inactive`/`dead`/`failed` for > N minutes while
      peer runners are active, so a stopped runner pages instead of silently stalling promotion for an hour. Repo:
      agent-orchestrator (deployment/monitoring). Cross-ref `/codex/05-infrastructure/deployment-observability.md`,
      `/codex/04-architecture/ci-alerting.md`.

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
