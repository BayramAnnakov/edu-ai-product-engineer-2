# Summarization Agent (Домашнее задание)

## Описание

Агент для автоматической суммаризации научных статей с помощью экстрактивного и абстрактивного подходов на базе OpenAI GPT-4.1 и OpenAI Agents SDK. Автоматически скачивает статью, строит два типа резюме, сравнивает их и формирует отчёт с метриками качества.

## Структура проекта

```
summarization_agent/
├─ src/
│  ├─ agents/
│  ├─ pipelines/
│  ├─ evaluators/
│  └─ utils/
├─ tests/
├─ notebooks/
├─ data/raw/
├─ results/
├─ requirements.txt
├─ README.md
└─ ...
```

## Установка и запуск

1. Клонируйте репозиторий и перейдите в папку проекта.
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Укажите ваш OpenAI API ключ в `.env`:
   ```env
   OPENAI_API_KEY=sk-...
   OPENAI_ORGANIZATION=
   ```
5. Запустите пайплайн:
   ```bash
   python -m summarization_agent.src.main \
      --url https://www.anthropic.com/engineering/built-multi-agent-research-system \
      --output summarization_agent/results/report.md
   ```

## Пример итогового отчёта

```
# Сравнительный отчёт по суммаризации

**URL:** https://www.anthropic.com/engineering/built-multi-agent-research-system

## Экстрактивное резюме
...

## Абстрактивное резюме
...

## Метрики ROUGE
| Метрика | Значение |
|---|---|
| ROUGE-1 | 0.4321 |
| ROUGE-2 | 0.2100 |
| ROUGE-L | 0.3900 |
```

## Тесты

```bash
pytest summarization_agent/tests/
```

## Используемые технологии
- Python 3.10+
- OpenAI Agents SDK ([документация](https://openai.github.io/openai-agents-python/))
- openai, nltk, scikit-learn, rouge-score, pytest и др.

---

> Автор: Max Surkiz and LLM
> Домашнее задание: Summarization Agent with Multi-Modal LLMs
