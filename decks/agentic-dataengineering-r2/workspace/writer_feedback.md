# Writer Feedback — Iteration 1 → 2

## Blocking Issues (CRITICAL + MAJOR only)

---

### Chunk 03 (slides 14–19)

**SURGICAL** — Slide "Feature Store Architecture — The Three-Part Pattern", claim:agde:014
Issue: Source (DragonflyDB) describes dual-store architecture eliminating skew through architectural separation but does not mention a "shared feature view registry" or "declared once" mechanism.
OLD: `- A feature store's offline/online/shared-transformation-definition pattern eliminates training-serving skew by enforcing that both the historical training path and the real-time serving path execute the same feature computation logic, declared once in a shared feature view registry. [claim:agde:014]`
NEW: `- A feature store's offline/online dual-store architecture eliminates training-serving skew by ensuring that both the historical training path and the real-time serving path read from the same materialized feature values, removing the divergent code-path problem. [claim:agde:014]`

---

### Chunk 07 (slides 35–41)

**SURGICAL** — Slide "HNSW in Depth — Parameters and Recall/Latency Tradeoff", claim:agde:038
Issue: Source documents efSearch range from 10 to 640 (recall 0.56 → 0.97), not from 100 to 640 (recall 0.85 → 0.97). Both the starting efSearch value and starting recall are wrong.
OLD: `- The query-time parameter efSearch is the operational dial: increasing it from 100 to 640 can improve recall@1 from ~0.85 to ~0.97 while proportionally increasing latency [claim:agde:038]`
NEW: `- The query-time parameter efSearch is the operational dial: increasing it from 10 to 640 can improve recall@1 from ~0.56 to ~0.97 while proportionally increasing latency [claim:agde:038]`

**SURGICAL** — Slide "Choosing a Vector Store — pgvector vs. Dedicated Databases", claim:agde:043
Issue: Source says "sub-20ms p95" but slide says "sub-10ms p95", halving the threshold.
OLD: `- Above 5–10M vectors or for sub-10ms p95 latency requirements, dedicated vector databases become preferable [claim:agde:043]`
NEW: `- Above 5–10M vectors or for sub-20ms p95 latency requirements, dedicated vector databases become preferable [claim:agde:043]`

---

### Chunk 08 (slides 42–48)

**REWRITE** — Slide "RAG Is Not a Single Similarity Lookup", claim:agde:044
Issue: The first bullet describes a "two-stage data pipeline" (retrieval then reranking) but cites claim:agde:044, which is the Mix-of-Granularity chunking paper and contains no description of a two-stage retrieval-reranking pipeline. The citation is mismatched to the content. Either retag the bullet to a different claim that supports the two-stage pipeline concept (claim:agde:049 covers reranker recall ceiling, claim:agde:046 covers hybrid retrieval), or restructure the bullet to match what claim:agde:044 actually states (chunking granularity).

**REWRITE** — Slide "The Canonical Failure — Relevant Chunk Outside Top-k", claim:agde:050 (all 3 bullets)
Issue: The source (arXiv:2411.11767) describes documents the first-stage bi-encoder FAILED TO RETRIEVE — a recall ceiling problem. The slide incorrectly frames this as a chunk that WAS retrieved but ranked just outside top-k. These are structurally different failures. Furthermore, bullet 3 recommends "increase the stage-1 retrieval window (higher k)" as a mitigation, but the source finds that larger reranker K actually DECREASES recall — contradicting the advice. Rewrite all three bullets to accurately describe the source's finding: the reranker cannot recover documents the first stage never retrieved, and increasing K for the reranker worsens recall. The failure is NOT about ranking position at the handoff boundary.

---

### Chunk 09 (slides 49–55)

**SURGICAL** — Slide "Production Case Study — The Expensive Nondeterministic Cron Job", claim:agde:053
Issue: (1) Agent names "Analyzer and Verifier" are fabricated — source says "Agent A" and "Agent B". (2) "$127" was a weekly cost, not a one-time starting figure.
OLD: `- In 2025, GetOnStack's multi-agent market-data research system escalated from $127 to $47,000 in API costs over four weeks due to an infinite conversation loop between two agents (Analyzer and Verifier) running undetected for 11 days [claim:agde:053]`
NEW: `- In 2025, GetOnStack's multi-agent market-data research system escalated from $127/week to $47,000 in API costs over four weeks due to an infinite conversation loop between two agents (Agent A and Agent B) running undetected for 11 days [claim:agde:053]`

**REWRITE** — Slide "The Autonomy Maturity Ladder", claim:agde:056
Issue: The draft's three stages (suggest-only / human-approval-gated / bounded-autonomous) do not match the source's three stages: (1) suggestions only, (2) autonomous for high-confidence cases, (3) human approval for edge cases. The draft invents a "bounded-autonomous" stage not in the source and collapses the source's stages 2 and 3. Rewrite to match the source's actual formulation while keeping Ramp's autonomy slider reference.

---

### Chunk 10 (slides 56–63)

**SURGICAL** — Slide "Data Poisoning and Prompt Injection as Pipeline Security Surfaces", claim:agde:062
Issue: Source says "5 malicious texts for each target question" — the draft omits "for each target question", making the attack appear far more efficient than documented.
OLD: `- Data poisoning is a concrete attack surface for RAG-based pipelines: the PoisonedRAG attack (2024) demonstrated that injecting just five malicious documents into a knowledge base of 2.6 million texts achieves a 97% attack success rate [claim:agde:062]`
NEW: `- Data poisoning is a concrete attack surface for RAG-based pipelines: the PoisonedRAG attack (2024) demonstrated that injecting five malicious texts per target question into a knowledge base of 2.6 million texts achieves a 97% attack success rate [claim:agde:062]`

**SURGICAL** — Slide "Lecture Summary — Ten Key Takeaways" (LO2), claim:agde:007
Issue: Google's three root causes are (1) divergent data handling, (2) data change between train/serve, (3) feedback loops. The bullet incorrectly attributes "point-in-time violations" to Google and drops feedback loops.
OLD: `- Training-serving skew is the central ML-data failure mode; Google identifies divergent code paths and point-in-time violations as its root causes (LO2) [claim:agde:007]`
NEW: `- Training-serving skew is the central ML-data failure mode; its root causes include divergent data handling between training and serving pipelines, and data changes between training and serving time (LO2) [claim:agde:007]`

**SURGICAL** — Slide "Lecture Summary — Ten Key Takeaways" (LO4), claim:agde:019
Issue: claim:agde:019 covers only Iceberg snapshots, but the bullet also asserts DVC hashes and lakeFS commit references. Add the correct claim citations.
OLD: `- Iceberg snapshot IDs, DVC hashes, and lakeFS commit references are the reproducibility tokens for ML datasets; expiring snapshots permanently destroys the ability to reconstruct a training run (LO4) [claim:agde:019]`
NEW: `- Iceberg snapshot IDs [claim:agde:019], DVC content hashes [claim:agde:021], and lakeFS commit references [claim:agde:022] are the reproducibility tokens for ML datasets; expiring snapshots permanently destroys time-travel capability [claim:agde:020] (LO4)`

**REWRITE** — Slide "Further Reading and Tooling Landscape", claim:agde:014
Issue: Source for claim:agde:014 does not mention Feast, Hopsworks, or specific product capabilities. Restructure this bullet to either remove the specific product claims or cite different sources. The factual content about Feast/Hopsworks is pedagogically useful but cannot be attributed to claim:agde:014.
