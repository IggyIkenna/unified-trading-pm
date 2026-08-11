#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: the prosewrap auto-repair is scoped to the violations THIS commit introduced.
#
# WHY THE SCOPE IS THE WHOLE POINT. fix_prosewrap_padding.py has existed since 2026-08-10 and
# agents still hand-repaired around it, because whole-file mode rewrites pre-existing corruption
# too — measured, 10 of 25 sampled active plans, one by 51 lines. Those rewrites are legitimate
# repairs (the corpus ratchet sits at BASELINE, not zero), but attaching them to every plan
# commit widens the merge-conflict surface on the busiest file class in the repo. So the test
# that matters is not "does it fix the bad line" — it is "does it leave the OTHER bad lines
# alone", because that property is what makes unattended auto-repair safe to wire in.
#
# The scripts are COPIED into a synthetic PM-shaped checkout rather than run in place: the check
# resolves its repo root as `$SCRIPT_DIR/../..` and reads the previous content via
# `git -C <that root> show HEAD:<path>`, so exercising the HEAD-vs-current comparison in place
# would mean committing a fixture to the live slot checkout. A test must never do that.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  WORK="${BATS_TEST_TMPDIR}"
  PM="${WORK}/unified-trading-pm"
  mkdir -p "${PM}/scripts/plan-hygiene" "${PM}/plans/active"
  cp "${REPO_ROOT}/scripts/plan-hygiene/check_prosewrap_padding.sh" "${PM}/scripts/plan-hygiene/"
  cp "${REPO_ROOT}/scripts/plan-hygiene/fix_prosewrap_padding.py" "${PM}/scripts/plan-hygiene/"
  cp "${REPO_ROOT}/scripts/plan-hygiene/prosewrap_padding_baseline.yaml" "${PM}/scripts/plan-hygiene/" 2>/dev/null || true
  CHECK="${PM}/scripts/plan-hygiene/check_prosewrap_padding.sh"
  FIX="${PM}/scripts/plan-hygiene/fix_prosewrap_padding.py"

  cd "$PM"
  git init -q .
  git config user.email "t@t"
  git config user.name "t"

  # Committed content carrying PRE-EXISTING corruption. It has to be at HEAD for the ratchet to
  # classify it as debt rather than as this commit's problem — that classification is the thing
  # under test.
  cat > plans/active/fixture.md <<'EOF'
# fixture

- [ ] 1. a todo
                      pre-existing over-indented continuation line that must survive untouched
EOF
  git add -A
  git commit -q -m "seed"
}

@test "scoped repair fixes the new violation and leaves pre-existing corruption untouched" {
  cd "$PM"
  cat > plans/active/fixture.md <<'EOF'
# fixture

- [ ] 1. a todo
                      pre-existing over-indented continuation line that must survive untouched
                      brand new over-indented line introduced by this commit
EOF

  run bash "$CHECK" --only plans/active/fixture.md
  [ "$status" -eq 1 ]

  run bash "$CHECK" --only --emit-lines plans/active/fixture.md
  [ "$status" -eq 0 ]
  # Exactly ONE line is in scope — the new one (line 5), not the pre-existing one (line 4).
  [ "${#lines[@]}" -eq 1 ]
  [[ "${lines[0]}" == *":5" ]]

  bash "$CHECK" --only --emit-lines plans/active/fixture.md | python3 "$FIX" --scoped

  # The new line was repaired...
  run bash "$CHECK" --only plans/active/fixture.md
  [ "$status" -eq 0 ]
  # ...and the pre-existing corrupted line is byte-identical to what was committed.
  run grep -c '^                      pre-existing over-indented continuation line' plans/active/fixture.md
  [ "$output" = "1" ]
}

@test "backtick-padding violations are scoped the same way" {
  cd "$PM"
  cat > plans/active/fixture.md <<'EOF'
# fixture

- [ ] 1. a todo
                      pre-existing over-indented continuation line that must survive untouched
- [ ] 2. new todo citing `market-tick-data-     service@92037f45`
EOF

  run bash "$CHECK" --only --emit-lines plans/active/fixture.md
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 1 ]
  [[ "${lines[0]}" == *":5" ]]

  bash "$CHECK" --only --emit-lines plans/active/fixture.md | python3 "$FIX" --scoped
  run bash "$CHECK" --only plans/active/fixture.md
  [ "$status" -eq 0 ]
  run grep -c 'market-tick-data- service@92037f45' plans/active/fixture.md
  [ "$output" = "1" ]
  run grep -c '^                      pre-existing over-indented continuation line' plans/active/fixture.md
  [ "$output" = "1" ]
}

@test "absolute paths round-trip check → fixer → git add (the shape run_hygiene_sweep uses)" {
  cd "$PM"
  # run_hygiene_sweep builds STAGED_PLANS as "$PM_DIR/$line" — absolute. If --emit-lines'
  # `<file>:<line>` output or the fixer's rpartition(':') mishandled that, the auto-repair would
  # silently no-op in the ONLY context it actually runs in.
  ABS="${PM}/plans/active/fixture.md"
  cat > "$ABS" <<'EOF'
# fixture

- [ ] 1. a todo
                      pre-existing over-indented continuation line that must survive untouched
                      brand new over-indented line introduced by this commit
EOF

  run bash "$CHECK" --only --emit-lines "$ABS"
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 1 ]
  [[ "${lines[0]}" == "${ABS}:5" ]]

  scope="$(bash "$CHECK" --only --emit-lines "$ABS")"
  printf '%s\n' "$scope" | python3 "$FIX" --scoped
  run bash "$CHECK" --only "$ABS"
  [ "$status" -eq 0 ]

  # The path the sweep feeds to `git add` must be a real, addable path.
  target="$(printf '%s\n' "$scope" | sed 's/:[0-9]*$//' | sort -u)"
  [ "$target" = "$ABS" ]
  run git -C "$PM" add -- "$target"
  [ "$status" -eq 0 ]
}

@test "whole-file mode still rewrites everything (corpus-remediation contract unchanged)" {
  cd "$PM"
  cat > plans/active/fixture.md <<'EOF'
# fixture

- [ ] 1. a todo
                      first over-indented line
                      second over-indented line
EOF

  run python3 "$FIX" plans/active/fixture.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"TOTAL lines changed: 2"* ]]
}

@test "--scoped with no input on stdin is a no-op, not an error" {
  run bash -c "printf '' | python3 '$FIX' --scoped"
  [ "$status" -eq 0 ]
}

@test "a failing sort (locale regression) hard-fails instead of silently false-flagging" {
  cd "$PM"
  # Simulate the 2026-08-09 "sort: Illegal byte sequence" crash (prosewrap_padding_precommit_
  # gate_locale_false_positive_2026_08_09.md) with a fake `sort` that always fails. A silent
  # regression would let --only continue with a truncated/empty comparison set and false-flag
  # byte-identical HEAD content as a NEW violation; the guard must instead abort with a loud
  # error and a non-zero exit.
  fakebin="${WORK}/fakebin"
  mkdir -p "$fakebin"
  cat > "$fakebin/sort" <<'EOF'
#!/usr/bin/env bash
echo "sort: string comparison failed: Illegal byte sequence" >&2
exit 1
EOF
  chmod +x "$fakebin/sort"

  cat > plans/active/fixture.md <<'EOF'
# fixture

- [ ] 1. a todo
                      brand new over-indented line introduced by this commit
EOF

  run env PATH="$fakebin:$PATH" bash "$CHECK" --only plans/active/fixture.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"sort -u"*"failed"* ]]
}
