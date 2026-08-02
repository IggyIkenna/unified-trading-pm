---
doc_type: issue
title: >-
  market-tick-data-service's QUALITY_GATE_BYPASS_AUDIT.md claims zero basedpyright exceptions while 237/442 files (54%)
  carry a blanket 7-check file-level pyright suppression header and 658 inline `# type: ignore` comments exist
  repo-wide, unratcheted and unenforced by quality-gates.sh
summary: >-
  Surfaced during review of unified-trading-pm@47ede96ce / market-tick-data-service@c8742adf+7be1c3b8
  (defi_hyperliquid_perp_funding_derivative_ticker_divergence_2026_07_28.md, slot 9) — the data-correctness work itself
  was sound, but the new `_perp_funding_hyperliquid.py` module carries a file-level `# pyright:
  reportUnknownVariableType=false, reportUnknownArgumentType=false, reportAny=false, reportUnknownMemberType=false,
  reportMissingTypeStubs=false, reportPrivateUsage=false, reportUnusedFunction=false` header plus 2 unjustified inline
  `# type: ignore[code]` comments. Confirmed this is NOT novel to that commit — the worker faithfully mirrored the
  dominant existing convention (the exact sibling file it named as its template, `_perp_funding_kalshi_polymarket.py`,
  carries the identical header). Repo-wide in market-tick-data-service alone: 237/442 `.py` files (54%) carry the
  identical blanket header; 658 inline `# type: ignore` comments exist. Meanwhile `QUALITY_GATE_BYPASS_AUDIT.md` §2.3
  "Basedpyright Exceptions" reads literally "None" — a required compliance artifact directly contradicting the actual
  codebase state. `scripts/quality-gates.sh` has no grep/ratchet check for either pattern (confirmed via grep), unlike
  the sibling `BE_EXCLUDE_GLOBS` / `FUNCTION_SIZE_EXTRA_EXCLUDES` / `ASYNCIO_RUN_EXCLUDE_GLOBS` categories, which ARE
  ratcheted and documented in the same audit doc. Per /codex/06-coding-standards/README.md +
  /codex/06-coding-standards/quality-gates.md STEP 5.22, blanket file-level pyright suppressions are explicitly BANNED
  ("institutionalise the downgrade... net-new broad/blanket suppressions must be 0") and every suppression must be
  logged — so this repo's "basedpyright clean" QG signal currently proves far less than the codex implies, since real
  type errors could be silently masked under any of the 7 disabled checks across 237 files.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    coding-standards,
    basedpyright,
    type-ignore,
    quality-gates,
    ssot-contradiction,
    audit-doc,
    ratchet,
    market-tick-data-service,
  ]
