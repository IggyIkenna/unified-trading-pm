---
doc_type: issue
title: rotate-exchange-keys registry lists ~15 venue secret names that don't match live GCP naming
summary:
  deployment-service/functions/rotate-exchange-keys/main.py's CEFI_KEY_PATTERNS-style venue list predates the two-axis
  secret-naming model (/codex/05-infrastructure/secret-manager-naming.md) — most entries (binance-api-key,
  deribit-api-key, okx-api-key, hyperliquid-api-key, etc.) don't match any real GCP secret, so key rotation likely
  silently no-ops for those venues. Found as a byproduct of the 2026-07-23 secret-naming migration; needs its own
  dedicated per-venue verification pass, not a drive-by fix.
status: resolved
nature: issue
asset_group: [infrastructure, cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [secret-manager, key-rotation, security, naming]
related: [/codex/05-infrastructure/secret-manager-naming.md]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
source: discovered while normalizing Betfair/Polymarket secret naming per operator request
resolved_by:
  "deployment-service@6eed099 (venue-list fix, 2026-07-26) + 2026-07-27 full live GCP verification (34/34 entries
  live-queried, 0 unverified) + invocation-path confirmed DEAD/UNWIRED (enable_secret_rotation=false in terraform, zero
  production impact) — see Progress Log"
locked_by:
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# rotate-exchange-keys registry lists stale venue secret names

## What was found

While fixing `PolymarketAdapterConfig`/`KalshiAdapterConfig`'s wrong secret-name defaults in execution-service (see
[`secret-manager-naming.md`](/codex/05-infrastructure/secret-manager-naming.md) § 1.2 / § 2.3), the same wrong
`polymarket-api-secret` name turned up in `deployment-service/functions/rotate-exchange-keys/main.py`'s venue key list.
Pulling on that thread: most of the ~29-entry list in that file predates the 2026-07-23 two-axis naming model and does
not match live GCP Secret Manager at all:

| Listed in rotate-exchange-keys                                                  | Real GCP shape (verified 2026-07-23)                                                               |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `binance-api-key` / `-secret`                                                   | `binance-{read,trade,write}-api-key` (+ `-secret` siblings for read/trade)                         |
| `deribit-api-key` / `-secret`                                                   | `deribit-{read,trade,write}-api-key` (+ `-secret` siblings for read/trade)                         |
| `okx-api-key` / `-secret`                                                       | No pooled/house OKX secret exists at all — client-scoped `exec-{client}-okx-*` only                |
| `hyperliquid-api-key` / `-secret`                                               | `hyperliquid-trade-key` (one JSON blob: private_key/wallet_address/main_wallet)                    |
| `polymarket-api-secret`                                                         | `polymarket-secret` (no `-api-` infix)                                                             |
| `coinbase-api-key` / `-secret`, `kraken-*`, `bitfinex-*`, `bitget-*`, `upbit-*` | **Not verified in this pass** — unknown if these venues have ANY provisioned secret under any name |

`bybit-api-key`/`-secret` and `betfair-session-token`/`kalshi-api-key` in the same list DO look consistent with real GCP
names, so this is not a "delete the whole file" situation — it's genuinely mixed.

## Why this matters

If `rotate-exchange-keys` is an active scheduled/triggered rotation function, every listed name that doesn't match a
real secret means rotation silently no-ops (or errors and is swallowed) for that venue — a rotation gap that could
persist indefinitely without anyone noticing, since "key rotation didn't happen" produces no loud failure signal by
default.

## What wasn't done and why

This session fixed the ONE line directly relevant to the Betfair/Polymarket normalization task (`polymarket-api-secret`
→ matches the real name only insofar as it was already being tracked) but did **not** touch the other ~13 stale entries.
Reasons:

- Key rotation is security-sensitive infrastructure — CLAUDE.md's hard-stop domain adjacency (wallet keys / force-push
  main are explicit human-only hard-stops; key rotation isn't listed but sits in the same risk class).
- Fixing 2 lines while leaving ~13 other equally-wrong lines untouched in the same list would be a misleading partial
  fix — a future reader would reasonably assume "this list is now correct" when it isn't.
- Several venues (`coinbase`, `kraken`, `bitfinex`, `bitget`, `upbit`) were never verified against live GCP in this pass
  — need a full per-venue GCP query before touching, same rigor as this session's Binance/Deribit/Bybit/
  Hyperliquid/Polymarket/Kalshi checks.

