# План сбора: ландшафт строительных технологий

> **Зона:** 2_collection (зона машины)
> **Оговорка:** рамка (`1_scope/scope.md`) пока в статусе «черновик». Первый проход выполнен по прямому поручению основателя до утверждения рамки; его результаты предварительные и пересматриваются, если основатель изменит этапы или границы.

## Режим

Mode: lean — бесплатные инструменты (web_search, web_fetch); платные запросы (Parallel) — только после вопросов основателя по итогам первого прохода.

## Бюджет

Потрачено: $0. Цель первого прохода: $0.

## Реестр

Главная таблица: `knowledge/companies/registry.csv` (читаемый вид: `registry.md`). Правило: размер, раунд, год основания, выручка — только со ссылкой в `источники_данных`, иначе `н/д`; выручка чаще всего `не раскрыта`.

## Проходы

| # | Проход | Инструмент | Результат | Статус |
|---|--------|-----------|-----------|--------|
| 1 | Объединение двух списков, дедупликация, кодирование этапов и ролей по описанию | вручную | 116 строк в реестре (затем +10 по решению «расширить», +21 топовые по рынкам, +9 местные игроки = 156) | выполнено |
| 2 | Обогащение: сайт, штаб, год основания, размер, раунд, выручка | web_search / web_fetch, партиями по ~10 компаний | поля реестра + источники | см. сводку этапа |
| 3 | Темпы роста отрасли по странам | web_search / web_fetch | `knowledge/markets/construction_growth.md` | выполнено, пробелы в файле |
| 4 | Сверка меток основателя и доменов «(проверить)» | web_fetch главной страницы | пометки в реестре | выполняется вместе с проходом 2 |

## Рыночные данные

Одна сопоставимая метрика: реальный годовой рост строительного выпуска (Euroconstruct; ONS для Великобритании; Евростат). США — расходы Census в текущих долларах, несопоставимы и помечены. Размер рынка в деньгах не оценивался (если понадобится — сверху вниз и снизу вверх, с разрывом).

## Внешние инструменты — на согласование

Первый проход платных или сторонних задач не содержит. Второй этап (2026-10-02): три задания для Parallel по региональной полноте (см. `regional_coverage.md`). Тексты — в файлах `.parallel/prompt_*.txt` (служебная папка вне git) и дословно в чате; в Parallel уходят только рыночные вопросы, данных гипотез и личных данных в них нет. Бюджет: цель $15–30 за три задания на процессоре `pro-fast`; потолок $50.

| # | Инструмент | Точный текст задания | Куда сохранить | Статус |
|---|-----------|----------------------|----------------|--------|
| 1 | Parallel, `pro-fast` | `.parallel/prompt_regional_es.txt`: карта поставщиков ПО для стройки в Испании (сметы, ERP, BIM, разрешения и лицензии, стартапы) | `2_collection/raw/parallel-es-vendors.md` | на согласовании |
| 2 | Parallel, `pro-fast` | `.parallel/prompt_permits_uk_nl.txt`: поставщики ПО для разрешений и строительного контроля в Великобритании и Нидерландах, обе стороны рынка | `2_collection/raw/parallel-permits-uk-nl.md` | на согласовании |
| 3 | Parallel, `pro-fast` | `.parallel/prompt_voc_es_uk_nl.txt`: голос покупателя о ПО для стройки в трёх странах (сметы, проверка проектов, разрешения, контроль хода) | `2_collection/raw/parallel-voc-es-uk-nl.md` | на согласовании |

<!-- Статусы: «на согласовании» → «одобрено» → «выполнено». Основатель сказал «запусти Parallel», но точный текст заданий ещё не видел: ждём подтверждения по правилу CLAUDE.md. -->

Тексты заданий дословно (для согласования):

**Задание 1** — карта поставщиков в Испании:
> Map the software and technology vendors that serve the construction industry in Spain. Use Spanish-language sources as well as English ones. For each vendor give: name, website, headquarters city, founding year, number of employees, ownership or funding (investors, rounds, amounts, dates), revenue if disclosed, which stage(s) of the building lifecycle it serves, who the customers are, and how widely it is used in Spain. Cover at least: (1) cost estimating, quantity measurement and price databases (Presto / RIB Spain, Arquimedes / CYPE, TCQ and BEDEC / ITeC, Menfis, others); (2) ERP and project management for contractors; (3) BIM, common data environments and design-review tools; (4) building permits and urban licences, including collaborating bodies (Entidades Colaboradoras Urbanisticas such as EQA), municipal digital-licence platforms (Madrid-DBP, Malaga's Check Digital Building Permit) and who supplies the software; (5) construction-monitoring, reality-capture and robotics startups and other funded Spanish ConTech startups. Separate facts from primary sources from vendor marketing claims, mark single-source claims as weak, note foreign ownership. Include a summary table and inline citations. Output as a structured markdown report.

**Задание 2** — разрешения в Великобритании и Нидерландах: полный текст в `.parallel/prompt_permits_uk_nl.txt`. Суть: обе стороны рынка (органы власти и заявители); Великобритания — Idox и конкуренты, Planning Portal, программа цифрового планирования, стартапы; Нидерланды — Omgevingswet и DSO, поставщики ПО для планов (Roxit, GISkit, xxllnc, Cadac), стартапы проверки норм (Struck); по каждому поставщику данные о компании, клиентах, структуре рынка, кто платит и длина цикла продаж; факты отделить от маркетинга.

**Задание 3** — голос покупателя: полный текст в `.parallel/prompt_voc_es_uk_nl.txt`. Суть: что сметчики, проектировщики, подрядчики и муниципальные проверяющие в трёх странах пишут о существующих программах (жалобы, чем заменяют, платят ли, как выбирают); источники — отзывы (G2, Capterra, Trustpilot), форумы, отчёты профессиональных объединений; по каждой находке ссылка, страна, профессия и оценка независимости; прямо сказать, где данных нет.

## Вне рамок первого прохода

- интервью и оценка боли со стороны покупателей;
- размер рынков программ для строительства в деньгах;
- Россия и СНГ;
- глубокие карточки отдельных компаний.
