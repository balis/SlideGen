# Outline: Data Engineering in the Age of Artificial Intelligence

**Course:** Data Engineering, Graduate Level — Lecture 7
**Duration:** 90 minutes (~60 slides at ~3 min/slide for content; non-content slides are fast)
**Learning Objectives covered:** LO1–LO10

---

## Slide 1: Title Slide
- type: TITLE
- content: "Data Engineering in the Age of AI — Data Preparation for ML, AI Agents in Pipeline Automation, and Vector Databases"; subtitle: "Lecture 7 · Graduate Data Engineering"; course name and date block

---

## Slide 2: Agenda
- type: AGENDA
- content: Ten thematic sections — (A) Why ML Changes Everything, (B) Training/Serving Skew, (C) Feature Stores & Point-in-Time Joins, (D) Reproducibility, (E) Data Quality & Observability for ML, (F) Embeddings as a Pipeline Stage, (G) Vector Databases, (H) RAG as a Two-Stage Pipeline, (I) AI Agents in Pipeline Automation, (J) Governance, Privacy & Evaluation

---

<!-- chunk-boundary: A | Why ML Changes Everything (LO1) -->
## Section A: Why ML Changes Everything (LO1)

## Slide 3: The Silent Failure Problem
- type: CONTENT
- claims: ["claim:agde:001"]
- speaker_notes_hint: Contrast with a broken dashboard: the business at least knows something is wrong; with a silently degrading model, the damage accumulates invisibly.

## Slide 4: The AI Hierarchy of Needs
- type: CONTENT
- claims: ["claim:agde:003", "claim:agde:004"]
- speaker_notes_hint: Monica Rogati's pyramid frames data infrastructure as a prerequisite to AI — 80% of data scientist time is spent in data layers, so the pyramid is not metaphor but budget allocation.

## Slide 5: BI vs. ML — A Different Contract on the Pipeline
- type: COMPARISON
- claims: ["claim:agde:001", "claim:agde:005"]
- speaker_notes_hint: BI asks "what is true now?"; ML asks "what was true when this label was created?"; the latter demands versioned, time-aware artifacts rather than a query target.

## Slide 6: Data as a Versioned, Time-Aware Artifact
- type: CONTENT
- claims: ["claim:agde:005"]
- speaker_notes_hint: Reinforce that immutability and audit trails for datasets are a first-class engineering requirement, not a nice-to-have; set up the reproducibility section later.

## Slide 7: Feature Engineering as a Stateful Pipeline Stage
- type: CONTENT
- claims: ["claim:agde:006"]
- speaker_notes_hint: The fit-time statistics (means, vocabularies, quantile boundaries) computed during training must be stored and replayed identically at inference — this is where the state lives.

## Slide 8: Code — Stateful Sklearn Pipeline (Fit vs. Transform)
- type: CODE
- claims: ["claim:agde:006"]
- code_block: Python; demonstrates a scikit-learn Pipeline with a StandardScaler — show that `.fit()` stores the mean/std, `.transform()` reapplies it, and that calling `.fit()` again on production data is the bug.
- speaker_notes_hint: Make concrete that calling fit() on inference data is the canonical stateful-transformation mistake.

---

<!-- chunk-boundary: B | Training/Serving Skew (LO2) -->
## Section B: Training/Serving Skew — The Central ML-Data Failure Mode (LO2)

## Slide 9: What Is Training/Serving Skew?
- type: CONTENT
- claims: ["claim:agde:007", "claim:agde:002"]
- speaker_notes_hint: Google identified this as a rule-of-ML production failure; emphasize that skew is not drift — it can exist from day one.

## Slide 10: Two Root Causes of Skew
- type: CONTENT
- claims: ["claim:agde:008", "claim:agde:009"]
- speaker_notes_hint: Root cause 1 is divergent code paths (training pipeline reimplements feature logic independently from serving pipeline); root cause 2 is a point-in-time correctness violation (future information leaks into training rows).

## Slide 11: Code — The Temporal Leak (Naive Join)
- type: CODE
- claims: ["claim:agde:010"]
- code_block: SQL; shows a naive JOIN of a transactions table to a customer_dim table and a labels table without a WHERE clause constraining customer attributes to those valid at or before the transaction timestamp — identify exactly which columns carry future information.
- speaker_notes_hint: Walk through the schema: transactions(tx_id, customer_id, tx_ts, amount), customer_dim(customer_id, churn_flag, credit_tier, updated_at), labels(tx_id, is_fraud, labeled_at) — the naive join pulls churn_flag as of query time, not as of tx_ts.