## Todos

- [x] [SCRIPT] P1. **[already covered by plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that
      doc for execution]** Verify every venue in `rotate-exchange-keys/main.py`'s key-pattern list against live GCP
      Secret Manager** (`central-element-323112`) — for each, confirm the referenced secret name(s) actually exist;
      produce a corrected list. — **PARTIAL (2026-07-26, slot-4): 10/15 venues classified with high confidence via
      cross-referenced evidence (codex doc + code-anchored secret-name usage), NOT a live `gcloud secrets` query — this
      worktree's service account lacks `secretmanager.secrets.list`/`.get` (verified: both calls return
      `PERMISSION_DENIED` for `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, the only credential
      available in this slot; `ikenna@odum-research.com` needs interactive reauth, unavailable non-interactively). 5
      venues (coinbase, kraken, bitfinex, bitget, upbit) remain genuinely UNVERIFIED — same as the original 2026-07-23
      pass, still `BLOCKED-CREDENTIALS`. See the Progress Log below for the full table + method.**
- [x] [SCRIPT] P1. **[already covered by plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that
      doc for execution]** Confirm whether `rotate-exchange-keys` is actually invoked on a schedule/trigger** (Cloud
      Scheduler / Cloud Function trigger config) — if it's dead/unwired like the Polymarket/Kalshi adapter stubs were,
      severity drops; if it's live, this is a real rotation gap needing prompt attention. — **NOT DONE (2026-07-26,
      slot-4): out of this pass's scope (only the venue-list fix below was dispatched); still open.**
- [x] ✅ [SCRIPT] P2. **DONE (2026-07-26, slot-4).** Fixed the corrected venue list in `rotate-exchange-keys/main.py`
      for the 10 confidently-classified venues (see Progress Log evidence table) — renamed-target entries updated to the
      verified real GCP name, `okx-*` (no-secret-exists) left with an explanatory comment, the 5 unverified venues
      (coinbase/kraken/bitfinex/bitget/upbit) left untouched with a comment citing this doc. Matches the two-axis model
      in `/codex/05-infrastructure/secret-manager-naming.md`. `deployment-service@6eed099`; 20/20 unit tests pass (2 new
      regression tests added); `quality-gates.sh` green.

## Progress Log

### 2026-07-27 (slot-5, data_engineering) — full live GCP verification (0 unverified) + invocation-path verdict

Dispatched as `cefi_satellite_ao_dispatch_batch1-028`. The 2026-07-26 pass (below) classified 10/15 venues via
code-cross-reference only because the worktree's identity lacked `secretmanager.secrets.list`/`.get`
(`PERMISSION_DENIED` for `unified-trading-sa`). That gap closed on 2026-07-27 — `unified-trading-sa` was granted
`secretmanager.viewer` + `secretmanager.secretAccessor` project-wide (see
[`orchestrator-cloud-identity-self-service.md`](/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md)).
This pass re-verified **every** entry directly against live GCP with
`gcloud secrets describe <name> --project=central-element-323112` run as
`unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (the gcloud active account defaulted to
`github-actions-deploy` in this worktree; switched via `gcloud config set account` before querying) — not
grep-against-a-list, an actual per-secret `describe` call for each of the 34 entries now in
`deployment-service/functions/rotate-exchange-keys/main.py`'s `_TRADE_KEY_PATTERNS` (grew from ~29 to 34 in the
2026-07-26 partial fix — copper/aster entries added). **0 unverified — every entry below has a live-queried verdict.**

**(a) Full per-entry table (34/34 entries, all live-verified 2026-07-27):**

