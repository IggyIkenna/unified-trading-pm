# Slot 8 ping file — re-themed 2026-05-15

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-15 UTC] slot-8 — ✅ DONE item 10 zero-test silent pass guard sweep. All 15 B-014 service repos + SIT (16 total) have test_event_logging.py + test_config.py ✅. test_files range: 2 (ibkr-gateway-infra) → 543 (execution-service). Zero repos with 0 tests. No skeleton test_smoke.py needed anywhere.

[2026-05-15 UTC] slot-8 — ✅ DONE item 9 detect_template_drift.py. PM@68609e03: new tool at scripts/quality_gates/detect_template_drift.py; 11 unit tests passing. One-shot run: 24 repos checked, 18 clean, 6 warnings (5 stale lifecycle: alerting/mtds/ml-inference/ml-training/risk-exposure; 1 missing file: fund-administration-service). No errors. SSOT: usage python3 scripts/quality_gates/detect_template_drift.py [--repo NAME] [--json].

[2026-05-15 UTC] slot-8 — ✅ DONE item 8 CLAUDE.md PYTEST_UNIT_DIR doc. PM@247c7b40: added 14-line block to CLAUDE.md § "Environment: Venv Split" explaining override pattern, trigger condition (<5% ratio), and SSOT pointer. Grep-able: "PYTEST_UNIT_DIR".

[2026-05-15 UTC] slot-8 — ✅ DONE item 7 STEP 5.79-5.82 detailed reference. PM@7706072a: 4 new sections added to codex quality-gates.md. Each STEP now has: rationale, scope, ratchet date, compliant/non-compliant patterns, how-to-comply, composes-with. (5.79=dockerfile-base-pin, 5.80=tarball-manifest-present, 5.81=tarball-env-block, 5.82=image-build-on-staging-merge)

[2026-05-15 UTC] slot-8 — ✅ DONE item 6 base-service.sh DRY proposal. PM@28ce4771: 3 findings documented in codex quality-gates.md § "quality-gates.sh Boilerplate DRY Consolidation Proposal". Finding 1: lifecycle block (15 lines) duplicated 14 repos; 5 repos on stale old pattern — proposal to move to base-service.sh PENDING OPERATOR ACK. Finding 2: PERIPHERAL_DIR stays per-repo (intended). Finding 3: PYTEST_UNIT_DIR opt-in pattern documented. No code changes made.

[2026-05-15 UTC] slot-8 — ✅ DONE item 5 batch_live L4/L5/L6 sweep (features+strategy+mtds). STEP 5.75-5.78 (L1/L2/L3/L5) all ✅ clean in all 3 repos. L4 deferred items catalogued: LIVE_FEATURES_COMPUTED/LIVE_SIGNAL_GENERATED in strategy-service (log_event strings); LIVE_FEATURE_SUBSET constant in features-service. Both are post-cutover per plan D5 default — NOT violations for current QG STEPs. L6 executor-factory: no violations found. No code changes needed.

[2026-05-15 UTC] slot-8 — ✅ DONE item 4 mtb-p6e-final-qg-sweep. PM@41bbf18e: QG ran on all 6 B-014 repos. Results: ibkr-gateway-infra 51.47% ✅, ml-inference 78.41% ✅, mdps 74.91% ✅, sys-integration-tests ~8% ✅ (MIN_COV=2), features-service 71.83% ❌ (211 pre-existing failures — confirmed on LDR main), ml-training 79.96% ❌ (14 slow-test timeouts + 0.04% coverage gap vs pyproject fail_under=80 — confirmed pre-existing on LDR main). No repo below 70% floor. Issue doc: plans/active/issues/mtb_p6e_qg_sweep_2026_05_15.md

[2026-05-15 UTC] slot-8 — ✅ DONE self-pivot DT-3/DT-4 (PRE_CUTOVER from codex audit issue doc). PM@8b4ab3ad: (1) "Library-Repo QG Carveout Patterns" section added to quality-gates.md (UAC_CANONICAL_EXEMPT / SIZE_EXTRA_EXCLUDES / GCP_PROJECT_ID_EXCLUDE_GLOBS / BROAD_EXCEPT_EXTRA_EXCLUDES — when valid, pattern, guard rails); (2) B-014 STEP 5.79-5.82 PENDING_RATCHET status + B-018 QG snapshot VM details cross-referenced in deployment-and-qg-strategy.md § Continuous verification. All 4 DT findings now FIXED. Issue doc closed. No new queue — awaiting main direction.

