"""Follow-up Parallel prompts: what the five `pro` fact-check reports left unconfirmed or disputed.

Reads landscapes/construction-tech/2_collection/raw/parallel-factcheck-*-pro.md and the batch prompts, and writes
parallel_prompts/factcheck2_*.txt:
  EU_n  - non-US companies with 4+ unconfirmed fields: official company registries and filed accounts
  US_1  - US companies with 4+ unconfirmed fields: SEC Form D, state registries, investor and company releases
  disputes - rows the reports contradicted or corrected from weak page types (accelerator profile, own marketing page)
Nothing is sent; sending is a separate founder-approved step.
"""
import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

BASE = ROOT / "landscapes" / "construction-tech" / "2_collection"
PRM = {"US-1-pro": "US_1", "US-2-pro": "US_2", "EU-1-pro": "EU_1", "EU-2-pro": "EU_2", "EU-3-pro": "EU_3"}
CAP = 22

COMMON = """Fact-check the following construction-technology companies a second time. A first pass checked them against company websites, press releases and investor announcements and could not confirm many fields. For each company I give the values held in a registry; they came mostly from aggregators and are unverified.

Do NOT use aggregator or profile-scraping sites (Tracxn, Latka, ZoomInfo, Growjo, Datanyze, PitchBook-type or LinkedIn-type profile pages), forums or discussion boards. Do not infer values; if no allowed source gives a value, say so.

"""

EU_BODY = """Use OFFICIAL COMPANY REGISTRIES and FILED ACCOUNTS first: Companies House (UK), KvK (Netherlands), Registro Mercantil and the Spanish official gazette BORME (Spain), Handelsregister / Unternehmensregister (Germany), Brønnøysund Register Centre (Norway), PRH (Finland), RCS Luxembourg, the Irish CRO, and the equivalent registry for any other country; then the company's own legal notice or imprint page, its annual report, and press releases. For each company find: the legal entity name and registration number, the incorporation (registration) date, the registered office address, and, where accounts are filed, the latest reported turnover and average number of employees with the financial year. Tell me if the registry shows a different legal entity from the brand name.

Output one block per company, in the order given, as a markdown table with the columns: field | registry value | verified value | status | primary source URL | source date. The status is one of: confirmed, corrected, unconfirmed (no primary source found), contradicted. Fields: legal entity and registration number, incorporation date, registered office, headcount, revenue. Keep the field names exactly as listed and keep one row per field. Add a one-line note per company on anything material (different legal entity, dissolved, acquired, renamed). Use inline citations. Do not reproduce long passages of source text.

Companies:
"""

US_BODY = """Use SEC EDGAR Form D filings (amount sold, date of first sale, related persons), state business registries (for example Delaware, California, New York, Texas), the company's own newsroom, and investor announcements. For each company find: the date and amount of the latest funding round and the total amount raised if a primary source states it, and the legal entity name, state and date of incorporation. A Form D shows the amount sold so far in an offering; say if it differs from the announced round. Tell me if the filings show a different legal entity from the brand name.

Output one block per company, in the order given, as a markdown table with the columns: field | registry value | verified value | status | primary source URL | source date. The status is one of: confirmed, corrected, unconfirmed (no primary source found), contradicted. Fields: latest funding round, total raised, legal entity, incorporation date. Keep the field names exactly as listed and keep one row per field. Add a one-line note per company on anything material. Use inline citations. Do not reproduce long passages of source text.

Companies:
"""

DISPUTE_BODY = """Resolve the following disputed facts with primary sources only (company registries and filings, the company's own site and legal notices, press releases of the company or its investors). Each item says what a registry holds and what a first-pass check found, and where the first pass relied on a weak page type (an accelerator profile or a company's own marketing page). For each item say which value is right, with the registry or filing that shows it, or say that no primary source decides it.

Output one block per item as a markdown table with the columns: question | registry value | first-pass value | verified value | status | primary source URL | source date. Use inline citations.

Items:
"""


def parse():
    reg = {r["компания"]: r for r in registry.read(registry.CSV_PATH)}
    data = {c["name"]: c for c in bm.build_data(registry.read(registry.CSV_PATH))}
    out = []
    for rep, pn in PRM.items():
        t = (BASE / "raw" / f"parallel-factcheck-{rep}.md").read_text(encoding="utf-8")
        names = [re.sub(r"^\d+\. ", "", l).split(" | ")[0]
                 for l in (BASE / "parallel_prompts" / f"factcheck_{pn}_pro.txt").read_text(encoding="utf-8").split("Companies:\n")[1].strip().split("\n")]
        parts = re.split(r"\n(?=#{2,3} \d+\.)", t)
        blocks = [p for p in parts if re.match(r"#{2,3} \d+\.", p) and re.search(r"\| (confirmed|corrected|contradicted|unconfirmed)", p)]
        if len(blocks) != len(names):
            print("MISMATCH", rep, len(blocks), len(names))
            continue
        for nm, b in zip(names, blocks):
            st = collections.Counter(re.findall(r"\| (confirmed|corrected|contradicted|unconfirmed)[^|]*\|", b))
            out.append((nm, st, b))
    return reg, data, out


