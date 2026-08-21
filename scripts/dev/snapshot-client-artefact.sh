#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# snapshot-client-artefact.sh -- pre-write safety snapshot for agent-authored edits to
# large, contested files (client-facing artefacts under codex/14-customer-journeys/, or
# any other large shared-checkout file a structure-pass agent is about to rewrite).
#
# WHY THIS EXISTS (2026-08-20/21,
# plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md):
# a single-file structure-pass agent lost committed AND uncommitted content on the same
# file three times in one session. Two of the three losses were a working-tree reset with
# NO corresponding git operation the editing session itself performed (a concurrent slot's
# blind "claim-ownership baseline restore", and a separate loss where the agent's own edits
# never survived to a commit at all). Recovery both times depended on a scratchpad backup
# that happened to exist -- luck, not design. This script makes that recovery path
# designed: snapshot the file's content (content-hashed, timestamped) to a location
# OUTSIDE the shared git working tree before an edit session starts, so a repeat
# working-tree loss always has a known-good, integrity-verified copy to restore from.
#
# STORAGE: $HOME/.cache/agent-artefact-snapshots/ by default -- deliberately NOT inside
# any repo clone (see per-tab-worktrees.md "What worktree isolation does NOT cover": a
# git reset/checkout/blind revert on the working tree cannot touch this path). Shared
# host-wide across every slot, same convention as PREK_CACHE_DIR / QM_ISO_VENV_CACHE, so
# a snapshot taken by one slot is recoverable from any other slot on the same host.
# Override with $SNAPSHOT_HOME (tests use this to stay hermetic).
#
# IDENTITY: snapshots are keyed by "<repo-name>/<repo-relative-path>", not by absolute
# path -- every slot's checkout has the same repo-relative structure (Path-B reference
# clones), so a snapshot taken in one slot's checkout is findable and restorable from any
# other slot's checkout of the same repo.
#
# USAGE:
#   snapshot-client-artefact.sh snapshot <file>
#   snapshot-client-artefact.sh list <file>
#   snapshot-client-artefact.sh restore <file> --to <dest> [--id <snapshot-id>]
#
# EXIT CODES: 0 success. 2 bad usage. 3 target file not found / not inside a git repo.
# 4 no snapshot found for this identity (or this --id). 5 integrity check failed -- the
# stored content's hash no longer matches its recorded hash, or a copy step didn't land
# byte-identical. Never restores unverified content; fails loudly instead.

set -euo pipefail

SNAPSHOT_HOME="${SNAPSHOT_HOME:-$HOME/.cache/agent-artefact-snapshots}"
MANIFEST="$SNAPSHOT_HOME/manifest.jsonl"

_log() { printf '[snapshot-client-artefact] %s\n' "$*" >&2; }
_err() { printf '[snapshot-client-artefact] ERROR: %s\n' "$*" >&2; }

# Portable sha256: `shasum` is the convention already used in this repo
# (scripts/dev/slot-cron-ff-pull.sh) for macOS-laptop portability; fall back to
# sha256sum for hosts without shasum.
_hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}

_hash_string() {
  if command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 256 | cut -d' ' -f1
  else
    printf '%s' "$1" | sha256sum | cut -d' ' -f1
  fi
}

_abs_path() {
  local f="$1"
  [ -f "$f" ] || { _err "not a file: $f"; exit 3; }
  printf '%s/%s\n' "$(cd "$(dirname "$f")" && pwd)" "$(basename "$f")"
}

# Prints "<repo-name>/<repo-relative-path>" for an already-absolute file path, or exits 3.
_identity_for() {
  local abs_file="$1" repo_root repo_name
  if ! repo_root="$(cd "$(dirname "$abs_file")" && git rev-parse --show-toplevel 2>/dev/null)"; then
    _err "not inside a git repo: $abs_file"
    exit 3
  fi
  repo_name="$(basename "$repo_root")"
  printf '%s/%s\n' "$repo_name" "${abs_file#"$repo_root"/}"
}

