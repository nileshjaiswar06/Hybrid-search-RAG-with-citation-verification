# System Architecture

## 1. Overview

This project implements a multi-stage Retrieval-Augmented Generation system.

The architecture separates the system into the following stages:

```text
Document Processing
        ↓
Chunking
        ↓
Embedding
        ↓
Storage
        ↓
Retrieval
        ↓
Fusion
        ↓
Reranking
        ↓
Context Construction
        ↓
Answer Generation
        ↓
Citation Mapping
        ↓
Citation Verification
        ↓
Evaluation
```

The purpose of this architecture is to make each stage independently testable and measurable.

---

# 2. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │    PDF Documents    │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │   PDF Ingestion     │
                         │      PyMuPDF        │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Page-level Text +   │
                         │      Metadata       │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │      Chunking       │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Gemini Embeddings   │
                         └──────────┬──────────┘
                                    ↓
                 ┌─────────────────────────────────────┐
                 │       PostgreSQL + pgvector         │
                 │                                     │
                 │ Documents / Pages / Chunks / Vectors│
                 └──────────────────┬──────────────────┘
                                    ↓
                         ┌─────────────────────┐
                         │      Question       │
                         └──────────┬──────────┘
                                    ↓
                  ┌─────────────────┴─────────────────┐
                  ↓                                   ↓
        ┌─────────────────────┐             ┌─────────────────────┐
        │  Dense Retrieval    │             │   BM25 Retrieval    │
        │     pgvector        │             │    rank-bm25        │
        └──────────┬──────────┘             └──────────┬──────────┘
                   │                                   │
                   └────────────────┬──────────────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Reciprocal Rank    │
                         │      Fusion        │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Cross-Encoder      │
                         │    Reranking       │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Context Builder    │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Gemini Generation  │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Citation Mapping   │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Citation Verifier  │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Verified Answer    │
                         └─────────────────────┘
```

---

# 3. Document Ingestion

The ingestion layer converts a PDF into structured database records.

```text
PDF
 ↓
PyMuPDF
 ↓
Document
 ↓
Pages
 ↓
Text
```

The ingestion system should preserve page boundaries because page information is required later for citations.

For example:

```text
employee_policy.pdf

Page 1
 └── extracted text

Page 2
 └── extracted text

Page 3
 └── extracted text
```

---

# 4. Data Model

The logical data model is:

```text
Document
   │
   ├── Page
   │      │
   │      └── Chunk
   │             │
   │             └── Embedding
   │
   └── Metadata
```

A simplified relational representation is:

```text
documents
---------
id
filename
path
created_at


pages
-----
id
document_id
page_number
text


chunks
------
id
document_id
page_id
chunk_index
text
metadata


chunk_embeddings
-----------------
id
chunk_id
embedding
model
created_at
```

The exact implementation may combine embedding information directly into the chunk table.

---

# 5. Chunking

Raw page text is split into smaller pieces.

Example:

```text
Page
 ↓
Paragraphs
 ↓
Chunks
```

Chunking exists because sending an entire document to the model is inefficient and can exceed context limits.

Chunks should retain:

```text
document_id
page_number
chunk_index
chunk_id
text
```

This metadata is essential for later citations.

---

# 6. Embedding Pipeline

Each chunk is converted into a vector.

```text
Chunk text
    ↓
Gemini embedding model
    ↓
Embedding vector
    ↓
PostgreSQL + pgvector
```

For example:

```text
"Employees must use at least 12 characters."

        ↓

[0.021, -0.118, 0.442, ...]
```

The exact vector dimensionality depends on the selected embedding model.

The important property is that semantically related text should produce nearby vectors.

---

# 7. Dense Retrieval

When a user asks a question:

```text
"What are the password requirements?"
```

the question is converted into an embedding.

```text
Question
 ↓
Gemini embedding
 ↓
Query vector
```

The query vector is compared with stored chunk vectors using cosine similarity.

Conceptually:

```text
similarity(query_vector, chunk_vector)
```

The highest-scoring chunks become dense retrieval candidates.

---

# 8. BM25 Retrieval

BM25 performs lexical retrieval.

The question is tokenized:

```text
"What are the password requirements?"
```

into searchable terms such as:

```text
password
requirements
```

BM25 scores documents based on term frequency, inverse document frequency, and document length.

This helps with exact terminology.

For example:

```text
Query:
JWT expiration

