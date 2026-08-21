---
doc_type: issue
title:
  sports catalogue re-roll (--since 2019-01-01) is an 840K-blob multi-hour corpus walk, not a single-command job —
  killed after ~26min direct on shared host
summary: >-
  /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md's "re-roll build_instrument_catalogue.py
  --asset-group sports --since 2019-01-01" todo was classified as a single-command, deterministic-outcome item.
  Smoke-tested it (confirmed auth/merge/monotonic-guard all work), then launched the real full run: it discovered
  840,035 by_date parquets to roll up — a genuinely corpus-scale, multi-hour GCS walk — and was killed by the harness
  ~26 min in with no OOM evidence and no sign the memory-cap wrapper fired. Recommends dispatching as a dedicated
  one-off VM job (infra craft) instead of direct-host execution.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [sports, instruments-service, catalogue, vm-launcher, corpus-scale]
related:
  [
    /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-15
author: claude-code (slot-18, backend_engineer, AO-dispatched)
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: >-
  Investigated while executing /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md's
  build_instrument_catalogue.py re-roll todo.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    instruments-service/scripts/build_instrument_catalogue.py,
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
  ]
drift_direction: advance-code
depends_on: []
---

# sports catalogue re-roll — corpus-scale finding

## What I found

`/plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md`'s todo "Re-roll
`build_instrument_catalogue.py --asset-group sports --since 2019-01-01` to pick up the +26,894 round rows" was
classified by the 2026-08-13 conflict-check as "a real, single-command, deterministic-outcome item" —
bounded/deterministic enough for direct backend_engineer dispatch.

Smoke-tested the exact command first (`--max-blobs 20`, which the script forces into `--dry-run`): confirmed GCS auth,
bucket resolution (`instruments-store-sports-prd-central-element-323112`, env=prod), the frozen-tail merge, and the
monotonic guard all function correctly — the truncated 20-blob sample correctly triggered `CATALOGUE_SHRINK_BLOCKED`
(new=534021 < current=534023) exactly as the diagnostic guard is designed to do for a truncated walk. No prod write
occurred (dry-run only).

Then launched the REAL full run (`--asset-group sports --since 2019-01-01`, no `--max-blobs`), wrapped in
`scripts/dev/run-bounded-analysis.sh --mem-cap 8G` (systemd-run unavailable on this host — fell back to the RSS-poll
cap), backgrounded via the harness per `async-wait-and-poll-discipline.md`. The command's own `--since` help text
already frames this as "the deliberate ONE-OFF full-history backfill... the (multi-hour) full walk is paid once" — but
the actual discovered scope is bigger than that framing suggested: the walk found **840,035** sports
fixture/team/player-source `by_date` parquets to roll up (16 download workers), logged at 23:50:57 UTC, roughly 3m15s
after the bucket resolve. No further log line was written after that point, and the background task was killed by the
harness (~26 minutes elapsed from launch, status=`killed`, "was stopped", no exit code reported).

Root-caused as far as possible: **not my own memory wrapper** — its kill message
(`🛑 [run-bounded-analysis] RSS ...K exceeded cap ...K — killing process group ...`) never appears in the log. **Not a
kernel OOM-kill either** — checked `dmesg -T` and `journalctl -k` for the exact window (2026-08-14 23:45–2026-08-15
00:20 UTC): no OOM-killer entries. Host memory/swap at the time I checked (00:16:58) was unremarkable (23Gi available,
5.0Gi swap used — not clearly abnormal for a 5-day-uptime shared host running many concurrent agent slots). The kill
mechanism itself is unconfirmed, but the population it was killed mid-walk on — an 840,035-object GCS listing+download —
is squarely the "genuinely corpus-scale" class `RULES.md` §1 says must be dispatched to a dedicated VM rather than run
directly on the shared `planning` host, precisely because a long, heavy, direct-host job is exactly the shape of the
three confirmed prior AO-outage incidents that rule exists to prevent (even though this job's own accumulator-dict
streaming design is memory-conscious, its multi-hour direct-host wall-clock footprint is itself the risk this class of
rule targets).

## Why it matters

The plan's conflict-check bounded/deterministic classification was correct about the COMMAND (it is exactly one command,
with a fully deterministic intended outcome) but not about the RUNTIME PROFILE: an 840K-object multi-hour walk does not
fit inside one backend_engineer worker session, and repeatedly relaunching it inline on the shared host either repeats
whatever killed this run or risks the exact resource-contention class the heavy-compute-on-shared-host rule exists to
prevent. Continuing to retry this todo as scoped (a bare backend_engineer CLI invocation) is not the right next step.

## Recommended decision

Dispatch as a dedicated one-off VM job per `/codex/05-infrastructure/vm-launcher-runbook.md` (SPOT default, in-region)
rather than direct-host — VM launches are `infra` craft, outside `backend_engineer`'s scope
(`agents/backend_engineer.md`'s `does_not: Infra provisioning, VM launches`), so this is escalated rather than absorbed
here.

## Follow-up todos

- [ ] [INFRA] P2. Launch a dedicated one-off VM (per `vm-launcher-runbook.md`, SPOT default, in-region) to run
      `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` (instruments-service) to completion.
      Verify on completion: (a) the run reaches `CATALOGUE_ROLLUP` success (not `CATALOGUE_SHRINK_BLOCKED`) and promotes
      `catalog.parquet`, (b) the new row count is `>=` the current 534,023-row baseline plus roughly the expected
      +26,894 net new rows (exact delta may differ from the plan's original estimate since that estimate predates this
      session's live numbers — treat 534,023 as the current authoritative baseline, not the plan's original figure).
      repo: instruments-service. **Already tracked as `sports_satellite_ao_dispatch_batch14_2026_08_16.md` todo 2**
      (`assigned_vm: planning`, status: draft — not yet dispatched), which merges this exact VM-launch action with the
      identical citation from `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`'s Track V item.
      Do NOT dispatch a second, competing todo for this — checkbox here flips once batch14's todo 2 lands.
- [ ] [DIAG] P3. If the VM-launched run is ALSO killed/interrupted before completion, capture `dmesg` + peak RSS + full
      stdout/stderr AT the moment of the kill (not after) so the root cause (protective host action vs. a genuine bug in
      the roll-up itself) is actually confirmed before a third attempt. **Also covered by batch14 todo 2** ("capture
      dmesg/RSS diagnostics if it is killed again") — same source, same status.

## Progress Log

- **context-scout 2026-08-15**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-17**: KEEP-NA-STALE (already-duplicated) — both open todos here are the SAME action
  `sports_satellite_ao_dispatch_batch14_2026_08_16.md` todo 2 already merges (verified: that batch's own
  "Conflict-check findings" section explicitly names this doc + explains the merge). REVISES an earlier same-run
  classification of this doc as an independent RECLASSIFY candidate — the conflict-check caught that batch14 (drafted
  one day prior) already claims this exact ground; dispatching a second copy would race the same VM launcher.
  Citation-only fix, not a reclassification. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-17**: refreshed context_scope (5 entries).
