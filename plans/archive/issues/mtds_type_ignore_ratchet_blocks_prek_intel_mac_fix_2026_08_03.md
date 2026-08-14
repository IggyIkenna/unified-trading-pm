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
status: resolved
nature: issue
asset_group: [cross-cutting]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, ratchet, ci-cd, ready-to-ship-blocked]
created: 2026-08-03
author: unknown
last_updated: "2026-08-14"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: cicd
priority: P2
estimate_class: research
source: [session on Ikenna's laptop, 2026-08-03]
drift_direction: unknown
depends_on: []
locked_by:
resolved_by: cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13
stage: [meta]
related: []
context_scope:
  [
    /plans/archive/issues/mtds_blanket_pyright_suppressions_ssot_contradiction_2026_07_30.md,
    market-tick-data-service/scripts/quality-gates.sh,
    scripts/quickmerge.sh,
  ]
---

> **🟢 ARCHIVED 2026-08-14** — `status: resolved` with zero open todos; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)'s
> archive-on-resolve rule. All 3 todos done: baseline root-cause + ratchet fix (2026-08-09), the unblocked prek
> Intel-Mac ship (2026-08-03), and the standalone-vs-quickmerge-re-gate fatality investigation + doc (2026-08-14,
> `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`) — no open work remains.

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

