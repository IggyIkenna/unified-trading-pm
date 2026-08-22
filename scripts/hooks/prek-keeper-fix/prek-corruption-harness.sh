#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: prek ships the keeper rollback-baseline fix upstream AND every host runs
#              a version >= that release (then this becomes the proof we can stop patching)
#
# Reproduction + verification oracle for the prek stash/restore corruption.
# SSOT: /plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md
#
# WHY THIS EXISTS
# ---------------
# prek stashes unstaged changes to a patch file before running hooks, then re-applies it
# afterwards. When that re-apply conflicts, it rolls back with `git checkout -- <root>` —
# which restores from the CURRENT index. Our prettier-autostage.sh calls `git add` DURING
# the hook run, so by rollback time the index already holds the hook's content. prek then
# makes that the baseline and applies a patch computed against the ORIGINAL content on top
# of it. Result: unstaged work silently lost or duplicated, and `git status` comes back
# CLEAN afterwards — so nothing downstream notices. This corrupted real plan docs on
# origin/live-defi-rollout more than once before it was understood.
#
# This harness is the ORACLE: run it against any prek build and it answers, in ~10s,
# "is this build safe for our hook chain?" — instead of reading upstream changelogs and
# hoping (which we did, and got wrong twice).
#
#   bash prek-corruption-harness.sh                     # test whatever `prek` is on PATH
#   PATH=/path/to/build:$PATH bash prek-corruption-harness.sh   # test a specific build
#
# Each scenario builds a throwaway repo and drives a REAL `git commit` (not `prek run` —
# the installed-hook path is what production uses), then checks worktree + index content.
#
# TRAPS HIT WHILE WRITING THIS (do not re-learn the hard way)
# ----------------------------------------------------------
# 1. `local d; d="$(newrepo)"` silently does nothing useful — command substitution runs in
#    a SUBSHELL, so the `cd` never reaches the caller and every scenario ran outside a git
#    repo, reporting a cheerful false CLEAN. newrepo() must set a global and cd directly.
# 2. Testing via `prek run` instead of `git commit` under-reports: the keeper engages on
#    the real hook path. Always drive a genuine commit.
# 3. An UNRELATED dirty file is NOT enough to trigger it (see S1 — clean). The corrupting
#    shape needs the SAME file to be both staged and dirty while a hook rewrites+stages it.
# 4. Checking file content alone is insufficient — assert the INDEX too (`git show :path`).
#    S4 empties the index entry while the worktree can still look plausible.
# 5. Upstream's `--no-stash` / `PREK_NO_STASH` opt-out does NOT exist in any release; that
#    PR (j178/prek#2130) was closed unmerged. Don't plan around it.
#
# Expected on a SAFE build: clean=5 corrupt=0.
# Expected on stock prek <= 0.4.11: S3 and S4 CORRUPT.
#
# Usage: bash prek-corruption-harness.sh [scenario...]   (default: all)

set -uo pipefail

PASS=0
FAIL=0

# ── helpers ──────────────────────────────────────────────────────────────────
# Sets REPO and cd's into it. Must NOT be called via $(...) — that would cd in a subshell.
newrepo() {
  REPO="$(mktemp -d)"
  cd "$REPO" || exit 1
  git init -q
  git config user.email t@t.com
  git config user.name t
  git config commit.gpgsign false
  git symbolic-ref HEAD refs/heads/main
}

# A hook that mimics prettier-autostage: rewrites matching files, re-stages ONLY
# those already in the index. $STAGE_MODE controls whether it calls `git add`.
write_autostage_hook() {
  local stage_mode="$1"   # "stage" | "nostage"
  cat > fixer.sh <<EOF
#!/usr/bin/env bash
set -euo pipefail
STAGED_BEFORE="\$(git diff --cached --name-only)"
for f in "\$@"; do
  case "\$f" in *.md) ;; *) continue ;; esac
  # "reformat": normalise the marker line (deterministic rewrite, like prettier)
  sed -i 's/^marker:.*/marker: NORMALISED/' "\$f"
