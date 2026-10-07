"""Analytics of the ConTech registry for the map and for publications (offline, reproducible).

Run:  python scripts/landscape_analytics.py
Needs: matplotlib (pip install matplotlib; tested with 3.11). No pandas, no network.

Reads knowledge/companies/registry.csv (never modifies it) and knowledge/value_chain.md (stage names).
Writes landscapes/construction-tech/3_map/analytics/:
  registry_normalized.csv, tables/*.csv, charts/*.png|svg, findings.md
Everything is a statement about the registry, not about the market.
"""
import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "knowledge" / "companies" / "registry.csv"
VC = ROOT / "knowledge" / "value_chain.md"
OUT = ROOT / "landscapes" / "construction-tech" / "3_map" / "analytics"
CHARTS = OUT / "charts"
TABLES = OUT / "tables"
TODAY = date.today().isoformat()

# fixed rates: ECB 2025 annual average (same source as knowledge/markets/tam_inputs.csv)
FX = {"$": 1.0, "€": 1.13, "£": 1.13 / 0.8568}
FX_NOTE = "ECB reference rates, 2025 annual average: 1 EUR = 1.1300 USD; 1 GBP = 1.3189 USD (1.13 / 0.8568)"
UNIT = {"млн": 1e6, "млрд": 1e9, "тыс": 1e3}

OUT_OF_SCOPE = ["не AEC", "к стройке отношения не имеет", "вне предметной области"]
OOS_NEAR = ["не имеет отношения", "не связан", "unrelated to construction"]  # reported, not applied

COMPLIANCE_KW = [r"комплаенс", r"compliance", r"проверк\w*\s+(?:проект\w*\s+)?(?:на\s+)?норм", r"соответстви\w+\s+норм",
                 r"норм\w+\s+(?:и\s+)?(?:правил|требовани)", r"building code", r"код\w*\s+норм", r"проверк\w+\s+норм",
                 r"нормативн", r"по\s+нормам", r"норм\w*\s+проверк"]

SOFT_CLASSES = ("стартап", "крупный вендор")
GROUP_HEAD = {"Nemetschek": "nemetschek", "Hilti": "hilti", "Schneider Electric": "rib-schneider", "OpenSpace": "openspace"}


# ---------------------------------------------------------------- stages
def load_stages():
    names, subs = {}, {}
    for line in VC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(S\d)\s*\|\s*([^|]+?)\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
        if not m:
            continue
        code, name, desc, note = m.groups()
        if code in names:  # the mapping table further down repeats S-codes with other columns
            continue
        name = re.sub(r"\s*\((?:принято|переименовано)[^)]*\)", "", name).strip()
        names[code] = name
        for sm in re.finditer(r"(S\d[a-d])\s+—\s+([^,;|]+)", desc + " ; " + note):
            subs[sm.group(1)] = sm.group(2).strip()
    # S8 holds two areas in one row
    names["S8a"] = "Эксплуатация"
    names["S8b"] = "Аренда, продажа, инвестиции"
    names.pop("S8", None)
    order = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8a", "S8b", "S9"]
    short = {k: names[k].split(":")[0].strip() for k in order}
    # axis labels: taxonomy names trimmed to fit a chart axis (only these four are shortened by hand)
    short.update({"S0": "Стратегия и участки", "S7": "Ввод и передача", "S8b": "Аренда и продажа", "S9": "Реновация и конец цикла"})
    return order, names, short, subs


# ---------------------------------------------------------------- parsing
AMT = re.compile(r"(более|свыше|около|~|≈)?\s*(\$|€|£)\s?(\d[\d\s ]*(?:[.,]\d+)?)(?:\s*[–\-]\s*(\d[\d\s ]*(?:[.,]\d+)?))?\s*(млрд|млн|тыс)\.?", re.I)


def num(s):
    return float(re.sub(r"[\s ]", "", s).replace(",", "."))


def parse_money(text):
    """-> (usd, status). First amount in the text; ranges -> midpoint; 'более/около/расчёт' -> estimate."""
    t = (text or "").strip()
    if not t or t.startswith("н/д") or t.startswith("не раскрыта"):
        return None, "missing"
    m = AMT.search(t)
    if not m:
        return None, "missing"
    q, cur, a, b, unit = m.groups()
    mult = UNIT[unit.lower()] * FX[cur]
    # "от $100 млн до $200 млн"
    m2 = re.search(r"от\s+(?:\$|€|£)\s?(\d[\d\s ]*(?:[.,]\d+)?)\s*(млрд|млн|тыс)\.?\s+до\s+(\$|€|£)\s?(\d[\d\s ]*(?:[.,]\d+)?)\s*(млрд|млн|тыс)", t)
    if m2:
        lo = num(m2.group(1)) * UNIT[m2.group(2)] * FX[m.group(2)]
        hi = num(m2.group(4)) * UNIT[m2.group(5)] * FX[m2.group(3)]
        return (lo + hi) / 2, "range"
    if b:
        return (num(a) + num(b)) / 2 * mult, "range"
    val = num(a) * mult
    if q or re.search(r"расчёт|агрегатор.*расходятся|источники расходятся", t[m.end():m.end() + 120]):
        return val, "estimate"
    return val, "ok"


def split_round(text):
    """The clause about the latest round: cut at 'ранее'; 'позднее' makes the row ambiguous."""
    t = (text or "").strip()
    amb = bool(re.search(r"позднее", t))
    clause = re.split(r";\s*ранее|,\s*ранее|\bранее\b", t)[0]
    return clause, amb


