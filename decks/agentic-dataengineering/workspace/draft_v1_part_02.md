## What Is Training-Serving Skew?

- Training-serving skew is a difference between model outputs during training and during serving, caused by divergent code paths for feature engineering or by data changes between training and serving [claim:agentic-de:007]
- Prevention: reuse the same feature-engineering code for both training and serving so that any raw input maps to the same feature vector in both environments [claim:agentic-de:008]
- Google's Rule 29: save the features used at serving time and pipe them into a log for training-time validation [claim:agentic-de:008]

<!-- Speaker: Define skew precisely, then immediately give the core prevention principle. Transition to the next slide by noting that temporal leakage is a specific, insidious form of skew that even shared code paths do not automatically prevent. -->

<!-- Notes:
Training-serving skew is arguably the single most common silent failure mode in production ML. The key insight is that two independently written implementations of the same feature logic will diverge — through rounding, library versions, or missing edge-case handling — even if they are "logically equivalent." Google's Rule 29 operationalises prevention: log the exact feature vectors served to users, then replay those vectors during training. This creates a closed loop where training data is guaranteed to match serving behaviour. Students already familiar with ETL testing can draw an analogy: skew is the ML equivalent of a staging-vs-production data mismatch, except it never raises an error — the model simply produces subtly wrong predictions.
-->

---

## Temporal Leakage — The Naive Join Trap

- Temporal leakage occurs when a naive join attaches current or future feature values to training rows instead of the values available at prediction time, producing over-optimistic offline metrics that do not generalise [claim:agentic-de:009]
- In the transactions/customer/labels schema, a join on `customer_id` without a temporal predicate picks up post-event attribute changes (e.g., a credit-limit increase recorded after a fraud label), leaking future information into the feature vector [claim:agentic-de:010]

```sql
-- BAD: naive join leaks future customer attributes into training rows
SELECT t.txn_id, t.amount, c.credit_limit, l.is_fraud
FROM   transactions  t
JOIN   customer      c ON c.customer_id = t.customer_id   -- no time guard
JOIN   labels        l ON l.txn_id      = t.txn_id;

-- The customer row reflects TODAY's credit_limit, not the value
-- at the time txn_id was recorded. If the limit was raised after
-- the fraud event, the model trains on information it will never
-- have at serving time.
```

<!-- EXEC_TEST -->

<!-- Speaker: Walk through the SQL line by line. Ask students: "Which column is the leak?" (credit_limit). Then preview that the fix — a point-in-time join — comes in the next section. -->

<!-- Notes:
This example uses the recurring transactions/customer/labels schema. The join on customer_id without a timestamp constraint means the query fetches the customer row as it exists now, not as it existed when the transaction occurred. If a customer's credit limit was 5000 at transaction time but was raised to 15000 a week later, the training row will contain 15000 — a value the model could never observe at inference time. The result is a model that looks excellent on offline evaluation (because it effectively has access to the future) but performs poorly once deployed. Students often underestimate how common this bug is; in practice, any slowly changing dimension that lacks an effective-date column is a candidate for temporal leakage. The fix requires either an as-of join or a snapshot table with validity windows.
-->

---

## Skew vs. Drift — Don't Conflate Them

| | **Training-Serving Skew** | **Data / Concept Drift** |
|---|---|---|
| **What** | Mismatch between training and serving code paths | Change in P(X, Y) over time under a deployed model |
| **Root cause** | Engineering bug — divergent feature logic | The world changes — P(X) shifts (covariate) or P(Y\|X) shifts (concept) |
| **Onset** | Can exist from day one of deployment | Emerges gradually (or abruptly) after deployment |
| **Fix** | Unify code paths; log and replay serving features | Monitor distributions; retrain or adapt the model |

- Skew is a consistency bug between two code paths that is fixable by engineering discipline [claim:agentic-de:011]
- Drift is a change in the joint distribution P(X, Y) over time — the underlying relationship between inputs and outputs evolves, requiring monitoring and retraining [claim:agentic-de:012]

<!-- Speaker: Use the comparison table to draw a sharp line. Emphasise that skew can be fully eliminated by engineering, while drift can only be detected and responded to. Ask students which is worse in practice — the answer is skew, because it is entirely preventable yet often invisible. -->

<!-- Notes:
Students frequently conflate skew and drift because both cause degraded model performance after deployment. The distinction matters because the remediation strategies are completely different. Skew is deterministic: given the same raw input, the training pipeline and the serving pipeline produce different feature vectors. This is a bug, and the fix is to share code. Drift is stochastic: even with identical code paths, the real-world distribution shifts — customer behaviour changes seasonally, fraud patterns evolve, economic conditions fluctuate. Concept drift is formally defined as a change in P(X, Y) between two time points. A concrete example: before COVID-19, a three-bedroom apartment in San Francisco cost around $2M; during COVID-19, the same apartment cost $1.5M — the relationship between features (location, size) and target (price) changed. Skew can exist from the moment a model is deployed; drift emerges only after the world changes relative to the training data.
-->