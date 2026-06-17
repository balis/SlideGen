## Why Exact k-NN Doesn't Scale

- Exact k-NN search requires O(N * D) distance computations per query, where N is the dataset size and D is the dimensionality [claim:agentic-de:036]
- At million- or billion-scale datasets, brute-force exact search becomes computationally impractical for real-time systems [claim:agentic-de:036]
- This motivates approximate nearest neighbor (ANN) indexes that trade a controlled amount of recall for orders-of-magnitude speedup

<!-- Speaker: Start with the cost model — O(N*D) per query — and let students feel why exhaustive search is a non-starter at scale. This sets up the three ANN families on the next slide. -->

<!-- Notes:
Exact k-NN computes the distance between the query vector and every vector in the dataset, then returns the k closest. With D-dimensional vectors this is O(N*D) per query. For a dataset of 10^9 vectors this is billions of floating-point operations per query — far too slow for any interactive or even batch-serving use case. The key insight is that we rarely need the exact nearest neighbors; an approximate set with 95%+ recall is sufficient for downstream tasks like RAG or recommendation. This gap between "exact but slow" and "approximate but fast" is what ANN indexes exploit. Students should understand that the choice is not whether to approximate, but how much recall to trade for how much speed.
-->

---

## ANN Index Families — HNSW, IVF-PQ, DiskANN

- **HNSW** — navigable small-world graph kept in memory; tuned via M (connectivity), efConstruction (build quality), and efSearch (query exploration depth) [claim:agentic-de:037]
  - Increasing efSearch from 100 to 500 raises recall from ~85% to ~98% but increases latency from ~1 ms to ~5 ms on a 10 M-vector dataset [claim:agentic-de:037]
- **IVF-PQ** — cluster-based partitioning (IVF) combined with product quantization for compression; nprobe controls how many clusters are searched [claim:agentic-de:038]
  - Sweeping nprobe from 1 to 256 moves recall from ~70% to ~99% while throughput drops from 50,000 QPS to 300 QPS [claim:agentic-de:038]
- **DiskANN** — SSD-resident graph index with compressed representation in RAM, enabling billion-point search on a single node with 64 GB RAM [claim:agentic-de:039]
  - On SIFT-1B: >5,000 QPS at 95%+ 1-recall@1 with <3 ms mean latency [claim:agentic-de:039]

<!-- Speaker: Walk through the three columns left to right. Emphasize that recall is a tuned property, not a fixed one — every family has knobs that trade recall for latency. -->

<!-- Notes:
HNSW builds a hierarchical graph where each node connects to M neighbors. At query time the algorithm greedily traverses the graph, expanding efSearch candidates at each layer. More exploration means higher recall but more distance computations. The entire graph lives in RAM, which limits dataset size per node.

IVF-PQ first clusters vectors into Voronoi cells (IVF) and then compresses each vector using product quantization (PQ), which splits the vector into sub-vectors and quantizes each independently. At query time only nprobe clusters are scanned, and distances are computed in the compressed domain. This is more memory-efficient than HNSW but generally lower recall at the same latency.

DiskANN (Subramanya et al., NeurIPS 2019) breaks the memory barrier by storing the full-precision graph on SSD while keeping only compressed vectors (via PQ) in RAM. During search it performs SSD reads for exact distance computation only on promising candidates. This enables billion-scale search on commodity hardware — a single 16-core machine with 64 GB RAM and an SSD — achieving >5,000 QPS at 95%+ recall. Students should appreciate that the three families represent different points on the memory-vs-latency-vs-scale Pareto frontier.
-->

---

## Metadata Filtering, Consistency, and Silent Recall Loss

- Metadata filtering interacts destructively with ANN graph traversal [claim:agentic-de:040]
  - **Pre-filtering** (skip non-matching nodes): recall plateaus at ~57% because filtered-out nodes serve as routing states connecting graph regions [claim:agentic-de:040]
  - **Post-filtering** (search first, filter results): preserves >99% recall but wastes compute on discarded results [claim:agentic-de:040]
- ANN recall is a silently violated SLO: as a vector database grows or parameters drift, retrieval quality degrades without generating exceptions [claim:agentic-de:042]
- Going from 0.8 to 0.95 recall increases HNSW latency by ~31% and IVF latency by ~3x [claim:agentic-de:042]

<!-- Speaker: The pre-filtering recall cap surprises students — draw the graph analogy of removing highway nodes and stranding entire neighborhoods. Then pivot to the silent-SLO point: no error is raised when recall drops. -->

<!-- Notes:
Pre-filtering seems intuitive — why search vectors that do not match the metadata predicate? The problem is that HNSW is a graph, and nodes that fail the filter may still be critical routing nodes. Removing them from traversal disconnects regions of the graph, capping recall regardless of how many candidates you explore. Post-filtering avoids this but returns fewer than k results when selectivity is high, wasting the compute spent on discarded candidates.

The silent-SLO problem is arguably more dangerous in production. Unlike latency (which triggers alerts) or throughput (which causes timeouts), recall degradation is invisible to standard monitoring. The system feeds progressively weaker context to downstream consumers such as RAG pipelines, increasing hallucinations, while all operational metrics remain green. Students should understand that recall must be actively measured — for example by periodically running exact search on a sample and comparing results — because no error will ever tell you it has degraded.
-->

---

## pgvector vs. Dedicated Vector DB

- **pgvector** is the better choice when you already run Postgres: adding vector search is one migration, not a new service [claim:agentic-de:041]
- **Dedicated engines** (e.g., Qdrant, Milvus) are the better choice when you need to scale beyond what a single Postgres instance handles or require advanced quantization features [claim:agentic-de:041]
- The decision axis is operational simplicity versus scale and specialized capabilities [claim:agentic-de:041]

<!-- Speaker: Frame this as an architecture decision, not a technology ranking. Most student projects start fine with pgvector; the dedicated-DB path matters when scale or feature requirements outgrow a single Postgres node. -->

<!-- Notes:
pgvector extends PostgreSQL with vector data types and ANN indexes (IVFFlat and HNSW). Its main advantage is operational: teams already running Postgres get vector search without provisioning, securing, and monitoring a separate service. It supports ACID transactions, familiar SQL tooling, and integrates naturally with relational data already in the database.

Dedicated vector databases are purpose-built for high-dimensional similarity search. They offer features like built-in quantization, distributed sharding, and optimized disk-based indexes that a general-purpose RDBMS extension does not prioritize. When the dataset or query load exceeds what a single Postgres instance can serve with acceptable latency, a dedicated engine becomes necessary.

The key point for students is that this is not a quality-of-results question — both can return the same neighbors for the same index type. It is an operational and scaling question. Start with pgvector if Postgres is already in the stack; migrate to a dedicated engine when you hit its scaling ceiling.
-->
