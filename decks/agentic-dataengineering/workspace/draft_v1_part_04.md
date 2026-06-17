## Reproducibility as a Three-Layer Temporal Problem

- ML reproducibility requires pinning three layers to the same point in time: data state (lakehouse snapshots or content-addressed versions), code/pipeline state (Git commits), and embedding-model version (checkpoint or API version) [claim:agentic-de:023]
- Without coupling all three layers, re-running a pipeline on "the same data" can produce different results if the embedding model has changed [claim:agentic-de:023]

<!-- Speaker: Frame this as the unifying insight of Section D — point-in-time correctness, dataset versioning, and embedding-model versioning are one temporal problem at three layers. Ask: "What was the data state when this artifact was produced?" -->

<!-- Notes:
This slide introduces the central conceptual framework for the reproducibility section. Students already understand point-in-time joins from the feature-store discussion; now we generalize that temporal discipline upward. The key insight is that "same data" is insufficient for reproducibility — you must also fix the transformation code and the embedding model version. A common failure scenario: a team re-embeds a corpus after an API provider silently upgrades their embedding model, and downstream retrieval quality changes with no code or data diff to explain it. This three-layer framing also previews the embedding-model lock-in problem covered later in the lecture. Encourage students to think of reproducibility not as a single version number but as a tuple of (data version, code commit, model checkpoint).
-->

---

## Lakehouse Time Travel — Delta Lake and Iceberg

| Aspect | Delta Lake | Apache Iceberg |
|---|---|---|
| Mechanism | Version/timestamp queries on the transaction log | Immutable snapshots referencing manifest lists and data files |
| Retention | Default 7-day VACUUM (`delta.deletedFileRetentionDuration`); extending retention costs additional storage [claim:agentic-de:018] | No automatic expiry; snapshots accumulate until explicitly expired |
| Storage model | Older data files removed by VACUUM [claim:agentic-de:018] | Time-travel queries reference the same underlying Parquet/ORC files — no data duplication — but snapshot accumulation causes metadata bloat [claim:agentic-de:019] |

<!-- Speaker: Walk through each column and stress the practical trade-off — Delta gives time travel cheaply but loses it after VACUUM; Iceberg preserves history longer but requires metadata housekeeping. -->

<!-- Notes:
Both Delta Lake and Iceberg solve the same problem — querying a table as it existed at a past point in time — but their architectures differ meaningfully. Delta Lake uses a transaction log and retains old data files only until VACUUM runs; the default 7-day retention is a pragmatic default for production workloads where storage cost matters. Extending retention is a simple configuration change but incurs linear storage growth. Iceberg takes an immutable-snapshot approach: every write creates a new snapshot, and time-travel queries simply follow older snapshot pointers to the same underlying data files, so no data is duplicated. The cost appears in metadata: each snapshot adds manifest entries, and over time this metadata bloat increases query-planning memory requirements. In practice, teams run periodic snapshot expiration (e.g., `expire_snapshots`) to manage this. Students should understand that neither approach is free — both trade storage or metadata overhead for temporal queryability, and the right choice depends on retention requirements and operational maturity.
-->

---

## Content-Addressable Versioning — DVC and lakeFS

| Aspect | DVC | lakeFS |
|---|---|---|
| Storage model | Content-addressable storage with MD5 hashes; files cached by hash to deduplicate; lightweight `.dvc` metafiles in Git act as pointers linking each commit to an exact dataset state [claim:agentic-de:020] | Git-like branches, commits, and merges over object storage (S3, GCS, Azure Blob) using zero-copy branching — creating a branch is a metadata-only operation with no data duplication [claim:agentic-de:021] |
| Sweet spot | Smaller data-science projects with Git-centric workflows [claim:agentic-de:022] | Enterprise-scale AI/ML infrastructure requiring branch isolation and atomic commits [claim:agentic-de:022] |
| Convergence | Treeverse (lakeFS) acquired DVC from Iterative.ai in November 2025, positioning lakeFS as the unified standard for data version control while DVC continues as a lightweight Git-based tool [claim:agentic-de:022] |

<!-- Speaker: Highlight that both tools solve dataset versioning but at different scales. Mention the 2025 acquisition as evidence that the ecosystem is consolidating around a Git-for-data metaphor. -->

<!-- Notes:
DVC and lakeFS represent two philosophies for dataset versioning. DVC stays close to Git: it stores small pointer files (`.dvc` metafiles) in the repository, each referencing a content-addressed blob in a separate cache. Because the cache is keyed by MD5 hash, identical files are never stored twice regardless of filename or location. This makes DVC lightweight and familiar to data scientists already using Git, but it does not natively support branching over the data itself — branches exist only at the Git (pointer) level. lakeFS, by contrast, operates directly on the object store, providing full Git semantics (branch, commit, merge, diff) over S3-compatible storage. Zero-copy branching means creating a branch writes only metadata; actual storage overhead appears only when data is modified on a branch. This makes lakeFS suitable for large-scale environments where teams need isolated experimentation branches without duplicating terabytes of data. The November 2025 acquisition of DVC by Treeverse signals market consolidation: rather than competing, the two projects now occupy complementary niches — DVC for individual or small-team workflows, lakeFS for organizational infrastructure. Students should recognize that dataset versioning is not optional in reproducible ML pipelines; the choice is which tool fits their operational context.
-->
