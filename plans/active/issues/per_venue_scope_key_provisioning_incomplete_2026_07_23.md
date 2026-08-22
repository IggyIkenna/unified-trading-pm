---
doc_type: issue
title: Per-venue read/trade/withdraw scope key provisioning stalled at 2/10 venues
summary: >-
  Phase 2.A/2.C of the archived api_keys_wallets_accounts_readiness plan split into an enforcement half (shipped —
  execution-service's AdapterScope/ScopedCLOBAdapter) and a Secret-Manager-provisioning half (operator-only, marked
  BLOCKED-OPERATOR at archival). Verified live against GCP 2026-07-23 — only Binance + Deribit actually have the
  {venue}-{read,trade,write}-api-key triple; the other 8 venues named in the original plan (Bybit, OKX, Hyperliquid,
  Aster, Upbit, Kraken, Bitfinex, Bitget) still have at most one unscoped/client-scoped key. No active plan currently
  owns finishing this rollout.
status: open
nature: issue
asset_group:
  [cefi] # corrected 2026-07-30 (/ag-closeout-audit infra, Phase 0.3 Orthogonality HARD CHECK) -- was
  # [cefi, infrastructure], a genuine mistag: every one of the 10 named venues (Binance/Deribit/Bybit/OKX/Hyperliquid/
  # Aster/Upbit/Kraken/Bitfinex/Bitget) is a CeFi venue, `repos:` is execution-service, `parent_epic` is
  # execution_master, and `tags:` already carries `cefi`. `infrastructure` read as a second peer-tranche marker only
  # because the mechanism is Secret Manager; the infra tranche's own charter is generic repo/dependency/terraform/org
  # hygiene, not per-venue trading credentials. Already covered by cefi_satellite_ao_dispatch_batch3_2026_07_26.md (now archived at /plans/archive/2026_07/), so
  # this retag creates no new orphan (linkage check re-run, still 0).
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [secret-manager, security, scope-separation, cefi]
related:
  [
    /codex/05-infrastructure/secret-manager-naming.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
  ]
created: 2026-07-23
last_updated: 2026-08-21
author: unknown
parent_epic: execution_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
source:
  discovered while investigating a prior session's "R8" reference during secret-naming reconciliation — that label was a
  misnomer (R8 in the source plan is an unrelated Pyth-on-Solana oracle smoke test); the actual items are Phase 2.A
  ("Per-venue sub-key provisioning") and 2.C ("Per-scope key separation in adapters")
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/secret-manager-naming.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
    execution-service/execution_service/trade_execution/base_adapter.py,
  ]
---

# Per-venue read/trade/withdraw scope key provisioning stalled at 2/10 venues

## Correction to a prior mislabel

A prior session's investigation referred to this as "the R8 plan." That's wrong — R8 in
`plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md` is Phase 4.E, "Pyth-on-Solana real-data
smoke," unrelated to credential scoping. The actual items are **Phase 2.A** ("Per-venue sub-key provisioning") and
**Phase 2.C** ("Per-scope key separation in adapters"). Use this doc's title/tags to find it going forward, not "R8."

## What's actually shipped vs. not

**Enforcement (Phase 2.C) — shipped, live**: `execution-service`'s `AdapterScope` + `ScopedCLOBAdapter`
(`base_adapter.py`, commit `e3f447e37`) — `get_order_adapter(venue, scope="read"|"trade"|"withdraw")` raises
`UnsupportedOperationError` if a read-scope adapter attempts `place_order`. 20 unit tests, all passing per the original
plan's verification note.

**Provisioning (Phase 2.A) — 2/10 venues as of 2026-07-23, Bybit's code wired same day**: the plan's intended shape was
`<venue>-<scope>-{api-key,api-secret,passphrase}` per venue, for 10 venues (Bybit, Deribit, Binance, OKX, Hyperliquid,
Aster, Upbit, Kraken, Bitfinex, Bitget). Verified live against GCP Secret Manager (`central-element-323112`) 2026-07-23:

