# Lecture Request

**Topic:** Spark Structured Streaming — Incremental Processing on a Batch Engine
**Course:** Data Engineering, graduate level (Lecture 4)
**Prerequisites:** Spark SQL, DataFrames, Catalyst optimizer, batch ETL, basic streaming concepts (event time vs. processing time)
**Duration:** 90 minutes (~30 slides)
**Learning objectives:**
1. Explain the "infinite table" model — how Structured Streaming reuses the Spark SQL engine by treating a stream as an unbounded DataFrame, and why this unification with batch matters
2. Describe the micro-batch execution model: trigger intervals, incremental planning, WAL-based exactly-once guarantees, and the offset tracking protocol between sources and the driver
3. Compare micro-batch vs. Continuous Processing mode — latency/throughput tradeoffs, why Continuous mode never left experimental, and where Flink's per-record model wins
4. Explain watermarks and late data handling: how withWatermark() bounds state, the tradeoff between completeness and latency, and what happens to data that arrives after the watermark
5. Describe stateful operations (aggregations, stream-stream joins, flatMapGroupsWithState) and the mechanics of state checkpointing — RocksDB state store vs. HDFS-backed store, checkpoint layout, and recovery semantics
6. Recognize operational failure modes: small-file problem from frequent micro-batch commits, state store growth under skewed keys, checkpoint compatibility across code changes, and how these interact with Iceberg/Delta Lake sinks

**Notes:**
- Use a running example: a real-time clickstream pipeline — reading from Kafka, computing windowed page-view counts per URL with a 10-minute tumbling window and 5-minute watermark, writing to an Iceberg table.
- Include a Mermaid diagram showing the micro-batch execution loop (trigger → scan offsets → incremental plan → execute → commit offsets → checkpoint state).
- Include a comparison table of micro-batch vs. Continuous Processing vs. Flink.
- Include a diagram showing checkpoint layout (offsets/, commits/, state/).
- Include a code slide with a complete Structured Streaming query (readStream → transformations → writeStream) using the clickstream example.
- Where possible, cite the original Spark Structured Streaming paper and official Spark documentation.

**Key readings:**
- Armbrust et al., "Structured Streaming: A Declarative API for Real-Time Applications in Apache Spark" (SIGMOD 2018)
- Zaharia et al., "Discretized Streams: Fault-Tolerant Streaming Computation at Scale" (SOSP 2013) — for DStream context and motivation
- Apache Spark Documentation: Structured Streaming Programming Guide
