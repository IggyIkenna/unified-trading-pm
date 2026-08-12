#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# audit-stash-pile.sh — per-host git stash pile audit + conservative cleanup.
#
# Stashes are NEVER pushed, so they can only be cleaned host-locally.
#
# CORRECTED 2026-08-11 (measured, not assumed): each slot is its OWN clone with its OWN .git
# and its OWN independent stash pile — `git rev-parse --git-common-dir` returns a plain `.git`
# in every `.tabs/<N>/<repo>`, NOT a shared path. The previous header here claimed stashes live
# in "a host's shared common .git (one refs/stash per repo, visible to every slot worktree on
# that host)". That is FALSE for this layout and actively misleading: it reads as "run the tool
# once and the host is clean". Measured 2026-08-11 the host carried 284 stashes across FOUR
# separate piles (slot 1: 47, slot 2: 34, slot 3: 118, slot 4: 85); cleaning slot 3 alone left
# 166 untouched in the other three. RUN THIS PER SLOT. The --host label is derived per slot
# automatically since 2026-08-12 (`Mac-slot3`), so archives and reports no longer collide;
# --host remains available to override it.
# SSOT for the per-slot-clone model: /codex/05-infrastructure/per-tab-worktrees.md.
# This script archives EVERYTHING first (gc-proof refs + portable bundle + manifest), then
# classifies each stash, and ONLY with --apply drops the provably-safe classes. Genuine WIP
# is always surfaced in a committed report for its owner to review — never auto-dropped, never
# auto-applied onto a working tree.
#
# Plan of record: unified-trading-pm/plans/active/stash_pile_workspace_cleanup_2026_06_03.md
# Pattern source: plans/active/issues/shared_stash_pile_archive_cleanup_2026_06_01.md
#
# Usage:
#   audit-stash-pile.sh [--apply] [--repo <name>] [--base <ref>] [--host <id>] [--report <path>]
#                       [--prune-age-days <N>]
#
#   (no flags)        Dry-run: archive + classify + write report, drop NOTHING. The default.
#   --apply           Drop the auto-drop classes (empty / redundant / foreign-park). Still archives first.
#   --repo <name>     Restrict to a single repo (smoke-test the classifier).
#   --base <ref>      Override the content-diff base ref for ALL repos.
#   --host <id>       Label used in archive/report filenames. Defaults to `<hostname -s>-slot<N>`
#                     when run inside a `.tabs/<N>/` slot clone (derivation SSOT:
#                     scripts/hooks/slot-identity-lib.sh), else bare `hostname -s`.
#   --report <path>   Report output path. Defaults under unified-trading-pm/plans/active/issues/.
#
# Classification (strict / conservative):
#   empty          tracked diff empty AND no captured untracked files           -> auto-drop
#   redundant      every changed path is byte-identical in the base ref         -> auto-drop
#   foreign-park   redundant AND label matches foreign-*/autostash              -> auto-drop
#   stale-autostash  `autostash`-labelled, older than --prune-age-days, NO      -> auto-drop
#                  captured untracked files, and NOT a safety-snapshot/quarantine
#                  label. The RETENTION class — the three above all require
#                  byte-identity with the base, so none of them can ever clean a
#                  REGROWN pile (measured 2026-08-11: 0 of 118 qualified).
#   genuine-WIP    anything else (incl. ANY captured untracked file, or         -> SURFACE to owner
#                  unverifiable base) -> never auto-dropped
#
set -euo pipefail

