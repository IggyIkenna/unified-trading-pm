---
doc_type: issue
title:
  "market-tick-data-service quality-gates.sh Codex compliance is red repo-wide (pre-existing) — blocks ALL quickmerge
  pushes to this repo"
summary:
  'While shipping a real Fluid lending_indices fix (fluid_adapter.py — ContractCustomError root-cause fix, see
  DEFI_INSTRUMENTS.md), quality-gates.sh --no-fix failed on ''Codex compliance FAILED: 1 violations (max allowed: 0)'',
  root cause ''Empty string fallback — fail fast'' (`.get("key", "")` pattern banned by
  scripts/quality-gates-base/base-service.sh). Verified via a controlled git-stash A/B test that this is 100%
  pre-existing and NOT introduced by the Fluid fix: 338 matching call sites exist across market_tick_data_service/ with
  the fix''s diff stashed out (i.e. on unmodified HEAD). Independently confirmed via real remote CI: `gh run list
  --branch live-defi-rollout` shows the most recent quality-gates-v2 run (28970063657, triggered 2026-07-08T19:31:49Z —
  before this session''s Fluid edits) already FAILED with the identical ''Empty string fallback'' / ''Codex compliance
  FAILED: 1 violations'' signature. `.qg_last_passed_sha` is stale (points to an ancestor commit, c7045054), meaning
  this repo has not had a clean local quality-gates.sh pass in a while. quickmerge.sh''s `--skip-codex` flag is
  explicitly DISABLED (WS-L #1014, 2026-06-26 operator policy: ''the full quality gate is mandatory before every push...
  no skip flags''), so there is currently no way to quickmerge ANY change to this repo, including changes fully
  unrelated to this violation class.'
status: open
nature: issue
asset_group: [defi]
stage: [data, meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, codex-compliance, ci-blocking, empty-string-fallback, technical-debt]
related: []
created: 2026-07-08
parent_epic: instruments_master
priority: P1
source:
  "Discovered while shipping instruments-service/market-tick-data-service fixes for 4 real DeFi data-pipeline bugs
  (Fluid lending_indices ContractCustomError, DEX-pool TVL-cutoff coverage gap, LST/VAULT key-field mismatch, DEX-pool
  bare-address code-verification) — the Fluid fix (fluid_adapter.py) is complete, tested, and verified with real
  on-chain calls, but cannot be pushed via the mandatory quickmerge.sh path because the repo's quality gate is
  independently red for unrelated pre-existing reasons."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
last_updated: 2026-07-16
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **CI-BLOCKING finding — every quickmerge push to `market-tick-data-service` is currently blocked**, not just the
> author's own change. Confirmed independently via real remote CI (not just a local run).

## What was found

`instruments_service`/`market-tick-data-service` quality gates were run to ship a real fix
(`market_tick_data_service/market_interface/adapters/defi/fluid_adapter.py` — Fluid's `lending_indices` MTDS collector
was 100% broken on an uncaught `ContractCustomError`; root cause and fix documented in
`instruments-service/docs/DEFI_INSTRUMENTS.md`). `bash scripts/quality-gates.sh --no-fix` failed:

```
❌ Empty string fallback — fail fast
...
❌ Codex compliance FAILED: 1 violations (max allowed: 0)
```

The offending pattern (`scripts/quality-gates-base/base-service.sh` — a PM-repo SSOT shared by every service) bans
`.get("key", "")`-shaped dict access anywhere in `$SOURCE_DIR` (tests excluded), zero tolerance, no baseline-ratchet
mechanism (unlike the DTZ/TID251/fallback-import checks, which explicitly allow existing debt as long as it doesn't
grow).

**Verified NOT caused by the Fluid fix** — `git stash` the fix's diff (isolating it from the rest of the tree) and
re-run the same grep the gate uses:

```
grep -rnE '\.get\(["\x27][[:alnum:]_]+["\x27]\s*,\s*["\x27]["\x27]\)' --include="*.py" market_tick_data_service/ \
  | grep -v "/tests/" | grep -v "noqa: qg-empty-fallback" | wc -l
# 338   (on unmodified HEAD, fix fully stashed out)
```

