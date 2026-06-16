---
plan_type: audit-ssot
owner: ikenna
created: 2026-05-22
last_updated: 2026-05-22
name: audit-readme
---

# Audit — SSOT for the audit lifecycle

**This file is the SSOT** for how audits are structured, run, linked to epics, and archived. It is referenced by
`codex/11-project-management/epic-execution-with-sub-agents.md` and `plans/epics/README.md`. When the audit workflow
evolves, update this file first; codex docs and the epics README are pointers.

---

## Directory structure

```
plans/audit/
├── README.md                          ← this file (SSOT)
├── instructions/                      ← EVERLASTING per-epic audit templates (never archive)
│   ├── README.md                      ← one-paragraph stub; points here for format
│   ├── defi_master_audit_instructions.md
│   ├── cefi_master_audit_instructions.md
│   └── ... (one file per epic, 19 total)
├── results/                           ← timestamped audit result snapshots + scripts + data
│   ├── README.md                      ← existing; documents result JSON schema
│   ├── <slug>_YYYY_MM_DD.md          ← human-readable result report (archives when findings shipped)
│   ├── a1_*.py / a2_*.py ...         ← audit runner scripts (kept permanently — analytics infra)
│   └── archive/                       ← result .md files where all findings are in code
├── agent_decisions/                   ← JSONL agent decision log (kept permanently)
└── <slug>_YYYY_MM_DD.md              ← root-level contract/thematic audits (legacy; new ones go in results/)
```

**Three layers:**

| Layer              | Path                                                 | Lifecycle                                                                  |
| ------------------ | ---------------------------------------------------- | -------------------------------------------------------------------------- |
| **Instructions**   | `instructions/<epic_slug>_audit_instructions.md`     | Everlasting. Updated when epic scope changes. Never archived.              |
| **Results**        | `results/<slug>_YYYY_MM_DD.md`                       | One-shot snapshot. Archives when all findings are `- [x]` in parent plans. |
| **Scripts + data** | `results/*.py`, `results/*.csv`, `results/*.parquet` | Permanent analytics artifacts. Never archived.                             |

---

## Audit instruction file format

Every file in `instructions/` uses this structure:

```yaml
---
name: <epic_slug>_audit_instructions
type: audit-instructions
epic: <epic_slug>
assigned_vm: <from epics registry>
tier: L0|L1|L2|L3|L4|L5
last_updated: YYYY-MM-DD
---
```

Body sections (**all required**):

```markdown
## Epic Scope

What code surfaces, repos, and data flows this epic owns.

## Triggers

When to run this audit:

- Monthly (minimum cadence)
- [Specific trigger conditions — e.g., after venue addition, after QG RED, etc.]

## Checklist

Concrete, grep-verifiable steps. Each item is actionable. Example:

- [ ] (a) All adapters emit ADAPTER_FETCH_FAILED on error grep: `rg "ADAPTER_FETCH_FAILED" <service_dir>/`
- [ ] (b) No hardcoded venue URLs: `bash scripts/quality-gates/no_hardcoded_venue_urls.sh`
- [ ] (c) ...

## Success Criteria

What GREEN looks like. One sentence per criterion:

- All checklist items pass
- QG exits 0 for the epic's primary service
- Manifest coverage for this epic's asset_group is zero MISSING_EXPECTED

## Output Format

What the audit result file must contain:

- Checklist results (each item: GREEN / AMBER / RED + evidence)
- Any new gap items (expressed as `- [ ] [TYPE] P#. ...` ready to paste into an active plan)
- Recommended active plan title + parent_epic for each gap

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
```

---

## Audit result file format

Results land in `results/<slug>_YYYY_MM_DD.md`. Every result must include:

1. **Frontmatter (canonical schema — QG-enforced by `scripts/plan-hygiene/check_frontmatter_schema.py`)** — every audit
   doc carries these NON-EMPTY: `type:` (`audit-result` | `analysis` | `benchmark`), `title:`, `epic:`, `auditor:`,
   `date:`, `status:` (`complete | in-progress`). **`epic:` is mandatory on EVERY audit doc** (operator 2026-06-16 —
   everything belongs to a single epic, or a LIST of epics when cross-concern); each slug MUST resolve to a real
   `plans/epics/<slug>.md`. **`instructions_ref:` is REQUIRED only for `type: audit-result`** (the epic-audit-lifecycle
   link; ad-hoc `analysis`/`benchmark` reports omit it).
2. **Checklist results** — each instruction checklist item marked GREEN / AMBER / RED with evidence (grep output, script
   run, SHA)
3. **Gap items** — expressed as `- [ ] [TYPE] P#. Description` ready to paste into an active plan; each gap includes
   `parent_epic:` and suggested priority
