from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from rag.config import settings
from rag.ingestion import bundled_documents, make_documents, read_upload
from rag.store import KnowledgeBase
from rag.workflow import build_workflow

st.set_page_config(page_title="Enterprise RAG Bot", page_icon="◈", layout="wide")
st.markdown("""
<style>
.stApp { background: linear-gradient(145deg, #f6f8fc 0%, #eef3f8 100%); }
.hero {padding: 1.6rem 1.8rem; border-radius: 18px; color: white; margin-bottom: 1rem;
 background: radial-gradient(circle at 85% 20%, #167d9a 0, #123653 34%, #0b2034 75%); box-shadow: 0 14px 38px #0b203426;}
.hero h1 {margin:0; font-size:2.25rem}.hero p{color:#c8dce9;margin:.45rem 0 0;max-width:760px}
.eyebrow{letter-spacing:.15em;text-transform:uppercase;font-size:.73rem;color:#69d6c5;font-weight:700}
.card{background:#fff;border:1px solid #dce5ed;border-radius:14px;padding:1rem 1.1rem;min-height:116px;box-shadow:0 7px 22px #16344e0b}
.card h3{font-size:1rem;margin:.1rem 0}.muted{color:#607487;font-size:.88rem}
[data-testid="stMetric"]{background:white;border:1px solid #dce5ed;padding:12px;border-radius:14px}
.stButton>button{border-radius:10px;font-weight:650}
</style>
<div class="hero"><div class="eyebrow">ACME Knowledge Systems</div><h1>Enterprise RAG Bot</h1>
<p>Grounded answers across people policies, platform documentation, and compliance controls—with transparent evidence at every step.</p></div>
""", unsafe_allow_html=True)


def get_kb():
    return KnowledgeBase(settings)


def source_caption(doc) -> str:
    meta = doc.metadata
    page = f" · page {meta['page']}" if meta.get("page") else ""
    return f"{meta.get('source', 'Unknown')} · {meta.get('section', 'General')}{page} · {meta.get('category', 'general').title()}"


tab_ingest, tab_qa = st.tabs(["▣  Document Ingestion", "✦  Question Answering Workflow"])

with tab_ingest:
    st.subheader("Build the knowledge base")
    st.caption("Index the bundled manuals or add an approved enterprise document.")
    configured = settings.model_provider == "ollama" or bool(os.getenv("OPENAI_API_KEY"))
    try:
        chunk_count = get_kb().count() if configured else 0
    except Exception:
        chunk_count = 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Document domains", "3")
    m2.metric("Source files", len(list(settings.docs_dir.rglob("*.txt"))))
    m3.metric("Indexed chunks", chunk_count)
    m4.metric("Model provider", settings.model_provider.title() if configured else "Key needed")

    cols = st.columns(3)
    domain_data = [
        ("People & HR", "Leave, benefits, conduct, performance and onboarding", "HR"),
        ("Platform & Engineering", "APIs, architecture, deployments, schemas and SLAs", "Technical"),
        ("Risk & Compliance", "Privacy, security, incidents, audits and continuity", "Compliance"),
    ]
    for col, (title, body, label) in zip(cols, domain_data):
        col.markdown(f'<div class="card"><span class="eyebrow">{label}</span><h3>{title}</h3><div class="muted">{body}</div></div>', unsafe_allow_html=True)

    st.divider()
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("#### Bundled corpus")
        for path in sorted(settings.docs_dir.rglob("*.txt")):
            st.markdown(f"✓ `{path.relative_to(settings.docs_dir)}`")
        if st.button("Index bundled documents", type="primary", use_container_width=True):
            try:
                with st.spinner("Chunking and embedding the corpus…"):
                    count = get_kb().add(bundled_documents(settings))
                st.success(f"Indexed {count} chunks successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Indexing failed: {exc}")
    with right:
        st.markdown("#### Add documents")
        category = st.selectbox("Document category", ["HR", "Technical", "Compliance"])
        uploads = st.file_uploader("TXT, PDF, or DOCX", type=["txt", "pdf", "docx"], accept_multiple_files=True)
        if st.button("Index uploaded documents", disabled=not uploads, use_container_width=True):
            try:
                docs = []
                for upload in uploads:
                    docs.extend(make_documents(read_upload(upload.name, upload), upload.name, category.lower(), settings))
                count = get_kb().add(docs)
                st.success(f"Indexed {count} chunks from {len(uploads)} file(s).")
                st.rerun()
            except Exception as exc:
                st.error(f"Upload failed: {exc}")
    if not configured:
        st.info("Add `OPENAI_API_KEY` to a local `.env` file before indexing. See `.env.example`.")

with tab_qa:
    st.subheader("Ask the enterprise knowledge base")
    st.caption("Each answer is routed, retrieved, checked, and grounded in indexed evidence.")
    control, conversation = st.columns([0.3, 0.7], gap="large")
    with control:
        st.markdown("#### Search controls")
        selected = st.radio("Knowledge domain", ["Auto", "HR", "Technical", "Compliance"], horizontal=False)
        st.markdown("#### Try asking")
        examples = ["How many annual leave days can I carry over?", "What should a client do after an HTTP 429?", "When must a GDPR breach be reported?"]
        for prompt in examples:
            if st.button(prompt, key=prompt, use_container_width=True):
                st.session_state.pending_prompt = prompt
        st.markdown("#### Workflow")
        st.caption("Route → Retrieve → Grade evidence → Answer")
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with conversation:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    with st.expander(f"Evidence · {len(message['sources'])} chunks"):
                        for i, doc in enumerate(message["sources"], 1):
                            st.markdown(f"**[{i}] {source_caption(doc)}**")
                            st.caption(doc.page_content)
                if message.get("trace"):
                    st.caption("  →  ".join(message["trace"]))
        prompt = st.chat_input("Ask about policy, systems, or compliance…")
        if st.session_state.get("pending_prompt"):
            prompt = st.session_state.pop("pending_prompt")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    if not configured:
                        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to `.env`, then index the documents.")
                    if get_kb().count() == 0:
                        raise RuntimeError("The knowledge base is empty. Use Document Ingestion to index the bundled corpus first.")
                    with st.spinner("Searching trusted sources…"):
                        result = build_workflow(get_kb(), settings).invoke({"question": prompt, "requested_category": selected.lower()})
                    st.markdown(result["answer"])
                    with st.expander(f"Evidence · {len(result['documents'])} chunks"):
                        for i, doc in enumerate(result["documents"], 1):
                            st.markdown(f"**[{i}] {source_caption(doc)}**")
                            st.caption(doc.page_content)
                    st.caption("  →  ".join(result["trace"]))
                    st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["documents"], "trace": result["trace"]})
                except Exception as exc:
                    message = f"I can’t run the workflow yet. {exc}"
                    st.error(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
