#!/usr/bin/env bash
#
# repro-stash-pathspec-loss.sh
#
# Scratch-repo repro of the two git-stash hypotheses in
#   cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md  item 1
# (source: plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md).
#
# Hypothesis (a): a STATIC, non-re-derived pathspec passed to repeated
#   `git stash push -- <list>` calls across push/pull/pop cycles drops content.
# Hypothesis (b): `git stash push -- $pathspec` where $pathspec is transiently empty
#   (nothing dirty at that instant) silently NO-OPS rather than erroring — no stash is
#   created and the exit code is 0 — so a following UNCONDITIONAL `git stash pop` pops
#   whatever unrelated stash happens to be on top of the stack.
#
# Tests (each in its own throwaway origin/work/upstream scratch repo under mktemp -d):
#   T1  (a, zero-commit flow): the incident's own observed shape — conflicts are
#       resolved in the working tree and NEVER committed. Static list across 4 forced-
#       conflict cycles. Verdict: content preserved or lost?
#   T2  (a+b handoff, commit flow): the doc's exact sequence — push static -> pull ->
#       pop with conflict -> resolve+COMMIT (sweeping the pop-staged files) -> push the
#       SAME static list again -> pull -> pop. Shows the second push NO-OPS (tree clean)
#       and the blind pop then pops the OLD KEPT stash, not a fresh one.
#   T3  (b1): empty/clean pathspec `stash push` no-op mechanics (exit code, stash count,
#       stderr message).
#   T4  (b2): no-op push -> blind `stash pop` pops an UNRELATED stash ON TOP, stranding
#       the agent's own stash underneath.
#   T5  (b3, compound): a STALE static list makes the push a no-op EVEN WHILE OTHER
#       (non-listed) files are dirty, so the blind pop re-introduces stale content with
#       no error.
#
# Exit code is always 0 — this is a measurement, not a gate.
#
# Run:   bash scripts/dev/repro-stash-pathspec-loss.sh
# Verdicts (2026-08-20):
#   T1  (a standalone, zero-commit): RULED OUT — all markers preserved across cycles.
#   T2  (a+b handoff): CONFIRMED — static-list second push no-ops; blind pop hits the
#       old kept stash. This is the mechanism behind the incident's "content stranded in
#       stashes, working tree clean" symptom.
#   T3/T4/T5 (b): CONFIRMED — empty-pathspec push is a silent no-op; blind pop then pops
#       an unrelated stash (stale content revived / the agent's own stash stranded).
#
# Observed git behaviour worth noting (verified in T1's debug):
#   - A CONFLICTED `git stash pop` STAGES the non-conflicted files and KEEPS the stash.
#   - So a later `git commit` (or resolve-commit) with no path restriction SWEEPS the
#     agent's other staged-but-uncommitted files into the commit — a mis-attribution
#     surface on top of the stranding mechanism.
#
# Epic: agent_operating_framework_master
# Lifecycle: re-runnable repro harness; keep while the stash-based reconciliation
#   guidance it validates is live.
# Delete-when: never unless that guidance is fully retired.
# shellcheck disable=SC2086  # intentional word-split: pathspec lists are space-separated
set -u

ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT

PASS=0
FAIL=0

say() { printf '%s\n' "$*"; }
hr() { say '------------------------------------------------------------------'; }

verdict() { # verdict <label> <PASS|FAIL> <detail...>
  local label="$1" rc="$2"
  shift 2
  say "VERDICT[$label]: $rc"
  for l in "$@"; do say "    $l"; done
  if [ "$rc" = PASS ]; then PASS=$((PASS + 1)); else FAIL=$((FAIL + 1)); fi
}

# Scaffold a fresh origin/work pair (upstream commits are made via fresh per-commit
# clones in upstream_touch so the simulated upstream is never stale behind commits the
# work clone pushed); cwd -> work. Files A.txt..D.txt each start with a LINE0 marker
# plus a body line.
setup_repo() { # $1 = test tag
  ORIGIN="$ROOT/$1-origin.git"
  WORK="$ROOT/$1-work"
  UPSTREAM="$ROOT/$1-upstream"
  git init --bare -b main -q "$ORIGIN"
  git clone -q "$ORIGIN" "$WORK" 2>/dev/null
  git -C "$WORK" config user.name Repro
  git -C "$WORK" config user.email repro@example.com
  for f in A B C D; do printf 'LINE0\nbody %s v1\n' "$f" > "$WORK/$f.txt"; done
  git -C "$WORK" add A.txt B.txt C.txt D.txt
  git -C "$WORK" commit -qm "seed"
  git -C "$WORK" push -q origin main
  cd "$WORK"
}

