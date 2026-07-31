# Research Plan

> **Zone:** 2_engine (machine-led, Claude Code generates this)
> **When to fill:** at the start of the engine zone, after the frame zone is complete.
> **Purpose:** make collection reproducible, source choices explicit, and budget bounded.

---

## Mode

<!-- lean: minimize Parallel queries, prefer Apify + web_fetch + web_search.
            Single data collection, dual adversarial read at the interpretation layer.
     full: separate collection passes for pro and skeptic optics. Roughly 2x cost. -->

Mode: lean

## Tooling note (this run)

Изначально Parallel.ai/Apify выглядели недоступны (не было MCP-подключения). По указанию фаундера скилл `skills/parallel-research.skill` был проверен и починен (был написан под Claude Cloud с путями `/home/claude/...` и push в чужой GitHub-репозиторий — адаптирован под Windows/Git Bash и под конвенцию этого репозитория: сохранение прямо в `collection/raw/`, без git push). После починки Parallel.ai реально использован — 2 запроса (`processor: pro`) выполнены и сохранены в `collection/raw/competitive_calculators.md` и `collection/raw/audience_and_voc.md`. Apify не использовался в этом прогоне (не требовался под lean-режим этой гипотезы). Wordstat/Keys.so по-прежнему недоступны напрямую — количественный поисковый объём (Q1) остаётся gap, см. Out of scope.

## Budget cap

Target: $50 (lean, 2-3 больших запроса)
Hard ceiling: $50
Фактически потрачено: 2 запроса × processor "pro" (оценка $15-30 каждый по таблице скилла — точная стоимость не возвращается API синхронно, нужно свериться в биллинге Parallel.ai)

## Questions to answer

<!-- Pulled directly from 04_devils_advocate.md → "Questions the engine zone MUST answer". -->

1. ~~Существует ли измеримый ненулевой поисковый спрос по каждой из 4 тем — и насколько он сопоставим с ВТ?~~ **Отвечено (Wordstat):** да, у всех — эвакуация 1718/мес, ВТ 1494/мес, санузлы (новая тема) 574/мес, водоподготовка 121/мес, условные блюда 71/мес. Эвакуация оказалась выше ВТ, а не сопоставима с ним "снизу" — важный пересмотр приоритета.
2. Кто на практике выполняет каждый из 4 расчётов — архитектор/технолог общего профиля или узкий специалист/аутсорс?
3. Есть ли у производителей лифтов (Otis, KONE, отечественные) свои бесплатные калькуляторы подбора, обесценивающие УТП ВТ-калькулятора?
4. Куда уходит трафик калькулятора дальше — доходит ли до остальной части сайта/ИИ-ассистента (риск S1 из 02_assumptions)?
5. Какой реалистичный SEO-ramp ожидать для только что запущенного домена по этим узким темам?

---

## Sources by category

### Competitive landscape

| Question | Source | Tool | Estimated cost |
|----------|--------|------|----------------|
| Q1, Q3 | Конкурентная карта по всем 4 калькуляторам + производители лифтов + SvodPro-позиционирование | Parallel.ai (processor: pro) — см. `collection/raw/competitive_calculators.md` | ~$15-30 |

### Market structure & sizing

| Question | Source | Tool | Estimated cost |
|----------|--------|------|----------------|
| Q2, Q5 | Роли/практика расчётов, оценка численности проектных кадров, статус пересмотра норм | Parallel.ai (processor: pro) — см. `collection/raw/audience_and_voc.md` | ~$15-30 |
| — | Домейн-возраст и текущее SEO-присутствие svodpro.ru (для оценки ramp, Q5) | web_fetch на svodpro.ru | $0 — выполнено при подготовке 1_frame |

### Voice of customer & signals

| Question | Source | Tool | Estimated cost |
|----------|--------|------|----------------|
| Q2, Q4 | Форумы dwg.ru, АВОК — упоминания ручного счёта/пересчёта, ролей | включено в тот же Parallel-запрос (marketing) выше | included above |
| Q4 | Поведенческий сигнал недоступен без аналитики сайта — помечено как gap, требует данных фаундера (Я.Метрика/GA) | N/A — запрос к фаундеру | $0 |

### Trends, regulatory, technological context

| Question | Source | Tool | Estimated cost |
|----------|--------|------|----------------|
| M2 (02_assumptions) | Статус пересмотра ГОСТ/СП 267.1325800, СП 1.13130, СанПиН — покрыто тем же Parallel-запросом | included above | included above |

---

## External tool tasks — for approval before running

**Ретроактивная запись.** Этот раздел появился в шаблоне после того, как оба запроса ниже уже были выполнены — фаундер не видел их точный текст до запуска. Это процессный пробел этого прогона, зафиксирован честно, не задним числом отредактирован под вид согласования. Начиная со следующего запроса в этой гипотезе — согласование обязательно до статуса «выполнено».

| # | Инструмент | Точный текст задания | Статус |
|---|-----------|----------------------|--------|
| 1 | Parallel.ai (pro) | Конкурентный анализ по 4 калькуляторам + производители лифтов + позиционирование SvodPro (полный текст ниже) | выполнено (без предварительного согласования) |
| 2 | Parallel.ai (pro) | Роли/практика расчётов, численность проектных кадров, статус пересмотра норм (полный текст ниже) | выполнено (без предварительного согласования) |
| 3 | Wordstat | 5 фраз: «расчет лифтов», «расчет эвакуации», «расчет санузлов», «расчет условных блюд», «расчет водоподготовки» — все регионы | выполнено (фаундер запустил сам вручную, согласование не требовалось) |

**Задание #1, полный текст (на английском — так был сформулирован промпт для Parallel):**

