---
doc_type: plan
title: AO satellite AO batch 16 — token-expiry early-warning for the git-health reporter (infrastructure_master epic)
summary: >-
  SIXTEENTH AO-dispatch batch for the `ao` topic tranche — a round11 `/na-eligibility-audit ao` re-sweep (2026-08-09)
  single-item satellite extraction from `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`. That doc's
  own P2 "Stop the 30-day treadmill for off-VM hosts" item was carried KEEP-NA by 5+ prior na-eligibility-audit passes
  under a generic "operator-gated, design-judgment" boilerplate marker, but a full re-read found the doc's own text
  already resolves the design fork explicitly in favor of option (a) ("(a) is the smallest and needs no new credential
  surface") with a concrete, worker-determinable done-when (emit one warning per state-transition into the AO activity
  feed per the existing alerting SSOT once the reporter's own already-decoded JWT reads within ~3 days of `exp`). Split
  into its own batch (rather than folded into an existing batch) because its source doc's `parent_epic` is
  `infrastructure_master`, distinct from every other currently-open `ao`-tranche batch's
  `orchestrator_master`/`agent_operating_framework_master` grouping — per the naming-and-conflict-check SSOT's
  `parent_epic`-is-the-grouping-axis rule (batch11/13 precedent). The doc's sole OTHER open item (P3, prune/tombstone
  ghost fleet-git-health host rows) stays genuinely NA — it asks the worker to "decide which" of two disposal
  strategies, a real design call the source doc itself never resolves.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-16, satellite-docs, satellite-extraction, git-health]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch16_finalize_2026_08_09.md,
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    scripts/dev/slot-git-status-report.sh,
    scripts/dev/remint-orch-token.sh,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
source: >-
  `/na-eligibility-audit ao` round11 re-sweep, 2026-08-09 (satellite-extraction gap check over docs that already carry a
  KEEP-NA marker but were never re-checked for extraction eligibility against the full precedent set accumulated since).
  Conflict-check: grepped every `status: draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-15) and their finalizes,
  `ao_open_issues_consolidated_close_out_2026_07_17.md`, and the `na_docs_validity_and_ao_
  eligibility_audit_2026_07_26.md` tracker for `slot-git-status-report`/`remint-orch-token`/"30-day treadmill" — zero
  hits. The source doc IS cited by `ao_satellite_ao_dispatch_batch2_2026_07_30.md`/its finalize, but only for 2
  DIFFERENT, already-`[x]`-closed items (the loopback fix + the `hk` token re-mint) — that citation is why the
  2026-08-09 `/ag-closeout-audit ao` batch12 run's citation-based pre-filter excluded this doc from its fresh 36-doc
  scan entirely, without re-checking whether the CURRENT 2 remaining open items are actually covered. They are not.
---

# AO satellite AO batch 16

> **`status: active`** — operator-approved, sole todo shipped (`unified-trading-pm@b427499b33`).
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`**, same as the rest of this series.

## Why this plan exists

`git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` carries 2 open `[INFRA]` items. Six prior
na-eligibility-audit passes (2026-07-30 through 2026-08-06) each carried it forward as KEEP-NA under a generic
"operator-gated, design-judgment, or standing-corpus-ruling work remains open" boilerplate marker — none of them quoted
the actual todo text or checked whether a design fork the doc names was already resolved by the doc's own prose. A full
re-read this round found:

- The **P2 item** ("Stop the 30-day treadmill for off-VM hosts") lists 3 options `(a)/(b)/(c)` but then states plainly
  **"(a) is the smallest and needs no new credential surface"** — a self-resolved preference, not an open fork — and
  gives a concrete mechanism: the reporter script already decodes the bearer JWT (used today only to read `exp` for the
  treadmill diagnosis itself); extend that same decode to fire ONE warning per state-transition into the AO activity
  feed, per the existing state-transition-dedup convention `/codex/04-architecture/agent-orchestrator-alerting.md`
  already documents for every other standing-condition alert in this codebase, once the token is within ~3 days of
  expiry. No credential/design ambiguity remains — this is bounded, worker-determinable work. Extracted below.
