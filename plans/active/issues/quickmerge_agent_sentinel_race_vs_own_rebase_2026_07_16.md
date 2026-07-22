---
doc_type: issue
title:
  quickmerge.sh --agent can never validate its own QG sentinel when shipping PRE-COMMITTED work on a busy branch — STAGE
  0.4's rebase rewrites the very commit the STAGE 3 sentinel points at
summary: >
  `quickmerge.sh --agent` writes/consumes a `.qg_last_passed_sha` sentinel to skip a Pass-2 QG re-run. STAGE 0.4
  (quickmerge.sh:554) does `git pull --rebase --autostash` when the branch is BOTH ahead and behind, which REWRITES the
  SHAs of local unpushed commits. STAGE 3 (quickmerge.sh:1241-1262) then requires the sentinel to be `==` HEAD, or an
  ANCESTOR of HEAD for the content-scoped fallback. When the sentinel points at one of YOUR OWN unpushed commits — which
  is exactly what happens when you run `quality-gates.sh` after committing — the rebase orphans that commit, so it is
  neither equal to nor an ancestor of the new HEAD, and BOTH checks fail. The failure is self-inflicted and
  self-perpetuating: every retry re-rebases and re-invalidates the freshly-written sentinel. On `live-defi-rollout`,
  which the AO fleet pushes to every ~1-3 min, `--agent` therefore cannot self-validate at all. The design implicitly
  assumes UNCOMMITTED work (sentinel = an upstream commit, which survives the rebase because the dirty files are
  autostashed), but the same script explicitly supports the pre-committed path ("clean tree with N unpushed commit(s)
  ... shipping the committed work", quickmerge.sh:1494-1511). Cost ~5 failed ship attempts during the CI-cost B1 deploy
  on 2026-07-16. Affects EVERY agent shipping to a busy branch, not just that plan. Workaround (used, imperfect): chain
  `quality-gates.sh --no-fix && quickmerge.sh ...` in ONE shell so no upstream push can land between them.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, quality-gates, sentinel, race-condition, agent-workflow, developer-experience]