Document:
JWT expiration policy is 30 minutes.
```

Lexical retrieval can identify the exact phrase very effectively.

---

# 9. Why Two Retrieval Systems?

Dense and lexical retrieval solve different problems.

Dense retrieval:

```text
"What rules must users follow for account credentials?"
```

can retrieve:

```text
"Password requirements for employee accounts"
```

even if the wording differs.

BM25 is stronger when exact terminology matters:

```text
Query:
OAuth2 PKCE

Document:
OAuth2 PKCE implementation requirements
```

Therefore the system combines both.

---

# 10. Reciprocal Rank Fusion

Dense retrieval and BM25 produce ranked lists.

Example:

```text
Dense:

Rank 1 → Chunk 17
Rank 2 → Chunk 42
Rank 3 → Chunk 8


BM25:

Rank 1 → Chunk 42
Rank 2 → Chunk 17
Rank 3 → Chunk 51
```

The raw scores are not directly comparable.

RRF combines rankings instead.

The standard formula is:

```text
RRF(d) = Σ 1 / (k + rank(d))
```

where:

* `d` is a document/chunk
* `rank(d)` is its rank in a retrieval list
* `k` is a constant used to reduce the influence of very high rankings

A chunk appearing near the top of multiple retrieval systems receives a strong fused score.

---

# 11. Cross-Encoder Reranking

RRF produces candidate chunks.

Those candidates are then passed to a cross-encoder.

The cross-encoder receives:

```text
(query, chunk)
```

together.

Conceptually:

```text
Question
+
Candidate Chunk
 ↓
Cross Encoder
 ↓
Relevance Score
```

Unlike the embedding model, the cross-encoder can directly examine the interaction between the query and candidate text.

---

# 12. Why Rerank Only Top-K?

A cross-encoder is more expensive than first-stage retrieval.

Therefore the architecture is:

```text
Large corpus
     ↓
Fast retrieval
     ↓
Top 20–50 candidates
     ↓
Cross-encoder
     ↓
Top 5–10 context chunks
```

This is a standard two-stage retrieval architecture.

---

# 13. Context Construction

The final ranked chunks are converted into a structured context.

Example:

```text
[1]
Document: employee_policy.pdf
Page: 4
Chunk ID: 17

Employees must use passwords containing at least
12 characters...


[2]
Document: security_policy.pdf
Page: 8
Chunk ID: 31

Passwords must be changed every 90 days...
```

The citation ID is generated by the application.

The model sees the evidence and its citation label.

---

# 14. Grounded Generation

Gemini receives:

```text
System instructions
+
User question
+
Retrieved context
```

The generation prompt should instruct the model to:

1. Answer using the provided evidence.
2. Avoid unsupported claims.
3. Cite claims using the provided citation IDs.
4. Abstain when the evidence is insufficient.

The intended behavior is:

```text
Evidence supports answer
        ↓
Answer with citation
```

or:

```text
Evidence insufficient
        ↓
"I don't know based on the provided documents."
```

---

# 15. Citation Mapping

Citation labels are controlled by Python.

Example:

```text
Context:

[1] employee_policy.pdf, page 4, chunk 17
[2] security_policy.pdf, page 8, chunk 31
```

Gemini returns:

```text
Employees must use at least 12 characters [1].
```

The application interprets:

```text
[1]
```

as a reference to the known context object.

It does not allow the model to freely generate:

```text
filename = anything.pdf
page = 999
```

This significantly reduces citation metadata hallucination.

---

# 16. Citation Verification

Citation verification happens after answer generation.

The pipeline is:

```text
Generated claim
       +
Citation
       ↓
Exact cited context
       ↓
Verification model
       ↓
Verification result
```

Possible outputs:

```text
SUPPORTED
UNSUPPORTED
INSUFFICIENT_EVIDENCE
```

Example:

```text
Claim:
Employees must use at least 12 characters.

Evidence:
"Passwords must contain at least 12 characters."

Result:
SUPPORTED
```

Another example:

```text
Claim:
Passwords must contain a special character.

Evidence:
"Passwords must contain at least 12 characters."

