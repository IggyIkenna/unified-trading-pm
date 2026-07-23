---
doc_type: codex-ssot
title: Rule 02 — Tone and posture
summary:
  "Odum's external-voice standard — calm, specific, credible, present-tense, lightly guided; institutional not
  crypto-native — with the banned AI-marketing patterns/postures list and the read-aloud / delete-adverbs /
  banned-vocab-grep enforcement pass."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [customer-journey, sales, tone, branding, docspec]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/01-grammar.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
  ]
created: 2026-04-20
authoritative_for: [Odum external voice and tone standard]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/01-grammar.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/experience/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 02 — Tone and posture

> Calm, specific, credible, lightly guided. Never desperate. Restrained institutional voice. Written by people who have
> run trading businesses — not by a marketing engine trying to sound like one.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On tone + posture".

## The posture

Odum's external voice is the voice a mid-career CIO would use describing their own operation to a peer. Assumed
seriousness, specific numbers where they matter, no hedging where certainty exists, no overclaiming where it doesn't.
The product is live. The firm is operating. Content should read that way.

Three postural rules collapse out of this:

1. **Present tense.** The platform exists. The strategies run. The reporting ships. Do not write in forward-looking
   tense ("we will offer", "we're building"). If something does not exist yet, do not write about it in an experience
   doc — it belongs in a roadmap.
2. **Specific over evocative.** "Thirteen pricing building blocks, two external tiers, twelve-month minimum." Not:
   "Flexible, institutional-grade pricing tailored to your needs." The specific version is shorter and more credible.
3. **Lightly guided.** Point the reader at what matters without walking them through the conclusion. An institutional
   reader resents being spoon-fed. Lay out the claim, the evidence, and let them close the loop.

## Benchmarks

### What to borrow from [axis.to](https://www.axis.to/)

- Restrained headline density. Two or three headline ideas on a page, not twelve.
- Proof points expressed as concrete capabilities ("venue X, chain Y, protocol Z"), not abstract adjectives
  ("comprehensive", "powerful").
- Sparse navigation. Every link earns its place.
- A few numbers that matter, on the page, without ceremony.

### What to borrow from [podlabs.xyz](https://podlabs.xyz/)

- Operating-team voice. Written by people who ship, not by a brand agency.
- Clean visual hierarchy; restrained typography.
- No waitlist energy. Product is live, take it or leave it.
- Low-drama trust markers: names of things that exist, commitments that are plainly stated.

### What NOT to borrow from either

- Crypto-native vocabulary. Odum sells to institutional allocators, regulated funds, and operating hedge funds; the
  language is institutional finance, not Web3 Twitter.
- Any implication of coming-soon / waitlist-first. Odum is live and operating.
- Visual flourishes that don't serve a claim.

## The anti-AI-tone guardrails

Generic AI-generated marketing copy has a recognisable signature. Avoid it.

**Banned patterns:**

- "Revolutionary" / "groundbreaking" / "cutting-edge" / "best-in-class" / "world-class" / "state-of-the-art".
- "We help [X] to [Y]" construction. Replace with a specific observed change. ("Allocator X cuts reconciliation from
  three days to four hours.")
- "Unlock" as a verb. ("Unlock the power of systematic trading.") Replace with what specifically becomes possible.
- Empty tricolons. ("Data. Analytics. Execution.") If the tricolon doesn't carry a claim, delete it.
- Adverb-laden assurances. ("Seamlessly", "effortlessly", "intuitively", "powerfully".) Describe the mechanism, not the
  feeling.
- Forward-tense marketing hedges. ("We're building the future of...") Odum ships present-tense content only.
- Emoji in prose. Bullet-point decoration is fine in code; prose stays clean.
- "Join our waitlist" / "get early access" / "be the first to". Odum is live.

**Banned posture:**

- Conversion pressure. No countdowns, no "limited spots", no "this offer expires".
- Overclaiming scale. Don't invent AUM, trader headcount, or venue breadth you don't have. Specificity survives due
  diligence; puffery doesn't.
- Competitor disparagement. Odum describes what Odum does; other firms are not named.
- Personal-brand voice. No "I built this because..." founder narratives in product docs. Founder voice has a home
  (investor comms, firm page); product docs are operational.

## Writing rhythm

- **Short sentences beat long ones.** Especially in bulleted lists. A bullet that wraps two lines is usually two
  bullets.
- **Paragraphs over bullets for narrative.** Walkthrough sections in briefings are prose. Bulleted walls of capability
  statements read as brochures.
- **Specific numbers on the page.** When a claim has a number, put it on the page. "Twelve-month minimum" lands harder
  than "long-term commitments".
- **No throat-clearing.** Don't open with "In today's complex markets...". Open with the audience's actual situation or
  a concrete statement about Odum.
- **One idea per sentence.** Comma-chained multi-clause sentences dilute claims.

## Voice calibration — two worked examples

### Example A — bad, revised

> **Bad (AI-generated marketing register):** "Odum's revolutionary platform empowers institutional clients to unlock the
> full potential of systematic trading through our cutting-edge, best-in-class infrastructure."

> **Good (Odum voice):** "Odum runs systematic strategies on its own capital, under its own FCA permissions, on
> infrastructure we built to run them. Clients either allocate capital to those strategies (IM), operate their own
> strategies on the same infrastructure (DART), or operate regulated activity under our cover (Reg Umbrella)."

The revised version takes two extra sentences to say three specific things. Worth it.

### Example B — bad, revised

> **Bad (forward-tense, waitlist posture):** "Coming soon: Odum's next-generation client reporting. Sign up for early
> access to be the first to experience our unified reporting surface."

> **Good:** "Client reporting is the same surface Odum uses internally. IM allocators and Reg Umbrella firms land on one
> route; entitlement-sliced views render from the same component tree. Book a walkthrough."

## Enforcement rules

1. **Read aloud before ship.** Every experience playbook gets read aloud by the author. Awkward marketing phrasing
   reveals itself instantly.
2. **Delete adverbs.** One pass per doc, deleting every `-ly` adverb. Reinstate only the ones that change meaning.
3. **Replace abstractions with specifics.** Every abstract noun ("solutions", "capabilities", "excellence") gets swapped
   for a specific thing or deleted.
4. **Check present tense.** No forward-tense marketing. If something doesn't exist, it doesn't go in an experience doc.
5. **Banned vocabulary audit.** Grep each doc for the banned pattern list above; zero matches required.
6. **Peer read by an operating voice.** Before commit, have someone who runs (or has run) an operating trading business
   read the doc. If they wince, fix it.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On tone + posture"
- [`01-grammar.md`](01-grammar.md) — the nine-section structure rule 02 fills
- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — what to leave off the page
- [`09-internal-commercial-oneliners.md`](09-internal-commercial-oneliners.md) — internal shorthand that expands into
  rule-02 voice for external docs
- [`../experience/im-decision-journey.md`](../experience/im-decision-journey.md) — canonical filled example of rule-02
  voice in a nine-section playbook
