# Methodology

The full description of the pipeline, the philosophy behind it, and the rules that hold it together.

## Why this pipeline exists

AI tools make it trivial to generate evidence in favor of any hypothesis. Ask a research assistant to validate an idea — it will find support. Ask it to size a market — it will return a fundable number. This is not malice; it is alignment. The system follows the direction you point it in.

For a founder, this is dangerous. The natural failure mode of AI-assisted validation is not "the system gives wrong answers" — it is "the system gives confidently right-looking answers to questions you asked in the wrong way." The result is a thick, well-researched case for a bad idea, built faster than ever before, with the founder fully convinced they performed due diligence.

The pipeline is designed against this failure mode. Every step is structured to surface disconfirming evidence with the same weight as supporting evidence. The user's role is to remain a skeptic of their own hypothesis throughout, with the system enforcing the structure that makes that possible.

## Core principles

### Validation precedes building

The pipeline produces a decision artifact, not a product. A `build` decision is the output, not the assumption. If a hypothesis cannot pass this pipeline, no code should be written for it.

### Adversarial is structural, not cosmetic

Disconfirming evidence is a first-class artifact. It lives in its own file with the same prominence as supporting evidence. If the supporting file is three pages and the disconfirming file is two paragraphs, that asymmetry is itself a signal worth investigating.

### Calibration before evidence

Before collecting any external data, the user records their priors: what they expect the data to show. After collection, deviations from those priors are inspected. If the data matches expectations perfectly, that is grounds for suspicion — real data rarely fits a hypothesis cleanly.

### Confidence is explicit

Every decision is tagged with a confidence level (L1/L2/L3). This is non-negotiable. A `build` decision at L1 is allowed but must carry the premature flag. The system never lets confidence remain implicit.

### The founder owns the start and the finish

The middle of the pipeline can be largely automated. The framing and the decision cannot. This is the trade the pipeline makes: speed in the engine, deliberation at the edges.

## Pipeline stages in detail

### Stage 1 — Frame (zone 1, founder-led)

**00_intake.** Raw idea as it appeared in the founder's head. No editing, no shaping. This is the baseline against which evolution is later measured.

**01_sharpened.** The idea converted into a testable hypothesis. Required form: a specific audience, a specific problem, a specific frequency or severity, a specific current behavior. "People struggle with X" is not testable. "[Specific role] at [specific company type] spend [N hours] [frequency] doing [Y] because [Z]" is testable.

**02_assumptions.** Every load-bearing assumption made explicit. The question to drive this: "What would have to be true for this hypothesis to hold?" Each assumption is listed individually so it can be tested separately.

**03_priors.** Before any external data is collected, the founder writes down what they expect to find. This is calibration. After collection, deviations from priors are flagged for inspection.

**04_devils_advocate.** A pre-research adversarial pass. Claude is asked to construct the strongest case against the hypothesis. This produces a list of questions that subsequent research must honestly answer. Hypothesis type (product vs discovery) is declared here and dictates the adversarial pattern.

### Stage 2 — Engine (zone 2, machine-led)

**research_plan.md.** What will be collected, from where, with what budget, in what mode (lean/full). Sources are tied to specific questions raised by the frame stage. Made explicit so the run is reproducible and the cost is bounded.

**collection/competitors.md.** Competitive landscape mapped by tier: direct competitors, indirect competitors, adjacent players, potential acquirers. For each tier, the strongest case for why they pose a threat — not the dismissible version.

**collection/market.md.** Both top-down and bottom-up sizing, separately. The gap between them is itself informative. Buyer landscape: who holds budget, who influences decisions.

**collection/signals.md.** Voice-of-customer signals from communities, reviews, search trends, social platforms. Regulatory and technological context. Trend direction (tailwind or headwind for the hypothesis).

**adversarial/supporting.md.** A read of the collected data with the question: "Where in this evidence does the hypothesis find support?"

**adversarial/disconfirming.md.** An independent read of the same data with the question: "Where in this evidence does the hypothesis fail?"

**adversarial/symmetry_check.md.** A meta-pass that compares the two reads. If one is significantly thicker than the other, a hypothesis is proposed for why (collection bias, real asymmetry in the evidence, framing error).

**interviews/target_profile.md.** Who exactly to talk to: job titles, company types, seniority, where they congregate (communities, events, channels).

**interviews/questions.md.** Interview framework structured to surface past behavior, not future intent. Audited for leading questions and socially-desirable-answer traps.

**interviews/outreach_brief.md.** Drafts of outreach messages. Tailored to channel and persona.

**interviews/raw/.** Audio recordings and unedited transcripts. Git-ignored.

**interviews/synthesis.md.** Structured aggregation across the interview batch: per interview, what confirms / what challenges / what surprised. Across batch, recurring themes and contradictions.

### Stage 3 — Decision (zone 3, founder-led)

**3_decision/synthesis.md.** The full picture: hypothesis as framed, evidence collected, supporting vs disconfirming, interview findings, what changed in the founder's understanding.

**3_decision/decision_log.md.** The final call. Required fields:

- Decision: `build` | `pivot` | `kill` | `continue research`
- Confidence level: L1 | L2 | L3
- Premature flag: yes/no (mandatory if L1 + build)
- Evidence cited: specific references to engine outputs and interview synthesis
- **Triggers for reconsideration**: what would have to change for me to revisit this decision

The triggers field is the most important. It is the founder's defense against sunk-cost reasoning: a pre-committed list of conditions under which the decision will be revisited.

## Confidence levels in detail

**L1 — desk research only.** All engine work completed, no interviews. The system has not heard from a single real target user. Decisions at L1: `kill` is fully supported; `continue research` is the natural next step; `pivot` is supported if the desk evidence strongly contradicts the framing; `build` is allowed but flagged as premature, with the expectation that the user will move to L2 quickly.

**L2 — desk + 3 to 7 interviews.** Real signal from target users. Sufficient for `pivot` or `kill` with confidence. Sufficient for early `build` if the interview signal is strong and the desk evidence does not contradict it. Confidence is meaningful but not high.

**L3 — desk + 10+ interviews across subsegments + prototype reactions.** This approaches problem-solution fit as described in the Founder's Playbook. Decisions at L3 carry the most weight.

The system does not interpret confidence levels — the user does. The system only enforces that the level is explicit and that the consequences (e.g., the premature flag at L1+build) are applied.

## The retrospective loop

After each zone, the user writes a short retrospective in `retrospectives/{slug}/{zone}.md`. The format is intentionally minimal (3–4 questions). The point is not to produce a report; it is to capture what the user noticed about the pipeline while running it.

These retrospectives accumulate. Before starting a new hypothesis, Claude Code reads the last several retrospectives and proposes changes to templates, prompts, or workflow. The user approves, declines, or edits. Approved changes flow back into the templates.

This is how the system stays current with how the user actually works, instead of becoming a frozen artifact of how things were set up on day one.

## What the pipeline does not do

It does not replace customer interviews. It prepares for them, processes them, and gives them weight — but the interviews themselves remain conversations between humans.

It does not generate ideas. The hypothesis comes from the founder.

It does not declare validation. The decision is always the founder's, with the system enforcing structure and surfacing evidence the founder might otherwise rationalize away.

It does not automate outreach by default. That can be added as an optional module later (via Claude Cowork + Gmail/Calendar MCP). In V0, outreach is manual.

## When to deviate from this methodology

When a retrospective surfaces a durable pattern that this methodology fails to capture. Change the templates, document the change in the retrospective, commit it. The pipeline is a living artifact, not a contract.