done
if [ "$stage_mode" = "stage" ]; then
  for f in "\$@"; do
    echo "\$STAGED_BEFORE" | grep -Fxq -- "\$f" || continue
    git diff --name-only -- "\$f" | grep -Fxq -- "\$f" || continue
    git add -- "\$f"
  done
fi
exit 0
EOF
  chmod +x fixer.sh
  cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: local
    hooks:
      - id: fixer
        name: fixer
        language: system
        entry: bash fixer.sh
        types_or: [markdown]
EOF
}

report() {
  local name="$1" ok="$2" detail="$3"
  if [ "$ok" = "ok" ]; then
    PASS=$((PASS + 1)); printf '  \033[32mCLEAN\033[0m   %s\n' "$name"
  else
    FAIL=$((FAIL + 1)); printf '  \033[31mCORRUPT\033[0m %s\n    -> %s\n' "$name" "$detail"
  fi
}

# ── S1: hook rewrites+STAGES a staged file; unrelated file dirty ─────────────
# This is our exact production shape (prettier-autostage + a foreign dirty file).
scenario_S1() {
  newrepo
  write_autostage_hook stage

  printf 'marker: ORIGINAL\nbody line\n' > doc.md
  printf 'other original\n' > other.txt
  git add doc.md other.txt .pre-commit-config.yaml fixer.sh
  git commit -qm init
  prek install -q >/dev/null 2>&1

  # stage a real edit to doc.md (this is the file the hook will rewrite+restage)
  printf 'marker: ORIGINAL\nbody line\nmy staged edit\n' > doc.md
  git add doc.md
  # unstaged change to an UNRELATED file -> engages prek's keeper
  printf 'other MODIFIED unstaged\n' > other.txt

  git commit -qm "s1" >/dev/null 2>&1

  local bad=""
  # the unstaged edit to other.txt must survive untouched
  [ "$(cat other.txt)" = "other MODIFIED unstaged" ] || bad="other.txt unstaged content lost/garbled: '$(cat other.txt)'"
  # doc.md must retain my staged edit line
  grep -q 'my staged edit' doc.md || bad="${bad:+$bad; }doc.md lost the staged edit"
  [ -s doc.md ] || bad="${bad:+$bad; }doc.md EMPTIED"

  report "S1 hook rewrites+STAGES staged file, unrelated file dirty" \
    "$([ -z "$bad" ] && echo ok || echo bad)" "$bad"
}

# ── S2: identical, but the hook does NOT git add ─────────────────────────────
scenario_S2() {
  newrepo
  write_autostage_hook nostage

  printf 'marker: ORIGINAL\nbody line\n' > doc.md
  printf 'other original\n' > other.txt
  git add doc.md other.txt .pre-commit-config.yaml fixer.sh
  git commit -qm init
  prek install -q >/dev/null 2>&1

  printf 'marker: ORIGINAL\nbody line\nmy staged edit\n' > doc.md
  git add doc.md
  printf 'other MODIFIED unstaged\n' > other.txt

  git commit -qm "s2" >/dev/null 2>&1

  local bad=""
  [ "$(cat other.txt)" = "other MODIFIED unstaged" ] || bad="other.txt unstaged content lost/garbled: '$(cat other.txt)'"
  grep -q 'my staged edit' doc.md || bad="${bad:+$bad; }doc.md lost the staged edit"
  [ -s doc.md ] || bad="${bad:+$bad; }doc.md EMPTIED"

  report "S2 hook rewrites but does NOT stage, unrelated file dirty" \
    "$([ -z "$bad" ] && echo ok || echo bad)" "$bad"
}

