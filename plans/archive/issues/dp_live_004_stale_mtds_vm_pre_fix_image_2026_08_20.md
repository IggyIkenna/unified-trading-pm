---
doc_type: issue
title: DP-LIVE-004 BYBIT-FUTURES book capture runs a pre-fix MTDS image
summary: >-
  The flagged BYBIT-FUTURES book_snapshot_5 shard runs on a VM created 2026-08-17,
  before market-tick-data-service@5f88715e4b landed on 2026-08-18. Read-only SSH
  inspection confirms the deployed connector still subscribes the unfiltered IS
  universe, so a fresh relaunch is required before judging the shipped fix.
status: resolved
nature: process
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline-alerts, dp-live-004, bybit-futures, stale-vm-image, live-capture]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_live_004_bybit_stale_vm_tarball_2026_08_21.md,
    /plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md,
  ]
created: 2026-08-20
author: data_pipeline_failure (slot 32, escalation agt-0d8048)
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: both todos done 2026-08-21 — VM cycled + fix confirmed deployed (todo 1); post-relaunch
  verification run, negative result root-caused, follow-up filed at
  dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21 (todo 2)
last_updated: 2026-08-21
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source: DP-LIVE-004 / DP_CRON_DID_NOT_FIRE (mtds-live-cefi-consolidated-20260817-025031, BYBIT-FUTURES, book_snapshot_5)
---

# DP-LIVE-004 BYBIT-FUTURES book shard is running a pre-fix image

> **RESOLVED 2026-08-21 (data_engineering, slot 19)**: both todos done. The stale-image condition this doc tracks
> is fixed (VM cycled, fix-provenance confirmed on the replacement). Post-relaunch verification found BYBIT-FUTURES
> still 0 captured rows — a genuine, DIFFERENT bug (silently-dropped Bybit subscribe ack frames), now tracked in
> its own follow-up: `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md`.
> DP-LIVE-004 itself stays open/unmuted — this doc closes only the "stale image" diagnosis this doc's own scope
> covers, per `/codex/11-project-management/issue-doc-lifecycle.md`'s terminal-status convention. No new codex
> contract is established by this resolution (the VM-relaunch pattern is already covered by
> `/codex/05-infrastructure/vm-launcher-runbook.md`); the durable NEW finding (subscribe-ack observability gap)
> lives in the follow-up doc above, not here.

> **CONSOLIDATED 2026-08-21 (ag-closeout-audit cefi tranche, Phase 3)**: this is the same incident as 3 sibling
> docs, filed independently by 4 different escalation dispatches, none cross-referencing each other, all naming the
> identical VM (`mtds-live-cefi-consolidated-20260817-025031`), the identical root cause (stale runtime predates
> `market-tick-data-service@5f88715e4b`), and the identical recommended action (cycle the VM through the registered
> launcher, then verify a real captured row). This doc is now the CANONICAL one (it already carried the correct
> `assigned_vm: planning` / `execution_scope: orchestrator-agent` dispatch frontmatter; the other 3 were either
> `execution_scope: local-only` or a stale `assigned_vm: vm-cross-cutting` legacy value that the single-VM AO
> ingestion path does not match, so none of them were actually reachable by AO dispatch). The other 3 are marked
> `status: superseded` and redirected here — their own evidence/detail is kept, not deleted:
> `/plans/active/issues/dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`,
> `/plans/archive/issues/dp_live_004_bybit_stale_vm_relaunch_required_2026_08_20.md`,
> `/plans/archive/issues/dp_live_004_bybit_vm_stale_tarball_2026_08_20.md`. A single consolidated Todos section
> (below) replaces the 4 separate un-dispatched recommendations.

## What was found

The flagged VM `mtds-live-cefi-consolidated-20260817-025031` is `RUNNING` in
`asia-northeast1-c`, created at `2026-08-17T02:50:40Z`. Its root-owned book process
started at `2026-08-17 02:52:18 UTC`. The MTDS fix
`5f88715e4bdf7fc0c17711d2647e22f8a4d4ba57` landed at `2026-08-18 10:49:19 UTC`.

Read-only SSH inspection of the deployed source at
`/home/ikennaigboaka/workspace/mtds` found:

- `bybit_ws.py` has no `_is_linear_derivative` helper.
- `bybit_futures_book_ticker_ws.py` still assigns
  `self._instrument_ids = set(instrument_ids)` in the book connector.
