## Reproducibility as a Three-Layer Temporal Problem

- ML treats datasets as versioned, time-aware artifacts — immutable snapshots tied to a specific point in time — rather than as query targets, because reproducibility requires knowing exactly what data state produced a given model or index [claim:agde:005]
- The embedding model is baked into every stored vector: vectors from model version A and version B occupy incompatible geometric spaces, so mixing them makes similarity scores meaningless; changing the embedding model requires a full re-index of the entire corpus [claim:agde:023]
- Three layers must be pinned together to reconstruct any artifact: (1) data state at training time, (2) dataset version, (3) embedding model version

<!-- Speaker: Frame this as a stack of temporal dependencies before diving into tools — if any one layer is unpinned, the artifact is not reproducible. Transition: "We'll look at a concrete mechanism for each layer." -->

<!-- Notes:
This slide establishes the conceptual frame for Section D. The three-layer decomposition helps students understand why reproducibility in ML is structurally harder than in software engineering, where pinning a code commit is usually sufficient.

Layer 1 (data state at training time) corresponds to time-travel in lakehouse formats — the question "what rows existed when training ran?" Layer 2 (dataset version) is the identity of the curated, processed training set — tools like DVC and lakeFS address this. Layer 3 (embedding model version) is often overlooked: vectors are derived artifacts whose semantics are entirely defined by the model that produced them, so a model upgrade silently invalidates the entire index.

A common student misconception is that "saving the data" is sufficient for reproducibility. This slide surfaces the two additional failure points: dataset versioning without model pinning, and model pinning without data-state traceability. Emphasize that all three must be stored together — for example in an experiment tracking entry — to allow any artifact to be reconstructed.
-->

---

## Lakehouse Time-Travel — Delta and Iceberg Snapshots

- Apache Iceberg represents every table state as an immutable snapshot — a manifest list pointing to manifest files, each listing data files — so querying a specific snapshot ID retrieves exactly the set of data files that existed at that point in time, making the snapshot ID a sufficient reproducibility token for a training dataset [claim:agde:019]
- Delta Lake and Apache Iceberg both support time-travel queries by version number or timestamp, but retaining historical snapshots incurs ongoing storage cost; expiring snapshots in Iceberg (via `expireSnapshots`) or running `VACUUM` in Delta Lake permanently removes the referenced data files, eliminating the ability to time-travel to those versions [claim:agde:020]
- Operators must explicitly configure a retention policy that balances the reproducibility window against storage cost [claim:agde:020]

<!-- Speaker: Stress the irreversibility of VACUUM/expireSnapshots — this is not a soft delete. Once run, the data files are gone and the snapshot cannot be restored. A retention policy is an operational contract, not a default. -->

<!-- Notes:
The Iceberg snapshot mechanism is elegant: the manifest list → manifest file → data file hierarchy means that a single integer (the snapshot ID) is a complete, stable pointer to a table state. Students who know Iceberg's spec will recognize this; for others, the key intuition is that Iceberg never overwrites data files in place — it always appends new files and updates the pointer, so old states remain accessible until explicitly expired.

The Delta Lake analogy is important because many students will encounter Delta in Databricks environments. The behavior is equivalent: `VACUUM` with a retention threshold removes files older than that threshold, breaking time-travel to those versions.

The practical tension to highlight: a 90-day retention window on a 10 TB table that ingests 100 GB/day means roughly 9 TB of historical snapshot data in addition to the current table. Finance and compliance teams often push for longer retention; the storage cost is real. The engineering answer is to pin the specific snapshot IDs used for training in a lightweight metadata record (experiment tracker, model card), so you don't need to retain all snapshots indefinitely — only the ones tied to live models.

Common misconception: students sometimes think "the table is versioned so I'm fine." The risk is that a nightly VACUUM job — often set up by a different team — quietly destroys the snapshots the ML team needs. Governance between teams is as important as the technical mechanism.
-->

---

## DVC — Content-Addressable Dataset Versioning

- DVC implements content-addressable storage for ML datasets: it computes an MD5 hash of each tracked file and stores a small `.dvc` metafile in Git, while the actual data lives in a remote (S3, GCS, etc.); only new or modified files are stored in the remote cache, with identical content deduplicated by hash [claim:agde:021]
- Reproducing a dataset at any prior state requires only `git checkout <commit>` followed by `dvc pull` — the metafile in Git drives retrieval of the exact data version [claim:agde:021]

<!-- Speaker: The elegance of DVC is that it piggybacks on Git's commit history — dataset versions are tied to code commits automatically. Walk through the two-command reproduction flow. -->

<!-- Notes:
DVC solves a specific and common problem: teams already using Git for code want dataset versioning without adopting a new storage system. The `.dvc` metafile is tiny (a few hundred bytes) and tracks by MD5 hash, so the Git history becomes the index of all dataset versions. The remote cache holds the actual bytes; local operations are fast because DVC only fetches what's needed.

