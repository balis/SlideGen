# Writer Feedback — Iteration 2 → 3

## Slide "Skew vs. Drift — Don't Conflate Them" (slides 6-8, chunk 2)

### [claim:agentic-de:011] "When" row — MAJOR
**Problem:** The bullet "Can exist from day one of deployment" is not stated in the TFDV source. The source describes causes of distribution skew (different corpora, faulty sampling) but says nothing about when skew manifests relative to deployment.
**Fix:** Rewrite the "When" row to: "When: Distribution skew exists when the training and serving data distributions diverge — which can occur due to a different training corpus or a faulty sampling mechanism at data collection time [claim:agentic-de:011]"

### [claim:agentic-de:011] "What" row — MINOR (fold in)
**Problem:** Source frames skew as a data-distribution difference, not a "code path" mismatch. "Consistency mismatch between training and serving code paths" is not supported by the TFDV source.
**Fix:** Rewrite to: "What: a difference in feature value distributions between training and serving data [claim:agentic-de:011]"

### [claim:agentic-de:011] "Root cause" row — MINOR (fold in)
**Problem:** Source does not say "engineering bug" or "divergent pipelines." It attributes skew to a different corpus or faulty sampling.
**Fix:** Rewrite to: "Root cause: using a different training corpus or a faulty sampling mechanism [claim:agentic-de:011]"

### [claim:agentic-de:012] "When" row — MINOR (fold in)
**Problem:** "Emerges gradually after a model that initially performed well" is an interpretation not in the source. Source says data changes "over time" but does not describe gradual emergence.
**Fix:** Rewrite to: "When: concept drift is a temporal phenomenon — the statistical properties of the target variable change over time [claim:agentic-de:012]"

---

## Slide "Reproducibility as a Three-Layer Temporal Problem" and "Content-Addressable Versioning — DVC and lakeFS" (slides 12-14, chunk 4)

### [claim:agentic-de:023] first bullet — MAJOR
**Problem:** The MTEB source's three versioning types (task/evaluation protocol, dataset revision, model checkpoint) are remapped onto "code/pipeline state (Git commits), data state (lakehouse snapshots), embedding-model version" — the first remapping ("task versioning -> Git commits") has no basis in the source. The source is scoped to embedding benchmark reproducibility, not general ML pipelines.
**Fix:** Either (a) rewrite to match the source scope: "Embedding benchmark reproducibility requires pinning three components: the evaluation task protocol, the dataset revision, and the model checkpoint or API version [claim:agentic-de:023]" — then add a separate, unsourced framing sentence about general ML reproducibility, or (b) remove the citation if the general framing is preferred and no supporting source exists.

### [claim:agentic-de:023] second bullet — MINOR (fold in)
**Problem:** "Re-running a pipeline on 'the same data' can produce different results" is a reasonable inference but not explicitly stated. The causal re-execution framing goes beyond the source.
**Fix:** Rewrite to: "Without versioning all three components, result comparability is lost — changing any of task protocol, dataset revision, or model checkpoint produces different results [claim:agentic-de:023]"

### [claim:agentic-de:022] — MAJOR
**Problem:** The bullet states the lakeFS/DVC acquisition was in "November 2025" but the source provides no acquisition date. Only a July 2025 funding round is mentioned.
**Fix:** Remove the specific date: "Treeverse (lakeFS) acquired the DVC open-source project from Iterative.ai; DVC continues as a lightweight Git-based tool for smaller data-science projects while lakeFS serves enterprise-scale AI/ML infrastructure [claim:agentic-de:022]"

---

## Slide "Metadata Filtering, Consistency, and Silent Recall Loss" and "pgvector vs. Dedicated Vector DB" (slides 21-24, chunk 7)

### [claim:agentic-de:040] 4th occurrence — MAJOR
**Problem:** The in-algorithm filtering bullet is attributed to claim:040, but that source (yudhiesh.github.io) covers only naive pre-filtering and post-filtering — it says nothing about in-algorithm filtering or graph traversal modification.
**Fix:** Either (a) retag this bullet to a different claim ID backed by a source that describes in-algorithm filtering (e.g., the ACORN or Pinecone documentation), or (b) drop the in-algorithm filtering bullet entirely and limit claim:040 citations to pre-filtering and post-filtering.

### [claim:agentic-de:042] — MAJOR
**Problem:** The bullet appends "on SIFT10M" as the benchmark dataset, but the source does not mention SIFT10M or any specific dataset.
**Fix:** Remove the dataset qualifier: "Going from 0.8 to 0.95 recall increases HNSW latency by ~31% and IVF latency by ~3x over the same recall range [claim:agentic-de:042]"

---

## Slide "GDPR Propagation to Derived Data" (slides 31-34, chunk 10)

### [claim:agentic-de:055] — MAJOR
**Problem:** The bullet states machine unlearning as an unconditional GDPR Article 17 requirement, but the source imposes a critical conditional: "In situations where it is proven that the trained ML model leaks personal data." The bullet omits this qualifying threshold, overstating the legal obligation.
**Fix:** Add the conditional: "When a trained ML model is proven to leak personal data from training, GDPR Article 17 requires not only erasing the personal data from the training set but also applying machine unlearning methods to the trained model itself; deleting the source data alone is insufficient in such cases [claim:agentic-de:055]"
