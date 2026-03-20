# Outline: Spark Structured Streaming — Incremental Processing on a Batch Engine

## Slide 1: Title Slide
- type: TITLE
- content: "Spark Structured Streaming — Incremental Processing on a Batch Engine", subtitle: "Treating streams as unbounded tables", course: "Data Engineering, Lecture 4"

## Slide 2: Agenda
- type: AGENDA
- content:
  1. The Infinite Table Model
  2. Micro-Batch Execution Engine
  3. Exactly-Once Guarantees and Checkpointing
  4. Running Example: Clickstream Pipeline
  5. Watermarks and Late Data Handling
  6. Stateful Operations and State Stores
  7. Micro-Batch vs. Continuous Processing vs. Flink
  8. Operational Failure Modes and Production Concerns
  9. Summary and Key Takeaways

---

## Section A: The Infinite Table Model

## Slide 3: Why Unify Batch and Streaming?
- type: CONTENT
- claims: [claim:sss:declarative_incrementalization:004]
- speaker_notes_hint: Contrast the old DStream/Storm model (user builds physical DAG of operators) with Structured Streaming's declarative approach — the SIGMOD 2018 paper's core thesis that a relational API can automatically incrementalize static queries.

## Slide 4: Stream as an Unbounded Table
- type: CONTENT
- claims: [claim:sss:unbounded_table:001, claim:sss:batch_like_query:002]
- speaker_notes_hint: Draw the mental picture — every arriving record is a new row appended to an ever-growing Input Table; the user writes the same query they would write on a static table, and Spark runs it incrementally.

## Slide 5: Same API, Batch and Streaming
- type: CONTENT
- claims: [claim:sss:same_api:003, claim:sss:catalyst_reuse:005]
- speaker_notes_hint: Emphasize that the DataFrame/Dataset query is identical for batch and streaming. Catalyst and Tungsten optimizations (predicate pushdown, projection pushdown, code generation) apply automatically — zero extra work for the developer.

## Slide 6: Incremental, Not Materialized
- type: CONTENT
- claims: [claim:sss:incremental_state:006, claim:sss:incremental_execution:012]
- speaker_notes_hint: Clarify the key misconception — the engine does NOT keep the entire unbounded table in memory. It reads the latest available data, processes it incrementally via IncrementalExecution (which injects streaming-specific planner strategies like StatefulAggregationStrategy and StreamingJoinStrategy), keeps minimal intermediate state, and discards source data.

---

## Section B: Micro-Batch Execution

## Slide 7: Trigger Modes Overview
- type: CONTENT
- claims: [claim:sss:trigger_types:007]
- speaker_notes_hint: Walk through all four trigger modes — ProcessingTime (fixed interval; 0 means as-fast-as-possible), Once (deprecated since 3.4), AvailableNow (multi-batch then stop, replaces Once), and Continuous (experimental, ~1 ms latency, at-least-once). Our running example uses ProcessingTime("30 seconds").

## Slide 8: The Micro-Batch Execution Loop
- type: DIAGRAM
- claims: [claim:sss:microbatch_loop:008, claim:sss:offset_tracking:009]
- speaker_notes_hint: Present the Mermaid diagram showing the full loop: trigger fires -> latestOffset()/getOffset() on each source -> write offset range to WAL -> getBatch(committedOffsets, availableOffsets) -> IncrementalExecution plan -> sink.addBatch() -> commit offsets -> checkpoint state. Trace one full iteration step by step. Emphasize ~100 ms end-to-end latency floor.
- diagram: Mermaid flowchart of the micro-batch loop (trigger -> scan offsets -> WAL write -> getBatch -> incremental plan -> execute -> commit -> checkpoint)

## Slide 9: Offset Tracking Protocol
- type: CONTENT
- claims: [claim:sss:offset_tracking:009, claim:sss:offset_seq_log:011]
- speaker_notes_hint: Detail the committedOffsets vs. availableOffsets distinction on the driver. Explain OffsetSeqLog — versioned files in HDFS-compatible storage, one per batch ID. On restart, populateStartOffsets reads the latest committed batch to determine the resume point.