Result:
UNSUPPORTED
```

---

# 17. Why Verify the Exact Context?

The verifier should not search the entire database again.

Instead:

```text
Answer citation [1]
       ↓
Context object [1]
       ↓
Exact source excerpt
       ↓
Verifier
```

This ensures the verification stage checks the same evidence that was supplied to the generator.

---

# 18. Abstention

Not every question should receive an answer.

Example:

```text
Question:
What is the company's revenue in 2035?
```

If the uploaded documents contain no relevant information, the system should not manufacture an answer.

Expected behavior:

```text
I don't know based on the provided documents.
```

This behavior is evaluated separately.

---

# 19. End-to-End Query Flow

The complete query lifecycle is:

```text
User Question
      ↓
Query Embedding
      ↓
Dense Retrieval
      │
      ├──────────────┐
      ↓              ↓
pgvector           BM25
      │              │
      └──────┬───────┘
             ↓
           RRF
             ↓
      Candidate Chunks
             ↓
      Cross-Encoder
             ↓
       Ranked Chunks
             ↓
      Context Builder
             ↓
       Gemini LLM
             ↓
     Answer + Citations
             ↓
      Citation Mapping
             ↓
       Claim Extraction
             ↓
    Citation Verification
             ↓
       Final Response
```

---

# 20. Evaluation Architecture

Evaluation is separate from the production query path.

```text
Evaluation Dataset
       ↓
┌───────────────────────────────┐
│                               │
↓                               ↓
Retrieval Evaluation       Answer Evaluation
│                               │
├── Precision@K                 ├── Citation support
├── Recall@K                    ├── Abstention accuracy
├── MRR@K                       └── Manual audit
├── nDCG@K
└── Latency
```

---

# 21. Retrieval Comparison

The evaluation compares:

```text
Dense
   ↓
BM25
   ↓
Hybrid RRF
   ↓
Hybrid + Reranker
```

The purpose is not simply to report one final score.

The experiment should demonstrate whether each additional engineering component provides measurable value.

For example:

```text
Dense
   ↓
Does BM25 improve retrieval?

Hybrid
   ↓
Does reranking improve ranking quality?

Reranked
   ↓
Does better retrieval improve answer/citation quality?
```

---

# 22. Module Responsibilities

Recommended responsibility boundaries:

```text
backend/app/ingestion/
    PDF parsing and document ingestion

backend/app/chunking/
    chunk creation and metadata

backend/app/embeddings/
    embedding generation

backend/app/retrieval/
    dense retrieval
    BM25 retrieval
    RRF

backend/app/reranking/
    cross-encoder scoring

backend/app/generation/
    Gemini prompts and answer generation

backend/app/verification/
    claim extraction and citation verification

backend/app/evaluation/
    evaluation metrics and reports

backend/app/db/
    SQLAlchemy models and database access
```

This separation prevents the application from becoming one large RAG script.

---

# 23. Design Principles

## Separation of concerns

Each pipeline stage has a specific responsibility.

## Deterministic source metadata

Source metadata comes from the database rather than being generated by the LLM.

## Cheap retrieval before expensive ranking

Fast retrieval reduces the number of chunks sent to the cross-encoder.

## Evidence-first generation

The LLM receives retrieved evidence rather than relying only on its pretrained knowledge.

## Verification after generation

The system treats generation as a potentially fallible stage and performs an independent support check.

## Measurable improvements

Each retrieval component can be evaluated independently.

---

# 24. Complete System

The final system can therefore be understood as five major layers:

```text
┌─────────────────────────────────────┐
│ 1. DOCUMENT PROCESSING              │
│ PDF → Pages → Chunks → Metadata     │
├─────────────────────────────────────┤
│ 2. RETRIEVAL                        │
│ Dense + BM25 → RRF                  │
├─────────────────────────────────────┤
│ 3. RANKING                          │
│ Cross-Encoder                       │
├─────────────────────────────────────┤
│ 4. GENERATION                       │
│ Context → Gemini → Citations        │
├─────────────────────────────────────┤
│ 5. VERIFICATION                     │
│ Claims → Evidence → Verification   │
└─────────────────────────────────────┘
```

The evaluation layer measures the effectiveness of all five stages.
