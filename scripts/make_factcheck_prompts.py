"""Build the Parallel fact-check prompts from the registry (software tab, aggregator-sourced rows).

Writes landscapes/construction-tech/2_collection/parallel_prompts/factcheck_*.txt. Nothing is sent anywhere:
sending is a separate, founder-approved step (see research_plan.md, 'Внешние инструменты').
Only public company facts from the registry go into the prompts.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

OUT = ROOT / "landscapes" / "construction-tech" / "2_collection" / "parallel_prompts"
CAP = 31  # companies per task; keeps a prompt near 12K characters

HEADER = """Fact-check the following list of construction-technology companies. For each company I give the values currently held in a registry. These values came mostly from aggregators (Crunchbase-type sites, Tracxn, Latka, LinkedIn-type profiles) and press, and are unverified.

For every company, check each given field against PRIMARY sources only: the company's own website and newsroom, its press releases, regulatory filings and annual reports, official company registries, investor announcements, and tender or government notices. Aggregators and AI-generated profiles are NOT primary sources. Do not infer values; if no primary source exists, say so.

Also report for each company: whether it was acquired, merged, rebranded, renamed, shut down or taken private (give the date and the acquirer), whether the product is still sold, and whether the company is a software vendor at all (as opposed to a consultancy, builder or hardware maker).

Output one block per company, in the order given, as a markdown table with the columns: field | registry value | verified value | status | primary source URL | source date. The status is one of: confirmed, corrected, unconfirmed (no primary source found), contradicted. Fields: headquarters, founding year, headcount, latest funding round, total raised, revenue, ownership, what the product does. Skip a field only if the registry value is n/a, and then add a verified value if you find one. Add a one-line note per company on anything material (acquisition, rebrand, closure, different legal entity). Finish with a short list of the companies where the registry is wrong in a way that changes how the company should be described. Use inline citations. Do not reproduce long passages of source text.

Companies:
"""


def line(i, c):
    e = c["en"]
    def v(x):
        return x if x and x != "n/a" else "n/a"
    return (f"{i}. {e['name']} | site: {c['site'] or 'n/a'} | HQ: {e['country'] or 'n/a'}{', ' + c['city'] if c['city'] and c['city'] != 'н/д' else ''}"
            f" | founded: {v(e['founded'])} | headcount: {v(e['size'])} | latest round: {v(e['round'])} | total raised: {v(e['raised'])}"
            f" | revenue: {v(e['revenue'])} | does: {e['sub'] or 'n/a'}")


def main():
    rows = registry.read(registry.CSV_PATH)
    data = {c["id"]: c for c in bm.build_data(rows)}
    pick = [r for r in rows
            if (r["тип_организации"].startswith("продукт") or r["тип_организации"].startswith("крупный"))
            and ("агрегатор" in r["данные_проверены"] or "отчёт Parallel" in r["данные_проверены"])]
    def bucket(r):
        k = r["штаб_страна"]
        if k == "США":
            return "US"
        if k in ("Великобритания", "Ирландия"):
            return "UKIE"
        if k in ("Нидерланды", "Испания"):
            return "NLES"
        return "REST"
    groups = {}
    for r in pick:
        groups.setdefault(bucket(r), []).append(r)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("factcheck_*.txt"):
        old.unlink()
    made = []
    plan = [("US", groups.get("US", [])),
            ("EU", groups.get("UKIE", []) + groups.get("NLES", []) + groups.get("REST", []))]
    for key, items in plan:
        items = sorted(items, key=lambda r: (bucket(r), r["компания"].lower())) if key == "EU" else sorted(items, key=lambda r: r["компания"].lower())
        parts = -(-len(items) // CAP)
        size = -(-len(items) // parts)
        for n in range(parts):
            batch = items[n * size:(n + 1) * size]
            body = HEADER + "\n".join(line(i + 1, data[r["id"]]) for i, r in enumerate(batch)) + "\n"
            f = OUT / f"factcheck_{key}_{n + 1}.txt"
            f.write_text(body, encoding="utf-8")
            made.append((f.name, len(batch), len(body), [r["компания"] for r in batch]))
    for name, cnt, size, names in made:
        print(name, cnt, "companies,", size, "chars")
    print("total", sum(m[1] for m in made))


if __name__ == "__main__":
    main()
