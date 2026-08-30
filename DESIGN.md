# Enterprise RAG Bot — Design Document

## 1. Product goal

Build a trustworthy internal assistant that answers natural-language questions from HR policies, technical documentation, and compliance manuals. Every substantive answer must be grounded in retrieved document chunks and show its sources. The application has two workspaces: **Document Ingestion** and **Question Answering Workflow**.

## 2. Users and jobs

- Employees: find policy answers without scanning long manuals.
- Engineers: retrieve implementation, API, deployment, and SLA details.
- Risk and compliance teams: locate controls, deadlines, owners, and incident procedures.
- Knowledge administrators: ingest documents, inspect indexing status, and rebuild the corpus.

## 3. Experience design

### Document Ingestion

The tab shows corpus metrics, the three supported categories, bundled source files, upload controls, and index actions. Users choose a category for uploaded files, then index either the bundled corpus or their uploads. Clear success/error messages communicate results.

### Question Answering Workflow

The tab presents a category selector (`Auto`, `HR`, `Technical`, `Compliance`), example prompts, a chat surface, and expandable evidence cards. A compact workflow trace makes routing and retrieval visible. Answers contain numbered source references and do not invent details when retrieval is weak.

## 4. Functional requirements

1. Load TXT, PDF, and DOCX files.
2. Preserve source filename, category, section, and page metadata.
3. Split content into overlapping chunks and create a persistent local vector index.
4. Route each question to one category or search all categories.
5. Retrieve the most relevant chunks, grade whether they are sufficient, and generate a cited answer.
6. Refuse unsupported answers and recommend a narrower question.
7. Maintain chat history for the current browser session.
8. Keep API keys in environment variables and avoid logging document contents or secrets.

## 5. Architecture

```text
Bundled files / Uploads
        │
        ▼
 loaders → metadata → chunker → OpenAI embeddings → Chroma persistence
                                                        │
Question → route category → retrieve top-k chunks ──────┘
                              │
                              ▼
                       evidence grading
                         │           │
                    sufficient    insufficient
                         │           │
                         ▼           ▼
                    cited answer   safe refusal
```

The orchestration layer is a LangGraph `StateGraph`. Nodes are deliberately small and independently testable. Chroma provides local persistence for this reference build; the `KnowledgeBase` boundary can be replaced by an enterprise vector database. OpenAI supplies embeddings and answer generation. Streamlit owns session state and presentation only.

## 6. Data and retrieval design

- Chunk size: 900 characters, 150-character overlap.
- Section-aware metadata is extracted from numbered, uppercase headings when possible.
- Retrieval uses cosine similarity through Chroma with a default `k=5`.
- Category filtering is applied before retrieval when the router or user selects a category.
- Context passed to the model is labeled `[1]`, `[2]`, etc.; the answer is instructed to cite only these labels.

## 7. Trust, security, and operations

- The model is explicitly told that retrieved text is data, not instructions, reducing prompt-injection risk.
- Uploaded content remains in the local runtime and index; production deployments should add authentication, tenant isolation, encryption, malware scanning, DLP, retention rules, and audit logging.
- No API key is written to disk by the app.
- Failures are surfaced without exposing stack traces in the UI.
- A production rollout should add retrieval/answer evaluations, feedback capture, tracing, access-control filters, and managed backups.

## 8. Acceptance criteria

- Both named tabs are visible and usable.
- The three bundled manuals can be indexed in one action.
- A question can be routed, retrieved, answered, and cited end-to-end.
- Manual category selection constrains retrieval.
- Missing configuration and empty-index states provide actionable guidance.
- Unit tests validate category routing heuristics and section extraction.

