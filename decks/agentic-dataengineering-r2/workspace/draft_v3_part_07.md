## Why Exact k-NN Fails at Scale

- Exact k-NN requires O(n·d) work per query — every stored vector must be compared against the query, making it infeasible at million- or billion-vector scale [claim:agde:037]
- A dataset of 10⁹ SIFT descriptors (128 dimensions) stored as floats uses 512 GB of memory; scanning it at SSD throughput of 512 MB/s would require 1,000 seconds to answer a single query [claim:agde:037]
- ANN indexes are necessary at million- or billion-vector scale because exact k-NN becomes computationally infeasible at those sizes [claim:agde:037]

<!-- Speaker: Lead with the arithmetic: 1,000 seconds per query makes the brute-force approach a non-starter. This motivates the entire ANN index landscape that follows. -->

<!-- Notes:
The O(n·d) complexity means cost grows linearly with both corpus size and vector dimensionality — modern embedding models at 768–1536 dimensions amplify the per-vector cost relative to older 128-dim descriptors like SIFT. The 512 GB figure makes RAM-based exhaustive search impractical even before considering latency; the SSD figure shows that even moving the problem to disk does not save it. This is the fundamental engineering constraint that makes ANN indexing a first-class data engineering concern rather than a narrow ML optimisation. Students who have worked with relational databases should recognise the analogy: a full table scan is acceptable on thousands of rows but catastrophic on billions — ANN indexes play the same role as B-tree indexes, accepting a small accuracy cost in exchange for polylogarithmic access. Emphasise that "approximate" here means a controlled, tunable accuracy loss, not arbitrary sloppiness.
-->

---

## ANN Index Families — HNSW, IVF, PQ, DiskANN

- HNSW is a graph-based ANN index achieving O(log n) search complexity via a multi-layer navigable small-world structure [claim:agde:038]
- IVF partitions vectors into clusters via k-means; at query time only nprobe clusters are searched, reducing cost at the expense of recall [claim:agde:039]
- PQ compresses each vector by splitting it into subvectors and replacing each with a centroid index, enabling >100x memory reduction at the cost of quantization error [claim:agde:039]
- DiskANN (NeurIPS 2019, Microsoft Research) is a disk-resident ANN index that serves a billion-point dataset on a single machine with 64 GB RAM at >5,000 QPS and <3 ms mean latency [claim:agde:040]

<!-- Speaker: Introduce the four families as solutions to four different constraints: graph traversal speed (HNSW), partition-based cost reduction (IVF), memory compression (PQ), and disk-resident scale (DiskANN). Subsequent slides drill into each. -->

<!-- Notes:
Each family addresses a different binding constraint. HNSW is the dominant in-memory index — its polylogarithmic complexity and high recall make it the default choice for datasets that fit in RAM. IVF is a partitioning strategy that limits search to a subset of clusters; it is often combined with PQ (hence IVF-PQ) to also address memory. PQ alone is a compression technique, not an index structure. DiskANN solves a different problem entirely: it pushes the corpus to SSD, enabling datasets 5–10x larger than what fits in RAM while maintaining sub-millisecond-class latency via the Vamana graph algorithm, which is optimised for sequential SSD reads. Understanding these families helps students reason about which tool to deploy given their constraints: memory budget, latency SLO, dataset size, and recall requirement.
-->

---

## HNSW in Depth — Parameters and Recall/Latency Tradeoff

- HNSW build-time parameters M (connections per node) and efConstruction (beam width) set the ceiling on achievable recall; they cannot be changed after index construction without a full rebuild [claim:agde:038]
- The query-time parameter efSearch is the operational dial: increasing it from 10 to 640 can improve recall@1 from ~0.56 to ~0.97, while latency rises from ~5 ms to ~68 ms [claim:agde:038]
- The recall-latency tradeoff should be treated as a tuned SLO, not a fixed property — the right efSearch value depends on the latency budget and the recall requirement for the application [claim:agde:038]

<!-- Speaker: Distinguish clearly between build-time parameters (set once, determine the recall ceiling) and query-time parameters (adjustable at serving time within that ceiling). The SLO framing is practical: teams should pick efSearch to meet a p95 latency target, then verify the resulting recall is acceptable. -->

