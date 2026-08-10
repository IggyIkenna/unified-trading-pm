#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Find plan/issue docs with 0 open todos and >0 done todos, still sitting in plans/active/ or
# plans/active/issues/ instead of plans/archive/ (a done doc whose status/archival was simply
# never flipped — the recurring gap CLAUDE.md's archival rule calls out: "A plan with every todo
# done + unlocked MUST be archived immediately (HARD RULE, recurring gap)"). This is DISTINCT from
# check_terminal_status_archived.py, which only catches a doc whose status ALREADY says
# resolved/complete but never got physically moved — this check catches the doc BEFORE that,
# where status was never flipped away from open/active at all.
#
# Was purely informational (`|| true` in run_hygiene_sweep.sh), never scanned plans/active/
# issues/ at all, AND used `grep -P` (Perl regex) — which silently fails with "invalid option"
# on plain BSD grep (macOS default /usr/bin/grep) outside an interactive shell that happens to
# alias grep to a PCRE-capable tool. That meant every non-interactive invocation (CI, prek,
# run_hygiene_sweep.sh's own subprocess, plain `bash check_archive_candidates.sh`) silently saw
# EVERY file's counts default to empty/0 via the `|| true` fallback, regardless of the real
# corpus — i.e. this check has likely NEVER actually found a real candidate outside an
# interactive session with a PCRE-aliased grep, since it was first written. THREE real gaps,
# all found + fixed 2026-07-29 (see
# plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md's Progress Log for the
# investigation): (1) advisory-only, (2) missing plans/active/issues/, (3) non-portable `-P`.
# Now uses portable POSIX ERE (`grep -E` + `[[:space:]]`, works on both BSD and GNU grep) and is
# a SHRINKING ratchet, same shape as check_terminal_status_archived.py / check_line_caps.sh /
# check_na_corpus_ratchet.py: pre-existing candidates are tolerated so this can be a real hard
# gate without blocking the shared pipeline over debt nobody introduced today. A live count
# EXCEEDING the baseline means a NEW done-but-unarchived doc landed — fix it (run the canonical
# archival ritual: flip status to a terminal value, add the archive banner, git mv to
# plans/archive/[issues/], fix every corpus referrer), never raise the number.
#
# locked_by docs are excluded from the count (they cannot be archived without [unlock-plan]
# regardless of todo state, so flagging them would be a false positive the operator can't act on).
#
# Docs gating a `depends_on` + `gate_on_depends: true` finalize plan are ALSO excluded (found
# 2026-07-29, plan_health escalation triage): the `<X>_finalize_<date>.md` companion pattern
# (cefi/ao/prediction/tradfi/sports satellite_ao_dispatch batches, bucket-fold plans, etc. all use
# it) makes archiving the base plan ITS OWN gated todo — the finalize plan reconciles source docs
# + re-checks deferred items FIRST, then archives the base plan as its last step. A base plan with
# 0 open todos of its own but a still-active finalize companion isn't forgotten, it's mid-chain;
# flagging it is the same false-positive shape as an un-actionable locked_by doc.
#
# `archive_exempt: true` (frontmatter, found 2026-08-02, plan_health escalation agt-80ebc8)
# excludes a doc whose 0-open-todos state is INTENTIONAL and durable, not a forgotten completion —
# two real shapes surfaced during that triage: (a) a standing coordination/reference hub doc that
# deliberately carries 0 native todos by design (e.g. a `gate_on_depends: false` parent hub, or a
# `data-pipeline-check-*` milestones gate meant to stay a live reference surface forever), and (b) a
# doc explicitly routed for archival THROUGH another plan's own dispatched reconciliation todo
# (e.g. a `[REVIEW]` todo on a finalize plan that re-verifies + archives it as part of a larger
# sequenced pass) rather than standalone right now. Both are judgment calls a human/agent already
# made and documented (cite the reasoning in the doc's own Progress Log) — re-litigating them at
# every hygiene-sweep run is wasted motion, and archiving them anyway would be a bare force-resolve.
# This is NOT a way to silence a doc that's simply inconvenient to archive today; every use requires
# a Progress Log entry naming why. Same shape as `locked_by`/`gate_on_depends` above — a real
# escape hatch for a real false-positive class, not a floor-lowering shortcut.
#
# ── Diff-scoped mode (`--diff-base <ref>`, operator ruling 2026-08-06) ──
# The promote path (LDR→main) runs this check inside quality-gates-v2 on every promote PR. A
# corpus-wide ratchet attributes every other slot's accumulated doc debt to whoever happens to be
# promoting — the promoter's PR touches zero plan docs and still fails. Diff-scoped mode fixes the
# shape: compare the candidate set at HEAD vs the candidate set at <ref> (e.g. origin/main), and
# fail only when the PR's OWN diff ADDS a candidate that wasn't already at <ref>. Pre-existing
# candidates at <ref> are tolerated. The daily cron sweep + the remediation todos in
# /plans/active/issues/archive_candidates_content_verification_backlog_2026_08_06.md own clearing
# the backlog — the promote path just stops attributing it to the wrong person.
#
# Usage: bash scripts/plan-hygiene/check_archive_candidates.sh [--quiet] [--update-baseline] [--diff-base <ref>]
# Exit 0 = candidate count <= baseline (or, in diff-scoped mode, no NEW candidates vs base).
# Exit 1 = count exceeds baseline (a NEW candidate appeared), or new candidates vs base.
# --update-baseline: after archiving flagged docs, persist the new (lower) count. Refuses to raise
# the baseline — if the live count is higher than what's on disk, the run still fails.
#   Incompatible with --diff-base (diff-scoped mode doesn't use the baseline file).
# --diff-base <ref>: diff-scoped mode — compare the candidate set at HEAD vs the candidate set at
#   <ref> (e.g. origin/main). Only candidates that appear at HEAD but NOT at <ref> are flagged as
#   NEW; pre-existing candidates at <ref> are tolerated.
# --only <paths>: precommit-scoped mode (2026-08-09) — check ONLY the given staged files, no
#   baseline/diff-base involved. This check previously had NO precommit-time presence at all (only
#   --ci mode's --diff-base and the full corpus-wide baseline mode), so a docs(plans) commit via
#   safe-doc-push.sh (the fast path -> run_hygiene_sweep.sh --precommit, never the full gate) could
#   flip a doc's last open todo to done and leave it unarchived with zero enforcement — invisible
#   until a later full quality-gates.sh run or the LDR-red Tier-A synthetic re-scan (which uses
#   baseline mode, not diff-scoped) caught the accumulated corpus debt. Root-caused 2026-08-09 after
#   the corpus-wide count reached 9 (baseline 0) entirely via commits that never ran this check.
#   Same reasoning as check_terminal_status_archived.py --only: a file YOU are actively staging
#   that's 0-open/some-done/unlocked/not-exempt is unconditionally wrong regardless of the rest of
#   the corpus's backlog — no baseline needed for a single-file check.
#
#   `archive_exempt: true` is the SANCTIONED BRIDGE for the flip-then-mv two-commit archival
#   pattern this mode otherwise deadlocks against (found 2026-08-09,
#   check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md). A doc whose own
#   LAST open todo is its own archival trigger has no legal single commit: combining the checkbox
#   flip with the `git mv` archival in ONE commit makes the diff at the original plan_ref path show
#   only a file deletion, which defeats the AO server's cross-repo `/done` M3 checkbox-flip
#   verification (plan-completion-and-archival-discipline.md's own HARD RULE) — but flipping ALONE,
#   unexempted, trips THIS check. Resolution: set `archive_exempt: true` in the SAME commit as the
#   checkbox flip (this mode already treats it as a skip, see the `archive_exempt` grep below — no
#   separate code path needed), then `git mv` the file to `plans/archive/[issues/]` in the
#   IMMEDIATELY FOLLOWING commit, dropping the now-moot `archive_exempt: true` line as part of that
#   same move (an archived doc is no longer in this check's scanned population at all, so the field
#   has nothing left to bridge once the mv lands). If the follow-up mv is ever forgotten, the doc is
#   still caught — just not at commit time: the corpus-wide baseline / `--diff-base` modes (run in
#   the full `quality-gates.sh`, the daily hygiene cron, and the LDR→main promote gate) re-scan and
#   flag it as a NEW candidate above baseline the next time either runs. See
#   `tests/test_check_archive_candidates_flip_then_mv.bats` for the regression coverage.

