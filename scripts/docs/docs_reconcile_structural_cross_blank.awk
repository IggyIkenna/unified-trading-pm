#!/usr/bin/awk -f
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# Cross-blank-line structural scan for the `/docs-reconcile` skill's Phase 1 item 6a
# (structural well-formedness) hunter (cursor-configs/skills/docs-reconcile/SKILL.md).
#
# The real-world defect shape this corpus has repeatedly hit: a `**bold**` span or a `(`
# parenthetical opens on one line, then a blank line intervenes before the closer — the
# renderer treats these as two separate blocks, so the bold/paren never actually closes.
# Skips frontmatter and fenced code blocks (``` ... ```) — code content isn't prose and
# legitimately contains unbalanced markdown-looking characters.
#
# Usage: awk -f scripts/docs/docs_reconcile_structural_cross_blank.awk <file.md>
# Output: "BOLD|PAREN OPEN ACROSS BLANK LINE: opened at L<N>, blank at L<M>"
#         "BOLD|PAREN STILL OPEN AT EOF: opened at L<N>" (unterminated span, file-wide)

BEGIN { fm = 0; bold_open = 0; bold_open_line = 0; paren_open = 0; paren_open_line = 0; in_fence = 0 }
{
  line = $0
  if (line == "---" && fm < 2) { fm++; next }
  if (fm < 2) next

  if (line ~ /^```/) { in_fence = !in_fence; next }
  if (in_fence) next

  if (line ~ /^[[:space:]]*$/) {
    if (bold_open) print "BOLD OPEN ACROSS BLANK LINE: opened at L" bold_open_line ", blank at L" NR
    if (paren_open) print "PAREN OPEN ACROSS BLANK LINE: opened at L" paren_open_line ", blank at L" NR
    bold_open = 0
    paren_open = 0
    next
  }

  copy = line
  n_bold = gsub(/\*\*/, "**", copy)
  if (n_bold % 2 == 1) {
    if (bold_open) { bold_open = 0 } else { bold_open = 1; bold_open_line = NR }
  }

  copy = line
  n_po = gsub(/\(/, "(", copy)
  copy = line
  n_pc = gsub(/\)/, ")", copy)
  diff = n_po - n_pc
  if (diff > 0) {
    if (!paren_open) { paren_open = 1; paren_open_line = NR }
  } else if (diff < 0) {
    paren_open = 0
  }
}
END {
  if (bold_open) print "BOLD STILL OPEN AT EOF: opened at L" bold_open_line
  if (paren_open) print "PAREN STILL OPEN AT EOF: opened at L" paren_open_line
}
