---
doc_type: codex-ssot
title: Elysium x IkeNova — Consulting Agreement (underlying contract, verbatim)
summary: >-
  Verbatim record of the underlying Elysium AM Ltd <-> IkeNova Ltd Consulting Agreement, copied into codex from the
  e-signed PDF (Doc ID 5f6491d2...) so the contract text is available in-repo. Carries the Article-4 work-product
  ownership position (ALL Work Product is the Group's, perpetually), the Article-6.2 24-month non-compete, Annex A's
  $45k+$45k phase split and scope exclusions, plus the version/date discrepancy and the drafting defects found on
  transcription.
status: current
nature: record
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, contract, ip-ownership, non-compete, source-document]
related:
  [
    /codex/14-customer-journeys/commercial-model/contracts/elysium-subcontracting-agreement-ikenova-odum.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/pod-elysium-client-onboarding.md,
    /plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md,
  ]
created: 2026-08-11
authoritative_for:
  [
    verbatim text of the Elysium x IkeNova Consulting Agreement,
    Article 4 work-product ownership position,
    Article 6.2 non-compete scope,
    Annex A phase split and scope exclusions,
  ]
referenced_by: []
owner:
last_reviewed: 2026-08-11
code_refs: []
---

# Elysium x IkeNova — Consulting Agreement (underlying contract, verbatim)

