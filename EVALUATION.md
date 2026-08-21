# Evaluation Methodology

## 1. Purpose

This project evaluates the RAG pipeline at two levels:

1. **Retrieval quality** — whether the system retrieves the correct evidence.
2. **Answer and citation quality** — whether the generated answer is grounded in the retrieved evidence and whether the system correctly abstains when evidence is unavailable.

The retrieval experiment compares four configurations:

```text
Dense Retrieval
      ↓
BM25 Retrieval
      ↓
Hybrid RRF
      ↓
Hybrid + Cross-Encoder Reranking
```

The answer evaluation additionally measures:

* Citation support
* Abstention behavior
* Verification outcomes

The purpose of the evaluation is to determine whether each additional retrieval component provides measurable value rather than assuming that a more complex RAG architecture is automatically better.

---

# 2. Evaluation Dataset

The current evaluation dataset contains **3 cases**:

```text
Dataset size: 3
Answerable cases: 2
Unanswerable cases: 1
```

The current dataset is intentionally small because this is the initial prototype evaluation.

The evaluation cases are:

| Case ID                       | Question                                          | Relevant Chunks | Answerable |
| ----------------------------- | ------------------------------------------------- | --------------- | ---------- |
| `password_requirements`       | What are the password requirements for employees? | `[60]`          | Yes        |
| `confidential_information`    | How should confidential information be handled?   | `[60]`          | Yes        |
| `unsupported_vacation_policy` | Does the company offer unlimited vacation?        | `[]`            | No         |

The source dataset is stored in:

```text
backend/evaluation/retrieval_cases.json
```

---

# 3. Ground-Truth Definition

Ground-truth chunk IDs are manually assigned after inspecting the source documents.

The current dataset defines:

```json
[
  {
    "id": "password_requirements",
    "question": "What are the password requirements for employees?",
    "relevant_chunk_ids": [60],
    "answerable": true
  },
  {
    "id": "confidential_information",
    "question": "How should confidential information be handled?",
    "relevant_chunk_ids": [60],
    "answerable": true
  },
  {
    "id": "unsupported_vacation_policy",
    "question": "Does the company offer unlimited vacation?",
    "relevant_chunk_ids": [],
    "answerable": false
  }
]
```

## Ground-Truth Validation

Before expanding the benchmark, the manually assigned relevant chunk IDs should be rechecked.

In particular, both of the first two evaluation cases currently use:

```text
chunk_id = 60
```

for ground truth.

The `password_requirements` result confirms that chunk 60 contains password-related evidence.

However, the `confidential_information` case should be manually verified to ensure that chunk 60 actually contains sufficient evidence for confidential-information handling.

If it does not, the ground-truth label should be corrected before using this case as a benchmark.

This is important because incorrect ground truth can make retrieval metrics misleading.

---

# 4. Retrieval Systems

Four retrieval configurations were evaluated.

## 4.1 Dense Retrieval

The dense retrieval pipeline is:

```text
Question
   ↓
Gemini Query Embedding
   ↓
pgvector
   ↓
Cosine Similarity
   ↓
Top-K Chunks
```

Dense retrieval is intended to capture semantic similarity between the question and document chunks.

---

## 4.2 BM25 Retrieval

BM25 performs lexical retrieval:

```text
Question
   ↓
Tokenization
   ↓
BM25
   ↓
Top-K Chunks
```

BM25 is particularly useful when the query contains terminology that appears directly in the source documents.

---

## 4.3 Hybrid Retrieval

The hybrid system combines:

```text
             Question
             /      \
            ↓        ↓
        Dense       BM25
        Search      Search
            \        /
             ↓      ↓
          RRF Fusion
              ↓
            Top-K
```

Reciprocal Rank Fusion is used because dense similarity scores and BM25 scores are not directly comparable.

The fusion operates on rankings rather than assuming that the two retrieval scores share the same numerical scale.

---

## 4.4 Hybrid + Cross-Encoder Reranking

The reranked system extends hybrid retrieval:

```text
Question
   ↓
Dense + BM25
   ↓
RRF
   ↓
Candidate Chunks
   ↓
Cross-Encoder
   ↓
Final Ranking
   ↓
Top-K
```

The cross-encoder evaluates the query and candidate chunk together.

This is more computationally expensive than first-stage retrieval, so it is applied only after candidate retrieval.

---

# 5. Evaluation Metrics

