---
name: fund-administration-service — real POD integration (crypto-only, spot + derivatives tracks)
overview:
  Replace the fund-administration-service's mock AML/KYC gate + NAV-strike resolution with real HTTP / file-drop
  integration against POD, the regulated fund administrator for **crypto-denominated** Pooled funds. Two fund tracks sit
  under POD — crypto-spot and crypto-derivatives — with different risk, leverage, and reporting profiles but the same
  POD-side mechanics. TradFi Pooled funds use a separate administrator (see
  `tradfi_fund_administrator_selection_2026_04_22.plan.md`).
type: mixed
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22

completion_gates:
  code: C5
  deployment: D3
  business: B3

repo_gates:
  - repo: fund-administration-service
    code: C0
    deployment: D3
  - repo: unified-api-contracts
    code: C0
    deployment: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
  - repo: unified-trading-pm
    code: C0
    deployment: none

depends_on:
  - fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md
  - fund_administration_persistence_swap_in_2026_04_22.plan.md
---

# Context

fund-administration-service Phase 2 shipped with stubbed provider interfaces:

- `AmlKycGate` — auto-approves every subscription in staging.
- `NavProvider` — returns a single hard-coded NAV snapshot.
- `SettlementExecutor` — logs withdrawal request but doesn't actually settle.

Each is a Protocol. Real POD integration means replacing the stub impls with real ones that talk to POD's API (or SFTP
file-drop if that's POD's integration mode).

**SCOPE: CRYPTO-ONLY.** POD administers crypto-denominated pooled funds. This plan covers BOTH crypto tracks:

- **Crypto-spot fund** — BTC / ETH / major-cap tokens held at the custodian (Copper reference); no leverage; venue set
  is spot exchanges (Coinbase, Binance spot, Bybit spot) + on-chain wallets. Subscription accepts fiat or stablecoins;
  NAV-strike cadence typically daily.
- **Crypto-derivatives fund** — BTC / ETH perpetuals and dated futures on CeFi venues (Binance USDM, Hyperliquid, Bybit,
  OKX) and on-chain perps; leverage capped per mandate; the custodian holds margin in a segregated collateral wallet and
  executes via API keys provisioned by POD to Odum. Separate share class / separate regulatory filings from the
  crypto-spot fund.

Both tracks share POD's subscription / redemption / NAV / AML mechanic — they differ in the custodian-side collateral
posture and the venue set. One `fund-administration-service` deployment serves both; the `fund_id` + `share_class`
determine which track the flow applies to.

TradFi Pooled funds use a separate administrator; that is a different plan.

# How the prospect lands on the right track

The public questionnaire at `/questionnaire` (`unified-trading-system-ui/app/(public)/questionnaire/page.tsx`, see also
`unified-trading-system-ui/lib/questionnaire/types.ts`) captures 6 base axes from prospects:

- `categories` — CeFi / DeFi / TradFi / Sports / Prediction
- `instrument_types` — spot / perp / dated_future / option / lending / staking / lp / event_settled
- `venue_scope` — venue pack preferences
- `strategy_style` — ml_directional / stat_arb / arbitrage / carry / event_driven / market_making / vol_trading
- `service_family` — IM / DART / RegUmbrella / combo
- `fund_structure` — SMA / Pooled / NA

**Fund-type resolution** (new this plan):

1. `service_family = IM` + `fund_structure = Pooled` → Pooled engagement; POD administrator.
2. Within the Pooled track, `categories` + `instrument_types` picks the fund:
   - `(CeFi ∪ DeFi) × {spot, lending, staking, lp}` → **crypto-spot fund**
   - `(CeFi ∪ DeFi) × {perp, dated_future, option}` → **crypto-derivatives fund**
   - `TradFi × *` → out-of-POD-scope; redirect to TradFi-admin follow-up
3. Mixed selections (client wants both spot and derivatives) offer two share classes within the Pooled engagement, one
   per track. Captured in the questionnaire response as two rows or documented as a second-call disambiguation.

Add a regulatory-notes free-text field to the questionnaire so prospects can flag jurisdiction-specific concerns (e.g.
"our end-investors are US-based; need 506(c) exemption" or "we're an Australian fund, need AUSTRAC registration") for
the compliance team to review pre-second-call. Responses feed into the pre-second-call prep pack.

Briefings cross-ref — the copy already landed and references a "fund administrator":

- `/briefings/investment-management` — Pooled section mentions qualified 3rd-party custodian (Copper for crypto) and
  "regulated fund administrator" generically. Do NOT name POD publicly.
- `/briefings/regulatory` — mentions Copper for crypto as well. Generic administrator wording.

Plan: update those two briefings as part of this plan to split the crypto track explicit: "crypto-spot fund" vs
"crypto-derivatives fund", with their different venue packs + leverage profiles. See Scope § Briefings copy below.

# Unknowns to resolve before coding

- [ ] **Crypto-spot and crypto-derivatives as separate legal vehicles or two share classes of one?** POD will likely
      advise on the fund structure to match the jurisdictions of the two asset-class tracks. (Typically: two separate
      sub-funds under a Cayman SPC umbrella, each with its own custody + NAV.)