def round_type(clause):
    c = clause.lower()
    if re.search(r"куплен|продан|поглощ|приобрет|acquired", c):
        return "acquisition"
    if re.search(r"публичная компания|nasdaq|nyse|aim:", c):
        return "public"
    if re.search(r"pre-seed|предпосевн", c):
        return "pre-seed"
    if re.search(r"pre-series a", c):
        return "seed"
    if re.search(r"посевн|seed", c):
        return "seed"
    if re.search(r"series a", c):
        return "A"
    if re.search(r"series b", c):
        return "B"
    if re.search(r"series [c-h]", c):
        return "C+"
    if re.search(r"долг|заём|кредит|debt|loan", c):
        return "debt"
    if re.search(r"частный капитал|private equity|владельцы\s.*(associates|partners|capital)", c):
        return "private-equity"
    if re.search(r"^\s*[$€£]|\d\s*(млн|тыс)", c):
        return "unspecified"
    return "none"


def round_year(clause):
    ys = re.findall(r"(?<!\d)(20[12]\d)(?!\d)", clause)
    if not ys:
        return None, "missing"
    return int(ys[0]), ("ok" if len(set(ys)) == 1 else "ambiguous")


def parse_stage_list(s):
    out = []
    for p in re.split(r"[;,]", s or ""):
        p = p.strip()
        m = re.match(r"^(S\d)([abcd]?)$", p)
        if m:
            base, sub = m.groups()
            if base == "S8":
                base, sub = "S8", (sub or "a")
                out.append(("S8" + sub, "S8" + sub))
            else:
                out.append((base, base + sub if sub else ""))
    return out


def klass(r, head_ids):
    t = r["тип_организации"]
    g = r.get("группа", "")
    if t.startswith("крупный"):
        return "крупный вендор"
    if g and r["id"] not in head_ids.values():
        return "крупный вендор"  # a product of a larger group (documented in findings)
    if "платформа интегратора" in t or t.startswith("строитель"):
        return "строитель"
    if t.startswith("консалтинг") or t.startswith("кастомная"):
        return "консалтинг-инжиниринг"
    if "государственный проект" in t or t.startswith("образование"):
        return "прочее"
    if t.startswith("продукт"):
        return "стартап"
    return "прочее"


def verified_level(s):
    s = (s or "").strip()
    if s.startswith("да"):
        return "да"
    if s.startswith("частично"):
        return "частично"
    return "нет"


# ---------------------------------------------------------------- normalization
def normalize():
    rows = list(csv.DictReader(open(REG, encoding="utf-8-sig"), delimiter=";"))
    norm = []
    for r in rows:
        prim = parse_stage_list(r["этапы_основные"].split(";")[0])
        sec = parse_stage_list(r["этапы_дополнительные"])
        sp = prim[0][0] if prim else ""
        sub_p = prim[0][1] if prim else ""
        all_subs = sorted({sub for base, sub in prim + sec if sub and sub != base})
        sec_codes = []
        for base, sub in sec:
            if base != sp and base not in sec_codes:
                sec_codes.append(base)
        clause, amb_later = split_round(r["последний_раунд"])
        rtype = round_type(clause)
        usd, ust = parse_money(clause if rtype not in ("acquisition", "public", "private-equity", "none") else "")
        if rtype in ("acquisition", "public", "private-equity", "none"):
            usd, ust = None, "missing"
        ry, ryst = round_year(clause)
        if re.search(r"расширен|расширение", clause) and ryst == "ok":
            ryst = "ambiguous"  # the year may belong to the extension, not to the base round
        if amb_later:
            ust = "ambiguous" if usd is not None else ust
            ryst = "ambiguous" if ry is not None else ryst
        traised, trst = parse_money(r["привлечено"])
        txt = " ".join([r["примечание"], r["профиль_по_списку"]]).lower()
        in_scope = not any(k.lower() in txt for k in OUT_OF_SCOPE)
        near = any(k.lower() in txt for k in OOS_NEAR)
        norm.append({
            "id": r["id"], "компания": r["компания"], "группа": r.get("группа", ""),
            "stage_primary": sp, "stage_primary_sub": sub_p,
            "stage_primary_parse_status": "ok" if sp else "missing",
            "stages_secondary": ";".join(sec_codes),
            "stages_secondary_parse_status": "ok" if sec_codes else "missing",
            "substages_all": ";".join(all_subs),
            "last_round_usd": "" if usd is None else round(usd),
            "last_round_usd_parse_status": ust,
            "last_round_year": "" if ry is None else ry, "last_round_year_parse_status": ryst,
            "last_round_type": rtype,
            "last_round_type_parse_status": "ambiguous" if amb_later else ("ok" if rtype != "unspecified" else "ambiguous"),
            "total_raised_usd": "" if traised is None else round(traised),
            "total_raised_usd_parse_status": trst,
            "company_class": klass(r, GROUP_HEAD), "in_scope": str(in_scope).lower(),
            "in_scope_near_marker": str(near and in_scope).lower(),
            "verified_level": verified_level(r["данные_проверены"]),
            "roles": r["роль_клиента"], "subcategory": r["подкатегория"], "layer": r["слой"],
            "markets": r["рынки_коды"], "markets_basis": r["рынки_основание"], "global": r["глобальная"],
            "round_text": r["последний_раунд"], "_desc": txt,
            "_profile": (r["подкатегория"] + " " + r["профиль_по_списку"]).lower(),
        })
    return rows, norm


def write_normalized(norm):
    OUT.mkdir(parents=True, exist_ok=True)
    cols = [k for k in norm[0].keys() if not k.startswith("_")]
    with open(OUT / "registry_normalized.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(norm)


def coverage(norm, pred, fields):
    sub = [n for n in norm if pred(n)]
    res = {}
    for f in fields:
        c = Counter(n[f + "_parse_status"] for n in sub)
        res[f] = (len(sub), c)
    return res


# ---------------------------------------------------------------- charts
def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#8a929a", "axes.labelcolor": "#2b3138", "xtick.color": "#4b535b", "ytick.color": "#4b535b",
        "text.color": "#1d2327", "figure.facecolor": "white", "axes.facecolor": "white",
    })
    return plt


