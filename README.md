# ReguLens — P_167 Regulatory Circular Summarizer

A local demo for a regulatory-document intelligence project.

## Features
- Upload regulatory PDFs
- Extract text with PyMuPDF
- Chunk documents with page metadata
- TF-IDF retrieval for robust local/offline search
- Optional Gemini-powered grounded summarization
- Q&A over the uploaded circular
- Page-level source citations
- Evidence/retrieval tab for explaining the RAG pipeline

## Run on Windows
1. Install Python and make sure the Windows `py` launcher can find it (`py -0p`).
2. Open this folder in PowerShell and run `.\run_windows.bat`.
3. The script creates `.venv` with the default Python selected by `py`, installs the requirements, and starts Streamlit.
4. Add your Gemini API key to `.env` if you want Gemini summaries. The app uses `gemini-3.8-flash` by default and falls back to local retrieval if no key is configured.

To run the steps manually:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-compile -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Copy `.env.example` to `.env` to start with the configuration template.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --no-compile -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Demo strategy for tomorrow
Use a short public regulatory circular PDF. Upload it, click Generate Regulatory Summary, then ask:
- What are the key changes?
- What is the effective date?
- Which functions are affected?
- What actions are required?

If Gemini is unavailable, the app still demonstrates PDF extraction and retrieval using a local TF-IDF fallback.

## Architecture
PDF → extraction → page-aware chunking → retrieval → grounded LLM → summary/Q&A → citations

## Next upgrades
- Replace TF-IDF with sentence-transformer embeddings + FAISS/Qdrant
- OCR for scanned PDFs
- Hybrid keyword + vector retrieval
- Reranking
- PostgreSQL document store
- FastAPI backend
- Authentication/audit logs
- RAG evaluation dataset and metrics