> **Provenance (2026-08-11).** Transcribed into codex on operator instruction ("check the contract... copy it into codex
> so that it's here"). Source: `~/Downloads/Elysium_x_IkeNova_contract.pdf`, which carries an e-signature footer
> `Doc ID: 5f6491d203e91ea6c5b836c722dba886e0d1565b` on every page and is therefore taken as the **executed** version.
> Page numbers and the repeated Doc ID footer are stripped; the wording is otherwise verbatim, **including the
> contract's own typos** (see § Drafting defects). Body text below is the contract, not commentary.
>
> **This doc is a RECORD, not an interpretation.** The commercial reading, the Exhibit A carve-out manifest and the
> negotiated positions built on top of this contract live in
> [`elysium-managed-sla-2026-05-14.md`](/codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md).
> Where that doc and this one disagree, **this one wins** — it is the contract.

---

## § Read this first — the ownership position (Article 4)

**Article 4 assigns ALL Work Product to the Group, perpetually, with no time limit and no carve-out for platform code.**
Specifically:

- **4.1** — "all plans, processes, documents, inventions, items, and materials (whether in tangible or electronic form)
  developed, conceptualized or designed by the Consultant" are works made for hire and "the exclusive collective
  property of the Company, its parent company, branch and representative office, subsidiaries, and affiliates
  (collectively, the 'Group')". Note the beneficiary is the **whole Group**, not Elysium AM Ltd alone.
- **4.2** — anything not legally classifiable as work-for-hire is **irrevocably and perpetually assigned** to the Group.
- **4.4** — the Consultant "shall not use, display, link to, reproduce, or **mimic** materials used in creating any Work
  Product **for any purpose whatsoever**" without the Group's express written consent. This is broader than a
  non-compete: it restricts reuse and imitation of the materials themselves.
- **4.5** — on request at any time, the Consultant must "account for and return" all Work Product plus supporting
  "documents, studies, formulas, **codes**, manuals, plans, abstracts, instructions, samples, copies, components, drafts
  or prototypes".
- **4.6** — the Consultant retains **only** "the right to use generic programming methods and open-sourced components".

**Consequences for how we describe the engagement (corrected 2026-08-11).**

1. Statements of the form "we own the trading code" are **wrong on the face of the contract**. Any code, design,
   document or process developed under this engagement is the Group's from creation.
2. What is genuinely ours is (a) whatever pre-dates the engagement, (b) whatever was developed outside its scope, and
   (c) the Art. 4.6 retention (generic methods + open source). Everything else needs the Exhibit A scope argument to
   land — and that argument is a **negotiating position, not a settled entitlement**.
3. Art. 4 has **no expiry**. It is therefore NOT correct to say the client's ownership runs only for the non-compete
   period — those are two independent clauses with different durations (Art. 4: perpetual; Art. 6.2: 24 months). Treat
   any "they own it for the non-compete duration" framing as a commercial _aspiration_ requiring a written variation,
   not as the current position.
4. Art. 4.5's return-on-request right is the practical risk the Exhibit A manifest exists to bound: absent an agreed
   manifest, a request could reach the whole delivered codebase.

## § Drafting defects found on transcription (2026-08-11)

Recorded so nobody "fixes" the verbatim text below, and so they can be raised in any variation:

| #   | Defect                                                                                                                                                                                                                                                                                                                                                      | Where       |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| 1   | Company name misspelled **"Eysium AM Ltd."** (missing the `l`) in the preamble of every version                                                                                                                                                                                                                                                             | Preamble    |
| 2   | **Two clauses numbered 2.2** — "Consultant Representation and Warranty on Personnel and Affiliates" and "Whole Agreement"                                                                                                                                                                                                                                   | Article 2   |
| 3   | Art. 4.1 cross-references **"Section 1.5 above"** for subcontracting, but Article 1 ends at 1.4; the subcontracting clause is **1.4**                                                                                                                                                                                                                       | Article 4.1 |
| 4   | Stray double bracket `"). ).` in the definition of Consulting Services                                                                                                                                                                                                                                                                                      | Article 1.1 |
| 5   | "crypyo" for "crypto"                                                                                                                                                                                                                                                                                                                                       | Article 6.1 |
| 6   | Art. 6.2 reads "For 24 months following **this agreement**" — ambiguous between "following execution" (expiring ~March 2027) and "following termination/completion". Codex previously asserted the latter; the text does not settle it                                                                                                                      | Article 6.2 |
| 7   | Execution date is **unresolved**: the e-signed PDF says **3 March 2025**; the `(w specifics)` DOCX and the track-changes PDF say **1 March 2025**. The subcontracting agreement also says 3 March. Article 4 and Article 6 wording is **identical** across versions, so nothing material turns on it except the date itself and any clock that runs from it | Preamble    |

**Not located:** the variation document behind the $90,000 -> $135,000 fee revision recorded in
[`elysium-managed-sla-2026-05-14.md`](/codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md)
§1. Annex A below totals **$90,000** ($45k + $45k). The uplift is therefore not evidenced by any document currently in
codex or on the operator's machine. Tracked on
[`elysium_sla_v4_support_period_and_stale_dates_2026_08_08`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).

---

## § Verbatim contract text

CONSULTING AGREEMENT

This Consulting Agreement (this “Agreement”), is made and entered into on 3 March 2025 by and among Eysium AM Ltd. (the
“Company”); and IkeNova Ltd, a company incorporated under the laws of the British Virgin Islands, having its registered
office at OMC Chambers, Wickhams Cay 1, Road Town, Tortola, British Virgin Islands, VG1110, Incorporation number 2169565
(the “Consultant”).

ARTICLE 1

SCOPE OF WORK

1.1 Services. The Company has engaged Consultant to provide services in connection with the Company’s cryptocurrency
delta one trading strategy development. Consultant will provide labor and services with the purpose of developing a
delta neutral cryptocurrency basis algorithmic trading system (collectively, the “Consulting Services”). ). Details of
the Consulting Services and corresponding Compensation are further set forth in Annex A of this Agreement. The parties
agree that the Company may change the Consulting Services subject to prior written notice to the Consultant.

1.2 Confidentiality. In order for Consultant to perform the Consulting Services, it may be necessary for the Company to
provide Consultant with Confidential Information (as defined below) regarding the Company’s business and products. The
Company will rely heavily upon Consultant’s integrity and prudent judgment to use this information only in the best
interests of the Company.

1.3 Standard of Conduct. In rendering Consulting Services under this Agreement, Consultant shall conform to high
professional standards of work and business ethics. Consultant shall not use time, materials, or equipment of the
Company without the prior written consent of the Company. In no event shall Consultant take any action or accept any
assistance or engage in any activity that would result in any university, governmental body, research institute or other
person, entity, or organization acquiring any rights of any nature in the results of work performed by or for the
Company.

1.4 Outside Services. Consultant may use the service of any other person, entity, or organization in the performance of
Consultant’s duties subject to the prior written consent of an officer of the Company. Should the Company consent to the
use by Consultant of the services of any other person, entity, or organization, no information regarding the services to
be performed under this Agreement shall be disclosed to that person, entity, or organization until such person, entity,
or organization has executed an agreement to protect the confidentiality of the Company’s Confidential Information (as
defined in Article 5) and the

Company’s absolute and complete ownership of all right, title, and interest in the work performed by such third party
engaged by the Consultant.

ARTICLE 2

