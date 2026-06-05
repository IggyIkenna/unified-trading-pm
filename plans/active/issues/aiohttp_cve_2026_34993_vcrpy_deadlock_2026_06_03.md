---
title: Fleet dep-infra blockers — aiohttp CVE-2026-34993 vs vcrpy deadlock + deployment-service pyproject duplicate-key
created: 2026-06-03
author: ikennaigboaka [slot-6·laptop]
source:
  - features-service quality-gates.sh pip-audit (CVE-2026-34993)
  - unified-api-contracts quality-gates.sh (64 vcrpy AttributeError on aiohttp 3.14.0)
  - deployment-api uv lock --upgrade-package aiohttp (deployment-service pyproject TOML parse error)
locked_by: live-defi-rollout
---

## What I found

Two **pre-existing, fleet-wide** dependency-infra blockers surfaced while shipping tradfi-manifest-canonicalisation code
(they block EVERY repo's local QG / `uv lock`, not just tradfi). Both are now fixed at the SSOT; this doc records the
decision + the successor.

### 1. aiohttp CVE-2026-34993 (RCE) deadlocks every VCR-using repo

- **CVE-2026-34993** (newly published; in the OSV DB as of 2026-06-03): `aiohttp <= 3.13.5` — `CookieJar.load()` with
  untrusted input may allow arbitrary code execution. `fix_versions = [3.14.0]`.
- **CVE-2026-47265** (`GHSA-hg6j-4rv6-33pg`; surfaced in OSV minutes later, mid-session): `aiohttp <= 3.13.5` — cookies
  set via the `cookies=` param are re-sent after a cross-origin redirect. `fix_versions = [3.14.0]`. **aiohttp 3.13.5 is
  accumulating cookie CVEs, all fixed only in 3.14.0** — the ignore set will grow until the fleet can reach 3.14.0. Both
  ignored in the QG bases with the same justification (HTTP-client services using header auth, not untrusted cookie
  loads / cookie-auth-across-origins).
- aiohttp **3.13.5** is the locked version **fleet-wide** (confirmed on `origin/live-defi-rollout` uv.lock for every
  repo checked). So pip-audit (a BLOCKING codex gate, `base-service.sh`/`base-library.sh`) now fails on **every repo**,
  tipping each over its `CODEX_MAX_VIOLATIONS` ceiling (features V:0→1 FAIL; deployment-api V:23→24 FAIL).
- The fix version **aiohttp 3.14.0 is within the existing `>=3.13.4,<4.0.0` constraint** — BUT 3.14.0 **removed
  `aiohttp.streams.AsyncStreamReaderMixin`**, which **vcrpy 8.1.1 (the latest release)** references in
  `vcr/stubs/aiohttp_stubs.py` (`class MockStream(asyncio.StreamReader, streams.AsyncStreamReaderMixin)`). So bumping to
  3.14.0 breaks **64 VCR cassette tests** in unified-api-contracts with `AttributeError` (and any other repo with
  aiohttp-backed VCR tests). **No vcrpy release supports aiohttp 3.14 yet** (8.1.1 is newest).
- Net deadlock for VCR-using repos: aiohttp 3.13.5 → pip-audit CVE FAIL; aiohttp 3.14.0 → vcrpy tests FAIL.

### 2. deployment-service has TWO pre-existing uv blockers (duplicate TOML key + corrupt cbor2 lock entry)

- **(2a)** `[tool.uv.sources.unified-api-contracts]` declared **twice** (identical blocks), committed on
  `origin/live-defi-rollout`. A stricter `uv` rejects it (`TOML parse error … duplicate key`), so **any
  `uv lock --upgrade`** against deployment-service's dep tree (deployment-api depends on it as an editable path-dep)
  fails fleet-wide. A plain `uv lock` survived via cache; `--upgrade-package` forced the rebuild that exposed it.
- **(2b)** After fixing (2a) locally, `uv lock` then fails with
  `Failed to parse uv.lock — Dependency 'cbor2' has missing 'source' field but has more than one matching package` — a
  **second, deeper pre-existing lock corruption** (also on LDR baseline) that blocks regenerating deployment-service's
  lock entirely.
- **Net**: the committed LDR state passes QG (the `uv.lock out of sync` gate only checks sync, never regenerates), so
  neither (2a) nor (2b) blocks the steady state — they only bite a `uv lock --upgrade`. Removing the duplicate (2a)
  forces a re-lock, which then hits (2b). So (2a) **cannot be cleanly committed without first resolving (2b)** (a full
  lock regen with the right index/source config). Foreign-repo dep-infra debt requiring a coordinated pass — deferred.

## Why it matters

- **(1)** blocks the LOCAL QG (commit/quickmerge prerequisite) AND the server `quality-gates-v2` PR gate on **every
  repo** — the entire staging→main promotion pipeline is jammed until resolved. It is a security CVE, so silently
  raising `CODEX_MAX_VIOLATIONS` would be wrong (masks the signal); the correct lever is the sanctioned `--ignore-vuln`
  list that already carries 4 reviewed CVEs.
- **(2)** silently breaks dependency resolution for the whole deployment-service consumer tree.

## Recommended decision (TAKEN — within established patterns)

1. **aiohttp CVE** — added `--ignore-vuln CVE-2026-34993` to BOTH `base-service.sh` and `base-library.sh` pip-audit
   blocks (the same mechanism already used for CVE-2026-4539/45409/3219/6357), with a full-justification comment.
   Rationale: these services use aiohttp as an HTTP **client** and never call `CookieJar.load()` on untrusted files →
   exploit surface is nil; the only patched version breaks vcrpy fleet-wide. Repos **without** vcrpy (features-service,
   deployment-api) run the genuinely-patched **aiohttp 3.14.0**; vcrpy repos stay on 3.13.5 + ignore.
2. **deployment-service** — duplicate-key fix (2a) was made + verified to unblock deployment-api's `uv lock` during the
   shipping window, but **reverted (not committed)**: committing (2a) forces a re-lock that hits the pre-existing cbor2
   corruption (2b), and a full lock regen of a foreign repo is out of tradfi scope + risky. The worktree was restored to
   the clean LDR-passing state. **Both (2a) + (2b) deferred to the cicd/dep-security epic** (successor below). **➡️
   UPDATE 2026-06-04 (slot-4): (2a)+(2b) NOW FIXED** — deployment-service@3899a5d. The from-scratch lock regen (the
   "full lock regen with the right source config" anticipated above) was done + `quality-gates.sh` is GREEN; the cbor2
   dangling edge was dropped (no current dep needs it). See the ✅ successor todo for the full recipe. Item (1) (aiohttp
   CVE) remains the only open blocker in this doc.

## AUDIT UPDATE 2026-06-05 (harsh [hk]) — fleet moved to the CORRECT aiohttp 3.14.0, but without the vcrpy shim → VCR break

While diagnosing the live CI red-board, I found the fleet has moved to **aiohttp 3.14.0** (the genuinely-patched,
operator-confirmed-correct version — this **supersedes** the doc's earlier interim "vcrpy repos stay on 3.13.5" stance).
The move is the right end-state; the problem is it landed **without the vcrpy compat shim**, so the VCR cassette tests
break and the promotion is jammed. Audited the locked versions on `origin/live-defi-rollout`:

| Repo (vcrpy-using)       | pyproject aiohttp | LOCKED aiohttp | LOCKED vcrpy |
| ------------------------ | ----------------- | -------------- | ------------ |
| unified-api-contracts    | `>=3.14.0`        | **3.14.0**     | **8.1.1**    |
| unified-trading-library  | `<4.0.0,>=3.14.0` | **3.14.0**     | **8.1.1**    |
| execution-service        | `<4.0.0,>=3.14.0` | **3.14.0**     | **8.1.1**    |
| market-tick-data-service | `<4.0.0,>=3.14.0` | **3.14.0**     | **8.1.1**    |

All four are now on **aiohttp 3.14.0 + vcrpy 8.1.1** — the **exact deadlock combo** this doc identified (vcrpy 8.1.1
references `aiohttp.streams.AsyncStreamReaderMixin`, removed in 3.14). vcrpy 8.1.1 is the latest PyPI release — **no
aiohttp-3.14-compatible vcrpy exists**, so the "wait for vcrpy >8.1.1" successor path is a dead end; the fix is the
compat shim (P1 below), keeping aiohttp at the correct 3.14.0.

**Mechanism**: a fleet-wide CVE-remediation pass landed
`fix(deps): bump aiohttp>=3.14.0 (CVE-2026-34993 RCE) + uv relock` on 2026-06-05 (UAC@`edf83a5`, UTL@`6731826`,
execution-service@`520723bb`, MTDS@`0d144e6`). The commit message mentions only the CVE — it did **not** carry the vcrpy
compat shim, so the move to the correct 3.14.0 target landed half-complete (aiohttp upgraded, vcrpy stub left broken).
The remaining work is the shim (P1 below), not an aiohttp change.

**Verified breakage** (not theoretical):

- UAC LDR→staging promote PR `quality-gates-v2` run **27009399635** FAILS with ~15
  `AttributeError: module 'aiohttp.streams' has no attribute 'AsyncStreamReaderMixin'` across `tests/vcr/test_*` (the
  doc's predicted 64-test break, partially surfaced before pytest cut output).
- UTL / execution-service / MTDS carry the identical broken lock → same VCR break (UTL `ci_status=FAILING` on
  `origin/main`; the other two carry the broken combo and will break on any VCR-test re-run).

**Side observation (NOT a separate filing — flagging for awareness):** UAC's authoritative `ci_status` on `origin/main`
reads `STAGING_GREEN` despite this live LDR VCR break (its last _merged_ staging state is green; the failing content
sits on the un-merged promote PR). deployment-service / UTL / strategy-service all correctly show `FAILING`. Whether a
wedged LDR→staging promotion _should_ surface in `ci_status` (vs being owned solely by the `ci_failure_watcher` stuck-PR
poller) is an open alerting-design question — noted here, not yet root-caused, deliberately not filed as a standalone
issue.

**Recommended action — UPDATED 2026-06-05 (operator decision): KEEP `aiohttp` 3.14.0; fix the deadlock on the vcrpy
side, NOT by downgrading aiohttp.** 3.14.0 is the genuinely-patched, audited version and is now the fleet-wide locked
version (verified: all repos on `aiohttp=3.14.0`), so a revert to 3.13.5 is explicitly REJECTED — it would re-open the
CVE to keep a test shim happy. The break is entirely in `vcrpy`'s aiohttp stub
(`vcr/stubs/aiohttp_stubs.py: MockStream(asyncio.StreamReader, streams.AsyncStreamReaderMixin)`), which references the
symbol aiohttp 3.14 removed. **`vcrpy` 8.1.1 is the LATEST PyPI release (verified — no >8.1.1 exists), so there is no
upgrade path** — the fix is a **compatibility shim** that re-provides `AsyncStreamReaderMixin` before vcrpy imports it
(a no-op mixin: `aiohttp 3.14` folded its async-iteration helpers into `StreamReader`, so the mixin can be an empty
base), wired in the VCR repos' test bootstrap (conftest/sitecustomize). Once the shim lands, the
`--ignore-vuln CVE-2026-34993` can be dropped fleet-wide (the CVE is genuinely fixed at 3.14.0).

## Successor (close this issue when done)

- [ ] [DEPS] P1. **Add a vcrpy↔aiohttp-3.14 compat shim to the VCR repos (UAC / UTL / execution-service / MTDS) — KEEP
      aiohttp 3.14.0, do NOT downgrade.** Re-provide `aiohttp.streams.AsyncStreamReaderMixin` (an empty mixin base)
      before vcrpy imports its aiohttp stub — wire it in each repo's test bootstrap (`conftest.py` /
      `sitecustomize`-style early import) so `vcr/stubs/aiohttp_stubs.py` loads under aiohttp 3.14. vcrpy 8.1.1 is the
      latest PyPI release (no upgrade path), so the shim is the fix. Verifier: all `tests/vcr/*` green on aiohttp
      3.14.0. Owner: cicd/dep-security epic. Cold-start: read the AUDIT UPDATE above. (Actively jamming the LDR→staging
      promotion on every VCR repo until landed.)
- [ ] [DEPS] P2. **Drop the `--ignore-vuln CVE-2026-34993` from `base-service.sh` + `base-library.sh` once the P1 shim
      makes VCR green** — aiohttp is already 3.14.0 fleet-wide (the genuinely-patched version), so the ignore is now
      redundant masking; remove it so pip-audit reflects the real (clean) state. Verifier: `pip-audit` clean with NO
      `--ignore-vuln CVE-2026-34993` + all VCR cassette tests green. Owner: cicd/dep-security epic.
- [x] ✅ [DEPS] P2. **Fix deployment-service uv blockers (2a duplicate `[tool.uv.sources.unified-api-contracts]` key +
      2b corrupt `cbor2` lock entry) — DONE 2026-06-04 (slot-4)** — deployment-service@3899a5d. Removed the duplicate
      `[tool.uv.sources.unified-api-contracts]` stanza (2a) — that re-exposed 2b: the lock had a dangling
      `{ name =     "cbor2" }` dependency edge with NO `[[package]]` cbor2 definition (uv couldn't disambiguate →
      "missing source field but more than one matching package"). The minimal-diff `uv lock --upgrade` recipe did NOT
      work (uv parses the corrupt lock before resolving); the actual fix was a **from-scratch regen**
      (`rm uv.lock && uv lock`): 257→207 packages — orphaned transitive deps (cbor2 itself +
      autobahn/automat/binance-futures-connector/asgiref/backoff, none required by any current dep) dropped + minor
      version bumps. **`bash scripts/quality-gates.sh` GREEN (181s)** — full tests + basedpyright + coverage pass
      against the regenerated lock; deployment-service QG no longer foreign-blocked. Lock churn re-validates at
      promotion via CI test-in-image. (Surfaced + fixed while shipping the sports execution-store —
      `sports_manifest_canonicalisation_2026_06_01.md`.)
