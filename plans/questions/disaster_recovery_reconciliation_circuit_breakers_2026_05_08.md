---
name: disaster-recovery-reconciliation-circuit-breakers
overview: End-to-end DR readiness — reconciliation audits across every state surface (positions / balances / custody / on-chain / events / manifest), circuit-breaker taxonomy (auto-halt conditions per asset_group + per archetype + per venue + per chain), recovery playbooks per failure scenario (key compromise, venue freeze, wallet drain, RPC outage, custody outage, cloud-region failover, data-source outage, manifest corruption, event-bus outage), and chaos-drill cadence. Answers "if X breaks at 03:00 UTC on May-24, can the operator recover without losing capital, double-trading, or trading on stale state."
type: question
status: drafting
created: 2026-05-08
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: null
ssot_bar: best-possible-no-unanswered-question-before-2026-05-23
related_codex:
  - codex/04-architecture/shard-level-failure-isolation.md
  - codex/04-architecture/kill-switch-circuit-breaker.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/04-architecture/interface-credential-convention.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
  - codex/14-playbooks/shared-core/signal-broadcast-architecture.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/infrastructure_master_2026_05_07.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/defi_master_2026_05_07.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md
  - plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
  - plans/questions/wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md
---

# Disaster recovery + reconciliation audit + circuit breakers — operational resilience SSOT

## SSOT bar — best-possible, no unanswered question, before 2026-05-23

This doc is targeting **the workspace's hardest completion bar**: by 2026-05-23 (live-DeFi cutover), every sub-question in Blocks A-I MUST be **answered against real codebase + codex + plan state**, with **zero unresolved gaps**, and the resulting plan + codex SSOTs MUST represent **the best-possible architecture for operational resilience** — not "good enough for now," not "we'll revisit," not "operator-improvise the rest." The discipline applies as a contract on this doc:

1. **Audit, don't speculate.** Every sub-question's answer comes from a real audit pass against existing assets — codebase grep across all 60+ repos, codex doc walk (`codex/04-architecture/`, `codex/14-playbooks/`, etc.), plan walk (`plans/active/` + `plans/epics/` + relevant `plans/archive/`), manifest + on-disk state probes, deployed-service state queries, event-stream evidence (`gs://{pid}-events/...`). Speculation without audit is a placeholder, not an answer; placeholders MUST be flagged `🔴 GAP — unaudited` rather than written as confident prose.
2. **Codex + plans + code together, not separately.** The audit pass walks all three layers in one sweep so drift between layers surfaces (codex says X, code does Y, plan says Z). Drift IS a finding, not a digression — every drift gets a triage action per *Findings Triage Discipline*.
3. **Closed-set sub-questions.** Each Block / sub-question is a closed-set bullet — when audit findings + operator clarification land, the bullet is `🟢 ANSWERED` (with file:line / commit-sha / codex-doc citation) or `🔴 GAP` (with named successor: plan filename, owner, deadline). No `🟡 partial`, no `see also`, no `TBD`. The doc closes only when every Block A-I bullet is GREEN against real evidence.
4. **Best-possible, not good-enough.** The plan that spawns from this doc must represent the architecturally best shape for operational resilience — not a band-aid, not a "ship-it-and-revisit," not a workaround. If best-possible requires more scope than fits before May-23, the doc enumerates the **explicit hard-cut** (P0 must-ship-before-May-23 vs P1 post-cutover continuation) with a **named continuation plan** in `plans/active/` for every cut. Cuts are explicit, not silent.
5. **Pre-May-23 sign-off gate.** This doc's `status: closed` transition requires:
   - Every Block / sub-question answered with audit evidence cited.
   - Spawned canonical plan in `plans/active/` (or fold into existing master / epic) with phased DAG + success criteria + downstream consumer updates per *Citadel-Grade Planning Standards*.
   - Every codex SSOT touched is updated (NEW or UPDATE) per the *Post-Plan-Phase Codex Audit* HARD RULE.
   - At least one chaos-drill / real-data run has executed against real (or staging-real) infra per the *Plans Run To Actual Completion* HARD RULE.
   - Operator sign-off recorded in `## Operator notes / answers`.
6. **Zero cross-contamination with siblings.** This doc is the SSOT for DR — reconciliation surfaces, circuit-breaker taxonomy, recovery playbooks, chaos drills. Sibling question docs cover credentials (`api_keys_wallets_accounts_readiness`), workflow maturity (`paper_vs_live_workflow_maturity`), treasury / client-flow (`wallet_treasury_client_flow_post_trade_readiness`), DeFi catalogue (`defi_readiness_catalogue`). Where surfaces overlap (e.g. credential-rotation playbook D2 references credential matrix from sibling), the boundary is named explicitly: this doc owns the **playbook**, sibling owns the **artifact**. No surface is owned by two docs.

Reviewers reject this doc closing with surviving `🔴 GAP` bullets, surviving `TBD` markers, surviving "operator-improvise" handoffs, or surviving codex drift. The bar is binary: **best-possible-and-complete by May-23, or open**.

## Intent

The May-23 live-DeFi cutover succeeds when the carry + funding-arb archetypes survive **the first real bad day**, not when they survive a green smoke-test in CI. Bad days look like: an OKX API key gets revoked at 03:00 UTC because OKX rotated their auth backend; the Solana RPC starts returning stale slot data for 90 seconds during a network partition; a Copper API call times out in the middle of a settlement; an on-chain reorg invalidates a Uniswap fill that strategy-service already booked as filled; a parallel-agent commit silently corrupts the availability manifest's index file; a Cloud Run deploy bumps a service to a revision missing a critical env var and the only signal is `CRITICAL` Telegram pings; an attacker drains an under-protected hot wallet via a phishing approval. Each one is recoverable **if** the system has (a) a reconciliation audit that detects the drift within minutes, (b) a circuit breaker that halts new exposure as soon as drift crosses tolerance, and (c) a recovery playbook the operator can execute without inventing the procedure on the fly.

