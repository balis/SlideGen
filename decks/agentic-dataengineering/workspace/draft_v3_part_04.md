## Reproducibility as a Three-Layer Temporal Problem

- Embedding benchmark reproducibility (e.g., MTEB) requires pinning three components: the evaluation task protocol, the dataset revision, and the model checkpoint or API version [claim:agentic-de:023]
- Without coupling all three, result comparability is lost — changing any of task protocol, dataset revision, or model checkpoint produces different results [claim:agentic-de:023]
- The same temporal coupling problem applies broadly to ML pipelines: data state, pipeline code, and model version must all be pinned to a consistent point in time for a run to be reproducible

<!-- Speaker: Introduce reproducibility as a multi-layer problem rooted in the MTEB benchmark literature, then broaden to general ML pipeline practice; stress that the three components must be pinned together, not just individually. -->

<!-- Notes:
The slide draws the key insight from MTEB (Massive Text Embedding Benchmark) reproducibility work: when comparing embedding model evaluations, you must pin the evaluation task protocol, the exact dataset revision, and the specific model checkpoint or API version. Change any one of these and you cannot compare results. The third bullet extends this lens to general ML pipelines without attributing it to the MTEB source — it is a synthesis the instructor should present as a conceptual generalization. Emphasize to students that this is not merely about saving files: it is about the coupling between all three versioning dimensions simultaneously. A common misconception is that versioning data is sufficient; students should understand that a model checkpoint change alone invalidates prior results even on the same data snapshot.
-->

---

## Lakehouse Time Travel — Delta Lake and Iceberg

- Delta Lake time travel supports querying historical table versions by timestamp or version number; the default VACUUM retention period is 7 days (`delta.deletedFileRetentionDuration`), so time travel beyond 7 days requires explicitly increasing retention at the cost of additional storage [claim:agentic-de:018]
- Apache Iceberg implements time travel through immutable snapshots: each write creates a new snapshot referencing manifest lists and data files; historical queries reference the same underlying Parquet/ORC files without duplicating data, until snapshot accumulation causes metadata bloat [claim:agentic-de:019]

<!-- Speaker: Compare the two lakehouse formats side by side — both enable time travel but differ in retention defaults and internal metadata mechanics; the metadata bloat caveat for Iceberg is an important operational detail. -->

<!-- Notes:
Delta Lake's time travel is straightforward to use but requires proactive retention configuration. The default 7-day VACUUM window is often too short for ML reproducibility needs, where a training run might be audited weeks or months later. Increasing `delta.deletedFileRetentionDuration` keeps older file versions available but increases storage costs proportionally. Apache Iceberg's snapshot model is conceptually elegant: each write appends a new snapshot in the metadata layer, and all historical snapshots share the original data files (no duplication). The practical risk is that without periodic snapshot expiration (e.g., via `expireSnapshots`), the metadata files grow unboundedly, increasing query planning overhead. Students should understand that "time travel" is a metadata-layer feature in both systems — the data files themselves are immutable and shared across snapshots.
-->

---

## Content-Addressable Versioning — DVC and lakeFS

- DVC uses content-addressable storage with MD5 hashes to deduplicate data: files are stored in a cache keyed by hash, and lightweight `.dvc` metafiles tracked in Git act as pointers, linking each Git commit to an exact dataset state without storing large files in the repository [claim:agentic-de:020]
- lakeFS provides Git-like version control (branches, commits, merges) over object storage (S3, GCS, Azure Blob) using zero-copy branching: creating a branch is a metadata-only operation with no data duplication; storage overhead only occurs when data is actually modified on a branch [claim:agentic-de:021]
- Treeverse (lakeFS) acquired the DVC open-source project from Iterative.ai; DVC continues as a lightweight Git-based tool for smaller data-science projects while lakeFS serves enterprise-scale AI/ML infrastructure [claim:agentic-de:022]

<!-- Speaker: Walk through both tools as complementary points on the versioning spectrum — DVC is file-centric and Git-integrated; lakeFS is object-store-native and branch-oriented; the acquisition brings them under one roof. -->

<!-- Notes:
DVC's content-addressable model is efficient because two datasets that share unchanged files share the same cache entries — only changed files need new storage. The `.dvc` pointer files are small text files that Git can track efficiently. This makes DVC well-suited to small teams and projects where data fits in a single object store bucket or even a shared filesystem. lakeFS operates at the object-store level and introduces a thin metadata layer (similar to a Git index) that intercepts reads and writes. Zero-copy branching means a data scientist can create an experimental branch of a 10 TB dataset in milliseconds, make modifications, and only pay for the delta in storage. The Treeverse acquisition of DVC is relevant context: the two tools now share governance but serve different niches, which is a deliberate positioning choice. Students should understand the architectural difference: DVC tracks file-level hashes via Git; lakeFS tracks object-store paths via its own commit graph.
-->
