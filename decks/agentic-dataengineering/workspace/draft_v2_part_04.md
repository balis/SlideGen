## Reproducibility as a Three-Layer Temporal Problem

- ML reproducibility requires pinning three layers to the same point in time: the data state (lakehouse snapshots or content-addressed versions), the code/pipeline state (Git commits), and the embedding-model version (checkpoint or API version) [claim:agentic-de:023]
- Without coupling all three layers, re-running a pipeline on "the same data" can produce different results if the embedding model has changed [claim:agentic-de:023]

<!-- Speaker: Frame this as the unifying insight of the section — point-in-time correctness, dataset versioning, and embedding-model versioning are one temporal problem at three layers. Ask: "what was the data state when this artifact was produced?" -->

<!-- Notes:
This slide introduces a conceptual frame that ties together the previous discussion of feature stores and point-in-time joins with the versioning tools covered next. The key insight is that reproducibility in ML is not just about pinning the dataset — it extends to the transformation code and the embedding model as well, since each defines part of the final numerical representation.

Students who have worked with Git understand code versioning, but may not appreciate that data and model checkpoints need the same treatment. A common misconception is that "same data + same code = same result," which breaks down when the embedding model is an external API that has been silently updated. The MTEB reproducibility work highlights this by requiring task versioning, dataset versioning, and model versioning as three co-equal pillars.

Connecting back to the recurring schema example: if you re-embed the transactions + customer dimension dataset with a newer model checkpoint, similarity scores change, and any downstream retrieval or classification pipeline produces different outputs — even though neither the raw data nor the pipeline code changed.
-->

---

## Lakehouse Time Travel — Delta Lake and Iceberg

- **Delta Lake:** time travel via `VERSION AS OF` or `TIMESTAMP AS OF` queries; the default VACUUM retention period is 7 days (`delta.deletedFileRetentionDuration`), so time travel beyond 7 days requires explicitly increasing retention at the cost of additional storage [claim:agentic-de:018]
- **Apache Iceberg:** every write creates a new immutable snapshot referencing manifest lists and data files; time-travel queries follow older snapshot pointers, but even small data changes create new versions of data and metadata files, increasing storage usage; over time snapshot accumulation also causes metadata bloat [claim:agentic-de:019]

<!-- Speaker: Compare the two approaches side by side — Delta Lake uses a log-based protocol with configurable retention, while Iceberg uses immutable snapshots with manifest-level indirection. Both enable time travel but differ in retention mechanics and storage trade-offs. -->

<!-- Notes:
Delta Lake and Iceberg are the two dominant open lakehouse table formats that provide time travel. Delta Lake records every transaction in a JSON/Parquet log; VACUUM physically deletes data files older than the retention window, so time travel is bounded by how long you keep files. The 7-day default is a pragmatic trade-off between storage cost and the ability to debug or roll back recent mistakes.

Iceberg takes a different approach: each write produces an immutable snapshot that points to manifest files, which in turn point to data files (Parquet or ORC). Time-travel queries simply resolve an older snapshot pointer. However, "immutable snapshots" does not mean "no data duplication" — the source explicitly warns that even small data changes create new data and metadata files, growing storage. Over time, snapshot accumulation makes metadata files larger and more complex, increasing memory requirements for query planning. Operators must run periodic snapshot expiration and orphan-file cleanup to control this bloat.

Students should understand that neither format gives free time travel — both trade storage for history, just through different mechanisms. The choice between them often depends on the broader ecosystem: Delta Lake is native to Databricks; Iceberg has broader multi-engine support (Spark, Trino, Flink, Dremio).
-->

---

## Content-Addressable Versioning — DVC and lakeFS

- **DVC:** uses content-addressable storage with MD5 hashes to deduplicate data; files are stored in a cache keyed by hash, and lightweight `.dvc` metafiles tracked in Git link each commit to an exact dataset state without storing large files in the repository [claim:agentic-de:020]
- **lakeFS:** provides Git-like version control (branches, commits, merges) over object storage (S3, GCS, Azure Blob) using zero-copy branching — creating a branch is a metadata-only operation with no data duplication; storage overhead only occurs when data is actually modified on a branch [claim:agentic-de:021]
- Treeverse (lakeFS) acquired the DVC open-source project from Iterative.ai in November 2025; DVC continues as a lightweight Git-based tool for smaller data-science projects while lakeFS serves enterprise-scale AI/ML infrastructure [claim:agentic-de:022]

<!-- Speaker: Contrast the two models — DVC wraps Git with pointer files for individual datasets, while lakeFS provides a full branching layer over the object store. Mention the 2025 acquisition to note the consolidation in this space. -->

<!-- Notes:
DVC and lakeFS represent two philosophies for dataset versioning. DVC is lightweight and developer-centric: you add a large file, DVC computes its MD5 hash, stores the file in a cache (local or remote), and writes a small `.dvc` pointer file that Git tracks. Because the cache is content-addressed, identical files are stored only once regardless of how many versions reference them. This makes DVC ideal for individual data scientists or small teams who already use Git and want minimal infrastructure overhead.

lakeFS operates at a higher level of abstraction: it exposes a Git-like interface (branches, commits, diffs, merges) over an entire object store. Zero-copy branching means creating a branch is a metadata pointer operation — no data is copied until a file is actually changed on that branch. This makes it practical to create isolated environments for ETL testing or model training without doubling storage costs. lakeFS integrates with Spark, Trino, and other engines via an S3-compatible gateway.

The November 2025 acquisition of DVC by Treeverse (the company behind lakeFS) consolidates the two leading open-source data versioning tools under one organization. The strategic positioning is clear: DVC for smaller, Git-native workflows; lakeFS for enterprise-scale pipelines requiring branch-level isolation across petabyte object stores.

For the recurring schema example, either tool can version the transactions + customer dimension tables: DVC would track snapshot files via pointer hashes, while lakeFS would let you branch the data lake, run a pipeline experiment, and merge results back — all without copying the underlying Parquet files.
-->
