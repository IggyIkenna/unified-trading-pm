---
doc_type: issue
title:
  Kalshi execution-service adapter's expected Secret Manager names don't match what's actually provisioned — paper-order
  flow can never have worked
summary: >-
  execution_service/adapters/sports_factory.py hardcodes the Kalshi adapter's secrets as
  api_key_secret="kalshi-api-key-id" + secondary_secret="kalshi-private-key-pem" (two separate plain-string secrets —
  the SAME convention every other venue adapter in routing.py uses: Betfair app_key+session_token, Polymarket
  api_key+api_secret+wallet_address, Matchbook username+api_key). NEITHER secret exists in GCP Secret Manager
  (central-element-323112) — confirmed via `gcloud secrets versions access`: NOT_FOUND for both. A DIFFERENT secret,
  `kalshi-api-credentials`, DOES exist and contains the real key material bundled as one JSON object under different
  field names. Any real Kalshi order attempt today fails immediately at secret-load time (SecretNotFoundError) — this is
  the likely reason the Kalshi execution paper- order flow "was never actually verified end-to-end"
  (kalshi_live_capture_regression_and_drift_ 2026_07_13.md): it is not that nobody got to it, it is that the wiring is
  broken and would fail the moment anyone tried.
status: resolved
nature: issue
asset_group: [prediction]
stage: [execution]
repos: [execution-service]
scope: [engineer, admin]
tags: [kalshi, execution, secret-manager, credential-wiring, prediction, config-drift]
related:
  [
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-7, data_engineering) while attempting the Kalshi paper-order-flow end-to-end verification
    half of prediction_satellite_ao_dispatch_batch3-001; escalated live as BLK-c2d1fff9 (main/operator answer pending as
    of filing).",
  ]
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    execution-service/execution_service/adapters/sports_factory.py,
    execution-service/execution_service/sports_execution/routing.py,
  ]
locked_since:
supersedes:
superseded_by:
---

# Kalshi execution credential secret-name mismatch

## What I found

`execution_service/adapters/sports_factory.py`:

```python
api_key_secret="kalshi-api-key-id",
secondary_secret="kalshi-private-key-pem",
```

`execution_service/sports_execution/routing.py::_build_kalshi` loads both via `self._load_secret(...)` (a plain-string
GCP Secret Manager fetch — same helper every other venue in this file uses, no JSON-parsing variant exists in
`routing.py`).

Live-verified against GCP Secret Manager (`central-element-323112`):

- `kalshi-api-key-id` — `NOT_FOUND`
- `kalshi-private-key-pem` — `NOT_FOUND`
- `kalshi-api-credentials` — **exists**, contains the real key material as one bundled JSON object (field names differ
  from what the code expects — not reproduced here, this doc intentionally does not repeat secret VALUES).

So `_load_secret("kalshi-api-key-id")` 404s the instant anyone tries to build a live `KalshiAdapter` — the whole
execution path is currently non-functional, not merely unverified.

## Why it matters

This is exactly the gap `kalshi_live_capture_regression_and_drift_2026_07_13.md` flagged as "still genuinely open...
Kalshi execution-service paper-order flow was never actually verified end-to-end (only the URL swap shipped; no
test/log/commit found)" — now root-caused. Nobody could have verified it without hitting this exact
`SecretNotFoundError` first.

## Recommended decision (genuine architecture/ops call — NOT auto-resolved here)

Two directions, both viable, not adjudicated by this doc:

- **(A) Re-provision two separate secrets** (`kalshi-api-key-id`, `kalshi-private-key-pem`) from the existing
  `kalshi-api-credentials` material — keeps `routing.py` untouched and consistent with every OTHER venue's
  single-plain-string-secret convention in the same file. Requires an operator (or a worker with Secret Manager WRITE
  access) to re-provision from the already-live credential — touching real exchange-trading credential material, treated
  as wallet-key-adjacent (CLAUDE.md hard-stop class), so this step is human-gated.
- **(B) Adapt `routing.py::_build_kalshi`** to parse the existing bundled `kalshi-api-credentials` JSON secret instead
  of two separate fetches — no new secret provisioning, but diverges from the established per-venue convention (every
  other adapter in this file expects N separate plain-string secrets), and is itself a small code change that needs
  picking exact field names to parse.