Today, the workspace has fragments. CLAUDE.md mandates *shard-level failure isolation* (no `raise` inside per-venue loops), *honest absence vs fake placeholders* (NaN/empty + `empty_confirmed` for honest gaps, never silent placeholders), *no fire-and-forget VM launches* (every VM emits STARTED + progress + STOPPED events), *manifest concurrency* (read-once + per-date freshness check + write-time CAS for any concurrent backfill), and *manifest phantom audit* (periodic reconciliation between manifest captured-rows and actual on-disk parquets). `codex/04-architecture/kill-switch-circuit-breaker.md` exists. The credentials question doc covers credential rotation + hot-reload via `ApiKeyReloader`. But there is **no canonical SSOT enumerating every "what if X breaks" scenario, the detection signal, the auto-circuit-breaker, and the recovery playbook end-to-end.** The discipline lives in pieces; the failure modes are implicit-knowledge-only.

The master plan's Group F item 21 ("circuit breakers + kill switches + alerting + auto-recovery") is the formal cutover gate. But the gate is satisfied today only at the symbol level — a kill-switch class exists; a circuit-breaker hook exists. There is no dry-run evidence that the system survives even one canonical failure scenario end-to-end against real infra. **A circuit breaker that has never tripped under realistic conditions is a circuit breaker we don't actually have.** A reconciliation audit that runs against a hand-curated test fixture but has never matched real Copper-vs-Bybit-vs-on-chain state on a real position is not yet a reconciliation audit — it's a reconciliation hypothesis. A recovery playbook that lives only in chat history is not yet a recovery playbook — it's tribal knowledge with a one-week half-life.

This question doc forces three shifts at once:

1. **Enumerate every reconciliation-audit surface** (Block A) so we have a complete map of "what state does the system claim, and how do we verify it against ground-truth from the upstream system." Reconciliation is the signal that feeds circuit breakers; without comprehensive audits, breakers fire late or never.
2. **Enumerate every disaster scenario** (Block B + G + H) so we have a closed-set catalogue of "what could break, what's the blast radius, what's the detection signal." The catalogue drives both circuit-breaker design (Block C) and recovery playbook authoring (Block D).
3. **Enumerate every recovery path with explicit owners + cadence** (Block D + I) so when a scenario fires, the operator runs the playbook instead of debugging-by-grep. Per the *Runbook Execution-Owner SSOT* HARD RULE, every recovery playbook needs an `execution.owner` declaration + chaos-drill cadence proving it actually works.

The audit is not "grep for `raise` in execution-service." It's **"if Bybit rejects every order at 03:00 UTC because their auth rotated, does the carry archetype halt within 60 seconds, log the reason in a way the operator can actually read, fail safe (no orphaned hedge legs), and surface a Telegram alert that says 'Bybit auth dead, run rotation playbook X'? Has anyone ever actually tested this end-to-end against the real Bybit API by revoking a real key mid-run? If not, we don't know."**

## Question

### Block A — Reconciliation audit surface (the detection layer)

Reconciliation is "compare what we claim is true vs what the upstream source-of-truth says is true; if drift > tolerance, alert + circuit-break." Every state surface needs a reconciliation rule with explicit tolerance + cadence + alerting.

A1. **Position reconciliation — strategy-service vs position-balance-monitor vs venue.** At any time T:
  - strategy-service has a notional position per (venue, instrument, archetype, client) from cumulative fills.
  - position-balance-monitor has the same position from event-stream consumption.
  - The venue API (Bybit `/v5/position/list`, Deribit `/private/get_positions`, etc.) reports the actual on-venue position.

  Audit:
  - Are all three views computed today? Where does the SSOT diverge if drift exists?
  - Reconciliation cadence — every fill? Every minute? Every hour? Daily EOD only?
  - Tolerance — exact match required, or absolute-bps tolerance per instrument size?
  - Drift action — alert-only, halt-strategy, halt-portfolio, or auto-flatten?
  - Per asset_group differences — CeFi venues report position via REST, DeFi positions live on-chain (read via `eth_call` on protocol contract), sports/prediction don't have "positions" the same way (open bets are positions; resolved bets are settled).

A2. **Balance + custody reconciliation — execution-service vs venue + position-balance vs custody API.** Per the sibling api_keys doc Block C4 (treasury reconciliation):
  - Total NAV = `Σ (custody_balance × mark_price)` + `Σ (venue_margin × mark_price)` + `Σ (on_chain_wallet × mark_price)`.
  - Each leg has its own ground-truth: Copper / CEFFU API for custody; venue REST for margin; chain RPC `eth_getBalance` + ERC20 `balanceOf` for on-chain.
  - Drift > X bps → alert + circuit-break.

  Audit:
  - Is there a treasury-rollup reconciler today, or is "what's our NAV" operator-eyeballing-multiple-UIs?
  - Per-leg reconciliation cadence — custody is slow-moving (sweep events; webhook-driven), venue is real-time, on-chain is block-paced (12s ETH, 0.4s SOL).
  - Cross-leg drift — if execution-service expects $X collateral on Bybit but Bybit reports $X-Δ, where did Δ go? Is there a reconciler that walks event history backward to attribute Δ to a specific event (fee, funding payment, liquidation, manual sweep, hack)?

A3. **On-chain reconciliation — execution-service expected state vs chain RPC actual state.** DeFi positions are inherently asynchronous: tx submitted → mempool → included in block → confirmation depth → reorg-safe. Per intermediate state:
  - **Pending** — tx hash exists but not yet included. State expected `expected_state`, on-chain state still `prev_state`. Tolerance: pending duration > N seconds → alert.
  - **Included but unconfirmed** — included in chain head but < N confirmations. Reorg-risk window. Strategy-service should not yet "book" the fill.
  - **Confirmed** — N+ confirmations. Strategy-service books fill.
  - **Reorged** — included then dropped. Catastrophic if strategy already booked.

  Audit:
  - Confirmation-depth threshold per chain (Ethereum mainnet ~12 blocks for finality, Arbitrum / Base / Polygon higher because of fraud-proof window, Solana 32 slots for finalized).
  - Reorg-detection — is there a reconciler that polls chain RPC for tx existence + block hash and detects reorgs? What's the action on reorg-detected (auto-flatten, alert, halt)?
  - Cross-protocol state — Aave deposit balance via `getUserAccountData()`, Uniswap LP position via NFT `positions()`, Lido stETH balance via `balanceOf()`. Does each connector have a reconciliation probe against the on-chain truth, or does execution-service trust its own internal ledger?

