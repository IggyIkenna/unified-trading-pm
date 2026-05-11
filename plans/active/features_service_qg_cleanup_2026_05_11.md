---
title: features-service QG-codex cleanup + full byte-for-byte parity run + org-naming transfer
type: plan
status: active
created: 2026-05-11
migrated_from: features_repo_consolidation_2026_05_08.md
owner: harsh (slot 2)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# features-service QG-codex cleanup + full parity run + org transfer

## What this is

The consolidated `features-service` repo (the 2026-05-08 `features_repo_consolidation` merge of the 8
`features-*-service` repos — Phase 7 done, 8 repos archived) ships functionally complete but its `scripts/quality-gates.sh`
**fails** on ~17 codex-compliance violations + function/file-size violations carried over from the 8 source repos, which
were masked there via per-file `ruff` ignores + `SKIP_*` env vars + per-repo `CODEX_MAX_VIOLATIONS`. The consolidated
gate (`CODEX_MAX_VIOLATIONS=0`, no per-package ignores) surfaces all of them. **`features_repo_consolidation_2026_05_08.md`
named this plan as the recommended successor** (Q1 rec (a)/(b)/(c)). This plan owns the three residual items — NONE of
which gate the May-23 cutover (Phase 7 — the deployable + 8 archived repos — is done; the consolidated repo imports +
runs across all 5 asset_groups; the residual is QG-green + verification + an org-naming tidy):

