#!/usr/bin/awk -f
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# Orphaned-table-row scan for the `/docs-reconcile` skill's Phase 1 item 6a (structural
# well-formedness) hunter (cursor-configs/skills/docs-reconcile/SKILL.md).
#
# Flags a non-pipe, non-blank line immediately following a `|`-prefixed table row — the
# signature of a table row that got split across physical lines by an embedded raw newline
# (a real, repeatedly-found defect class in this corpus: a table cell's content wrapped onto
# its own line instead of staying on the row's single line). Skips frontmatter and fenced code
# blocks.
#
# Usage: awk -f scripts/docs/docs_reconcile_structural_table_break.awk <file.md>
# Output: "ORPHAN NON-PIPE LINE RIGHT AFTER TABLE ROW: L<N>: <line text, truncated>"

BEGIN { fm = 0; in_fence = 0; prev_pipe = 0 }
{
  line = $0
  if (line == "---" && fm < 2) { fm++; next }
  if (fm < 2) next
  if (line ~ /^```/) { in_fence = !in_fence; prev_pipe = 0; next }
  if (in_fence) { prev_pipe = 0; next }

  is_pipe = (line ~ /^\|/) ? 1 : 0
  is_blank = (line ~ /^[[:space:]]*$/) ? 1 : 0

  if (!is_pipe && !is_blank && prev_pipe) {
    print "ORPHAN NON-PIPE LINE RIGHT AFTER TABLE ROW: L" NR ": " substr(line, 1, 180)
  }
  prev_pipe = is_pipe
}
