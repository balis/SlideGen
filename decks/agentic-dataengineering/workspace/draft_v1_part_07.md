## Why Exact k-NN Doesn't Scale

- Exact k-NN search requires O(N * D) distance computations per query, where N is the dataset size and D the dimensionality [claim:agentic-de:036]
- At billion scale this is infeasible: brute-force scan of 10^9 128-d SIFT vectors would take ~17 minutes per query and require 512 GB of RAM [claim:agentic-de:036]
- This motivates approximate nearest neighbor (ANN) indexes that trade a small amount of recall for orders-of-magnitude speedup

<!-- Speaker: Start by showing why we need ANN indexes at all — exact search simply does not work at production scale. The numbers make the problem visceral. -->

<!-- Notes:
Exact k-NN is the baseline every ANN index is measured against. The O(N * D) cost
means every query must touch every stored vector, computing a full distance
(cosine, L2, or inner product) each time. For a 1536-dimensional embedding space
(typical for OpenAI models), the constant factor is even worse than the 128-d SIFT
benchmark quoted here.

Students sometimes assume that "just add more machines" solves this, but even with
sharding you still pay O(N * D / S) per shard and must merge results — latency
remains in the seconds-to-minutes range for billion-scale datasets. ANN indexes
restructure the search space so that only a fraction of vectors are visited,
reducing query time to milliseconds at the cost of occasionally missing a true
nearest neighbor. The next slide covers the three dominant families of ANN indexes.
-->
---
## ANN Index Families — HNSW, IVF-PQ, DiskANN

| Property | HNSW | IVF-PQ | DiskANN |
|---|---|---|---|
| **Structure** | Navigable small-world graph | Cluster partitions + product quantization | SSD-resident graph with compressed RAM cache |
| **Tuning knobs** | M, efConstruction, efSearch | nlist, nprobe, nbits | L (search list size), beam width |
| **Recall range** | ~85% to ~98% (efSearch 100 → 500) | ~70% to ~99% (nprobe 1 → 256) | 95%+ 1-recall@1 at billion scale |
| **Latency** | ~1 ms to ~5 ms (10 M vectors) | 0.02 ms to 3.3 ms (throughput 50 k → 300 QPS) | < 3 ms mean on SIFT-1B |
| **Memory** | Full vectors in RAM | Compressed vectors in RAM | 64 GB RAM + SSD for 10^9 vectors |

- HNSW recall is tuned via efSearch: increasing it from 100 to 500 raises recall from ~85% to ~98% but increases per-query latency from ~1 ms to ~5 ms on a 10 M-vector dataset [claim:agentic-de:037]
- IVF-PQ combines cluster-based partitioning with product quantization; sweeping nprobe from 1 to 256 moves recall from ~70% to ~99% while throughput drops from 50,000 QPS to 300 QPS [claim:agentic-de:038]
- DiskANN stores the graph index on SSD with a compressed representation in RAM, enabling billion-point search on a single node with 64 GB RAM — achieving >5,000 QPS at 95%+ recall with <3 ms mean latency [claim:agentic-de:039]

<!-- Speaker: Walk through the table column by column. Emphasize that recall is not a fixed property of an index — it is a tuned parameter that trades off against latency and throughput. -->

<!-- Notes:
These three families represent fundamentally different design points. HNSW builds a
multi-layer graph where each layer is a navigable small-world network; traversal
starts at the top (sparse) layer and descends. It delivers excellent recall but
keeps all vectors in RAM, so cost scales linearly with dataset size. M controls how
many edges each node has — higher M improves recall and increases memory.

IVF-PQ first clusters the dataset (IVF) then compresses each vector into a short
code (PQ). At query time, only nprobe clusters are searched, and distances are
approximated from the PQ codes. This dramatically reduces memory but at a recall
cost that is highly sensitive to nprobe.

DiskANN (Subramanya et al., NeurIPS 2019) is the key innovation for billion-scale
on commodity hardware. It keeps only a compressed representation in RAM for
beam-search initialization, then fetches full vectors from SSD during graph
traversal. This gives 5-10x more vectors per machine compared to DRAM-only HNSW.
Students should understand that the choice among these families depends on dataset
size, latency budget, and available hardware — there is no universally best index.
-->
---
## Metadata Filtering, Consistency, and Silent Recall Loss