| Venue                           | Read/trade/write split?        | Real shape                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Binance                         | ✅ Yes                         | `binance-{read,trade,write}-api-key` (+ secret siblings for read/trade)                                                                                                                                                                                                                                                                                                      |
| Deribit                         | ✅ Yes                         | `deribit-{read,trade,write}-api-key` (+ secret siblings for read/trade)                                                                                                                                                                                                                                                                                                      |
| Bybit                           | 🟡 Half-provisioned 2026-08-21 | `bybit-trade-api-key` now EXISTS in GSM (created since the table above was last verified) but `bybit-trade-api-key-secret` does NOT — execution-service's fallback requires BOTH scoped values non-None before using them, so it correctly still falls back to the unscoped `bybit-api-key`/`bybit-api-secret` pair today (both present, verified working via a live probe 2026-08-21/22). See checklist below — only the `-secret` half remains. |
| OKX                             | ❌ Different model             | `exec-{client}-okx-*` (client-scoped only, no pooled/house key at all) — the read/trade/write split doesn't apply the same way to a client-scoped venue; needs its own design, not a copy of the Binance/Deribit pattern                                                                                                                                                     |
| Hyperliquid                     | ❌ Different model             | One wallet-style JSON blob `hyperliquid-trade-key` (EIP-712 agent-wallet signing, not a REST key pair) — "read vs. trade vs. withdraw" would need a different mechanism (e.g. separate agent wallets with different on-chain authorizations), not three secrets                                                                                                              |
| Aster                           | ❌ No execution adapter at all | `aster-api-key`/`aster-secret-key` exist in GCP but are consumed ONLY for MTDS market-data collection — `execution-service`'s venue-dispatch (`factory.py`'s `CCXT_VENUES`/`DIRECT_REST_VENUES`/`TRADFI_VENUES`) has no `aster` entry and no `aster_*.py` adapter file exists. Scope separation is moot until an execution adapter is built — see the build-scope note below |
| Upbit, Kraken, Bitfinex, Bitget | ❌ Zero credentials            | Confirmed 2026-07-23 — no secret under any name exists in GCP for any of these 4 venues (not even an unscoped key). Matches the plan's own 2026-05-17 note that Bitfinex/Bitget were `BLOCKED-CREDENTIALS`; Upbit/Kraken have adapter code and factory dispatch but nothing to authenticate with                                                                             |

The plan's own archival note flagged this as `[BLOCKED-OPERATOR]` — "Agent cannot provision venue sub-keys. Operator
must complete before May-23 cutover" — and it appears that operator step was only carried out for 2 of the 10 named
venues.

## Bybit — provisioning checklist (operator action required)

Create these two secrets in GCP Secret Manager (project `central-element-323112`), sourced from a Bybit API key scoped
to **trading permissions only, no withdrawal permission** (the whole point of the split — a compromised trade-scope key
can't move funds out):

- `bybit-trade-api-key` — the new key's API key value — **DONE, exists in GSM as of 2026-08-21** (verified via
  `gcloud secrets versions list`, ENABLED, non-empty).
- `bybit-trade-api-key-secret` — the new key's API secret value — **still absent as of 2026-08-21/22** (confirmed:
  `gcloud secrets versions list bybit-trade-api-key-secret` returns `NOT_FOUND`). Only this half remains.

No code change or deploy is needed once these exist — `execution-service`'s `_load_venue_trade_credentials` already
checks for them first and only falls back to the current unscoped `bybit-api-key`/`bybit-api-secret` if they're absent
(**shipped "feat(credentials): wire Bybit trade-scope secret with safe fallback", 2026-07-24 — corrected 2026-08-19
(`/plan-reconcile execution_master`): the previously-cited SHA `execution-service@3f550b14` is a pre-rewrite artifact of
the 2026-08-05 history rewrite (`git merge-base --is-ancestor 3f550b14 origin/live-defi-rollout` fails) — the same
commit (identical message + author date 2026-07-24 11:30:36) is reachable today as `execution-service@da5803912`, since
re-provenanced as `execution-service@d473a6477` ("chore(provenance): re-provenance da580391..."); both verified
`git merge-base --is-ancestor` ancestors of `origin/live-defi-rollout` 2026-08-19**). The switch to the scoped key
happens automatically the next time the service reads Secret Manager.

## Aster — execution adapter doesn't exist; build-scope estimate

