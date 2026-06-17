## GDPR Propagation to Derived Data

- Embeddings and trained models are derived data that can encode and leak personal information from source records [claim:agentic-de:056]
- When a trained ML model is proven to leak personal data from training, GDPR Article 17 requires not only erasing that personal data from the training set but also applying machine unlearning methods to the trained model itself; deleting the source data alone is insufficient in such cases [claim:agentic-de:055]
- Current ML artifact management systems such as MLflow provide provenance capabilities that are still rudimentary — mainly due to incomplete traces, coarse granularity, and limited query capabilities — motivating PROV-compliant lineage models that capture end-to-end relationships between data versions and model artifacts [claim:agentic-de:056]

<!-- Speaker: Emphasize the conditional on machine unlearning — the obligation arises only when leakage is proven. Transition: governance extends beyond deletion to security of the pipeline itself. -->

<!-- Notes:
This slide addresses a non-obvious GDPR implication that many practitioners miss: derived artifacts such as vector embeddings and trained model weights can memorize and re-emit personal data. The right-to-erasure obligation under Article 17 therefore cannot be satisfied merely by removing the source record from a database.

The machine unlearning obligation is conditional and important to state precisely: it is triggered when it is proven that the trained model leaks personal data. This is a meaningful threshold — not every model trained on personal data triggers it. The practical challenge is that proving leakage (e.g., via membership inference attacks or model inversion) is itself non-trivial, and unlearning techniques such as approximate unlearning via gradient ascent or exact retraining are costly at scale.

MLflow's provenance limitations are relevant here because without end-to-end lineage — knowing which training rows contributed to which model artifact — it is nearly impossible to identify all derived artifacts that must be remediated when a deletion request arrives. PROV-compliant lineage models aim to close this gap by capturing the full directed acyclic graph of data-to-model relationships.

Students with a legal background may ask whether GDPR applies to model weights; the answer depends on whether the model can be used to reconstruct or infer personal data, which is an active regulatory interpretation question.
-->

---

## Pipeline Security — Prompt Injection and Data Poisoning

- PoisonedRAG shows that injecting just five malicious texts per target question into a knowledge database of millions of clean texts achieves a 90% attack success rate, making the RAG knowledge base a practical attack surface [claim:agentic-de:057]
- LLM-based agents face privilege escalation risks: prompt injection can manipulate an agent to access sensitive data or execute commands beyond its intended scope, motivating mandatory access control frameworks with fine-grained, role-based tool permissions [claim:agentic-de:058]
- The ALARA (As Low As Reasonably Achievable) principle — adapted from nuclear safety — advocates that agents operate with the minimum access required to accomplish their designated tasks, equivalent to the NIST principle of least privilege applied to LLM tool scoping [claim:agentic-de:059]

<!-- Speaker: PoisonedRAG is a concrete, quantified result — five injected texts achieving 90% ASR makes the threat tangible. Connect ALARA to the autonomy ladder: the more autonomous the agent, the more consequential over-permissioning becomes. -->

<!-- Notes:
This slide covers two related but distinct attack surfaces: the knowledge base (poisoning) and the agent's tool access (privilege escalation via prompt injection).

PoisonedRAG's 90% attack success rate with only five injected documents is striking because it underscores that retrieval systems are not just latency concerns — they are security perimeters. In a data engineering context, a compromised ETL pipeline could write poisoned chunks into the vector store; downstream RAG answers would then be attacker-controlled. Defenses include input sanitization, signed provenance on indexed documents, and anomaly detection on retrieval patterns.

Prompt injection in agents is structurally different from SQL injection in traditional systems: the "input" is natural language and the "interpreter" is an LLM, so character-level sanitization does not work. The recommended defense is architectural — scope the agent's tool set to exactly what is needed for its task (ALARA/least privilege), so that even a successfully injected instruction cannot escalate beyond the allowed tool surface.

The ALARA analogy is pedagogically useful: nuclear safety established that minimizing radiation exposure is a design obligation, not an afterthought. The same engineering discipline should apply to agent permissions.

Common student question: "Can we just sandbox the agent?" The answer is yes, sandboxing is one layer, but tool-scope restriction is complementary — sandboxing limits what code can run; permission scoping limits which data and services can be touched.
-->

---

## Evaluating AI-Assisted Workflows — Reliability, Cost, Latency

