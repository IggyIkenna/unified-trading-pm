---
title:
  "semver-agent version-bump `[skip ci]` blocks staging→main promotion (+ re-bump loop) — root cause + recommended fix"
created: 2026-06-09
source:
  - plans/active/issues/ci_incident_findings_2026_06_09.md
  - plans/active/dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md
  - codex/08-workflows/ci-cd-flow.md (§ "[skip ci] and required checks")
locked_by: live-defi-rollout
status: active
priority: P1
---

# semver-agent `[skip ci]` version-bump blocks promotion — root cause + recommended fix

> **✅ MIGRATED 2026-06-09 → `plans/active/cicd_contract_hardening_2026_06_01.md` § "Auto-remediation pipeline gaps"
> (Option C is now a dispatchable `[SCRIPT] P1` todo there, target repo `unified-trading-pm`).** The watcher-disposition
> open question (§10 Q3) is RESOLVED: do NOT retire `ci-failure-watcher` — `--escalate` (merge-conflict / sit_failure
> walls) is untouched and `--auto-recover` stays as a backstop for any non-semver v2-never-reported head (it is
> signature-keyed, not dead code); §8's "retire the band-aid" wording over-reached. This doc remains as the design
> rationale; ARCHIVE CANDIDATE once Option C ships. The cross-link is also recorded in
> `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md` Phase 3.

> **For review by Ikenna + Harsh.** This is a fleet-wide CI/CD design decision (touches the rolled-out
> `semver-agent.yml` + `quality-gates-v2.yml` templates). No code has been changed by this doc — it is a proposal. The
> immediate incident has a manual recovery; this doc is about the **permanent** fix.

## TL;DR

The release version bump is committed as a **separate `chore(release): bump version to X [skip ci]` commit on
`staging`**. Because `staging`→`main` is a **`quality-gates-v2`-required PR**, and `[skip ci]` produces **zero check
runs**, that bump commit (when it is the PR head) makes the required check **MISSING → the PR is permanently BLOCKED**,
which also feeds a **re-bump loop** (the change never releases → semver-agent re-bumps → `0.2.0 → 0.3.0 → 0.4.0`).

**Recommended fix (Option C):** stop using `[skip ci]` on the bump commit, and add a **"version-only" fast-path** to
`quality-gates-v2` so a commit whose entire diff is the `version =` line **reports the required check green in seconds**
(nothing to test). This unblocks the promotion **without** re-running the full ~12-min gate on a zero-code commit, keeps
the version in `pyproject.toml`, and is loop-safe (the existing chore-skip already prevents re-trigger). Smallest blast
radius of all options considered.

---

## 1. The incident (concrete evidence, 2026-06-09)

- `execution-service` staging→main PR **#231** = `mergeStateStatus: BLOCKED`, **0 checks on the PR head**.
- The PR head (the `staging` HEAD) = `2d8c0ce5 "chore(release): bump version to 0.3.0 [skip ci]"` → **no check runs**.
- Required context on `main` = `Quality Gates (execution-service) / quality-gates-v2` → **MISSING** (never ran), not
  failing. GitHub will not let `--admin` bypass a never-reported required check.
- The LDR→staging PR **#230** was fully green + `CLEAN` — the cascade was gated entirely on #231.
- The version then escalated **`0.3.0 → 0.4.0`** mid-investigation (staging head moved to
  `9f627f3c "chore(release): bump version to 0.4.0 [skip ci]"`) — the re-bump loop. A manual recovery
  (`gh workflow run quality-gates-v2.yml --ref staging`) ran green but on the now-stale `0.3.0` head, so it did not
  stick. Manual recovery is whack-a-mole against a moving `[skip ci]` head.

## 2. How the bump works today (universal, every staging-flow repo)

1. Code lands on `staging` → `quality-gates-v2` runs.
2. On success, `semver-agent` (triggered by `workflow_run` on QG success, branch `staging`) computes the bump from
   conventional commits + the AST public-surface differ (`scripts/cicd/detect_breaking_change.py`).