## Slide 12: Skew vs. Drift — Do Not Conflate Them
- type: COMPARISON
- claims: ["claim:agde:011", "claim:agde:012"]
- speaker_notes_hint: Skew is a day-one engineering defect between two environments; drift is a temporal phenomenon that develops after deployment — mixing the two leads to wrong remediation (you can't fix skew by retraining).

## Slide 13: Section Checkpoint — Skew Diagnosis Heuristic
- type: CONTENT
- claims: ["claim:agde:002", "claim:agde:007"]
- speaker_notes_hint: Pose the diagnostic question: "If I freeze the training code and replay training data through the serving pipeline, do I get the same features?" — if not, skew exists; brief pause for questions before next section.

---

<!-- chunk-boundary: C | Feature Stores and Point-in-Time Joins (LO3) -->
## Section C: Feature Stores and Point-in-Time Joins (LO3)

## Slide 14: Point-in-Time Joins — The Mechanism
- type: CONTENT
- claims: ["claim:agde:013"]
- speaker_notes_hint: Feast's as-of semantics: for each entity row retrieve the latest feature values with timestamp ≤ event_timestamp — this single constraint eliminates the temporal leak.

## Slide 15: Code — Point-in-Time Join in SQL (ANSI Window Function)
- type: CODE
- claims: ["claim:agde:017"]
- code_block: SQL; ANSI window-function implementation of a point-in-time join using ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) with a WHERE clause filtering to updated_at ≤ tx_ts.
- speaker_notes_hint: This is the portable version; note that the optimizer cannot apply a merge-join strategy so it is slower than dialect-specific ASOF JOIN.

## Slide 16: ASOF JOIN — Dialect-Specific Fast Path
- type: CODE
- claims: ["claim:agde:016"]
- code_block: SQL (DuckDB dialect); shows an ASOF JOIN between transactions and customer_dim on customer_id with inequality condition ON transactions.tx_ts >= customer_dim.updated_at — contrast with the ANSI version.
- speaker_notes_hint: Mention kdb+ origin in quantitative finance (aj operator), ClickHouse 2019 adoption, and DuckDB's hash-partition implementation that benchmarks orders of magnitude faster.

## Slide 17: Feature Store Architecture — The Three-Part Pattern
- type: DIAGRAM
- claims: ["claim:agde:014"]
- speaker_notes_hint: Diagram shows: shared feature view registry → offline store (training, historical retrieval) ← materialization → online store (serving, sub-10ms); the single transformation definition prevents skew.

## Slide 18: The Second Consistency Problem — Offline/Online Staleness
- type: CONTENT
- claims: ["claim:agde:015"]
- speaker_notes_hint: Materialization creates a window of staleness; if the job writes to only one store, eventual consistency breaks — this is the cost of having both stores.

## Slide 19: When NOT to Adopt a Feature Store
- type: CONTENT
- claims: ["claim:agde:018"]
- speaker_notes_hint: Single model, single team, batch-only inference — the online store and materialization add complexity with no benefit; simpler SQL tables with versioned transformation scripts suffice.

---

<!-- chunk-boundary: D | Reproducibility Strategy for ML Datasets (LO4) -->
## Section D: Reproducibility — One Temporal Problem at Three Layers (LO4)

## Slide 20: Reproducibility as a Three-Layer Temporal Problem
- type: CONTENT
- claims: ["claim:agde:005", "claim:agde:023"]
- speaker_notes_hint: Three layers: (1) data state at training time, (2) dataset version, (3) embedding model version — all three must be pinned together to reconstruct any artifact; emphasize this framing before diving into tools.

## Slide 21: Lakehouse Time-Travel — Delta/Iceberg Snapshots
- type: CONTENT
- claims: ["claim:agde:019", "claim:agde:020"]
- speaker_notes_hint: Iceberg snapshot ID is a sufficient reproducibility token — but retaining snapshots costs storage; VACUUM/expireSnapshots permanently destroys the ability to time-travel; operators must set an explicit retention policy.