set -uo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────
QUIET=""
UPDATE_BASELINE=""
DIFF_BASE=""
ONLY_PATHS=()
ONLY_MODE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --quiet) QUIET="1"; shift ;;
    --update-baseline) UPDATE_BASELINE="1"; shift ;;
    --diff-base)
      DIFF_BASE="$2"
      shift 2
      ;;
    --only)
      ONLY_MODE="1"
      shift
      while [ $# -gt 0 ]; do
        ONLY_PATHS+=("$1")
        shift
      done
      ;;
    *)
      # Unknown flag — swallow (back-compat with run_check's appended --quiet)
      shift
      ;;
  esac
done

# ── Paths ─────────────────────────────────────────────────────────────────────
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BASELINE_PATH="$(dirname "$0")/archive_candidates_baseline.yaml"

# ── Helper: build the set of candidate slugs at a given git tree ref ──────────
# Usage: _candidate_slugs_at <tree-ish> → prints one slug per line to stdout
# A tree-ish of "" (empty string) means "the current worktree (HEAD)".
_candidate_slugs_at() {
  local ref="$1"
  local gated_slugs=" "

  # ---- Phase 1: build gated_slugs for this ref ----
  if [ -z "$ref" ]; then
    # HEAD / worktree — scan disk
    for g in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
      [ -f "$g" ] || continue
      grep -qE '^gate_on_depends:[[:space:]]*true' "$g" 2>/dev/null || continue
      local deps_line
      deps_line="$(grep -E '^depends_on:' "$g" 2>/dev/null | head -1)"
      [ -z "$deps_line" ] && continue
      for slug in $(echo "$deps_line" | grep -oE '[A-Za-z0-9_-]+'); do
        [ "$slug" = "depends_on" ] && continue
        gated_slugs="${gated_slugs}${slug} "
      done
    done
  else
    # Remote ref — use git ls-tree + git show
    local ref_plans
    ref_plans="$(git -C "$PM_DIR" ls-tree --name-only "$ref" -- plans/active/ plans/active/issues/ 2>/dev/null || true)"
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      [[ "$rel" == *.md ]] || continue
      local name; name="$(basename "$rel")"
      [ "$name" = "INDEX.md" ] && continue
      [ "$name" = "task_template.md" ] && continue
      case "$name" in *.HANDOVER.md|_*) continue ;; esac

      local content
      content="$(git -C "$PM_DIR" show "$ref:$rel" 2>/dev/null || true)"
      [ -z "$content" ] && continue

      if echo "$content" | grep -qE '^gate_on_depends:[[:space:]]*true'; then
        local deps_line
        deps_line="$(echo "$content" | grep -E '^depends_on:' | head -1)"
        [ -z "$deps_line" ] && continue
        for slug in $(echo "$deps_line" | grep -oE '[A-Za-z0-9_-]+'); do
          [ "$slug" = "depends_on" ] && continue
          gated_slugs="${gated_slugs}${slug} "
        done
      fi
    done <<< "$ref_plans"
  fi

  # ---- Phase 2: identify candidates ----
  if [ -z "$ref" ]; then
    # HEAD / worktree — scan disk
    for f in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
      [ -f "$f" ] || continue
      local name; name="$(basename "$f")"
      [ "$name" = "INDEX.md" ] && continue
      [ "$name" = "task_template.md" ] && continue
      case "$name" in *.HANDOVER.md|_*) continue ;; esac

      local locked_by
      locked_by="$(grep -E '^locked_by:' "$f" 2>/dev/null | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
      [ -n "$locked_by" ] && continue

      grep -qE '^archive_exempt:[[:space:]]*true' "$f" 2>/dev/null && continue

      local slug="${name%.md}"
      case "$gated_slugs" in
        *" ${slug} "*) continue ;;
      esac

      local total_count done_count open_count
      total_count="$(grep -cE '^[[:space:]]*- \[.\]' "$f" 2>/dev/null || true)"
      total_count="${total_count:-0}"
      done_count="$(grep -cE '^[[:space:]]*- \[x\]' "$f" 2>/dev/null || true)"
      done_count="${done_count:-0}"
      open_count=$(( total_count - done_count ))

      if [ "$open_count" -eq 0 ] && [ "$done_count" -gt 0 ]; then
        echo "$slug"
      fi
    done
  else
    # Remote ref — use git ls-tree + git show
    local ref_plans
    ref_plans="$(git -C "$PM_DIR" ls-tree --name-only "$ref" -- plans/active/ plans/active/issues/ 2>/dev/null || true)"
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      [[ "$rel" == *.md ]] || continue
      local name; name="$(basename "$rel")"
      [ "$name" = "INDEX.md" ] && continue
      [ "$name" = "task_template.md" ] && continue
      case "$name" in *.HANDOVER.md|_*) continue ;; esac

      local content
      content="$(git -C "$PM_DIR" show "$ref:$rel" 2>/dev/null || true)"
      [ -z "$content" ] && continue

      local locked_by
      locked_by="$(echo "$content" | grep -E '^locked_by:' | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
      [ -n "$locked_by" ] && continue

      echo "$content" | grep -qE '^archive_exempt:[[:space:]]*true' && continue

      local slug="${name%.md}"
      case "$gated_slugs" in
        *" ${slug} "*) continue ;;
      esac

      local total_count done_count open_count
      total_count="$(echo "$content" | grep -cE '^[[:space:]]*- \[.\]' 2>/dev/null || true)"
      total_count="${total_count:-0}"
      done_count="$(echo "$content" | grep -cE '^[[:space:]]*- \[x\]' 2>/dev/null || true)"
      done_count="${done_count:-0}"
      open_count=$(( total_count - done_count ))

      if [ "$open_count" -eq 0 ] && [ "$done_count" -gt 0 ]; then
        echo "$slug"
      fi
    done <<< "$ref_plans"
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
CANDIDATES=0
FOUND=()
OK=1

