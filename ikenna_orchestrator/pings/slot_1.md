# Slot 1 — Main Orchestrator Intra-Side Ledger

## [slot 1 main] DAY-3 REASSIGNMENT v2 — full slot stacks for May-23 cutover — 2026-05-13 ~19:00 UTC

**Operator direction**: _"anything within 23rd may cutover so that each slot has a decent list because we are moving at 200 ai days per day"_

**Pace**: ~200 cal AI-days/side/day combined = each slot ships ~20-25 cal AI-days/day at sub-agent fan-out compression. So each slot needs a stacked queue, not a single assignment.

### Status changes since DAY-3 v1 (per latest LDR + agent pings)

- ✅ Slot 3 SHIPPED: defi_legacy_blank_reclassification (599,486 rows corrected via `7319d4ac` + UAC@ca62a19 + UTL@b0c38a21 + IS@fafaa0c). Now free for next pickup.
- ✅ Slot 5 SHIPPED: TradFi Item 1 (UAC@37f6dfd + UAC@6110d05) + Item 2 Phase 1A (UAC@2ac74e2) + Phase 1B (UAC@dd407ae). Now free for Phase 3-5 cascade + new pickups.
- ✅ Slot 4 CLAIMED: 3 sports classifier gap issues (per `ee21e9c2`); still has propagation chain Phase 3.1-3.N + Phase 4 + PART C + bucket provisioning handshake in queue.
- ✅ MASSIVE wallet_treasury work shipped: Phase 4.A-D (`73af5895`) + Phase 5.A-5.I (`35ac17e2`) + Phase 8.A-D (`96fe459a`). Slot 6 (Phase 1) + Slot 7 (Phase 3) still doing the pulled-forward work.
- ✅ Writegate Phase 6.9 [PM] P0 checkbox FLIPPED (`06688e7f`).
- ✅ Sports Phase 3.5 SHIPPED + api_football pre-flight P1 FIXED (`54e8d253`).

### Full slot stacks (priority-ordered; each slot rolls through their queue)

#### Slot 1 main (me)
1. ✅ This reassignment ping + coordination + cross-side acks
2. **`governance_qg_automation_gaps_post_cutover_2026_05_12.md`** (~3 cal days, P1) — HARD RULE automation + QG ratchet authoring
3. **Phase 6.9 workspace QG flip-sweep** (~2 cal days, serial after 6.6/6.7/6.8 PART B fully ships) — Gate 4 firing
4. **Master plan refresh** + active-plan-inventory regenerator (EOD)
5. **`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`** (~1.8 cal days, P2) — IF Harsh-side doesn't take

#### Slot 2 (currently on defi_classifier_missing_catalog_crossref)
1. **Verify scope remaining**: slot 3 shipped `EXPECTED_PRE_VENUE_LAUNCH` for 599k pre-launch rows. Remaining for slot 2 = **Wave 3 per-instrument catalog cross-ref** for the 789k cefi cleanup (post-launch rows that need `EXPECTED_INSTRUMENT_NOT_LISTED` based on `instruments-service` catalog `available_from`/`available_to`).
2. **`wave2_polymarket_record_captured_from_counts_2026_05_09.md`** Polymarket subset (~2 cal days, P1) — Phases 1/2/4/5 shared foundation + Phase 3 Polymarket-only
3. **`solana_defi_coverage_gaps_2026_05_13.md`** — successor plan B (Lido/Marinade/Jito LST capture) — 1 of 5 successor plans
4. After: pick from Solana plan A/C/D/E or `code_freeze` Phase 2 entry tasks

#### Slot 3 (just freed — 4 deliverables shipped in 1h)
1. **`emerging_perp_venue_adapters_broken_2026_05_13.md`** P0 — own filed issue, manifest evidence loaded (ASTER 0%, HYPERLIQUID 68% failure across 5 venues)
2. **`batch_live_symmetry`** Tab 1 — codex `cefi-batch-live.md` + `mode-axis-discipline.md` (Harsh audit slot deadline-eligible ask)
3. **`solana_defi_coverage_gaps`** successor plan A (full audit context already loaded)
4. **`code_freeze` Phase 2** entry tasks (post-freeze-gate cutover work)

