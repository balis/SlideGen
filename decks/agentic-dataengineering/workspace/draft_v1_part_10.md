## GDPR Propagation to Derived Data

- When a trained ML model is shown to leak personal data, GDPR Article 17 requires not only erasing the personal data from the training set but also applying machine unlearning methods to the model itself; deleting the source data alone is insufficient [claim:agentic-de:055]
- Current ML artifact management systems like MLflow provide provenance capabilities that are still rudimentary — mainly due to incomplete traces, coarse granularity, and limited query capabilities — motivating PROV-compliant provenance models that capture end-to-end lineage linking data versions, model artifacts, and their relationships [claim:agentic-de:056]

<!-- Speaker: Stress that embeddings and trained weights are derived data — deletion obligations do not stop at the source table. Current lineage tooling is not yet mature enough to automate this propagation reliably. -->

<!-- Notes:
GDPR's right to erasure (Article 17) creates a non-trivial engineering problem for ML pipelines. A trained model can memorize and leak fragments of its training data, which means simply removing a record from the training set does not guarantee that the personal data is gone from the system. Machine unlearning — retraining, fine-tuning to forget, or approximate unlearning — must be applied to the model artifact itself. This obligation extends to embedding vectors, which can sometimes be inverted to recover source text.

The provenance problem compounds this: to know which models and vectors are affected by a deletion request, you need end-to-end lineage from source records through feature transformations to model artifacts. MLflow and similar tools track runs and parameters but lack the granularity to trace a single training example through to its influence on a model checkpoint. PROV-compliant provenance models aim to close this gap by recording fine-grained relationships between data versions, transformation steps, and output artifacts.

Students should understand that this is not a hypothetical concern — GDPR enforcement actions have already addressed ML models, and the inability to demonstrate deletion compliance is a material legal risk.
-->

---

## Pipeline Security — Prompt Injection and Data Poisoning

- PoisonedRAG demonstrates that injecting just five malicious texts per target question into a knowledge database containing millions of clean texts achieves a 90%+ attack success rate, establishing the RAG knowledge base as a practical attack surface [claim:agentic-de:057]
- LLM-based agents face privilege escalation risks where agents are manipulated through prompt injection to access sensitive data or execute unintended commands beyond their operational scope, motivating mandatory access control frameworks that enforce fine-grained, role-based tool permissions [claim:agentic-de:058]
- The ALARA (As Low As Reasonably Achievable) principle from nuclear safety has been adapted for multi-agent AI systems, advocating that agents should operate with the minimum access required to accomplish their designated tasks [claim:agentic-de:059]

<!-- Speaker: Walk through PoisonedRAG's attack model first — it is surprisingly low-cost. Then pivot to agent privilege escalation and the ALARA principle as the defensive response. -->

<!-- Notes:
This slide covers two related threat models that data engineers must consider when building AI-augmented pipelines.

First, data poisoning in RAG systems: PoisonedRAG showed that an attacker who can insert just five crafted documents into a corpus of millions can reliably steer the LLM's answers for targeted questions. This is alarming because many RAG pipelines ingest from sources with weak access controls — shared knowledge bases, scraped web content, or user-contributed documents. The defense requires treating the RAG knowledge base as a security-critical data store with ingestion validation, provenance tracking, and anomaly detection on newly added content.

Second, agent privilege escalation: when an LLM agent has access to tools (database queries, API calls, file system operations), prompt injection can trick the agent into invoking tools it should not use or accessing data outside its intended scope. The mitigation mirrors classical security engineering — mandatory access control with fine-grained, role-based permissions for each tool, analogous to OS-level security models.

The ALARA principle, borrowed from nuclear safety where radiation exposure is minimized to what is reasonably achievable, provides a useful mental model: scope each agent's tool access to the minimum required for its task. This is the NIST Principle of Least Privilege applied to LLM tool scoping. Students familiar with Linux capabilities or Android permissions will recognize the pattern.
-->