## Slide 22: DVC — Content-Addressable Dataset Versioning
- type: CONTENT
- claims: ["claim:agde:021"]
- speaker_notes_hint: DVC stores an MD5 metafile in Git and the actual data in a remote; reproducing a dataset is git checkout + dvc pull — elegant for moderate-scale ML projects.

## Slide 23: lakeFS — Git Semantics Over Object Storage
- type: CONTENT
- claims: ["claim:agde:022"]
- speaker_notes_hint: Zero-copy branching means a terabyte dataset can be branched in milliseconds; the lakeFS commit reference is the reproducibility token analogous to a Git commit hash.

## Slide 24: Comparison — Three Reproducibility Strategies
- type: COMPARISON
- claims: ["claim:agde:021", "claim:agde:022", "claim:agde:024", "claim:agde:020"]
- speaker_notes_hint: Table: Iceberg snapshots (built-in, couples to table format, storage cost), DVC (Git-friendly, degrades at petabyte scale, no extra infra), lakeFS (large-scale, requires metadata server, zero-copy). Help students choose based on team scale and existing infrastructure.

---

<!-- chunk-boundary: E | Data Quality and Observability for ML (LO5) -->
## Section E: Data Quality and Observability for ML (LO5)

## Slide 25: Three Drift Types — Schema, Distribution, Concept
- type: CONTENT
- claims: ["claim:agde:025", "claim:agde:026"]
- speaker_notes_hint: Schema drift breaks pipelines visibly; distribution drift and concept drift degrade models silently — the decomposition P(X,Y) = P(X)·P(Y|X) makes the two silent drifts independently driftable.

## Slide 26: Measuring Distribution Drift — PSI and KL Divergence
- type: CONTENT
- claims: ["claim:agde:027", "claim:agde:028"]
- speaker_notes_hint: PSI = Σ(Cᵢ − Rᵢ) × ln(Cᵢ/Rᵢ) — walk through the thresholds (< 0.1, 0.1–0.25, > 0.25); PSI is symmetric KL (P||Q + Q||P) so it avoids the asymmetry problem.

## Slide 27: What Data Contracts Cannot Catch
- type: CONTENT
- claims: ["claim:agde:029"]
- speaker_notes_hint: Great Expectations / data contracts catch schema drift reliably but a column can pass every structural check while its distribution has shifted dramatically from what the model was trained on.

## Slide 28: The Offline-Online Metrics Trap
- type: CONTENT
- claims: ["claim:agde:030"]
- speaker_notes_hint: Documented phenomenon: offline test-set metrics improve but online A/B test metrics regress or stagnate; algorithm rankings on offline benchmarks can reverse in live experiments — always instrument both.

## Slide 29: Observability Strategy — Layered Monitoring
- type: CONTENT
- claims: ["claim:agde:029", "claim:agde:027", "claim:agde:030"]
- speaker_notes_hint: Layer 1: data contracts (schema); layer 2: distributional monitors (PSI per feature); layer 3: online model metrics (A/B test, shadow mode). Treat as a pipeline, not a one-shot validation.

---

<!-- chunk-boundary: F | Embeddings as a Pipeline Stage (LO6) -->
## Section F: Embeddings as a First-Class, Version-Sensitive Pipeline Stage (LO6)

## Slide 30: Embeddings in Context — Section Intro
- type: CONTENT
- claims: ["claim:agde:023"]
- speaker_notes_hint: Transition: now that we can reproduce data, we add another layer of versioning complexity — the embedding model itself. Every stored vector is baked to a specific model version; changing models is a hard dependency.

## Slide 31: Model Selection — Dimension, Quality, Cost Tradeoff
- type: CONTENT
- claims: ["claim:agde:031", "claim:agde:032"]
- speaker_notes_hint: OpenAI text-embedding-3-large at 256 dims (Matryoshka truncation) outperforms full 1536-dim ada-002 on MTEB — dimension is a configurable dial, not a fixed property.

## Slide 32: Batch Throughput and Rate-Limit Handling
- type: CONTENT
- claims: ["claim:agde:033", "claim:agde:034"]
- speaker_notes_hint: OpenAI Batch API: 50K inputs per batch, 50% cost discount, separate rate-limit pool; for synchronous paths, exponential backoff with jitter on HTTP 429 prevents thundering-herd retry storms.

