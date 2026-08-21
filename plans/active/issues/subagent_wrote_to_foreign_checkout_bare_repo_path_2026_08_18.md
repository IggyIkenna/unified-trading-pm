---
doc_type: issue
title: Sub-agent given an absolute slot path wrote to a different operator's checkout instead
summary: >-
  A dispatched sub-agent was given the absolute path
  `/Users/.../unified-trading-system-repos/.tabs/6/unified-trading-pm/codex/.../strategy-service-walkthrough.html`
  and instead edited the same relative path under the BARE `unified-trading-system-repos/unified-trading-pm/`
  clone — a real, live checkout on live-defi-rollout belonging to another operator, which was carrying five
  unrelated dirty files at the time. No work was lost and nothing of the peer's was committed, but the peer's
  working tree was left dirty with edits it did not make, and the recovery depended on the orchestrating session
  noticing the path in the agent's own report.
status: open
nature: record
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, sub-agent, slot-discipline, worktrees, near-miss]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Observed live 2026-08-18 during the client-artefact remediation, interactive session in slot 6.
drift_direction: advance-code
depends_on: []
---

# Sub-agent wrote to a foreign checkout despite being given an absolute slot path

## What happened

Two sub-agents were dispatched to edit one client artefact each. Both prompts named the target with a **fully
absolute path** under `.tabs/6/`. The Nick AI agent honoured it. The Elysium agent reported, in its own summary,
that it had edited:

```
/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/codex/.../strategy-service-walkthrough.html
```

— the bare-repo path, not `.tabs/6/`. Measured immediately after: that bare path is a real clone on
`live-defi-rollout` carrying **five unrelated dirty files**, i.e. another operator's live working tree. Slot 6's own
copy was untouched and byte-identical to origin.

The same agent also reported that its assigned plan "does not exist in this slot's checkout (slot 6); it exists in
`.tabs/2/unified-trading-pm/`" — which was false (the plan had just been pushed and was present in slot 6). So the
agent was resolving paths across at least three checkouts and reasoning about "this slot" incorrectly.

## Why it was recoverable, and why that is not reassuring

Recovery worked only because the agent volunteered the path in its report and the orchestrating session read it.
The content itself was verified as purely the agent's own work (diff size and every claimed edit matched, with the
shared base confirmed identical to origin), then copied into slot 6 and shipped from there with only that one file
staged — `unified-trading-pm@171dc40739`. The peer's other five dirty files were never touched.

**Residual risk that could not be eliminated**: if that checkout's owner had their own uncommitted edits to that
same file before the agent ran, those were imported. The evidence says otherwise but this is an inference, not a
measurement. The peer's tree was also left dirty with the agent's version, so a `git add .` there would commit
content that has already landed.

Had the agent not named the path, the edits would simply have been invisible — the orchestrating session would have
found slot 6 clean and concluded the agent did nothing.

## Todos

- [x] N. ✅ [DOC] P1. **Harden the sub-agent rule** — done as a one-line clause in
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` ("write ONLY under the absolute path your task names; a bare
      `<repo>/` path is ANOTHER operator's live checkout; `realpath` your target before the first write.") —
      unified-trading-pm@34ebb7e5f. Verified live 2026-08-19: clause is present verbatim in the file; file measures
      9893 bytes, under its 10 KB QG-enforced cap.
- [ ] [SCRIPT] P2. **Consider a mechanical guard**: a sub-agent whose task names a `.tabs/<N>/` path should fail
      loudly on a write outside that subtree. Prompt discipline alone did not hold here — the prompt was correct and
      unambiguous, and the agent still resolved elsewhere. Weigh against the cost of wrapping every sub-agent write.
- [x] N. ✅ [REVIEW] P2. **Check whether other recent sub-agent work landed in the bare checkout** rather than a slot.
      This was caught by chance; the same failure in a session that did not read the agent's path would look like a
      no-op. A sweep of the bare clone's dirty files against recent sub-agent tasks would size the problem. —
      extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 1 (na-eligibility-audit
      2026-08-19, ao tranche, RECLASSIFY per-todo split — this item is bounded/deterministic, the sibling items above
      are not).

## Progress Log

**2026-08-18 — filed.** Content recovered and shipped from slot 6 (`unified-trading-pm@171dc40739`); the peer's
checkout was deliberately left alone rather than cleaned, per the hard rule against touching a live peer's dirty
working tree.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:4a9dbc02450782c8]: KEEP-NA-STALE (items closed) — todo 1 (harden SUB_AGENT_MANDATORY_RULES.md) verified done: unified-trading-pm@34ebb7e5f, clause confirmed present, file 9893 bytes < 10KB cap. Todo 3 (bounded, GENUINE_WORK) extracted to plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md item 1 (RECLASSIFY per-todo split). Todo 2 (mechanical guard) stays NA — explicit judgment/cost tradeoff, no determinable outcome.
- **context-scout 2026-08-19**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — sole open item (`[SCRIPT] P2`,
  consider a mechanical guard wrapping every sub-agent write) remains an explicit judgment/cost-tradeoff call with
  no determinable outcome, re-affirming the 2026-08-19 verdict.