# Simulate another session landing a commit on origin: rewrite $1's LINE0 line with $2
# so a later stash pop on that file is forced to CONFLICT (both sides changed the line).
# Uses a FRESH clone of origin so the simulated upstream is never stale behind commits
# the work clone pushed (the real fleet's other sessions rebase/land on the same branch).
upstream_touch() { # $1 = file, $2 = marker
  local tmp="$ROOT/upstream-touch-$$"
  git clone -q "$ORIGIN" "$tmp" 2>/dev/null
  git -C "$tmp" config user.name Repro
  git -C "$tmp" config user.email repro@example.com
  sed -i "0,/LINE0/s//LINE0_$2/" "$tmp/$1"
  git -C "$tmp" add -A
  git -C "$tmp" commit -qm "$2"
  git -C "$tmp" push -q origin main
  rm -rf "$tmp"
}

# After a conflicted `git stash pop`, resolve every unmerged file by keeping BOTH sides
# (strip conflict markers) and `git add` — the "agent resolved the conflict" step.
# commit_msg, when given, also COMMITS (sweeping whatever the pop left staged) and the
# caller is expected to push — models the commit-sweep agent flow.
resolve_conflicts() { # $1 = optional commit message
  local -a unmerged
  local f
  readarray -t unmerged < <(git diff --name-only --diff-filter=U)
  for f in "${unmerged[@]}"; do
    sed -i '/^<<<<<<< /d; /^=======$/d; /^>>>>>>> /d' "$f"
    git add "$f"
  done
  if [ "${1:-}" ]; then
    git commit -qm "$1"
  fi
}

# -------------------------------------------------------------------------------
# T1 — hypothesis (a), the incident's OWN zero-commit flow: static pathspec across
# repeated push/pull/pop cycles, conflicts resolved in the tree but NEVER committed.
# -------------------------------------------------------------------------------
test_a_zero_commit_flow() {
  hr
  say 'TEST T1 (a): static pathspec, zero-commit flow, 4 forced-conflict cycles'
  setup_repo a
  for f in A B C D; do sed -i "0,/LINE0/s//LINE0_SED_$f/" "$f.txt"; done
  local STATIC="A.txt B.txt C.txt D.txt"

  # per-file upstream marker that lands during each cycle (pulled, then pop conflicts)
  say '  cycle 1: push -- static | upstream B | pull | pop(conflict B) | resolve in-tree'
  git stash push -m "a-c1" -- $STATIC >/dev/null 2>&1
  upstream_touch B.txt UPB1
  git pull --ff-only -q origin main
  git stash pop >/dev/null 2>&1
  resolve_conflicts

  say '  cycle 2: push -- static | upstream C | pull | pop(conflict C) | resolve in-tree'
  git stash push -m "a-c2" -- $STATIC >/dev/null 2>&1
  upstream_touch C.txt UPC2
  git pull --ff-only -q origin main
  git stash pop >/dev/null 2>&1
  resolve_conflicts

  say '  cycle 3: push -- static | upstream D | pull | pop(conflict D) | resolve in-tree'
  git stash push -m "a-c3" -- $STATIC >/dev/null 2>&1
  upstream_touch D.txt UPD3
  git pull --ff-only -q origin main
  git stash pop >/dev/null 2>&1
  resolve_conflicts

  say '  cycle 4: push -- static | upstream A | pull | pop(conflict A) | resolve in-tree'
  git stash push -m "a-c4" -- $STATIC >/dev/null 2>&1
  upstream_touch A.txt UPA4
  git pull --ff-only -q origin main
  git stash pop >/dev/null 2>&1
  resolve_conflicts

  # Every file's own SED marker AND its upstream marker must be present in the tree.
  local lost=0
  local f up
  for f in A B C D; do
    up=$(case "$f" in A) echo UPA4;; B) echo UPB1;; C) echo UPC2;; D) echo UPD3;; esac)
    if ! grep -q "LINE0_SED_$f" "$f.txt"; then lost=1; say "  LOST from tree: LINE0_SED_$f"; fi
    if ! grep -q "LINE0_$up" "$f.txt"; then lost=1; say "  LOST from tree: LINE0_$up"; fi
  done
  local nstash
  nstash=$(git stash list | wc -l | tr -d ' ')
  say "  kept-stashes=$nstash (all 4 conflicted-pop keeps — the recoverable surface)"
  if [ "$lost" = 0 ]; then
    verdict 'T1 (a) standalone, zero-commit' PASS \
      "all agent + upstream markers preserved across 4 static-list cycles; nothing lost from the tree"
  else
    verdict 'T1 (a) standalone, zero-commit' FAIL "content lost — inspect above"
  fi
}