The retrieval evaluation uses:

* Precision@5
* Recall@5
* MRR@5
* nDCG@5
* Average retrieval latency

---

## 5.1 Precision@5

Precision@5 measures the fraction of the top five retrieved chunks that are relevant.

```text
Precision@5 =
Relevant retrieved chunks / 5
```

For example, if one relevant chunk appears in the top five:

```text
Precision@5 = 1 / 5
             = 0.20
```

---

## 5.2 Recall@5

Recall@5 measures whether the required relevant chunks were retrieved.

```text
Recall@5 =
Relevant retrieved chunks
/
Total relevant chunks
```

For the current cases, each answerable question has one labeled relevant chunk.

Therefore, retrieving that chunk anywhere in the top five produces:

```text
Recall@5 = 1.0
```

---

## 5.3 MRR@5

Mean Reciprocal Rank measures how early the first relevant result appears.

For an individual query:

```text
RR = 1 / rank of first relevant result
```

Examples:

```text
Relevant at rank 1
→ RR = 1.0

Relevant at rank 2
→ RR = 0.5

Relevant at rank 4
→ RR = 0.25
```

MRR is the average reciprocal rank across evaluation cases.

---

## 5.4 nDCG@5

nDCG@5 measures ranking quality while assigning greater importance to relevant results appearing near the top.

A relevant result at rank 1 receives more ranking value than the same result appearing at rank 5.

This is useful because two systems can have identical Recall@5 while producing very different rankings.

---

## 5.5 Retrieval Latency

Latency measures the time required to perform retrieval.

The current report records latency per query and reports the average latency for each retrieval system.

Latency includes the operations performed by the corresponding retrieval implementation.

External API latency and local model execution can significantly affect the measured values.

Therefore latency should be interpreted as an engineering benchmark for the current implementation rather than a universal hardware-independent number.

---

# 6. Retrieval Results

The current retrieval evaluation uses:

```text
Dataset size: 3
Answerable cases evaluated by retrieval: 2
Top-K: 5
```

The unanswerable vacation question is not included in the retrieval summary because it has no relevant ground-truth chunk.

---

## 6.1 Summary

| System            | Precision@5 | Recall@5 | MRR@5 | nDCG@5 | Avg Latency |
| ----------------- | ----------: | -------: | ----: | -----: | ----------: |
| Dense             |       0.000 |    0.000 | 0.000 |  0.000 |  1801.40 ms |
| BM25              |       0.200 |    1.000 | 0.625 | 0.7153 |     0.38 ms |
| Hybrid RRF        |       0.200 |    1.000 | 0.625 | 0.7153 |  1561.57 ms |
| Hybrid + Reranker |       0.200 |    1.000 | 1.000 | 1.0000 |  3000.56 ms |

---

# 7. Dense Retrieval Results

Dense retrieval produced:

```text
Precision@5 = 0.000
Recall@5    = 0.000
MRR@5       = 0.000
nDCG@5      = 0.000
Avg Latency = 1801.40 ms
```

The individual retrieval results were:

### Password requirements

```text
Relevant:
[60]

Retrieved:
[]
```

Result:

```text
Precision@5 = 0
Recall@5    = 0
MRR@5       = 0
nDCG@5      = 0
```

### Confidential information

```text
Relevant:
[60]

Retrieved:
[]
```

Result:

```text
Precision@5 = 0
Recall@5    = 0
MRR@5       = 0
nDCG@5      = 0
```

## Interpretation

The current dense retrieval implementation did not return any chunks for either evaluated answerable query.

This is a significant result and should be investigated before drawing conclusions about the quality of Gemini embeddings themselves.

Potential implementation-level causes include:

* embedding dimension mismatch
* query embedding generation failure
* stored embeddings not being available
* incorrect database filtering
* incorrect pgvector query construction
* similarity threshold being too restrictive
* embedding model configuration mismatch
* document/chunk ID mapping problems

Therefore, the current result should be described as:

> Dense retrieval returned no candidates for the evaluated queries.

It should **not** be interpreted as proof that dense retrieval or Gemini embeddings are inherently ineffective.

---

# 8. BM25 Results

BM25 produced:

```text
Precision@5 = 0.200
Recall@5    = 1.000
MRR@5       = 0.625
nDCG@5      = 0.7153
Avg Latency = 0.38 ms
```

The individual results were:

### Password requirements

```text
Relevant:
[60]

Retrieved:
[60, 53, 59, 61, 51]
```

The relevant chunk was ranked first.

Therefore:

```text
Precision@5 = 0.20
Recall@5    = 1.00
MRR@5       = 1.00
nDCG@5      = 1.00
```

### Confidential information

```text
Relevant:
[60]

Retrieved:
[47, 52, 62, 60, 63]
```

The relevant chunk appeared at rank 4.

Therefore:

```text
Precision@5 = 0.20
Recall@5    = 1.00
MRR@5       = 0.25
nDCG@5      ≈ 0.4307
```

## Interpretation

BM25 successfully retrieved the labeled relevant chunk for both answerable evaluation cases.

However, the results also show why Recall alone is insufficient.

Both cases have:

```text
Recall@5 = 1.0
```

but their ranking quality differs significantly:

```text
Password:
MRR = 1.0

Confidential:
MRR = 0.25
```

The second relevant chunk was retrieved, but only at rank 4.

---

# 9. Hybrid RRF Results

Hybrid retrieval produced:

```text
Precision@5 = 0.200
Recall@5    = 1.000
MRR@5       = 0.625
nDCG@5      = 0.7153
Avg Latency = 1561.57 ms
```

The retrieved results were:

### Password requirements

```text
[60, 53, 59, 61, 51]
```

The relevant chunk was ranked first.

### Confidential information

```text
[47, 52, 62, 60, 63]
```

The relevant chunk was ranked fourth.

The hybrid metrics therefore matched the BM25 metrics in the current experiment.

---

# 10. Why Hybrid Did Not Improve Over BM25

The current result is:

```text
                 Precision  Recall  MRR    nDCG
BM25             0.20       1.00    0.625  0.7153
Hybrid RRF       0.20       1.00    0.625  0.7153
```

This does not mean RRF is useless.

The important observation is that dense retrieval returned no candidates in the current experiment.

Therefore BM25 effectively provided the useful retrieval signal.

If one retrieval branch is empty or ineffective, hybrid fusion cannot demonstrate the full benefit of combining complementary retrieval signals.

The next engineering priority should therefore be debugging dense retrieval and rerunning the experiment.

---

# 11. Hybrid Latency

The current hybrid average latency is:

```text
1561.57 ms
```

This is substantially higher than BM25:

```text
BM25:
0.38 ms

Hybrid:
1561.57 ms
```

The large difference is expected to some extent because hybrid retrieval invokes the dense retrieval pipeline in addition to BM25.

However, the exact latency should be profiled to determine how much time is spent in:

```text
Query embedding generation
Database vector search
BM25 search
RRF fusion
```

The current number should therefore be treated as an implementation benchmark.

---

# 12. Hybrid + Cross-Encoder Reranking

The reranked system produced:

```text
Precision@5 = 0.200
Recall@5    = 1.000
MRR@5       = 1.000
nDCG@5      = 1.000
Avg Latency = 3000.56 ms
```

The individual results were:

### Password requirements

```text
Relevant:
[60]

Retrieved:
[60, 53, 61, 59, 63]
```

Relevant chunk:

```text
Rank = 1
```

Therefore:

```text
Precision@5 = 0.20
Recall@5    = 1.00
MRR@5       = 1.00
nDCG@5      = 1.00
```

### Confidential information

```text
Relevant:
[60]

Retrieved:
[60, 62, 47, 53, 61]
```

Relevant chunk:

```text
Rank = 1
```

Therefore:

```text
Precision@5 = 0.20
Recall@5    = 1.00
MRR@5       = 1.00
nDCG@5      = 1.00
```

---

# 13. Effect of Reranking

The strongest positive result in the current experiment is the change from hybrid retrieval to reranked retrieval.

Before reranking:

```text
Hybrid RRF

MRR@5  = 0.625
nDCG@5 = 0.7153
```

After reranking:

```text
Hybrid + Reranker

MRR@5  = 1.000
nDCG@5 = 1.000
```

Recall remained:

```text
Recall@5 = 1.000
```

Therefore, in this small benchmark, reranking did not increase whether the relevant evidence was retrieved within the top five.

Instead, it improved **where the relevant evidence appeared**.

This is exactly the type of problem cross-encoder reranking is intended to address.

---

# 14. Reranking Latency Trade-Off

The improvement comes with a latency cost.

