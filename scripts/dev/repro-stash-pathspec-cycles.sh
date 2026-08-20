#!/usr/bin/env bash
set -euo pipefail

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: the stash pathspec recovery guidance and its repro gap are retired

ROOT="$(mktemp -d)"
printf 'repro artifacts: %s\n' "$ROOT"

git_configure() {
  git -C "$1" config user.name repro
  git -C "$1" config user.email repro@example.invalid
}

stash_count() {
  git -C "$1" stash list | wc -l | tr -d ' '
}

new_remote() {
  local name="$1"
  git init --bare -q "$ROOT/$name.git"
  git clone -q "$ROOT/$name.git" "$ROOT/$name"
  git_configure "$ROOT/$name"
  printf '%s\n' "$ROOT/$name.git"
}

printf '%s\n' '== hypothesis A: stale static pathspec across a conflict cycle =='
remote_a="$(new_remote a)"
git -C "$ROOT/a" checkout -q -b main
printf 'base-a\n' > "$ROOT/a/a.txt"
printf 'base-b\n' > "$ROOT/a/b.txt"
printf 'base-d\n' > "$ROOT/a/d.txt"
git -C "$ROOT/a" add a.txt b.txt d.txt
git -C "$ROOT/a" commit -q -m base
git -C "$ROOT/a" push -q -u origin main

printf 'local-a-cycle-1\n' > "$ROOT/a/a.txt"
printf 'local-b-cycle-1\n' > "$ROOT/a/b.txt"
static_pathspec=(a.txt b.txt)
before="$(stash_count "$ROOT/a")"
git -C "$ROOT/a" stash push -q -m cycle-1 -- "${static_pathspec[@]}"
after="$(stash_count "$ROOT/a")"
printf 'cycle 1 stash count: %s -> %s\n' "$before" "$after"

git clone -q "$remote_a" "$ROOT/peer-a"
git_configure "$ROOT/peer-a"
git -C "$ROOT/peer-a" checkout -q -b main origin/main
printf 'remote-a-cycle-1\n' > "$ROOT/peer-a/a.txt"
git -C "$ROOT/peer-a" add a.txt
git -C "$ROOT/peer-a" commit -q -m remote-cycle-1
git -C "$ROOT/peer-a" push -q origin main
git -C "$ROOT/a" pull -q --ff-only
if git -C "$ROOT/a" stash pop -q; then
  printf '%s\n' 'cycle 1 pop unexpectedly had no conflict'
else
  printf '%s\n' 'cycle 1 pop conflicted as intended; resolving a.txt'
  printf 'local-a-cycle-1\n' > "$ROOT/a/a.txt"
  git -C "$ROOT/a" add a.txt b.txt
  git -C "$ROOT/a" commit -q -m resolve-cycle-1
fi

# The original list is intentionally not re-derived. d.txt is now dirty but absent
# from that list, so the second push silently saves nothing.
printf 'local-d-cycle-2\n' > "$ROOT/a/d.txt"
before="$(stash_count "$ROOT/a")"
git -C "$ROOT/a" stash push -q -m cycle-2 -- "${static_pathspec[@]}"
after="$(stash_count "$ROOT/a")"
printf 'cycle 2 stale-list stash count: %s -> %s\n' "$before" "$after"
if [[ "$before" == "$after" && "$(<"$ROOT/a/d.txt")" == 'local-d-cycle-2' ]]; then
  printf '%s\n' 'RESULT A: reproduced stale-list omission (d.txt stayed dirty and was not stashed).'
else
  printf '%s\n' 'RESULT A: stale-list omission did not reproduce.'
  exit 1
fi

printf '%s\n' '== hypothesis B: empty pathspec followed by unconditional pop =='
new_remote b >/dev/null
git -C "$ROOT/b" checkout -q -b main
printf 'base-foreign\n' > "$ROOT/b/foreign.txt"
git -C "$ROOT/b" add foreign.txt
git -C "$ROOT/b" commit -q -m base
git -C "$ROOT/b" push -q -u origin main

printf 'unrelated-stash-content\n' > "$ROOT/b/foreign.txt"
git -C "$ROOT/b" stash push -q -m unrelated-stash
git -C "$ROOT/b" checkout -q -- foreign.txt
before="$(stash_count "$ROOT/b")"
empty_pathspec=()
# With an empty expansion after --, git accepts the command and reports success,
# but does not create a stash. The following pop is therefore unrelated.
git -C "$ROOT/b" stash push -q -m empty-pathspec -- "${empty_pathspec[@]}"
after="$(stash_count "$ROOT/b")"
printf 'empty-pathspec stash count: %s -> %s\n' "$before" "$after"
git -C "$ROOT/b" stash pop -q
if [[ "$before" == "$after" && "$(<"$ROOT/b/foreign.txt")" == 'unrelated-stash-content' ]]; then
  printf '%s\n' 'RESULT B: reproduced empty-pathspec no-op and unrelated stash pop.'
else
  printf '%s\n' 'RESULT B: empty-pathspec no-op/pop did not reproduce.'
  exit 1
fi

printf '%s\n' 'BOTH REPRODUCTIONS PASSED'
