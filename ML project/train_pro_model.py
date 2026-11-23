import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath("."))

from src.intent_classifier import intent_classifier

def main():
    print("=" * 60)
    print("🤖 PRO-LEVEL ML INTENT MODEL TRAINING & BENCHMARKING")
    print("=" * 60)

    # 1. Load intent data
    intents = intent_classifier.load_intents()
    print(f"Loaded {len(intents)} intent categories.")

    # 2. Compare algorithms and feature sets using grouped cross-validation.
    print("\n[1/3] Benchmarking ML Algorithms...")
    comparison_results = intent_classifier.compare_all_models()

    print("\n" + "-" * 60)
    print(f"{'Algorithm':<32} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 60)
    for model_name, metrics in comparison_results.items():
        print(f"{model_name:<32} | {metrics['accuracy']:<10.4f} | {metrics['precision']:<10.4f} | {metrics['recall']:<10.4f} | {metrics['f1_score']:<10.4f}")
    print("-" * 60)

    # compare_all_models refits and saves the configuration selected by cross-validation.
    final_metrics = intent_classifier.metrics

    print("\n" + "=" * 60)
    print("FINAL GROUPED-HOLDOUT MODEL PERFORMANCE")
    print("=" * 60)
    print(f"• Algorithm Selected: {final_metrics['model_name']}")
    print(f"• Total Intents:     {final_metrics['total_intents']}")
    print(f"• Total Samples:     {final_metrics['total_samples']}")
    print(f"• Test Accuracy:     {final_metrics['accuracy'] * 100:.2f}%")
    print(f"• Weighted Precision:{final_metrics['precision'] * 100:.2f}%")
    print(f"• Weighted Recall:   {final_metrics['recall'] * 100:.2f}%")
    print(f"• Weighted F1-Score: {final_metrics['f1_score'] * 100:.2f}%")
    print(f"• Macro F1-Score:    {final_metrics['macro_f1'] * 100:.2f}%")
    print(f"• CV Accuracy:       {final_metrics['cross_validation']['accuracy_mean'] * 100:.2f}%")
    print(f"• CV Macro F1:       {final_metrics['cross_validation']['macro_f1_mean'] * 100:.2f}%")
    print(f"• Tuned threshold:   {final_metrics['confidence_threshold']:.2f}")
    print(f"• Held-out fallback: {final_metrics['validation_fallback_rate'] * 100:.2f}%")
    print("=" * 60)

    print("\n10 lowest-scoring held-out intents:")
    class_scores = [
        (tag, values["precision"], values["recall"], values["f1-score"], int(values["support"]))
        for tag, values in final_metrics["classification_report"].items()
        if isinstance(values, dict) and "f1-score" in values
    ]
    for tag, precision, recall, f1, support in sorted(class_scores, key=lambda row: row[3])[:10]:
        print(f"  {tag:<32} P={precision:.2f} R={recall:.2f} F1={f1:.2f} n={support}")

    print("\nSample inference:")
    sample_queries = [
        "Hello there, how are you?",
        "What branches of engineering are available?",
        "How much is the B.Tech fee per year?",
        "Tell me about placements and average salary package",
        "What is the difference between Supervised and Unsupervised Learning?",
        "Explain NLTK tokenization and lemmatization",
        "What is text preprocessing?",
        "How do I remove stop words?",
        "What is POS tagging?",
        "How does TF-IDF work?",
        "What is Python used for in AI and Data Science?",
        "Who built this project?",
        "Can I get hostel wifi and mess facility?",
        "When are the semester exams held?",
        "How do I apply for admissions?",
        "random unintelligible gibberish xyz123"
    ]

    print("-" * 75)
    print(f"{'Sample User Query':<48} | {'Predicted Intent':<18} | {'Confidence':<10}")
    print("-" * 75)
    fallback_count = 0
    for q in sample_queries:
        res = intent_classifier.predict_intent(q)
        tag = res["tag"]
        conf = res["confidence"]
        fallback_str = " (FALLBACK)" if res["is_fallback"] else ""
        fallback_count += int(res["is_fallback"])
        print(f"{q:<48} | {tag + fallback_str:<18} | {conf * 100:.1f}%")
    print("-" * 75)
    print(
        f"Sample fallback rate: {fallback_count}/{len(sample_queries)} "
        f"({fallback_count / len(sample_queries):.1%})"
    )

    print("\nModel training complete. Artifacts saved to models/")

if __name__ == "__main__":
    main()