INDEPENDENT CONTRACTOR

2.1 Independent Contractor. Consultant is an independent contractor and is not an employee, partner, or co-venturer of,
or in any other service relationship with, the Company. The manner in which Consultant’s services are rendered shall be
within Consultant’s sole control and discretion. Consultant is not authorized to speak for, represent, or obligate the
Company in any manner without the prior express written authorization from an officer of the Company.

2.2 Consultant Representation and Warranty on Personnel and Affiliates. Consultant shall ensure that all personnel
and/or affiliates performing the Services under this Agreement are bound by the terms and provisions of this Agreement.
Consultant represents and warrants that all such personnel have been informed of and will strictly comply with these
obligations.

2.2 Whole Agreement. This Agreement defines the terms for the establishment of the Company’s crypto basis funding
strategy and represents the whole agreement among the parties.

2.3 Best efforts to establish future engagement. The parties acknowledge that this strategy will be subject to ongoing
development, improvement, optimisation, and maintenance. Subject to the satisfactory completion of this agreement (as
determined by both parties), the Company and Consultant shall exert best efforts over a reasonable time period (not
shorter than 30 days not longer than 90 days) to establish further agreement with respect to Consultant satisfying the
ongoing role noted above which shall be subject to further agreement and subject to contract.

ARTICLE 3

TERM AND TERMINATION

3.1 Compensation. The Company shall pay to Consultant the fee schedule defined in

Annex A of this Agreement. Each payment shall be completed no later than 10 business days from the due date defined in
Annex A.

3.2 Term. This Agreement shall be divided into two Phases as defined in Annex A. The commencement of Phase Two shall be
at a date agreed by the parties. The parties expect the total project engagement to be 8 months allocated as follows:

 Months 1-4: Research & Design Phase o Data infrastructure setup o Initial strategy development o Risk framework design
o Backtesting environment  Months 4-6: Development & Testing o Core system implementation o Exchange integration o
Initial testing o Performance optimization  Months 6-8: Production & Deployment o Production system setup o Live
testing o Monitoring implementation o Documentation and training

3.3 Termination. Neither party may terminate this Agreement within a Phase which has commenced.

3.4 Responsibility upon Termination. Any material, document, Confidential Information or equipment provided by the
Company to the Consultant in connection with or furtherance of the Consulting Services under this Agreement, including,
but not limited to, computers, laptops, and personal management tools, shall, immediately upon the termination of this
Agreement, be returned to the Company.

3.5 Survival. The provisions of Articles 4, 5, 6, and 7 of this Agreement shall survive the termination of this
Agreement and remain in full force and effect thereafter.

ARTICLE 4

NON-IMPAIRMENT OF RIGHTS IN WORK PRODUCT

4.1 The Consultant affirms that all plans, processes, documents, inventions, items, and materials (whether in tangible
or electronic form) developed, conceptualized or designed by the Consultant (on his own or through a subcontractor, as
provided in Section 1.5 above) are works made for hire (“Work Product”), which, along with any intellectual property
rights attaching to such Work Products, are the exclusive collective property of the Company, its parent company, branch
and representative office, subsidiaries, and affiliates (collectively, the “Group”).

4.2 To the extent that any Work Product cannot be legally classified as works made for hire, the Consultant hereby
irrevocably and perpetually assigns to the Group his ownership of, title to, and all intellectual property rights in
such Work Product.

4.3 The Consultant shall cooperate with the Group at all times to perfect, protect or defend the Group’s rights over any
Work Product.

4.4 The Consultant shall not use, display, link to, reproduce, or mimic materials used in creating any Work Product for
any purpose whatsoever, nor shall he claim authorship of or claim any residual rights over the same, without the express
written consent of the Group.

4.5 Any time upon request by the Group, the Consultant shall account for and return to the Group all Work Products and
their supporting documents, studies, formulas, codes, manuals, plans, abstracts, instructions, samples, copies,
components, drafts or prototypes.

4.6 The Consultant retains the right to use generic programming methods and open-sourced components.

ARTICLE 5

NON-DISCLOSURE OF CONFIDENTIAL INFORMATION

5.1 As used in this Agreement, “Confidential Information” is any insight, information, or trade secret stored or shared
in any form that the Consultant may learn, have access to or develop in the course of his engagement with the Company,
which includes but is not limited to the following -

