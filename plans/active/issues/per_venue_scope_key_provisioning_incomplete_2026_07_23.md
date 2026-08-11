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
context_scope:
  [
    /codex/05-infrastructure/secret-manager-naming.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
    execution-service/execution_service/trade_execution/base_adapter.py,
  ]
drift_direction: advance-code
depends_on: []
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
| Bybit                           | 🟡 Code ready, not provisioned | Currently one unscoped `bybit-api-key`/`bybit-api-secret`; execution-service now prefers `bybit-trade-api-key`/`bybit-trade-api-key-secret` and falls back to the unscoped pair automatically — see checklist below                                                                                                                                                          |
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

- `bybit-trade-api-key` — the new key's API key value
- `bybit-trade-api-key-secret` — the new key's API secret value

No code change or deploy is needed once these exist — `execution-service`'s `_load_venue_trade_credentials` already
checks for them first and only falls back to the current unscoped `bybit-api-key`/`bybit-api-secret` if they're absent
(**shipped `execution-service@3f550b14` "feat(credentials): wire Bybit trade-scope secret with safe fallback",
2026-07-24 — corrected 2026-07-25, was stale "commit pending push" text; verified reachable on
`origin/live-defi-rollout`**). The switch to the scoped key happens automatically the next time the service reads Secret
Manager.

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
- [ ] [HUMAN] P1. **RULED 2026-07-28 (applying the operator's general theme — recurring cost here is $0, this is a
      security-hardening control reducing a compromised-key's blast radius, and the theme favors full completion of
      exactly this kind of item — DIRECTION APPROVED, proceed).** Create `bybit-trade-api-key`/
      `bybit-trade-api-key-secret` in GCP per the checklist above — the one remaining step to actually complete Bybit's
      scope split. The decision to do this is no longer open; only the credential-creation ACTION remains, and only the
      operator's own Bybit exchange login can perform it (no cloud identity or automation can create a new exchange-side
      API key) — that is why the tag stays `[HUMAN]` rather than moving to an AO execution tag.
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
- [ ] [HUMAN] P3. **Decide whether to provision Upbit/Kraken/Bitfinex/Bitget credentials**, given none of the 4
      currently have any live trading volume. **NOT part of the 2026-08-08 "build both" ruling** — that answer named
      only OKX/Hyperliquid scope-separation and the Aster adapter; this credential-provisioning question stays an open
      priority call (also needs the operator's own exchange logins, same class as the Bybit item above).

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