# -------------------------------------------------------------------------------
# T2 — the doc's EXACT sequence with a commit-sweep resolve: the second static-list
# push NO-OPS (tree clean after the sweep commit) and the blind pop then pops the OLD
# KEPT stash, not a fresh one.
# -------------------------------------------------------------------------------
test_a_b_handoff() {
  hr
  say 'TEST T2 (a->b handoff): doc exact sequence, commit-sweep flow'
  setup_repo b
  for f in A B C D; do sed -i "0,/LINE0/s//LINE0_SED_$f/" "$f.txt"; done
  local STATIC="A.txt B.txt C.txt D.txt"

  say '  cycle 1: push -- static | upstream B | pull | pop(conflict) | resolve+commit(sweeps staged A/C/D) | push'
  git stash push -m "b-c1" -- $STATIC >/dev/null 2>&1
  upstream_touch B.txt UPB1
  git pull --ff-only -q origin main
  git stash pop >/dev/null 2>&1
  resolve_conflicts "b-c1-resolve"     # commits resolved B AND the pop-staged A/C/D
  git push -q origin main              # agent ships between batches
  # state: tree CLEAN, stash@{0} = b-c1 (kept from the conflicted pop)

  say '  cycle 2: push the SAME static list again (no git status re-query) -> observe no-op'
  local before after
  before=$(git stash list | wc -l | tr -d ' ')
  git stash push -m "b-c2" -- $STATIC >/dev/null 2>&1
  after=$(git stash list | wc -l | tr -d ' ')
  say "  stash_count ${before}->${after} (equal = the push NO-OPed: every listed file clean)"

  say '  cycle 2: upstream C | pull | blind pop -> which stash does it hit?'
  upstream_touch C.txt UPC2
  git pull --ff-only -q origin main
  local top_before
  top_before=$(git stash list | head -1)
  git stash pop >/dev/null 2>&1
  local top_after
  top_after=$(git stash list | head -1)
  local hit_old=0
  echo "$top_before" | grep -q "b-c1" && hit_old=1
  say "  pop target was: ${top_before%%:*}  (contains old kept b-c1? $hit_old)"

  if [ "$after" = "$before" ] && [ "$hit_old" = 1 ]; then
    verdict 'T2 (a->b handoff)' PASS \
      "the SAME static list pushed again after a commit-swept cycle NO-OPs; the blind pop then hits the OLD KEPT stash"
  else
    verdict 'T2 (a->b handoff)' FAIL "sequence did not no-op / did not hit the old kept stash"
  fi
}

# -------------------------------------------------------------------------------
# T3 — hypothesis (b1): empty/clean pathspec `stash push` silently no-ops.
# -------------------------------------------------------------------------------
test_b_noop_push() {
  hr
  say 'TEST T3 (b1): empty/clean pathspec `stash push` is a silent no-op'
  setup_repo c

  local before after out rc
  before=$(git stash list | wc -l | tr -d ' ')
  out=$(git stash push -m "c-noop" -- 2>&1)
  rc=$?
  after=$(git stash list | wc -l | tr -d ' ')
  say "  exit=$rc  stash_count ${before}->${after}  stderr='$out'"
  if [ "$rc" = 0 ] && [ "$after" = "$before" ]; then
    verdict 'T3 (b1) no-op push' PASS "exit 0, NO stash created — silent no-op confirmed"
  else
    verdict 'T3 (b1) no-op push' FAIL "push did not behave as a silent no-op"
  fi
}