- The **P3 item** ("Ghost host rows") explicitly asks the worker to "decide which" of prune-vs-tombstone the fleet
  git-health view should apply to a host with no live instance — a real, unresolved design call the doc's own text never
  picks a side on (unlike the P2 item). Stays NA.

## Rules for every worker on this plan

- Do not edit the source doc's remaining checkbox beyond appending your evidence when done — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch16_finalize_2026_08_09.md`) reconciles evidence back into the source
  doc.
- This is a **fleet-observability alert**, not a live-dispatch-critical-path change (it only ADDS a warning event; it
  does not touch `/boot`/`/done`/backlog-regen/task-id derivation) — the standing "live-dispatch-critical-path stays
  local-only" caution seen elsewhere in this tranche does not apply here.

## Todos

- [x] ✅ [INFRA] P2. **Add a token-near-expiry early warning to `slot-git-status-report.sh` (option (a), the doc's own
      stated preference).** The reporter already decodes the bearer JWT (used for the treadmill diagnosis in the source
      doc's own evidence trail — the `exp` claim is already being read). Add: if `exp` is within ~3 days of the current
      time, emit ONE warning event per state-transition (i.e. dedup so it doesn't refire every ~5-min cron tick while
      still-near-expiry) into the AO activity feed, per `/codex/04-architecture/agent-orchestrator-alerting.md`'s
      standing-condition state-transition-dedup convention (fire on transition into the near-expiry state / RESOLVED on
      re-mint, never every tick). Do **NOT** raise the token TTL (the source doc explicitly rules this out — it just
      delays and worsens the eventual outage). **Done when**: a test harness with a JWT `exp` set ~2 days out fires
      exactly one warning event; a second consecutive run with the same `exp` does not re-fire; a run after
      `remint-orch-token.sh` resets `exp` clears the near-expiry state (either an explicit RESOLVED event or the state
      naturally not re-firing). Source:
      `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md:140` (its `[INFRA] P2` item
      — the sole remaining unclaimed AO-eligible item). Repo: unified-trading-pm. **Evidence**:
      unified-trading-pm@b427499b33 — `scripts/dev/slot-git-status-report.sh` decodes the reporter's bearer JWT `exp`
      claim and fires one state-transition-dedup warning into the AO activity feed within `TOKEN_EXPIRY_WARN_DAYS`
      (default 3) of expiry, clearing on re-mint; TTL unchanged; `tests/test_slot_git_status_token_expiry.bats` covers
      fire-once / no-refire / clear-on-remint.

## Codex SSOTs (read before starting)

`/codex/04-architecture/agent-orchestrator-alerting.md` (state-transition-dedup convention),
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09 (round11 na-eligibility-audit satellite-extraction gap check)** — Authored after a per-doc re-read of 22
  `ao`-tranche docs that each already carried a KEEP-NA marker but had never been re-checked for RECLASSIFY/ extraction
  eligibility against the accumulated round7-10 precedent set. 21 of the 22 confirmed genuinely KEEP-NA on re-read
  (design forks, standing operator rulings, live-dispatch-critical-path exclusions, or already covered by an active plan
  — several independently cross-validated against the SAME-DAY 2026-08-09 `/ag-closeout-audit ao` batch12 run's fresh
  36-doc classification). This doc's P2 item was the one genuine gap: its own text already resolves the design fork it
  appears to pose, and its citation by an EARLIER batch (batch2, for different, already-closed items) caused batch12's
  citation-based pre-filter to skip re-examining it. Conflict-check run against all `status: draft`/`active` batch1-15 +
  finalizes + the consolidated close-out + the na_docs_validity tracker — zero hits for this specific item.
  File-disjoint by construction (single todo, single file).
- **context-scout 2026-08-15**: populated/refreshed context_scope (4 entries).
