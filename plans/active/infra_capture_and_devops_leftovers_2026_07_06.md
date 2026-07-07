---
doc_type: plan
title: Infra capture wiring + devops leftovers (Stage 5 infra) — AO Plan 6
summary:
  The infra-role slice of the instruments-completion capture work — the VM launches, connector registrations, and live
  runners that are not data_engineering tasks, plus the credential/operator-gated capture items that stay visible but
  cannot auto-dispatch. Wires the ASTER live connector (moved out of Plan 1 for role-homogeneity — it gates Plan 1's
  ASTER re-measure), stands up the Deribit options_chain live runner (the handler is live/replay only), and parks the
  paid-RPC / quota / classification items as BLOCKED-CREDENTIALS or BLOCKED-OPERATOR. Source detail lives in
  data_completion_to_100_all_ag + cefi_hl_aster_batch_data_gaps.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [infra, capture, live-connector, vm-launch, credentials-gated, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    data_completion_to_100_all_ag_2026_06_21.md,
    issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    ../../codex/05-infrastructure/spot-vms-for-backfill.md,
    ../../codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Infra capture wiring + devops leftovers (Stage 5 infra) — AO Plan 6

> **🤖 AO PLAN 6 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** _(Re-homed 2026-07-07
> from role `infra` → `data_engineering`: the fleet has no infra-craft worker, so these tasks parked as craft-mismatch
> ~6×; data_engineering agents have the VM-launch tools and execute them under the no-fire-and-forget guards below.)_
> Coordinator = `instruments_completion_tracker_2026_07_06.md` (Stage 5, infra slice).
>
> **Worker guards (HARD):** (1) **No fire-and-forget** on ANY VM/connector launch — STARTED <60s, ≥1 progress/hr, verify
> T+10-15min with a **data-quality spot-check** (per-VM shard parquet captured/empty ratio — events alone hide
> silent-zero bugs), arm your own `run_in_background` watchdog. (2) **live/forward VMs stay on-demand** (preemption
> loses live data) — SPOT is for backfill only. (3) launchers live in `deployment-service/scripts/vm/`; the VM name must
> be in `VM_PREFIX_TO_BUCKET` + `lifecycle_class`. (4) **credential/operator-gated items are BLOCKED-\*** — build the
> scaffold, do not descope; the credential ask is the operator's, not a reason to skip.

## Codex SSOTs (read before touching)

- `codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT default for backfill; live/forward stay on-demand.
- `codex/05-infrastructure/deployment-observability.md` — no fire-and-forget; STARTED/progress/STOPPED verification.
- `codex/02-data/external-data-always-available-rule.md` — exhausting the free path = a credential ask, NOT a descope.

## Capture wiring (dispatchable)

- [ ] [DATA] P1. **Register + launch the ASTER live connector** — `aster_book_liq_ws.py` into
      `live/connector_registry.py` + a live VM (the KALSHI-PERP book5 VM is the in-cefi template). **PREREQ: Plan 1's
      enumerator `start_date` support + the UAC capability flip for ASTER book5/liquidations have landed** (else you
      re-create the 17,282-row over-seed). Verify `live_aster` rows land (per-VM shard spot-check at T+10-15min). **This
      gates Plan 1's ASTER re-measure (2c/2f).** Connector SSOT: `issues/cefi_hl_aster_batch_data_gaps_2026_06_22` BUG
      #4. Gate: `live_aster` book5/liquidations rows landing daily.
- [ ] [DATA] P1. **Deribit `options_chain` live runner** — wire a live cron/VM to run
      `--operation deribit-options-chain` (the handler `mtds@9ecd1e29e` is **live/replay only — no backfill**,
      `process()` collects `date.today()`), so it captures BTC/ETH `options_chain` daily → then feeds Plan 4's
      re-measure. Historical options are NOT captured by this handler. Gate: Deribit `options_chain` rows land daily;
      the D5 captured=0 clears in the next measure.
- [ ] [DATA] P2. **Long-lived VM logs not backed up** — the live/long-lived VMs' `run.log` is lost on VM delete; wire a
      periodic log sync to GCS (`long_lived_vm_logs_not_backed_up`). Gate: long-lived VM logs persist to GCS.
      **BLOCKED-CRAFT-MISMATCH (2026-07-06)** — auto-dispatched to a data_engineering slot; work sits in
      `deployment-service/scripts/vm/*.sh` (VM launchers, setup-data-pipeline-vm.sh tee wiring, cron/systemd for
      long-lived VMs) which is infra scope. Awaiting redispatch to an infra-role worker. See progress log.
- [ ] [DATA] P1. **Test-fleet image builds from current code** — the base-image local-build strategy + GCP build per
      service (`test_fleet_image_builds_from_current_code`) so the fleet images track HEAD. Gate: images build from
      current code; canonical build invocation documented.

## Credential / operator-gated (visible, not auto-dispatched — scaffold + park)

- [ ] [DATA] P1. **BLOCKED-CREDENTIALS — defi oracle/pyth `collect-oracle-prices` launcher.** No launcher for the
      `collect-oracle-prices` data_type today. Build the launcher scaffold; the pyth Hermes endpoint may need a key →
      credential ask [ack-pending]. Gate: launcher scaffold exists; status BLOCKED-CREDENTIALS until the key lands.
- [ ] [DATA] P1. **BLOCKED-CREDENTIALS — gas-fees MANTLE paid RPC.** gas-fees on MANTLE needs a paid RPC endpoint key (→
      Secret Manager) [ack-pending]. Build the adapter scaffold anyway. Gate: adapter scaffold ready;
      BLOCKED-CREDENTIALS.
- [ ] [DATA] P2. **BLOCKED-CREDENTIALS — Live ODDS quota + cheap second source.** The live ODDS quota decision + a cheap
      second source [ack-pending]. Gate: quota decision documented; scaffold for the second source.
- [ ] [INFRA] P1. **BLOCKED-OPERATOR-DECISION — rate-limit probe VM.** Needs a disposable-IP VM (operator-gated). Gate:
      probe design ready; awaits the operator's disposable-IP sanction.
- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION — CLOB-on-chain asset_group classification** (Lighter / Pacifica /
      Extended): are these cefi or a distinct on-chain-CLOB group? Operator classification call. Gate: classification
      decided; the enumerator + data-status read it consistently.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) **RE-DISPATCHED TO WRONG CRAFT — 6TH OCCURRENCE TODAY**.
  Dispatcher routed the same infra-scope task to slot 12 (also `data_engineering`). Slot 12 escalated via /blocked
  (`BLK-e37d3486`), same PARK recommendation as the prior 5 identical rulings (slots 2 `BLK-a92f81ab`, 6 `BLK-fc827a35`,
  8 `BLK-ec05e5dd`, 3 `BLK-58cfb164`, 11 `BLK-f1d45b7a`). Pattern continues unchanged — 6 data_engineering slot boot
  windows wasted on the same infra-scope task in one day. Operator action still required: (a) manually route to an
  infra-capable slot OR (b) land the AO dispatcher-side `assigned_role` filter. Slot 12 idle after this note.
- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) **RE-DISPATCHED TO WRONG CRAFT — 5TH OCCURRENCE TODAY**.
  Dispatcher routed the same infra-scope task to slot 11 (also `data_engineering`). Slot 11 escalated via /blocked
  (`BLK-f1d45b7a`), same PARK recommendation as the prior 4 identical rulings (slots 2 `BLK-a92f81ab`, 6 `BLK-fc827a35`,
  8 `BLK-ec05e5dd`, 3 `BLK-58cfb164`). Pattern continues: the AO dispatcher will keep routing this infra-scope task to
  `data_engineering` slots until (a) an operator manually routes it to an infra-capable slot, or (b) the AO
  dispatcher-side `assigned_role` filter lands. Slot 11 idle after this note.
- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) **RE-DISPATCHED TO WRONG CRAFT — 4TH OCCURRENCE TODAY**.
  Dispatcher routed the same infra-scope task to slot 3 (also `data_engineering`). Slot 3 escalated via /blocked
  (`BLK-58cfb164`); consistent PARK recommendation per prior 3 rulings (slots 2 `BLK-a92f81ab`, 6 `BLK-fc827a35`, 8
  `BLK-ec05e5dd`). **Escalation level UPGRADED**: 4 data_engineering slot boot windows wasted on the same task in one
  day — operator action now required to (a) manually route to an infra-capable slot OR (b) land the AO dispatcher-side
  `assigned_role` filter. The dispatcher will continue bouncing this task to `data_engineering` slots until one of those
  happens. Slot 3 idle after this note.
- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) **RE-DISPATCHED TO WRONG CRAFT — 3RD OCCURRENCE TODAY**.
  Dispatcher routed the same infra-scope task to slot 8 (also `data_engineering`). Slot 8 escalated via /blocked
  (`BLK-ec05e5dd`); main answered PARK (3rd identical ruling — see slots 2 `BLK-a92f81ab`, 6 `BLK-fc827a35`). Systemic
  issue confirmed: this task will keep bouncing until either (a) an operator manually routes it to an infra-capable
  slot, or (b) the AO dispatcher gains an `assigned_role` filter. Operator escalation required — three data_engineering
  slot boot windows wasted in one day. Slot 8 idle after this note.
- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) **RE-DISPATCHED TO WRONG CRAFT AGAIN** — dispatcher routed
  the same infra-scope task to slot 6 (also `data_engineering`). Slot 6 escalated via /blocked (`BLK-fc827a35`, same
  reasoning as slot 2's `BLK-a92f81ab`); main answered PARK again — do NOT cross the craft boundary. Confirms the
  epic-level fix required: the AO dispatcher needs `assigned_role` filtering so infra tasks stop going to
  `data_engineering` workers. Operator action = either manually route this task to an infra-capable slot, or land the
  dispatcher-side role filter. Slot 6 idle after this note.
- **2026-07-06** — `long_lived_vm_logs_not_backed_up` (P2) marked **BLOCKED-CRAFT-MISMATCH**. Server dispatcher does not
  filter by `assigned_role`, so this infra-scope task auto-routed to a data_engineering slot (slot 2). Per worker
  boot-prompt STEP 0.5 (do not cross craft lines), slot 2 escalated via /blocked → main answered PARK; the task's
  checkbox now carries the BLOCKED-CRAFT-MISMATCH marker so an infra-role redispatch (via
  `/api/slots/<N>/skip-current-task` or affinity re-routing) can pick it up cleanly. Finding logged as an operating
  observation — cross-craft dispatch is a recurring class; the dispatcher-side filter is a separate epic-level fix.
- **2026-07-06** — Plan authored + dispatched to AO (Plan 6 of the instruments-completion set). Infra-role slice of
  Stage-5 capture: ASTER connector (moved from Plan 1, gates its ASTER re-measure), Deribit options live runner, + the
  credential/operator-gated capture items parked as BLOCKED-\* (scaffold, don't descope).
