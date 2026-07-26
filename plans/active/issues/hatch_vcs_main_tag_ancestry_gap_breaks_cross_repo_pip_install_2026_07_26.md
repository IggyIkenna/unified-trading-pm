---
doc_type: issue
title: >-
  hatch-vcs version on `main` is computed from a tag NOT reachable from main's squashed history — breaks any fresh
  cross-repo `pip install -e` of UAC against a package requiring the current release floor
summary: >-
  Extending unified-trading-system-ui's registry-drift CI job (defi_wizard_batch2_018_residual_findings-004), `pip
  install -e _deps/unified-api-contracts -e _deps/unified-trading-library` (a pre-existing, unrelated step also used by
  the established ui-reference-data.json check) hard-fails with `ResolutionImpossible` on a FRESH checkout of UAC's
  `main` branch: hatch-vcs resolves `unified-api-contracts` to `0.71.1.dev158+gb22f9fca2`, but unified-trading-library
  declares `unified-api-contracts<1.0.0,>=0.72.0` — a real version floor the fresh-clone resolves BELOW. Root cause
  (confirmed via `git describe --tags` + `git merge-base --is-ancestor`): the `v0.72.0` tag is NOT an ancestor of UAC's
  `main` HEAD (`b22f9fca`) — `git merge-base --is-ancestor v0.72.0 origin/main` returns false — while it IS an ancestor
  of `live-defi-rollout` (`git describe --tags origin/live-defi-rollout` → `v0.72.0-646-g2ded0993`). `main`'s
  squash-merge promotion history (each promote is one squash commit whose parent is the PREVIOUS squash commit, not the
  individual LDR commits) has structurally "lost" the ancestor path to that tag, so `git describe`/hatch-vcs walking
  `main`'s own graph falls back to the older `v0.71.0` and computes a dev-distance from there instead — permanently
  below any downstream floor pinned at `>=0.72.0`, for as long as this ancestry gap persists on `main`. **This is NOT
  the "528 commits behind" false alarm I almost filed** — `git diff --stat origin/main origin/live-defi-rollout` and
  `git rev-parse origin/main^{tree}` vs `origin/live-defi-rollout^{tree}` for UAC (and UTL, unified-trading-system-ui,
  strategy-service, execution-service, features-service, checked as a sanity sweep) are all byte-identical trees right
  now — content-wise `main` is fully caught up (the promotion pipeline itself is healthy); this is purely a
  **version-string** defect caused by squash-merge breaking `git describe`'s tag-ancestor walk, distinct from (but same
  class as, and possibly related to) the tag-mechanism issues already tracked in
  `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` and
  `promotion_lag_alert_hides_provenance_block_2026_07_17.md`.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [cicd, hatch-vcs, versioning, git-tag, squash-merge, pip, dependency-resolution, registry-drift]
related:
  [
    /plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /plans/active/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md,
    /plans/archive/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
    /plans/active/issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
sequential: true
source:
  [
    unified-trading-system-ui/.github/workflows/ci.yml,
    unified-api-contracts/pyproject.toml,
    unified-trading-library/pyproject.toml,
  ]
---

## What I found

While verifying the `registry-drift` CI job extension for `capability-manifest.json`
(`defi_wizard_batch2_018_residual_findings-004`) against a real GHA run, the pre-existing
`pip install -e _deps/unified-api-contracts -e _deps/unified-trading-library` step (used by BOTH the established
`ui-reference-data.json` drift check and my new `capability-manifest.json` one) failed with:

```
ERROR: Cannot install unified-api-contracts 0.71.1.dev158+gb22f9fca2 (from editable ...) and
unified-trading-library==0.57.1.dev5+gc2ce80145 because these package versions have conflicting
dependencies.
The conflict is caused by:
    The user requested unified-api-contracts 0.71.1.dev158+gb22f9fca2
    unified-trading-library 0.57.1.dev5+gc2ce80145 depends on unified-api-contracts<1.0.0 and >=0.72.0
