## Embeddings Are Derived Personal Data — GDPR Obligations

- Embeddings and trained model weights are derived personal data under GDPR: if a trained model stores personal information or makes it reproducible, the model is subject to deletion obligations [claim:agde:058]
- Erasure requests must propagate to vector stores and training sets, not only to source records [claim:agde:058]
- Machine unlearning — removing the influence of specific training samples from already-trained weights — is required to satisfy right-to-be-forgotten requests; naive deletion from the training set does not affect weights already trained on that data [claim:agde:059]

<!-- Speaker: Stress that GDPR compliance is not satisfied by deleting rows from a source database — vectors and model weights are independent artifacts that carry the obligation. Machine unlearning is an open problem with no proven scalable solution for general models. -->

<!-- Notes:
GDPR's right to erasure (Article 17) is well-understood for transactional databases: delete the row. For ML systems it is far more complex. Embeddings of personal text or images are themselves derived personal data — a 1536-dimensional vector generated from a customer's support ticket still encodes that person's information. Deleting the source ticket does not touch the vector in the store or the model weights trained on it.

Machine unlearning is an active research area, but no production-grade, fully general solution exists at the time of writing. The Cloud Security Alliance (2025) notes that supervisory authorities expect models to be subject to deletion obligations if they store or reproduce personal information. For practitioners, this means designing systems from the start with erasure propagation paths: soft-delete in the vector store, retraining pipelines that can exclude specific data subjects, and lineage records that identify which artifact versions contain data about a given individual.

A common student misconception is that anonymization before embedding is a complete solution. Embeddings can still encode sufficient signal to re-identify individuals depending on the corpus and model, so legal counsel should be involved in any production deployment that processes personal data.
-->

---

## ML Lineage Extended to Artifacts

- ML lineage must extend beyond source tables to ML artifacts: each model version and each vector index must record which data snapshot and which embedding model version produced it [claim:agde:060]
- This audit trail satisfies requirements under GDPR, EU AI Act, HIPAA, and SOX [claim:agde:060]

<!-- Speaker: Draw the lineage graph on the board: source table → snapshot ID → training job → model version → vector index. Each arrow must be recorded. Regulatory frameworks now explicitly require this chain. -->

<!-- Notes:
Traditional data lineage tracks how a column in a report was derived from upstream tables. ML lineage must extend that chain further: a model artifact is produced from a specific data snapshot (Iceberg snapshot ID or DVC commit), using a specific embedding model version, via a specific code version. A vector index is likewise derived from a specific embedding model and corpus snapshot.

Without this extended lineage, operators cannot answer the questions regulators increasingly ask: "Which model version processed this individual's data?" "Can you prove that the data used to train this model did not include records that were subsequently subject to an erasure request?" "What data was in the knowledge base of this RAG system when it produced this output?"

The EU AI Act (in force from 2024–2026 depending on risk tier) adds documentation requirements for high-risk AI systems that overlap substantially with ML lineage. Lineage tooling (MLflow, Weights & Biases, Marquez/OpenLineage extended to ML artifacts) must be evaluated for coverage beyond traditional ETL — specifically whether they can capture embedding model version and vector index provenance.

Encourage students to think of ML artifacts as first-class versioned objects in their lineage systems, not as outputs that appear at the end of the pipeline.
-->

---

## Least-Privilege Tool Scoping for Agents (OWASP LLM06)

- OWASP LLM06:2025 (Excessive Agency) identifies least-privilege tool scoping as the primary mitigation for agentic AI systems: LLM extensions should be granted only the minimum permissions necessary [claim:agde:061]
- Agents should not access downstream systems with broader privileges than the task requires, and all high-impact actions must be independently authorized and logged [claim:agde:061]

<!-- Speaker: Analogize to database column-level permissions: just as a read-only reporting role should not have DELETE grants, an agent that reads pipeline metadata should not have write access to production tables. The OWASP framework makes this concrete for LLM tooling. -->

