# Feedback Analysis Agent

Агент для анализа пользовательского фидбека с автоматической категоризацией и генерацией инсайтов для продуктовых команд.

## Возможности

- **Обработка файлов**: Поддержка TXT, CSV, JSON, Excel файлов
- **LLM анализ**: Интеграция с OpenAI GPT-4 и Anthropic Claude
- **Автоматическая категоризация**: Классификация по 6 основным категориям
- **Анализ тональности**: Определение позитивного, негативного или нейтрального настроения
- **Приоритизация**: Автоматическое определение приоритета (высокий/средний/низкий)
- **Генерация инсайтов**: Создание отчетов с рекомендациями для продуктовой команды
- **CLI интерфейс**: Удобный интерфейс командной строки

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd feedback-analyzer
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте API ключи:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ваши API ключи
```

## Использование

### Быстрый старт

1. Создайте пример файлов для тестирования:
```bash
python main.py create-sample
```

2. Проверьте подключение к LLM:
```bash
python main.py test-connection
```

3. Анализируйте фидбек:
```bash
python main.py analyze data/sample_feedback.txt
```

### Основные команды

#### Анализ фидбека
```bash
# Базовый анализ
python main.py analyze input_file.txt

# С сохранением отчета
python main.py analyze input_file.csv -o report.json

# Выбор модели и провайдера
python main.py analyze input_file.json --provider anthropic --model claude-3-sonnet

# Подробный вывод
python main.py analyze input_file.xlsx --verbose
```

#### Тестирование соединения
```bash
python main.py test-connection --provider openai
python main.py test-connection --provider anthropic
```

#### Создание примеров данных
```bash
python main.py create-sample
```

## Поддерживаемые форматы файлов

### TXT файлы
Каждая строка = отдельный отзыв:
```
App crashes when uploading photos
Love the new interface design
Loading times are too slow
```

### CSV файлы
Должны содержать колонку с текстом фидбека (автоматическое определение):
```csv
feedback,user_id,timestamp
"App is great!",user1,2024-01-01
"Found a bug",user2,2024-01-02
```

### JSON файлы
```json
[
  {
    "text": "Feedback text",
    "user_id": "user1",
    "timestamp": "2024-01-01"
  }
]
```

### Excel файлы
Аналогично CSV, автоматическое определение колонок.

## Категории анализа

- **Functionality** - Функциональность продукта
- **UX/UI** - Пользовательский интерфейс и опыт
- **Performance** - Производительность и скорость
- **Bugs** - Баги и технические проблемы
- **Feature Request** - Запросы новых функций
- **General** - Общие отзывы

## Структура отчета

Отчет включает:
- Общую статистику
- Распределение по категориям
- Анализ тональности
- Элементы высокого приоритета
- Ключевые темы
- Рекомендации для каждой категории
- Исполнительное резюме

## Настройка

### Переменные окружения
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEFAULT_MODEL=gpt-4
FEEDBACK_DATA_DIR=./data
OUTPUT_DIR=./output
```

### Конфигурация
Настройки можно изменить в `config/config.yaml`.

## API

### Программное использование

```python
from src.processors import FileProcessor
from src.analyzers.feedback_analyzer import FeedbackAnalyzer, AnalyzerConfig
from src.generators import InsightGenerator

# Настройка
config = AnalyzerConfig(model_provider="openai", model_name="gpt-4")
analyzer = FeedbackAnalyzer(config)

# Обработка файла
processor = FileProcessor()
feedback_items = processor.process_file("feedback.txt")

# Анализ
results = analyzer.analyze_batch(feedback_items)

# Генерация отчета
generator = InsightGenerator()
report = generator.generate_report(results)
```

## Примеры

### Анализ файла с подробным выводом
```bash
python main.py analyze data/user_feedback.csv --verbose -o detailed_report.json
```

### Использование Claude вместо GPT
```bash
python main.py analyze feedback.txt --provider anthropic --model claude-3-sonnet
```

## Разработка

### Структура проекта
```
feedback-analyzer/
├── src/
│   ├── models/          # Pydantic модели данных
│   ├── processors/      # Обработка файлов
│   ├── analyzers/       # LLM анализ
│   └── generators/      # Генерация отчетов
├── config/              # Конфигурационные файлы
├── data/                # Данные для анализа
├── tests/               # Тесты
├── main.py              # CLI приложение
└── requirements.txt     # Зависимости
```

### Добавление новых процессоров
Расширьте `FileProcessor` для поддержки новых форматов файлов.

### Добавление новых категорий
Обновите `FeedbackCategory` enum в `src/models/feedback.py`.

## Лицензия

MIT License

## Поддержка

При возникновении проблем создайте issue в репозитории.