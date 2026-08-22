#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# reconcile-sha-citations.sh -- rewrite plan evidence citations that a rebase invalidated,
# BEFORE the push, instead of letting them surface downstream as a QG failure.
#
# THE FAILURE THIS FIXES (measured 2026-08-10). A worker commits its work locally (SHA X),
# records `Evidence: <repo>@X` in a plan todo, and ships. Both shipping scripts rebase onto
# origin before pushing -- which REWRITES every local commit, so what actually lands is SHA Y.
# The citation now points at an object that exists nowhere, and
# `check_plan_commit_sha_evidence.py` fails for work that was genuinely done. Live instance:
# `unified-trading-pm@0f9b8a65ca` cited in
# plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md; the
# change had really landed, as 034cb4e2ad. Nothing was fabricated -- the SHA simply aged out
# between `git commit` and `git push`.
#
# Why the pre-commit check cannot catch it: at commit time the citation IS resolvable (the
# local commit exists). The rebase invalidates it afterwards. So the only correct place to
# re-check is AFTER the rebase and BEFORE the push -- which is exactly here.
#
# TWO PASSES, because one mechanism cannot cover both cases:
#
#   PASS 1 (same repo, ORIG_HEAD): `git rebase` leaves the pre-rebase tip in ORIG_HEAD and
#   preserves each commit's SUBJECT, so for every commit now in origin/<branch>..HEAD we find
#   the pre-rebase commit with the identical subject in the ORIG_HEAD range; that pair IS the
#   old->new mapping. Precise, but only usable in the SAME repo and only in the same
#   invocation as the rebase (ORIG_HEAD is overwritten by the next one).
#
#   PASS 2 (cross-repo, ORPHAN DETECTION -- added 2026-08-10): a PM plan overwhelmingly cites
#   OTHER repos (`Evidence: market-tick-data-service@<sha>`), and PM's ORIG_HEAD says nothing
#   about a rebase that happened in MTDS. So pass 2 asks a question that needs no map at all:
#   is the cited commit reachable from anything that survives? A cited SHA that resolves in
#   the sibling clone but is an ancestor of NEITHER `origin/<integration-branch>` NOR that
#   repo's local HEAD is, by definition, an orphan left behind by a rebase -- and its landed
#   twin is the commit with the same subject (disambiguated by tree hash) on the branch.
#
#   Pass 2 also catches the SILENT variant of the same bug, which pass 1 cannot: the orphaned
#   object still EXISTS locally, so `git cat-file -t` succeeds and the downstream checker
#   passes on the machine that authored the citation -- then fails in CI and on every other
#   slot, where the object was never created. Reachability is the honest test; existence is
#   not. (The design note in the issue doc weighed a published old->new map vs patch-id
#   matching; reachability needs neither, and unlike both it still works when the citation is
#   written in a later session than the rebase.)
#
# THE FALSE-POSITIVE GUARD THAT MAKES PASS 2 SAFE: a citation for work that is committed but
# NOT YET PUSHED is perfectly valid -- it is reachable from the sibling repo's local HEAD.
# Healing it would rewrite a correct citation into a wrong one. Hence the ancestor test is
# against `origin/<branch>` OR local `HEAD`; only a commit reachable from neither is touched.
#
# Usage:  reconcile_sha_citations <branch> <file> [<file> ...]
#   Returns 0 always (best-effort; never blocks a push). Prints what it rewrote.
#   Set SHA_CITATION_RECONCILE=0 to disable.

# Rewrite `<repo>@<old-prefix>` -> `<repo>@<new-same-length>` in one file.
# Returns 0 if the file changed, 1 if nothing matched. Abbreviation length is preserved so a
# 10-char citation stays 10 chars.
_rsc_rewrite_file() {
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import re, sys, pathlib
path, repo, old, new = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
p = pathlib.Path(path)
text = p.read_text()
pat = re.compile(rf"\b{re.escape(repo)}@([0-9a-f]{{7,40}})\b")
def sub(m):
    cited = m.group(1)
    if old.startswith(cited):
        return f"{repo}@{new[:len(cited)]}"
    return m.group(0)
out = pat.sub(sub, text)
if out == text:
    raise SystemExit(1)
p.write_text(out)
print(f"  ↻ {path}: {repo}@{old[:10]} → {repo}@{new[:10]} (rebase rewrote the commit)")
raise SystemExit(0)
PY
}

# The workspace root that holds the sibling repo clones. Under isolated-worktree mode the
# script runs from a throwaway worktree in $TMPDIR, whose parent is NOT the workspace -- so
# the CALLER's repo path, as each ship script propagates it, is the authoritative anchor.
# Getting this wrong is SILENT: sibling lookup lands in $TMPDIR, finds nothing, and pass 2
# no-ops while reporting success.
_rsc_workspace_root() {
  local repo_root="${RSC_CALLER_REPO:-${SDP_CALLER_REPO:-${QM_CALLER_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}}"
  dirname "$repo_root"
}