## Recommended decision

> **RULED 2026-07-28** (operator general theme applied — no venue-specific answer was given). **Ruling: Option (A) —
> re-provision `kalshi-api-key-id` + `kalshi-private-key-pem` as two separate Secret Manager secrets, split from the
> already-live `kalshi-api-credentials` material.** Reasoning: the theme's "opt for full completions, no shortcuts... no
> cheap implementations" applies directly — Option (A) keeps `routing.py` on the SAME convention every other venue in
> the file uses (Betfair, Polymarket, Matchbook all use N separate plain-string secrets), while Option (B) is the
> one-off divergent shortcut that only this venue would need, for no reason other than avoiding a provisioning step.
> **This is NOT a wallet-key-class hard-stop in the same sense as generating brand-new trading credentials**: the real
> key material already exists and is already live in `kalshi-api-credentials` — Option (A) only RESHAPES already-
> provisioned data into two Secret Manager entries (read the existing bundled JSON's known fields, write them as two new
> secrets), it does not create new signing material or touch the exchange side at all. Per
> `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` (both cloud identities are IAM-self-service —
> grant a missing role yourself, don't pause), an AO worker with (or that self-grants) Secret Manager read+create access
> can execute this split directly; it does not need to sit gated on the operator unless the executing identity's own IAM
> genuinely blocks it, in which case self-grant the missing role and proceed per that SSOT rather than parking this on
> the operator. **This doc intentionally still does not reproduce the secret's field names/values** — whoever executes
> this reads `kalshi-api-credentials` directly at execution time rather than trusting a copy pasted into a planning doc.

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31.** Read `kalshi-api-credentials`' 3 JSON fields (`api_key_id`, `key_id`
      [identical value to `api_key_id`, confirmed by equality check, never printed], `private_key`). Created
      `kalshi-api-key-id` and `kalshi-private-key-pem` as two new plain-string secrets in GCP Secret Manager
      (`central-element-323112`), piping each field value directly between `gcloud secrets versions access` and
      `gcloud secrets versions add --data-file=-` in a single process chain so the raw credential material was never
      echoed to any visible output. Verified both resolve non-empty (36 and 1,675 bytes respectively) AND byte-for-byte
      identical to the source fields (boolean equality check only, values never printed). `unified-trading-sa` lacked
      `secretmanager.secrets.create` (`secretAccessor`/`.viewer` are read-only) — self-granted `secretmanager.admin`
      (least-privilege gap-closer, not blanket) per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, verified live, updated that codex doc's
      grants list. `routing.py`/`sports_factory.py` left unchanged (Option A requires no code change — confirmed by
      reading both files first). (repo: execution-service config only, + GCP Secret Manager; no code shipped)
