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
    ("S3", "Проектирование"), ("S4", "Разрешения"), ("S5", "Тендеры и закупки"),
    ("S6", "Строительство"), ("S7", "Сдача объекта"), ("S8a", "Эксплуатация"),
    ("S8b", "Аренда и продажа"), ("S9", "Реновация и ретрофит"),
]
COLS = [[c, ru, T.STAGES_EN[c]] for c, ru in STAGES]
STAGE_CODES = {c for c, _ in STAGES}
EU_OTHER = {"Германия", "Франция", "Португалия", "Швеция", "Австрия", "Швейцария", "Ирландия", "Люксембург",
            "Словения", "Италия", "Бельгия", "Дания", "Финляндия", "Норвегия"}
OUT = {"Индия", "Канада", "Япония", "Израиль", "ОАЭ"}
NAME_EN = [("бывш.", "formerly"), ("строительное направление", "construction unit")]


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
        })
    return out


def main():
    rows = registry.read(registry.CSV_PATH)
    data = build_data(rows)
    SITE.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    en_dicts = {"region": T.REGION_EN, "role": T.ROLE_EN}
    tpl = (Path(__file__).resolve().parent / "map_template.html").read_text(encoding="utf-8")
    html = (tpl.replace("__DATA__", payload)
            .replace("__COLS__", json.dumps(COLS, ensure_ascii=False))
            .replace("__EN__", json.dumps(en_dicts, ensure_ascii=False))
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
