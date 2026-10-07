"""One-off (2026-10-07): apply the checked comments of data/construction_saas_map_recheck_2026-10-07.md.

Every row change below rests on a page opened on 2026-10-06/07 or on the named URL from the re-check
(marked in the note when the page itself did not open). English overrides go to en_part9c.tsv.
Run once on a clean registry.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
import build_map as bm  # noqa: E402

D = "07.10.2026"
rows = registry.read(registry.CSV_PATH)
by = {r["id"]: r for r in rows}
per_id, _ = bm.load_en()
en, star = [], []


def cur_en(cid, key):
    for i, k, t in reversed(en):
        if i == cid and k == key:
            return t
    return per_id.get((cid, key), "")


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


def stages(cid, extra):
    cur = [s.strip() for s in by[cid]["этапы_дополнительные"].split(";") if s.strip()]
    for s in extra:
        if s not in cur and s != by[cid]["этапы_основные"]:
            cur.append(s)
    by[cid]["этапы_дополнительные"] = "; ".join(cur)


def note_add(cid, ru, en_txt):
    r = by[cid]
    r["примечание"] = (r["примечание"] + " | " if r["примечание"] else "") + "повторная проверка " + D + ": " + ru
    old = cur_en(cid, "note")
    en.append((cid, "note", (old + " | " if old else "") + "re-check " + D + ": " + en_txt))


def note_rep(cid, ru_old, ru_new, en_old, en_new):
    r = by[cid]
    if ru_old in r["примечание"]:
        r["примечание"] = r["примечание"].replace(ru_old, ru_new)
    else:
        print("RU note phrase not found:", cid, ru_old[:50])
    e = cur_en(cid, "note")
    if en_old in e:
        en.append((cid, "note", e.replace(en_old, en_new)))
    else:
        print("EN note phrase not found:", cid, en_old[:50])


def ver(cid, ru, en_txt):
    by[cid]["данные_проверены"] = ru
    star.append(("verified", ru, en_txt))


# R01 Idox: two different events
setf("idox", "последний_раунд",
     "куплена Long Path Partners через Frankel UK Bidco: о завершении приобретения сообщено 05–06.05.2026 (£339,5 млн по полностью разводнённому капиталу); отмена допуска к торгам на AIM — с 29.05.2026",
     "round", "acquired by Long Path Partners via Frankel UK Bidco: completion reported on 05–06.05.2026 (£339.5M on a fully diluted equity basis); admission to trading on AIM cancelled from 29.05.2026")
src("idox", "https://uk.advfn.com/stock-market/london/idox-IDOX/share-news/AIM-Cancellation-IDOX-Plc/98631386")
note_add("idox", "дата делистинга уточнена: сообщение о завершении приобретения и отмена торгов на AIM — разные события; дата отмены (29.05.2026) — по уведомлению AIM/RNS (страница ADVFN не открылась, 403; дата подтверждена выдачей поиска по сообщениям Idox о предстоящей отмене)",
         "the delisting date is clarified: the completion announcement and the AIM cancellation are separate events; the cancellation date (29.05.2026) is from the AIM/RNS notice (the ADVFN page returned 403; the date is supported by search results quoting Idox's notices of the planned cancellation)")

# R03 Planon: 17 countries with own offices, not 17 offices
setf("planon", "рынки_цель", "около 3 750 клиентов в 40 странах; собственные офисы в 17 странах — по заявлению компании", "markets",
     "about 3,750 clients in 40 countries; own offices in 17 countries — company claim")

# nPlan: markets beyond the HQ country
setf("nplan", "рынки_цель", "Великобритания (HS2, Network Rail, Anglian Water), Австралия (North East Link, A$11 млрд), Гонконг (MTR), Саудовская Аравия (NEOM) — по сообщениям компании", "markets",
     "UK (HS2, Network Rail, Anglian Water), Australia (North East Link, A$11B), Hong Kong (MTR), Saudi Arabia (NEOM) — per company releases")
setf("nplan", "рынки_коды", "UK; OTHER")
setf("nplan", "рынки_основание", "текст")
src("nplan", "https://www.nplan.io/press-releases/nplan-raises-16m-series-b-to-scale-its-ai-led-transformation-of-capital-project-delivery",
    "https://www.nplan.io/press-releases/spark-nel-ignites-ai-partnership-with-nplan-to-assure-and-de-risk-victorias-largest-highways-project")
note_add("nplan", "рынки расширены по двум сообщениям компании (открыты): Series B от 17.10.2025 и проект North East Link в Виктории от 09.12.2025",
         "markets widened from two company releases (opened): the Series B of 17.10.2025 and the North East Link project in Victoria of 09.12.2025")

# Madaster: design stage
stages("madaster", ["S3"])
src("madaster", "https://docs.madaster.com/no/en/knowledge-base/tendering.html")
note_add("madaster", "добавлен S3: в документации (открыта) паспорт здания создаёт проектная команда на стадии проектирования, по модели BIM или шаблону Excel",
         "S3 added: the documentation (opened) says the design team creates the building passport at the design stage, from a BIM model or an Excel template")

# Yardi: the official pages, as listed in the re-check (pages themselves returned 403 to me)
stages("yardi", ["S5", "S6"])
setf("yardi", "размер_сотрудников", "более 9 000 специалистов (по странице компании, как указано в повторной проверке)", "size",
     "over 9,000 professionals (company page, as stated in the re-check)")
setf("yardi", "рынки_цель", "региональные предложения на сайте компании: США, Великобритания, Нидерланды, другие страны; более 40 офисов", "markets",
     "regional offerings on the company site: US, UK, Netherlands, other countries; over 40 offices")
setf("yardi", "рынки_коды", "US; UK; NL; EU; OTHER")
setf("yardi", "рынки_основание", "широкий охват")
setf("yardi", "год_основания", "1984 (по странице компании, как указано в повторной проверке)", "founded", "1984 (company page, as stated in the re-check)")
src("yardi", "https://www.yardi.com/company/about-us/", "https://www.yardi.com/product/construction-manager/")
note_rep("yardi", "сайт не открылся (403); штаб и штат — по справочникам в выдаче поиска; выручка из одного агрегатора без года — в сортировке не используется",
         "страницы yardi.com не открылись у меня (403); данные об основании, штате, офисах и функциях Construction Manager (тендеры, договоры, стоимость, ход строительства — S5, S6) приведены по повторной проверке с этими ссылками; выручка из одного агрегатора без года — в сортировке не используется",
         "the site returned 403; HQ and headcount are from reference pages in search results; revenue comes from one aggregator with no year and is not used in sorting",
         "the yardi.com pages returned 403 to me; the founding year, headcount, offices and Construction Manager functions (tenders, contracts, cost, progress — S5, S6) are as given in the re-check with these links; revenue comes from one aggregator with no year and is not used in sorting")
ver("yardi", "частично: страницы yardi.com не открылись (403), данные — по повторной проверке 07.10.2026 со ссылками; остальное — агрегаторы",
    "partial: the yardi.com pages returned 403, the data is from the 07.10.2026 re-check with links; the rest from aggregators")

# editorial
note_rep("fieldwire-hilti", "добавлено; принадлежность проверить | ", "добавлено | ",
         "1M+ projects in 100 countries (company claim) | correction", "1M+ projects in 100 countries (company claim); ownership confirmed (Hilti, 2021) | correction")
note_rep("skyciv", "регистрация — Австралия по номеру ABN в подвале сайта; штаб не подтверждён", "регистрация — Австралия по номеру ABN в подвале сайта (офисы Сидней и Чикаго — по странице компании; офисы сами по себе штаб не доказывают)",
         "registered in Australia per the ABN in the site footer; HQ not confirmed",
         "registered in Australia per the ABN in the site footer (offices in Sydney and Chicago per the company page; offices alone do not prove the HQ)")
note_rep("costx", "по обзорам — широко известна среди британских сметчиков; владелец и финансы не найдены", "по обзорам — широко известна среди британских сметчиков; принадлежит RIB; финансы не найдены",
         "per reviews, widely known among UK quantity surveyors; owner and finances not found",
         "per reviews, widely known among UK quantity surveyors; owned by RIB; finances not found")

registry.write(rows)
out = ROOT / "knowledge" / "companies" / "i18n" / "en_part9c.tsv"
lines = ["\t".join(x) for x in en] + ["*\t" + k + "\t" + a + "\t" + b for k, a, b in star]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("rows", len(rows), "en", len(en), "star", len(star))
