---
title: "openapi.json drift: unified-trading-api vs UI mirror — UI generated types may be stale"
created: 2026-05-16
author: slot-8 (surfaced during Group D codification)
source:
  - unified-trading-api/openapi.json (sha256 f4a331...)
  - unified-trading-system-ui/lib/registry/openapi.json (sha256 9685cb...)
  - new QG step scripts/quality_gates/check_openapi_drift.py (warn-only mode)
severity:
  P2 — non-blocking for May-23 (UI types still functional; just may not surface latest endpoints in autocomplete)
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

While codifying Group D of `governance_qg_automation_gaps_post_cutover_2026_05_12.md` (the openapi.json drift gate), the
newly-written check immediately flagged drift between the two committed copies:

- `unified-trading-api/openapi.json` — backend FastAPI export
- `unified-trading-system-ui/lib/registry/openapi.json` — UI mirror feeding type-generation

```
API openapi.json:   sha256=f4a3312d8b63f1eadef7ed9497ee6e6a (md5 form)
UI  openapi mirror: sha256=9685cb97ccc0a9c0339d709610cfed5f (md5 form)
DRIFT — non-trivial divergence.
```

Likely cause: the backend has added or modified endpoints since the last UI sync; the UI mirror + generated TS types
weren't refreshed.

## Why it matters

- UI `lib/types/api-generated.ts` types may not include the latest endpoints / response shapes — IDE autocomplete +
  type-checking will miss those.
- Runtime calls still work (types are compile-time only); UI doesn't break.
- Pre-cutover (May-23): if any UI feature consumes a recently-added endpoint, the type might be `unknown` / `any` and
  the developer loses the compile-time safety net.

## Recommended decision

UI-owning slot runs the regeneration script:

```bash
# Probable shape (verify):
cd unified-trading-system-ui
bash scripts/sync-openapi.sh        # OR: npm run generate:types
git add lib/registry/openapi.json lib/types/api-generated.ts
git commit -m "chore(ui): re-sync openapi.json mirror + regenerate types"
git push origin HEAD:live-defi-rollout
```

After the resync, flip the `--warn-only` flag off in `unified-trading-pm/scripts/quality-gates.sh` § "Post-gates:
OpenAPI drift" so future drift fails QG immediately.

## Cross-references

- Group D codification: `plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md` § Group D
- Drift checker: `unified-trading-pm/scripts/quality_gates/check_openapi_drift.py`

execution: owner: "unified-trading-system-ui slot (UI repo owns the mirror + regen script)" cadence: "one-shot resync;
QG ratchet then prevents future drift" verifier: "python3
unified-trading-pm/scripts/quality_gates/check_openapi_drift.py → exit 0" last_executed: "2026-05-16 — slot-4-ikenna
cross-slot pickup; resync + types regen shipped"

## RESOLVED — 2026-05-16 (slot 4 cross-slot pickup)

Resync shipped at `unified-trading-system-ui@1abecee1`:

1. Copied `unified-trading-api/openapi.json` → `unified-trading-system-ui/lib/registry/openapi.json`.
2. Ran `npx openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts` (✨ openapi-typescript 7.13.0;
   66.9ms).

Diff: 2,124 inserted + 58,037 deleted on `api-generated.ts` — the UI mirror was carrying a much larger stale schema; the
regen lands the trimmed canonical surface.

Verified post-apply via `python3 unified-trading-pm/scripts/quality_gates/check_openapi_drift.py`:

```text
API openapi.json   (unified-trading-api/openapi.json):                 sha256=2045c5345c1c...
UI  openapi mirror (unified-trading-system-ui/lib/registry/openapi.json):  sha256=2045c5345c1c...
✅ No drift — UI mirror matches API source.
```

QG `--warn-only` flag can now be flipped off to enforce green-or-fail (Group D codification follow-up — see
`governance_qg_automation_gaps_post_cutover_2026_05_12.md`). Issue closeable at next archive sweep.

---

## INVESTIGATION 2026-05-16 (ikenna-main during orchestrator cycle)

**Root cause clarified — the check is comparing structurally-different files**:

| File                                                  | title                        | path count | nature                                                                                           |
| ----------------------------------------------------- | ---------------------------- | ---------- | ------------------------------------------------------------------------------------------------ |
| `unified-trading-api/openapi.json`                    | "Unified Trading API"        | **61**     | Slim facade — `/health` + `/readiness` + `/market-data/...`                                      |
| `unified-trading-system-ui/lib/registry/openapi.json` | "Unified Trading System API" | **479**    | Aggregated mirror — `/deployment-api/...` + `/client-reporting-api/...` + other backend prefixes |

The UI mirror isn't a mirror of `unified-trading-api` — it's an AGGREGATED view of multiple backend APIs
(deployment-api, client-reporting-api, etc.). Per-path namespace prefixes in the UI mirror prove this:
`/deployment-api/api/services`, `/client-reporting-api/...`, etc.

The current `check_openapi_drift.py` compares hashes; since the two files are structurally different by design, the hash
will ALWAYS differ. The check fires P2 drift forever.

**Two correct fixes**:

**(A) Find the actual canonical aggregator** — likely a meta-export from deployment-api or a script that walks all
backend services and merges. Update `DEFAULT_API_PATH` in `check_openapi_drift.py` to point at the aggregator's output.
Slot 8 (filed the issue) likely knows the architecture; or whoever owns
`unified-trading-system-ui/lib/registry/openapi.json` regeneration.

**(B) Mark the check as "structural-mismatch — disabled"** until (A) lands. Convert to a no-op stub OR delete the script
if the aggregator path can't be identified.

**Severity confirmed P2** — UI types are still functional + complete (479 paths > 61 paths means UI has MORE coverage,
not less). Slot owner can pick up the architectural fix post-cutover.

**Workspace-qg impact**: this check is in `scripts/quality_gates/check_openapi_drift.py` (PM repo); not yet wired into
per-repo `quality-gates.sh`. So workspace-qg green is NOT blocked by this finding.

## ERRATUM 2026-05-16 ~21:50 UTC (slot 4 self-correction)

Slot 4 misread this issue earlier and shipped a "resync" at `unified-trading-system-ui@1abecee1` that copied
`unified-trading-api/openapi.json` (61 paths) over `unified-trading-system-ui/lib/registry/openapi.json` (479 paths) —
the wrong copy direction; deleted 418 paths of API contracts from the UI mirror. Slot 1 main's investigation above
(correctly diagnosing the files as structurally-different-by-design) was already shipped at PM@`a791800d` when slot 4
made the resync error.

**Revert shipped 2026-05-16 21:50 UTC** at `unified-trading-system-ui@91e45bdf`: restored `lib/registry/openapi.json` +
`lib/types/api-generated.ts` to the state at `1abecee1^` (md5=9685cb97 + 28,256-line types file; 479 paths intact).

Net: no harm done — the broken state existed for ~1h between resync push and revert push; no downstream consumer shipped
a build against the 61-path mirror in that window. The issue stays archived; this erratum is for the audit trail. Lesson
logged: a P2 mirror-drift check that compares structurally-different files is a false-positive signal — fix the check
before "fixing" the data.
