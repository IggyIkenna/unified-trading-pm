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

## Successor (close this issue when done)

- [ ] [DEPS] P2. **Remove the `CVE-2026-34993` ignore + bump `aiohttp>=3.14` fleet-wide** once **vcrpy** ships an
      aiohttp-3.14-compatible release (track vcrpy >8.1.1) OR an aiohttp 3.13.x backport of the CookieJar fix lands.
      Repos: ALL (edit `base-service.sh` + `base-library.sh` to drop the ignore, then
      `uv lock --upgrade-package aiohttp` + `uv lock --upgrade-package vcrpy` per repo, re-QG). Owner: cicd/dep-security
      epic. Verifier: `pip-audit` clean with NO `--ignore-vuln CVE-2026-34993` + all VCR cassette tests green.
      Cold-start: read this issue doc.
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