```

Confirmed via `gh run view --log` this has been failing this exact way (or a shallow-clone variant, see below) on every
`registry-drift` run on `unified-trading-system-ui`'s `main`/promote PRs going back to at least 2026-07-21 — pre-dating
and unrelated to my capability-manifest.json work.

**Two layered bugs, not one:**

1. **Shallow-clone fallback (I fixed this half in the CI job)**: the sibling checkouts (UAC, UTL, execution-service,
   features-service, strategy-service) didn't set `fetch-depth: 0`, so hatch-vcs saw NO tags at all and fell back to a
   bogus `0.1.dev1+<sha>`. Fixing `fetch-depth: 0` surfaced the REAL version instead (`0.71.1.dev158+gb22f9fca2`) —
   progress, but still below the `>=0.72.0` floor, so the install still fails.

2. **Tag-ancestry gap on `main` (this is the actual remaining blocker, NOT mine to fix)**:

   ```
   $ git describe --tags origin/main            # v0.71.0-158-gb22f9fca
   $ git describe --tags origin/live-defi-rollout # v0.72.0-646-g2ded0993
   $ git merge-base --is-ancestor v0.72.0 origin/main            # NOT an ancestor
   $ git merge-base --is-ancestor v0.72.0 origin/live-defi-rollout # IS an ancestor
   ```

   The `v0.72.0` tag exists in the repo but is unreachable from `main`'s own commit graph. UAC's `main` is built
   entirely from LDR→main squash-merge commits (each promote = one squash commit whose parent is the PREVIOUS squash
   commit on `main` — per `ci-cd-flow.md`'s "LDR is the backmerge sink; not rebaseable" squash design). If `v0.72.0` was
   tagged on an LDR commit (or a main commit later superseded by a squash that doesn't include it as an ancestor),
   `git describe`/hatch-vcs walking `main`'s linear squash-commit history will never find it, and falls back to the next
   reachable tag (`v0.71.0`) — computing a version permanently below the current real release floor, for as long as this
   specific gap persists.

**This is NOT a promotion-lag / stalled-pipeline problem** — I initially mismeasured this as "UAC main is 528 commits
behind live-defi-rollout" using `git rev-list --count origin/main..origin/live-defi-rollout`, which is exactly the
squash-inflated `ahead_by` metric `ci-cd-flow.md` and `promotion_lag_alert_hides_provenance_block_2026_07_17.md` already
warn against (squash merges break commit-count ancestry even when content is fully caught up). Redid it with the correct
content-diff check and confirmed **all 6 repos I sampled (UAC, UTL, unified-trading-system-ui, strategy-service,
execution-service, features-service) have byte-identical trees between `main` and `live-defi-rollout` right now**
(`git rev-parse origin/main^{tree}` == `origin/live-defi-rollout^{tree}` for every one). The promotion pipeline itself
is healthy; only the derived VERSION STRING is wrong for UAC specifically, because of the tag ancestry gap above.

## Why it matters

Any fresh CI checkout of `main` (not `live-defi-rollout`) that does `pip install -e unified-api-contracts` alongside a
package pinned to the current real floor (`unified-trading-library` requires `>=0.72.0`) will permanently fail to
resolve, regardless of how many times the checkout is retried — it's not flaky, it's a structural consequence of the
tag-ancestry gap. This currently blocks:

- The established `ui-reference-data.json` registry-drift check (confirmed broken since ≥2026-07-21).
- My new `capability-manifest.json` registry-drift check (this session).
- Potentially any OTHER cross-repo consumer that checks out UAC's `main` fresh and pip-installs it editable alongside a
  version-floor-pinned sibling.

## Root cause diagnosed (2026-07-26, slot 6)

**`v0.72.0` was a manual one-off "baseline" tag, and it was placed on the wrong side of the LDR↔main promotion
boundary.** Full evidence chain (all read-only: `git cat-file`, `git log`, `git merge-base --is-ancestor`,
`git branch --contains`, `git rev-parse ^{tree}`, `gh run list/view`):

1. `v0.72.0` is an **annotated** tag:
   `tagger ikennaigboaka [slot-3·laptop] … baseline release tag for git-tag migration (pyproject 0.72.0)`, created
   2026-06-27T14:40:55+0100 — the same day as the D13 `version_source=git-tag` rollout
   (`reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` dates D13 to `execution-service@f4a3865e`,
   2026-06-27). The message and human-operator tagger identity (the exact `[slot-N·host]` convention CLAUDE.md defines
   for agent/operator commits, not a bot) confirm this was a manual bootstrap tag, not an automated mint.
2. The tagged commit is `4ac8be3f` — **`Merge remote-tracking branch 'origin/staging' into _backmerge`** — one leg of
   the `main-backmerge-to-ldr` flow that folds `main`'s content back into `live-defi-rollout`.
   `git branch -a --contains 4ac8be3f` lists only `live-defi-rollout` (+ its derived `promote/*` and `wip-preserve/*`
   refs) — **`main` is never in that list.** This commit structurally lives on the LDR/backmerge side of the graph,
   never on `main`'s own.
3. `main` only ever advances via single-parent squash commits titled `chore(promote): LDR → main (Option-B direct)` —
   confirmed the pattern holds fleet-wide (every commit in `main`'s recent log matches) and confirmed by parent-count
   (e.g. `acbd08825` has exactly ONE parent). Each squash's parent is the PREVIOUS squash commit on `main`, never any
   LDR-side commit. So **no LDR/backmerge commit can ever become an ancestor of `main`, structurally, no matter how much
   time passes or how many further promotions land** — this isn't a lag that will resolve itself.
4. The content tagged `v0.72.0` DID land on `main` — **2 hours later**, as squash commit
   `b52aea5d237153ba74568b5cb195934cd255b361` (`chore(promote): LDR → main (Option-B direct)`,
   2026-06-27T16:37:46+0100), whose tree (`9c2d88022f10f9a8d4929bbfdfb5bdc593391763`) is **byte-identical** to the
   tagged commit's tree. `b52aea5d` is the one and only `main`-side commit that could have correctly carried this tag.
5. **Control case — `v0.71.0` (the tag hatch-vcs currently falls back to) was tagged directly on `acbd08825`, itself a
   `chore(promote): LDR → main` squash commit** — i.e. genuinely on `main`'s own graph, which is exactly why
   `git merge-base --is-ancestor v0.71.0 origin/main` succeeds. One tag was placed on the right side of the promotion
   boundary, the other wasn't; that is the entire delta between "works" and "doesn't".
6. Ruling out the automated minter as the actual cause: at tag-time (2026-06-27) `semver-agent.yml` triggered on
   `push:[staging]` (rolled out 2026-06-15) — a `_backmerge` merge commit was never something that trigger fires on
   regardless. And per the CURRENT `semver-agent.yml`'s own changelog comment, that `push:[staging]` path went fully
   dead the very next day: "the staging drain was stopped 2026-06-28 … staging never advanced → semver went dead
   fleet-wide → zero tags minted". So this was unambiguously a manual, one-time tag — not a minter bug.

**Adjacent finding for whoever executes todo 2 below** (not itself in scope here): `semver-agent.yml` was retargeted to
`push:[main]` on 2026-07-25 and IS firing SUCCESS on every subsequent `main` squash-promote
(`gh run list --workflow=semver-agent.yml --branch main`, 8/8 recent runs green) — any tag it mints there WOULD land
correctly on `main`'s own graph and self-heal this class going forward. However the most recent run (30197445904,
2026-07-26T09:59:29Z) shows its **bump-rate circuit breaker (≥3 pending bumps on main) TRIPPED**, refusing to dispatch a
new version bump — so no new tag has actually been minted since the retarget, and "wait for the next automated tag" is
not currently a live self-heal path until that breaker clears.

## Recommended decision

- [x] ✅ [DEVOPS] P2. Diagnose exactly how/when `v0.72.0` was tagged and why it isn't an ancestor of `main`'s current
      squash-commit chain (repo: unified-api-contracts) — unified-trading-pm@\<SHA\>. See "Root cause diagnosed" section
      above: manual D13-bootstrap tag placed on an LDR-side `_backmerge` commit instead of the corresponding `main`-side
      squash commit (`b52aea5d`, same tree, ~2h later); not a `semver-agent` bug.
- [x] ✅ [DEVOPS] P2. Once root-caused, decide the fix direction: (a) always tag on `main`'s own HEAD right after each
      squash-promote lands (never on an LDR-only commit), or (b) reconcile the existing gap by re-tagging `v0.72.0` (or
      a corrected release tag) onto current `main` HEAD if the tag is meant to represent "what's actually released on
      main" — do NOT silently move an existing tag without checking downstream consumers that may have already resolved
      a wheel against the old tag sha. — unified-trading-pm (this doc), see `## Decision` section below (slot 8,
      2026-07-26, **REVISED** after the (a)-only conclusion proved wrong): **(b) — force-retag `v0.72.0` onto `b52aea5d`
      — is the actual required fix; blocked on operator/main authorization for the shared-ref force-push, see `/blocked`
      question.**
- [x] ✅ [DEVOPS] P2. Implement direction (B) from main's `BLK-2d9aae3f` partial answer (authorized 2026-07-26, see
      "Decision" section below) — main approved proceeding with B now while A (force-retag) stays operator-reserved, but
      B was never captured as a tracked todo, so it hasn't landed. Harden the semver-agent tag-mint idempotency guard
      from existence-only (`git rev-parse "v${NEW_VERSION}"`, currently
      `scripts/workflow-templates/     semver-agent.yml.tmpl` lines ~721-725) to ancestry-aware
      (`git merge-base --is-ancestor "v${NEW_VERSION}" HEAD`) so a stale/unreachable pre-existing tag of the same name
      no longer silently short-circuits the mint (the exact "Tag v0.72.0 already exists — idempotent, nothing to do"
      wedge documented in the "Decision" section). Edit the TEMPLATE, never a per-repo workflow copy, then run
      `rollout-workflow-templates.sh` and verify every generated copy is committed + pushed (repo: unified-trading-pm).
      This is what would let the NEXT qualifying `main` promote mint a genuinely new, correctly-anchored tag (e.g.
      `v0.72.1`/`v0.73.0`) above the `>=0.72.0` floor — placed BEFORE todo "re-run registry-drift" below since that todo
      can only succeed once this lands (or A does) AND a new tag is actually minted on `main`. — DONE 2026-07-26 (slot
      6): template hardened at unified-trading-pm@85cca9314 (existence-only guard replaced with
      `git merge-base --is-ancestor "v${NEW_VERSION}" HEAD`; a genuine ancestor still idempotent-skips, a
      stale/unreachable same-name tag now `exit 1`s loudly instead of silent no-op). Ran
      `rollout-workflow-templates.sh --template semver-agent.yml.tmpl` and pushed the rendered copy to all 24 fleet
      repos (YAML-validated + diff-verified before push): alerting-service@7462d86,
      batch-live-reconciliation-service@76dfad7, client-reporting-api@8d26322, deployment-api@c31f6f8,
      deployment-service@d636b57, execution-service@37b5c61b, features-service@1bdae3e0,
      fund-administration-service@1f95b00, greeks-service@8d50a0f, ibkr-gateway-infra@5aff2e1,
      instruments-service@5deb3c52, market-data-processing-service@294f9fb, market-tick-data-service@c584de99,
      ml-service@0ff61d1, strategy-service@d4eae25a, system-integration-tests@822604d, trading-agent-service@bbbce47,
      unified-api-contracts@4db2f706, unified-trading-library@bd5180b7, unified-trading-api@ac66ace,
      unified-trading-system-ui@02072c74, deployment-ui@9ccf69c, e2e-testing@797a9de, agent-orchestrator@b4669c7. Note:
      unified-trading-system-ui and deployment-ui carried a stale pre-2026-07-25 semver-agent.yml copy (still on the
      retired `push:[staging]` trigger) — the rollout also caught those two fully current to the template as a
      byproduct, not just this guard change. This does NOT retroactively fix `main`'s existing wedged baseline (still
      `v0.71.0` per the ancestry gap) — that still needs direction A (force-retag `v0.72.0` onto `b52aea5d`,
      operator-reserved) or a brand-new tag past the floor; what this todo unblocks is that the NEXT qualifying mint
      attempt fails loudly instead of silently no-op'ing, so the wedge can no longer hide.
- [ ] [SCRIPT] P3. Once the tag-ancestry gap is fixed, re-run the `registry-drift` job on unified-trading-system-ui's
      `main`/next promote PR and confirm
      `pip install -e     _deps/unified-api-contracts -e _deps/unified-trading-library` succeeds (both the
      `ui-reference-data.json` AND `capability-manifest.json` diff steps should then execute for real, rather than the
      whole job dying at the install step).
- [x] ✅ [DOCS] P3. Cross-link this doc from `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` and
      `promotion_lag_alert_hides_provenance_block_2026_07_17.md` — same hatch-vcs/git-tag subsystem, adjacent failure
      modes, worth a shared "known rough edges" note so the next diagnosis doesn't restart from zero. —
      unified-trading-pm@pending (both docs' `related:` frontmatter + a "Known rough edge" body note added).

## Decision (2026-07-26, slot 8 — resolves todo 2)

Independently re-verified the root cause while making this call (parallel to -001's own diagnosis; corroborating, not
superseding it) — same evidence slot 6's "Root cause diagnosed" section above documents (manual D13-baseline tag on
LDR-only commit `4ac8be3f`, byte-identical to `main`-side squash `b52aea5d`, never reachable from `main`).

**First pass concluded (a) and is WRONG — corrected below after reading the actual semver-agent run log, not just the
workflow source.** My first read of `semver-agent.yml` (trigger `push:[main]` + checkout `ref: github.sha` + tag-mint
from that ref) is real and does mean every _future_ mint is ancestor-safe — but reading the source alone missed that the
mechanism is **currently wedged**, and will stay wedged indefinitely. Direction (a) alone does not fix this issue;
concrete evidence below.

**The self-heal does NOT happen — proven from the actual run, not inferred:** pulled the full log of the most recent
semver-agent run on `main` (`gh run view 30197445904 --log`, 2026-07-26T09:59:29Z, `completed/success` — NOT the
"circuit breaker tripped" the "Root cause diagnosed" section above reports; the literal log lines are
`Dynamic repo (version_source=git-tag): counted 0 v* tag mint(s) in the last hour` →
`Circuit breaker clear — proceeding.`, so that part of the adjacent finding is itself incorrect and should not be relied
on). What the log actually shows:

```
Baseline (latest git tag) for unified-api-contracts: 0.71.0      # main's own describe — the gap, live
Current version: 0.71.0
Resolved bump category: breaking
Label matches API diff ... breaking bump confirmed.
...
NEW_VERSION="0.72.0"   CURRENT="0.71.0"        # pre-1.0.0 override: breaking -> MINOR -> 0.72.0
version_source=git-tag — minting tag v0.72.0 (no pyproject commit)
Tag v0.72.0 already exists — idempotent, nothing to do.          # <- exit 0, SILENT no-op
```

This is the actual mechanism: because `main`'s baseline is pinned at `v0.71.0` (the ancestry gap), every future
breaking/minor-worthy promote computes the SAME `NEW_VERSION=0.72.0` forever — and the tag-mint step's idempotency guard
(`git rev-parse "v${NEW_VERSION}"`, workflow §721-724) checks tag _existence_, not _ancestry_. Since the stale,
unreachable `v0.72.0` object already exists in the repo's global ref namespace, every run hits the idempotent-skip
branch and exits 0 — a **green run that silently did nothing**, the exact "healthy no-op vs. broken lookup" failure
class `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` already names for a sibling workflow.
**There is no future promote, however qualifying, that breaks this loop** — waiting is not a fix.

**Direction (b) is therefore the correct, necessary fix — but as a ref-correction, not a version invention.** Move the
existing `v0.72.0` tag from `4ac8be3f` (LDR-only) to `b52aea5d237153ba74568b5cb195934cd255b361` (the `main`-side squash
commit slot 6 identified, confirmed **byte-identical tree** to the original — `9c2d88022f10f9a8d4929bbfdfb5bdc593391763`
both sides). This changes zero content, only the ref target, and directly answers the original todo's own downstream-
consumer caution: no GitHub release exists for `v0.72.0` (`gh release view v0.72.0` → not found), and
`publish-package.yml` is _also_ `push:[main]`-only, so no wheel was ever published under a clean `0.72.0` version string
(`main` never had the tag reachable to resolve it) — nothing downstream is pinned to the current tag sha. Once
re-pointed: `main`'s baseline immediately reads `0.72.0` (unblocking `pip install` today), and the NEXT qualifying
promote computes `0.72.1`/`0.73.0` against a live, correctly-anchored baseline — no idempotency collision, no manual
version invention, self-healing resumes exactly as (a) describes for everything after this one correction.

**Not executed in this task.** Force-moving a published tag on a shared upstream ref is exactly the kind of
consequential, git-push-adjacent action `RULES.md`/CLAUDE.md gate to human/main-agent authorization (same family as
"never force-push a shared branch") — filed as a `/blocked` question with this evidence + recommendation rather than run
`git push --force origin v0.72.0` unilaterally. -003 (re-run `registry-drift`) stays correctly blocked until the retag
lands.

## Provenance

Found 2026-07-26 while executing `defi_wizard_batch2_018_residual_findings-004` (extend `registry-drift` for
`capability-manifest.json`) — verifying the new CI job end-to-end against real GHA runs per that todo's explicit
instruction ("do not assume a config-only guess is correct"). Diagnosed read-only: `gh run view --log`,
`git describe --tags`, `git merge-base --is-ancestor`, `git diff --stat`, `git rev-parse ^{tree}` across 6 repos. No
repo was touched by this investigation; the `fetch-depth: 0` half-fix IS shipped as part of
`defi_wizard_batch2_018_residual_findings-004`'s own commit (unrelated bug, fixed because it blocked verifying my own
change and is a genuine independent improvement either way).

## 2026-07-26 premature-dispatch finding + `sequential: true` fix (slot 10)

Dispatched todo 3 (`-003`, `[SCRIPT] P3. Once the tag-ancestry gap is fixed, re-run the registry-drift job...`) fresh.
That todo's own text is explicitly gated on todos 1 and 2 (`[DEVOPS] P2` root-cause + fix) landing first — but this doc
had no `sequential: true` and no `depends_on`/`gate_on_depends` split, so the backlog deriver dispatched all of 1/2/3
independently instead of enforcing the chain (the "no per-todo prereq syntax" gap `task_template.md` warns about: a
todo's prose dependency does nothing on its own — only `sequential: true` or a `depends_on`+`gate_on_depends` plan-split
actually gates dispatch).

Re-verified the root cause is still genuinely open before touching anything: `git fetch origin main --tags` +
`git describe --tags origin/main` → still `v0.71.0-158-gb22f9fca`; `git merge-base --is-ancestor v0.72.0 origin/main` →
still NOT an ancestor (vs. `origin/live-defi-rollout`, where it IS). `GET /api/backlog` confirmed `-001` and `-002` are
both `dispatched` (in progress elsewhere), neither `done`. Re-running the `registry-drift` job now would reproduce the
exact same `ResolutionImpossible` failure documented above — flipping todo 3's checkbox now would be a false-completion
claim (the failure mode `check_evidence_backed_completion.py` / the runtime-verification HARD RULE exist to stop).

**Fix applied** (adjacent, in this same file — this doc IS my `plan_ref`): added `sequential: true` to the frontmatter
above. Todos 1→2→3→4 are a genuine dependency/documentation chain in this small (4-todo) doc — no reason to split into a
gated plan-pair for something this size, per `task_template.md`'s own guidance ("a real dependency chain... →
`sequential: true`"). This does not undo the two already-in-flight dispatches of `-001`/`-002` (which happened before
this fix landed), but it should stop `-003`/`-004` from being re-offered to another slot until their true predecessors
are `done`. Declining to flip todo 3's checkbox; skipping this task (`reason_code: GATED`) rather than fabricating
completion. Root cause (this doc's own todos 1-2) is still unfixed as of this note.

## 2026-07-26 re-verified still GATED + captured the missing "B" todo (slot 4)

Dispatched `-003` again. Re-verified live before touching anything: `git fetch origin main --tags` in
`unified-api-contracts` → `git describe --tags origin/main` still `v0.71.0-160-g40177041`;
`git merge-base --is-ancestor v0.72.0 origin/main` still NOT an ancestor (vs. `origin/live-defi-rollout`, where it IS).
Confirmed via `GET /api/backlog` and the activity log that todo 2's decision produced `BLK-2d9aae3f`, which main
answered `PARTIAL` (2026-07-26T10:56Z): proceed with direction B (harden the semver-agent idempotency guard to be
ancestry-aware) now; direction A (force-retag `v0.72.0` onto `b52aea5d`) stays HELD pending operator authorization.
**Gap found**: B was authorized but never turned into a tracked todo — no backlog task or checkbox existed for it
(confirmed via `GET /api/backlog` grep for `semver`/`ancestry-aware`/`idempotency` — zero hits), so it could never
actually get dispatched or executed. This is the same "decision made but not captured as a `- [ ]` todo" gap
`RULES.md`/CLAUDE.md's "capture discoveries as plan todos immediately" rule exists to close.

**Fix applied**: added the B-implementation todo above (`[DEVOPS] P2`, names the exact template file + lines + rollout
script), positioned it BEFORE the `-003` SCRIPT todo in document order (this doc is `sequential: true`, so doc-order
gates dispatch) — `-003` cannot correctly precede its own unblocking work in a sequential chain, so I moved it rather
than appending at the end. Re-running `registry-drift` now would reproduce the exact same `ResolutionImpossible` failure
already documented above; flipping `-003` would be a false-completion claim. Declining to flip todo 3 (the SCRIPT
re-run); skipping this task (`reason_code: GATED`). Neither A nor B has landed as of this note — the gap is still open.