# ---------------------------------------------------------------------------- args
APPLY=0
# Retention cutoff for the `stale-autostash` class, in days. 0 disables the class entirely
# (restoring the pre-2026-08-12 identity-only behaviour).
#
# Default 2 (48h) per operator ruling 2026-08-12. It was briefly 14, chosen to match
# stash-pile-detect.sh's STASH_WARN_AGE_DAYS — but 14 cannot hold this pile: measured the same
# day, a 14d cutoff made 0 of 30 entries droppable while the pile still regrew past
# safe-doc-push's "extreme" quarantine threshold within ONE day and quarantined a live push.
# The binding constraint is the ship scripts' count threshold, not the detector's age warn, so
# the prune horizon is now set by how fast the pile regrows rather than by knob symmetry.
#
# Consequence, deliberate: with a 2d prune the detector's AGE warn (oldest_days > 14) can now
# essentially never fire, because nothing survives to 14 days. Its COUNT warn is what still
# carries the signal. If you ever raise this back up, re-check that pairing.
PRUNE_AGE_DAYS="${STASH_PRUNE_AGE_DAYS:-2}"
ONLY_REPO=""
BASE_OVERRIDE=""
# Empty = derive below, once WORKSPACE_ROOT is known. It used to default to a bare
# `hostname -s`, which is IDENTICAL for every slot on one machine — so slot 3's report
# and slot 4's report both wanted the name `stash-audit-Mac-<date>.md` and silently
# clobbered each other, while the committed reports (Mac-slot2, Mac-slot4) had been
# hand-renamed by whoever committed them. The header below used to warn "pass --host so
# each slot's report is distinguishable"; a flag you must remember or lose data is a
# defaulting bug wearing a documentation warning, so the default now derives the slot.
HOST=""
REPORT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)   APPLY=1; shift ;;
    --prune-age-days) PRUNE_AGE_DAYS="${2:?--prune-age-days needs a value}"; shift 2 ;;
    --repo)    ONLY_REPO="${2:?--repo needs a value}"; shift 2 ;;
    --base)    BASE_OVERRIDE="${2:?--base needs a value}"; shift 2 ;;
    --host)    HOST="${2:?--host needs a value}"; shift 2 ;;
    --report)  REPORT_PATH="${2:?--report needs a value}"; shift 2 ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# ---------------------------------------------------------------------------- paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/dev -> scripts -> unified-trading-pm -> workspace root
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
# Slot-aware host label. The machine part stays `hostname -s` (matches the committed
# `Mac-slot2` / `Mac-slot4` / `ip-172-31-5-118` reports); the slot suffix comes from the
# SSOT path derivation in scripts/hooks/slot-identity-lib.sh — the same `…/.tabs/<N>/<repo>`
# rule that stamps commit identity — rather than a second copy of that regex here.
# A checkout that is not a slot clone resolves to `main` and gets no suffix, which is the
# pre-existing behaviour for the AO VM (`ip-172-31-5-118-<date>`).
if [[ -z "$HOST" ]]; then
  HOST="$(hostname -s 2>/dev/null || hostname)"
  _SLOT_LIB="$SCRIPT_DIR/../hooks/slot-identity-lib.sh"
  if [[ -f "$_SLOT_LIB" ]]; then
    # shellcheck source=/dev/null
    . "$_SLOT_LIB"
    slot_identity_resolve "$WORKSPACE_ROOT/unified-trading-pm" 2>/dev/null || true
    [[ "${SLOT_ID_LABEL:-main}" != "main" ]] && HOST="${HOST}-${SLOT_ID_LABEL//-/}"
  else
    echo "WARNING: slot-identity-lib.sh not found at $_SLOT_LIB — report/archive will use the bare host label '$HOST', which COLLIDES across slots on one machine. Pass --host explicitly." >&2
  fi
fi
# A stable, sortable date label. Date.now() is fine in shell; the plan/report carry the human date.
DATE="$(date -u +%Y%m%d)"
ARCHIVE_ROOT="$WORKSPACE_ROOT/.stash-archive-${HOST}-${DATE}"
if [[ -z "$REPORT_PATH" ]]; then
  REPORT_DIR="$WORKSPACE_ROOT/unified-trading-pm/plans/active/issues/stash_audit_reports"
  REPORT_PATH="$REPORT_DIR/stash-audit-${HOST}-${DATE}.md"
fi
mkdir -p "$(dirname "$REPORT_PATH")"

MODE_LABEL="DRY-RUN (no drops)"; [[ "$APPLY" -eq 1 ]] && MODE_LABEL="APPLY (auto-drop enabled)"
SUMMARY_MARKER="<!-- workspace-summary -->"
case "$PRUNE_AGE_DAYS" in ''|*[!0-9]*) echo "ERROR: --prune-age-days must be a non-negative integer (got '$PRUNE_AGE_DAYS')" >&2; exit 2 ;; esac
PRUNE_CUTOFF=$(( $(date +%s) - PRUNE_AGE_DAYS * 86400 ))
if [[ "$PRUNE_AGE_DAYS" -gt 0 ]]; then
  echo ">> retention: autostash entries older than ${PRUNE_AGE_DAYS}d are auto-droppable (safety-snapshot/quarantine labels + any captured untracked files are always exempt)"
