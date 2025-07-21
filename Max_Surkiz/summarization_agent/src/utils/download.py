import requests
from bs4 import BeautifulSoup
import os

RAW_HTML_PATH = "summarization_agent/data/raw/anthropic_multi_agent.html"
RAW_TXT_PATH = "summarization_agent/data/raw/anthropic_multi_agent.txt"


def download_article(url: str):
    response = requests.get(url)
    response.raise_for_status()
    with open(RAW_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(response.text)
    return response.text


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Удаляем скрипты и стили
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Минимальная очистка
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def save_text(text: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def fetch_and_process(url: str):
    html = download_article(url)
    text = html_to_text(html)
    save_text(text, RAW_TXT_PATH)
    return text

if __name__ == "__main__":
    url = "https://www.anthropic.com/engineering/built-multi-agent-research-system"
    fetch_and_process(url) 