related:
  [
    /plans/archive/issues/defi_hyperliquid_perp_funding_derivative_ticker_divergence_2026_07_28.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source:
  "Review-agent spot-check (slot 1, agt-5162a5) of unified-trading-pm@47ede96ce / market-tick-data-service@c8742adf,
  2026-07-30. Escalated to main (agt-fd75de) via chat for the policy-scoping call; main ACKed as a CLAUDE.md 'big
  finding — SSOT-vs-reality contradiction in a required compliance artifact' and directed this doc's filing +
  decomposition."
---

# market-tick-data-service's basedpyright-exceptions audit doc contradicts the actual codebase

## What I found

Reviewing `market-tick-data-service@c8742adf` (new `_perp_funding_hyperliquid.py` stage module, part of an otherwise
excellent data-correctness fix — see the related issue doc, no defect in that work itself), the new file opens with:

```python
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportAny=false, reportUnknownMemberType=false, reportMissingTypeStubs=false, reportPrivateUsage=false, reportUnusedFunction=false
```

plus 2 inline `# type: ignore[union-attr]` / `# type: ignore[arg-type]` comments, neither carrying the `# <dep> reason`
justification the codex's narrow-exemption bar requires (`/codex/06-coding-standards/quality-gates.md:1837-1840`:
"Exemptions are NARROW + per-line + exact-rule only... a single `# pyright: ignore[exactRule]  # <dep> reason`...
**Banned:** blanket file-level `# pyright: reportX=false`, broad `# type: ignore` (no rule code)... Net-new
broad/blanket suppressions must be 0").

**Checked scope before escalating** (to avoid pinning a repo-wide gap on one worker):

- The new file's header is a byte-identical copy of `_perp_funding_kalshi_polymarket.py`'s header — the exact sibling
  module this commit's own docstring names as its template. Not novel.
- `grep -rl "^# pyright: report" market_tick_data_service/ | wc -l` → **237** files (of 442 `.py` files total, 54%).
- `grep -rn "# type: ignore" --include="*.py" . | grep -v .venv | wc -l` → **658** occurrences repo-wide.
- `grep -n "type: ignore" scripts/quality-gates.sh scripts/quality_gates/*.py` → **zero hits**. No ratchet/grep check
  exists for either pattern in this repo's gate.
- `QUALITY_GATE_BYPASS_AUDIT.md` §2.3 "Basedpyright Exceptions" reads literally "None." §2.2 "Ruff Exceptions" also
  reads "None." Meanwhile §1.1 (`BE_EXCLUDE_GLOBS`), §2.1 (`FUNCTION_SIZE_EXTRA_EXCLUDES`), and §1.3
  (`ASYNCIO_RUN_EXCLUDE_GLOBS`) all show real, itemized, ratcheted entries with per-file justification — proving the
  audit-doc-plus-ratchet mechanism works and is actively maintained for OTHER categories. Basedpyright/type-ignore is
  the one category that fell through entirely.

## Why it matters

- **The audit artifact is factually false**, not just stale — "None" when the true count is 237 files / 658 comments is
  a defect in the compliance doc itself, independent of whatever policy the operator eventually picks for the underlying
  pattern.
- **The QG's basedpyright-clean signal is weaker than the codex implies.** `reportUnknownVariableType`,
  `reportUnknownArgumentType`, `reportAny`, `reportUnknownMemberType`, `reportMissingTypeStubs`, `reportPrivateUsage`,
  and `reportUnusedFunction` are all disabled in 237 files — any of the 7 could currently be masking a real bug in those
  files, and nothing in CI would surface it.
- **`reportPrivateUsage=false` specifically is doing real work being suppressed, not just noise**: the new
  `_perp_funding_hyperliquid.py` module reaches into another module's underscore-prefixed "private" symbols extensively
  (`_h._resolve_pipeline_mode_for_protocol`, `_h._make_session`, `_h._COIN_BATCH_SIZE`, `_h._BATCH_DELAY_SECONDS`,
  `_h.HYPERLIQUID_API_URL`, etc.) — an architecture smell (reaching across a private boundary instead of a public API)
  that the suppression hides rather than surfaces.
- **No partial fix**: per CLAUDE.md's data-pipeline/coding-standards discipline, once a gap like this is found it gets
  closed in full, not left as a chat-log observation — hence this doc + the todos below rather than a one-off ping.

## Recommended decision

This splits into a standards-determined part (do regardless of the policy call) and an operator policy part (durable
codex-wording decision, not an agent's unilateral call) — see Todos. Main's grounding (2026-07-30, `agt-fd75de`): the
codex's existing wording is explicitly ban-and-shrink ("BANNED", "must be 0", "baselines only go DOWN"), so the
standards-default leans toward drive-to-zero — but the sheer scale (54% of the repo, including the exact sibling file
this pattern was copied from) is a legitimate reason the operator might instead sanction a narrowed, explicit carve-out
for loosely-typed vendor-response glue code. Either way, the audit-doc correction and the ratchet (todos 1-2) ship first
and are correct under both outcomes; todo 3 sets the eventual target.

## Todos

- [x] ✅ [SCRIPT] P2. **Correct `market-tick-data-service/QUALITY_GATE_BYPASS_AUDIT.md` §2.3 "Basedpyright Exceptions"**
      to reflect reality instead of "None": itemize (or reference a generated inventory file for) the 237 files carrying
      the blanket file-level `# pyright: report*=false` header and the 658 inline `# type: ignore` comments, grouped by
      directory/module for readability (a flat 237-row table is unwieldy — consider one row per distinct
      suppression-set + a file-count, matching how §2.1's `FUNCTION_SIZE_EXTRA_EXCLUDES` entry summarizes ~30 files as a
      named list rather than 30 rows). This todo is required under EITHER outcome of todo 3. (repo:
      market-tick-data-service) — market-tick-data-service@409ee88f. Re-measured at correction time (counts unchanged:
      237 files / 658 comments); §2.3 now itemizes both by directory bucket with regen grep commands.
- [x] ✅ [CODE] P2. **Add a freeze-and-shrink ratchet to `market-tick-data-service/scripts/quality-gates.sh`** for both
      patterns (blanket file-level pyright headers via a grep/AST count of `^# pyright: report\w+=false` lines; inline
      `# type: ignore` via a grep count), mirroring the existing `BE_EXCLUDE_GLOBS` / `FUNCTION_SIZE_EXTRA_EXCLUDES` /
      `ASYNCIO_RUN_EXCLUDE_GLOBS` ratchet mechanism (freeze current counts as the baseline — 237 files / 658 comments as
      of this doc's filing, re-measure exact counts at implementation time since more may land before this ships — fail
      the gate on any INCREASE, never require a decrease to ship). This closes the "basedpyright clean proves less than
      it should" gap immediately regardless of the operator's todo-3 answer: even if vendor-glue suppressions get
      sanctioned, net-new UNSANCTIONED ones should still be gated to 0 per the codex's own existing rule. (repo:
      market-tick-data-service) — market-tick-data-service@d072b035.
- [ ] [OPERATOR] P3. **Choose the durable policy direction** for the 237-file / 658-comment inventory once todos 1-2
      ship: (a) drive it toward zero as genuine codex enforcement (a real type-safety recovery project — likely large,
      since it's 54% of the repo, and would need its own follow-up plan with a scoped rollout), OR (b) formally ACCEPT
      blanket suppressions as the sanctioned convention specifically for loosely-typed vendor-response glue code (the
      CLI stage-handler modules under `cli/handlers/`) and relax the codex wording in
      `/codex/06-coding-standards/README.md` + `/codex/06-coding-standards/quality-gates.md` STEP 5.22 to say so
      explicitly, scoped to that glob (not a blanket workspace-wide relaxation). Repo: unified-trading-pm (codex
      wording, if (b)); market-tick-data-service (follow-up cleanup plan, if (a)).

## Progress Log

- **2026-07-30 (review, slot 1, agt-5162a5)**: Filed per main's (agt-fd75de) direction after a chat escalation — see
  this doc's `source:` field for the full exchange. Not pinging the discovering worker (slot 9,
  market-tick-data-service@c8742adf/7be1c3b8) — they mirrored the dominant existing convention faithfully, they did not
  introduce anything novel, and the actual data-correctness work in that commit is sound (reviewed separately, verdict
  ok).
- **2026-07-30 (backend_engineer, slot 3)**: Todo 1 shipped — market-tick-data-service@409ee88f. Re-measured both counts
  fresh (grep -rl "^# pyright: report" market_tick_data_service/ | wc -l → still 237; grep -rn "# type: ignore"
  --include="*.py" . | grep -v .venv | wc -l → still 658, no drift since filing). Corrected §2.3 from "None" to two
  tables (blanket-header files + inline-ignore occurrences), each grouped by directory bucket, plus the two regen grep
  commands so future re-measurement doesn't require re-deriving the query. Todos 2 (ratchet) and 3 (operator policy
  call) remain open — not in this task's scope.