Current averages:

```text
BM25:
0.38 ms

Hybrid:
1561.57 ms

Hybrid + Reranker:
3000.56 ms
```

Therefore:

```text
Better ranking quality
        ↕
Higher latency
```

The reranker is significantly more expensive than BM25-only retrieval.

This demonstrates an important production engineering trade-off:

> Retrieval quality should not be evaluated independently from latency.

A production system may choose a smaller candidate set or a faster reranker if the quality improvement does not justify the additional latency.

---

# 15. Answer Evaluation

The answer evaluation contains:

```text
Case count: 3
Answerable cases: 2
Unanswerable cases: 1
```

The reported metrics are:

```text
Abstention accuracy:
0.6667

Automated citation support rate:
1.0000
```

Verification status:

```text
SUPPORTED: 2
```

---

# 16. Password Requirements Answer

Question:

```text
What are the password requirements for employees?
```

The system generated:

```text
Based on the provided documents, the password requirements for employees are:

* Rotation: Passwords must be rotated at least every 180 days [1][2].
```

Two citations were produced.

Citation 1:

```text
Source: security_policy.pdf
Page: 4
Chunk: 60
Status: SUPPORTED
```

Citation 2:

```text
Source: employee_handbook.pdf
Page: 11
Chunk: 53
Status: SUPPORTED
```

Both citations were judged supported.

This produced:

```text
Citation count = 2
Supported citations = 2
Support rate = 100%
```

---

# 17. Confidential Information Answer

Question:

```text
How should confidential information be handled?
```

The system returned:

```text
I don't know based on the provided documents.
```

The case is labeled:

```text
answerable = true
```

Therefore the system's abstention was considered incorrect for this case.

This is an important failure case.

The retrieval evaluation indicates that chunk 60 was considered relevant for this question, but the final answer pipeline still abstained.

Possible causes include:

* the answer-generation retrieval path differs from the retrieval-evaluation path
* insufficient context was passed to generation
* the generation prompt was too conservative
* the retrieved context did not contain enough usable evidence
* the ground-truth chunk assignment is incorrect
* the final context builder filtered the relevant chunk
* citation/context formatting affected generation

This case should be debugged before drawing conclusions about answer-generation quality.

---

# 18. Unsupported Vacation Policy

Question:

```text
Does the company offer unlimited vacation?
```

Ground truth:

```text
answerable = false
relevant_chunk_ids = []
```

The system returned:

```text
I don't know based on the provided documents.
```

This is the desired behavior.

The system correctly abstained rather than inventing a vacation policy.

This demonstrates the basic abstention mechanism working for an explicitly unanswerable query.

---

# 19. Abstention Accuracy

The reported result is:

```text
Abstention Accuracy = 0.6667
```

The three cases contain:

```text
1. Answerable → answered
2. Answerable → abstained
3. Unanswerable → abstained
```

Therefore the system made two correct answerability decisions out of three:

```text
2 / 3 = 0.6667
```

This is consistent with the observed behavior.

However, the raw `answer_report.json` contains an `abstention_correct` field whose meaning should be reviewed.

For an answerable case that was successfully answered, `abstention_correct` should not be interpreted as the correctness of the answer itself.

A clearer evaluation model would separately record:

```text
answerability_decision_correct
answer_correct
abstention_correct
```

This avoids conflating answer correctness with abstention behavior.

---

# 20. Automated Citation Support

The current automated citation support rate is:

```text
1.0000
```

or:

```text
100%
```

The system verified:

```text
Total citations: 2
Supported citations: 2
Unsupported citations: 0
Insufficient evidence: 0
```

Therefore:

```text
Citation Support Rate
=
2 / 2
=
1.0
=
100%
```

This is a positive result, but the sample size is extremely small.

Only two citations were evaluated.

Therefore the result should **not** be presented as evidence that the system will maintain 100% citation correctness on a larger benchmark.

The appropriate interpretation is:

> Both citations generated in the current three-case evaluation were automatically verified as supported.

---

# 21. Important Evaluation Limitation

The current benchmark is very small:

```text
3 total cases
2 answerable cases
1 unanswerable case
2 generated citations
```

This is sufficient for validating that the evaluation pipeline works, but it is not sufficient for making strong statistical claims.

The current evaluation should therefore be considered:

```text
Prototype / smoke-test benchmark
```

rather than:

```text
Production-scale benchmark
```