<!-- Notes:
HNSW's multi-layer graph assigns each vector to one or more layers, with higher layers acting as express lanes for coarse navigation and the bottom layer containing all vectors for fine-grained traversal. M controls how densely each node is connected; higher M improves recall but increases memory and build time. efConstruction controls how many candidate neighbours are considered when inserting each node — larger values produce a higher-quality graph at greater build cost. Once built, only efSearch remains tunable. The practical implication is that HNSW index build is a one-time capital expenditure that determines the quality ceiling; efSearch is the operational cost dial. For teams running HNSW in production, a common pattern is to build with generous efConstruction (400–800), then tune efSearch at query time to hit a latency p95 SLO (e.g., 20 ms), and then verify that the recall at that efSearch is sufficient for the use case. Recall degradation as the dataset grows with fixed parameters is a known issue — this is covered in slide 39.
-->

---

## IVF-PQ — The Memory Compression Case

- IVF partitions vectors into clusters; at query time only nprobe clusters are searched, trading recall for speed; increasing nprobe recovers recall at the cost of more work [claim:agde:039]
- PQ splits each vector into subvectors and replaces each with a centroid index (controlled by nbits), introducing quantization error that degrades recall [claim:agde:039]
- For a 10M-vector 1536-dim dataset, raw storage is 61.4 GB; IVF-PQ with m=48, nbits=8 reduces this to ~480 MB — a 128x memory reduction [claim:agde:039]

<!-- Speaker: Present the tradeoff triangle: memory ↓, recall ↓ due to quantization error, nprobe ↑ to recover recall. IVF-PQ is the go-to when the corpus exceeds available RAM but DiskANN is not yet warranted. -->

<!-- Notes:
IVF and PQ are complementary compression strategies that are almost always used together. IVF reduces the search space by partitioning — with 1,000 clusters and nprobe=10, only 1% of vectors are examined per query. PQ reduces the per-vector storage by quantizing each subvector to a small codebook: with m=48 subvectors and nbits=8, each subvector is mapped to one of 256 centroids, stored as a single byte, so a 1536-dim float32 vector (6144 bytes) becomes 48 bytes. The 128x figure in the claim reflects this compression ratio. The memory savings are substantial but not free: quantization error means the distances computed during search are approximations of the true distances, so the nearest neighbours found may not be the true nearest neighbours. The standard mitigation is to retrieve extra candidates from IVF-PQ and re-score them against the original vectors (a technique called re-ranking with exact distances), recovering some recall at moderate latency cost. Students should understand that IVF-PQ is a pragmatic choice for datasets that must fit in limited RAM — when latency requirements are strict and RAM is not the constraint, HNSW typically gives better recall at the same query cost.
-->

---

## Recall as a Silently-Violated SLO

- ANN search achieves speed by accepting silent recall losses — vectors disappear from results without any error notification [claim:agde:041]
- Even with a substantial latency budget, recall@1 may reach only 0.9, meaning the true nearest neighbour is absent in ~10% of queries [claim:agde:041]
- Recall degrades silently as the dataset grows: a 10%+ drop from 50k to 200k vectors with fixed index parameters has been observed [claim:agde:041]
- HNSW deletes require soft-delete tombstoning rather than immediate graph repair, accumulating stale references until periodic cleanup [claim:agde:041]

<!-- Speaker: Connect this back to the lecture's opening theme — ML systems fail silently, and vector search is no exception. Recall is an SLO that must be actively measured, not assumed. -->

<!-- Notes:
This slide surfaces a critical operational risk that is easy to overlook. Unlike a database query that returns all matching rows or raises an error, an ANN index returns a ranked list with no indication of whether the true nearest neighbour is present. A recall@1 of 0.9 is practically invisible in production unless the application explicitly measures it — the user just gets a slightly worse result. The dataset-growth degradation is particularly insidious: an index tuned at launch will silently drift out of its recall SLO as the corpus grows, with no alarm triggered. Teams must implement continuous recall monitoring, typically by running a held-out ground-truth evaluation set against the live index on a schedule. The delete tombstoning issue is a practical gotcha: HNSW cannot efficiently remove a node from its multi-layer graph structure, so deleted vectors are marked as tombstones and excluded from result sets but still consume memory and slow traversal until the index is rebuilt or compacted. This is relevant for use cases with frequent deletions, such as RAG pipelines with rolling document windows.
-->

