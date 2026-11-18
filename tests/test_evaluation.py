import pytest
from unittest.mock import MagicMock
from app.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    context_relevance_score,
    faithfulness_score
)
from app.evaluation.benchmark import evaluate_retrieval, DEFAULT_EVALUATION_DATASET


def test_precision_at_k():
    retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    ground_truth = ["doc1", "doc3"]

    assert precision_at_k(retrieved, ground_truth, k=2) == 0.5  # 1/2
    assert precision_at_k(retrieved, ground_truth, k=4) == 0.5  # 2/4
    assert precision_at_k(retrieved, ground_truth, k=5) == 0.4  # 2/5


def test_recall_at_k():
    retrieved = ["doc1", "doc2", "doc3", "doc4"]
    ground_truth = ["doc1", "doc3", "doc9"]

    # In top 2: doc1 (1/3)
    assert recall_at_k(retrieved, ground_truth, k=2) == 0.3333
    # In top 4: doc1, doc3 (2/3)
    assert recall_at_k(retrieved, ground_truth, k=4) == 0.6667


def test_mean_reciprocal_rank():
    # Relevant item at rank 1 -> RR = 1.0
    assert mean_reciprocal_rank(["docA", "docB"], ["docA"]) == 1.0
    # Relevant item at rank 2 -> RR = 0.5
    assert mean_reciprocal_rank(["docX", "docA"], ["docA"]) == 0.5
    # Not found -> RR = 0.0
    assert mean_reciprocal_rank(["docX", "docY"], ["docA"]) == 0.0


def test_context_relevance():
    query = "What is hybrid search in Qdrant?"
    context = ["Qdrant supports hybrid vector search with BM25 Okapi."]
    score = context_relevance_score(context, query)
    assert score > 0.5


def test_faithfulness_score():
    passages = ["NexusRAG uses sentence-transformers/all-MiniLM-L6-v2 on CPU by default."]
    answer = "NexusRAG runs sentence-transformers all-MiniLM-L6-v2 on CPU by default."
    score = faithfulness_score(answer, passages)
    assert score >= 0.8

    # Unfaithful / fabricated claim
    hallucinated_answer = "NexusRAG runs GPT-4o on high-end cloud supercomputers with secret GPUs."
    bad_score = faithfulness_score(hallucinated_answer, passages)
    assert bad_score < 0.5


def test_benchmark_runner():
    mock_retriever = MagicMock()
    # Mock retrieval returning the expected ground truth doc id
    mock_retriever.retrieve.return_value = [
        {"id": "c1", "text": "text", "metadata": {"document_id": "nexus_overview"}},
        {"id": "c2", "text": "text", "metadata": {"document_id": "nexus_retrieval"}},
    ]

    report = evaluate_retrieval(mock_retriever, dataset=DEFAULT_EVALUATION_DATASET[:2], k_values=[1, 3])
    assert report["total_queries"] == 2
    assert "mrr" in report
    assert 1 in report["precision"]
    assert 3 in report["recall"]
