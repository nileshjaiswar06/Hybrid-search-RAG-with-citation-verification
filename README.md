# Hybrid Search RAG with Citation Verification

A production-style Retrieval-Augmented Generation (RAG) system designed to improve retrieval quality and reduce unsupported answers.

The system combines:

* Dense semantic retrieval using Gemini embeddings
* BM25 lexical retrieval
* Reciprocal Rank Fusion (RRF)
* Cross-encoder reranking
* Grounded Gemini answer generation
* Deterministic citation mapping
* Claim-level citation verification
* Retrieval and answer evaluation

The goal is not simply to retrieve documents and ask an LLM to answer. The system explicitly separates retrieval, ranking, generation, citation mapping, and verification so that each stage can be measured and improved independently.

---

## Why This Project Exists

A basic RAG pipeline usually looks like:

```text
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
LLM
   ↓
Answer
```

This approach has several weaknesses.

Semantic search can miss:

* exact terminology
* identifiers
* error messages
* product names
* policy terms
* technical keywords

An LLM can also produce an answer that sounds convincing but is not actually supported by the retrieved context.

This project addresses those problems by combining multiple retrieval strategies and adding a verification layer after generation.

The complete pipeline is:

```text
Question
   ↓
Dense Retrieval + BM25
   ↓
Reciprocal Rank Fusion
   ↓
Cross-Encoder Reranking
   ↓
Context Construction
   ↓
Gemini Answer Generation
   ↓
Citation Mapping
   ↓
Citation Verification
   ↓
Final Answer
```

---

## Features

### Document ingestion

* PDF ingestion using PyMuPDF
* Page-level text extraction
* Document metadata preservation
* Page number preservation

### Chunking

* Text chunking with configurable chunk size
* Configurable overlap
* Stable chunk IDs
* Document/page/chunk relationships

### Embeddings

* Gemini embedding model
* Query embeddings
* Document chunk embeddings
* Vector storage using pgvector

### Retrieval

* Dense vector retrieval
* BM25 lexical retrieval
* Hybrid retrieval
* Reciprocal Rank Fusion

### Reranking

* Cross-encoder reranking
* Candidate retrieval before expensive reranking
* Top-K context selection

### Generation

* Gemini grounded answer generation
* Context-only answering
* Explicit abstention when evidence is insufficient

### Citations

Every citation is mapped to a real source chunk:

```text
[1] document.pdf — page 4 — chunk 17
```

The model does not directly invent filenames or page numbers.

### Citation verification

Generated claims are checked against the exact retrieved evidence.

Possible verification states:

```text
SUPPORTED
UNSUPPORTED
INSUFFICIENT_EVIDENCE
```

### Evaluation

The project compares:

```text
Dense
BM25
Hybrid RRF
Hybrid + Reranker
```

using retrieval metrics such as:

* Precision@K
* Recall@K
* MRR@K
* nDCG@K
* retrieval latency

Answer-level evaluation includes:

* citation support rate
* abstention accuracy
* manual citation correctness

---

# Architecture

```text
PDF Documents
      ↓
PDF Ingestion
      ↓
Page-Level Text
      ↓
Chunking + Metadata
      ↓
Gemini Embeddings
      ↓
PostgreSQL + pgvector
      ↓
 ┌───────────────┐
 │               │
 ↓               ↓
Dense           BM25
Retrieval       Retrieval
 │               │
 └───────┬───────┘
         ↓
Reciprocal Rank Fusion
         ↓
Cross-Encoder Reranking
         ↓
Top Context Chunks
         ↓
Context Builder
         ↓
Gemini Answer Generation
         ↓
Citation Mapping
         ↓
Citation Verification
         ↓
Verified Final Answer
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the detailed architecture and data flow.

---

# Tech Stack

## Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic

## Database

* PostgreSQL
* pgvector

## AI

* Gemini API
* Gemini Embeddings
* Gemini LLM generation

## Retrieval

* pgvector cosine similarity
* rank-bm25
* Reciprocal Rank Fusion

## Reranking

* Sentence Transformers
* Cross-Encoder
* MS MARCO MiniLM

## Document Processing

* PyMuPDF

## Testing

* Pytest

---

# Project Structure

```text
hybrid-search-rag/
│
├── README.md
├── ARCHITECTURE.md
├── EVALUATION.md
├── docker-compose.yml
├── requirements.txt
│
├── backend/
│   ├── app/
│   │   ├── ingestion/
│   │   ├── chunking/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   ├── reranking/
│   │   ├── generation/
│   │   ├── verification/
│   │   ├── evaluation/
│   │   ├── db/
│   │   └── .env.example
│   │ 
│   ├── tests/
│   ├── alembic/
│   └── evaluation/
│       ├── dataset.json
│       └── results/
│
├── scripts/
│   ├── ingest.py
│   ├── embed.py
│   ├── search.py
│   ├── search_bm25.py
│   ├── search_hybrid.py
│   ├── search_reranked.py
│   ├── ask.py
│   ├── ask_verified.py
│   ├── evaluate_retrieval.py
│   └── evaluate_answers.py
│
└── data/
    └── documents/