- Metadata filtering interacts destructively with ANN graph traversal [claim:agentic-de:040]
- **Pre-filtering** (skip non-matching nodes during traversal) caps recall at ~57% because filtered-out nodes serve as routing states connecting graph regions [claim:agentic-de:040]
- **Post-filtering** preserves >99% recall but wastes compute on results that are discarded after retrieval [claim:agentic-de:040]
- **In-algorithm filtering** (e.g., Qdrant ACORN, Pinecone merged indexes) modifies traversal to maintain both recall and efficiency [claim:agentic-de:040]
- ANN recall is a silently violated SLO: as the database grows or parameters drift, retrieval quality degrades without raising exceptions [claim:agentic-de:042]
- Latency metrics remain stable while progressively weaker context is fed to downstream consumers such as RAG, increasing hallucinations [claim:agentic-de:042]
- Going from 0.8 to 0.95 recall increases HNSW latency by ~31% and IVF latency by ~3x on SIFT10M [claim:agentic-de:042]

<!-- Speaker: This is the slide students need to internalize — vector search fails silently. There is no exception when recall drops. Connect this to the "ML fails silently" theme from Slide 3. -->

<!-- Notes:
The filtering problem is subtle and often overlooked. In an HNSW graph, nodes that
do not match a metadata predicate still serve as "routing states" — they connect
different regions of the graph. When pre-filtering skips these nodes, the greedy
traversal cannot reach the neighbors behind them, causing recall to plateau at
roughly 57% in the benchmarks cited. This is catastrophic for filtered queries with
high selectivity (e.g., "find similar documents from the last 7 days" when most
documents are older).

Post-filtering avoids this by searching the full graph and discarding non-matching
results afterward, but it wastes compute proportional to the inverse of the filter
selectivity. In-algorithm approaches like ACORN modify the graph structure itself
to remain navigable under arbitrary filters.

The silent recall degradation is a recurring theme in this lecture. Just as ML
models continue predicting with degraded quality (Slide 3), vector indexes
continue returning results with degraded recall. There is no error, no timeout —
only subtly worse answers. This makes recall monitoring essential: teams should
periodically evaluate recall against a ground-truth sample, not just track p99
latency.
-->
---
## pgvector vs. Dedicated Vector DB

| Consideration | pgvector (Postgres extension) | Dedicated Vector DB (Qdrant, Pinecone, Milvus) |
|---|---|---|
| **Operational overhead** | Zero — one migration on existing Postgres | New service to deploy, monitor, and secure |
| **SQL integration** | Join vector similarity with relational predicates in one query | Separate query path; application-level joins |
| **Scale ceiling** | Low millions of vectors on a single instance | Horizontal scaling beyond ~10 M vectors |
| **Advanced features** | Basic HNSW and IVF-flat | Advanced quantization, hybrid BM25+vector ranking |
| **Consistency model** | Full ACID transactions | Varies — eventual consistency is common |

- pgvector eliminates a new service, enables SQL joins of vector similarity with relational predicates in one query, and is sufficient for datasets up to low millions of vectors [claim:agentic-de:041]
- Dedicated engines offer horizontal scaling, advanced quantization, and hybrid BM25+vector ranking needed beyond ~10 M vectors or at high query concurrency [claim:agentic-de:041]

<!-- Speaker: Frame this as an engineering trade-off, not a technology race. For most teams starting out, pgvector is the right default — add a dedicated engine when you outgrow it. -->

<!-- Notes:
This slide deliberately pushes back against the vendor narrative that every project
needs a purpose-built vector database. For a team that already runs Postgres,
pgvector is a single CREATE EXTENSION command and an ALTER TABLE to add a vector
column. The familiar SQL interface means existing monitoring, backup, and access
control all carry over.

The decision to move to a dedicated engine should be driven by concrete signals:
query latency exceeding SLOs at your dataset size, need for multi-tenant isolation,
or requirements for hybrid sparse+dense retrieval that pgvector does not support
natively. The ~10 M vector threshold is a rough guideline — actual limits depend on
vector dimensionality, available RAM, and concurrency requirements.

Students should also note the consistency trade-off: pgvector inherits Postgres
ACID guarantees, meaning a newly inserted vector is immediately searchable after
commit. Many dedicated vector databases offer only eventual consistency, which can
cause issues when an ingestion pipeline writes a vector and a query immediately
follows. This matters in transactional workflows where a user uploads a document
and expects to search it seconds later.
-->