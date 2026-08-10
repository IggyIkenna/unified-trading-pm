#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for reconcile-sha-citations.sh PASS 2 (cross-repo orphan healing).
#
# WHY THIS EXISTS. The bug it guards is silent by construction: a citation to a rebased-away
# commit still passes `git cat-file -t` on the machine that wrote it (the orphaned object is
# right there), and only fails in CI and on every other slot. So "it worked when I tried it"
# proves nothing, and the only honest check is a constructed workspace where the orphan and
# its landed twin both exist and the healer has to tell them apart.
#
# The three negatives matter as much as the positive: a healer that rewrites a CORRECT
# citation is worse than the stale one it replaces. Case 2 (committed, not yet pushed) is the
# one that would actually happen in production every day -- Commit+Push+Flip cites work that
# is still local at the moment the flip is written.
#
# Builds a throwaway workspace under $TMPDIR; touches no real repo. Usage: run it, no args.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$HERE/reconcile-sha-citations.sh"

WS="$(mktemp -d "${TMPDIR:-/tmp}/xrepo-cite-XXXXXX")"
trap 'rm -rf "$WS"' EXIT
BR="live-defi-rollout"
pass=0
fail=0

_git() { git -C "$1" -c user.name=t -c user.email=t@t "${@:2}"; }

check() { # check <name> <expected> <actual>
  if [ "$2" = "$3" ]; then
    printf '  ✅ %s\n' "$1"
    pass=$((pass + 1))
  else
    printf '  ❌ %s\n     expected: %s\n     actual:   %s\n' "$1" "$2" "$3"
    fail=$((fail + 1))
  fi
}

# ── workspace: a bare "origin" + a service clone + a PM clone ───────────────────────────────
git init -q --bare "$WS/origin-svc.git"
git init -q --bare "$WS/origin-pm.git"
git clone -q "$WS/origin-svc.git" "$WS/fake-service"
git clone -q "$WS/origin-pm.git" "$WS/unified-trading-pm"
SVC="$WS/fake-service"
PM="$WS/unified-trading-pm"

for r in "$SVC" "$PM"; do
  _git "$r" checkout -q -b "$BR"
  echo seed >"$r/seed.txt"
  _git "$r" add seed.txt
  _git "$r" commit -q -m "chore: seed"
  _git "$r" push -q origin "$BR"
done

# ── construct the orphan: commit locally, let origin move, rebase, push ─────────────────────
# A second clone stands in for the peer session that pushes first.
git clone -q "$WS/origin-svc.git" "$WS/peer"
_git "$WS/peer" checkout -q "$BR"
echo peer >"$WS/peer/peer.txt"
_git "$WS/peer" add peer.txt
_git "$WS/peer" commit -q -m "chore: peer moves origin"
_git "$WS/peer" push -q origin "$BR"

echo thing >"$SVC/thing.txt"
_git "$SVC" add thing.txt
_git "$SVC" commit -q -m "feat: the thing that was really done"
ORPHAN="$(_git "$SVC" rev-parse HEAD)" # the SHA a worker would cite RIGHT NOW
_git "$SVC" fetch -q origin
_git "$SVC" rebase -q "origin/$BR" >/dev/null 2>&1
LANDED="$(_git "$SVC" rev-parse HEAD)"
_git "$SVC" push -q origin "$BR"

[ "$ORPHAN" != "$LANDED" ] || {
  echo "❌ setup failed: rebase did not rewrite the SHA"
  exit 1
}
# The orphan must still RESOLVE locally -- that is precisely why the downstream checker passes
# on this machine and fails everywhere else. If it did not resolve, the test would be testing
# a different (easier) bug.
[ "$(_git "$SVC" cat-file -t "$ORPHAN")" = "commit" ] || {
  echo "❌ setup failed: orphan object already gone; test would be vacuous"
  exit 1
}

# A commit that is committed but NOT pushed -- a citation to this is CORRECT and must survive.
echo later >"$SVC/later.txt"
_git "$SVC" add later.txt
_git "$SVC" commit -q -m "feat: committed but not yet pushed"
UNPUSHED="$(_git "$SVC" rev-parse HEAD)"

# ── the plan file, citing all four cases ────────────────────────────────────────────────────
write_plan() {
  cat >"$PM/plan.md" <<EOF
- [x] 1. orphaned citation — fake-service@${ORPHAN:0:10}
- [x] 2. committed-not-pushed — fake-service@${UNPUSHED:0:10}
- [x] 3. already landed — fake-service@${LANDED:0:10}
- [x] 4. unknown repo — no-such-repo@${ORPHAN:0:10}
- [x] 5. full-length orphan — fake-service@${ORPHAN}
EOF
}
write_plan
_git "$PM" add plan.md
_git "$PM" commit -q -m "docs(plans): flip"