def line(i, n, d):
    e = d["en"]
    return (f"{i}. {e['name']} | site: {d['site'] or 'n/a'} | registry HQ: {e['country'] or 'n/a'}{', ' + d['city'] if d['city'] and d['city'] != 'н/д' else ''}"
            f" | registry founded: {e['founded'] if e['founded'] not in ('', 'n/a') else 'n/a'} | registry headcount: {e['size'] if e['size'] not in ('', 'n/a') else 'n/a'}"
            f" | registry latest round: {e['round'] if e['round'] not in ('', 'n/a') else 'n/a'} | registry total raised: {e['raised'] if e['raised'] not in ('', 'n/a') else 'n/a'}"
            f" | registry revenue: {e['revenue'] if e['revenue'] not in ('', 'n/a') else 'n/a'}")


def main():
    reg, data, rows = parse()
    eu, us = [], []
    for nm, st, b in rows:
        r = reg.get(nm)
        if not r:
            continue
        if st.get("unconfirmed", 0) >= 4:
            (us if r["штаб_страна"] == "США" else eu).append(nm)
    out = BASE / "parallel_prompts"
    for old in out.glob("factcheck2_*.txt"):
        old.unlink()
    made = []
    parts = -(-len(eu) // CAP)
    size = -(-len(eu) // parts) if parts else 0
    for k in range(parts):
        chunk = eu[k * size:(k + 1) * size]
        body = COMMON + EU_BODY + "\n".join(line(i + 1, n, data[n]) for i, n in enumerate(chunk)) + "\n"
        f = out / f"factcheck2_EU_{k + 1}.txt"
        f.write_text(body, encoding="utf-8")
        made.append((f.name, len(chunk), len(body)))
    if us:
        body = COMMON + US_BODY + "\n".join(line(i + 1, n, data[n]) for i, n in enumerate(us)) + "\n"
        f = out / "factcheck2_US_1.txt"
        f.write_text(body, encoding="utf-8")
        made.append((f.name, len(us), len(body)))
    items = [
        ("1001 AI: registry HQ San Francisco, USA; the first pass says the Series A release describes a GCC- and London-based company. Where is the legal entity registered, and where is it headquartered?", "San Francisco, USA", "GCC and London (press release)"),
        ("ArchiLabs: registry HQ Houston, USA; the first pass says Y Combinator lists San Francisco. Where is the legal entity registered, and where is it headquartered?", "Houston, USA", "San Francisco (accelerator profile)"),
        ("Helonic: registry HQ San Francisco, USA; the first pass says Y Combinator lists a New York team and Articulate AI as the legal entity. Which legal entity operates the product and where is it registered?", "San Francisco, USA", "New York team; legal entity Articulate AI (accelerator profile)"),
        ("Permitify: registry HQ San Francisco and founded 2024; the first pass says an accelerator profile lists Salt Lake City, Utah and 2025. What does the state registry show for the legal entity (state, incorporation date, address)?", "San Francisco; 2024", "Salt Lake City; 2025 (accelerator profile)"),
        ("Keyway: registry says founded 2020; the first pass says the company's own page says 2021. What does the state registry show as the incorporation date?", "2020", "2021 (company page)"),
        ("Asite: the registry says it raised no outside money (self-funded, per an aggregator); the first pass found a 2024 senior secured credit facility from Ashgrove Capital. Does any primary source show equity investors or ownership?", "no outside funding (self-funded)", "2024 credit facility; equity history not established"),
        ("Fresco: the registry website is fresco-ai.com, but the company-authored pages found are at fresco.build. Which domain is the operating company's and is it the same entity as the YC-listed Fresco (Division 8 estimating)?", "fresco-ai.com", "fresco.build"),
        ("Revizto: the registry founding year is 2008; the first pass reports 2012 from company material. Which is right according to the Swiss commercial registry?", "2008", "2012"),
        ("ZuTec: the registry founding year is 1999; the first pass reports 1998 from company material. Which is right according to Companies House or an official registry?", "1999", "1998"),
        ("Sablono: the registry lists High-Tech Gruenderfonds, Hasso Plattner Ventures and Nemetschek Allplan for its May 2021 EUR 5.3M Series A and names no lead; the first pass says the company names Bachmaier Invest as lead. Who led the round according to a primary source?", "no lead named (HTGF, Hasso Plattner Ventures, Nemetschek Allplan)", "Bachmaier Invest (company)"),
        ("CASAFARI: the registry holds debt financing of USD 5.3M in 2024 and USD 30.3M raised over 4 rounds; the first pass found a USD 20M extended Series A in the company's own release and a separate USD 120M property mandate. What is the latest equity round, and is the USD 120M a mandate rather than funds raised by the company?", "debt USD 5.3M (2024); total USD 30.3M over 4 rounds", "USD 20M extended Series A; USD 120M mandate"),
        ("Entrata: confirm from an SEC Form D or the issuer's release whether the USD 200M Blackstone investment of May 2025 was a minority equity investment or a numbered preferred round (the registry says Series D), and the date.", "Series D, USD 200M", "minority investment (company release)"),
    ]
    body = DISPUTE_BODY + "\n".join(f"{i + 1}. {q} | registry value: {a} | first-pass value: {b}" for i, (q, a, b) in enumerate(items)) + "\n"
    f = out / "factcheck2_disputes.txt"
    f.write_text(COMMON + body, encoding="utf-8")
    made.append((f.name, len(items), len(COMMON + body)))
    for m in made:
        print(m)


if __name__ == "__main__":
    main()
