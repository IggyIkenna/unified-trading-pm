---
doc_type: issue
title:
  "market-tick-data-service's inline type:ignore ratchet is 1 over its frozen baseline, blocking an unrelated
  ready-to-ship commit"
summary: >-
  A verified, ready-to-ship fix (prek fork Intel-Mac wheel marker in pyproject.toml/uv.lock) is blocked by quickmerge's
  re-gate step failing STEP 5.95: inline type:ignore count is 659, frozen baseline is 658. A plain `quality-gates.sh
  --no-fix` run reports the same finding but still concludes "ALL QUALITY GATES PASSED" (informational in that path);
  quickmerge's internal re-gate treats it as a hard failure. Not caused by the blocked commit (its diff is
  pyproject.toml + uv.lock only, no Python). The nearest concurrent commit on the branch
  (`market-tick-data-service@fa991f12`) does not itself add a new `# type: ignore` (checked directly, zero matches) —
  root cause not identified, only the blocking symptom and a safe uncommitted fix waiting behind it.
status: open
nature: issue
asset_group: [cross-cutting]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, ratchet, ci-cd, ready-to-ship-blocked]
created: 2026-08-03
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
assigned_role: cicd
priority: P2
estimate_class: research
source: [session on Ikenna's laptop, 2026-08-03]
drift_direction: unknown
depends_on: []
locked_by:
resolved_by:
stage: [meta]
related: []
---

# market-tick-data-service type:ignore ratchet blocks a ready-to-ship, unrelated commit

## What I found

Shipping the Intel-Mac (`x86_64-apple-darwin`) marker branch for the `prek` fork wheel override in
`market-tick-data-service/pyproject.toml` + `uv.lock` (the same pattern already shipped clean in 6 sibling repos this
session) via `quickmerge.sh` failed at the re-gate step:

```
[0;31m❌ 5.95: inline '# type: ignore' comment count rose to 659 (frozen baseline: 658)...[0m
[market-tick-data-service] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.
```

The blocked commit's own diff is `pyproject.toml`/`uv.lock` only (verified: `git diff --stat` shows no Python files) —
it cannot be the source of a new `# type: ignore` comment. A standalone `bash scripts/quality-gates.sh --no-fix` run
against the same tree reports the identical STEP 5.95 finding but still prints "ALL QUALITY GATES PASSED" overall — that
path treats it as non-blocking, while quickmerge's internal re-gate treats it as fatal. This inconsistency between the
two invocation paths is itself worth someone's attention, separate from the ratchet violation.

Checked the nearest commit landed on the branch during this session (`fa991f12`, "fix(cefi): exclude processed_candles
from drop-stale sweep"): `git show fa991f12 | grep -n ignore` returns zero matches — that commit does not add a
`# type: ignore` anywhere. Root cause of the +1 is NOT identified — could be a different concurrent commit landed in the
same window, a file-count/scan-scope change, or something else. Not investigated further; this issue exists to unblock
whoever picks it up, not to have fully solved it.

## Why it matters

This ratchet gate is repo-wide — it will block ANY commit to `market-tick-data-service` via `quickmerge.sh` until either
the actual offending `# type: ignore` is found and given a proper rule-code + reason, or the frozen baseline is
deliberately bumped by someone who has confirmed the new occurrence is legitimate (not a banned broad ignore).

## Current state — what's safe, what's not

- **Nothing is lost or at risk.** The blocked fix sits uncommitted in the working tree at
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/3/market-tick-data-service` (`pyproject.toml`,
  `uv.lock`) — already `uv lock`-verified clean (no unrelated package churn) and already passed a standalone
  `quality-gates.sh --no-fix` run. It is NOT committed because quickmerge's re-gate refused it.
- Also present in that same working tree, unrelated to this issue and NOT to be touched: 3 modified
  `tests/schema_artifacts/*.json` files (pre-existing test-run byproducts, same pattern seen earlier this session, never
  staged) and instruments-service's separately-noted foreign `buildspec.aws.yaml` (different repo, different
  pre-existing WIP, not this issue's concern).

## Recommended next step

1. `cd market-tick-data-service && grep -rn '# type: ignore' --include='*.py' . | wc -l` vs the ratchet's own counting
   method (check `scripts/quality-gates-base/base-service.sh` STEP 5.95 for its exact grep/count logic) to find the
   actual 659th occurrence.
2. Either fix it properly (exact-rule `# type: ignore[code]  # <dep> reason`) or, if it's a legitimate necessary broad
   ignore, get the baseline bumped by whoever owns that ratchet's ownership process (grep the STEP 5.95 script/doc for
   how baselines get raised — likely NOT a silent self-service bump, given "freeze-and-shrink" ratchets in this
   workspace are explicitly one-directional).
3. Once green, re-run the blocked commit:
   `cd market-tick-data-service && bash scripts/quickmerge.sh "fix(deps): add x86_64-apple-darwin (Intel Mac) marker branch for prek fork wheel" --agent --files 'pyproject.toml uv.lock'`.

## Todos

- [ ] [SCRIPT] P2. Root-cause the exact `# type: ignore` occurrence that pushed the count to 659, and either fix it with
      an exact rule code or get the baseline properly raised.
- [ ] [SCRIPT] P2. Once unblocked, ship the already-verified prek Intel-Mac uv.sources fix in
      `market-tick-data-service/pyproject.toml`+`uv.lock` (already sitting correct in the working tree, just
      uncommitted) via the exact quickmerge command in "Recommended next step" above.
- [ ] [SCRIPT] P3. Look at why `quality-gates.sh --no-fix` standalone treats STEP 5.95 as non-fatal ("ALL QUALITY GATES
      PASSED" despite the ❌ line) while `quickmerge.sh`'s internal re-gate treats the identical finding as fatal —
      likely intentional (re-gate may run a stricter/full mode) but worth a comment or confirming, since the
      inconsistent signal cost time to understand during this session.
