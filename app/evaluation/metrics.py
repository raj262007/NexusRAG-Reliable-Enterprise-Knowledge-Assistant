import re
from typing import List, Set, Dict, Any


def precision_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
    """
    Precision@K: Fraction of top-K retrieved items that are relevant.
    Score ranges from 0.0 to 1.0.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    if not retrieved_ids or not ground_truth_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    gt_set = set(ground_truth_ids)
    relevant_in_top_k = sum(1 for item in top_k if item in gt_set)
    return round(relevant_in_top_k / k, 4)


def recall_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
    """
    Recall@K: Fraction of relevant items that appear in the top-K retrieved results.
    Score ranges from 0.0 to 1.0.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    if not retrieved_ids or not ground_truth_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    gt_set = set(ground_truth_ids)
    relevant_in_top_k = sum(1 for item in top_k if item in gt_set)
    return round(relevant_in_top_k / len(gt_set), 4)


def mean_reciprocal_rank(ranked_retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
    """
    Reciprocal Rank (RR): 1 / rank of the first relevant document.
    Returns 0.0 if no relevant items are found.
    """
    if not ranked_retrieved_ids or not ground_truth_ids:
        return 0.0

    gt_set = set(ground_truth_ids)
    for rank, item in enumerate(ranked_retrieved_ids, start=1):
        if item in gt_set:
            return round(1.0 / rank, 4)
    return 0.0


def context_relevance_score(retrieved_texts: List[str], query: str) -> float:
    """
    Automated Context Relevance Estimate:
    Measures the token overlap and coverage of query keywords in the retrieved context.
    Note: Automated heuristic proxy. Human evaluation or calibrated LLM-as-a-judge is
    recommended for nuanced semantic evaluation.
    """
    if not retrieved_texts or not query.strip():
        return 0.0

    query_tokens = set(re.findall(r"\w+", query.lower()))
    # Exclude common stopwords
    stopwords = {"what", "is", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with"}
    meaningful_tokens = query_tokens - stopwords
    if not meaningful_tokens:
        meaningful_tokens = query_tokens

    combined_context = " ".join(retrieved_texts).lower()
    matched = sum(1 for token in meaningful_tokens if token in combined_context)

    return round(matched / len(meaningful_tokens), 4)


def faithfulness_score(answer: str, context_passages: List[str]) -> float:
    """
    Automated Faithfulness Estimate:
    Measures what fraction of substantive claims/phrases in the generated answer
    are grounded in the retrieved context passages.
    Score ranges from 0.0 to 1.0.
    Note: Heuristic n-gram containment estimate; distinguish clearly from human audit.
    """
    if not answer.strip():
        return 0.0
    if not context_passages:
        # If no context but answer refused to hallucinate, consider faithful
        if "not have sufficient information" in answer.lower():
            return 1.0
        return 0.0

    combined_context = " ".join(context_passages).lower()

    # Split answer into meaningful sentences or clauses
    clauses = [s.strip() for s in re.split(r"[.!?\n]", answer) if len(s.strip()) > 10]
    if not clauses:
        return 1.0

    grounded_count = 0
    for clause in clauses:
        tokens = [t for t in re.findall(r"\w+", clause.lower()) if len(t) > 3]
        if not tokens:
            continue
        # Check if majority of clause tokens appear in context
        in_context = sum(1 for t in tokens if t in combined_context)
        if (in_context / len(tokens)) >= 0.5:
            grounded_count += 1

    return round(grounded_count / len(clauses), 4) if clauses else 1.0
