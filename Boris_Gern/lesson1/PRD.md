# Mini-PRD · DZ-1  
### **Version-Focused Review Summariser Agent**  
*(OpenAI Agentic SDK, non-linear plan-execution)*

---

## 1 · Goal  
Пользователь передаёт **(а) путь к CSV** и **(б) номер версии**.  
Агент **сам** (планируя шаги) формирует HTML-отчёт, который:  

1. Сравнивает два подхода  
   - **Extractive** (TextRank, полный корпус версии)  
   - **Abstractive** (Map-Reduce на GPT-4.1 mini)  
2. Показывает:  
   - share версии (доля отзывов среди всего файла)  
   - топ-темы (Praise / Pain / Request)  
   - оба summary  
   - ROUGE-L, latency, cost  
3. Отдаёт один файл `report.html`.

---

## 2 · Inputs  

| CLI Flag | Тип | Описание |
|----------|-----|----------|
| `--csv`  | str | Путь к любому CSV/TSV с колонками `App Version Name`, `Review Text`, `Reviewer Language` |
| `--version` | str | Целевая версия (например, `11.11.1`) |

*(Если `--version` не указан — агент должен спросить пользователя или выбрать последнюю версию.)*

---

## 3 · Tools (регистрируются через `@assistant_tool`)  

| Название | Args | Что делает |
|----------|------|-----------|
| `load_reviews(file_path)` | str | читает CSV (tab/utf-16 или auto-detect) |
| `filter_version(df, ver)` | DataFrame, str | оставляет строки нужной версии и ru-языка |
| `calc_share(df_all, df_ver)` | – | возвращает число 0-1 |
| `textrank_summary(text)` | str | 2 предложения (summa) |
| `chunk(texts)` | list[str] | list[list[str]] длиной ≤ 10 000 симв. |
| `abstractive_summary(chunk)` | list[str] | GPT-4.1 mini, ≤ 70 слов |
| `reduce_summary(minis)` | list[str] | GPT-4.1 mini на mini-summaries |
| `theme_extract(texts)` | list[str] | embeddings + k-means, top-3 тем + цитаты |
| `metric_rouge(ref, cand)` | str, str | ROUGE-L f-score |
| `build_html(payload)` | dict | собирает и сохраняет `report.html` |

---

## 4 · Agent Behaviour (non-linear)  

*System prompt:*  
> «Ты Review PM-Agent. Когда пользователь даёт CSV + версию, сам решай порядок вызова tools, чтобы:  
> • посчитать share версии; • сделать extractive; • сделать map-reduce abstractive;  
> • вычислить ROUGE-L, latency, cost; • выделить темы; • собрать HTML.  
> Вызови `build_html` в конце.»

Агент планирует, ветвится на ошибки (не найдена версия → спросить другую; файл без нужных колонок → объяснить) — это и есть «agentic».

---

## 5 · Runtime Flow (пример, но **не фиксированный**)  

```

user → agent: "Пожалуйста, проанализируй 11.11.1 в reviews.csv"

1. load\_reviews
2. filter\_version
3. (если пусто) ↺ Clarifying question
4. calc\_share
5. textrank\_summary
6. chunk → abstractive\_summary (map, параллельно) → reduce\_summary
7. metric\_rouge (+ latency, cost из usage)
8. theme\_extract
9. build\_html
10. agent → user: "Отчёт готов: report.html"

````

---

## 6 · Acceptance Criteria  

| ID | Проверка | Ожидание |
|----|----------|----------|
| AC-1 | Запуск `python hw1_agent.py --csv path --version 11.11.1` → файл `report.html` | pass |
| AC-2 | В отчёте есть: share %, темы ≥3, два summary, ROUGE-L, latency, cost | pass |
| AC-3 | Агент динамически выбирает шаги; при отсутствии версии задаёт уточняющий вопрос | pass |
| AC-4 | Код ≤ 400 строк, README с инструкцией | pass |

---

## 7 · HTML Skeleton (в отчёт вставляется агентом)

```html
<h2>Version 11.11.1 — Share 32.5 %</h2>

<table border="1">
  <tr><th>Approach</th><th>ROUGE-L</th><th>Latency ms</th><th>Cost $</th></tr>
  <tr><td>Extractive</td><td>—</td><td>0</td><td>0.0000</td></tr>
  <tr><td>Abstractive</td><td>0.29</td><td>3250</td><td>0.038</td></tr>
</table>

<h3>Top themes</h3>
<ul>
  <li><b>Praise</b> – быстрая доставка (цитата)</li>
  <li><b>Pain</b> – вылет при оплате (цитата)</li>
  <li><b>Request</b> – Apple Pay (цитата)</li>
</ul>

<h3>Extractive summary</h3><p>…</p>
<h3>Abstractive summary</h3><p>…</p>

<details><summary>Mini-summaries (8)</summary><ul><li>Chunk 1: …</li></ul></details>
````

---

## 8 · Timeline (1 день)

| Время       | Задача                                    |
| ----------- | ----------------------------------------- |
| Утро        | Реализовать load, filter, share, textrank |
| Полдень     | chunk + abstractive + reduce (async)      |
| После обеда | theme\_extract + metric + build\_html     |
| Вечер       | Интегрировать в Agentic SDK, README, тест |

---

## Key Points

* **Agentic**: порядок шагов не зашит — ассистент сам решает, какие tools вызвать.
* **Version-specific**: пользователь задаёт нужную версию, агент внутри фильтрует.
* **HTML** выводит сравнение + PM-инсайты, как просил Байрам.