# Summarization Agent with Multi-Modal LLMs

## Project Overview

This project implements a Summarization Agent capable of both extractive and abstractive summarization of long-form articles using modern NLP and LLM technologies. The agent automatically downloads a source article (e.g., Anthropic's "We built a multi-agent research system"), processes it, generates two types of summaries, and compares their quality using ROUGE metrics. The project demonstrates practical agent-based orchestration, deterministic and probabilistic summarization, and automated evaluation in Python.

## Tools and Technologies Used

- **Python 3.10+** — main programming language for all modules
- **OpenAI Agents SDK** — for agent orchestration and tool integration
- **OpenAI GPT-4.1 API** — for abstractive summarization and self-critique
- **NLTK** — for text preprocessing and extractive summarization
- **BeautifulSoup4** — for HTML parsing and text extraction
- **ROUGE-score** — for summary quality evaluation
- **pytest** — for unit and integration testing
- **Git, pre-commit, GitHub Actions** — for version control, code style, and CI

These tools were selected for their reliability, community support, and suitability for modern NLP and agent-based workflows.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SMakc/edu-ai-product-engineer-2.git
   cd edu-ai-product-engineer-2/Max_Surkiz/summarization_agent
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and add your OpenAI API key and organization.

5. **Prepare data:**
   - By default, the script will download and process the Anthropic article. You can also place your own raw text files in `data/raw/`.

6. **Run the summarization pipeline:**
   ```bash
   python src/main.py --url https://www.anthropic.com/engineering/built-multi-agent-research-system --output results/report.md
   ```
   - The final report and metrics will be saved in the `results/` directory.

7. **Run tests:**
   ```bash
   pytest tests/
   ```
