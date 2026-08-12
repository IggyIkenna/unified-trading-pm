---
doc_type: issue
title: >-
  alerting-service has 43 basedpyright errors against a 21-error ratchet cap — blocks every ship on the repo, including
  docs-only changes
summary: >-
  Discovered 2026-08-12 while validating quickmerge `--isolated` mode on a second repo
  (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md todo E): a trivial, docs-only README change to
  `alerting-service` failed `quickmerge.sh --isolated` at the type-check stage — 43 basedpyright errors vs
  `BASEDPYRIGHT_MAX_ERRORS=21`. Not caused by the change being shipped (which touched only README.md); this is
  pre-existing debt in the repo's own tree. Errors cluster in `alerting_service/rules/defi_rules.py`,
  `feed_refetch_rules.py`, and `alerting_service/subscribers/alert_subscriber.py`, largely
  `unified_api_contracts`-vs-local-type mismatches (`DefiAlertType`, `AlertSeverity`) plus one `_EVENTS_INITIALISED is
  constant` redefinition. Not investigated further — out of scope for the todo that surfaced it (a PM-repo
  precommit-latency issue), and this session did not have budget to root-cause a different repo's type debt. Filed so it
  is tracked rather than silently dropped.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service]
scope: [engineer]
tags: [basedpyright, type-check, quickmerge, quality-gates, ratchet-regression]
related: [/plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12 (slot-1) — surfaced as a side effect of validating quickmerge isolation on a second
  repo for a different issue doc's todo; not this session's primary subject.
depends_on: []
---

# alerting-service is currently unshippable via quickmerge — 43 basedpyright errors, cap is 21

## What was measured

`bash scripts/quickmerge.sh "docs: ..." --agent --isolated --files 'README.md'` in `alerting-service`, run from a clean
tree, shipping ONLY a docs addition to `README.md`. The isolated re-gate (full `quality-gates.sh`, run in a throwaway
worktree at `origin/HEAD`) failed at the type-check phase:

```
43 errors, 0 warnings, 0 notes
❌ Type check FAILED — 43 error(s) > BASEDPYRIGHT_MAX_ERRORS=21 (ratchet down to fix errors)
[alerting-service] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.
```

Since the shipped change touched only `README.md` and the failure is in unrelated application code
(`alerting_service/rules/*.py`, `alerting_service/subscribers/alert_subscriber.py`), this is pre-existing debt on
`origin/live-defi-rollout`, not something the shipping attempt introduced. **Any commit to this repo — including a pure
docs change — currently fails to ship via quickmerge**, since the gate re-checks the whole tree regardless of what's
being shipped.

## Errors seen (sample, not exhaustive — full list in the quickmerge run's basedpyright output)

- `alerting_service/rules/defi_rules.py` — multiple `reportArgumentType` on `DefiAlertType` /
  `unified_api_contracts.canonical.crosscutting.errors.defi.DefiAlertType` mismatches (looks like a local
  `DefiAlertType` enum has drifted from UAC's canonical one, or an import is resolving to the wrong module), plus
  `reportUnknownVariableType` / `reportUnknownArgumentType` around `event_name` / `route_event`.
- `alerting_service/rules/feed_refetch_rules.py:153` — `AlertSeverity` local type vs
  `unified_api_contracts...codes.AlertSeverity` mismatch, same shape as the `DefiAlertType` issue above.
- `alerting_service/subscribers/alert_subscriber.py:103` — `_EVENTS_INITIALISED` is constant (uppercase) and cannot be
  redefined (`reportConstantRedefinition`).

The `DefiAlertType`/`AlertSeverity` pattern recurring across two files suggests a single root cause (a UAC type that
moved/renamed and a local shadow that didn't follow, or a stale local copy vs the UAC canonical import) rather than 43
independent bugs — worth checking that hypothesis first before fixing errors one at a time.

## Not investigated further

This session did not: read the actual UAC `DefiAlertType`/`AlertSeverity` definitions to confirm the drift hypothesis,
check `git blame`/git log for when these errors were introduced, check whether this is already known to
alerting-service's own maintainers, or attempt any fix. Filed purely to make the finding durable rather than losing it
to chat history — the todo that surfaced this (isolation validation) is unrelated and does not need this fixed to close.

## Todos

- [ ] [INFRA] P1. **Root-cause the `DefiAlertType`/`AlertSeverity` mismatch pattern** — check whether a local type
      shadows a UAC canonical one that moved/renamed, or whether an import path is stale. If it's one root cause, fixing
      it may resolve a large fraction of the 43 errors at once. **Done when**: the root cause is identified and
      documented (or fixed, if small). Repo: alerting-service.
- [ ] [INFRA] P1. **Fix or ratchet the remaining basedpyright errors in alerting-service** so the repo can ship again.
      **Done when**: `bash scripts/quality-gates.sh` type-check phase passes (0 errors, or the ratchet is re-baselined
      with each entry justified as genuine pre-existing debt, never silently raised without review). Repo:
      alerting-service.
- [ ] [INFRA] P2. **Fix the one unrelated error**: `alerting_service/subscribers/alert_subscriber.py:103` —
      `_EVENTS_INITIALISED` redefinition (`reportConstantRedefinition`) is a distinct, probably-trivial issue from the
      DefiAlertType/AlertSeverity cluster; fix independently. Repo: alerting-service.

## Progress Log

- **2026-08-12 (filed, slot-1 interactive)**: discovered as a side effect of validating quickmerge `--isolated` mode on
  a second repo for `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` todo E. Not investigated beyond
  what's captured above; filed so the finding survives session end rather than being lost to chat.
