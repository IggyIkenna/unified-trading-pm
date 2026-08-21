---
doc_type: issue
title: sports P2 exchange_odds/fixed_odds purge (59,310 GCS objects) lacks a recorded same-run §3a retention-check citation
summary: >-
  The largest single GCS object-delete in sports_taxonomy_p2_migration_2026_08_08.md — the exchange_odds/fixed_odds
  P0 purge's 59,310-object `migrate --confirm` run — never had its §3a fresh, same-run
  gcs_bucket_soft_delete_retention_seconds() value recorded in the plan's Progress Log, unlike every sibling delete
  in the same plan. Independent post-write VERIFY already confirmed the delete's outcome is data-safe; this is a
  protocol-documentation gap, not a live incident.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, delete-safety, protocol-3a, retroactive-audit, finalize]
related:
  - /plans/active/sports_taxonomy_p2_migration_2026_08_08.md
  - /plans/active/sports_taxonomy_p2_migration_2026_08_08_finalize.md
  - /codex/02-data/gcs-and-manifest-delete-safety-protocol.md
created: "2026-08-21"
parent_epic: sports_master
assigned_vm: NA
priority: P3
source: [sports_taxonomy_p2_migration_2026_08_08_finalize.md item 3]
author: slot-10 (review, finalize audit)
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  - /plans/active/sports_taxonomy_p2_migration_2026_08_08.md
  - /codex/02-data/gcs-and-manifest-delete-safety-protocol.md
---

# sports P2 exchange_odds/fixed_odds purge lacks a recorded same-run §3a retention-check citation

## What I found

While running the sports P2 finalize plan's item 3 ("confirm every prod delete ran through the §3a reversibility
path"), I read every delete/purge todo in `sports_taxonomy_p2_migration_2026_08_08.md` end to end and checked each
for a recorded, same-run `gcs_bucket_soft_delete_retention_seconds()` citation (per the finalize todo's own rule:
"not assumed, not carried from a prior run, not from the plan's own text").

**6 of 7 object-deleting purges in that plan carry an explicit same-run `604800s`/`604800` citation**:
- `trades_inplay` fold (plan line 134)
- footystats `ODDS` uppercase phantom purge (plan line 356)
- the 785-key exchange/fixed_odds content-merge `finalize` (plan line 976: "fresh §3a check again")
- the `league=` legacy-object purge (plan line 586: "§3a fresh check retention=604800s")
- the SPORT-residue purge (plan ~line 794: "Fresh §3a check this-session (604800 on both buckets)")
- the 785-key content-merge's own `merge --confirm` step (plan line 976)

Manifest-only purges (KALSHI — population already absent, nothing to delete; the 2,490 blank-venue rows; the
ODDS_API/`batch_footystats` legacy-seed residue; the 3-tiny-fixes VM run) correctly note that §3a's object-delete
gate does not apply to them and cite no retention check — that absence is itself correct, since no GCS object was
touched in those cases.

**The one exception**: the `exchange_odds`/`fixed_odds` P0 purge's actual `migrate --confirm` GCS delete (plan lines
~892-897) — **59,310 GCS objects DROPPED, the single largest object-delete in the entire plan** — has no fresh-check
retention value quoted anywhere in its Progress Log entry. The plan does describe the underlying tool
(`purge_exchange_fixed_odds_2026_08_14.py`) as "§3a fresh-check gated" (plan line 867), meaning the SCRIPT enforces
the check internally (it would presumably have hard-failed had the bucket's retention read below 604800s) — but the
actual VALUE that check returned during this specific run was never written down, unlike every sibling delete above.

## Why it matters

The finalize plan's own review criterion exists precisely to prevent inferring "the check must have passed because
the tool has a gate" — that is an assumption, not a measurement, and this plan's own text says as much: "not assumed,
not carried from a prior run, not from the plan's own text." A future reader auditing this plan's delete-safety
compliance cannot verify, from the Progress Log alone, that this specific 59,310-object delete was actually checked
against a compliant bucket retention at the time it ran.

That said, this is **not evidence of a live data-safety problem**: the same Progress Log entry's independent
post-write re-download `verify` step already confirmed `0` non-excluded fork objects remaining and `0` target
objects missing (VERIFY PASSED) before this todo was flipped to done — i.e. the delete's actual OUTCOME is
independently confirmed safe by a different, already-executed check, regardless of the missing retention citation.

**Retroactive check (2026-08-21, NOT a substitute for the required same-run check, but the best evidence now
available)**: `gcs_bucket_soft_delete_retention_seconds("market-data-tick-sports-prd-central-element-323112")` =
**604800s (≥604800)**, today — consistent with the plan's own stated baseline ("every `-prd-` GCP bucket audits at
604800, 0 gaps"). Nothing found suggests the bucket's retention was ever non-compliant; the gap is purely that the
2026-08-14 run's own check value was never written into the plan.

## Recommended decision

No corrective action is possible against the historical delete itself (it already ran, and its outcome is
independently verified safe). This issue exists purely to make the documentation gap visible rather than have it be
silently treated as compliant. Recommend: no further action beyond this record — close as informational once read,
unless a future §3a-compliance sweep wants a durable example of "gate existed in the tool, but its output wasn't
logged" as a pattern to watch for in newer purge scripts (e.g. adding a mandatory `--log-retention-check` echo to
`purge_*.py` templates going forward would prevent recurrence, but that is a tooling improvement, not a fix to this
specific historical gap).

## Todos

- [ ] [SCRIPT] P3. Consider adding a mandatory retention-check echo/log line to the shared §3a-gated purge script
      template (wherever one exists / gets built) so a future purge's Progress Log entry cannot omit the value the
      way this one did. Optional hardening, not required to close this issue. (repo: market-tick-data-service or
      wherever the shared purge-script scaffolding lives)

## Progress Log

- **2026-08-21 (slot-10, review)**: Filed during the sports P2 finalize plan's item-3 §3a audit. Full detail above;
  parent plan's Progress Log carries only a one-line pointer to this doc (the parent plan is already near its
  1000-line hard cap).