> Conduct a comprehensive competitive analysis for: free and paid online calculators used by Russian architects and engineers for four specific building-code calculations under Russian norms (ГОСТ/СП): (1) vertical transportation sizing — number and capacity of elevators/escalators per ГОСТ Р 55964 and СП 267.1325800, including any tool from "Крупт" (Krupt), and whether elevator manufacturers (Otis, KONE, and domestic manufacturers such as Щербинский завод, Карачаровский механический завод, Могилевлифтмаш) offer free online elevator selection/sizing calculators tied to their product catalogs for the Russian market; (2) evacuation route throughput capacity calculations for fire safety compliance (расчет пропускной способности путей эвакуации); (3) "условные блюда" (standardized dish count) calculations for catering facility design per SanPiN/SP norms; (4) swimming pool water treatment (водоподготовка бассейна) calculations per Russian norms.
>
> Cover: key players/tools per calculation type, whether each is free or paid, what functionality each offers (does it just compute values, or also help select specific equipment/models), positioning approach (calculator-only tool vs full engineering platform vs manufacturer sales tool vs professional forum-shared spreadsheet), and any gaps where no good calculator currently exists online in Russian for a given topic. Also identify the company "svodpro" (svodpro.ru) — an AI assistant for navigating Russian СП/ГОСТ construction norms — and note whether it or comparable AI-assistant-for-norms products already offer any of these calculators.
>
> Include a summary comparison table by calculation type (columns: topic, known tools/competitors, free/paid, does it select equipment or just calculate, apparent gap). Output as a structured markdown report with inline citations. Write the report in Russian.

**Задание #2, полный текст:**

> Research the professional practice of Russian building design engineers (архитекторы, технологи, инженеры-проектировщики) regarding four specific calculation tasks under Russian construction norms (СП/ГОСТ): vertical transportation (lift/escalator) sizing per СП 267.1325800 and ГОСТ Р 55964, evacuation route throughput capacity for fire safety, standardized dish count (условные блюда) for catering facility design, and swimming pool water treatment (водоподготовка) sizing.
>
> Cover:
> (a) Which professional role typically performs each calculation inside a Russian design institute or bureau — is it done by general architects/technologists themselves, or handed off to specialized consultants, subcontractors, or equipment suppliers? Look for evidence in professional forums, job descriptions, or industry articles.
> (b) Any evidence in Russian professional forums, Telegram channels, or industry communities (e.g. АВОК, форумы проектировщиков, форумы архитекторов) of discussion, complaints, or requests related to: repeated recalculation when client requirements change, manual Excel-based calculation workflows for these tasks, or demand for online calculator tools for any of these specific topics.
> (c) A rough estimate, from official Russian statistics (Росстат) or industry sources, of how many practicing architects and technologists work in Russia today, and any data or informed estimates on what share of them personally perform this kind of technical/regulatory calculation versus outsourcing or not encountering it at all.
> (d) Whether any of the underlying norms (СП 267.1325800, evacuation capacity norms in СП 1.13130 or similar, SanPiN catering norms, pool water treatment norms in СП 31-113 or similar) are scheduled for revision or update in the near term (this year or next).
>
> Output as a structured markdown report with inline citations, in Russian.

---

## Out of scope

- ~~Точные цифры поисковой частотности (Wordstat/Keys.so/Ahrefs)~~ — **закрыто**: фаундер прогнал Wordstat вручную по всем 4 исходным темам + 1 новому кандидату («расчёт санузлов»), см. `collection/raw/wordstat_search_volume.md` и обновлённый `collection/market.md`. Keys.so/Ahrefs (позиции в выдаче, а не только показы) по-прежнему не собраны — остаётся мелким остаточным gap.
- Полная конкурентная карта производителей лифтов вне РФ — фокус только на игроках, реально присутствующих на российском рынке.
- Ценообразование конкурентов/подписки svodpro — не относится напрямую к вопросам из 04_devils_advocate для этого прогона.
- Интервью с реальными архитекторами/технологами — это отдельный шаг (interviews/), не часть этого collection-прохода.

---

## Adversarial read configuration

### Lean mode (default)

Single collection pass. Two independent Claude reads over the same corpus:
- `adversarial/supporting.md` — pro reading
- `adversarial/disconfirming.md` — skeptic reading
- `adversarial/symmetry_check.md` — meta-comparison

### Full mode

Each Parallel/Apify query is run twice with mirrored framing. Raw outputs are stored separately. Reads operate on different corpora.

Configuration for THIS hypothesis: lean, single collection pass — 2 Parallel.ai запроса (competitive + marketing/VoC, оба processor "pro"), затем два независимых Claude-прочтения (supporting/disconfirming) + symmetry_check.

---

## Re-run conditions

- ~~Появляется доступ к Wordstat~~ — **выполнено вручную фаундером в этом прогоне.** Остаточный gap — позиции в выдаче / Keys.so / Ahrefs, если понадобится точнее оценить SEO-ramp (Q5).
- Если фаундер решит серьёзно рассматривать «расчёт санузлов» как 5-ю тему — прогнать по ней отдельный конкурентный Parallel-запрос (сейчас есть только спрос, конкуренция не проверена).
- Производитель лифтов выпускает новый бесплатный калькулятор подбора — переоценить Q3.
- Фаундер получает данные веб-аналитики (Я.Метрика/GA) по первым неделям после публикации — заново протестировать Q4 (риск S1) на реальных данных, а не по прокси-сигналам.
- Обнаруживается информация о готовящемся пересмотре одной из используемых норм (ГОСТ/СП 267, СанПиН, СП по бассейнам) — переоценить M2.