The Fluid fix's own diff contains exactly one new `.get(` call (`self._token_decimals_cache.get(cache_key)`, no default
argument at all — does not match the banned pattern).

**Verified independently via real remote CI** (not just this local run):

```
gh run list --branch live-defi-rollout --repo <org>/market-tick-data-service --limit 5
# completed  failure  quality-gates-v2  ...  28970063657  ...  2026-07-08T19:31:49Z   <- most recent, FAILED
# completed  success  quality-gates-v2  ...  28962752748  ...  2026-07-08T17:32:03Z
```

`gh run view 28970063657 --log-failed` shows the identical failure signature (`❌ Empty string fallback — fail fast` →
`❌ Codex compliance FAILED: 1 violations (max allowed: 0)`) at `2026-07-08T19:33:00Z` — **before** this session made
any edits to `fluid_adapter.py`. This confirms the repo's `live-defi-rollout` branch tip was already red in real CI,
independent of local environment differences.

`.qg_last_passed_sha` (`c7045054e24d3bf112cb0b5be12b01f0db40eadc`) is an ancestor of current HEAD but not HEAD itself —
the sentinel is stale, meaning quality-gates.sh has not exited 0 on this branch in a while, yet multiple real fix
commits have landed on top of it since (e.g. `c20ea464` "canonicalize on-chain-perp HL/ASTER live connectors...").

## Why this matters

`quickmerge.sh` re-runs the FULL `quality-gates.sh` (with `--no-fix --lint`) before allowing any push, and
`--skip-codex` is explicitly disabled per WS-L #1014 (2026-06-26 operator policy): "the full quality gate is mandatory
before every push... no skip flags." There is currently **no sanctioned way to quickmerge any change** to
`market-tick-data-service` — not just changes that touch the violating pattern — until either (a) the violation count is
brought to 0, or (b) this specific check gets a baseline-ratchet mechanism (matching the DTZ/TID251/ fallback-import
pattern already used for comparable pre-existing-debt classes elsewhere in the same script).

## Todos

- [ ] [DECISION] P1. **Decide the fix mechanism**: (a) bulk-annotate the 338 call sites with `# noqa: qg-empty-fallback`
      where the empty-string default is a deliberate, safe choice (the pattern already used by ~15 sites in
      `bybit.py`/`thegraph_base_client.py`), (b) rewrite genuinely-unsafe ones to a fail-fast pattern (raise / `None`
      sentinel) where an empty string silently masks a real missing-field bug, or (c) add a baseline-ratchet file for
      this specific check (matching `/codex/06-coding-standards/quality-gates.md`'s existing DTZ/TID251/fallback-import
      precedent) so pre-existing debt doesn't block unrelated pushes while still preventing NEW violations. Needs a real
      per-callsite audit (338 sites) to know which of (a)/(b) applies where — not safe to blanket-apply either without
      reading each one.
- [ ] [SCRIPT] P1. **Once the mechanism is decided, execute it** and get `bash scripts/quality-gates.sh` exiting 0 on
      `market-tick-data-service`'s `live-defi-rollout` tip, restoring `.qg_last_passed_sha` to a current commit.
