---
doc_type: issue
title:
  Prettier emphasis-mangling corrupts underscore identifiers across plans + codex docs (deterministic, two defect
  classes)
summary:
  Prettier's markdown formatter deterministically corrupts doc passages in this repo — underscores in unbackticked
  identifiers get rewritten as asterisks (`data_types`→`data*types`, `schema_version`→`schema*version`,
  `{mode}_{source}`→`{mode}*{source}`, `LIVE_`/`BATCH_`→`LIVE*`/`BATCH\_`) and wrapped paragraphs collapse into blob
  lines with multi-space runs. Two proven defect classes — (1) a code span split across a line break and/or bare
  underscore identifiers mis-pair backtick/emphasis parsing for the whole paragraph; (2) very long single-paragraph list
  items with many inline code spans re-corrupt on EVERY reformat even when backtick-clean (fix requires a paragraph
  split). Found during the 2026-07-14 verify-rerun-2 close-out; the reference repairs are unified-trading-pm@169a8c8cd
  and @65420c363. A corpus scan found ~31 plans docs (repair waves dispatched same session) and 13 codex docs (SSOTs —
  repair operator-gated) carrying the signature; plans/archive copies are left as historical record.
status: resolved
resolved_by:
  "doc-reconciliation session 2026-07-14 — corpus repaired (~60 docs: plans waves @6118a3258/@61bf72297/@6ad39dc29/
  @d87565728/@9a914087d/@e1b983b90 + codex @f54f0e9d6 operator-approved + 9 late asset-group-token finds), prevention
  shipped (PRETTIER_MIN_VERSION=3.9.5 guard in prettier-autostage.sh — 3.9.5 proven non-mangling by repro — +
  check_prettier_mangling.sh backstop in the plan-hygiene gate), corpus scan 1,459 files clean. plans/archive copies
  intentionally left as historical record."
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [docs-integrity, prettier, tooling, plans-corpus, codex, quality-gates]
related:
  [
    /plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
  ]
created: 2026-07-14
source:
  - verify-rerun-2 chunk-7 fixer agent flagged pre-existing multi-space corruption in
    instruments_foundation_completeness_2026_06_24.md; root-caused + corpus-scanned during the close-out.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
drift_direction: advance-docs
parent_epic: agent_operating_framework_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-14
locked_by:
locked_since:
---

# Prettier emphasis-mangling — corpus-wide doc corruption (two defect classes)

## What happens

Running prettier (directly or via the prek pre-commit auto-stage hook) on affected markdown deterministically corrupts
content — this is NOT a concurrency race (it reproduces on a clean single-threaded `npx prettier --write`):

- Underscores in unbackticked identifiers become asterisks: `data_types` → `data*types`, `schema_version` →
  `schema*version`, `{mode}_{source}` → `{mode}*{source}`, `LIVE_`/`BATCH_` → `LIVE*`/`BATCH\_`. This can invert meaning
  in normative text (a QG rule describing `LIVE_`-prefixed enum members now reads `LIVE*`).
- Wrapped paragraph lines collapse into a single blob line with 4-6-space runs where newlines were; spaces around inline
  code spans get eaten (`` glued `PROTOCOL-CHAIN` `` → ``glued`PROTOCOL-CHAIN` ``).

## Root causes (both proven by isolated repro)

1. **Backtick/emphasis mis-pairing** — a code span split across a line break (e.g. `` `master_data_canonicalisation_ ``
   at end-of-line continuing `` migration_catalogue_2026_06_07` `` on the next) and/or bare underscore identifiers in
   prose make prettier's parser mis-pair delimiters for the whole paragraph. Repair: restore original text, backtick
   every bare underscore identifier, never split a code span across a line break. Reference: `169a8c8cd`.
2. **Very-long-paragraph re-corruption** — a single-paragraph list item long enough (many inline code spans) re-mangles
   on every `--write` pass even when backtick-clean. Repair: split into two paragraphs inside the same list item at a
   sentence boundary (wording unchanged). Reference: `65420c363` (isolated repro: each half alone stable, combined blob
   breaks).

**Verification recipe for any repair**: detection grep clean + TWO consecutive `npx prettier --write` passes with the
second reporting unchanged (one pass is NOT sufficient proof under defect 2) + `npx prettier --check` green.

Detection signature (has false positives — legit globs like `data_type=*/`, escaped `\*`; verify each hit in context):

```
[a-z]\*[a-z_]+ < v9|\{mode\}\*\{source\}|asset\*group=|schema\*version|pipeline\*mode|instrument\*type|data\*type
```