```

---

# Setup

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd hybrid-search-rag
```

---

## 2. Create a Python virtual environment

Windows:

```bash
cd backend

python -m venv .venv

.venv\Scripts\activate
```

Linux/macOS:

```bash
cd backend

python3 -m venv .venv

source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create `.env` from `.env.example`.

Example:

```env
DATABASE_URL=postgresql+psycopg2://rag_user:rag_password@localhost:5433/rag_db

GEMINI_API_KEY=your_gemini_api_key

EMBEDDING_MODEL=<your_embedding_model>
GENERATION_MODEL=<your_generation_model>
```

Never commit the real `.env` file.

---

# Database Setup

The project uses PostgreSQL with pgvector.

Start PostgreSQL:

```bash
docker compose up -d
```

Check that the database container is running:

```bash
docker compose ps
```

Run database migrations:

```bash
alembic upgrade head
```

The database stores document, page, chunk, and embedding information.

---

# Document Ingestion

Place PDFs inside:

```text
data/documents/
```

Example:

```text
data/documents/
└── employee_policy.pdf
```

Run:

```bash
python scripts/ingest.py data/documents/employee_policy.pdf
```

The ingestion pipeline:

```text
PDF
 ↓
Extract pages
 ↓
Create document record
 ↓
Create page records
 ↓
Prepare text for chunking
 ↓
Create chunks
 ↓
Store metadata
```

Each chunk retains source information such as:

```text
document_id
filename
page_number
chunk_index
chunk_id
source_text
```

---

# Generate Embeddings

After ingestion, generate embeddings:

```bash
python scripts/embed.py <document_id>
```

The embedding pipeline:

```text
Chunk text
   ↓
Gemini embedding API
   ↓
Vector
   ↓
pgvector
```

The vector is stored together with the chunk metadata.

---

# Dense Retrieval

Run semantic retrieval:

```bash
python scripts/search.py "What are the password requirements?"
```

The process is:

```text
Question
   ↓
Gemini query embedding
   ↓
pgvector cosine similarity
   ↓
Top-K chunks
```

Dense retrieval is useful when the query and source text use different wording but have similar meaning.

---

# BM25 Retrieval

Run lexical retrieval:

```bash
python scripts/search_bm25.py "password"
```

BM25 is useful for exact or near-exact terms.

For example:

```text
Query:
OAuth2 refresh token

Document:
OAuth2 refresh token expiration policy
```

Keyword retrieval can strongly match the terminology even when semantic similarity is less effective.

---

# Hybrid Retrieval

Run:

```bash
python scripts/search_hybrid.py "What are the password requirements?"
```

The system performs:

```text
Question
 ├── Dense Retrieval
 │
 └── BM25 Retrieval
          ↓
    Reciprocal Rank Fusion
          ↓
       Top-K results
```

RRF is used because dense similarity scores and BM25 scores are not directly comparable.

---

# Cross-Encoder Reranking

Run:

```bash
python scripts/search_reranked.py "What are the password requirements?"
```

The pipeline becomes:

```text
Question
   ↓
Dense Retrieval
   +
BM25 Retrieval
   ↓
RRF
   ↓
Candidate chunks
   ↓
Cross-Encoder
   ↓
Final ranked chunks
```

The cross-encoder is intentionally applied only to a limited candidate set because it is more computationally expensive than first-stage retrieval.

---

# Grounded Question Answering

Run:

```bash
python scripts/ask.py "What are the password requirements?"
```

The system:

1. Retrieves evidence.
2. Builds a context.
3. Sends the context and question to Gemini.
4. Instructs Gemini to answer using only the supplied evidence.
5. Produces citations.

---

# Verified Question Answering

Run:

```bash
python scripts/ask_verified.py "What are the password requirements?"
```

This adds the verification layer:

```text
Question
 ↓
Hybrid Retrieval
 ↓
Reranking
 ↓
Context
 ↓
Gemini
 ↓
Answer + citations
 ↓
Claim extraction
 ↓
Citation verification
 ↓
Verified response
```

---

# Citation Design

The application assigns deterministic citation labels to retrieved chunks.

Example:

```text
[1] employee_policy.pdf — page 4 — chunk 17
[2] security_policy.pdf — page 8 — chunk 31
```

The LLM receives citation IDs associated with context chunks.

Python then resolves those IDs against the database.

Therefore:

```text
LLM citation [1]
       ↓
