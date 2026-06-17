# Research Review — Objective 3

## Claims Summary

6 claims written for objective 3 (claim:agde:pit-join:001 through claim:agde:feature-store-when-not:006).

## Step 0: Embedded Factual Assertions in the Objective

The following specific factual assertions are embedded in objective 3's wording and were checked:

| Assertion | Claim ID | Status |
|---|---|---|
| Point-in-time joins prevent temporal leakage | claim:agde:pit-join:001 | VERIFIED — Feast docs confirm explicitly |
| Feature store = offline + online + shared-transformation-definition pattern | claim:agde:feature-store-arch:002 | VERIFIED — multiple sources confirm the dual-store + feature view registry architecture |
| Feature store introduces a "second consistency problem" | claim:agde:feature-store-consistency:003 | VERIFIED — Hopsworks docs confirm online-offline consistency as a distinct operational concern |
| ANSI window/lateral is the portable SQL implementation of as-of semantics | claim:agde:ansi-window-pit:005 | PARTIALLY VERIFIED — ANSI window functions and LATERAL are confirmed in SQL:2003/2008, but no source explicitly benchmarks them as slower than ASOF JOIN for this purpose |
| ASOF JOIN exists as named syntax in DuckDB, ClickHouse, and kdb+ | claim:agde:asof-join-dialects:004 | VERIFIED — DuckDB blog and Altinity blog confirm all three; kdb+ aj function confirmed via web search |
| ClickHouse ASOF JOIN was inspired by kdb+ | claim:agde:asof-join-dialects:004 | VERIFIED — Altinity blog states "ClickHouse's ASOF implementation was based on the kdb+ asof operator" |
| Feature store not needed for single model, single team, batch-only inference | claim:agde:feature-store-when-not:006 | VERIFIED — multiple practitioner sources confirm batch-only / single-model exemption |

## Confidence Gaps

**claim:agde:ansi-window-pit:005 (MEDIUM):** The claim that ANSI window/LATERAL implementations are "typically slower" than dialect-specific ASOF JOIN is supported by DuckDB's own blog stating their ASOF join is "several orders of magnitude" faster than window-function alternatives, but this comparison is DuckDB-specific. No cross-database benchmark was found to generalize this claim. The core assertion (ANSI window functions and LATERAL are portable mechanisms for as-of semantics) is HIGH confidence; the performance comparison is LOW-MEDIUM confidence.

**Hopsworks source (claim:agde:feature-store-consistency:003):** The Hopsworks dictionary page timed out when fetching directly. The excerpt was confirmed via Google search snippet text. If direct verification is required, the page at https://www.hopsworks.ai/dictionary/online-offline-feature-store-consistency should be visited manually.

## No Unverified Claims in Objective Wording

No assertion in the objective wording was found to be factually incorrect or unverifiable. All key technical claims are supported by authoritative sources (Feast documentation, DuckDB official blog, Altinity/ClickHouse technical blog, Hopsworks MLOps dictionary).
