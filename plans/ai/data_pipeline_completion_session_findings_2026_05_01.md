---
title: "Data-pipeline-completion epic — Harsh's session findings (2026-05-01)"
priority: P0
status: active
owner: harsh + ikenna
created: 2026-05-01
type: tracker
epic: data-pipeline-completion
parent_plan: plans/active/instruments_and_market_tick_data_completion_2026_05_01.plan.md
---

## Purpose

Running checklist of bugs, drift, and decisions discovered during the 2026-05-01 session driving the data-pipeline
completion epic forward. Each item has enough context to act on without re-investigating. Tick boxes as we resolve;
expand item bodies with resolution notes when closed so this stays useful as a forensic record.

Not a full plan with phases / DAG — that's
[instruments_and_market_tick_data_completion_2026_05_01.plan.md](../active/instruments_and_market_tick_data_completion_2026_05_01.plan.md).
This file is the running-todo pad for things that came up while executing it.

## Manifest data-quality bugs (CRITICAL — discovered 2026-05-02)

Found while inspecting the CSV download for `(market-tick-data-service, BINANCE-SPOT, 2026-01-01)`. Three distinct
issues compound to make the manifest unreliable for `empty_confirmed` rows. Each is independent; address separately.

### Bug A — `empty_confirmed` written without API confirmation (orchestrator sentinel pass)

- [ ] **Location**: `market-tick-data-service/market_tick_data_service/engine/orchestrator.py:1915`
- **Symptom**: rows like `(2026-01-01, BINANCE-SPOT, "", book_snapshot_5, BTC-USDT, empty_confirmed)` exist in the
      manifest. BTC-USDT trades on Binance every day since 2017 — the underlying truth is "data was definitely
      available; we just didn't capture it." `empty_confirmed` is a lie here.
- **Root cause**: in the Tier-3 sentinel fan-out (orchestrator line 1899-1915), for each expected instrument NOT in
      `captured_per_instrument_shards`:
      - if there was a classified adapter error → `record_failed` (correct)
      - **else → `record_empty(row_key=row_key_instrument)` (wrong)**
      The "else" assumes "not in captured set ⇒ source confirmed empty." But there are several non-confirmed-empty
      reasons an instrument can be missing from the captured set: VM died mid-batch, network failed, the previous run
      wrote under a different `instrument_id` shape (lowercase / non-hyphenated), pre-flight skipped due to a stale
      phantom row, etc.
- **Workspace rule violated**: per `unified-trading-pm/cursor-configs/CLAUDE.md` (manifest section): *"`record_empty`
      is for legitimately-empty source responses only (we tried, API returned 200+empty)"*. The sentinel pass writes
      `empty_confirmed` without ever probing the API for that specific instrument.
- **Impact**: every row that the sentinel marked `empty_confirmed` without API proof inflates the apparent
      "completion" of the manifest. CeFi headline coverage % is overstated. Reads against the manifest will skip
      "empty_confirmed" instruments on rerun, locking in the bad state.
