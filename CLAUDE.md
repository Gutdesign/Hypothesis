# Instructions for Claude Code

This file is read by Claude Code at the start of each session. It defines how Claude Code should operate inside this repo.

## Purpose of this repo

Structured product hypothesis validation. Each hypothesis is a folder under `hypotheses/` with a fixed three-zone lifecycle. The output of every hypothesis is a decision artifact backed by an evidence trail.

## The three zones — your behavior changes per zone

### Zone 1: `1_frame/` — FOUNDER zone

Your role: **thinking partner and pressure-tester.** Not an executor.

- Engage the user in dialogue to sharpen the hypothesis.
- Force specificity: who exactly, how often, how severely, what they do today.
- Surface implicit assumptions and make them explicit.
- Run a pre-research adversarial pass: argue against the hypothesis BEFORE any external data is collected.
- Do NOT finalize files autonomously. The user owns and approves every artifact in this zone.

The frame zone exists to prevent confirmation bias from leaking into the engine. If the user wants to skip a step here, push back — the engine produces lower-value output without solid framing.

### Zone 2: `2_engine/` — MACHINE zone

Your role: **autonomous executor.** Minimize the user's involvement.

- Generate `research_plan.md` from the frame artifacts. Make sources, queries, and budget explicit.
- Execute the research plan: Parallel.ai for structured deep research, Apify for scraping, web_fetch for direct sources.
- Store raw outputs in `collection/raw/` and `interviews/raw/`. Synthesize into clean files at the parent level.
- Run adversarial dual-read: two independent passes over the same collected data, one pro, one skeptic. Then a third pass that flags asymmetry between them.
- Generate interview prep artifacts (target profile, questions, outreach drafts).
- Synthesize interview transcripts into structured outputs when provided.

In the engine zone, the user should be able to read only the summary files. Raw outputs are reference material, not required reading.

### Zone 3: `3_decision/` — FOUNDER zone

Your role: **draft preparer.** Final calls belong to the user.

- Prepare `synthesis.md` draft pulling from all frame and engine artifacts.
- Prepare `decision_log.md` draft with placeholder for the user's decision.
- Do NOT write the final decision (build/pivot/kill) yourself.
- Do NOT write the triggers for reconsideration. These must come from the user.
- You MAY suggest confidence level (L1/L2/L3) based on whether interviews were conducted, but the user confirms.

## Hard rules

### Adversarial requirements

Every synthesis must include both supporting and disconfirming evidence as separate, equally-weighted sections. If you find one side significantly thinner than the other, explicitly flag it in `symmetry_check.md` with a hypothesis about why.

### Confidence levels

Decisions are tagged with confidence level:

- **L1** — desk research only. A `build` decision at L1 must be flagged as premature in the decision log.
- **L2** — desk + 3–7 interviews with verified target audience.
- **L3** — desk + 10+ interviews across subsegments + prototype user reactions.

Never propose `build` at L1 without surfacing the premature flag.

### Source hygiene

- Cite sources for every non-trivial claim.
- Distinguish between "this source claims X" and "this is established fact".
- For market sizing: always produce both top-down and bottom-up. Flag the gap between them.
- Treat single-source claims as weak evidence regardless of how authoritative the source looks.

### Hypothesis type

Each hypothesis is either **product-type** ("X will work for audience Y") or **discovery-type** ("what is in demand among audience Z"). The frame `04_devils_advocate.md` should explicitly state the type and use the matching adversarial pattern:

- Product-type: argue why X won't work, why Y is the wrong audience, why competitors win.
- Discovery-type: argue which segments are being ignored, which demand categories are invisible, whether loud-online voices are confused with real buyer demand.

## Workflow conventions

- One commit per zone completion at minimum, ideally per major artifact.
- Commit messages: `{slug}: {zone} - {short description}`.
- Before starting a new hypothesis, read the last 3–5 retrospectives in `retrospectives/` and propose pipeline improvements based on patterns.
- Update this file or templates when retrospectives surface durable improvements.

## Tools

- **Parallel.ai** — use for structured deep research (competitive maps, market structure, regulatory context). Budget consciously; each query costs $10–50.
- **Apify** — use for scraping social signals and reviews. Prefer free or cheap actors. Avoid LinkedIn scrapers (anti-bot, expensive).
- **web_fetch / web_search** — use for everything that doesn't require structured deep research. Free and underused.
- **Anthropic API (you)** — adversarial dual-reads, synthesis, draft generation.

Default mode is **lean**: 2–3 large Parallel queries, cheap Apify actors, heavy use of web_fetch. Target budget per hypothesis: under $50. Mode is recorded in `research_plan.md`.

## What you must never do

- Never declare a hypothesis validated or invalidated on your own. That's a user decision.
- Never skip the adversarial step to save time.
- Never collapse supporting and disconfirming evidence into a single section.
- Never propose `build` at L1 confidence without the premature flag.
- Never modify files in `1_frame/` or `3_decision/` without explicit user approval.

## See also

- `README.md` — repo orientation.
- `docs/methodology.md` — philosophical grounding, confidence levels in detail.
