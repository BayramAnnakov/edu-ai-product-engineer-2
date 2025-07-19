from rouge_score import rouge_scorer

def metric_rouge(reference: str, candidate: str) -> float:
    """Calculates the ROUGE-L F-score between a reference and a candidate summary."""
    if not reference or not candidate:
        return 0.0
        
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores['rougeL'].fmeasure