3. `semver-agent` commits **`chore(release): bump version to X [skip ci]`** to `staging`, touching **only** the
   `pyproject.toml` `version =` line. _(semver-agent.yml ~:477)_
4. `semver-agent` dispatches `version-bump` to PM carrying the **original code SHA** (not the bump commit) + `version` +
   `is_breaking`. _(semver-agent.yml ~:490-517)_
5. PM `update-repo-version.yml` updates `staging_versions{}` (and `versions{}` on promotion), records `commit_sha` as
   **metadata**, bumps PM's own patch, and — if `is_breaking` — locks staging + fans the SIT cascade to dependents.
   Manifest writes are serialized by a `manifest-update` concurrency group. _(update-repo-version.yml ~:24-26, :131-152,
   :311-332, :360-383)_
6. The bumped `staging` promotes to `main` via the required-check PR; the **release image is tagged by VERSION**
   (`cloud-build-router.yml`, `IMAGE_TAG="${VERSION}"`), **not** by commit SHA, built on the `main` QG run after the
   bump reaches main.

## 3. The two structural flaws (independent of any one PR)

1. **A `[skip ci]` commit can never satisfy a required-check-gated PR head.** The bump lands _on staging_, and
   staging→main is a `quality-gates-v2`-required PR, so the bump commit is **structurally unmergeable** through that
   gate. There is a band-aid (`ci-failure-watcher --auto-recover` close+reopens to re-fire v2), but it fights the
   symptom and loses to churn.
2. **Bump-then-block creates a re-bump loop.** A blocked promotion means the change stays "unreleased," so any further
   `staging` churn re-triggers `semver-agent` and the version escalates (`0.2→0.3→0.4`).

