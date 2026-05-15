# Slot 9 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 11:55 UTC] harsh-slot-9 — ✅ DONE queue item 5 (MTDS handler additions audit): mtds@0c40d02. Added 8 tests for PACIFICA-SOLANA + LIGHTER-ZKSYNC venue adapters (78e3b28): 3 tests TestPacificaCanonicalWrite (hive path, launch-date guard, per-coin isolation), 2 tests TestLighterCanonicalWrite (Tardis coverage guard, API-key guard), 3 unit + 1 skipped integration TestLighterCsvParser. QG green (21 passed, 1 skipped). B-015 still HOLD — no Ikenna phantom-fix DONE in _agent_pings.md. Reserve queue items 1-5 complete. Awaiting item 6 (ups-p2-run-tag-mtds-calendar) greenlight (slot 4 must DONE features-service first) or B-015 re-smoke greenlight.

[2026-05-15 06:02 UTC] [main → slot 9] — ✅ ALL 4 handlers acked (lst_rates@f657431 + evm_defi/gas_fee/solana_defi@3bca360). LEDGER flipped. CYCLE-CLOSE acked. 🛑 B-015 STILL HOLD — Ikenna phantom-fix NOT YET confirmed in _agent_pings.md as of 06:02 UTC. Do NOT launch re-smoke yet. Continue PBM Phase 8 reserve. Poll _agent_pings.md every ~30 min; when Ikenna posts phantom-fix DONE, ping main immediately — we will greenlight re-smoke at that point.

[2026-05-15 06:02 UTC] harsh-slot-9 — ✅ DONE lst_rates handler hardening: mtds@f657431 — eigenlayer pattern applied
(write+record_captured wrapped in try/except, record_failed on exception). B-015 re-smoke can proceed once Ikenna's
phantom-fix confirms. Moving to PBM Phase 8 reserve.

[2026-05-15 05:42 UTC] harsh-slot-9 — ✅ DONE items 2+3+4: mtds@8693c57 (UAC facade audit clean + 4 Helius RPC tests);
PM@9c666020 (phantom structural issue doc). B-015 still HOLD — (a) Ikenna phantom-fix not yet confirmed; (b) operator
direction needed on lst_rates handler hardening before re-smoke. Moving to reserve queue (PBM Phase 8 coverage). Polling
\_agent_pings.md every ~30 min.

[2026-05-15 05:33 UTC] harsh-slot-9 — 🚨 BIG FINDING (P1): DeFi handler phantom risk is STRUCTURAL —
`lst_rates_handler.py` (+ evm_defi/gas_fee/solana_defi) call `record_captured()` OUTSIDE the GCS upload try-block. After
Ikenna's apply-flips, B-015 re-smoke will re-accumulate phantoms unless handler code hardened first. Issue:
`plans/active/issues/defi_handler_phantom_risk_structural_2026_05_15.md`. Recommend: hold re-launch until lst_rates
hardened (~30 min). Awaiting operator direction.

[2026-05-15 05:08 UTC] harsh-slot-9 — STARTED slot 9 (plans/active/continuation_prompts_harsh_2026_05_15.md § Slot 9) —
B-015 HOLD, pivoting to items 2-4: MTDS UAC facade audit + Helius RPC tests + DeFi handler readiness audit

[2026-05-15 04:46 UTC] [main → slot 9] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-15 04:18 UTC] [main → slot 9] — 🌅 **DAY-1 START (Lever 1+2) — 🛑 B-015 STILL HOLD**. Read
[`../../plans/active/continuation_prompts_harsh_2026_05_15.md`](../../plans/active/continuation_prompts_harsh_2026_05_15.md)
§ "Slot 9". **CRITICAL OVERNIGHT UPDATE**: Ikenna posted @02:00 UTC — smoke VMs FAILED SILENTLY due to phantom manifest
rows skipping both write paths (lst_rates + features-onchain); ZERO data written. Ikenna slot 8 owns phantom-clear via
`reconcile_phantom_manifest_rows_all.py --asset-group DEFI --apply-flips` + re-smoke. **HOLD B-015 Phase 2 until Ikenna
slot 8 confirms phantom-fix DONE + green smoke**. Meanwhile execute queue items 2+3: (2) MTDS UAC facade audit
(deep-import cleanup); (3) MTDS Solana Helius RPC integration tests. Self-pivot; when Ikenna phantom-fix lands, pivot
back to B-015 Phase 2.

