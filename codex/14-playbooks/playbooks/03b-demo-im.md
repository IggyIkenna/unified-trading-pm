# Playbook 3b — Demo: Investment Management flavour

> **Layer:** Implementation. Narrative lives in
> [experience/investment-management-demo.md](../experience/investment-management-demo.md).

## Who this is for

A warm prospect considering allocating capital to Odum-managed strategies. They've been provisioned a demo account on
staging; the demo is framed around client-reporting because that's where their allocator experience lives (performance,
invoices, NAV, reconciliation).

## Pre-req state

- Admin has provisioned an organisation + demo user with **IM flavour entitlements** per
  [../authentication/firebase-staging.md](../authentication/firebase-staging.md)
- Entitlements: `reporting` + optionally `investor-relations` (for board-level views); other tiers locked
- Prospect has staging credentials

## This playbook is UI-identical to pb3a

> User quote: "investment management (all the same as reg umbrella / coverage same features same reporting)."

Every UI click, every route, every feature demonstrated in pb3b is identical to
[03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md). The only difference is the **narrative framing** during the demo
call:

- **pb3a** (Reg Umbrella frame): "you get regulatory filings + investor reporting + performance reporting plumbing —
  compliance, MLRO, umbrella coverage bundled"
- **pb3b** (IM frame): "this is how your allocated capital performs and gets reported on — Odum runs the strategies, you
  see the allocator view"

See [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md) for the full canonical click path and UI details.

## Narrative-only differences

| Topic                     | pb3a frame                                                         | pb3b frame                                                                                      |
| ------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Why am I looking at this  | "I need a regulated structure for my activities"                   | "I'm allocating capital to a manager"                                                           |
| What are the API keys for | "These are your venue API keys — you operate, we supervise"        | "These identify your allocation for reporting + attribution"                                    |
| SMA vs Pooled             | "Which structure is right for the type of activity I'm conducting" | "Which structure is right for my allocation — separate account or share class in a pooled fund" |
| Regulatory reports        | "This is your MiFID II + transaction reporting surface"            | "These are your regulated reports as an allocator; your fund manager also sees them"            |

## Flavour-specific slicing

Identical to pb3a — entitlements: `["reporting", "investor-relations"?]` with all other tiers locked (padlocked-visible,
not hidden). See [../cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md).

## Cross-cutting content (same as pb3a)

- Pooled vs SMA: [../cross-cutting/sma-vs-pooled.md](../cross-cutting/sma-vs-pooled.md)
- Client reporting: [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md)
- Fund/org/client hierarchy: [../cross-cutting/fund-org-hierarchy.md](../cross-cutting/fund-org-hierarchy.md)
- Visibility slicing: [../cross-cutting/visibility-slicing.md](../cross-cutting/visibility-slicing.md)

## Exit state

- **Commits** → becomes real IM client → admin provisions production Firebase user + IM reporting access
- **Refines demo** → admin unlocks additional tiers if prospect wants to see strategy detail
- **Drops** → admin deactivates demo user

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/03b-im.spec.ts`
- Assertions: **identical** to pb3a spec, parametrised over `prospect-im` persona instead of `prospect-reg`
- The two spec files share a helper function that validates the common flow; only the persona + narrative strings differ

## Related

- Parent hub: [03-warm-prospect-demo.md](03-warm-prospect-demo.md)
- Sibling (same UI): [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md)
- Sibling (different structure): [03c-demo-dart.md](03c-demo-dart.md)
- Research briefing that led here: [02a-research-im.md](02a-research-im.md)
