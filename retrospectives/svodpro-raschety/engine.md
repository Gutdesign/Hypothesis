# Retrospective — Engine Zone

> **When to fill:** after the engine zone is complete (collection, adversarial reads, interview prep + synthesis).
> **Time budget:** 5–10 minutes.

---

**Hypothesis slug:** svodpro-raschety
**Date:** 2026-07-30
**Mode used:** lean
**Total budget spent (approximate):** ~$30-60 (2 Parallel.ai queries, processor "pro", ~$15-30 each per the skill's own cost table — API doesn't return exact spend synchronously, not verified against actual Parallel billing)

---

## What worked in the engine stage

- Both Parallel queries (competitive landscape, marketing/VoC) came back with specific, citation-backed findings, not generic filler — exact URLs, exact norm version numbers (ГОСТ Р 52941-2008 vs ГОСТ Р 55964-2014), a direct forum quote. This is the opposite of the "generic adversarial output is worse than none" failure mode CLAUDE.md warns about for 04_devils_advocate — same principle applies here and the queries cleared that bar.
- Splitting the 4-calculator hypothesis into per-topic findings (rather than one blended "market" verdict) turned out to be the single most useful structural choice — it surfaced that the 4 sub-bets have wildly different competitive densities (эвакуация empty, условные блюда saturated), which a single aggregate read would have averaged into mush.
- The forum-search framing in the marketing prompt ("look for evidence in professional forums... of complaints or discussion") produced one genuinely independent confirmation of the founder's personal pain story (dwg.ru recalculation case) — this is exactly the kind of single-source-risk mitigation the frame zone flagged as needed.

## What didn't work

- Discovered mid-run that `skills/parallel-research.skill` was non-functional in this environment: written for a Claude Cloud sandbox (`/home/claude/...` paths, git push to an unrelated external repo `Gutdesign/Discovery`). Had to reverse-engineer the zip, rewrite both scripts, and repackage before it could be used at all. This wasn't an engine-zone research problem, but it ate real time before any research happened.
- `poll_and_save.sh`'s first version silently failed on both real requests — it interpolated the raw curl JSON response into a Python heredoc via bash variable substitution (`'''${VAR}'''`), which breaks on multi-KB responses containing unescaped control characters. Both job files ended up marked "failed" even though Parallel had actually completed and billed the work; recovered the content from `/tmp` dumps instead of losing the spend. Fixed by writing curl output straight to a file and parsing with `json.loads(..., strict=False)`.
- Quantitative search-volume data (Wordstat/Keys.so) was never available in this run — Parallel's research answers "does a market/competitor exist" well but doesn't substitute for actual keyword-volume tools. Q1 (search demand) stayed only qualitatively answered (inferred from "competitors already exist for 3 of 4 topics").

## Adversarial read assessment

The dual-read genuinely changed the picture, it didn't just produce symmetric-looking padding. Volume came out roughly 1:1 as expected for a reasonably rich corpus, but the disconfirming read had access to more independently-verifiable, specific facts (KONE TrafCal already in active use, vaco-eng.ru's 100+ templates, 3 condition-calc competitors) than the supporting read's strongest point (one forum anecdote). The symmetry_check didn't have to strain to find asymmetry — it fell out of the four calculators naturally having different competitive realities, which is a good sign the framing wasn't rigged either direction.

## Cost vs value

Two "pro" queries were worth it — the KONE TrafCal find alone (a real, currently-used competitor the founder didn't know about) justified the spend, since it directly changes the risk profile of the one calculator with founder's personal domain expertise. Would not spend more without first getting real Wordstat/Keys.so numbers — that's the one gap two more Parallel queries wouldn't have fixed, since Parallel is a research/reasoning layer, not a keyword-data source.

## What I'd change in the templates

- `research_plan.md`'s "Estimated cost" column assumes cost-per-query is known upfront; in practice Parallel's `/result` endpoint doesn't return the actual billed amount, only the processor tier. Template should note "estimated, verify against Parallel billing dashboard" instead of implying the number is precise.
- Add a line item in `research_plan.md`'s Out of scope / re-run conditions for "tooling had to be fixed before use" — this run's biggest time cost isn't reflected anywhere in the template structure, only in this retro.

## New sources or actors discovered

- KONE TrafCal (vendor-provided elevator calculation tool, confirmed in active use via dwg.ru forum) — not previously known to the founder, worth checking again on future lift-related hypotheses.
- vaco-eng.ru (pool water treatment calculator, 100+ templates) and dwg.ru / forum.abok.ru as reliable forum sources for this professional audience — worth reusing directly (not through Parallel) for cheaper follow-up signal checks.
- НОПРИЗ specialist registry (`reestr.nopriz.ru`) flagged by Parallel as a potentially real (not estimated) source for architect/technologist headcount — not queried directly this run, worth trying next time instead of relying on expert-estimate figures.

## Notes for the decision zone

- The founder's own decision to launch all 4 calculators simultaneously (rather than piloting one) is now in tension with real evidence: 2 of the 4 topics (условные блюда, водоподготовка) show saturated/already-served niches. Decision zone should surface this conflict explicitly rather than smooth it into an average verdict.
- ВТ is a genuine toss-up (real gap on norm version vs a real, already-used vendor competitor) — not a clean "yes" or "no," and the synthesis should say so rather than force a single confidence direction.
- Interviews haven't happened yet (outreach is founder-led, per `interviews/outreach_brief.md`) — any decision made before that is capped at L1 and a `build` call would need the premature flag per CLAUDE.md.
