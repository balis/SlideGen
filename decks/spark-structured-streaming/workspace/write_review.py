import json

data = {
  "batch": 3,
  "draft": "draft_v2.md",
  "slides_checked": "17-24 (Sections E-F)",
  "checker_mode": "full_rescan",
  "verdict": "VERIFIED",
  "summary": "All 11 claim references across 8 slides in Sections E-F are supported by their source files. The previously flagged issue with claim:sss:rocksdb_state_store:028 (changelog shown as default in v1) has been corrected.",
  "claim_verdicts": {
    "verified_count": 11,
    "misrepresented": [],
    "unverified": [],
    "details": [
      {
        "claim_id": "claim:sss:watermark_state_bound:020",
        "slide": "The Late Data Problem - Unbounded State",
        "bullet": "Without watermarks, every window since the application began must be kept in state because a late record could arrive for any window",
        "verdict": "VERIFIED",
        "source_excerpt": "the system needs to remember a count for every 1-minute window since the application began, because a late record might still arrive for any particular minute"
      },
      {
        "claim_id": "claim:sss:watermark_definition:019",
        "slide": "Watermark Definition",
        "bullet": "Watermark = max(event_time) - delay_threshold and naturally robust to backlog",
        "verdict": "VERIFIED",
        "source_excerpt": "the watermark for C is max(C) - t_C... this choice of watermark is naturally robust to backlogged data"
      },
      {
        "claim_id": "claim:sss:withwatermark_api:024",
        "slide": "withWatermark() API and Placement Rules",
        "bullet": "withWatermark() must be on the same column as the aggregation and must precede the groupBy. Calling it on a non-streaming Dataset is silently a no-op",
        "verdict": "VERIFIED",
        "source_excerpt": "withWatermark must be called on same column as the timestamp column used in the aggregate... withWatermark must be called before the aggregation... using withWatermark on a non-streaming Dataset is no-op"
      },
      {
        "claim_id": "claim:sss:watermark_state_cleanup:021",
        "slide": "How Watermarks Clean Up State",
        "bullet": "In Append mode: engine holds partial results, waits for watermark to pass window end, emits final result and drops state",
        "verdict": "VERIFIED",
        "source_excerpt": "The engine waits for late data to be counted, then drops intermediate state of a window < watermark, and appends the final counts to the Result Table/sink"
      },
      {
        "claim_id": "claim:sss:watermark_guarantee:022",
        "slide": "How Watermarks Clean Up State / Late Data Scenario Walkthrough",
        "bullet": "One-sided guarantee: data within threshold never dropped. Data beyond threshold may or may not be processed",
        "verdict": "VERIFIED",
        "source_excerpt": "any data less than 2 hours behind is guaranteed to be aggregated... Data delayed by more than 2 hours is not guaranteed to be dropped. It may or may not get aggregated"
      },
      {
        "claim_id": "claim:sss:watermark_output_modes:023",
        "slide": "Watermarks and Output Modes",
        "bullet": "Watermarks interact differently with each output mode. Append emits once after watermark, Update prunes old state, Complete retains all state",
        "verdict": "VERIFIED",
        "source_excerpt": "Append: appends the final counts... Update mode uses watermark to drop old aggregation state... Complete mode does not drop old aggregation state"
      },
      {
        "claim_id": "claim:sss:stream_joins:026",
        "slide": "Built-In Stateful Operations",
        "bullet": "Stream-stream joins buffer both sides as state so every future input can be matched with past input. Inner joins watermarks optional, outer joins watermarks mandatory",
        "verdict": "VERIFIED",
        "source_excerpt": "for both the input streams, we buffer past input as streaming state, so that we can match every future input with past input"
      },
      {
        "claim_id": "claim:sss:stateful_ops:025",
        "slide": "Built-In Stateful Operations",
        "bullet": "mapGroupsWithState / flatMapGroupsWithState for custom logic like sessionization. mapGroupsWithState returns one record, flatMapGroupsWithState returns zero or more",
        "verdict": "VERIFIED",
        "source_excerpt": "flatMapGroupsWithState can return zero or more values of type R per update instead of one... sessionization"
      },
      {
        "claim_id": "claim:sss:hdfs_state_store:027",
        "slide": "State Store - HDFS-Backed vs. RocksDB",
        "bullet": "HDFS-backed state store: all state in JVM heap, backed by versioned HDFS files, prone to GC pauses with millions of keys",
        "verdict": "VERIFIED",
        "source_excerpt": "all the data is stored in memory map in the first stage, and then backed by files in an HDFS-compatible file system... large number of state objects puts memory pressure on the JVM causing high GC pauses"
      },
      {
        "claim_id": "claim:sss:rocksdb_state_store:028",
        "slide": "State Store - HDFS-Backed vs. RocksDB",
        "bullet": "RocksDB: off-heap native memory + local disk, changelog checkpointing uploads only deltas. Table correctly shows Full snapshot (default) or changelog (opt-in, Spark 3.3+)",
        "verdict": "VERIFIED",
        "note": "Previously MISREPRESENTED in v1 (changelog shown as default). Now FIXED - table correctly shows Full snapshot (default) or changelog (opt-in, Spark 3.3+).",
        "source_excerpt": "changelog checkpointing uploads changes made to the state since the last checkpoint... Enable with: spark.sql.streaming.stateStore.rocksdb.changelogCheckpointing.enabled=true"
      },
      {
        "claim_id": "claim:sss:state_store_growth:033",
        "slide": "State Store - HDFS-Backed vs. RocksDB",
        "bullet": "RocksDB memory must be explicitly bounded via boundedMemoryUsage to prevent unbounded native memory growth",
        "verdict": "VERIFIED",
        "source_excerpt": "If left unbounded, RocksDB memory usage across multiple instances could grow indefinitely... setting the spark.sql.streaming.stateStore.rocksdb.boundedMemoryUsage config to true"
      }
    ]
  },
  "previously_flagged_resolution": {
    "claim_id": "claim:sss:rocksdb_state_store:028",
    "v1_issue": "Changelog checkpointing was presented as the default behavior of RocksDB state store",
    "v2_status": "FIXED - table now correctly shows Full snapshot (default) or changelog (opt-in, Spark 3.3+)"
  }
}

with open("/home/balis/slidegen/slide-agent/decks/spark-structured-streaming/workspace/review_v2_batch_3.json", "w") as f:
    json.dump(data, f, indent=2)

print("Written successfully")