A4. **Event-stream reconciliation — published events vs consumed events vs database state.** Every service publishes events to Pub/Sub (`gs://{pid}-events/...`) that downstream services + UI consume. Audit:
  - Event-publish ack vs consumer ack — Pub/Sub guarantees at-least-once; are consumers idempotent? If a consumer crashes mid-batch, does it duplicate or skip on restart?
  - DLQ depth — per topic, what's the alert threshold for DLQ size? A DLQ filling silently is a DR scenario in itself.
  - Event-vs-state drift — if a service emits a `FILL_BOOKED` event but its own internal database doesn't have the fill (or vice-versa), how is the divergence detected?

A5. **Manifest reconciliation — claimed coverage vs on-disk parquets.** Per CLAUDE.md *manifest phantom audit*, the periodic `reconcile_phantom_manifest_rows_all.py` script checks for drift between manifest `captured` rows and actual on-disk parquets. Audit:
  - Cadence — daily? Weekly? Per-asset_group?
  - Owner per asset_group — who runs it, who triages findings?
  - Mid-run safety — phantom audit should never trigger during active backfill (race with writers); what's the lockout mechanism?
  - Cross-cloud — does the phantom audit run against both GCS + S3 (per Tab 4 GCS→S3 migration)? Drift between clouds is itself a DR scenario.

A6. **Order-state reconciliation — execution-service order ledger vs venue order book.** Per venue, every open order has lifecycle: `submitted → ack → partial_fill* → filled | cancelled | rejected | expired`. Audit:
  - Per venue, query venue's open-order endpoint (`GET /v5/order/realtime` Bybit, etc.) and compare to execution-service's open-order ledger.
  - Drift — orders execution-service thinks are open but venue says are gone (= silently filled / cancelled / rejected without event delivery).
  - Cadence — every 30s? Every fill event?
  - Action on drift — auto-correct ledger from venue truth, alert, halt-strategy?

A7. **PnL reconciliation — strategy attribution vs venue P&L vs custody P&L.** Per the sibling client-reporting question doc:
  - strategy-service computes per-archetype + per-client PnL from booked fills + mark-to-market.
  - venue P&L (e.g. Bybit `/v5/account/wallet-balance` reports realized + unrealized).
  - custody P&L is asset-deposit-vs-asset-withdraw delta over the period.

  Audit:
  - All-three-must-agree-within-X-bps reconciler exists?
  - Bps tolerance per asset class.
  - Drift attribution — fees not captured, funding payments not captured, liquidations not captured, slippage estimate vs realized fill price drift.

A8. **Time + clock reconciliation.** All upstream systems have their own clock. Audit:
  - Per venue / chain / data source — what timestamp does the source emit, and does the workspace map it to UTC consistently?
  - Clock drift on VMs — is NTP synced? What's the alert threshold?
  - Latency SLA per source — if a venue REST call returns a quote with `quote_time` 5s in the past, is that quote stale enough to reject?
  - This composes with `LookaheadBiasError` (CLAUDE.md) — a clock-skewed source can spoof `available_at` and silently leak future info backward.

A9. **Cross-mode reconciliation (per CLAUDE.md "Live = batch").** Live and batch must produce identical schemas + identical `data_types` + identical fields. Audit:
  - Per `(asset_group, data_type, day)`, does live-replay = batch-replay byte-for-byte (after normalising for timestamp jitter)?
  - Drift here is a critical correctness bug — production strategy decisions diverge from backtest predictions.
  - The master plan Group F item 18 (batch-vs-live reconciliation + P&L attribution) is the formal gate for this.

### Block B — Disaster scenario catalogue (the failure-mode taxonomy)

The closed-set "what could go wrong" — every scenario gets a circuit-breaker (Block C) + recovery playbook (Block D). Categorised by surface; each row is a row in the master DR matrix.

B1. **Authentication / authorisation failures.**
  - Venue API key revoked / rotated by venue without notice.
  - Venue API key permissions silently downgraded (trade → read-only).
  - Cloud service-account binding silently revoked (`secretmanager.secretAccessor` removed).
  - Wallet private key compromised (phishing approval, dust attack revealing key, leaked from `.env`).
  - Custody API session expired without auto-refresh.
  - 2FA / IP whitelist drift — production VM's IP changed and venue rejects from non-whitelisted IP.

B2. **Connectivity / network failures.**
  - Venue API entirely unreachable (DNS, BGP, regional outage).
  - Venue WebSocket dropped + reconnect loop.
  - Chain RPC rate-limited / throttled / 5xx.
  - Chain RPC returning stale data (provider-side cache lag).
  - Pub/Sub publisher backed up; events arriving > X seconds late at consumer.
  - Cloud Run cold-start latency spike rejecting traffic.
  - GCP region outage (asia-northeast1).
  - AWS region outage (ap-northeast-1).
  - Cross-cloud transfer (per Tab 4 GCS→S3) stalled.

B3. **Data correctness failures.**
  - Manifest phantom rows (claimed coverage, no parquet on disk).
  - 1440-NaN-OHLC placeholder bars (per CLAUDE.md 2026-05-05 reference incident).
  - Schema drift on disk (column added/removed without reader update).
  - Hive-vocab drift (`category=` vs `asset_group=`) — should fall through canonical-then-legacy reader, but a reader bug could silently empty the data.
  - Source returned 200 + empty for a (venue, day) that should have data — incident class: 2026-05-07 RED ALERT 5 CeFi VMs writing 96-100% empty rows.
  - Look-ahead bias in feature compute — a calculator references `available_at` incorrectly and leaks future info.
  - Cluster-coverage failure on bundled shards (ES.OPT 11-cluster, prediction canonical-question-group, sports per-fixture bundle).