else
  echo ">> retention: DISABLED (--prune-age-days 0) — identity-based classes only"
fi

# ---------------------------------------------------------------------------- helpers
# Base ref per repo: agent-orchestrator tracks main, every other repo tracks live-defi-rollout.
resolve_base() {
  local repo="$1"
  if [[ -n "$BASE_OVERRIDE" ]]; then echo "$BASE_OVERRIDE"; return; fi
  if [[ "$repo" == "agent-orchestrator" ]]; then echo "origin/main"; else echo "origin/live-defi-rollout"; fi
}

git_in() { git -C "$REPO_PATH" "$@"; }

# ---------------------------------------------------------------------------- report header
{
  echo "# Stash audit — host \`${HOST}\` — ${DATE}"
  echo
  echo "- Mode: **${MODE_LABEL}**"
  echo "- Workspace: \`${WORKSPACE_ROOT}\`"
  echo "- Archive root: \`${ARCHIVE_ROOT}\` (+ \`refs/stash-archive/*\` inside each repo's .git)"
  echo "- Classifier: strict / conservative (see plan stash_pile_workspace_cleanup_2026_06_03.md)"
  echo
  # Marker replaced by the workspace summary table at the end of the run, once the
  # per-repo counts exist. Anchored on this line rather than a fixed line offset:
  # the previous `head -n 7` / `tail -n +8` splice silently broke the moment the
  # header changed length, which is exactly what adding frontmatter above does.
  echo "$SUMMARY_MARKER"
} > "$REPORT_PATH"

GRAND_TOTAL=0; GRAND_DROP=0; GRAND_WIP=0
SUMMARY_ROWS=()

