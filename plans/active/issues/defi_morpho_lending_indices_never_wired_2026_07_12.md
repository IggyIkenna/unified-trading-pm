---
doc_type: issue
title:
  MORPHO lending_indices — adapter exists (519 lines, dead code) but never wired into the collection handler; 0%
  captured
summary:
  MORPHO lending_indices sits at 0% coverage (0 captured, all expected_unattempted/empty_confirmed) despite being a
  confirmed MVP-in-scope venue (465 catalog instruments). Root cause is lending_indices_handler.py's _DEFAULT_PROTOCOLS
  never including "morpho", with no launcher override, even though a complete, unused MorphoAdapter
  (download_market_data()) already exists in the codebase. Blocks the mvp_backfill_defi_onchain_v10 G2 gate.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, lending_indices, morpho, coverage-gap, dead-code, mvp-backfill]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    plans/active/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md,
  ]
created: 2026-07-12
parent_epic: defi_master
assigned_vm: planning
resolved_by:
source: [mvp_backfill_defi_onchain_v10_2026_06_27.md G2 verification run, slot-3 data_engineering]
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

Found while re-running the G2 final-verification gate for `mvp_backfill_defi_onchain_v10_2026_06_27.md`. The
availability manifest shows MORPHO `lending_indices` at **0% coverage** — 564,126 total cells, all
`expected_unattempted` (416,522) or `empty_confirmed` (145,410), **zero `captured`, zero `attempted_failed`** (direct
parquet query against `_index/availability_index.parquet`, `venue LIKE 'MORPHO%'` `AND data_type=lending_indices`).
Confirmed genuinely zero — no manifest-recording gap: a `google.cloud.storage.list_blobs` glob search
(`raw_tick_data/by_date/**venue=MORPHO**data_type=lending_indices**`) across the whole bucket returns **0 files**.

A prior Progress Log entry (this same plan, "G2 verification run #2", 2026-07-12 03:48 UTC) flagged this as "captured=0
despite [a related doc] reporting 465 real rows as of 2026-07-07 — loose thread, not yet root-caused." That "465 rows"
claim is from `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` — re-read closely, those 465 rows are
**instrument-catalog** definitions (`LENDING_MARKET` instrument records in instruments-service — i.e. MORPHO IS
correctly MVP-tagged reference data), not manifest capture rows. No contradiction; the two docs are talking about
different tables. The manifest reading (0% captured) is correct and is the real gap.

**Root cause**: `market_tick_data_service/cli/handlers/lending_indices_handler.py:171` —
`_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3", "kamino_lending", "solend", "marginfi"]` — MORPHO is not in
this list, and no launcher ever overrides it with `--lending-protocols` to include morpho (confirmed:
`deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh` has no `--lending-protocols` flag at all, so
every backfill run — including the completed G1 `mtds-lending-indices-*` VMs — only ever touched the 6 listed
protocols). Meanwhile a full, apparently-intended-for-this-purpose adapter already exists:
`market_tick_data_service/market_interface/adapters/defi/morpho_adapter.py` (519 lines, `MorphoAdapter` class,
`async def download_market_data(instrument, date, data_types) -> dict` at line 310 — docstring: "Download Morpho market
data for date; returns dict by data_type (lending_indices, utilization, flash_loan_availability)", built explicitly to
serve both instruments-service `fetch_markets()` discovery AND market-tick-data-service `download_market_data()`
history). Import search confirms it is **never called from any handler** —
`grep -rl morpho_adapter market_tick_data_service/` only matches the adapter's own file + `adapters/defi/__init__.py`'s
export line. This is the same dead-code-from-launch pattern as
`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` G1.6 (ORCA/RAYDIUM/KAMINO `dex_pool_state`): real,
apparently-finished adapter code that was simply never plugged into the dispatch path a real backfill VM invokes.

## Why it matters

Blocks the `mvp_backfill_defi_onchain_v10_2026_06_27.md` G2 gate
(`lending_indices attempted_failed=0 AND expected_unattempted=0`) — MORPHO alone accounts for ~562K of the outstanding
`expected_unattempted` cells for this data_type. MORPHO is confirmed MVP-in-scope (465 catalog instruments,
`is_mvp()`-eligible per the referenced instrument-split doc). Silent zero-coverage for an MVP-tagged venue is exactly
the class of gap the plan's "Definition of 100%" section calls out.

