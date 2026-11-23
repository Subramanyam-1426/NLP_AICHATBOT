import streamlit as st
import pandas as pd
import plotly.express as px
from html import escape
from src.preprocessing import preprocessor
from src.nltk_explainer import explainer
from src.sentiment_analyzer import sentiment_analyzer
from ui.theme import apply_plotly_theme, render_page_header

_DEFAULT_TEXT = (
    "Natural Language Processing with NLTK enables computers to understand "
    "human languages! The Institute of Technology is conducting research in AI and ML."
)

def _token_box(items: list, title: str):
    """Render tokens as theme-aware, escaped chips."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if items:
            chips = " ".join(f'<span class="token-chip">{escape(str(item))}</span>' for item in items)
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.caption("No tokens to display.")


def render_nltk_lab():
    render_page_header(
        "NLTK Lab",
        "psychology",
        "Explore how local text processing breaks down and interprets language.",
    )

    # ── Receive text forwarded from the Chat page ─────────────────────────────
    prefill = st.session_state.pop("nltk_prefill", None)

    if prefill is not None:
        st.session_state["_nltk_version"] = st.session_state.get("_nltk_version", 0) + 1
        st.session_state["_nltk_stored_text"] = prefill
        st.success(
            f"📨 **Forwarded from Chat → NLTK Lab**\n\n"
            f"*Analyzing your prompt:* \"{prefill[:160]}{'...' if len(prefill) > 160 else ''}\"",
            icon="🧠"
        )

    version    = st.session_state.get("_nltk_version", 0)
    widget_key = f"nltk_ta_v{version}"

    initial_text = prefill if prefill is not None else st.session_state.get("_nltk_stored_text", _DEFAULT_TEXT)

    sample_text = st.text_area(
        "Input text",
        value=initial_text,
        key=widget_key,
        height=120,
        help="Enter text to inspect the local NLP pipeline.",
    )
    st.session_state["_nltk_stored_text"] = sample_text

    if not sample_text.strip():
        st.info("Enter some text above to begin.")
        return

    details = preprocessor.get_full_nlp_pipeline_details(sample_text)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Tokens", "Stopwords", "POS tags",
        "Stemming & lemmas", "Named entities", "Frequency", "Sentiment"
    ])

    with tab1:
        info = explainer.get_stage_explanation("tokenization")
        st.info(f"**{info['title']}** — {info['definition']}")
        st.caption(f"NLTK method: `{info['nltk_method']}`")
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown(f"**Sentence Tokens · {len(details['raw_sentences'])} sentences**")
                if details["raw_sentences"]:
                    sentence_cards = "".join(
                        f'<li><span class="sentence-number">{index}</span>{escape(str(sentence))}</li>'
                        for index, sentence in enumerate(details["raw_sentences"], 1)
                    )
                    st.markdown(
                        f'<ol class="sentence-list">{sentence_cards}</ol>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No sentences detected.")
        with c2:
            _token_box(details["raw_tokens"], "Word Tokens")

    with tab2:
        info = explainer.get_stage_explanation("stopwords")
        st.info(f"**{info['title']}** — {info['definition']}")
        st.caption(f"NLTK method: `{info['nltk_method']}`")
        c1, c2 = st.columns(2)
        with c1:
            _token_box(details["raw_tokens"], f"Raw ({len(details['raw_tokens'])} tokens)")
        with c2:
            _token_box(details["filtered_tokens"], f"Filtered ({len(details['filtered_tokens'])} tokens)")

    with tab3:
        info = explainer.get_stage_explanation("pos_tagging")
        st.info(f"**{info['title']}** — {info['definition']}")
        st.caption(f"NLTK method: `{info['nltk_method']}`")
        tag_colors = {
            "NN": "blue", "VB": "green", "JJ": "orange", "RB": "violet",
            "PR": "red", "IN": "gray", "DT": "gray", "CC": "gray",
        }
        with st.container(horizontal=True, gap="small"):
            for token, tag in details["pos_tags"]:
                color = next((value for prefix, value in tag_colors.items() if tag.startswith(prefix)), "gray")
                st.badge(f"{token} · {tag}", color=color)

    with tab4:
        info = explainer.get_stage_explanation("lemmatization")
        st.info(f"**{info['title']}** — {info['definition']}")
        rows = [
            {"Original": t, "Stem": s, "Lemma": l}
            for t, s, l in zip(details["filtered_tokens"], details["stems"], details["lemmas"])
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    with tab5:
        info = explainer.get_stage_explanation("ner")
        st.info(f"**{info['title']}** — {info['definition']}")
        if details["named_entities"]:
            df = pd.DataFrame(details["named_entities"], columns=["Entity", "Label"])
            st.dataframe(df, hide_index=True, width="stretch")
        else:
            st.write("No named entities detected.")

    with tab6:
        st.markdown("**Top Token Frequencies**")
        df_freq = pd.DataFrame(
            list(details["frequency_distribution"].items()), columns=["Token", "Count"]
        ).sort_values("Count", ascending=False).head(20)
        if not df_freq.empty:
            is_dark = st.session_state.get("dark_mode", False)
            fig = px.bar(
                df_freq.sort_values("Count", ascending=True),
                x="Count",
                y="Token",
                orientation="h",
                text="Count",
                color_discrete_sequence=["#a99cff" if is_dark else "#5147d9"],
                template="plotly_dark" if is_dark else "plotly_white",
            )
            fig.update_layout(
                height=470,
                margin=dict(t=10, b=10, l=8, r=12),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Occurrences",
                yaxis_title=None,
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            apply_plotly_theme(fig, is_dark)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with tab7:
        info = explainer.get_stage_explanation("sentiment")
        st.info(f"**{info['title']}** — {info['definition']}")
        sentiment = sentiment_analyzer.analyze(sample_text)
        st.metric("Overall tone", f"{sentiment['emoji']} {sentiment['sentiment']}")
        st.progress(
            min(max((sentiment["compound"] + 1) / 2, 0.0), 1.0),
            text=f"Compound polarity: {sentiment['compound']:.2f}",
        )
        st.caption(
            f"Positive {sentiment['pos']:.0%} · Neutral {sentiment['neu']:.0%} · Negative {sentiment['neg']:.0%}"
        )
