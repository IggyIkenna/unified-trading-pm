---
doc_type: issue
title: Codex drift — deployment-template + Phase 8 surfaces (post-2026-05-12 audit, slot-8 Harsh-side)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: slot-8 (Harsh)
source:
  [
    plans/active/continuation_prompts_harsh_2026_05_15.md § Slot 8 item 3,
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md,
  ]
locked_by: live-defi-rollout
---

# Codex drift — deployment-template + Phase 8 surfaces

> Findings from item 3 in `continuation_prompts_harsh_2026_05_15.md` § Slot 8. The original codex_vs_citadel audit
> (Phases 0-5) closed 2026-05-12. This doc covers drift introduced by work shipped **after** that audit during the
> 2026-05-12→2026-05-15 density push.

## What I found

### DT-1 — STEP 5.79-5.82 missing from `quality-gates.md` STEP cross-reference table [IMMEDIATE — FIXED]

**Status**: ✅ FIXED this session (slot-8 2026-05-15, PM commit pending) — 4 table rows added to
`/codex/06-coding-standards/quality-gates.md` § "QG STEP cross-reference".

**Finding**: `base-service.sh` has 4 new enforcement steps added in B-014 (deployment_and_qg_strategy
\_implementation_2026_05_13.md Phase 3):

- STEP 5.79: `dockerfile-base-pin` — Dockerfiles must use `@sha256:` not `:tag`
- STEP 5.80: `tarball-manifest-present` — `create-code-tarballs.sh` must write `manifest.json`
- STEP 5.81: `tarball-env-block` — deployment-api must gate staging/prod tarball uploads
- STEP 5.82: `image-build-on-staging-merge` — staging branch workflow must trigger Cloud Build

None of these appeared in the STEP table, leaving agents implementing new repos with no way to look up what these CI
failures mean.

**Fix applied**: added 4 rows to `quality-gates.md` table (disposition: `(no section here — see enforcement file)` with
CLAUDE.md cross-refs pointing to the relevant plan/codex anchors).

**Companion finding**: STEPs 5.71-5.78 (batch_live_symmetry enforcement steps, added in Phase 6+) were also missing from
the table. Fixed in the same edit — 8 rows added. See DT-2.

---

### DT-2 — STEP 5.71-5.78 missing from `quality-gates.md` STEP cross-reference table [IMMEDIATE — FIXED with DT-1]

**Status**: ✅ FIXED this session (same edit as DT-1).

**Finding**: The following 8 steps are enforced in `base-service.sh` but had no table entry:

- 5.71: emission-policy paired-callsite (writegate Phase 6.9)
- 5.72: UAC chain_env inclusion invariant
- 5.73: `ManifestWriter.add()` with bundled `data_type` — banned
- 5.74: MDPS bar-boundary truncation bypass check
- 5.75: `DataType` mode-agnosticism (batch_live_symmetry L1)
- 5.76: no service-level `DataType` redeclarations (batch_live_symmetry L5)
- 5.77: no `mode == "batch"/"live"` outside CLI seam (batch_live_symmetry L2)
- 5.78: `RuntimeMode` declared only in UAC (batch_live_symmetry L3)

The table comment says "Steps without a dedicated section here are enforced inline in `base-service.sh` and documented
in CLAUDE.md" — technically these were covered by that note. But for discoverability (agents get CI errors citing "STEP
5.71 FAILED" and have nowhere to look them up), table rows are the right fix.

---

### DT-3 — UAC `SIZE_EXTRA_EXCLUDES` / `UAC_CANONICAL_EXEMPT` carveout patterns not in `quality-gates.md` [PRE_CUTOVER]

**Status**: 🟡 OPEN — PRE_CUTOVER, no blocking risk for May-23.

**Finding**: `unified-api-contracts/scripts/quality-gates.sh` has several carveout patterns that are NOT explained in
`/codex/06-coding-standards/quality-gates.md`:

- `UAC_CANONICAL_EXEMPT=true` — disables the "no internal deep-imports" check for UAC itself
- `BROAD_EXCEPT_EXTRA_EXCLUDES` — per-file suppress for overly-broad `except` in registry code
- `GCP_PROJECT_ID_EXCLUDE_GLOBS` — excludes files containing live GCS bucket names as provenance docs
- `SIZE_EXTRA_EXCLUDES` — per-file suppress for oversized declarative/registry files (12 files listed)

No codex section explains when to use these patterns or why they exist. An author adding a new declarative UAC file
(e.g., a new registry module) would not know they need to add an exclusion entry.

