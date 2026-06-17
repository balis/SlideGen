# Data Engineering in the Age of AI

**Data Preparation for ML, AI Agents in Pipeline Automation, and Vector Databases**

Lecture 7 · Graduate Data Engineering

<!-- Speaker: Welcome the class and frame the scope — this lecture connects the pipeline skills they already have to the additional correctness, versioning, and architectural demands that ML and AI systems impose. -->

<!-- Notes:
This title slide sets up a lecture that spans three large, interconnected themes: preparing data correctly for ML (training/serving skew, feature stores, reproducibility, quality), using vector databases and embeddings as first-class pipeline stages, and deploying AI agents as components in automated pipelines. Students come in with solid SQL, Python, and Spark skills; the goal is to show them where those skills are necessary but no longer sufficient. The framing is deliberately practical — every section pairs a conceptual failure mode with a concrete engineering remedy.
-->

---

## Agenda

- **(A) Why ML Changes Everything** — how ML pipelines differ from BI pipelines and why silent failure is the default
- **(B) Training/Serving Skew** — the central ML-data failure mode and its two root causes
- **(C) Feature Stores & Point-in-Time Joins** — the mechanism that eliminates temporal leakage
- **(D) Reproducibility** — versioning data, datasets, and embedding models as a three-layer temporal problem
- **(E) Data Quality & Observability for ML** — schema drift, distribution drift, concept drift, and layered monitoring
- **(F) Embeddings as a Pipeline Stage** — model selection, batching, idempotency, and version coupling
- **(G) Vector Databases** — ANN index families, recall as an SLO, and metadata filtering
- **(H) RAG as a Two-Stage Pipeline** — chunking, hybrid retrieval, reranking, and recall ceilings
- **(I) AI Agents in Pipeline Automation** — where agents earn their place, failure modes, and architectural constraints
- **(J) Governance, Privacy & Evaluation** — GDPR obligations, lineage, security surfaces, and cost-aware evaluation

<!-- Speaker: Read through the ten sections briefly and note the arc: correctness problems first, then storage and search, then automation, then governance. Tell students the sections build on each other — skew in B motivates feature stores in C, which motivates reproducibility in D. -->

<!-- Notes:
The agenda slide doubles as a cognitive map for the 90-minute lecture. Sections A–E address the correctness and quality demands that ML imposes on data pipelines — problems that do not exist or are less severe in pure BI contexts. Sections F–H introduce the embedding and vector retrieval stack as a new, version-sensitive pipeline stage that most data engineers will encounter when their organization adopts RAG or semantic search. Section I examines AI agents as pipeline components, distinguishing the narrow, bounded use cases where agents add value from the open-ended tasks where they accumulate costs and failures. Section J closes with governance and evaluation — the operational and compliance layer that wraps the entire stack. Instructors may choose to break the lecture at the end of section E for a short pause or Q&A before moving into the embedding and agent material.
-->