## Slide 33: Code — Idempotent Embedding Pipeline
- type: CODE
- claims: ["claim:agde:035"]
- code_block: Python; shows a loop that (1) computes SHA-256 of source text, (2) checks embedding store for existing hash, (3) skips API call if found, (4) batches new texts in groups of 100–500 and calls embedding API, (5) stores result keyed by hash.
- speaker_notes_hint: The hash-keyed store makes the pipeline safe to re-run after partial failures — critical for large offline ingestion jobs.

## Slide 34: The Hard Dependency — Embedding Model Versioning
- type: CONTENT
- claims: ["claim:agde:023", "claim:agde:036"]
- speaker_notes_hint: Vectors from model A and model B occupy incompatible geometric spaces; mixing them produces meaningless similarity scores; upgrading the model means a full re-index of the entire corpus — 100 GPU-hours at 1M scale, weeks at 1B scale.

---

<!-- chunk-boundary: G | Vector Databases (LO7) -->
## Section G: Vector Databases — Storage and Search at Scale (LO7)

## Slide 35: Why Exact k-NN Fails at Scale
- type: CONTENT
- claims: ["claim:agde:037"]
- speaker_notes_hint: O(n·d) per query — 10⁹ SIFT descriptors = 512 GB RAM, 1000 seconds to answer one query at SSD throughput; this is why ANN indexes are necessary, not optional.

## Slide 36: ANN Index Families — HNSW, IVF, PQ, DiskANN
- type: CONTENT
- claims: ["claim:agde:038", "claim:agde:039", "claim:agde:040"]
- speaker_notes_hint: Four families: HNSW (graph, in-memory, O(log n)), IVF (partition/cluster, nprobe tradeoff), PQ (compression, 128x size reduction), DiskANN (disk-resident, 1B points on one node at >5K QPS). Each solves a different constraint.

## Slide 37: HNSW in Depth — Parameters and Recall/Latency Tradeoff
- type: CONTENT
- claims: ["claim:agde:038"]
- speaker_notes_hint: Build-time M and efConstruction set the recall ceiling; query-time efSearch is the dial — increasing from 100 to 640 lifts recall@1 from ~0.85 to ~0.97 while proportionally increasing latency; present as a tuned SLO, not a fixed property.

## Slide 38: IVF-PQ — The Memory Compression Case
- type: CONTENT
- claims: ["claim:agde:039"]
- speaker_notes_hint: For 10M × 1536-dim vectors: raw = 61.4 GB, IVF-PQ (m=48, nbits=8) = 480 MB (128x reduction); present the tradeoff table: memory ↓, recall ↓ due to quantization error, nprobe ↑ to recover recall.

## Slide 39: Recall as a Silently-Violated SLO
- type: CONTENT
- claims: ["claim:agde:041"]
- speaker_notes_hint: ANN search loses vectors without raising errors — even at efSearch producing 35ms latency, recall@1 may be only 0.9; recall also degrades as the dataset grows with fixed parameters; HNSW deletes require soft-delete tombstoning.

## Slide 40: Metadata Filtering and ANN — The Interaction Problem
- type: CONTENT
- claims: ["claim:agde:042"]
- speaker_notes_hint: Post-filter can return zero results for selective predicates; pre-filter degrades to brute force on large subsets; dedicated vector DBs (Qdrant, Weaviate) integrate filters inside HNSW traversal; pgvector uses post-filter.

## Slide 41: Choosing a Vector Store — pgvector vs. Dedicated DBs
- type: COMPARISON
- claims: ["claim:agde:043"]
- speaker_notes_hint: Decision heuristic: under 2M vectors and Postgres already in stack → pgvector; 5M+ or sub-10ms p95 latency → dedicated (Qdrant for filtered search, Pinecone for zero-ops, Milvus for billion-scale sharding); Pinecone at 3–8x cost premium.

---

<!-- chunk-boundary: H | RAG as a Two-Stage Pipeline (LO8) -->
## Section H: RAG Retrieval as a Two-Stage Data Pipeline (LO8)

## Slide 42: RAG Is Not a Single Similarity Lookup
- type: CONTENT
- claims: ["claim:agde:044", "claim:agde:045"]
- speaker_notes_hint: Frame RAG as a two-stage data pipeline: retrieval stage (recall) + reranking stage (precision); chunking is the schema-design decision that precedes both.