**Recommended fix**: Add a "Library-repo carveout patterns" section to `quality-gates.md` documenting:

- When `SIZE_EXTRA_EXCLUDES` applies (closed-set enumerations > file-size limit)
- When `GCP_PROJECT_ID_EXCLUDE_GLOBS` applies (provenance docs with literal bucket names)
- When `UAC_CANONICAL_EXEMPT=true` is valid (schema/registry owner only)

**Owner**: slot 8 (Harsh) or governance slot. **Disposition**: PRE_CUTOVER — doesn't block May-23 cutover but should
land before a new registry module is added post-cutover without exclusion guidance.

---

### DT-4 — `deployment-and-qg-strategy.md` doesn't cross-reference B-014 (STEP 5.79-5.82 rollout) or B-018 (Phase 4.A QG snapshot cron) [PRE_CUTOVER]

**Status**: 🟡 OPEN — PRE_CUTOVER.

**Finding**: `/codex/05-infrastructure/deployment-and-qg-strategy.md` describes the Phase 3 ratchet rollout ("Every
service repo has `scripts/quality-gates.sh`") and the daily QG snapshot ("bash
unified-trading-pm/scripts/quality_gates/snapshot.sh") but:

- No mention of **B-014** (the STEP 5.79-5.82 rollout that ran 2026-05-13→2026-05-15; 15 service repos)
- **B-018** (QG snapshot cron VM at `quality_gates_snapshot/` in GCS) is described in prose at line 148 but is not named
  as B-018, has no VM prefix registration note, and doesn't cross-reference the `launch-qg-snapshot-vm.sh` launcher

**Impact**: Agents updating deployment strategy may duplicate B-018 work (re-create cron pattern) or not know the STEP
5.79-5.82 ratchet has ratchet dates (PENDING_RATCHET flags with specific Phase target dates that need follow-up).

**Recommended fix**: Add a "Phase 3 QG ratchet rollout (B-014)" and "Phase 4.A QG snapshot cron (B-018)" reference entry
to deployment-and-qg-strategy.md's "Continuous verification" section with:

- B-014 completion date + remaining PENDING_RATCHET steps (5.79/5.80/5.81/5.82 each pending Phase 5)
- B-018 VM prefix + GCS path + scheduler BLOCKED-OPERATOR-DECISION status

**Owner**: slot 8 (Harsh) or slot 2 (deployment-service theme). **Disposition**: PRE_CUTOVER.

---

## Recommended next steps

| #    | Finding                                                             | Disposition | Owner               | Done?                 |
| ---- | ------------------------------------------------------------------- | ----------- | ------------------- | --------------------- |
| DT-1 | STEP 5.79-5.82 table rows missing from quality-gates.md             | IMMEDIATE   | slot-8              | ✅ FIXED              |
| DT-2 | STEP 5.71-5.78 table rows missing from quality-gates.md             | IMMEDIATE   | slot-8              | ✅ FIXED              |
| DT-3 | UAC carveout patterns not documented in quality-gates.md            | PRE_CUTOVER | slot-8 / governance | ✅ FIXED @PM@8b4ab3ad |
| DT-4 | B-014 + B-018 not cross-referenced in deployment-and-qg-strategy.md | PRE_CUTOVER | slot-8 / slot-2     | ✅ FIXED @PM@8b4ab3ad |

All 4 DT findings closed. Issue doc archived — no remaining open items.

**No BIG findings** (no data-correctness, no cross-repo architectural contradiction, no May-23 critical path impact).

---

## RESOLUTION UPDATE 2026-05-15 (ikenna-main audit during pings/issues triage)

**All 4 DT findings now ✅ RESOLVED** — DT-1 + DT-2 already fixed by slot-8 Harsh earlier today; DT-3 + DT-4 verified
post-audit to already be in codex (likely landed between issue-doc filing and now):

- ✅ DT-3 RESOLVED — `UAC_CANONICAL_EXEMPT` documented at `quality-gates.md:461`; `SIZE_EXTRA_EXCLUDES` documented at
  `quality-gates.md:480`. Both with examples + when-to-use guidance.
- ✅ DT-4 RESOLVED — `B-014 Phase 3 QG ratchet rollout` documented at `deployment-and-qg-strategy.md:313` with rollout
  dates + remaining PENDING_RATCHET flags. `B-018 Phase 4.A QG snapshot cron` documented at
  `deployment-and-qg-strategy.md:312` with VM prefix + GCS path + scheduler BLOCKED-OPERATOR-DECISION status.

Issue can be moved to `plans/archive/issues/` at next archive sweep. No further action required.