This is exactly the foot-gun already codified as a _rule_ in `codex/08-workflows/ci-cd-flow.md` ("never `[skip ci]` a
commit that becomes the HEAD of a v2-gated promotion PR") — but the **semver-agent itself violates it on every
release**, so the rule needs a _mechanism_ fix, not just documentation.

## 4. Scenarios the fix must cover (whole fleet)

| Dimension   | Cases                                                                                                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repo type   | service (Docker image) · library (wheel, no image) · UI (+Playwright) — all use the staging flow; **PM + agent-orchestrator** are main-direct (no staging)             |
| Bump kind   | non-breaking patch/minor (range-pins absorb, no consumer rebuild) · breaking (locks staging + SIT cascade) · chore/docs (no bump) · post-1.0.0 MAJOR (manual approval) |
| Concurrency | multiple repos bumping at once → PM manifest writes serialized by the `manifest-update` concurrency group                                                              |

## 5. Edge cases the fix must NOT break (verified, with pointers)

- **Loop prevention is DUAL** — `[skip ci]` **and** the `chore(release)` → "no bump, skip" path _(semver-agent.yml
  ~:264-268)_. So **removing `[skip ci]` does not loop**: the chore-skip catches the re-trigger. This is the key
  enabling fact for Option C.
- **Breaking cascade** triggers off the dispatched `is_breaking` flag + manifest lock — **independent** of where/how the
  bump commit is CI-treated. Unchanged by Option C.
- **Image = VERSION-tagged** (not SHA). Version must be final at the **main** build (after the bump reaches main).
  Option C preserves this (bump on staging → promote to main → main build = bumped version).
- **`commit_sha` = code SHA, metadata only** — no SHA pin / no cryptographic signing anywhere (verified: no
  cosign/sigstore/gpg/sha256/attestation in the release path). Moving/retreating the bump commit breaks no signature.
- **Baseline detection greps `"bump version to X"`** — the commit-message format is load-bearing; **keep it verbatim**.
- **main→LDR backmerge, Option-B phantom exclusion (PM/AO), manifest race serialization** — all orthogonal to the bump's
  CI treatment; untouched.

## 6. Candidate fixes evaluated

| Option                                                          | Unblocks PR | No wasteful QG | Version stays in toml | Image timing OK                        | Blast radius                                                | Verdict         |
| --------------------------------------------------------------- | ----------- | -------------- | --------------------- | -------------------------------------- | ----------------------------------------------------------- | --------------- |
| **A** — bump on `main` directly post-merge (`[skip ci]` direct) | ✅          | ✅             | ✅                    | ❌ no main QG → image/version mismatch | medium                                                      | Rejected        |
| **B** — fold bump into LDR→staging promotion content            | ✅          | ✅             | ✅                    | ✅                                     | **large** (moves bump pre-SIT; re-wire cascade/lock timing) | Long-term ideal |
| **C** — drop `[skip ci]` + version-only fast-path in QG-v2      | ✅          | ✅ (seconds)   | ✅                    | ✅                                     | **small** (2 template tweaks)                               | **Recommended** |

- **Why not A:** a `[skip ci]` bump on `main` produces no QG run → no image build on the bumped version → the image tag
  (VERSION) and the manifest disagree.
- **Why B is deferred:** conceptually cleanest (no separate bump commit at all, one QG covers code+bump), but it moves
  the bump _before_ SIT (today it is deliberately post-SIT) and requires re-wiring the breaking-cascade/lock timing —
  more new edge cases than warranted for the immediate problem.

## 7. Recommended fix — Option C (detail)

"Option 1 made smart": the bump commit gets a **real required check that returns in seconds** because its diff is only
the version line (nothing to validate). Two rolled-out-template edits:

**(a) `semver-agent.yml`** — drop `[skip ci]` from the bump commit message:

```
- git commit -m "chore(release): bump version to ${NEW_VERSION} [skip ci]"
+ git commit -m "chore(release): bump version to ${NEW_VERSION}"
```

Loop safety: the re-trigger is already caught by the chore-skip (§5), so `[skip ci]` is redundant for that purpose. Side
benefit: the bump now propagates via `staging-backmerge-to-ldr` immediately instead of waiting on the drift-tick cron.

**(b) `quality-gates-v2.yml`** — add a **first step** in the `quality-gates-v2` job that short-circuits a version-only
commit:

```
# Pseudocode — first step of the quality-gates-v2 job (same job → same required-check context name)
DIFF=$(git diff --name-only HEAD~1 HEAD)
if [ "$DIFF" = "pyproject.toml" ] && \
   git diff HEAD~1 HEAD -- pyproject.toml | grep -qE '^[+-]version = ' && \
   ! git diff HEAD~1 HEAD -- pyproject.toml | grep -qvE '^([+-]version = |[ +-]|@@|diff |index |--- |\+\+\+ )'; then
    echo "Version-only change — nothing to validate; reporting green."
    # DO NOT dispatch qg-passed / image build for a metadata-only staging commit.
    exit 0
fi
# ...otherwise run the full gate as today...
```

Implementation requirements (get these exactly right):

1. The fast-path **must run inside the same `quality-gates-v2` job** so it reports the exact required context
   `Quality Gates (<repo>) / quality-gates-v2` (branch protection matches on that string).
2. It must trigger **only** when the diff is _solely_ the `version =` line — semver-agent already guarantees the bump
   commit touches nothing else, so this is a clean, safe signal.
3. It must **skip the `qg-passed` / image-build dispatch** (no rebuild for a metadata-only commit; the real image is
   built on the `main` QG run after promotion).

## 8. Why C is the right fleet-wide call

- Satisfies all constraints: version stays in `pyproject.toml`; **zero wasteful QG** (version-only ⇒ seconds); no
  crypto/SHA breakage (verified).
- **Kills both flaws:** the promotion PR head always carries its required check (no block); once it merges the change is
  released, so the re-bump loop stops.
- **Loop-safe by construction** — chore-skip already prevents re-trigger.
- **Uniform** for service/library/UI; PM + agent-orchestrator (main-direct) were never the problem and are unaffected
  (their `[skip ci]` manifest commits land directly on `main` — the documented-safe case).
- Lets us **retire the `ci-failure-watcher` close+reopen band-aid** for this case.

## 9. Rollout (when approved)

1. Edit the **PM templates** `scripts/workflow-templates/semver-agent.yml` +
   `scripts/workflow-templates/quality-gates-v2.yml` (never per-repo copies).
2. `bash scripts/propagation/rollout-workflow-templates.sh` (PM's own copy is hand-maintained — align it too).
3. Land via the sanctioned PM `scripts/**` + `.github/**` carve-out (chicken-and-egg: a corrected gate can't pass
   through the gate it fixes).
4. Verify on the next real release that: (a) the bump commit reports `quality-gates-v2` green in seconds, (b) the
   staging→main PR merges without manual recovery, (c) no version escalation, (d) the `main` image is tagged with the
   bumped version.

## 10. Open questions for Ikenna

1. **C now, B later?** Adopt C as the immediate fleet fix, and keep B (bump folded into the promotion content, zero
   extra commits) as a future cleanup — or go straight to B?
2. **Fast-path scope:** is "diff is exactly the `version =` line" the right trigger, or should it also cover the PM
   `chore(manifest): … [skip ci]` commits (those land direct-on-main, the safe case, so probably out of scope)?
3. **Retire the band-aid?** OK to drop the `ci-failure-watcher` close+reopen auto-recovery for the
   `[skip ci]`-promotion-head signature once C lands (it becomes dead code)?

## Appendix — crypto/SHA safety check (done 2026-06-09)

- **No cryptographic signing** of commits or release artifacts (no cosign/sigstore/gpg/sha256/attestation in the release
  path; the `signature` hits are _function signatures_ in `detect_breaking_change.py`).
- **Release image = VERSION-tagged** (`cloud-build-router.yml` `IMAGE_TAG="${VERSION}"`), so the commit SHA is **not**
  the artifact identity.
- **SHA coupling is metadata + a commit status only** (PM manifest records `commit_sha`; semver-agent posts a SHA-keyed
  label-vs-API-diff status) — neither is cryptographic, neither pins the artifact.
- Conclusion: relocating/retreating the bump commit (Option B or C) breaks **no** signature, hash, or pin.

---

## 11. Implementation status (2026-06-09, Harsh — Option C, BROADENED to metadata-only)

### New finding: the `[skip ci]` flaw has a **second source** (dep pins), not just semver bumps

When validating on the live blocker, the actual `execution-service` staging→main PR **#231** head was **not** a semver
bump — it was **`dd24b100 chore(deps): pin unified-api-contracts to 0.3.0 [skip ci]`**, produced by
`update-dependency-version.yml` (MINOR/PATCH dep bump → `[skip ci]` direct commit, "compatible update, no QG needed").
**Identical structural flaw, sibling source.** So the fix must cover BOTH `[skip ci]` producers, not just semver-agent.

### What shipped (broadened: "version-only" → **metadata-only**)

- **`python-quality-gates-v2.yml`** (reusable, `@live-defi-rollout` → all repos immediately): fast-path now matches a
  commit whose message is **`chore(release): bump version to …`** OR **`chore(deps): pin …`** AND whose diff is confined
  to **`pyproject.toml`/`uv.lock`** → skips clone/sync/run, reports `quality-gates-v2` GREEN in seconds, emits output
  `metadata_only`. Fires on **`push` and `workflow_dispatch`** (so manual recovery of a stuck head is fast too). A MAJOR
  dep update is a `feat!:` PR with full QG (not matched).
- **`semver-agent.yml.tmpl`**: bump commit drops `[skip ci]` (loop-safe; chore-skip prevents re-trigger).
- **`update-dependency-version.yml`**: MINOR/PATCH pin commit drops `[skip ci]` (preserves the existing "no QG needed"
  decision via the fast-path).
- **`quality-gates-v2.yml.tmpl`** caller: skips the `qg-passed`/image dispatch when `metadata_only == 'true'`.

**Landed:** PM LDR `86013a1d2` → `6cbaa92b9` → `303d62d21` (SSOT + templates). Rolled out to **execution-service only**
(operator decision) on its LDR `c63f6c09`. Reusable fast-path is **live for all repos** now (via `@live-defi-rollout`).

### Validated (deterministic, no live CI)

Ran the reusable's detection logic against #231's exact head `dd24b100`: message matches `chore(deps): pin …`, changed
files = `pyproject.toml` only → **`metadata_only=TRUE`** → the fast-path would report `quality-gates-v2` GREEN on that
commit. So once active, #231 unblocks without a wasteful full run.

### NOT yet done — entangled live recovery (needs a decision)

The live `execution-service` recovery is **not** a clean apply: `staging` carries a tangle of stacked `[skip ci]`
commits with a version escalation (`0.2.0→0.3.0→0.4.0`) and a manifest mismatch (`versions=0.3.0` vs
`staging_versions=0.4.0`, while `pyproject` reads `0.1.1` after a clean-start force-sync). To recover #231 so it
**sticks**, the new `semver-agent.yml` (no `[skip ci]`) must first reach `execution-service` **main** (admin
`.github/**` carve-out) — otherwise the still-old main semver-agent can re-bump on the next QG-green (whack-a-mole).
Merging the tangled staging to main also needs the escalation artifacts reconciled. **This is live-incident untangling
in the CICD domain → coordinate before executing.**

### Updated open questions for Ikenna

1. **Live recovery of `execution-service` #231**: OK to (a) admin-push the 3 fixed workflows to `execution-service`
   `main`, then (b) reconcile the staging version-escalation tangle + recover #231 via the fast-path? Or do you want to
   drive the untangle?
2. **Full 24-repo rollout**: the per-repo rollout also carries 3 of your pending template changes (checkout@v5/
   setup-python@v6, content-based breaking-detection, chore-release-before-dispatch) — proceed fleet-wide, or sequence
   them yourself?
3. **C now, B later?** (unchanged — fold the bump into the promotion content as a future cleanup).
4. **Retire the `ci-failure-watcher` close+reopen band-aid** for this signature once the fleet has the fast-path?

---

## 12. Recurrence 2026-06-10 — fleet rollout still pending, 17 repos re-jammed (Ikenna, slot-1)

**Confirms OQ #2 is the live gap.** A day after §11's fix landed on PM templates + `execution-service`, the
`update-dependency-version.yml` `[skip ci]` producer is **still active on every other repo**, so the
`unified-api-contracts 0.5.0` promotion wave (dep-pin commits dispatched ~23:57 UTC 2026-06-09) re-created the exact
deadlock fleet-wide.

### Evidence (swept 2026-06-10 ~01:1x UTC)

- **17 repos** had a `[skip ci]` staging tip with **`status=pending`, 0 check-runs** (the unsatisfiable-required-check
  state): `agent-orchestrator` (a `chore(release)` bump), and 16 `chore(deps): pin … [skip ci]` tips on
  `alerting-service · batch-live-reconciliation-service · client-reporting-api · deployment-api · deployment-service · features-service · fund-administration-service · greeks-service · instruments-service · market-data-processing-service · market-tick-data-service · ml-service · strategy-service · system-integration-tests · trading-agent-service · unified-trading-api`.
- Surfaced via **`deployment-api#36` `chore(release): promote staging to main` = BLOCKED** (head
  `a79715e7 chore(deps): pin unified-api-contracts to 0.5.0 [skip ci]`, required
  `Quality Gates (deployment-api) / quality-gates-v2` = MISSING). `trading-agent-service#31` /
  `system-integration-tests#46` were masked as BEHIND (same latent block, behind main first).
- Root cause line still present: `update-dependency-version.yml:151` — `git commit -m "chore(deps): pin … [skip ci]"`
  (the MINOR/PATCH path). The reusable `python-quality-gates-v2.yml` metadata-only fast-path **is** live fleet-wide via
  `@live-defi-rollout`, but `[skip ci]` suppresses the trigger entirely, so the fast-path never gets a chance on the
  push — confirming the fix is incomplete until the per-repo `update-dependency-version.yml` edit (drop `[skip ci]`)
  reaches each repo.

### Immediate recovery performed (slot-1, 2026-06-10)

- Dispatched `gh workflow run quality-gates-v2.yml --ref staging` on **all 17** affected repos (workflow_dispatch is not
  suppressed by `[skip ci]`). Verified on the `deployment-api` canary: `quality-gates-v2` now `completed/success` on
  `a79715e7`, so the required context reports on the staging tip. This is the documented manual recovery from §1, now
  fast via the reusable fast-path. (Note: `deployment-api#36` had already been closed by semver-agent at 01:10 — the
  dispatch keeps the staging tip promotable for the next promotion PR rather than recovering that specific closed PR.)

### Residual action (the actual fix — tracked, not yet done)

- **Complete the fleet rollout** of the `update-dependency-version.yml` (drop `[skip ci]`) + `quality-gates-v2.yml`
  caller edits to the remaining ~17 repos (only `execution-service` got them per §11's operator decision). Until then,
  **every future dep-pin re-jams that repo's staging→main promotion and needs a manual dispatch** — manual recovery is a
  band-aid against a recurring producer. This is OQ #2 / the `[SCRIPT] P1` rollout todo in
  `plans/active/cicd_contract_hardening_2026_06_01.md` § "Auto-remediation pipeline gaps".

## 13. Incident 2026-06-10 — cascade SIT parked ~5 h on a 1-char lint error in the harness repo (Harsh, slot-3)

A **third, distinct promotion-block class** (≠ the `[skip ci]` producer of §1–12): the cascade validation **conflates
SIT-harness repo hygiene with cohort integration validity**.

### Mechanism

- `ml-service=0.3.0` breaking cascade locked staging at 01:41Z. Each validation attempt = `workflow_dispatch`
  `quality-gates-v2` on **system-integration-tests LDR**.
- SIT LDR HEAD `e712ab1` (slot-1, 02:47Z, `fix(sit): UAC adoption …`) carried a Unicode `∪` in a COMMENT
  (`tests/integration/test_uac_completeness.py:44`) → ruff **RUF003** → lint-codex slice fails → v2 fails → cascade
  cannot validate. Tests + typecheck slices were green throughout.
- 3 retries exhausted (`sit_retry_count` = cap) → **parked**; `locked_alert_sent=true` but no actor picked it up for ~5
  h; meanwhile ci-failure-watcher kept re-dispatching v2 on the **same broken SHA** (03:03 / 04:59 / 06:35Z) —
  re-fire-without-root-cause burn.

### Recovery performed (slot-3, 2026-06-10 ~06:45Z)

1-char fix `∪`→`+`, local QG green (191 s), direct LDR push `system-integration-tests@429cc26` under the chicken-and-egg
carve-out (quickmerge STAGE 1.5 hard-blocks on the very lock the fix clears), then `sit-debounce-trigger`
`drain_pending=true` (resets the retry counter + re-dispatches). Retries reset 3→1, `pending_repos` shrank to
`['ml-service']`, v2 re-ran on the fixed SHA.

### Open items

- [ ] [SCRIPT] P2. Decouple harness hygiene from cascade validity — the cascade unlock should not hinge on the SIT
      repo's OWN lint/codex slice (route a harness lint failure to a fix-task; gate the unlock on the
      tests/cross-repo-invariants slices). Repos: `unified-trading-pm` (`sit-debounce-trigger.yml`/`sit-gate.yml`) +
      `system-integration-tests`.
- [ ] [SCRIPT] P2. Retry-cap parking is alert-only — `locked_alert_sent` fired and nothing acted for ~5 h. Teach
      `ci_failure_watcher.py` (or the debounce) to diff the failing slice log on retry-cap and dispatch a fix task /
      orchestrator ping with the extracted error, instead of re-firing v2 on an unchanged SHA. Repo:
      `unified-trading-pm`.
- [ ] [PROCESS] P3. A lint-red commit reached SIT LDR at all — QG-before-commit should have caught RUF003 locally. Audit
      the producing path (direct push without Pass-1 QG, or ruff version/config skew on the producing host).
