#!/usr/bin/env bash
#
# audit-stash-pile.sh — per-host git stash pile audit + conservative cleanup.
#
# Stashes live in a host's shared common .git (one refs/stash per repo, visible to every
# slot worktree on that host) and are NEVER pushed, so they can only be cleaned host-locally.
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
#
#   (no flags)        Dry-run: archive + classify + write report, drop NOTHING. The default.
#   --apply           Drop the auto-drop classes (empty / redundant / foreign-park). Still archives first.
#   --repo <name>     Restrict to a single repo (smoke-test the classifier).
#   --base <ref>      Override the content-diff base ref for ALL repos.
#   --host <id>       Label used in archive/report filenames. Defaults to `hostname -s`.
#   --report <path>   Report output path. Defaults under unified-trading-pm/plans/active/issues/.
#
# Classification (strict / conservative):
#   empty         tracked diff empty AND no captured untracked files            -> auto-drop
#   redundant     every changed path is byte-identical in the base ref          -> auto-drop
#   foreign-park  redundant AND label matches foreign-*/autostash               -> auto-drop
#   genuine-WIP   anything else (incl. ANY captured untracked file, or          -> SURFACE to owner
#                 unverifiable base) -> never auto-dropped
#
set -euo pipefail

# ---------------------------------------------------------------------------- args
APPLY=0
ONLY_REPO=""
BASE_OVERRIDE=""
HOST="$(hostname -s 2>/dev/null || hostname)"
REPORT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)   APPLY=1; shift ;;
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
# A stable, sortable date label. Date.now() is fine in shell; the plan/report carry the human date.
DATE="$(date -u +%Y%m%d)"
ARCHIVE_ROOT="$WORKSPACE_ROOT/.stash-archive-${HOST}-${DATE}"
if [[ -z "$REPORT_PATH" ]]; then
  REPORT_DIR="$WORKSPACE_ROOT/unified-trading-pm/plans/active/issues/stash_audit_reports"
  REPORT_PATH="$REPORT_DIR/stash-audit-${HOST}-${DATE}.md"
fi
mkdir -p "$(dirname "$REPORT_PATH")"

MODE_LABEL="DRY-RUN (no drops)"; [[ "$APPLY" -eq 1 ]] && MODE_LABEL="APPLY (auto-drop enabled)"

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
    fi

    action="surface"
    case "$class" in
      empty|redundant|foreign-park) action="auto-drop"; DROP_INDICES+=("$idx"); r_drop=$((r_drop+1)) ;;
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

# prepend a workspace-wide summary table just after the report header
SUMMARY_TMP="$(mktemp)"
{
  echo "## Workspace summary"
  echo
  echo "| repo | stashes | auto-droppable | genuine-WIP | base-verified |"
  echo "| ---- | ------- | -------------- | ----------- | ------------- |"
  printf '%s\n' "${SUMMARY_ROWS[@]}"
  echo "| **TOTAL** | **$GRAND_TOTAL** | **$GRAND_DROP** | **$GRAND_WIP** | |"
  echo
} > "$SUMMARY_TMP"
# insert summary after the 7-line header block
head -n 7 "$REPORT_PATH" > "$REPORT_PATH.new"
cat "$SUMMARY_TMP" >> "$REPORT_PATH.new"
tail -n +8 "$REPORT_PATH" >> "$REPORT_PATH.new"
mv "$REPORT_PATH.new" "$REPORT_PATH"
rm -f "$SUMMARY_TMP"

echo
echo "==== ${MODE_LABEL} ===="
echo "repos with stashes : $(( ${#SUMMARY_ROWS[@]} ))"
echo "total stashes      : $GRAND_TOTAL"
echo "auto-droppable     : $GRAND_DROP"
echo "genuine-WIP        : $GRAND_WIP"
echo "report             : $REPORT_PATH"
echo "archive            : $ARCHIVE_ROOT"
[[ "$APPLY" -eq 0 ]] && echo "(dry-run — nothing dropped; re-run with --apply once the report looks right)"
