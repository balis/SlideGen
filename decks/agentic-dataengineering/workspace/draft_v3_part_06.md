## Embedding Model Selection — Dimensions, Quality, Cost

- OpenAI's text-embedding-3-small (1 536 dimensions, MTEB 62.3 %) costs $0.02 per million tokens; text-embedding-3-large (3 072 dimensions, MTEB 64.6 %) costs $0.13 per million tokens — a 6.5x price premium for roughly 2 MTEB points, making the small model the default for most RAG workloads [claim:agentic-de:030]
- The Batch API processes embedding requests asynchronously within a 24-hour window at a 50 % cost discount, with dedicated TPD quotas separate from synchronous TPM/RPM limits, allowing up to 50 000 inputs per batch submission without consuming real-time capacity [claim:agentic-de:031]

| Property | text-embedding-3-small | text-embedding-3-large |
|---|---|---|
| Dimensions | 1 536 | 3 072 |
| MTEB score | 62.3 % | 64.6 % |
| Cost / 1 M tokens | $0.02 | $0.13 |
| Batch API cost | $0.01 | $0.065 |

<!-- Speaker: Walk through the table row by row. Stress that for most retrieval workloads the small model is the right default; the large model earns its premium only when recall on hard queries is the bottleneck. Mention the Batch API as the bridge to the code slide that follows. -->

<!-- Notes:
The MTEB (Massive Text Embedding Benchmark) score is the standard leaderboard metric for embedding quality. A ~2-point gap sounds small, but on tail queries it can matter — students should understand that the choice is workload-dependent, not universal. The 6.5x cost multiplier compounds quickly at scale: a 100 M-token corpus costs $2 with the small model versus $13 with the large model in synchronous mode, and half those amounts via the Batch API. The Batch API's 24-hour SLA makes it ideal for nightly ETL-style embedding jobs but unsuitable for real-time ingestion. Emphasize that TPD quotas are separate from TPM/RPM — a batch job cannot starve the synchronous serving path.
-->

---

## Idempotent Re-Embedding and the Model Lock-In Problem

- Each embedding model defines its own coordinate system — vectors from one model are incompatible with those from another, even when dimensions match; changing models forces a full re-embedding and re-indexing of the entire corpus, and failure to do so produces silent retrieval degradation rather than an error [claim:agentic-de:033]
- Re-embedding cost creates de facto vendor lock-in: ~$1 300 for 100 M tokens with text-embedding-3-large, plus hours of compute and doubled infrastructure during migration — most teams pick one model early and never change it because the switching cost is too high [claim:agentic-de:034]
- Idempotent re-embedding pipelines use content-addressable hashing: chunk hashes are computed, compared against stored hashes, and only new or modified chunks are sent for embedding — unchanged chunks are skipped, avoiding redundant API calls and index mutations [claim:agentic-de:035]

<!-- Speaker: Emphasize the "silent degradation" failure mode — mixing vectors from two models produces results, not errors, which makes the bug invisible to alerting. Then pivot to content-addressable hashing as the mitigation: even a full re-embedding becomes cheaper when only changed chunks are processed. -->

<!-- Notes:
This slide covers two related but distinct problems. First, model lock-in: because each model learns its own embedding space, cosine similarities between vectors from different models are meaningless. A migration therefore requires re-embedding every stored document, rebuilding every ANN index, and running old and new pipelines in parallel until cutover — a process that can take days for large corpora. The $1 300 figure is API cost alone for 100 M tokens; infrastructure and engineering time multiply the true cost. Second, idempotent pipelines: content-addressable hashing (e.g., SHA-256 of the raw chunk text) lets the pipeline detect which chunks changed between runs and skip unchanged ones. This is the same principle as DVC's content-addressable storage (Slide 14) applied at the embedding stage. Students should connect this back to the reproducibility theme: if you version both the chunk content hash and the model identifier, you can reconstruct exactly which vectors were active at any point in time.
-->

---

## Batch Throughput and Rate-Limit Handling

- The synchronous OpenAI embeddings endpoint accepts a maximum of 2 048 inputs per request; exceeding this returns a 400 error, so throughput optimization requires batching inputs within this cap and staying within the account's TPM quota, typically via client-side rate limiting with exponential backoff [claim:agentic-de:032]

```python
import time
import hashlib
from openai import OpenAI

client = OpenAI()
MODEL = "text-embedding-3-small"
BATCH_SIZE = 2048          # API hard limit per request
MAX_RETRIES = 5
BASE_DELAY = 1.0           # seconds


def content_hash(text: str) -> str:
    """SHA-256 hash for idempotent deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()


def embed_batches(
    texts: list[str],
    seen_hashes: set[str] | None = None,
) -> list[dict]:
    """Embed texts in batches of BATCH_SIZE with exponential backoff.

    Skips chunks whose content hash is already in *seen_hashes*
    (idempotent re-embedding).
    """
    if seen_hashes is None:
        seen_hashes = set()

    # Filter unchanged chunks
    pending = []
    for t in texts:
        h = content_hash(t)
        if h not in seen_hashes:
            pending.append((h, t))

    results: list[dict] = []
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start : start + BATCH_SIZE]
        batch_texts = [t for _, t in batch]
        batch_hashes = [h for h, _ in batch]

        for attempt in range(MAX_RETRIES):
            try:
                response = client.embeddings.create(
                    model=MODEL,
                    input=batch_texts,
                )
                for emb, h in zip(response.data, batch_hashes):
                    results.append({"hash": h, "vector": emb.embedding})
                break  # success — move to next batch
            except Exception as exc:
                if "429" in str(exc) or "rate" in str(exc).lower():
                    delay = BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise  # non-retriable error
        else:
            raise RuntimeError(
                f"Batch starting at index {start} failed after {MAX_RETRIES} retries"
            )

    return results
```

<!-- EXEC_TEST -->

<!-- Speaker: Walk through the code top to bottom: content_hash for idempotency, the outer loop that slices into batches of 2 048, and the inner retry loop with exponential backoff. Point out that this is the synchronous path — for bulk jobs the Batch API from the previous slide is preferable. -->

<!-- Notes:
This code combines three ideas from the section: the 2 048 per-request cap (claim 032), the content-addressable deduplication (claim 035 from the previous slide), and standard retry/backoff for HTTP 429 rate-limit errors. In production, you would persist seen_hashes in a metadata store (e.g., a hash column in the chunks table) rather than passing it as an in-memory set. The exponential backoff uses powers of two with a 1-second base, giving delays of 1, 2, 4, 8, 16 seconds — conservative enough to recover from short bursts without wasting too much wall-clock time. Note that the code checks for "429" in the exception string; the openai Python SDK raises an APIStatusError with the status code, so a more robust check would inspect exc.status_code directly. The function returns a list of dicts with hash and vector, which downstream code can upsert into the vector store keyed on the hash. Students should recognize this as a standard ETL pattern: extract (texts), transform (embed), load (upsert), with idempotency baked in.
-->