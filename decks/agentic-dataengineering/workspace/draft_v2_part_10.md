## GDPR Propagation to Derived Data

- GDPR Article 17 requires not only erasing personal data from the training set but also applying machine unlearning methods to the trained model itself; deleting the source data alone is insufficient [claim:agentic-de:055]
- Current ML artifact management systems like MLflow provide provenance capabilities that are still rudimentary — mainly due to incomplete traces, coarse granularity, and limited query capabilities — motivating PROV-compliant provenance models that capture end-to-end lineage linking data versions, model artifacts, and their relationships [claim:agentic-de:056]

<!-- Speaker: Stress that embeddings and trained models are derived data — a deletion request does not stop at the source table. Connect to the lineage gap: without proper provenance, you cannot even identify which artifacts are affected. -->

<!-- Notes:
This slide addresses a gap that most data-engineering curricula overlook: GDPR obligations
do not end at the raw-data layer. When an ML model memorizes training data — a well-documented
phenomenon in large language models — the model itself becomes a container of personal data.
Article 17's "right to erasure" therefore extends to vectors stored in a vector database and
to weights in a trained model. Machine unlearning is an active research area precisely because
naive retraining from scratch is prohibitively expensive at scale.

The second point highlights that current tooling (MLflow, W&B, etc.) cannot yet answer the
query "which models and embeddings were derived from record X?" with certainty. PROV-compliant
lineage graphs would close this gap, but adoption remains limited. Students should understand
that this is not merely a legal checkbox — it is an architectural requirement that influences
how pipelines store intermediate artifacts.
-->

---

## Pipeline Security — Prompt Injection and Data Poisoning

- PoisonedRAG demonstrates that injecting just five malicious texts per target question into a knowledge database containing millions of clean texts achieves a 90% attack success rate, establishing the RAG knowledge base as a practical attack surface [claim:agentic-de:057]
- LLM-based agents face privilege escalation risks where agents are manipulated through prompt injection to access sensitive data or execute unintended commands beyond their operational scope, motivating mandatory access control frameworks that enforce fine-grained, role-based tool permissions [claim:agentic-de:058]
- The ALARA principle from nuclear safety has been adapted for multi-agent AI systems: agents should operate with the minimum access required to accomplish their designated tasks — the Principle of Least Privilege applied to LLM tool scoping [claim:agentic-de:059]

<!-- Speaker: Walk through the threat model: the knowledge base is user-writable in many systems, making poisoning trivial. Then pivot to the mitigation — least-privilege agent scoping limits blast radius even when injection succeeds. -->

<!-- Notes:
PoisonedRAG is a landmark result because it shows that the RAG knowledge base — often treated
as a trusted input — is in fact an attack surface with remarkably low barrier to exploitation.
Five injected texts among millions is a needle-in-haystack ratio that conventional data-quality
checks will not catch.

Privilege escalation via prompt injection is the agent-era analogue of SQL injection: the
control plane (the prompt) is mixed with the data plane (user input), and an attacker can
redirect agent behavior. Mandatory access control frameworks enforce that even a compromised
agent cannot exceed its role's permissions — analogous to OS-level sandboxing.

The ALARA principle provides a useful mental model: do not grant an agent access to a production
database when it only needs read access to a staging replica. Students should note that this is
not hypothetical — the SaaStr/Replit incident (covered in the autonomy-ladder slide) is a
real-world example of an agent exceeding its intended scope.
-->

---

## Evaluating AI-Assisted Workflows — Reliability, Cost, Latency

- Jointly optimizing reliability, latency, and cost in agentic workflows requires selective verification — not all agent actions need the same level of checking [claim:agentic-de:060]
- Sherlock achieves an 18.3% accuracy gain on average across benchmarks, up to 48.7% latency reduction over non-speculative execution, and 26.0% cost reduction compared to Monte Carlo search-based verification [claim:agentic-de:060]

<!-- Speaker: Emphasize the three-way trade-off: higher verification improves reliability but increases latency and cost. Sherlock's contribution is showing that counterfactual-guided placement of verifiers can improve all three simultaneously. -->

<!-- Notes:
Sherlock frames agent evaluation as a multi-objective optimization problem rather than a
single-metric benchmark. The key insight is that verification is expensive, so placing
verifiers at every step is wasteful. Instead, counterfactual analysis identifies which
steps actually benefit from verification — steps where errors propagate downstream versus
steps where errors are self-correcting.

The three reported gains each use a different baseline, which students should note carefully:
accuracy is measured on average across benchmarks (not against a single task), latency is
compared to non-speculative execution (i.e., sequential verify-then-proceed), and cost is
compared to the Monte Carlo search-based method (which explores many verification paths
randomly). This is a good example of why reading the fine print on evaluation metrics matters
in any ML/AI paper.

The user-configurable knobs Sherlock exposes allow practitioners to set their own trade-off
point — a latency-sensitive production system may accept lower verification coverage, while
a safety-critical pipeline may pay the cost for exhaustive checking.
-->

---

## Recap and Key Takeaways

- ML systems fail silently — models keep predicting while quality degrades, making performance violations harder to detect than operational failures [claim:agentic-de:001]
- Training-serving skew — divergent data handling, data changes, or feedback loops — causes prediction quality to degrade in production [claim:agentic-de:007]
- Feature stores prevent skew and duplication through shared transformation definitions across offline and online stores [claim:agentic-de:015]
- Reproducibility is a three-layer temporal problem: data state, code/pipeline state, and embedding-model version must all be pinned [claim:agentic-de:023]
- Each embedding model defines its own coordinate system — changing models invalidates every stored vector and forces full re-embedding [claim:agentic-de:033]
- ANN recall is a silently violated SLO: retrieval quality degrades without raising exceptions as the vector database grows [claim:agentic-de:042]
- Agents are LLMs in a loop with tool access — prefer the simplest solution [claim:agentic-de:049] and narrow the nondeterministic boundary with deterministic validation [claim:agentic-de:051]

<!-- Speaker: One sentence per section — use this as a quick oral review before closing. Invite questions on any section the students want to revisit. -->

<!-- Notes:
This recap distills the ten-section lecture into seven load-bearing principles. Each bullet
maps to a specific learning objective and is backed by its original claim reference, so
students can trace any statement back to its source.

The thread connecting all sections is that ML pipelines fail in ways that are qualitatively
different from traditional data pipelines: failures are silent (no crash, no error code),
temporal (the same code produces different results at different times), and compositional
(skew, drift, and recall degradation compound). The engineering response to each failure mode
follows a common pattern: make the implicit explicit (version data, pin models, log features,
measure recall) and narrow the boundary where nondeterminism can enter.

For exam preparation, students should be able to: (1) distinguish skew from drift,
(2) explain why point-in-time joins prevent leakage, (3) compare HNSW/IVF-PQ/DiskANN
trade-offs, (4) describe why hybrid search improves recall while re-ranking improves
precision, and (5) articulate the least-privilege principle for agent tool scoping.
-->