5.1.1 the Group’s Work Product, business relationships, operations, projects, plans, processes, policies, strategies,
techniques; financial position, status, sources, resources, costs, and expenses; contracts, agreements, research, data,
documents, statistics, products, services, and ideas; devices, facilities, software, tools, and applications; suppliers,
vendors, contractors, competitors, and clients

5.1.2 information about any of the affiliates, subsidiaries, branch or representative office, and parent company
comprising the Group, and any fund, business associate, joint venture partner or managed entity of any Group member

5.1.3 personal information of the Group’s directors, officers, shareholders, employees, agents, lenders, investors,
lawyers, accountants, advisors, and consultants (“Representatives”), and

5.1.4 any note, invention, material, process, correspondence, memorandum, manual, study, opinion, report, audiovisual
presentation, advisory, summary, white paper or document based on or with reference to Confidential Information; and

5.1.5. the terms and conditions set out in this Agreement, including but not limited to your Basic Monthly Compensation.

5.2 The Consultant shall keep all Confidential Information in absolute secrecy, and shall not share, divulge or use the
same without the prior written consent of the Group.

5.3 The Consultant shall not interfere in any way with the Group’s use, transfer or disclosure of any of its
Confidential Information. Further, the Consultant shall not seek payment for having contributed to the creation,
discovery, improvement or development of any Confidential Information, over and above the compensation already set forth
in this Agreement, unless otherwise agreed with the Group in writing.

ARTICLE 6

NON-DISCLOSURE, NON-COMPETITION, AND NON-SOLICITATION

6.1. Non-Disclosure to Competitors. You understand that maintaining the Group’s competitive advantage necessitates
protecting its Confidential Information against disclosure to entities or individuals that are engaged in any business
that is similar to us or any member of the Group, including but not limited to any crypyo basis funding trading strategy
or system, and any fund tokenisation initiative

6.2. Non-Competition. For 24 months following this agreement, the Consultant agrees not to engage in:  Tokenisation of
investment funds  Systematic DeFi Basis trading and funding strategies premised on staking/re-staking  Systematic CeFi
funding rate and staking yields strategies whose primary objective is capturing funding rates (aka. basis)

6.3. Non-Solicitation. For a period of two (2) years from the end of your engagement with the Company, you agree that
you will not, for yourself or on behalf of any Competitor, directly or indirectly, perform any of the following
prohibited acts:

1. Solicit, invite, or induce, or attempt to solicit, invite or induce the Representatives of any Group member to
   terminate or violate their engagement with the Group and instead be engaged by, work with or promote a Competitor in
   any capacity; and

2. Solicit, invite, or induce, or attempt to solicit, invite or induce the Group’s Customers to avail themselves of any
   product or service offered by any entity, whether or not a Competitor.

"Customer" means any entity which has been captured in the Group’s customer list anytime during your engagement with the
Company, regardless of whether you have personal knowledge of such a list or whether the Customer actually obtains
credit products from us.

6.4 Disclosures. The Consultant has disclosed existing roles and projects enumerated in

Annex B. The Consultant confirms that these activities do not compete with the strategy being developed under this
Agreement.

ARTICLE 7

GENERAL PROVISIONS

7.1 Construction of Terms. If any provision of this Agreement is held unenforceable by a court of competent
jurisdiction, that provision shall be severed and shall not affect the validity or enforceability of the remaining
provisions.

7.2 Governing Law. This Agreement shall be governed by and construed in accordance with the internal laws (and not the
laws of conflicts) of Ireland.

7.3 Complete Agreement. This Agreement constitutes the complete agreement and sets forth the entire understanding and
agreement of the parties as to the subject matter of this Agreement and supersedes all prior discussions and
understandings in respect to the subject of this Agreement, whether written or oral.

7.4 Dispute Resolution. If there is any dispute or controversy between the parties arising out of or relating to this
Agreement, the parties agree that such dispute or controversy will be arbitrated in accordance with the rules of the
Irish Arbitration Centre, and such arbitration will be the exclusive dispute resolution method under this Agreement. The
decision and award determined by such arbitration will be final and binding upon both parties. All costs and expenses,
including reasonable attorney’s fees and expert’s fees, of all parties incurred in any dispute that is determined and/or
settled by arbitration pursuant to this Agreement will be borne by the party determined to be liable in respect of such
dispute; provided, however, that if complete liability is not assessed against only one party, the parties will share
the total costs in proportion to their respective amounts of liability so determined. Except where clearly prevented by
the area in dispute, both parties agree to continue performing their respective obligations under this Agreement until
the dispute is resolved.

