---
doc_type: issue
title:
  MTDS live-mode capture (native connectors + tardis-machine sidecar) never opens the authenticated
  `datasets.tardis.dev` connection — the premise behind wiring the Tardis N=1 concurrency guard into
  `launch-mtds-live.sh`/siblings does not hold
summary:
  Code-trace evidence (both `market-tick-data-service`'s live capture path and `tardis-concurrency-guard.sh`'s own
  embedded documentation) shows MTDS's live WS producer never contends for the shared single-IP authenticated Tardis key
  that the concurrency guard exists to protect — contradicting the premise of
  `mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` and this batch's
  `cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1 (P1), which both infer contention from the BATCH-mode
  `VENUE_TO_ADAPTER_KEY == 'tardis'` classification without checking that the LIVE path is structurally different.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tardis, concurrency-guard, mtds, live-leg, false-premise, ssot-contradiction]
related:
  [
    /plans/archive/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-02
author: unknown
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
resolved_by:
locked_by:
source: cefi_satellite_ao_dispatch_batch5_2026_08_02.md (todo 1, [INFRA] P1)
drift_direction: advance-code
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/launch-mtds-live.sh,
    market-tick-data-service/market_tick_data_service/live/connectors/tardis_machine_ws.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
  ]
---

## What I found

Working `cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1 ("Wire the Tardis N=1 concurrency guard into
`launch-mtds-live.sh` and every sibling live launcher"), I traced whether MTDS's LIVE capture path actually opens the
authenticated `datasets.tardis.dev` connection the guard protects (single shared IP, cap=1, per
`tardis-concurrency-guard.sh`). It does not, for either of `launch-mtds-live.sh`'s two `--live-source` modes:

1. **`--live-source native` (the default).** The per-venue native WS connectors (e.g.
   `market_tick_data_service/live/connectors/binance_spot_ws.py`, `binance_futures_ws.py`, `bybit_ws.py`,
   `kraken_futures_ws.py`, `deribit_ws.py`) connect directly to each exchange's own WebSocket API. A few of them import
   `market_interface.adapters.cefi.tardis_margin_marker` / `tardis_shared` — but those two modules are **pure
   string/symbol-parsing utilities** (settlement-dimension parsing, margin-marker canonicalisation, canonical
   partition-path helpers) with **zero network I/O, no `aiohttp`/`requests` usage, no API key** — confirmed by grep
   (`grep -n "aiohttp\|requests\.\|api_key\|datasets.tardis" tardis_margin_marker.py tardis_shared.py` → no matches).
   They're shared code-reuse for symbol normalisation between the batch Tardis adapters and the live connectors, not a
   live network call to Tardis.
2. **`--live-source tardis-machine`.** `market_tick_data_service/live/connectors/tardis_machine_ws.py`'s own docstring
   states it implements against the **`stream-normalized`** endpoint of a local tardis-machine sidecar, explicitly
   contrasted with the **billed, authenticated** `replay-normalized` endpoint: _"`stream-normalized` is the real-time /
   FREE endpoint (no API key, unlike the billed historical `replay-normalized`)"_. MTDS's connector only ever calls
   `stream-normalized`.

Both are corroborated by `tardis-concurrency-guard.sh` itself (the file this batch's todo sources), in its own
"Self-declaring metadata model" comment block: _"a name-regex can never stay in sync with every Tardis-consuming
launcher... it can ALSO wrongly catch VMs that do NOT hold the licensed slot (live MTDS tardis-machine is an
unauthenticated local sidecar; IS Tardis hits public api.tardis.dev metadata; neither contends)."_ The guard's own
author already reasoned about this exact launcher family and reached the same conclusion.

I additionally traced `market_tick_data_service/live/backfill_runner.py` (the only other `market_interface`-importing
module under `live/`) — it's an unwired scaffold (`Status: scaffold + framework shipped`, zero callers anywhere in the
codebase) for a generic REST gap-backfill Protocol, not Tardis-specific and not currently reachable from any launch
path.

`TardisAdapter` / `datasets.tardis.dev` calls only occur in `market_interface/clients/tardis_stream_client.py` and
`adapters/umi_tick_provider.py` — both exclusively reached from the **batch** backfill/forward-poll CLI paths, never
from `cli/handlers/websocket_streaming_handler.py` (the live-mode entry point `launch-mtds-live.sh`'s VM invokes).

**The `TARDIS_CONCURRENCY_LEASE` metadata passthrough already present in `launch-mtds-live.sh` (lines ~214-219) is a red
herring, not counter-evidence**: `setup-data-pipeline-vm.sh` exports it unconditionally near the top of the script
(before any `VM_TASK` dispatch), and it is only actually consumed by `tardis_concurrency_lease.py`, which the live WS
code path never calls. It reads like boilerplate copied from `launch-cefi-sharded-backfill.sh` rather than something
that does anything for a `VM_TASK=mtds-live` run.

**Only 2 of the 8 `launch-*live*.sh` scripts even create CeFi WS-capture VMs at all** (`launch-mtds-live.sh`,
`launch-mtds-live-cefi-consolidated.sh` — the latter hardcodes a fixed shard bundle that includes Tardis-adapter venues
BINANCE-FUTURES/BYBIT-FUTURES/KRAKEN-FUTURES/OKX-FUTURES/DERIBIT alongside cap-exempt HYPERLIQUID/ASTER). The other 6
are structurally out of scope for this finding (and for the guard) regardless of the question below:
`launch-mtds-live-prediction-consolidated.sh` (POLYMARKET/KALSHI, prediction asset_group — Tardis only covers cefi per
UAC `VENUE_TO_ADAPTER_KEY`), `launch-mdps-features-live.sh` (MDPS+features, consumes already-published candle events, no
market-data ingestion), `launch-perp-clob-live.sh` (KALSHI-PERP/POLYMARKET-PERP, public-read WS, non-Tardis venues),
`launch-prediction-live.sh` (POLYMARKET|KALSHI, prediction asset_group), `launch-strategy-live-vm.sh`
(strategy/execution engine, no ingestion), `launch-batch-live-recon-cron-vm.sh` (reconciliation report generator, no
ingestion). None of these 6 mention "tardis" anywhere in their source (`grep -in tardis` on all 8 confirms).

## Why it matters

`cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1 (P1, dispatched to me, `assigned_vm: planning`,
operator-authorized) and its source `mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` both instruct wiring
`tardis_concurrency_guard` (pre-flight refusal) + `tardis_guard_reserve_slot` (hard gate immediately before VM create)
into `launch-mtds-live.sh` and its siblings, gated on `tardis_venue_list_needs_guard "<venue>"` — i.e., treating any
non-cap-exempt venue (BINANCE-FUTURES, BYBIT-FUTURES, KRAKEN-FUTURES, OKX-FUTURES, DERIBIT, etc.) as needing the guard
for a LIVE launch, exactly as it's needed for a BATCH launch.

If that premise is wrong (live capture structurally never touches the authenticated single-IP key), wiring the guard as
instructed would not close any real contention gap. Worse, it would **actively harm the live pipeline**:
`launch-mtds-live.sh`'s own docs describe its VMs as 24/7 continuous producers
(`Cost: e2-standard-8 ~24/7 — live producer`). Cap=1 is deliberately very tight — a real cefi Tardis backfill/sharded-VM
campaign is a common, expected, legitimately-concurrent state (multiple batch campaigns have run in this corpus recently
per the plan's own `cefi_satellite_ao_dispatch_batch4/5` history). Gating a live-producer launch/restart on that cap
would REFUSE a legitimate live launch for a venue that was never actually going to contend, at exactly the moment a live
producer needs to (re)start — a false-positive block of critical live infrastructure for zero actual protection. This is
precisely the failure mode `tardis-concurrency-guard.sh`'s own header already warns against and was already fixed once
for the BATCH side (`mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`,
`TARDIS_CAP_EXEMPT_VENUES` / `tardis_venue_list_needs_guard`) — but that fix scopes exemption by VENUE, not by
LIVE-vs-BATCH MODE, so it does not (and structurally cannot, from inside a venue-keyed exemption list) protect live
launches of non-exempt venues from an unnecessary refusal.

This is a genuine judgment call, not a mechanical implementation detail — it contradicts the stated premise of an
already-`assigned_vm: planning`, operator-authorized plan, so I'm not overriding it unilaterally.

## Recommended decision

**Option A (recommended): do NOT gate live-launcher VM creation behind `tardis_concurrency_guard`/
`tardis_guard_reserve_slot`.** Correct the source issue doc's finding (close its P1/P2 as "verified not-a-bug — live
mode never touches the authenticated endpoint, see this doc") and this batch's todo 1 similarly. Optionally still add a
passive `VM_TARDIS_CONSUMER` label or code comment for future auditors, but not a hard refusal gate, since a refusal
protects against contention that cannot occur via this launch path.

**Option B: wire the guard anyway**, per the plan's literal instruction, as defense-in-depth against a hypothetical
future venue/connector change that _does_ route through the paid endpoint. Cost: a live-producer (re)launch can be
refused by an unrelated, legitimately-concurrent batch campaign with zero corresponding benefit today.

I recommend **A** — the evidence that live mode never touches the guarded resource is strong and multiply corroborated
(the connector code, the docstrings, and the guard's own embedded reasoning), and gating a 24/7 live producer on a cap
that cannot actually be threatened is a correctness/availability regression, not a safety improvement.

## Resolution (2026-08-02, operator ruling on BLK-5aa3ce78)

**Option A adopted.** Do NOT gate live-launcher VM creation behind `tardis_concurrency_guard`/
`tardis_guard_reserve_slot`. Operator's stated reasoning: a hard-refusal gate (cap=1) on a 24/7 live producer closes no
real gap (this doc's evidence stands) AND introduces a new failure mode — refusing a legitimate live-producer relaunch
whenever an unrelated cefi backfill runs concurrently, i.e. live data loss, which is exactly what CLAUDE.md's
live/forward-VM on-demand rule protects against. Defense-in-depth that can take down a live producer is a new outage
class, not a protection.

Both `mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` (P1 + P2) and
`cefi_satellite_ao_dispatch_batch5_2026_08_02.md` (todo 1) have been flipped closed, citing this doc, in the same commit
as this update.

**Follow-up (filed as its own todo below, per operator instruction — NOT folded into the close above):**

- [ ] [OBSERVABILITY] P3. IF a future MTDS live connector change ever routes live capture through the authenticated
      `datasets.tardis.dev` endpoint (i.e. `TardisAdapter`/`tardis_stream_client.py` becomes reachable from
      `cli/handlers/websocket_streaming_handler.py` or any `live/connectors/*.py`, not just the current pure
      symbol-utility imports), add a NON-REFUSING, log-only observability check to the affected live launcher(s)
      (`deployment-service/scripts/vm/launch-mtds-live.sh` and/or `launch-mtds-live-cefi-consolidated.sh`) that flags
      co-occurrence with a running Tardis batch/backfill VM — informational only, never a hard
      `tardis_concurrency_guard`/`tardis_guard_reserve_slot` refusal gate on a live producer. This todo has no current
      trigger condition (the premise it guards against does not exist today) — it is a standing tripwire for future
      connector changes, not presently actionable. Repos: deployment-service, market-tick-data-service.

## Progress Log

- **2026-08-02, slot 15 (infra craft, `cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1):** Filed this finding
  before implementing todo 1 as literally written. Posted a `/blocked` question citing this doc to get a ruling before
  wiring (or not wiring) the guard into `launch-mtds-live.sh` / `launch-mtds-live-cefi-consolidated.sh`. Continuing
  meanwhile with the non-controversial half of the todo: triaging the other 6 sibling launchers (all confirmed
  structurally Tardis-exempt, see "What I found" above).
- **2026-08-02, slot 15:** Operator answered BLK-5aa3ce78 with Option A. Flipped both the source issue doc's P1/P2 and
  this batch's todo 1 closed as not-a-bug, citing this doc. Added the follow-up observability todo above per the
  operator's explicit instruction to file it as its own separate, trackable item rather than folding it into the close.
  This doc stays `status: open` (one todo remains open, contingent on a future connector change) — no archival due yet.
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid (first pass, no prior marker) — the
  sole remaining open item is an explicitly non-actionable standing tripwire for a hypothetical future connector change,
  not currently dispatchable work.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-04 verdict; the
  doc's main question was resolved via an explicit 2026-08-02 operator ruling (`BLK-5aa3ce78`), the sole remaining item
  is a self-described non-actionable standing tripwire for a future connector change, kept open (not archived) per the
  doc's own Progress Log.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: KEEP-NA, valid — re-checked against the
  full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none apply. The sole open item has "no current trigger condition" by its own explicit wording (a standing tripwire for
  a future connector change that does not exist today) — not worker-determinable. No reclassification.
- **ag-closeout-audit 2026-08-13**: a same-session ag-closeout-audit classifier flagged this doc archivable_now —
  independently re-verified WRONG and overturned before any archival action. The sole open item is a genuine dormant
  conditional tripwire ("IF a future connector change ever routes live capture through the authenticated endpoint"), not
  zero remaining work. Stays open, untouched. Do not re-flag as archivable on this same reasoning.
