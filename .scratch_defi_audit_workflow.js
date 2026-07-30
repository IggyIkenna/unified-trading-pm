export const meta = {
  name: 'defi-closeout-audit-phase1',
  description: 'Classify defi-tranche AG-primary docs as archivable/orphaned given current covering-plan coverage',
  phases: [{ title: 'Classify' }],
}

const REPO = '/home/ubuntu/unified-trading-system-repos/.tabs/2/unified-trading-pm'

const SCHEMA = {
  type: 'object',
  properties: {
    path: { type: 'string', description: 'the relative path you were given' },
    frontmatter_status: { type: 'string' },
    open_todo_count: { type: 'number' },
    done_todo_count: { type: 'number' },
    has_prose_remaining_work: {
      type: 'boolean',
      description: 'true if there is genuinely remaining open work expressed as prose/numbered-list with no checkbox',
    },
    has_dated_override_section: {
      type: 'boolean',
      description: 'true if a dated Update/RE-TRIAGE/RESOLVED section near the end changes the doc status from what earlier checkboxes suggest',
    },
    remaining_open_work: {
      type: 'array',
      items: { type: 'string' },
      description: 'each genuinely remaining open item as of now, briefly described (one line each)',
    },
    verdict: {
      type: 'string',
      enum: [
        'archivable_now',
        'archivable_after_planned_work',
        'orphaned_partial_coverage',
        'orphaned_never_touched',
        'exclude_cross_cutting',
      ],
    },
    reasoning: {
      type: 'string',
      description: 'cite the SPECIFIC evidence: which covering plan + which todo closes which item, or why nothing does',
    },
    covering_citations: {
      type: 'array',
      items: { type: 'string' },
      description: 'e.g. "defi_satellite_ao_dispatch_batch2_2026_07_26.md todo 14 covers item X" — empty if none',
    },
  },
  required: ['path', 'verdict', 'reasoning', 'remaining_open_work'],
}

function buildPrompt(item) {
  const hitsBlock =
    item.hits.length > 0
      ? `A pre-computed basename grep found this doc's filename mentioned in these covering plan(s) — verify each is a REAL citing todo (not just a passing related:/mention) and note what it actually closes:\n${item.hits.map((h) => `  - ${REPO}/${h}`).join('\n')}`
      : `A pre-computed basename grep found ZERO covering plans mentioning this doc's filename anywhere. This is a strong orphan signal, but still verify by reading the doc fully — it may already be self-resolving, superseded by a dated section, or trivially archivable on its own.`

  return `You are auditing ONE doc as part of a DeFi asset-group closeout-completeness audit (the /ag-closeout-audit skill, Phase 1). Your job: read the target doc in FULL, determine its genuinely remaining open work, then judge whether that work is covered by anything currently active/dispatched for the DeFi tranche.

TARGET DOC (read this in full with the Read tool): ${REPO}/${item.path}

Instructions:
1. Read the target doc IN FULL, end to end. Never conclude from checkbox count alone — this corpus has a confirmed trap where real remaining work is expressed as numbered PROSE lists with zero checkboxes. Always read to the doc's END, including any dated "## Update" / "## RE-TRIAGE" / "## RESOLVED" section — these OVERRIDE earlier [x] marks back to open, or vice versa; the latest dated section is authoritative over earlier checkbox state.
2. Note the frontmatter status: and related: fields.
3. Enumerate every genuinely remaining open item (checkbox AND prose-form) as of now — a plan whose every checkbox is [x] but whose prose says "still needs X" has remaining work; a plan with open [ ] checkboxes that a later dated section says are actually done does NOT.
4. ${hitsBlock}
   For each remaining item from step 3, determine: does an existing covering plan's todo fully close it, partially cover it, or not touch it at all? Read the actual citing context (open the covering plan file, find the relevant todo/section) rather than trusting the filename match alone.
5. Sanity-check real scope vs the asset_group tag: if this doc's actual content is NOT really DeFi-primary (e.g. it's actually cross-AG, or its DeFi angle is incidental), verdict exclude_cross_cutting instead.
6. Return your verdict:
   - archivable_now: no genuinely remaining open work (everything is done or was never real work to begin with).
   - archivable_after_planned_work: remaining work is FULLY covered by an existing covering-plan todo that just hasn't shipped yet.
   - orphaned_partial_coverage: SOME remaining items are covered, others are not.
   - orphaned_never_touched: remaining work exists and NOTHING currently active/dispatched touches it.
   - exclude_cross_cutting: this doc isn't really DeFi-primary despite its tag/filename.

Be precise and evidence-based — cite the specific todo/section you found, don't guess. Call the StructuredOutput tool with your verdict.`
}

phase('Classify')

const results = await pipeline(args, (item) =>
  agent(buildPrompt(item), {
    phase: 'Classify',
    schema: SCHEMA,
    label: item.path.split('/').pop(),
  })
)

return results.filter(Boolean)