B4. **Trade execution failures.**
  - Venue rejection rate spike (auth, balance, rate-limit, market-closed, instrument-delisted).
  - Venue silent partial-fill (REST says filled but no fill event).
  - Venue liquidity collapse (next-tick quote = 0 size; can't unwind).
  - On-chain tx revert with cryptic reason (out-of-gas, slippage exceeded, contract paused).
  - On-chain reorg invalidating a booked fill.
  - Flash-loan callback contract not found (per CLAUDE.md "execution-service `connect()` validates on-chain via `eth_getCode`").
  - Custody sweep request times out / rejects.
  - Order-of-operations bug — perp hedge leg fills at 09:00:00.500 but spot leg fills at 09:00:01.500, leaving a 1s naked exposure.

B5. **Strategy / risk failures.**
  - Strategy emits inconsistent positions (long + short same instrument simultaneously due to race).
  - Risk pre-flight allows a trade that breaches a limit (limit-table stale).
  - Kill-switch fails to halt new orders.
  - Auto-recovery fires before the underlying condition cleared (kill-switch flap).
  - Risk simulation drifts from live (per sibling risk question doc).

B6. **Storage + state failures.**
  - GCS / S3 bucket-write failure (quota, IAM, regional outage).
  - BigQuery emulator vs prod schema drift.
  - Manifest CAS race (per CLAUDE.md "Per-VM shard isolation for concurrent backfills").
  - Cloud Run revision rollback — config change deploys a revision missing an env var.
  - Database (if any) corruption / partition lost.

B7. **Custody failures.**
  - Copper / CEFFU API rejects authentication mid-day.
  - Sweep request silently dropped (no error, no settlement).
  - Custody balance mismatch with venue margin (over-margined or under-margined).
  - Asset listed at custody but not on the venue we want to trade on.

B8. **Operator-action failures.**
  - Operator force-pushes to `main` and silently reverts a safety fix.
  - Operator runs a destructive script in the wrong env (prod instead of staging).
  - Two-teammate × multi-agent collision — one agent's `git add -A` bundles another's WIP into the wrong commit (per CLAUDE.md foot-gun #1).
  - Operator misreads alerting noise, ignores a P0 alert, escalates a P3.

B9. **Time-based failures.**
  - Daylight-savings transitions (especially on TradFi pre-cutover backfills).
  - End-of-day / EOM / EOQ boundary conditions (settlement, funding payments, options expiry).
  - Unicode / leap-second edge cases (rare but real on the 2-year backtest).

B10. **Adversarial scenarios.**
  - Front-running on DEX (sandwich attack on Uniswap swap).
  - MEV extraction degrading fill quality.
  - Oracle manipulation (Pyth / Chainlink price spoofed temporarily — usually reverted but if our circuit-breaker uses oracle price during the spoof window, we trip on bad data).
  - Phishing email mimicking venue support requesting key rotation.

B11. **Regulatory / venue-side policy failures.**
  - Venue suddenly delists an instrument we hold (e.g. OFAC sanctioning, exchange policy change).
  - Account flagged for compliance review → withdraw freeze.
  - Venue changes API contract without backward-compat (REST endpoint deprecated mid-flight).

### Block C — Circuit breakers (the auto-halt layer)

A circuit breaker is a rule that, when triggered, halts new exposure (orders blocked, strategies halted, position-balance-monitor enters no-new-actions). Auto-recovery is a sister rule that disarms the breaker once the condition clears (or requires manual operator re-arm if the breaker is stickier).

C1. **Breaker taxonomy — where do breakers live?**
  - **Per-venue breaker** — Bybit-specific rejection-rate breaker, OKX-specific WebSocket-stale breaker. Lives in the venue's adapter / order-flow layer.
  - **Per-archetype breaker** — carry archetype P&L drawdown > X bps in 5min. Lives in strategy-service.
  - **Per-account / per-client breaker** — single client's positions exceed limit. Lives in risk-and-exposure.
  - **Per-asset_group breaker** — all DeFi positions paused while chain reorg suspected. Lives at the asset_group orchestrator level.
  - **Global kill-switch** — halt EVERYTHING, manual or auto-armed from any catastrophic breaker.

  Audit: which breaker types exist today? Which scopes are missing? Cross-reference `codex/04-architecture/kill-switch-circuit-breaker.md` for current taxonomy.

C2. **Per-scenario breaker mapping.** For each Block B scenario, what's the breaker that catches it and what's the trigger condition?

  | Scenario (Block B row) | Detection signal | Breaker trigger condition | Action |
  | --- | --- | --- | --- |
  | B1 venue API key revoked | 401 / 403 rate > X% in Y seconds | per-venue breaker | halt-strategy on that venue + alert |
  | B2 venue WebSocket dropped | reconnect attempts > N in 60s | per-venue breaker | halt-strategy + auto-flat existing positions if duration > T |
  | B3 manifest phantom rows | phantom-audit cron returns drift | manifest breaker | block downstream consumption + alert |
  | B4 venue rejection spike | reject rate > 10% in 60s | per-venue breaker | halt-strategy on venue |
  | B4 on-chain reorg | block hash for tx changes within finality window | on-chain breaker | flatten leg + alert |
  | B5 inconsistent positions | strategy emits long+short same instrument | per-strategy breaker | halt-strategy + auto-flat |
  | ... | ... | ... | ... |

  Audit: fill in this table per Block B scenario. Identify which rows have NO breaker today (= silent failure mode).

C3. **Breaker-state observability.** A tripped breaker that nobody knows about is worse than no breaker (capital sits idle, alerts silently flood, operator confidence erodes). Audit:
  - Per-breaker, is there a `breaker_state` event published when armed / disarmed?
  - Is the breaker state visible in the deployment-ui?
  - Is there a daily report of "breakers that armed in the last 24h, why, when did they disarm" vs "breakers that have NEVER armed in production" (probably broken)?

C4. **Auto-recovery semantics.** Per the master plan Group F item 21 ("circuit breakers + kill switches + alerting + auto-recovery"). Audit:
  - Per breaker, is auto-recovery enabled or does it require manual operator re-arm?
  - Hysteresis — what's the gap between "trip" condition and "untrip" condition? Without hysteresis, a breaker flaps.
  - Cooldown — once tripped, how long must the condition stay clear before auto-disarm?
  - Failure-of-failure — what happens if auto-recovery itself errors (e.g. tries to query venue, venue still down)? Default-safe stance is "stay tripped" not "assume recovered."

C5. **Breaker priority + composition.** Multiple breakers can fire simultaneously. Audit:
  - Is there a priority order (kill-switch > asset_group > archetype > venue) so the most-restrictive one wins?
  - What happens if a per-venue breaker is tripped but the global kill-switch disarms? Does the per-venue breaker need its own clear, or does kill-switch override?

C6. **Per-asset_group breaker differences.**
  - **CeFi** — venue-side breakers are first-class (rejection rate, liquidity collapse, position-vs-margin).
  - **DeFi** — chain-side breakers (RPC stale, reorg, gas spike, oracle deviation) are first-class.
  - **Sports / prediction** — fixture-life-cycle breakers (fixture postponed, market suspended), data-source breakers (api_football outage during in-play).
  - **TradFi** — market-hours breakers (no trades during pre-market / post-close unless explicitly enabled), session breakers (half-day, holiday).

C7. **Pre-flight risk vs circuit breaker — same surface or parallel?** The DR-doc answer should be definitive — are they the SAME mechanism viewed from two angles (pre-flight is "block this order because the breaker is in tripped state"; circuit breaker is "the persistent state the pre-flight checks against") or parallel surfaces? Cross-reference `codex/04-architecture/kill-switch-circuit-breaker.md` for canonical answer; if codex is silent, this doc forces resolution.

C8. **Per-venue / per-chain rate-limit-aware breakers.** Per CLAUDE.md singleton-locked launchers (rate-limited adapters: SFI forward-poll, MTDS prediction-backfill). The same pattern applies to live trading: if an adapter exceeds the per-venue rate budget, the breaker should pre-emptively pause to avoid venue-side ban.

### Block D — Recovery playbooks (the operator-action layer)

Once a breaker fires, the operator + possibly an auto-recovery loop walks a documented procedure. Each playbook has owner + cadence + chaos-drill verification.

D1. **Per-scenario playbook catalogue.** For each Block B scenario, the playbook structure:
  - **Trigger** — which breaker / alert fired.
  - **Detection** — how operator confirms scope (queries to run, dashboards to check).
  - **Containment** — immediate steps to limit blast radius (e.g. halt all strategies on venue, freeze withdraws, alert backups).
  - **Diagnosis** — narrowing the root cause.
  - **Recovery** — restoring normal operation (rotate key, redeploy, manual fill correction, fund movement).
  - **Verification** — how operator confirms recovery (probe script, reconciliation re-run).
  - **Post-incident** — capture root cause for codex SSOT, update playbook if drift found.

  Audit: which Block B scenarios have a written playbook today vs operator-improvised vs not-documented.

D2. **Key compromise playbook (Block B1 wallet private key compromised).** Highest-stakes scenario:
  - Containment: identify scope (which wallets, which chains, which approvals); pause every running DeFi connector.
  - Recovery: deploy new wallet, transfer un-compromised funds (race against the attacker), revoke approvals on old wallet for all protocols, update Secret Manager + restart services.
  - Verification: every connector validates on-chain that the new wallet is correctly funded + approvals set + flash-loan-receiver-deployer is updated.
  - Open: do we have a pre-deployed "spare" wallet ready to swap in, or is wallet creation part of the playbook (slower)?
  - Boundary: this doc owns the **playbook**; sibling `api_keys_wallets_accounts_readiness` Block D6 owns the **approval registry artifact**.

D3. **Venue freeze playbook (Block B11 account flagged + withdraw freeze).** Capital is trapped at the venue:
  - Containment: halt new positions on the frozen venue; reroute hedge flow to alternate venues.
  - Diagnosis: contact venue support, gather compliance docs.
  - Recovery: cooperate with venue compliance; in worst-case (long freeze), plan around the trapped capital + close out delta-hedge legs at other venues.
  - Open: is there a playbook for "we lost X% of perp hedge capacity for Y weeks because Bybit froze us"?

D4. **Cloud region failover playbook (Block B2 GCP region outage).** Per master plan AWS↔GCP cloud parity goal:
  - Containment: traffic-shift to surviving cloud (assumes cloud parity is real, not aspirational).
  - Recovery: when failed region comes back, sync state forward.
  - Open: is cloud-parity actually live for trading services, or is it data-only (manifest replicated, but execution-service is GCP-only)?
  - Open: does the AWS-side have provisioned + warm Cloud Run / ECS replicas, or is it cold-spin-up?

D5. **On-chain reorg playbook (Block B4 reorg invalidating booked fill).**
  - Containment: pause new on-chain trades on affected chain.
  - Diagnosis: identify which booked fills were invalidated; recompute strategy state.
  - Recovery: re-submit invalidated trades or accept the position-state delta; reconcile execution-service ledger with on-chain truth.
  - Open: is reorg-detection live today (Block A3), or theoretical?

D6. **Manifest corruption playbook (Block B6 manifest CAS race).**
  - Containment: pause every backfill VM.
  - Diagnosis: run phantom audit; find drift rows.
  - Recovery: reconcile per the phantom-audit script's `--apply-flips`; restart backfills with proper per-VM shard isolation.
  - Open: has the phantom-audit ever been run with `--apply-flips` against production state, or is this dry-run only?

D7. **Telegram / Anthropic / GitHub bot down playbook (Block B2 auxiliary connectivity).**
  - Containment: alerting falls back to alternate channel (e.g. PagerDuty, email, secondary Telegram bot).
  - Recovery: rotate bot token if root cause is auth.
  - Open: is the secondary alerting channel actually wired, or is Telegram the only path? "Single-channel alerting" is itself a Block B scenario.

D8. **Multi-agent collision playbook (Block B8 foot-gun #1).** Per CLAUDE.md "two teammates × multiple parallel agents":
  - Containment: pause own work, do not push.
  - Diagnosis: `git diff --cached --stat` (no path arg), identify foreign work in index.
  - Recovery: surgical un-stage via `git restore --staged <file>` OR pathspec commit form `git commit --only -- <file>`.
  - Open: is the pre-commit-check rule QG-enforced, or trust-based?

D9. **Playbook owner registry.** Per `Runbook Execution-Owner SSOT`:
  - Per playbook, named owner (a service / a specific operator / a cron / a Tab in a daily work-split).
  - Cadence — chaos-drill how often (monthly DR exercise? Quarterly? Pre-cutover only?).
  - Verifier — what's the green signal that the drill passed (event-stream evidence, reconciliation re-run, alert acknowledgement).
  - `last_executed` — required field per the HARD RULE.

D10. **Chaos drill design.** A playbook that has never been chaos-drilled is unverified. Audit:
  - Pre-cutover, which playbooks must be chaos-drilled at least once against real (or staging-real) infra? E.g. revoke a real test API key, force a real reorg via Tenderly fork, trigger a real Cloud Run deployment failure.
  - Cadence post-cutover — quarterly? Monthly? On every major-bump?
  - Drill scope — single-scenario at a time, or correlated multi-scenario (e.g. cloud outage during venue rejection spike — both breakers fire simultaneously)?

### Block E — State persistence + replay (the rebuild layer)

If everything dies, can we rebuild state from event-stream + manifest + on-chain + venue REST without operator-curated rescue files?

E1. **Event-stream as source of truth.** Per CLAUDE.md the event-stream at `gs://{pid}-events/...` is workspace-durable. Audit:
  - Per service, can full state be replayed from events?
  - Replay performance — at what scale does replay take longer than the disaster window the operator can tolerate?
  - Snapshot cadence — periodic state snapshots so replay doesn't have to start from genesis.

E2. **Manifest as durable index.** Per CLAUDE.md the v5 availability manifest is the SSOT for "what data exists where." Audit:
  - If the manifest is corrupted, can it be rebuilt from on-disk parquets + reverse-engineered shard keys?
  - Phantom-audit + parquet-walk should reconstruct manifest state; verify this works end-to-end.

E3. **On-chain as immutable truth.** For DeFi positions, the chain itself is the durable record. Audit:
  - Per protocol, can execution-service's expected state be reconstructed from on-chain reads alone, or does it depend on local state we'd lose?
  - Decimal-precision parity — chain reports balances in raw units; we display in decimals; reconstruction must round-trip without drift.

E4. **Venue REST as ground-truth for CeFi.** Audit:
  - Per venue, the set of REST endpoints that together fully describe account state (positions, balances, open orders, fills, funding history).
  - Documented as a "rebuild-CeFi-state-from-Bybit-alone" recipe per venue.

E5. **Custody as fund-record source.** Audit:
  - Copper / CEFFU APIs let us reconstruct deposits + withdrawals + current holdings.
  - Reconstruction recipe documented?

E6. **Operator-curated rescue files — banned or constrained?** If rebuild requires an operator-edited spreadsheet of "here's the fills I think happened," that's a fragility point. Goal: rebuild path uses only durable upstream sources.

### Block F — Cross-cloud failover + parity

The master plan has AWS↔GCP cloud parity as a goal. Audit DR specifically.

F1. **What's actually parity-live today?** Tab 4 shipped DeFi buckets on both clouds; bucket-naming SSOT lifted to UTL; Storage Transfer Service active. Beyond data:
  - Cloud Run replicas — does AWS have ECS / Fargate or Lambda equivalents running, or is it cold?
  - Pub/Sub equivalent — SNS/SQS provisioned + tested?
  - Secret Manager parity — all credentials have AWS Secrets Manager versions?
  - Service-account parity — the IAM matrix from sibling api_keys doc Block A1 has AWS equivalents.

F2. **Failover trigger + execution.**
  - Detection — what signal fires "GCP region down → switch to AWS"?
  - Switch mechanism — manual operator action, automatic via DNS health-check, automatic via service-discovery layer?
  - State-sync — events + manifest + custody-balance-cache must be live on AWS at switchover time.

F3. **Failback to GCP.** Once GCP region recovers, how do we sync forward + cut traffic back?

F4. **Per-asset_group cloud-parity audit.** DeFi was Tab 4 scoped — what's the state per other asset_groups (CeFi / TradFi / sports / prediction)?

### Block G — Per-venue / per-custody / per-source DR specifics

Each upstream system has its own DR profile. Audit each.

G1. **Per-venue DR.** For each of Bybit / Deribit / Binance / OKX / Hyperliquid / Aster / Upbit / Kraken / Bitfinex / Bitget:
  - Historical outage frequency + duration.
  - Auth-rotation cadence + notice period (Binance has rotated auth; OKX has historical key revocations).
  - Withdraw-freeze policy (compliance reviews).
  - Disaster-mode posture (does Bybit have a "trade-only-mode" if their settlement layer is down?).
  - Our exposure when this venue is unavailable — is the strategy degradable to N-1 venues, or does it require all 6?

G2. **Per-chain DR.** For each of Ethereum / Arbitrum / Base / Polygon / Solana:
  - Reorg frequency + max-historical-depth.
  - RPC provider failover (Alchemy → public → Helius).
  - Gas-spike threshold for breaker trip.
  - Chain-pause / contract-pause history (Solana has had network-wide pauses).
  - Restaking / slashing risk per LST.

G3. **Per-custody DR.** Copper + CEFFU:
  - Outage history if any.
  - SLA for sweep operations.
  - Recovery if Copper goes offline mid-settlement.
  - Cold-storage fallback.

G4. **Per-data-source DR.** Tardis / Databento / Barchart / api_football / footystats / etc.:
  - Outage history.
  - Coverage during outage (is there a degraded mode where we proceed on stale-but-flagged data?).
  - Per CLAUDE.md, *honest absence vs fake placeholders*: if a source goes down, every consumer must `record_failed` not `record_empty`, and downstream must `DependencyError(fail_fast=True)` rather than silent NaN.

### Block H — On-chain DR specifics

DeFi has unique DR concerns vs CeFi.

H1. **Hot-wallet vs cold-wallet topology.** Audit:
  - Is every operator wallet a hot wallet (fast-trading, exposed if compromised), or is there cold-storage for "long-term hold" assets with periodic sweep to hot?
  - Hardware-key vs software-key — are private keys derived from HSM / Fireblocks signer / KMS, or stored as raw bytes in Secret Manager?

H2. **Approval revocation procedure.** A compromised wallet has cumulative `approve()` allowances. Recovery requires revoking each. Audit:
  - Documented list of "every approval that exists per (chain, wallet, protocol)."
  - Revocation script that walks the list + emits `approve(spender, 0)` for each.
  - Per CLAUDE.md "Per-protocol approvals — pre-signed token allowances" (api_keys doc Block D6) — this needs to be maintained as an SSOT.

H3. **MEV / front-running DR.** When a swap is sandwiched:
  - Detection — fill price > expected + slippage tolerance.
  - Containment — Flashbots / private mempool routing default-on for sensitive trades?
  - Recovery — accept the loss and continue, or halt that DEX path.

H4. **Oracle deviation DR.** Pyth + Chainlink:
  - Primary + fallback oracle per asset.
  - Deviation threshold (primary vs fallback > X%) → halt trading on that asset.
  - Single-oracle dependence audit — any asset with no fallback?

H5. **Bridge / cross-chain DR.** If we move USDC ETH→SOL via CCTP and the bridge stalls:
  - Containment — pause downstream trades that depend on the cross-chain leg.
  - Diagnosis — query bridge state.
  - Recovery — wait or use alternate bridge.

### Block I — End-to-end audit recipe + chaos drills

Bringing it all together — what's the operator's pre-cutover gate + ongoing DR posture verification?

I1. **Single DR readiness probe script.** Analogous to the api_keys doc Block I credential-probe — a script that:
  - Runs every reconciliation audit (Block A) against live state and reports green/red per surface.
  - Verifies every circuit breaker (Block C) is in expected state (armed / disarmed / cooling-down).
  - Verifies every recovery playbook (Block D) has `execution.owner` populated + `last_executed` within cadence.
  - Verifies cloud-parity (Block F) — every primary-cloud resource has a matching secondary-cloud resource.
  - Outputs per-scenario green/red + a final sign-off line.

I2. **Pre-cutover DR drill catalogue.** Before May-23:
  - Each Block B scenario has at least one chaos drill scheduled + executed against staging or fork-of-prod.
  - Drill evidence — event-stream link, reconciliation re-run output, alert acknowledgement.
  - Drill-pass criteria per scenario.

I3. **Continuous DR posture monitoring.** Post-cutover:
  - Daily: reconciliation audits run + green.
  - Weekly: phantom-audit + playbook owner-attestation.
  - Monthly: chaos drill (rotating subset of Block B scenarios).
  - Quarterly: full playbook walkthrough with operator + secondary operator (so DR isn't single-operator-dependent).

I4. **Master plan continuous-verification column.** Per the HARD RULE, every Group F + G item needs a continuous-verification path. DR scenarios contribute to:
  - Item 18 (batch-vs-live reconciliation + P&L attribution) — Block A9.
  - Item 21 (circuit breakers + kill switches + alerting + auto-recovery) — Blocks C + D.
  - Item 22 (live testnet replicating prod) — Block I drill catalogue.
  - Item 23 (DART manual-trade gate) — composes with playbook D9 owner registry.

I5. **DR SSOT — the canonical doc.** Should be `codex/14-playbooks/disaster-recovery/README.md` (NEW) cross-linking every per-scenario playbook + per-breaker spec + per-reconciliation-rule definition. Not implicit in CLAUDE.md or scattered across plans.

I6. **Pre-cutover DR sign-off gate.** Define the explicit gate the master plan uses to declare "DR is GO for live cutover":
  - All Block A reconciliation audits green within last 24h.
  - All Block B scenarios have a documented playbook + primary owner.
  - All Block C breakers armed-or-disarmed-correctly + tested-at-least-once-in-production-or-staging.
  - All Block D playbooks have `execution.owner` populated + chaos-drill evidence within last quarter.
  - All Block E rebuild paths verified (event-stream replay + on-chain reconstruction).
  - All Block F cross-cloud failover paths tested at least once.
  - The DR readiness probe script's `last_executed` stamp is within last 24h before cutover.

## What "answered" looks like

Per the SSOT bar at the top of this doc — every bullet below must be `🟢 ANSWERED` (with audit evidence cited) before the doc closes. No `🟡 partial`, no `🔴 GAP`, no `TBD`.

- A canonical plan exists in `plans/active/disaster_recovery_reconciliation_circuit_breakers_<date>.md` (or fold into infra-master if scoped narrowly). Plan body has per-Block phase + per-scenario todo (one row per Block B scenario × detection-signal × breaker × playbook).
- A codex SSOT in `codex/14-playbooks/disaster-recovery/README.md` (NEW) enumerates every DR scenario with: detection signal, circuit breaker, recovery playbook, owner, cadence, chaos-drill evidence. Sub-pages per Block (per-venue / per-chain / per-custody / per-data-source).
- A workspace-wide `scripts/audit/dr-readiness-probe.sh` exists, owned by deployment-service, runnable per-asset_group + per-mode, with the Block I.1 probe set. Output: per-scenario green/red + final sign-off.
- The master plan's continuous-verification column references this probe + the per-playbook chaos-drill cadence for every Group F + G DR-dependent gate.
- Every Block A reconciliation rule has explicit tolerance + cadence + alerting in UAC AlertCode taxonomy (composes with `alerting_service_live_rules_2026_05_07.md`).
- Every Block C circuit breaker has test evidence — at least one chaos drill in production or staging where the breaker tripped under realistic conditions and the system halted safely.
- Every Block D playbook has `execution.owner` + `last_executed` populated; chaos-drill cadence honored.
- Per-archetype DR readiness checklists exist so the operator can answer "is `carry_staked_basis` DR-ready today?" without running the full probe.
- A real cutover-grade DR drill has executed end-to-end: a planned outage of one venue + one chain + one cloud region simultaneously, with the system halting safely + reconciling state on recovery.
- Audit findings (next section) are populated for EVERY sub-question A1-A9, B1-B11, C1-C8, D1-D10, E1-E6, F1-F4, G1-G4, H1-H5, I1-I6 — with `Code state` / `Coverage state` / `Detection state` / `Breaker state` / `Playbook state` / `Real-system state` / `Cross-cloud state` / `Per-mode state` / `Per-archetype state` / `Codex state` / `Gap analysis` cited from real audit evidence (file:line, codex-doc, commit-sha, event-stream link).
- Operator sign-off recorded in `## Operator notes / answers` confirming "DR posture is best-possible and complete for live-DeFi May-23 cutover."

## Audit findings (to be filled by audit pass)

For each sub-question above (A1-A9, B1-B11, C1-C8, D1-D10, E1-E6, F1-F4, G1-G4, H1-H5, I1-I6):

- **Code state**: <which repo + file:line implements / consumes the reconciliation/breaker/playbook surface; existing factory/event-handler patterns>
- **Coverage state**: <which scenarios / venues / chains / custodies are covered today vs not>
- **Detection state**: <does the detection signal exist; latency between condition and detection; alert wiring>
- **Breaker state**: <is the breaker wired; has it ever tripped in production; auto-recovery semantics>
- **Playbook state**: <written / unwritten / operator-improvised; last execution date; owner declared>
- **Real-system state**: <when was this DR surface last verified end-to-end against real or staging-real infra; chaos-drill evidence>
- **Cross-cloud state**: <does the surface have GCP + AWS parity; failover-tested>
- **Per-mode state**: <which of paper / batch / live actually exercises this surface>
- **Per-archetype state**: <which archetypes block on this DR surface being live>
- **Codex state**: <which codex doc covers it, drift vs current code, gaps>
- **Gap analysis**: <what's missing for the "answered" criteria; concrete blockers; named successor plan if cut to post-May-23>

## Operator notes / answers

(Empty — to be filled during iteration.)

Operator clarifications likely needed during iteration:

- DR scope vs sibling risk surface — circuit-breakers + kill-switches are referenced in `codex/04-architecture/kill-switch-circuit-breaker.md`. Definitive answer to C7: "are circuit breakers a subset of risk pre-flight or a parallel surface" determines doc-ownership boundary.
- Chaos-drill cadence comfort — monthly / quarterly / pre-cutover only? Cost vs coverage trade-off.
- Per-archetype DR priority — which Block B scenarios are May-23 P0 (must be drilled) vs P1 (post-May-23)?
- Cloud-parity DR scope — full DR failover for both clouds, or DR-on-GCP-primary with AWS-as-data-only-replica?
- Wallet topology — single hot-wallet per chain (simpler DR, larger blast radius) vs multi-wallet isolation per archetype (smaller blast radius, more credentials to rotate)?
- Custody DR posture — Copper + CEFFU as primary + secondary, or single-custody with self-custody fallback?

## Iteration log

| Date | Author | Change |
| ---- | ------ | ------ |
| 2026-05-08 | ikenna + main agent | Initial draft created |
| 2026-05-09 | main agent | SSOT bar codified at top; recreated after multi-agent collision wiped initial draft |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD (likely `plans/active/disaster_recovery_reconciliation_circuit_breakers_<date>.md` with sub-plan fan-out per Block, or fold reconciliation-audit into infra-master + circuit-breakers/playbooks into a dedicated DR plan)
- **Plan type**: `infra` (cloud + breaker wiring + reconciliation infrastructure) with strands of `code` (per-service breaker hooks + reconciler implementations + audit-script) + `business` (custody DR procedures, venue-relationship-management for freeze playbooks)
- **Owner side**: likely both — Ikenna for cross-cutting design (breaker taxonomy, recovery playbook authoring, chaos-drill cadence, custody-DR judgment), Harsh for the audit-script + per-Block reconciler implementations + breaker-state observability + per-venue playbook implementations
- **Codex SSOTs touched**:
  - `codex/14-playbooks/disaster-recovery/README.md` — NEW — workspace DR SSOT
  - `codex/14-playbooks/disaster-recovery/per-venue.md` — NEW — per-venue DR profiles
  - `codex/14-playbooks/disaster-recovery/per-chain.md` — NEW — per-chain DR profiles
  - `codex/14-playbooks/disaster-recovery/per-custody.md` — NEW — Copper + CEFFU DR profiles
  - `codex/14-playbooks/disaster-recovery/circuit-breaker-taxonomy.md` — NEW — breaker scopes + composition + auto-recovery
  - `codex/14-playbooks/disaster-recovery/reconciliation-audit-rules.md` — NEW — per-surface reconciliation tolerance + cadence
  - `codex/04-architecture/kill-switch-circuit-breaker.md` — UPDATE — extend with breaker-composition + cross-reference DR taxonomy
  - `codex/04-architecture/shard-level-failure-isolation.md` — UPDATE — extend with breaker-composition
  - `codex/02-data/availability-manifest-and-data-status.md` — UPDATE — phantom-audit cadence + DR rebuild
  - `codex/02-data/honest-absence-downstream-handling.md` — UPDATE — per-data-source outage handling
- **Cross-plan dependencies**:
  - `plans/active/master_to_live_defi_2026_05_23.md` — Group F items 17/18/21/22/23 reference this DR plan
  - `plans/epics/infrastructure_master_2026_05_07.md` — cloud-parity DR (Block F) feeds infra master scope
  - `plans/epics/cefi_master_2026_05_07.md` — per-venue DR (Block G1) feeds cefi master scope
  - `plans/epics/defi_master_2026_05_07.md` — per-chain + on-chain DR (Blocks G2 + H) feeds defi master scope
  - `plans/active/alerting_service_live_rules_2026_05_07.md` — every Block A reconciliation rule + Block C breaker emits via UAC AlertCode taxonomy
  - `plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md` — credential-rotation playbook (Block D2) consumes credential-matrix
  - `plans/questions/wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md` — treasury reconciliation (Block A2) consumes wallet/treasury shape
  - `plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md` — chaos-drill harness composes with paper-vs-live workflow
- **Estimated scope**: Large — ~15-20 AI-days for full Block A-I implementation. Breakdown: Block A (reconciliation infra) ~3d, Block B (scenario catalogue) ~1d (mostly enumeration + cross-link), Block C (circuit breakers) ~3d, Block D (playbooks) ~3d, Block E (rebuild paths) ~2d, Block F (cross-cloud) ~2d, Block G (per-venue/chain/custody/source) ~3d, Block H (on-chain specifics) ~1d, Block I (audit-script + chaos-drill harness) ~2d.

## Plan extraction record

(Empty — fills when the plan ships.)