Python citation mapping
       ↓
Real database record
       ↓
Real filename + page + chunk
```

This prevents the model from inventing arbitrary filenames or page numbers.

---

# Citation Verification

Each generated claim is checked against its cited evidence.

Example:

```text
Claim:
Employees must use at least 12 characters.

Citation:
[1]

Verification:
SUPPORTED
```

If the evidence does not support the claim:

```text
UNSUPPORTED
```

If the available evidence is insufficient:

```text
INSUFFICIENT_EVIDENCE
```

The verifier evaluates the exact context excerpt associated with the citation rather than searching the entire document again.

---

# Evaluation

The project evaluates retrieval independently from answer generation.

Four retrieval configurations are compared:

| System            | Retrieval                    |
| ----------------- | ---------------------------- |
| Dense             | Gemini embeddings + pgvector |
| BM25              | Lexical BM25                 |
| Hybrid RRF        | Dense + BM25 + RRF           |
| Hybrid + Reranker | Hybrid + cross-encoder       |

Run retrieval evaluation:

```bash
python scripts/evaluate_retrieval.py --k 5
```

Run answer/citation evaluation:

```bash
python scripts/evaluate_answers.py
```

Detailed methodology is documented in:

```text
EVALUATION.md
```

---

# Results

Results should be added only after running the evaluation scripts.

Example:

| System            | Precision@5 |  Recall@5 |     MRR@5 |    nDCG@5 |      Latency |
| ----------------- | ----------: | --------: | --------: | --------: | -----------: |
| Dense             |   `<value>` | `<value>` | `<value>` | `<value>` | `<value> ms` |
| BM25              |   `<value>` | `<value>` | `<value>` | `<value>` | `<value> ms` |
| Hybrid RRF        |   `<value>` | `<value>` | `<value>` | `<value>` | `<value> ms` |
| Hybrid + Reranker |   `<value>` | `<value>` | `<value>` | `<value>` | `<value> ms` |

Do not fabricate benchmark numbers.

---

# Tests

Run:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

Tests should cover:

* PDF ingestion
* chunking
* metadata preservation
* embedding storage
* dense retrieval
* BM25 retrieval
* RRF
* reranking
* citation mapping
* citation verification
* evaluation metrics

---

# Key Engineering Decisions

## Why pgvector?

PostgreSQL allows relational metadata and vectors to live in the same database.

This makes it easier to associate:

```text
embedding
    ↓
chunk
    ↓
page
    ↓
document
```

without maintaining a separate vector database for this project.

## Why dense + BM25?

Dense retrieval captures semantic similarity.

BM25 captures lexical similarity.

They complement each other.

## Why RRF?

Dense and BM25 scores have different scales.

RRF combines their rankings instead of directly combining incompatible scores.

## Why a cross-encoder?

First-stage retrieval should be fast.

The cross-encoder is more expensive but generally provides stronger query-document relevance scoring.

Therefore:

```text
Large corpus
 ↓
Cheap retrieval
 ↓
Small candidate set
 ↓
Expensive reranking
```

## Why deterministic citations?

The model should not be responsible for inventing source metadata.

Instead:

```text
Database chunk
 ↓
Citation ID
 ↓
LLM
 ↓
Citation ID
 ↓
Database lookup
```

## Why citation verification?

A citation existing in an answer does not automatically mean the citation supports the claim.

The verifier checks:

```text
Claim
 +
Exact cited evidence
 ↓
Support judgment
```

---

# Limitations

* BM25 is currently rebuilt in memory for the local corpus.
* Citation verification is LLM-assisted.
* Verification is not a substitute for human review.
* The current cross-encoder is primarily English-focused.
* Evaluation quality depends on manually labeled ground truth.
* The system currently targets PDF documents.
* Retrieval latency depends on database, embedding, and reranking configuration.

---

# Future Improvements

* FastAPI retrieval endpoint
* FastAPI question-answering endpoint
* Frontend document upload
* Chat interface
* Persistent BM25 index
* Metadata filtering
* Streaming responses
* Authentication
* Rate limiting
* Human feedback collection
* Retrieval analytics dashboard
* Citation-quality dashboard
* Multi-document conversational memory

---

# Project Documentation

Detailed system architecture:

```text
ARCHITECTURE.md
```

Evaluation methodology:

```text
EVALUATION.md
```

---

# License

Add the project's chosen license here.

Example:

```text
MIT License
```

---

# Author

Nilesh Jaiswar

Built as a production-oriented RAG engineering project focused on retrieval quality, grounded generation, and citation reliability.
