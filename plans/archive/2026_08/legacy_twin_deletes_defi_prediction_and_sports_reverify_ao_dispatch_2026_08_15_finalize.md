---
doc_type: plan
title: Finalize — legacy-twin deletes (defi/prediction) + sports re-verify
summary: Gated finalize companion for legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md.
status: complete
nature: process
asset_group: [defi, prediction, sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, finalize]
related: [/plans/active/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope: [/plans/active/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md]
locked_since:
resolved_by:
---

# Finalize — legacy-twin deletes (defi/prediction) + sports re-verify

- [x] ✅ [REVIEW] P2. Confirm all todos landed with evidence (defi/prediction delete-after-copy evidence, and the sports
      fresh twin-coverage measurement — NOT just "checked", the actual numbers against the 2 call sites and Part 5 %);
      the parent plan has grown from 2 headline todos to 5 (todos 3-5 were spawned as follow-up work during
      execution) — confirm all 5, not just the original 2; update `instruments_completion_tracker_2026_07_06.md` with
      the sports result either way; archive the parent plan once done and unlocked. [Reworded 2026-08-17
      (plan_reconciler): "both" → "all" — the parent doc now has 5 todos, not 2.] **DONE 2026-08-17 (slot-5, review)**
      — all 5 parent-plan todos verified landed with real evidence (VM run ids, exit codes, commit shas, per-object
      verdict counts — not self-report): todo 1 defi dry-run `0 deletable/1080 blocked` (correctly gated, no apply);
      todo 2 sports re-check cites both live call sites by file:line, Part 5 not re-measured per the protocol's own
      Part-4-overrides rule (not a rubber stamp — an explicit, cited categorical override); todo 3 root-caused the
      crc32c gap to a schema-width tooling artifact via 5-sample content compare; todo 4 shipped the fix
      (`instruments-service@d24a098e18`) + re-ran the full 1,080-candidate dry-run to 837 deletable/243 blocked
      (77.5% twin-coverage); todo 5 resolved the 243 residual (38 stale ghost entries fixed via
      `instruments-service@1ef9288af1`, 205 genuine permanent no-migrate-first). Updated
      `instruments_completion_tracker_2026_07_06.md` Stage-1 legacy-twin-deletes todo with the final numbers for all
      three legs (defi/prediction/sports). Parent plan is unlocked (`locked_by:` empty) — archiving both docs now.
