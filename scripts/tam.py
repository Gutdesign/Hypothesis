"""TAM by country x stage: bottom-up model (see knowledge/markets/tam_method.md).

Reads knowledge/markets/tam_inputs.csv and raw statistics in knowledge/markets/tam_data/,
writes knowledge/markets/tam_results.md. Run: python scripts/tam.py
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MK = ROOT / "knowledge" / "markets"
DATA = MK / "tam_data"
sys.path.insert(0, str(Path(__file__).resolve().parent))

COUNTRIES = ["US", "UK", "ES", "NL"]
STAGES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8a", "S8b", "S9"]
CONSTRUCTION = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S9"]
REAL_ESTATE = ["S8a", "S8b"]
TOP_DOWN_STAGES = ["S2", "S3", "S5", "S6", "S7", "S9"]  # what analysts call "construction software"
LEVELS = ["low", "base", "high"]
YEAR_EU = "2023"

# ---------- inputs ----------
P = {}      # (key, country) -> {low, base, high, grade}
for r in csv.DictReader(open(MK / "tam_inputs.csv", encoding="utf-8"), delimiter=";"):
    P[(r["ключ"], r["страна"])] = {
        "low": float(r["low"]), "base": float(r["base"]), "high": float(r["high"]), "grade": r["оценка"],
        "src": r["источник"],
    }


def par(key, c, lvl):
    return (P.get((key, c)) or P[(key, "ALL")])[lvl]


def grade(key, c):
    return (P.get((key, c)) or P[(key, "ALL")])["grade"]


# ---------- pools (firms, employees) ----------
def load_pools():
    pools = {c: {} for c in COUNTRIES}
    es = json.load(open(DATA / "eurostat_sbs.json", encoding="utf-8"))
    for x in es:
        if x["size_emp"] == "TOTAL" and x["time"] == YEAR_EU and x["geo"] in ("ES", "NL"):
            k = ("e_" if x["indic_sbs"] == "EMP_NR" else "f_") + x["nace_r2"]
            pools[x["geo"]][k] = x["value"]
    # UK firms (nomis business counts, 2025) and employment (BRES, GB 2023)
    for r in csv.DictReader(open(DATA / "uk_counts.csv", encoding="utf-8")):
        if r["DATE_NAME"] == "2025" and r["EMPLOYMENT_SIZEBAND_NAME"] == "Total":
            pools["UK"]["f_" + r["INDUSTRY_NAME"].split(" ")[0]] = float(r["OBS_VALUE"])
    for r in csv.DictReader(open(DATA / "uk_emp.csv", encoding="utf-8")):
        if r["OBS_VALUE"]:
            pools["UK"]["e_" + r["INDUSTRY_NAME"].split(" ")[0]] = float(r["OBS_VALUE"])
    # US (SUSB 2022): F41->236, F42->237, F43->238, M71->5413, L68->531, N81->5617, K64->522
    m = {"236": "F41", "237": "F42", "238": "F43", "5413": "M71", "531": "L68", "5617": "N81", "522": "K64"}
    for r in csv.DictReader(open(DATA / "us_susb_2022_extract.csv", encoding="utf-8")):
        if r["NAICS"] in m:
            pools["US"]["e_" + m[r["NAICS"]]] = float(r["EMPL"])
            pools["US"]["f_" + m[r["NAICS"]]] = float(r["FIRM"])
    return pools


POOLS = load_pools()


def emp(c, *codes, w=1.0):
    return sum(POOLS[c].get("e_" + k, 0.0) for k in codes) * w


def f411(c, lvl):
    if c == "US":
        return POOLS[c]["f_F41"] * par("US_F411_proxy", c, lvl)
    return POOLS[c]["f_F411"] if "f_F411" in POOLS[c] else POOLS[c].get("f_411", 0.0)


def f_l68(c):
    return POOLS[c]["f_L68"] if "f_L68" in POOLS[c] else POOLS[c].get("f_68", 0.0)


# ---------- model ----------
def adoption(stage, c, lvl):
    d = par(stage + "_D", c, lvl)
    return d if stage == "S4" else min(1.0, d * par("Dmult", c, lvl))


def tam(stage, c, lvl, over=None):
    """USD million. `over` = {(key): level} overrides one input to another level (for sensitivity)."""
    def L(key):
        return (over or {}).get(key, lvl)
    if stage == "S0":
        n = (f411(c, L("US_F411_proxy")) + f_l68(c) * par("S0_L68_weight", c, L("S0_L68_weight"))) * par("S0_s", c, L("S0_s"))
    elif stage == "S4":
        n = par("S4_N_" + c, c, lvl)
    else:
        base = {"S1": ("K64",), "S2": ("M71",), "S3": ("M71",), "S8b": ("L68",)}.get(stage, ("F41", "F42", "F43"))
        if stage == "S8a":
            pool = emp(c, "L68") + 0.1 * emp(c, "N81")
        else:
            pool = emp(c, *base)
        n = pool * par(stage + "_s", c, L(stage + "_s"))
    pk = ("S4_P_" + c) if stage == "S4" else stage + "_P"
    ak = ("S4_A_" + c) if stage == "S4" else stage + "_A"
    return n * par(pk, c, L(pk)) * par(ak, c, L(ak)) / 1e6


def cur(stage, c, lvl):
    return tam(stage, c, lvl) * adoption(stage, c, lvl)


def keys_of(stage, c):
    ks = [stage + "_s", stage + "_P", stage + "_A", stage + "_D"]
    if stage == "S4":
        ks = ["S4_P_" + c, "S4_N_" + c, "S4_A_" + c, "S4_D"]
    return ks


def worst(stage, c):
    letters = []
    for k in keys_of(stage, c):
        g = grade(k, c)
        letters.append(max(g.replace("/", ""), key=lambda ch: "ABCD".index(ch) if ch in "ABCD" else 0))
    return max(letters, key=lambda ch: "ABCD".index(ch))


# ---------- registry floor ----------
# not software subscriptions, or stale: excluded from the floor
EXCLUDE = {
    "Ayesa": "инженерно-проектная фирма, не продавец программ",
    "Grupo Alava (Alava Ingenieros)": "инженерно-проектная фирма, не продавец программ",
    "Cotality (бывш. CoreLogic)": "данные 2019 года и данные о недвижимости, а не подписки на ПО этапа",
    "Dodge Construction Network": "поставщик данных о проектах, оценки расходятся в разы",
}


def registry_floor():
    import build_map as bm
    rows = list(csv.DictReader(open(ROOT / "knowledge" / "companies" / "registry.csv", encoding="utf-8-sig"), delimiter=";"))
    single, multi = {}, {}
    for r in rows:
        rev = bm.parse_rev(r["выручка"])
        if rev is None:
            continue
        if any(r["компания"].startswith(k) for k in EXCLUDE):
            continue
        st = r["этапы_основные"].strip()
        mk = [x.strip() for x in r["рынки_коды"].split(";") if x.strip()]
        if len(mk) == 1 and mk[0] in COUNTRIES and st in STAGES:
            single[(mk[0], st)] = single.get((mk[0], st), 0.0) + rev
        else:
            multi.setdefault(st or "н/д", []).append((r["компания"], rev))
    return single, multi


def fmt(x):
    if x >= 1000:
        return f"{x/1000:.1f} млрд"
    if x >= 10:
        return f"{x:.0f}"
    return f"{x:.1f}"


def main():
    # fix UK keys: nomis industry codes are bare numbers ("41"); map to F-codes
    u = POOLS["UK"]
    for src, dst in (("41", "F41"), ("42", "F42"), ("43", "F43"), ("411", "F411"), ("412", "F412"), ("64", "K64"),
                     ("65", "K65"), ("66", "K66"), ("68", "L68"), ("71", "M71"), ("81", "N81"), ("77", "N77")):
        for pre in ("e_", "f_"):
            if pre + src in u:
                u[pre + dst] = u[pre + src]
    out = []
    w = out.append
    w("# Объём рынка (TAM): результаты первого расчёта\n")
    w("> Сгенерировано `scripts/tam.py` из `tam_inputs.csv` и `tam_data/`. Метод — `tam_method.md`. Год 2025, USD млн (если не указано иное), курс ECB за 2025: 1 EUR = 1.13 USD. **Не публикуется без разрешения основателя.** Это оценка порядка величины на основе допущений: большинство ключевых входов — оценка D (см. раздел «Надёжность»).\n")

    w("## 1. TAM (потенциал), базовый сценарий, USD млн\n")
    w("| Этап | " + " | ".join(COUNTRIES) + " | Итого |")
    w("|---|" + "---|" * (len(COUNTRIES) + 1))
    sub = {k: {c: 0.0 for c in COUNTRIES} for k in ("constr", "re")}
    for s in STAGES:
        vals = [tam(s, c, "base") for c in COUNTRIES]
        for c, v in zip(COUNTRIES, vals):
            sub["re" if s in REAL_ESTATE else "constr"][c] += v
        flag = " ⚠" if s in ("S1", "S8b") else ""
        w(f"| {s}{flag} | " + " | ".join(fmt(v) for v in vals) + f" | {fmt(sum(vals))} |")
    for k, name in (("constr", "**Подитог: строительство (S0–S7, S9)**"), ("re", "**Подитог: недвижимость (S8a, S8b)**")):
        w(f"| {name} | " + " | ".join(fmt(sub[k][c]) for c in COUNTRIES) + f" | {fmt(sum(sub[k].values()))} |")
    tot = {c: sub['constr'][c] + sub['re'][c] for c in COUNTRIES}
    w("| **Всего** | " + " | ".join(fmt(tot[c]) for c in COUNTRIES) + f" | {fmt(sum(tot.values()))} |")
    w("\n⚠ — самые слабые клетки (S1, S8b): входы целиком допущения.\n")

    w("## 2. Диапазон low–high по странам (подитоги)\n")
    w("| Страна | Строительство TAM low / base / high | Недвижимость TAM low / base / high | Текущие траты (всего) low / base / high |")
    w("|---|---|---|---|")
    for c in COUNTRIES:
        a = [sum(tam(s, c, l) for s in CONSTRUCTION) for l in LEVELS]
        b = [sum(tam(s, c, l) for s in REAL_ESTATE) for l in LEVELS]
        d = [sum(cur(s, c, l) for s in STAGES) for l in LEVELS]
        w(f"| {c} | " + " / ".join(fmt(x) for x in a) + " | " + " / ".join(fmt(x) for x in b) + " | " + " / ".join(fmt(x) for x in d) + " |")

    w("\n## 3. Текущие траты (TAM × внедрение), базовый сценарий, USD млн\n")
    w("| Этап | " + " | ".join(COUNTRIES) + " | Итого |")
    w("|---|" + "---|" * (len(COUNTRIES) + 1))
    csub = {c: 0.0 for c in COUNTRIES}
    for s in STAGES:
        vals = [cur(s, c, "base") for c in COUNTRIES]
        for c, v in zip(COUNTRIES, vals):
            csub[c] += v
        w(f"| {s} | " + " | ".join(fmt(v) for v in vals) + f" | {fmt(sum(vals))} |")
    w("| **Всего** | " + " | ".join(fmt(csub[c]) for c in COUNTRIES) + f" | {fmt(sum(csub.values()))} |")

    w("\n## 4. Проверка сверху вниз (только текущие траты)\n")
    w(f"Аналитики называют «строительными программами» примерно этапы {', '.join(TOP_DOWN_STAGES)} (без S0, S1, S4, S8). Сравниваем с ними.\n")
    w("| Страна | Снизу вверх S2,S3,S5,S6,S7,S9 low / base / high | Сверху вниз (аналитики) low / base / high | Объём строительства × доля (low / base / high) | Разрыв base: снизу/аналитики |")
    w("|---|---|---|---|---|")
    for c in COUNTRIES:
        bu = [sum(cur(s, c, l) for s in TOP_DOWN_STAGES) for l in LEVELS]
        tdk = P.get(("td_%s_software" % c, c))
        an = [tdk[l] for l in LEVELS] if tdk else None
        vol = P[("td_construction_" + c, c)]["base"]
        rt = [par("td_ratio", c, l) * vol for l in LEVELS]
        gap = f"{bu[1] / an[1]:.1f}×" if an else "н/д (оценки по стране нет)"
        w(f"| {c} | " + " / ".join(fmt(x) for x in bu) + " | " + (" / ".join(fmt(x) for x in an) if an else "н/д") + " | " + " / ".join(fmt(x) for x in rt) + f" | {gap} |")
    w("\nПримечания: для Испании и Нидерландов объём строительства — валовая добавленная стоимость (занижает выпуск примерно вдвое); для Великобритании — только новые работы; оценки аналитиков для Великобритании — пересчёт доли региона, для США — одиночная оценка (оценка C).\n")

    w("## 5. Нижняя граница: выручка вендоров из реестра\n")
    single, multi = registry_floor()
    w("Выручка из реестра — оценки разной надёжности, у многих компаний её нет; вендоры с одним рынком отнесены к стране, остальные перечислены отдельно (выручка компании целиком, не только этапа).\n")
    w("| Этап | " + " | ".join(COUNTRIES) + " |")
    w("|---|" + "---|" * len(COUNTRIES))
    for s in STAGES:
        w(f"| {s} | " + " | ".join(fmt(single.get((c, s), 0.0)) if single.get((c, s)) else "—" for c in COUNTRIES) + " |")
    w("\nИсключены из нижней границы: " + "; ".join(f"{k} — {v}" for k, v in EXCLUDE.items()) + ".\n")
    bad = [(c, s, single[(c, s)], cur(s, c, "base")) for (c, s) in sorted(single) if single[(c, s)] > cur(s, c, "base")]
    if bad:
        w("**Клетки, где выручка вендоров из реестра выше расчётных текущих трат (модель, вероятно, занижает, либо вендор шире этапа):**\n")
        for c, s, f, m in bad:
            w(f"- {c} {s}: выручка вендоров {fmt(f)} против расчётных {fmt(m)}")
        w("")
    w("Компании с несколькими рынками (по основному этапу, USD млн, выручка компании целиком):\n")
    for st in sorted(multi):
        top = sorted(multi[st], key=lambda x: -x[1])[:5]
        w(f"- {st}: " + "; ".join(f"{n} {fmt(v)}" for n, v in top))

    w("\n## 6. Что сильнее всего двигает результат\n")
    drivers = []
    for s in STAGES:
        for k in ("_s", "_P", "_A"):
            key = s + k if s != "S4" else None
            if s == "S4":
                continue
            lo = sum(tam(s, c, "base", {key: "low"}) for c in COUNTRIES)
            hi = sum(tam(s, c, "base", {key: "high"}) for c in COUNTRIES)
            drivers.append((hi - lo, key, lo, hi))
    drivers.sort(reverse=True)
    w("Размах суммарного TAM (4 страны) при замене одного входа с base на low/high:\n")
    w("| Вход | TAM при low | TAM при high | Размах | Оценка входа |")
    w("|---|---|---|---|---|")
    for sp, key, lo, hi in drivers[:6]:
        w(f"| {key} | {fmt(lo)} | {fmt(hi)} | {fmt(sp)} | {grade(key, 'US')} |")

    w("\n## 7. Надёжность клеток\n")
    w("| Этап | " + " | ".join(COUNTRIES) + " |")
    w("|---|" + "---|" * len(COUNTRIES))
    for s in STAGES:
        w(f"| {s} | " + " | ".join(worst(s, c) for c in COUNTRIES) + " |")
    w("\nКлетка получает оценку самого слабого ключевого входа (доля мест, цена, применимость, внедрение). Покупатели (фирмы, занятые) — везде оценка A (официальная статистика); цены S3, S5, S6 — B (публичные цены вендоров); остальное — D.\n")

    w("## 8. Ограничения и оговорки\n")
    w("- Роботы по подписке: цены в открытом доступе не найдены, вклад в итог принят равным 0 (`S6_RaaS`) — это пробел, а не оценка.")
    w("- Модель по местам (занятые × доля пользователей × цена места) сама учитывает микрофирмы: они дают мало занятых. Отдельной чувствительности «с микрофирмами и без» не считалось.")
    w("- США 2022 (Census SUSB), Испания и Нидерланды 2023 (Eurostat), Великобритания: фирмы 2025, занятые GB 2023 (ONS) — годы разные.")
    w("- Соответствие NACE и NAICS приблизительное (особенно N81 ↔ 5617, K64 ↔ 522, F41.1 ↔ доля фирм 236).")
    w("- Цена места одинакова для всех стран (кроме S4); различия внедрения по странам задаёт множитель `Dmult` (допущение D).")
    w("- S4: часть органов власти не выдаёт разрешений сама; региональные и национальные порталы не учтены.")
    w("- Ни одна цена этапов S0, S1, S2, S7, S8, S9 не подтверждена источником: перед использованием числа нужна проверка (интервью с покупателями или Parallel).")
    (MK / "tam_results.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
