## RAG Is Not a Single Similarity Lookup

- RAG retrieval is a two-stage data pipeline: stage 1 (retrieval) maximizes recall by casting a wide net; stage 2 (reranking) maximizes precision by scoring the retrieved set more carefully [claim:agde:049]
- Chunking is the schema-design decision that precedes both stages: chunk size, boundary policy, and structure determine which information units are indexed and retrieved [claim:agde:044]
- There is no universal optimal chunk size — smaller chunks (64–128 tokens) favor fact-based queries while larger chunks (512–1024 tokens) favor contextual queries [claim:agde:044]

<!-- Speaker: Frame RAG as a two-stage pipeline with chunking as its schema layer — this resets expectations before diving into each stage. Transition: chunking decisions are made once at index time but affect every query. -->

<!-- Notes:
Many students arrive thinking RAG is a single vector similarity lookup. This slide corrects that mental model early. The two-stage framing (retrieval for recall, reranking for precision) is the organizing principle for the next four slides.

Chunking is deliberately called a "schema-design decision" because it shares the same characteristics: it is made at index time, it affects the entire downstream system, and changing it requires rebuilding the index — analogous to changing a table's grain in a data warehouse. The chunk is the unit of retrieval, so choosing its size is equivalent to choosing at what granularity to answer questions.

The absence of a universal optimal size is a useful analogy to table normalization: the right grain depends on the query patterns, and in practice systems often index at multiple granularities (small chunks for retrieval, larger context windows returned to the LLM) to get the benefits of both.
-->

---

## Chunking Strategy — A Schema Design Decision

- Large chunks can exceed token limits or include irrelevant content, reducing precision; small chunks may lack surrounding context needed for accurate generation [claim:agde:045]
- Chunk size is a design tradeoff: increasing it improves context availability but dilutes specificity; decreasing it sharpens specificity but loses context [claim:agde:045]
- This tradeoff is directly analogous to schema-design decisions about table granularity — the right answer depends on the dominant query pattern [claim:agde:045]

<!-- Speaker: Drill into the precision–recall tension introduced on the previous slide. Use the schema analogy to ground it: a too-wide table wastes I/O; a too-narrow table requires too many joins. -->

<!-- Notes:
The key insight is that chunk size creates a direct tension between two desirable properties: specificity (the chunk contains exactly the answer) and context (the chunk contains enough surrounding text for the LLM to interpret the answer correctly). Neither extreme is correct for all workloads.

In practice, teams commonly adopt one of three strategies: (1) fixed-size chunking with overlap (simple, predictable); (2) sentence or paragraph boundary chunking (respects natural language units); (3) hierarchical/multi-granularity indexing where both small and large chunks are stored and the retriever chooses. The last strategy is increasingly common in production systems.

The schema-design analogy is pedagogically useful: students who have designed fact tables understand that choosing the wrong grain is expensive to fix. The same is true of chunk size — re-chunking and re-embedding a large corpus is a significant engineering effort, so the decision should be deliberate.

A common student misconception is that larger chunks are always better because they give the LLM more context. Emphasize that the retrieval stage operates on the chunk as a unit: a large chunk that contains the answer plus five unrelated paragraphs will receive a lower similarity score than a focused chunk that contains only the answer.
-->

---

## Hybrid Retrieval — BM25 + Dense ANN

- BM25 sparse retrieval and dense ANN retrieval fail in complementary directions: BM25 excels at exact-match queries (product codes, error codes, rare identifiers) but has no semantic understanding [claim:agde:046]
- Dense retrieval handles paraphrase and conceptual queries but may assign low scores to exact rare-term matches — making hybrid retrieval the recommended baseline for production RAG [claim:agde:046]
- RRF (Reciprocal Rank Fusion), introduced at SIGIR 2009, is the standard fusion algorithm: it computes RRF(c) = Σ 1/(rank_i(c) + k) with k=60, operating on rank positions rather than raw scores [claim:agde:047]

<!-- Speaker: Explain why neither retriever alone is sufficient, then introduce RRF as the fusion mechanism. The key point is that RRF sidesteps score incompatibility by working on ranks. -->

<!-- Notes:
The complementary failure modes of BM25 and dense retrieval are the core justification for hybrid search. BM25 is a term-frequency model: it rewards documents that contain the query terms frequently and penalizes common terms (IDF). It has no model of meaning, so paraphrase ("automobile" vs "car") is invisible to it. Dense retrieval encodes both query and document into a shared semantic space, so paraphrase is handled naturally — but rare, highly specific terms (a product SKU, an error code) may be underrepresented in the embedding space if they appeared infrequently in training data.