## Slide 10: Micro-Batch Latency
- type: CONTENT
- claims: [claim:sss:microbatch_latency:013]
- speaker_notes_hint: Set expectations — ~100 ms end-to-end latency is the practical floor for micro-batch due to task launch and scheduling overhead between batches.

---

## Section C: Exactly-Once Guarantees and Checkpointing

## Slide 11: WAL-Based Exactly-Once Protocol
- type: CONTENT
- claims: [claim:sss:wal_exactly_once:010]
- speaker_notes_hint: Walk through the two-log protocol — OffsetSeqLog written before execution, CommitLog written after successful sink output. On failure, compare the two to find the uncommitted batch and replay it. Combined with replayable sources and idempotent sinks this yields end-to-end exactly-once.

## Slide 12: Checkpoint Directory Layout
- type: DIAGRAM
- claims: [claim:sss:checkpoint_layout:029]
- speaker_notes_hint: Show directory tree: checkpoint/ -> offsets/ (one file per batch, written at start), commits/ (one file per batch, written at end), state/ (partitioned state store snapshots), metadata (query ID and config). On recovery the engine compares offsets vs. commits to find incomplete batches.
- diagram: Tree diagram of checkpoint directory structure (offsets/, commits/, state/, metadata)

## Slide 13: Recovery Semantics
- type: CONTENT
- claims: [claim:sss:state_checkpoint_recovery:030]
- speaker_notes_hint: Walk through recovery: read WAL to find last uncommitted epoch, load latest state snapshot, replay intermediate epochs with output disabled, rerun failed epoch relying on sink idempotence, resume. State checkpointing is async and does not need to happen every epoch.

---

## Section D: Running Example — Clickstream Pipeline

## Slide 14: Running Example Introduction
- type: CONTENT
- claims: [claim:sss:unbounded_table:001]
- speaker_notes_hint: Introduce the scenario — real-time clickstream from a web application (Kafka topic with user_id, url, event_time). Goal: 10-minute tumbling-window page-view counts per URL with a 5-minute watermark, writing to an Iceberg table. This example threads through the rest of the lecture.

## Slide 15: Complete Clickstream Query
- type: CODE
- claims: [claim:sss:same_api:003, claim:sss:batch_like_query:002, claim:sss:withwatermark_api:024]
- speaker_notes_hint: Walk through every line — readStream from Kafka, parse JSON, withWatermark("event_time", "5 minutes"), groupBy(window("event_time", "10 minutes"), "url").count(), writeStream to Iceberg with ProcessingTime trigger and checkpointLocation. Point out this is the same code as a batch groupBy, plus watermark and writeStream.
- code_block: PySpark — complete Structured Streaming query (readStream from Kafka -> parse JSON -> withWatermark -> groupBy window + URL -> count -> writeStream to Iceberg)

## Slide 16: What Happens Under the Hood
- type: CONTENT
- claims: [claim:sss:microbatch_loop:008, claim:sss:incremental_execution:012]
- speaker_notes_hint: Trace one micro-batch of the clickstream query through the execution loop — Kafka offsets discovered, IncrementalExecution builds plan with StatefulAggregationStrategy, window counts updated in state store, results written to Iceberg.

---

## Section E: Watermarks and Late Data

## Slide 17: The Late Data Problem — Unbounded State
- type: CONTENT
- claims: [claim:sss:watermark_state_bound:020]
- speaker_notes_hint: Without watermarks, every 1-minute window since the application began must be kept in state because a late record could arrive for any window — state grows without bound, especially when combined with a grouping key like URL.