cmd_snapshot() {
  local file="${1:?usage: snapshot <file>}"
  local abs_file identity key ts hash bytes obj_dir id dest repo_root git_head dest_hash

  abs_file="$(_abs_path "$file")"
  identity="$(_identity_for "$abs_file")"
  key="$(_hash_string "$identity" | cut -c1-16)"
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  hash="$(_hash_file "$abs_file")"
  bytes="$(wc -c < "$abs_file" | tr -d ' ')"
  repo_root="$(cd "$(dirname "$abs_file")" && git rev-parse --show-toplevel)"
  git_head="$(git -C "$repo_root" rev-parse HEAD 2>/dev/null || echo null)"
  id="${ts}_$(printf '%s' "$hash" | cut -c1-12)"

  obj_dir="$SNAPSHOT_HOME/objects/$key"
  mkdir -p "$obj_dir"
  dest="$obj_dir/${id}.snap"
  cp -p "$abs_file" "$dest"

  # Verify the copy landed byte-identical before trusting it as a recovery point.
  dest_hash="$(_hash_file "$dest")"
  if [ "$dest_hash" != "$hash" ]; then
    _err "snapshot copy verification FAILED for $abs_file (source=$hash dest=$dest_hash)"
    rm -f "$dest"
    exit 5
  fi

  printf '{"id":"%s","ts":"%s","identity":"%s","path_abs":"%s","sha256":"%s","bytes":%s,"git_head":"%s","snapshot_file":"%s"}\n' \
    "$id" "$ts" "$identity" "$abs_file" "$hash" "$bytes" "$git_head" "$dest" >> "$MANIFEST"

  _log "snapshotted $identity -> $dest (sha256=$hash, ${bytes} bytes)"
  printf '%s\n' "$dest"
}

cmd_list() {
  local file="${1:?usage: list <file>}"
  local abs_file identity
  abs_file="$(_abs_path "$file")"
  identity="$(_identity_for "$abs_file")"
  [ -f "$MANIFEST" ] || { _log "no snapshots recorded yet"; return 0; }
  grep -F "\"identity\":\"$identity\"" "$MANIFEST" || { _log "no snapshots for $identity"; return 0; }
}

cmd_restore() {
  local file="${1:?usage: restore <file> --to <dest> [--id <snapshot-id>]}"
  shift || true
  local dest="" want_id=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --to) dest="$2"; shift 2 ;;
      --id) want_id="$2"; shift 2 ;;
      *) _err "unknown arg: $1"; exit 2 ;;
    esac
  done
  [ -n "$dest" ] || { _err "--to <dest> is required (this never restores in place implicitly)"; exit 2; }

  local abs_file identity line snapshot_file recorded_hash actual_hash dest_hash
  abs_file="$(_abs_path "$file")"
  identity="$(_identity_for "$abs_file")"
  [ -f "$MANIFEST" ] || { _err "no snapshot store yet"; exit 4; }

  if [ -n "$want_id" ]; then
    line="$(grep -F "\"identity\":\"$identity\"" "$MANIFEST" | grep -F "\"id\":\"$want_id\"" | tail -n1 || true)"
  else
    line="$(grep -F "\"identity\":\"$identity\"" "$MANIFEST" | tail -n1 || true)"
  fi
  [ -n "$line" ] || { _err "no snapshot found for $identity${want_id:+ (id=$want_id)}"; exit 4; }

  snapshot_file="$(printf '%s' "$line" | sed -n 's/.*"snapshot_file":"\([^"]*\)".*/\1/p')"
  recorded_hash="$(printf '%s' "$line" | sed -n 's/.*"sha256":"\([^"]*\)".*/\1/p')"
  [ -f "$snapshot_file" ] || { _err "snapshot object missing on disk: $snapshot_file"; exit 5; }

  actual_hash="$(_hash_file "$snapshot_file")"
  if [ "$actual_hash" != "$recorded_hash" ]; then
    _err "integrity check FAILED: $snapshot_file recorded=$recorded_hash actual=$actual_hash -- refusing to restore"
    exit 5
  fi

  mkdir -p "$(dirname "$dest")"
  cp -p "$snapshot_file" "$dest"
  dest_hash="$(_hash_file "$dest")"
  if [ "$dest_hash" != "$recorded_hash" ]; then
    _err "post-restore verification FAILED: $dest hash=$dest_hash expected=$recorded_hash"
    exit 5
  fi
  _log "restored $identity -> $dest (sha256=$dest_hash, verified)"
  printf '%s\n' "$dest"
}

main() {
  local sub="${1:-}"
  shift || true
  case "$sub" in
    snapshot) cmd_snapshot "$@" ;;
    list) cmd_list "$@" ;;
    restore) cmd_restore "$@" ;;
    *) _err "usage: $0 {snapshot|list|restore} <file> [...]"; exit 2 ;;
  esac
}

main "$@"
