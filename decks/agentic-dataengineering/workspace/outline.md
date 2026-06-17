# Outline: Data Engineering in the Age of AI

## Slide 1: Title Slide
- type: TITLE
- content: "Data Engineering in the Age of AI — Data Preparation for ML, AI Agents in Pipeline Automation, and Vector Databases"; subtitle: "Lecture 7 — Data Engineering (Graduate)"; course: Data Engineering
- speaker_notes_hint: Welcome students; frame this lecture as the bridge between classical data engineering (ETL, quality, contracts) and ML-era requirements.

## Slide 2: Agenda
- type: AGENDA
- content:
  1. Why ML Changes the Data Contract
  2. Training-Serving Skew
  3. Feature Stores and Point-in-Time Joins
  4. Dataset Versioning and Reproducibility
  5. Data Quality and Observability for ML
  6. Embeddings as a Pipeline Stage
  7. Vector Databases
  8. RAG Retrieval Pipelines
  9. AI Agents for Pipeline Automation
  10. Governance, Privacy, and Evaluation
- speaker_notes_hint: Ten sections mapping to ten learning objectives; each roughly 2-3 slides plus a code or diagram slide where applicable.

<!-- chunk-boundary: A | Why ML Changes the Data Contract (LO1) -->
## Section A: Why ML Changes the Data Contract

## Slide 3: Silent Failure — ML vs. BI Pipelines
- type: CONTENT
- claims: ["claim:agentic-de:001", "claim:agentic-de:005"]
- speaker_notes_hint: Contrast BI dashboards (visibly wrong when data breaks) with ML models that keep predicting silently with degraded quality; data shifts from query-target to versioned, time-aware artifact.

## Slide 4: The Data Science Hierarchy of Needs
- type: DIAGRAM
- claims: ["claim:agentic-de:003", "claim:agentic-de:004", "claim:agentic-de:002"]
- speaker_notes_hint: Show Rogati's pyramid — 70-80% of effort lives in the data layers; Sculley's small-box-of-ML-code diagram reinforces that infrastructure dwarfs the model.

## Slide 5: Feature Engineering as a Stateful Pipeline Stage
- type: CONTENT
- claims: ["claim:agentic-de:006"]
- speaker_notes_hint: Explain that transformations like standardization, one-hot encoding, and TF-IDF require fit-time statistics (means, vocabularies, quantile boundaries) that must be persisted and reapplied identically at inference — this is what makes the pipeline stateful.

<!-- chunk-boundary: B | Training-Serving Skew (LO2) -->
## Section B: Training-Serving Skew

## Slide 6: What Is Training-Serving Skew?
- type: CONTENT
- claims: ["claim:agentic-de:007", "claim:agentic-de:008"]
- speaker_notes_hint: Define skew as divergence between training and serving outputs; root cause is divergent code paths for feature engineering; prevention = reuse the same code for both.

## Slide 7: Temporal Leakage — The Naive Join Trap
- type: CODE
- claims: ["claim:agentic-de:009", "claim:agentic-de:010"]
- code_block: SQL — naive join on a transactions/customer/labels schema that leaks future information by joining without a timestamp constraint
- speaker_notes_hint: Walk through a concrete SQL example showing how a naive JOIN ON customer_id picks up future rows, inflating offline metrics but failing in production.

## Slide 8: Skew vs. Drift — Don't Conflate Them
- type: COMPARISON
- claims: ["claim:agentic-de:011", "claim:agentic-de:012"]
- speaker_notes_hint: Two-column comparison: skew is a consistency bug between two code paths (fixable by engineering); drift is P(X,Y) changing over time (requires monitoring and retraining). Students must never conflate these.

<!-- chunk-boundary: C | Feature Stores and Point-in-Time Joins (LO3) -->
## Section C: Feature Stores and Point-in-Time Joins

## Slide 9: Point-in-Time / As-Of Joins
- type: CODE
- claims: ["claim:agentic-de:013", "claim:agentic-de:014"]
- code_block: SQL — ANSI window-function approach to as-of join vs. dialect-specific ASOF JOIN (DuckDB/ClickHouse/kdb+)
- speaker_notes_hint: Show how an as-of join retrieves only features available at the label timestamp; contrast the portable ANSI approach (LATERAL + window) with the concise dialect-specific ASOF JOIN.

## Slide 10: Feature Store Architecture
- type: DIAGRAM
- claims: ["claim:agentic-de:015", "claim:agentic-de:016"]
- speaker_notes_hint: Three-part architecture: offline store, online store, shared transformation definitions. Highlight the second consistency problem — keeping offline and online stores in sync.

## Slide 11: When NOT to Adopt a Feature Store
- type: CONTENT
- claims: ["claim:agentic-de:017"]
- speaker_notes_hint: Single model, single team, or batch-only inference — a feature store adds operational complexity without proportional benefit. This is an important counterpoint to vendor hype.

