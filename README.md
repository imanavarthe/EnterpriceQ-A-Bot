# Enterprise RAG Bot

A LangGraph-powered Retrieval-Augmented Generation application for grounded question answering across HR policies, technical documentation, and compliance manuals. The Streamlit interface separates corpus administration from end-user search and exposes evidence and workflow status for every answer.

## Features

- **Two focused tabs:** Document Ingestion and Question Answering Workflow.
- **Three knowledge domains:** HR, Technical, and Compliance, with automatic or manual routing.
- **Multiple file formats:** bundled and uploaded TXT, PDF, and DOCX documents.
- **Persistent retrieval:** section-aware overlapping chunks embedded into a local Chroma collection.
- **Grounded answers:** retrieved context is graded before generation; claims cite numbered evidence chunks.
- **Safe fallback:** questions without adequate evidence return a clear refusal instead of a fabricated answer.
- **Transparent UX:** source filename, section, page, category, and graph trace are visible with each response.
- **Session conversation:** chat history persists during the active Streamlit session.

## Architecture

```text
                        INGESTION
 TXT / PDF / DOCX → loaders → chunk + metadata → embeddings → Chroma
                                                               │
                        QUESTION ANSWERING                       │
 Question → category router → filtered retrieval ───────────────┘
                                │
                                ▼
                         evidence grader
                          │           │
                       enough       weak/none
                          │           │
                          ▼           ▼
                    cited answer   safe fallback
```

The workflow is a LangGraph state machine with `route`, `retrieve`, `grade`, `generate`, and `refuse` nodes. `KnowledgeBase` isolates vector-store operations, keeping the UI independent of Chroma and making a managed vector database a straightforward production replacement. Metadata (`source`, `category`, `section`, and `page`) travels from ingestion through citation display.

Core components:

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Streamlit | Tabs, uploads, controls, chat, evidence display |
| Orchestration | LangGraph | Deterministic workflow and conditional fallback |
| Models | OpenAI via LangChain | Embeddings, evidence grading, grounded generation |
| Retrieval | Chroma | Persistent semantic vector search and category filters |
| Loaders | pypdf, python-docx | TXT/PDF/DOCX extraction |

See [DESIGN.md](DESIGN.md) for product decisions, detailed requirements, trust boundaries, and acceptance criteria.

## Quick start

Requires Python 3.10+ and an OpenAI API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY
streamlit run app.py
```

In the app, open **Document Ingestion**, select **Index bundled documents**, then move to **Question Answering Workflow** and ask a question.

## Project layout

```text
app.py                 Streamlit application
rag/config.py          Environment-backed settings
rag/ingestion.py       Loaders, metadata, and chunking
rag/store.py           Chroma persistence and retrieval
rag/workflow.py        LangGraph RAG workflow
docs/                  Bundled enterprise manuals
tests/                 Fast unit tests
DESIGN.md              Product and technical design
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | required | Model authentication |
| `OPENAI_CHAT_MODEL` | `gpt-4.1-mini` | Grading and answer model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Vector embedding model |

The index is stored in `.rag_index/` and excluded from Git. Re-indexing uses stable content-derived IDs; Chroma updates the same IDs rather than multiplying identical chunks.

## Testing

```powershell
python -m pytest
```

Tests cover deterministic section extraction and routing behavior. Before production, add a curated question/answer evaluation set, retrieval recall metrics, faithfulness checks, load tests, and end-to-end tests with a disposable vector collection.

## Production considerations

This reference build intentionally runs locally. An enterprise deployment should add SSO/RBAC, document-level permissions, tenant isolation, managed encrypted storage, malware scanning, audit logs, retention enforcement, PII/DLP controls, tracing, rate limits, model and retrieval evaluations, user feedback, and a reviewed index rebuild process. Access-control metadata must be applied as a retrieval filter—not only as a UI rule.