4. **Active plans created** — table linking each gap to the active plan that absorbed it (filled in after plans are
   created)
5. **Archive condition** — explicit statement: "Archives when all gap items below are `- [x]` in their parent plans"

---

## Full lifecycle

```
PLANNING VM (Ikenna + Harsh, Opus 4.7 1M context)
   │
   ├── Read instruction file: plans/audit/instructions/<epic>_audit_instructions.md
   ├── Run audit (grep evidence, script runs, cross-code + cross-plan + cross-codex read)
   ├── Produce result: plans/audit/results/<slug>_YYYY_MM_DD.md
   │      → each gap = one `- [ ] [TYPE] P#.` item with parent_epic + priority
   ├── Create or extend active plans for gap items
   │      → each active plan carries parent_epic: <epic-slug>
   │      → each carries estimate_class + estimate_baseline_ai_days + estimate_calibrated_ai_days
   ├── Add active plans to epic body priority blocks (related_plans: update in epic frontmatter)
   └── Update instruction file's ## Linked Results table
                │
                ▼
EPIC VM (assigned_vm from epic frontmatter)
   │
   ├── Workers pick up P0 items first from epic priority blocks
   ├── Items ship → plan-flip per Half-1+2 rule (CLAUDE.md)
   └── When ALL gap items from the result are `- [x]` in parent plans:
          → move result file to plans/audit/results/archive/
          → update instruction file's Linked Results table: status → ARCHIVED
```

---

## Archival rules

**Instructions** (`instructions/*.md`): **Never archive.** These are templates. Update them when epic scope changes or
new invariants are codified. They stay until the epic itself is cancelled.

**Results** (`results/<slug>_YYYY_MM_DD.md`): Archive when ALL of the following are true:

1. Every gap item the result spawned is `- [x]` in its parent active plan
2. The parent active plan itself is either `status: complete` or the items are provably in code (commit SHA exists)
3. No remaining AMBER or RED items without an active plan absorbing them

Archive action: `mv plans/audit/results/<slug>.md plans/audit/results/archive/` + update Linked Results table in the
instruction file.

**Scripts and data files** (`results/*.py`, `results/*.csv`, `results/*.parquet`): Never archive — these are analytics
infrastructure.

---

## Epic creation rule (HARD RULE)

When a new epic is created in `plans/epics/`, a corresponding instruction file MUST be created in the same commit:

```
plans/epics/<new_epic_slug>.md          ← new epic
plans/audit/instructions/<new_epic_slug>_audit_instructions.md  ← REQUIRED in same PR
```

An epic without a corresponding instruction file is **review-blocking**, mirroring the rule for orphan active plans.

The inventory regenerator (`regenerate_active_plan_inventory.py`) will be updated to flag missing instruction files.

---

## Audit hygiene (planning VM cadence)

Run at each planning-VM session start:

1. **Check for archived results**: for each file in `results/`, verify if all spawned gap items are `- [x]`. If yes →
   archive.
2. **Check for scope drift**: if an epic's scope changed since the last audit run (new QG steps, new vendors, new code
   surfaces), update the instruction file's checklist.
3. **Check for new epics without instructions**:
   `diff <(ls plans/epics/*.md | xargs -I{} basename {} .md | sort) <(ls plans/audit/instructions/*.md | xargs -I{} basename {} _audit_instructions.md | sort)`
   — any epic missing a corresponding instruction file is a gap.

---

## Cross-references

- `plans/epics/README.md` — full audit → active plan → epic flow diagram; `## Audit instructions per epic` section
- `codex/11-project-management/epic-execution-with-sub-agents.md` — codex-level summary with audit lifecycle table
- `codex/11-project-management/issue-doc-lifecycle.md` — how pre-audit diagnostics in issues/ should be handled (archive
  once acked into a plan)
- `plans/PLAN_FORMAT.md` — plan format for active plans created from audit gap items
