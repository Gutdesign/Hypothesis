# Product Hypotheses

A repository for running structured product hypothesis validation with AI assistance.

This is not a tool. It's a workflow: each hypothesis lives in its own folder, follows the same lifecycle, and produces a paper trail of evidence and reasoning that holds up under external scrutiny.

## What this repo is for

Validating product ideas before building them. Each hypothesis goes through a pipeline that combines desk research, adversarial pressure-testing, and customer discovery into a structured decision artifact. The output of every hypothesis is one of: `build`, `pivot`, `kill`, or `continue research` — with the evidence trail attached.

## Three-zone architecture

Every hypothesis is divided into three zones. Your attention lives in zones 1 and 3. Zone 2 is the engine — automated as much as possible.

```
hypotheses/{slug}/
├── 1_frame/      ← FOUNDER zone (start)
│   Where the hypothesis is shaped, assumptions are surfaced,
│   and adversarial pressure is applied BEFORE research begins.
│
├── 2_engine/     ← MACHINE zone (middle)
│   Where Claude Code orchestrates research, collection,
│   adversarial dual-reads, and interview prep.
│   You can skip reading the raw outputs.
│
└── 3_decision/   ← FOUNDER zone (finish)
    Where the final synthesis is reviewed and the decision
    is recorded with explicit confidence level and reconsideration triggers.
```

## Lifecycle of one hypothesis

1. **Frame** — sharpen the idea, surface assumptions, record priors, run pre-research adversarial pass.
2. **Engine** — research plan → collection (competitors, market, signals) → adversarial dual-read → interview prep → interview synthesis (if interviews were conducted).
3. **Decision** — final synthesis, decision log with confidence level (L1/L2/L3) and triggers for reconsideration.

Between zones: write a short retrospective in `retrospectives/{slug}/{zone}.md`. These feed the cross-hypothesis self-improvement loop.

## Confidence levels

Decisions are tagged with confidence level. Levels above L1 require interviews.

- **L1** — desk research only. Decision `build` at L1 is flagged as premature.
- **L2** — desk + 3–7 interviews with target audience.
- **L3** — desk + 10+ interviews across subsegments + prototype reactions.

See `docs/methodology.md` for the full description.

## Starting a new hypothesis

```bash
cp -r templates/hypothesis hypotheses/{your-slug}
```

Then open `hypotheses/{your-slug}/1_frame/00_intake.md` and start writing.

For the retrospective folder of this hypothesis:

```bash
mkdir -p retrospectives/{your-slug}
cp templates/retrospective/*.md retrospectives/{your-slug}/
```

## Tools used

- **Claude Code** — orchestrates the pipeline, reads templates, drives the engine zone.
- **Parallel.ai** — structured deep research (competitive landscape, market structure).
- **Apify** — scraping (Reddit, App Store reviews, Product Hunt, HN, niche communities).
- **Anthropic API** — adversarial dual-reads, synthesis.

API keys go in `.env` (see `.env.example`). Never commit `.env`.

## Repo conventions

- One commit per zone completion at minimum.
- Commit messages: `{hypothesis-slug}: {zone} - {short description}`.
- Audio recordings of interviews go in `interviews/raw/` and are git-ignored.
- Hypothesis content can be written in any language. Templates and instructions are in English.

## See also

- `docs/methodology.md` — full description of the pipeline and philosophy.
- `CLAUDE.md` — instructions for Claude Code when working in this repo.