- [x] [VERIFY] P2. ✅ **RUN 2026-07-16 — fleet-wide sweep executed, results below.** **Check whether other repos have
      the same latent gap** (zero-tolerance check with no baseline-ratchet, silently accumulating pre-existing debt
      until it blocks a push) — this class of gate design (hard `max allowed: 0` with no ratchet) is a repeatable
      failure mode, not unique to this one check. **Update 2026-07-08**: the baseline-ratchet mechanism (option (c) from
      Todo #1 above) has since been built — `scripts/quality_gates/check_no_empty_string_fallback.py` (QG STEP 5.101) +
      per-repo `scripts/quality_gates/no_empty_string_fallback_baseline.yaml`, seeded fleet-wide 2026-07-08.
      `instruments-service` is now independently confirmed to ALSO be over its own seeded baseline — see the new todo
      below; this repo's `quality-gates.sh` is currently red for every push, same failure class as this doc's original
      MTDS finding.
- [x] [SCRIPT] P1. ✅ **RESOLVED SINCE — re-measured 2026-07-16: `instruments-service` is now `361 < baseline 366`, i.e.
      UNDER baseline and passing** (it now WARNs to ratchet DOWN, the healthy direction). The 11 sites were fixed in the
      interim; this todo's premise no longer holds. Original finding retained for provenance. ~~**`instruments-service`
      is over its QG STEP 5.101 baseline (369) at a live count of 380**~~ — 11 new-since-seed empty-string-fallback
      sites, verified 2026-07-08 by re-running `check_no_empty_string_fallback.py --scope instruments-service` directly
      (not just trusting a report): `scripts/rescan_sports_fixtures_canonical.py:492,495,496`,
      `scripts/retry_transient_cefi_failures_2026_06_28.py:148,149`,
      `scripts/run_fixture_completeness_audit_2026_06_25.py:237`,
      `scripts/type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py:95`,
      `scripts/type_footystats_odds_non_covered_leagues_2026_06_29.py:76`,
      `scripts/type_sfi_eu_no_provider_coverage_2026_06_27.py:98`,
      `scripts/type_tm_non_provider_coverage_2026_06_27.py:108`,
      `scripts/type_weather_eu_no_provider_coverage_2026_06_27.py:103` (8 files, 11 sites). Confirmed genuinely
      pre-existing via `git log -1` per file: real commits from 2026-06-23 through 2026-07-08 by other slots/sessions
      (e.g. `19693caa` "fix(sports): weather/SFI EU typing scripts must exclude covered leagues", slot-0/human-planning)
      — none from an in-flight uncommitted diff. Most likely explanation: these commits landed in the window between the
      2026-07-08 fleet-wide baseline seed scan and this later re-scan (ordinary multi-agent-fleet timing, not a hidden
      regression from one session). **Do NOT fix by raising the baseline** — `write_baseline()` in
      `check_no_empty_string_fallback.py` hard-clamps every count to `min(observed, prior)` (mechanically cannot raise a
      repo's count via `--update-baseline`), the script's own docstring says "NEVER raise a count" in caps, and
      CLAUDE.md's coding-standards HARD RULE states "DTZ / TID251 / fallback-import baselines only go DOWN (no new
      violations on shipping)" — same ratchet family. A sibling-agent request to hand-edit the YAML to 380 to unblock
      pushes was evaluated and declined for exactly this reason (bypasses the ratchet's only purpose). **Real fix**
      (needs `instruments-service` write access, which this issue-doc-updating pass deliberately did not take — several
      sibling agents had real uncommitted work in that repo at the time): per-site audit of the 11 sites, each resolved
      via either (a) `# noqa: qg-empty-fallback` with a one-line reason for genuinely deliberate/safe cases, or (b)
      rewrite to fail fast (raise / return `None`) where the empty-string default silently masks a real missing-field
      bug — same decision process as Todo #1, just applied to instruments-service specifically. Until then,
      `instruments-service` quickmerge pushes stay blocked by this gate (working as designed — the gate is supposed to
      stop silent accumulation, not be argued around). **Update 2026-07-09**: this exact 380/11-site snapshot was
      resolved by `instruments-service@98198613` (10 noqa + 1 fail-fast) — superseded by fresh overage (377/8 sites,
      different files) that accumulated afterward from other unrelated commits; see the 2026-07-09 Progress Log entry
      below for that batch's resolution (`instruments-service@a326f6b9`, code-complete + gate-verified, landing pending
      on an unrelated concurrent WIP collision). Not checking this box — checkbox flips require the fix to be actually
      landed (pushed), and the overage this todo names has already moved on twice since it was written; the durable
      state lives in the Progress Log, not this checkbox.

## Progress Log

- **2026-07-08** — Filed while shipping the Fluid `lending_indices` fix (`fluid_adapter.py`). Real fix is complete,
  tested (`_download_rate_indices`/`download_market_data` unit tests green, live on-chain verification against the real
  `FluidVaultResolver` contract on Ethereum mainnet), and cannot currently be pushed via the mandatory quickmerge path
  due to this unrelated, pre-existing, independently-CI-confirmed gate failure. Not attempting the 338-site audit in
  this pass (out of scope for a 4-bug DeFi data-pipeline fix task) — filed here per the "outside every plan" triage path
  instead of silently skipping or force-pushing around the gate.
- **2026-07-08 (later)** — A separate dispatch asked a sub-agent to "update the baseline for instruments-service to 380"
  to unblock sibling-agent pushes, framing it as matching the DTZ/TID251 ratchet precedent. Investigated instead of
  complying: re-verified the count independently (confirmed real — 380 live vs. 369 baseline, same 11 sites), but
  declined the baseline edit because raising a count contradicts this very mechanism's design (shrink-only ratchet,
  hard-clamped in code, "NEVER raise a count" in the script's own docstring, and the workspace's general
  baselines-only-go-DOWN HARD RULE). Logged as a new P1 todo above instead, scoped to the real fix (per-site
  noqa/fail-fast audit by someone with `instruments-service` write access) rather than the gate check.
  `instruments-service`'s `quality-gates.sh` remains red for STEP 5.101 pending that audit — this is the gate
  functioning as intended, not a bug to be routed around.
