# AWS Credits Negotiation Strategy

**Purpose:** Laser-focused strategy for securing $200K-$300K in AWS migration credits  
**Target:** AWS Migration & Modernization Program (MMP)  
**Timeline:** Decision by end Q1 2026, migration start Q2 2026

---

## Executive Summary

**The Ask:** $250,000 in migration credits

**The Justification:**

- Year 1 AWS spend: $540K-756K (projected)
- Credits = 33-46% of Year 1 spend (within normal MMP range)
- FCA-regulated financial services (strategic vertical)
- 50TB+ data migration from GCP (competitive displacement)
- Bedrock (Claude) heavy usage (strategic product)
- Public case study opportunity

**The Leverage:**

- You're leaving GCP (AWS wins)
- You have real production workload (not prototype)
- You're AI-heavy (Bedrock strategic priority)
- You're financial services (strategic vertical for AWS UK)
- You're willing to be case study (marketing value)

**Realistic Outcome:** $200K-$300K (very achievable with correct approach)

---

## The Three Decks - Know Which to Use When

### 1. ✅ **aws-credits-request.html** (THIS ONE FOR CREDITS)

**Use for:** MMP application, credits negotiation, AWS account executive  
**Focus:** Spend projections, migration timeline, concrete numbers  
**Tone:** Practical, financially grounded, "here's the AWS revenue"

### 2. **aws-autonomous-development-pitch.html** (PARTNERSHIP/VISION)

**Use for:** AWS partnerships team, Bedrock specialists, technical deep-dive  
**Focus:** Platform capabilities, AI workload, long-term vision  
**Tone:** Visionary, technically impressive, "here's the future"  
**Warning:** ⚠️ Do NOT use for credits ask (too visionary, scares finance team)

### 3. **gemini-autonomous-development-pitch.html** (GOOGLE)

**Use for:** Google Gemini team if you decide not to migrate  
**Focus:** Current GCP platform, Gemini integration

---

## Who to Contact at AWS

### Priority 1: AWS Account Executive (UK Financial Services)

**Why:** Gateway to MMP, credits approval, enterprise support  
**How to find:**

- AWS website contact form → "I'm an FCA-regulated investment manager migrating from GCP"
- Request "UK Financial Services vertical team"
- Mention "interested in MMP for 50TB+ data migration"

**What to say:**

```
"We're Odum Capital, an FCA-regulated investment manager currently on GCP.
We're evaluating migration to AWS and are interested in the Migration &
Modernization Program. We have 50TB+ data, 30 microservices, and project
$540K-756K Year 1 AWS spend. Can we schedule a call with the UK Financial
Services team?"
```

### Priority 2: AWS Migration & Modernization Program (MMP)

**Why:** This is where migration credits come from  
**How to find:** AWS account executive will connect you  
**What to prepare:** aws-credits-request.html deck + GCP bill screenshots

### Priority 3: AWS Bedrock Specialist Team

**Why:** Heavy AI workload = leverage for credits  
**How to find:** Via account executive  
**What to say:** "We're migrating from Gemini to Claude, 50M-100M tokens/month"

---

## The Call Script

### Initial AWS Account Executive Call (30 minutes)

**Opening (2 min):**

```
"Thanks for taking the call. I'm Ikenna from Odum Capital. We're an
FCA-regulated investment manager based in the UK. We're currently running
on Google Cloud and evaluating a migration to AWS.

Quick context: We have 50TB+ of market data, 30 microservices, and we're
spending about $60-75K/month on GCP. We're particularly interested in
Bedrock for our AI workloads and the Migration & Modernization Program."
```

**The Ask (1 min):**

```
"We're projecting $540K-756K in AWS spend over Year 1, scaling to $1M+ by
Year 3. We're applying for the MMP and are requesting $250,000 in migration
credits to help with the transition costs - data migration, parallel run,
testing, etc.

Given our spend projection, that's about 33-46% of Year 1, which I
understand is within the typical MMP range."
```

**The Value Prop (2 min):**

```
"Why this makes sense for AWS:

1. We're a competitive win from GCP - 50TB+ data migration
2. We're FCA-regulated financial services - strategic vertical for AWS UK
3. We're AI-heavy - perfect Bedrock case study (Claude for code generation)
4. We're willing to be a public case study
5. This is a long-term relationship - we're projecting growth to $1M+ by Year 3

Plus our data is sticky - once 50TB is in S3, we're not moving it again."
```

**Next Steps (2 min):**

```
"What I'd like to do:

1. Share our credits request deck with you
2. Schedule a technical deep-dive with your solutions architect
3. Get connected to the MMP team
4. Get an introduction to the Bedrock specialists

Timeline-wise, we're looking to decide by end of Q1 and start migration
in Q2. Does that work?"
```

**Questions to Ask:**

- "What's the typical timeline for MMP credits approval?"
- "What additional information do you need from us?"
- "Who should I speak to on the Bedrock team?"
- "Is $250K realistic given our projected spend?"
- "What's the process for becoming an AWS case study?"

---

## Key Numbers to Memorize

**Current State (GCP):**

