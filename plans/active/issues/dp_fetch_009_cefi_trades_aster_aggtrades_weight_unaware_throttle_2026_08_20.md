---
doc_type: issue
title: >-
  DP-FETCH-009 cefi/trades root cause: Aster's throttle() paced by raw request count (10 req/s)
  while aggTrades actually costs 20 REQUEST_WEIGHT/call against a 2400-weight/minute budget --
  fixed with a weight-aware throttle
summary: >-
  Escalation agt-a67330 fired DP-FETCH-009 (CRITICAL DP_RUN_MOSTLY_EMPTY) for asset_group=cefi
  data_type=trades: 97,470 attempted_failed of 1,619,620 attempted (6.0%), with 3,322
  attempted_failed rows fresh in the last 1 day. A live-manifest probe (pyarrow, column-projected,
  bounded) found the FRESH subset was 100% pipeline_mode=batch_aster, venue=ASTER,
  error_reason="Aster aggTrades HTTP 429 for <symbol>" across ~150+ distinct symbols and many
  distinct backfill days -- i.e. NOT the already-tracked 2026-08-16 corrective-migration
  overreach population (that population's live_* rows were already reverted; this is a
  DIFFERENT, NEW root cause on the batch_aster lane specifically). Traced to
  AsterBaseClient.throttle() pacing outbound aggTrades requests at a flat 10 req/s
  (rate_limit_per_second), which assumes 1 REQUEST_WEIGHT per call -- but a live probe of
  fapi.asterdex.com/fapi/v1/aggTrades?limit=1000 (2026-08-20, exchangeInfo rateLimits +
  x-mbx-used-weight-1m response header, 3 sequential calls: weight jumped +20/call) confirmed
  each aggTrades call costs 20 weight against a real 2400-weight/minute budget. At 10 req/s x 20
  weight/call, a single VM exhausts its ENTIRE minute's weight budget in ~12s, then gets 429'd for
  the remaining ~48s of every minute -- every minute, for the VM's whole runtime. The adapter's
  existing 429-handling (5 retries, exponential backoff 2s/4s/8s/16s/32s, then raise ->
  record_failed) is CORRECT and honest (the 2026-07-20 misclassified-empty fix is intact and not
  regressed) -- but the sustained per-minute throttle window (~48s) regularly outlasts the ~62s
  total retry budget, so genuinely-fetchable data was recorded attempted_failed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, dp-fetch-009, trades, aster, rate-limit, request-weight, manifest, attempted_failed, data-correctness]
related:
  [
    /plans/active/issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
parent_epic: cefi_master
source: >-
  DP-FETCH-009 escalation agt-a67330 (data_pipeline_failure worker, slot 33, 2026-08-20) --
  CRITICAL DP_RUN_MOSTLY_EMPTY for asset_group=cefi data_type=trades: 97470 attempted_failed of
  1619620 attempted (6.0%); 3322 attempted_failed rows fresh in the last 1 day.
assigned_vm: NA
created: 2026-08-20
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    market-tick-data-service/market_tick_data_service/market_interface/clients/aster_base_client.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py,
  ]
---

# DP-FETCH-009 cefi/trades -- Aster aggTrades throttle was request-count-paced, not weight-aware

## What I found

Escalation `agt-a67330` fired DP-FETCH-009 for `asset_group=cefi data_type=trades` (97,470/1,619,620
attempted_failed, 6.0%; 3,322 fresh in the last 1 day). A bounded pyarrow probe of the live cefi
availability index (column-projected: date/venue/data_type/service_name/capture_status/error_reason/
pipeline_mode/attempted_at; `run-bounded-analysis.sh`-wrapped) found:

