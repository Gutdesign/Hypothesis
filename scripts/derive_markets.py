"""Fill `рынки_коды` / `рынки_основание` in the registry from `рынки_цель`, `глобальная` and the headquarters.

  python scripts/derive_markets.py        (re-run after editing markets text; hand-edited rows with основание 'вручную' are kept)

Codes: US, UK, ES, NL, EU (other Europe), OTHER (outside USA and Europe).
Basis: 'текст' (named in the markets text), 'широкий охват' (text says dozens of countries / continents),
'глобальная' (flagged global), 'штаб' (no market information: headquarters used as a placeholder, unconfirmed),
'вручную' (set by hand).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

ALL = ["US", "UK", "ES", "NL", "EU", "OTHER"]
KEYS = {
    "US": ["сша", "северной америке", "new york", "san francisco"],
    "UK": ["великобритани", "london"],
    "ES": ["испани", "испаноязычн"],
    "NL": ["нидерланд"],
    "EU": ["европ", "германи", "франци", "швеци", "швейцари", "австри", "дани", "бельги", "ирланд", "люксембург",
           "португали", "словени", "финлянд", "норвег", "польш", "итали", "стран ес", "в ес", "eu "],
    "OTHER": ["япони", "индия", "израил", "оаэ", "персидск", "gcc", "саудовск", "австрали", "китай", "азиатско",
              "гонконг", "канад", "ближнем востоке", "азии", "африк", "океани", "tel aviv", "singapore", "singapore"],
}
HQ = {"США": "US", "Великобритания": "UK", "Нидерланды": "NL", "Испания": "ES", "Индия": "OTHER", "Канада": "OTHER",
      "Япония": "OTHER", "Израиль": "OTHER", "ОАЭ": "OTHER"}
EU_HQ = {"Австрия", "Германия", "Дания", "Ирландия", "Люксембург", "Португалия", "Словения", "Франция", "Швейцария",
         "Швеция", "Лихтенштейн", "Бельгия", "Италия"}
BROAD = re.compile(r"(\d[\d ]*)\+?\s*стран|континент|по всему миру")
# hand-set rows (source: the registry note of that row)
MANUAL = {
    "buildots": ("US; EU", "вручную: в примечании — работает в США и Европе"),
    "idom": ("US; UK; ES; NL; EU; OTHER", "вручную: офисы в Америке, Азии, Африке, Европе и на Ближнем Востоке"),
}


def derive(r):
    if r["id"] in MANUAL:
        return MANUAL[r["id"]]
    t = (r["рынки_цель"] or "").lower()
    codes = [c for c, ks in KEYS.items() if any(k in t for k in ks)]
    m = BROAD.search(t)
    broad = bool(m and (not m.group(1) or int(re.sub(r"\D", "", m.group(1)) or 0) >= 50 or "континент" in t or "по всему миру" in t))
    if r.get("глобальная") == "да":
        return "; ".join(ALL), "глобальная"
    if broad:
        return "; ".join(ALL), "широкий охват"
    if codes:
        return "; ".join(codes), "текст"
    c = HQ.get(r["штаб_страна"]) or ("EU" if r["штаб_страна"] in EU_HQ else "")
    return (c, "штаб") if c else ("", "нет данных")


def main():
    rows = registry.read(registry.CSV_PATH)
    stat = {}
    for r in rows:
        if r.get("рынки_основание", "").startswith("вручную") and r["id"] not in MANUAL:
            continue
        codes, basis = derive(r)
        r["рынки_коды"], r["рынки_основание"] = codes, basis
        stat[basis.split(":")[0]] = stat.get(basis.split(":")[0], 0) + 1
    registry.write(rows)
    print(stat)


if __name__ == "__main__":
    main()
