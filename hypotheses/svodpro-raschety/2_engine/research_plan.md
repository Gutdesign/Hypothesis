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

1. Существует ли измеримый ненулевой поисковый спрос по каждой из 4 тем — и насколько он сопоставим с ВТ?
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

## Out of scope

- Точные цифры поисковой частотности (Wordstat/Keys.so/Ahrefs) — недоступны без платных API в этой сессии. Отмечено как gap, не как "нулевой спрос".
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

- Появляется доступ к Wordstat API / Keys.so / Ahrefs — прогнать количественную оценку поискового спроса (Q1), это сейчас главный оставшийся gap (Parallel.ai уже подключён и использован в этом прогоне).
- Производитель лифтов выпускает новый бесплатный калькулятор подбора — переоценить Q3.
- Фаундер получает данные веб-аналитики (Я.Метрика/GA) по первым неделям после публикации — заново протестировать Q4 (риск S1) на реальных данных, а не по прокси-сигналам.
- Обнаруживается информация о готовящемся пересмотре одной из используемых норм (ГОСТ/СП 267, СанПиН, СП по бассейнам) — переоценить M2.
