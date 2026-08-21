---
doc_type: plan
title: cefi-phase2-gap-audit
summary: Phase 2 (CeFi) gap audit + root-cause fix list before relaunching MTDS backfill VMs
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, deployment-ui, instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
type: mixed
epic: data-pipeline-completion
owner: Harsh
completion_gates: { code: C5, deployment: D2, business: B1 }
repo_gates:
  - { repo: market-tick-data-service, code: C0, deployment: D0, business: B0 }
  - { repo: unified-trading-library, code: C0, deployment: D0, business: B0 }
  - { repo: deployment-service, code: C0, deployment: D0, business: B0 }
depends_on: [instruments-and-market-tick-data-completion-2026-05-01]
isProject: false
---

## Deferred work — migrated to: `plans/active/cefi_consolidated_closeout_2026_07_18.md` — successor:

cefi_consolidated_closeout_2026_07_18 (also `plans/active/data_completion_cefi_2026_07_15.md` for the pure
backfill/manifest-completion slice). This is the 2026-05-01 root-cause gap audit for
`instruments_and_market_tick_data_completion_2026_05_01` (itself long since archived) — the 29 open items are CeFi
instruments-service reference-data + MTDS backfill root-cause fixes. Both named plans are the current living CeFi data
umbrella: `cefi_consolidated_closeout_2026_07_18` explicitly aggregates every open CeFi/CeFi-adjacent IS/MTDS plan/issue
into one ordered pass (mirroring the defi/tradfi siblings), and `data_completion_cefi_2026_07_15` is the CeFi
backfill/canonicalisation slice split out of the M-1 data-completion program. Given the depth of this 615-line audit
doc, individual item-level tracing back to specific current todos was NOT done — this is a domain-level successor
citation, not a line-by-line reconciliation; flag for a future pass if item-level fidelity is needed.

# CeFi Phase 2 — gap audit + root-cause fix list

This is the working doc for Phase 2 of the data-pipeline-completion epic
(`instruments_and_market_tick_data_completion_2026_05_01.md`). The parent plan says "relaunch
`launch-cefi-sharded-backfill.sh` for any year+venue+instrument shards still showing `attempted_failed`" — but a
state-of-the-world audit on 2026-05-01 shows that doing so naively will only recover ~37% of the gap. The other 63% need
code fixes first.

This plan captures the audit findings, the three root-cause clusters, and the work-order to unblock Phase 2.

## Audit snapshot (2026-05-01 ~14:45 UTC)

### Instruments-service CeFi side (reference data)

- Manifest: `gs://instruments-store-cefi-central-element-323112/_index/availability_index.parquet` (194 KiB, last
  written 2026-05-01 14:27 UTC).