# -------------------------------------------------------------------------------
# T4 — hypothesis (b2): no-op push -> blind `stash pop` pops the UNRELATED stash ON
# TOP, stranding the agent's own stash underneath it.
# -------------------------------------------------------------------------------
test_b_wrong_pop() {
  hr
  say 'TEST T4 (b2): no-op push -> blind pop pops the unrelated stash, stranding the agent own stash'
  setup_repo d

  printf 'hbase\n' > H.txt
  git add H.txt
  git commit -qm "h"
  git push -q origin main
  # Agent's REAL content stashed first -> underneath.
  printf 'H_REAL\n' >> H.txt
  git stash push -m "agent-real" >/dev/null 2>&1          # stash@{1} (after next push)
  # An UNRELATED entry lands on top (e.g. the failed-commit hook's own patch autostash).
  printf 'H_OTHER\n' >> H.txt
  git stash push -m "other-cycle" >/dev/null 2>&1         # stash@{0}
  # Tree clean again; the agent's own push is a NO-OP (nothing dirty)...
  git stash push -m "agent-noop" -- >/dev/null 2>&1
  # ...so the blind pop hits the unrelated entry, not the agent's.
  git stash pop >/dev/null 2>&1
  local other_applied=0 real_stranded=0
  grep -q 'H_OTHER' H.txt && other_applied=1
  git stash list | grep -q 'agent-real' && real_stranded=1
  say "  unrelated H_OTHER applied to tree? $other_applied ; agent-real still stranded on stack? $real_stranded"
  if [ "$other_applied" = 1 ] && [ "$real_stranded" = 1 ]; then
    verdict 'T4 (b2) wrong-pop' PASS \
      "blind pop applied the UNRELATED stash and LEFT the agent real stash stranded underneath"
  else
    verdict 'T4 (b2) wrong-pop' FAIL "wrong-pop / stranding not demonstrated"
  fi
}

# -------------------------------------------------------------------------------
# T5 — hypothesis (b3) compound: a STALE static list no-ops the push WHILE OTHER files
# are dirty, so the blind pop re-introduces stale content with no error.
# -------------------------------------------------------------------------------
test_b_stale_list_compound() {
  hr
  say 'TEST T5 (b3): stale static list no-ops the push while OTHER files are dirty; blind pop re-introduces stale content'
  setup_repo e

  printf 'fbase\n' > F.txt
  printf 'gbase\n' > G.txt
  git add F.txt G.txt
  git commit -qm "seed2"
  git push -q origin main
  # Old unrelated stash touching F.txt only (a kept/forgotten entry).
  printf 'F_OLD\n' >> F.txt
  git stash push -m "old-f" >/dev/null 2>&1
  # Agent's REAL current work: G.txt dirty. The static list is STALE (from an earlier
  # cycle) and names only F.txt, which is clean right now.
  printf 'G_NEW\n' >> G.txt
  local stale="F.txt"
  git stash push -m "agent-cycle" -- $stale >/dev/null 2>&1   # NO-OP despite dirty G

  local before after
  before=$(git stash list | wc -l | tr -d ' ')
  git stash pop >/dev/null 2>&1                               # blind pop
  after=$(git stash list | wc -l | tr -d ' ')
  local f_old=0 g_new=0
  grep -q 'F_OLD' F.txt && f_old=1
  grep -q 'G_NEW' G.txt && g_new=1
  say "  stash_count ${before}->${after}; F.txt polluted with stale F_OLD? $f_old ; agent G_NEW still in tree? $g_new"
  if [ "$f_old" = 1 ] && [ "$g_new" = 1 ]; then
    verdict 'T5 (a+b compound)' PASS \
      "stale list silent-no-oped the push; blind pop re-introduced stale content, real work untouched"
  else
    verdict 'T5 (a+b compound)' FAIL "compound not demonstrated"
  fi
}

main() {
  say 'git stash pathspec repro — scratch-repo harness'
  test_a_zero_commit_flow
  test_a_b_handoff
  test_b_noop_push
  test_b_wrong_pop
  test_b_stale_list_compound
  hr
  say "SUMMARY: $PASS PASS / $FAIL FAIL (verdicts)"
  hr
  say 'Interpretation for the source issue:'
  say '  (a) The stale, non-re-derived pathspec is NOT itself what erases content: with a'
  say '      push followed by its own pop every cycle (T1, conflicts resolved in-tree), all'
  say '      content round-trips through the stashes and stays in the tree. Its only'
  say '      mechanical behaviour is that it SILENTLY SKIPS clean files -> a no-op push'
  say '      when none of the listed files is dirty -> the blind pop then hits an unrelated'
  say '      stash (T2/T4/T5). So (a) is a contributing precondition, not the dropping'
  say '      mechanism.'
  say '  (b) CONFIRMED: an empty pathspec `stash push` exits 0 and creates NO stash, so an'
  say '      unconditional `stash pop` pops whatever unrelated entry is on top of the stack'
  say '      (stale content revived into a clean tree, or the agent own stash stranded).'
  say '  Practical fix (matches the source doc): re-derive the pathspec from live `git status`'
  say '      AND only `stash pop` when `git stash list | wc -l` actually grew after the push.'
  exit 0
}

main "$@"
