#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# cursor-storage-management.sh — Cursor IDE storage management
# Analyzes and cleans up Cursor storage to reduce disk usage
#
# Usage:
#   bash cursor-storage-management.sh                # Show storage breakdown
#   bash cursor-storage-management.sh --analyze      # Detailed analysis
#   bash cursor-storage-management.sh --clean-old    # Clean old data (>30 days)
#   bash cursor-storage-management.sh --vacuum-db    # Compact databases

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1)
  GREEN=$(tput setaf 2)
  YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6)
  BOLD=$(tput bold)
  NC=$(tput sgr0)
else
  RED=""
  GREEN=""
  YELLOW=""
  CYAN=""
  BOLD=""
  NC=""
fi

# ── Configuration ─────────────────────────────────────────────────────────────
CURSOR_DIR="${HOME}/.cursor"
CLEANUP_AGE_DAYS=30

# ── Helper functions ──────────────────────────────────────────────────────────
log_info() { echo "${CYAN}ℹ${NC} $*"; }
log_success() { echo "${GREEN}✅${NC} $*"; }
log_warning() { echo "${YELLOW}⚠${NC} $*"; }
log_error() { echo "${RED}✗${NC} $*" >&2; }

format_size() {
  local size=$1
  if command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec-i --suffix=B "$size"
  else
    echo "$size bytes"
  fi
}

