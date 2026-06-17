# Data Engineering in the Age of AI

**Data Preparation for ML, AI Agents in Pipeline Automation, and Vector Databases**

Lecture 7 — Data Engineering (Graduate)

<!-- Speaker: Welcome students and frame this lecture as the bridge between classical data engineering — ETL, quality contracts, batch pipelines — and the new requirements that ML and AI workloads impose on those same foundations. -->

<!-- Notes:
This lecture connects what students already know about batch ETL, data-quality contracts, and SQL-based pipelines to the additional demands that machine learning and AI systems place on data infrastructure. The central theme is that ML does not replace data engineering — it makes it harder, because failures become silent, pipelines become stateful, and temporal correctness becomes critical. We will move through ten sections, each tied to a concrete learning objective, progressing from the conceptual shift (why ML changes the data contract) through specific engineering patterns (feature stores, versioning, embeddings, vector databases, RAG pipelines) to the organisational and governance implications (agents, privacy, evaluation). By the end, students should be able to design and critique an end-to-end ML data pipeline, not just write model code.
-->

---

## Agenda

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

<!-- Speaker: Walk through the ten sections briefly, noting that each maps to a learning objective and builds on the previous one — from conceptual foundations through concrete systems to governance. -->

<!-- Notes:
The ten sections are sequenced so that each one motivates the next. We start by establishing why ML changes the rules (Section 1), then identify the central failure mode — training-serving skew (Section 2) — and the engineering pattern that prevents it — feature stores with point-in-time joins (Section 3). Sections 4 and 5 address reproducibility and quality monitoring, which are prerequisites for trustworthy pipelines. Sections 6-8 pivot to the unstructured-data world: turning text into embeddings, storing them in vector databases, and assembling RAG retrieval pipelines. Section 9 examines where AI agents fit into pipeline automation, and Section 10 closes with governance, privacy, and evaluation. Each section includes roughly two to three content slides plus a code or diagram slide where applicable.
-->