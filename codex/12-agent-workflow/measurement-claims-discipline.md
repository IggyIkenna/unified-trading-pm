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
| exit code 0                  | the thing under test ran                       | A `cd` that failed, an `&&` chain that short-circuited, a flag that silently no-op'd (`cherry-pick -q`), a test asserting on a hand-built shape production never produces. **Strongest form — a PIPE fabricates it**: `pipefail` is OFF in this workspace's shell, so `cmd \| tail -40` reports TAIL's status, never `cmd`'s. Verified: `(exit 7) \| tail -1` → `0`. See "Long-running commands" below.                                                                                |
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

## Long-running commands: CAPTURE, never `| tail` (gates, quickmerge, safe-doc-push, VM jobs)

`pipefail` is **OFF** in this workspace's shell (verify: `set -o | grep pipefail`). So `cmd | tail -40` throws away
`cmd`'s exit status and hands you `tail`'s, which is 0 essentially always. Verified mechanically: `(exit 7) | tail -1` →
`0`; `(exit 7) > /dev/null` → `7`. This is not a weak proxy, it is a **fabricated** one — the pipe manufactures a
success signal that no part of the system ever produced.

It costs you twice, and the second cost is the expensive one:

1. **A fabricated green.** Measured 2026-08-15: a UAC gate reported "exit code 0" while its pytest summary said
   `1 failed`; a `quickmerge` reported "exit code 0" while it had actually printed `QUICKMERGE_BLOCKED` and pushed
   nothing. Both looked identical to a clean pass.
2. **The truncated verdict — the part you cut is where the fix instruction lives.** `tail -N` keeps the END of the
   stream, but a gate's diagnosis is not always last. In the same session `[re-gate] ❌ Files exceed 900 lines:` arrived
   with its file list already scrolled past, and quickmerge's own remedy line —
   `Re-run ... with IGNORE_TIMEOUT=true if the content already gated green` — was only ever visible once the output was
   captured whole. That one line was the entire fix; a blind `tail` had been hiding it across two prior attempts.

**The pattern** (scratchpad path, not `/tmp`):

```bash
OUT="$SCRATCHPAD/uac_quickmerge.log"
bash scripts/quality-gates.sh --no-fix > "$OUT" 2>&1
echo "REAL_EXIT=$?"                      # the actual status, before any pipe can eat it
grep -E 'ALL QUALITY GATES|FAILED|❌|BLOCKED' "$OUT" | head   # extract the VERDICT, not the last N lines
```

**Do not delete the log when the command finishes.** Its whole value is that it outlives the invocation: when a run
fails you grep the file instead of re-running a 300–450s gate to see what it already told you. The scratchpad is
session-scoped and discarded automatically, so there is nothing to clean up — an explicit `rm` only recreates the re-run
cost this pattern exists to avoid.

**Context/token note** (secondary, but real): a targeted `grep` for the verdict puts ~5 lines in context where a blind
`tail -40` puts 40, and — far more significantly — it removes whole re-invocations. Each avoided gate re-run saves both
its wall-clock and a full cached-prompt-prefix re-read (~406k tokens, measured). The correctness win is the reason for
the rule; the budget win follows from it.

## The absence-from-one-probe failure (2026-08-12, five instances in one session)

**The single most expensive error class measured to date: asserting a thing is ABSENT after one probe.** Five instances
in one session, costing more than every other error kind combined. The generalisation is stronger than "0 hits ≠
missing" — it is **a negative result is a statement about your probe until you have established the probe could have
found the thing.**

| What was wrongly declared absent                   | Why the probe missed it                                                                                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| SOL LST staking data ("possibly `BLOCKED-DATA`")   | Data lives under data-type **`lst_rates`**; grepped `staking_yields`. **Three** successive wrong verdicts on one question |
| `staking_yields` "has no schema contract"          | It is in `_defi_v2_contracts.py`; `lst_rates` is in `contracts.py`. **Neither file is "the" registry**                    |
| Hot reload "absent from strategy-service"          | Searched `engine/core/` + `config.py`; `config_reloaders.py` sits at package root                                         |
| Dispersion params "not in `PARAM_SCHEMA_REGISTRY`" | Grep formatting artifact. **Loading the registry in Python** gave the real answer                                         |
| Three separate plan phrases "missing"              | **Prettier wraps prose mid-sentence**, so the phrase spans a newline                                                      |

**Three more instances, 2026-08-15, all on the same investigation** — the class did not stop at code searches:

| What was wrongly declared                                    | Why the probe missed it                                                                                                                                                                                                |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Revocation "has never successfully fired"                    | Searched logs for `revocation_action` / `DP-REVOCATION`; the writer emits **`revocation deps_drain delivered`**. The empty result was read as CONFIRMATION on a mechanism that had delivered to 30 VMs in 12h          |
| Revocation "rejects every alert it sees, zero evaluations"   | Measured ONE Cloud Run job (`dp-meta-watchers`) and stated the conclusion about **the mechanism**. A second job was delivering correctly the whole time                                                                |
| Emitters of an alert id (`rg -rn -o 'DP-(LIVE\|WATCHER)-…'`) | `-r` is rg's **`--replace`**, so `-rn` consumed `n` as the replacement text and every match printed `:n`. A malformed flag produced silent, plausible-looking output — not an error                                    |
| PBMS "deployed as a service in NO environment"               | Listed Cloud Run for a service NAMED pbms/position, found none. It is **mounted inside strategy-service** (`app.mount("/position", …)`) and ships with it. **Searched for a deployment UNIT; never read the consumer** |

