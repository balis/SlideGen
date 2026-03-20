# Writer Feedback for draft_v1

## Fact-Check Issues

### Issue 1: Missing "most" qualifier on Catalyst optimizations (Slide: Same API, Batch and Streaming)
The bullet says optimizations "apply automatically" without qualification. The source says "most of the optimization rules." Insert "most" before "optimizations."

### Issue 2: Exactly-once attribution incomplete (Slide: WAL-Based Exactly-Once Protocol)
The opening bullet attributes exactly-once to "two persistent logs" alone. The source requires three components working together: write-ahead logs + replayable sources + idempotent sinks. Fix the opening bullet to mention all three.

### Issue 3: Changelog checkpointing shown as RocksDB default (Slide: State Store HDFS-Backed vs. RocksDB)
The comparison table cell says "Changelog -- only deltas uploaded" as if it is the default. Changelog checkpointing is opt-in (Spark 3.3+). Change to "Full snapshot (default) or changelog (opt-in, Spark 3.3+)."

### Issue 4: Flink claims exceed source (Slide: Comparison Table)
The Flink column says "Sub-millisecond" latency and "Local state (RocksDB)." The cited source says "very low processing latencies" (no sub-millisecond claim) and "local, often in-memory, state" (no RocksDB mention). Change to "Very low (per-event)" and "Local, often in-memory state."