Aster has no execution path today, so "add scope separation" doesn't apply until an adapter is built. Good news: **CCXT
already has a working `aster` connector** (`ccxt.async_support.aster`, standard `apiKey`/`secret` `requiredCredentials`
— no Hyperliquid-style special handling needed), so this would follow the same CCXT-wrapper pattern already used for
`upbit_ccxt.py` (403 lines) / `hyperliquid_ccxt.py` (503 lines), NOT a from-scratch native REST client like
`bitfinex_native.py`/`bitget_native.py` (~370-420 lines each, built natively because CCXT support was inadequate for
those two at the time).

Scope for a real `aster_ccxt.py`:

- New adapter file mirroring `upbit_ccxt.py`'s shape (place/cancel order, fetch balance/positions/fills, sim-mode
  support).
- Add `"aster"` to `factory.py`'s `CCXT_VENUES` + a dispatch branch in `_create_ccxt_adapter()`.
- Add an `aster` case to `live_execution_handler.py`'s `_load_venue_trade_credentials` (the secrets already exist:
  `aster-api-key`/`aster-secret-key`, just need a service_config.py field + wiring — no new GCP provisioning needed for
  a first, unscoped-key version).
- Unit tests mirroring the existing CCXT-adapter test suites (~35-40 tests based on `test_hyperliquid_ccxt.py`'s count).
- Estimated at roughly 1 day of focused work (refactor-tier — following an established pattern, not novel design).

## Why this matters

If per-scope key separation is a genuine security control the operator still wants (the stated rationale: "a compromised
read-key shouldn't be able to withdraw funds"), most target venues currently have no scope separation at the credential
level — the `ScopedCLOBAdapter` enforcement layer works, but there's only one key to enforce scopes _against_ for those
venues, so a compromised single key still has full withdraw capability regardless of what scope the caller requests.

## What this issue does NOT resolve

- Whether OKX/Hyperliquid warrant their own scope-separation designs, and what those designs should look like.
- Whether Upbit/Kraken/Bitfinex/Bitget are still wanted as trading venues at all, given zero credentials months after
  the original plan targeted them.
- Whether building the Aster execution adapter is worth prioritizing given it currently has zero trading volume (no
  adapter exists to have generated any).

All three are real design/priority calls, not something determinable from code or docs alone.

## Todos

- [x] [SCRIPT] P2. **Verify Upbit/Kraken/Bitfinex/Bitget's live GCP secret shape** — done 2026-07-23, zero credentials
      confirmed for all 4 (table above).
- [x] [AGENT] P2. **Wire Bybit's trade-scope credential lookup with safe fallback** — execution-service
      `_load_venue_trade_credentials` now prefers `bybit-trade-api-key`/`-secret`, falls back to the unscoped pair; 3
      new unit tests.
- [ ] [HUMAN] P1. **RULED 2026-08-21 (D19, OPERATOR-RULED): `bybit-trade-api-key-secret` still absent as of
      2026-08-21/22 — blocked on the operator's own Bybit exchange login** (no cloud identity or automation can
      create a new exchange-side API key). Create `bybit-trade-api-key-secret` in GCP (the paired
      `bybit-trade-api-key` now exists, confirmed 2026-08-21 — see checklist above; only the `-secret` half
      remains) per the checklist above — the one remaining step to actually complete Bybit's scope split. **RULED
      2026-07-28** (applying the operator's general theme — recurring cost here is $0, this is a
      security-hardening control reducing a compromised-key's blast radius, and the theme favors full completion of
      exactly this kind of item — DIRECTION APPROVED, proceed). The decision to do this is no longer open; only the
      credential-creation ACTION remains. **[plan-reconcile 2026-08-19: reordered so the action leads physical
      line 1 — task_template.md §3 line-1-completeness; the prior ordering put the entire actionable instruction on
      physical line 3, invisible to any first-line-only reader/parser.]**
- [x] [SCRIPT] P2. EXTRACTED — na-eligibility-audit 2026-08-16, conflict-cleared, live todo now
      `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` item 8. Original text: **MTDS's own key-reload preflight
      (`unified_trading_library.startup_validation.validate_api_keys_for_venues`, called via
      `api_key_reloader.py`/`tick_data_handler.py._start_key_reloader`) has NO fallback to the unscoped `bybit-api-key`
      — unlike `execution-service`'s already-shipped fallback (item above).** Found 2026-08-14 launching the CeFi Tardis
      equity-perp backfill (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`):
      `cefi-bybit-2026-heavy-20260814-151808` failed all 16/16 date-chunks with
      `StartupValidationError: Missing API keys for venues [...]: ["bybit (secret: 'bybit-trade-api-key')"]` even though
      `bybit-api-key` (the unscoped credential, created 2026-07-23) exists and is presumably still a real, usable key.
      `validate_api_keys_for_venues` (`startup_validation.py:225-233`) does a single fixed
      `secret_client.get_secret(secret_name)` per venue via `get_required_secrets(venues)` with no fallback attempt —
      the venue is BLOCKED-CODE-GAP for market-data capture, not BLOCKED-CREDENTIALS (a working credential exists, MTDS
      just can't find it under the name it's hardcoded to look for). Fix: mirror execution-service's
      `_load_venue_trade_credentials` fallback pattern in `validate_api_keys_for_venues` (or in `get_required_secrets`
      itself) — try the scoped name first, fall back to the unscoped `bybit-api-key` pair. **Not fixed in this pass**
      (equity-perp backfill session deferred BYBIT and proceeded with OKX-SWAP/BINANCE-FUTURES, which have working
      scoped keys) — a proper fix needs a test + QG run, not a rushed mid-launch patch. Repo: unified-trading-library.
- [ ] [BACKEND] P2. **Decide on OKX/Hyperliquid's scope-separation design**, if wanted at all, since neither fits the
      Binance/Deribit pattern. **APPROVED (operator, 2026-08-08)**: "Build both: OKX/Hyperliquid scope-separation AND
      the Aster execution adapter" — retagged `[HUMAN]`→`[BACKEND]`. This item's own text already narrows the design
      space (see table above): OKX is client-scoped only (`exec-{client}-okx-*`, no pooled/house key) so a read/trade/
      write split needs a per-client design, not a copy of Binance/Deribit's pooled-key pattern; Hyperliquid is a
      wallet-style EIP-712 agent-wallet blob (`hyperliquid-trade-key`), not a REST key pair, so scope separation there
      means separate agent wallets with different on-chain authorizations, not three Secret Manager entries. Scope the
      exact per-venue mechanism (client-scoped OKX sub-keys vs. multi-wallet Hyperliquid) before estimating — this is a
      genuine build task once scoped, not a config change. Repo: execution-service.
- [x] ✅ [BACKEND] P2. **Build the Aster execution adapter** — extracted 2026-08-09 to
      `cefi_satellite_ao_dispatch_batch14_2026_08_09.md` todo 1 for AO dispatch (parent_epic: execution_master), now
      archived at `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch14_2026_08_09.md`; shipped 2026-08-09 —
      `execution-service@05b425e6` ("feat(execution): add Aster CCXT execution adapter"), verified reachable on
      `origin/live-defi-rollout`. New `aster_ccxt.py` (477 lines) mirrors `upbit_ccxt.py`'s CCXT-wrapper shape
      (perpetual-only per UAC `ASTER -> {"PERPETUAL"}`, apiKey/secret credentials, Binance-futures symbol convention);
      `"aster"` wired into `factory.py`'s CCXT dispatch + Venue mapping; `aster-api-key`/`aster-secret-key` wired into
      `live_execution_handler.py`'s credential loader via new `service_config.py` fields; 44 unit tests added
      (`test_aster_ccxt.py`); `quality-gates.sh` green (sentinel=05b425e6c313cb87d606893e544ab6c0fb9ff587). **Remaining
      open count in this doc: 3, all human/operator-gated** — the `[HUMAN] P1` Bybit key-creation todo (operator's own
      exchange login), the `[BACKEND] P2` OKX/Hyperliquid scope-separation todo (operator-approved to build but still
      gated on an unresolved per-venue design call), and the `[HUMAN] P3` Upbit/Kraken/Bitfinex/Bitget-provisioning todo
      (open priority call) — none touched by this Aster shipment.
- [ ] [HUMAN] P3. **DEFERRED-BY-DESIGN — RULED 2026-08-21 (D110, ADOPTED-REC): DECLINE** — no demand signal;
      provisioning Upbit/Kraken/Bitfinex/Bitget credentials ahead of need has ongoing credential-hygiene cost. None
      of the 4 currently have any live trading volume. **NOT part of the 2026-08-08 "build both" ruling** — that
      answer named only OKX/Hyperliquid scope-separation and the Aster adapter.

## Codex SSOTs

- `/codex/05-infrastructure/secret-manager-naming.md` § 2.2 — the live read/trade/write split pattern for
  Binance/Deribit, and the note distinguishing this real pooled/house pattern from the dead per-client
  `exec-{client}-{venue}-{read,trade,withdraw}-*` design the archived plan originally also described.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — One item is genuinely
  human-only (operator's own exchange-login credential creation, doc-confirmed); other two are explicit design/priority
  judgment calls the doc itself labels as such.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged from prior scout — still accurate: the
  secret-naming SSOT, the archived source plan, and the `AdapterScope`/`ScopedCLOBAdapter` enforcement file).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict, all
  3 open todos still explicitly [HUMAN]-tagged (one operator-only credential creation, two stated design/priority
  calls); unchanged since.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; all
  3 open todos remain explicitly `[HUMAN]`-tagged (one operator-only exchange-login credential creation, two stated
  design/priority calls). Independently reconfirmed by today's
  `/plans/archive/2026_08/ag_closeout_audit_cefi_parked_2026_08_06.md`.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 3 open items: 1 credential-blocked (Bybit key, operator's own
  exchange login), 2 operator design/priority calls.
- **na-corpus-digest-closeout 2026-08-08 (item 29 — OKX/Hyperliquid + Aster)**: operator ruled "Build both:
  OKX/Hyperliquid scope-separation AND the Aster execution adapter." Retagged both todos `[HUMAN]`→`[BACKEND]` and
  spelled out the concrete build scope (already mostly pre-specced in this doc's own analysis sections). The
  Upbit/Kraken/Bitfinex/Bitget credential-provisioning question was NOT part of this ruling — split into its own
  `[HUMAN] P3` todo, still an open priority call.
- **na-corpus-digest-closeout 2026-08-08 (item 33 — Bybit key creation)**: operator answer: "Operator will create it
  later — leave blocked for now." Doc status re-confirmed accurate as-is — the `[HUMAN] P1` todo already correctly
  states only the operator's own Bybit exchange login can perform this, direction already approved 2026-07-28, action
  still pending. No change needed.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — whole-doc flip fails on 3 of 4 open
  items. Checked carefully against cheat-sheet rulings #1 (IAM self-service) and #9 (self-service sibling-precedent) as
  directed: NEITHER applies — the `[HUMAN] P1` Bybit item needs the operator's own EXCHANGE-side API-key login (not a
  GCP IAM role grant; no cloud identity/service-account can create a third-party exchange trading key), so ruling #1 is
  a category mismatch, and there is no adjacent-script `--flag` precedent making ruling #9 fit either. The
  `[BACKEND] P2` OKX/Hyperliquid item is operator-approved to build but its own text still asks the worker to "scope the
  exact per-venue mechanism... before estimating" — an unresolved design call (task_template.md's "figure out how X
  should look" trap), not yet bounded. The `[HUMAN] P3` Upbit/Kraken/Bitfinex/Bitget item is an explicit, undispatched
  priority call. Only the `[BACKEND] P2` Aster-adapter item (scope fully specced: mirror `upbit_ccxt.py`, wire
  `factory.py` + `live_execution_handler.py`, ~35-40 tests, ~1 day) is independently bounded — noted as a future
  split-candidate for a dedicated single-item AO doc, not split this round (out of this audit's scope, which
  reclassifies existing docs whole, not decomposes them). No conflict found in
  [`cefi_satellite_ao_dispatch_batch9_2026_08_07.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md)
  (lists this doc as "no new work landed," consistent).
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms
  2026-07-30/08-04/08-06/08-07/08-08 verdicts. Item 1 needs the operator's own Bybit exchange-side API-key login (not
  GCP-IAM-self-serviceable); items 2-3 are credential/design-scoping calls.
