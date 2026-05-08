---
scope: [engineer, admin]
---

# Partial archive

Pages where SOME content/tabs/components promote into a playbook but OTHER content stays investor-only or archives.
Unlike `archive`, partial-archive preserves reusable elements.

## Investor Relations presentations → pb2 briefings

The four IR presentations (investment, platform, regulatory, disaster-recovery) contain slide blocks that are:

- **Fundraising / board-level** — confidential financials, forward-looking statements, roadmap timelines, cap table —
  INVESTOR-ONLY
- **Commercial / product-level** — feature walkthroughs, coverage demos, compliance explainers — CAN BE PROMOTED to pb2
  briefings (redacted of sensitive bits)

### `/investor-relations/investment-presentation`

**Keep (investor-only):**

- AUM progression
- Forward-looking return targets
- Fee tier structure (specific %)
- Cap table / equity ownership

**Promote to pb2a (`/briefings/investment-management`):**

- Strategy taxonomy slides (what strategies exist)
- Client-reporting capability overview
- Regulatory framework slides (already public-facing)

### `/investor-relations/platform-presentation`

**Keep (investor-only):**

- Revenue projections
- Client count growth
- Competitive landscape with named peers

**Promote to pb2b (`/briefings/platform`):**

- Four-catalogue walkthrough (already appropriate for clients)
- Research-to-trading lifecycle
- Infrastructure capabilities
- Observability features

### `/investor-relations/regulatory-presentation`

**Keep (investor-only):**

- Regulatory risk analysis
- Licensing roadmap

**Promote to pb2c (`/briefings/regulatory`):**

- FCA scope explainer (public info)
- MiFID II reporting features
- Compliance + MLRO provisioning model
- Client-reporting regulatory outputs

### `/investor-relations/disaster-recovery`

**Keep (investor-only):**

- Internal BCP drill results
- Vendor-specific failover details

**Promote to pb2c (`/briefings/regulatory`):**

- BCP framework overview
- RTO / RPO commitments (client-facing)
- DR architecture at high level

## How partial-archive works in practice

1. Identify the sensitive slide blocks and the shareable slide blocks in the IR presentation.
2. Extract the shareable blocks into briefing content fixtures
   ([lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts)) or dedicated briefing components.
3. Keep the sensitive blocks in the IR presentation page — no change to the IR surface.
4. Ensure briefing rendering can include extracted blocks (text + optional images).
5. Add a "View the full investor deck" link from IR (investor-only) to the sensitive version — NOT from briefings.

This preserves:

- Sensitive info stays gated behind IR-level entitlements
- Shareable content reused (no duplication between IR and briefings)
- Investor deck remains unabridged for its audience

## Other partial-archive candidates

Currently only IR presentations qualify. Other orphans either promote whole or defer.

## Related

- Triage matrix: [triage-matrix.md](triage-matrix.md)
- IR doc: [../cross-cutting/investor-relations.md](../cross-cutting/investor-relations.md)
- pb2 briefings: [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
