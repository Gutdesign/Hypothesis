"""One-off: apply the verified part of the 2026-10-06 fact-check to knowledge/companies/registry.csv.

Every change below was checked against the primary page named in knowledge/.../verification_log.md
(opened 2026-10-06) or is a downgrade of an unsourced value to н/д. English overrides go to
knowledge/companies/i18n/en_part9.tsv. Re-running is safe only on a clean registry (it appends notes).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

D = "06.10.2026"
V_PART = "частично: часть полей сверена с первоисточником " + D + " (по фактчеку), остальное — агрегаторы"
V_PART_EN = "partial: some fields checked against the primary source on " + D + " (per the fact-check), the rest from aggregators"
V_NONE = "не подтверждено: " + D + " первоисточник не открылся, запись по описанию в фактчеке"
V_NONE_EN = "unconfirmed: on " + D + " the primary source did not open; the record rests on the fact-check's description"
V_HIGHARC = "да: первоисточник открыт " + D + " (пресс-релиз о Series C)"
V_HIGHARC_EN = "yes: primary source opened on " + D + " (Series C press release)"

rows = registry.read(registry.CSV_PATH)
by = {r["id"]: r for r in rows}
per_id, _ = bm.load_en()
en_lines = []   # (id, field, text)
star = []       # (kind, ru, en)


def note(cid, ru, en):
    r = by[cid]
    r["примечание"] = (r["примечание"] + " | " if r["примечание"] else "") + "правка " + D + ": " + ru
    old_en = per_id.get((cid, "note"), "")
    en_lines.append((cid, "note", (old_en + " | " if old_en else "") + "correction " + D + ": " + en))


def setf(cid, field, ru, key=None, en=None):
    by[cid][field] = ru
    if key:
        en_lines.append((cid, key, en if en is not None else "n/a"))


def add_src(cid, *urls):
    r = by[cid]
    have = r["источники_данных"].split()
    for u in urls:
        if u not in have:
            have.append(u)
    r["источники_данных"] = " ".join(have)


def verified(cid, ru, en):
    by[cid]["данные_проверены"] = ru
    star.append(("verified", ru, en))


def stages(cid, extra):
    cur = [s.strip() for s in by[cid]["этапы_дополнительные"].split(";") if s.strip()]
    for s in extra:
        if s not in cur and s != by[cid]["этапы_основные"]:
            cur.append(s)
    by[cid]["этапы_дополнительные"] = "; ".join(cur)


# ---------- section 2: sourced corrections ----------
setf("idox", "последний_раунд",
     "куплена Long Path Partners (через Frankel UK Bidco): вывод с биржи завершён 05.05.2026, £339,5 млн по полностью разводнённому капиталу",
     "round", "acquired by Long Path Partners (via Frankel UK Bidco): take-private completed 05.05.2026, £339.5M on a fully diluted equity basis")
add_src("idox", "https://www.idoxgroup.com/news/long-path-partners-completes-acquisition-of-idox/",
        "https://www.morningstar.com/news/pr-newswire/20260505ny50181/long-path-partners-completes-take-private-acquisition-of-idox-plc")
note("idox", "статус «публичная компания» устарел: сделка завершена 05.05.2026 (страница компании открыта; сумма и дата подтверждены сообщением и СМИ); выручка выше — за год до 31.10.2025, когда компания была публичной",
     "the 'public company' status is out of date: deal completed on 05.05.2026 (company page opened; amount and date confirmed by the release and the press); the revenue above is for the year to 31.10.2025, when it was still public")

setf("hqo", "последний_раунд", "Series D, более $50 млн, 18.10.2023 (ведущий инвестор Koch Real Estate Investments); более поздние раунды не искались",
     "round", "Series D, over $50M, 18.10.2023 (led by Koch Real Estate Investments); later rounds were not searched for")
setf("hqo", "привлечено", "более $200 млн на 18.10.2023 (заявление компании)", "raised", "over $200M as of 18.10.2023 (company statement)")
add_src("hqo", "https://www.hqo.com/fr/resources/releases/hqo-raises-over-50m-in-series-d-funding-to-revolutionize-the-real-estate-landscape/")
verified("hqo", V_PART, V_PART_EN)
note("hqo", "раунд и сумма — по сообщению компании, открыто " + D, "round and total — from the company release, opened " + D)

setf("autodesk", "подкатегория", "проектирование и управление стройкой (Revit, Autodesk Forma — ранее Construction Cloud)")
star.append(("sub", by["autodesk"]["подкатегория"], "design and construction management (Revit, Autodesk Forma, formerly Construction Cloud)"))
stages("autodesk", ["S0", "S5"])
add_src("autodesk", "https://adsknews.autodesk.com/en/news/autodesk-construction-cloud-is-now-autodesk-forma/")
note("autodesk", "Construction Cloud переименован в Autodesk Forma 24.03.2026 (сообщение компании открыто); S5 — по тендерному инструменту BuildingConnected в Forma (там же); S0 — Forma Site Design, страница не открылась (403), по фактчеку",
     "Construction Cloud was renamed Autodesk Forma on 24.03.2026 (company release opened); S5 from the BuildingConnected bidding tool in Forma (same release); S0 from Forma Site Design, page returned 403, per the fact-check")

setf("nemetschek", "подкатегория", "проектирование и работа с чертежами (Allplan, Graphisoft, Bluebeam); эксплуатация (Spacewell, Crem Solutions)")
star.append(("sub", by["nemetschek"]["подкатегория"], "design and drawing work (Allplan, Graphisoft, Bluebeam); operations (Spacewell, Crem Solutions)"))
stages("nemetschek", ["S8a"])
add_src("nemetschek", "https://www.nemetschek.com/en/solutions/manage-operate")
note("nemetschek", "добавлена эксплуатация: в портфеле «Manage & Operate» Spacewell и Crem Solutions (страница компании открыта)",
     "operations added: the 'Manage & Operate' portfolio lists Spacewell and Crem Solutions (company page opened)")

stages("oracle-construction", ["S0", "S8a"])
add_src("oracle-construction", "https://www.oracle.com/construction-engineering/primavera-unifier-project-controls-asset-management/")
note("oracle-construction", "S0 и S8a добавлены: Primavera Unifier — планирование капитальных проектов и управление объектами и активами (страницы Oracle в выдаче поиска; сама страница подразделения не открылась, 403)",
     "S0 and S8a added: Primavera Unifier covers capital planning and facilities and asset management (Oracle pages in search results; the division page itself returned 403)")

setf("fieldwire-hilti", "рынки_цель",
     "США и страны, для которых на сайте есть страница контактов: Великобритания, Испания, Нидерланды, другие страны Европы, Австралия, Канада, Новая Зеландия; 1 млн+ проектов в 100 странах — заявление компании",
     "markets", "US and countries with a contact page on the site: UK, Spain, Netherlands, other European countries, Australia, Canada, New Zealand; 1M+ projects in 100 countries — company claim")
setf("fieldwire-hilti", "рынки_коды", "US; UK; ES; NL; EU; OTHER")
setf("fieldwire-hilti", "рынки_основание", "текст")
add_src("fieldwire-hilti", "https://www.fieldwire.com/country-information/")
verified("fieldwire-hilti", V_PART, V_PART_EN)
note("fieldwire-hilti", "география расширена по странице компании со странами (открыта); страница контактов не равна платным клиентам в стране",
     "geography widened from the company's country page (opened); a contact page is not the same as paying customers in the country")

setf("dalux", "рынки_цель", "пользователи в более чем 147 странах (заявление компании)", "markets", "users in more than 147 countries (company claim)")
setf("dalux", "рынки_коды", "US; UK; ES; NL; EU; OTHER")
setf("dalux", "рынки_основание", "глобальная")
setf("dalux", "глобальная", "да")
setf("dalux", "размер_сотрудников", "более 750 (заявление компании, " + D + ")", "size", "over 750 (company statement, " + D + ")")
add_src("dalux", "https://www.dalux.com/about-dalux/")
verified("dalux", V_PART, V_PART_EN)
note("dalux", "охват и штат — по странице компании (открыта); пользователи в стране не равны платным клиентам; ARR выше — оценка агрегатора, не годовая выручка",
     "reach and headcount are from the company page (opened); users in a country are not paying customers; the ARR above is an aggregator estimate, not annual revenue")

setf("planon", "сайт", "planonsoftware.com")
setf("planon", "рынки_цель", "около 3 750 клиентов в 40 странах, 17 офисов (заявление компании)", "markets", "about 3,750 clients in 40 countries, 17 offices (company claim)")
setf("planon", "рынки_коды", "NL; EU; OTHER")
setf("planon", "рынки_основание", "широкий охват")
add_src("planon", "https://planonsoftware.com/uk/about-us/the-story-behind-planon/")
verified("planon", V_PART, V_PART_EN)
note("planon", "Нидерланды — место происхождения и штаб, не весь рынок; список стран не опубликован, страны вне NL не приписаны",
     "the Netherlands is the origin and HQ, not the whole market; no country list is published, so countries beyond NL are not assigned")

setf("revizto", "последний_раунд", "миноритарная (вторичная) инвестиция Summit Partners, 10.07.2024; сумма не раскрыта",
     "round", "minority (secondary) investment by Summit Partners, 10.07.2024; amount not disclosed")
setf("revizto", "рынки_цель", "по всему миру: более 2 500 клиентов, 260 000 пользователей (заявление компании); рост в Северной Америке и на Ближнем Востоке",
     "markets", "worldwide: over 2,500 customers, 260,000 users (company claim); growth in North America and the Middle East")
setf("revizto", "рынки_коды", "US; EU; OTHER")
setf("revizto", "рынки_основание", "широкий охват")
setf("revizto", "размер_сотрудников", "250 в 29 странах (заявление компании, 27.11.2025)", "size", "250 across 29 countries (company statement, 27.11.2025)")
add_src("revizto", "https://revizto.com/resources/newsroom/company-news/revizto-announces-minority-investment-from-summit-partners-to-continue-propelling-the-aeco-industry-forward",
        "https://revizto.com/resources/newsroom/company-news/revizto-reports-record-growth-middle-east-and-north-america-expansion")
verified("revizto", V_PART, V_PART_EN)
note("revizto", "штаб — Лозанна (Швейцария) по сообщению компании; рынки уточнены по двум сообщениям компании (открыты)",
     "HQ is Lausanne (Switzerland) per the company release; markets refined from two company releases (opened)")

# RIB products
by["costx"]["компания"] = "CostX (RIB)"
setf("costx", "сайт", "rib-software.com/en/rib-costx")
add_src("costx", "https://www.rib-software.com/en/rib-costx")
note("costx", "это продукт RIB (RIB CostX), не самостоятельная компания; сметы и обмеры, есть облачный вариант и локальные лицензии; Великобритания — подтверждённый рынок, не полный охват",
     "this is a RIB product (RIB CostX), not a standalone company; estimating and takeoff, with a cloud option and on-premise licences; the UK is a confirmed market, not the full reach")
by["candy"]["компания"] = "Candy (RIB)"
setf("candy", "сайт", "rib-software.com/en/rib-candy")
stages("candy", ["S6"])
add_src("candy", "https://www.rib-software.com/en/rib-candy")
verified("candy", V_PART, V_PART_EN)
note("candy", "принадлежит RIB Software GmbH и дочерним компаниям (страница открыта); охватывает обмеры и сметы, планирование и контроль проекта, поэтому добавлен S6",
     "owned by RIB Software GmbH and subsidiaries (page opened); covers takeoff and estimating, planning and project control, hence S6 added")

stages("buildertrend", ["S5"])
note("buildertrend", "S5 добавлен по фактчеку (сметы, тендеры, заказы поставщикам); сайт компании не открылся (403)",
     "S5 added per the fact-check (estimates, bids, purchase orders); the company site returned 403")

stages("zutec", ["S6", "S8a"])
add_src("zutec", "https://zutec.com/")
note("zutec", "добавлены S6 (среда общих данных, RFI, журнал, контроль качества и дефектов) и S8a (управление активами); основной S7 сохранён как редакторское решение; страница компании открыта",
     "S6 (CDE, RFI, site diary, QA and defects) and S8a (asset management) added; S7 kept as the main stage by editorial choice; company page opened")

setf("elecosoft", "выручка", "не раскрыта по бренду (по группе Eleco plc: £38,8 млн за 2025, ARR £34,3 млн на 31.12.2025 — это вся группа)",
     "revenue", "not disclosed for the brand (Eleco plc group: £38.8M for 2025, ARR £34.3M at 31.12.2025 — the whole group)")
add_src("elecosoft", "https://ir.eleco.com/regulatory/final-results-8/")
verified("elecosoft", V_PART, V_PART_EN)
note("elecosoft", "$35,4 млн агрегатора убраны: Elecosoft — один из брендов группы Eleco plc (с BestOutcome, Pemac, Kivue); отчёт компании от 28.04.2026 открыт",
     "the aggregator's $35.4M removed: Elecosoft is one brand of Eleco plc (with BestOutcome, Pemac, Kivue); the company report of 28.04.2026 was opened")

setf("4ps", "последний_раунд", "куплена Hilti: сделка объявлена в июле 2023, завершена 05.10.2023 после одобрения регуляторов",
     "round", "acquired by Hilti: announced in July 2023, completed on 05.10.2023 after regulatory approval")
add_src("4ps", "https://www.hilti.group/content/hilti/CP/XX/en/company/media-relations/media-releases/4ps_group_acquisition_erp_software_solutions_conclusion.html")
verified("4ps", V_PART, V_PART_EN)

by["cadac"]["компания"] = "Cadac Group (направление для органов власти, бывш. NedGraphics)"
setf("cadac", "сайт", "cadac.com")
add_src("cadac", "https://www.cadac.com/us/news/nedgraphics-becomes-cadac-group/")
note("cadac", "NedGraphics переименована в Cadac Group с 01.01.2022 (сообщение компании в выдаче поиска, страница не открывалась); карточка относится к направлению для органов власти, не ко всей группе",
     "NedGraphics was renamed Cadac Group on 01.01.2022 (company release in search results, page not opened); the card refers to the government line, not the whole group")

setf("roxit", "последний_раунд", "куплена Main Capital (2015), затем Visma: сообщение Visma от 11.02.2019",
     "round", "bought by Main Capital (2015), then Visma: Visma release dated 11.02.2019")
setf("roxit", "размер_сотрудников", "около 250 (на 11.02.2019, историческое значение)", "size", "about 250 (as of 11.02.2019, historical)")
add_src("roxit", "https://www.visma.com/newsroom/visma-acquires-roxit-group-046f861d")
verified("roxit", V_PART, V_PART_EN)

# 011h: builder
setf("011h", "тип_организации", "строитель/застройщик")
setf("011h", "размер_сотрудников", "н/д", "size")
setf("011h", "последний_раунд", "н/д", "round")
setf("011h", "привлечено", "н/д", "raised")
by["011h"]["источники_данных"] = "https://011h.com"
verified("011h", V_PART, V_PART_EN)
note("011h", "по официальному сайту — проектирование и строительство «под ключ»; цифровая платформа показана как внутренний инструмент, продажа ПО внешним клиентам не найдена; цифры Tracxn (штат, раунд, сумма) убраны — ссылки только на корень tracxn.com",
     "per the official site it is turnkey design and construction; the digital platform is presented as an internal tool, no sale of software to outside clients was found; the Tracxn figures (headcount, round, amount) removed — the sources were only the tracxn.com root")

setf("planx", "тип_организации", "продукт (государственный проект)")
note("planx", "продукт инициативы Open Digital Planning для органов власти, не коммерческая компания",
     "a product of the Open Digital Planning initiative for authorities, not a commercial company")

setf("greenlite", "тип_организации", "продукт + экспертная услуга")
setf("greenlite", "сайт", "greenlite.com")
setf("greenlite", "размер_сотрудников", "н/д (106 из прежних данных — без даты и отдельного источника)", "size")
by["greenlite"]["роль_клиента"] = "генподрядчик; муниципалитет"
add_src("greenlite", "https://greenlite.com/")
verified("greenlite", V_PART, V_PART_EN)
note("greenlite", "по сайту компании (открыт): две стороны — строители и строительные департаменты; услуги экспертов (управление разрешениями, частная проверка планов, проверка норм) плюс платформы Atlas и LiteTable",
     "per the company site (opened): two sides — builders and building departments; expert services (permit management, private plan review, code compliance) plus the Atlas and LiteTable platforms")

# ---------- section 3: downgrades ----------
setf("fresco", "последний_раунд", "н/д", "round")
setf("fresco", "привлечено", "н/д", "raised")
verified("fresco", V_PART, V_PART_EN)
note("fresco", "раунд $3,1 млн и сумма $3,5 млн убраны: страница Y Combinator (открыта) суммы не называет; те же цифры у Bild AI — возможное смешение двух компаний, не доказано",
     "the $3.1M round and $3.5M total removed: the Y Combinator page (opened) states no amount; the same figures belong to Bild AI — a possible mix-up of two companies, not proven")
setf("flowmanual", "последний_раунд", "участник Y Combinator (набор S26); сумма и условия финансирования не подтверждены", "round",
     "Y Combinator participant (S26 batch); amount and terms of funding not confirmed")
setf("flowmanual", "привлечено", "н/д", "raised")
setf("archilabs", "последний_раунд", "участник Y Combinator (по агрегатору, дек. 2024); сумма и условия финансирования не подтверждены", "round",
     "Y Combinator participant (per aggregator, Dec 2024); amount and terms of funding not confirmed")
setf("archilabs", "привлечено", "н/д", "raised")
setf("bouwconnect", "размер_сотрудников", "н/д", "size")
setf("bouwconnect", "выручка", "н/д", "revenue")
note("bouwconnect", "цифры агрегатора (1 сотрудник, около 83 тыс. без валюты) убраны как непригодные", "the aggregator's figures (1 employee, about 83K with no currency) removed as unusable")
verified("hoprin", V_NONE, V_NONE_EN)
note("hoprin", "сайт не прочитан автоматически; это не доказывает, что компании нет — запись не подтверждена", "the site could not be read automatically; this does not prove the company does not exist — the record is unconfirmed")

for cid in ("istram", "saalg", "aridditive"):
    for f, k in (("размер_сотрудников", "size"), ("последний_раунд", "round"), ("привлечено", "raised")):
        if "Tracxn" in by[cid][f]:
            setf(cid, f, "н/д", k)
    by[cid]["источники_данных"] = " ".join(u for u in by[cid]["источники_данных"].split() if u.rstrip("/") != "https://www.tracxn.com")
    note(cid, "цифры агрегатора Tracxn убраны: источник — только корень tracxn.com, без профиля компании или документа",
         "the Tracxn aggregator figures removed: the only source was the tracxn.com root, with no company profile or document")

# ---------- section 4: Higharc ----------
by["higharc"]["примечание"] = by["higharc"]["примечание"].replace("; Series C $95 млн (2026) не подтверждена первоисточником", "")
if ("higharc", "note") in per_id:
    per_id[("higharc", "note")] = per_id[("higharc", "note")].replace("; the Series C of $95M (2026) is not confirmed by a primary source", "")
add_src("higharc", "https://www.higharc.com/newsroom/higharc-95m-series-c-for-homebuilding-ai")
verified("higharc", V_HIGHARC, V_HIGHARC_EN)
note("higharc", "Series C $95 млн, 30.06.2026, Insight Partners, всего более $170 млн — подтверждено сообщением компании (открыто)",
     "Series C $95M, 30.06.2026, Insight Partners, total over $170M — confirmed by the company release (opened)")

# ---------- sites ----------
for cid, site, ru in [("openspace", "openspace.ai", ""), ("sablono", "sablono.com", ""), ("cmic", "cmicglobal.com", ""),
                      ("foundation-software", "foundationsoft.com", ""), ("dusty-robotics", "dustyrobotics.com", ""),
                      ("nbs", "thenbs.com", ""), ("ayesa", "ayesa.com", ""), ("ineco", "ineco.com", ""), ("dodge", "construction.com", "")]:
    if by[cid]["сайт"].strip() in ("", "н/д"):
        by[cid]["сайт"] = site

# ---------- new rows ----------
NEW = [
    dict(id="testfit", name="TestFit", site="testfit.io", st="S0", st2="S3; S5", role="застройщик; проектировщик",
         sub="поиск вариантов застройки участка и ТЭО", sub_en="site planning and feasibility analysis for real estate development",
         note="по сайту компании (открыт): генерация планов участка, парковок, финансовая модель; штаб на сайте не указан",
         note_en="per the company site (opened): site plan and parking generation, pro forma; HQ not stated on the site"),
    dict(id="skyciv", name="SkyCiv", site="skyciv.com", st="S3", st2="", role="проектировщик",
         sub="облачные расчёты строительных конструкций", sub_en="cloud structural analysis and design",
         note="по сайту компании (открыт): моделирование, анализ и проверка по нормам (AISC, EN, NDS, AS, CSA); регистрация — Австралия по номеру ABN в подвале сайта; штаб не подтверждён",
         note_en="per the company site (opened): modelling, analysis and code checks (AISC, EN, NDS, AS, CSA); registered in Australia per the ABN in the site footer; HQ not confirmed"),
    dict(id="nplan", name="nPlan", site="nplan.io", st="S6", st2="S5", role="генподрядчик; собственник",
         sub="прогноз рисков и срыва графика проекта", sub_en="schedule risk forecasting for projects",
         city="London", country="Великобритания", codes="UK", basis="штаб", layer="данные",
         note="по сайту компании (открыт): база более 750 000 графиков проектов (заявление компании); адрес в Лондоне",
         note_en="per the company site (opened): over 750,000 project schedules in the dataset (company claim); London address"),
    dict(id="one-click-lca", name="One Click LCA", site="oneclicklca.com", st="S3", st2="S0", role="проектировщик; производитель материалов",
         sub="оценка углеродного следа и жизненного цикла зданий, экологические декларации (EPD)", sub_en="whole-life carbon and lifecycle assessment of buildings, environmental product declarations (EPD)",
         layer="комплаенс", note="по сайту компании (открыт): 500 000+ наборов данных, 170+ стран (заявление компании); штаб на странице не указан",
         note_en="per the company site (opened): 500,000+ datasets, 170+ countries (company claim); HQ not stated on the page"),
    dict(id="madaster", name="Madaster", site="madaster.com", st="S7", st2="S8a; S9", role="собственник; проектировщик",
         sub="паспорта материалов здания и показатели циркулярности", sub_en="building material passports and circularity indicators",
         city="Amsterdam", country="Нидерланды", codes="NL; UK; EU", basis="текст", layer="данные",
         markets="Нидерланды, Бельгия, Германия, Австрия, Швейцария, Норвегия, Великобритания (по сайту компании)",
         markets_en="Netherlands, Belgium, Germany, Austria, Switzerland, Norway, UK (per the company site)",
         note="по сайту компании (открыт): паспорта материалов, углерод, соответствие таксономии ЕС",
         note_en="per the company site (opened): material passports, embodied carbon, EU taxonomy compliance"),
    dict(id="yardi", name="Yardi", site="yardi.com", st="S8a", st2="S8b", role="управляющая компания; собственник",
         sub="ПО для управления недвижимостью", sub_en="property management software",
         verified=V_NONE, verified_en=V_NONE_EN,
         note="сайт не открылся (403); назначение — по фактчеку; штаб, размер и финансы не искались",
         note_en="the site returned 403; the purpose is per the fact-check; HQ, size and finances were not searched"),
    dict(id="mri-software", name="MRI Software", site="mrisoftware.com", st="S8a", st2="S8b", role="управляющая компания; собственник",
         sub="ПО для управления недвижимостью и объектами, аренда и учёт", sub_en="real estate and facilities management software, leasing and accounting",
         city="Solon", country="США", codes="US; UK; ES; NL; EU; OTHER", basis="глобальная", glob="да",
         markets="более 170 стран, 45 000+ клиентов (заявление компании)", markets_en="170+ countries, 45,000+ clients (company claim)",
         note="по сайту компании (открыт): адрес — Solon, Огайо, США; охват — заявление компании",
         note_en="per the company site (opened): address — Solon, Ohio, US; reach is a company claim"),
]
fields = list(rows[0].keys())
for n in NEW:
    r = {k: "" for k in fields}
    r.update({
        "id": n["id"], "компания": n["name"], "сайт": n["site"], "список_источника": "добавлено (фактчек " + "2026-10-06" + ")",
        "тип_организации": "продукт", "профиль_по_списку": "н/д", "этапы_основные": n["st"], "этапы_дополнительные": n["st2"],
        "слой": n.get("layer", ""), "роль_клиента": n["role"], "подкатегория": n["sub"], "рынки_цель": n.get("markets", "н/д"),
        "рынки_коды": n.get("codes", ""), "рынки_основание": n.get("basis", "нет данных"), "глобальная": n.get("glob", ""),
        "штаб_город": n.get("city", "н/д"), "штаб_страна": n.get("country", "н/д"), "размер_сотрудников": "н/д",
        "последний_раунд": "н/д", "привлечено": "н/д", "год_основания": "н/д", "выручка": "не раскрыта",
        "источники_данных": "https://" + n["site"], "данные_проверены": n.get("verified", V_PART),
        "примечание": n["note"] + " | этапы — оценка по описанию",
    })
    rows.append(r)
    star.append(("sub", n["sub"], n["sub_en"]))
    star.append(("verified", r["данные_проверены"], n.get("verified_en", V_PART_EN)))
    en_lines.append((n["id"], "note", n["note_en"]))
    if "markets" in n:
        en_lines.append((n["id"], "markets", n["markets_en"]))

registry.write(rows)

out = I18N = ROOT / "knowledge" / "companies" / "i18n" / "en_part9.tsv"
lines = ["\t".join(x) for x in en_lines] + ["*\t" + k + "\t" + a + "\t" + b for k, a, b in star]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("rows:", len(rows), "en lines:", len(en_lines), "star:", len(star))
