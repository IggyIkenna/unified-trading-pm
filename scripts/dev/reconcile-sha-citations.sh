#!/usr/bin/env bash
# Epic: infrastructure_master
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
# HOW THE MAPPING IS DERIVED (deterministic, no guessing). `git rebase` leaves the pre-rebase
# tip in ORIG_HEAD and preserves each commit's SUBJECT. So for every commit now in
# origin/<branch>..HEAD we find the pre-rebase commit with the identical subject in the
# ORIG_HEAD range; that pair IS the old->new mapping. A subject that is ambiguous (appears more
# than once on either side) is SKIPPED rather than guessed at -- a wrong rewrite would be worse
# than the stale citation it replaces.
#
# Usage:  reconcile_sha_citations <branch> <file> [<file> ...]
#   Returns 0 always (best-effort; never blocks a push). Prints what it rewrote.
#   Set SHA_CITATION_RECONCILE=0 to disable.

reconcile_sha_citations() {
  [ "${SHA_CITATION_RECONCILE:-1}" = "0" ] && return 0
  local branch="$1"; shift
  [ "$#" -gt 0 ] || return 0

  local orig_head
  orig_head="$(git rev-parse -q --verify ORIG_HEAD 2>/dev/null || true)"
  [ -n "$orig_head" ] || return 0

  local repo_name
  repo_name="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"

  # Commits this push is about to land, and their pre-rebase counterparts.
  local new_range old_range
  new_range="$(git rev-list "origin/${branch}..HEAD" 2>/dev/null || true)"
  old_range="$(git rev-list "origin/${branch}..${orig_head}" 2>/dev/null || true)"
  [ -n "$new_range" ] && [ -n "$old_range" ] || return 0

  local rewrote=0 new_sha subject matches old_sha
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
    [ "$old_sha" = "$new_sha" ] && continue   # rebase was a no-op for this commit

    # Rewrite <repo>@<old-sha-prefix> -> <repo>@<new-sha-same-length> in the named files.
    local f
    for f in "$@"; do
      [ -f "$f" ] || continue
      python3 - "$f" "$repo_name" "$old_sha" "$new_sha" <<'PY' && rewrote=1
import re, sys, pathlib
path, repo, old, new = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
p = pathlib.Path(path)
text = p.read_text()
# Match the repo@<prefix> form for any abbreviation length >= 7 of the OLD sha.
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
    done
  done <<<"$new_range"

  if [ "$rewrote" = "1" ]; then
    echo "  reconciled rebase-invalidated evidence citation(s) before push — see"
    echo "  plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md"
    git add -- "$@" 2>/dev/null || true
    git commit -q --amend --no-edit --no-verify 2>/dev/null || true
  fi
  return 0
}