| Entry in current `_TRADE_KEY_PATTERNS` | Live GCP result | Classification       | Note                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| -------------------------------------- | --------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `binance-read-api-key`                 | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `binance-trade-api-key`                | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `binance-write-api-key`                | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `binance-read-api-key-secret`          | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `binance-trade-api-key-secret`         | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `bybit-api-key`                        | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `bybit-api-secret`                     | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `deribit-read-api-key`                 | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `deribit-trade-api-key`                | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `deribit-write-api-key`                | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `deribit-read-api-key-secret`          | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `deribit-trade-api-key-secret`         | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `okx-api-key`                          | NOT_FOUND       | no-secret-exists     | Confirmed: only client-scoped `exec-{client}-okx-{api-key,api-secret,passphrase}` exist (24 secrets across 8 clients); no pooled/house secret.                                                                                                                                                                                                                                                                                                                                       |
| `okx-api-secret`                       | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `coinbase-api-key`                     | NOT_FOUND       | no-secret-exists     | **Now verified (was BLOCKED-CREDENTIALS).** Zero `coinbase-*` secrets of any name exist in the project.                                                                                                                                                                                                                                                                                                                                                                              |
| `coinbase-api-secret`                  | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `betfair-session-token`                | **NOT_FOUND**   | **no-secret-exists** | **Correction to 2026-07-26's "match" verdict** (that was code-only evidence, never live-checked). The 3 ad hoc Betfair auth-input secrets (`betfair-api-key`, `betfair-app-key`, `betfair-username`) DO exist, but the session-token itself — the one `execution_service/sports_execution/routing.py:209` and `instruments-service/.../adapters/betfair.py` actually fetch at auth time — is currently absent from Secret Manager.                                                   |
| `kalshi-api-credentials`               | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `hyperliquid-trade-key`                | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `aster-api-key`                        | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `aster-secret-key`                     | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `upbit-api-key`                        | NOT_FOUND       | no-secret-exists     | **Now verified (was BLOCKED-CREDENTIALS).** Zero `upbit-*` secrets exist.                                                                                                                                                                                                                                                                                                                                                                                                            |
| `upbit-api-secret`                     | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `kraken-api-key`                       | NOT_FOUND       | no-secret-exists     | **Now verified (was BLOCKED-CREDENTIALS).** Zero `kraken-*` secrets exist.                                                                                                                                                                                                                                                                                                                                                                                                           |
| `kraken-api-secret`                    | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `bitfinex-api-key`                     | NOT_FOUND       | no-secret-exists     | **Now verified (was BLOCKED-CREDENTIALS).** Zero `bitfinex-*` secrets exist.                                                                                                                                                                                                                                                                                                                                                                                                         |
| `bitfinex-api-secret`                  | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `bitget-api-key`                       | NOT_FOUND       | no-secret-exists     | **Now verified (was BLOCKED-CREDENTIALS).** Zero `bitget-*` secrets exist.                                                                                                                                                                                                                                                                                                                                                                                                           |
| `bitget-api-secret`                    | NOT_FOUND       | no-secret-exists     | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `polymarket-api-key`                   | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `polymarket-secret`                    | EXISTS          | match                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `copper-api-key`                       | **NOT_FOUND**   | **no-secret-exists** | **Correction to 2026-07-26's "match" verdict** (code-only evidence, never live-checked). Zero `copper-*` secrets of ANY name exist — including the code's actual runtime-fetched names `copper-sandbox-api-key`/`copper-sandbox-api-secret` (`execution-service/tests/integration/test_copper_custody_provider.py:38-40`), also verified NOT_FOUND live. Consistent with Copper being a client-provided May-23/June-1 cutover credential (`custody/factory.py`) not yet provisioned. |
| `copper-api-secret`                    | **NOT_FOUND**   | **no-secret-exists** | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `copper-org-id`                        | **NOT_FOUND**   | **no-secret-exists** | **Correction to 2026-07-26's "renamed-target→copper-org-id, match" verdict.** That exact target name does not exist live either.                                                                                                                                                                                                                                                                                                                                                     |

**Summary**: 20/34 match (live-confirmed correct), 14/34 no-secret-exists (0 renamed-target this pass — all prior
renames from 2026-07-26 already landed in the current list and verified as matches above). **3 corrections** to the
2026-07-26 code-only pass: `betfair-session-token`, `copper-api-key`/`copper-api-secret`, `copper-org-id` were
previously classified match/renamed-target on code evidence alone — live GCP proves none of these 4 names (nor Copper's
actual runtime-fetched sandbox names) currently exist. Not a `main.py` bug (those are still the _correct_ target names
per the code) — a genuine credential-provisioning gap: Betfair's session token and all Copper custody credentials are
unprovisioned in this project as of 2026-07-27.

**(b) Invocation-path verdict: DEAD / UNWIRED.** Exhaustive live query, all executed 2026-07-27 against
`central-element-323112`:

- `gcloud functions list --project=central-element-323112` (gen2, all regions) → 4 functions total
  (`ext-firestore-send-email-processqueue`, `run_jobs_tardis_data_loader`, `trigger-instruments-job`,
  `trigger-market-tick-cefi-job`). **No `rotate-exchange-keys` function deployed.**