---

## Metadata Filtering and ANN — The Interaction Problem

- Post-filtering (run ANN first, then apply predicate) can return zero results when a selective filter eliminates all ANN candidates [claim:agde:042]
- Pre-filtering (apply predicate first, then run ANN on the subset) degrades to brute force when the filtered subset is large [claim:agde:042]
- Tight filters cause tail latencies of 200–300 ms in post-filter fallback engines [claim:agde:042]
- Dedicated vector databases such as Qdrant and Weaviate address this by integrating filters inside HNSW graph traversal; pgvector performs post-filter on a candidate set, making selective queries scan hundreds of thousands of candidates [claim:agde:042]

<!-- Speaker: Filtering is one of the most common production requirements and one of the least well-handled. Frame this as a fundamental tension between the ANN index's global graph structure and the localised subset that a metadata filter defines. -->

<!-- Notes:
Metadata filtering is ubiquitous in real RAG and search applications: "find similar documents, but only within this tenant's data" or "find similar products, but only those currently in stock." The naive post-filter approach runs ANN on all vectors and then drops results that don't match the predicate — if the predicate is selective (say, 0.1% of the corpus), ANN must over-retrieve by 1,000x to have a chance of returning k results, which defeats the purpose of ANN. Pre-filtering — restricting the graph traversal to nodes that match the predicate — sounds better but is not natively supported by standard HNSW implementations, which assume they can traverse any node. Qdrant's solution is to build a payload index on metadata fields and check the predicate during graph traversal, skipping non-matching nodes; this keeps the traversal within the ANN structure rather than falling back to brute force. pgvector as of 2024 does not support this — it uses a candidate set post-filter, which causes the latency blowup described in the claim. The practical takeaway is that teams who need filtered vector search at sub-10ms latency should evaluate Qdrant or Weaviate rather than defaulting to pgvector.
-->

---

## Choosing a Vector Store — pgvector vs. Dedicated Databases

- pgvector is the appropriate default for datasets under ~2M vectors when Postgres is already in the stack, offering full SQL join capability and zero additional infrastructure [claim:agde:043]
- Above 5–10M vectors or for sub-20ms p95 latency requirements, dedicated vector databases become preferable [claim:agde:043]
- Qdrant provides best-in-class filtered search by integrating predicates inside HNSW traversal; Pinecone offers zero-ops managed scale at a 3–8x cost premium; Milvus is designed for billion-vector sharded deployments [claim:agde:043]
- Past 2M vectors on a single Postgres instance, index build times can exceed 20 minutes [claim:agde:043]

<!-- Speaker: Give students a concrete decision heuristic: start with pgvector, migrate when you hit 2M vectors or a latency wall. The cost premium for Pinecone is worth naming explicitly — it surprises teams used to open-source tooling. -->

<!-- Notes:
The pgvector vs. dedicated-DB decision is one of the most common architectural questions teams face when adding vector search to an existing system. pgvector's main advantages are operational simplicity (no new infrastructure, native SQL joins with relational data, existing backup and access-control tooling) and cost (no additional service). Its limitations become binding at scale: the HNSW index in pgvector is built entirely in memory, so a 2M-vector 1536-dim index requires ~12 GB of RAM for construction; build times above 2M vectors become operationally disruptive. Qdrant is the recommended choice for filtered search at scale — its payload index integration is the strongest among open-source options as of 2026. Pinecone is fully managed and removes operational overhead entirely, but the 3–8x cost premium makes it hard to justify for cost-sensitive deployments. Milvus is designed for horizontal sharding and is the right choice for billion-scale corpora that require distributed index construction and serving. Students should understand that the right tool depends on scale, latency SLO, filtering requirements, and operational complexity tolerance — there is no single correct answer.
-->