RRF was introduced by Cormack, Clarke, and Büttcher at SIGIR 2009. The formula RRF(c) = Σ 1/(rank_i(c) + 60) is summed over all retrieval systems that returned candidate c. The smoothing constant k=60 prevents very high-ranked documents from dominating too strongly. The critical engineering advantage of RRF over score-level fusion is that BM25 scores (TF-IDF based, unbounded) and cosine similarities (bounded [-1, 1]) are not on the same scale — combining them directly requires calibration that is query-dependent and brittle. RRF avoids this entirely by discarding scores and using only rank order.

Students sometimes ask whether k=60 is tunable. It is, but empirically k=60 has proven robust across many retrieval tasks and is the standard default.
-->

---

## Code — Reciprocal Rank Fusion

- RRF operates on rank positions, not raw scores — this avoids the score-incompatibility problem between BM25 and cosine similarity [claim:agde:047]

```python
def reciprocal_rank_fusion(
    result_lists: list[list[str]],
    k: int = 60,
    top_n: int = 10,
) -> list[tuple[str, float]]:
    """
    Fuse multiple ranked lists via Reciprocal Rank Fusion.

    Args:
        result_lists: Each inner list is a ranked sequence of document IDs,
                      best-first. Lists may come from BM25, dense ANN, etc.
        k: Smoothing constant (default 60, per Cormack et al. 2009).
        top_n: Number of top candidates to return.

    Returns:
        List of (doc_id, rrf_score) tuples, sorted descending by RRF score.
    """
    scores: dict[str, float] = {}
    for ranked_list in result_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]


# Example: fuse BM25 results and dense ANN results
bm25_results  = ["doc_C", "doc_A", "doc_D", "doc_B"]   # BM25 ranking
ann_results   = ["doc_A", "doc_B", "doc_C", "doc_E"]   # Dense ANN ranking

fused = reciprocal_rank_fusion([bm25_results, ann_results], k=60, top_n=3)
# doc_A: 1/(2+60) + 1/(1+60) ≈ 0.0161 + 0.0164 = 0.0325  (top)
# doc_C: 1/(1+60) + 1/(3+60) ≈ 0.0164 + 0.0159 = 0.0323
# doc_B: 1/(4+60) + 1/(2+60) ≈ 0.0156 + 0.0161 = 0.0317
for doc_id, score in fused:
    print(f"{doc_id}: {score:.4f}")
```
<!-- EXEC_TEST -->

<!-- Speaker: Walk through the arithmetic for doc_A: it ranks 2nd in BM25 and 1st in dense, so it accumulates contributions from both lists. The rank-based nature means a document that is 1st in one list and absent in another still scores well. -->

<!-- Notes:
This implementation is intentionally minimal to make the algorithm transparent. In a production system the doc_id would be an opaque identifier and the caller would perform a single metadata lookup to retrieve chunk text and metadata for the top-n candidates before passing them to the reranker.

The worked arithmetic in the comments is pedagogically important: students can verify by hand that doc_A, which appears in both lists (ranked 2nd and 1st), outscores doc_C (ranked 1st and 3rd) because both contributions matter. This concretizes why RRF rewards documents that appear across multiple retrievers.

The k=60 constant deserves a brief mention: it prevents a document ranked 1st from receiving a score of 1.0 (which would dominate), and it also means the difference between rank 1 and rank 2 is smaller than it would be with k=0. The practical effect is a gentler score distribution that makes the fused ranking more stable.

Note that this function accepts an arbitrary number of ranked lists — extending to three or more retrievers (e.g., adding a keyword title-field search) requires no changes to the algorithm.
-->

---

## How Hybrid Retrieval Improves Recall

- Hybrid retrieval (BM25 + dense ANN fused via RRF) improves recall because each retriever surfaces relevant documents the other misses [claim:agde:048]
- Measured Recall@5: dense-only 0.587, BM25-only 0.644, hybrid RRF 0.695, hybrid RRF + neural reranker 0.816 [claim:agde:048]
- The hybrid recall gain is attributable to BM25 pulling in relevant documents the dense retriever ranked too low — not to reranking, which cannot improve recall [claim:agde:048]

<!-- Speaker: Present the numbers as evidence for the architectural decision. Emphasize the last bullet: reranking does not contribute to recall — that is the job of stage 1. This sets up the next slide. -->

<!-- Notes:
These Recall@5 numbers are drawn from a study comparing retrieval strategies in a two-stage RAG pipeline. The progression is instructive: moving from dense-only (0.587) to BM25 (0.644) shows BM25 is competitive; moving to hybrid RRF (0.695) shows synergy; adding the reranker (0.816) shows large precision improvement, but the key point is that the reranker's gain is precision-improving, not recall-improving — the recall ceiling was already set at 0.695 by stage 1.

