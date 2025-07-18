import argparse
import os
from summarization_agent.src.utils.download import fetch_and_process
from summarization_agent.src.pipelines.extractive import extractive_summary
from summarization_agent.src.pipelines.abstractive import abstractive_summary
from summarization_agent.src.evaluators.rouge_eval import compute_rouge

def main():
    parser = argparse.ArgumentParser(description="Summarization Agent CLI")
    parser.add_argument('--url', type=str, required=True, help='URL статьи для суммаризации')
    parser.add_argument('--output', type=str, default='summarization_agent/results/report.md', help='Путь для итогового отчёта')
    args = parser.parse_args()

    print(f"\n[1] Скачивание и обработка статьи...")
    text = fetch_and_process(args.url)

    print(f"[2] Экстрактивное суммирование...")
    extractive = extractive_summary(text, ratio=0.2)

    print(f"[3] Абстрактивное суммирование...")
    abstractive = abstractive_summary(text)

    print(f"[4] Сравнение и метрики...")
    rouge = compute_rouge(extractive, abstractive)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# Сравнительный отчёт по суммаризации\n\n")
        f.write(f"**URL:** {args.url}\n\n")
        f.write(f"## Экстрактивное резюме\n\n{extractive}\n\n")
        f.write(f"## Абстрактивное резюме\n\n{abstractive}\n\n")
        f.write("## Метрики ROUGE\n\n")
        f.write("| Метрика | Значение |\n|---|---|\n")
        for k, v in rouge.items():
            f.write(f"| {k} | {v:.4f} |\n")

    print(f"\nГотово! Итоговый отчёт: {args.output}")
    print("\nКраткие метрики:")
    for k, v in rouge.items():
        print(f"{k}: {v:.4f}")

if __name__ == "__main__":
    main() 