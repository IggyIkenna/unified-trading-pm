---
title:
  UTL main quality-gates-v2 RED while LDR is GREEN — dep-resolution skew on testnet-contracts / UAC registry during
  in-flight UAC promotion
created: 2026-06-11
source:
  - unified-trading-library main quality-gates-v2 run 27357450067 (FAILURE, head e8622793)
  - unified-trading-library LDR quality-gates-v2 runs 27357535116 + 27357977210 (SUCCESS, same content era)
locked_by: live-defi-rollout
priority: P1
status: active
---

## What I found

`unified-trading-library` (T0 base library) `main` `quality-gates-v2` is **FAILING** (run 27357450067, head `e8622793`,
the CURRENT main tip) while the SAME-era `live-defi-rollout` v2 is **GREEN** (runs 27357535116 @ 15:20, 27357977210 @
15:27). There is **no open staging→main PR** to heal it, and main is `ahead 31 / behind 4 / 13 files` vs LDR.

The failing tests (9 test files) are all empty-registry / wrong-resolution assertions:

- `AssertionError: assert 'aave_v3' in []`
- `AssertionError: assert 'pool' in {}`
- `AssertionError: assert <PipelineMode.BATCH_DATABENTO> is <PipelineMode.BATCH_MASSIVE>` (the `0bbed198` "fix stale
  databento asserts" commit landed but the assert still fails on main)
- `assert len(registry.contracts) > 0` → `assert 0 > 0`
- widespread `ValueError: I/O operation on closed file` (logging/fixture teardown after the registry errors)

Diagnosis: these come from
`7124adb8 fix(testnet-contracts): resolve testnet_contracts.yaml from installed UAC package via importlib.resources` +
`0bbed198` (BATCH_MASSIVE source-priority, a UAC `feat!`). On **main**, the version-aware clone resolves
`unified-api-contracts` to its released main-line TAG, which does NOT yet carry the relocated `testnet_contracts.yaml` /
the new registry data / the massive-first source-priority — so the registry resolves EMPTY (`[]`/`{}`) and the
pipeline-mode resolves to the old `BATCH_DATABENTO`. On **LDR**, the clone resolves UAC to LDR (which HAS the new data)
→ green. This is a **dependency-resolution skew during an in-flight UAC promotion**: UTL's new commits depend on UAC
content that has reached LDR but not yet the UAC released tag UTL `main` resolves against.

## Why it matters

UTL is T0 — every service resolves it. A red UTL `main` (a) blocks the LDR→staging→main drain Tier-A gate for UTL and
everything downstream, and (b) is a real "main lags during promotion" dam. It is NOT a code bug (LDR is green); it is a
promotion-ordering problem: UTL's main needs the aligned UAC release first.

## Recommended decision

- [x] ✅ [CICD] P1. Heal UTL `main` by completing the dependency-aligned promotion in dep order: ensure
      `unified-api-contracts` promotes its new registry/`testnet_contracts.yaml`/source-priority content to its
      main-line release FIRST, THEN promote `unified-trading-library` LDR→staging→main so its version-aware clone
      resolves the aligned UAC and the 9 test files pass. Do NOT "fix" the asserts or pin UAC differently — the asserts
      are correct against the new UAC; the skew is purely promotion-ordering (LDR proves the content is green). If the
      drain is stuck (no staging→main PR opening), open it manually once UAC main carries the aligned content.
      **RESOLVED 2026-06-16 (operator-authorized force-sync).** The drain WAS stuck: UAC `main` was pinned at **0.11.0**
      (12 commits behind LDR — all already ⊆ LDR, no main-only content) while staging/LDR were at **0.13.0**, and the
      `staging→main` promote PR **#339 was DIRTY** (conflicting only on `pyproject.toml` version + `semver-agent.yml`).
      Per the "LDR is the SSOT — clean-start force-sync" model, ran
      `admin-force-sync-all-to-main.sh --repo unified-api-contracts --no-commit [--stag-branch] --force-version-override`
      (version-drift gate flagged only NON-target repos — manifest-surface noise — so the override was safe; UAC itself
      had no drift). Result: **main == staging == LDR == `6c74eaf0` (0.13.0)**, #339 auto-resolved to MERGED, UAC `main`
      `quality-gates-v2` GREEN. UTL side confirmed: latest UTL LDR build (`71eddf9`, the current tip) is **SUCCESS**
      (the alerted `a57dc44` cloud-build FAILURE @17:55 was a transient sibling-context resolve; builds @18:57/19:09
      recovered, and the force-sync now makes the index-resolution path coherent too).
- [x] ✅ [CICD] P1. SHIPPED 2026-06-16 (unified-trading-library@b859a1532 cloudbuild.yaml — in-image QG installs UAC
      editable from the cloned sibling, not the lagging index; external deps still index-resolved). **SYSTEMIC — the
      floor-outpaces-publish lag RECURS every UAC version bump (per-version whack-a-mole; observed 0.13→0.14→0.15 on
      2026-06-16).** Root cause precisely: the **UTL Cloud Build's `quality-gates` step (Step #7, INSIDE the image)
      resolves `unified-api-contracts` from the published INDEX** (the Dockerfile installs the editable sibling at line
      88, but the in-image QG re-installs with `--no-sources` → index), so during the window between
      `chore(deps): pin unified-api-contracts to X` landing on the consumer's LDR and UAC `X` reaching
      `main`+publishing, the build fails `No matching distribution unified-api-contracts>=X`. The **GHA QG does NOT hit
      this** — it resolves from the editable sibling source (`file:///…`, verified on features-service:
      `OK 0.15.0 satisfies >=0.15.0`). So it is cloud-build-specific + TRANSIENT (self-heals in minutes once UAC
      publishes — UTL build abe97c24 went green at 20:51 once 0.14.0 landed). Fix options (pick one): (a) make the
      in-image QG resolve internal deps from the sibling source like the GHA QG / the Dockerfile line 88 (drop
      `--no-sources` for internal deps); (b) order the consumer floor-bump fan-out AFTER UAC publishes (trigger on UAC
      `main` promotion, not the staging version bump); (c) don't bump the floor on a non-breaking UAC minor
      (range-absorb per the pull-not-push model — only re-pin on a real breaking change). NOTE distinct from the v0.15.0
      CASCADE failures (features-service/fund-administration-service), which are a REAL breaking change — UAC renamed a
      `CoverageVerdict` value (`out_of_coverage`→`upstream_missing`) — needing code updates, not a dep-lag.
- [ ] [CICD] P2. **DEFERRED** Confirm whether the `ValueError: I/O operation on closed file` cascade is purely a
      teardown artifact of the registry-empty failures (expected to vanish once the registry resolves) or a separate
      logging-fixture bug; if the former, no action — provenance: run 27357450067.