- **review (slot-4) 2026-08-09**: reconciled the line-163 Aster-adapter pointer —
  `cefi_satellite_ao_dispatch_batch14_2026_08_09.md`'s todo 1 landed (`execution-service@05b425e6`, verified reachable
  on `origin/live-defi-rollout`, `quality-gates.sh` green per that plan's Progress Log). Flipped the todo to `[x]` with
  the verified commit + evidence in place of the "see that doc" indirection. Remaining open count in this doc: **3, all
  human/operator-gated** (Bybit key creation `[HUMAN P1]`, OKX/Hyperliquid scope-separation design `[BACKEND P2]` gated
  on an unresolved design call, Upbit/Kraken/Bitfinex/Bitget provisioning `[HUMAN P3]`) — unchanged by this Aster
  shipment.
- **na-eligibility-audit 2026-08-16** [body-hash:65255e7671dec15f]: RECLASSIFY-SPLIT — extracted bounded item(s) 8 to `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` (see that plan + this doc's own checkbox citations for exact mapping). 3 items remain genuinely NA (2 [HUMAN] exchange-login-only credential/priority calls, 1 [BACKEND] P2 design call gated on an unresolved per-venue mechanism choice). Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **plan-reconcile execution_master 2026-08-19**: adversarial verification of this doc's cited evidence (this epic's
  only `parent_epic: execution_master`-matched child doc). Found + fixed one stale-SHA citation: the Bybit fallback
  todo's evidence cited `execution-service@3f550b14`, which `git merge-base --is-ancestor` shows is NOT an ancestor of
  `origin/live-defi-rollout` — it is a pre-2026-08-05-history-rewrite artifact of the same commit, now reachable as
  `da5803912`/`d473a6477` (verified). Corrected the citation in place. Also fixed a task_template.md §3
  line-1-completeness defect on the `[HUMAN] P1` Bybit todo (the entire actionable instruction sat on physical line 3
  behind a bolded "RULED..." qualifier on line 1) — reordered so the action leads. Independently re-verified the 2
  other cited SHAs (`e3f447e37`, `05b425e6`) — both genuine ancestors of `origin/live-defi-rollout`, no drift. The 3
  remaining open todos (`[HUMAN] P1` Bybit, `[BACKEND] P2` OKX/Hyperliquid, `[HUMAN] P3` Upbit/Kraken/Bitfinex/Bitget)
  are unchanged and correctly still open — no new done-but-unchecked or contradiction found. See the epic's own
  `## Report` section for the full run's findings.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; 3 open items unchanged (Bybit key
  creation needs the operator's own exchange login; OKX/Hyperliquid scope-separation design call approved-to-build
  but still unscoped; Upbit/Kraken/Bitfinex/Bitget provisioning is an open priority call).
