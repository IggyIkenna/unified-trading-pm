---
title: "e2e-testing STEP 5.95 TID251 ratchet is over baseline — pre-existing, blocks ALL e2e commits"
created: 2026-06-20
status: open
priority: P1
source:
  - quality-gates STEP 5.95 (check_ruff_rule_ratchet.py --scope e2e-testing)
locked_by: live-defi-rollout
---

## What I found

`e2e-testing` quality-gates **STEP 5.95** (`check_ruff_rule_ratchet.py`) fails on `live-defi-rollout`:

```
[FAIL] e2e-testing/tid251: 15 violation(s) > baseline 10.
  New/over-baseline site(s):
    scripts/sports/live_arb_scanner.py:308          from google.cloud import secretmanager
    scripts/sports/odds_api_live_feed.py:100        from google.cloud import secretmanager
    scripts/sports/prediction_market_scanner.py:46  from google.cloud import secretmanager
    scripts/sports/run_weekly_pipeline.py:52         from google.cloud import storage
    scripts/sports/run_weekly_pipeline.py:108        from google.cloud import secretmanager
```

These 5 un-`# noqa`'d direct `google.cloud` imports are in **sports** campaign scripts and are **pre-existing on LDR** —
the count was already 15 vs baseline 10 **before** any paper-trading change (verified: reverting all
`scripts/paper_trading/` edits still shows 15>10; the over-baseline sites are all `scripts/sports/*`, none mine). The
ratchet is a SHRINKING gate (`NEVER raise a count`), so the baseline cannot simply be bumped to 15.

Compounding config issue: `# noqa: TID251` on these lines trips **RUF100 (unused-noqa)** under the repo's own ruff (its
`select` does not enable TID251 — TID251 is enforced only by the separate `check_ruff_rule_ratchet.py` run), so a naive
noqa needs a matching `RUF100` per-file-ignore (as `scripts/paper_trading/*` already carries).

## Why it matters

STEP 5.95 is a HARD gate → **every** `e2e-testing` quickmerge from a fresh/up-to-date clone fails on this, regardless of
what is being landed. It is currently blocking the (otherwise gate-clean) paper-trading POC engine source landing
(`PB.2` in `citadel_paper_batch_live_reconciliation_2026_06_19.md`), and would block any other e2e change too.

## Recommended decision

Sports/e2e-domain owner: for each of the 5 sites, either (a) route through `get_secret_client()` /
`get_storage_client()` from `unified_trading_library.cloud_interface` (the canonical cloud-agnostic fix), or (b) add
`# noqa: TID251 — <reason>` **and** add `"scripts/sports/*"` (or the specific files) to
`[tool.ruff.lint.per-file-ignores]` with `RUF100` so the noqa is honored. Either restores the ratchet to ≤ baseline and
unblocks the e2e gate fleet-wide. The paper-trading POC source (`scripts/paper_trading/`, all OWN gate items green:
ruff/basedpyright-excluded/codex/TID251-noqa/dockerfile-digest-pinned) lands as soon as this is resolved; meanwhile the
engine is already DEPLOYED (Cloud Run jobs) and its source lives in `.tabs/1/` working copies.