- **Fix candidates (need Ikenna's call before patching core orchestrator)**:
  - **(a)** Replace `record_empty(...)` at line 1915 with `record_failed(..., error="sentinel_unconfirmed_empty")` so
        the manifest stays honest and the next backfill VM retries. Cheapest, no behavior change in legitimate cases
        because real "empty_confirmed" rows are written by the adapter itself before this fan-out runs.
  - **(b)** Probe the venue API explicitly before declaring empty (per-instrument cost; rate-limit-heavy).
  - **(c)** Don't write anything for missing instruments; let readers derive `missing = expected - captured`.

### Bug B — Duplicate `instrument_id` rows for the same logical instrument (case / format drift)

- [ ] **Symptom**: same `(date, venue, data_type)` has rows for `BTC-USDT`, `btcusdt`, AND `BTCUSDT`. All three are
      semantically the same Binance spot market.
- **Root cause**: pre-canonical writers (2026-04-22 batch) used `btcusdt` (lowercase, no separator). Canonical
      writers (2026-04-30 batch) use `BTC-USDT` (uppercase, hyphenated, per UAC `make_canonical_instrument_id`).
      Phantom recon (2026-05-01) flipped the third form `BTCUSDT` (uppercase, no separator) to `attempted_failed`.
      No cleanup pass dedupes the legacy lowercase rows after the canonical rerun lands.
- **Impact**: manifest shard counts are inflated by 1.5–3x because the same `(date, venue, data_type)` slot is
      counted multiple times. CeFi coverage calculations become meaningless.
- **Fix**: add a one-time dedup script (or extend `reconcile_phantom_manifest_rows.py`) that, for each
      `(date, venue, data_type)`, picks the canonical `instrument_id` form (UAC `make_canonical_instrument_id`) and
      drops the legacy variants. Requires careful handling because the canonical form's row may be the "empty_confirmed"
      lie from Bug A — dropping the legacy row without fixing Bug A first would lock the lie in.

### Bug C — Inconsistent `instrument_type` field shapes

- [ ] **Symptom**: same `(date, venue, data_type, instrument_id)` slot exists with `instrument_type` taking three
      different values: `""` (empty), `"SPOT_PAIR"` (uppercase), `"spot_pair"` (lowercase).
- **Root cause**: writers across different epochs chose different conventions; no enum enforcement at write time.
      The newest canonical form leaves `instrument_type` empty (because the GCS path encodes it via hive partition
      `instrument_type=spot_pair`); older forms wrote it as a column too.
- **Impact**: readers must flatten three shapes for one logical type. Coverage calculations may double-count
      depending on whether the reader normalizes. Phantom recon may probe wrong paths.
- **Fix**: pick the canonical form (likely empty in column + present in hive path, per UAC enum). Migrate older
      rows by dropping the column value where the hive path is authoritative. Ties into Bug B's dedup pass.

### Cross-bug observation

These three bugs are **why the sports SFI / footystats / api-football headline coverage % has been bouncing around
between 74% → 83% → 75% → 80% across 2026-04-29 to 2026-05-02**. Each phantom recon and rename pass is correcting
*one* layer of dishonesty while leaving others. Until all three are fixed, the manifest's coverage % is not a
trustworthy signal for "are we done with backfill" — only direct GCS-vs-manifest reconciliation is.

**Action sequence (depends on Ikenna)**: Fix A (3-line orchestrator change) → run on a small year of CeFi to prove
the false-empty rows convert to attempted_failed → relaunch CeFi backfill (those rows now retry) → ship Bug B/C
dedup script after the backfill lands → re-baseline coverage %.

## Phase 0 — UI unblockers (status)

Phase 0 of the parent active plan. Tracking the verification state here separately because some items shipped but need
re-verification after the Pub/Sub IAM grant landed.

- [x] **0.1 Day-shard list capped at 60** — Replaced inline `.slice(0, 60)` with `<DateList>` component (60-per-page +
      "Load more" button). Verified working: user sees `+95 more` on a 219-day list.
- [x] **0.2 CSV download returns headers-only** — Was blocked by Pub/Sub permission denial in deployment-api's audit
      middleware (every request 500'd). IAM grant `roles/pubsub.publisher` on
      `harshkantariya@odum-research.com` is now live, topic `deployment-api-events` exists, live publish test passed
      (messageId `19351384314253488`). The temporary `_log_event_safe` swallow in
      `unified-trading-library/unified_trading_library/core/audit_middleware.py` was reverted to direct
      `log_event(...)` calls (fail-loud restored).
  - [ ] **Re-verify CSV download end-to-end** with audit middleware reverted: pick any captured shard in the UI →
        click `⬇ download CSV` → CSV with rows lands. If still empty, the original headers-only bug is
        deployment-api-side (server-side projection), not the Pub/Sub workaround.
- [x] **0.3 View Schema button** — Was the same Pub/Sub blocker. Modal now opens; venue-row schema button uses first
      known data_type from `subData.data_types` instead of `"AUTO"`. Per-data-type schema button added on sub-rows.
  - [ ] **Re-verify schema modal** end-to-end after audit middleware revert. CeFi → BINANCE-FUTURES → click
        `schema` on venue row should return `trades` columns; click `schema` on `book_snapshot_5` sub-row should
        return book columns.
- [x] **0.4 Sports league/day aggregated CSV download button** — Wired up via `buildFixturesCsvDownloadUrl()` in the
      sports drilldown.
- [ ] **0.5 Unified MTDS + MDPS view (P1)** — Still split across separate parent-tab service selections. Backend
      `/api/data-status/manifest` already takes `service` param; UI can fan out two requests and merge. Defer until
      after CeFi gap-fill is unblocked — not on the critical path for backfill verification.

## Phase 0.5 — UI/API SSOT drift discovered this session

- [ ] **Asset-group filter chips don't show SPORTS or PREDICTION on instruments-service / MDPS data-status tabs.**
      Root cause: two SSOTs disagree.
  - **Deploy SSOT** (`deployment-service/configs/sharding.<service>.yaml`): asset_group axis values list — narrow on
      purpose. instruments-service yaml lists only `[CEFI, TRADFI, DEFI]`; MTDS lists `[CEFI, TRADFI, DEFI, SPORTS]`;
      MDPS lists `[CEFI, TRADFI, DEFI]`. No service lists PREDICTION. This is the right scope for **what can I dispatch
      a sharded deploy for**, because SPORTS uses dedicated launchers
      (`launch-api-football-backfill-vm.sh` etc.) with source-specific args (`--sports-provider`, `--league`,
      `--season`), and PREDICTION instruments are produced as a side-effect of MTDS — no instruments-service VM ever
      runs `--asset-group PREDICTION` and the handler at
      `instruments-service/instruments_service/cli/instruments_handler.py:174` hardcodes `("SPORTS", "CEFI", "DEFI",
      "TRADFI")` for manifest flush, no PREDICTION.
  - **Manifest scope SSOT** (`deployment-api/deployment_api/services/data_status_service.py:1908-1926`,
      `_SERVICE_CATEGORY_RESTRICTIONS`): explicitly documents *"Services NOT listed (e.g. instruments-service,
      market-tick-data-service, market-tick-data-handler, features-calendar-service) apply to ALL 5 categories (CEFI /
      TRADFI / DEFI / SPORTS / PREDICTION)"*. The UI coverage-summary cards already show SPORTS (4,158 dates / 2.3M
      shards) + PREDICTION (574 dates / 3,170 shards / POLYMARKET) for instruments-service — proving manifest data
      exists.
  - **The UI uses the deploy SSOT for both purposes** — `getServiceAssetGroups(serviceName)` reads
      `sharding.{service}.yaml` and feeds the result to both the deploy form *and* the data-status filter chips.
  - **Right fix**: split into two endpoints. Deploy form keeps the sharding-yaml-derived list. Data-status drilldown
      gets a new endpoint (e.g. `/data-status/service-asset-group-scope/{service}`) backed by
      `_SERVICE_CATEGORY_RESTRICTIONS` (default = all 5 when not in the restrictions dict).
  - **Wrong fix** (do NOT do): adding `SPORTS, PREDICTION` to `sharding.instruments-service.yaml` — would let the UI
      dispatch a generic sharded deploy with `--asset-group SPORTS` that doesn't have the source-specific args wired,
      and `--asset-group PREDICTION` that the handler can't flush.
  - **Action**: ping Ikenna to confirm intent before changing — the narrow sharding lists are likely deliberate, and
      the deployment-api endpoint split is the cleaner break. He may also have an opinion on whether the data-status
      tab should show all-5 by default or stay restricted for SPORTS/PREDICTION until those pipelines are mature.