- **D12/D19 dispatch, execution-service (slot 6) 2026-08-21/22**: Live-verified this doc's central Bybit claim
  against real GCP Secret Manager state (never printed secret values, only presence/`gcloud secrets versions
  list` state + a direct call to `_CredentialsMixin._load_venue_trade_credentials(config, "bybit")`). Two findings:
  (1) `bybit-trade-api-key` now EXISTS (was absent when this doc's table was last verified 2026-07-23) — the Bybit
  provisioning checklist above and the `[HUMAN] P1` todo text updated to reflect only the `-secret` half remains.
  (2) Confirmed live, end-to-end, that the scoped-name fallback works exactly as designed: since
  `bybit-trade-api-key-secret` is still absent, `_load_venue_trade_credentials` logged
  `"Bybit trade-scope secret 'bybit-trade-api-key' not found -- falling back to unscoped 'bybit-api-key'"` and
  returned both values non-empty from the unscoped `bybit-api-key`/`bybit-api-secret` pair — the exact behavior this
  doc's "Bybit — provisioning checklist" section already documented, now confirmed against live GSM state rather
  than just read from the code. No code change needed; this was a verification pass (D12/D19 operator-ruling
  dispatch), not a new fix.
- **2026-08-21 — ruling D19 (Bybit trade-scoped key)**: OPERATOR-RULED 2026-08-21 — partially present: bybit-trade-api-key exists, bybit-trade-api-key-secret does NOT. EXECUTABLE half: confirm the code's scoped-name fallback works with bybit-api-secret (confirmed live, see entry above); the missing secret stays a credential-ask (operator's Bybit login). Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-21 — ruling D110 (Dormant CEX venue credentials)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Decline — no demand signal; provisioning ahead of need has ongoing credential-hygiene cost. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
