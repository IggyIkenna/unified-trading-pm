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
resolved_by: "prediction_satellite_ao_dispatch_batch6-abb85b31cce7 (slot 12, 2026-08-09)"
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
- [x] ✅ [DATA] P1. **DONE 2026-08-09 — `execution-service@9f25d0e5`.** RULED 2026-08-06 (operator): "NO — do not
      touch the live exchange." The 2026-07-28 ruling's scope limit stood; placing a real order on
      `api.elections.kalshi.com` stayed unauthorized, so the original verification ask
      (`kalshi_live_capture_regression_and_drift_2026_07_13.md`) was fulfilled via the ruling's own non-live path
      instead: `TestKalshiRealCredentialWiringNonLiveVerification`
      (`execution-service/tests/sports_execution/unit/test_kalshi_adapter.py`) loads the REAL
      `kalshi-api-key-id`/`kalshi-private-key-pem` secrets through the SAME `SportsExecutionRouter` +
      `_LIVE_VENUE_CONFIGS` production wiring `sports_factory.py` uses, drives the REAL RSA-PKCS1v15
      request-signing code with that key, and exercises order submit → fill/ack → position update with the aiohttp
      transport swapped for an in-process fake — zero network calls reach any Kalshi host, live or demo. Manually
      run (outside the QG pytest network sandbox, which blocks the real Secret Manager call — the test correctly
      self-skips under `quality-gates.sh`, same as every other `requires_credentials` test in this repo) against
      the real provisioned credentials: both tests PASS, including a genuine 256-byte RSA-2048 signature on every
      request (not `_build_kalshi_headers`'s silent SHA-256-fallback for an unparseable key). Kalshi's demo host
      (the sandbox/testnet option this todo's text suggested) was not attempted — untested whether it accepts the
      same live-account credentials; the mocked-response path fully satisfies the ruling on its own. Full evidence
      + reasoning: `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5. (repo: execution-service)

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
- **RESOLVED 2026-08-09 (slot 12, `prediction_satellite_ao_dispatch_batch6-abb85b31cce7`)**: the sync gap flagged by the
  2026-08-07/2026-08-09 audit passes is now closed (batch6 todo 5 mirrors this doc's 2026-08-06 ruling). Both todos in
  this doc are now `[x]` — Option C (mocked-response verification) executed and passing against the real provisioned
  credentials, `execution-service@9f25d0e5`. Full evidence in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
  todo 5. `status: resolved`. Not archived in this same commit (per the archival-discipline rule against combining a
  checkbox flip with a `git mv` in one commit) — archival-eligibility is a separate follow-up for the next hygiene
  sweep / `/archive-candidates-audit` pass.