<!-- Notes:
OWASP LLM06:2025 (Excessive Agency) addresses a risk that is unique to agentic systems: an LLM with broad tool grants can cause unintended side-effects far beyond what any single prompt intended, either through prompt injection (an attacker causes the model to misuse its tools) or through reasoning errors that chain multiple tool calls in destructive ways.

The practical engineering response mirrors database permission design: each tool an agent is granted should have the narrowest possible scope (read-only vs. read-write, one table vs. all tables, one API endpoint vs. all endpoints). High-impact actions — deleting records, sending external communications, modifying pipeline configurations — should require a separate authorization step rather than being directly callable by the LLM in a single tool invocation.

Logging every tool call with its arguments is the audit mechanism that makes post-incident forensics possible. Without it, the GetOnStack-style cost escalation incident (slide 50) is undetectable until the billing report arrives.

Students should also understand prompt injection as a related concern: when an agent retrieves documents from a knowledge base, those documents are an attack surface. Retrieved content containing instructions can redirect the agent's tool calls — OWASP LLM01 (Prompt Injection) and LLM06 interact here.
-->

---

## Data Poisoning and Prompt Injection as Pipeline Security Surfaces

- Data poisoning is a concrete attack surface for RAG-based pipelines: the PoisonedRAG attack (2024) demonstrated that injecting five malicious texts per target question into a knowledge base of 2.6 million texts achieves a 97% attack success rate [claim:agde:062]
- The knowledge base of a RAG pipeline is a new attack surface; prompt injection can enter via retrieved documents, not only via the user prompt [claim:agde:062]

<!-- Speaker: Five documents in 2.6 million is a 0.0002% contamination rate — vanishingly small, yet sufficient for a near-perfect attack. This is the threat model that pipeline ingestion controls must defend against. -->

<!-- Notes:
PoisonedRAG (Zou et al., 2024, arXiv:2402.07867) is one of the clearest demonstrations that the retrieval knowledge base is not a passive data store — it is an active attack surface. The intuition is that an ANN retriever is optimized to return semantically relevant documents; a carefully crafted malicious document can be constructed to be retrieved for specific target queries while appearing benign to automated content filters.

The 97% attack success rate at 0.0002% contamination should recalibrate students' threat models: traditional content moderation that flags obvious spam or toxic content will not catch adversarially crafted retrieval poisoning. Defense requires ingestion-time validation of provenance (where did this document come from?), integrity controls on the vector store (can ingestion be gated to trusted sources only?), and monitoring for anomalous answer patterns.

Prompt injection via retrieval is the connection to OWASP LLM01: when an agent retrieves a document and passes it to an LLM, that document's content becomes part of the prompt. An attacker who controls even a small fraction of the knowledge base can inject instructions into retrieved context. The defense is to keep retrieved content structurally separated from system instructions — a design constraint that must be enforced at the prompt assembly layer, not just at ingestion.

This is an area of active research; students interested in AI security should follow the OWASP LLM Top 10 updates and the EMNLP/ACL proceedings on adversarial NLP.
-->

---

## Joint Evaluation — Reliability, Cost, and Latency

- AI-assisted pipeline workflows must be evaluated jointly on reliability, cost-per-invocation, and latency — not accuracy alone [claim:agde:063]
- Optimizing for accuracy alone yields agents 4.4–10.8× more expensive than cost-aware alternatives with comparable performance [claim:agde:063]
- Single-run accuracy (60%) overstates real reliability: the same agents achieve only 25% consistency across 8 runs [claim:agde:063]

<!-- Speaker: The 60% → 25% drop from single-run to 8-run consistency is the key number. It means an agent that appears to work in a demo may fail three times out of four in production. Always evaluate on multi-run consistency, cost-per-invocation, and latency budgets before deployment. -->

<!-- Notes:
The CLEAR framework paper (arXiv:2511.14136) makes a case that should feel familiar to anyone who has evaluated recommender systems: the metric you optimize in development does not predict production success unless it reflects the actual operating conditions. For agents, single-run accuracy on a benchmark is the equivalent of offline AUC — necessary but not sufficient.

