import os, re, json, tempfile
from pathlib import Path
from typing import List, Dict

import streamlit as st
import pymupdf
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

APP_TITLE = "ReguLens — Regulatory Circular Intelligence"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title=APP_TITLE, page_icon="📑", layout="wide")


def get_setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default


def extract_pdf(file_bytes: bytes, filename: str) -> List[Dict]:
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append({"page": i + 1, "text": text, "source": filename})
    return pages


def chunk_pages(pages: List[Dict], chunk_words: int = 180, overlap: int = 35) -> List[Dict]:
    chunks = []
    for p in pages:
        words = p["text"].split()
        start = 0
        idx = 0
        while start < len(words):
            end = min(len(words), start + chunk_words)
            text = " ".join(words[start:end])
            chunks.append({
                "id": f"{p['source']}-p{p['page']}-c{idx}",
                "page": p["page"],
                "source": p["source"],
                "text": text,
            })
            if end == len(words):
                break
            start = max(end - overlap, start + 1)
            idx += 1
    return chunks


def retrieve(query: str, chunks: List[Dict], k: int = 5):
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=15000)
    X = vectorizer.fit_transform(texts)
    q = vectorizer.transform([query])
    scores = cosine_similarity(q, X).ravel()
    order = scores.argsort()[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in order if scores[i] > 0]


def gemini_generate(prompt: str) -> str:
    key = get_setting("GEMINI_API_KEY")
    if not key:
        return ""
    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=get_setting("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=prompt,
        )
        return response.text or ""
    except Exception as e:
        st.warning(f"Gemini unavailable: {e}")
        return ""


def build_context(chunks: List[Dict]) -> str:
    return "\n\n".join(
        f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}" for c in chunks
    )


def fallback_summary(chunks: List[Dict]) -> str:
    if not chunks:
        return "No relevant text was found."
    # Simple extractive fallback for a demo without an API key.
    sentences = []
    for c in chunks[:4]:
        parts = re.split(r"(?<=[.!?])\s+", c["text"])
        sentences.extend(parts[:2])
    return " ".join(sentences[:8])


def summarize(chunks: List[Dict]) -> str:
    context = build_context(chunks)
    prompt = f"""
You are a regulatory compliance analyst. Summarize the regulatory circular using ONLY the supplied context.

Return these sections:
1. Executive Summary — 4-6 bullets
2. Key Regulatory Changes — concise bullets
3. Effective Dates / Deadlines — if explicitly present
4. Impacted Functions — departments/processes affected, only if supported
5. Required Actions — practical compliance actions, clearly marked as inferred when not explicit
6. Risks / Attention Points

Every factual statement must include an inline source like [Page 3]. Do not invent facts. If information is missing, say so.

CONTEXT:
{context}
"""
    answer = gemini_generate(prompt)
    return answer if answer else fallback_summary(chunks)


def answer_question(question: str, chunks: List[Dict]) -> str:
    context = build_context(chunks)
    prompt = f"""
Answer the user's question about a regulatory circular using ONLY the context below.
Be concise and precise. Cite every factual claim with [Page N]. If the answer is not in the context, say: 'I could not find that in the uploaded circular.'

Question: {question}

Context:
{context}
"""
    answer = gemini_generate(prompt)
    if answer:
        return answer
    if not chunks:
        return "I could not find that in the uploaded circular."
    return f"Relevant passage: {chunks[0]['text']} [Page {chunks[0]['page']}]"


# ---- UI ----
st.title("📑 ReguLens")
st.caption("Regulatory Circular Intelligence • PDF → Retrieval → Grounded Summary → Q&A")

with st.sidebar:
    st.header("Configuration")
    api_present = bool(get_setting("GEMINI_API_KEY"))
    st.success("Gemini API connected") if api_present else st.info("Demo mode: no Gemini API key")
    top_k = st.slider("Retrieved passages", 3, 8, 5)
    chunk_words = st.slider("Chunk size (words)", 100, 300, 180, 20)
    st.markdown("**Demo flow**")
    st.markdown("1. Upload circular\n2. Extract + chunk\n3. Retrieve relevant passages\n4. Generate grounded summary\n5. Ask questions with page citations")

uploaded = st.file_uploader("Upload a regulatory circular (PDF)", type=["pdf"])

if uploaded:
    with st.spinner("Processing PDF…"):
        pages = extract_pdf(uploaded.getvalue(), uploaded.name)
        chunks = chunk_pages(pages, chunk_words=chunk_words)
        st.session_state["chunks"] = chunks
        st.session_state["filename"] = uploaded.name

    if not pages:
        st.error("No text was extracted. This PDF may be scanned/image-only; OCR support should be added for this document.")
        st.stop()

    st.success(f"Processed **{uploaded.name}** — {len(pages)} pages, {len(chunks)} searchable chunks.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Pages", len(pages))
    c2.metric("Searchable chunks", len(chunks))
    c3.metric("LLM", "Gemini" if api_present else "Fallback")

    tab1, tab2, tab3 = st.tabs(["Executive Summary", "Ask the Circular", "Retrieved Evidence"])

    with tab1:
        if st.button("Generate Regulatory Summary", type="primary"):
            with st.spinner("Generating grounded summary…"):
                summary_chunks = retrieve(
                    "regulatory changes requirements effective date compliance actions applicability key changes",
                    chunks,
                    k=min(top_k, len(chunks)),
                )
                st.session_state["summary"] = summarize(summary_chunks)
                st.session_state["summary_sources"] = summary_chunks
        if st.session_state.get("summary"):
            st.markdown(st.session_state["summary"])

    with tab2:
        question = st.text_input("Ask a question", placeholder="What are the key compliance requirements?")
        if st.button("Ask", type="primary", disabled=not question):
            with st.spinner("Searching the circular…"):
                hits = retrieve(question, chunks, k=top_k)
                st.session_state["answer"] = answer_question(question, hits)
                st.session_state["answer_hits"] = hits
        if st.session_state.get("answer"):
            st.markdown(st.session_state["answer"])

    with tab3:
        query = st.text_input("Search within document", value="compliance requirements")
        if query:
            hits = retrieve(query, chunks, k=top_k)
            for h in hits:
                with st.expander(f"Page {h['page']} • relevance {h['score']:.2f}"):
                    st.write(h["text"])
                    st.caption(f"Source: {h['source']}")
else:
    st.info("Upload a PDF to start the demonstration.")
    st.markdown("### What this prototype demonstrates")
    cols = st.columns(4)
    cols[0].markdown("**📄 Document AI**\n\nPDF extraction and chunking")
    cols[1].markdown("**🔎 Retrieval**\n\nRelevant passage search")
    cols[2].markdown("**🤖 LLM**\n\nGrounded regulatory summary")
    cols[3].markdown("**🔗 Citations**\n\nPage-level evidence")