ACCENT = "#1f5f8b"
GRAY = "#b9c0c6"
INK2 = "#4b535b"


def save(fig, name, plt):
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / (name + ".png"), dpi=100, facecolor="white")
    fig.savefig(CHARTS / (name + ".svg"), facecolor="white")
    plt.close(fig)


def footer(fig, text, y=0.012, size=11):
    text = text if "\n" in text else wrap(text, 175)
    fig.text(0.02, y, text, ha="left", va="bottom", fontsize=size, color=INK2)


def wrap(s, n):
    import textwrap
    return "\n".join(textwrap.wrap(s, n, break_long_words=False))


def main():
    rows, norm = normalize()
    write_normalized(norm)
    order, names, short, subs = load_stages()
    TABLES.mkdir(parents=True, exist_ok=True)
    byid = {n["id"]: n for n in norm}
    scope = [n for n in norm if n["in_scope"] == "true"]
    soft = [n for n in scope if n["company_class"] in SOFT_CLASSES]
    startups = [n for n in scope if n["company_class"] == "стартап"]
    big = [n for n in scope if n["company_class"] == "крупный вендор"]
    N_ALL, N_SCOPE, N_SOFT, N_ST = len(norm), len(scope), len(soft), len(startups)

    # ---- coverage of parsing (step 1)
    fields = ["stage_primary", "stages_secondary", "last_round_usd", "last_round_year", "last_round_type", "total_raised_usd"]
    cov_all = coverage(norm, lambda n: True, fields)
    cov_st = coverage(norm, lambda n: n["company_class"] == "стартап" and n["in_scope"] == "true", fields)
    ok_usd = cov_st["last_round_usd"][1].get("ok", 0)
    gate_share = ok_usd / N_ST if N_ST else 0
    gate_pass = gate_share >= 0.5

    def stage_label(c):
        return f"{c} {short[c]}"

    # ---- Q1
    q1_prim = Counter(n["stage_primary"] for n in soft if n["stage_primary"])
    q1_any = Counter()
    for n in soft:
        for c in {n["stage_primary"], *[s for s in n["stages_secondary"].split(";") if s]}:
            if c:
                q1_any[c] += 1
    q1_all_prim = Counter(n["stage_primary"] for n in scope if n["stage_primary"])
    q1_sub = {"S5": Counter(), "S6": Counter()}
    q1_sub_n = {"S5": 0, "S6": 0}
    for n in soft:
        cov = {n["stage_primary"], *[s for s in n["stages_secondary"].split(";") if s]}
        for base in q1_sub:
            if base in cov:
                q1_sub_n[base] += 1
                subs_here = [s for s in n["substages_all"].split(";") if s.startswith(base)]
                if subs_here:
                    for s in subs_here:
                        q1_sub[base][s] += 1
                else:
                    q1_sub[base][base + " (без подэтапа)"] += 1
    with open(TABLES / "q1_stage_coverage.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап", "название", "основной_ПО", "с_дополнительными_ПО", "основной_все_in_scope"])
        for c in order:
            w.writerow([c, short[c], q1_prim.get(c, 0), q1_any.get(c, 0), q1_all_prim.get(c, 0)])

    # ---- Q2 niches (startups)
    sub_top = Counter(n["subcategory"] for n in startups if n["subcategory"] not in ("", "н/д")).most_common(10)
    clusters = {
        "обмер объёмов и сметы": r"обмер|смет|takeoff|объём",
        "контроль хода и качества на площадке": r"контрол\w* (хода|качества)|прогресс|progress|снимк|фото|съёмк",
        "разрешения и согласование": r"разрешен|permit|согласован|лиценз",
        "проверка проекта и норм": r"проверк\w* (проект|чертеж|норм)|ошибк\w* в чертеж|нормам",
        "управление проектом, график, документы": r"график|расписан|документооборот|управление проект|среда данных|cde",
        "роботы и техника": r"робот|техник|экскаватор|автономн|принтер",
        "эксплуатация зданий": r"эксплуатац|обслуживан|арендатор|управление здани",
        "анализ участков и инвестиций": r"участк|инвестиц|актив|недвижимост",
    }
    q2_cluster = {}
    for k, rx in clusters.items():
        members = [n for n in startups if re.search(rx, n["_profile"])]
        q2_cluster[k] = members
    with open(TABLES / "q2_niches.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["вид", "ниша_или_подкатегория", "стартапов"])
        for s, c in sub_top:
            w.writerow(["подкатегория (точное совпадение)", s, c])
        for k, mem in q2_cluster.items():
            w.writerow(["кластер по словам (см. findings)", k, len(mem)])

    # ---- Q3/Q4 money and freshness (startups, equity rounds)
    EQ = {"pre-seed", "seed", "A", "B", "C+"}
    rounds = [n for n in startups if n["last_round_type"] in EQ and n["last_round_year"] != ""]
    q4 = Counter()
    q4_names = defaultdict(list)
    for n in rounds:
        if int(n["last_round_year"]) in (2025, 2026) and n["stage_primary"]:
            q4[n["stage_primary"]] += 1
            q4_names[n["stage_primary"]].append(n["компания"])
    n_new = sum(q4.values())
    q3 = {}
    q3_names = {}
    if gate_pass:
        for n in startups:
            if n["last_round_type"] in EQ and n["last_round_year"] in (2025, 2026) and n["last_round_usd"] != "" \
               and n["last_round_usd_parse_status"] == "ok" and n["stage_primary"]:
                q3.setdefault(n["stage_primary"], []).append(int(n["last_round_usd"]))
                q3_names.setdefault(n["stage_primary"], []).append((int(n["last_round_usd"]), n["компания"]))
    with open(TABLES / "q4_new_rounds_2025_2026.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап", "название", "стартапов_с_раундом_2025_2026", "компании"])
        for c in order:
            w.writerow([c, short[c], q4.get(c, 0), "; ".join(q4_names.get(c, []))])

    # ---- Q5 stage x market (startups)
    MK = ["US", "UK", "ES", "NL", "EU", "OTHER"]
    MKN = {"US": "США", "UK": "Великобритания", "ES": "Испания", "NL": "Нидерланды", "EU": "Другая Европа", "OTHER": "Вне США и Европы"}
    q5_conf = {(s, m): 0 for s in order for m in MK}
    q5_unc = {(s, m): 0 for s in order for m in MK}
    for n in startups:
        stg = {n["stage_primary"], *[s for s in n["stages_secondary"].split(";") if s]} - {""}
        mk = [m.strip() for m in n["markets"].split(";") if m.strip()]
        if n["global"] == "да":
            mk = list(MK)
        conf = n["markets_basis"] not in ("штаб", "нет данных") or n["global"] == "да"
        for s in stg:
            for m in mk:
                if m in MK and s in order:
                    (q5_conf if conf else q5_unc)[(s, m)] += 1
    with open(TABLES / "q5_stage_market_startups.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап"] + [f"{MKN[m]} (подтверждено)" for m in MK] + [f"{MKN[m]} (по штабу)" for m in MK])
        for s in order:
            w.writerow([s] + [q5_conf[(s, m)] for m in MK] + [q5_unc[(s, m)] for m in MK])
    q5_empty = [(s, m) for s in order for m in MK if q5_conf[(s, m)] + q5_unc[(s, m)] == 0]
    q5_only_guess = [(s, m) for s in order for m in MK if q5_conf[(s, m)] == 0 and q5_unc[(s, m)] > 0]

    # ---- Q6 stage x client role (software, primary stage)
    q6 = defaultdict(Counter)
    role_tot = Counter()
    for n in soft:
        if not n["stage_primary"]:
            continue
        rl = [r.strip() for r in n["roles"].split(";") if r.strip() and r.strip() != "н/д"]
        for r in rl:
            q6[n["stage_primary"]][r] += 1
            role_tot[r] += 1
    top_roles = [r for r, _ in role_tot.most_common(8)]
    with open(TABLES / "q6_stage_role.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап"] + top_roles)
        for s in order:
            w.writerow([s] + [q6[s].get(r, 0) for r in top_roles])

    # ---- Q7 stage x class (all in scope, primary stage)
    CL = ["стартап", "крупный вендор", "консалтинг-инжиниринг", "строитель", "прочее"]
    q7 = defaultdict(Counter)
    for n in scope:
        if n["stage_primary"]:
            q7[n["stage_primary"]][n["company_class"]] += 1
    with open(TABLES / "q7_stage_class.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап"] + CL)
        for s in order:
            w.writerow([s] + [q7[s].get(c, 0) for c in CL])

    # ---- Q8 compliance
    rx = re.compile("|".join(COMPLIANCE_KW), re.I)
    q8 = [n for n in scope if n["layer"] == "комплаенс" or rx.search(n["subcategory"] + " " + n["_desc"])]
    q8_stage = Counter(n["stage_primary"] for n in q8 if n["stage_primary"])
    q8_type = Counter(n["last_round_type"] for n in q8)
    q8_mk = Counter()
    for n in q8:
        for m in [x.strip() for x in n["markets"].split(";") if x.strip()]:
            q8_mk[m] += 1
    with open(TABLES / "q8_compliance.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "компания", "класс", "этап", "тип_раунда", "год_раунда", "рынки", "слой_комплаенс"])
        for n in q8:
            w.writerow([n["id"], n["компания"], n["company_class"], n["stage_primary"], n["last_round_type"], n["last_round_year"], n["markets"], n["layer"] == "комплаенс"])

    # ---- Q9 verification by stage (software)
    q9 = defaultdict(Counter)
    for n in soft:
        if n["stage_primary"]:
            q9[n["stage_primary"]][n["verified_level"]] += 1
    with open(TABLES / "q9_verification_by_stage.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["этап", "да", "частично", "нет", "всего"])
        for s in order:
            c = q9[s]
            w.writerow([s, c["да"], c["частично"], c["нет"], sum(c.values())])

    # ================= charts (Russian and English variants) =================
    plt = setup_mpl()
    import matplotlib.colors as mc
    charts = []
    SHORT_EN = {"S0": "Strategy and sites", "S1": "Deal and financing", "S2": "Surveys", "S3": "Design", "S4": "Permits and review",
                "S5": "Pre-construction", "S6": "Construction", "S7": "Handover", "S8a": "Operations", "S8b": "Leasing and sales",
                "S9": "Renovation, end of life"}
    MKN_EN = {"US": "USA", "UK": "United Kingdom", "ES": "Spain", "NL": "Netherlands", "EU": "Other Europe", "OTHER": "Outside US and Europe"}
    CL_EN = {"стартап": "startup", "крупный вендор": "major vendor", "консалтинг-инжиниринг": "consulting / engineering", "строитель": "builder", "прочее": "other"}

    # numbers shared by the charts and the findings
    st_prim = Counter(n["stage_primary"] for n in startups if n["stage_primary"])
    tot_st = sum(st_prim.values())
    top3 = [c for c, _ in st_prim.most_common(3)]
    top3_share = sum(st_prim[c] for c in top3) / tot_st if tot_st else 0
    thin = [c for c in order if st_prim.get(c, 0) <= 3]
    n_money = sum(len(v) for v in q3.values())

    for old in CHARTS.glob("*"):
        old.unlink()

    MONTHS_RU = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    _t = date.today()

    def draw(lang):
        ru = lang == "ru"
        tr = (lambda r, e: r) if ru else (lambda r, e: e)
        sfx = "" if ru else "_en"
        sh = short if ru else SHORT_EN
        mkn = MKN if ru else MKN_EN
        d_ = f"данные на {_t.day} {MONTHS_RU[_t.month - 1]} {_t.year}" if ru else f"data as of {_t.day} {_t.strftime('%B %Y')}"
        reg = tr("Реестр ConTech", "ConTech registry")

        def lab(c):
            return f"{c}  {sh[c]}"

        # C2 coverage: primary vs with secondary (software)
        fig, ax = plt.subplots(figsize=(16, 9))
        xs = list(range(len(order)))
        w_ = 0.38
        ax.bar([x - w_ / 2 for x in xs], [q1_prim.get(c, 0) for c in order], w_, color=ACCENT, label=tr("главный этап компании", "the company's main stage"))
        ax.bar([x + w_ / 2 for x in xs], [q1_any.get(c, 0) for c in order], w_, color=GRAY, label=tr("все этапы, которые закрывает компания", "all stages the company covers"))
        for x, c in zip(xs, order):
            ax.text(x - w_ / 2, q1_prim.get(c, 0) + 0.8, str(q1_prim.get(c, 0)), ha="center", fontsize=12)
            ax.text(x + w_ / 2, q1_any.get(c, 0) + 0.8, str(q1_any.get(c, 0)), ha="center", fontsize=12, color=INK2)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{c}\n{wrap(sh[c], 15)}" for c in order], fontsize=11)
        ax.yaxis.set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.legend(frameon=False, fontsize=13, loc="upper right")
        fig.suptitle(tr("Сколько компаний работает на каждом этапе", "How many companies work at each stage"), x=0.03, y=0.97, ha="left", fontsize=22, fontweight="bold")
        fig.subplots_adjust(left=0.03, right=0.98, top=0.88, bottom=0.2)
        footer(fig, tr(f"{N_SOFT} программных продуктов из реестра ConTech, {d_}. Одна компания может попасть на несколько этапов.",
                       f"{N_SOFT} software products from the ConTech registry, {d_}. One company can appear at several stages."), y=0.02)
        save(fig, "02_stage_coverage_1600x900" + sfx, plt)

        # C3 stage x market heatmap (startups)
        fig, ax = plt.subplots(figsize=(16, 9))
        M = [[q5_conf[(s, m)] for m in MK] for s in order]
        cmap = mc.LinearSegmentedColormap.from_list("one", ["#f1f5f8", ACCENT])
        mx = max(max(r) for r in M) or 1
        ax.imshow(M, cmap=cmap, vmin=0, vmax=mx, aspect="auto")
        for i, s in enumerate(order):
            for j, m in enumerate(MK):
                c_, u_ = q5_conf[(s, m)], q5_unc[(s, m)]
                txt = str(c_) + (f" +{u_}?" if u_ else "")
                ax.text(j, i, txt, ha="center", va="center", fontsize=14, color="white" if c_ > mx * 0.55 else "#1d2327")
        ax.set_xticks(range(len(MK)))
        ax.set_xticklabels([mkn[m] for m in MK], fontsize=13)
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([f"{c} {sh[c]}" for c in order], fontsize=13)
        for sp_ in ax.spines.values():
            sp_.set_visible(False)
        ax.tick_params(length=0)
        fig.suptitle(tr("Где какие этапы закрывают стартапы", "Where startups cover which stages"), x=0.03, y=0.975, ha="left", fontsize=22, fontweight="bold")
        fig.subplots_adjust(left=0.22, right=0.98, top=0.82, bottom=0.1)
        footer(fig, tr(f"{N_ST} стартапов реестра, {d_}. Цифра — стартапы, у которых рынок назван в источниках. «+3?» — ещё три стартапа, у которых рынок мы только предположили по стране штаб-квартиры.",
                       f"{N_ST} registry startups, {d_}. The number is startups whose market is named in sources. '+3?' means three more startups whose market we only guessed from the headquarters country."), y=0.02, size=11)
        save(fig, "03_stage_market_startups_1600x900" + sfx, plt)

        # C4 stage x class (stacked, accent = startups)
        fig, ax = plt.subplots(figsize=(16, 9))
        left = [0] * len(order)
        pal = {"стартап": ACCENT, "крупный вендор": "#6f7d89", "консалтинг-инжиниринг": GRAY, "строитель": "#d6dade", "прочее": "#e8ebee"}
        for cl in CL:
            v = [q7[s].get(cl, 0) for s in order]
            ax.barh(range(len(order)), v, left=left, color=pal[cl], label=cl if ru else CL_EN[cl], height=0.68, edgecolor="white", linewidth=1.5)
            left = [a + b for a, b in zip(left, v)]
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([f"{c} {sh[c]}" for c in order], fontsize=13)
        ax.invert_yaxis()
        for i, t_ in enumerate(left):
            ax.text(t_ + 0.6, i, str(t_), va="center", fontsize=12)
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.legend(frameon=False, fontsize=12, ncol=5, loc="upper center", bbox_to_anchor=(0.45, -0.01))
        fig.suptitle(tr("Распределение типа компаний по этапам", "Company types by stage"), x=0.03, y=0.975, ha="left", fontsize=22, fontweight="bold")
        fig.subplots_adjust(left=0.22, right=0.97, top=0.9, bottom=0.12)
        footer(fig, tr(f"{N_SCOPE} компаний реестра, {d_}. В «крупных вендорах» учтены и продукты, входящие в группы крупных вендоров.",
                       f"{N_SCOPE} companies in the registry, {d_}. 'Major vendor' also counts products that belong to groups of major vendors."), y=0.02, size=11)
        save(fig, "04_stage_by_class_1600x900" + sfx, plt)

        # C5 new rounds 2025-2026 by stage (count)
        fig, ax = plt.subplots(figsize=(16, 9))
        v = [q4.get(c, 0) for c in order]
        mxv = max(v) or 1
        ax.bar(range(len(order)), v, color=[ACCENT if x == mxv else GRAY for x in v], width=0.62)
        for i, x in enumerate(v):
            ax.text(i, x + 0.15, str(x), ha="center", fontsize=14)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([f"{c}\n{wrap(sh[c], 15)}" for c in order], fontsize=11)
        ax.yaxis.set_visible(False)
        ax.spines["left"].set_visible(False)
        fig.suptitle(tr("Кто привлекал деньги в 2025–2026: стартапы по этапам", "Who raised money in 2025–2026: startups by stage"), x=0.03, y=0.97, ha="left", fontsize=22, fontweight="bold")
        fig.subplots_adjust(left=0.03, right=0.98, top=0.88, bottom=0.2)
        footer(fig, tr(f"{n_new} из {N_ST} стартапов, у которых последний раунд пришёлся на 2025 или 2026 год, {d_}. Считаем раунды, а не суммы; данные из пресс-релизов и открытых баз.",
                       f"{n_new} of {N_ST} startups whose latest round fell in 2025 or 2026, {d_}. We count rounds, not amounts; data from press releases and open databases."), y=0.02, size=11)
        save(fig, "05_new_rounds_by_stage_1600x900" + sfx, plt)

        # C7 money by stage (only when the parsing gate passed)
        if gate_pass and q3:
            fig, ax = plt.subplots(figsize=(16, 9))
            stg = [c for c in order if q3.get(c)]
            tot = [sum(q3[c]) / 1e6 for c in stg]
            mxm = max(tot)
            ax.barh(range(len(stg)), tot, color=[ACCENT if x == mxm else GRAY for x in tot], height=0.62)
            for i, c in enumerate(stg):
                med = statistics.median(q3[c]) / 1e6
                medtxt = (f"{med:.1f}".rstrip("0").rstrip(".")) if med % 1 else f"{med:.0f}"
                medtxt = medtxt.replace(".", ",") if ru else medtxt
                ax.text(tot[i] + mxm * 0.01, i, f"{tot[i]:.0f}   " + tr(f"Медиана: {medtxt} млн", f"Median: ${medtxt}M"), va="center", fontsize=14)
            ax.set_yticks(range(len(stg)))
            ax.set_yticklabels([f"{c} {sh[c]}" for c in stg], fontsize=14)
            ax.invert_yaxis()
            ax.set_xlim(0, mxm * 1.35)
            ax.xaxis.set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_visible(False)
            fig.suptitle(tr("Сколько привлекли стартапы в 2025–2026: сумма раундов по этапам, млн $", "How much startups raised in 2025–2026: total of rounds by stage, $ million"), x=0.03, y=0.97, ha="left", fontsize=22, fontweight="bold")
            fig.subplots_adjust(left=0.22, right=0.97, top=0.88, bottom=0.12)
            footer(fig, tr(f"{n_money} стартапов с точной суммой раунда 2025–2026 (из {N_ST}), {d_}. Данные из пресс-релизов и открытых баз.",
                           f"{n_money} startups with an exact round amount in 2025–2026 (of {N_ST}), {d_}. Data from press releases and open databases."), y=0.02, size=11)
            save(fig, "07_last_rounds_money_by_stage_1600x900" + sfx, plt)

    draw("ru")
    draw("en")
    charts = [(f.stem, "") for f in sorted(CHARTS.glob("*.png")) if not f.stem.endswith("_en")]

    # ================= findings.md =================
    L = []
    w = L.append
    w("# Аналитика реестра ConTech\n")
    w(f"> Сгенерировано `scripts/landscape_analytics.py` {TODAY}. Все утверждения — о **реестре**, а не о рынке: выборка составлена основателем и дополнена вручную, смещена в сторону стартапов с внешними деньгами и не репрезентативна. `registry.csv` не менялся; новые данные в этом разделе не искались.\n")
    w("## Правила нормализации\n")
    w(f"- Курсы: {FX_NOTE}. Один документированный курс для всех пересчётов (тот же, что в `knowledge/markets/tam_inputs.csv`).")
    w("- Статус разбора: `ok` — точная сумма или год; `estimate` — «более», «около», сумма-расчёт; `range` — диапазон (берётся середина); `ambiguous` — в строке два раунда или два года без возможности выбрать, либо тип не определён; `missing` — нет данных.")
    w("- Последний раунд берётся из фразы до слова «ранее»; если в строке есть «позднее», строка помечается `ambiguous`.")
    w("- Покупки, публичный статус, частный капитал и записи без раунда не дают суммы раунда (`last_round_usd` пуст); заём (`debt`) тоже не входит в суммы акционерных раундов.")
    w("- Выручка из агрегаторов (Latka и подобные) в расчёты не входит.")
    w(f"- `in_scope = false` для записей с пометками «{'», «'.join(OUT_OF_SCOPE)}» в примечании или профиле; выбыло {N_ALL - N_SCOPE} из {N_ALL}. Записей с близкими формулировками ({', '.join(OOS_NEAR)}), оставленных в выборке: {sum(1 for n in norm if n['in_scope_near_marker'] == 'true')}.")
    w("- Классы: `стартап` — тип начинается с «продукт», нет материнской группы (или это головная запись группы); `крупный вендор` — тип «крупный вендор» и продукты, входящие в группу (Bluebeam, Fieldwire, 4PS, RIB и др.); `консалтинг-инжиниринг` — консалтинг и кастомная разработка; `строитель` — строители и платформа интегратора (011h); `прочее` — образование и государственный проект (PlanX).")
    w(f"- Население «записи ПО» = in_scope и класс «стартап» или «крупный вендор» (n = {N_SOFT}: стартапов {N_ST}, крупных вендоров и продуктов их групп {len(big)}). Hilti, Fieldwire и 4PS — три отдельные записи. Консалтинг, строители и прочее считаются только там, где указано (вывод 7).")
    w("- Названия этапов — из `knowledge/value_chain.md` (v0.3), на осях — часть до двоеточия.\n")

    w("## Покрытие разбора полей\n")
    w("| Поле | все записи (n = %d): ok | стартапы in_scope (n = %d): ok | estimate/range | ambiguous | missing |" % (N_ALL, N_ST))
    w("|---|---|---|---|---|---|")
    for f in fields:
        a = cov_all[f][1]
        s = cov_st[f][1]
        w(f"| {f} | {a.get('ok', 0)} ({round(a.get('ok', 0) / N_ALL * 100)}%) | {s.get('ok', 0)} ({round(s.get('ok', 0) / N_ST * 100)}%) | {s.get('estimate', 0) + s.get('range', 0)} | {s.get('ambiguous', 0)} | {s.get('missing', 0)} |")
    w("")
    w(f"**Проверка перед денежными расчётами:** сумма последнего раунда распарсена со статусом `ok` у {ok_usd} из {N_ST} стартапов ({gate_share * 100:.1f}%). " +
      ("Порог 50% пройден: денежные расчёты допустимы." if gate_pass else "**Порог 50% не пройден. Денежные графики и таблица «деньги по этапам» (вопрос 3) не строились.** Решение за основателем: снизить требование или собирать данные точнее."))
    w("")

    w("## Выводы\n")
    # 1
    w("### 1. Покрытие этапов\n")
    w(f"- Утверждение: записи ПО распределены по основному этапу неравномерно. Цифра: " + "; ".join(f"{c} {short[c]} — {q1_prim.get(c, 0)}" for c in order) + f". n = {N_SOFT}. Оговорка: этап присвоен по описанию продукта.  График: `charts/02_stage_coverage_1600x900`.")
    w(f"- С учётом дополнительных этапов: " + "; ".join(f"{c} — {q1_any.get(c, 0)}" for c in order) + ".")
    for base in ("S5", "S6"):
        parts = ", ".join(f"{k} {subs.get(k, '')} — {v}" if k in subs else f"{k} — {v}" for k, v in sorted(q1_sub[base].items()))
        w(f"- Подэтапы {base} (записи ПО, закрывающие {base} как основной или дополнительный этап, n = {q1_sub_n[base]}; запись с несколькими подэтапами считается по каждому): {parts}.")
    w(f"- Доля трёх самых плотных этапов среди стартапов: {round(top3_share * 100)}% ({', '.join(short[c] + ' ' + str(st_prim[c]) for c in top3)}), n = {tot_st}. Оговорка: реестр собирался вокруг стройки и ИИ, поэтому плотность этапов S5 и S6 может отражать собирание, а не рынок.\n")
    # 2
    w("### 2. Плотность ниш\n")
    w("Топ-10 подкатегорий стартапов (точное совпадение текста, n = %d):\n" % N_ST)
    for s, c in sub_top:
        w(f"- {s} — {c}")
    w("\nКластеры по ключевым словам (правила — в скрипте, словарь `clusters`; стартапы, n = %d):\n" % N_ST)
    for k, mem in q2_cluster.items():
        flag = " ← пять и больше" if len(mem) >= 5 else ""
        w(f"- {k}: {len(mem)}{flag}" + (f" ({', '.join(n['компания'] for n in mem[:8])}{'…' if len(mem) > 8 else ''})" if mem else ""))
    w("\nОговорка: подкатегории — свободный текст, точные совпадения редки; кластеры — приближение по словам и могут включать лишнее или пропускать нужное. Утверждение «почти одно и то же» требует чтения описаний.\n")
    # 3
    w("### 3. Деньги по этапам\n")
    if gate_pass:
        w("| Этап | n с суммой | сумма, USD млн | медиана, USD млн | крупнейший раунд |\n|---|---|---|---|---|")
        for c in order:
            vals = q3.get(c, [])
            if vals:
                big_r = max(q3_names[c])
                w(f"| {c} {short[c]} | {len(vals)} | {sum(vals) / 1e6:.1f} | {statistics.median(vals) / 1e6:.1f} | {big_r[1]} {big_r[0] / 1e6:.0f} ({round(big_r[0] / sum(vals) * 100)}% суммы) |")
        n_money = sum(len(v) for v in q3.values())
        w(f"\nn = {n_money} стартапов с точной суммой акционерного раунда 2025–2026 из {N_ST}; только акционерные раунды, без займов, покупок и частного капитала. Суммы — по данным агрегаторов и пресс-релизов, курсы — см. выше. Оговорка: на этапе по 1–13 раундов, один крупный раунд определяет сумму (см. последний столбец); медиана устойчивее суммы. Не выводите из таблицы «куда идут деньги в отрасли». График: `charts/07_last_rounds_money_by_stage_1600x900`.")
    else:
        w(f"Не рассчитывалось: порог разбора не пройден ({ok_usd} из {N_ST} стартапов, {gate_share * 100:.1f}%). Для справки, акционерных раундов с годом разобрано {len(rounds)}; из них 2025–2026 — {n_new}. Остальные суммы в реестре — оценки, диапазоны, покупки или «н/д».\n")
    # 4
    w("### 4. Свежесть\n")
    w(f"- Стартапов с акционерным раундом (pre-seed … C+) в 2025–2026 годах: {n_new} из {N_ST}. По этапам: " + "; ".join(f"{c} {short[c]} — {q4.get(c, 0)}" for c in order if q4.get(c, 0)) + f". График: `charts/05_new_rounds_by_stage_1600x900`. Оговорка: год раунда взят из последней записи в реестре; ранние раунды компаний не видны; считаются раунды, а не суммы.\n")
    # 5
    w("### 5. Этап × рынок (стартапы)\n")
    w(f"- Ячеек этап × рынок без единого стартапа: {len(q5_empty)} из {len(order) * len(MK)}; ячеек, где стартапы есть только по предположению из штаба: {len(q5_only_guess)}. Пустые ячейки: " + ("; ".join(f"{s} × {MKN[m]}" for s, m in q5_empty) or "нет") + ".")
    w(f"- Только по штабу (нет подтверждения): " + ("; ".join(f"{s} × {MKN[m]}" for s, m in q5_only_guess) or "нет") + f". n = {N_ST}. График: `charts/03_stage_market_startups_1600x900`. Оговорка: пустая клетка — это «нет в реестре», а не «нет на рынке» и не «возможность»; возможные причины — нет денег, регулирование, раздробленные покупатели, выборка.\n")
    # 6
    w("### 6. Этап × роль клиента (записи ПО)\n")
    w("Самые частые роли клиента: " + ", ".join(f"{r} — {role_tot[r]}" for r in top_roles) + f". n = {N_SOFT}. Таблица: `tables/q6_stage_role.csv`. Оговорка: роль присвоена по описанию; запись может иметь несколько ролей и считается по каждой.\n")
    # 7
    w("### 7. Этап × класс\n")
    only_st = [c for c in order if q7[c].get("стартап", 0) > 0 and q7[c].get("крупный вендор", 0) == 0]
    only_big = [c for c in order if q7[c].get("крупный вендор", 0) > 0 and q7[c].get("стартап", 0) == 0]
    w(f"- Этапы, где в реестре только стартапы (без крупных вендоров): {', '.join(c + ' ' + short[c] for c in only_st) or 'нет'}. Только крупные вендоры: {', '.join(c + ' ' + short[c] for c in only_big) or 'нет'}. n = {N_SCOPE} записей in_scope. График: `charts/04_stage_by_class_1600x900`.")
    w("- Оговорка: крупные вендоры внесены выборочно (по запросам основателя по рынкам), поэтому «нет крупных вендоров на этапе» означает «нет в реестре».\n")
    # 8
    w("### 8. Комплаенс и проверка норм\n")
    w(f"- Записей: {len(q8)} (метка `слой = комплаенс` или слова из правил: {', '.join(COMPLIANCE_KW)}). Этапы: " + "; ".join(f"{c} — {q8_stage.get(c, 0)}" for c in order if q8_stage.get(c, 0)) + ". Типы последнего раунда: " + ", ".join(f"{k} — {v}" for k, v in q8_type.most_common()) + ". Рынки: " + ", ".join(f"{MKN.get(k, k)} — {v}" for k, v in q8_mk.most_common()) + f". Список: `tables/q8_compliance.csv`.")
    w("- Оговорка: правила по словам дают ложные срабатывания и пропуски; список нужно прочитать глазами перед публикацией.\n")
    # 9
    w("### 9. Качество данных\n")
    tot_v = Counter(n["verified_level"] for n in soft)
    w(f"- Записи ПО (n = {N_SOFT}) по уровню проверки: да — {tot_v['да']}, частично — {tot_v['частично']}, нет — {tot_v['нет']}. По этапам: `tables/q9_verification_by_stage.csv`. Оговорка: «частично» означает, что часть полей сверена; это не гарантия остальных.\n")

    w("## Что нельзя утверждать по этим данным\n")
    for s in [
        "Нельзя утверждать о размере, росте или долях рынка: реестр — список основателя плюс ручные дополнения, не выборка.",
        "Нельзя считать плотность этапа спросом: число записей показывает, где собирали, а не где платят.",
        "Нельзя считать пустую ячейку возможностью: объяснения «нет денег», «регулирование», «раздробленные покупатели», «артефакт списка» не исключены.",
        "Нельзя складывать суммы раундов в «рынок»: суммы — по данным агрегаторов и пресс-релизов, разного года и качества; покупки, займы и инвестиции частного капитала — не раунды.",
        "Нельзя сравнивать выручку записей: ARR, выручка группы и оценки агрегаторов несопоставимы (в расчёты не включены).",
        "Нельзя считать записи независимыми компаниями: продукты одной группы считаются отдельно.",
        "Известные ошибки исходных строк в реестре (по отчёту Parallel 06.10.2026, `2_collection/raw/parallel-factcheck-US-1-pro.md`) в этом расчёте не исправлялись, так как реестр заморожен: Entrata (миноритарная инвестиция, не Series D), ALICE ($47 млн включают заём), Bluebeam, Fieldwire, Foundation Software (покупки, не раунды). Парсер относит строки с «куплена» к покупкам и не включает их в суммы, но другие подобные ошибки возможны.",
        "География стартапов частично подставлена по штабу; такие значения показаны отдельно («+N?»).",
    ]:
        w(f"- {s}")
    w("")
    w("## Кандидаты в хук\n")
    w("Хуки будут написаны после финализации графиков (решение основателя 07.10.2026).\n")
    w("## Файлы\n")
    w("- `registry_normalized.csv`: нормализованные поля и статусы разбора; `tables/`: таблицы по вопросам; `charts/`: PNG и SVG. Пересборка: `python scripts/landscape_analytics.py`.")
    w("- Внешние ориентиры и источники, ожидающие одобрения, — в `external_benchmarks.md` (отдельно: скрипт сеть не использует).")
    (OUT / "findings.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"records {N_ALL}, in_scope {N_SCOPE}, soft {N_SOFT}, startups {N_ST}, big {len(big)}")
    print(f"gate: ok usd {ok_usd}/{N_ST} = {gate_share*100:.1f}% -> {'PASS' if gate_pass else 'FAIL'}")
    for f in fields:
        print(f, dict(cov_st[f][1]))
    print("charts:", [c[0] for c in charts])


if __name__ == "__main__":
    main()