- Overall cefi/trades `attempted_failed`: 360,755 rows. Dominant historical `error_reason`s:
  `UNCLASSIFIED:Tardis HTTP 403` (112,579), `VENUE_FETCH_FAILED` (93,935), `Tardis HTTP 403`
  (44,647), `UNCLASSIFIED_ADAPTER_ERROR` (37,436) -- pre-existing, already-tracked Tardis-side
  issues, out of scope here. The 2026-08-16 corrective-migration sentinel
  (`CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16`) accounts
  for 7,435 rows, all `batch_*` pipeline_mode -- the already-known, deliberately-deferred
  batch-side population from `dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md`
  todo 2 (not touched by this investigation; still open there).
- **Fresh (attempted_at within the last 1 day): 3,306 rows, 100% `pipeline_mode=batch_aster`,
  100% `venue=ASTER`**, `error_reason` exclusively `"Aster aggTrades HTTP 429 for <symbol>"` across
  ~150+ distinct symbols (BTCUSDT 217, ETHUSDT 97, SOLUSDT 80, HYPEUSDT 67, ... long tail). This is
  a DIFFERENT, NEW population from the migration-overreach one above -- not previously documented.

Live GCP check (`gcloud compute instances list`) confirmed 3 concurrently-RUNNING ASTER
year-sharded backfill VMs (`cefi-aster-2024-20260819-000150`, `-2025-`, `-2026-`, launched
2026-08-18, one per `launch-cefi-hl-aster-historical-backfill.sh`'s year-shard loop) -- each with
its OWN distinct external IP (34.104.226.218 / 35.189.137.42 / 34.84.3.142, confirmed via
`gcloud compute instances describe`), ruling out the "VMs share one NAT egress IP" hypothesis.

**Root cause, confirmed live 2026-08-20**: `fapi.asterdex.com/fapi/v1/exchangeInfo`'s `rateLimits`
field states `REQUEST_WEIGHT: 2400/MINUTE` (matches the value already hardcoded in
`aster_base_client.py`'s comment) -- but a direct probe of the aggTrades endpoint itself
(`GET /fapi/v1/aggTrades?symbol=BTCUSDT&limit=1000`, 3 sequential calls) showed the
`x-mbx-used-weight-1m` response header incrementing by exactly **20 per call** (21 -> 41 -> 61).
`AsterAdapter._agg_trades_page()` requests `limit=1000` (matches the probe exactly) and calls
`AsterBaseClient.throttle()` with NO weight parameter -- `throttle()` only paced by
`rate_limit_per_second` (10.0), implicitly assuming 1 weight/request. At 10 req/s x 20
weight/call = 200 weight/s = 12,000 weight/minute against a real 2,400-weight/minute budget, a
single VM burns its ENTIRE minute's budget in ~12s, then gets 429'd for the remaining ~48s of
every 60s window, indefinitely, for the VM's whole runtime -- every symbol/day it happens to be
paginating through during that ~48s window fails.

The existing 429-handling (`_AGG_TRADES_MAX_RETRIES=5`, exponential backoff 2/4/8/16/32s, ~62s
total) is itself CORRECT and honest: on a retryable status it backs off and retries, and only
after exhausting retries does it `raise` (routing to `record_failed` / `attempted_failed`), never
silently returning `[]` (which would fabricate `empty_confirmed`) -- the 2026-07-20 fix
(`aster_adapter.py`'s own docstring cites 412,697 fabricated rows from that earlier bug) is
intact and NOT regressed. The defect is purely that the retry window (~62s) is shorter than the
~48s-per-minute throttled window RECURS every minute -- so a retry sequence starting anywhere in
that window has a real chance of exhausting all 5 attempts before the window clears, especially
since every retry attempt ALSO calls `throttle()` and is itself weight-gated once the fix below is
applied (this doc's fix reduces effective throughput further, which is the intended, correct
behaviour -- see "Why it matters").

## Why it matters

This is not a misclassification bug (unlike the 2026-07-20 and 2026-08-16 incidents it neighbors)
-- the manifest is being told the honest truth (fetch attempts failed). But "honest failure,
persistently" still means real, fetchable Aster trade data is not being captured: at 10 req/s the
adapter is instructed to run ~5x faster than Aster's real weight budget allows for this specific
endpoint, so the failure is self-inflicted and 100% avoidable, not a genuine upstream outage or
Aster-side capacity issue. Left uncorrected, EVERY current and future ASTER trades batch backfill
run will keep tripping this same DP-FETCH-009 shape indefinitely, and the underlying data gap
(days/symbols recorded `attempted_failed` instead of `captured`) will persist until a future
resumed run happens to retry those specific (venue, date, symbol) shards and get lucky within a
non-throttled window.

## What I did

- [x] ✅ [DATA] P1. **Root-caused via live measurement, not guesswork**: confirmed Aster's real
      REQUEST_WEIGHT budget (2400/min) and the aggTrades endpoint's real weight cost (20/call at
      `limit=1000`) via direct, read-only probes against the live public API (no credentials
      needed) -- both values match what `aster_base_client.py`'s own comment already claimed for
      the *budget*, but the *per-call weight* had never been measured/accounted for anywhere in
      the pacing logic.
- [x] ✅ [CODE] P1. **Made `AsterBaseClient.throttle()` weight-aware.** Added
      `weight_limit_per_minute: float = 2000.0` to `AsterClientConfig` (2000, not 2400, for ~17%
      safety headroom against clock skew) and extended `throttle(weight: float = 1.0)` to track a
      rolling 60s weight budget in addition to the existing flat `rate_limit_per_second` floor --
      default `weight=1.0` keeps every OTHER (lighter) Aster call site's behaviour byte-for-byte
      unchanged (2000/min ceiling never engages below the existing 10 req/s=600/min pace for
      weight-1 calls). Wired `AsterAdapter._agg_trades_page()`'s `throttle()` call to
      `weight=20.0`, the measured live value.
      **DONE 2026-08-20 — `market-tick-data-service@8d51b537ef`.**
- [ ] [DATA] P2. **Not investigated here (out of scope for this escalation's fresh-population
      diagnosis)**: whether the OTHER Aster endpoints this adapter calls (funding-rate/premiumIndex
      at `limit=1500`, exchangeInfo symbol lookups) also carry a weight >1 that the default
      `weight=1.0` under-counts. None of them appeared in the FRESH failing population this
      escalation traced (only aggTrades/trades did), so they were not probed live. If a future
      DP-FETCH-009 fires for cefi/`derivative_ticker` on ASTER specifically, measure that
      endpoint's real weight the same way (live `x-mbx-used-weight-1m` probe) before assuming this
      fix's default `weight=1.0` is safe for it too.
- [ ] [DATA] P2. **Not attempted here**: re-running/resuming the 3 currently-live ASTER
      year-shard VMs is out of scope for a one-shot escalation worker (would need to confirm
      whether they self-recover via retry-failed re-verification on their next pass, or need an
      explicit relaunch) -- once this fix lands and a future ASTER batch run (new launch or a
      resumed/relaunched existing shard) passes over the currently-`attempted_failed` cells, they
      should convert to `captured` on their own; no manifest write performed by this investigation.

## Progress Log

- 2026-08-20, `data_pipeline_failure` worker (slot 33, escalation `agt-a67330`): filed after
  root-causing DP-FETCH-009 for cefi/trades to a weight-unaware Aster throttle (aggTrades weight
  20/call vs. the 1.0-weight-per-request pacing assumption). Fixed in
  `aster_base_client.py`/`aster_adapter.py`, shipping via quickmerge this session.
- 2026-08-20, `data_pipeline_failure` worker (slot 1, escalation `agt-2efe94`): re-fire of the
  SAME DP-FETCH-009 condition (cefi/trades: 97,578 attempted_failed / 1,604,161 attempted, 6.1%;
  3,055 fresh in last 1d) after the code fix landed. Verified NOT a new regression — see the
  `## Re-fire resolution` section appended below.

## Re-fire resolution (agt-2efe94, 2026-08-20)

DP-FETCH-009 re-fired for `asset_group=cefi data_type=trades` (97,578 attempted_failed of
1,604,161 attempted, 6.1%; 3,055 fresh in the last 1d) after this doc's code fix shipped. This is
a re-fire of the SAME already-root-caused condition, NOT a new regression.

### Verified

- **Fix landed**: `market-tick-data-service@8d51b537ef` (weight-aware Aster throttle) is an
  ancestor of `origin/live-defi-rollout` (verified via `git merge-base --is-ancestor`).
- **Fresh population is the same cause** (bounded pyarrow probe of the live cefi consolidated
  availability index, row-group streaming under the shared-host memory cap; ~4G peak):
  - LIFETIME attempted_failed/trades: 360,828 rows.
  - FRESH last-1d: **3,027 rows — 100% `batch_aster` / `venue=ASTER`, error_reason exclusively
    `"Aster aggTrades HTTP 429 for <symbol>"`** (~150+ distinct symbols; BTCUSDT 223, ETHUSDT 107,
    SOLUSDT 79, ...).
  - FRESH last-6h: 483 rows, max `attempted_at` 2026-08-20T04:00Z — **still actively climbing at
    probe time**, i.e. not a static backlog.
- **Why it kept re-firing**: the 3 ASTER year-shard backfill VMs
  (`cefi-aster-2024/2025/2026-20260819-000150`, launched 2026-08-18, **pre-fix**) were STILL
  RUNNING the old weight-unaware throttle. Backfill VMs deploy code from a MANUAL GCS tarball
  (`create-code-tarballs.sh` → `gs://deployment-scripts-{project}/code/mtds-code.tar.gz`) at boot —
  they do not self-pull LDR, so the shipped fix never reached them. Each VM burns its full
  2400-weight/min budget in ~12s and gets 429'd ~48s of every minute, indefinitely.

### Action taken (main-agent endorsed Option A via BLK-573b0aee)

1. **Rebuilt the code tarballs** (`bash scripts/vm/create-code-tarballs.sh`, default core scope):
   `mtds-code.tar.gz` fixed-name + `@801e0d31efad...` SHA-pinned copy re-uploaded 2026-08-20
   04:47Z from `market-tick-data-service@801e0d31` (= origin/live-defi-rollout, whose ancestor
   chain includes the fix `8d51b537ef`). Manifest verified: `commit_sha=801e0d31efad370d...`,
   `git_status_clean=True`, `created_at=2026-08-20T04:46:55Z`.
2. **Restarted the 3 ASTER VMs** (`gcloud compute instances stop` → `start`, zone
   asia-northeast1-c): all 3 now RUNNING with fresh external IPs
   (34.180.101.206 / 34.84.63.145 / 35.200.107.78). The `startup-script-url` re-runs
   `setup-data-pipeline-vm.sh` on boot → re-installs the fixed `mtds-code.tar.gz` → resumes
   `collect-onchain-perp-batch` from manifest progress (standard VM recovery pattern; no
   `START_DATE` replay).

### Follow-on verification (not waited for in this one-shot escalation)

- Confirm fresh `attempted_failed` stops accumulating for cefi/trades on the next DP-FETCH-009
  sweep (or any later manifest probe) once the restarted VMs finish setup + resume fetching.
- The **historical** `attempted_failed` cells (this doc's original population) still convert to
  `captured` only when a future ASTER batch run passes over them (todo 2's retry-failed path) —
  the restart alone re-captures the cells the running VMs had already failed; the older failed
  cells need a resumed run, unchanged by this action.

- **context-scout 2026-08-20**: refreshed context_scope (5 entries) — added the VM-deployment codex doc backing
  the "Re-fire resolution" section's root cause (manual tarball deploy vs. LDR self-pull).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — 2 open items remain explicitly conditional/contingent
  (other Aster endpoints' weight, only relevant if a future alert fires; VM re-run self-recovery, no manifest write
  needed) — not currently actionable.