The 4.4–10.8× cost multiplier for accuracy-optimized agents is the direct consequence of using larger models, more tool calls, and longer chains to squeeze out the last few percentage points of benchmark accuracy. Cost-aware alternatives that accept a small accuracy trade-off can be an order of magnitude cheaper to run in production at scale.

The 60% → 25% consistency drop is perhaps the most practically important finding: a task that the agent completes correctly when run once may fail on re-runs due to nondeterminism in sampling, different retrieved documents, or ambiguous tool call sequences. Production deployment requires testing across multiple runs with the same inputs to get a realistic reliability estimate.

For data engineering specifically: agents that automate schema mapping, data-quality triage, or lineage generation will be invoked at scale, potentially thousands of times per day. A 25% reliability rate at that scale produces a large volume of incorrect outputs. Students should budget for human review workflows even for agents that appear to work well in benchmarks.
-->

---

## Lecture Summary — Ten Key Takeaways

- ML systems fail silently — unlike software exceptions, degraded predictions accumulate without raising alarms (LO1) [claim:agde:001]
- Training-serving skew is the central ML-data failure mode; its root causes include divergent data handling between training and serving pipelines, and data changes between training and serving time (LO2) [claim:agde:007]
- Point-in-time joins eliminate temporal leakage by constraining feature values to those available at or before the event timestamp (LO3) [claim:agde:013]
- Iceberg snapshot IDs [claim:agde:019], DVC content hashes [claim:agde:021], and lakeFS commit references [claim:agde:022] are the reproducibility tokens for ML datasets; expiring snapshots permanently destroys time-travel capability [claim:agde:020] (LO4)
- PSI quantifies distributional shift per feature — values above 0.25 indicate a major population shift requiring model review (LO5) [claim:agde:027]
- Changing an embedding model requires a full re-index: vectors from different models occupy incompatible geometric spaces (LO6) [claim:agde:036]
- Exact k-NN is O(n·d) per query and infeasible at billion-vector scale; ANN indexes trade guaranteed recall for tractable latency (LO7) [claim:agde:037]
- Hybrid BM25 + dense retrieval fused via RRF is the production baseline [claim:agde:047]; a cross-encoder reranker improves precision within the retrieved set but cannot recover recall lost at stage 1 (LO8) [claim:agde:049]
- An agent is an LLM using tools in a loop with a stopping condition; treat agents as DAG nodes with bounded scope, not as open-ended orchestrators (LO9) [claim:agde:051]
- Embeddings are derived personal data under GDPR; erasure obligations propagate to vector stores and model weights, and machine unlearning is an open problem (LO10) [claim:agde:058]

<!-- Speaker: Use this slide as a study guide pointer — each bullet maps to one LO and one section of the lecture. Encourage students to re-read the section for any takeaway that is not yet clear before the exam. -->

<!-- Notes:
This summary slide serves two purposes: as a lecture closing that reinforces the throughline across ten sections, and as a student study reference that maps directly to the learning objectives.

The ordering follows the lecture arc: silent failure (why data quality matters for ML) → skew and temporal correctness (what specifically goes wrong) → feature stores (the solution pattern) → reproducibility (how to version data artifacts) → observability (how to detect drift) → embeddings (a new versioning complexity) → vector databases (the storage infrastructure) → RAG retrieval (how search pipelines work) → agents (automation with guardrails) → governance (the regulatory and security envelope).

The key through-line that connects all ten sections: ML systems require time-awareness, versioning, and provenance tracking at every layer — data, transformations, embeddings, indexes, and model artifacts — in ways that traditional BI pipelines do not. Governance obligations (GDPR, EU AI Act) extend that requirement into the legal domain.

Encourage students to identify which of these takeaways is most relevant to a system they have worked on or plan to build, and to trace how a failure in that area would manifest.
-->

---

## Further Reading and Tooling Landscape

