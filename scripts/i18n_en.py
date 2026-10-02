"""Russian -> English helpers for the market map.

Static dictionaries (stages, types, roles, countries, layers) plus a phrase-based translator for short
data strings (rounds, funding, size, revenue, founding year). Free text that the phrase translator cannot
fully convert is covered by knowledge/companies/registry_en.csv (per-id overrides, filled by hand).
"""
import re

KIND_EN = {
    "product": "product", "vendor": "major vendor", "builder": "builder or developer",
    "services": "services, consulting, education",
}
STAGES_EN = {
    "S0": "Strategy, sites, feasibility", "S1": "Deal and financing", "S2": "Surveys",
    "S3": "Design", "S4": "Permits", "S5": "Tenders and procurement", "S6": "Construction",
    "S7": "Handover", "S8a": "Operations", "S8b": "Leasing and sales", "S9": "Renovation and retrofit",
}
COUNTRY_EN = {
    "Австрия": "Austria", "Великобритания": "United Kingdom", "Германия": "Germany", "Дания": "Denmark",
    "Израиль": "Israel", "Индия": "India", "Ирландия": "Ireland", "Испания": "Spain", "Канада": "Canada",
    "Люксембург": "Luxembourg", "Лихтенштейн": "Liechtenstein", "Нидерланды": "Netherlands", "ОАЭ": "UAE", "Португалия": "Portugal",
    "США": "USA", "Словения": "Slovenia", "Франция": "France", "Швейцария": "Switzerland", "Швеция": "Sweden",
    "Япония": "Japan", "н/д": "n/a",
}
REGION_EN = {
    "США": "USA", "Великобритания": "United Kingdom", "Нидерланды": "Netherlands", "Испания": "Spain",
    "Другая Европа": "Other Europe", "Вне США и Европы": "Outside USA and Europe", "Не определён": "Unknown",
}
ROLE_EN = {
    "субподрядчик": "subcontractor", "генподрядчик": "general contractor", "проектировщик": "designer",
    "застройщик": "developer", "н/д": "n/a", "инвестор/собственник": "investor / owner",
    "управляющая компания": "property manager", "муниципалитеты": "municipalities",
    "муниципалитет": "municipality",
    "корпоративные заказчики и застройщики (частная проверка планов)": "corporate clients and developers (private plan review)",
    "дистрибьютор/производитель": "distributor / manufacturer", "подрядчик": "contractor", "страховщик": "insurer",
    "кредитор": "lender", "собственник": "owner", "владелец инфраструктуры": "infrastructure owner",
    "домостроитель": "homebuilder", "жилищная организация": "housing association",
    "институциональный инвестор": "institutional investor", "производитель материалов": "materials manufacturer",
    "генподрядчик (капитальные проекты)": "general contractor (capital projects)",
    "промышленный строитель": "industrial builder", "генподрядчик (крупный)": "general contractor (large)",
    "субподрядчик (малый и средний)": "subcontractor (small and mid-size)",
    "подрядчик по инженерным системам": "MEP contractor",
    "генподрядчик (капитальные проекты)": "general contractor (capital projects)",
    "производитель материалов": "materials manufacturer",
    "сметчик": "quantity surveyor", "подрядчик по гражданскому строительству": "civil engineering contractor",
}
LAYER_EN = {
    "данные": "data", "финансы и страхование": "finance and insurance", "комплаенс": "compliance",
    "образование": "education",
}
TYPE_EN = {
    "продукт": "product", "продукт (аппаратное устройство)": "product (hardware)", "крупный вендор": "major vendor",
    "консалтинг/инжиниринг": "consulting / engineering", "кастомная разработка": "custom development",
    "кастомная разработка (инженерные расчёты)": "custom development (engineering calculations)",
    "строитель/застройщик": "builder / developer", "образование": "education",
}

# order matters: longer phrases first
PHRASES = [
    (r"не раскрыта компанией", "not disclosed by the company"), (r"не раскрыта", "not disclosed"),
    (r"оценка агрегатора Latka", "Latka aggregator estimate"), (r"оценка агрегатора", "aggregator estimate"),
    (r"оценки расходятся", "estimates differ"), (r"источники расходятся", "sources differ"),
    (r"по агрегатору", "per aggregator"), (r"агрегаторы", "aggregators"), (r"агрегатор", "aggregator"),
    (r"предпосевной раунд", "pre-seed round"), (r"Предпосевной раунд", "Pre-seed round"),
    (r"посевной раунд", "seed round"), (r"Посевной раунд", "Seed round"),
    (r"публичная компания", "public company"), (r"частная компания", "private company"),
    (r"\(ведущий инвестор ", "(led by "), (r"\(лид ", "(led by "),
    (r"за финансовый (\d{4}) год", r"for fiscal \1"), (r"за (\d{4})", r"for \1"),
    (r"более ", "over "), (r"около ", "about "), (r"сотрудников", "employees"), (r"штатный сотрудник", "employees"),
    (r"в июле", "in July"), (r"слабая оценка", "weak estimate"),
    (r"млрд", "B"), (r"млн", "M"), (r"тыс\.", "K"),
    (r"н/д", "n/a"), (r"\bдата не подтверждена\b", "date not confirmed"),
    (r"\bиз них\b", "of which"), (r"\bи\b", "and"), (r"\bпо\b", "per"), (r"\bдо\b", "up to"),
    (r"янв\.", "Jan"), (r"фев\.", "Feb"), (r"мар\.", "Mar"), (r"апр\.", "Apr"), (r"июнь", "June"),
    (r"июль", "July"), (r"авг\.", "Aug"), (r"сент\.", "Sep"), (r"окт\.", "Oct"), (r"нояб\.", "Nov"), (r"дек\.", "Dec"),
]


def tr_num(s):
    s = re.sub(r"(\d) (\d{3})", r"\1,\2", s)
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    return s


def phrase(s):
    out = s
    for pat, rep in PHRASES:
        out = re.sub(pat, rep, out)
    return tr_num(out)


def has_cyr(s):
    return bool(re.search(r"[А-Яа-яЁё]", s or ""))