# ---------------------------------------------------------------------------- repo loop
for repo_dir in "$WORKSPACE_ROOT"/*/; do
  REPO_NAME="$(basename "$repo_dir")"
  REPO_PATH="${repo_dir%/}"
  [[ -e "$REPO_PATH/.git" ]] || continue
  [[ -n "$ONLY_REPO" && "$REPO_NAME" != "$ONLY_REPO" ]] && continue

  # any stashes?
  if ! git_in rev-parse --verify --quiet refs/stash >/dev/null; then continue; fi
  STASH_COUNT="$(git_in stash list | wc -l | tr -d ' ')"
  [[ "$STASH_COUNT" -eq 0 ]] && continue

  BASE="$(resolve_base "$REPO_NAME")"
  git_in fetch --quiet origin 2>/dev/null || true
  BASE_VERIFIED=1
  if ! git_in rev-parse --verify --quiet "$BASE" >/dev/null; then
    BASE_VERIFIED=0   # cannot prove redundancy -> nothing in this repo will be auto-dropped
  fi

  echo ">> $REPO_NAME : $STASH_COUNT stash(es), base=$BASE verified=$BASE_VERIFIED"

  # ----- archive EVERYTHING first (both dry-run and apply) ---------------------------
  REPO_ARCHIVE="$ARCHIVE_ROOT/$REPO_NAME"
  mkdir -p "$REPO_ARCHIVE"
  : > "$REPO_ARCHIVE/manifest.txt"
  mapfile -t STASH_LINES < <(git_in stash list --format='%gd|%H|%gs')
  idx=0
  declare -a ARCHIVE_REFS=()
  for line in "${STASH_LINES[@]}"; do
    sha="$(cut -d'|' -f2 <<<"$line")"
    label="$(cut -d'|' -f3- <<<"$line")"
    ref="refs/stash-archive/$(printf '%04d' "$idx")"
    git_in update-ref "$ref" "$sha"
    ARCHIVE_REFS+=("$ref")
    printf '%s\t%s\t%s\n' "$idx" "$sha" "$label" >> "$REPO_ARCHIVE/manifest.txt"
    idx=$((idx+1))
  done
  # portable bundle of the archive refs (+ base anchor when available)
  bundle_refs=("${ARCHIVE_REFS[@]}")
  [[ "$BASE_VERIFIED" -eq 1 ]] && bundle_refs+=("$BASE")
  git_in bundle create "$REPO_ARCHIVE/$REPO_NAME.bundle" "${bundle_refs[@]}" >/dev/null 2>&1 || \
    echo "   ! bundle failed for $REPO_NAME (refs still gc-proof in refs/stash-archive/*)"

  # ----- classify -------------------------------------------------------------------
  declare -a DROP_INDICES=()
  REPORT_ROWS=()
  r_total=0; r_drop=0; r_wip=0
  idx=0
  for line in "${STASH_LINES[@]}"; do
    sel="$(cut -d'|' -f1 <<<"$line")"          # stash@{N}
    sha="$(cut -d'|' -f2 <<<"$line")"
    label="$(cut -d'|' -f3- <<<"$line")"
    r_total=$((r_total+1))

    # provenance only (attribution, never the safety decision)
    branch="$(sed -E 's/^(WIP on|On) ([^:]+):.*/\2/' <<<"$label")"
    age="$(git_in log -1 --format='%cr' "$sha" 2>/dev/null || echo '?')"
    # Absolute commit epoch for the age-based retention class below. Empty (never prunable) if
    # the stash commit can't be read — same fail-safe posture as BASE_VERIFIED.
    sha_epoch="$(git_in log -1 --format='%ct' "$sha" 2>/dev/null || echo '')"

    # tracked changed paths = diff between stash parent^1 (anchor) and stash tip
    mapfile -t tracked < <(git_in diff --name-only "${sha}^1" "$sha" 2>/dev/null || true)
    # captured untracked files live on the 3rd parent, if present
    has_untracked=0
    if git_in rev-parse --verify --quiet "${sha}^3" >/dev/null; then
      mapfile -t untracked < <(git_in ls-tree -r --name-only "${sha}^3" 2>/dev/null || true)
      [[ "${#untracked[@]}" -gt 0 ]] && has_untracked=1
    else
      untracked=()
    fi
    file_count=$(( ${#tracked[@]} + ${#untracked[@]} ))
    py_count=$(printf '%s\n' "${tracked[@]}" "${untracked[@]}" | grep -c '\.py$' || true)

    # ----- classification (strict / conservative order) -----
    class="genuine-WIP"
    if [[ "${#tracked[@]}" -eq 0 && "$has_untracked" -eq 0 ]]; then
      class="empty"
    elif [[ "$has_untracked" -eq 1 ]]; then
      class="genuine-WIP"                       # never auto-drop captured untracked files
    elif [[ "$BASE_VERIFIED" -eq 1 ]] && git_in diff --quiet "$BASE" "$sha" -- "${tracked[@]}" 2>/dev/null; then
      if printf '%s' "$label" | grep -qiE 'foreign|autostash'; then class="foreign-park"; else class="redundant"; fi
    elif [[ "$PRUNE_AGE_DAYS" -gt 0 && -n "$sha_epoch" && "$sha_epoch" -lt "$PRUNE_CUTOFF" ]] \
         && printf '%s' "$label" | grep -qiE 'autostash' \
         && ! printf '%s' "$label" | grep -qiE 'safety-snapshot|quarantine'; then
      # RETENTION class, per /plans/active/issues/unified_trading_pm_stash_pile_accumulation_2026_07_26.md.
      # The three classes
      # above all require byte-identity with the base ref, which is why they can never clean a
      # REGROWN pile: measured 2026-08-11, 0 of 118 stashes across 12 repos qualified, because
      # after days of drift nothing is still identical to today's base. The pile therefore grew
      # 0 -> 284 in the 12 days since the previous manual sweep, and crossed quickmerge's
      # "extreme pile" threshold, which quarantined a working tree mid-ship.
      #
      # An `autostash` entry is a MACHINE artifact: `git pull --rebase --autostash` parks the
      # dirty tree and re-applies it seconds later, so a surviving entry is by definition one
      # whose re-apply already happened (or whose session is long gone). Past a multi-day
      # cutoff it is abandoned by construction, whether or not its content still matches base.
      # That is what makes age a sound criterion here where content-identity is not.
      #
      # Deliberately NOT covered, and both guards are load-bearing:
      #   - captured untracked files -> caught by the `has_untracked` branch ABOVE this one, so
      #     an autostash carrying untracked work can never reach this class regardless of age.
      #   - `safety-snapshot` / `quarantine` labels -> a human-or-ship-script-authored park of a
      #     genuine dirty tree (quickmerge writes these before a risky reconcile). Never aged out.
      class="stale-autostash"
    fi

    action="surface"
    case "$class" in
      empty|redundant|foreign-park|stale-autostash) action="auto-drop"; DROP_INDICES+=("$idx"); r_drop=$((r_drop+1)) ;;
      *) r_wip=$((r_wip+1)) ;;
    esac

    REPORT_ROWS+=("| $sel | \`${sha:0:9}\` | $class | $action | \`$branch\` | $age | $file_count | $py_count |")
    idx=$((idx+1))
  done

  # ----- act (apply only) -----------------------------------------------------------
  dropped=0
  if [[ "$APPLY" -eq 1 && "${#DROP_INDICES[@]}" -gt 0 ]]; then
    # descending so earlier drops don't renumber the indices we still need
    mapfile -t SORTED_DROP < <(printf '%s\n' "${DROP_INDICES[@]}" | sort -rn)
    for di in "${SORTED_DROP[@]}"; do
      git_in stash drop "stash@{$di}" >/dev/null && dropped=$((dropped+1))
    done
  fi

  # ----- per-repo report section ----------------------------------------------------
  {
    echo "## $REPO_NAME"
    echo
    echo "- stashes: **$r_total** · auto-droppable: **$r_drop** · genuine-WIP survivors: **$r_wip**"
    echo "- base ref: \`$BASE\` · base-verified: $([[ $BASE_VERIFIED -eq 1 ]] && echo yes || echo '**NO — nothing auto-dropped**')"
    [[ "$APPLY" -eq 1 ]] && echo "- dropped this run: **$dropped** (archived in \`$REPO_ARCHIVE\`)"
    echo
    echo "| stash | sha | class | action | owner-branch | age | files | .py |"
    echo "| ----- | --- | ----- | ------ | ------------ | --- | ----- | --- |"
    printf '%s\n' "${REPORT_ROWS[@]}"
    echo
  } >> "$REPORT_PATH"

  SUMMARY_ROWS+=("| $REPO_NAME | $r_total | $r_drop | $r_wip | $([[ $BASE_VERIFIED -eq 1 ]] && echo yes || echo NO) |")
  GRAND_TOTAL=$((GRAND_TOTAL+r_total)); GRAND_DROP=$((GRAND_DROP+r_drop)); GRAND_WIP=$((GRAND_WIP+r_wip))
  unset DROP_INDICES
done

# ---------------------------------------------------------------------------- archive README + summary
mkdir -p "$ARCHIVE_ROOT"
cat > "$ARCHIVE_ROOT/README.md" <<EOF
# Stash archive — host ${HOST} — ${DATE}

Every stash present at audit time was archived three ways BEFORE any drop:

1. **gc-proof refs** — \`refs/stash-archive/NNNN\` inside each repo's own .git (local, gc-immune).
2. **portable bundle** — \`<repo>/<repo>.bundle\` here (clone-able even if .git is lost).
3. **manifest** — \`<repo>/manifest.txt\` (index → sha → label).

## Restore one stash
\`\`\`
cd <repo>
git stash apply <sha>          # sha from manifest.txt; or: git stash store -m "restored" <sha>
\`\`\`
## Restore from the bundle (if .git refs are gone)
\`\`\`
git -C <repo> fetch ${ARCHIVE_ROOT}/<repo>/<repo>.bundle 'refs/stash-archive/*:refs/stash-archive/*'
\`\`\`

Do NOT purge this directory or the refs/stash-archive/* refs until the confirmation window
in plans/active/stash_pile_workspace_cleanup_2026_06_03.md (Phase 4) has closed.
EOF

# substitute the workspace-wide summary table in place of its marker
SUMMARY_TMP="$(mktemp)"
{
  echo "## Workspace summary"
  echo
  echo "| repo | stashes | auto-droppable | genuine-WIP | base-verified |"
  echo "| ---- | ------- | -------------- | ----------- | ------------- |"
  [[ ${#SUMMARY_ROWS[@]} -gt 0 ]] && printf '%s\n' "${SUMMARY_ROWS[@]}"
  echo "| **TOTAL** | **$GRAND_TOTAL** | **$GRAND_DROP** | **$GRAND_WIP** | |"
  echo
} > "$SUMMARY_TMP"

# Frontmatter. The report lands in plans/active/issues/stash_audit_reports/, and every
# report anyone actually committed there carries frontmatter that was added BY HAND —
# the script never emitted any.
#
# Measured 2026-08-12, because the obvious assumption is wrong: a frontmatter-less doc
# on that surface does NOT fail plan hygiene. check_frontmatter_schema.py skips it
# entirely — stripping the frontmatter from a report moved the corpus from 1995 docs to
# 1994 and still printed "zero violations". So the cost is not a red gate, it is
# INVISIBILITY: the L0→L4 doc-retrieval model finds docs by grepping L1 frontmatter
# facets (`rg -l '^doc_type: issue'`), so a report without frontmatter is unfindable by
# every documented retrieval path. In that directory 3 of 6 reports were invisible.
# That is also why the two unfrontmattered ones were simply never committed.
#
# Emitted HERE, at the end, rather than in the header block, because `summary:` quotes
# the real counts and those do not exist until the walk is done.
FRONTMATTER_TMP="$(mktemp)"
_HUMAN_DATE="$(date -u +%Y-%m-%d)"
_APPLY_WORD="dry-run"; [[ "$APPLY" -eq 1 ]] && _APPLY_WORD="apply-mode"
{
  echo "---"
  echo "doc_type: issue"
  echo "title: \"Stash audit — host ${HOST} — ${_HUMAN_DATE}\""
  echo "summary: >-"
  echo "  Auto-generated ${_APPLY_WORD} stash-audit output (${GRAND_TOTAL} stashes across ${#SUMMARY_ROWS[@]} repos,"
  echo "  ${GRAND_WIP} genuine-WIP, ${GRAND_DROP} auto-droppable). Machine-written by scripts/dev/audit-stash-pile.sh;"
  echo "  diagnostic input for the standing stash_pile_workspace_cleanup_2026_06_03.md effort."
  echo "status: open"
  echo "nature: notes"
  echo "asset_group: [cross-cutting]"
  echo "stage: [meta]"
  echo "repos: []"
  echo "scope: [admin]"
  echo "tags: [stash-audit, workspace-hygiene, generated-report]"
  echo "related: [stash_pile_workspace_cleanup_2026_06_03]"
  echo "created: ${_HUMAN_DATE}"
  echo "author: claude-agent"
  echo "source: \"Auto-generated ${_APPLY_WORD} stash audit, ${_HUMAN_DATE}, host ${HOST}\""
  echo "priority: P3"
  echo "parent_epic: infrastructure_master"
  echo "assigned_vm: NA"
  echo "execution_scope: local-only"
  echo "drift_direction: advance-code"
  echo "depends_on: []"
  echo "locked_by:"
  echo "resolved_by:"
  echo "---"
  echo
} > "$FRONTMATTER_TMP"

if ! grep -qF "$SUMMARY_MARKER" "$REPORT_PATH"; then
  echo "ERROR: summary marker '$SUMMARY_MARKER' not found in $REPORT_PATH — the report would ship with no workspace summary." >&2
  rm -f "$SUMMARY_TMP" "$FRONTMATTER_TMP"
  exit 1
fi
cat "$FRONTMATTER_TMP" > "$REPORT_PATH.new"
awk -v marker="$SUMMARY_MARKER" -v sf="$SUMMARY_TMP" '
  $0 == marker { while ((getline line < sf) > 0) print line; close(sf); next }
  { print }
' "$REPORT_PATH" >> "$REPORT_PATH.new"
mv "$REPORT_PATH.new" "$REPORT_PATH"
rm -f "$SUMMARY_TMP" "$FRONTMATTER_TMP"

echo
echo "==== ${MODE_LABEL} ===="
echo "repos with stashes : $(( ${#SUMMARY_ROWS[@]} ))"
echo "total stashes      : $GRAND_TOTAL"
echo "auto-droppable     : $GRAND_DROP"
echo "genuine-WIP        : $GRAND_WIP"
echo "report             : $REPORT_PATH"
echo "archive            : $ARCHIVE_ROOT"
[[ "$APPLY" -eq 0 ]] && echo "(dry-run — nothing dropped; re-run with --apply once the report looks right)"
