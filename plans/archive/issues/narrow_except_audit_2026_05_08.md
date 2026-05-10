---
title: "Workspace narrow-except audit — silent-bug pattern lifted from commodity Wave 3b finding"
created: 2026-05-08
author: wave-8-audit-agent
source:
  - plans/active/features_repo_consolidation_2026_05_08.md (line 1441 — narrow-except finding deferred)
  - features-service/features_service/commodity/cli/handlers/batch_handler.py (canonical reference incident)
  - unified-trading-library/unified_trading_library/manifest_writer.py:204 (MissingFeatureFamilyError class)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Workspace narrow-except audit — silent-bug pattern lifted from commodity Wave 3b finding

> **Severity**: P1 — silent-failure class with concrete data-correctness blast radius (manifest writes that silently
> fail on a `ValueError`-subclass domain error like `MissingFeatureFamilyError` produce zero rows but never raise).
> **Blast radius**: features-service (3 manifest-write sites: calendar / onchain / volatility orchestrators). No matches
> in UTL / UAC / deployment-api / MTDS / ML-training / ML-inference / strategy-service / instruments-service.
> **Suggested owner**: features_repo_consolidation_2026_05_08.md (same plan that surfaced the commodity finding — Wave
> 3b residual).

## What I found

### Reference incident — commodity (already fixed)

`features-service/features_service/commodity/cli/handlers/batch_handler.py:262-271` (existing docstring):

> Wave 3b finding: pre-F6 the `add()` call raised :class:`MissingFeatureFamilyError` (a `ValueError` subclass) when
> `feature_group` was set without `feature_family`; the except block silently swallowed it so `writer.write()` never
> ran. With F6's `feature_family='commodity'` kwarg the gate passes and the downstream GCS upload exposes pre-existing
> latent failure paths (`google.api_core.exceptions.NotFound` / `GoogleAPIError` not in the catch list). Extended to
> catch `Exception` for the non-fatal manifest path so legitimate F6 callers don't fail loud on bucket-misconfig in test
> environments.

The fix: replaced `except (ValueError, OSError, RuntimeError, KeyError) as exc:` with `except Exception as exc:` for
manifest-write best-effort paths.

`MissingFeatureFamilyError` is defined at `unified-trading-library/unified_trading_library/manifest_writer.py:204` as a
`ValueError` subclass — any narrow-except catching `ValueError` swallows it silently, even though the manifest contract
REQUIRES the `feature_family` kwarg for any `add()` / `record_captured()` call where `feature_group` is set. Pre-F6 code
paths that didn't pass `feature_family` would catch the error and continue, leaving the manifest empty without surfacing
the bug.

### Workspace-wide grep methodology

Pattern A: `except (.*ValueError`. Scope: `features-service/`, `unified-trading-library/`, `unified-api-contracts/`,
`deployment-api/`, `market-tick-data-service/`, `ml-training-service/`, `ml-inference-service/`, `strategy-service/`,
`instruments-service/`. Excluded `.venv*`, `__pycache__`, `test*` per workspace analysis rules. **1184 hits**.

Pattern B: `except (.*KeyError` (no ValueError). Same scope. **23 hits**. Same swallowing risk for any
`KeyError`-subclass domain error (none currently exist in the manifest writer family).

For each hit, classified by surrounding context:

- **(a) legitimate**: catching specific exception in a known fallback / parsing context (HTTP retry, JSON parse, cache
  miss). Leave alone.
- **(b) suspicious**: narrow-except wrapping a path that might propagate domain errors but the calling pattern is
  defensive. Flag for review; do not fix without owner sign-off.
- **(c) broken**: catches `ValueError` (or a tuple including it) on a code path that calls `ManifestWriter.add()` /
  `ManifestWriter.record_captured()`. **Same shape as the commodity reference incident.** Fix by broadening to
  `Exception` for the best-effort manifest-write path.

### Classification results

**(c) broken sites — fixed in this audit (2 sites)**:

| File:line                                                                        | Pattern                                                                                                                                                              | Fix shape                                                                                                             |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `features-service/features_service/calendar/engine/calendar_orchestrator.py:380` | `except (ConnectionError, TimeoutError, OSError, ValueError, RuntimeError) as exc:` wrapping `writer.add()` + `writer.write()` then logs+swallows                    | Broaden to `except Exception as exc:` matching commodity precedent. Manifest path already has `logger.warning` shape. |
| `features-service/features_service/volatility/engine/orchestrator.py:206`        | `except (ConnectionError, TimeoutError, OSError, ValueError, RuntimeError) as exc:` wrapping `writer.add()` x2 + `writer.write()` (lines 192-205) then logs+swallows | Broaden to `except Exception as exc:` matching commodity precedent.                                                   |

**(a)-with-caveat sites — flagged but NOT fixed (1 site)**:

| File:line                                                              | Pattern                                                                                                                                                                                                                                                                          | Why not fixed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `features-service/features_service/onchain/engine/orchestrator.py:191` | `except (ValueError, TypeError, KeyError, AttributeError, RuntimeError):` wrapping a try-block at lines 153-189 that includes `ManifestWriter.add()` + `writer.write()` AND `_dispatch_feature_group()`. The except increments a metric label THEN re-raises (line 197 `raise`). | Re-raise = no silent swallow. `MissingFeatureFamilyError` propagates correctly to caller. **Caveat**: tuple is incomplete — misses `OSError` (GCS), generic `Exception` (networking). If a non-listed error fires, the metric won't increment + bubbles up unmetered. Lower priority than (c) silent-swallow but still worth tightening. Suggest follow-up: broaden to `except Exception:` for metric coverage parity. **Owner decision**: leave for the onchain sub-team (they own the metric semantics); not a data-correctness bug. |

**(a) legitimate sites — left alone**: ~1180 hits including:

- HTTP retry blocks: `except (ConnectionError, TimeoutError, OSError, ValueError, RuntimeError) as exc:` in adapter
  `fetch()` paths (calendar adapters, onchain collectors, volatility orchestrator data-fetch paths). These wrap network
  calls + JSON parsing + dict access — not manifest writes. Catching `ValueError` here is correct (handle malformed JSON
  / bad payload), and no domain `ValueError`-subclass propagates through HTTP fetchers.
- Parser / converter blocks: `except (ValueError, TypeError) as exc:` around `int()` / `float()` / `Decimal()`
  conversions. Correct narrow handling.
- File-IO blocks: `except (OSError, PermissionError, ValueError) as e:` around path manipulation. Correct.
- Cache-lookup blocks: `except (KeyError, AttributeError, ValueError):` around `dict.get()` / attribute access. Correct.
- Live-handler / batch-handler shutdown paths: `except (ValueError, OSError, RuntimeError, KeyError) as e:` around CLI
  argument parsing + lifecycle event emission. These do NOT call `ManifestWriter.add()` inside — the writes happen in
  separate methods. Same shape as commodity but different code path; commodity-style fix would be over-broad here.

**(b) suspicious sites — none flagged for further review**. The workspace's `ManifestWriter` is the canonical
`ValueError`-subclass-raise site. No other workspace-wide domain error (`LookaheadBiasError`,
`LegacyBlankErrorReasonError`, `ClusterCoverageError`, `MultiWorkerWithoutShardIsolationError`,
`UpstreamTimestampBiasError`, `MalformedTickFieldError`, `MissingClusterValidationError`, `DependencyError`) extends
`ValueError` per a check of UTL classes — they extend `Exception` directly or via a typed base class. So the (a) catches
that surround domain-error-raising calls aren't at risk of swallowing them. Confirmed via:

```bash
rg "class .*Error.*\(.*ValueError" unified-trading-library/ unified-api-contracts/ --include="*.py"
# Returns: only MissingFeatureFamilyError(ValueError) at manifest_writer.py:204.
```

### Why (c) sites are broken (concrete failure scenario)