7.5 Modification. No modification, termination, or attempted waiver of this Agreement, or any provision thereof, shall
be valid unless in writing signed by the party against whom the same is sought to be enforced.

7.6 Waiver of Breach. The waiver by a party of a breach of any provision of this Agreement by the other party shall not
operate or be construed as a waiver of any other or subsequent breach by the party in breach.

7.7 Successors and Assigns. This Agreement may not be assigned by either party without the prior written consent of the
other party; provided, however, that the Agreement shall be assignable by the Company without Consultant’s consent in
the event the Company is acquired by or merged into another corporation or business entity. The benefits and obligations
of this Agreement shall be binding upon and inure to the parties hereto, their successors and assigns.

7.8 No Conflict. Consultant warrants that Consultant has not previously assumed any obligations inconsistent with those
undertaken by Consultant under this Agreement.

IN WITNESS WHEREOF, this Agreement is executed as of the date set forth above.

---

PATRICK LYNCH IKENNA IGBOAKA Director Director For and on behalf of Group: For and on behalf of Consultant: Elysium AM
Ltd. IkeNova Ltd

Annex A - Details of Consulting Services

Phases

Phase One: Research & Design: $45,000 The output of Phase One is a CeFi & DeFi basis trading strategy in BTC, ETH, and
SOL and their respective perpetuals/derivates whose performance, risk/volatility, and liquidity is understood across
major trading venues (CeFi and DeFi)  Development of back-testing framework  Strategy documentation and design 
Performance analysis methodology  Risk management framework design  Historical performance, risk & volatility, and
liquidity of basis trading strategy across major trading venues and staking/re-staking programs  Execution plan to
bring trading strategy to life

Phase Two: Production Implementation: $45,000 The output of Phase Two is the market-execution of the trading strategy
developed in Phase One with the capacity to trade across major trading venues (CeFi and DeFi):  Development of
production trading system designed in Phase One  Monitoring dashboard implementation  Risk management system
deployment  Documentation and training  Pilot execution with ‘seed’ capital provided by Company

Acceptance & Testing Each phase shall be subject to testing and acceptance by the Client. The Client shall have 10
business days to review and accept or reject each deliverable.

Any rejection must be accompanied by specific written details of the deficiencies. The Contractor shall have 10 business
days to remedy any deficiencies.

Payment Terms for Phase Commencement and Completion Each Phase is considered independent.  Phase One commences as of
the date of this Agreement  Phase Two commences at a date agreed by the parties

Each Phase shall follow the same payment terms:  50% upon Commencement  50% upon Phase Completion & Acceptance

Scope Exclusions:

 Tokenisation of fund  Fund setup and administration  Fund settlement and clearing  Prime broker/exchange
relationship management  Ultra low latency execution  Liquidity provision  Post-launch maintenance and upgrades (can
be arranged separately)

Annex B – Disclosures

1. Board position on crypto launchpad 2. Cross exchange DeFi arbitrage development 3. Tokenized launchpad development 4.
   Previous HFT strategy operation 5. AI machine learning prediction strategy development

Sign Audit trail

Elysium x IkeNova contract Title

File name 20250301___Elysiu...reement__vFF.docx

Document ID 5f6491d203e91ea6c5b836c722dba886e0d1565b Audit trail date format MM / DD / YYYY Status Signed

03 / 03 / 2025 Sent for signature to Patrick Thomas Lynch 00:13:48 UTC (lynch.patrickt@gmail.com) and Ikenna Igboaka
(ikenna@odum-research.com) from patrick@firstcircle.com IP: 194.156.224.44

03 / 03 / 2025 Viewed by Patrick Thomas Lynch (lynch.patrickt@gmail.com) 00:19:13 UTC IP: 194.156.224.44

03 / 03 / 2025 Signed by Patrick Thomas Lynch (lynch.patrickt@gmail.com) 00:19:31 UTC IP: 194.156.224.44

03 / 03 / 2025 Viewed by Ikenna Igboaka (ikenna@odum-research.com) 00:20:10 UTC IP: 199.79.156.50

03 / 03 / 2025 Signed by Ikenna Igboaka (ikenna@odum-research.com) 00:20:31 UTC IP: 199.79.156.50

03 / 03 / 2025 The document has been completed. 00:20:31 UTC

Powered by Sign