## Slide 18: Watermark Definition
- type: CONTENT
- claims: [claim:sss:watermark_definition:019]
- speaker_notes_hint: Define watermark = max(event_time) - threshold. Emphasize natural robustness to backlog — if the system cannot keep up with the input rate, the watermark will not advance arbitrarily during that time. Cite SIGMOD 2018 Section 4.3.1.

## Slide 19: withWatermark() API and Placement Rules
- type: CODE
- claims: [claim:sss:withwatermark_api:024]
- speaker_notes_hint: Show correct and incorrect placement — must be on the same column as the aggregation, must precede the groupBy in the query plan. Calling withWatermark on a non-streaming DataFrame is a no-op. Show both valid and invalid code examples.
- code_block: PySpark — correct vs. incorrect withWatermark() placement examples

## Slide 20: How Watermarks Clean Up State
- type: CONTENT
- claims: [claim:sss:watermark_state_cleanup:021, claim:sss:watermark_guarantee:022]
- speaker_notes_hint: In Append mode the engine holds partial counts, waits for the watermark to pass the window end, then emits the final result and drops the window's state. The guarantee is one-sided: data within the threshold is never dropped, but data beyond the threshold may still be processed (just not guaranteed).

## Slide 21: Watermarks and Output Modes
- type: COMPARISON
- claims: [claim:sss:watermark_output_modes:023]
- speaker_notes_hint: Three-column comparison — Append (emit once after watermark passes, state cleaned), Update (emit partials each trigger, watermark cleans old state), Complete (emit full result table, state never cleaned). For the clickstream example writing to Iceberg, Append is the right choice.

## Slide 22: Late Data Scenario Walkthrough
- type: CONTENT
- claims: [claim:sss:watermark_definition:019, claim:sss:watermark_state_cleanup:021, claim:sss:watermark_guarantee:022]
- speaker_notes_hint: Concrete timeline using the clickstream example — max event_time is 12:30, watermark is 12:25 (5-min delay). A record at 12:22 is above the watermark and included in the 12:20-12:30 window. A record at 12:18 is below the watermark — may or may not be counted. The 12:10-12:20 window can now be emitted and its state dropped.

---

## Section F: Stateful Operations and State Stores

## Slide 23: Built-In Stateful Operations
- type: CONTENT
- claims: [claim:sss:stateful_ops:025, claim:sss:stream_joins:026]
- speaker_notes_hint: Three families — windowed aggregations (groupBy + agg), stream-stream joins (buffer both sides as state; inner joins optionally use watermarks, outer joins require them to bound state and emit NULLs), and arbitrary stateful processing via mapGroupsWithState/flatMapGroupsWithState for use cases like sessionization.

## Slide 24: State Store — HDFS-Backed vs. RocksDB
- type: COMPARISON
- claims: [claim:sss:hdfs_state_store:027, claim:sss:rocksdb_state_store:028, claim:sss:state_store_growth:033]
- speaker_notes_hint: Two-column comparison. HDFS-backed (default): all state in JVM heap HashMap, backed by versioned HDFS files — simple but large GC pauses with millions of keys. RocksDB (since 3.2): off-heap native memory + local disk, scales to 100M keys per executor, changelog checkpointing uploads only deltas — but requires explicit memory bounding via boundedMemoryUsage config.

---

## Section G: Micro-Batch vs. Continuous vs. Flink

## Slide 25: Comparison Table — Micro-Batch vs. Continuous vs. Flink
- type: COMPARISON
- claims: [claim:sss:microbatch_latency:013, claim:sss:continuous_mode_latency:014, claim:sss:continuous_ops_limited:015, claim:sss:continuous_long_running:016, claim:sss:flink_per_event:018]
- speaker_notes_hint: Three-column table — Spark Micro-Batch (~100 ms, exactly-once, full SQL/stateful), Spark Continuous (~1 ms, at-least-once, map-like ops only, no auto retry of failed tasks, Kafka/Rate sources only), Flink (per-event pipelined, exactly-once via async checkpoints, full stateful support, local state access). Discuss latency/throughput/guarantee tradeoffs.

