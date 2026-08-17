---
doc_type: record
title: "Extracted Progress Log history — elysium_october_delivery_and_code_disclosure_readiness (2026-08-15 line-cap remediation)"
summary: >-
  Verbatim extraction of Progress Log entries (2026-08-11 through 2026-08-12, all passes) from the Elysium October
  delivery plan — pure historical session narration, superseded by that plan's own "State as of 2026-08-13" section
  and its later Progress Log entries; no open todo lives in the extracted text. Extracted to keep the live plan
  under the workspace's 1000-line hard cap, per this issue's established extraction pattern. Extended 2026-08-17
  (plan_reconciler, defi tranche) with 3 more entries (measurement lesson, fourth pass, third pass) after the live
  plan crept back to 1001L via later-appended entries.
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [line-cap-remediation, historical, elysium, progress-log]
created: "2026-08-15"
author: slot-16
parent_epic: client_isolation_and_governance_master
source:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
---

# Extracted — Progress Log history (2026-08-11 → 2026-08-12 "second pass")

> **Extracted verbatim 2026-08-15** → this file (line-cap remediation,
> `/plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` Follow-up todo) — the three
> oldest Progress Log entries from
> [elysium_october_delivery_and_code_disclosure_readiness](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md),
> superseded by that plan's own "State as of 2026-08-13" section and its later Progress Log entries. No open todo lives
> in this extracted text — it is pure session narration. The live plan retains a one-line pointer at the end of its
> Progress Log section.

## Progress Log (extracted, verbatim)

> **Extended 2026-08-17** (plan_reconciler, defi tranche) — 3 more entries below (measurement lesson, fourth pass,
> third pass), same extraction rationale, moved after the live plan crept back to 1001L (2 entries appended after
> the 2026-08-15 extraction). Order preserved from the live doc (its own newest-first convention).

- **2026-08-12 — measurement lesson, recorded because it is the SECOND proxy-vs-property slip in one session.** I ran
  `bash scripts/quality-gates.sh --no-fix 2>&1 | tail -45` in the background, was notified "exit code 0", and reported
  the gate green. **That 0 was `tail`'s exit code, not the gate's** — a shell pipeline reports its LAST command's
  status, so piping a gate through `tail`/`grep`/`head` discards the verdict and replaces it with "did the pager run".
  The output file was exactly 45 lines, which is the tell. Compounding it, the visible tail showed only a
  peripheral-directory ruff warning, which read as "nearly clean" when in fact the summary had been cut off. **Rule:
  never pipe a gate. Redirect the full log to a file and capture `$?` on its own line**
  (`bash scripts/quality-gates.sh > "$LOG" 2>&1; echo "EXIT=$?"`), then read the log. Same shape as the
  `check_reference_paths` false negative earlier the same day — exit 0 from something that never did the work — which is
  why this is worth writing down rather than filing as a one-off slip.
- **2026-08-12 (fourth pass — codex ↔ code reconciliation)** — Operator asked for the remaining fixes plus a
  reconciliation of codex and strategy-service docs. **The root cause of my own H.5 blind spot turned out to be a
  documentation defect, not my search technique: the codex allocator SSOT and the code docstring both said "8 allocator
  archetypes" against a registry of 17, and they corroborated each other.** A false consensus between doc and code is
  far more dangerous than either being wrong alone, because cross-checking one against the other confirms the error.
  Fixed in all four locations, including an `authoritative_for:` frontmatter facet that asserted authority over the
  wrong count. Roster de-duplicated so two codex docs no longer maintain parallel tables — that duplication is what let
  both drift to the same wrong number. Wrote the missing `CARRY_FUNDING_DISPERSION` archetype doc (implemented and
  registered, zero codex entry) after reconciling all 60 enum members against doc slugs; corrected four stale counts and
  a never-existent `templates/archetype-doc.md` link in the architecture-v2 README, replacing counts with the command
  that derives them. Two archetypes remain undocumented and are now named in the README's own gap table rather than
  hidden behind an "all archetypes documented" claim that was false. **Refinement to yesterday's ADV tick:** the dynamic
  ADV universe is real but `enable_dynamic_carry_universe` defaults **False**, so "ADV-filtered" describes the
  capability and not the running default — now an operator decision. **Counter-finding worth keeping:** the client
  documents' "26 repositories" is right and the naive recount (31 `.git` dirs) is wrong — five are history-rewrite
  backup clones sharing a remote. Recorded in the authoring notes with the distinct-remote command, because the next
  person to measure will otherwise "correct" a correct number.
