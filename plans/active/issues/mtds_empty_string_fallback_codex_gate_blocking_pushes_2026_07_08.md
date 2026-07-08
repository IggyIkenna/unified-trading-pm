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
last_updated: 2026-07-08
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
      this specific check (matching `codex/06-coding-standards/quality-gates.md`'s existing DTZ/TID251/fallback-import
      precedent) so pre-existing debt doesn't block unrelated pushes while still preventing NEW violations. Needs a real
      per-callsite audit (338 sites) to know which of (a)/(b) applies where — not safe to blanket-apply either without
      reading each one.
- [ ] [SCRIPT] P1. **Once the mechanism is decided, execute it** and get `bash scripts/quality-gates.sh` exiting 0 on
      `market-tick-data-service`'s `live-defi-rollout` tip, restoring `.qg_last_passed_sha` to a current commit.
- [ ] [VERIFY] P2. **Check whether other repos have the same latent gap** (zero-tolerance check with no
      baseline-ratchet, silently accumulating pre-existing debt until it blocks a push) — this class of gate design
      (hard `max allowed: 0` with no ratchet) is a repeatable failure mode, not unique to this one check.

## Progress Log

- **2026-07-08** — Filed while shipping the Fluid `lending_indices` fix (`fluid_adapter.py`). Real fix is complete,
  tested (`_download_rate_indices`/`download_market_data` unit tests green, live on-chain verification against the real
  `FluidVaultResolver` contract on Ethereum mainnet), and cannot currently be pushed via the mandatory quickmerge path
  due to this unrelated, pre-existing, independently-CI-confirmed gate failure. Not attempting the 338-site audit in
  this pass (out of scope for a 4-bug DeFi data-pipeline fix task) — filed here per the "outside every plan" triage path
  instead of silently skipping or force-pushing around the gate.