- Monthly spend: $60K-75K
- Annual spend: $720K-900K
- Storage: 50TB+
- Services: 30 microservices
- Been on GCP: ~2 years

**Projected State (AWS):**

- Year 1: $540K-756K (conservative)
- Year 2: $800K-1M (growth)
- Year 3: $1.2M-1.5M (scale)
- Storage: 50TB → S3 (saving 60% vs GCS)
- Compute: Lambda + ECS (saving 30-40% vs Cloud Run)
- AI: Bedrock (50M-100M tokens/month, saving 40-50% vs Gemini)

**The Ask:**

- Amount: $250,000
- Program: MMP (Migration & Modernization Program)
- Use: Data migration, parallel run, testing, training
- As % of Year 1: 33-46%

**ROI for AWS:**

- Credits: $250K
- Year 1 revenue: $540K-756K (net $290K-506K)
- Year 2 revenue: $800K-1M
- Year 3 revenue: $1.2M-1.5M
- **3-year total: $2.5M-3.2M**

---

## Month-by-Month AWS Spend Model

This is what AWS finance team wants to see.

| Month | Phase                      | Storage | Compute | Data Warehouse | AI/ML | Other | **Total**   | **Notes**                        |
| ----- | -------------------------- | ------- | ------- | -------------- | ----- | ----- | ----------- | -------------------------------- |
| M1    | Data migration start       | $15K    | $5K     | $0             | $2K   | $3K   | **$25K**    | DataSync + S3, GCP still running |
| M2    | Data migration complete    | $20K    | $5K     | $5K            | $2K   | $3K   | **$35K**    | 50TB in S3, Athena testing       |
| M3    | Compute migration start    | $10K    | $20K    | $8K            | $3K   | $4K   | **$45K**    | Lambda + ECS pilot (15 services) |
| M4    | Compute migration complete | $10K    | $25K    | $10K           | $4K   | $5K   | **$54K**    | All 30 services on AWS           |
| M5    | AI/ML migration            | $11K    | $25K    | $10K           | $8K   | $5K   | **$59K**    | Bedrock + SageMaker              |
| M6    | Full production            | $12K    | $25K    | $11K           | $8K   | $5K   | **$61K**    | GCP decommissioned               |
| M7-12 | Steady state               | $12K    | $25K    | $11K           | $8K   | $5K   | **$61K/mo** | × 6 months = $366K               |

**6-Month Total:** $279K (ramp-up) + $366K (steady) = **$645K**  
**12-Month Total:** $645K (first 6) + ~$100K (buffer/growth) = **$540K-756K**

**GCP Parallel Run Cost (Months 1-4):**

- $60K × 4 months = $240K
- This is what credits help with (running both clouds in parallel)

---

## What NOT to Say

❌ "We could make $180M-250M annual revenue"  
✅ "We project $540K-756K Year 1 AWS spend"

❌ "Our platform will transform trading"  
✅ "We're migrating 50TB from GCP to S3"

❌ "We have a 9-stage maturity model"  
✅ "We have 30 production microservices ready to migrate"

❌ "This is a huge opportunity for AWS"  
✅ "Here's the concrete AWS spend over 12 months"

**Why:** AWS credits are tied to **projected spend**, not potential revenue. Finance teams want concrete numbers, not
vision.

---

## The Counter-Offer Strategy

AWS will likely counter with less than $250K. Here's how to respond:

### If they offer $150K-200K:

**Response:** "We can make that work if we adjust the migration timeline to reduce parallel run costs. Can we also get
AWS Professional Services support included?"

### If they offer $100K-150K:

**Response:** "That's lower than we hoped given our $540K-756K Year 1 spend. Can we revisit this after 6 months once
we've proven out the spend projections?"

### If they offer $50K-100K:

**Response:** "That doesn't really move the needle for us. Our decision on AWS vs staying on GCP will be heavily
influenced by migration support. Is there any flexibility?"

**The Walk-Away:** "We'll need to reconsider the migration timeline or potentially stay on GCP."

**Why this works:** AWS wants the competitive win over GCP. The threat of staying on GCP gives you leverage.

---

## Supporting Materials to Prepare

### 1. GCP Bill Screenshots (Last 3 Months)

Show them you're a real customer spending $60K-75K/month. Redact sensitive details but show:

- Total monthly spend
- Breakdown by service (GCS, Cloud Run, BigQuery, etc.)
- Trend over time

### 2. Architecture Diagram

One-page diagram showing:

- Current GCP architecture
- Target AWS architecture
- Service mapping (GCS → S3, Cloud Run → Lambda/ECS, etc.)

### 3. Migration Plan (One-Pager)

- Month 1-2: Data
- Month 3-4: Compute
- Month 5: AI/ML
- Month 6: Full production
- Milestones + success criteria

### 4. Spend Projection Spreadsheet

Excel/Google Sheet with:

- Month-by-month AWS service costs
- Conservative vs optimistic scenarios
- 3-year projection

### 5. FCA Authorization Proof

- Company registration
- FCA authorization letter
- Confirms you're regulated financial services (strategic vertical)

---

## Common Objections & Responses

