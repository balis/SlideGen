## What Is Training/Serving Skew?

- Training-serving skew is defined as a difference between model performance during training and performance during serving, caused by discrepancies in data handling, changes in data between training and serving time, or feedback loops between the model and its algorithm [claim:agde:007]
- Google addresses skew mitigation in Rules 29, 31, and 32 of its ML engineering guide, covering code reuse and data consistency between training and serving pipelines [claim:agde:007]
- Skew is a silent killer: the model runs without errors and produces predictions, but those predictions are based on incorrect inputs and accuracy degrades without raising any alarm [claim:agde:002]
- Unlike data drift, which develops gradually after deployment, skew can exist from day one and go unnoticed [claim:agde:002]

<!-- Speaker: Open by contrasting with a broken dashboard — at least that fails visibly. Skew is insidious because the pipeline looks healthy while accuracy erodes from the first prediction onward. -->

<!-- Notes:
Google's Rules of Machine Learning (Rules 29, 31, 32) codifies training-serving skew as one of the most consequential ML production failure modes precisely because it is invisible at the infrastructure layer. A monitoring system that checks for exceptions, null rates, or pipeline DAG health will report green while every prediction is subtly wrong.

The three-root-cause taxonomy from Google is worth unpacking: (1) divergent code paths — training and serving re-implement the same transformation independently; (2) data change — the distribution of inputs shifts between when the model was trained and when it serves, which is distinct from the code-path problem; and (3) feedback loops — the model's own outputs influence future inputs (e.g., a recommendation model whose outputs become training data).

A critical nuance is that skew is not a temporal phenomenon in the way drift is. A model can have skew from the very first inference call, before it has been in production for even a second. This is the distinction between an engineering defect (present at deployment) and a temporal phenomenon (develops over time after deployment). That distinction drives different remediation strategies — you cannot fix skew by retraining on fresher data; you must fix the pipeline code.
-->

---

## Two Root Causes of Skew

- Divergent batch-training vs. online-inference code paths are a primary source of skew: when training and serving pipelines independently re-implement the same feature transformation, small differences in tokenization, string normalization, missing-value defaults, or floating-point rounding compound into a feature gap that silently degrades model performance [claim:agde:008]
- Point-in-time correctness violations are the second root cause: when feature generation, predictions, and label generation occur at different points in time, a naive join that does not constrain feature values to those available at the prediction timestamp incorporates future information, causing models to perform well in training but fail in production [claim:agde:009]

<!-- Speaker: Root cause 1 is a code-divergence problem — two teams, two languages, two implementations of the same logic. Root cause 2 is a time-travel problem — the training set accidentally sees the future. Both are engineering defects, not data problems. -->

<!-- Notes:
Root cause 1 (divergent code paths) is especially common at organizations where training is done in Python/scikit-learn and serving is done in Java or Go. Even when both pipelines are in Python, a training job that uses pandas and a serving endpoint that uses a different library can diverge on edge cases: how NaN is handled, how string whitespace is trimmed, or how categorical encodings are ordered. Google's Rule 32 — "reuse code between your training pipeline and your serving pipeline whenever possible" — is the direct remediation: a shared transformation library with a single code path eliminates this class of bug by construction.

Root cause 2 (point-in-time correctness) is more subtle and often more damaging. Consider a fraud detection model trained on a join of transactions to a customer dimension table. If the join uses the customer's current churn_flag or credit_tier rather than the value that existed at transaction time, the model learns from future information. This produces artificially high offline AUC scores — the model "knows" which customers will later churn — but those signals are absent at inference time, so the deployed model underperforms severely. This is the topic of slide 11.

Students often conflate these two root causes. It helps to separate them clearly: root cause 1 is about which code runs; root cause 2 is about which time window the data covers.
-->

---

## The Temporal Leak (Naive Join)

- A naive equi-join of a transactions table to a customer dimension table and timestamped labels — without constraining customer attributes to those that existed at or before the transaction timestamp — leaks future customer state into training rows, creating overly optimistic offline metrics that collapse at deployment [claim:agde:010]

```sql
-- Schema:
--   transactions(tx_id, customer_id, tx_ts, amount)
--   customer_dim(customer_id, churn_flag, credit_tier, updated_at)
--   labels(tx_id, is_fraud, labeled_at)

-- NAIVE JOIN — leaks future state:
-- customer_dim is joined without a time constraint,
-- so churn_flag and credit_tier reflect their value
-- as of query time, not as of tx_ts.
SELECT
    t.tx_id,
    t.customer_id,
    t.tx_ts,
    t.amount,
    c.churn_flag,      -- value as of NOW, not as of tx_ts
    c.credit_tier,     -- value as of NOW, not as of tx_ts
    l.is_fraud
FROM transactions t
JOIN customer_dim c
    ON t.customer_id = c.customer_id   -- no time constraint!
JOIN labels l
    ON t.tx_id = l.tx_id;
```
<!-- EXEC_TEST -->