#### Slot 4 (claimed sports gaps; still has propagation chain queue)
1. **3 sports classifier gap issues** (already claimed `ee21e9c2`):
   - `sports_classifier_sfi_footystats_fixture_pin_2026_05_13` (P1)
   - `sports_classifier_player_values_cadence_2026_05_13` (P1)
   - `sports_classifier_weather_no_fixture_2026_05_13` (P1)
2. **Propagation chain Phase 3.1-3.N** — spawn 6 sub-agents (delta_one + calendar + onchain + volatility + sports + commodity); Option A runtime comparison
3. **Phase 4 ml-training + ml-inference** propagation (post-Phase 3)
4. **PART C writegate 2.A** — MDPS 4-state output routing (parallel with Phase 3)
5. **6-bucket provisioning** (3 envs × 2 clouds with ≥7yr retention) — slot 8 awaiting handoff
6. **Sports/prediction phantom apply-flips on VMs** (slot 4 owns per work-split)

#### Slot 5 (TradFi Item 1+2 Phase 1A+1B shipped — Phase 3-5 cascade pending)
1. **TradFi Item 2 Phase 3** — one-shot manifest migration script `migrate_tradfi_expiry_schema.py` (~0.5 cal days)
2. **TradFi Item 2 Phase 4** — Downstream consumer cascade (instruments-service futures factory → MTDS Databento bridge → mtds-tradfi-staleness → features-service → strategy-service `FuturesRollInstruction`) ~1-2 cal days
3. **TradFi Item 2 Phase 5** — QG ratchet asserting all 5 required kwargs on `CanonicalFuturesContract(...)` ~0.5 cal days
4. **`solana_defi_coverage_gaps`** successor plan C (own pickup if interested)
5. After: `sports_retired_data_types_code_cleanup_2026_05_13.md` (new plan filed 18e971df)

#### Slot 6 (wallet_treasury Phase 1 — Real HMAC withdrawal chain)
1. **wallet_treasury_post_cutover Phase 1** — Cloud-KMS withdrawal signing + deployment-api `/api/clients/{id}/withdrawal/{id}/approve` + 8 unit tests (~3.2 cal days)
2. **4 DeFi-specific alert codes** (`DEFI_AAVE_UTILIZATION_SPIKE` / `FUNDING_RATE_FLIP` / `FEATURE_STALE` / `WEETH_DEPEG`) — features-onchain producer-side emission wiring + alerting-service rule wiring (~1 cal day)
3. **`basefc_validation_flip_2026_05_10.md`** — ClassVar enforcement × 75 BaseFeatureCalculators (~3 cal days, P1) — features-service maintainer scope
4. After: any remaining wallet_treasury phases or features tail work