if [ -n "$ONLY_MODE" ]; then
  # ── Precommit-scoped mode: check exactly the given staged files, no baseline/diff-base ──
  for f in "${ONLY_PATHS[@]}"; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    [ "$name" = "INDEX.md" ] && continue
    [ "$name" = "task_template.md" ] && continue
    case "$name" in
      *.HANDOVER.md) continue ;;
      _*) continue ;;
    esac
    # Scope to plans/active/ + plans/active/issues/ only — a staged file elsewhere
    # (e.g. codex/, plans/archive/) is out of this check's population.
    case "$f" in
      */plans/active/*.md|plans/active/*.md) ;;
      *) continue ;;
    esac

    locked_by="$(grep -E '^locked_by:' "$f" 2>/dev/null | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
    [ -n "$locked_by" ] && continue

    grep -qE '^archive_exempt:[[:space:]]*true' "$f" 2>/dev/null && continue

    slug="${name%.md}"
    # gate_on_depends exclusion: scan the whole active corpus for a finalize plan gating this slug
    # (the same check the full modes run — cheap enough to redo per --only invocation, which is
    # only ever a handful of staged files).
    is_gated=""
    for g in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
      [ -f "$g" ] || continue
      grep -qE '^gate_on_depends:[[:space:]]*true' "$g" 2>/dev/null || continue
      deps_line="$(grep -E '^depends_on:' "$g" 2>/dev/null | head -1)"
      [ -z "$deps_line" ] && continue
      case " $(echo "$deps_line" | grep -oE '[A-Za-z0-9_-]+' | tr '\n' ' ')" in
        *" ${slug} "*) is_gated="1"; break ;;
      esac
    done
    [ -n "$is_gated" ] && continue

    total_count="$(grep -cE '^[[:space:]]*- \[.\]' "$f" 2>/dev/null)"
    total_count="${total_count:-0}"
    done_count="$(grep -cE '^[[:space:]]*- \[x\]' "$f" 2>/dev/null)"
    done_count="${done_count:-0}"
    open_count=$(( total_count - done_count ))

    if [ "$open_count" -eq 0 ] && [ "$done_count" -gt 0 ]; then
      status="$(grep '^status:' "$f" 2>/dev/null | head -1 | sed 's/status: //')"
      status="${status:-unknown}"
      FOUND+=("${f}  done=${done_count}  status=${status}")
      CANDIDATES=$(( CANDIDATES + 1 ))
    fi
  done

  if [ -z "$QUIET" ]; then
    for line in "${FOUND[@]}"; do
      echo "  DONE-BUT-UNARCHIVED  $line"
    done
  fi

  if [ "$CANDIDATES" -eq 0 ]; then
    echo "✅ check_archive_candidates (--only): 0 candidate(s) in staged files"
    exit 0
  else
    echo "❌ check_archive_candidates (--only): ${CANDIDATES} candidate(s) in staged files — archive them: flip status to a terminal value, add the archive banner, git mv to plans/archive/[issues/], fix corpus referrers."
    exit 1
  fi
fi

if [ -n "$DIFF_BASE" ]; then
  # ── Diff-scoped mode ──────────────────────────────────────────────────────
  # Verify the base ref is reachable; degrade gracefully if not.
  if ! git -C "$PM_DIR" rev-parse --verify "$DIFF_BASE" >/dev/null 2>&1; then
    [ -z "$QUIET" ] && echo "⚠️  check_archive_candidates: --diff-base ref '$DIFF_BASE' not reachable — falling back to baseline mode"
    DIFF_BASE=""
  fi
fi

if [ -n "$DIFF_BASE" ]; then
  # Diff-scoped: build candidate sets at base and HEAD, report only NEW ones.
  BASE_CANDIDATES_FILE="$(mktemp)"
  trap 'rm -f "$BASE_CANDIDATES_FILE"' EXIT
  _candidate_slugs_at "$DIFF_BASE" > "$BASE_CANDIDATES_FILE"

  # Build HEAD candidates the same way, checking against the base set.
  HEAD_SLUGS="$(_candidate_slugs_at "")"

  while IFS= read -r slug; do
    [ -z "$slug" ] && continue
    if ! grep -qFx "$slug" "$BASE_CANDIDATES_FILE" 2>/dev/null; then
      # This candidate is at HEAD but NOT at base → NEW
      # Find the file path for reporting
      for d in "plans/active" "plans/active/issues"; do
        if [ -f "$PM_DIR/$d/${slug}.md" ]; then
          # Top-level script scope here (not inside a function) — `local` is invalid
          # (SC2168, pre-existing, found while shellcheck-verifying an unrelated change
          # to this file 2026-08-09).
          status="$(grep '^status:' "$PM_DIR/$d/${slug}.md" 2>/dev/null | head -1 | sed 's/status: //')"
          status="${status:-unknown}"
          FOUND+=("$d/${slug}.md  status=${status}")
          CANDIDATES=$(( CANDIDATES + 1 ))
          break
        fi
      done
    fi
  done <<< "$HEAD_SLUGS"

  if [ -z "$QUIET" ]; then
    echo "Archive candidates NEW since $DIFF_BASE (diff-scoped — pre-existing at base tolerated):"
    echo ""
    if [ "${#FOUND[@]}" -gt 0 ]; then
      for line in "${FOUND[@]}"; do
        echo "  $line"
      done
    else
      echo "  (none)"
    fi
    echo ""
  fi

  OK=1
  [ "$CANDIDATES" -gt 0 ] && OK=0

  if [ -z "$QUIET" ]; then
    if [ "$OK" -eq 1 ]; then
      echo "✅ check_archive_candidates: 0 new candidates vs $DIFF_BASE (diff-scoped — pre-existing debt in corpus tolerated)"
    else
      echo "❌ check_archive_candidates: ${CANDIDATES} NEW candidate(s) vs $DIFF_BASE — this PR's diff adds one or more done-but-unarchived docs. Archive them: flip status to a terminal value, add the archive banner, git mv to plans/archive/[issues/], fix corpus referrers."
    fi
  fi

  # --update-baseline is a no-op in diff-scoped mode
  if [ -n "$UPDATE_BASELINE" ]; then
    [ -z "$QUIET" ] && echo "⚠️  --update-baseline ignored in --diff-base mode (diff-scoped checks don't use the baseline file)"
  fi

else
  # ── Baseline (corpus-wide ratchet) mode — existing behaviour ─────────────
  BASELINE_COUNT="$(grep -E '^candidate_count:' "$BASELINE_PATH" 2>/dev/null | sed -E 's/^candidate_count:[[:space:]]*//')"
  BASELINE_COUNT="${BASELINE_COUNT:-0}"

  # Build gated_slugs from HEAD (worktree)
  GATED_SLUGS=" "
  for g in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
    [ -f "$g" ] || continue
    grep -qE '^gate_on_depends:[[:space:]]*true' "$g" 2>/dev/null || continue
    deps_line="$(grep -E '^depends_on:' "$g" 2>/dev/null | head -1)"
    [ -z "$deps_line" ] && continue
    for slug in $(echo "$deps_line" | grep -oE '[A-Za-z0-9_-]+'); do
      [ "$slug" = "depends_on" ] && continue
      GATED_SLUGS="${GATED_SLUGS}${slug} "
    done
  done

  for f in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    [ "$name" = "INDEX.md" ] && continue
    [ "$name" = "task_template.md" ] && continue
    case "$name" in
      *.HANDOVER.md) continue ;;
      _*) continue ;;
    esac

    locked_by="$(grep -E '^locked_by:' "$f" 2>/dev/null | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
    [ -n "$locked_by" ] && continue

    grep -qE '^archive_exempt:[[:space:]]*true' "$f" 2>/dev/null && continue

    slug="${name%.md}"
    case "$GATED_SLUGS" in
      *" ${slug} "*) continue ;;
    esac

    total_count="$(grep -cE '^[[:space:]]*- \[.\]' "$f" 2>/dev/null)"
    total_count="${total_count:-0}"
    done_count="$(grep -cE '^[[:space:]]*- \[x\]' "$f" 2>/dev/null)"
    done_count="${done_count:-0}"
    open_count=$(( total_count - done_count ))

    if [ "$open_count" -eq 0 ] && [ "$done_count" -gt 0 ]; then
      status="$(grep '^status:' "$f" 2>/dev/null | head -1 | sed 's/status: //')"
      status="${status:-unknown}"
      FOUND+=("${f#"$PM_DIR"/}  done=${done_count}  status=${status}")
      CANDIDATES=$(( CANDIDATES + 1 ))
    fi
  done

  if [ -z "$QUIET" ]; then
    echo "Archive candidates (0 open todos, all work done, unlocked):"
    echo ""
    if [ "${#FOUND[@]}" -gt 0 ]; then
      for line in "${FOUND[@]}"; do
        echo "  $line"
      done
    fi
    echo ""
  fi

  OK=1
  [ "$CANDIDATES" -gt "$BASELINE_COUNT" ] && OK=0

  if [ -z "$QUIET" ]; then
    if [ "$OK" -eq 1 ]; then
      echo "✅ check_archive_candidates: ${CANDIDATES} candidate(s) (baseline ${BASELINE_COUNT})"
    else
      echo "❌ check_archive_candidates: ${CANDIDATES} candidate(s) (baseline ${BASELINE_COUNT}) — a NEW done-but-unarchived doc landed. Archive it: flip status to a terminal value, add the archive banner, git mv to plans/archive/[issues/], fix corpus referrers. Never raise the baseline."
    fi
  fi

  if [ -n "$UPDATE_BASELINE" ]; then
    NEW_COUNT="$CANDIDATES"
    if [ "$BASELINE_COUNT" -gt 0 ] && [ "$NEW_COUNT" -gt "$BASELINE_COUNT" ]; then
      NEW_COUNT="$BASELINE_COUNT"
    fi
    cat > "$BASELINE_PATH" <<EOF
# Baseline for check_archive_candidates.sh — no plan/issue doc with 0 open todos and >0 done
# todos (and not locked_by someone) may sit in plans/active/ or plans/active/issues/ indefinitely
# without being archived (operator finding 2026-07-29 — see
# plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md's Progress Log for the
# investigation: three real gaps — advisory-only (\`|| true\`), never scanned
# plans/active/issues/, and non-portable \`grep -P\` that silently failed outside an interactive
# PCRE-aliased shell).
#
# This is a SHRINKING ratchet (same shape as terminal_status_archived_baseline.yaml /
# line_caps_baseline.yaml / na_corpus_baseline.yaml). candidate_count is the number of
# pre-existing done-but-unarchived docs the gate tolerates. A live count EXCEEDING this fails the
# check — a NEW one landed without being archived, fix it (archive it), don't raise the number.
# LOWER it (re-run --update-baseline) as candidates get archived. NEVER hand-raise it.
candidate_count: ${NEW_COUNT}
EOF
    [ -z "$QUIET" ] && echo "Baseline updated: ${NEW_COUNT}"
  fi
fi

exit $(( 1 - OK ))