---

## Evaluating AI-Assisted Workflows — Reliability, Cost, Latency

- Sherlock demonstrates that jointly optimizing reliability, latency, and cost in agentic workflows requires selective verification: it achieves an 18.3% accuracy gain over non-verifying baselines, up to 48.7% latency reduction via speculative execution, and 26.0% cost reduction through counterfactual-guided verifier placement [claim:agentic-de:060]

<!-- Speaker: Emphasize the three-way trade-off — not every agent action warrants the same level of verification. Sherlock's insight is that you can place verifiers strategically rather than uniformly. -->

<!-- Notes:
This slide introduces the idea that evaluating AI-assisted data pipelines requires optimizing across three dimensions simultaneously: reliability (does the agent produce correct results?), latency (how long does the workflow take?), and cost (how much compute and API spend is consumed?).

Sherlock's key contribution is selective verification — rather than verifying every intermediate step of an agentic workflow (which is reliable but slow and expensive) or verifying nothing (which is fast and cheap but unreliable), it uses counterfactual analysis to determine which steps benefit most from verification. Steps where the agent is likely to make consequential errors get verified; steps where errors are unlikely or low-impact are executed speculatively without verification.

The concrete numbers are instructive: an 18.3% accuracy gain shows that blind trust in agent outputs is insufficient, while 48.7% latency reduction and 26.0% cost reduction show that blanket verification is wasteful. The system exposes user-configurable knobs so that pipeline operators can adjust the trade-off based on their specific requirements — a safety-critical pipeline might favor reliability, while a batch analytics pipeline might favor throughput.

This connects back to the autonomy maturity ladder from Slide 30: as agents move from L1 (suggest-only) to L3 (bounded-autonomous), the verification strategy must evolve accordingly.
-->

---

## Recap and Key Takeaways

- ML systems fail silently — models keep predicting with degraded quality without raising operational alarms, unlike traditional software [claim:agentic-de:001]
- Training-serving skew is the central failure mode: divergent code paths between training and serving pipelines cause silent prediction degradation [claim:agentic-de:007]
- Feature stores prevent skew through a three-part architecture — offline store, online store, and shared transformation definitions [claim:agentic-de:015]
- Reproducibility is a three-layer temporal problem: data state, code/pipeline state, and embedding-model version must all be pinned to the same point in time [claim:agentic-de:023]
- Changing the embedding model invalidates every stored vector and forces full re-embedding — failure to do so produces silent retrieval degradation [claim:agentic-de:033]
- ANN recall is a silently violated SLO: retrieval quality degrades without exceptions as a vector database grows, feeding progressively weaker context to downstream consumers [claim:agentic-de:042]
- Agents are LLMs in a loop with tool access — prefer the simplest solution and narrow the nondeterministic boundary with deterministic validation [claim:agentic-de:049]

<!-- Speaker: One sentence per section to close the lecture. Emphasize the thread that connects all ten sections: silent failure is the recurring theme, and engineering discipline — not just better models — is the response. -->

<!-- Notes:
This recap slide distills the lecture into seven key messages, one per major section. The unifying theme is that ML-era data engineering is defined by silent failure modes: models that degrade without crashing, skew that inflates offline metrics but fails in production, recall that drops without raising errors, and agents that escalate privileges without explicit authorization.

The engineering response to each of these silent failures follows a common pattern: make the implicit explicit. Feature stores make transformation logic explicit and shared. Dataset versioning makes data state explicit and reproducible. Embedding versioning makes coordinate-system dependencies explicit. Recall monitoring makes retrieval quality explicit as an SLO. Agent permission frameworks make tool access explicit and auditable.

Students should leave with the understanding that the shift from traditional data engineering to ML-era data engineering is not primarily about new tools — it is about new failure modes that require new engineering disciplines. The tools (feature stores, vector databases, agent frameworks) are means to an end; the end is making silent failures visible and preventable.
-->