# ── S3: hook rewrites+stages a file that ALSO has unstaged changes ───────────
# Same file is both staged and dirty -> patch conflict lands on the hook's file.
scenario_S3() {
  newrepo
  write_autostage_hook stage

  printf 'marker: ORIGINAL\nbody line\n' > doc.md
  git add doc.md .pre-commit-config.yaml fixer.sh
  git commit -qm init
  prek install -q >/dev/null 2>&1

  printf 'marker: ORIGINAL\nbody line\nstaged edit\n' > doc.md
  git add doc.md
  # now ALSO dirty the same file (unstaged delta on a staged file)
  printf 'marker: ORIGINAL\nbody line\nstaged edit\nUNSTAGED TAIL\n' > doc.md

  git commit -qm "s3" >/dev/null 2>&1

  local bad=""
  [ -s doc.md ] || bad="doc.md EMPTIED"
  grep -q 'UNSTAGED TAIL' doc.md || bad="${bad:+$bad; }lost the unstaged tail"
  grep -q 'staged edit' doc.md || bad="${bad:+$bad; }lost the staged edit"
  # duplicated-line runaway (our production signature)
  [ "$(grep -c 'staged edit' doc.md)" -le 1 ] || bad="${bad:+$bad; }DUPLICATED content (runaway): $(grep -c 'staged edit' doc.md)x"

  report "S3 hook rewrites+STAGES a file that also has unstaged changes" \
    "$([ -z "$bad" ] && echo ok || echo bad)" "$bad"
}

scenario_S3nostage() {
  newrepo
  write_autostage_hook nostage

  printf 'marker: ORIGINAL\nbody line\n' > doc.md
  git add doc.md .pre-commit-config.yaml fixer.sh
  git commit -qm init
  prek install -q >/dev/null 2>&1

  printf 'marker: ORIGINAL\nbody line\nstaged edit\n' > doc.md
  git add doc.md
  # now ALSO dirty the same file (unstaged delta on a staged file)
  printf 'marker: ORIGINAL\nbody line\nstaged edit\nUNSTAGED TAIL\n' > doc.md

  git commit -qm "s3" >/dev/null 2>&1

  local bad=""
  [ -s doc.md ] || bad="doc.md EMPTIED"
  grep -q 'UNSTAGED TAIL' doc.md || bad="${bad:+$bad; }lost the unstaged tail"
  grep -q 'staged edit' doc.md || bad="${bad:+$bad; }lost the staged edit"
  # duplicated-line runaway (our production signature)
  [ "$(grep -c 'staged edit' doc.md)" -le 1 ] || bad="${bad:+$bad; }DUPLICATED content (runaway): $(grep -c 'staged edit' doc.md)x"

  report "S3nostage hook rewrites but does NOT stage, file also has unstaged changes" \
    "$([ -z "$bad" ] && echo ok || echo bad)" "$bad"
}

# ── S4: index desync (upstream #1889's own test shape) ────────────────────────
scenario_S4() {
  newrepo
  cat > corrupt.py <<'PYEOF'
import pathlib, subprocess
empty = subprocess.check_output(["git","hash-object","-w","--stdin"], input=b"").decode().strip()
subprocess.check_call(["git","update-index","--cacheinfo","100644",empty,"new-file.txt"])
pathlib.Path("new-file.txt").write_text("hook content\n")
PYEOF
  cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: local
    hooks:
      - id: corrupt-index
        name: corrupt-index
        language: system
        entry: python3 corrupt.py
        pass_filenames: false
        always_run: true
EOF
  echo initial > README.md
  git add .
  git commit -qm init
  prek install -q >/dev/null 2>&1

  echo "staged content" > new-file.txt
  git add new-file.txt
  echo "unstaged content" > new-file.txt

  git commit -qm "s4" >/dev/null 2>&1

  local bad=""
  [ -s new-file.txt ] || bad="worktree new-file.txt EMPTIED"
  [ -n "$(git show :new-file.txt 2>/dev/null)" ] || bad="${bad:+$bad; }INDEX entry EMPTIED"

  report "S4 hook desyncs the index (upstream #1889 shape)" \
    "$([ -z "$bad" ] && echo ok || echo bad)" "$bad"
}

echo "prek version: $(prek --version)"
echo "scenarios:"
for s in "${@:-S1 S2 S3 S4}"; do :; done
if [ "$#" -eq 0 ]; then set -- S1 S2 S3 S3nostage S4; fi
for s in "$@"; do "scenario_$s"; done
echo ""
echo "clean=$PASS corrupt=$FAIL"