<!-- chunk-boundary: D | Dataset Versioning and Reproducibility (LO4) -->
## Section D: Dataset Versioning and Reproducibility

## Slide 12: Reproducibility as a Three-Layer Temporal Problem
- type: CONTENT
- claims: ["claim:agentic-de:023"]
- speaker_notes_hint: Frame the unifying insight: point-in-time correctness, dataset versioning, and embedding-model versioning are one temporal problem at three layers — "what was the data state when this artifact was produced?"

## Slide 13: Lakehouse Time Travel — Delta Lake and Iceberg
- type: COMPARISON
- claims: ["claim:agentic-de:018", "claim:agentic-de:019"]
- speaker_notes_hint: Compare Delta Lake (version/timestamp queries, default 7-day VACUUM) with Iceberg (immutable snapshots, manifest-based metadata). Both enable time travel but differ in retention and implementation.

## Slide 14: Content-Addressable Versioning — DVC and lakeFS
- type: COMPARISON
- claims: ["claim:agentic-de:020", "claim:agentic-de:021", "claim:agentic-de:022"]
- speaker_notes_hint: DVC uses MD5 content-addressable storage for deduplication; lakeFS provides Git-like branching over object storage with zero-copy. Note the 2025 acquisition of DVC by Treeverse (lakeFS).

<!-- chunk-boundary: E | Data Quality and Observability for ML (LO5) -->
## Section E: Data Quality and Observability for ML

## Slide 15: Three Kinds of Drift
- type: CONTENT
- claims: ["claim:agentic-de:024"]
- speaker_notes_hint: Distinguish schema drift (structural), distribution drift (statistical), and concept drift (semantic) — each requires a different detection and response strategy.

## Slide 16: Distributional Validation — PSI and KL Divergence
- type: CONTENT
- claims: ["claim:agentic-de:025", "claim:agentic-de:026"]
- speaker_notes_hint: PSI quantifies distributional shift; preferred over raw KL divergence because PSI is symmetric. Walk through the binned computation and interpretation thresholds.

## Slide 17: When Contracts Are Not Enough
- type: CONTENT
- claims: ["claim:agentic-de:027", "claim:agentic-de:028", "claim:agentic-de:029"]
- speaker_notes_hint: Data contracts catch structural breaks but miss silent distributional shift; the offline-online metric gap is a concrete failure mode where offline accuracy improves but online metrics regress.

<!-- chunk-boundary: F | Embeddings as a Pipeline Stage (LO6) -->
## Section F: Embeddings as a Pipeline Stage

## Slide 18: Embedding Model Selection — Dimensions, Quality, Cost
- type: CONTENT
- claims: ["claim:agentic-de:030", "claim:agentic-de:031"]
- speaker_notes_hint: Compare text-embedding-3-small vs. -large on dimensions, MTEB score, and cost; introduce the Batch API's 50% discount with 24-hour window for bulk pipelines.

## Slide 19: Idempotent Re-Embedding and the Model Lock-In Problem
- type: CONTENT
- claims: ["claim:agentic-de:033", "claim:agentic-de:034", "claim:agentic-de:035"]
- speaker_notes_hint: Each embedding model defines its own coordinate system — changing models invalidates the entire index. Content-addressable hashing enables idempotent re-embedding by skipping unchanged chunks.

## Slide 20: Batch Throughput and Rate-Limit Handling
- type: CODE
- claims: ["claim:agentic-de:032"]
- code_block: Python — batching inputs to the OpenAI embeddings endpoint respecting the 2048-input-per-request limit, with retry/backoff for rate limits
- speaker_notes_hint: Show the practical pipeline code: chunk inputs into batches of 2048, handle rate-limit errors with exponential backoff, and write vectors to storage idempotently.

<!-- chunk-boundary: G | Vector Databases (LO7) -->
## Section G: Vector Databases

## Slide 21: Why Exact k-NN Doesn't Scale
- type: CONTENT
- claims: ["claim:agentic-de:036"]
- speaker_notes_hint: O(N*D) per query — at 100M vectors with 1536 dimensions, exact search is infeasible. This motivates approximate nearest neighbor (ANN) indexes.

## Slide 22: ANN Index Families — HNSW, IVF-PQ, DiskANN
- type: COMPARISON
- claims: ["claim:agentic-de:037", "claim:agentic-de:038", "claim:agentic-de:039"]
- speaker_notes_hint: Three-column comparison — HNSW (graph, in-memory, tuned via M/efConstruction/efSearch), IVF-PQ (partition + compression, tuned via nprobe/nbits), DiskANN (SSD-resident, billion-scale). Emphasize recall as a tuned property, not a fixed one.

## Slide 23: Metadata Filtering, Consistency, and Silent Recall Loss
- type: CONTENT
- claims: ["claim:agentic-de:040", "claim:agentic-de:042"]
- speaker_notes_hint: Pre-filtering caps recall when filter selectivity is high; post-filtering wastes compute. Recall is a silently violated SLO — no error is raised when it degrades.

