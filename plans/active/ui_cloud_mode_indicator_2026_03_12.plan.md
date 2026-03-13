---
name: ui-cloud-mode-indicator
overview: |
  Add a dynamic cloud provider + mock/live indicator to every UI's top-right
  header. Each UI fetches cloud_provider and mock_mode from its backing API's
  /api/health endpoint and renders a badge. deployment-ui already has a
  hard-coded "GCP" badge — this plan makes it dynamic and extends the pattern
  to all 12 UI repos. Improves operator situational awareness: seeing "GCP •
  MOCK" vs "AWS • LIVE" instantly surfaces environment misconfiguration.
type: feature
epic: epic-observability
status: active

completion_gates:
  code: C0
  deployment: none
  business: none

repo_gates:
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
    readiness_note: Add cloud_provider + mock_mode to /api/health response
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
    readiness_note: Make cloud badge dynamic; add MOCK/LIVE pill
  - repo: market-data-api
    code: C0
    deployment: none
    business: none
    readiness_note: Add cloud_provider + mock_mode to /health response
  - repo: trading-analytics-api
    code: C0
    deployment: none
    business: none
    readiness_note: Add cloud_provider + mock_mode to /health response

depends_on: []
  # NOTE (2026-03-13 audit): This plan modifies deployment-ui Header.tsx.
  # cicd_audit_remediation_2026_03_13 modifies deployment-ui BuildSelector.tsx in the same repo.
  # COORDINATION: If both plans execute concurrently on deployment-ui, merge conflicts are likely.
  # Agent sequencing: complete cicd_audit_remediation deployment-ui changes FIRST (BuildSelector),
  # then this plan's deployment-ui changes (Header). Or: one agent does both in a single commit.

todos:
  # ── PHASE 1: API changes (add cloud_provider + mock_mode to health) ─────────
  - id: api-health-cloud-fields
    content: |
      In each service API, add cloud_provider (str) and mock_mode (bool) to the
      /api/health (or /health) response. Read from UnifiedCloudConfig:
        from unified_config_interface import UnifiedCloudConfig
        cfg = UnifiedCloudConfig()
        cloud_provider = cfg.cloud_provider   # "gcp" | "aws" | "local"
        mock_mode = cfg.mock_mode             # True | False
      APIs affected: deployment-api, market-data-api, trading-analytics-api,
      client-reporting-api, batch-audit-api, ml-training-api, ml-inference-api,
      and any other API backing a UI repo.
    status: pending

  # ── PHASE 2: UI HealthResponse type update ──────────────────────────────────
  - id: ui-type-update
    content: |
      In each UI repo, extend the HealthResponse (or equivalent) TypeScript
      interface to include:
        cloud_provider?: "gcp" | "aws" | "local";
        mock_mode?: boolean;
      File: typically src/types/index.ts or src/api/health.ts
    status: pending

  # ── PHASE 3: deployment-ui header badge (pilot) ─────────────────────────────
  - id: deployment-ui-badge-pilot
    content: |
      In deployment-ui/src/components/Header.tsx, replace the hard-coded
      cloud provider badge with a dynamic one using health.cloud_provider.
      Add a MOCK/LIVE pill next to it:
        - "MOCK" badge: yellow/amber, when health.mock_mode === true
        - "LIVE" badge: green, when health.mock_mode === false
        - Fallback: show "?" if cloud_provider undefined (API not yet updated)
      Badge format: " [MOCK]" or "[AWS] [LIVE]" in top-right header.
      Cloud provider text: uppercase("gcp" -> "GCP", "aws" -> "AWS",
      "local" -> "LOCAL"). Use existing Tailwind + Radix Tooltip for hover
      detail ("Cloud: Google Cloud Platform • Mode: Mock/Sandbox").
    status: pending

  # ── PHASE 4: Roll out badge to all other UI repos ──────────────────────────
  - id: ui-badge-rollout
    content: |
      Apply the same CloudModeBadge component pattern to all 12 UI repos:
        batch-audit-ui, client-reporting-ui, deployment-ui, execution-analytics-ui,
        live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, onboarding-ui,
        settlement-ui, strategy-ui, trading-analytics-ui, unified-admin-ui.
      Each UI may have a different header structure — adapt accordingly.
      Extract CloudModeBadge to a shared pattern or copy the component per repo
      (no cross-repo component import allowed — each repo is independent).
    status: pending

  # ── PHASE 5: E2E smoke test ─────────────────────────────────────────────────
  - id: e2e-badge-smoke
    content: |
      In deployment-ui Playwright smoke tests, assert the cloud badge text
      matches the expected value from the mock health response.
      Example: mock /api/health to return {cloud_provider: "gcp", mock_mode: true}
      and assert badge text includes "GCP" and "MOCK".
    status: pending
---

## Architecture

### API side

Each backing API adds two fields to its existing health endpoint:

```python
# health_routes.py
from unified_config_interface import UnifiedCloudConfig

@router.get("/api/health")
async def health() -> dict:
    cfg = UnifiedCloudConfig()
    return {
        "status": "healthy",
        "version": __version__,
        "cloud_provider": cfg.cloud_provider,   # "gcp" | "aws" | "local"
        "mock_mode": cfg.mock_mode,             # True | False
        # ... existing fields ...
    }
```

### UI side

```typescript
// src/types/index.ts — extend existing interface
interface HealthResponse {
  status: string;
  version: string;
  cloud_provider?: "gcp" | "aws" | "local";
  mock_mode?: boolean;
  // ... existing fields ...
}

// src/components/CloudModeBadge.tsx — new component
const PROVIDER_LABELS: Record<string, string> = {
  gcp: "GCP", aws: "AWS", local: "LOCAL",
};

export function CloudModeBadge({ health }: { health: HealthResponse }) {
  const provider = health.cloud_provider
    ? PROVIDER_LABELS[health.cloud_provider] ?? health.cloud_provider.toUpperCase()
    : "?";
  const isMock = health.mock_mode ?? true; // default mock-safe

  return (
    <div className="flex items-center gap-1.5 text-xs font-mono">
      <span className="rounded px-1.5 py-0.5 bg-cyan-900/40 text-cyan-300 border border-cyan-700/50">
        {provider}
      </span>
      <span className={cn(
        "rounded px-1.5 py-0.5 border",
        isMock
          ? "bg-amber-900/40 text-amber-300 border-amber-700/50"
          : "bg-green-900/40 text-green-300 border-green-700/50"
      )}>
        {isMock ? "MOCK" : "LIVE"}
      </span>
    </div>
  );
}
```

### Header integration (deployment-ui pattern)

```tsx
// Before (hardcoded):
<span className="... text-cyan-300">GCP</span>

// After (dynamic):
<CloudModeBadge health={health} />
```

## Notes

- `deployment-ui` is the pilot — already has health polling (`useHealth` hook, 30s interval) and a top-right badge area.
  Minimal changes needed.
- Other UIs may need the `useHealth` hook added if not present.
- `mock_mode` defaults to `true` if API doesn't return it yet (fail-safe: show MOCK rather than falsely showing LIVE).
- CloudModeBadge is duplicated per repo (no shared component lib) — consistent with workspace architecture (each repo is
  independent).
- LIVE badge in production should be visually distinct from MOCK to prevent operators from accidentally running live
  trades in mock mode.