<!-- Speaker: Walk through each table column by column. The bug is the JOIN on customer_dim with no WHERE or inequality on updated_at — it pulls the current row from the SCD, not the row that was current when the transaction occurred. -->

<!-- Notes:
This slide makes the temporal leak concrete with a schema students can reason about. The three tables represent a realistic fraud detection setup: transactional events, a slowly-changing dimension (SCD) table for customer attributes, and an external label table.

The critical point is that customer_dim is a slowly-changing dimension — customer attributes like churn_flag and credit_tier are updated over time. A customer who was not churned at the time of a transaction may have churned by the time the training query runs. The naive join attaches the post-churn flag to the pre-churn transaction, giving the model a signal that would not have been available at inference time.

The EXEC_TEST comment is included because this query is valid SQL against the stated schema and should be testable. In a teaching context, it is worth running both the naive version and the corrected point-in-time version (shown in slide 15) side-by-side on a small synthetic dataset to demonstrate the difference in training set distributions.

A common student question: "Doesn't the labels table also cause leakage?" Yes — labeled_at may be days or weeks after tx_ts. The label is correctly associated with the transaction, but any features derived from customer behavior between tx_ts and labeled_at would also constitute leakage. The fix for the label table is the same: time-constrain all dimension lookups to tx_ts, not to labeled_at.
-->

---

## Skew vs. Drift — Do Not Conflate Them

- Training-serving skew and concept/distribution drift are distinct failure modes: skew is a consistency mismatch between two code paths or between feature values used at training vs. serving time, present at the moment of deployment and requiring no time to manifest [claim:agde:011]
- Concept drift is formally defined as P(Y|X) changing while P(X) stays the same — the relationship between features and labels changes because the world changed; covariate shift is P(X) changing while P(Y|X) stays the same [claim:agde:012]
- Both drift types are temporal phenomena occurring after deployment; training-serving skew is an engineering defect present from day one [claim:agde:011]

<!-- Speaker: Stress that mixing these two up leads to wrong remediation: you cannot fix skew by retraining on fresher data, and you cannot fix drift by unifying your code paths. They require different interventions. -->

<!-- Notes:
This distinction is one of the most frequently confused concepts in ML operations. The decomposition P(X,Y) = P(X) · P(Y|X) is the formal basis for distinguishing the two drift types: covariate shift affects P(X) (the marginal input distribution), while concept drift affects P(Y|X) (the conditional relationship between inputs and outputs).

Training-serving skew sits in a different category entirely — it is not a statistical phenomenon at all. It is an engineering defect: the model was trained on feature vector f(x) but served on feature vector g(x) where f ≠ g. This could be because the code paths implement f and g differently, or because the training data used future-state values that are not available at inference time. Either way, the defect is present from the first inference call and does not require any passage of time.

A practical diagnostic heuristic: if you see model degradation shortly after deployment (within the first hours or days), suspect skew. If you see degradation months after a healthy deployment period, suspect drift. The remediation is different: skew requires fixing the pipeline (code audit, shared transformation library, point-in-time joins); drift requires monitoring, retraining triggers, and possibly a feedback mechanism to collect new labels.

Chip Huyen's blog post on data distribution shifts is an excellent reference to assign here — it provides the formal definitions alongside real-world examples and monitoring strategies.
-->

---

## Section Checkpoint — Skew Diagnosis Heuristic

- Training-serving skew is defined as a difference between model performance during training and performance during serving, caused by discrepancies in data handling, changes in data between training and serving time, or feedback loops between the model and its algorithm [claim:agde:007]
- Skew can exist from day one and go unnoticed, because the model continues producing predictions without raising errors even when feature inputs are systematically wrong [claim:agde:002]
- Diagnostic heuristic: freeze the training code and replay training data through the serving pipeline — if the resulting feature vectors differ from those produced during training, skew exists and must be fixed before retraining will help

<!-- Speaker: Use this as a brief pause point. Pose the diagnostic question aloud and let it sit for a moment — "If I replay training data through the serving pipeline right now, do I get the same features?" If the answer is no, skew is live in production. -->

<!-- Notes:
This checkpoint slide consolidates the two core ideas from Section B before moving into the remediation (Section C, feature stores and point-in-time joins). The diagnostic heuristic is actionable: it gives students a concrete procedure they can apply to their own pipelines.

The heuristic works because it isolates the code-path divergence root cause: if training data replayed through the serving pipeline produces different features, there is a mismatch in transformation logic. If the features match but the model still underperforms, the culprit is likely point-in-time correctness — the training set itself was contaminated with future information, and that contamination is not detectable by replaying data through the serving path alone.

A secondary diagnostic for point-in-time leakage: compute offline AUC/F1 on a hold-out set, then deploy to a shadow environment and compare predictions against those generated offline for the same rows. If shadow predictions diverge from offline predictions for the same feature values, there is serving-side skew. If shadow predictions match offline predictions but real-world performance is poor, the issue is in the training data (likely temporal leakage).

This is a good moment for questions before transitioning to feature stores and point-in-time joins in Section C, which provide the structural solutions to both root causes covered in this section.
-->