# ── Storage breakdown ─────────────────────────────────────────────────────────
show_storage_breakdown() {
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Cursor IDE Storage Breakdown${NC}"
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  if [ ! -d "$CURSOR_DIR" ]; then
    log_error "Cursor directory not found: $CURSOR_DIR"
    exit 1
  fi

  log_info "Analyzing storage in: ${BOLD}${CURSOR_DIR}${NC}"
  echo ""

  # Total size
  local total_size
  total_size=$(du -sh "$CURSOR_DIR" 2>/dev/null | awk '{print $1}')
  echo "📊 ${BOLD}Total Cursor storage: ${total_size}${NC}"
  echo ""

  # Breakdown by directory
  echo "Breakdown by component:"
  echo ""
  du -sh "${CURSOR_DIR}"/* 2>/dev/null | sort -rh | while read -r size path; do
    local component
    component=$(basename "$path")
    printf "  %-20s %10s\n" "$component" "$size"
  done

  echo ""

  # Database files
  echo "Large database files (>10MB):"
  echo ""
  find "$CURSOR_DIR" -name "*.db" -size +10M -exec du -h {} \; 2>/dev/null | sort -rh | while read -r size path; do
    local relpath="${path#${CURSOR_DIR}/}"
    printf "  %-50s %10s\n" "$relpath" "$size"
  done || echo "  ${YELLOW}No large database files found${NC}"

  echo ""
}

# ── Analyze old data ──────────────────────────────────────────────────────────
analyze_old_data() {
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Old Data Analysis (>${CLEANUP_AGE_DAYS} days)${NC}"
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  # Old agent transcripts
  local old_transcripts
  old_transcripts=$(find "${CURSOR_DIR}/projects" -name "*.jsonl" -type f -mtime +${CLEANUP_AGE_DAYS} 2>/dev/null || true)
  local transcript_count=0
  local transcript_size="0"

  if [ -n "$old_transcripts" ]; then
    transcript_count=$(echo "$old_transcripts" | wc -l | tr -d ' ')
    transcript_size=$(echo "$old_transcripts" | xargs du -ch 2>/dev/null | tail -1 | awk '{print $1}')
  fi

  echo "Agent transcripts:"
  echo "  Count: ${BOLD}${transcript_count}${NC} files"
  echo "  Size:  ${BOLD}${transcript_size}${NC}"
  echo ""

  # Old chat databases
  local old_chats
  old_chats=$(find "${CURSOR_DIR}/chats" -name "store.db" -type f -mtime +${CLEANUP_AGE_DAYS} 2>/dev/null || true)
  local chat_count=0
  local chat_size="0"

  if [ -n "$old_chats" ]; then
    chat_count=$(echo "$old_chats" | wc -l | tr -d ' ')
    chat_size=$(echo "$old_chats" | xargs du -ch 2>/dev/null | tail -1 | awk '{print $1}')
  fi

  echo "Chat databases:"
  echo "  Count: ${BOLD}${chat_count}${NC} conversations"
  echo "  Size:  ${BOLD}${chat_size}${NC}"
  echo ""

  local total_cleanable=$((transcript_count + chat_count))
  if [ "$total_cleanable" -eq 0 ]; then
    log_success "No old data to clean (everything is recent)"
  else
    log_warning "Found ${total_cleanable} items that could be cleaned"
    echo ""
    echo "Run with ${CYAN}--clean-old${NC} to remove old data"
  fi

  echo ""
}

# ── Clean old data ────────────────────────────────────────────────────────────
clean_old_data() {
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Cleaning Old Data (>${CLEANUP_AGE_DAYS} days)${NC}"
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  log_warning "This will delete agent transcripts and chat databases older than ${CLEANUP_AGE_DAYS} days"
  read -r -p "Continue? [y/N]: " confirm

  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    log_info "Cleanup cancelled"
    exit 0
  fi

  echo ""

  # Clean agent transcripts
  log_info "Cleaning old agent transcripts..."
  local transcript_count
  transcript_count=$(find "${CURSOR_DIR}/projects" -name "*.jsonl" -type f -mtime +${CLEANUP_AGE_DAYS} -delete -print 2>/dev/null | wc -l | tr -d ' ')
  if [ "$transcript_count" -gt 0 ]; then
    log_success "Deleted ${transcript_count} old agent transcript(s)"
  else
    log_info "No old agent transcripts to delete"
  fi

  # Clean chat databases (remove entire conversation folders)
  log_info "Cleaning old chat databases..."
  local chat_count=0
  while IFS= read -r db_file; do
    if [ -n "$db_file" ]; then
      local chat_dir
      chat_dir=$(dirname "$db_file")
      rm -rf "$chat_dir" 2>/dev/null && ((chat_count++)) || true
    fi
  done < <(find "${CURSOR_DIR}/chats" -name "store.db" -type f -mtime +${CLEANUP_AGE_DAYS} 2>/dev/null)

  if [ "$chat_count" -gt 0 ]; then
    log_success "Deleted ${chat_count} old conversation(s)"
  else
    log_info "No old conversations to delete"
  fi

  echo ""
  log_success "Cleanup complete!"
  echo ""

  # Show new size
  local new_size
  new_size=$(du -sh "$CURSOR_DIR" 2>/dev/null | awk '{print $1}')
  echo "📊 Cursor storage now: ${BOLD}${new_size}${NC}"
  echo ""
}

# ── Vacuum databases ──────────────────────────────────────────────────────────
vacuum_databases() {
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Database Compaction (VACUUM)${NC}"
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  if ! command -v sqlite3 >/dev/null 2>&1; then
    log_error "sqlite3 not found. Install it to use this feature."
    exit 1
  fi

  log_warning "This will compact SQLite databases (may take a few minutes)"
  log_warning "Close Cursor IDE before running this!"
  echo ""
  read -r -p "Cursor is closed and ready to proceed? [y/N]: " confirm

  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    log_info "Vacuum cancelled"
    exit 0
  fi

  echo ""

  # Find all .db files
  local db_files
  db_files=$(find "$CURSOR_DIR" -name "*.db" -type f 2>/dev/null || true)
  local total_count=0
  local success_count=0
  local space_saved=0

  if [ -z "$db_files" ]; then
    log_info "No database files found"
    exit 0
  fi

  total_count=$(echo "$db_files" | wc -l | tr -d ' ')
  log_info "Found ${total_count} database(s) to compact"
  echo ""

  while IFS= read -r db_file; do
    if [ -f "$db_file" ]; then
      local before_size
      before_size=$(stat -f%z "$db_file" 2>/dev/null || stat --format=%s "$db_file" 2>/dev/null)

      # Try to vacuum
      if sqlite3 "$db_file" "VACUUM;" 2>/dev/null; then
        local after_size
        after_size=$(stat -f%z "$db_file" 2>/dev/null || stat --format=%s "$db_file" 2>/dev/null)
        local saved=$((before_size - after_size))

        if [ "$saved" -gt 0 ]; then
          space_saved=$((space_saved + saved))
          local saved_mb=$((saved / 1024 / 1024))
          log_success "$(basename "$db_file"): saved ${saved_mb}MB"
        fi
        ((success_count++))
      else
        log_warning "Failed to vacuum: $(basename "$db_file")"
      fi
    fi
  done <<<"$db_files"

  echo ""
  log_success "Compacted ${success_count}/${total_count} database(s)"

  if [ "$space_saved" -gt 0 ]; then
    local space_mb=$((space_saved / 1024 / 1024))
    echo "💾 Space saved: ${BOLD}${space_mb}MB${NC}"
  else
    echo "💾 No space saved (databases were already compact)"
  fi

  echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  local command="${1:-}"

  case "$command" in
    --analyze)
      show_storage_breakdown
      echo ""
      analyze_old_data
      ;;
    --clean-old)
      clean_old_data
      ;;
    --vacuum-db)
      vacuum_databases
      ;;
    --help | -h)
      echo "Usage: $0 [OPTION]"
      echo ""
      echo "Options:"
      echo "  (no args)      Show storage breakdown"
      echo "  --analyze      Detailed analysis including old data"
      echo "  --clean-old    Clean data older than ${CLEANUP_AGE_DAYS} days"
      echo "  --vacuum-db    Compact SQLite databases (close Cursor first!)"
      echo "  --help         Show this help message"
      ;;
    "")
      show_storage_breakdown
      ;;
    *)
      log_error "Unknown option: $command"
      echo "Run with --help for usage"
      exit 1
      ;;
  esac
}

main "$@"