- Feature stores: the offline/online dual-store pattern eliminates training-serving skew; adoption is not warranted for single-model, single-team, batch-only inference — simpler SQL tables with versioned scripts suffice [claim:agde:018]
- Dataset versioning: DVC for Git-friendly moderate-scale projects; lakeFS for large-scale object storage with zero-copy branching [claim:agde:021]
- Vector stores: pgvector for under ~2M vectors in an existing Postgres stack; Qdrant, Pinecone, or Milvus for larger scale or sub-20ms p95 latency requirements [claim:agde:043]

<!-- Speaker: Point students to the Chip Huyen blog (huyenchip.com) for distribution shift and monitoring, and to the Anthropic "Building Effective Agents" post for the agent architecture framework. The OWASP LLM Top 10 is updated annually and covers the security landscape. -->

<!-- Notes:
Key references by section:

Section A–B (Silent failures, skew): Chip Huyen, "Data Distribution Shifts and Monitoring" (huyenchip.com, 2022); Google, "Rules of Machine Learning" (developers.google.com).

Section C (Feature stores): Feast documentation (docs.feast.dev); Hopsworks documentation on stateful transformations.

Section D (Reproducibility): Apache Iceberg spec (iceberg.apache.org/spec); DVC documentation (doc.dvc.org); lakeFS blog on scalable ML data version control.

Section E (Observability): Evidently AI model monitoring guide; arXiv:2004.05785 (concept drift survey).

Section F (Embeddings): OpenAI embedding models announcement; arXiv:2509.23471 (Drift-Adapter, embedding model upgrade costs).

Section G (Vector databases): arXiv:1603.09320 (HNSW paper); NeurIPS 2019 DiskANN paper; pgvector vs. dedicated database comparison.

Section H (RAG): arXiv:2406.00456 (chunking granularity); SIGIR 2009 RRF paper (dl.acm.org/doi/10.1145/1571941.1572114); arXiv:2411.11767 (reranker recall ceiling).

Section I (Agents): Anthropic, "Building Effective Agents" (anthropic.com/research/building-effective-agents); ZenML LLMOps database case studies.

Section J (Governance): arXiv:2402.07867 (PoisonedRAG); arXiv:2511.14136 (CLEAR framework); OWASP Top 10 LLM 2025.
-->

---

## Q&A and Discussion Prompts

- Discussion 1: "At what point in your current ETL stack would you first notice training/serving skew — and how long would it take to detect?"
- Discussion 2: "What would a minimum viable lineage system look like for a RAG pipeline under GDPR? What artifacts must be tracked, and what does a compliant erasure workflow look like?"
- Discussion 3: "Where in a data pipeline would you insert an agent node — and what deterministic wrapper (input validation, output validation, budget ceiling, stopping condition) would you put around it?"

<!-- Speaker: Give students 2 minutes to write down their answers individually before opening the floor — this prevents the discussion from being dominated by the first person to speak. These prompts are intentionally open-ended; there are no single correct answers. -->

<!-- Notes:
These discussion prompts are designed to bridge from lecture content to practical application. Each maps to a core tension in the lecture:

Prompt 1 (skew detection) forces students to think concretely about their own systems: do they have feature monitoring in place? Is there a test harness that replays training-time transformations through the serving pipeline? The expected range of answers is wide — some students will say "we would never notice," which is the correct and sobering answer for most production systems without dedicated monitoring.

Prompt 2 (RAG lineage under GDPR) is intentionally hard. A complete answer requires: tracking which documents were in the knowledge base at the time of each query, which embedding model version encoded them, which users' data appears in the knowledge base, and how to propagate an erasure request to vector store entries, re-embed if the model was fine-tuned on personal data, and potentially retrain. Students often underestimate how far the compliance obligation extends.

Prompt 3 (agent node design) operationalizes the architectural principles from Section I. Good answers will identify a specific, bounded task (e.g., classifying data quality alerts, generating column descriptions) and specify concrete wrapper elements: what does the input contract look like? What does the output validation check? What is the per-invocation budget ceiling? What is the escalation path when the agent returns low-confidence output?

Allow 10–15 minutes for discussion; these questions have enough depth to sustain a full class discussion if time allows.
-->