- [ ] Does POD expose a REST API, an SFTP file-drop, or both? Confirm with compliance / POD account manager.
- [ ] What AML/KYC does POD do vs what does Odum do? Responsibility matrix for investor onboarding, refresh,
      suspicious-activity reporting. Typically: POD owns investor-side KYC; Odum has limited visibility into investor
      identity beyond the client-reporting entitlement.
- [ ] NAV strike cadence — daily for crypto-spot is standard; crypto-derivatives needs mark-to-market on perpetual
      funding so daily strike possibly with intraday refresh. Confirm.
- [ ] Subscription / redemption settlement SLA — confirm grace-period default (currently 5 days in fund-admin scaffold).
      Derivatives redemptions that force position-unwind may need longer grace period; confirm.
- [ ] Custodian handoff — POD coordinates with Copper on asset movement. Odum's role in that handoff is? (For
      derivatives, Copper wallet → exchange margin wallet is a pre-trade flow the trading desk cares about.)
- [ ] Regulatory disclosures — the crypto-derivatives fund has different risk factors than crypto-spot. Offering
      document prep is a compliance task, not this plan's code scope.

# Scope

## Contracts + discovery

- [ ] Obtain POD integration spec (API docs or SFTP schema). File into
      `/codex/14-playbooks/external-integrations/pod.md` (internal-only). Document BOTH fund tracks.
- [ ] Add `PodClient` Protocol to fund-administration-service (not UAC — POD is internal-specific). Single client;
      per-fund-track dispatch via `fund_id`.
- [ ] Add `FundTrack` enum to UAC: `CRYPTO_SPOT`, `CRYPTO_DERIVATIVES`, `TRADFI_*` (placeholders for tradfi plan). Each
      `FundAllocation` / `AllocatorSubscription` carries a track tag via the fund_id → track map.
- [ ] Secret Manager: API key / SFTP credentials provisioned via deployment-service. One set of POD creds covers both
      tracks (POD treats them as one counterparty).

## Implementation

- [ ] `RealAmlKycGate` — calls POD for investor-level AML check. Same interface for spot + derivatives.
- [ ] `RealNavProvider` — pulls NAV from POD at the published strike cadence per fund_id; caches with TTL. Derivatives
      fund gets intraday refresh support.
- [ ] `RealSettlementExecutor` — initiates the withdrawal (POD executes on custodian; fund-admin waits for confirmation
      webhook / polls SFTP).
- [ ] Webhook receiver for POD → fund-administration-service callbacks (if REST) OR SFTP poller (if file-drop).
- [ ] Circuit breaker: if POD is unreachable, subscriptions queue as PENDING rather than fail. Alerts ops.

## Questionnaire wiring

- [ ] Add `regulatory_notes` free-text field to `QuestionnaireResponse` UAC type + UI form.
- [ ] Backend route that resolves questionnaire → fund-track recommendation (helper function in
      `unified-trading-library` or a service-level util). Returns `CRYPTO_SPOT` / `CRYPTO_DERIVATIVES` / `BOTH` /
      `TRADFI_PENDING`.
- [ ] Admin view `/admin/organizations/[id]/questionnaire` surfaces the regulatory-notes + fund-track recommendation so
      the compliance team has the prospect's self-declared context ahead of the second call.

## Briefings copy

- [ ] `unified-trading-system-ui/lib/briefings/content.ts` — IM briefing Pooled section: split mention into "crypto-spot
      fund" vs "crypto-derivatives fund" with their distinct venue + leverage + NAV-cadence profiles. Keep "POD" off the
      public copy; use "regulated fund administrator".
- [ ] `/investment-management` marketing page: if the page surfaces fund-type detail, add the same split; otherwise link
      to `/briefings/investment-management` and leave marketing page at headline level.
- [ ] `/questionnaire`: the form already captures categories + instrument_types; add a `regulatory_notes` textarea + a
      small inline note that the (categories × instrument_types) selection will map to a specific fund track + that
      compliance reviews the regulatory_notes ahead of the second call.

## Tests

- [ ] Unit: each Real\* impl with `responses` library faking POD. Cover both fund tracks.
- [ ] Integration (staging): stub POD sandbox if POD provides one; otherwise gate behind manual-test flag.
- [ ] Playwright: `/questionnaire` E2E covering (a) crypto-spot-only selection, (b) crypto-derivatives-only selection,
      (c) both-tracks selection, (d) TradFi selection → redirect-to-TradFi-admin message.

## Commercial + compliance

- [ ] Legal agreement with POD confirmed + e-signed before production traffic.
- [ ] Compliance sign-off on AML responsibility matrix.
- [ ] Separate offering documents for crypto-spot and crypto-derivatives funds.

## Out of scope

- TradFi Pooled administrator integration — separate plan.
- IM SMA flow — doesn't touch POD (clients hold their own venue accounts).
- Retail / non-accredited investor onboarding — all funds are accredited/professional-investor-only.

# Commercial gate

Production rollout (D5) gated on first signed IM Pooled mandate + POD contract effective. Crypto-spot fund is likely the
first live track since it's simpler; crypto-derivatives follows once spot is operational and the derivatives offering
document is signed off.