[2026-05-15 05:50 UTC] [main → slot 9] — ✅ DONE ack items 2+3+4 (mtds@8693c57 + PM@9c666020). LEDGER flipped. BIG
FINDING relayed to Ikenna-main via \_agent_pings.md. B-015 still HOLD — do NOT launch until: (a) Ikenna's phantom-fix
confirmed + (b) operator direction on handler hardening. Continue PBM Phase 8 reserve. If you can fix lst_rates handler
(~30 min) while waiting, go ahead — it unblocks re-smoke and the eigenlayer_rewards pattern is the target.

[2026-05-15 06:25 UTC] [main → slot 9] — ✅ OPERATOR APPROVED handler hardening. Fix `lst_rates_handler.py` +
`evm_defi_handler.py` + `gas_fee_handler.py` + `solana_defi_handler.py` now. Target pattern =
`eigenlayer_rewards_handler.py` (record_captured inside try, record_failed in except/finally). Ship all 4 in one commit
to market-tick-data-service. QG green → quickmerge. Ping DONE with SHA when all 4 hardened. B-015 re-smoke can proceed
once Ikenna's phantom-fix is also confirmed.

[2026-05-15 08:05 UTC] [main → slot 9] — ✅ lst_rates hardening acked (mtds@f657431). ⚠️ Three handlers still pending
from original direction: **evm_defi_handler.py + gas_fee_handler.py + solana_defi_handler.py**. Apply same
eigenlayer_rewards pattern to all 3. Ship in one commit. Ping DONE with SHA when all 3 done. PBM reserve can run in
parallel if you context-switch, but all 4 handlers must be hardened before B-015 re-smoke.

[2026-05-15 09:15 UTC] harsh-slot-9 — ✅ DONE all 3 remaining handler hardenings: mtds@3bca360. evm_defi_handler.py
(removed inner swallowing except from \_collect_protocol_chain + \_collect_protocol_chain_batch), gas_fee_handler.py
(widened Solana+BTC except to Exception, removed unused \_SchemaValidationError import), solana_defi_handler.py (removed
inner swallowing except from \_collect_protocol). QG green. Tests updated (test_handles_client_error now expects
propagation, not return-0). ALL 4 handlers now eigenlayer-safe. 🏁 Day-4 CYCLE-CLOSE — see below.

[2026-05-15 07:10 UTC] [main → slot 9] — 📋 **EXTENDED RESERVE QUEUE while B-015 HOLD continues**. Work through in order, self-pivot:

1. **MTDS UAC facade migration audit** (continuation_prompts item 2): grep for remaining `from market_tick_data_service.unified_api_contracts` deep-imports across all MTDS handlers; fix any found. QG green.
2. **MTDS Solana Helius RPC integration tests** (continuation_prompts item 3): happy-path + 429 rate-limit + fallback + SOLANA_RPC_PROVIDER toggle. 4+ tests + QG green.
3. **MTDS handler readiness audit** (continuation_prompts item 4): all 5 DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) — latest write date vs expectation + manifest vs parquet row parity (phantom check). File issue doc per handler with phantoms.
4. **PBM Phase 8 coverage extensions**: read `market-data-processing-service/` coverage report; identify uncovered paths; add tests for any below 70%. QG green.
5. **MTDS handler additions audit**: review continuation_prompts § "MTDS handler additions for new venues" — identify any new venue adapter stubs that are missing integration tests; add skeleton tests with `@pytest.mark.requires_credentials`.
6. **master plan `ups-p2-run-tag-mtds-calendar`**: wire `--run-tag` into MTDS GCS output path so per-VM shard isolation (MANIFEST_PER_VM_SHARDS) is tag-aware. Also update features-service to consume run-tagged MTDS output. Done-def: `--run-tag` flows from CLI → GCS path → features-service read; unit test covers the path; QG green.
Poll `_agent_pings.md` every 30 min for B-015 greenlight (Ikenna phantom-fix). When it lands: drop everything, verify smoke, launch Phase 2.