## Slide 24: pgvector vs. Dedicated Vector DB
- type: COMPARISON
- claims: ["claim:agentic-de:041"]
- speaker_notes_hint: pgvector wins on operational simplicity (existing Postgres, ACID, familiar tooling); dedicated DBs win on scale and specialized features. Decision depends on dataset size and latency requirements.

<!-- chunk-boundary: H | RAG Retrieval Pipelines (LO8) -->
## Section H: RAG Retrieval Pipelines

## Slide 25: RAG as a Two-Stage Data Pipeline
- type: DIAGRAM
- claims: ["claim:agentic-de:043", "claim:agentic-de:044"]
- speaker_notes_hint: Frame RAG retrieval not as a single similarity lookup but as a pipeline: chunking (schema design) -> hybrid retrieval (sparse BM25 + dense ANN in parallel) -> fusion -> re-ranking -> top-k to LLM.

## Slide 26: Hybrid Search, RRF, and Re-Ranking
- type: CONTENT
- claims: ["claim:agentic-de:045", "claim:agentic-de:046", "claim:agentic-de:047"]
- speaker_notes_hint: RRF formula fuses ranked lists; hybrid search improves recall (surface lexical matches dense misses); cross-encoder re-ranking improves precision (reorders but cannot fix recall). Clean separation of concerns.

## Slide 27: The Top-k Cutoff Failure Mode
- type: CONTENT
- claims: ["claim:agentic-de:048"]
- speaker_notes_hint: A relevant chunk is retrieved but ranked at position k+1 — the system silently drops it. This is the canonical RAG failure that motivates larger retrieval windows and re-ranking.

<!-- chunk-boundary: I | AI Agents for Pipeline Automation (LO9) -->
## Section I: AI Agents for Pipeline Automation

## Slide 28: What Is an Agent? — A Precise Definition
- type: CONTENT
- claims: ["claim:agentic-de:049", "claim:agentic-de:054"]
- speaker_notes_hint: An agent is an LLM in a loop with tool access and a stopping condition — distinct from a single LLM call and from rule-based automation. Anthropic's guidance: prefer simplest solution, add complexity only when needed.

## Slide 29: Agent Use Cases and Failure Modes
- type: CONTENT
- claims: ["claim:agentic-de:050", "claim:agentic-de:051"]
- speaker_notes_hint: Text-to-SQL with verification layers, schema mapping, data-quality triage. Key principle: narrow the nondeterministic boundary — wrap agent output in deterministic validation, treat agents as DAG nodes not orchestrators.

## Slide 30: The Autonomy Maturity Ladder
- type: DIAGRAM
- claims: ["claim:agentic-de:052", "claim:agentic-de:053"]
- speaker_notes_hint: L1 suggest-only -> L2 human-approval-gated -> L3 bounded-autonomous. Motivate with the SaaStr/Replit incident (July 2025): an agent deleted a production database during a vibe-coding session.

<!-- chunk-boundary: J | Governance, Privacy, and Evaluation (LO10) -->
## Section J: Governance, Privacy, and Evaluation

## Slide 31: GDPR Propagation to Derived Data
- type: CONTENT
- claims: ["claim:agentic-de:055", "claim:agentic-de:056"]
- speaker_notes_hint: Embeddings and trained models are derived data that can leak source content; GDPR Article 17 deletion obligations must propagate to vectors and training sets. Current MLflow lineage is rudimentary.

## Slide 32: Pipeline Security — Prompt Injection and Data Poisoning
- type: CONTENT
- claims: ["claim:agentic-de:057", "claim:agentic-de:058", "claim:agentic-de:059"]
- speaker_notes_hint: PoisonedRAG shows 5 injected texts can reach 90%+ attack success; agents face privilege escalation via prompt injection; ALARA principle adapted from nuclear safety for least-privilege agent tool scoping.

## Slide 33: Evaluating AI-Assisted Workflows — Reliability, Cost, Latency
- type: CONTENT
- claims: ["claim:agentic-de:060"]
- speaker_notes_hint: Sherlock demonstrates joint optimization of reliability, latency, and cost in agentic workflows through selective verification — not all agent actions need the same level of checking.

## Slide 34: Recap and Key Takeaways
- type: CONTENT
- claims: ["claim:agentic-de:001", "claim:agentic-de:007", "claim:agentic-de:015", "claim:agentic-de:023", "claim:agentic-de:033", "claim:agentic-de:042", "claim:agentic-de:049"]
- speaker_notes_hint: One sentence per section — ML fails silently; skew is the central failure mode; feature stores prevent it; reproducibility is a three-layer temporal problem; embedding models lock you in; recall is a silent SLO; agents need narrow nondeterminism boundaries.