- **2026-07-30 (backend_engineer, slot 5)**: Todo 2 shipped — market-tick-data-service@d072b035. Re-measured both counts
  fresh at implementation time (`grep -rl "^# pyright: report" market_tick_data_service/ | wc -l` → still 237;
  `grep -rn "# type: ignore" --include="*.py" . | grep -v .venv | wc -l` → still 658, no drift). Added STEP 5.94
  (blanket file-level pyright-suppression header freeze-and-shrink ratchet, baseline=237 files) and STEP 5.95 (inline
  `# type: ignore` freeze-and-shrink ratchet, baseline=658 occurrences) directly to
  `market-tick-data-service/scripts/quality-gates.sh`, mirroring this file's own local grep-based STEP-block style (STEP
  5.92/5.93) rather than the shared `unified-trading-pm/scripts/quality-gates-base/base-service.sh` YAML-baseline
  mechanism, since this todo is scoped to the one repo only. Both fail the gate on any count increase above the frozen
  baseline; a decrease only warns (ratchet the baseline number down in the script, never raise it). Verified both PASS
  at the frozen baselines in a full local `quality-gates.sh` run (267s, all green, sentinel=d072b035) before shipping.
  Note: this repo's local STEP numbering already collided with `base-service.sh`'s own STEP 5.92/5.93 before this
  change: my new local 5.94/5.95 similarly duplicate the labels of `base-service.sh`'s STEP 5.94 (fallback-import
  ratchet) and STEP 5.95 (DTZ/TID251 ratchet), which also run in the same QG pass — cosmetically confusing in the log
  (two different checks both print "STEP 5.94"/"STEP 5.95") but functionally harmless, and consistent with this file's
  pre-existing convention. Todo 3 (operator policy call) remains open, not in this task's scope.