### Objection: "Your projected spend is lower than current GCP spend. Why should we give credits?"

**Response:** "We're optimizing as we migrate - S3 Intelligent Tiering, Athena vs BigQuery, Lambda vs Cloud Run. But
even at $540K, that's net $290K+ Year 1 after credits, scaling to $1M+ by Year 3. Plus you get a competitive win over
GCP."

### Objection: "$250K is high for a first-year customer."

**Response:** "We're not a startup - we're an FCA-regulated investment manager with $720K current cloud spend. Year 1
AWS spend is $540K-756K, so $250K is 33-46%, within typical MMP range. Plus we're committing to public case study."

### Objection: "We need more proof you'll actually spend that much."

**Response:** "Happy to structure this as milestone-based credits:

- $50K upon 50TB data migration complete
- $100K upon 15 services migrated
- $100K upon full GCP decommission That way you only pay for results."

### Objection: "Can you do the migration without credits?"

**Response:** "We can, but it makes the economics much tighter. We're evaluating AWS vs staying on GCP vs potentially
Azure. Credits significantly tip the balance toward AWS."

---

## Success Metrics

You'll know the negotiation is going well when:

✅ AWS assigns you a dedicated account executive (not general support)  
✅ You get connected to UK Financial Services team (not general sales)  
✅ AWS Solutions Architect schedules technical deep-dive  
✅ MMP application moves to "under review" quickly  
✅ Bedrock team reaches out (confirms AI workload interest)  
✅ They ask for case study details (confirms marketing value)

You'll know it's not going well when:

❌ They refer you to standard Activate program ($5K-25K)  
❌ Long delays in response  
❌ Keep asking for more "proof of spend"  
❌ Won't commit to timeline  
❌ Try to push you to start migration before credits approved

---

## The Bottom Line

**What You Need to Communicate:**

1. **We're real:** $60K-75K/month current GCP spend, 50TB+ data, 30 services
2. **We're strategic:** FCA-regulated, AI-heavy, financial services vertical
3. **We're committed:** $540K-756K Year 1, scaling to $1M+ by Year 3
4. **We're valuable:** Public case study, reference customer, competitive GCP win
5. **We're reasonable:** $250K = 33-46% of Year 1 spend (typical MMP range)

**What You Don't Need to Communicate:**

❌ $180M-250M revenue potential  
❌ 9-stage maturity model  
❌ Autonomous development platform vision  
❌ Long-term transformation goals

**Save the vision for:**

- Technical deep-dive with Solutions Architect
- Bedrock specialist team
- AWS blog post / case study (after migration)

---

## Timeline

| Week     | Action                                       | Owner        |
| -------- | -------------------------------------------- | ------------ |
| Week 1   | Contact AWS via website form                 | You          |
| Week 1   | Schedule call with AWS Account Executive     | AWS          |
| Week 2   | Initial call (use script above)              | You + AWS    |
| Week 2   | Share aws-credits-request.html deck          | You          |
| Week 3   | Technical deep-dive with Solutions Architect | You + AWS SA |
| Week 3   | MMP application submission                   | You          |
| Week 4   | Connect with Bedrock team                    | AWS          |
| Week 5-6 | MMP review process                           | AWS internal |
| Week 7   | Credits approval (target)                    | AWS          |
| Week 8   | Migration kickoff                            | You          |

**Critical deadline:** End of Q1 2026 (March 31) for decision

---

## If They Say No

**Plan B:**

1. Ask for smaller amount ($100K-150K)
2. Request AWS Professional Services support instead
3. Request Technical Account Manager (TAM) assignment
4. Negotiate better pricing (reserved instances, savings plans)
5. Revisit after 3 months once spend is proven

**Plan C:**

- Stay on GCP, use their credits for negotiation leverage
- Negotiate with AWS again after 6 months with actual AWS spend proof
- Consider Azure (they're even more aggressive with credits for GCP migrations)

---

## Final Checklist Before The Call

- [ ] Review aws-credits-request.html deck
- [ ] Memorize key numbers (spend projections, timeline, ask amount)
- [ ] Prepare GCP bill screenshots
- [ ] Have architecture diagram ready
- [ ] Practice the call script
- [ ] Clear your calendar for follow-up calls (week 2-4)
- [ ] Get FCA authorization documents ready
- [ ] Identify who can do technical deep-dive (you or CTO)

---

## Realistic Outcome

**Best case:** $250K-300K + TAM assignment + case study opportunity  
**Likely case:** $200K-250K + AWS Solutions Architect support  
**Acceptable case:** $150K-200K + ProServe discount  
**Walk-away:** <$100K or too many conditions

Given your profile:

- FCA-regulated ✅
- 50TB+ data ✅
- $720K current cloud spend ✅
- AI-heavy ✅
- GCP → AWS migration ✅
- Public case study ✅

**Prediction: $200K-250K is very achievable.**

Go get it! 💪

---

**Next Step:** Contact AWS UK via website, request Financial Services team, mention MMP + 50TB migration from GCP.

**Status:** Ready to execute  
**Date:** 2026-02-13  
**Version:** 1.0