echo "=== PASS 2: cross-repo orphan healing ==="
(cd "$PM" && reconcile_sha_citations "$BR" plan.md) >"$WS/out.log" 2>&1
sed 's/^/     /' "$WS/out.log"

check "orphaned citation rewritten to the landed twin" \
  "fake-service@${LANDED:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/plan.md" | sed -n 1p)"

check "committed-but-not-pushed citation left ALONE" \
  "fake-service@${UNPUSHED:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/plan.md" | sed -n 2p)"

check "already-landed citation left ALONE" \
  "fake-service@${LANDED:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/plan.md" | sed -n 3p)"

check "citation for a repo with no sibling clone left ALONE" \
  "no-such-repo@${ORPHAN:0:10}" \
  "$(grep -oE 'no-such-repo@[0-9a-f]+' "$PM/plan.md")"

check "abbreviation length preserved (40-char citation stays 40)" \
  "fake-service@${LANDED}" \
  "$(grep -oE 'fake-service@[0-9a-f]{40}' "$PM/plan.md")"

check "the rewrite was folded into the commit, not left dirty" \
  "" \
  "$(_git "$PM" status --porcelain)"

# ── isolated-worktree path: cwd is a throwaway worktree, siblings live next to the CALLER ───
# This is the configuration safe-doc-push actually runs in on a laptop. If SDP_CALLER_REPO is
# ignored, _rsc_workspace_root lands in $TMPDIR, finds no sibling repos, and the whole pass
# silently no-ops -- green tests, zero healing in production.
echo "=== PASS 2 under isolated-worktree mode ==="
write_plan
_git "$PM" add plan.md
_git "$PM" commit -q -m "docs(plans): flip again"
ISO="$WS/iso-wt"
_git "$PM" worktree add -q --detach "$ISO" HEAD
(cd "$ISO" && SDP_CALLER_REPO="$PM" reconcile_sha_citations "$BR" plan.md) >"$WS/out2.log" 2>&1
sed 's/^/     /' "$WS/out2.log"
check "healing works when cwd is an isolated worktree (SDP_CALLER_REPO honoured)" \
  "fake-service@${LANDED:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$ISO/plan.md" | sed -n 1p)"

# ── ambiguity: two same-subject candidates on the branch, neither matching the orphan's tree ─
echo "=== ambiguity is refused, never guessed ==="
for n in 1 2; do
  echo "dup$n" >"$SVC/dup$n.txt"
  _git "$SVC" add "dup$n.txt"
  _git "$SVC" commit -q -m "chore: duplicated subject"
done
_git "$SVC" push -q origin "$BR"
echo amb >"$SVC/amb.txt"
_git "$SVC" add amb.txt
_git "$SVC" commit -q -m "chore: duplicated subject"
AMB="$(_git "$SVC" rev-parse HEAD)"
_git "$SVC" reset -q --soft HEAD~1 # orphan it without rewriting anything else
_git "$SVC" restore --staged . 2>/dev/null || _git "$SVC" reset -q HEAD

printf -- '- [x] ambiguous — fake-service@%s\n' "${AMB:0:10}" >"$PM/amb.md"
_git "$PM" add amb.md
_git "$PM" commit -q -m "docs(plans): ambiguous"
(cd "$PM" && reconcile_sha_citations "$BR" amb.md) >"$WS/out3.log" 2>&1
sed 's/^/     /' "$WS/out3.log"
check "ambiguous twin left ALONE" \
  "fake-service@${AMB:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/amb.md")"
check "ambiguity is reported, not silent" \
  "yes" \
  "$(grep -q 'left as-is' "$WS/out3.log" && echo yes || echo no)"

# ── patch-id must pick the RIGHT twin when the subject is not unique ─────────────────────────
# The dangerous case the subject key alone cannot handle: two commits on the branch share a
# subject, and only one is the rebased twin of the citation. PM subjects repeat constantly
# ("docs(plans): flip item 3 …"), so this is the common shape, not a corner case.
echo "=== patch-id picks the right twin among same-subject commits ==="
DUPSUB="chore: recurring subject"
echo decoy >"$SVC/decoy.txt" # same subject, DIFFERENT content -> different patch-id
_git "$SVC" add decoy.txt
_git "$SVC" commit -q -m "$DUPSUB"
_git "$SVC" push -q origin "$BR"

