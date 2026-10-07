"""Build the static market map page from knowledge/companies/registry.csv.

  python scripts/build_map.py            writes site/index.html and site/registry.csv

The page is self-contained (data embedded as JSON), has a Ru/Eng switch, and works from GitHub Pages or a local
file. English data comes from knowledge/companies/i18n/en_part*.tsv (per-id overrides) with
scripts/i18n_en.py as a fallback for short numeric strings. The public CSV drops the internal
`список_источника` column.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402
import i18n_en as T  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
I18N = ROOT / "knowledge" / "companies" / "i18n"
LABEL = "этапы — оценка по описанию"

STAGES = [
    ("S0", "Стратегия, участки, ТЭО"), ("S1", "Сделка и кредит"), ("S2", "Изыскания"),
    ("S3", "Проектирование"), ("S4", "Разрешения"), ("S5", "Подготовка: объёмы, сметы, тендеры, закупки"),
    ("S6", "Строительство"), ("S7", "Ввод, передача, исполнительная документация"), ("S8a", "Эксплуатация"),
    ("S8b", "Аренда и продажа"), ("S9", "Реновация и ретрофит"),
]
COLS = [[c, ru, T.STAGES_EN[c]] for c, ru in STAGES]
STAGE_CODES = {c for c, _ in STAGES}
EU_OTHER = {"Германия", "Франция", "Португалия", "Швеция", "Австрия", "Швейцария", "Ирландия", "Люксембург", "Лихтенштейн",
            "Словения", "Италия", "Бельгия", "Дания", "Финляндия", "Норвегия"}
OUT = {"Индия", "Канада", "Япония", "Израиль", "ОАЭ", "Австралия"}
NAME_EN = [("направление для органов власти", "government line"), ("бывш.", "formerly"), ("строительное направление", "construction unit"), ("дистрибьютор Tekla", "Tekla distributor")]


def region(country):
    if country == "США":
        return "США"
    if country in ("Великобритания", "Нидерланды", "Испания"):
        return country
    if country in EU_OTHER:
        return "Другая Европа"
    if country in OUT:
        return "Вне США и Европы"
    return "Не определён"


def kind(t):
    if "аппаратное" in t:
        return "hardware"
    if t.startswith("продукт"):
        return "product"
    if t.startswith("крупный"):
        return "vendor"
    if t.startswith("строитель"):
        return "builder"
    return "services"


def norm_stage(s):
    s = s.strip()
    if not s or s == "н/д":
        return "none"
    m = re.match(r"^(S\d)([abcd]?)$", s)
    if m:
        base, sub = m.groups()
        return "S8" + (sub or "a") if base == "S8" else base
    return s if s in STAGE_CODES else "none"


def site_url(s):
    s = (s or "").strip()
    if not s or s == "н/д":
        return ""
    return s if s.startswith("http") else "https://" + s


RATES = {"$": 1.0, "€": 1.1, "£": 1.3, "CHF": 1.2}  # rough, for ordering only
_NUM = r"(?:\d[\d \xa0]*\d|\d)"


def _n(s):
    return float(s.replace(" ", "").replace(" ", "").replace(",", "."))


def parse_emp(s):
    """First headcount number in the string (range -> midpoint); None if absent."""
    s = (s or "").strip()
    if not s or s.startswith("н/д") or s.startswith("не "):
        return None
    m = re.match(r"\D*(" + _NUM + r")(?:\s*[–-]\s*(" + _NUM + r"))?", s)
    if not m:
        return None
    a = _n(m.group(1))
    b = _n(m.group(2)) if m.group(2) else a
    return int(round((a + b) / 2))


def parse_rev(s):
    """First revenue amount in USD millions (rough rates); None if undisclosed."""
    s = (s or "").strip()
    if not s or s == "н/д" or (s.startswith("не раскрыта") and "оценка" not in s):
        return None
    m = re.search(r"(\$|€|£|CHF)\s?(" + _NUM + r"(?:,\d+)?)(?:\s*[–-]\s*(" + _NUM + r"(?:,\d+)?))?\s*(млн|млрд|тыс\.)", s)
    if not m:
        return None
    cur, a, b, unit = m.groups()
    a = _n(a)
    b = _n(b) if b else a
    mult = {"млн": 1.0, "млрд": 1000.0, "тыс.": 0.001}[unit]
    return round((a + b) / 2 * mult * RATES[cur], 1)


WEAK = re.compile(r"недостоверно|расчёт|слабая оценка|слабые оценки|предположение|не подтвержд|шум|возможно")
SOFT = re.compile(r"агрегатор|latka|оценк|заявлен|заявле|по сообщению|по описанию|по прессе|по данным|по сайту|по обзору|пресс[еы]\b")


def quality(field, text, verified):
    """A: company reporting / primary document; B: press release or news; C: aggregator estimate or company claim; D: calculation or doubtful."""
    if not text or text.startswith("н/д") or text.startswith("не раскрыта") and ";" not in text:
        return ""
    t = text.lower()
    if WEAK.search(t):
        return "D"
    if SOFT.search(t):
        return "C"
    if verified.startswith("да") and field in ("revenue", "size"):
        return "A"
    return "B"


def load_en():
    per_id, star = {}, {}
    for f in sorted(I18N.glob("en_part*.tsv")):
        for line in f.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                per_id[(parts[0], parts[1])] = parts[2]
            elif len(parts) == 4:
                star[(parts[1], parts[2])] = parts[3]
    return per_id, star


def en_block(r, per_id, star):
    cid = r["id"]
    e = {}
    for ru_key, key in [("последний_раунд", "round"), ("привлечено", "raised"), ("размер_сотрудников", "size"),
                        ("выручка", "revenue"), ("год_основания", "founded"), ("рынки_цель", "markets")]:
        v = r[ru_key]
        if not v or v == "н/д":
            e[key] = "n/a" if key != "markets" else ""
        elif (cid, key) in per_id:
            e[key] = per_id[(cid, key)]
        else:
            t = T.phrase(v)
            e[key] = t if not T.has_cyr(t) else v
    note = per_id.get((cid, "note"), "")
    if LABEL in r["примечание"]:
        note = (note + " " if note else "") + "Stage coding is an estimate from the description."
    e["note"] = note
    e["sub"] = star.get(("sub", r["подкатегория"]), r["подкатегория"] if not T.has_cyr(r["подкатегория"]) else "")
    e["verified"] = star.get(("verified", r["данные_проверены"]), r["данные_проверены"])
    e["role"] = "; ".join(T.ROLE_EN.get(x.strip(), x.strip()) for x in r["роль_клиента"].split(";") if x.strip())
    e["country"] = T.COUNTRY_EN.get(r["штаб_страна"], r["штаб_страна"])
    e["layer"] = "; ".join(T.LAYER_EN.get(x.strip(), x.strip()) for x in r["слой"].split(";") if x.strip())
    name = r["компания"]
    for a, b in NAME_EN:
        name = name.replace(a, b)
    e["name"] = name
    return e


def load_pains():
    """Rows of knowledge/pains.md (table with P-numbers) + English texts from i18n/pains_en.tsv."""
    en = {}
    f = I18N / "pains_en.tsv"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            p = line.split("\t")
            if len(p) >= 6:
                en[p[0]] = {"pain": p[1], "who": p[2], "why": p[3], "stype": p[4], "src": p[5]}
    out = []
    for line in (ROOT / "knowledge" / "pains.md").read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| P\d+ ", line):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 9:
            continue
        links = [{"t": m.group(1), "u": m.group(2)} for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)]+)\)", c[7])]
        out.append({"id": c[0], "pain": c[1], "stage": c[2], "who": c[3], "why": c[4], "grade": c[5], "stype": c[6],
                    "src": re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", c[7]), "links": links, "en": en.get(c[0], {})})
    return out


def build_data(rows):
    per_id, star = load_en()
    out = []
    for r in rows:
        primary = norm_stage(r["этапы_основные"].replace(",", ";").split(";")[0])
        secondary = []
        for s in r["этапы_дополнительные"].replace(",", ";").split(";"):
            n = norm_stage(s)
            if n != "none" and n != primary and n not in secondary:
                secondary.append(n)
        out.append({
            "id": r["id"], "name": r["компания"], "site": site_url(r["сайт"]), "type": r["тип_организации"],
            "kind": kind(r["тип_организации"]), "primary": primary, "secondary": secondary,
            "role": r["роль_клиента"], "sub": r["подкатегория"], "markets": r["рынки_цель"],
            "city": r["штаб_город"], "country": r["штаб_страна"], "region": region(r["штаб_страна"]),
            "size": r["размер_сотрудников"], "round": r["последний_раунд"], "raised": r["привлечено"],
            "founded": r["год_основания"], "revenue": r["выручка"],
            "sources": [u for u in r["источники_данных"].split() if u.startswith("http")],
            "layer": r.get("слой", ""), "global": r.get("глобальная", ""), "verified": r["данные_проверены"],
            "note": r["примечание"], "profile": r["профиль_по_списку"], "en": en_block(r, per_id, star),
            "mk": r.get("рынки_коды", ""), "mb": r.get("рынки_основание", ""), "group": r.get("группа", ""),
            "emp": parse_emp(r["размер_сотрудников"]),
            # weak estimates (grade D) are shown on the card but kept out of the revenue sort
            "rev": None if quality("revenue", r["выручка"], r["данные_проверены"]) == "D" else parse_rev(r["выручка"]),
            "q": {k: quality(k, r[f], r["данные_проверены"]) for k, f in
                  [("round", "последний_раунд"), ("raised", "привлечено"), ("size", "размер_сотрудников"),
                   ("revenue", "выручка"), ("founded", "год_основания"), ("markets", "рынки_цель")]},
        })
    return out


CHART_CAPTIONS = {
    "01_linkedin_startups_by_stage": ("Стартапы реестра по основному этапу", "Registry startups by main stage", True),
    "02_stage_coverage": ("Покрытие этапов: записи ПО по основному этапу и с учётом дополнительных", "Stage coverage: software records by main stage and including additional stages", False),
    "03_stage_market_startups": ("Этап × рынок: стартапы реестра", "Stage × market: registry startups", False),
    "04_stage_by_class": ("Кто держит этап: стартапы, крупные вендоры, сервисные организации", "Who holds a stage: startups, major vendors, service organisations", False),
    "05_new_rounds_by_stage": ("Стартапы с последним раундом в 2025–2026 годах, по этапам", "Startups with their latest round in 2025–2026, by stage", False),
    "06_compliance_by_stage": ("Комплаенс и проверка норм по этапам", "Compliance and code checking by stage", False),
    "07_last_rounds_money_by_stage": ("Сумма последних раундов 2025–2026 по этапам", "Total of the latest 2025–2026 rounds by stage", False),
}


def load_charts():
    """Copy the analytics charts next to the page and return their list for the Analytics tab."""
    src = ROOT / "landscapes" / "construction-tech" / "3_map" / "analytics" / "charts"
    dst = SITE / "charts"
    out = []
    if not src.exists():
        return out
    dst.mkdir(exist_ok=True)
    for old in dst.glob("*"):
        old.unlink()
    for png in sorted(src.glob("*.png")):
        stem = png.stem
        key = next((k for k in CHART_CAPTIONS if stem.startswith(k)), None)
        if not key:
            continue
        ru, en, tall = CHART_CAPTIONS[key]
        for ext in ("png", "svg"):
            f = src / f"{stem}.{ext}"
            if f.exists():
                (dst / f.name).write_bytes(f.read_bytes())
        out.append({"id": stem, "ru": ru, "en": en, "tall": tall})
    return out


def main():
    rows = registry.read(registry.CSV_PATH)
    data = build_data(rows)
    SITE.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    en_dicts = {"region": T.REGION_EN, "role": T.ROLE_EN, "layer": T.LAYER_EN}
    tpl = (Path(__file__).resolve().parent / "map_template.html").read_text(encoding="utf-8")
    charts = load_charts()
    html = (tpl.replace("__DATA__", payload)
            .replace("__CHARTS__", json.dumps(charts, ensure_ascii=False))
            .replace("__COLS__", json.dumps(COLS, ensure_ascii=False))
            .replace("__EN__", json.dumps(en_dicts, ensure_ascii=False))
            .replace("__PAINS__", json.dumps(load_pains(), ensure_ascii=False).replace("</", "<\\/"))
            .replace("__DATE__", date.today().strftime("%d.%m.%Y"))
            .replace("__COUNT__", str(len(data))))
    (SITE / "index.html").write_text(html, encoding="utf-8")
    cols = [c for c in registry.COLUMNS if c != "список_источника"]
    with open(SITE / "registry.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    left = [(d["id"], k) for d in data for k, v in d["en"].items() if T.has_cyr(v)]
    print(f"wrote {SITE / 'index.html'} ({len(data)} companies, {len(html) // 1024} KB); EN fields still in Russian: {len(left)}")
    for x in left[:40]:
        print("  ", x)


if __name__ == "__main__":
    main()