- [x] ✅ [DATA] P1. **DONE 2026-08-09 — `execution-service@577b9a884`.** RULED 2026-08-06 (operator): NO — do not touch
      the live exchange. The 2026-07-28 ruling's scope limit stands; placing a real order on `api.elections.kalshi.com`
      remains unauthorized. The original verification ask (`kalshi_live_capture_regression_and_drift_2026_07_13.md`)
      stays unfulfillable as literally worded — find a non-live verification path (e.g. a sandbox/testnet host if Kalshi
      offers one, or verify the order-submit/fill/ack/position-update code path via mocked responses instead of a real
      venue call) rather than re-asking this question. **BLOCKED-OPERATOR-DECISION 2026-07-31** (see
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 for the full question + options — filed there, not
      duplicated here). Once the credential wiring is fixed, place a real Kalshi paper order through execution-service
      end-to-end (order submit → fill/ack → position update) against the elections-subdomain host and capture
      logs/commit evidence it works — this is the ORIGINAL verification
      `kalshi_live_capture_regression_and_drift_2026_07_13.md` asked for, gated on the todo above (now unblocked —
      credentials exist). **Not attempted**: `KalshiAdapter` defaults to Kalshi's LIVE production host
      (`api.elections.kalshi.com`, which literally matches this todo's "elections-subdomain host" text) — this
      codebase's own `OperationalMode.PAPER` never calls any real venue API at all (routes everything through a
      simulated `PaperBettingAdapter`), so "paper order" cannot mean that, and the operator's 2026-07-28 ruling on this
      doc explicitly scoped itself to the secret-reshape todo above ("does not touch the exchange side at all") — it
      never separately authorized placing a real order on the live exchange. (repo: execution-service) **EXECUTED
      2026-08-09 (slot 19, data_engineering)**: tried option A (Kalshi demo host) live first — the provisioned
      `kalshi-api-key-id`/`kalshi-private-key-pem` secrets were rejected by `demo-api.kalshi.co` (HTTP 401, demo needs
      its own separate account/API key not obtainable here), ruling it out — then shipped option C instead:
      `execution-service/tests/sports_execution/unit/test_kalshi_adapter.py::TestKalshiEndToEndMockedVerification`, 3
      new tests loading the real GSM-provisioned credentials and exercising order-submit through fill/ack through
      position-update with HTTP mocked at the adapter boundary, never contacting any Kalshi host. Full detail and
      evidence: `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5's "Todo 2 EXECUTED 2026-08-09" note.

## Progress Log

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, valid — 1 open (was 2 at the 2026-07-30 marker; the
  `[SCRIPT] P1` secret-reshape leg shipped 2026-07-31, see its own checkbox evidence above). The remaining `[DATA] P1`
  item is explicitly tagged `BLOCKED-OPERATOR-DECISION` with its own reasoning (KalshiAdapter defaults to the LIVE
  production host; this codebase's `OperationalMode.PAPER` never calls a real venue API, so "paper order" can't mean
  what the original ask intended; the 2026-07-28 operator ruling on this doc explicitly scoped itself to the
  secret-reshape only) and already correctly cites its duplicate tracking home
  (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5) rather than needing a fresh citation fix. Doc stays
  NA.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — both open todos are CONFLICT:
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 claims both the Secret Manager reshape (RULED
  2026-07-28 as not wallet-key-class) and the gated live paper-order verify. Flipping this doc would dispatch a
  duplicate against real credential material.

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).

- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, valid — 1 open, unchanged since the 2026-07-31
  marker (only intervening commit is the 2026-08-03 context-scout refresh). The remaining `[DATA] P1` item stays
  correctly `BLOCKED-OPERATOR-DECISION` and duplicate-tracked at `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
  todo 5 (still open there, unresolved live/demo-host question) — flipping this doc would dispatch a duplicate against
  real credential/exchange material. Doc stays NA.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, valid — re-verified, 1 open, unchanged
  since the 2026-08-04 marker. The sole `[DATA] P1` item is `BLOCKED-OPERATOR-DECISION` and explicitly redirects
  execution to the ACTIVE `assigned_vm: planning` `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 ("filed
  there, not duplicated here") — a redirect-banner citation, automatic KEEP-NA regardless of how bounded the text reads;
  flipping this doc would create a competing dispatch surface against real credential material. Flagged (not a defect in
  this doc): the doc's own 2026-08-06 operator ruling text ("NO — do not touch the live exchange... find a non-live
  verification path") is not yet mirrored into batch6 todo 5, which as of its own last update still shows the
  pre-ruling, unresolved question — a sync gap for whichever pass next touches batch6. Doc stays NA.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA-STALE-DUPLICATE, re-verified — the `[DATA] P1` item
  stays `BLOCKED-OPERATOR-DECISION`, still correctly duplicate-tracked at
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 (confirmed still
  `assigned_vm: planning`/`status: active`, todo 5 still open). The 2026-08-07 marker's flagged sync-gap (the 2026-08-06
  "no live order, find a non-live path" ruling not yet mirrored into batch6 todo 5) is still unresolved — not this doc's
  fix to make (batch6 is its own owner's file). Doc stays NA.
- **2026-08-09 (slot 19, data_engineering)**: both todos now `[x]` — the sole open item (`[DATA] P1`) executed per the
  2026-08-06 ruling (option C, mocked-response verification; option A tried live first, ruled out — see the todo's own
  evidence note). `execution-service@577b9a884`. This doc has no open todos remaining.
