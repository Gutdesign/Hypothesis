"""One-off, part 2 (2026-10-06): financial data for the seven rows added from the fact-check,
the 011h correction requested by the founder, and the new `группа` column.

Sources for every value are in the row's `источники_данных` (pages opened 2026-10-06 unless noted).
English overrides go to knowledge/companies/i18n/en_part10.tsv. Run once on a clean registry.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

D = "06.10.2026"
rows = registry.read(registry.CSV_PATH)
by = {r["id"]: r for r in rows}
per_id, _ = bm.load_en()
en, star = [], []


def setf(cid, field, ru, key=None, en_txt=None):
    by[cid][field] = ru
    if key:
        en.append((cid, key, en_txt if en_txt is not None else "n/a"))


def src(cid, *urls):
    have = by[cid]["источники_данных"].split()
    for u in urls:
        if u not in have:
            have.append(u)
    by[cid]["источники_данных"] = " ".join(have)


def note(cid, ru, en_txt):
    r = by[cid]
    r["примечание"] = (r["примечание"] + " | " if r["примечание"] else "") + "финансы, " + D + ": " + ru
    old = next((t for (i, k, t) in reversed(en) if i == cid and k == "note"), per_id.get((cid, "note"), ""))
    en.append((cid, "note", (old + " | " if old else "") + "financials, " + D + ": " + en_txt))


def ver(cid, ru, en_txt):
    by[cid]["данные_проверены"] = ru
    star.append(("verified", ru, en_txt))


V1 = "частично: пресс-релиз или страница компании открыты " + D + ", остальное — агрегаторы"
V1E = "partial: a press release or company page opened on " + D + ", the rest from aggregators"
V2 = "частично: агрегаторы и пресса, первоисточник не открывался; сайт компании не открылся " + D
V2E = "partial: aggregators and press, no primary source opened; the company site did not open on " + D

# ---- 011h: the founder's correction (company wording) ----
setf("011h", "тип_организации", "продукт (платформа интегратора)")
by["011h"]["подкатегория"] = "цифровая платформа интегратора: проектирование по каталогу готовых решений и строительство с сетью производителей"
star.append(("sub", by["011h"]["подкатегория"], "an integrator's digital platform: design from a catalogue of ready solutions and construction with a network of manufacturers"))
note("011h", "основатель карты уточнил: компания развивает собственный цифровой продукт; по её формулировке — «интегратор»: собственная цифровая платформа для проектирования по каталогу готовых решений и строительства с сетью производителей. Продажа платформы внешним клиентам на сайте не найдена, поэтому запись остаётся с пометкой «платформа интегратора», а не «ПО как услуга»",
     "the map's founder clarified that the company builds its own digital product; in its own words it is an 'integrator' with its own digital platform for design from a catalogue of ready solutions and for construction with a network of manufacturers. No sale of the platform to outside clients was found on the site, so the record stays marked as an 'integrator platform', not as software as a service")

# ---- financials ----
setf("testfit", "штаб_город", "Dallas")
setf("testfit", "штаб_страна", "США")
setf("testfit", "рынки_коды", "US")
setf("testfit", "рынки_основание", "штаб")
setf("testfit", "последний_раунд", "Series A, $20 млн, 26.07.2022 (ведущий инвестор Parkway Venture Capital)", "round",
     "Series A, $20M, 26.07.2022 (led by Parkway Venture Capital)")
setf("testfit", "привлечено", "$22 млн всего на 26.07.2022", "raised", "$22M in total as of 26.07.2022")
src("testfit", "https://www.globenewswire.com/news-release/2022/07/26/2486004/0/en/testfit-announces-20-million-investment-by-parkway-venture-capital.html")
ver("testfit", V1, V1E)
note("testfit", "раунд и штаб — по пресс-релизу (открыт); штат и выручка не найдены; 6 200+ пользователей — заявление компании",
     "the round and HQ are from the press release (opened); headcount and revenue not found; 6,200+ users is a company claim")

setf("skyciv", "штаб_город", "Sydney")
setf("skyciv", "штаб_страна", "Австралия")
setf("skyciv", "год_основания", "2013 (по сайту компании)", "founded", "2013 (per the company site)")
setf("skyciv", "последний_раунд", "внешних инвестиций нет: компания называет себя самофинансируемой", "round", "no outside investment: the company describes itself as self-funded")
setf("skyciv", "привлечено", "н/д (агрегатор: около $20 тыс. от UNSW Founders)", "raised", "n/a (aggregator: about $20K from UNSW Founders)")
setf("skyciv", "размер_сотрудников", "около 26 (оценка агрегатора, 2026)", "size", "about 26 (aggregator estimate, 2026)")
setf("skyciv", "выручка", "оценка агрегатора Latka: $2,9 млн за 2025; не раскрыта компанией", "revenue", "Latka aggregator estimate: $2.9M for 2025; not disclosed by the company")
setf("skyciv", "рынки_цель", "инженеры в более чем 160 странах (заявление компании)", "markets", "engineers in more than 160 countries (company claim)")
setf("skyciv", "рынки_коды", "US; UK; ES; NL; EU; OTHER")
setf("skyciv", "рынки_основание", "широкий охват")
src("skyciv", "https://skyciv.com/about/", "https://getlatka.com/companies/skyciv.com")
ver("skyciv", V1, V1E)
note("skyciv", "офисы Сидней и Чикаго, 160+ стран и 10 000+ инженеров — по странице компании (открыта); выручка — оценка агрегатора, не годовая выручка по отчётности",
     "offices in Sydney and Chicago, 160+ countries and 10,000+ engineers are from the company page (opened); revenue is an aggregator estimate, not reported annual revenue")

setf("nplan", "год_основания", "2017 (по словам основателя в сообщении об инвестиции)", "founded", "2017 (per the founder's words in the funding release)")
setf("nplan", "последний_раунд", "Series B, £11,9 млн (около $16 млн), 17.10.2025 (ведущий инвестор CapHorn; также Chevron Technology Ventures, Suffolk Technologies, GV, Pentech Ventures, LocalGlobe)", "round",
     "Series B, £11.9M (about $16M), 17.10.2025 (led by CapHorn; also Chevron Technology Ventures, Suffolk Technologies, GV, Pentech Ventures, LocalGlobe)")
src("nplan", "https://www.uktechnews.info/2025/10/17/nplan-secures-11-9-million-series-b-investment-led-by-caphorn/")
ver("nplan", V1, V1E)
note("nplan", "общая сумма, штат и выручка в сообщении не названы", "total raised, headcount and revenue are not stated in the release")

setf("one-click-lca", "штаб_город", "Helsinki")
setf("one-click-lca", "штаб_страна", "Финляндия")
setf("one-click-lca", "рынки_коды", "US; UK; ES; NL; EU; OTHER")
setf("one-click-lca", "рынки_основание", "широкий охват")
setf("one-click-lca", "год_основания", "2001 (агрегатор)", "founded", "2001 (aggregator)")
setf("one-click-lca", "последний_раунд", "€40 млн, 28.11.2023 (PSG и InfraVia)", "round", "€40M, 28.11.2023 (PSG and InfraVia)")
setf("one-click-lca", "привлечено", "€40 млн в раунде 2023; общая сумма не найдена (агрегатор: $43,8 млн)", "raised", "€40M in the 2023 round; total not found (aggregator: $43.8M)")
setf("one-click-lca", "размер_сотрудников", "170–236 (агрегаторы)", "size", "170–236 (aggregators)")
setf("one-click-lca", "выручка", "слабая оценка агрегатора: $21 млн, год не указан", "revenue", "weak aggregator estimate: $21M, year not given")
src("one-click-lca", "https://tech.eu/2023/11/28/one-click-lca-secures-40-m-investment-to-decarbonise-the-world-s-construction/",
    "https://oneclicklca.com/en/resources/press-release/40m-growth-equity-psg-infravia/")
ver("one-click-lca", V2, V2E)
note("one-click-lca", "раунд и штаб Хельсинки — по пресс-релизам в выдаче поиска (страницы не открывались); штат и выручка — агрегаторы, расходятся",
     "the round and the Helsinki HQ are from press releases in search results (pages not opened); headcount and revenue are from aggregators and differ")

setf("madaster", "год_основания", "2017 (агрегатор)", "founded", "2017 (aggregator)")
setf("madaster", "последний_раунд", "заём Фонда «Зелёный, здоровый, умный» (Economic Board Utrecht), 17.01.2019; сумма не указана", "round",
     "loan from the Green, Healthy, Smart Fund (Economic Board Utrecht), 17.01.2019; amount not stated")
setf("madaster", "привлечено", "около $4 млн (агрегатор)", "raised", "about $4M (aggregator)")
src("madaster", "https://madaster.com/inspiration/green-healthy-smart-fund-loan-impulse-for-further-development-of-madasters-online-material-passport/")
ver("madaster", V1, V1E)
note("madaster", "в 2019 компания называла себя Utrecht-платформой; на текущем сайте адрес в Амстердаме; штат и выручка не найдены; 200+ клиентов — заявление 2019 года",
     "in 2019 the company called itself an Utrecht platform; the current site gives an Amsterdam address; headcount and revenue not found; 200+ customers is a 2019 claim")

setf("yardi", "штаб_город", "Santa Barbara")
setf("yardi", "штаб_страна", "США")
setf("yardi", "год_основания", "1984 (справочник)", "founded", "1984 (reference)")
setf("yardi", "последний_раунд", "частная компания", "round", "private company")
setf("yardi", "размер_сотрудников", "около 10 000 (оценка агрегаторов)", "size", "about 10,000 (aggregator estimate)")
setf("yardi", "выручка", "слабая оценка агрегатора: $2,2 млрд, год не указан", "revenue", "weak aggregator estimate: $2.2B, year not given")
src("yardi", "https://en.wikipedia.org/wiki/Yardi_Systems")
ver("yardi", V2, V2E)
note("yardi", "сайт не открылся (403); штаб и штат — по справочникам в выдаче поиска; выручка из одного агрегатора без года — в сортировке не используется",
     "the site returned 403; HQ and headcount are from reference pages in search results; revenue comes from one aggregator with no year and is not used in sorting")

setf("mri-software", "последний_раунд", "частная компания: владельцы TA Associates, GI Partners, Harvest Partners; в сентябре 2025 сообщалось о продаже или IPO с оценкой до $10 млрд с учётом долга", "round",
     "private company owned by TA Associates, GI Partners, Harvest Partners; in September 2025 a sale or IPO at up to $10B including debt was reported")
setf("mri-software", "выручка", "около $1 млрд в год, EBITDA около $400 млн — по сообщению Private Equity Wire от 30.09.2025; компанией не раскрыта", "revenue",
     "about $1B a year, EBITDA about $400M — per Private Equity Wire, 30.09.2025; not disclosed by the company")
src("mri-software", "https://www.privateequitywire.co.uk/pe-backers-eye-10bn-mri-software-exit-via-sale-or-ipo/")
ver("mri-software", V1, V1E)
note("mri-software", "выручка и владельцы — по сообщению отраслевого издания (открыто), со ссылкой на источники; сумма и состав — не отчётность компании",
     "revenue and owners are from a trade publication (opened), citing sources; the figures are not company reporting")

# ---- group column ----
GROUPS = {
    "Nemetschek": ["nemetschek", "bluebeam"],
    "Hilti": ["hilti", "fieldwire-hilti", "4ps"],
    "Schneider Electric": ["rib-schneider", "rib-spain-presto", "costx", "candy", "planon"],
    "Cegid": ["cegid-menfis", "sigrid"],
    "OpenSpace": ["openspace", "disperse"],
}
for g, ids in GROUPS.items():
    for i in ids:
        by[i]["группа"] = g
        print("group", g, "<-", i, by[i]["компания"])

registry.write(rows)
out = ROOT / "knowledge" / "companies" / "i18n" / "en_part9b.tsv"
lines = ["\t".join(x) for x in en] + ["*\t" + k + "\t" + a + "\t" + b for k, a, b in star]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("rows", len(rows), "en", len(en), "star", len(star))