- **2026-07-09** — Independently re-confirmed while trying to ship an unrelated BINANCE-FUTURES/BINANCE-DELIVERY
  `instrument_id` `@LIN`/`@INV` canonicalization fix (`instrument_id_format_canonicalization_2026_07_08.md` finding 1;
  new file `instruments-service/scripts/canonicalize_binance_futures_delivery_catalog_2026_07_09.py`, zero overlap with
  the sites below). `bash scripts/quality-gates.sh --no-fix` on `instruments-service` still fails STEP 5.101: **live
  count 377 vs. baseline 369** (8 over, not the 11-over/380 snapshot from the prior entry — some of that entry's 8 files
  have since been fixed, but new sites appeared from other, later-merged commits, net movement 380→377, still over
  baseline). Confirmed via direct re-run of
  `unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py --workspace-root <ws> --scope instruments-service`,
  and confirmed every offending file is CLEAN in `git status` (i.e. genuinely committed to `live-defi-rollout` HEAD, not
  this session's or any sibling's uncommitted WIP): `scripts/reconcile_phantom_manifest_rows_all.py:564-568` (5 sites),
  `scripts/reconcile_sports_blank_empty_reason_2026_06_24.py:229`,
  `scripts/reconcile_tradfi_non_trading_day_captured_2026_06_26.py:375`,
  `scripts/relabel_sports_no_provider_coverage_2026_06_21.py:174`. Did not attempt the per-site audit (out of scope for
  the BINANCE task; no context on these 4 sports/tradfi/phantom-reconcile scripts). Net effect: **every quickmerge push
  to `instruments-service` is still blocked**, including this session's fully-implemented, tested, real-GCS-verified
  BINANCE canonicalization fix — left uncommitted in the working tree rather than force-pushed around the gate. Same
  conclusion as the prior entries: real fix is the per-site noqa/fail-fast audit (Todo above), not a baseline edit.