## Affected inventory (scan 2026-07-14)

- **Repaired 2026-07-14**: `instruments_foundation_completeness_2026_06_24.md` (@169a8c8cd), 6 propagated docs
  (@65420c363), ~31 further plans/{active,epics,audit} docs dispatched to 5 repair batches same session (batch commits
  cited in the reconciliation issue doc's Progress Log).
- **plans/archive/** copies: left as historical record (out of repair scope).
- **codex/ — 13 docs, repair OPERATOR-GATED**: `POST_PLAN_REALITY_2026_05_06`, 15-runbooks/alerting/alert-code-taxonomy,
  04-architecture/service-contract-audit-template, 04-architecture/instrument-universe-registry-consolidation,
  02-data/honest-absence-downstream-handling, 02-data/mtds-data-source-coverage-matrix,
  02-data/service-output-emission-semantics, 09-strategy/architecture-v2/instruments-resolver-architecture,
  02-data/defi-canonical-naming-ssot, 02-data/partitioning, 02-data/availability-manifest-and-data-status,
  06-coding-standards/quality-gates, plus audit-instruction siblings.

  Verified-real examples: partitioning.md line 51 and availability-manifest-and-data-status.md line 1140 (both say "data
  types" in prose with the underscore rewritten as an asterisk); quality-gates.md line 185 (the enum-member underscore
  prefixes for LIVE and BATCH rewritten as asterisk / escaped-underscore). Meta-note: the first draft of THIS paragraph
  was itself mangled by prettier on save (defect 2) — it originally quoted the fragile tokens literally; it now
  describes them instead.

## Todos

- [x] ✅ [SCRIPT] P1. Codex repair wave — DONE unified-trading-pm@f54f0e9d6 (operator ruled option A in chat,
      2026-07-14: "yeah repair it"). 17 spots / 13 codex docs mechanically de-mangled + backticked, every file two-pass
      prettier-stable. (was: BLOCKED-OPERATOR-DECISION) — codex repair wave. The 13 codex docs above carry verified
      mangling in normative SSOT text. Options: (A, RECOMMENDED) approve a mechanical repair wave using the proven
      recipe (reference commits 169a8c8cd/65420c363, per-hit false-positive verification, two-pass idempotence proof),
      one commit, operator spot-review of the diff; (B) operator repairs by hand; (C) leave as-is (mangled SSOT text
      keeps misleading readers and re-propagating into plans via copy-paste). Codex edits require an explicit operator
      ruling per the plan-reconcile HARD GATE — do not execute without it.
- [x] ✅ [SCRIPT] P2. Gate hardening — DONE (this commit): `scripts/plan-hygiene/check_prettier_mangling.sh` (curated
      signature, fenced-block + inline-code-span stripping so quoting docs and genuine backticked wildcards never
      self-flag) wired into the plan-hygiene gate at all three paths: precommit staged-plans, precommit staged-codex,
      and the full-sweep hard checks. Home is plan-hygiene (not scripts/quality*gates/) because that gate already runs
      on exactly the staged plans/codex slice. First corpus run found + fixed 9 further `asset*group` mangles the
      original `=`-anchored scan pattern had missed. (was:) add the detection signature (narrow, low-false-positive
      form: `\{mode\}\*\{source\}|asset\*group=|schema\*version|[a-z]\*[a-z*]+ <     v9`) as a PM quality-gate / prek
      check on staged `.md`files so newly mangled text is rejected at commit time instead of accumulating. Home:
      `scripts/quality_gates/`per script-homes SSOT; wire into the PM`quality-gates.sh`.
- [x] ✅ [SCRIPT] P3. Prettier-level fix — RESOLVED (this commit): head-to-head repro proves prettier 3.9.5 does NOT
      mangle (3.8.4 mangles the same input; 3.9.5 output byte-correct incl. the split-code-span and repeated-wildcard
      triggers). Fix shipped as a `PRETTIER_MIN_VERSION=3.9.5` guard in `scripts/hooks/prettier-autostage.sh`: a
      resolved binary <3.9.5 is never used — pinned `npx -y     prettier@3.9.5` preferred, else the format pass is
      SKIPPED (skipped format recoverable, corruption not). Global prettier upgraded to 3.9.5 on this host; the guard
      propagates fleet-wide via the standardized prek hook install (PM@583b01b83, Harsh 2026-07-14). (was:) pin/bump the
      prettier version and minimally repro defect 2 upstream (very-long list-item paragraph with many code spans); if an
      upstream issue exists, link it here; if a config mitigation exists (e.g. `proseWrap`), evaluate against the repo's
      md conventions.

## Additional findings from the repair waves (2026-07-14)

- **Third trigger confirmed** (batch 01, ~15 isolated repros): a bare underscore identifier co-occurring in the same
  paragraph with ANY asterisk — a literal `*`, a proper italic span, or a code span containing `*` — re-mangles on the
  next format pass even in freshly repaired, backtick-clean text. Backticking the bare identifier sufficed in every case
  tested.
- **Config pin-down** (batch 02): prettier 3.8.4 with this repo's `proseWrap: always` is the combination that makes bare
  underscore identifiers unsafe; the reflow step is what re-triggers the desync.
- **Detection-regex gap** (batch 03): the original lowercase-only signature missed uppercase manglings (e.g. the
  VOL/MARKET_MAKING family, AUTONOMOUS AGENT RULES refs) — sweeps must be case-insensitive / uppercase-aware.
- **Structural damage class** (batch 04): beyond prose, a 4-row markdown table in the MTDS/MDPS epic was shattered
  across ~15 physical lines by the same parser desync (rows rendered as broken plain text); repaired by rejoining rows.
- **Repair-without-stabilize is futile** (orchestrator's own failed quick-fix on the final 2 files): restoring text and
  even backticking the target token gets re-mangled on the next `--write` if sibling bare underscore tokens remain in
  the paragraph — the WHOLE paragraph must be stabilized.
- **Fourth trigger** (final-residuals fixer @e1b983b90, minimal repro): a paragraph with 2+ occurrences of the SAME
  underscore-plus-asterisk wildcard token (e.g. two mentions of the DP event-family glob) re-corrupts on every `--write`
  even when each occurrence is individually backticked and the paragraph is short. Stable fix: the escaped-bare form
  (backslash-underscore backslash-asterisk, no backticks) for repeated tokens in one paragraph.
- **Version nuance**: the pre-commit hook resolves the GLOBAL prettier binary (3.8.4), not the npx-latest (3.9.5); the
  versions differ materially in paragraph-continuation-indentation stability — verify repairs against the binary the
  hook actually runs.

## Progress Log (append-only)

- 2026-07-14: issue filed during verify-rerun-2 close-out. Root causes proven + reference repairs shipped (@169a8c8cd
  single doc, @65420c363 six propagated docs incl. the defect-2 discovery). Corpus scan complete; 5 parallel repair
  batches over ~31 plans docs dispatched. Codex subset parked pending operator ruling (todo 1).
- 2026-07-14 (repair waves landed): batch 00 @6118a3258 (6 files), batch 01 @61bf72297 (5 files, 27 mangles, third
  trigger discovered), batch 02 @6ad39dc29 (5 files, ~42 spots, proseWrap pin-down), batch 03 @d87565728 (7 files, ~62
  spots, uppercase-gap + embedded-backtick cascade), batch 04 @9a914087d (8 files, table-structure repair). Residual
  sweep then found 2 more infested files the narrow signature missed (`tradfi_multisource_backfill_2026_06_22.md`,
  `data_pipeline_hardening_self_monitoring_2026_06_22.md` — ~20 further spots incl. the DP-underscore event-family
  refs); dedicated fixer dispatched. Known unresolved residual: `master_data_canonicalisation_migration_catalogue` line
  ~1488 truncated value (needs domain verification, not a mechanical repair). The corpus long tail beyond the detection
  signature is expected — the P2 gate-hardening todo is the durable stop.
- 2026-07-14 (RESOLVED): operator ruled "yeah repair it [codex] but also how do we make it so it doesn't happen again".
  Codex repaired @f54f0e9d6 (17 spots / 13 docs). Prevention shipped: (1) root cause — head-to-head repro proved
  prettier 3.9.5 fixed the bug upstream, so prettier-autostage.sh gained a PRETTIER_MIN_VERSION=3.9.5 guard (never
  formats with an older binary; pinned npx fallback; skip-with-warning as last resort) and this host's global prettier
  was upgraded; (2) backstop — check_prettier_mangling.sh added to the plan-hygiene gate (precommit staged plans +
  staged codex + full sweep), which immediately caught 9 further mangled asset-group tokens missed by every earlier
  sweep (fixed same commit; the gate sees mangled tokens in bare prose, so this Progress Log deliberately writes the
  token as asset-group rather than quoting the mangled form literally — quoting it would self-flag). Corpus verified
  clean: 1,459 files. Fleet propagation rides the standardized prek hook install (@583b01b83).
