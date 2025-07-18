from rouge_score import rouge_scorer

def compute_rouge(summary1: str, summary2: str) -> dict:
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(summary1, summary2)
    # Приводим к удобному виду
    result = {
        "ROUGE-1": scores["rouge1"].fmeasure,
        "ROUGE-2": scores["rouge2"].fmeasure,
        "ROUGE-L": scores["rougeL"].fmeasure,
    }
    return result

if __name__ == "__main__":
    # Пример использования
    s1 = "The cat sat on the mat."
    s2 = "A cat was sitting on the mat."
    print(compute_rouge(s1, s2)) 