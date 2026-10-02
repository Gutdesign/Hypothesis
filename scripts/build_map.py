"""Build the static market map page from knowledge/companies/registry.csv.

  python scripts/build_map.py            writes site/index.html and site/registry.csv

The page is self-contained (data embedded as JSON), so it works from GitHub Pages or a local file.
The public CSV drops the internal `список_источника` column.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

STAGES = [
    ("S0", "Стратегия, участки, ТЭО"), ("S1", "Сделка и кредит"), ("S2", "Изыскания"),
    ("S3", "Проектирование"), ("S4", "Разрешения"), ("S5", "Тендеры и закупки"),
    ("S6", "Строительство"), ("S7", "Сдача объекта"), ("S8a", "Эксплуатация"),
    ("S8b", "Аренда и продажа"), ("S9", "Реновация и ретрофит"),
    ("X-DATA", "Данные и среда данных"), ("X-FIN", "Финансы и страхование"),
    ("X-COMP", "Комплаенс и нормы"), ("X-EDU", "Образование"), ("none", "Этап не определён"),
]
STAGE_CODES = {c for c, _ in STAGES}
COLS = [s for s in STAGES if s[0].startswith("S")]
LAYERS = {c: n for c, n in STAGES if c.startswith("X-")}
EU_OTHER = {"Германия", "Франция", "Португалия", "Швеция", "Австрия", "Швейцария", "Ирландия", "Люксембург",
            "Словения", "Италия", "Бельгия", "Дания", "Финляндия", "Норвегия"}
OUT = {"Индия", "Канада", "Япония", "Израиль", "ОАЭ"}


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
        if base == "S8":
            return "S8" + (sub or "a")
        return base
    return s if s in STAGE_CODES else "none"


def site_url(s):
    s = (s or "").strip()
    if not s or s == "н/д":
        return ""
    return s if s.startswith("http") else "https://" + s


def build_data(rows):
    out = []
    for r in rows:
        primary = norm_stage(r["этапы_основные"].replace(",", ";").split(";")[0])
        secondary = []
        for s in r["этапы_дополнительные"].replace(",", ";").split(";"):
            n = norm_stage(s)
            if n != "none" and n != primary and n not in secondary:
                secondary.append(n)
        kd = kind(r["тип_организации"])
        if kd in ("services", "builder") and primary == "none":
            primary = "none"
        out.append({
            "id": r["id"], "name": r["компания"], "site": site_url(r["сайт"]), "type": r["тип_организации"], "kind": kd,
            "primary": primary, "secondary": secondary, "role": r["роль_клиента"], "sub": r["подкатегория"],
            "markets": r["рынки_цель"], "city": r["штаб_город"], "country": r["штаб_страна"],
            "region": region(r["штаб_страна"]), "size": r["размер_сотрудников"], "round": r["последний_раунд"],
            "raised": r["привлечено"], "founded": r["год_основания"], "revenue": r["выручка"],
            "sources": [u for u in r["источники_данных"].split() if u.startswith("http")],
            "layer": r.get("слой", ""), "verified": r["данные_проверены"], "note": r["примечание"], "profile": r["профиль_по_списку"],
        })
    return out


TEMPLATE = (Path(__file__).resolve().parent / "map_template.html").read_text(encoding="utf-8")


def main():
    rows = registry.read(registry.CSV_PATH)
    data = build_data(rows)
    SITE.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE.replace("__DATA__", payload)
            .replace("__COLS__", json.dumps(COLS, ensure_ascii=False))
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
    print(f"wrote {SITE / 'index.html'} ({len(data)} companies, {len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