A stronger benchmark should contain substantially more questions.

A practical next target is:

```text
30–50 evaluation questions
```

with a stronger benchmark containing:

```text
50–100+ questions
```

---

# 22. Recommended Evaluation Categories

The expanded benchmark should include multiple question types.

## Exact terminology

Example:

```text
What is the password expiration period?
```

Useful for evaluating BM25.

## Semantic paraphrases

Example:

```text
What rules govern employee credentials?
```

Useful for evaluating dense retrieval.

## Technical terminology

Example:

```text
What is the OAuth2 PKCE requirement?
```

Useful for testing exact terminology retrieval.

## Multi-evidence questions

Example:

```text
What are the password length and expiration requirements?
```

Useful for testing recall.

## Cross-page questions

Questions requiring information from multiple chunks or pages.

## Unanswerable questions

Questions for which the documents contain no evidence.

Useful for evaluating abstention.

---

# 23. Current Findings

The current experiment produces several useful observations.

### Finding 1 — BM25 is currently the only reliable first-stage retriever

BM25 retrieved the labeled relevant chunk for both answerable retrieval cases.

```text
Recall@5 = 1.0
```

Dense retrieval returned no chunks for either case.

---

### Finding 2 — Hybrid currently matches BM25

Hybrid RRF produced the same retrieval metrics as BM25:

```text
Precision@5 = 0.20
Recall@5    = 1.00
MRR@5       = 0.625
nDCG@5      = 0.7153
```

This is likely because the dense retrieval branch currently contributes no usable candidates.

---

### Finding 3 — Reranking improved ranking position

Hybrid retrieval produced:

```text
MRR@5 = 0.625
nDCG@5 = 0.7153
```

After reranking:

```text
MRR@5 = 1.0
nDCG@5 = 1.0
```

The relevant chunk moved to rank 1 for both evaluated cases.

---

### Finding 4 — Reranking increases latency

Average latency increased from:

```text
Hybrid:
1561.57 ms
```

to:

```text
Hybrid + Reranker:
3000.56 ms
```

Therefore the reranker provides a quality improvement at a significant latency cost.

---

### Finding 5 — Citation verification worked on the current generated citations

Both evaluated citations were classified:

```text
SUPPORTED
```

giving:

```text
Automated citation support rate = 100%
```

However, only two citations were evaluated.

---

### Finding 6 — Abstention works for the unanswerable case

The vacation-policy question was correctly rejected:

```text
I don't know based on the provided documents.
```

This demonstrates that the system can avoid answering at least one unsupported question.

---

# 24. Current Failure Cases

The evaluation also identifies problems that should be addressed.

## Failure 1 — Dense retrieval returns no results

Current result:

```text
Dense Recall@5 = 0
```

This should be debugged before considering the dense branch complete.

---

## Failure 2 — Confidential-information question is incorrectly rejected

The question is labeled answerable, but the answer pipeline abstains.

This should be investigated across:

```text
retrieval
context construction
generation
answerability logic
```

---

## Failure 3 — Ground-truth chunk needs validation

Both answerable questions currently use:

```text
chunk 60
```

as their relevant chunk.

This may be valid if chunk 60 contains both pieces of evidence, but it should be manually confirmed.

---

## Failure 4 — Evaluation dataset is too small

Three cases are enough to verify the evaluation pipeline but not enough for robust benchmark claims.

---

# 25. Next Evaluation Iteration

Before presenting final benchmark results, the following steps should be completed.

```text
1. Verify chunk 60 for confidential-information case.
        ↓
2. Debug dense retrieval.
        ↓
3. Verify embedding storage and query embedding.
        ↓
4. Verify pgvector similarity search.
        ↓
5. Rerun retrieval evaluation.
        ↓
6. Fix answerability/abstention metric semantics.
        ↓
7. Expand evaluation dataset.
        ↓
8. Rerun all retrieval systems.
        ↓
9. Rerun answer and citation evaluation.
        ↓
10. Perform manual citation audit.
```

---

# 26. Evaluation Reproducibility

The following configuration should be recorded with every benchmark:

```text
Embedding model:
<configured model>

Generation model:
<configured model>

Cross-encoder:
<configured model>

Chunk size:
<configured value>

Chunk overlap:
<configured value>

Dense Top-K:
<configured value>

BM25 Top-K:
<configured value>

RRF parameters:
<configured value>

Reranker candidate count:
<configured value>

Final context size:
<configured value>

Evaluation dataset:
retrieval_cases.json
```

