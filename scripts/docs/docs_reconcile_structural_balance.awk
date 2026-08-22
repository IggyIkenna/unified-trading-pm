#!/usr/bin/awk -f
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# Per-line structural-balance scan for the `/docs-reconcile` skill's Phase 1 item 6a
# (structural well-formedness) hunter (cursor-configs/skills/docs-reconcile/SKILL.md).
#
# Flags any single line (after frontmatter) whose paren/bracket/backtick/bold-marker counts
# don't balance WITHIN that line — the fast, cheap first pass. A flagged line is a CANDIDATE,
# not a confirmed defect: a markdown construct can legitimately span multiple lines (this check
# only catches same-line imbalance; see docs_reconcile_structural_cross_blank.awk for the
# blank-line-crossing case, which is the more common real defect shape in this corpus).
#
# Usage: awk -f scripts/docs/docs_reconcile_structural_balance.awk <file.md>
# Output: "<line#> [p:opens/closes b:brackets k:backticks bold:**]: <line text, truncated>"

BEGIN { fm = 0 }
{
  line = $0
  if (line == "---") { fm++; next }
  if (fm < 2) next

  copy = line
  paren_open = gsub(/\(/, "(", copy)
  copy = line
  paren_close = gsub(/\)/, ")", copy)
  copy = line
  brack_open = gsub(/\[/, "[", copy)
  copy = line
  brack_close = gsub(/\]/, "]", copy)
  copy = line
  backtick = gsub(/`/, "`", copy)
  copy = line
  bold = gsub(/\*\*/, "**", copy)

  if (paren_open != paren_close || brack_open != brack_close || backtick % 2 != 0 || bold % 2 != 0) {
    printf "%d [p:%d/%d b:%d k:%d bold:%d]: %s\n", NR, paren_open, paren_close, brack_open + brack_close, backtick, bold, substr(line, 1, 220)
  }
}
