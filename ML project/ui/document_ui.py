import os
import tempfile
import re
from html import escape
import streamlit as st
from src.document_qa import document_qa
from ui.theme import render_page_header

def render_document_qa():
    render_page_header(
        "Document Q&A",
        "description",
        "Search your local documents. Answers include the source passage they came from.",
    )

    user = st.session_state.get("user")
    scope_id = user["id"] if user else st.session_state.get("guest_session_id", "guest")
    st.session_state.setdefault("document_file_status_by_owner", {})
    owner_key = str(scope_id)
    file_status = st.session_state.document_file_status_by_owner.setdefault(owner_key, {})
    for source, passages in document_qa.list_documents(user_id=scope_id).items():
        file_status.setdefault(source, {"name": source, "size": 0, "passages": passages})
    # Retain the established state key for the current browser session.
    st.session_state.document_file_status = file_status
    st.session_state.setdefault("document_uploader_version", 0)
    st.session_state.setdefault("document_auto_sample_disabled_by_owner", {})
    sample_disabled = st.session_state.document_auto_sample_disabled_by_owner.get(owner_key, False)
    st.session_state.document_auto_sample_disabled = sample_disabled

    # File uploader
    uploaded_files = st.file_uploader(
        "Add documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Drop PDF, DOCX, or TXT files here. Files are indexed locally for this session.",
        key=f"document_uploader_{st.session_state.document_uploader_version}",
    )

    if uploaded_files:
        for ufile in uploaded_files:
            file_id = ufile.name
            if file_id in file_status or file_id in document_qa.list_documents(user_id=scope_id):
                continue
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(ufile.name)[1]) as tmp:
                tmp.write(ufile.getvalue())
                tmp_path = tmp.name
            with st.spinner(f"Indexing {ufile.name}…"):
                chunks = document_qa.process_document(tmp_path, source_name=ufile.name, user_id=scope_id)
            os.remove(tmp_path)
            file_status[file_id] = {
                "name": ufile.name,
                "size": ufile.size,
                "passages": len(chunks),
            }
            st.toast(f"Indexed {len(chunks)} passages from {ufile.name}", icon=":material/check_circle:")

    # Auto-load sample doc
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "sample_documents", "sample_college_guide.txt"
    )
    if (
        not sample_disabled
        and os.path.exists(sample_path)
        and not document_qa.has_documents(user_id=scope_id)
    ):
        chunks = document_qa.process_document(sample_path, source_name="sample_college_guide.txt", user_id=scope_id)
        file_status["sample_college_guide.txt"] = {
            "name": "sample_college_guide.txt", "size": os.path.getsize(sample_path), "passages": len(chunks)
        }

    col1, col2 = st.columns([4, 1])
    col1.metric("Indexed passages", sum(document_qa.list_documents(user_id=scope_id).values()), border=True)
    with col2:
        if st.button("Clear index", icon=":material/delete_sweep:"):
            document_qa.clear_index(user_id=scope_id)
            file_status.clear()
            st.session_state.document_auto_sample_disabled_by_owner[owner_key] = True
            st.session_state.document_auto_sample_disabled = True
            st.session_state.document_uploader_version += 1
            st.toast("Document index cleared.", icon=":material/delete:")
            st.rerun()

    for file_info in file_status.values():
        with st.container(border=True):
            with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
                st.markdown(f"**:material/description: {file_info['name']}**")
                st.badge(f"{file_info['passages']} passages", color="green")
            st.caption(f"{file_info['size'] / 1024:.1f} KB · Indexed locally for this session")

    query = st.text_input(
        "Ask about your documents",
        placeholder="For example: What does the document say about admissions?",
        key="document_question",
    )

    if query:
        with st.spinner("Searching indexed passages…"):
            results = document_qa.search_document(query, top_k=3, user_id=scope_id)
        if results:
            st.subheader("Relevant passages")
            for idx, res in enumerate(results):
                with st.container(border=True):
                    top = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
                    with top:
                        st.badge(f"Match {idx + 1}", color="violet")
                        st.badge(f"{int(res['score'] * 100)}%", icon=":material/target:", color="green")
                    query_terms = sorted(set(re.findall(r"[\w-]+", query)), key=len, reverse=True)
                    snippet = escape(res["raw_text"][:2200])
                    for term in query_terms:
                        snippet = re.sub(
                            re.escape(escape(term)),
                            lambda match: f"<mark>{match.group(0)}</mark>",
                            snippet,
                            flags=re.IGNORECASE,
                        )
                    st.markdown(f'<div class="doc-snippet">{snippet}</div>', unsafe_allow_html=True)
                    st.caption(f"Source: {res['source']} · Page/paragraph {res['page']}")
        else:
            st.info("No close passage found. Try a phrase or term used in the document.", icon=":material/search_off:")
