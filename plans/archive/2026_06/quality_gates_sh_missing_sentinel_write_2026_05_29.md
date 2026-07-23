---
doc_type: plan
title: quality-gates.sh doesn't write .qg_last_passed_sha sentinel despite codex doc claim
summary:
status: RESOLVED 2026-05-29
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: [plans/active/ci_canonical_v2_migration_2026_05_29.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-05-29
parent_epic: infrastructure_master
locked_by: live-defi-rollout
priority: P2
---

> **RESOLVED 2026-05-29**: Investigation found the sentinel-write logic WAS implemented in commit
> `a8b758c58 fix(ci): QG sentinel + SHA check in quickmerge + remove LDR from workspace-qg triggers` — but only landed
> on `live-defi-rollout` + `staging`, not main. Promoted to main via PR #95 (admin-merged 2026-05-29 20:09:40Z). The
> original investigation that hit "no sentinel" was running on PM main HEAD `8996f5fa0` BEFORE this commit reached main.
>
> What landed (per commit message): `base-service.sh` writes `.qg_last_passed_sha` on full (non-partial) QG runs with
> guards `RUN_TESTS=true`, `RUN_LINT=true`, `QUICK_MODE=false`, `ACT_MODE=false`, `SKIP_CODEX_FLAG` unset.
> `quickmerge.sh` reads the sentinel in `--agent` mode. `.gitignore` excludes the artifact.
>
> Issue archives. The original analysis below is preserved as the investigation record.

## What I found

`/codex/08-workflows/ci-cd-flow.md` (the canonical SSOT for the workspace CI/CD pipeline) describes a sentinel-write
contract:

> Pass 1 — Quality Gates (MANDATORY — FULL run, no skip flags) bash scripts/quality-gates.sh ... **On clean exit with NO
> skip flags → writes .qg_last_passed_sha = git rev-parse HEAD** Partial runs (--skip-tests / --skip-lint / --skip-codex
> / --quick) do NOT write sentinel

And quickmerge.sh enforces it at line 818-830:

```bash
# ── AGENT FAST-PATH: verify Pass 1 sentinel instead of re-running QG ──
_SENTINEL=".qg_last_passed_sha"
...
echo "[$REPO_NAME] ✅ SHA sentinel verified — skipping Pass 2 QG re-runs (already verified in Pass 1)"
```

**But the actual `scripts/quality-gates.sh` does NOT write the sentinel** — confirmed by exhaustive grep across PM's
`scripts/`, `scripts/quality-gates-base/`, and all `.sh` files in the workspace:

```bash
$ grep -rln "qg_last_passed_sha" scripts/
# (no matches)

$ grep -rln "qg_last_passed" $(find . -name "*.sh" -not -path "./.git/*")
# (no matches)
```

Only the READ-side in `scripts/quickmerge.sh:819` references the sentinel. There is no corresponding WRITE.

## Verified end-to-end 2026-05-29

Ran `bash scripts/quality-gates.sh` on PM main HEAD `8996f5fa0` after fixing all blocking gates. Output:

- Exit code: **0** (clean pass)
- All stages green: lint, strategy manifest, runbook check, coverage, architectural ratchets, plan discipline, codex doc
  freshness, VM registry, credential-ask orphan, UI/API flow, CI/CD diagram regen
- After clean exit: `.qg_last_passed_sha` file **not present** in the repo root

Manually wrote the sentinel after the fact (`echo $(git rev-parse HEAD) > .qg_last_passed_sha`) so the QG pass is
recorded, but this is a workaround — the script should do it automatically.

## Why it matters

The canonical CI flow's two-pass model (Pass 1 = full local QG → writes sentinel; Pass 2 = quickmerge --agent verifies
sentinel SHA matches HEAD before push) **doesn't work end-to-end** without the write step. Current behavior:

1. Agent runs `quality-gates.sh` → exits 0 → no sentinel written
2. Agent runs `quickmerge.sh "msg" --agent` → reads `.qg_last_passed_sha` → not found → quickmerge EXIT 1: "Run
   quality-gates.sh on current HEAD first" (even though it just ran)
3. Agent must manually write the sentinel to proceed, OR drop `--agent` flag (which loses the optimization)

This violates the canonical doc contract and forces every agent to discover the gap by trial-and-error.

## Where the write should land

`scripts/quality-gates.sh` final stage. Pattern (from the codex doc):

```bash
# At the END of quality-gates.sh, after all stages exit 0:
if [ -z "$SKIP_TESTS" ] && [ -z "$SKIP_LINT" ] && [ -z "$SKIP_CODEX" ] && [ -z "$QUICK" ]; then
    git rev-parse HEAD > .qg_last_passed_sha
    log_success "Sentinel .qg_last_passed_sha written for $(git rev-parse --short HEAD)"
fi
```

OR in `scripts/quality-gates-base/base-service.sh` if the write should be inherited by all repos using the base — review
which level is canonical.

## Why it matters

Composes with: `Plans Run To Actual Completion` (canonical SSOT must actually implement what it claims);
`Citadel-Grade Planning Standards` (doc-vs-code drift is review-blocking when discovered).

## Recommended decision

Add the sentinel-write logic at the end of `scripts/quality-gates.sh` (or wherever full-pass detection lives). Land as a
small PR. Verification: after fix, `bash scripts/quality-gates.sh` exit 0 produces `.qg_last_passed_sha` matching
`git rev-parse HEAD`, and `quickmerge.sh ... --agent` succeeds without manual sentinel intervention.

Workspace-wide impact: every service repo that uses PM's base-service.sh wrapper will inherit the fix automatically —
single SSOT change.

## Provenance

Discovered 2026-05-29 during ci_canonical_v2_migration_2026_05_29 Phase 1 Step 1 (PM full local QG pass). Operator chat
verified the canonical doc does claim the sentinel write. Confirmed via grep that the actual implementation is absent.