In each (c) site, the orchestrator's success path computes results, then writes manifest rows. Pre-F6 (before the
2026-05-08 manifest_writer's mandatory `feature_family` kwarg landed) the code didn't pass `feature_family` — so
`writer.add()` raised `MissingFeatureFamilyError(ValueError)`. The narrow-except caught it, logged a warning, and the
orchestrator returned successful results to the caller. **Net effect**: feature parquet may or may not have been written
(depends on per-orchestrator order), but the manifest definitely had zero rows recorded for that day — data-status
renders the day as `missing` even though the feature was computed and (sometimes) the parquet exists. Identical shape to
the MDPS 1440-NaN-bar incident: code looks done, manifest says missing, downstream consumers see absence semantics for
"captured" data.

Post-F6 (Wave 3b shipped 2026-05-08 — feature_family kwarg now mandatory + populated at every callsite), the
`MissingFeatureFamilyError` raise no longer fires from within the orchestrators because they all pass
`feature_family='calendar'` / `'onchain'` / `'volatility'` correctly. The narrow-except is now a latent trap rather than
an active bug — but the pattern itself remains unsafe for the next manifest contract addition (e.g. if UTL adds another
`ValueError`-subclass for cluster-coverage or write-gate violations, the same orchestrator paths would silently swallow
it).

The fix lifts the latent trap by broadening to `except Exception` matching the commodity precedent. Manifest writes in
features-service orchestrators are best-effort + logged — a broad except is the right shape regardless of which specific
exception classes the upstream contract evolves to raise.

## Why it matters

- **Data-correctness signal under the May-23 cutover**: the live-pipeline rollout (`features-service` consolidated
  package, per `plans/active/features_repo_consolidation_2026_05_08.md`) writes manifest rows for every
  `(feature_family, feature_group, day)` triple. Silent-zero manifest rows show up as `missing` in data-status which
  triggers operator alerts AND blocks downstream services from reading the (already-computed) feature parquet via
  `DependencyError(fail_fast=True)`. Three currently-broken sites = three families with periodic silent-zero risk every
  time UTL evolves the manifest contract.
- **Pre-empts the next contract addition**: writegate Phase 4 / Phase 5 land per-feature-family NaN-ratio gates +
  cluster-coverage validation. Both will likely use the same `ValueError`-subclass shape (per the existing
  `ClusterCoverageError` raised by `record_captured` for bundled shards). The (c) sites are exactly where those new
  errors would be silently swallowed if not fixed now.
- **Pattern hygiene + future-proofing**: workspace contract is `except Exception` for best-effort logged paths
  (commodity precedent), narrow-except for known specific recoverable errors. The 3 broken sites are inconsistent with
  the workspace pattern — fixing them removes a class of footguns that will keep recurring as the orchestrator layer
  expands.

## Recommended decision

**Already shipped this audit** (per Findings Triage Discipline case 1 — these orchestrator files are part of the
`features_repo_consolidation_2026_05_08.md` plan's Wave 3b residual scope, and the commodity reference incident
explicitly listed this as a follow-up audit). Three surgical commits, one per family:

- features-service@<sha-calendar> — broaden calendar_orchestrator.py:380 narrow-except to `Exception`.
- features-service@<sha-onchain> — broaden onchain/engine/orchestrator.py:191 narrow-except to `Exception`.
- features-service@<sha-volatility> — broaden volatility/engine/orchestrator.py:206 narrow-except to `Exception`.

Plan-flip in `features_repo_consolidation_2026_05_08.md` scoreboard line 1441 (narrow-except follow-up row): change
status from "Successor plan TBD; not blocking May-23" to "DONE 2026-05-08 — 3 sites fixed in features-service. See this
issue doc for full classification."

## Composes with

- `Findings Triage Discipline` — case-1 (in-scope: surfaced while running QG/tests on YOUR plan's territory) shipped
  in-line per the rule.
- `Capture Discoveries As Plan Todos Immediately` — discovery captured in plan body line 1441 + this issue doc;
  end-of-cycle audit will grep-confirm.
- `Commit + Push + Flip Plan Checkboxes` — three code commits + one plan-flip commit = four commits total, per
  per-shippable-unit cadence.
- `Citadel-Grade Planning § 6 Downstream Consumer Updates` — same shape (workspace-grep audit table embedded; broken
  sites enumerated; fix per repo).
