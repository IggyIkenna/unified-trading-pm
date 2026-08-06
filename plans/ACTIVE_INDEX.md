# Active Plans Index (Day 1–2)

**⚠️ STALE — superseded by [`plans/active/INDEX.md`](active/INDEX.md) (corrected 2026-07-14, verify-rerun-2 finding
222).** This file's claims no longer hold: `plans/archive/2026_08/` is a real directory on disk (not a symlink),
`.cursor/plans` does not exist, and `plans/archive/2026_08/` holds ~140 plan files, not 4. `plans/active/INDEX.md` is
the canonical, currently maintained index (self-described as such, last updated 2026-07-12) and is the doc
`PLAN_FORMAT.md`'s own SSOT references cite. Treat this file as a historical Day-1–2 relic only.

**Note (was: unqualified, no staleness banner):** `archive/2026_08/` is a symlink to `.cursor/plans`. This index lists
the 4 plans currently in progress (2 per person).

| Plan                         | File                                        | Notes                                                              |
| ---------------------------- | ------------------------------------------- | ------------------------------------------------------------------ |
| **plans_to_deployable**      | `plans_to_deployable_unified_audit.plan.md` | Canonical four-stage pipeline (Plans → Code → Tested → Deployable) |
| **phase1**                   | `phase1_foundation_prep.plan.md`            | Foundation prep                                                    |
| **AWS_MIGRATION**            | `AWS_MIGRATION_PLAN.md`                     | Dual-cloud readiness (GCP primary, AWS secondary)                  |
| **SPORTS_MIGRATION_GAP_FIX** | `SPORTS_MIGRATION_GAP_FIX.md`               | Sports migration gap fix (Part A complete; Part B in progress)     |

---

**Staged:** Plans queued for activation live in `plans/staged/`.
