---
doc_type: issue
title:
  act-preflight.sh defaults --workflow to the retired quality-gates.yml, so the documented no-flag invocation exits 2
  ("workflow not found") on every repo in the workspace
summary: >-
  `unified-trading-pm/scripts/dev/act-preflight.sh` hardcodes `WORKFLOW="quality-gates.yml"` as its default (line 27).
  That filename no longer exists in ANY repo: the workspace-wide count is 0 repos with `quality-gates.yml` vs 26 repos
  with `quality-gates-v2.yml` (measured 2026-07-31 via `find <ws> -maxdepth 4 -path '*/.github/workflows/<name>'`). The
  script's own arg-validation then hits `if [[ ! -f "$WORKSPACE_ROOT/$REPO/.github/workflows/$WORKFLOW" ]]` and exits 2,
  so the documented invocation `act-preflight.sh --repo <name>` — the form cited as the `verifier:` of
  `/codex/05-infrastructure/act-preflight-coverage.md` and in that doc's operational guidance — cannot succeed for any
  repo. The `--repo all` path degrades differently but equivalently: its discovery loop only appends repos where
  `.github/workflows/$WORKFLOW` exists, so it silently resolves to ZERO target repos and reports success over an empty
  set. The fix is a one-line default change to `quality-gates-v2.yml`; the codex doc has already been corrected to pass
  `--workflow quality-gates-v2.yml` explicitly so the runbook is usable in the meantime.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, act, quality-gates, dev-tooling, staleness]
related:
  [
    /codex/05-infrastructure/act-preflight-coverage.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-07-31
priority: P3
parent_epic: infrastructure_master
source: "slot-3, codex freshness re-review shard-B, discovered re-reviewing act-preflight-coverage.md, 2026-07-31"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: >-
  Both todos done: script default fixed unified-trading-pm@075e4e11b (WORKFLOW="quality-gates-v2.yml" + loud-fail on
  empty --repo all); codex caveat dropped + verifier: restored to the no-flag form unified-trading-pm@1b4c9c9eb.
locked_by:
locked_since:
---

# act-preflight.sh default `--workflow` points at a retired filename

## What I found

Re-reviewing `/codex/05-infrastructure/act-preflight-coverage.md` (which carried a `last_reviewed: 2026-05-17` stamp and
names `act-preflight.sh` as its `verifier:`), I checked whether the verifier command still works. It does not.

`scripts/dev/act-preflight.sh` line 27:

```bash
WORKFLOW="quality-gates.yml"
```

Measured workspace reality on 2026-07-31:

| Workflow filename             | Repos containing it |
| ----------------------------- | ------------------- |
| `quality-gates.yml`           | **0**               |
| `quality-gates-v2.yml`        | 26                  |
| `python-quality-gates.yml`    | 0                   |
| `python-quality-gates-v2.yml` | 1 (PM)              |

The v2 rename is the shipped state (`quality-gates-v2` is the required check on every repo per
`/codex/08-workflows/ci-cd-flow.md`); the script was simply never updated alongside it.

## Two distinct failure modes

1. **`--repo <name>`** — the explicit-repo path validates the workflow file exists and exits 2 with
   `ERROR: workflow not found at <ws>/<repo>/.github/workflows/quality-gates.yml`. Loud, harmless, but the tool is
   unusable without knowing to pass `--workflow`.
2. **`--repo all`** — the discovery loop only appends a repo when `[[ -f "$d/.github/workflows/$WORKFLOW" ]]`. With a
   filename that matches nothing, `TARGET_REPOS` stays empty, the for-loop body never executes, `OVERALL_EXIT` stays 0
   and the script prints an empty `=== Summary ===` and **exits 0**. This is the dangerous one: a green exit that
   rehearsed nothing. Anyone wiring `act-preflight.sh --repo all` into a pre-push habit or a gate would get a
   permanently-passing no-op.

   Verified 2026-07-31 by replaying the script's own discovery loop + empty-array expansion verbatim under
   `set -euo pipefail` against the live workspace: `TARGET_REPOS count = 0`, loop body never entered, `ACTUAL EXIT: 0`.
   Two preconditions bound the claim: (a) the `command -v act` / `docker info` preflight runs _before_ repo resolution,
   so on a host without act or a running docker daemon the script exits 2 there and never reaches this path; (b) the
   empty-array expansion `"${TARGET_REPOS[@]}"` is only safe-under-`set -u` on bash 4.4+ — measured on bash 5.3.9. On
   macOS's system bash 3.2 the same line would instead abort with `unbound variable`.

## Suggested fix

- [x] ✅ [SCRIPT] P3. Change the `act-preflight.sh` default to `WORKFLOW="quality-gates-v2.yml"`, and make the
      `--repo all` path fail loudly (exit 2) when `TARGET_REPOS` resolves empty rather than exiting 0 over an empty set.
      Ship via `unified-trading-pm` quality gates + quickmerge. Provenance: codex freshness re-review shard-B,
      2026-07-31. — unified-trading-pm@075e4e11b
- [x] ✅ [DOC] P3. Once shipped, drop the ⚠️ caveat + this issue reference from
      `/codex/05-infrastructure/act-preflight-coverage.md` § Operational guidance and restore the no-flag invocation in
      its `verifier:` frontmatter field. — unified-trading-pm@1b4c9c9eb

## Why this was not fixed in the discovering session

The discovering session was scoped to a pure-doc codex freshness re-review (prek-only shipping lane). Changing
`scripts/dev/act-preflight.sh` is a code change that must clear a full `quality-gates.sh`-green tree before commit per
the workspace HARD RULE, which is outside that session's lane. The codex doc was corrected in place to pass the explicit
`--workflow quality-gates-v2.yml` flag so the documented runbook is accurate and usable today.