[2026-05-15 07:11 UTC] [main → slot 9] — ⚠️ **CORRECTION to extended queue**: item 6 (`ups-p2-run-tag-mtds-calendar` touching features-service) is DEPRIORITIZED — slot 4 is actively in features-service right now. Work items 1-5 first; return to item 6 only after slot 4 pings DONE for features-service work. This avoids simultaneous edits to the same repo.

[2026-05-15 07:41 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION** — add 4 more items after your 6-item batch. Total ~20 AI-days.
7. **PBM honest-coverage emission audit** — verify market-data-processing-service emits honest-coverage updates per CLAUDE.md "Manifest + Honest Absence" rules. Audit + fix gaps. Done-def: every PBM batch_handler emits captured/empty/failed via UTL record_*.
8. **MTDS Pyth oracle integration tests** — Pyth UNBANNED 2026-05-06 for Solana on-chain price feeds. Add MTDS-side Pyth adapter integration tests (happy-path, stale-feed detection, missing-symbol). Done-def: 3+ tests + MTDS QG green.
9. **PBM Phase 8 service-output emission tests** — verify `_resolve_policy_output_data_type` + `_publish_emission_check` exist on every PBM publish path. Add tests for STRICT_FAIL/WARN_ONLY/NAN_FILL outcomes. Done-def: callsite coverage + QG green.
10. **MTDS handler retry-and-backoff audit** — verify all 5 DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) respect 429 rate-limit headers with exponential backoff. Add tests where missing. Done-def: each handler tested for 429 → backoff → retry → success scenario.

[2026-05-15 07:45 UTC] [main → slot 9] — 📋 **QUEUE EXTENSION 2** — slot 4 features-service work is ~8-10 AI-days; adding 4 more pure-MTDS/PBM items so you never idle waiting on slot 4. Item 6 stays DEPRIORITIZED — pick it up only after slot 4 features-service close-out ping.

11. **MTDS calendar boundary tests** — date-rollover at midnight UTC: verify handlers correctly partition (a) trades spanning 23:59→00:01; (b) end-of-month rollovers; (c) DST edge cases (no DST in UTC but venue-local DST when timestamps converted). Done-def: 6+ boundary tests + MTDS QG green.
12. **MTDS adapter rate-limit + cache layer tests** — every MTDS venue adapter (Binance/Bybit/OKX/Deribit/Hyperliquid/Kraken + DEXes) should have rate-limit retry + response-cache tests. Audit + fill gaps. Done-def: per-adapter test parity confirmed + MTDS QG green.
13. **PBM phantom-manifest detection unit tests** — write tests for the phantom detection logic in `market-data-processing-service` (manifest row exists but parquet missing OR vice-versa). Use synthetic fixture data. Done-def: 4+ phantom-detection scenarios covered + PBM QG green.
14. **MTDS CLI flag validation tests** — verify `--operation/--mode/--asset-group` flag combinations: invalid combos raise loud at parse-time, not runtime. Add tests if missing. Done-def: bad-flag combos rejected + good combos pass + MTDS QG green.

After items 11-14, total slot 9 queue: 13 pure-MTDS/PBM items + 1 deferred features-service item = ~24 AI-days non-conflicting work. Item 6 only becomes actionable when slot 4 pings features-service CYCLE-CLOSE.
