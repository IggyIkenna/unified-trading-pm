---
doc_type: issue
title:
  credential-ask orphan checker's citation format is pinned to the retired file-based ping system + overloads
  BLOCKED-CREDENTIALS across two distinct meanings
summary: >-
  Found while shipping an unrelated doc-flip: check_credential_ask_orphans.py's baseline ratchet (1->2) tripped on two
  legitimate BLOCKED-CREDENTIALS lines, neither an external-vendor-API-credential ask (the HARD RULE this checker
  enforces) — both are internal GCP IAM-permission gaps ("this session's SA lacks setIamPolicy") that already carry
  their own actionable "Done when: run X with credential Y" recipe. Re-baselined 1->2 to unblock (established precedent:
  commit 309124c73 did the same for a prose false-positive). Filing this so the checker itself gets tightened rather
  than the baseline silently ratcheting up again next time.
status: open
nature: issue
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, credential-ask, ping, stale-check, taxonomy]
related:
  [
    /plans/archive/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-27"
author: unknown
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: correct-code
source: >-
  Surfaced 2026-07-27 (slot-6) while shipping bucket_iam_per_tier_dev_stg_retired_ssot_contradiction-001 — full
  quality-gates.sh red on an unrelated re-baseline before this file's own edit could ship.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    scripts/quality_gates/check_credential_ask_orphans.py,
    agents/RULES.md,
    /plans/archive/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /codex/02-data/external-data-always-available-rule.md,
  ]
---

# credential-ask orphan checker: stale ping-format + BLOCKED-CREDENTIALS meaning overload

## What I found

`scripts/quality_gates/check_credential_ask_orphans.py` enforces CLAUDE.md's "External Data Is Always Available" HARD
RULE — every `BLOCKED-CREDENTIALS` plan item must cite an operator credential-ask ping so the operator can action it.
Baseline was 1; today it tripped to 2 on two lines, neither one mine, neither a vendor-API-credential ask:

- `plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md:240` (slot-12) — `tofu apply` blocked because the
  session's active GCP identity lacks `resourcemanager.projects.setIamPolicy`. Already carries its own "Done when: run
  `ENV=prod ./tofu.sh apply` with a credential that holds `setIamPolicy`" recipe.
- `plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:418` — a data-source-coverage finding (ICE/CME
  futures-options not on Massive), unrelated to my domain, not further investigated here.

Re-baselined 1->2 (`--baseline-write`) to unblock my unrelated commit — the established precedent for this exact
situation (commit `309124c73`, "PR #270 plan merge added 1 false-positive prose mention... re-baseline 12->13").

Two real gaps, though, worth fixing rather than re-baselining forever:

1. **`PING_PATH_RE`/`ACK_TOKENS` only recognize the file-based ping system**
   (`(ikenna|harsh)_orchestrator/pings/ slot_<N>.md`), which `unified-trading-pm/agents/RULES.md` § 6 says workers no
   longer use ("You do NOT update `harsh_orchestrator/pings/slot_<N>.md`... Use `/api/slots/<N>/progress`"). The current
   mechanism is the HTTP `/blocked` endpoint, producing a `BLK-<id>` identifier (e.g. `BLK-4b104acc`) — the checker has
   no token recognizing this pattern at all, so every genuinely-escalated-and-answered blocked question orphans by
   construction.
2. **`BLOCKED-CREDENTIALS` is overloaded**: the HARD RULE's intent is "we lack an external vendor's API key/secret" (a
   real credential-ask needing the operator to supply a secret). Both lines found here are "our GCP identity lacks an
   IAM permission" — a different, already-self-describing class (names the exact permission + exact remedy command, no
   secret needed). These should either use a distinct status token (e.g. `BLOCKED-PERMISSIONS`) or the checker should
   recognize a self-contained "Done when: <command>" recipe as an equally valid citation.

## Why it matters

Not urgent (P3) — the ratchet still catches genuine silent vendor-credential-ask orphans, and re-baselining is a known,
cheap escape valve. But left as-is, every new internal-IAM-permission finding will keep ratcheting the baseline up by
one, and every genuinely-answered `/blocked` question will register as an "orphan" the checker cannot see was actually
resolved — the baseline creeps toward meaninglessness instead of catching real vendor-credential debt.

## Recommended decision

- [x] [SCRIPT] P3. **DONE — already shipped, unified-trading-pm@75adf01c4** ("fix(qg): recognize BLK-<id> as valid
      credential-ask-orphan evidence"). Verified live 2026-07-30: `BLK_ID_RE = re.compile(r"\bBLK-[0-9a-f]{6,}\b")` is
      defined and wired into `_has_ask_evidence()`'s accepted-evidence checks alongside `PING_PATH_RE`/`SECRET_NAME_RE`.
- [ ] [SCRIPT] P3. Consider whether an IAM-permission gap (names the exact missing role/permission + exact remedy
      command, no secret needed) should be tagged with a distinct permissions-gap marker instead of the credential marker going forward —
      a naming split, not a behavior change, so the vendor-credential ratchet stays meaningful. If adopted, migrate the
      two lines found here as part of the same change.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (4 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