The deduplication property is practically important: if you have 50 versions of a training set that differ only in 5% of rows, the remote stores roughly 100% + 5%×49 ≈ 345% of the single-version size, not 5000%. This makes DVC viable for moderate-scale ML teams.

The scalability caveat (covered on the next comparison slide) is worth previewing: MD5 hashing millions of small files serializes on the client, and there is no server-side metadata index — at petabyte scale with billions of objects, this becomes a bottleneck. DVC works best for projects where datasets are tens to hundreds of GB and the number of tracked files is in the thousands, not billions.

Students with a software engineering background will immediately grasp DVC because it mirrors how npm lock files and package managers work: a small manifest in the versioned repo, actual artifacts in a content-addressed store.
-->

---

## lakeFS — Git Semantics Over Object Storage

- lakeFS implements Git-like versioning (branch, commit, merge, tag, revert) as a metadata layer directly over object storage (S3, Azure Blob, GCS) without copying data objects; branch creation is a zero-copy operation that creates a lightweight metadata pointer to the current commit [claim:agde:022]
- A lakeFS commit reference provides a reproducibility token analogous to a Git commit hash for code, allowing any experiment to be reproduced by checking out the same lakeFS commit of the dataset even as the underlying data evolves [claim:agde:022]

<!-- Speaker: The key differentiator from DVC is operational scale — branching a terabyte dataset is a millisecond metadata operation, not a data copy. Position lakeFS as the choice when DVC's per-file hashing becomes impractical. -->

<!-- Notes:
lakeFS's architectural insight is to separate the control plane (metadata: which objects belong to which branch/commit) from the data plane (the objects themselves, which stay in the object store). Because the data plane is untouched, branching, committing, and merging are purely metadata operations — O(1) in time, regardless of dataset size.

This makes lakeFS qualitatively different from DVC: where DVC computes hashes client-side and transfers data through its cache, lakeFS clients talk directly to the object store for reads and writes, with only metadata flowing through the lakeFS server. At petabyte scale with billions of objects, this is the difference between a practical and an impractical system.

The Git analogy is deliberately close: lakeFS exposes a branching model that data engineers familiar with Git can reason about immediately. Experimentation happens on feature branches; merges to main require passing data quality checks (analogous to CI on code). This pattern enables atomic dataset changes with full audit history.

The tradeoff is infrastructure: lakeFS requires a running metadata server (deployable on Kubernetes, managed via Treeverse, or as a SaaS), which DVC does not. For small teams or early-stage projects, this operational overhead may not be justified. This is the core of the comparison slide that follows.
-->

---

## Comparison — Three Reproducibility Strategies

- Iceberg/Delta time-travel is built into the table format with no additional tooling, but couples reproducibility to the table format and incurs storage cost for retained snapshots; `VACUUM`/`expireSnapshots` permanently destroys the reproducibility window if run without an explicit retention policy [claim:agde:020]
- DVC stores an MD5 metafile in Git and the actual data in a remote, making it Git-friendly and requiring no additional infrastructure, but performance degrades significantly at hundreds of millions or billions of objects (petabyte-scale data lakes) because per-file MD5 hashing is not viable at that scale [claim:agde:021] [claim:agde:024]
- lakeFS provides zero-copy branching and commit references over object storage at very large scale by routing only metadata through its server while data I/O goes directly to the object store; however, it requires deploying and maintaining a dedicated metadata server [claim:agde:022] [claim:agde:024]

<!-- Speaker: Summarize the decision heuristic: team scale and existing infrastructure drive the choice — not feature completeness. A single-model team on Iceberg already has time-travel; a multi-team org at petabyte scale needs lakeFS. -->

<!-- Notes:
This comparison slide is the practical payoff of Section D. The three strategies are not competing on the same axis: Iceberg/Delta time-travel solves the data-state layer (layer 1) but does not address dataset curation versioning the way DVC or lakeFS do. DVC and lakeFS are more directly comparable.

Decision heuristic to share with students:
- If the team is already on a lakehouse (Iceberg or Delta), use time-travel for training data snapshots and pin snapshot IDs in the experiment tracker. No additional tooling needed.
- If the team uses Git for everything and datasets are under a few hundred GB with thousands of files, DVC is the lowest-friction addition.
- If the organization manages petabyte-scale data lakes with multiple teams and needs atomic, branchable, auditable dataset changes, lakeFS justifies its metadata-server overhead.

The MEDIUM confidence on claim:agde:024 is worth noting to advanced students: the DVC scalability threshold is not precisely documented; "hundreds of millions of objects" is qualitative, and teams should benchmark against their own workload.

Also worth emphasizing: none of these tools eliminate the need to pin all three layers (data state, dataset version, embedding model version). They each address layer 1 and 2; layer 3 (embedding model versioning) requires separate discipline — recording the model ID and version alongside every vector index.
-->