- The slot's `live-defi-rollout` origin contains the fix, which filters the
  IS-resolved BYBIT catalog to `PERPETUAL`/`FUTURE` before constructing topics.

Therefore this alert is explained by stale deployment state: the process has
never loaded the shipped fix. The source fix is present and does not need a
second code change.

## Why it matters

The VM continues producing `attempted` activity and manifest updates, so it is
not a dead process, but its pre-fix connector can continue subscribing the
unfiltered BYBIT catalog and yield zero captured rows. The existing plan's
fresh-relaunch verification must run before this DP-LIVE-004 condition can be
closed.

## Recommended decision

Use the registered CEFI live forward-poll relaunch path to replace the stale
VM with a current MTDS tarball. Do not terminate this healthy live VM from the
alert-triage worker. After the fresh VM starts, verify the deployed source (or
revision) contains the filter and verify at least one real
`captured` BYBIT-FUTURES row for `book_snapshot_5`; then close the related
follow-up in `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`.

## Todos

- [x] ✅ [INFRA] P1. Cycled the singleton `mtds-live-cefi-consolidated-*` VM through the registered launcher —
      deployment-service (see Progress Log 2026-08-21 infra entry for full evidence: replacement VM
      `mtds-live-cefi-consolidated-20260821-200626` RUNNING in `asia-northeast1-c`, tarball @`f88dfdbd19db` (a
      descendant of `5f88715e4b`), code-provenance confirmed via SSH grep — `_is_linear_derivative` present and
      applied in the deployed `bybit_ws.py`/`bybit_futures_book_ticker_ws.py`). The stale VM
      `mtds-live-cefi-consolidated-20260817-025031` was deliberately left RUNNING (not stopped/deleted) — that step
      belongs to todo #2 below, which is still open.