## Slide 43: Chunking Strategy — A Schema Design Decision
- type: CONTENT
- claims: ["claim:agde:044", "claim:agde:045"]
- speaker_notes_hint: No universal optimal chunk size: 64–128 tokens for fact-based queries, 512–1024 tokens for contextual queries; larger chunks dilute specificity, smaller chunks lose context — analogize to table granularity decisions in schema design.

## Slide 44: Hybrid Retrieval — BM25 + Dense ANN
- type: CONTENT
- claims: ["claim:agde:046", "claim:agde:047"]
- speaker_notes_hint: BM25 and dense ANN fail in complementary directions — BM25 excels on exact identifiers/codes, dense on paraphrase/semantics; RRF (SIGIR 2009, k=60) fuses ranked lists without score-incompatibility problems.

## Slide 45: Code — Reciprocal Rank Fusion
- type: CODE
- claims: ["claim:agde:047"]
- code_block: Python; implements RRF: given two ranked lists (bm25_results, ann_results), compute RRF score = Σ 1/(rank + 60) for each candidate across both lists, sort descending, return top-k.
- speaker_notes_hint: Show that RRF operates on rank positions, not raw scores — this sidesteps the problem of BM25 scores being incomparable to cosine similarities.

## Slide 46: How Hybrid Improves Recall (Numbers)
- type: CONTENT
- claims: ["claim:agde:048"]
- speaker_notes_hint: Recall@5 numbers: dense-only 0.587, BM25-only 0.644, hybrid RRF 0.695, hybrid + reranker 0.816 — the hybrid improvement comes from BM25 pulling in documents the dense retriever ranked too low.

## Slide 47: Cross-Encoder Reranking — What It Can and Cannot Do
- type: CONTENT
- claims: ["claim:agde:049", "claim:agde:050"]
- speaker_notes_hint: Reranker improves precision within the retrieved set; it cannot improve recall because documents outside the retrieval window are permanently lost; the recall ceiling is set entirely by stage 1.

## Slide 48: The Canonical Failure — Relevant Chunk Outside Top-k
- type: CONTENT
- claims: ["claim:agde:050"]
- speaker_notes_hint: The chunk was in the corpus, was retrieved by stage 1, but ranked 51st when the reranker received only 50 — silently dropped. Mitigation: increase stage-1 k (at cost of reranking latency) or improve stage-1 recall via hybrid.

---

<!-- chunk-boundary: I | AI Agents in Pipeline Automation (LO9) -->
## Section I: AI Agents in Pipeline Automation (LO9)

## Slide 49: What Is an Agent? (Precise Definition)
- type: CONTENT
- claims: ["claim:agde:051"]
- speaker_notes_hint: LLM + tools + loop + stopping condition — structurally distinct from a single LLM call (no loop) and from rule-based automation (no LLM reasoning); this definition determines when an agent is warranted vs. over-engineered.

## Slide 50: Production Case Study — The Expensive Nondeterministic Cron Job
- type: CONTENT
- claims: ["claim:agde:053"]
- speaker_notes_hint: GetOnStack 2025: $127 → $47,000 over 4 weeks; Analyzer and Verifier agents in an infinite mutual-clarification loop for 11 days; root causes: no per-agent budget ceiling, no external stopping condition. Vivid and memorable.

## Slide 51: Where Agents Earn Their Place — Bounded Problems
- type: CONTENT
- claims: ["claim:agde:052"]
- speaker_notes_hint: Ramp's policy agent handles 65% of expense approvals autonomously on a bounded, well-specified task; the survey of 1,200 deployments shows agents fail on open-ended tasks and where humans can't be removed from the loop.

## Slide 52: Data Engineering Agent Use Cases and Their Failure Modes
- type: CONTENT
- claims: ["claim:agde:057", "claim:agde:055"]
- speaker_notes_hint: Four use cases: (1) schema mapping / entity resolution, (2) text-to-SQL with verification layer (3x accuracy improvement with live metadata), (3) data-quality triage, (4) lineage / doc generation (80%+ ROUGE-1 F1, ~90% steward acceptance); each paired with its failure mode.

## Slide 53: Architectural Principle — Narrowing the Nondeterministic Boundary
- type: CONTENT
- claims: ["claim:agde:055", "claim:agde:054"]
- speaker_notes_hint: Hybrid architecture principle: deterministic components (retrieval, validation, permissions) in infrastructure with hard guarantees; nondeterministic components (reasoning, generation) constrained by tool scoping and staged decision-making. Stripe's DAG pattern: 96% helpfulness, 26% AHT reduction.

