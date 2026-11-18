from typing import List, Dict, Any, Optional
from app.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    context_relevance_score,
    faithfulness_score
)

# Standard reproducible evaluation dataset for NexusRAG
DEFAULT_EVALUATION_DATASET = [
    {
        "id": "eval-01",
        "query": "What vector database does NexusRAG use for persistent embeddings?",
        "ground_truth_doc_ids": ["nexus_overview"],
        "expected_answer_keywords": ["qdrant", "vector", "database", "persistent"],
        "ground_truth_context": "NexusRAG leverages Qdrant as its local persistent vector database."
    },
    {
        "id": "eval-02",
        "query": "Which embedding model and vector dimension are used?",
        "ground_truth_doc_ids": ["nexus_overview"],
        "expected_answer_keywords": ["all-minilm-l6-v2", "384", "sentence-transformers"],
        "ground_truth_context": "The embedding engine uses sentence-transformers/all-MiniLM-L6-v2 producing 384-dimensional normalized vectors."
    },
    {
        "id": "eval-03",
        "query": "How is hybrid search implemented in NexusRAG?",
        "ground_truth_doc_ids": ["nexus_retrieval"],
        "expected_answer_keywords": ["reciprocal rank fusion", "rrf", "bm25", "dense"],
        "ground_truth_context": "NexusRAG implements hybrid retrieval combining dense vector search and BM25 lexical search using Reciprocal Rank Fusion."
    },
    {
        "id": "eval-04",
        "query": "What happens when an uploaded document contains prompt injection attacks?",
        "ground_truth_doc_ids": ["nexus_security"],
        "expected_answer_keywords": ["ignore", "untrusted", "context_passages", "security"],
        "ground_truth_context": "NexusRAG isolates retrieved text within strict context tags and instructs the model to disregard instructions found in uploaded documents."
    },
    {
        "id": "eval-05",
        "query": "What should the model answer when there is insufficient evidence in the context?",
        "ground_truth_doc_ids": ["nexus_security"],
        "expected_answer_keywords": ["not have sufficient information", "refusal", "insufficient"],
        "ground_truth_context": "If context is insufficient, the model must state: 'I do not have sufficient information in the provided documents to answer this question.'"
    }
]


def evaluate_retrieval(
    retriever,
    dataset: Optional[List[Dict[str, Any]]] = None,
    k_values: List[int] = [1, 3, 5]
) -> Dict[str, Any]:
    """
    Run automated retrieval evaluation across a benchmark dataset.
    Calculates Precision@K, Recall@K, and MRR.
    """
    eval_set = dataset or DEFAULT_EVALUATION_DATASET
    results = {
        "total_queries": len(eval_set),
        "mrr": 0.0,
        "precision": {k: 0.0 for k in k_values},
        "recall": {k: 0.0 for k in k_values},
        "query_details": []
    }

    total_rr = 0.0
    prec_accum = {k: 0.0 for k in k_values}
    rec_accum = {k: 0.0 for k in k_values}

    for item in eval_set:
        query = item["query"]
        gt_ids = item["ground_truth_doc_ids"]

        retrieved = retriever.retrieve(query=query, limit=max(k_values))
        # Extract doc IDs or sources from retrieved items
        retrieved_ids = [
            r.get("metadata", {}).get("document_id") or r.get("metadata", {}).get("source") or r.get("id")
            for r in retrieved
        ]

        rr = mean_reciprocal_rank(retrieved_ids, gt_ids)
        total_rr += rr

        query_metrics = {"query": query, "rr": rr, "precision": {}, "recall": {}}

        for k in k_values:
            p = precision_at_k(retrieved_ids, gt_ids, k=k)
            r = recall_at_k(retrieved_ids, gt_ids, k=k)
            prec_accum[k] += p
            rec_accum[k] += r
            query_metrics["precision"][k] = p
            query_metrics["recall"][k] = r

        results["query_details"].append(query_metrics)

    n = len(eval_set)
    results["mrr"] = round(total_rr / n, 4)
    for k in k_values:
        results["precision"][k] = round(prec_accum[k] / n, 4)
        results["recall"][k] = round(rec_accum[k] / n, 4)

    return results
