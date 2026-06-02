# Branch-and-Version Reference Model — two layers, two references (SSOT)

> **The one-line rule:** `live-defi-rollout` (LDR) is the **code-integration** reference; **staging → main + semver** is
> the **dependency-safety** reference. They answer different questions, so they are deliberately different references.
> Do not collapse them.

Codified 2026-06-02 after an operator question about what "origin"/"behind" mean in `quickmerge.sh` for a repo's own
branch versus for its dependencies. The confusion is real and the answer is two-layered.

---

## The two questions (and why one reference can't answer both)

| Question | Reference | Mechanism |
| --- | --- | --- |
| **"Is my code current with the shared integration line?"** | **`origin/live-defi-rollout`** (`active_feature_branch` in `workspace-manifest.json`) | branch position — am I *behind* the branch HEAD |
| **"Am I depending on an integration-tested version of my dependencies?"** | **`staging` → `main` + the semver `versions`/`staging_versions` maps** | promoted version — is my pinned dep version *behind* what cleared SIT |

These are NOT the same. A dependency's LDR HEAD churns rapidly (fast shared dev, **no remote CI** on LDR — quality is
enforced locally by `quality-gates.sh` at `quickmerge`). That LDR code is **not yet known-safe for consumers**. Safety
is established only when the dependency is promoted **LDR → staging → main**, where `quality-gates-v2` +
**system-integration-tests** run and `semver-agent` records the new version in `staging_versions`. Consumers depend on
that **version**, not the dependency's raw LDR HEAD — so the version is the stable contract that decouples consumers
from LDR churn.

## The two "behind"s

1. **Branch-behind** — *your own repo's branch* has unpulled commits from `origin/live-defi-rollout`. You must pull the
   latest shared line before merging (you may be arbitrarily **ahead** / have local diverging commits + dirty files —
   that is the work you are merging and is expected; only **behind** is disallowed). Enforced by `quickmerge.sh`
   **STAGE 0.4 (Not-Behind Gate)**: pass when `behind == 0`; if behind, pull first (FF, else rebase local on top); block
   only on genuine rebase conflict. Override `QUICKMERGE_ALLOW_BEHIND=1`.

2. **Version-behind** — *your pinned dependency versions* are older (semver `<`) than the versions that have been
   promoted to staging (`staging_versions` on `origin/main`). Building on an older dep than the integration-tested one
   is the risk. Enforced by `quickmerge.sh` **STAGE 1.6 (Dependency Version Gate)**: if any of this repo's deps is
   semver-behind `staging_versions`, auto-pull the PM manifest (`origin/main`) and re-check; block if still behind.
   Override `QUICKMERGE_ALLOW_BEHIND=1`.

## What `quickmerge.sh` checks, against which reference

| Stage | Check | Reference | Layer |
| --- | --- | --- | --- |
| 0.4 Not-Behind Gate | repo's own branch not behind | `origin/live-defi-rollout` | code-integration |
| 1 Dependency validation | dep repos aligned to the shared dev branch | `origin/live-defi-rollout` | code-integration |
| 1.6 Dependency Version Gate | pinned dep versions not semver-behind | `staging_versions` (read from `origin/main`) | dependency-safety |

`active_feature_branch` (= `live-defi-rollout`) is the SSOT for layer-1 references. `versions` (current) +
`staging_versions` (the per-repo baseline `semver-agent` advances on each staging promotion) are the SSOT for the
layer-2 reference; both live in `workspace-manifest.json` and are read from `origin/main`.

## Where dependency-safety is actually *enforced* (not just surfaced)

The integration guarantee for a dependency — "this version passed SIT, so it won't break consumers" — is established at
the **staging → main promotion** (`quality-gates-v2` + `system-integration-tests`, then `semver-agent` records the
version). `quickmerge.sh` STAGE 1.6 is the **consumer-side guard** that you are not pinning *behind* that promoted
version; it does not itself run SIT. See `codex/08-workflows/ci-cd-flow.md` for the promotion mechanism and
`codex/08-workflows/deployment-flow.md` for the full dev → staging → main flow.

## Anti-patterns (review-blocking)

- Treating LDR as the dependency-safety reference ("my dep is on LDR, good enough") — LDR is un-SIT-tested; safety is the
  promoted **version**, not LDR HEAD.
- Treating "has local commits / diverges from origin" as a reason to block a merge — local deviation is the work; only
  **behind** blocks (both for branch and for version).
- Hand-editing `staging_versions` to mask a behind-version — `semver-agent` owns it; it advances only on real staging
  promotion.
- Pinning a consumer to a dependency's LDR HEAD sha instead of its promoted semver version.

## Cross-references

- `scripts/quickmerge.sh` — STAGE 0.4 (branch not-behind), STAGE 1 (dep branch alignment), STAGE 1.6 (dep version gate)
- `workspace-manifest.json` — `active_feature_branch`, `versions`, `staging_versions`
- `codex/08-workflows/ci-cd-flow.md` — `quality-gates-v2`, branch protection, staging → main promotion
- `codex/08-workflows/deployment-flow.md` — dev → staging → main + paper → live
- `plans/active/cicd_contract_hardening_2026_06_01.md` — staging → main / SIT / semver promotion automation (under repair)
