---
doc_type: record
title: "Extracted Progress Log history — elysium_october_delivery_and_code_disclosure_readiness (2026-08-15 line-cap remediation)"
summary: >-
  Verbatim extraction of the three oldest Progress Log entries (2026-08-11 through 2026-08-12 "second pass") from the
  Elysium October delivery plan — pure historical session narration, superseded by that plan's own "State as of
  2026-08-13" section and its later Progress Log entries; no open todo lives in the extracted text. Extracted to keep
  the live plan under the workspace's 1000-line hard cap, per this issue's established extraction pattern.
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
    /plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
---

# Extracted — Progress Log history (2026-08-11 → 2026-08-12 "second pass")

> **Extracted verbatim 2026-08-15** → this file (line-cap remediation,
> `/plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` Follow-up todo) — the three
> oldest Progress Log entries from
> [elysium_october_delivery_and_code_disclosure_readiness](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md),
> superseded by that plan's own "State as of 2026-08-13" section and its later Progress Log entries. No open todo lives
> in this extracted text — it is pure session narration. The live plan retains a one-line pointer at the end of its
> Progress Log section.

## Progress Log (extracted, verbatim)

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