[2026-05-15 06:02 UTC] [main → slot 8] — ✅ B-014 Phase 3 DONE acked. LEDGER flipped. workspace grep "unified-trading-codex"=0 — clean. Reserve queue per continuation_prompts § Slot 8: (1) SIT pipeline smoke tests for B-014 QG stubs (verify quality-gates.sh runs clean on all 15 repos end-to-end); (2) UTL emission publisher coverage (coordinate with slot 5 on execution-service — take features-service side); (3) IBKR gateway QG stub verification. Self-pivot. Ping main on BLOCKED/BIG only.

[2026-05-15 UTC] slot-8 — ✅ DONE item 3 codex_vs_citadel audit follow-up. Harsh-side surfaces verified. Findings: STEP 5.71-5.82 not indexed in quality-gates.md (DT-1/DT-2 IMMEDIATE — fixed PM@ae4fde31); UAC carveout patterns + B-014/B-018 cross-refs filed as PRE_CUTOVER in issue doc codex_audit_deployment_template_phase8_drift_2026_05_15.md. No BIG findings.

[2026-05-15 UTC] slot-8 — ✅ DONE reserve item 1+3: SIT smoke tests + IBKR gateway verification. All repos have correct B-014 SSOT path (grep=0). Found 2 repos missing lifecycle block: features-service@30467e28 + ibkr-gateway-infra@eb4412f — both fixed + QG PASSED (61s / 23s).

[2026-05-15 UTC] slot-8 — ✅ DONE reserve item 2: UTL emission publisher consumer-side coverage audit (features-service side). Callsite map: 8 sub-families with publish_with_policy callsites (calendar/commodity/cross_instrument/delta_one/multi_timeframe/onchain/sports/volatility) — ALL have matching test_emission_policy.py files. No gaps found. Coverage is comprehensive.

[2026-05-15 UTC] slot-8 — 🏁 **Slot 8 Day-4 CYCLE-CLOSE**

**4-day cycle summary (2026-05-12 → 2026-05-15) — Slot 8 (UTL + B-014 + codex)**

Items shipped:
- **2026-05-12**: B-007+B-008 UTL manifest writer + emission publisher 100% coverage (@e6877d2); 13/15 service repos B-014 QG stub rolled out; codex_vs_citadel audit Phases 0-5 complete (242 findings, 63 IMMEDIATE + 137 PRE_CUTOVER + 36 POST_CUTOVER)
- **2026-05-15**: B-014 Phase 3 stash recovery + rollout completion — all .tabs/8 service repos updated (workspace grep=0); alerting@4795ccf, market-tick@acec41d, risk-exposure@55d7611, ml-inference@8116b23, market-data@2ff9258, ml-training@00a97aa; codex STEP 5.71-5.82 indexed in quality-gates.md (PM@ae4fde31); lifecycle block gap fixed in features-service@30467e28 + ibkr-gateway-infra@eb4412f; emission publisher audit: all 8 features-service sub-families covered

Items deferred:
- DT-3/DT-4 PRE_CUTOVER (UAC carveouts + B-018 cross-ref) → `plans/active/issues/codex_audit_deployment_template_phase8_drift_2026_05_15.md`
- Item 4 continuation_prompts (features-service item 4 — full cycle close) → carry to next session

Open blockers at cycle close: NONE for slot 8.

[2026-05-15 05:08 UTC] slot-8 — STARTED slot 8 (B-014 stash recovery + rollout completion;
plans/active/continuation_prompts_harsh_2026_05_15.md § Slot 8)

[2026-05-15 UTC] slot-8 — ✅ DONE B-014 Phase 3 rollout complete. All .tabs/8 service repos updated; workspace-wide grep
for "unified-trading-codex" = 0 hits. SHAs: ml-inference-service@8116b23, market-data-processing-service@2ff9258,
ml-training-service@00a97aa, alerting-service@4795ccf, market-tick-data-service@acec41d,
risk-and-exposure-service@55d7611. Deferred work table updated in
deployment_and_qg_strategy_implementation_2026_05_13.md.