- `gcloud scheduler jobs list --project=central-element-323112 --location=<region>` run across **all 27** GCP locations
  (enumerated via `gcloud scheduler locations list`) → 163 jobs project-wide, **zero** matching `rotate` or `secret` in
  the name.
- `gcloud run services list --project=central-element-323112` → no `rotate-exchange-keys` service.
- `gcloud iam service-accounts describe secret-rotator@central-element-323112.iam.gserviceaccount.com` → **exists**
  (displayName "Secret Rotation Cloud Function SA"), bound to `roles/pubsub.publisher` + `roles/secretmanager.viewer` —
  the exact SA `main.py`'s docstring names, but unused by any deployed compute.
- `gcloud pubsub topics describe secret-rotation-alerts` → **exists** (terraform-managed).
- Terraform source confirms this is by design, not drift: `deployment-service/terraform/gcp/secret_rotation.tf` creates
  the SA + PubSub topic + GCS source bucket unconditionally, but gates the actual
  `google_cloudfunctions2_function.rotate_exchange_keys` (line 87-127) and
  `google_cloud_scheduler_job.rotate_keys_daily` (line 129-154) resources behind
  `count = var.enable_secret_rotation ? 1 : 0`; `variables.tf:32-36` declares `enable_secret_rotation` with
  `default = false` ("Off by default"). Live state matches this exactly (SA + topic present, function + scheduler
  absent) — no drift between IaC and reality.

**Net effect on severity**: the venue-registry staleness this issue tracks currently has **zero production impact** —
`rotate-exchange-keys` has never been deployed to this project, so no code is actually reading any of these secret names
on a schedule. The correctness of `_TRADE_KEY_PATTERNS` matters only if/when an operator flips
`enable_secret_rotation = true` and applies the Terraform. This does not change the P1 priority of getting the list
correct before that flip (14/34 entries are still `no-secret-exists`, by design or by gap), but it does mean there is no
active/silent rotation gap today.

**Residual scope**: the venue-list itself was fixed to match on 2026-07-26 (`deployment-service@6eed099`); this pass
adds zero new code changes (both (a) and (b) were explicitly read-only per the plan todo) — it only closes the
verification gap and corrects 3 code-only classifications. If Betfair/Copper trading is expected to be live, the missing
`betfair-session-token` / Copper sandbox secrets are worth a follow-up credential-provisioning todo, but that is an
`[OPERATOR]` action (provisioning real trading credentials), not something this worktree's identity can self-service —
out of scope for this read-only verification pass.

### 2026-07-26 (slot-4, data_engineering) — venue-list fix + partial verification

Dispatched as `cefi_satellite_ao_dispatch_batch2-016` (P2, "fix the venue key-pattern list"), which assumed the batch1
verification todo above had already appended a full ~29-entry evidence table. It hadn't (batch1's todo was still
unchecked at dispatch time) — per this same plan's established precedent for a stale-but-bounded prerequisite (the
ASTER-regression todo ran its own ≤30min read-only prereq check rather than blocking), I performed the venue
classification myself, using two evidence sources since live `gcloud secrets list`/`describe` both returned
`PERMISSION_DENIED` for the only credential in this worktree:

1. `/codex/05-infrastructure/secret-manager-naming.md` — dated 2026-07-23 (3 days old), explicitly states it was
   "verified against live GCP inventory... 194 secrets."
2. Direct code grep for the literal secret name each service actually resolves at runtime (`service_config.py`,
   `credentials_registry.py`, adapter modules) — several of these carry their own "verified live 2026-07-23" comments,
   and one grep (`betfair-session-token`) overrode the codex doc's incomplete Betfair section (the codex doc only
   covered the 3 ad hoc auth-input secrets, not the session-token these produce).

**Evidence table** (15 venues / 29 entries in `_TRADE_KEY_PATTERNS`):