- [x] ✅ [SCRIPT] P2. Root-cause the exact `# type: ignore` occurrence that pushed the count to 659, and either fix it
      with an exact rule code or get the baseline properly raised. **DONE (staleness-recheck 2026-08-09)** —
      `market-tick-data-service@b16c9f69` (2026-08-07 20:04:46 UTC, same day as this doc's 2026-08-07 KEEP-NA marker)
      ratcheted `_MTDS_TYPE_IGNORE_BASELINE` in `scripts/quality-gates.sh` from 660 down to 658, with the shipped code
      comment explicitly citing this issue's own methodology ("mirroring the issue doc's own
      `grep -rn "# type: ignore" ...` methodology"). Live-reverified:
      `grep -rn "# type: ignore" --include='*.py' . | grep     -v .venv | wc -l` on the current tree returns exactly
      **658**, matching the frozen baseline exactly — the ratchet no longer blocks quickmerge.
- [x] ✅ [SCRIPT] P2. Once unblocked, ship the already-verified prek Intel-Mac uv.sources fix in
      `market-tick-data-service/pyproject.toml`+`uv.lock` (already sitting correct in the working tree, just
      uncommitted) via the exact quickmerge command in "Recommended next step" above. — **SHIPPED
      `market-tick-data-service@b55cf9ad`** (2026-08-03, ancestor-verified on `origin/live-defi-rollout`):
      `git show b55cf9ad -- pyproject.toml` confirms `[[tool.uv.sources.prek]]` split into separate `arm64`/`x86_64`
      marker branches, exactly this fix. It landed bundled inside a larger multi-purpose commit rather than standalone
      via the recommended command, which is why the checkbox was never flipped — found by `/plan-reconcile ao`
      2026-08-06.
- [x] ✅ [SCRIPT] P3. Look at why `quality-gates.sh --no-fix` standalone treats STEP 5.95 as non-fatal ("ALL QUALITY
      GATES PASSED" despite the ❌ line) while `quickmerge.sh`'s internal re-gate treats the identical finding as fatal
      — likely intentional (re-gate may run a stricter/full mode) but worth a comment or confirming, since the
      inconsistent signal cost time to understand during this session. **DONE (2026-08-14, cross-cutting AO dispatch
      batch 13b)** — investigated + documented; NOT a --no-fix-vs-full-mode difference (confirmed: STEP 5.94/5.95 has no
      branch on that flag at all). Root cause is a MOVING-HEAD attribution window, not a severity difference: 1. The
      2026-08-03 symptom (global baseline 658/659 mismatch) is OBSOLETE — the ratchet was redesigned since
      (`market-tick-data-service@d072b035` era → the current diff-scoped-attribution form) to compare only files touched
      in `git diff <merge-base-with-origin/live-defi-rollout> HEAD`, reading each touched file's live on-disk content
      for the "new" count. There is no remaining whole-repo scalar-vs-frozen-baseline compare for 5.94/5.95 in the
      current script (`grep -n BASELINE market-tick-data-service/scripts/quality-gates.sh` finds only a historical
      comment). 2. Both invocation paths run the identical `bash scripts/quality-gates.sh --no-fix` — quickmerge's
      `--agent` path only re-invokes it (the "re-gate") inside its sentinel-invalid RETRY loop
      (`unified-trading-pm/scripts/quickmerge.sh:2454`), reached only after `_qm_stage_0_4_not_behind_gate` (same file,
      called at line 2443 right before the re-gate) fetches + rebases the local HEAD onto whatever a peer slot pushed to
      `live-defi-rollout` in the meantime. 3. Because 5.94/5.95's touched-file list comes from `git diff <base> HEAD`, a
      peer commit swept in by that rebase — one that never appears in YOUR OWN diff — can still widen the re-gate's
      `base..HEAD` window enough to surface a net-new bare `# type: ignore` in a file you never touched, and `log_fail`
      there is an immediate `exit 1` (`market-tick-data-service/scripts/quality-gates.sh:631,664`). An earlier
      standalone run, whose HEAD hadn't yet absorbed that peer commit, saw a narrower window and printed "ALL QUALITY
      GATES PASSED" legitimately for the state it was scoped to at that moment. 4. Documented in place:
      `market-tick-data-service/scripts/quality-gates.sh` (the diff-scoped-attribution helper's docstring, immediately
      above `_mtds_ratchet_diff_base`) — `market-tick-data-service@9effa3529c`. No code BEHAVIOR change — this was an
      investigate-and-document todo; the mechanism is working as designed (attribution scoped to `base..HEAD`), just
      under-documented for why two invocations of the same script can legitimately disagree.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- **context-scout 2026-08-03**: populated context_scope (4 entries) — root-caused the exact ratchet mechanism: this
  issue's own "Recommended next step" points at `scripts/quality-gates-base/base-service.sh` STEP 5.95, but that shared
  script's STEP 5.95 is actually the unrelated DTZ/TID251 ratchet. The real type:ignore-count ratchet is a LOCAL STEP
  5.94/5.95 block added directly inside `market-tick-data-service/scripts/quality-gates.sh`
  (`market-tick-data-service@d072b035`, baseline 658 per `QUALITY_GATE_BYPASS_AUDIT.md` §2.3) — the local labels
  deliberately collide with `base-service.sh`'s own STEP 5.94/5.95 (documented in
  `mtds_blanket_pyright_suppressions_ssot_contradiction_2026_07_30.md` as "cosmetically confusing... but functionally
  harmless"), which is very likely why quickmerge's re-gate treats this finding as fatal while the standalone script
  reports "ALL QUALITY GATES PASSED."
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — first assessment: genuine mix — todo 1's root cause is
  unresolved and needs the ratchet-owner's sign-off, todo 2 depends on todo 1 landing first (no structural gate, so
  default concurrent AO dispatch would race it) and touches a laptop-local uncommitted WIP; whole doc stays NA.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — todo 2 (the prek Intel-Mac ship) is now
  closed (see checkbox above, already shipped `market-tick-data-service@b55cf9ad`, found by `/plan-reconcile ao`
  2026-08-06), so the 'todo 2 depends on todo 1' rationale is now moot; doc stays NA on the 2 remaining items (todo 1
  root-cause + baseline-owner sign-off, todo 3 investigate the quickmerge-regate-vs-standalone-QG inconsistency). Both
  are fairly bounded/mechanical — flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` in this audit's report for a possible
  future reclassify pass rather than reclassified here.
- **staleness-recheck 2026-08-09**: closed todo 1 (root-cause the type:ignore ratchet block) —
  `market-tick-data-service@b16c9f69` ratcheted `_MTDS_TYPE_IGNORE_BASELINE` 660→658 same-day as the 2026-08-07 marker,
  live-reverified current repo count is exactly 658 (matches baseline, no longer blocking). 1 open todo remains (todo 3,
  the `--no-fix`-vs-quickmerge-re-gate fatality inconsistency — no evidence found of anyone investigating it).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **cross_cutting_satellite_ao_dispatch_batch13b 2026-08-14**: closed todo 3 (the final open item) — root-caused +
  documented the standalone-vs-quickmerge-re-gate fatality split as a MOVING-HEAD attribution window, not a
  --no-fix-vs-full-mode severity difference (full explanation on the checkbox above). Doc-level comment shipped at
  `market-tick-data-service/scripts/quality-gates.sh` (diff-scoped-attribution helper docstring). All 3 todos now closed
  — flipping `status: open -> resolved`.
