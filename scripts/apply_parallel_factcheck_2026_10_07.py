"""One-off (2026-10-07): apply the corrections of the Parallel `pro` fact-check reports to registry.csv.

Source reports: landscapes/construction-tech/2_collection/raw/parallel-factcheck-{US-1,US-2,EU-1,EU-3}-pro.md,
parallel-factcheck2-disputes.md and (for three founding years) parallel-factcheck-EU-2-pro.md.
Only values that a report ties to a primary page are applied; values it could not decide stay as they were or
become н/д / "не подтверждено". Cells whose old value was an aggregator number the report could not support are
replaced by н/д with the old number kept in the note.
English overrides go to knowledge/companies/i18n/en_part9d.tsv. Run once on a clean registry.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

D = "07.10.2026"
V = "частично: часть полей сверена с первоисточниками " + D + " (Parallel, источники — в списке); остальное — агрегаторы"
VE = "partial: some fields checked against primary sources on " + D + " (Parallel, sources listed); the rest from aggregators"

rows = registry.read(registry.CSV_PATH)
by = {r["id"]: r for r in rows}
per_id, _ = bm.load_en()
en, star = [], []
touched = set()


def cur_en(cid, key):
    for i, k, t in reversed(en):
        if i == cid and k == key:
            return t
    return per_id.get((cid, key), "")


def E(cid, field, ru, key=None, en_txt=None):
    by[cid][field] = ru
    if key:
        en.append((cid, key, en_txt if en_txt is not None else "n/a"))
    touched.add(cid)


def note(cid, ru, en_txt, urls=()):
    r = by[cid]
    r["примечание"] = (r["примечание"] + " | " if r["примечание"] else "") + "сверка Parallel " + D + ": " + ru
    old = cur_en(cid, "note")
    en.append((cid, "note", (old + " | " if old else "") + "Parallel check " + D + ": " + en_txt))
    have = r["источники_данных"].split()
    for u in urls:
        if u not in have:
            have.append(u)
    r["источники_данных"] = " ".join(have)
    touched.add(cid)


# ---------------- US ----------------
E("alice-technologies", "год_основания", "2013 (по сообщению компании; связана с исследованиями Стэнфорда)", "founded", "2013 (company announcement; linked to Stanford research)")
E("alice-technologies", "последний_раунд", "Series B, $30 млн (ведущий инвестор Vanedge Capital), расширен: $13 млн акционерного капитала от Swire Properties плюс кредит Bridge Bank — вместе доступно $47 млн по Series B (2023)", "round",
  "Series B, $30M (led by Vanedge Capital), extended: $13M of equity from Swire Properties plus a Bridge Bank loan — $47M accessible under Series B in total (2023)")
E("alice-technologies", "привлечено", "н/д ($74,1 млн за 14 раундов — по агрегатору, первичным источником не подтверждено)", "raised", "n/a ($74.1M over 14 rounds is from an aggregator and not confirmed by a primary source)")
note("alice-technologies", "$47 млн включают банковский кредит и не являются только акционерным капиталом", "the $47M includes a bank loan and is not equity alone",
     ["https://blog.alicetechnologies.com/news/alice-extends-funding-series-b-round-to-access-new-capital"])

E("bluebeam", "последний_раунд", "куплена Nemetschek (сделка завершена 31.10.2014; цена около $100 млн)", "round", "acquired by Nemetschek (completed 31.10.2014; price about $100M)")
note("bluebeam", "покупка, а не раунд", "an acquisition, not a funding round", ["https://ir.nemetschek.com/en/news/nemetschek-successfully-concludes-acquisition-of-bluebeam-software/bfdb4bd8-9446-4650-b179-a171e5ba973f"])

E("built", "последний_раунд", "Series D, $125 млн, 30.09.2021 (ведущий инвестор TCV; также Goldman Sachs, Index Ventures); расширение $23,6 млн (июль 2022) первичным источником не подтверждено", "round",
  "Series D, $125M, 30.09.2021 (led by TCV; also Goldman Sachs, Index Ventures); the $23.6M extension (July 2022) is not confirmed by a primary source")
note("built", "раунд подтверждён сообщением компании; общая сумма $289,1 млн по агрегатору не подтверждена", "the round is confirmed by the company release; the $289.1M total from an aggregator is unconfirmed", ["https://getbuilt.com/series-d"])

E("cotality", "последний_раунд", "выкуплена Stone Point Capital и Insight Partners (сделка завершена 04.06.2021); переименована из CoreLogic в Cotality 25.03.2025", "round",
  "taken private by Stone Point Capital and Insight Partners (completed 04.06.2021); renamed from CoreLogic to Cotality on 25.03.2025")
note("cotality", "смена владельца, а не раунд", "a change of owner, not a round", ["https://www.stonepoint.com/news/stone-point-capital-and-insight-partners-complete-acquisition-of-corelogic"])

E("dealpath", "последний_раунд", "Series C, $43 млн, 08.09.2022 (ведущий инвестор Morgan Stanley Expansion Capital)", "round", "Series C, $43M, 08.09.2022 (led by Morgan Stanley Expansion Capital)")
note("dealpath", "дата раунда подтверждена сообщением компании; сумма «всего» не подтверждена", "the round date is confirmed by the company; the total raised is unconfirmed", ["https://www.dealpath.com/blog/series-c"])

E("dodge", "год_основания", "н/д (1891 — история предшественника Dodge Reports; текущая сеть образована слиянием Dodge Data & Analytics и The Blue Book в 2021)", "founded",
  "n/a (1891 is the history of the predecessor Dodge Reports; the current network was formed by the 2021 merger of Dodge Data & Analytics and The Blue Book)")
E("dodge", "последний_раунд", "частный капитал: Clearlake Capital и Symphony Technology Group; в ноябре 2024 — $100 млн нового капитала и продление долга", "round",
  "private equity: Clearlake Capital and Symphony Technology Group; in November 2024 — $100M of new capital and a debt extension")
note("dodge", "год основания 1891 — история предшественника, не текущего юрлица", "1891 is predecessor history, not the current entity's founding year",
     ["https://www.construction.com/dodge-construction-network-enters-next-phase-with-executive-leadership-changes-and-100-million-of-new-capital/"])

E("doxel", "год_основания", "2015 (по описанию инвестора: декабрь 2015; год регистрации не установлен)", "founded", "2015 (investor's account: December 2015; incorporation year not established)")

E("entrata", "последний_раунд", "миноритарная инвестиция Blackstone, $200 млн, 15.05.2025, оценка $4,3 млрд (компания не называет её Series D)", "round",
  "minority investment by Blackstone, $200M, 15.05.2025, valuation $4.3B (the company does not call it Series D)")
note("entrata", "миноритарная инвестиция, не покупка и не раунд с номером", "a minority investment, neither a takeover nor a numbered round", ["https://www.entrata.com/press/blackstone"])

E("fieldwire-hilti", "последний_раунд", "куплена Hilti: сделка объявлена 16.11.2021, цена около $300 млн (по сообщению)", "round", "acquired by Hilti: announced 16.11.2021, price about $300M (as reported)")
E("foundation-software", "последний_раунд", "куплена Thoma Bravo: о завершении сообщено 31.08.2020", "round", "acquired by Thoma Bravo: completion announced 31.08.2020")
note("foundation-software", "покупка частным фондом, а не раунд", "a buyout by a private equity firm, not a round",
     ["https://www.thomabravo.com/press-releases/thoma-bravo-announces-completion-of-strategic-growth-investment-in-foundation-software"])

E("hover", "последний_раунд", "Series D, $60 млн, 17.11.2020; более поздних раундов не подтверждено", "round", "Series D, $60M, 17.11.2020; no later round confirmed")
E("hover", "привлечено", "$147 млн на 17.11.2020 (по сообщению компании; текущая сумма не установлена)", "raised", "$147M as of 17.11.2020 (company statement; the current total is not established)")

E("ineight", "год_основания", "2014 (InEight; предшественник Hard Dollar — с 1989 года)", "founded", "2014 (InEight; its predecessor Hard Dollar dates from 1989)")
note("ineight", "Kiewit вложилась в Hard Dollar в 2012, купила её и в 2014 запустила InEight как дочернюю компанию", "Kiewit invested in Hard Dollar in 2012, bought it and launched InEight as a subsidiary in 2014")

E("keyway", "год_основания", "2021 (по сообщению компании; дата регистрации не установлена; в документе SEC указан штат Delaware)", "founded",
  "2021 (company statement; incorporation date not established; an SEC filing gives Delaware)")
E("keyway", "привлечено", "н/д (по сообщениям компании: seed $15 млн, Series A $25 млн, отдельно долговое финансирование более $100 млн)", "raised",
  "n/a (company statements: $15M seed, $25M Series A, and separately over $100M of debt financing)")

E("newforma", "последний_раунд", "частный капитал: портфельная компания Ethos Capital; приобретение объявлено 03.04.2023, цена не раскрыта", "round",
  "private equity: an Ethos Capital portfolio company; the acquisition was announced 03.04.2023, price not disclosed")

E("openspace", "последний_раунд", "Series D, $102 млн, и ещё $9 млн стратегического капитала (09.08.2022); более поздних раундов не подтверждено", "round",
  "Series D, $102M, plus $9M of strategic capital (09.08.2022); no later round confirmed")
E("openspace", "привлечено", "н/д ($111 млн по Series D с учётом расширения — сообщение компании; общая сумма не установлена)", "raised",
  "n/a ($111M under Series D including the extension — company statement; the total is not established)")

E("oracle-construction", "штаб_город", "н/д")
E("oracle-construction", "штаб_страна", "н/д")
note("oracle-construction", "штаб подразделения не установлен: штаб корпорации Oracle не приписывается ему", "the division's HQ is not established: the parent Oracle's HQ is not assigned to it")

E("parspec", "штаб_город", "San Mateo")
note("parspec", "San Mateo (Калифорния) — место из сообщения компании о Series A (08.07.2025); формальный штаб не установлен; заявлен рост выручки в 4 раза, сумма не раскрыта",
     "San Mateo (California) is the place given in the company's Series A release (08.07.2025); a formal HQ is not established; 4x revenue growth is claimed, the amount is not disclosed")

E("togal-ai", "последний_раунд", "pre-Series A (SAFE) $5 млн, март 2023, предельная оценка $50 млн (по прессе ведущий инвестор — Florida Funders)", "round",
  "pre-Series A (SAFE) $5M, March 2023, valuation cap $50M (per the press the lead investor is Florida Funders)")

E("vts", "последний_раунд", "Series E, более $125 млн, 06.09.2022 (ведущий инвестор CBRE); синдицированный кредит $150 млн был раньше — 03.03.2022", "round",
  "Series E, over $125M, 06.09.2022 (led by CBRE); the $150M syndicated debt facility came earlier — 03.03.2022")
note("vts", "CBRE — инвестор и клиент, а не покупатель", "CBRE is an investor and a customer, not an acquirer")

note("xpanner", "офисы в Santa Fe Springs (Калифорния) и Сеуле; единый штаб не установлен", "offices in Santa Fe Springs (California) and Seoul; a single HQ is not established", ["https://www.xpanner.com"] if False else [])

# disputes / young companies
E("1001-ai", "штаб_город", "н/д")
E("1001-ai", "штаб_страна", "н/д")
note("1001-ai", "в сообщении о Series A — Ближний Восток и Лондон; юрлицо 1001 AI LIMITED зарегистрировано 05.12.2025 в Англии и Уэльсе, зарегистрированный офис в Лондоне; фактический штаб не установлен (запись ранее: Сан-Франциско — не подтверждено)",
     "the Series A release says the Middle East and London; 1001 AI LIMITED was registered on 05.12.2025 in England and Wales with a registered office in London; the operational HQ is not established (the earlier San Francisco entry is unconfirmed)",
     ["https://find-and-update.company-information.service.gov.uk/company/16893514"])
E("archilabs", "штаб_город", "н/д")
E("archilabs", "штаб_страна", "н/д")
note("archilabs", "Houston (агрегатор) и San Francisco (страница Y Combinator) не подтверждены документами; юрлицо — ArchiLabs, Inc. (условия использования), штат регистрации не установлен",
     "Houston (aggregator) and San Francisco (a Y Combinator page) are not confirmed by documents; the legal entity is ArchiLabs, Inc. (terms of service), the state of registration is not established", ["https://app.archilabs.ai/tos.html"])
E("helonic", "штаб_город", "New York")
note("helonic", "New York — по странице Y Combinator (команда); юрлицо — Articulate AI, Inc. (после переименования из Articulate в Helonic); штат регистрации не установлен",
     "New York is from the Y Combinator page (the team); the legal entity is Articulate AI, Inc. (after the rename from Articulate to Helonic); the state of registration is not established", ["https://helonic.com/blog/articulate-rebrand-helonic"])
E("permitify", "штаб_город", "Salt Lake City")
E("permitify", "год_основания", "2025 (по странице Y Combinator; дата регистрации не установлена)", "founded", "2025 (per the Y Combinator page; incorporation date not established)")
note("permitify", "Salt Lake City — по странице Y Combinator; юрлицо — Permitify, Inc.; штат, дата и адрес регистрации не установлены (ранее: Сан-Франциско, 2024 — не подтверждено)",
     "Salt Lake City is from the Y Combinator page; the legal entity is Permitify, Inc.; the state, date and address of registration are not established (earlier: San Francisco, 2024 — unconfirmed)", ["https://www.permitify.com/privacy"])
E("fresco", "сайт", "fresco.build")
note("fresco", "операционный сайт — fresco.build (оценка Division 8, набор YC F24); fresco-ai.com не подтверждён", "the operating site is fresco.build (Division 8 estimating, YC F24 batch); fresco-ai.com is unconfirmed", ["https://fresco.build/blog/about-fresco"])

# ---------------- Europe ----------------
E("aridditive", "штаб_город", "Sant Vicenç dels Horts")
E("centric-leefomgeving", "последний_раунд", "холдинговые структуры Centric куплены нидерландским консорциумом во главе с Imker Capital Partners (объявлено 15.07.2024)", "round",
  "Centric's holding structures were bought by a Dutch consortium led by Imker Capital Partners (announced 15.07.2024)")
E("kraan", "последний_раунд", "куплена Nedvest Capital: сделка закрыта 08.08.2019", "round", "acquired by Nedvest Capital: the deal closed on 08.08.2019")
E("planon", "последний_раунд", "Schneider Electric подписала соглашение об увеличении доли до 80% (30.07.2024; с 2020 года — миноритарная доля); закрытие сделки не проверено", "round",
  "Schneider Electric signed an agreement to raise its stake to 80% (30.07.2024; a minority stake since 2020); closing not verified")
E("rated-power", "последний_раунд", "Series A, $6 млн (по сообщению компании; ведущий инвестор Seaya Ventures), 2021; позднее куплена Enverus (дата закрытия не установлена)", "round",
  "Series A, $6M (company announcement; led by Seaya Ventures), 2021; later acquired by Enverus (closing date not established)")
E("saalg", "последний_раунд", "€3,65 млн, 10.07.2023 (при участии Acciona и Европейской комиссии)", "round", "€3.65M, 10.07.2023 (with Acciona and the European Commission)")
E("spotr", "последний_раунд", "€4,5 млн, 23.01.2024 (ведущий инвестор EDF Pulse Ventures); посевной раунд €2,5 млн, 05.07.2021; название «Series A» в сообщении не подтверждено", "round",
  "€4.5M, 23.01.2024 (led by EDF Pulse Ventures); seed €2.5M, 05.07.2021; the 'Series A' label is not confirmed in the release")
E("arcus-global", "штаб_город", "Cambridge")
E("asite", "последний_раунд", "кредитная линия (первая очередь, обеспеченная) от AshGrove Capital, 2024, на рефинансирование и рост; сведений о капитале и владельцах нет", "round",
  "a senior secured credit facility from AshGrove Capital, 2024, for refinancing and growth; no information on equity or owners")
note("asite", "«самофинансирование» неверно: AshGrove — кредитор, не акционер; юрлицо ASITE SOLUTIONS LIMITED (04040122)", "'self-funded' is wrong: AshGrove is a creditor, not a shareholder; the legal entity is ASITE SOLUTIONS LIMITED (04040122)",
     ["https://www.ashgrovecap.com/asite", "https://find-and-update.company-information.service.gov.uk/company/04040122"])
E("causeway", "штаб_город", "Gerrards Cross")
E("causeway", "год_основания", "1999 (по данным компании); юрлицо зарегистрировано 09.02.2000", "founded", "1999 (company data); the legal entity was incorporated on 09.02.2000")
E("civica", "последний_раунд", "куплена Blackstone: сделка завершена 02.05.2024", "round", "acquired by Blackstone: completed 02.05.2024")
E("converge", "последний_раунд", "£17 млн, 21.05.2025 (ведущий инвестор ABN AMRO Sustainable Impact Fund); название «Series B» не подтверждено", "round",
  "£17M, 21.05.2025 (led by ABN AMRO Sustainable Impact Fund); the 'Series B' label is not confirmed")
E("evercam", "год_основания", "2013 (по истории компании)", "founded", "2013 (company history)")
E("evercam", "последний_раунд", "венчурный долг €5 млн от Salica Investments, 2025 (отдельно от акционерного раунда €8,9 млн, окт. 2022)", "round",
  "€5M venture debt from Salica Investments, 2025 (separate from the €8.9M equity round of Oct 2022)")
E("fenestrapro", "год_основания", "2012 (по сообщению основателей на сайте компании)", "founded", "2012 (founders' account on the company site)")
E("nbs", "последний_раунд", "в ноябре 2020 продана Byggfakta Group (с 01.10.2024 — Hubexo)", "round", "sold to Byggfakta Group in November 2020 (Hubexo since 01.10.2024)")
E("searchland", "последний_раунд", "посевной раунд £2,3 млн, 01.03.2023 (Fuel Ventures; сообщение компании)", "round", "seed round £2.3M, 01.03.2023 (Fuel Ventures; company announcement)")
E("searchland", "привлечено", "£2,3 млн (посевной раунд; сообщение компании)", "raised", "£2.3M (seed round; company announcement)")
E("q-bot", "последний_раунд", "£3,5 млн, сент. 2023 (ведущий инвестор EMV); позднее £350 тыс. акционерного капитала (27.06.2025) и конвертация займов £865 тыс.", "round",
  "£3.5M, Sep 2023 (led by EMV); later £350K of equity (27.06.2025) and conversion of £865K of loans")
E("revizto", "год_основания", "2012 (по сообщению компании; в реестре швейцарского юрлица не проверено)", "founded", "2012 (company statement; not checked in the Swiss commercial registry)")
E("sablono", "последний_раунд", "Series A, €5,3 млн, 27.05.2021 (ведущий инвестор Thomas Bachmaier, Bachmaier Invest GmbH; также High-Tech Gründerfonds, Hasso Plattner Ventures, Nemetschek Allplan)", "round",
  "Series A, €5.3M, 27.05.2021 (led by Thomas Bachmaier, Bachmaier Invest GmbH; also High-Tech Gründerfonds, Hasso Plattner Ventures, Nemetschek Allplan)")
E("zutec", "год_основания", "1998 (по хронологии компании; британское юрлицо ZUTEC INC. (UK) LIMITED зарегистрировано отдельно)", "founded", "1998 (company timeline; the UK entity ZUTEC INC. (UK) LIMITED was registered separately)")
E("casafari", "последний_раунд", "Series A $15 млн, расширен до $20 млн (стратегическая инвестиция Starwood Capital); отдельно $120 млн от инвесторов-покупателей недвижимости — не капитал компании", "round",
  "Series A $15M, extended to $20M (a strategic investment by Starwood Capital); separately a $120M mandate from property investors — not company capital")
E("casafari", "привлечено", "н/д ($30,3 млн за 4 раунда — по агрегатору; $120 млн не капитал компании)", "raised", "n/a ($30.3M over 4 rounds is from an aggregator; the $120M is not company capital)")

# verification status for every touched row that was only aggregator-checked
for cid in touched:
    v = by[cid]["данные_проверены"]
    if v.startswith("частично") and "Parallel" not in v and "первоисточник открыт" not in v and "сверена с первоисточник" not in v:
        by[cid]["данные_проверены"] = V
        star.append(("verified", V, VE))
    elif v.startswith("частично") and "07.10.2026" not in v and "Parallel" not in v:
        by[cid]["данные_проверены"] = V
        star.append(("verified", V, VE))

registry.write(rows)
out = ROOT / "knowledge" / "companies" / "i18n" / "en_part9d.tsv"
lines = ["\t".join(x) for x in en] + ["*\t" + k + "\t" + a + "\t" + b for k, a, b in star]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("touched", len(touched), "en", len(en), "star", len(star))