| Venue entry(ies) in old list      | Classification                       | Real GCP name(s)                                                                                                                        | Evidence                                                                                                                                                                    |
| --------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `binance-api-key` / `-secret`     | renamed-target                       | `binance-read-api-key`, `binance-trade-api-key`, `binance-write-api-key`, `binance-read-api-key-secret`, `binance-trade-api-key-secret` | codex §2.2 + `execution-service/service_config.py:464-474` ("verified live against GCP Secret Manager 2026-07-23")                                                          |
| `bybit-api-key` / `-secret`       | match                                | unchanged                                                                                                                               | codex §1 ("as of 2026-07-23"); `bybit-trade-api-key` exists in code as the _target_ shape but is explicitly "not provisioned yet" (`service_config.py:489-491`) — not added |
| `deribit-api-key` / `-secret`     | renamed-target                       | `deribit-read-api-key`, `deribit-trade-api-key`, `deribit-write-api-key`, `deribit-read-api-key-secret`, `deribit-trade-api-key-secret` | codex §2.2 + `service_config.py:476-484`                                                                                                                                    |
| `okx-api-key` / `-secret`         | no-secret-exists                     | n/a — client-scoped `exec-{client}-okx-*` only                                                                                          | codex §1                                                                                                                                                                    |
| `coinbase-api-key` / `-secret`    | **UNVERIFIED — BLOCKED-CREDENTIALS** | unknown                                                                                                                                 | no live access this pass, same as 2026-07-23                                                                                                                                |
| `betfair-session-token`           | match                                | unchanged                                                                                                                               | code-anchored: `execution_service/sports_execution/routing.py:209`, `instruments-service/.../adapters/betfair.py:70,98,159` — distinct from the 3 ad hoc auth-input secrets |
| `kalshi-api-key`                  | renamed-target                       | `kalshi-api-credentials`                                                                                                                | `execution_service/sports_execution/prediction_markets/kalshi.py:7,23` ("verified"), `credentials_registry.py:62`                                                           |
| `hyperliquid-api-key` / `-secret` | renamed-target (merged)              | `hyperliquid-trade-key` (one JSON blob)                                                                                                 | `service_config.py:516`, `hyperliquid_ccxt.py:49`                                                                                                                           |
| `aster-api-key`                   | match                                | unchanged                                                                                                                               | `canonical_mappings.py:459` (`DATA_SOURCE_TO_SECRET["aster"]`)                                                                                                              |
| `aster-api-secret`                | renamed-target                       | `aster-secret-key`                                                                                                                      | codex §1                                                                                                                                                                    |
| `upbit-api-key` / `-secret`       | **UNVERIFIED — BLOCKED-CREDENTIALS** | unknown                                                                                                                                 | no live access this pass                                                                                                                                                    |
| `kraken-api-key` / `-secret`      | **UNVERIFIED — BLOCKED-CREDENTIALS** | unknown                                                                                                                                 | no live access this pass                                                                                                                                                    |
| `bitfinex-api-key` / `-secret`    | **UNVERIFIED — BLOCKED-CREDENTIALS** | unknown                                                                                                                                 | no live access this pass                                                                                                                                                    |
| `bitget-api-key` / `-secret`      | **UNVERIFIED — BLOCKED-CREDENTIALS** | unknown                                                                                                                                 | no live access this pass                                                                                                                                                    |
| `polymarket-api-key`              | match                                | unchanged                                                                                                                               | codex §2.3                                                                                                                                                                  |
| `polymarket-api-secret`           | renamed-target                       | `polymarket-secret`                                                                                                                     | `polymarket.py:70` ("`secret_name_api_secret: str = "polymarket-secret"`")                                                                                                  |
| `copper-api-key` / `-secret`      | match                                | unchanged                                                                                                                               | codex §2.1                                                                                                                                                                  |
| `copper-organization-id`          | renamed-target                       | `copper-org-id`                                                                                                                         | `test_copper_custody_provider.py:40` (`_fetch_secret("copper-org-id")`)                                                                                                     |

**Fix applied**: `deployment-service/functions/rotate-exchange-keys/main.py`'s `_TRADE_KEY_PATTERNS` updated per the
table above (10 venues fixed/confirmed-match; `okx` left with an explanatory comment; the 5 unverified venues left
untouched with a comment citing this doc). `tests/unit/test_rotate_exchange_keys.py` updated (6 fixtures that used the
now-dead `binance-api-key` literal switched to `binance-trade-api-key`) plus 2 new regression tests locking in the
stale-name/ renamed-name behavior. `bash scripts/quality-gates.sh` green; 20/20 unit tests pass.

**Residual scope, not closed by this pass** (both still open above): (a) the 5 unverified venues need a credentialed
`gcloud secrets list --project=central-element-323112` pass (or an operator running it) before their entries can be
trusted; (b) the invocation-path (schedule/trigger) check was never attempted this pass.

## Codex SSOTs

- `/codex/05-infrastructure/secret-manager-naming.md` — the two-axis naming model this registry needs to match.