- [x] ✅ [DATA] P1. After the cycle, verify at least one real `captured` `BYBIT-FUTURES`/`book_snapshot_5` row in
      the new per-VM manifest shard (direct GCS/manifest read, never a fabricated/placeholder row). Never
      reclassify the existing all-`empty_confirmed`/`SOURCE_RETURNED_ZERO` rows without this proof. If the fresh
      runtime is still unproductive, inspect Bybit subscribe acknowledgements/rejections and file a follow-up code
      issue rather than muting DP-LIVE-004. Once verified, close the related follow-up in
      `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`. — **DONE 2026-08-21 (negative result, root-caused
      + follow-up filed, per the todo's own contingency)**: see Progress Log entry for full evidence. Confirmed
      still 0 captured rows (100% `empty_confirmed` across all 4 BYBIT-FUTURES data_types, stable across 5 repeated
      reads) via a targeted per-VM shard read (never a full-bucket per-VM merge — that path timed out/was too
      expensive for this bucket's 1700+ shards). Did NOT reclassify the existing rows. Root-caused via SSH log
      inspection + code read: Bybit's subscribe/unsubscribe ack frames are silently dropped, unlogged, in both
      `bybit_ws.py` and `bybit_futures_book_ticker_ws.py` — filed
      `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md` with 3 tracked
      todos. DP-LIVE-004 stays open/unmuted per the todo's own instruction — this is diagnosis, not closure.

## Progress Log

- **2026-08-22 — ruling D10 (Stale/wedged VM remediation)**: OPERATOR-RULED 2026-08-21 — APPROVED all three VM
  remediations (cycle BYBIT-FUTURES live VM via its registered launcher; inspect the deribit-sweep VM then delete only
  if confirmed hung; kill/relaunch the 2 stale mdps-features-live VMs, bounded backfill VMs finish with a corrective
  re-pass). This doc's own scope (BYBIT-FUTURES cycle) was already done pre-ruling (see the `[INFRA]`/`[DATA]` todos
  above, both `[x]`) — no retag needed here; the deribit-sweep and mdps-features-live remediations this ruling also
  covers live on their own sibling docs. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **dedup pass 2026-08-21**: found a 5th independent filing of this exact incident,
  `/plans/active/issues/dp_live_004_bybit_stale_vm_tarball_2026_08_21.md` (same VM →
  `mtds-live-cefi-consolidated-20260821-200626` replacement, same root cause), not caught by the 2026-08-21
  ag-closeout-audit consolidation above. Kept it `status: open` (not flipped to `superseded` like the other 3 —
  its decommission-step todo and its diagnostic detail aren't literally duplicated here yet) but marked its
  overlapping open todo `DUPLICATE OF` this doc's own todo 2 below, added it to `related:` above. It carries
  genuinely useful, not-yet-duplicated diagnostic progress on this doc's own open todo 2 below: on the post-fix replacement VM, BYBIT-FUTURES still shows 100% `empty_confirmed` across all 4
  MVP data types (zero `captured` rows) while every sibling venue on the same VM captures normally in the same
  window; universe resolution and `canonical_instrument_id` shape are both confirmed correct, so the remaining
  hypothesis space narrows to the connector's runtime subscribe-set / websocket-ack behavior — read that doc's "NEW
  FINDING 2026-08-21" entry in full before re-diagnosing todo 2 from scratch.
- **2026-08-21 (data_engineering, slot 19)**: independently reached the same "connector subscribe-ack behavior"
  conclusion the dedup-pass entry above flags — closed out both todos. Verified todo 2 via a targeted per-VM
  manifest-shard read (bypassing the earlier-noted rolling-buffer flush instability by reading the SAME target
  file 5x ~10s apart and confirming a stable, unchanging result — 100% `empty_confirmed` across all 4
  BYBIT-FUTURES data_types, cross-checked against a genuinely-`captured` sibling venue on the identical shard).
  Root-caused the negative result via SSH log inspection (zero subscribe/ack/reject log lines across the
  connector's full ~2h run) + a direct code read (both `bybit_ws.py` and `bybit_futures_book_ticker_ws.py` send
  `{"op":"subscribe",...}` with no logging, and their receive loops silently drop any frame that isn't a
  recognized tick payload — including Bybit's own ack control frames). Filed
  `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md` (3 tracked `[CODE]`/
  `[DATA]` todos) and updated `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`'s matching Finding-C
  nested todo with the same evidence. This doc's own scope (stale VM image) is now fully resolved — archiving per
  the plan-completion-and-archival-discipline HARD RULE (all todos `[x]`, unlocked). DP-LIVE-004 the ALERT
  condition stays open (tracked in the new follow-up doc), only THIS doc's narrower "stale image" diagnosis is
  closed.

- **2026-08-21 (infra, slot 8, applying operator ruling)**: Operator (Harsh, via `/ao-watchdog` interactive session,
  2026-08-21) APPROVED the `[OPERATOR]` todo. Cycled the VM via
  `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh --force` (`--force` required to bypass the
  launcher's singleton-RUNNING guard for a controlled overlap cutover — this flag only allows a second VM to exist
  concurrently, it never touches the existing VM; the old VM was never stopped/deleted). Tarball auto-verified fresh
  by the launcher's own `lc_verify_tarball_freshness` (market-tick-data-service @`f88dfdbd19db`, a descendant of the
  `5f88715e4b` fix). Replacement reached RUNNING with all 22 MVP CeFi shard processes up within ~5 min; SSH grep of
  the deployed source confirmed `_is_linear_derivative` present and wired into both `bybit_ws.py` and
  `bybit_futures_book_ticker_ws.py` (matches the fix commit, not the stale pre-fix source the original escalation
  found).
  **Duplicate-launch finding**: discovered a SECOND fresh replacement (`mtds-live-cefi-consolidated-20260821-200626`,
  created ~5 min before my own launch) already RUNNING with the identical fix — most likely an earlier crashed
  instance of this same dispatched task (boot response showed `already_in_progress: true` / `dispatch_reason:
  "resume"` before I ever launched anything), or a duplicate concurrent dispatch. Verified both were fully healthy,
  MVP-shard-complete, and fix-provenance-confirmed twins before acting; kept the older one (`-200626`, more
  accumulated capture history) as the canonical replacement and deleted my own newer duplicate
  (`mtds-live-cefi-consolidated-20260821-201205`) — safe because both were <15 min old, functionally identical, and
  streaming the same exchange feeds redundantly (no unique data lost). Anyone auditing VM-launch history for this
  incident should expect exactly one extra short-lived duplicate in the log, now cleaned up.
  **Manifest read caveat for whoever picks up todo #2**: a direct per-VM manifest-shard read
  (`_index/per_vm/mtds-live-cefi-consolidated-20260821-200626.parquet`, via
  `unified_trading_library.cloud_interface.download_from_storage` — never `gsutil`/`gcloud storage` subprocess calls,
  which the `pkill`/GCS-object-op guardrails on this host block) is NOT a stable point-in-time full history: repeated
  reads a few minutes apart on the same shard showed the total row count and even the presence of a given
  (venue, data_type) slice fluctuate (e.g. one read showed 492 `BYBIT-FUTURES`/`book_snapshot_5` rows, the next two
  showed 0) — consistent with the per-VM shard being a rolling buffer that a background consolidator periodically
  flushes/merges into the canonical manifest, not an appending ledger. A single 0-row read is NOT proof of
  non-capture; retry a few times or read the canonical merged manifest instead of concluding "unproductive" from one
  snapshot. Did not complete todo #2 myself (it is untagged-from-`[OPERATOR]`, `[DATA]`-scoped, separate acceptance
  criteria) — left it open and dispatchable; the replacement VM is confirmed RUNNING with the fix and producing
  `captured` (non-`empty_confirmed`) `book_snapshot_5` rows for other MVP venues (`ASTER`, `BINANCE-FUTURES`,
  `KRAKEN-FUTURES`, `OKX-FUTURES` all showed real `captured` counts in the same crosstab), so the pipeline mechanism
  itself is proven live — todo #2 just needs a clean, non-racing read to close out the `BYBIT-FUTURES` cell
  specifically.

- **2026-08-21 (data-pipeline-failure escalation `agt-793267`, slot 31)**: a 6th independent escalation dispatch
  fired for this exact identity (`DP_CRON_DID_NOT_FIRE` carrying `registry_id=DP-LIVE-004`, "last attempt 0.0h ago").
  Read-only `gcloud compute instances describe mtds-live-cefi-consolidated-20260817-025031` confirms the VM is
  unchanged: still `RUNNING`, still `creationTimestamp=2026-08-16T19:50:40.547-07:00` (== the pre-fix VM every prior
  dispatch identified). No new diagnosis needed and no code change to make — `market-tick-data-service@5f88715e4b`
  is already on `live-defi-rollout`; the sole remaining action is still the `[OPERATOR]` VM-cycle todo above, unactioned
  since 2026-08-20. Did not file a new issue doc. Note for whoever next triages the meta-pattern: 6 independent
  escalation dispatches have now fired for one already-tracked, already-`assigned_vm: planning`-dispatchable finding
  with no change in state between them — that repeat-dispatch-despite-already-tracked shape is itself covered by the
  open `dp_cron_did_not_fire_*` dedup issue docs (see `related:` above / `/codex/05-infrastructure/data-pipeline-alerts.md`'s
  2026-08-18 regression note), not something to re-diagnose here.
- **2026-08-21 (data-pipeline-failure escalation `agt-934add`, slot 31)**: a 5th independent escalation dispatch
  fired for this exact identity (`mtds-live-cefi-consolidated-20260817-025031` / `BYBIT-FUTURES` / `book_snapshot_5`,
  `DP_CRON_DID_NOT_FIRE` event carrying `registry_id=DP-LIVE-004`, "last attempt 0.0h ago" — the VM is still alive
  and attempting). The VM name is unchanged from every prior sighting, confirming it has **not** yet been cycled
  through the launcher — the P1 `[OPERATOR]` todo above is still the correct, only remaining action. No new code
  change: the fix (`market-tick-data-service@5f88715e4b`) is already on `live-defi-rollout`; nothing further to
  diagnose. Did not file a new issue doc — this is the same tracked condition as the 4 prior dispatches this doc
  already consolidates. Recording here rather than as a 5th duplicate.
- **ag-closeout-audit 2026-08-21 (cefi tranche, Phase 3 sweep)**: consolidated this doc's 3 sibling near-duplicates
  (identical VM + root cause + recommended action, filed by 4 independent escalation dispatches with zero
  cross-referencing) into this canonical doc — added `related:` links, a consolidation banner, and the 2 tracked
  `- [ ]` todos above (previously all 4 docs carried only unactionable prose "Recommended decision" text, and this
  doc specifically had zero `- [ ]` todos despite `assigned_vm: planning`, so nothing was actually dispatchable).
  Marked the 3 siblings `status: superseded` + `superseded_by:` pointing here, with their own evidence kept intact.
- 2026-08-20 (slot 32, escalation `agt-0d8048`): confirmed the MTDS worktree is
  clean and current on `live-defi-rollout`; inspected commit
  `5f88715e4b` and its book-connector tests; inspected the live VM and found the
  process and deployed source predate the fix. No code change was made because
  the root-cause fix is already shipped. The VM remains running; relaunch and
  post-relaunch captured-row verification are operator/infra follow-up work.