- Sherlock demonstrates that jointly optimizing reliability, latency, and cost in agentic workflows requires selective verification: it achieves an 18.3% accuracy gain over non-verifying baselines, up to 48.7% latency reduction via speculative execution, and 26.0% cost reduction through counterfactual-guided verifier placement [claim:agentic-de:060]
- Sherlock exposes user-configurable knobs to flexibly trade off reliability, latency, and cost, establishing that these three dimensions are not independently optimizable but must be balanced as a system [claim:agentic-de:060]

<!-- Speaker: Sherlock shows that "just add verification" is not a free lunch — where and when to verify is itself an optimization problem. Connect to the broader theme: evaluation is a first-class engineering concern, not a post-hoc check. -->

<!-- Notes:
Sherlock is a research system that makes explicit what practitioners often leave implicit: in agentic workflows, verification actions (re-running a step, calling a validator, invoking a second model) each consume latency and cost while reducing error rates. The key contribution is a framework for deciding which verifications are worth their overhead.

The three numbers from the abstract are worth dwelling on: 18.3% accuracy gain (from selective verification over no verification), 48.7% latency reduction (from speculative parallel execution rather than sequential), and 26.0% cost reduction (from placing verifiers only where counterfactual analysis predicts the most impact). This demonstrates that naive "verify everything" and "verify nothing" are both dominated strategies.

For data engineering students, the practical implication is that when integrating AI agents into pipelines — for schema mapping, data quality triage, or text-to-SQL — the evaluation and monitoring infrastructure for those agents must be as carefully engineered as the agents themselves. Reliability, latency, and cost SLOs should be defined before deployment, not inferred from production incidents.

This slide also closes the loop from the "autonomy maturity ladder" slide: bounded autonomy requires continuous evaluation of whether the agent is performing within acceptable bounds, and Sherlock provides a concrete example of what that infrastructure looks like at a research level.
-->

---

## Recap and Key Takeaways

- ML systems fail silently: performance expectation violations do not raise operational alarms, unlike traditional software failures [claim:agentic-de:001]
- Training-serving skew is caused by a discrepancy between how data is handled in training and serving pipelines, or by data changes between training and serving time [claim:agentic-de:007]
- A feature store prevents skew and feature duplication through shared transformation definitions applied identically across an offline store and an online store [claim:agentic-de:015]
- Embedding benchmark reproducibility requires pinning the evaluation task protocol, the dataset revision, and the model checkpoint or API version; changing any of the three breaks result comparability [claim:agentic-de:023]
- Each embedding model defines its own coordinate system — changing the model invalidates all stored vectors and forces full re-embedding, creating de facto vendor lock-in [claim:agentic-de:033]
- ANN recall is a silently violated SLO: as a vector database grows or parameters drift, retrieval quality degrades without raising errors while latency metrics remain stable [claim:agentic-de:042]
- Agents are LLM-driven systems that dynamically direct their own processes and tool usage in a loop, distinct from workflows where LLMs follow predefined code paths [claim:agentic-de:049]

<!-- Speaker: Walk through each bullet as a one-sentence synthesis of its section. Invite students to identify which of the ten sections produced the most unexpected insight for them. -->

<!-- Notes:
This recap slide is intentionally sparse — one bullet per major section, keyed to the most foundational claim from each. The goal is not to re-teach the material but to give students a structured mental map they can use for retrieval.

The seven bullets map to sections A, B, C, D, F, G, and I respectively. Sections E (data quality/observability), H (RAG), and J (governance/security) are not represented by a dedicated recap bullet to keep the slide scannable; lecturers may choose to add a brief oral summary of those sections.

Key connections to reinforce verbally:
- Silent failure (bullet 1) motivates the entire lecture: if ML systems gave clear error signals, most of the engineering discipline covered here would be unnecessary.
- Skew (bullet 2) and feature stores (bullet 3) are two sides of the same coin: skew is the problem, feature stores are one structural solution.
- Reproducibility (bullet 4) and embedding lock-in (bullet 5) are both instances of the temporal coupling problem: what was the system state at artifact-creation time?
- Silent recall degradation (bullet 6) mirrors silent ML failure (bullet 1) at the retrieval layer.
- The agent definition (bullet 7) grounds the autonomy and governance discussion: agents are powerful precisely because they are dynamic and tool-using, which is also why they require the governance mechanisms covered in section J.
-->