- **2026-07-09 (resolution)** — Ran the real checker
  (`unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py --workspace-root <ws> --scope instruments-service`)
  directly rather than trusting the prior entry's snapshot: live count **377 vs baseline 369 (8 over)** — confirmed
  genuinely reproducible, exactly the 8 sites the prior entry predicted:
  `scripts/reconcile_phantom_manifest_rows_all.py:564-568` (5 sites),
  `scripts/reconcile_sports_blank_empty_reason_2026_06_24.py:229`,
  `scripts/reconcile_tradfi_non_trading_day_captured_2026_06_26.py:375`,
  `scripts/relabel_sports_no_provider_coverage_2026_06_21.py:174`. **Concurrent-fix race discovered mid-task**: a
  separate sibling dispatch
  (`86df11b3 "fix(qg): unblock quality-gates-v2 on LDR — stale CME-spread test + empty-string-fallback ratchet"`, author
  `slot-0·human-planning`) independently fixed 2 of the 8 sites (the `reconcile_tradfi_non_trading_day_captured`
  `MANIFEST_PER_VM_SHARDS` read + `relabel_sports_no_provider_coverage` `VM_NAME` read, both
  `# noqa: qg-empty-fallback`) and pushed to `origin/live-defi-rollout` while this fix was in progress in the same
  shared working tree; a background auto-pull rebased local history onto it mid-session. Per-site audit + fix for the
  remaining 6 (all `# noqa: qg-empty-fallback`, no fail-fast rewrite needed this pass — see commit body for full
  per-site reasoning): 5 reported sites + the adjacent `venue` read in
  `reconcile_phantom_manifest_rows_all.py::_build_triage_records` (a cross-asset-group best-effort Gate-3 triage-report
  builder — `main()` already guards `"venue" in phantom_df.columns` a few lines below the same function, confirming
  these columns are genuinely optional depending on `asset_group`/schema vintage) +
  `reconcile_sports_blank_empty_reason_2026_06_24.py`'s `VM_NAME` read (same optional-env-flag pattern as the
  98198613/86df11b3 precedent). Verified via direct re-run: 377 → 368 (< baseline 369, real fix, not a baseline edit —
  `write_baseline()` is hard-clamped DOWN-only regardless). Landed as `instruments-service@a326f6b9`
  ("fix(instruments-service): resolve remaining QG STEP 5.101 empty-string-fallback overage"). Also caught + fixed a
  genuine STEP 5.95 DTZ007 regression this fix's own `ruff --fix` pre-commit hook introduced as collateral damage
  (auto-stripped a pre-existing, unrelated `# noqa: DTZ007` on an adjacent line as "unused" — this repo's own
  `pyproject.toml` `[tool.ruff.lint] select` excludes `DTZ`, so the routine hook and the isolated
  `check_ruff_rule_ratchet.py` STEP 5.95 checker disagree about whether that suppression is "used"; the routine hook
  wins and strips it every time the file is re-linted, so a bare noqa restore does not durably survive a future commit
  touching this file). Real fix instead of a suppression: `reconcile_phantom_manifest_rows_all.py`'s
  `PHANTOM_WEEKEND_TRADFI` weekday check only ever needed `date.fromisoformat(...)`, not `datetime.strptime(...)` — a
  `date` has no timezone concept at all, eliminating the DTZ007 violation at the source. Verified via direct
  `check_ruff_rule_ratchet.py` re-run: `dtz 25 == baseline 25` (was 26 mid-fix, confirmed the regression was real before
  fixing it). **Landing status — blocked on an unrelated, live, concurrent multi-agent collision, not on this fix**:
  `git log origin/live-defi-rollout..HEAD` shows 3 local-only commits (`a326f6b9` this fix, `57f8a754` a sibling's real
  on-chain-perp `@LIN` margin-marker fix, `1a696db7` a sibling's real BINANCE-FUTURES/BINANCE-DELIVERY migration — all
  genuinely committed, none authored by this pass).
  `quickmerge.sh --agent --files "scripts/reconcile_phantom_manifest_rows_all.py scripts/reconcile_sports_blank_empty_reason_2026_06_24.py" --skip-preflight`
  (pre-flight skipped because an unrelated dependency repo, `unified-api-contracts`, has unrelated uncommitted changes
  from another session) reaches Stage 3 (Local Quality Gates) and fails on 4 pre-existing, unrelated test failures in
  `tests/unit/test_cefi_tradfi_comprehensive.py::TestDatabentoHelpers::test_parse_cme_spread_legs*\*`— root cause
  confirmed (not assumed) by inspecting`git status`: another agent has a **live** uncommitted WIP on
  `instruments*service/reference_data/adapters/tradfi/databento/{**init**,adapter,symbology}.py` (mtime ~5 min old at
  observation time, actively multi-file, matches this session's explicit "DO NOT touch databento files" scope boundary)
  that has \_temporarily\* reverted `_parse_cme_calendar_spread_legs` to a 1-arg signature, while the already-committed
  test file (from `86df11b3`) expects the real, current 2-arg `(raw_symbol, venue)` signature (corrected 2026-07-14,
  finding 145: this was a mid-transition snapshot, not the durable target — the 1-arg form is the intentional, permanent
  signature per the venue-drop decision in
  `active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md:153-156`, which fixed the 2-arg test calls as
  the actual regression, shipped 2026-07-09; live code confirms 1-arg —
  `instruments-service/instruments_service/reference_data/adapters/tradfi/databento/symbology.py:244`
  `def _parse_cme_calendar_spread_legs(raw_symbol: str) -> list[InstrumentLeg] | None:` — was: this doc characterized
  2-arg as "the real, current" signature and 1-arg as a temporary revert, the opposite of what shipped). Confirmed via a
  bounded 3-minute poll (6× 30s) that this WIP was still unresolved at observation end — not something this pass fixed
  or should fix (explicitly out-of-scope file per this dispatch's own instructions; touching another agent's live WIP
  file is a workspace HARD RULE violation). This pass's own STEP 5.101 + STEP 5.95 fix is itself real, complete, and
  independently gate-clean (verified via direct checker re-runs above, not just quickmerge's full-suite run) — landing
  is pending only on that unrelated sibling WIP resolving (or a future push once the tree is quiescent). No baseline
  edits, no force-push, no `--skip-tests`.
- **2026-07-09 (re-confirmed, blocking a 4th independent fix)** — Hit the identical wall shipping the real
  OKX-SWAP/OKX-FUTURES `margin_type` full-sweep (`prod/catalog.parquet` 2,753 rows + `instrument_availability/by_date/`
  per-day corpus 4,762 files, both real production GCS writes, already applied + verified independent of this gate — see
  `instruments-service/docs/CEFI_INSTRUMENTS.md`). `bash scripts/quality-gates.sh --no-fix` on `instruments-service`
  again fails STEP 5.101: **live count 372 vs. baseline 369 (3 over)**, exactly
  `scripts/reconcile_phantom_manifest_rows_all.py:470-472` — net movement since the `a326f6b9` fix (368) is +4, i.e. new
  sites landed via later, unrelated commits in the same fast-moving shared tree (consistent with this doc's own
  368→377→368-pattern across entries: this ratchet keeps drifting back over baseline as concurrent agents ship unrelated
  real fixes, not from any one change). Confirmed the specific flagged lines are genuinely pre-existing (not this
  session's or any sibling's uncommitted WIP):
  `git show origin/live-defi-rollout:scripts/reconcile_phantom_manifest_rows_all.py` contains the identical code at
  those lines. Did not attempt a per-site audit (out of scope for the OKX task; same reasoning as every prior entry).
  Net effect: this session's `docs/CEFI_INSTRUMENTS.md` OKX write-up +
  `scripts/canonicalize_okx_margin_type_2026_07_09.py` are staged and ready but left uncommitted, same as the BINANCE/
  Deribit/Bybit-Kraken fixes above — the real, authorized, already-applied production data migration is NOT gated by
  this (GCS writes are independent of git), only the paperwork commit is.

## Fleet-wide QG STEP 5.101 sweep — RUN 2026-07-16 (closes Todo 3)

Todo 3 asked whether other repos carry the same latent gap, "in one pass instead of discovering them one push at a
time". **Nobody had run it in the 8 days since it was filed.** Run now, workspace-wide, no `--scope`
(`check_no_empty_string_fallback.py --workspace-root /active/unified-trading-system-repos`). 25 repos measured:

| Verdict                                  | Count | Repos                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FAIL** (over baseline — blocks pushes) | **1** | **`agent-orchestrator`: 26 > baseline 25**                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| OK (== baseline)                         | 19    | alerting-service, batch-live-reconciliation-service, client-reporting-api (230), deployment-api, deployment-ui, e2e-testing (221), execution-service (65), features-service (28), fund-administration-service, greeks-service, ibkr-gateway-infra, market-data-processing-service (66), strategy-service (166), system-integration-tests, unified-api-contracts (12), unified-trading-api (3), unified-trading-library (2), unified-trading-pm (319), unified-trading-system-ui |
| WARN (under baseline — ratchet DOWN)     | 5     | deployment-service 89<91 · instruments-service 361<366 · market-tick-data-service **62<199** · ml-service 6<8 · trading-agent-service 1<2                                                                                                                                                                                                                                                                                                                                       |

**Answer to Todo 3: the latent gap is NOT widespread.** One repo is over baseline; the rest are at or under. The
zero-tolerance-gate failure class this doc worried about did not replicate fleet-wide.

- [x] [SCRIPT] P1. ✅ **FIXED 2026-07-16 — `agent-orchestrator@54c9e8d`; re-measured
      `[OK] agent-orchestrator: 25 (== baseline)`, full QG PASSED.** The real site was
      **`server/notifications/slack.py:405` (2026-07-14)**, NOT the `_git_alerts.py:364` the checker named — that line
      is from 2026-06-11 and was an artefact of the positional tail-slice fallback (this repo's baseline has no
      `commit:` anchor). Fixed by indexing `loss["sha"]` (fail-fast), not by a `noqa` and not by raising the baseline.
      See the new P2 todo below — stamping AO's `commit:` anchor stops the next breach from mis-reporting the same way.
      ~~**`agent-orchestrator` is over its QG STEP 5.101 baseline (25) at a live count of 26**~~ — a NEW
      empty-string-fallback site at `server/worker_liveness/_git_alerts.py:364`, measured 2026-07-16 by running
      `check_no_empty_string_fallback.py --scope agent-orchestrator` directly (not trusting a report). This means
      `agent-orchestrator`'s `quality-gates.sh` is **currently red for every push** — the same failure class as this
      doc's original MTDS finding, now recurring in the repo the AO remediation work is about to touch heavily. **Do NOT
      fix by raising the baseline** (`write_baseline()` hard-clamps to `min(observed, prior)`; the ratchet only goes
      DOWN — CLAUDE.md coding-standards HARD RULE). Real fix: rewrite the fallback to fail fast, or annotate
      `# noqa: qg-empty-fallback` with a one-line reason **if** the empty string is genuinely a meaningful not-present
      value there. The checker reports it as a "positional tail-slice — no baseline commit on record for this repo yet",
      so confirm the site is genuinely new before annotating. (repo: agent-orchestrator)
- [ ] [SCRIPT] P3. **Ratchet 5 baselines DOWN** (`--update-baseline` per repo): deployment-service 91→89,
      instruments-service 366→361, **market-tick-data-service 199→62** (this doc's own subject repo — a 137-site
      improvement never banked), ml-service 8→6, trading-agent-service 2→1. Pure hygiene; each unbanked baseline leaves
      headroom for a real regression to slip in unnoticed, which is exactly how `agent-orchestrator` reached 26.

- [ ] [SCRIPT] P2. **Stamp a `commit:` anchor into the `agent-orchestrator` baseline row** (and audit which other repos
      lack one). Root cause of the 2026-07-16 mis-report: AO's row is bare `count: 25` with no `commit:`, so an
      over-baseline failure cannot git-diff against a known-good point and falls back to a **positional tail-slice** —
      it named a 2026-06-11 line as the culprit when the real one was 2026-07-14. This is the second recorded instance
      of that exact confusion (see `instruments_service_empty_string_fallback_baseline_breach_2026_07_14`), so it is a
      pattern, not bad luck: whoever hits the next breach will be sent to the wrong file unless the anchor exists.
      Running `--update-baseline` on a green repo stamps the anchor and clamps the count DOWN (never up), so it is safe.
      **Gate**: `no_empty_string_fallback_baseline.yaml`'s `agent-orchestrator` row carries a `commit:`; a
      deliberately-introduced test site is reported at its real path, not a tail-slice guess.