## Slide 54: Agents as DAG Nodes, Not Orchestrators
- type: DIAGRAM
- claims: ["claim:agde:054"]
- speaker_notes_hint: Diagram: data pipeline DAG with agent nodes as steps that execute within defined input/output contracts — contrasted with an agent that orchestrates the whole DAG (anti-pattern). Each agent node has bounded scope, deterministic input validation, deterministic output validation.

## Slide 55: The Autonomy Maturity Ladder
- type: CONTENT
- claims: ["claim:agde:056"]
- speaker_notes_hint: Three stages: (1) suggest-only → human reviews all outputs, (2) human-approval-gated → agent acts on high-confidence, routes edge cases, (3) bounded-autonomous → acts within policy limits with audit. Ramp's "autonomy slider" — different teams, different risk tolerances.

---

<!-- chunk-boundary: J | Governance, Privacy, and Evaluation (LO10) -->
## Section J: Governance, Privacy, and Evaluation for AI-Oriented Pipelines (LO10)

## Slide 56: Embeddings Are Derived Personal Data — GDPR Obligations
- type: CONTENT
- claims: ["claim:agde:058", "claim:agde:059"]
- speaker_notes_hint: GDPR right-to-be-forgotten must propagate to vector stores and training sets, not just source records; machine unlearning from trained weights is an open engineering problem — naive deletion from training set does not affect already-baked weights.

## Slide 57: ML Lineage Extended to Artifacts
- type: CONTENT
- claims: ["claim:agde:060"]
- speaker_notes_hint: Each model version and each vector index must record: which data snapshot, which embedding model, which code version — this audit trail is required under GDPR, EU AI Act, HIPAA, SOX; lineage tools must span source tables → ML artifacts.

## Slide 58: Least-Privilege Tool Scoping for Agents (OWASP LLM06)
- type: CONTENT
- claims: ["claim:agde:061"]
- speaker_notes_hint: OWASP LLM06:2025 (Excessive Agency): minimum permissions per tool, no downstream system access beyond task scope, all high-impact actions independently authorized and logged — treat agent tool grants like database column-level permissions.

## Slide 59: Data Poisoning and Prompt Injection as Pipeline Security Surfaces
- type: CONTENT
- claims: ["claim:agde:062"]
- speaker_notes_hint: PoisonedRAG 2024: 5 malicious documents in 2.6M-text corpus → 97% attack success rate; the knowledge base of a RAG pipeline is a new attack surface; prompt injection enters via retrieved documents, not the user prompt.

## Slide 60: Joint Evaluation — Reliability, Cost, and Latency (Not Accuracy Alone)
- type: CONTENT
- claims: ["claim:agde:063"]
- speaker_notes_hint: CLEAR framework: accuracy-optimizing agents cost 4.4–10.8× more than cost-aware alternatives with comparable performance; single-run accuracy (60%) overstates real reliability (25% across 8 runs) — always evaluate on multi-run consistency, cost-per-invocation, and latency budgets.

---

## Slide 61: Lecture Summary — Ten Key Takeaways
- type: CONTENT
- claims: ["claim:agde:001", "claim:agde:007", "claim:agde:013", "claim:agde:019", "claim:agde:027", "claim:agde:036", "claim:agde:037", "claim:agde:047", "claim:agde:051", "claim:agde:058"]
- speaker_notes_hint: One bullet per learning objective, in order — this slide doubles as a study guide. Explicitly tie each takeaway back to its LO number.

## Slide 62: Further Reading and Tooling Landscape
- type: CONTENT
- claims: ["claim:agde:014", "claim:agde:018", "claim:agde:021", "claim:agde:043"]
- speaker_notes_hint: Two-column layout: (left) papers and references cited in this lecture; (right) key tools in each category — feature stores, versioning, vector DBs, monitoring. Encourage students to bookmark the Chip Huyen blog and Anthropic agents post.

## Slide 63: Q&A and Discussion Prompts
- type: CONTENT
- claims: []
- speaker_notes_hint: Three discussion prompts: (1) "At what point in your current ETL stack would you first notice training/serving skew?" (2) "What would a minimum viable lineage system look like for a RAG pipeline under GDPR?" (3) "Where in your pipeline would you insert an agent node — and what deterministic wrapper would you put around it?"
