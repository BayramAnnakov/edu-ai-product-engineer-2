import openai
from summarization_agent.src.utils.config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE


def abstractive_summary(text: str) -> str:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Ты — профессиональный научный редактор. Сделай краткое, связное и информативное абстрактивное резюме следующей статьи."},
            {"role": "user", "content": text}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    with open("summarization_agent/data/raw/anthropic_multi_agent.txt", encoding="utf-8") as f:
        text = f.read()
    summary = abstractive_summary(text)
    print(summary) 