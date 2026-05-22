# Codex 04-architecture phantom + retired provider ref audit — 2026-05-20

**Auditor**: slot-10 (ikenna-vm) **Scope**: `codex/04-architecture/` — all `.md` files **Pattern searched**:
`URDI|Elysium|Arkham|Bloxroute|Infura` **Outcome**: **0 violations** — all hits are correctly classified

## Methodology

```bash
rg "URDI|Elysium|Arkham|Bloxroute|Infura" codex/04-architecture/ -n
```

## Audit table

| File                             | Line | Pattern   | Context                                                                                 | Classification                                                                                                          | Action           |
| -------------------------------- | ---- | --------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `mev-protection.md`              | 350  | Bloxroute | `Bloxroute \| **REMOVED** \| Per CLAUDE.md; do not re-introduce`                        | HISTORICAL — retirement table row, correctly labeled REMOVED                                                            | No action needed |
| `custody-providers.md`           | 21   | Elysium   | `POD / Elysium client scope clarified 2026-05-12`                                       | ACTIVE — POD is the live DeFi allocator client; "Elysium" is the POD sub-entity name, unrelated to the banned MEV route | No action needed |
| `custody-providers.md`           | 23   | Elysium   | `POD (Elysium sub-entity, AIFM Ireland; BVI Fund)`                                      | ACTIVE — same POD client context                                                                                        | No action needed |
| `custody-providers.md`           | 299  | Elysium   | `POD (Elysium sub-entity, BVI Fund)`                                                    | ACTIVE — same POD client context                                                                                        | No action needed |
| `tenderly-execution-provider.md` | 128  | Infura    | `Infura is on the workspace "Removed providers" list (...) and MUST NOT be referenced.` | HISTORICAL — documenting the removal warning, not a claim of current existence                                          | No action needed |
| `commercial-service-families.md` | 134  | Elysium   | `For DeFi-first shapes (Elysium):` — client persona template                            | ACTIVE — Elysium/POD client shape configuration                                                                         | No action needed |

## Notes

- **URDI**: 0 references in `codex/04-architecture/`. (URDI appears in `codex/10-audit/` files which document the
  URDI→UCI consolidation history — those are outside this audit's scope but are correctly annotated as historical.)
- **Arkham**: 0 references in `codex/04-architecture/`. (Appears in `codex/02-venues/` as `Arkham | Removed` — correctly
  documented.)
- **Elysium disambiguation**: `codex/14-customer-journeys/pod-elysium-client-onboarding.md` explicitly states the
  POD/Elysium client entity is unrelated to the banned `Elysium` MEV route. The references in `codex/04-architecture/`
  are the active-client meaning, not the retired-provider meaning.

## Result

**PASS — 0 violations in `codex/04-architecture/`.** No fixes required. All retired-provider references are correctly
annotated; active-client references using "Elysium" are valid.
