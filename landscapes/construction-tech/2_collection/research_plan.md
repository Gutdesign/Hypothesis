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
| 1 | Объединение двух списков, дедупликация, кодирование этапов и ролей по описанию | вручную | 116 строк в реестре (затем +10 по решению «расширить», +21 топовые по рынкам, +9 местные игроки, +22 по отчётам Parallel = 178) | выполнено |
| 2 | Обогащение: сайт, штаб, год основания, размер, раунд, выручка | web_search / web_fetch, партиями по ~10 компаний | поля реестра + источники | см. сводку этапа |
| 3 | Темпы роста отрасли по странам | web_search / web_fetch | `knowledge/markets/construction_growth.md` | выполнено, пробелы в файле |
| 4 | Сверка меток основателя и доменов «(проверить)» | web_fetch главной страницы | пометки в реестре | выполняется вместе с проходом 2 |

## Рыночные данные

Одна сопоставимая метрика: реальный годовой рост строительного выпуска (Euroconstruct; ONS для Великобритании; Евростат). США — расходы Census в текущих долларах, несопоставимы и помечены. Размер рынка в деньгах не оценивался (если понадобится — сверху вниз и снизу вверх, с разрывом).

## Внешние инструменты — на согласование

Первый проход платных или сторонних задач не содержит. Второй этап (2026-10-02): три задания для Parallel по региональной полноте (см. `regional_coverage.md`). Тексты — в файлах `.parallel/prompt_*.txt` (служебная папка вне git) и дословно в чате; в Parallel уходят только рыночные вопросы, данных гипотез и личных данных в них нет. Бюджет: цель $15–30 за три задания на процессоре `pro-fast`; потолок $50.

| # | Инструмент | Точный текст задания | Куда сохранить | Статус |
|---|-----------|----------------------|----------------|--------|
| 1 | Parallel, `pro-fast` | `.parallel/prompt_regional_es.txt`: карта поставщиков ПО для стройки в Испании (сметы, ERP, BIM, разрешения и лицензии, стартапы) | `2_collection/raw/parallel-es-vendors.md` | выполнено 02.10.2026 (запущено после одобрения основателя: «Запусти Pro»; отчёт готов за 3–4 минуты по метке файла) |
| 2 | Parallel, `pro-fast` | `.parallel/prompt_permits_uk_nl.txt`: поставщики ПО для разрешений и строительного контроля в Великобритании и Нидерландах, обе стороны рынка | `2_collection/raw/parallel-permits-uk-nl.md` | выполнено 02.10.2026 (запущено после одобрения основателя: «Запусти Pro»; отчёт готов за 3–4 минуты по метке файла) |
| 3 | Parallel, `pro-fast` | `.parallel/prompt_voc_es_uk_nl.txt`: голос покупателя о ПО для стройки в трёх странах (сметы, проверка проектов, разрешения, контроль хода) | `2_collection/raw/parallel-voc-es-uk-nl.md` | выполнено 02.10.2026 (запущено после одобрения основателя: «Запусти Pro»; отчёт готов за 3–4 минуты по метке файла) |

| 4 | Parallel, `pro-fast` | `parallel_prompts/factcheck_US_1.txt`: сверка 24 американских программных компаний с первоисточниками (штаб, год, штат, раунд, выручка, владелец, суть продукта; поглощения, переименования, закрытия) | `2_collection/raw/parallel-factcheck-US-1.md` | выполнено 06.10.2026 как пробное (одобрено основателем: «запускай»; отчёт готов за 4 минуты); run_id trun_91c5025d20fc485a934ee233ef0efe6f; правки реестра по отчёту не внесены, ждут решения |
| 5 | Parallel, `pro-fast` | `parallel_prompts/factcheck_US_2.txt`: то же, ещё 24 американские компании | `2_collection/raw/parallel-factcheck-US-2.md` | на согласовании |
| 6 | Parallel, `pro-fast` | `parallel_prompts/factcheck_EU_1.txt`: то же, 31 компания вне США (Нидерланды, Испания: от 011h до Amrax) | `2_collection/raw/parallel-factcheck-EU-1.md` | на согласовании |
| 7 | Parallel, `pro-fast` | `parallel_prompts/factcheck_EU_2.txt`: то же, 31 компания вне США (остальная Европа и прочие страны: от Augment до ZuTec) | `2_collection/raw/parallel-factcheck-EU-2.md` | на согласовании |
| 8 | Parallel, `pro-fast` | `parallel_prompts/factcheck_EU_3.txt`: то же, 29 компаний (Великобритания и Ирландия: от 3D Repo до XYZ Reality) | `2_collection/raw/parallel-factcheck-EU-3.md` | на согласовании |

Задания 4–8 (2026-10-06) — сверка записей, где значения взяты из агрегаторов (139 компаний на вкладке «Программы и вендоры»). Тексты собираются `scripts/make_factcheck_prompts.py` из реестра; в Parallel уходят только публичные сведения о компаниях, данных гипотез и личных данных нет. Оценка: $5–10 за задание на `pro-fast` (по трём прошлым запускам), $25–50 за все пять; задание 4 запущено как пробное и оценить качество, затем остальные. Фактическая стоимость — в панели Parallel (API её не возвращает).

<!-- Статусы: «на согласовании» → «одобрено» → «выполнено». Тексты показаны основателю и одобрены 2026-10-02; run_id: trun_91c5025d20fc485ab5a6f55ba5a1a309 (Испания), trun_91c5025d20fc485aa32da54cb9ff1a28 (разрешения UK и NL), trun_91c5025d20fc485a8a200c93a6d6a8b4 (голос покупателя). -->

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
