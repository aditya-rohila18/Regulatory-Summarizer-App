# ReguLens

ReguLens is a Streamlit prototype for exploring regulatory circulars. Upload a PDF to extract its text, search relevant passages, generate a Gemini assisted summary, and ask questions with page level citations.

> **Prototype notice:** ReguLens is an informational demo, not a compliance or legal decision-making system. Verify generated summaries and citations against the original circular.

## Features

- Upload a regulatory circular in PDF format.
- Extract selectable text and retain page numbers for citations.
- Split text into page aware chunks and retrieve passages with TF-IDF.
- Generate a grounded summary and answer questions with Google Gemini when configured.
- Run without a Gemini key using local retrieval and a simple extractive fallback.
- Inspect retrieved passages and relevance scores.

## How it works

```text
PDF → text extraction → page-aware chunks → TF-IDF retrieval → Gemini summary and Q&A → page citations
```

The app processes one uploaded PDF at a time. Scanned/image-only PDFs are not OCR-processed and may produce no searchable text.

## Run locally

Requirements: Python 3.10 or newer.

### Windows

The included batch file creates a virtual environment, installs dependencies, copies `.env.example` to `.env` if needed, and launches Streamlit:

```powershell
.\run_windows.bat
```

Or run the setup manually:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Gemini is optional. To enable it locally, add your key to `.env`:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

The model setting is optional; the app uses `gemini-3.8-flash` by default. Without a key, the app uses its local fallback.

## Configuration

| Name | Required | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | No | Gemini API key. Set in local `.env` or hosted app secrets to enable Gemini generation. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-3.8-flash`. |

Do not commit `.env`, API keys, or confidential documents. `.env` and uploaded PDFs under `data/` are excluded by `.gitignore`. This repository currently tracks PDF files at its root; confirm you have the right to redistribute them and that they contain no sensitive information before making the repository public.

## Data handling and limitations

- Uploaded PDF text and retrieval results are handled by the running app; the app does not provide user accounts or durable document storage.
- When Gemini is enabled, the retrieved text passages used for a summary or answer are sent to the configured Gemini API. Do not upload documents unless you are permitted to process them this way.
- Local fallback summarization is extractive and less capable than Gemini. Treat all output as a starting point and check it against the source PDF.
- The current retrieval approach uses TF-IDF, not vector embeddings. Scanned PDF OCR, multi-document workspaces, authentication, and persistent storage are not implemented.

## Project files

- `app.py` — Streamlit application and document processing pipeline.
- `requirements.txt` — Python dependencies.
- `run_windows.bat` — Windows setup and launch helper.
- `.env.example` — local configuration template.