## Recommended decision

- [x] ✅ [CODE] P1. Wire `morpho_adapter.MorphoAdapter` into `lending_indices_handler.py`'s protocol dispatch — add
      `"morpho"` to `_DEFAULT_PROTOCOLS` (line 171) and add the branch that instantiates `MorphoAdapter` + calls
      `download_market_data()` per (instrument, date), following the existing `kamino_lending`/`solend`/`marginfi`
      Solana-protocol branch pattern at lines 406-410 as the template (Morpho is EVM/Ethereum-first per
      `chain: str = "ETHEREUM"` default, so it likely needs its own non-Solana branch, not that exact one — check how
      `aave_v3`/`spark`/`compound_v3` EVM protocols are dispatched instead). (repo: `market-tick-data-service`) —
      market-tick-data-service@4c340f93. Added a dedicated per-market `_collect_morpho_lending` collector (IS-seeded
      instruments-store-defi market list via `pool_address`, `MorphoAdapter.fetch_markets()` live-API fallback) since
      Morpho's per-market `marketHourlySnapshots` query doesn't fit the generic aave_v3/spark/compound_v3
      whole-deployment Messari-cascade in `_query_and_parse`; extracted into a new `lending_indices_morpho.py` stage
      module (same split pattern as `_subgraph`/`_rpc`/`_parsers`) to stay under the file/method-size ratchet.
      quality-gates.sh green (SHA sentinel verified for 4c340f93); quickmerge landed on live-defi-rollout.
- [x] ✅ [SCRIPT] P1. Once wired, launch a MORPHO-scoped lending_indices backfill (either a dedicated
      `--lending-protocols morpho` VM, analogous to the G1.6 ORCA/RAYDIUM/KAMINO dedicated-VM precedent, or fold into
      the next full lending-indices re-run once the handler fix ships). SPOT VM per the fleet default. (repo:
      `deployment-service`) — **Done 2026-07-12 (slot 7).** Shipped `deployment-service@93c0c07`: added
      `--lending-protocols` passthrough to `launch-mtds-lending-indices-backfill-vm.sh` (→ `VM_LENDING_PROTOCOLS`
      metadata → `--lending-protocols` CLI arg in `setup-data-pipeline-vm.sh`'s generic dispatch), analogous to
      `VM_SOLANA_PROTOCOLS`. Waited for `market-tick-data-service@4c340f93` (item above, slot 3) to land, then launched
      dedicated VM `mtds-lending-indices-20260712-104450` (zone `asia-northeast1-c`, SPOT, `--lending-protocols morpho`,
      window 2023-01-01→2026-07-12) via the Python `compute_v1` client — `gcloud` CLI is unavailable in this agent-slot
      sandbox (snap-confine/`cap_dac_override`, same failure as the G1.6 precedent), so the instance-create call was
      issued directly against the Compute API mirroring the launcher's `--dry-run` output. Verified post-launch:
      `status=RUNNING`, `machine_type=e2-standard-4`, `provisioning_model=SPOT`.
- [ ] [SCRIPT] P2. Re-run this plan's (`mvp_backfill_defi_onchain_v10_2026_06_27.md`) G2 gate for `lending_indices`
      after the backfill completes. (repo: `instruments-service`)
- [ ] [INFRA] P2. Close the VM-launch/GCS-publish race found 2026-07-12 (slot-12) — a VM can boot and pull
      `startup-script-url` from `gs://deployment-scripts-*/vm/setup-data-pipeline-vm.sh` _before_
      `create-code-tarballs.sh`'s `gsutil cp` has actually published a just-landed fix, silently running stale pre-fix
      logic despite correct instance metadata. Add a pre-launch check (poll the GCS object's `updated` timestamp for
      `>= commit push time`, or a launcher precondition) so a fix-then-immediately-launch turn can't race itself. (repo:
      `deployment-service`)