**The PBMS row is the most expensive of the four**, because a negative result was written straight into a codex SSOT and
an `[OPERATOR]` todo asking someone to deploy an already-deployed thing — work against a non-problem. It was caught only
because the operator said "I thought that was inside strategy-service now". **When a probe's answer would create work
for someone else, the bar rises: read the consumer before writing the finding down.** A thing can be absent as a
deployment unit and fully present as a mounted module; "is it deployed" and "is there a service named X" are different
questions, and only the second was asked.

**The middle row is the one worth internalising: the SCOPE of your probe bounds the scope of your claim.** "Job X
rejects every alert" and "the mechanism never fires" are different sentences with different blast radii, and only the
first was measured. Before writing a conclusion, check whether its subject is the thing you actually sampled — an
instance-scoped measurement stated as a system-scoped verdict is wrong even when the measurement itself is perfect.

**The four discharges, in order of cheapness:**

1. **For anything with a registry, ASK THE REGISTRY.** `python3 -c "from … import REGISTRY; print(len(REGISTRY))"` beats
   any grep and cannot be defeated by formatting. This alone would have caught two of the five.
2. **Enumerate the vocabulary the WRITER emits, then search for that** — never for the name you expect. A data type,
   enum member or path segment you invented is not evidence of anything.
3. **Normalise before grepping prose**: `tr -s ' \n' ' '`. In a prettier-formatted corpus, 0 hits for a multi-word
   phrase is uninformative.
4. **One file is not a registry.** Schemas, capabilities and enums are split across modules here by design; a
   single-file grep establishes only what that file contains.
5. **A negative from LOGS needs the same vocabulary discipline as a negative from code** — read the emitting
   `logger.*`/`log_event` call and search for ITS format string, never for the field name you would have chosen. Prefer
   a stable literal the writer definitely emits (`revocation deps_`) over a semantic guess (`revocation_action`).
6. **Sanity-check the flags before trusting a zero.** A single-letter flag that silently changes a tool's MODE (`rg -r`
   = replace, and the workspace `rg` config has already turned `-E` into `--encoding` once) turns a real search into a
   no-op that still exits 0. If a search returns nothing, re-run it once in its simplest possible form — no combined
   short flags — before recording the absence.

**A corollary that cost its own time: over-stating an error's scope is itself a defect.** Twice in that session a
correction was broader than the fault — "there is no `templates/` directory" (one exists, elsewhere) and "the
liquidity-provision family is invented" (`DEFI_LP_CONCENTRATED`/`_POOL`/`_VAULT` are real; it was misfiled, not
fabricated). **A reader acts on the record, so an over-broad correction sends them to delete something true.** Diagnose
the exact shape before writing it down.

**And the most dangerous variant: a doc and the code agreeing does not make either right.** "8 allocator archetypes"
appeared in the codex SSOT _and_ in the code docstring against a registry of 17 — so cross-checking doc against code
CONFIRMED the error. Corroboration between two derived artefacts is not verification; only the registry is.

## Duplicate-content corruption — verify a large text block isn't already present before appending (three instances, 2026-08-16)

**A large multi-paragraph Edit/append is a claim that the content is NEW — verify that before landing it, not after.**
Three independent instances in one session, all the same shape: a big chunk of prose (a codex-doc correction, a plan
todo bullet, an auto-generated index block) got appended a second time, verbatim or near-verbatim, onto content that was
already there — in `/codex/05-infrastructure/manifest-consolidator-ssot.md` (a 60-line "CORRECTED 2026-08-16" block,
committed once in `d85158ab02`, then re-appended uncommitted on top of itself — `grep -c` for a distinctive phrase found
2 occurrences where 1 was correct), in this session's own tracking plan (a ~40-line todo block duplicated with a
corrupted fragment spliced into one copy), and in `/plans/active/INDEX.md` (an auto-generated block regenerated 5-6 times
without clearing the previous run — `_Auto-generated ... 350 plans_` / `352 plans` / `303 plans` / `314 plans` /
`284 plans` / `285 plans` stacked as six consecutive header lines, each with its own duplicated `### cefi (N)` section
and duplicated plan-entry bullets beneath it).

**Why this evades the obvious checks**: the resulting file is still valid markdown/YAML, `docspec.py`/frontmatter
checks pass (they check schema, not content uniqueness), and a diff against HEAD looks like a normal-shaped addition
(N new lines) rather than an error — nothing about the diff's SHAPE signals duplication. The tell is in the CONTENT: a
distinctive phrase or count that should be unique appears twice.

**The rule**: before committing any Edit that appends or re-states more than a few lines of prose to an existing doc —
especially one you (or a dispatched agent) may have touched earlier in the same session, or one a concurrent session
might also be touching — grep the target file for a short, distinctive substring from the NEW content
(`grep -c "<distinctive phrase>" <file>`) and confirm it returns 1, not 2+. This is a two-second check that would have
caught all three instances above before they ever reached a diff. For a doc you suspect might already have the content
committed, also check `git show HEAD:<path> | grep -c "..."` — the working-tree copy can carry a duplicate that HEAD
does not (i.e., the correct content already shipped and your local edit is redundant), which is a DIFFERENT, cheaper fix
(`git restore` the file) than merging two genuinely-diverged copies.

**For auto-generated files specifically** (the INDEX.md case): a doubling pattern across MULTIPLE stacked headers is
evidence the regenerator script itself has a concurrency bug (two sessions running it against the same working tree
without a lock, each appending instead of the generator doing a clean truncate-and-rewrite) — this is a finding to file
against the generator, not something to hand-fix by deleting duplicate text, since the underlying race will just
reproduce it. See `/plans/active/issues/plan_index_regenerator_concurrent_write_duplication_2026_08_16.md`.

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
