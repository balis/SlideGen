## Embeddings in Context

- Every stored vector is baked to a specific embedding model version: vectors from model A and model B occupy incompatible geometric spaces, so mixing them makes similarity scores meaningless [claim:agde:023]
- Changing the embedding model requires re-encoding the entire corpus and rebuilding the ANN index from scratch before queries using the new model can be served correctly [claim:agde:023]

<!-- Speaker: Transition from reproducibility to embeddings — the model itself is now part of the versioning problem. Frame the section by establishing that the embedding model is a hard dependency of every vector in the store. -->

<!-- Notes:
Sections A–E covered data-layer reproducibility: snapshot IDs, DVC hashes, lakeFS commits. This section adds another layer: the embedding model version. Students who have used word2vec or sentence-transformers may already know that vector spaces are not interchangeable across models, but the operational consequence — that a model upgrade forces a full re-index — is often underappreciated until they encounter it in production.

The key intuition is geometric: cosine similarity between two vectors is only meaningful if both vectors were produced by the same encoder with the same weights. A query vector from model B compared to corpus vectors from model A is numerically a valid dot product but semantically meaningless. This is not a corner case; it is an invariant of the representation learning setup.

Use this slide to motivate the rest of Section F: model selection (slide 31), throughput concerns (slides 32–33), and the versioning obligation (slide 34) all follow from this single hard dependency.
-->

---

## Model Selection — Dimension, Quality, Cost Tradeoff

- OpenAI text-embedding-3-large (3072 dims, $0.13/1M tokens) supports Matryoshka truncation: a 256-dimensional output still outperforms the full 1536-dim text-embedding-ada-002 on MTEB, making dimension a configurable dial rather than a fixed property [claim:agde:031]
- Embedding models trained with Matryoshka Representation Learning expose dimension as an explicit performance-cost tradeoff: truncating to a smaller dimension saves vector-database storage with only modest quality loss [claim:agde:032]
- text-embedding-3-small costs 5× less than ada-002 ($0.00002 vs $0.0001 per 1k tokens) with a higher average MTEB score (62.3% vs 61.0%), so model selection involves an explicit three-way tradeoff: dimension, quality, and cost [claim:agde:031]

<!-- Speaker: Walk through the Matryoshka result — the counter-intuitive finding that fewer dimensions can beat more dimensions across model versions. Emphasize that "dimension" is now a tunable parameter at inference time, not a fixed architectural constant. -->

<!-- Notes:
The Matryoshka Representation Learning (MRL) result deserves explanation. Traditional embedding models produce a fixed-length vector; quality is monotonically non-decreasing with dimension for a given model. MRL trains the model so that the first k dimensions of the full vector already encode a useful representation — meaning you can truncate at inference time without retraining. OpenAI exposes this via a `dimensions` parameter.

The practical consequence: a 256-dim text-embedding-3-large vector is cheaper to store, faster to index (ANN build time scales with d), and still more accurate than a 1536-dim ada-002 vector on MTEB benchmarks. This breaks the naive intuition that "more dimensions = better."

MTEB (Massive Text Embedding Benchmark) is the standard multi-task benchmark for text embedding models, covering retrieval, classification, clustering, and semantic similarity. Students should know it as the de facto leaderboard for comparing models.

The cost comparison (3-small vs ada-002) is worth pausing on: same or better quality at 5× lower price is a genuine engineering decision, not a marginal one. The three-way tradeoff (dimension, quality, cost) is the mental model to carry into model selection.
-->

---

## Batch Throughput and Rate-Limit Handling

- OpenAI's Batch API processes embedding requests asynchronously within 24 hours at 50% of standard token prices, supports up to 50,000 embedding inputs and a 200 MB input file per batch, and draws from a separate rate-limit pool that does not consume synchronous per-model token quotas [claim:agde:033]
- For synchronous embedding paths with per-minute rate limits, the recommended strategy is to send larger per-request batches to reduce request count, implement exponential backoff with jitter on HTTP 429 responses, and insert pacing delays — the combination prevents thundering-herd retry storms while maximising token throughput within quota [claim:agde:034]

<!-- Speaker: Distinguish the two throughput regimes: offline batch jobs (use Batch API) vs. synchronous paths (use backoff + pacing). The Batch API's separate rate-limit pool is a key operational detail — it means large offline jobs do not degrade production serving quotas. -->

<!-- Notes:
Large-scale offline embedding pipelines face two distinct bottlenecks: cost and rate limits. The OpenAI Batch API addresses both simultaneously — the 50% cost discount and the separate quota pool make it the natural choice for any job that can tolerate up to 24-hour turnaround (e.g., nightly re-ingestion, bulk document updates).

For synchronous paths (e.g., embedding new documents at write time), rate limits are still a real constraint. The thundering-herd problem arises when many workers retry simultaneously after a 429 response: they all back off by the same interval and then hammer the API again in lock-step. Jitter (randomized sleep within the backoff window) breaks the synchronization. Exponential backoff (doubling the wait interval on each retry) prevents sustained overload.

The Voyage AI example (voyage-3.5 at 2,000 RPM / 8M TPM) is illustrative of a real-world rate limit profile. Batching 500 texts per request reduces request count by 500×, which is often the most effective single lever for staying within RPM limits.