#### Slot 7 (wallet_treasury Phase 3 — Audit log immutability)
1. **wallet_treasury_post_cutover Phase 3** — GCS Object Versioning + 7-year retention lock on audit bucket + Cloud Audit Logs wire-in + 4 compliance tests (~1.6 cal days)
2. **Treasury rollup endpoint `/api/treasury/rollup`** — deployment-api Phase 3.D ~1-2 cal days (collision with slot 8 cross_cutting #4 RESOLVED)
3. **DART manual-trade UX refactor** (`dart_manual_trade_ux_refactor_2026_05_13`) — Sheet → dedicated `/dart/terminal/manual/*` route extraction (1,256-line panel) + unified `lib/api/dart-client.ts` + Playwright e2e (~2.4 cal days, P1)
4. After: any remaining wallet_treasury phases

#### Slot 8 (slot 3 took emerging_perp; needs new direction)
1. **`AUDIT_pre_may_8_cleanup_2026_05_13`** (P1, from harsh audit slot orphan-plan assignment)
2. **Wave 3 per-instrument catalog cross-ref for 789k cefi cleanup** (coordinate with slot 2; either slot can lead — partition by venue)
3. **`solana_defi_coverage_gaps`** successor plan D
4. After: any new findings or pickup from reserve queue

#### Slot 9 (api_football_phase_3b_3c may be obsolete; verify first)
1. **VERIFY**: `api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md` — sports Phase 3.5 just shipped (`54e8d253`); may be done. Read issue + check status before picking up.
2. **If done**: pick `sports_retired_data_types_code_cleanup_2026_05_13.md` (new plan from `18e971df`)
3. **OR**: `solana_defi_coverage_gaps` successor plan E
4. After: any remaining sports / sports_master deferred items

### Items NOT assigned (awaiting operator decision)

- **`defi_recursive_borrow_archetypes` Solidity (`RecursiveLeverageReceiver.sol`) + execution-service orchestrator/tracer** — Harsh audit slot ask: 1 Solidity + 1 execution-service slot for May-23 push, OR descope. **OPERATOR DECISION PENDING.**
- **`batch_live_symmetry` Tab 2/3** — Tab 1 is slot 3; Tab 2/3 still need second slot allocation (could come from Harsh-side or another Ikenna slot once their queue clears).

### Cross-side notes

- Harsh-side has ~9 idle slots per shift-end LEDGER `PM@6bf6e932` — symmetric capacity. If they want to absorb `codex_doc_currency` (item 4 in their pull-forward) or `batch_live_symmetry` Tab 2/3, all good.
- 117 UTL test failures debt = Harsh's per their own ownership claim; not pulling.

### What this looks like by end of cycle (May-15 target)

If every slot rolls through 2-3 items in its stack (which is realistic at 200 cal AI-days/side/day), we ship ~30-40 distinct items across both sides → wipes out the 542 cal AI-day backlog and pulls additional reserve work forward. **No descope. Perfect cutover.**

---


## [slot 1 main] CORRECTIONS to DAY-3 reassignment — 2026-05-13 ~18:00 UTC

**Operator caught mis-marks based on agent ping responses**. Fixes:

### Correction 1: Issues I assigned were ALREADY RESOLVED

| Slot | Previous direction | Actual state |
|------|-------------------|--------------|
| Slot 8 (a) | `uac_normalize_aster_ticker_missing_2026_05_13.md` | ✅ RESOLVED `d8290295` — archived |
| Slot 8 (b) | `standings_entity_gcs_ambiguity_2026_05_13.md` | ✅ RESOLVED `01ad724a` (entity=standings/ is api_football, NOT SFI; no GCS action) — archived |
| Slot 3 | "in flight ~1-2h sports corrector" | ✅ DONE at `7319d4ac` — `DEFI_VENUE_LAUNCH_DATES` + corrector shipped + 599,486 defi rows corrected |

### Correction 2: Phase 2 (Copper/CEFFU) is NOT our blocker — it's CLIENT-SIDE

Per harsh-side 1M-context audit slot ping `[2026-05-13 14:50 UTC]` shipped at `PM@e1e67656`:

> _"Copper / CEFFU → marked client-side, NOT our blocker per operator direction 2026-05-13. Master plan Group F Week 2 Treasury row + api_keys_wallets 3.A/3.B flipped."_

I framed Phase 2 as "STAYS post-cutover due to hard external dependency on operator-provisioned Copper API key + CEFFU institutional account". **Wrong**. The Copper / CEFFU integration is the client's responsibility — not ours. If/when the client provisions, we flip `WalletProvisioningConfig.signing_surface` (config-only, per `codex/04-architecture/custody-providers.md`). No build work needed from us.

**Plan body updated** (`wallet_treasury_post_cutover_custody_signing_2026_06_01.md` frontmatter + PULL-FORWARD UPDATE section): Phase 2 DESCOPED; deadline now 2026-05-15 only (Phase 1 + Phase 3); estimate corrected 9.6 → 4.8 cal AI-days.

### Correction 3: NEW work surfaced by Harsh audit slot — slot reallocation asks

Per same harsh-audit-slot ping (14:50 UTC):

- **2 slots needed** on `batch_live_symmetry` (confirmed 0/70 done is real; codex `cefi-batch-live.md` + `mode-axis-discipline.md` missing; **drives Tabs 1-3 before 2026-05-23**)
- **2 slots needed** on `defi_recursive_borrow_archetypes` Solidity (`RecursiveLeverageReceiver.sol`) + execution-service orchestrator/tracer (genuinely unshipped; revised 3% → 7% after silent shipments flipped). **OR operator descope decision**
- NEW P0 filed: `emerging_perp_venue_adapters_broken_2026_05_13.md` (5 perp venues at 0-32% capture rate — ASTER 0%, EXTENDED-STARKNET, PACIFICA-SOLANA, LIGHTER-ZKSYNC, HYPERLIQUID; affects DeFi hedge legs)
- NEW P0 filed: `api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md` (deadline 2026-05-14 EOD)

### Corrected Ikenna slot table

| Slot | Status | Direction |
|------|--------|-----------|
| **1 main** | 🟢 active | Coordination + corrections refresh |
| **2** | 🟡 picking up | `defi_classifier_missing_catalog_crossref` P0 (UNCHANGED — still valid) |
| **3** | ✅ DONE | `DEFI_VENUE_LAUNCH_DATES` + corrector shipped @`7319d4ac` (599,486 defi rows corrected). 🟪 FREE for next pickup |
| **4** | 🟡 picking up | propagation chain Phases 3+4+2.A + bucket provisioning handshake (UNCHANGED) |
| **5** | 🟢 in flight | TradFi `MarketSession` SSOT + `CanonicalFuturesContract` (UNCHANGED — greenlit @`1e81aceb`) |
| **6** | 🟡 picking up | wallet_treasury_post_cutover Phase 1 PULL FORWARD (UNCHANGED) |
| **7** | 🟡 picking up | wallet_treasury_post_cutover Phase 3 PULL FORWARD (UNCHANGED) |
| **8** | 🟡 picking up | **REASSIGNED** → `emerging_perp_venue_adapters_broken` P0 (5 venues; investigate root cause + propose fix) — previous 2 issues archived |
| **9** | 🟡 picking up | **REASSIGNED** → `api_football_phase_3b_3c_smoke_forward_poll` P0 (deadline 2026-05-14 EOD) — previous `defi_legacy_blank_reclassification` was the corrector pickup which slot 3 already shipped; remaining reclass scope folds into slot 2's P0 fix |
| **Slot 3 NEW** | 🟡 free | **NEW PICKUP** → 1 slot on `batch_live_symmetry` Tab 1 (codex `cefi-batch-live.md` doc) — per harsh-audit-slot ask. Operator may want to assign 2nd slot. |

### Operator decisions pending

1. **`batch_live_symmetry` 2-slot allocation**: confirm or descope to "principle documented, full enforcement post-cutover" with successor plan. I've parked Slot 3 on Tab 1 as starter; second slot can come from Harsh-side (their idle capacity is symmetric).
2. **`defi_recursive_borrow_archetypes` Solidity + execution**: confirm 2-slot push for May-23 OR descope archetype to "documented, Phase 2-3 deferred". This needs operator decision — the Solidity contract is bespoke May-23 scope.
3. **Harsh audit slot's framing of 530 cal AI-days remaining**: this is the corrected number (was 566 visible / actual ~530 post TBD-backfill calibration). Acknowledge.

### What I'm acking back to Harsh-audit-slot

Filing cross-side ack in `_agent_pings.md` confirming:
- Phase 2 reframing applied
- 2 RESOLVED issues archived
- Slot 8 / 9 reassigned to new P0s
- Operator decisions queued on batch_live_symmetry + recursive_borrow

---


## [slot 1 main] DAY-3 reassignment — pulling post-cutover work into May-15 freeze window — 2026-05-13 ~17:00 UTC

**Why now**: Harsh-side reported all 6 active implementor slots DONE Wave 4 at PM@`6bf6e932`. Combined idle Ikenna+Harsh capacity ≈ 15 slots. At density-push pace ~100-200 cal AI-days/side/day, the workspace's remaining 566 cal AI-days backlog (per latest inventory regen `2026-05-13 15:05 UTC`) clears in 1.5-3 calendar days at full capacity. We're 2 days from May-15 freeze gate, 10 days from May-23 cutover — there's room to pull post-cutover work into the pre-freeze window.

### Pull-forward targets (post-cutover → pre-May-15)

| Item | Original schedule | New schedule | Pulled because |
|---|---|---|---|
| **wallet_treasury_post_cutover Phase 1** (Real HMAC withdrawal chain) | June 3 (`wallet_treasury_post_cutover_custody_signing_2026_06_01.md`) | **Pre-May-15** | Cloud-KMS already live; ~3.2 cal days = hours at density-push pace |
| **wallet_treasury_post_cutover Phase 3** (Audit log immutability + GCS 7yr retention) | June 12 | **Pre-May-15** | GCS bucket already ready; ~1.6 cal days = hours |
| **wallet_treasury_post_cutover Phase 2** (Real Copper + CEFFU integrations) | June 10 | **STAYS post-cutover** | Operator dependency: Copper API key + CEFFU institutional account not provisioned until between May-23 and June-1 |

### Ikenna-side reassignment table (DAY-3, effective immediately)

| Slot | Status | New direction | Plan-of-record |
|------|--------|---------------|----------------|
| **1 main** | 🟢 active | Coordination + reassignment + post-pull master plan refresh | this file + master plan |
| **2** | 🟡 ready for pickup | **PICK UP**: `defi_classifier_missing_catalog_crossref_2026_05_13.md` (P0 — 604k row Script 3 blocker; root-cause fix in UTL `_classify_defi` + instruments-service catalog cross-ref) | issue doc + `legacy_reason_classifier.py` + reconciler |
| **3** | 🟢 in flight (~1-2h) | Continue: ship sports corrector (corrector script + UAC dict + run + verify) | per most recent slot_3.md tail |
| **4** | 🟡 SESSION CLOSE last update | **PICK UP**: finish propagation chain Phases 3+4+2.A + 6-bucket provisioning handshake (slot 8 awaiting) | `expected_unattempted_propagation_chain_2026_05_12.md` + bucket_name_ssot |
| **5** | 🟢 in flight | Continue: TradFi `MarketSession` SSOT + `CanonicalFuturesContract` lifecycle fields (greenlit @1e81aceb) | slot_5.md GREENLIT entry above |
| **6** | 🟡 ready for pickup | **PICK UP — PULL FORWARD**: `wallet_treasury_post_cutover` Phase 1 (Real HMAC withdrawal approval chain). Wire `sign_withdrawal_approval()` using Cloud-KMS; deployment-api `/api/clients/{id}/withdrawal/{id}/approve` endpoint; 8 unit tests (single-sig, 2-of-2, M-of-N multisig) | `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` Phase 1 |
| **7** | 🟡 ready for pickup | **PICK UP — PULL FORWARD**: `wallet_treasury_post_cutover` Phase 3 (Audit log immutability). Enable GCS Object Versioning + 7-year retention lock on audit bucket; wire deployment-api withdrawal calls into Cloud Audit Logs; 4 compliance tests | `wallet_treasury_post_cutover_custody_signing_2026_06_01.md` Phase 3 |
| **8** | 🟡 ready for pickup | **PICK UP**: 2 P1 follow-ups — (a) `uac_normalize_aster_ticker_missing_2026_05_13.md` (1-line restore in UAC `tickers.py` re-exports); (b) `standings_entity_gcs_ambiguity_2026_05_13.md` resolution | both issue docs |
| **9** | 🟡 ready for pickup | **PICK UP**: `defi_legacy_blank_reclassification_2026_05_13.md` (Script 3 follow-up — gates on Slot 2 fixing classifier first; serial dependency. Slot 9 starts pre-audit grep + design while Slot 2 ships classifier fix) | issue doc + reconciler |

**Sub-agent fan-out OK**: Slot 6 + Slot 7 wallet_treasury work touches different code paths (signing vs audit log) — fully parallel. Slot 2 + Slot 9 defi classifier work has a serial dep (Slot 2 ships first); Slot 9 design phase can overlap.

### What I'm NOT pulling forward (and why)

- **wallet_treasury Phase 2** (Copper + CEFFU custody integrations) — hard external dependency on operator-provided Copper API key + CEFFU institutional account. Cannot ship without those credentials. STAYS June 1+.
- **Master plan Group A through G items that are "manual sign-off" or "operator-only"** — out of agent scope.
- **117 UTL test failures** (`pipeline_mode` hardening debt from Harsh slot 9) — Harsh explicitly retained ownership in cross-side FYI (`fbd8d419`); not pulling unless operator wants Ikenna to absorb.
- **Phase 4.DEFAULT-REMOVAL final tail** — gating freeze-gate item 3, currently in Harsh's lap; will monitor.

### Updated capacity math

- Ikenna idle slots: 2, 4, 6, 7, 8, 9 (6 reassigned this round)
- Ikenna in flight: 3, 5 (will close in hours)
- Harsh idle slots (per shift-end LEDGER): 5, 8, 10 reserve + 2/3/4/6/7/9 all Wave 4 DONE (ready for Wave 5)
- Total combined capacity: ~15 slots at ~5-7× density-push compression each
- Remaining workspace backlog: 566 cal AI-days
- Wall-clock estimate: **~1-3 calendar days to clear backlog** at full capacity — well inside the May-15 freeze window

### Cross-side ping

Filed in `plans/active/_agent_pings.md` informing Harsh-main of (a) Ikenna pull-forwards from post-cutover; (b) wallet_treasury Phase 2 stays post-cutover; (c) capacity assessment.

---


## [slot 1 main] Writegate Phase 6.x scoreboard refresh + 6.6/6.7/6.9 assignment — 2026-05-13

**Status**: ✅ Phase 6.3 AUTO-SHIPPED; ✅ Phases 6.6/6.7/6.9 ASSIGNED to Ikenna

### Phase 6.x complete status (corrected from earlier "Phase 6.3 orphaned" finding)

| Phase | Scope | Status | Commit / Slot |
|-------|-------|--------|---------------|
| **6.3 volatility** | features-service | ✅ SHIPPED 2026-05-13 14:16 UTC | `features-service@d7514a08` (Rollout Agent — auto-shipped while orphan triage was in flight) |
| **6.4 cross_instrument** | features-service | ✅ SHIPPED | `features-service@e31ef632` (Ikenna slot 7 PART A) |
| **6.5 delta_one+onchain+calendar+commodity** | features-service | ✅ SHIPPED | `features-service@5e24a18c` / `@6cbf50ff` / `@4623c669` / `@9f4b6427` (Ikenna slot 7 PART B) |
| **6.6 ml-training + ml-inference** | 2 services | 🔴 NOT STARTED | **👉 Ikenna next-cycle slot (post-Wave 4)** |
| **6.7 strategy + execution + position + risk** | 4 services | 🔴 NOT STARTED | **👉 Ikenna next-cycle slot (sub-agent fan-out, ~10-15 cal days)** |
| **6.8 instruments-service catalog** | PART A ✅ / PART B 🔴 | PART A shipped | `instruments-service@27fbc90` (Ikenna slot 8). PART B gated on 6.9 sweep. |
| **6.9 workspace QG ratchet + flip-sweep** | workspace-wide | 🔴 NOT STARTED | **👉 Ikenna slot 1 main (Gate 4 firing slot, serial after 6.6/6.7/6.8 PART B)** |

### Why Ikenna owns 6.6/6.7/6.9

Per Harsh slot_2.md note (2026-05-13 08:38 UTC): _"Phase 6.3-6.9 = Ikenna slots 6/7/8. Harsh slot 3 clear."_
Harsh-side never owned the writegate slice (c) tail; it was always Ikenna's. The earlier "Phase 6.3 orphaning"
issue was a transient mid-cycle Slot 6 reassignment — now obsolete since 6.3 auto-shipped.

### Slot freed: Slot 6+ spawn no longer needed

Phase 6.3 Option B (Ikenna spawns emergency Slot 6+ tab for volatility) is **CANCELLED**. Phase 6.3 was
auto-shipped by Rollout Agent at `d7514a08` while the orphan triage was still being acted on. Slot capacity
freed for higher-priority work next cycle (likely Phase 6.6 fan-out).

### Updated Gate 4 fire conditions

Gate 4 (writegate slice-c complete) now requires:
- ✅ Phase 6.3 (done)
- ✅ Phase 6.4 (done)
- ✅ Phase 6.5 (done — all 4 modules)
- 🔴 Phase 6.6 (Ikenna next-cycle, ~3-10 cal AI-days)
- 🔴 Phase 6.7 (Ikenna next-cycle, ~5-15 cal AI-days, sub-agent fan-out)
- 🟡 Phase 6.8 PART B (gated on 6.9 sweep, ~1-2 cal AI-days)
- 🔴 Phase 6.9 (Ikenna slot 1 main — serial after 6.6/6.7/6.8 PART B, ~2 cal AI-days)

**Estimated Gate 4 fire** (per density-push pace ~100-200 cal AI-days/side/day; ref `feedback_pace_calibration`):
Total ~10-30 cal AI-days at ~100-200/day = **0.5-1.5 calendar days from 2026-05-13** = **2026-05-14 to 2026-05-15**.
Phase 6.9 freeze-gate workspace flip lands **PRE-FREEZE-GATE** and **PRE-CUTOVER**. Workspace QG baseline reset
completes inside the May-15 freeze window — does NOT roll into post-cutover backlog.

**Earlier (incorrect) estimate** of 2026-05-26 to 2026-06-02 mis-applied 1 cal-day = 1 calendar-day. Per the
2026-05-12 Day-1 measured pace (5 of 7 Ikenna slots closed entire 4-day cycle in 1 calendar day = ~5× prior
calibration), the workspace runs ~100-200 cal AI-days/side/day. Corrected here.

### Updated coordination plan

- Cross-side ping to be filed in `_agent_pings.md`: Ikenna formally claims Phase 6.6/6.7/6.9 ownership (no
  Harsh-side action required; just informational).
- Writegate plan body annotated with Ikenna ownership at Phase 6.6/6.7/6.9 (this commit).
- Master plan inventory regenerator to be re-run EOD to pick up the new flip + ownership annotations.

---



## [slot 1 main] Operator decisions locked + coordination ledger filed — 2026-05-13

**Status**: ✅ DECISIONS LOCKED; 🟡 AWAITING HARSH-MAIN PHASE 6.x STATUS

**What filed**:

### Phase 6.3 Orphaning Decision

- **Decision**: CHOSEN Option B (Ikenna spawns emergency Slot 6+ tab post-Slot-7/8 close)
- **Rationale**: Single-operator coordination preferred; Ikenna proven at sub-agent fan-out; Harsh-side at capacity with manifest + codex work
- **Timeline**: 3–4 calibrated AI-days within cycle margin (estimated Day 3 AM start)
- **Scope**: `features-service/features_service/volatility/` module emission semantics
  - Add `_check_emission_policy()` call in cross-module orchestrator
  - Add `_apply_emission_policy()` logic to volatility writer
  - Wire `publish_with_policy()` on output
  - Add 4–6 unit tests (STRICT_FAIL, NAN_FILL × full, partial completeness)
  - QG check (lint/format/basedpyright/codex/import-patterns)
- **Reference pattern**: Slot 7 commits `features-service@5e24a18c` (cross_instrument) + `@6cbf50ff` (delta_one) show exact pattern
- **Documentation**: `plans/active/issues/writegate_phase_6_3_features_volatility_orphaned_2026_05_13.md` (Decision section updated; locked by live-defi-rollout)

### Wallet Treasury Design Decisions Acked (Q1–Q5)

- **Q1** ✅ Slot 4 Phase 3.D `/api/treasury/rollup` endpoint ready by Day 1 EOD — **confirmed**
- **Q2** ✅ Require backend Phase 6.A live before wallet UI — **confirmed**
- **Q3** 🔄 DEFERRED: Simple button-click stub for May-23 cutover; real HMAC-signed approval chain post-cutover
- **Q4** ✅ Daily HWM crystallization confirmed — **confirmed**
- **Q5** 🔄 DEFERRED: Stubs (Cloud-KMS-only signing) for May-23; real Copper + CEFFU integration June-1+

**Successor plan filed**: `wallet_treasury_post_cutover_custody_signing_2026_06_01.md`
- **Scope**: Q3 + Q5 deferred work (real signing + real custody + audit immutability)
- **Phases**: 
  - Phase 1: Real withdrawal approval chain (HMAC-SHA256 + 2-of-N multisig) — 3.2 cal days, June 3 milestone
  - Phase 2: Real Copper + CEFFU integrations — 4.8 cal days, June 10 milestone
  - Phase 3: Compliance + GCS audit log immutability (7-year retention lock) — 1.6 cal days, June 12 milestone
- **Total**: 9.6 calibrated AI-days across 15-day post-cutover window
- **Handoff trigger**: May-23 cutover completion + 48-hour live smoke green; operator signals go-ahead for Phase 1

### Coordination Artifacts Filed

- **PM Coordination Ledger** (pm_coordination_ledger_2026_05_13.md): Consolidated view of 2 cross-side pings + 8 slot status + 7 active issues + blocker matrix + operator-pending decisions (P0/P1/P2 triage targets)
- **Cross-side pings** (2 filed):
  1. Phase 6.3 orphaning (11:30 UTC) — OPTIONS A/B/C, CHOSEN Option B, awaiting Harsh-main ack
  2. Phase 6.x status request (11:45 UTC) — Gate 1 fired; requesting Harsh confirmation on Phase 6.6/6.7/6.9 status

---

## [main ↔ slot] Open Questions

| Question | Status | Blocker? | Notes |
|----------|--------|----------|-------|
| **Harsh-main Phase 6.6/6.7/6.9 status** | 🟡 AWAITING RESPONSE | ✅ YES (Gate 4) | 2h response target; affects Gate 4 fire timing |
| **Gate 3 phantom audit runbook ownership** | ✅ ASSIGNED | ❌ NO | Ikenna Slot 1 main = operational owner; runbook ready (`gate_3_phantom_audit_runbook_2026_05_13.md`) |
| **Non-blocking issue routing** | 🟡 IN PROGRESS | ❌ NO | 4 issues to route (sports, strategy, audit, blank-reason); 1 to archive (bookmaker_registry) |

---

## [main → slots] Status Update + Upcoming Milestones

**Current tab registry** (as of 2026-05-13 ~15:00 UTC):
- Slot 2: defi_catalogue Phases 1–3 (status: UNKNOWN, awaiting update)
- Slot 3: code_freeze Phase 1 audit + apply-flips (status: ✅ COMPLETE, ready for Phase 2)
- Slot 4: api_keys_wallets scope-contracted (status: UNKNOWN, Phase 3.D Treasury.rollup due Day 1 EOD)
- Slot 5: defi_recursive_borrow Phase 1–2 design (status: ⏸ GATED ON SLOT 2)
- Slot 6: defi_simulation_realism Phase 1–3 design (status: UNKNOWN, AMM matrix due Day 2 noon)
- Slot 7: simulation_scenarios Phase 1–2 (status: ✅ SHIPPED, ready for Phase 3 scenario runner integration)
- Slot 8: cross_cutting #4 + manifest Phase 3 (status: ✅ SHIPPING D1+D4 HELPERS, manifest Phase 3 ready to start)
- **Slot 6+** (TBD): Phase 6.3 volatility emission semantics (FUTURE SPAWN — estimated Day 3 AM, after Slot 7+8 close)

**Upcoming critical milestones**:
1. **TODAY (2026-05-13) by 15:00 UTC**: Harsh-main must ack Phase 6.3 Option B decision
2. **TODAY by 18:00 UTC**: Harsh-main must confirm Phase 6.6/6.7/6.9 status + Ikenna-main route non-blocking issues + archive resolved issues
3. **EOD (2026-05-13)**: Master plan inventory refresh (active-plan-inventory-tracker.py regenerate)
4. **Day 2 AM**: Expect Slot 6+ spawn (Phase 6.3 volatility) if Day 1 evening Slot 7+8 completions hold

---

## Notes

**Why this structure**: Per CLAUDE.md "Daily Work-Split Process," Slot 1 main files intra-side pings for coordination with spawned slots. Cross-side coordination goes through `plans/active/_agent_pings.md` (workspace-shared with Harsh-side). This file (Slot 1 ledger) documents main-orchestrator status + pending decisions + upcoming spawns.

**Commit**: unified-trading-pm@490c96a0 (docs(decisions): Phase 6.3 Option B + wallet_treasury post-cutover plan)
