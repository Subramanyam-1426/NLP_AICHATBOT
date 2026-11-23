import pandas as pd
import plotly.express as px
import streamlit as st

from src.intent_classifier import intent_classifier
from ui.theme import apply_plotly_theme, render_page_header


def _render_stepper(state: str) -> None:
    steps = [
        ("data", "Data"),
        ("training", "Train"),
        ("done", "Evaluate"),
    ]
    active_index = {"idle": 0, "training": 1, "done": 2}.get(state, 0)
    items = "".join(
        (
            f'<div class="training-step {"active" if index == active_index else ""} '
            f'{"complete" if index < active_index else ""}">'
            f'<span>{index + 1}</span><strong>{label}</strong></div>'
        )
        for index, (_, label) in enumerate(steps)
    )
    st.markdown(f'<div class="training-stepper">{items}</div>', unsafe_allow_html=True)


def _render_metrics(metrics: dict) -> None:
    with st.container(horizontal=True, gap="small"):
        st.metric("Accuracy", f"{metrics.get('accuracy', 0):.1%}", border=True)
        st.metric("Precision", f"{metrics.get('precision', 0):.1%}", border=True)
        st.metric("Recall", f"{metrics.get('recall', 0):.1%}", border=True)
        st.metric("F1 score", f"{metrics.get('f1_score', 0):.1%}", border=True)


def render_model_training():
    render_page_header(
        "Model training",
        "model_training",
        "Train and compare local intent classifiers using the current labeled dataset.",
    )
    st.session_state.setdefault("training_step", "idle")
    st.session_state.setdefault("benchmark_results", None)
    st.session_state.setdefault("training_metrics", None)
    _render_stepper(st.session_state.training_step)

    with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
        algorithm = st.selectbox(
            "Algorithm",
            ["MultinomialNB", "LogisticRegression", "LinearSVC"],
            key="training_algorithm",
        )
        train_btn = st.button(
            "Train model",
            key="train_model",
            icon=":material/play_arrow:",
            type="primary",
        )

    if train_btn:
        st.session_state["pending_training_algorithm"] = algorithm
        st.session_state.training_step = "training"
        st.rerun()

    if st.session_state.training_step == "training":
        pending_algorithm = st.session_state.get("pending_training_algorithm")
        if pending_algorithm:
            with st.status(f"Training {pending_algorithm}", expanded=True) as status:
                progress = st.progress(10, text="Preparing stratified training data…")
                progress.progress(35, text="Cross-validating word and character features…")
                metrics = intent_classifier.train(model_type=pending_algorithm)
                progress.progress(100, text="Training and evaluation complete")
                status.update(label=f"{pending_algorithm} is ready", state="complete", expanded=False)
            st.session_state.training_metrics = metrics
            st.session_state.training_step = "done"
            st.session_state.pop("pending_training_algorithm", None)
            st.toast(f"{pending_algorithm} trained successfully.", icon=":material/check_circle:")
            st.rerun()

    metrics = st.session_state.training_metrics or (
        intent_classifier.metrics if intent_classifier.is_trained else None
    )
    if metrics:
        st.subheader(f"Active model · {metrics.get('model_name', intent_classifier.model_name)}")
        _render_metrics(metrics)
        if metrics.get("cross_validation"):
            st.caption(
                "Grouped stratified CV accuracy: "
                f"{metrics['cross_validation'].get('accuracy_mean', 0):.1%} "
                "· macro F1: "
                f"{metrics['cross_validation'].get('macro_f1_mean', 0):.1%} "
                "± "
                f"{metrics['cross_validation'].get('macro_f1_std', 0):.1%}"
            )

        matrix = metrics.get("confusion_matrix")
        if matrix:
            with st.container(border=True, key="training_confusion_matrix"):
                st.markdown("**:material/grid_on: Confusion matrix · actual vs predicted**")
                fig = px.imshow(
                    matrix,
                    labels=dict(x="Predicted", y="Actual", color="Count"),
                    x=intent_classifier.intent_tags,
                    y=intent_classifier.intent_tags,
                    color_continuous_scale=(
                        [[0, "#191e2b"], [0.45, "#5147d9"], [1, "#d4cbff"]]
                        if st.session_state.get("dark_mode")
                        else "Blues"
                    ),
                )
                fig.update_layout(
                    height=700,
                    margin=dict(t=12, b=12, l=12, r=12),
                    template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white",
                )
                apply_plotly_theme(fig)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        report = metrics.get("classification_report", {})
        per_intent = [
            {"Intent": tag, **scores}
            for tag, scores in report.items()
            if isinstance(scores, dict) and "f1-score" in scores
        ]
        if per_intent:
            worst = sorted(per_intent, key=lambda row: row["f1-score"])[:10]
            with st.expander("10 lowest-scoring intents", expanded=False):
                st.dataframe(pd.DataFrame(worst), hide_index=True, width="stretch")

    st.subheader("Benchmark all algorithms")
    if st.button(
        "Run full benchmark",
        key="run_full_benchmark",
        icon=":material/bolt:",
        type="secondary",
    ):
        with st.status("Comparing Naive Bayes, Logistic Regression, and LinearSVC", expanded=True) as status:
            progress = st.progress(5, text="Preparing stratified benchmark…")
            progress.progress(35, text="Evaluating word and character n-grams…")
            results = intent_classifier.compare_all_models()
            progress.progress(100, text="Benchmark complete")
            status.update(label="Benchmark complete", state="complete", expanded=False)
        st.session_state.benchmark_results = results
        st.rerun()

    results = st.session_state.benchmark_results
    if results:
        rows = [
            {
                "Algorithm": algorithm_name,
                "Features": result.get("feature_set", "word + character"),
                "Accuracy": result["accuracy"],
                "Precision": result["precision"],
                "Recall": result["recall"],
                "F1": result["f1_score"],
                "CV macro F1": result.get("cross_validation", {}).get("macro_f1_mean", 0),
            }
            for algorithm_name, result in results.items()
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch")
        fig = px.bar(
            df,
            x="Algorithm",
            y=["Accuracy", "Precision", "Recall", "F1"],
            barmode="group",
            title="Held-out model comparison",
            template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white",
        )
        fig.update_layout(margin=dict(t=35, b=10))
        apply_plotly_theme(fig)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