related:
  [
    plans/active/github_actions_ci_cost_reduction_2026_07_15.md,
    codex/08-workflows/ci-cd-flow.md,
    codex/06-coding-standards/quality-gates.md,
    codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: 2026-07-16
parent_epic: deployment_and_user_management_master
priority: P1
source:
  github_actions_ci_cost_reduction_2026_07_15 D1-D6 deploy, slot 1, 2026-07-16 — hit 5x while shipping the glue-runner
  work to LDR
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-16
locked_by:
resolved_by: unified-trading-pm@e264b3c9 (bounded retry — NOT this doc's own recommended fix B; see resolution note)
depends_on: []
---

# quickmerge `--agent` races its own rebase and invalidates its own QG sentinel

> **Operator 2026-07-16: "we will also fix the issues with quickmerge --agent, please write a new issue doc explaining
> this so I can work on that later on."** This doc is the write-up. **UNACKED** — no plan owns the fix yet.

## TL;DR

`quickmerge.sh --agent` rebases your commits in STAGE 0.4, then in STAGE 3 demands that a sentinel pointing at one of
those (now-rewritten) commits still be an ancestor of HEAD. It cannot be. **The tool invalidates its own precondition.**

It only bites when **all three** hold — which is the normal state for an agent on LDR:

1. you have **unpushed local commits** (`ahead > 0`), and
2. the branch is **also behind** (`behind > 0`) → STAGE 0.4 must **rebase**, not fast-forward, and
3. the sentinel points at **one of your own commits** (i.e. you ran `quality-gates.sh` _after_ committing).

## Why it happens (exact mechanism, with line refs)

**1. The sentinel is just `HEAD` at QG time** — `scripts/quality-gates-base/base-service.sh:3778`:

```bash
git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha"
```

So if you commit and then run QG, the sentinel is **your own unpushed commit**.

**2. STAGE 0.4 rewrites that commit** — `scripts/quickmerge.sh:552-554`:

```bash
if git pull --ff-only "$_QM_REMOTE_NAME" "$_QM_REMOTE_BRANCH" --quiet 2>/dev/null; then
  echo "✅ fast-forwarded to latest — now current"
elif git pull --rebase --autostash "$_QM_REMOTE_NAME" "$_QM_REMOTE_BRANCH" --quiet 2>/dev/null; then
  echo "✅ rebased local commits onto latest — now current"
```

`--ff-only` **cannot** succeed when you are ahead _and_ behind (diverged), so it falls through to `--rebase`. Rebase
replays your commits onto the new upstream tip, giving them **new SHAs**. Your old commit — the one the sentinel names —
becomes unreachable.

**3. STAGE 3 then requires ancestry that no longer exists** — `scripts/quickmerge.sh:1241-1262`:

```bash
if [ "$_SENTINEL_SHA" = "$_CURRENT_SHA" ]; then
  # SHA sentinel verified
elif [ -n "$FILES_ARG" ] \
     && git cat-file -e "${_SENTINEL_SHA}^{commit}" 2>/dev/null \
     && git merge-base --is-ancestor "$_SENTINEL_SHA" "$_CURRENT_SHA" 2>/dev/null \
     && git diff --quiet "$_SENTINEL_SHA" "$_CURRENT_SHA" -- $FILES_ARG 2>/dev/null; then
  # CONTENT sentinel verified
else
  echo "❌ Pass 1 quality-gates.sh sentinel invalid for current state."
  exit 1
fi
```

- `==` fails: HEAD is the **rebased** SHA, the sentinel is the **pre-rebase** SHA.
- The content fallback fails at `merge-base --is-ancestor`: the pre-rebase commit is an **orphan**, not an ancestor of
  the rebased HEAD.

Both arms fail → `exit 1`. Retrying re-runs QG (new sentinel), which STAGE 0.4 rebases again the moment another agent
pushes. **The loop is stable.**

## Why the design works for UNCOMMITTED work (and why that's the blind spot)

With a dirty tree and no local commits:

- the sentinel = the **upstream** commit you gated on;
- `--autostash` sets your dirty files aside, so the rebase has nothing of yours to rewrite; HEAD just fast-forwards;
- the old upstream commit **is** an ancestor of the new HEAD → `--is-ancestor` passes;
- your shipped files are unchanged **in git history** (they're dirty in the worktree, identical in both commits) →
  `git diff --quiet ... -- $FILES_ARG` passes → **CONTENT sentinel verified**.

That is the path the comment at `quickmerge.sh:1232-1240` describes ("an UNRELATED fast-forward ... advances HEAD and
stales a still-valid green QG"). It correctly solves the _someone else pushed_ case, but assumes the sentinel is a
commit **you don't own**. The moment the sentinel is your own commit, the same rebase that the fallback was written to
tolerate is the thing that breaks it.

This matters because the pre-committed path is **explicitly supported**, not an abuse — `quickmerge.sh:1494-1511`
prints:

```
[unified-trading-pm] clean tree with 2 unpushed commit(s) ahead of origin/live-defi-rollout — shipping the committed work
```

and amends a `Quickmerge:` trailer onto HEAD. So the script has a first-class pre-committed mode whose sentinel check
cannot pass on a busy branch.

It also collides with a HARD RULE: CLAUDE.md § "Quality gates BEFORE COMMIT — the commit is the per-repo quality
boundary" tells agents to **commit from a QG-green tree**. Following that rule produces exactly the sentinel-points-at-
my-own-commit state that breaks `--agent`.

## Reproduction

On a branch receiving pushes every ~1-3 min (LDR under the AO fleet):

```bash
# 1. do work, commit it (per the commit-from-a-green-tree rule)
git add <files> && git commit -m "..."
# 2. gate it -> sentinel = YOUR commit
bash scripts/quality-gates.sh --no-fix        # writes .qg_last_passed_sha = HEAD (your commit)
# 3. ship -> STAGE 0.4 rebases (a peer pushed), STAGE 3 rejects the sentinel it just certified
bash scripts/quickmerge.sh "msg" --agent --files '<files>'
# ❌ Pass 1 quality-gates.sh sentinel invalid for current state.
#    Sentinel: <pre-rebase sha>  HEAD: <post-rebase sha>
```

Observed 2026-07-16, five consecutive times, HEAD walking `e524bc944 → 748e52f4c → 5fb85f72e → 20a77504a` — one rewrite
per attempt.

## Observed BOTH ways on the same branch, minutes apart (2026-07-16, while writing this doc)

The analysis above is not inferred — both paths were exercised back-to-back on LDR under identical traffic (peer pushes
every ~2 min). The only variable was **committed vs uncommitted**.

**PRE-COMMITTED → fails.** quickmerge printed the mechanism itself, in two consecutive lines:

```
[unified-trading-pm] ✅ rebased local commits onto latest — now current      <- STAGE 0.4 rewrote MY commit
[unified-trading-pm] ❌ Pass 1 quality-gates.sh sentinel invalid for current state.   <- STAGE 3 rejects it
```

Confirmed by hand at the moment of failure:

```
sentinel : 619530d9c
HEAD     : e20b1c720
ahead=1 behind=0
sentinel is ancestor of HEAD? NO      <- rebased away; both STAGE 3 arms are now unsatisfiable
```

**UNCOMMITTED → passes, despite a peer pushing during the very same run:**

```
[unified-trading-pm] ✅ CONTENT sentinel verified — HEAD fast-forwarded 409135ffb→d1c76acac but the
--files set is byte-identical between them, so Pass-1 QG still covers exactly these files
```

Same branch, same push cadence, opposite result. The sentinel pointed at an **upstream** commit, so the pull was a
**fast-forward** (not a rebase of my own commits), ancestry held, and the content fallback worked exactly as designed.
**This is the proof that the fallback logic is sound and only the ancestry precondition is wrong** — which is why fix B
(relax ancestry, scoped via `ORIG_HEAD`) is the minimal correct change rather than a rewrite.

### Bonus: a SECOND busy-branch failure one layer down

Once the sentinel passed, quickmerge's own STAGE 5 commit was rejected by the `check-branch-drift` **pre-commit hook**
("You are 1 commit(s) behind origin/live-defi-rollout") — a peer had pushed between STAGE 0.4 and STAGE 5. So even after
the sentinel is fixed, quickmerge can still lose to a push inside its own run. Worth fixing in the same pass: re-check
drift (or pull) immediately before the STAGE 5 commit, rather than relying on the STAGE 0.4 snapshot.

## Workaround that actually works: DON'T pre-commit (use the path the design supports)

`git reset --soft HEAD~1` (never `--hard` — that destroys work and is BANNED), leave the change staged, gate it, and let
quickmerge do the commit via `--files`. The sentinel then names an upstream commit that the pull can only fast-forward
past, so the CONTENT fallback passes. This is what finally shipped this doc, and it is strictly more reliable than
racing the clock. Cost: quickmerge authors the commit message, so pass the full message as `$1` (it is multi-line safe).

## Weaker workaround (what was used for the earlier ships — narrows the window, does not close it)

Chain the gate and the ship in **one shell** so no upstream push can land between them:

```bash
git pull --rebase --autostash origin live-defi-rollout -q
timeout 900 bash scripts/quality-gates.sh --no-fix >/dev/null 2>&1 \
  && timeout 1200 bash scripts/quickmerge.sh "msg" --agent --files '<paths>'
```

This worked on the 6th attempt and for every ship afterwards. It is still a race: the window is now just QG duration
(~22s) plus STAGES 0-2, versus a ~1-3 min push cadence. It will fail again, just less often. **Do not treat this as the
fix.**

## Candidate fixes (pick one — B is the smaller, more honest change)

**A. Re-derive the sentinel AFTER STAGE 0.4.** Once the rebase settles, map the sentinel forward and re-certify. Costs a
rebase-aware SHA translation (`git reflog` / `ORIG_HEAD` walk), which is fiddly and easy to get subtly wrong.

**B. Make the content fallback use the MERGE-BASE instead of requiring ancestry.** The check's real question is _"were
the files I'm shipping verified by the last green QG?"_ — ancestry is a proxy that a rebase invalidates for no good
reason. Compare the shipped files against the **merge-base of the sentinel and HEAD**, or simply drop `--is-ancestor`
and keep `git diff --quiet "$_SENTINEL_SHA" "$_CURRENT_SHA" -- $FILES_ARG`:

- the `git cat-file -e` guard already proves the sentinel commit still exists (a rebased-away commit stays reachable via
  reflog for the gc window, so this holds in practice);
- the byte-identical diff on `$FILES_ARG` is the property that actually matters — if the shipped files are identical
  between the certified commit and HEAD, the Pass-1 QG still covers exactly those files, **whether or not** history was
  rewritten underneath.
- Safety to preserve: the current `--is-ancestor` also rejects **divergence/rewind** (per the comment at
  `quickmerge.sh:1239`). Dropping it wholesale would weaken that. Prefer scoping the relaxation to "sentinel is
  reachable **or** was rewritten by our own rebase this run" — e.g. record `ORIG_HEAD` in STAGE 0.4 and accept a
  sentinel that is an ancestor of `ORIG_HEAD`.

**C. Have quickmerge write the sentinel itself** after STAGE 0.4 and before STAGE 3, when it knows the tree is green and
the rebase has settled. Biggest change; removes the ordering hazard entirely.

**Recommendation: B, scoped via `ORIG_HEAD`.** It keeps the anti-rewind guard, is ~5 lines, and fixes the actual
question the gate is asking.

## Blast radius / why P1 not P3

- Hits **every agent** shipping pre-committed work to LDR — i.e. the default workflow under the commit-from-green-tree
  HARD RULE — not just the CI-cost plan.
- Failure mode is **wasted work, not wrong work**: it blocks the ship, it never ships something ungated. So it is
  expensive and confusing, not dangerous. That is why this is P1 and not P0.
- The tempting "fix" is the dangerous one: an agent that hits this 5 times may reach for `SKIP_BRANCH_DRIFT=1` or a raw
  `git push` (both BANNED for agents) purely to escape the loop. **The bug creates pressure toward the exact
  rule-violations the pipeline exists to prevent** — a real reason to fix it rather than document it.

## Verification for the fix

1. Reproduce per § "Reproduction" on LDR → confirm the `❌ sentinel invalid` with `ahead>0, behind>0`.
2. Apply the fix; re-run the same sequence **without** the one-shell chaining and with a deliberate concurrent push
   between the QG and the quickmerge (e.g. `git commit --allow-empty` from another clone, pushed in the gap).
3. Assert: `✅ CONTENT sentinel verified` and the shipped diff on origin is byte-identical to the local one.
4. Negative test — the anti-rewind guard must SURVIVE: point the sentinel at a commit on a genuinely **divergent**
   branch (not merely rebased) and assert it is still **rejected**. A fix that green-lights that has broken the
   protection it was meant to keep.

## Resolution (2026-07-22) — the operator-decided alternative, NOT this doc's fix B

**`unified-trading-pm@e264b3c9`** did **not** implement this doc's own recommended fix B (relax ancestry via
`ORIG_HEAD`-scoped content-diff). Between this doc (07-16) and the fix landing, a sibling doc
(`quickmerge_sentinel_invalidated_by_its_own_autopull_2026_07_18.md`) recorded an operator decision (2026-07-19) that
explicitly **rejects weakening the sentinel/ancestry check** — the STAGE-3 content fallback was independently hardened
the SAME window (2026-07-18, `TREE-scoped, NOT --files-scoped`) to compare the WHOLE tree rather than just `$FILES_ARG`,
precisely because typecheck/pytest are whole-program and a peer's edit to an unrelated file can break one you never
touched. That hardening is the opposite direction from this doc's fix B and stands.

The actual fix ships **Option 2** from the sibling doc (bounded retry with backoff+jitter): `quickmerge.sh`'s STAGE 0.4
pull was extracted into a reusable function (`_qm_stage_0_4_not_behind_gate`), and STAGE 3's AGENT_MODE sentinel check
was split into a checking function (`_qm_check_agent_sentinel`, returns 0/1, never exits) driven by an `until` loop that
on a lost race automatically re-pulls, re-runs `quality-gates.sh --no-fix`, and re-checks — up to 3 attempts with
`sleep $((2 + RANDOM % 4 + attempt * 3))` backoff — instead of hard-failing on the first loss and dumping the retry onto
the calling agent (which is what produced this doc's own "~5 failed ship attempts" and the sibling retry-storm doc's "27
consecutive full-QG losses"). The sentinel/ancestry logic itself is byte-for-byte unchanged. Verified: `bash -n` syntax
check, the existing `test-quickmerge-blocked-contract.sh` STAGE-0.4 extraction test (5/5 pass — confirms the
function-wrap didn't disturb the block the test slices out), `test_check_strict_quickmerge.py` (13/13 pass), and an
isolated control-flow harness exercising the retry loop's three cases (immediate success, success-on-retry, exhaustion)
against a faked sentinel-check/pull/gate. Full PM `quality-gates.sh` green. **Not yet covered**: doc1's "Bonus" residual
(STAGE 5's own commit can still lose to a peer push landing between STAGE 0.4 and STAGE 5) and the retry-storm doc's
Option 1 (a content-hash fast-path to skip a full re-gate when the tree delta is carve-out-only) remain open — the
latter needs care since `scripts/` isn't uniformly safe to fast-path across every repo (unlike PM, other repos'
`scripts/` can hold real tested Python).