- 21,952 rows; date range 2019-03-30 → 2026-04-14.
- Per-venue captured days **match UAC `venue_start_dates` exactly** — every venue is at its inception through
  2026-04-14. The "trailing 17 days" gap to today is intentional (operator said "we ran everything up to 2026-04-14, the
  last 15 days is throwaway").
- **Conclusion: instruments-service CeFi is essentially complete. No backfill work here.**

### MTDS CeFi side (raw market data) — the actual Phase 2 work

- Manifest: `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` (13.7 MiB, last
  written 2026-05-01 14:29 UTC).
- 1,040,592 rows; honest-coverage v5 (`captured` / `empty_confirmed` / `attempted_failed`).

| capture_status     |    Rows |        % |
| ------------------ | ------: | -------: |
| `empty_confirmed`  | 768,659 |    73.9% |
| `captured`         | 180,942 |    17.4% |
| `attempted_failed` |  90,991 | **8.7%** |

**Phase 2 target = drive the 90,991 `attempted_failed` rows to either `captured` or `empty_confirmed`.**

### Failure breakdown by venue × data_type (top clusters)

| Venue           | data_type          | Failed rows | Notes                |
| --------------- | ------------------ | ----------: | -------------------- |
| **DERIBIT**     | trades             |      17,240 | ~50% of all failures |
| **DERIBIT**     | book_snapshot_5    |      17,240 |                      |
| **DERIBIT**     | derivative_ticker  |      17,240 |                      |
| **DERIBIT**     | options_chain      |       3,448 | adapter bug (BUG-2)  |
| **DERIBIT**     | futures_chain      |       3,448 | adapter bug (BUG-2)  |
| **DERIBIT**     | liquidations       |       1,798 |                      |
| BINANCE-SPOT    | trades / book      |      14,909 |                      |
| BYBIT           | trades / book / dt |       7,880 |                      |
| BINANCE-FUTURES | trades / book / dt |       4,436 |                      |
| Others          | various            |     < 3,500 |                      |

DERIBIT is **66% of all CeFi failures (60,414 / 90,991)**.

### Failure breakdown by `error_reason` (root-cause clusters)

| Error reason                                                  |    Rows | Cluster |
| ------------------------------------------------------------- | ------: | :-----: |
| `Response payload is not completed`                           |  31,142 |    A    |
| `FUTURE row requires 'expiry_date'`                           |  27,032 |    B    |
| `OPTION row requires 'expiry_date', 'strike', 'option_right'` |  19,002 |    B    |
| `In CSV column #N` (parser failures, scattered N)             | ~10,000 |    C    |
| `HTTPSConnectionPool` / `Connection timeout`                  |  ~1,200 |    A    |
| `StreamingParquetWriter pre-write validation failed`          |     232 |    B    |
| `UNCLASSIFIED_VENUE_ERROR`                                    |     389 |    D    |

- **Cluster A (transient / retryable): ~33,500 rows (~37%)** — Tardis HTTP cut-off, network pool errors. Re-running on a
  fresh VM will likely recover most of these.
- **Cluster B (adapter / schema bugs): ~46,500 rows (~51%)** — DERIBIT chain endpoints are returning rows with
  `expiry_date=None` (and for options, `strike=None`, `option_right=None`). Schema validation rejects them at
  write-time. **Re-running won't fix these.**
- **Cluster C (Tardis CSV schema drift): ~10,000 rows (~11%)** — "In CSV column #N" parse errors at scattered column
  positions on specific dates. Tardis likely changed CSV layouts on some dates and the parser doesn't tolerate it.
- **Cluster D (unclassified errors): 389 rows (<1%)** — adapter swallowed an exception without classifying it through
  `classify_venue_error()`. Error-classification gap.

## Operational findings (separate from the gap)

### BUG-3 — Event-bucket GCS 429 crashes every CeFi VM in ~7 minutes

**Root cause located.**
[unified-trading-library/unified_trading_library/event_sink.py:81-103](unified-trading-library/unified_trading_library/event_sink.py#L81-L103)

`GcsEventSink.write_event()` does a full **read-modify-write of the entire `events.jsonl` GCS object on every event
emit**:

```python
def write_event(self, name, metadata):
    # ...build record string...
    path = f"events/{service}/{date}/{instance_id}/events.jsonl"
    existing = ""
    if client.blob_exists(self._bucket, path):       # 1 HEAD per event
        existing = client.download_bytes(self._bucket, path).decode()  # 1 GET per event
    client.upload_bytes(self._bucket, path, (existing + record + "\n").encode())  # 1 PUT (mutation) per event
```

The 2026-04-22 fix qualified the path with `instance_id` (per-VM), eliminating cross-VM contention. **It does NOT
address per-event mutations within a single VM.** GCS caps mutations at ~1/second per object; emitting >1 event/sec on a
single VM saturates the object and every excess event 429s.

CeFi VMs emit dense events: `ADAPTER_FETCH_FAILED` per shard, `MANIFEST_WRITE` per parquet, `DEPLOYMENT_PROGRESS` every
heartbeat tick. With 90k attempted_failed shards to retry, the first per-shard failure event burst exceeds 1/sec and
crashes the VM.

**Symptom on 2026-05-01:** all 20 CeFi VMs crashed 7-13 min after boot with:

```
TooManyRequests: 429 ... events/.../<vm-name>/events.jsonl exceeded the rate limit
for object mutation operations
```

**Proposed fix options:**

- (a) **In-memory buffer + periodic flush** — buffer events for N seconds (or M events), flush as one PUT. Single
  mutation/flush regardless of event rate. Loses on-the-fly visibility but trivially solves 429.
- (b) **Pubsub-only on VMs** — services already construct `PubSubEventSink` for live mode (heartbeat_cli.py:173). Switch
  CeFi backfill VMs to a Pubsub-only sink (no GCS file). GCS write happens server-side from a pubsub subscriber that
  batches. Cleaner separation, but moves the work to a new service.
- (c) **Per-event sharded path** — `events/.../{vm-name}/events-{HHMMSS}.jsonl`. One mutation per object always.
  Thousands of small files; harder to read, but trivially solves 429.

Option (a) is the cheapest fix. Option (b) is the right long-term answer.

### BUG-4 — Deployment lifecycle reports `exit_code=0` for failed workloads

**Root cause located.**
[deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh:121](deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh#L121)

The wrapper invokes the workload as:

```bash
( "$@" 2>&1; echo "[vm-exec] command exited rc=$?" ) >> "$LOCAL_LOG" &
CMD_PID=$!
# ...
wait "$CMD_PID"
RC=$?
```

The exit code of a subshell `( ... )` is the exit code of its **last command** — which is the `echo` (always rc=0), not
`"$@"`. So `wait "$CMD_PID"` always returns 0, the wrapper writes `0` to `EXIT_STATUS_FILE`, the daemon reads 0 via
`signals.read_exit_status()`, and emits `DEPLOYMENT_COMPLETED` with `exit_code=0` even when the workload returned 1.

The workload's real rc is captured INSIDE the subshell by `$?` (correctly logged as `rc=1`) but never escapes.

**Verified:** EXIT_STATUS file on `cefi-binance-futures-2020-heavy` contains literal `"0\n"` (hex `30 0a`), while
run.log shows `[vm-exec] command exited rc=1`.

**Proposed fix:** capture the real rc inside the subshell into a separate file, or restructure so the subshell's exit
code IS the workload's:

```bash
# Option A — write rc to a file inside the subshell
(
  "$@" 2>&1
  WORKLOAD_RC=$?
  echo "[vm-exec] command exited rc=$WORKLOAD_RC"
  echo "$WORKLOAD_RC" > "$WORKLOAD_RC_FILE"
  exit $WORKLOAD_RC
) >> "$LOCAL_LOG" &

# Option B — drop the trailing echo, log the rc after the wait
"$@" >> "$LOCAL_LOG" 2>&1 &
CMD_PID=$!
wait "$CMD_PID"
RC=$?
echo "[vm-exec] command exited rc=$RC" >> "$LOCAL_LOG"
```

Option B is cleaner. Side effect of BUG-4 fix: `VM_SHUTDOWN_ON_COMPLETION=true` will start firing for failures
(currently it only fires for fake-success), which is the correct behaviour but means failed VMs will self-delete, losing
post-mortem SSH. Add a knob (`VM_SHUTDOWN_ON_FAILURE=false`) if we want to preserve failed VMs for diagnosis.

## Three-cluster fix strategy

```
            ┌─────────────────────────────────────────────────────┐
            │  Phase 2.0 — operational unblockers (no backfill)   │
            │  - BUG-3: event-bucket 429 (UTL events flush)       │
            │  - BUG-4: lifecycle exit-code reporting             │
            │  - Clean up the 20 zombie cefi-* VMs                │
            └────────────────────┬────────────────────────────────┘
                                 │
        ┌────────────────────────┼─────────────────────────┐
        ▼                        ▼                         ▼
  Phase 2.A                Phase 2.B                  Phase 2.C
  Cluster A retry          Cluster B fixes            Cluster C parser
  (~33k rows, ~37%)        (~46k rows, ~51%)          (~10k rows, ~11%)
  - relaunch only          - DERIBIT adapter:         - Tardis CSV
    failed shards            populate expiry_date,      schema drift
  - rely on transient        strike, option_right       per-date
    error retry            - re-run failed shards     - investigate +
                                                        widen parser
        └────────────────────────┼─────────────────────────┘
                                 │
                                 ▼
                       Phase 2.D — verify
                       - phantom recon
                       - re-snapshot drilldown
                       - confirm <1% attempted_failed
```

## Todos

### Phase 2.0 — Operational unblockers (sequential, blocks all backfill)

- [ ] [HUMAN] P0. **Clean up 20 zombie `cefi-*` VMs** still showing RUNNING from the 2026-05-01 14:28 UTC launch.
      They've already crashed (rc=1 in run.log) but `VM_SHUTDOWN_ON_COMPLETION` self-delete didn't fire. Each is billing
      on `e2-standard-2`.
      `bash for vm in $(gcloud compute instances list --filter='status=RUNNING AND name~"^cefi-"' --format='value(name)'); do gcloud compute instances delete "$vm" --zone=asia-northeast1-c --quiet done `

- [ ] [AGENT] P0. **BUG-3 — Event-bucket GCS 429 fix.** UTL event flusher hammers
      `events/<service>/<date>/<vm-name>/events.jsonl` faster than GCS's per-object rate cap. Investigate
      `unified-trading-library/unified_trading_library/events/` for the flush cadence + retry behaviour; either: (a)
      batch flushes to ≤1/sec (with exponential backoff on 429), or (b) shard the destination object (e.g. one append
      per N events with a counter in the path). Validate by running one CeFi VM end-to-end without 429.

- [ ] [AGENT] P0. **BUG-4 — Lifecycle exit-code reporting.** `vm-exec-with-gcs-tee.sh` + `heartbeat_cli.py` report
      `exit_code=0` to the deployment registry while the workload returned `rc=1`. Locate the bug in
      `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` (rc capture between workload exit and daemon shutdown) or
      `deployment-service/deployment_service/vm/heartbeat_cli.py` (archive event builder). Verify by running one VM that
      intentionally exits rc=1 and confirming the registry shows `exit_code=1, status=failed`.

- [ ] [AGENT] P1. **Tarball refresh after BUG-3 + BUG-4 fixes land.** Run
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI` (covers UTL + deployment-service +
      MTDS). Bare invocation only re-tars CORE, so the asset-group flag is required.

### Phase 2.A — Retry transient (Cluster A, ~33k rows)

- [ ] [AGENT] P0. **Build a "retry only attempted_failed" mode for the launcher.** The existing
      `launch-cefi-sharded-backfill.sh` always launches the full grid (95+ VMs across all years × venues × heavy/light);
      orchestrator skip-existing only skips `captured` rows. We want to launch _only_ the venue×year shards that
      currently contain `attempted_failed` rows, to avoid relaunching e.g. a year that's 100% green. Read the manifest,
      group by (venue, year), launch one VM per group with start/end dates clipped to that year.

- [ ] [HUMAN] P0. After Phase 2.0 lands + the targeted launcher exists, kick off Phase 2.A retry run. Expected recovery:
      ~33k of 91k failures (Cluster A). Track a sample of 5 (venue, date, data_type) tuples that were `attempted_failed`
      and verify they flip to `captured` or `empty_confirmed` after the retry VM completes.

- [ ] [AGENT] P1. After Phase 2.A completes, re-snapshot the manifest and recompute cluster sizes. Expected: Cluster A
      drops to <5k transient residuals; Clusters B + C unchanged.

### Phase 2.B — DERIBIT chain adapter fixes (Cluster B, ~46k rows)

**Root cause partially located.**
[market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:255-339](market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py#L255-L339)

`derive_row_instrument_id()` already implements symbol-fallback parsing:

- Line 287: `parse_deribit_option_symbol(symbol)` for OPTION rows
- Line 317: `parse_deribit_future_symbol(symbol)` for FUTURE rows

The regex (lines 172-182) expects:

- Inverse: `BTC-29MAR24` / `BTC-29MAR24-50000-C`
- Linear: `BTC_USDC-29DEC25` / `BTC_USDC-29DEC25-100000-C`

So the failures (27,032 FUTURE + 19,002 OPTION = 46,034) fall into one of three buckets:

1. **Perpetuals routed through `futures_chain` endpoint** — `BTC-PERPETUAL` / `ETH-PERPETUAL` won't match
   `_DERIBIT_FUTURE_SYMBOL_RE`. Bundling logic at line 696
   (`shard_it = "futures_chain" if len(symbols) > 1 else "future"`) suggests perps could be present in the futures
   bundle. **Most likely root cause** given the launcher passes `BTC-PERPETUAL;ETH-PERPETUAL` for DERIBIT (per
   `launch-cefi-sharded-backfill.sh:84`).
2. **Tardis CSV column shape changed on certain dates** — Tardis sometimes carries `expiration` instead of
   `expiry_date`, code probes both at line 279 — but if the column is genuinely missing AND the symbol can't parse, we
   fail.
3. **Expired-contract symbols with weirder shapes** — pre-2020 Deribit symbols may have used different formats.

**Hypothesis #1 CONFIRMED via manifest sampling (2026-05-01).** Every single failing FUTURE/OPTION row has a perpetual
instrument_id:

| instrument_id      | FUTURE failures | OPTION failures |
| ------------------ | --------------: | --------------: |
| BTC-PERP           |           2,118 |           1,623 |
| ETH-PERP           |           2,118 |           1,623 |
| SOL-PERP           |           2,118 |           1,623 |
| BNB-PERP           |           2,118 |           1,623 |
| XRP-PERP           |           2,118 |           1,623 |
| ADA-PERP           |           2,118 |           1,623 |
| AVAX-PERP          |           2,118 |           1,623 |
| DOGE-PERP          |           2,118 |           1,623 |
| MATIC-PERP         |           2,118 |           1,623 |
| ARB-PERP           |           2,118 |           1,623 |
| BTC (chain bundle) |           1,412 |               0 |
| ETH (chain bundle) |           1,412 |               0 |
| (blank)            |             706 |               0 |

**Total perp-misroute rows: 43,712 (~95% of Cluster B).** The remaining ~2,300 BTC/ETH chain-bundle rows are legitimate
but failing for a different reason (likely Tardis returned 0 rows for those bundle days; should be `record_empty`, not
`record_failed`).

Two anomalies in the symbol set:

1. Launcher only lists `BTC;ETH;BTC-PERPETUAL;ETH-PERPETUAL` for DERIBIT
   ([launch-cefi-sharded-backfill.sh:84](deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh#L84)), yet
   failures cover **10 different perps** (SOL/BNB/XRP/ADA/AVAX/DOGE/MATIC/ARB never appear in the launcher). Something
   downstream is auto-expanding the symbol universe.
2. Canonical instrument_id is `BTC-PERP` (not `BTC-PERPETUAL`) — some normalize_utils layer transforms the input.

**Root cause:** perpetuals are being routed into `futures_chain` and `options_chain` data_types. Perps have no expiry,
no strike, no option_right — by definition they cannot be in a futures or options chain. Schema validation correctly
rejects them, but the orchestrator should never have emitted those shards in the first place.

**Action items:**

- [ ] [AGENT] P0. **Locate the symbol-expansion source.** Failing instrument_ids include 8 perps not in the launcher.
      Grep the orchestrator + instruments-service catalogue readers for where `BTC-PERP` / `ETH-PERP` / etc. enter the
      futures_chain / options_chain shard set for DERIBIT. Likely the instruments-service catalogue includes all top-N
      perps and the bundler doesn't filter by data_type compatibility.

- [ ] [AGENT] P0. **Add a write-time guard in the orchestrator** that refuses to emit
      `(data_type ∈ {futures_chain, options_chain}, instrument_id matching '-PERP$')` shards. This is a code-correctness
      invariant, not a CeFi-specific quirk. The orchestrator should `record_empty(reason="perp_not_in_chain_dtype")` for
      these so the manifest reflects "we correctly didn't try" rather than `attempted_failed`.

- [ ] [AGENT] P1. **Investigate the 2,300 BTC/ETH chain-bundle failures separately** — these look like genuine "Tardis
      returned 0 rows" days that should have been recorded as `empty_confirmed` via `record_empty(row_key=...)`, not
      `record_failed`. Check the adapter's empty-vs-error classification path.

- [ ] [AGENT] P2. **If you find symbol-shape edge cases** beyond perpetuals (the regex doesn't cover something Tardis
      emits), extend the regex. Schema validation stays — fix populates the field, doesn't relax validation.

**Recovery estimate after Phase 2.B fix:** Cluster B drops from 46,500 → ~2,300 (the chain-bundle empty-vs-failed
reclassification). That's 95% of Cluster B closed by a single orchestrator-level guard.

- [ ] [AGENT] P1. **Implement the fix(es).** Either: parse expiry/strike/option_right from the Tardis symbol (canonical
      source), or fall back to UAC instrument registry lookup if the symbol-parse fails. Add unit tests for the symbol
      shapes that currently fail. Schema enforcement at write-time stays — the fix populates the fields, doesn't relax
      validation.

- [ ] [AGENT] P1. **Investigate `StreamingParquetWriter pre-write validation failed` (232 rows).** Probably the same
      expiry/strike/option_right cause but caught at a different layer. Should disappear once BUG-1 is fixed; verify
      after.

- [ ] [HUMAN] P0. After fixes land + tarball refreshed, relaunch the DERIBIT-only shards that previously failed Cluster
      B. Expected recovery: ~46k rows.

### Phase 2.C — Tardis CSV parser tolerance (Cluster C, ~10k rows)

- [ ] [AGENT] P1. **Investigate "In CSV column #N" cluster.** Pick 5 representative failures — different N values (4, 7,
      10, 16, 22) — pull the failing date + venue + data_type, fetch the Tardis CSV directly, diff the column count vs
      what the adapter expects. Tardis schema-drift on specific dates is the hypothesis; confirm or refute.

- [ ] [AGENT] P2. **Implement parser tolerance.** Either: (a) version-detect the CSV schema per-date and route to
      per-version parsers, or (b) tolerate trailing extra columns with a warning. **Do NOT** silently drop rows — the
      playbook's "no fudging data quality" rule applies. If a date genuinely returns a schema we can't parse,
      `record_failed` with a more specific error_reason than "column #N".

- [ ] [HUMAN] P2. After Cluster C fix + tarball refresh, relaunch the failed shards. Expected recovery: ~10k rows.

### Phase 2.D — Adapter error-classification gap (Cluster D, ~400 rows)

- [ ] [AGENT] P2. **`UNCLASSIFIED_VENUE_ERROR` audit.** 389 rows hit the unclassified branch in
      `classify_venue_error()`. Sample 5, identify the actual exception types raised, add classifications. Workspace
      rule: every adapter MUST classify errors through `classify_venue_error()` and emit `ADAPTER_FETCH_FAILED`.

### Phase 2.E — Verification

- [ ] [AGENT] P0. **Phantom-row recon for CeFi.** Run
      `instruments-service/scripts/reconcile_phantom_manifest_rows.py --asset-group cefi --dry-run`. Should report zero
      phantoms (the manifest is honest-coverage v5 so this should already hold, but verify).

- [ ] [AGENT] P0. **Re-snapshot manifest and confirm `attempted_failed` < 1% of total** (i.e. <10,400 of ~1.04M). Phase
      2 success criterion.

- [ ] [AGENT] P1. **Verify deployment-ui drilldown** for `asset_group=cefi` shows every (venue, year, data_type) cell
      green or yellow under the secondary-cutoff denominator.

- [ ] [AGENT] P1. **Update parent plan** (`instruments_and_market_tick_data_completion_2026_05_01.md`) Phase 2 todos to
      reference this audit + check off the items as they complete.

## Where to ping Ikenna

Per the playbook's "playbook says X, code does Y" rule, the items below need a heads-up because they span multiple repos
/ shared infrastructure:

- **BUG-3 (event-bucket 429)** affects every backfill VM, not just CeFi. If sports / DeFi / TradFi VMs aren't crashing
  the same way, it might be CeFi-specific event volume — but worth confirming before patching.
- **BUG-4 (lifecycle exit-code reporting)** has cross-asset_group implications: any dashboard or sweep script reading
  deployment archives is currently being lied to about failure counts.
- **DERIBIT adapter `expiry_date=None` (BUG-1)** — if there's an existing in-flight fix or a known reason the source
  returns None (e.g. Tardis-side schema drift), we should know before forking.

## Success criteria

- **Phase 2.0:** one CeFi VM runs to completion without a 429; deployment registry reports correct exit codes; zombie
  VMs cleaned up.
- **Phase 2.A:** Cluster A drops from ~33k to <5k.
- **Phase 2.B:** Cluster B drops from ~46k to <500.
- **Phase 2.C:** Cluster C drops from ~10k to <500.
- **Phase 2.D:** Cluster D drops from 389 to <50.
- **Phase 2.E:** Total `attempted_failed` < 1% of CeFi manifest rows; phantom-recon clean; drilldown green.

## Out of scope

- TradFi / DeFi / sports / prediction backfill (other phases).
- Trailing 17-day instruments-service ingest gap (operator confirmed throwaway — the daily ingest can pick that up
  anytime).
- New CeFi venues beyond the existing universe.
- Combo bundling (covered in `cefi_combo_capture_2026_04_29.md` + the 2026-04-30 TradFi session migration).

## Reference data captured during audit (2026-05-01 14:45 UTC)

- MTDS CeFi manifest path: `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet`
- Total rows: 1,040,592
- Date range: 2019-03-30 → 2026-04-28
- `captured`: 180,942 / `empty_confirmed`: 768,659 / `attempted_failed`: 90,991
- DERIBIT failures: 60,414 (66% of total)
- Top error_reason: `Response payload is not completed` (31,142)
- Top venue×data_type: DERIBIT trades / book_snapshot_5 / derivative_ticker (17,240 each)
- 20 in-flight VMs from `launch-cefi-sharded-backfill.sh` 2026-05-01 14:28 UTC: all crashed in 7-13 min on event-bucket
  429 (`run.log` tails confirm rc=1 on 4/4 sampled).
- UAC venue start dates verified to match instruments-service manifest exactly — no inception-date discrepancy.

## 2026-05-05 re-audit + corrected DERIBIT diagnosis

### Manifest state today (vs 2026-05-01)

| capture_status     | 2026-05-01 |     Today | Δ          |
| ------------------ | ---------: | --------: | ---------- |
| `captured`         |    180,942 | 1,020,857 | +839,915   |
| `empty_confirmed`  |    768,659 | 1,117,828 | +349,169   |
| `attempted_failed` |     90,991 |    86,066 | −4,925     |
| **Total rows**     |  1,040,592 | 2,224,751 | +1,184,159 |
| **% failed**       |       8.7% |      3.9% | ↓ 4.8pp    |

Manifest grew 2.1× (date range now extends through 2026-05-04). The 4 CeFi VMs running on 2026-05-05
(bitfinex-spot-2023, bitget-spot/futures-2025, coinbase-spot-tbbo) successfully landed ~840k captured rows.
`attempted_failed` shrank slightly in absolute terms, but the underlying failure shape on DERIBIT is essentially
unchanged.

### Phase 2.B initial hypothesis (from 2026-05-01) was WRONG

The 2026-05-01 audit hypothesised that perpetuals were being routed into `futures_chain` / `options_chain` shards
("`(futures_chain, BTC-PERP)` ghost shards"). **Re-auditing the manifest on 2026-05-05 disproves this.** The actual
manifest shows:

| `data_type`         | failing `instrument_id`s             |   rows |
| ------------------- | ------------------------------------ | -----: |
| `trades`            | **all 10 perps** (BTC-PERP…ARB-PERP) | 12,470 |
| `book_snapshot_5`   | **all 10 perps**                     | 12,470 |
| `derivative_ticker` | **all 10 perps**                     | 12,470 |
| `futures_chain`     | only BTC, ETH (correct UAC seed)     |     68 |
| `options_chain`     | only BTC, ETH (correct UAC seed)     |     68 |
| `liquidations`      | (blank instrument_id)                |     34 |

Every chain-shard failure is on the legitimate `(BTC, ETH)` underlyings. **There is no perp leak into chain
data_types.** UAC's `_OPTION_FUTURE_MVP_SEED_UNDERLYINGS = ("BTC", "ETH")` is being respected by the orchestrator.

### Real BUG-1: per-instrument shards are running OPTION schema validation

Every failing perp row on `trades` / `book_snapshot_5` / `derivative_ticker` carries:

- `instrument_type` column = **blank** in the manifest
- `error_reason` = `"OPTION row requires 'expiry_date', 'strike', and 'option_right' (got expiry=None…)"`

This is a category error inside the schema validator. A `(DERIBIT, BTC-PERP, trades)` shard cannot legitimately produce
OPTION rows — perps have no expiry. Either:

1. The row-type classifier in the writer pre-validation is mis-classifying perp rows as OPTION, OR
2. The validator is keying off something other than `data_type` / `instrument_type` (possibly the venue's default
   `_VENUE_INSTRUMENT_TYPE["DERIBIT"] = "perpetual"`) and falling through to the OPTION branch on rows where the symbol
   parser couldn't extract canonical fields.

**The "blank instrument_type in manifest" detail is load-bearing.** Manifest row shape suggests the writer's pre-write
validation path is the entry point — `StreamingParquetWriter pre-write validation failed` (3,220 rows in today's
manifest, up from 232 on 2026-05-01) is the same failure surfacing at a different layer.

### Updated Phase 2.B work order

The previous Phase 2.B todos (orchestrator-level "filter perps out of chain data_types") are **moot** — that filter
would do nothing because perps are not in chain shards. New work order:

- [ ] [AGENT] P0. **Locate the schema validator emitting `OPTION row requires 'expiry_date'`.** Likely in
      `market-tick-data-service/market_tick_data_service/engine/` (writer / pre-write validation) or
      `market_tick_data_service/market_interface/adapters/cefi/` (Tardis row classifier). Document the exact entry
      point + row-classification logic.
- [ ] [AGENT] P0. **Reproduce the failure with real Tardis data.** Pick one failing shard (e.g.
      `(DERIBIT, BTC-PERP, trades, 2024-01-15)`), download the Tardis CSV directly, run the validator on it, and observe
      the mis-classification. Captures the input shape that triggers the OPTION branch.
- [ ] [AGENT] P0. **Identify the misclassification trigger.** Likely candidates: empty `instrument_type` column → falls
      through to OPTION branch as default; symbol-parser side-effect populating `expiry_date=None` and triggering OPTION
      schema check; venue-level `_VENUE_INSTRUMENT_TYPE["DERIBIT"] = "perpetual"` getting overridden by a row-level
      classifier elsewhere.
- [ ] [AGENT] P0. **Propose minimal fix.** Schema enforcement stays — perp rows on `trades` should validate against the
      `trades` schema (`timestamp`, `price`, `amount`), never the OPTION schema.
- [ ] [AGENT] P1. **Investigate `StreamingParquetWriter pre-write validation failed` (3,220 rows, up from 232).** Likely
      the same bug surfacing at the writer layer; confirm or refute after the row-classifier fix.
- [ ] [HUMAN] P0. After the fix lands + tarball refreshed, relaunch DERIBIT-only shards that failed BUG-1. Expected
      recovery: ~37k rows of Cluster B.

### New finding: ASTER venue is 0 captured / 18.2% failed

ASTER (a perpetual-only venue, 2026 onboarding) has **17,681 manifest rows: 0 captured, 14,461 empty_confirmed, 3,220
attempted_failed**. All three core data_types fail in identical 920-row batches plus 460 liquidations. Symptom matches
the DERIBIT BUG-1 signature.

- [ ] [AGENT] P1. **Confirm whether Tardis has archive coverage for ASTER.** If yes, ASTER inherits DERIBIT's BUG-1 fix.
      If no, instruments-service is emitting shards we can't fulfil and the right answer is to mark ASTER's `start_date`
      correctly in UAC.

### New finding: cluster sizes shifted

| Cluster                                         | 2026-05-01 |   Today | Status                                      |
| ----------------------------------------------- | ---------: | ------: | ------------------------------------------- |
| A: `Response payload not completed` (transient) |     31,142 |  29,513 | flat — Cluster A retry not run yet          |
| B: `FUTURE/OPTION expiry_date None`             |     46,034 |  39,863 | partial recovery + corrected diagnosis      |
| B': `StreamingParquetWriter pre-write fail`     |        232 |   3,220 | **regression — 14× worse, same root cause** |
| C: `In CSV column #N` (Tardis schema drift)     |    ~10,000 | ~10,200 | flat                                        |

### Operational notes (still relevant)

- BUG-3 (event-bucket 429): the 4 currently-running CeFi VMs have been alive for 18-24h without crashing, suggesting
  either the fix landed or the failure mode is event-rate-dependent and these VMs run quietly. **Defer confirming BUG-3
  until next bulk relaunch.**
- BUG-4 (lifecycle exit-code reporting): unchanged — still reports `exit_code=0` on failure per audit findings. Lower
  priority than the schema-validator fix because the data-quality impact is observability-only.
- Phase 2.0 zombie cleanup happened at some point (was 20 zombies on 2026-05-01; 4 healthy VMs today).

## 2026-05-05 fix landed — BUG-X1 + BUG-X2

The corrected diagnosis was confirmed by a second pass through the manifest data: chain-shard failures are clean (only
BTC/ETH underlyings as UAC seeds), and the per-instrument failures all share `instrument_type=` blank with the OPTION
schema error message — meaning they're sentinel rows fanned out from a venue-level exception, not actual write attempts
on each instrument. Two compounding bugs fixed:

### BUG-X1 — instrument_id vocabulary mismatch (closed)

The orchestrator's Tier-3 `captured_per_instrument_shards` set stored the writer's wire-format symbol (`BTC-PERPETUAL` /
`BTCUSDT` / `BTC-USDT-SWAP` / `ADA_USDC-PERPETUAL` / `BTCF0:USTF0`). UAC's MVP seed tables emit canonical IDs
(`BTC-PERP` / `BTC-USDT`). The set-diff at the sentinel comparison never matched on perp venues — every captured shard
re-emitted as a sentinel `attempted_failed` row, even on dates where the data was successfully captured.

Two-part fix:

- **MTDS** (commit `fe5cc2c` on `live-defi-rollout`): added `_canonicalize_captured_instrument_id(venue, raw_symbol)`
  helper that maps wire→UAC seed canonical at the captured-side write into `captured_per_instrument_shards`. Driven by
  the existing `_VENUE_INSTRUMENT_TYPE` dict so adding a new perp venue updates one place. Never mutates the parquet
  `file_stem` or manifest `instrument_id` column — those keep wire form as the immutable downstream-reader contract. 28
  unit tests in `test_orchestrator_canonicalize_captured.py` lock per-venue rules (DERIBIT inverse + linear, BYBIT
  USDT + USD inverse, OKX-SWAP, HYPERLIQUID bare, BITFINEX margin `:USTF0`, BITGET / KRAKEN packed, BINANCE-SPOT,
  COINBASE-SPOT).
- **UAC** (commit `82d7d50` on `live-defi-rollout`): fixed three sub-bugs in `get_expected_instruments_for_venue`'s
  default seed path: (1) `-FUTURES` venues fell through to SPOT branch and seeded `BTC-USDT` instead of `BTC-PERP`; (2)
  `derivative_ticker` returned PERP seeds unconditionally even for spot-only venues that physically can't publish it;
  (3) `trades` / `book_snapshot_5` ignored the venue's `VENUE_DATA_TYPE_CAPABILITIES` entry, so ASTER (no
  `book_snapshot_5` capability) seeded book sentinels anyway. `VENUE_DATA_TYPE_CAPABILITIES` is now consulted as the
  SSOT before any seed is emitted.

### BUG-X2 — venue-level error fanned out as if per-instrument (closed)

A single bad row in a venue fetch (one Tardis option row missing `expiry_date`) raised `ValueError`, the exception was
caught at the venue level, and the Tier-3 sentinel stamped its 80-char description
(`"OPTION row requires 'expiry_date'..."`) onto **every** per-instrument sentinel row for that (venue, date, dt). Made
it look like every perp failed schema validation when in fact one option row in the bundle did. Same pattern in the
sports Tier-2 fan-out.

Fix in MTDS commit `fe5cc2c`: when `classify_venue_error` cannot bucket the exception, the sentinel writes the generic
code `VENUE_FETCH_FAILED` instead of leaking exception text. Descriptive message stays in logs; manifest stops lying.
Applied symmetrically to the CeFi Tier-3 path and the sports Tier-2 fan-out.

### Manifest-state expectations after fix lands

The 86k stale `attempted_failed` rows from 2026-04-29/30 are still in the manifest — they pre-date the fix. Expect them
to flip on next backfill pass (the orchestrator's pre-flight will skip them as "already attempted" unless `--force` is
passed; alternatively, the next phantom-recon sweep will reclassify any with parquets present). Going forward, new runs
will write honest manifest rows.

**Pre-existing test failures fixed in passing**: `test_umi_tick_provider_routes.py` had three failing tests on the
baseline (missing `fetch_l2_book` AsyncMock stub); patched in the same MTDS commit so the QG can pass.

### Affected venues (X1 blast radius — 100% covered by fix)

- DERIBIT (perp + linear perp + options chains): wire forms `BTC-PERPETUAL`, `ADA_USDC-PERPETUAL` etc. → canonical
  `BTC-PERP`, `ADA-PERP` etc.
- BINANCE-FUTURES, BYBIT, OKX-SWAP, ASTER, HYPERLIQUID: packed/wire forms → `BASE-PERP`.
- BITFINEX-FUTURES (margin pair `BTCF0:USTF0`), BITGET-FUTURES, KRAKEN-FUTURES: packed → `BASE-PERP`.
- BINANCE-SPOT, COINBASE-SPOT, OKX-SPOT, BITFINEX-SPOT, BITGET-SPOT, KRAKEN-SPOT, UPBIT: packed/dash → canonical
  `BASE-QUOTE`.

### Out-of-scope / deferred

- **ASTER backfill**: 0 `captured` rows of any data_type in the manifest. Unclear whether Tardis has archive coverage
  for ASTER or the wire-symbol format passed by the launcher is wrong. Investigate before launching ASTER VMs. The X1
  fix covers ASTER's vocabulary mismatch but won't help if the upstream archive is genuinely empty.
- **Manifest backfill of stale rows**: the 86k stale `attempted_failed` rows from 2026-04-29/30 don't auto-fix; they
  need a phantom-recon sweep or a forced re-run. Not blocking — new captures will land cleanly.
- **UAC `normalize_symbol` separately**: UAC's own `_normalize_deribit` regex doesn't handle linear `ADA_USDC-PERPETUAL`
  shapes, and `_normalize_bybit` quotes set is missing `USD`. These are documented separately because the MTDS-side
  helper handles them. Fold into UAC if any other consumer hits the same issue.