1. **QG-codex cleanup** (Phase 4.6 of the parent) — fix the ~17 codex-compliance + size violations the **proper way**
   (fix the root cause; **NOT** per-package-ignore restoration — that's a hack per CLAUDE.md "No double SSOT / fix the
   root cause"). Per operator direction 2026-05-11: _"slot 2 can solve the quality-gates codex issues and make it
   solid."_
2. **Full byte-for-byte parity run** (Phase 6 of the parent — the reusable utility `scripts/dev/feature_parity_diff.py`
   PM@`44d23659` is already shipped; the RUN itself was never executed — only a lightweight import/CLI/route smoke).
   **`blocked_by: code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3 (resume backfills 2026-05-19→05-23)** —
   the run needs a 7-day reference window with live feature-input data on GCS. Per operator direction 2026-05-11: _"we
   need the data so it is blocked until we have the proper data in gcs buckets and then we can run full byte-to-byte
   parity."_
3. **F9 — `features-service` GitHub org transfer** (CosmicTrader → IggyIkenna, to match `workspace-manifest.json`).
   **Non-blocking** — per operator direction 2026-05-11: _"F9 regarding the repo owner is nothing major, until its
   working solid, we can do that anytime — I don't think it's a blocker."_ Do anytime once features-service is QG-green
   and solid.

## Phases

### Phase 1 — QG-codex cleanup (the proper fix; NO per-package-ignore restoration)

- [ ] [AGENT] P0. Phase 1.1 — Enumerate the ~17 codex-compliance violations + function/file-size violations from
      `cd features-service && bash scripts/quality-gates.sh` CODEX-COMPLIANCE step. Categories per the parent plan Q1:
      `os.getenv()`/`os.environ` → route through `UnifiedCloudConfig`; `asyncio.run()` in a loop
      (`features_service/calendar/cli/handlers/batch_handler.py`) → fix the loop; imports inside functions → hoist to
      top-level (or document the genuine circular-import exception); empty-string + empty-dict/list fallbacks → fail
      loud / honest absence per CLAUDE.md "no empty fallbacks"; local `BaseModel`/`TypedDict`/`dataclass` → move to
      UAC/UIC per schema-provenance; direct `from google.cloud import …` → route through `unified_cloud_interface`;
      files >900L → split; methods >50L / functions >200L → decompose. Produce a violation-by-violation table
      (file:line / category / fix shape).
- [ ] [AGENT] P0. Phase 1.2 — Fix each violation at the root. Per-violation commit (or small batches per category).
      Run `cd features-service && bash scripts/quality-gates.sh` after each batch.
- [ ] [AGENT] P0. Phase 1.3 — `cd features-service && bash scripts/quality-gates.sh` returns green (CODEX_MAX_VIOLATIONS=0,
      no per-package ignores added). Flip `features_repo_consolidation_2026_05_08.md` Phase 4.6 checkbox `- [x]` with the
      QG-green evidence; remove the `**DEFERRED**` annotation.
- [ ] [AGENT] P1. Phase 1.4 — Codex SSOT audit pass per CLAUDE.md "Post-Plan-Phase Codex Audit": verify
      `codex/04-architecture/features-service-architecture.md` reflects the cleaned-up shape; update if drifted.

### Phase 2 — Full byte-for-byte parity run (BLOCKED on data)

- [ ] [AGENT] P0. Phase 2.1 — **BLOCKED until `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3 backfills
      land a 7-day reference window of live feature-input data on GCS.** Then: (1) check out the 8 source `features-*-service`
      repos at their last-pre-consolidation commit (archived read-only on GitHub but cloneable; local sibling clones still
      have the pre-archival HEAD); (2) run each of the 8 source CLIs over the 7-day window → baseline parquets in
      `${WORKSPACE_ROOT}/.feature_parity_diff/baseline/<family>/`; (3) run `python -m features_service --feature-family
      <f> --mode batch` for each family over the same window → `${WORKSPACE_ROOT}/.feature_parity_diff/postmerge/<f>/`;
      (4) `python unified-trading-pm/scripts/dev/feature_parity_diff.py` — assert schema match, row-count match, value
      match (within float tolerance) per family; (5) any divergence → diagnose + fix or document as an accepted
      difference with rationale.
- [ ] [AGENT] P0. Phase 2.2 — Parity run green → flip `features_repo_consolidation_2026_05_08.md` Phase 6 checkbox
      `- [x]` with the run evidence (commands + machine + duration + per-family pass); remove the `**DEFERRED**` annotation.

`execution:` for Phase 2 — owner: harsh slot 2 (or whichever slot owns features work when Phase 3 backfills land);
cadence: one-shot; verifier: `feature_parity_diff.py` exit 0 / per-family pass; last_executed: NEVER (blocked on data).

### Phase 3 — F9 org-naming transfer (non-blocking; do anytime once features-service is solid)

- [ ] [AGENT] P2. Phase 3.1 — Transfer the `features-service` GitHub repo from `CosmicTrader` org to `IggyIkenna` org
      (or — if a transfer is impractical — re-create under `IggyIkenna` + push the full history + archive the
      `CosmicTrader` copy). Update every clone's `origin` remote. Confirm `workspace-manifest.json` line for
      `features-service` already points at `IggyIkenna` (it does — the manifest was pre-set; this aligns reality to it).
- [ ] [AGENT] P2. Phase 3.2 — Update any plan/codex/CI reference that hardcodes `CosmicTrader/features-service` →
      `IggyIkenna/features-service` (the DEPRECATION_NOTICE.md banners on the 8 archived repos already point at
      `IggyIkenna/features-service`, so those are fine).

## Done definition

- ✅ `cd features-service && bash scripts/quality-gates.sh` green (Phase 1).
- ✅ Full byte-for-byte parity run executed + green per family (Phase 2 — after `code_freeze` Phase 3 backfills land
  the data).
- ✅ `features-service` GitHub repo under `IggyIkenna` org; all `origin` remotes + references updated (Phase 3).
- ✅ `features_repo_consolidation_2026_05_08.md` Phase 4.6 + Phase 6 checkboxes flipped `- [x]` + this plan's pointer
  removed from those annotations; that plan can then archive cleanly.

## Composes with

- `features_repo_consolidation_2026_05_08.md` — the parent; this plan owns its Phase 4.6 + Phase 6 residual + F9.
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3 — the gate Phase 2 (parity run) is blocked on.
- CLAUDE.md "No double SSOT / fix the root cause" — Phase 1 fixes violations at the root, NOT via per-package-ignore.
- CLAUDE.md "Plans Run To Actual Completion" — Phase 2's `execution:` block + the one-shot run requirement.
- CLAUDE.md "Plan Archival HARD RULE" — this plan is the named active home for `features_repo_consolidation`'s deferred
  Phase 4.6 + Phase 6 + F9 (so the parent can archive without losing them).