The decomposition matters for debugging: if a system has poor end-to-end answer quality, the first diagnostic question is whether the answer is in the stage-1 retrieved set at all. If not, the problem is stage-1 recall, and adding a better reranker will not help. If the answer is in the stage-1 set but not in the LLM's context window, the problem is the k cutoff passed to the reranker.

A common misconception is that a powerful reranker can compensate for weak retrieval. This slide directly refutes that: the reranker cannot recover a document it never saw.
-->

---

## Cross-Encoder Reranking — What It Can and Cannot Do

- A cross-encoder jointly encodes the query and each candidate passage through a shared transformer to produce a finer-grained relevance score — improving precision within the retrieved set [claim:agde:049]
- Reranking operates only on the candidate set already retrieved by stage 1: any relevant document not retrieved is permanently lost to the reranker [claim:agde:049]
- The recall ceiling is set entirely by stage 1; a reranker cannot raise it [claim:agde:049]

<!-- Speaker: Contrast cross-encoders with bi-encoders (used in dense retrieval): bi-encoders encode query and document independently for speed; cross-encoders encode them jointly for accuracy but are too slow to run over the full corpus. -->

<!-- Notes:
The architectural reason cross-encoders are restricted to stage 2 is computational: a cross-encoder must process (query, document) pairs jointly, so its cost scales linearly with the number of candidates. Running a cross-encoder over a 10M-document corpus per query is infeasible. Instead, stage 1 uses a bi-encoder (or BM25) to reduce the candidate set to 50–200 documents, and the cross-encoder scores only those.

The quality difference between bi-encoders and cross-encoders is significant: cross-encoders can attend to fine-grained interactions between query terms and document terms (e.g., negation, coreference) that bi-encoders cannot capture because the two representations never interact in a bi-encoder.

The recall ceiling concept is critical for students to internalize. In a production RAG system, increasing the cross-encoder's quality has no effect on recall — only on the ordering of already-retrieved documents. The only levers for recall improvement are: (1) improve stage-1 retrieval (better embeddings, hybrid search, higher k), (2) improve chunking so the relevant information is not split across chunk boundaries.

Common student question: "Can we just use the cross-encoder for everything?" Answer: no, due to latency. A cross-encoder scoring 200 candidates takes ~100ms on GPU; scoring 10M candidates would take ~5000 seconds.
-->

---

## The Canonical Failure — Recall Ceiling of the First Stage

- The canonical two-stage RAG failure is that a relevant document was never retrieved by the first-stage bi-encoder at all — no amount of reranking can recover a document the initial retriever failed to surface [claim:agde:050]
- While rerankers improve precision with small reranker K values, scaling to larger K decreases recall precipitously, often dropping beneath the quality of the standalone retriever [claim:agde:050]
- The efficacy of the two-stage pipeline is bounded by the recall ceiling of stage 1; improving that ceiling requires better first-stage retrieval (e.g., hybrid BM25 + dense), not a more powerful reranker [claim:agde:050]

<!-- Speaker: Make the failure concrete: the chunk was there in the corpus, but the bi-encoder never retrieved it — the reranker never saw it and cannot help. Larger reranker K makes this worse, not better. -->

<!-- Notes:
This failure mode is structurally similar to the silent failure problem introduced in Section A: the system continues to produce output without any signal that relevant information was dropped. There is no exception, no null result, no degraded confidence score surfaced to the user — the LLM simply generates an answer from whatever context it received.

The counterintuitive finding from arXiv:2411.11767 is that scaling up the reranker's K (the number of candidates passed to it) does not help and actively hurts: recall drops precipitously at large K values, often falling below the recall of the standalone bi-encoder retriever. This is because rerankers trained on small candidate sets generalize poorly when asked to score many more documents — the signal-to-noise ratio in the candidate set degrades.

The implication for system design is that the correct mitigation for poor recall is to improve stage-1 retrieval quality — for example, switching from dense-only to hybrid BM25 + dense retrieval as shown in the previous slides — rather than increasing the reranker's input window. These two interventions address different problems: stage-1 improvement raises the recall ceiling; reranker tuning improves precision within that ceiling.

A useful framing for students: the reranker is a precision instrument applied to what stage 1 found. If stage 1 missed the relevant document, the reranker has no path to recovery. Diagnosing RAG failures therefore requires checking stage-1 recall first, before investigating reranker behavior.
-->
