---
doc_type: plan
title: ui-cloud-mode-indicator
summary: 'Add a dynamic cloud provider + mock/live indicator to every UI''s top-right

  header. Each UI fetches cloud_provider and mock_mode from its backing API''s

  /api/health endpoint and renders a badge. deployment-ui already has a

  hard-coded "GCP" badge — this plan makes it dynamic and extends the pattern

  to all 12 UI repos. Improves operator situational awareness: seeing "GCP •

  MOCK" vs "AWS • LIVE" instantly surfaces environment misconfiguration.'
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-12'
type: feature
epic: epic-observability
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C0, deployment: none, business: none}
repo_gates:
- {repo: deployment-api, code: C0, deployment: none, business: none, readiness_note: Add cloud_provider + mock_mode to /api/health response}
- {repo: deployment-ui, code: C0, deployment: none, business: none, readiness_note: Make cloud badge dynamic; add MOCK/LIVE pill}
- {repo: market-data-api, code: C0, deployment: none, business: none, readiness_note: Add cloud_provider + mock_mode to /health response}
- {repo: trading-analytics-api, code: C0, deployment: none, business: none, readiness_note: Add cloud_provider + mock_mode to /health response}
depends_on: []
todos:
- {id: api-health-cloud-fields, content: "In each service API, add cloud_provider (str) and mock_mode (bool) to the\n/api/health (or /health) response. Read from UnifiedCloudConfig:\n  from unified_config_interface import UnifiedCloudConfig\n  cfg = UnifiedCloudConfig()\n  cloud_provider = cfg.cloud_provider   # \"gcp\" | \"aws\" | \"local\"\n  mock_mode = cfg.mock_mode             # True | False\nAPIs affected: deployment-api, market-data-api, trading-analytics-api,\nclient-reporting-api, batch-audit-api, ml-training-api, ml-inference-api,\nand any other API backing a UI repo.\n", status: pending}
- {id: ui-type-update, content: "In each UI repo, extend the HealthResponse (or equivalent) TypeScript\ninterface to include:\n  cloud_provider?: \"gcp\" | \"aws\" | \"local\";\n  mock_mode?: boolean;\nFile: typically src/types/index.ts or src/api/health.ts\n", status: pending}
- {id: deployment-ui-badge-pilot, content: "In deployment-ui/src/components/Header.tsx, replace the hard-coded\ncloud provider badge with a dynamic one using health.cloud_provider.\nAdd a MOCK/LIVE pill next to it:\n  - \"MOCK\" badge: yellow/amber, when health.mock_mode === true\n  - \"LIVE\" badge: green, when health.mock_mode === false\n  - Fallback: show \"?\" if cloud_provider undefined (API not yet updated)\nBadge format: \" [MOCK]\" or \"[AWS] [LIVE]\" in top-right header.\nCloud provider text: uppercase(\"gcp\" -> \"GCP\", \"aws\" -> \"AWS\",\n\"local\" -> \"LOCAL\"). Use existing Tailwind + Radix Tooltip for hover\ndetail (\"Cloud: Google Cloud Platform • Mode: Mock/Sandbox\").\n", status: pending}
- {id: ui-badge-rollout, content: "Apply the same CloudModeBadge component pattern to all 12 UI repos:\n  batch-audit-ui, client-reporting-ui, deployment-ui, execution-analytics-ui,\n  live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, onboarding-ui,\n  settlement-ui, strategy-ui, trading-analytics-ui, unified-admin-ui.\nEach UI may have a different header structure — adapt accordingly.\nExtract CloudModeBadge to a shared pattern or copy the component per repo\n(no cross-repo component import allowed — each repo is independent).\n", status: pending}
- {id: e2e-badge-smoke, content: 'In deployment-ui Playwright smoke tests, assert the cloud badge text

    matches the expected value from the mock health response.

    Example: mock /api/health to return {cloud_provider: "gcp", mock_mode: true}

    and assert badge text includes "GCP" and "MOCK".

    ', status: pending}
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