## Slide 26: Why Continuous Processing Never Graduated
- type: CONTENT
- claims: [claim:sss:continuous_never_graduated:017, claim:sss:continuous_ops_limited:015, claim:sss:continuous_long_running:016]
- speaker_notes_hint: Three blockers — only map-like operations with no stateful processing, would have required maintaining two separate checkpointing systems, and significant engine reimplementation needed. Long-running tasks with no automatic retries made it fragile. The mode remains experimental and is not recommended for production.

---

## Section H: Operational Pitfalls

## Slide 27: The Small-File Problem
- type: CONTENT
- claims: [claim:sss:small_file_problem:031, claim:sss:iceberg_streaming_maintenance:036]
- speaker_notes_hint: Each micro-batch writes separate output files; _spark_metadata log grows unbounded and can OOM the driver. With Iceberg, each batch produces a new snapshot with its own small data files. Mitigations: increase trigger interval, run periodic compaction (rewriteDataFiles every 1-4 hours), expire old snapshots.

## Slide 28: State Store Growth Under Skewed Keys
- type: CONTENT
- claims: [claim:sss:state_store_growth:033, claim:sss:rocksdb_state_store:028]
- speaker_notes_hint: Skewed keys cause uneven state distribution — one executor holds disproportionate state, leading to GC pressure (HDFS store) or unbounded RocksDB memory growth. Mitigations: salting keys, switching to RocksDB with explicit memory bounds, monitoring state metrics via StreamingQueryListener.

## Slide 29: Checkpoint Compatibility — What You Can and Cannot Change
- type: COMPARISON
- claims: [claim:sss:checkpoint_compatibility:032, claim:sss:checkpoint_allowed_changes:035]
- speaker_notes_hint: Two-column table — safe changes (add/remove filters, change rate limits, change trigger interval) vs. breaking changes requiring a new checkpoint (shuffle partitions, state store provider, watermark policy, source count/type, stateful op modifications). Emphasize that shuffle.partitions is frozen because state is hash-partitioned.

## Slide 30: Table-Format Sinks — Delta Lake and Iceberg
- type: CONTENT
- claims: [claim:sss:delta_streaming_sink:034, claim:sss:iceberg_streaming_maintenance:036]
- speaker_notes_hint: Delta Lake provides auto-compaction and exactly-once via its transaction log, even with concurrent writers. Iceberg requires explicit maintenance — tune commit rate, expire snapshots, compact data files, rewrite manifests. Pitfall: deleting checkpoint and restarting without changing appId causes silent data loss in Delta. Tie back to the clickstream example writing to Iceberg.

---

## Section I: Wrap-Up

## Slide 31: Summary — Key Takeaways
- type: CONTENT
- claims: [claim:sss:declarative_incrementalization:004, claim:sss:wal_exactly_once:010, claim:sss:watermark_definition:019, claim:sss:unbounded_table:001]
- speaker_notes_hint: Recap the six learning objectives. (1) Infinite table model unifies batch and streaming via declarative incrementalization. (2) Micro-batch loop with two-log WAL protocol for exactly-once. (3) Continuous mode traded guarantees for latency but never matured; Flink wins on per-event latency. (4) Watermarks = max(event_time) - threshold; bound state and control completeness vs. latency. (5) State stores (HDFS vs. RocksDB) and checkpoint-based recovery enable fault-tolerant stateful processing. (6) Operational pitfalls — small files, state growth, checkpoint compatibility — require production planning.

## Slide 32: References and Further Reading
- type: CONTENT
- claims: []
- speaker_notes_hint: List key readings — Armbrust et al. "Structured Streaming: A Declarative API for Real-Time Applications in Apache Spark" (SIGMOD 2018), Zaharia et al. "Discretized Streams" (SOSP 2013), Apache Spark Structured Streaming Programming Guide, Delta Lake and Iceberg streaming documentation.
