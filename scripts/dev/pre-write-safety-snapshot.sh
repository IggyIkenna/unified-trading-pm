#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# pre-write-safety-snapshot.sh -- content-hashed, timestamped pre-write snapshots for
# agent-authored edits to large/contested files, stored OUTSIDE the shared working tree.
#
# WHY THIS EXISTS (2026-08-20/21, walkthrough_file_shared_checkout_repeated_content_loss):
# a single-file structure-pass agent lost committed AND uncommitted content on the same
# client-artefact file three times in one session -- once via an unrelated slot's blind
# whole-file revert, once via the working tree resetting mid-edit with zero corresponding
# commit history. Recovery both times depended on a scratchpad file that happened to exist
# by luck, not by design. This script gives that recovery path a designed home: snapshot a
# file's exact bytes (+ sha256 + timestamp) to a directory outside any repo's working tree
# BEFORE a contested edit session starts, so a repeat working-tree loss has something to
# restore from regardless of whether the editing agent's own commit/push ever landed.
#
# WHERE SNAPSHOTS LIVE: $UTS_SNAPSHOT_DIR (default: $HOME/.uts-pre-write-snapshots), keyed
# by repo name + the file's repo-relative path -- deliberately NOT inside any slot's
# .tabs/<N>/<repo> checkout (that IS the contended location this exists to protect against)
# and NOT a per-session scratchpad (those get cleaned up; this must outlive the session that
# wrote it so a LATER session/slot can recover from it too).
#
# USAGE:
#   pre-write-safety-snapshot.sh snapshot <file>
#       Snapshot <file>'s current on-disk bytes. Prints the snapshot path on success.
#   pre-write-safety-snapshot.sh list <file>
#       List snapshots taken for <file> (newest first): timestamp, short sha256, path.
#   pre-write-safety-snapshot.sh latest <file>
#       Print the path of the most recent snapshot for <file> (empty + exit 1 if none).
#   pre-write-safety-snapshot.sh restore <snapshot-path> [<target-file>]
#       Verify the snapshot's recorded sha256 still matches its on-disk bytes (corruption
#       check), then write those bytes to <target-file> (default:
#       <target-file-implied-by-meta>.restored-from-snapshot -- never overwrites the live
#       working-tree file directly; the caller reviews + moves it into place themselves).
#
# EXIT CODES: 0 success. 2 bad usage. 3 file not found / not inside a git repo.
# 4 snapshot not found. 5 snapshot corrupted (sha256 mismatch against its own sidecar meta).
set -euo pipefail

SNAPSHOT_ROOT="${UTS_SNAPSHOT_DIR:-$HOME/.uts-pre-write-snapshots}"

_die() {
  echo "pre-write-safety-snapshot.sh: $1" >&2
  exit "$2"
}

# Resolve (repo_name, repo_relative_path, snapshot_dir_for_this_file) for a given file path.
# Sets globals: _REPO_NAME, _REL_PATH, _SNAP_DIR
_resolve_target() {
  local file="$1"
  [ -n "$file" ] || _die "missing <file> argument" 2
  local abs_file
  abs_file="$(cd "$(dirname "$file")" 2>/dev/null && pwd)/$(basename "$file")" || _die "cannot resolve path: $file" 3
  local repo_root
  repo_root="$(cd "$(dirname "$abs_file")" && git rev-parse --show-toplevel 2>/dev/null)" || _die "not inside a git repo: $file" 3
  _REPO_NAME="$(basename "$repo_root")"
  _REL_PATH="${abs_file#"$repo_root"/}"
  # Encode the relative path into a flat directory-safe token (slashes -> __).
  local safe_rel="${_REL_PATH//\//__}"
  _SNAP_DIR="$SNAPSHOT_ROOT/$_REPO_NAME/$safe_rel"
}

cmd_snapshot() {
  local file="$1"
  [ -f "$file" ] || _die "file does not exist: $file" 3
  _resolve_target "$file"
  mkdir -p "$_SNAP_DIR"
  local ts sha
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  sha="$(sha256sum "$file" | awk '{print $1}')"
  local short="${sha:0:12}"
  local snap_path="$_SNAP_DIR/${ts}_${short}.snapshot"
  local meta_path="$_SNAP_DIR/${ts}_${short}.meta"
  cp -p -- "$file" "$snap_path"
  {
    echo "timestamp_utc=$ts"
    echo "sha256=$sha"
    echo "repo=$_REPO_NAME"
    echo "repo_relative_path=$_REL_PATH"
    echo "source_abs_path=$file"
  } >"$meta_path"
  echo "$snap_path"
}

cmd_list() {
  local file="$1"
  _resolve_target "$file"
  [ -d "$_SNAP_DIR" ] || { echo "no snapshots for $_REPO_NAME/$_REL_PATH"; return 0; }
  local f
  for f in $(find "$_SNAP_DIR" -maxdepth 1 -name '*.snapshot' | sort -r); do
    local base ts sha
    base="$(basename "$f" .snapshot)"
    ts="${base%%_*}"
    sha="${base#*_}"
    echo "$ts  $sha  $f"
  done
}

cmd_latest() {
  local file="$1"
  _resolve_target "$file"
  [ -d "$_SNAP_DIR" ] || _die "no snapshots for $_REPO_NAME/$_REL_PATH" 4
  local latest
  latest="$(find "$_SNAP_DIR" -maxdepth 1 -name '*.snapshot' | sort -r | head -n1)"
  [ -n "$latest" ] || _die "no snapshots for $_REPO_NAME/$_REL_PATH" 4
  echo "$latest"
}

cmd_restore() {
  local snap_path="$1"
  local target="${2:-}"
  [ -f "$snap_path" ] || _die "snapshot not found: $snap_path" 4
  local meta_path="${snap_path%.snapshot}.meta"
  [ -f "$meta_path" ] || _die "snapshot meta missing (cannot verify integrity): $meta_path" 4
  local recorded_sha actual_sha source_abs_path
  recorded_sha="$(grep '^sha256=' "$meta_path" | cut -d= -f2)"
  actual_sha="$(sha256sum "$snap_path" | awk '{print $1}')"
  [ "$recorded_sha" = "$actual_sha" ] || _die "snapshot CORRUPTED: recorded sha256=$recorded_sha, actual=$actual_sha" 5
  source_abs_path="$(grep '^source_abs_path=' "$meta_path" | cut -d= -f2-)"
  if [ -z "$target" ]; then
    target="${source_abs_path}.restored-from-snapshot"
  fi
  cp -p -- "$snap_path" "$target"
  echo "restored (sha256 verified: $actual_sha) -> $target"
}

main() {
  local sub="${1:-}"
  case "$sub" in
    snapshot) shift; cmd_snapshot "$@" ;;
    list) shift; cmd_list "$@" ;;
    latest) shift; cmd_latest "$@" ;;
    restore) shift; cmd_restore "$@" ;;
    *) _die "usage: $0 {snapshot|list|latest|restore} <args...>" 2 ;;
  esac
}

main "$@"
