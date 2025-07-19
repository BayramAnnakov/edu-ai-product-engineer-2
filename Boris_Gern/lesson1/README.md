# Version-Focused Review Summariser Agent

This project is a Python-based agent that analyzes user reviews from a CSV file for a specific application version. It generates an HTML report comparing extractive and abstractive summarization methods, along with key themes and performance metrics.

## Setup

1.  **Create an environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up OpenAI API Key:**
    Create a `.env` file in the root directory and add your API key:
    ```
    OPENAI_API_KEY="your_key_here"
    ```

## Usage

Run the agent from your terminal using the following command:

```bash
python hw1_agent.py --csv reviews_reviews_ru.dodopizza.app_202507.csv --version <app_version>
```

**Arguments:**

*   `--csv`: (Required) The path to the input CSV or TSV file. The file must contain `App Version Name`, `Review Text`, and `Reviewer Language` columns.
*   `--version`: (Optional) The specific app version to analyze (e.g., `11.11.1`). If not provided, the agent will automatically use the most recent version found in the file.

**Example:**

```bash
python hw1_agent.py --csv reviews_reviews_ru.dodopizza.app_202507.csv --version 11.11.1
```

Upon completion, the script will generate a `report.html` file in the root directory with the full analysis.

### Available Versions

The following versions are available for analysis in the provided dataset:

```
['11.12.0', '11.11.1', '11.10.0', '11.9.0', '11.8.0', '11.7.1', '11.6.0', '11.5.0', '11.3.0', '10.23.4', '10.23.3', '10.21.0', '10.20.0', '10.17.1', '10.11.2', '9.20.0', '9.11.0', '8.21.1']
```