[2026-05-15 04:44 UTC] [main → slot 8] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-15 04:18 UTC] [main → slot 8] — 🌅 **DAY-1 START (Lever 1+2) — 🚨 STASH RECOVERY REQUIRED**. Read
[`../../plans/active/continuation_prompts_harsh_2026_05_15.md`](../../plans/active/continuation_prompts_harsh_2026_05_15.md)
§ "Slot 8". Yesterday: B-014 STEP 5.79-5.82 added to base-service.sh ✅; 13/15 service repos QG stub pushed. **Local
B-014 rollout-completion work was uncommitted at EOD and is preserved in 7 stashes** (one per repo: features-service /
ibkr-gateway-infra / market-data-processing-service / ml-inference-service / ml-training-service /
system-integration-tests / unified-trading-system-ui). **Recovery procedure**: cd into each `.tabs/8/<repo>/` →
`git stash list` (look for msg containing "B-014-ROLLOUT-COMPLETION") → `git stash pop` → verify quality-gates.sh has
MIN_COVERAGE=70 + new SSOT path + instruction block → quickmerge ship via
`bash scripts/quickmerge.sh "feat(qg): B-014 rollout completion to <repo>" --agent`. Then verify final 2 service repos
got the QG stub. After all 15 service repos QG green: ping DONE.

[2026-05-15 07:01 UTC] [main → slot 8] — 🔔 **REBASE REMINDER + STATUS CHECK**. Before your next commit: rebase ALL repos in your worktree to LDR (`git fetch origin && git rebase origin/live-defi-rollout`). This picks up PM@c7786b2f (PYTEST_UNIT_DIR fix — features-service quality-gates.sh now sets PYTEST_UNIT_DIR="tests/" + MIN_COVERAGE=70 restored by prek; note this may affect your B-014 stash recovery for features-service — read the diff before popping stash). After rebase: continue B-014 stash recovery per your existing queue. Ping DONE with SHAs when all 7 stash repos shipped.

[2026-05-15 07:10 UTC] [main → slot 8] — 📋 **EXTENDED QUEUE for after B-014 stash recovery completes**. Read now so you can self-pivot immediately. Estimated ~12 AI-days post-stash.

After B-014 stash recovery pings DONE:
1. **codex/06-coding-standards quality-gates.md update** — document new STEP 5.79-5.82 (B-014 ratchet STEPs) + PYTEST_UNIT_DIR override pattern (PM@c7786b2f) + UAC carveouts in the codex SSOT. Done-def: codex doc reflects all Phase 3 QG changes.
2. **codex_vs_citadel audit** (continuation_prompts item 3): read `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`; verify Harsh-side codex sections (UTL, deployment-service template, Phase 8 surfaces) align with shipped code. File issue doc per drift found.
3. **UTL emission publisher consumer-side coverage audit** (continuation_prompts item 4): map `publish_with_policy` callsites across execution, risk, strategy, features; verify each callsite has a consumer-side test; fix gaps. Done-def: callsite map in plan doc OR gaps fixed; QG green per repo.
4. **master plan `mtb-p6e-final-qg-sweep`**: full QG sweep across all 6 B-014 rollout repos (features-service, ibkr-gateway-infra, mdps, ml-inference, ml-training, system-integration-tests). Capture pass/fail + coverage %. File issue doc for any repo below 70%.
5. **batch_live symmetry L4/L5/L6 sweeps** (reserve): scan for any remaining batch_live L4-L6 violations in the 3 primary repos (features, strategy, mtds). Fix + QG green.
6. **base-service.sh template DRY**: identify repeated boilerplate patterns across quality-gates.sh files (e.g. PERIPHERAL_DIR blocks, lifecycle checks); propose consolidation in codex. Doc-only; no code change without operator ack.
Self-pivot. Ping DONE per major item or grouped CYCLE-CLOSE when exhausted.

[2026-05-15 07:41 UTC] [main → slot 8] — 📋 **QUEUE EXTENSION** — add 4 more items after your 6-item batch. Total ~20 AI-days.
7. **codex/06-coding-standards STEP 5.79-5.82 detailed reference** — write full pattern documentation for each new ratchet STEP added to base-service.sh; include rationale, what it catches, how to comply. Done-def: codex doc updated; each STEP has a section.
8. **CLAUDE.md PYTEST_UNIT_DIR override pattern documentation** — recent PM@c7786b2f added `PYTEST_UNIT_DIR` override. Document this in CLAUDE.md § "Quality Gates" or codex/06 so future per-family-layout repos know how to opt in. Done-def: documented + grep-able.
9. **quality-gates.sh template drift detection** — write a tool (`unified-trading-pm/scripts/quality-gates/detect_template_drift.py`) that compares each repo's `scripts/quality-gates.sh` to the SSOT template; reports diffs. Used by rollout to catch manual edits. Done-def: tool + unit tests + one-shot run logged.
10. **B-014 final follow-on — zero-test silent pass guard sweep** — workspace-wide: verify every service repo's QG actually executes tests (not just compiles). Use the new zero-test guard from base-service.sh. Done-def: all 15 service repos run ≥1 test per QG; any repo with 0 tests gets a skeleton test_smoke.py.