Not attempted inline in this dispatch — this is new capability wiring (verify the EVM dispatch integration point, not
just adding a protocol string to a list), consistent with how the G1.6 dex_pool_swaps Solana-indexer finding was scoped
as its own follow-up rather than done inline during a verification pass.

**UPDATE 2026-07-12 (slot-12 sonnet/medium) — the first backfill VM (`mtds-lending-indices-20260712-104450`) never
actually ran Morpho-scoped: a launch/publish race, found + fixed, VM stopped + relaunched correctly.** Dispatched to the
"re-run G2 gate" todo above; before checking the gate, verified the backfill VM was actually producing Morpho data (it
wasn't complete yet, but this check is cheap and the prior 2 items in this doc set the precedent of verifying rather
than trusting). Findings:

- VM instance metadata correctly carried `VM_LENDING_PROTOCOLS=morpho` (the launcher script wrote it correctly).
- BUT the VM's actual `run.log` showed the CLI invocation as
  `--operation collect-lending-indices --mode batch --asset-group DEFI --start-date 2023-01-01 --end-date 2026-07-12` —
  **no `--lending-protocols` flag at all**, and zero `morpho` mentions anywhere in 789 log lines; the day-by-day
  collection summary only listed the 6 pre-existing default protocols (`aave_v3`/`spark`/`compound_v3` × chains).
- Root cause: `gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh` (the `startup-script-url`
  every VM in this fleet pulls at boot) is a **separately-published GCS object**, not auto-synced on
  `deployment-service` commit — `create-code-tarballs.sh` has to run `gsutil cp` to push it. Commit `93c0c07` (the
  `VM_LENDING_PROTOCOLS` → `--lending-protocols` wiring) landed at **10:28:57Z**; the VM booted and pulled the startup
  script at **~10:46:58Z**; but the GCS object's `updated` timestamp was **10:49:22Z** — i.e. the VM launched and
  started running ~2.5 min _before_ the fixed script was actually published, so it silently executed the pre-fix script
  (which ignores `VM_LENDING_PROTOCOLS` entirely) despite the correct metadata being present. This is a **launch/publish
  race in the deploy pipeline itself**, not a bug in the fix's logic (confirmed correct by reading the now-live GCS
  object: it does contain both `VM_LENDING_PROTOCOLS` parsing and the `--lending-protocols` passthrough).
- Impact if unnoticed: the VM would have run ~3-6h (full default-protocol history per the launcher's own docstring
  estimate) writing duplicate data for protocols G1 already backfilled, producing **zero** Morpho rows, and this task's
  G2 re-run would have found the gate still red with no obvious explanation.
- **Fix applied**: stopped the misconfigured VM (`mtds-lending-indices-20260712-104450`, deleted via direct `compute_v1`
  — `gcloud` unavailable in this slot, same snap-confine issue as every prior session) and launched a replacement,
  `mtds-lending-indices-20260712-105600`, with identical metadata (now correctly picking up the live GCS script) — SPOT,
  `e2-standard-4`, same 2023-01-01→2026-07-12 window, `VM_LENDING_PROTOCOLS=morpho`. Verified `status=RUNNING`
  post-launch (STARTED <60s, per the no-fire-and-forget rule) and confirmed via a fresh `run.log` read that the new VM's
  collection summary now includes `morpho_ETHEREUM` alongside the default protocols (see Progress Log entry below for
  the exact readout).
- **New P2 todo** (not this dispatch's scope — a deploy-pipeline hardening item, not a data fix): the
  `create-code-tarballs.sh` GCS-publish step should complete (or be verified live) _before_ any VM launch that depends
  on the just-shipped fix, to close this race for future single-shot fix+launch turns. Filing as a plan todo rather than
  fixing inline (design decision — could be a pre-launch poll, a launcher precondition check, or a CI gate — out of
  scope for a data_engineering G2-gate task).
- G2 re-run itself still NOT done — the new VM needs to run to completion first (same as before, just now against the
  correctly-scoped run). Checkbox stays unflipped; `skip-current-task`'d rather than poll-wait on a multi-hour VM run.
