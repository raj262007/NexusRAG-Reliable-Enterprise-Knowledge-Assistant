import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app.evaluation.benchmark import evaluate_retrieval, DEFAULT_EVALUATION_DATASET
from app.evaluation.metrics import faithfulness_score, context_relevance_score
from app.api.services import services


def run_benchmark():
    print("=" * 70)
    print("NexusRAG Retrieval & Grounding Evaluation Suite")
    print("=" * 70)
    print("Evaluating against standard benchmark dataset (5 reference queries)...")

    retriever = services.retriever
    results = evaluate_retrieval(retriever, dataset=DEFAULT_EVALUATION_DATASET, k_values=[1, 3, 5])

    print("\n[RETRIEVAL METRICS]")
    print(f"Total Evaluation Queries: {results['total_queries']}")
    print(f"Mean Reciprocal Rank (MRR): {results['mrr']:.4f}")
    for k in [1, 3, 5]:
        print(f"  Precision@{k}: {results['precision'][k]:.4f}  |  Recall@{k}: {results['recall'][k]:.4f}")

    print("\n[PER-QUERY BREAKDOWN]")
    for item in results["query_details"]:
        print(f"\nQuery: {item['query']}")
        print(f"  RR: {item['rr']:.4f} | P@1: {item['precision'][1]} | P@3: {item['precision'][3]} | R@3: {item['recall'][3]}")

    print("\n" + "=" * 70)
    print("Note: Automated metrics above serve as objective reproducible baselines.")
    print("Faithfulness and context relevance estimates complement human evaluation.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