- **2026-08-12 (third pass)** — **H.5 audited; all four operator asks were already built.** Composite composition is
  architecture (a) and the allocator composes on two levels (across instances via `target_weights` + family/category
  guard rails, within an axis via the 2-stage hierarchical rank engines) — so H.3 keying can proceed and **no
  composite-archetype concept should be built**. Collateral-driven selection gates slot EMISSION, which is stronger than
  runtime switching, and already encodes the stETH/wstETH per-venue nuance in a reasoned denylist. ADV filters exist and
  are wired. The dispersion basket is complete and two-sided. Two findings raised to H.7 (SOL staked-basis has zero
  eligible pairs; the allocator docstring undercounts its registry). **Three published-document corrections, all of the
  same class — an asserted total that rotted:** the carry-archetype count was 6 and is 7 (the missed one is
  `CARRY_FUNDING_DISPERSION`, i.e. the number was wrong _because_ the dispersion capability was unknown); "liquidity
  provision" was listed as a `StrategyFamily` in `carveout-engineering.html` and in the deferral record, having been
  fixed in the deep dive a day earlier and missed in the other two. **And a correction to my own correction**: I had
  recorded that family as "invented", which is wrong — `DEFI_LP_CONCENTRATED`/`_POOL`/`_VAULT` are real archetypes, so
  liquidity provision is a genuine capability that was merely misfiled as a family. Recording an error's shape
  imprecisely is as costly as the error, because the record is what the next reader acts on. Counts have been removed
  rather than corrected wherever the argument did not need them.

- **2026-08-12 (second pass)** — Recorded four un-audited operator asks in H.5: composite-strategy modelling (which
  gates H.3), collateral-driven archetype selection, rotation volume/ADV filter coverage, and the dispersion basket.
  **Sections H and H.5 were blocked for seven `safe-doc-push` attempts by a single `check_reference_paths --only`
  violation, and the diagnosis was wrong for all seven.** Root cause, measured: line 371 of this file carried a **bare**
  `codex/...` reference (missing the leading slash) — a FORMAT violation, not the hypothesised dangling-at-origin
  existence violation. Two things hid it, and both are now recorded as gate findings in H.6: `run_hygiene_sweep.sh`
  invokes the checker with `--quiet`, which prints the violation **count without the filename**; and `_run_only()`
  **silently `continue`s past any path it cannot stat, then reports 0 violations and exit 0** — so the "same checker
  returns 0 locally" evidence that anchored six wrong guesses was a false negative produced by running it from the wrong
  working directory. The lesson is the one already in the rules: after two identical consecutive failures, stop guessing
  and get the actual identifier — a throwaway worktree at `origin/<branch>` plus the checker run **without** `--quiet`
  named the reference in one shot.
- **2026-08-12** — Investigation outcomes recorded in section H. **Corrected my own earlier over-call**: the "four
  duplicate `TransferStatus`/`TransferResult` declarations" are actually **three legitimate layers plus one deliberate
  mirror** — a bus contract, an on-chain observation schema and an adapter-level result, which merely share a name.
  `canonical/crosscutting/transfer_events.py` is already the self-declared SSOT, so the manual route belongs there
  rather than in anything new. The genuine debts are the `BusTransferType` vs `TransferType` value overlap (acknowledged
  in the file's own docstring) and the hand-synced fund-admin mirror, which exists to respect the no-service-imports
  tier rule and must not simply be deleted. Confirmed the operator's recollection that treasury/client prior art exists:
  `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` and
  `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md` are both written and must be read before
  any keying change. ⚠️ **The rail-enum sentence that follows is WRONG — corrected in H.11, kept here so the error is
  traceable rather than silently rewritten.** Measured the manual gap precisely: the rail enum has three members, all
  API-executed, so a bookmaker deposit is unrepresentable; and `ApprovalBus` provides approval of a system-executed
  transfer, which is the inverse of the manual case. Added manual **trade** capture alongside manual transfers, since
  betting venues will be hand-operated at first and the fills must still book canonically.
- **2026-08-11** — Rewritten as a **claims audit** on operator instruction: no new repository build, full audit of
  everything missing, every fix in line with the existing architecture. Twenty-three load-bearing document claims were
  checked against the tree: **17 verified in source, 1 partial, 2 unverified, 1 false, 2 already-wrong-and-now-fixed.**
  The two wrong ones were in a document already published, and both are corrected — the family count was 8 where the
  enum has **9** members and the list invented "liquidity provision"; and "compliance attestation on every instruction"
  is untrue for the contracted archetypes, since only the MEV modules populate the field. The unverified claims are now
  todos rather than assumptions: capital-budget enforcement, and the backtest launch endpoint (inferred from test
  _filenames_, which is a proxy for an endpoint, not evidence of one). Production gaps carried from reading the tree:
  **stub transfer handlers labelled "for May-23"** — the highest risk, because a stub returning success on a funds path
  reports money moved that did not move — the never-built `CustodyRoute` matrix, **placeholder risk thresholds in the
  client's own strategy config**, and a test-only funding reader. Separately found and fixed: the codex move left **four
  stale duplicate copies** of client documents live on origin, because `safe-doc-push` commits named files from an
  isolated worktree and therefore never saw the deletions.