# The integration branch ref to test reachability against, in a given sibling repo.
_rsc_integration_ref() {
  local rp="$1" ref
  for ref in origin/live-defi-rollout origin/main origin/master; do
    if git -C "$rp" rev-parse -q --verify "$ref" >/dev/null 2>&1; then
      echo "$ref"
      return 0
    fi
  done
  return 1
}

# PASS 1 -- same repo, driven by the ORIG_HEAD mapping this invocation's rebase left behind.
_rsc_pass_orig_head() {
  local branch="$1"; shift
  local orig_head
  orig_head="$(git rev-parse -q --verify ORIG_HEAD 2>/dev/null || true)"
  [ -n "$orig_head" ] || return 1

  local repo_name
  repo_name="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"

  local new_range old_range
  new_range="$(git rev-list "origin/${branch}..HEAD" 2>/dev/null || true)"
  old_range="$(git rev-list "origin/${branch}..${orig_head}" 2>/dev/null || true)"
  [ -n "$new_range" ] && [ -n "$old_range" ] || return 1

  local rewrote=1 new_sha subject matches old_sha f
  while IFS= read -r new_sha; do
    [ -n "$new_sha" ] || continue
    subject="$(git log -1 --format=%s "$new_sha" 2>/dev/null || true)"
    [ -n "$subject" ] || continue

    # Pre-rebase commit(s) with this exact subject. Ambiguity => skip, never guess.
    matches=""
    while IFS= read -r old_sha; do
      [ -n "$old_sha" ] || continue
      if [ "$(git log -1 --format=%s "$old_sha" 2>/dev/null)" = "$subject" ]; then
        matches="${matches}${old_sha}"$'\n'
      fi
    done <<<"$old_range"
    [ "$(printf '%s' "$matches" | grep -c .)" -eq 1 ] || continue
    old_sha="$(printf '%s' "$matches" | head -1)"
    [ "$old_sha" = "$new_sha" ] && continue # rebase was a no-op for this commit

    for f in "$@"; do
      [ -f "$f" ] || continue
      _rsc_rewrite_file "$f" "$repo_name" "$old_sha" "$new_sha" && rewrote=0
    done
  done <<<"$new_range"
  return "$rewrote"
}

# PASS 2 -- any repo, driven by reachability. Heals a citation whose commit survives nowhere.
_rsc_pass_orphan() {
  local ws f citations token repo sha rp ref subject cands n twin pid twin_pid narrowed
  ws="$(_rsc_workspace_root)"
  [ -d "$ws" ] || return 1

  # Cheap pre-filter: no `<repo>@<sha>`-shaped token anywhere => nothing to do, touch no repos.
  citations="$(grep -ohE '\b[a-z][a-z0-9-]{2,}@[0-9a-f]{7,40}\b' "$@" 2>/dev/null | sort -u || true)"
  [ -n "$citations" ] || return 1

  local rewrote=1
  while IFS= read -r token; do
    [ -n "$token" ] || continue
    repo="${token%@*}"
    sha="${token##*@}"
    rp="$ws/$repo"
    # Must be a real sibling clone. `.git` is a FILE in a linked worktree, hence -e not -d.
    [ -e "$rp/.git" ] || continue
    # A --depth=1 clone (CI's dep_repos fetch) can resolve only its own tip; every older, real
    # commit looks unreachable there. Treat it as "cannot judge", never as an orphan.
    [ "$(git -C "$rp" rev-parse --is-shallow-repository 2>/dev/null)" = "true" ] && continue
    [ "$(git -C "$rp" cat-file -t "$sha" 2>/dev/null)" = "commit" ] || continue

    ref="$(_rsc_integration_ref "$rp")" || continue

    # SURVIVAL TEST: is the cited commit reachable from ANY ref -- remote branch, local
    # branch, or tag?
    #
    # An earlier version of this asked only "is it an ancestor of origin/live-defi-rollout",
    # and that was WRONG in a way that only a cross-machine check exposed: it classified 513
    # of 3336 real citations as orphans, and spot-checking them against two other slots'
    # clones found 0/120 actually missing. They were alive on `main`, on promote-PR refs, on
    # tags -- everywhere except the one branch being asked about. Healing those would have
    # rewritten perfectly good citations onto a different (also real) SHA. "Survives
    # somewhere" is the honest question; "is on this branch" is a different one.
    [ -n "$(git -C "$rp" for-each-ref --contains "$sha" --count=1 --format='%(refname)' \
      refs/remotes refs/heads refs/tags 2>/dev/null)" ] && continue
    # Also alive: a commit made in THIS invocation's isolated worktree, whose HEAD is detached
    # and therefore named by no ref in the caller's clone. (In a sibling repo the sha simply
    # will not resolve here, so this is a no-op there.)
    git merge-base --is-ancestor "$sha" HEAD 2>/dev/null && continue

    # Orphan. Find its landed twin: subject narrows the search, PATCH-ID decides.
    #
    # Subject alone is NOT a safe key here, and the corpus proves it: 513 of 3336 real
    # citations in plans/active are orphans, and PM subjects repeat heavily ("docs(plans):
    # flip item 3 …"). A subject that happens to be unique within the search window while the
    # TRUE twin sits outside it would rewrite a citation to a genuinely unrelated commit --
    # worse than leaving it stale. Patch-id is invariant under rebase (that is what it is
    # for), so it identifies the twin regardless of how the base moved. Tree hash cannot do
    # this job: rebasing onto a moved base changes the tree, so the true twin's tree differs
    # from the orphan's.
    subject="$(git -C "$rp" log -1 --format=%s "$sha" 2>/dev/null || true)"
    [ -n "$subject" ] || continue
    cands="$(git -C "$rp" log -n 800 --format='%H%x09%s' "$ref" 2>/dev/null |
      awk -F'\t' -v s="$subject" '$2 == s {print $1}' || true)"
    n="$(printf '%s' "$cands" | grep -c . || true)"
    [ "$n" -ge 1 ] || continue

    pid="$(git -C "$rp" diff-tree -p --no-commit-id "$sha" 2>/dev/null | git patch-id --stable 2>/dev/null | cut -d' ' -f1)"
    if [ -z "$pid" ]; then
      # An empty or merge commit has no patch-id. Refuse rather than fall back to the weak key.
      echo "  ⚠ ${repo}@${sha:0:10} is orphaned but has no patch-id (empty/merge commit) — left as-is; verify by hand." >&2
      continue
    fi
    narrowed=""
    while IFS= read -r twin; do
      [ -n "$twin" ] || continue
      twin_pid="$(git -C "$rp" diff-tree -p --no-commit-id "$twin" 2>/dev/null | git patch-id --stable 2>/dev/null | cut -d' ' -f1)"
      [ "$twin_pid" = "$pid" ] && narrowed="${narrowed}${twin}"$'\n'
    done <<<"$cands"
    n="$(printf '%s' "$narrowed" | grep -c . || true)"
    if [ "$n" -ne 1 ]; then
      echo "  ⚠ ${repo}@${sha:0:10} is orphaned (rebased away) but its landed twin is not uniquely identifiable (${n} same-subject commits with a matching patch-id) — left as-is; verify by hand." >&2
      continue
    fi
    twin="$(printf '%s' "$narrowed" | head -1)"

    for f in "$@"; do
      [ -f "$f" ] || continue
      _rsc_rewrite_file "$f" "$repo" "$sha" "$twin" && rewrote=0
    done
  done <<<"$citations"
  return "$rewrote"
}

