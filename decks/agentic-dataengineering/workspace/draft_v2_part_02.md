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

- Temporal leakage occurs when a naive join uses current or future feature values instead of the values available at prediction time, producing over-optimistic offline metrics that do not generalize to production [claim:agentic-de:009]
- In the transactions/customer/labels schema, a join on customer_id without a timestamp constraint attaches post-event attributes (e.g., a credit limit increased after the label was recorded) to training rows, giving the model access to information unavailable at prediction time [claim:agentic-de:010]

```sql
-- WRONG: naive join leaks future customer attributes
SELECT t.txn_id,
       t.amount,
       c.credit_limit,        -- current value, not point-in-time
       c.account_tier,
       l.is_fraud
FROM   transactions  t
JOIN   customers     c ON c.customer_id = t.customer_id
JOIN   labels        l ON l.txn_id      = t.txn_id;
-- If c.credit_limit was updated AFTER l.label_ts,
-- the model trains on a feature it cannot see at serving time.
```

<!-- Speaker: Walk through the SQL example line by line. The join on customer_id has no temporal guard, so the customer row reflects its current state — not the state at the time the label was recorded. Ask students: what happens when the credit_limit column was updated a week after the fraud label? -->

<!-- Notes:
This slide makes temporal leakage concrete using the recurring schema example (transactions, customer dimension, timestamped labels). The naive join is perfectly valid SQL and will execute without errors, which is exactly why temporal leakage is so dangerous — there is no syntactic signal that something is wrong.

The key insight is that the customer dimension table is slowly changing: attributes like credit_limit, account_tier, or address update over time. A plain JOIN ON customer_id always returns the latest row, which may contain values that did not exist when the label event occurred. A model trained on these "future-leaked" features learns correlations that are impossible to exploit at serving time, because at serving time only the current feature values (not future ones) are available. The result is a model that looks great on offline evaluation but underperforms in production — a classic manifestation of training-serving skew.

The fix is a point-in-time join (covered in the next section), which constrains the join to return only feature values that existed at or before the label timestamp.
-->

---

## Skew vs. Drift — Don't Conflate Them

| | **Training-Serving Skew** | **Concept / Distribution Drift** |
|---|---|---|
| **What** | Consistency mismatch between training and serving code paths [claim:agentic-de:011] | Change in the joint probability distribution P(X, Y) over time [claim:agentic-de:012] |
| **When** | Can exist from day one of deployment [claim:agentic-de:011] | Emerges gradually after a model that initially performed well [claim:agentic-de:012] |
| **Root cause** | Engineering bug — divergent pipelines [claim:agentic-de:011] | The world changing — statistical phenomenon [claim:agentic-de:012] |
| **Fix** | Log-and-replay, shared transformation definitions, integration tests | Monitoring (PSI, KL), retraining triggers, adaptive models |

<!-- Speaker: Use the two-column table to drive home the distinction. Skew is something you can fix today with better engineering; drift is something you must continuously monitor for. Students frequently conflate these — press them on the difference. -->

<!-- Notes:
This comparison slide addresses one of the most common student misconceptions: treating skew and drift as synonyms. They are fundamentally different failure modes with different causes and different remedies.

Training-serving skew is a consistency bug. It means the training pipeline and the serving pipeline compute different feature values for the same raw input. This can happen because of different library versions, different data sources, or different code paths. Critically, skew can degrade model quality from the very first prediction in production — it does not require time to manifest.

Concept drift, by contrast, is formally defined as a change in P(X, Y) between two time points. A model that was accurate at deployment gradually becomes less accurate as the real-world relationship between inputs and outputs shifts. The classic example is housing prices before and during COVID-19: the same three-bedroom apartment in San Francisco that cost $2M in 2019 might cost $1.5M in 2020. The model's learned relationship is no longer valid, but this has nothing to do with pipeline engineering.

The remedies differ accordingly: skew is prevented by engineering discipline (shared transformations, log-and-replay as per Rule 29, integration tests that compare training and serving feature vectors); drift is managed by continuous monitoring (tracking distributional statistics like PSI, setting retraining triggers, and in some cases using online learning or adaptive models).
-->