Students who have built data pipelines before will recognize this pattern from Kafka consumer lag, S3 throttling, and database connection pools — the retry-with-backoff pattern is general; the jitter addition is what makes it safe at scale.
-->

---

## Idempotent Embedding Pipeline

- Idempotent re-embedding pipelines use a content hash (SHA-256 of source text) stored alongside each vector: before calling the embedding API the pipeline checks whether the hash already exists in the embedding store and skips the call if so, reducing both API cost and re-processing risk [claim:agde:035]
- Optimal API batch size for cost-effective embedding is 100–500 texts per call [claim:agde:035]

```python
import hashlib
import openai

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def embed_documents(texts: list[str], store: dict, client: openai.OpenAI,
                    model: str = "text-embedding-3-small", batch_size: int = 200):
    """
    Idempotent embedding pipeline.
    store: dict mapping content_hash -> embedding vector (pre-loaded from DB).
    Returns dict of {hash: vector} for newly embedded texts only.
    """
    new_results = {}
    to_embed = []

    for text in texts:
        h = sha256(text)
        if h in store:
            continue  # already embedded; skip API call
        to_embed.append((h, text))

    # batch in groups of batch_size to stay within rate limits
    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i : i + batch_size]
        hashes, batch_texts = zip(*batch)
        response = client.embeddings.create(input=list(batch_texts), model=model)
        for h, item in zip(hashes, response.data):
            new_results[h] = item.embedding

    return new_results
```

<!-- EXEC_TEST -->

<!-- Speaker: Walk through the three logical phases: hash check (skip), batch collection, store-and-return. Emphasise that the hash key makes the pipeline safe to restart after partial failures — re-running on the same corpus costs nothing for already-processed items. -->

<!-- Notes:
Idempotency is a core property of well-designed data pipelines. For embedding pipelines specifically, the cost motivation is strong: at $0.00002/1k tokens, re-embedding a 10M-document corpus unnecessarily could cost thousands of dollars on top of wall-clock time. The SHA-256 key approach is also model-agnostic — the same store structure works across providers.

Students should notice that the hash is over the source text, not the chunk ID or document ID. This is intentional: if the text content of a chunk changes (e.g., document updated), the hash changes and the pipeline correctly re-embeds. If only metadata changes (title, category), the text hash is unchanged and the embedding is reused.

The batch_size=200 default sits within the 100–500 recommended range. The tradeoff: too small increases request count (hitting RPM limits); too large may hit per-request token limits or increase memory pressure. For most models 200–300 is a safe starting point.

A common student question: "Why not use the document's database ID as the key?" — because IDs are not content-addressable. If the same text is stored under two IDs, a hash-keyed store deduplicates automatically; an ID-keyed store embeds it twice and wastes cost. The hash approach also enables cross-corpus deduplication transparently.

The `# already embedded; skip API call` comment is the critical line. In a distributed pipeline this check should be atomic (e.g., a Redis SETNX or a database upsert with ON CONFLICT DO NOTHING) to avoid race conditions between workers.
-->

---

## The Hard Dependency — Embedding Model Versioning

- Changing an embedding model typically requires re-encoding the entire corpus and rebuilding the ANN index from scratch: a query vector from the new model cannot be meaningfully compared to corpus vectors from the old model, even when both models share the same output dimensionality [claim:agde:036]
- For a 1-million-item database, a full re-index amounts to approximately 100 GPU-hours of recompute plus CPU-hours for index building; billion-item systems can require weeks [claim:agde:036]
- Embedding model version must be tracked as part of ML lineage alongside data snapshot and code version: mixing vectors from different model versions makes similarity scores meaningless [claim:agde:023]

<!-- Speaker: Land the operational cost of the hard dependency. Connect back to the reproducibility section: embedding model version is a third dimension of the artifact lineage. A model upgrade is not a drop-in replacement — it is a migration event. -->

<!-- Notes:
This slide closes Section F by making the versioning obligation concrete. The geometric argument (incompatible spaces) was introduced on slide 30; here we quantify the operational consequence: 100 GPU-hours for 1M items, weeks for 1B items. Students should internalize these numbers as a reason to treat embedding model upgrades with the same care as database schema migrations.

The "same output dimensionality" caveat is important: two models both producing 768-dimensional vectors do not produce comparable vectors. Dimension is a shape property of the tensor; compatibility requires identical weights and tokenizer. This catches students who assume that dimensionality equality implies geometric compatibility.

The lineage requirement (model version + data snapshot + code version) ties back to Section D. A reproducibility token for a vector index must include all three: the source data version (e.g., Iceberg snapshot ID), the embedding model version (e.g., text-embedding-3-small:v2), and the index build configuration (e.g., HNSW M=16 efConstruction=200). Without all three, the index cannot be reconstructed deterministically.

A practical mitigation pattern: maintain a model_version column in the vector store metadata table. During a model upgrade, build the new index in parallel under a new version tag, validate recall on a held-out query set, then swap the serving pointer. This blue-green index upgrade pattern avoids downtime but doubles storage temporarily.
-->