echo real >"$SVC/real.txt" # the one that will be cited
_git "$SVC" add real.txt
_git "$SVC" commit -q -m "$DUPSUB"
TWIN_ORPHAN="$(_git "$SVC" rev-parse HEAD)"
echo peer2 >"$WS/peer/peer2.txt" # origin moves under us -> the rebase rewrites the SHA
_git "$WS/peer" pull -q --rebase origin "$BR"
_git "$WS/peer" add peer2.txt
_git "$WS/peer" commit -q -m "chore: peer moves origin again"
_git "$WS/peer" push -q origin "$BR"
_git "$SVC" fetch -q origin
_git "$SVC" rebase -q "origin/$BR" >/dev/null 2>&1
TWIN_LANDED="$(_git "$SVC" rev-parse HEAD)"
_git "$SVC" push -q origin "$BR"
[ "$TWIN_ORPHAN" != "$TWIN_LANDED" ] || {
  echo "❌ setup failed: twin rebase did not rewrite the SHA"
  exit 1
}

printf -- '- [x] dup-subject — fake-service@%s\n' "${TWIN_ORPHAN:0:10}" >"$PM/twin.md"
_git "$PM" add twin.md
_git "$PM" commit -q -m "docs(plans): twin"
(cd "$PM" && reconcile_sha_citations "$BR" twin.md) >"$WS/out4.log" 2>&1
sed 's/^/     /' "$WS/out4.log"
check "healed to the patch-matching twin, not the same-subject decoy" \
  "fake-service@${TWIN_LANDED:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/twin.md")"

# ── a commit alive on ANOTHER ref (main) is not an orphan ───────────────────────────────────
# The false positive that a branch-scoped survival test produces, and the reason this test
# exists: measured on the real corpus, asking only "is it an ancestor of live-defi-rollout"
# classified 513 of 3336 citations as orphans; the all-refs question says 39. The other 474
# were alive on main / promote-PR refs / tags. This case is built so the weak oracle would
# actually REWRITE it -- same subject, same patch, different SHA on the integration branch --
# because a test the broken version passes proves nothing.
echo "=== a commit living on main (not LDR) is NOT an orphan ==="
echo projected >"$SVC/projected.txt"
_git "$SVC" add projected.txt
_git "$SVC" commit -q -m "feat: projected to main"
LDR_SHA="$(_git "$SVC" rev-parse HEAD)"
_git "$SVC" push -q origin "$BR"
# Branch from HEAD~2, not HEAD~1: cherry-picking onto the commit's OWN parent reproduces it
# byte-for-byte and git hands back the SAME SHA, which is another way this case goes vacuous.
_git "$SVC" checkout -q -b mainline "HEAD~2"
# NOT `cherry-pick -q` — cherry-pick has no -q (only --quit), so it errors out and, with
# output swallowed, leaves HEAD where it was. That made this whole case VACUOUS the first
# time it was written: MAIN_SHA came out as an ordinary LDR ancestor, both oracles skipped
# it, and the test "passed" against the very bug it was built to catch. Hence the setup
# assertions below — a negative test has to prove it is testing something.
_git "$SVC" cherry-pick "$LDR_SHA" >/dev/null 2>&1
MAIN_SHA="$(_git "$SVC" rev-parse HEAD)"
_git "$SVC" push -q origin mainline:main
_git "$SVC" fetch -q origin
_git "$SVC" checkout -q "$BR"
[ "$MAIN_SHA" != "$LDR_SHA" ] || {
  echo "❌ setup failed: cherry-pick produced the same SHA"
  exit 1
}
_git "$SVC" merge-base --is-ancestor "$MAIN_SHA" "origin/$BR" && {
  echo "❌ setup vacuous: the main-only commit is an ancestor of $BR, so no oracle would flag it"
  exit 1
}
[ "$(_git "$SVC" log -1 --format=%s "$MAIN_SHA")" = "$(_git "$SVC" log -1 --format=%s "$LDR_SHA")" ] || {
  echo "❌ setup vacuous: subjects differ, so the weak oracle would refuse for the wrong reason"
  exit 1
}

printf -- '- [x] on main only — fake-service@%s\n' "${MAIN_SHA:0:10}" >"$PM/mainref.md"
_git "$PM" add mainref.md
_git "$PM" commit -q -m "docs(plans): main-ref"
(cd "$PM" && reconcile_sha_citations "$BR" mainref.md) >"$WS/out5.log" 2>&1
sed 's/^/     /' "$WS/out5.log"
check "citation alive on origin/main left ALONE (not rewritten to its LDR twin)" \
  "fake-service@${MAIN_SHA:0:10}" \
  "$(grep -oE 'fake-service@[0-9a-f]+' "$PM/mainref.md")"

echo
echo "---- passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
