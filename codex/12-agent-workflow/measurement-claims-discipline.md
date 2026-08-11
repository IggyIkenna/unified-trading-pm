---
doc_type: codex-ssot
title: Measurement-Claims Discipline — never report a property you did not measure
summary:
  SSOT for the rule that an agent's stated conclusion may not be stronger than the measurement behind it. A cheap proxy
  (line count, file size, name match, hit count, "the command exited 0") is NOT the property it stands in for, and
  silently upgrading proxy → property is how confident-sounding wrong claims reach the operator and get acted on. Gives
  the discharge rule (measure the real property, or say plainly it was not checked), the proxy→property table for the
  proxies that have actually misled in this workspace, and the standing instances the rule generalises.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [regression-prevention, verification, agent-behaviour, evidence, false-confidence]
related:
  [
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
  ]
created: 2026-08-10
authoritative_for: [measurement-claims discipline, proxy-metric vs property, grep-then-conclude generalisation]
referenced_by: [CLAUDE.md § "Agent behavior", cursor-configs/SUB_AGENT_MANDATORY_RULES.md]
owner:
last_reviewed:
code_refs:
---

# Measurement-Claims Discipline

> **The rule**: your CLAIM may never be stronger than your MEASUREMENT. If you measured a proxy, either measure the real
> property before speaking, or state plainly which property was not checked. "I checked X" when you checked a stand-in
> for X is not a shortcut — it is a false statement that the next decision is built on.

## Why this is its own rule

The workspace already enforces this in specific places — and kept having to, which is the signal it belongs at the top
level rather than once per domain:

- **Canonical path oracle** (`canonical_path_violations()`) is PATH-STRUCTURE-ONLY and VALUE-BLIND: it does not check
  the filename's `instrument_id`, nor `instrument_type`/`data_type`/`venue`/`chain` VALUES. CLAUDE.md's reconciliation
  section already says: check them separately **or say they weren't checked**.
- **Absence probes**: an absence result is evidence ONLY once you have confirmed you probed the vocabulary the WRITER
  actually emits — a wrong-vocabulary probe already produced one false "twin absent" verdict.
- **Grep-then-READ, not grep-then-conclude**: 0 hits ≠ missing, because features are runtime-resolved.

All three are the same rule wearing a domain costume. This doc is the general form; those stay as the domain-specific
statements of it.

## The proxies that have actually misled here

| Proxy measured               | Property claimed                               | Why the gap bites                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `wc -l` equal                | files are byte-identical                       | Equal length is not equal content. Two 84-line YAMLs differed in `runs-on`, `actions/checkout` version, and an invocation line.                                                                                                                                                                                                                                                                                                                                                        |
| `grep -c` = 0                | the symbol/feature is absent                   | Runtime-resolved consumers, or the wrong vocabulary probed.                                                                                                                                                                                                                                                                                                                                                                                                                            |
| exit code 0                  | the thing under test ran                       | A `cd` that failed, an `&&` chain that short-circuited, a flag that silently no-op'd (`cherry-pick -q`), a test asserting on a hand-built shape production never produces.                                                                                                                                                                                                                                                                                                             |
| a test passes                | the production path is covered                 | The pre-existing `_promote_pr_cause` tests all hand-built a PR dict WITH `mergeable_state`; production fed it a list-derived dict that never has that field, so the branch under test was dead code.                                                                                                                                                                                                                                                                                   |
| a name/path matches          | the content is the one meant                   | A generated snapshot (`hosted-baseline/`) sitting where a source template was assumed.                                                                                                                                                                                                                                                                                                                                                                                                 |
| tree hash equal              | same change                                    | Rebasing onto a moved base changes the tree; patch-id is the rebase-invariant identity.                                                                                                                                                                                                                                                                                                                                                                                                |
| local `origin/<branch>` ref  | what the remote holds                          | The cached ref goes stale under concurrent fleet activity — verify with `git ls-remote` or after an explicit fetch.                                                                                                                                                                                                                                                                                                                                                                    |
| "N workers feels like a lot" | a provider rate/concurrency limit is being hit | 33 AO slots sharing 2 DeepSeek accounts was assumed to be a likely concurrency collision causing a fleet-wide crash loop — DeepSeek's actually-published ceiling (api-docs.deepseek.com) is 500 concurrent connections on v4-pro, 2,500 on v4-flash, nowhere close to 33. The instinct-based number was never checked against the vendor's documented one before being stated as the likely cause. See `/plans/active/issues/fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md`. |

## The discharge

Pick one, explicitly:

1. **Measure the real property.** Content equality → `git hash-object` / `cmp -s` / `diff`. "Same work, different
   wrapping" → a WORD-level diff (`git diff --word-diff`), because a line diff on prose-wrapped files overstates the
   difference enormously — measured twice in one session, once at 34/39 "unique" lines that were 3 and 1 real tokens.
2. **State the limit.** "Line counts match; I did not diff the contents" is a perfectly good sentence and costs one
   clause. It leaves the reader able to decide whether that is enough.

What is NOT acceptable is silently narrating the proxy as the property. The failure is not in using a cheap check —
cheap checks are correct as pre-filters. It is in the sentence afterwards.

## Where it bit (2026-08-10, the incident this doc was written from)

Propagating a one-line workflow fix to the repos carrying `plan-alignment-agent.yml`, the agent ran `wc -l`, saw five
repos at 84 lines and the template at 84-plus-its-own-edit, and reported to the operator: _"5 of 6 matched the template
byte-for-byte at 84 lines."_ It had measured length. Acting on that claim would have rendered the template over all six
copies and shipped three regressions inside a commit labelled as a one-line npm fix:

- `instruments-service` and `market-data-processing-service` migrated from `runs-on: ubuntu-latest` onto the
  `[self-hosted, glue]` pool — repos that never had the bug being fixed;
- `actions/checkout` v4→v5 in `market-tick-data-service`;
- a changed `claude --print` invocation and `GH_ORG` form in `execution-service`.

What caught it was not a better instinct but a cheap follow-up: printing the diff's REMOVED lines per repo before
committing. The removed set is the honest answer to "what does this overwrite?", and it is one command.

Corollary worth keeping: the rule cuts both ways on drift. The same session found the TEMPLATE was the stale side —
`strategy-service` carried a `concurrency:` block the template lacked, so the render would have silently stripped it.
"Never hand-edit a per-repo copy" is usually framed as protecting the template; verify the template is a SUPERSET of
every live copy before any rollout, not merely that it differs.
