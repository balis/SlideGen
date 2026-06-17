## What Is Training-Serving Skew?

- Training-serving skew is a difference between performance during training and during serving, caused by: (1) divergent data handling in training vs. serving pipelines, (2) data changes between training and serving time, or (3) feedback loops between model and algorithm [claim:agentic-de:007]
- Prevention: log the features used at serving time and replay them during training to verify consistency between the two environments [claim:agentic-de:008]

<!-- Speaker: Define skew precisely using the three causes from Google's Rules of ML. Emphasize that Rule 29's recommended mitigation is a log-and-replay strategy, not merely sharing code — you save the actual feature values computed at serving time and pipe them into training logs. -->

<!-- Notes:
Training-serving skew is one of the most insidious failure modes in production ML because it can silently degrade prediction quality without triggering any operational alarm. The three root causes are worth unpacking: (1) divergent code paths means the training pipeline computes features differently from the serving pipeline — for example, a Python batch job uses a different tokenizer version than the Java serving endpoint; (2) data changes mean the statistical properties of input data shift between training time and serving time; (3) feedback loops arise when the model's own predictions influence the data it later trains on, creating a self-reinforcing cycle.

Google's Rule 29 prescribes a concrete mitigation: save the exact feature vectors computed at serving time into a log, then use those logged features as training inputs. This log-and-replay approach ensures that training sees the same feature values that serving actually produced, making any discrepancy between the two environments immediately detectable. This is stronger than merely "sharing code" because even identical code can produce different outputs if the underlying data or library versions differ between environments.
-->

---

## Temporal Leakage — The Naive Join Trap

- Temporal leakage occurs when a naive join attaches current or future feature values to training rows instead of the values available at prediction time, producing over-optimistic offline metrics that do not generalise [claim:agentic-de:009]
- A point-in-time correct (as-of) join ensures the training set reflects the state of features at the timestamp of each label event, not the current state of the feature table [claim:agentic-de:010]

```sql
-- NAIVE JOIN: leaks future customer attributes (e.g., credit_limit updated after fraud event)
SELECT
    t.transaction_id,
    t.amount,
    c.credit_limit,   -- current value, may post-date the label
    l.is_fraud
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id   -- no temporal predicate
JOIN labels     l ON t.transaction_id = l.transaction_id;

-- POINT-IN-TIME CORRECT: use only customer attributes visible at transaction time
SELECT
    t.transaction_id,
    t.amount,
    c_pit.credit_limit,
    l.is_fraud
FROM transactions t
JOIN labels l ON t.transaction_id = l.transaction_id
JOIN LATERAL (
    SELECT credit_limit
    FROM customer_history ch
    WHERE ch.customer_id = t.customer_id
      AND ch.valid_from <= t.event_timestamp
    ORDER BY ch.valid_from DESC
    LIMIT 1
) AS c_pit ON TRUE;
```
<!-- EXEC_TEST -->

<!-- Speaker: Walk through the naive join first — point out that `JOIN customers ON customer_id` picks up the *current* row, which may have been updated after the label. The LATERAL subquery fixes this by filtering to attributes valid at `event_timestamp`. -->

<!-- Notes:
This slide makes temporal leakage concrete. The fraud-detection schema is easy to reason about: a customer's credit limit raised after a fraudulent transaction would be invisible to the model at inference time (since it hadn't happened yet), yet the naive join silently includes it in training. The model learns a feature it cannot observe in production. The LATERAL subquery pattern is the ANSI SQL way to perform an as-of join — it retrieves the most recent row in `customer_history` whose `valid_from` is on or before the event timestamp. Some databases offer more concise syntax (e.g., `ASOF JOIN` in DuckDB or ClickHouse), but the LATERAL form is portable. Emphasise that over-optimistic offline metrics are a canonical symptom: the model appears to perform well in evaluation but degrades sharply in production. This is a form of training-serving skew caused specifically by temporal boundary violations.
-->

---

## Skew vs. Drift — Don't Conflate Them

| | **Training-Serving Skew** | **Concept / Distribution Drift** |
|---|---|---|
| **What** | A difference in feature value distributions between training and serving data [claim:agentic-de:011] | A change in the joint probability distribution P(X, Y) between two time points — the relationship between inputs and the target evolves over time [claim:agentic-de:012] |
| **Root cause** | Using a different training corpus or a faulty sampling mechanism at data collection time [claim:agentic-de:011] | The statistical properties of the target variable change over time as the world changes [claim:agentic-de:012] |
| **When** | Distribution skew exists when training and serving data distributions diverge — which can occur due to a different training corpus or a faulty sampling mechanism [claim:agentic-de:011] | Concept drift is a temporal phenomenon — the statistical properties of the target variable change over time [claim:agentic-de:012] |
| **Fix** | Engineering: align the training corpus and sampling mechanism with the serving distribution [claim:agentic-de:011] | Monitoring and retraining: detect distributional shift and update the model [claim:agentic-de:012] |

<!-- Speaker: Stress the conceptual boundary: skew is about the *data pipeline* not reflecting reality at serving time; drift is about *reality itself* changing. Both cause performance degradation but require different remedies. -->

<!-- Notes:
Students frequently conflate skew and drift because both manifest as a gap between expected and observed model performance. The critical distinction is causal. Skew is a data engineering failure: the training distribution does not match the serving distribution because of how data was collected or sampled — it is fixable by correcting the pipeline. Drift is a world-change phenomenon: the model was trained on a distribution that was once correct, but the real-world relationship between features and target has since shifted (e.g., consumer behaviour changes, a new product category appears, fraud patterns evolve). Drift requires ongoing monitoring — typically statistical tests comparing incoming serving data to the training distribution — and periodic retraining. The two problems can also co-occur: a pipeline bug introduces skew while the world is also drifting. Teaching students to diagnose each separately is the goal of this slide.
-->