## Phase 2 prerequisite — CeFi zombie VMs

- [ ] **12 CeFi VMs from `run-ts=20260429-184942` rollout are zombies; need to be killed before relaunch.** Summary
      sent to Ikenna; waiting on his go-ahead before deletion.
  - **VMs**: 11 backfill (`cefi-mr-20260429-184942-{258,296,297,303,317,318,321,323,325,328,329}`) + 1 forward-poll
      (`cefi-fwd-20260429-095441`).
  - **Evidence of zombie state**:
    - 5 backfill VMs (`325, 328, 329, 258, 321`) never wrote a per-VM manifest shard since boot ~50h ago
      (`gs://market-data-tick-cefi-central-element-323112/_index/per_vm/cefi-mr-20260429-184942-{n}.parquet` doesn't
      exist).
    - 6 backfill VMs (`296, 317, 323, 297, 303, 318`) wrote shards 36–48h ago, then went silent.
    - Forward-poll VM never wrote a manifest shard.
    - Cloud Logging: zero application log lines in last 24h on any VM. Only systemd cert-refresh + 100% noise from
      `OSConfigAgent / google_guest_agent`: `network error when requesting metadata, dial tcp 169.254.169.254:80:
      connect: network is unreachable`.
    - CPU monitoring (last 1h, all 12 VMs): 0.22–0.35% sustained. System idle. Active Tardis/Binance fetch would run
      50%+ on at least one core.
    - Network counters (last 6h, sample VM 303 on `e2-highmem-8`): sent_bytes_count = **0 bytes** across all 357
      samples. received_bytes_count ≈ 228 KB total, ~638 B/min — DNS keepalive noise only.
    - Failure signature matches the playbook gotcha: *"CeFi VM rc=137 (OOM-kill) does NOT write EXIT_STATUS — atexit
      doesn't fire on SIGKILL"*. Notable: all 11 backfill VMs are already on `e2-highmem-8` (DERIBIT OOM
      mitigation in place), so this is a different failure mode (likely L2 network partition + Python crash, or a
      different OOM victim).
  - **Manifest itself is healthy** — `availability_index.parquet` last consolidated within minutes of inspection,
      consolidator daemon (`manifest-consolidator-20260429-162442`) alive.
  - [ ] Confirm with Ikenna → delete all 12 zombies (`gcloud compute instances delete ...`). Burn rate ~$1.30/hr each on
        `e2-highmem-8`.
  - [ ] After delete: refresh tarballs (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group
        CEFI` or `--all`). Per the playbook: "Tarball-stale-code is silent."
  - [ ] After tarball refresh: audit `attempted_failed` shards in consolidated manifest; scope what actually needs
        gap-fill vs. what landed before VMs died.
  - [ ] Relaunch via `launch-cefi-sharded-backfill.sh` against the gap list, scoped to C5 MVP universe (top ~25
        assets × 6 venues + Deribit combos). **Decision still open**: full `attempted_failed` gap-fill or MVP-only?

## Sports — in-flight (don't collide)

- [ ] Confirm sports backfills (af / tm / sfi / fs) have settled before launching anything new on sports.
      `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"'` showed all 4 +
      consolidator running at session start; user said leave them. Re-check before starting Phase 1 sports priorities
      (FIXTURE_FEATURES 0%, PLAYER_VALUES 2%, etc.).

## Decisions still open (asked Ikenna)

- [ ] **Scope of Phase 2 CeFi backfill**: full `attempted_failed` sweep, or MVP-only (top ~25 assets × 6 venues +
      Deribit combos per playbook)?
- [ ] **SPORTS/PREDICTION on instruments-service data-status drilldown**: split deploy-vs-data-status endpoints
      (right fix per audit), or stay restricted intentionally until sports/prediction pipelines mature?
- [ ] **DERIBIT options/perps `book_snapshot_5`**: previous session noted ~60k `attempted_failed` rows; e2-highmem-8
      should mitigate the OOM, but the 11-VM zombie batch was already on e2-highmem-8 and still died. Need to
      diagnose the new failure mode before relaunching DERIBIT-heavy shards.

## Reference — what shipped this session

- **deployment-ui DataStatusTab**: `<DateList>` pagination component (60/page + Load more); CSV download `⬇`
      anchor with `e.stopPropagation()` so it doesn't toggle the `<details>`; venue-row schema button uses first known
      data_type instead of `"AUTO"`; per-data-type schema button added at sub-row.
- **unified-trading-library audit_middleware**: temporary `_log_event_safe` swallow added (Pub/Sub block workaround) →
      reverted today after IAM grant. File now back to direct `log_event(...)` per fail-loud rule.
- **GCP IAM**: `roles/pubsub.publisher` granted to `harshkantariya@odum-research.com` on `central-element-323112`;
      topic `deployment-api-events` confirmed; live publish smoke test passed.

## How to use this file

- One row per discovered issue / decision / verification. Tick when done. Add a one-line resolution note inline (e.g.
      "→ deleted, see commit X").
- New findings during this epic: append here rather than creating fresh files. Move stable findings into the parent
      active plan or relevant codex doc when they outlive the session.
- Archive (move to `plans/ai/archive/` or delete) once the parent active plan ships and all rows are ticked.