# Resolve `<repo>@PENDING` placeholders in the PM plan corpus to the sha this push just landed.
#
# WHY: the Commit+Push+Flip rule makes an agent write the plan checkbox while the work is fresh
# — before the sha exists. Today that costs a round trip per flip: write the todo, ship, read the
# landed sha, EDIT THE DOC AGAIN, ship the doc. Paid twice in one session on 2026-08-10. Worse,
# the natural shortcut is to write the sha you see at `git commit` time, which the rebase then
# invalidates — the exact defect the two passes above exist to clean up after.
#
# So: write `market-tick-data-service@PENDING` once, and the push that creates the commit fills
# it in. The placeholder is deliberately shaped like the citation it becomes, and a staged plan
# still carrying one is blocked at commit time by run_hygiene_sweep's --precommit guard, so an
# unresolved placeholder cannot reach the corpus.
#
# Scope is `plans/active` + `plans/epics` only: archive is the historical record, and a
# placeholder there would be somebody else's business.
resolve_pending_citations() {
  local repo="$1" sha="$2" pm_root="$3"
  [ "${SHA_CITATION_RECONCILE:-1}" = "0" ] && return 0
  [ -n "$repo" ] && [ -n "$sha" ] && [ -d "$pm_root" ] || return 0

  local hits f
  hits="$(grep -rl --include='*.md' -F "${repo}@PENDING" \
    "$pm_root/plans/active" "$pm_root/plans/epics" 2>/dev/null || true)"
  [ -n "$hits" ] || return 0

  while IFS= read -r f; do
    [ -f "$f" ] || continue
    python3 - "$f" "$repo" "${sha:0:10}" <<'PY'
import sys, pathlib
path, repo, sha = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
text = p.read_text()
token = f"{repo}@PENDING"
if token not in text:
    raise SystemExit(1)
p.write_text(text.replace(token, f"{repo}@{sha}"))
print(f"  ✓ {path}: {token} → {repo}@{sha}")
raise SystemExit(0)
PY
  done <<<"$hits"
  echo "  resolved @PENDING evidence placeholder(s) to the sha that actually landed"
  return 0
}

reconcile_sha_citations() {
  [ "${SHA_CITATION_RECONCILE:-1}" = "0" ] && return 0
  local branch="$1"; shift
  [ "$#" -gt 0 ] || return 0

  local rewrote=1
  _rsc_pass_orig_head "$branch" "$@" && rewrote=0
  _rsc_pass_orphan "$@" && rewrote=0

  if [ "$rewrote" = "0" ]; then
    echo "  reconciled rebase-invalidated evidence citation(s) before push — see"
    echo "  plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md"
    git add -- "$@" 2>/dev/null || true
    git commit -q --amend --no-edit --no-verify 2>/dev/null || true
  fi
  return 0
}
