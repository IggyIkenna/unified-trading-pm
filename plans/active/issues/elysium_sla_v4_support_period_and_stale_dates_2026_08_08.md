---
doc_type: issue
title: >-
  ODUM_SLA_v4 — binding 60-day support period contradicts the 30 days stated in every client-facing summary, plus stale
  June-2026 dates
summary: >-
  Reconciliation of the Elysium client pack (2026-08-08) found two defects in `ODUM_SLA_v4_2026-07-24.md`, the version
  sent to the client as `ODUM_Production_Operations_and_SLA.docx`. (1) SUPPORT PERIOD — binding §3 defines the Initial
  Support Period as "sixty (60) calendar days" and §5's heading reads "DAYS 1-60", but §2 line 88 refers to "the two
  post-30-day continuation options", the docx executive summary states "Initial Support | 30 days", and both the
  2026-07-20 delay letter and the 2026-08-08 follow-up promise "a complimentary 30-day post-launch monitoring period".
  The docx exec summary carries an express "substantive provisions prevail" clause, so on the current drafting the
  client is contractually entitled to 60 days while being told 30. (2) STALE DATES — a document dated 2026-07-24 still
  states Phase-2 acceptance occurs "on or around June 2026" (§2), Exhibit C custody integrations are "scheduled for June
  2026" (§3, Exhibit C), pre-cutover testing runs "through and including May 2026" (§3), and client seed capital arrives
  "from 30 June 2026 onwards" (§3) — all overtaken by the September-readiness / October-acceptance timeline in the very
  letter this SLA accompanied.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, sla, contract, client-communication, operator-gated]
related:
  [
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/elysium-delay-letter-2026-07-20.md,
    /codex/14-customer-journeys/commercial-model/elysium-remaining-work-appendix-2026-07-24.md,
  ]
created: 2026-08-08
author: interactive-session (slot 2)
last_updated: "2026-08-09"
parent_epic: client_isolation_and_governance_master
priority: P1
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role:
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  interactive session, 2026-08-08 Elysium client-pack reconciliation. Never committed — sat as an uncommitted new file
  in a `.tabs/2` working tree, swept into a protective `foreign-wip-elysium-not-mine-preserved-during-quickmerge-3`
  autostash during a concurrent quickmerge, and undiscovered until a 2026-08-09 fresh stash-pile re-audit found and
  recovered it (content independently re-verified against the live codex docs as still accurate/unchanged before
  filing).
---

# Elysium SLA v4 — support-period contradiction + stale dates

Found during the 2026-08-08 reconciliation of the Elysium client pack against the PM repo record, while checking whether
the two `.docx` attachments sent to the client matched their codex counterparts.

## Finding 1 — 30 vs 60 day Initial Support Period (**material, contract term**)

| Location                                                     | States      |
| ------------------------------------------------------------ | ----------- |
| `ODUM_SLA_v4_2026-07-24.md` §3, line 131 (**binding**)       | **60 days** |
| `ODUM_SLA_v4_2026-07-24.md` §5 heading, line 220             | **60 days** |
| `ODUM_SLA_v4_2026-07-24.md` §2, line 88                      | **30 days** |
| `ODUM_Production_Operations_and_SLA.docx` executive summary  | **30 days** |
| Delay letter 2026-07-20 (sent), Main points + CEFFU sections | **30 days** |
| Follow-up email 2026-08-08                                   | **30 days** |

The docx executive summary states: _"This executive summary is provided for convenience only. In the event of any
inconsistency, the substantive provisions of the Agreement prevail."_ On the current drafting the substantive provision
is **60 days**, so the client's contractual entitlement is double what every client-facing summary has promised. The
exposure runs in the client's favour, which is why it has not surfaced — but it is a live inconsistency in a document
already in the client's hands.

**Decision required (operator, not dispatchable):** is 60 the intent and every summary wrong, or is 30 the intent and
§3 + §5 wrong? Do not "fix" this by silently editing either number — the document has been sent.

## Finding 2 — stale dates in a doc dated 2026-07-24

| Line | Text                                                                 |
| ---- | -------------------------------------------------------------------- |
| 119  | Phase-2 production acceptance "occurring on or around **June 2026**" |
| 142  | Exhibit C custody integrations "scheduled for **June 2026**"         |
| 145  | Pre-cutover testing "through and including **May 2026**"             |
| 149  | Client seed capital "provided **from 30 June 2026 onwards**"         |
| 1192 | Integration services delivered "in or around **June 2026**"          |

All are superseded by the September-readiness / October-acceptance timeline stated in the delay letter this SLA was
attached to. §3's capital-and-timing paragraph is the most exposed: it asserts pre-cutover testing "is expected to be
complete" by 30 June 2026, which did not happen.

## Todos

- [x] ✅ [OPERATOR] P1. **RULED 2026-08-09 (operator, interactive): 60 calendar days is the correct Initial Support
      Period** — §3 (line 131, binding) and §5's heading (line 220) were right; §2 (line 88) and the docx executive
      summary were wrong. Fixed the internal codex-record inconsistency: `ODUM_SLA_v4_2026-07-24.md`:88 now reads
      "post-60-day continuation options" (was "post-30-day"), matching §3/§5. **This does NOT correct what's already in
      the client's hands** — the docx executive summary (30 days) and both sent delay-letter/follow-up communications
      (30 days) are unchanged; the client has been told a shorter support window than they're actually entitled to. That
      correction is todo 2 below (reissue vs. side letter) — ruled on the internal record only, not on how/whether to
      notify the client of the discrepancy.
- [ ] [OPERATOR] P1. Decide how to correct the five stale June/May-2026 dates given the SLA has been sent: reissue as v5
      with the September/October timeline, or handle by side letter.
- [ ] [OPERATOR] P2. Confirm the actual send date of the delay letter. The codex record is dated 2026-07-20, but both
      attachments carry mtime 2026-07-29 18:56, and the sent copy opens "Following the quick WhatsApp massager the other
      day" — wording absent from the 2026-07-20 draft. If the real send was ~29 July, rename/redate the codex record.
- [ ] [AGENT] P3. Typo in the sent letter recorded verbatim in the codex record: "WhatsApp massager" (should be
      "message"). Recorded as-sent deliberately, since that doc is `authoritative_for` exact wording. Correct in any
      future reissue only.

## Progress Log

- **2026-08-08** — Found during Elysium client-pack reconciliation. Both `.docx` attachments in `~/Downloads` extracted
  and compared against codex. SLA body matched (8,136 docx words vs 8,369 md words; delta is the exec summary the docx
  adds and markdown syntax). Commercial terms verified identical: \$3,000/mo retainer, 25% first \$100M AUM / 10%
  thereafter, \$2,500 per additional venue, \$2,500 per additional LST. The remaining-work appendix did **not** match
  and has been corrected under separate change; this issue covers the SLA only.
- **2026-08-09 (recovered)** — This doc was drafted 2026-08-08 but never committed; a concurrent `quickmerge` swept it
  into a protective autostash (`stash@{8}`, tagged `foreign-wip-elysium-not-mine-preserved-during-quickmerge-3`) in a
  `.tabs/2` checkout, where it sat undiscovered for a day. Found and recovered by a fresh stash-pile re-audit
  (dispatched as part of a broader operator-queue cleanup session); both findings independently re-verified against the
  live `codex/14-customer-journeys/commercial-model/` docs before filing — still accurate, unchanged since 2026-08-08.
  Filed now rather than left in the stash pile.
