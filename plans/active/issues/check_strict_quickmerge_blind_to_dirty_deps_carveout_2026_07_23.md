---
doc_type: issue
title:
  check_strict_quickmerge.py's carve-out detection is path-prefix-only — it flags sanctioned dirty-deps direct pushes as
  quickmerge bypasses because they touch real code, not a carve-out path
summary: >-
  Found while investigating mtds_pr671_promotion_chain_of_walls_2026_07_21.md's Wall-3 (a 29-commit provenance-gate
  block on market-tick-data-service PR #672). Sampled 4 of the 29 flagged commits (a7569298, 3253cae3, d302f07a,
  c85af5b2) — all 4 carry an explicit commit-body note ("Direct-push dirty-deps carve-out: quickmerge pre-flight blocked
  on foreign uncommitted WIP in <repo>...") documenting the sanctioned CLAUDE.md carve-out ("Closed carve-out direct
  pushes: (1) dirty-deps"). These are legitimate, documented, sanctioned direct pushes — not governance violations.
  `check_strict_quickmerge.py`'s CARVE_PREFIX is `(".github/", "scripts/", "plans/", "codex/", "docs/")` — a commit that
  legitimately bypasses quickmerge under the dirty-deps carve-out but touches real product code matches NONE of these
  path prefixes, and by definition has no `Quickmerge:` trailer (quickmerge never ran — that is the entire point of the
  carve-out), so the checker flags it as a bypass every time. The flag was not wrong given the checker's own narrow
  rule; the rule just does not model an entire sanctioned carve-out category.
status: open
resolved_by:
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, provenance-gate, check-strict-quickmerge, carve-out, dirty-deps, governance]
related:
  - plans/active/issues/mtds_pr671_promotion_chain_of_walls_2026_07_21.md
  - plans/active/issues/provenance_gate_squash_perpetual_block_2026_06_17.md
created: "2026-07-23"
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: none
source: [mtds_pr671_promotion_chain_of_walls_2026_07_21 todo 2 follow-up]
locked_by:
depends_on: []
---

# check_strict_quickmerge.py cannot recognize the dirty-deps carve-out

## What was found

`scripts/cicd/check_strict_quickmerge.py` flags a CODE-source commit (`*.py`/`*.ts` outside scripts/tests/.github)
reaching the integration branch without a `Quickmerge:` trailer, UNLESS the commit is a carve-out — and carve-outs are
detected PURELY by file path prefix (`CARVE_PREFIX = (".github/", "scripts/", "plans/", "codex/", "docs/")`) or
extension. CLAUDE.md documents a SEPARATE, sanctioned carve-out class that this path-based logic cannot see: "Closed
carve-out direct pushes: (1) dirty-deps" — when quickmerge's pre-flight blocks on a dependency repo's uncommitted WIP, a
direct commit+push is the sanctioned recovery, and by convention (not enforced anywhere) the commit body notes why,
e.g.:

> Direct-push dirty-deps carve-out: quickmerge pre-flight blocked on foreign uncommitted WIP in unified-trading-library
> (concurrent agent). MTDS QG green (6187 passed, cov 80.22%).

Such a commit touches real product code (not a carve-out path) and has no `Quickmerge:` trailer by construction, so
`check_strict_quickmerge.py` correctly-per-its-own-rule, but incorrectly-per-the-actual-policy, flags it as a bypass.
Confirmed on 4 of 29 commits flagged on market-tick-data-service PR #672's provenance block; the other 25 were not
individually checked but the pattern (an actively-shipping repo whose deps are frequently dirty under fleet concurrency)
makes it likely most/all are the same class.

## Why this matters

- **False-positive governance blocks**: a repo can sit provenance-blocked (auto-merge not armed on its LDR→main promote
  PR) indefinitely for commits that were never actually ungated — they were QG-green, sanctioned, documented direct
  pushes.
- **Erodes the signal**: CLAUDE.md's own note on the sibling class of block ("Do NOT hand-arm auto-merge to 'unblock'
  this — that promotes the bypassed code AND moves the provenance baseline past it, so the violation is laundered and
  never flagged again") means a human/agent facing a wall of 29 false positives is under real pressure to hand-arm past
  the gate — which is exactly how the 2026-07-16 incident (33 genuinely-bypassed commits laundered through a manual
  override) happened. A checker that cries wolf on sanctioned carve-outs makes the NEXT genuine violation more likely to
  be waved through, not less.

## Options (not chosen — needs careful review, this is a governance-adjacent checker)

1. **Recognize a commit-body marker.** Grep the commit message for a specific, stable phrase (e.g. "Direct-push
   dirty-deps carve-out:") and treat a match as carve-out-exempt. Cheap, matches the ALREADY-organic convention agents
   use. Risk: the marker is free-text in a commit message — trivially spoofable by anyone who wants to bypass the gate
   for real. Would need either a stricter, less-guessable marker format, or acceptance that this checker already trusts
   commit messages in other ways (the `Quickmerge:` trailer itself is also just commit-message text).
2. **A structured, machine-written marker instead of free text.** Have the dirty-deps direct-push RECIPE (wherever it's
   documented — SUB_AGENT_MANDATORY_RULES.md / the workspace git-safety codex) also update the commit trailer convention
   itself, e.g. `Quickmerge: direct-carveout-dirty-deps` (a THIRD trailer value alongside today's `agent`/`human`), so
   the checker's EXISTING trailer-presence logic just gains one more accepted value — no new text-matching heuristic,
   reuses the mechanism already trusted for `Quickmerge: agent`/`human`.
3. **Do nothing; treat false positives as acceptable noise.** Cheapest, but directly contradicts the "crying wolf erodes
   the real signal" concern above — not recommended.

## Recommendation

Lean toward (2): extending the `Quickmerge:` trailer's accepted value set is the smallest change that closes the gap
without introducing a new, spoofable free-text heuristic, and it requires updating the recipe agents already follow for
a dirty-deps direct push (add one line: stamp `Quickmerge: direct-carveout-dirty-deps` on the commit) rather than
teaching the checker to parse prose. Needs operator sign-off before implementation — this touches the provenance gate's
trust model, which is explicitly governance-sensitive (see "Why this matters" above).

## Not urgent to act on

market-tick-data-service PR #672 itself is long since closed/superseded; the repo's `main`/`live-defi-rollout` trees are
now identical (fully promoted). This doc is about preventing the SAME false-positive class recurring for the next
repo/commit that legitimately uses the dirty-deps carve-out, not about unblocking anything currently stuck.

## Codex SSOTs

`codex/08-workflows/ci-cd-flow.md` (quickmerge / strict-quickmerge / carve-out list).
