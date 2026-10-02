"""Company registry helper.

  python scripts/registry.py build            regenerate knowledge/companies/registry.md
  python scripts/registry.py merge FILE.csv   update rows of registry.csv by `id` (empty cells in FILE are ignored; new ids are appended)
  python scripts/registry.py stats            stage coverage and field fill-rate

CSV format: ';'-delimited, UTF-8 with BOM (opens in Russian-locale Excel).
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "knowledge" / "companies" / "registry.csv"
MD_PATH = ROOT / "knowledge" / "companies" / "registry.md"

COLUMNS = [
    "id", "компания", "офисы_и_дубли", "сайт", "список_источника", "тип_организации",
    "профиль_по_списку", "этапы_основные", "этапы_дополнительные", "слой", "роль_клиента",
    "подкатегория", "рынки_цель", "рынки_коды", "рынки_основание", "глобальная", "штаб_город", "штаб_страна", "размер_сотрудников",
    "последний_раунд", "привлечено", "год_основания", "выручка",
    "источники_данных", "данные_проверены", "примечание",
]
MD_COLUMNS = [
    "компания", "сайт", "тип_организации", "этапы_основные", "этапы_дополнительные",
    "роль_клиента", "рынки_цель", "штаб_город", "штаб_страна", "размер_сотрудников",
    "последний_раунд", "привлечено", "год_основания", "выручка", "данные_проверены",
]
FILL_COLUMNS = ["сайт", "рынки_цель", "штаб_город", "размер_сотрудников", "последний_раунд",
                "привлечено", "год_основания", "выручка"]
EMPTY = {"", "н/д"}


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write(rows):
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def build():
    rows = read(CSV_PATH)
    esc = lambda s: (s or "").replace("|", "/").replace("\n", " ")
    lines = [
        "# Реестр компаний",
        "",
        "> Генерируется из `registry.csv` командой `python scripts/registry.py build`. Не править вручную.",
        f"> Строк: {len(rows)}. Коды этапов — в `../value_chain.md`. Подробные поля (профиль, источники, примечания) — в CSV.",
        "",
        "| " + " | ".join(MD_COLUMNS) + " |",
        "|" + "|".join(["---"] * len(MD_COLUMNS)) + "|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(esc(r.get(c)) for c in MD_COLUMNS) + " |")
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {MD_PATH} ({len(rows)} rows)")


def merge(path):
    rows = read(CSV_PATH)
    by_id = {r["id"]: r for r in rows}
    upd = read(path)
    changed = added = 0
    for u in upd:
        rid = u.get("id", "").strip()
        if not rid:
            continue
        if rid in by_id:
            for c, v in u.items():
                v = (v or "").strip()
                if c == "id" or c not in COLUMNS or not v:
                    continue
                cur = by_id[rid].get(c, "")
                if c in ("примечание", "источники_данных") and cur and v not in cur:
                    by_id[rid][c] = cur + (" | " if c == "примечание" else " ") + v
                else:
                    by_id[rid][c] = v
            changed += 1
        else:
            by_id[rid] = {c: u.get(c, "").strip() for c in COLUMNS}
            rows.append(by_id[rid])
            added += 1
    write(rows)
    print(f"updated {changed}, added {added}, total {len(rows)}")


def stats():
    rows = read(CSV_PATH)
    print(f"rows: {len(rows)}")
    primary = Counter()
    for r in rows:
        for s in (r["этапы_основные"] or "н/д").replace(",", ";").split(";"):
            primary[s.strip()] += 1
    print("primary stage counts:", dict(sorted(primary.items())))
    print("type counts:", dict(Counter(r["тип_организации"] for r in rows)))
    print("verified:", dict(Counter(r["данные_проверены"] for r in rows)))
    for c in FILL_COLUMNS:
        filled = sum(1 for r in rows if r.get(c, "").strip() not in EMPTY)
        print(f"  filled {c}: {filled}/{len(rows)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build()
    elif cmd == "merge" and len(sys.argv) > 2:
        merge(sys.argv[2])
    elif cmd == "stats":
        stats()
    else:
        print(__doc__)