The exact values should be taken from the actual project configuration rather than manually guessed.

---

# 27. Raw Evaluation Reports

The evaluation scripts produce machine-readable reports.

Current reports:

```text
evaluation/
├── retrieval_report.json
└── answer_report.json
```

These reports should be retained because they contain the raw per-case evaluation information used to produce the summary tables.

The Markdown report is a human-readable interpretation of those machine-generated results.

---

# 28. Final Benchmark Table

Current measured results:

| System            | Precision@5 | Recall@5 | MRR@5 | nDCG@5 | Avg Latency |
| ----------------- | ----------: | -------: | ----: | -----: | ----------: |
| Dense             |       0.000 |    0.000 | 0.000 |  0.000 |  1801.40 ms |
| BM25              |       0.200 |    1.000 | 0.625 | 0.7153 |     0.38 ms |
| Hybrid RRF        |       0.200 |    1.000 | 0.625 | 0.7153 |  1561.57 ms |
| Hybrid + Reranker |       0.200 |    1.000 | 1.000 | 1.0000 |  3000.56 ms |

These numbers correspond to the current three-case prototype evaluation and should not be treated as final benchmark results.

---

# 29. Answer and Citation Results

Current measured results:

| Metric                          | Result |
| ------------------------------- | -----: |
| Evaluation cases                |      3 |
| Answerable cases                |      2 |
| Unanswerable cases              |      1 |
| Abstention accuracy             | 66.67% |
| Generated citations evaluated   |      2 |
| Supported citations             |      2 |
| Unsupported citations           |      0 |
| Insufficient-evidence citations |      0 |
| Automated citation support rate |   100% |

Again, the citation support result is based on only two evaluated citations.

---

# 30. Manual Audit

Automated verification should eventually be supplemented by manual review.

Recommended format:

| Case ID                       | Answer Relevant | Citation Correct | Citation Complete | Notes              |
| ----------------------------- | --------------: | ---------------: | ----------------: | ------------------ |
| `password_requirements`       |             1/0 |              1/0 |               1/0 | `<notes>`          |
| `confidential_information`    |             1/0 |              1/0 |               1/0 | `<notes>`          |
| `unsupported_vacation_policy` |             1/0 |              N/A |               N/A | Correct abstention |

For each manually audited answer:

1. Read the question.
2. Read the generated answer.
3. Inspect every citation.
4. Open the exact cited source chunk.
5. Determine whether the evidence supports the claim.
6. Determine whether important claims are properly cited.
7. Record the result.

---

# 31. What the Current Experiment Demonstrates

The current evaluation demonstrates that the project already has a functioning experimental framework capable of:

```text
✓ Comparing multiple retrieval strategies
✓ Measuring retrieval metrics
✓ Measuring retrieval latency
✓ Evaluating reranking
✓ Testing answerability
✓ Testing abstention
✓ Generating citations
✓ Verifying citations
✓ Producing machine-readable evaluation reports
```

However, the experiment also identified implementation and dataset issues that need to be resolved before the benchmark can be considered mature.

This is an expected part of building an evaluation-driven RAG system.

---

# 32. Final Interpretation

The current results should be interpreted as follows:

> On the initial three-case benchmark, BM25 successfully retrieved the labeled relevant chunk for both answerable retrieval cases, while dense retrieval returned no candidates. Hybrid RRF therefore produced the same retrieval metrics as BM25. Cross-encoder reranking improved MRR@5 from 0.625 to 1.0 and nDCG@5 from 0.7153 to 1.0, moving the relevant chunk to rank 1 for both evaluated cases, but increased average retrieval latency to approximately 3.0 seconds. The answer evaluation correctly abstained on the unanswerable vacation-policy question, while the confidential-information case exposed an answer-generation or ground-truth issue that requires further investigation. Both generated citations in the current benchmark were automatically verified as supported, although the sample contains only two citations.

The next objective is therefore not to artificially improve the reported numbers.

The next objective is to:

```text
Fix dense retrieval
      ↓
Validate ground truth
      ↓
Fix answerability evaluation semantics
      ↓
Expand the benchmark
      ↓
Rerun the experiment
      ↓
Compare quality vs latency
```

That will produce a substantially more defensible evaluation for the final project.
