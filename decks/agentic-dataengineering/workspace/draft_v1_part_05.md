## Three Kinds of Drift

- **Schema drift** — a structural change such as a missing column or type mismatch; breaks pipelines visibly [claim:agentic-de:024]
- **Distribution drift** (covariate shift) — P(X) changes while P(Y|X) stays the same; degrades models silently [claim:agentic-de:024]
- **Concept drift** — P(Y|X) changes while P(X) stays the same; degrades models silently [claim:agentic-de:024]

| Drift type | What changes | Detection | Failure mode |
|---|---|---|---|
| Schema | Structure (columns, types) | Contract checks | Visible breakage |
| Distribution | P(X) | Statistical tests (PSI, KS) | Silent degradation |
| Concept | P(Y\|X) | Label monitoring | Silent degradation |

<!-- Speaker: Walk through each drift type with a concrete example — e.g., a renamed column (schema), a shift in transaction amounts after a holiday season (distribution), and a change in what counts as fraud after a policy update (concept). Emphasize that only schema drift is caught by traditional contracts. -->

<!-- Notes:
This slide establishes a critical taxonomy that students must internalize. Schema drift is the only category that traditional data-quality tooling (Great Expectations, dbt tests, Soda) catches reliably because it manifests as a structural violation. Distribution drift and concept drift are far more dangerous precisely because the pipeline continues to run without errors — the model keeps producing predictions, but those predictions quietly become less accurate.

A useful intuition for covariate shift: imagine a fraud model trained on transaction amounts that average $50. If a new merchant onboards with an average transaction of $500, P(X) has shifted but the relationship between features and fraud has not. Concept drift is subtler: the same feature distribution now maps to different labels, as when regulatory changes redefine what constitutes a reportable event. Students often conflate distribution drift and concept drift — stress that the distinction matters because remediation differs: covariate shift may be fixable with reweighting, while concept drift typically requires retraining on fresh labels.
-->

---

## Distributional Validation — PSI and KL Divergence

- PSI quantifies distributional shift between a reference and current feature distribution: PSI(P,Q) = D_KL(P||Q) + D_KL(Q||P) = sum of (p_i - q_i) * ln(p_i / q_i) [claim:agentic-de:025]
- Industry-standard thresholds: PSI < 0.1 = no significant change; 0.1 <= PSI < 0.25 = moderate shift; PSI >= 0.25 = significant shift requiring investigation or retraining [claim:agentic-de:025]
- PSI is preferred over raw KL divergence for production monitoring because PSI is symmetric — swapping baseline p(x) and sample q(x) yields the same value, whereas KL divergence is asymmetric (D_KL(P||Q) != D_KL(Q||P)) [claim:agentic-de:026]

| PSI range | Interpretation | Action |
|---|---|---|
| < 0.1 | Stable | None |
| 0.1 – 0.25 | Moderate shift | Investigate |
| >= 0.25 | Significant shift | Retrain / escalate |

<!-- Speaker: Remind students that PSI is computed by binning the feature into discrete buckets, computing proportions in each bin for both reference and current distributions, and summing the per-bin divergence terms. The symmetry property is what makes PSI practical — you do not need to worry about which distribution is the "reference" vs. the "sample." -->

<!-- Notes:
PSI originates from credit-risk modeling where regulators require evidence that a scorecard's input distribution has not shifted since validation. The formula is equivalent to Jeffreys divergence — the sum of the two directional KL divergences. This symmetry is more than a mathematical nicety: in production monitoring, it is often ambiguous which distribution should be treated as the "true" distribution, and an asymmetric metric would give different alerts depending on that arbitrary choice.

The binning step is a practical concern students should understand. Continuous features are typically discretized into 10-20 equal-frequency bins derived from the training distribution. The choice of binning can affect sensitivity — too few bins miss subtle shifts, too many bins introduce noise. When a bin has zero counts in one distribution, a small smoothing constant (e.g., 0.0001) is added to avoid division by zero in the log term.

The threshold values (0.1 and 0.25) are industry conventions, not mathematically derived cutoffs. Teams should calibrate them to their own domain — a PSI of 0.15 on a critical fraud feature may warrant immediate action, while the same value on a low-importance feature may be acceptable.
-->

---

## When Contracts Are Not Enough

- Data contracts catch structural breaks (missing columns, type mismatches, null violations) but cannot detect silent distributional shift in feature values — a column can pass every schema contract while its distribution shifts enough to invalidate model assumptions [claim:agentic-de:027]
- Detecting distributional drift requires statistical monitoring (PSI, KL divergence, KS test) layered on top of contract enforcement [claim:agentic-de:027]
- Offline metric improvements can fail to translate into online gains — in some cases online metrics regress even as offline metrics improve, because offline datasets are static while production inputs are dynamic and subject to feedback loops [claim:agentic-de:028]
- The offline-online metric gap arises when a model overfits to historical patterns: temporal leakage in offline features, latency regressions invisible to accuracy metrics, and feedback loops where model outputs reshape future training distributions all contribute [claim:agentic-de:029]

<!-- Speaker: Connect this back to the recurring transactions schema — imagine the customer_age column passes its NOT NULL and INT type contracts every day, but the age distribution shifts from a median of 35 to 55 after a marketing campaign targets a new demographic. No contract fires, but the model's assumptions are violated. Then pivot to the offline-online gap as the ultimate consequence of missing these shifts. -->

<!-- Notes:
This slide is the capstone of the data-quality section and ties together two ideas students have seen separately: (1) the limitations of structural validation, and (2) the disconnect between offline and online evaluation.

The first point reinforces that data contracts — as commonly implemented in tools like dbt, Great Expectations, or Soda — are necessary but insufficient for ML pipelines. They excel at catching what amounts to schema drift (the first row of the taxonomy from the previous slide) but are blind to distribution and concept drift. Forward-looking organizations are beginning to embed statistical checks (PSI thresholds, KS tests) directly into their contract definitions, but this practice is not yet mainstream.

The offline-online metric gap is one of the most consequential failure modes in applied ML. The research by Rossetti et al. demonstrates that the ranking of models can change depending on available data, and that offline improvements exhibit diminishing returns online. In practice, this means an A/B test is the only reliable arbiter of model quality — offline metrics are a necessary filter but not a sufficient one. Students should understand that this gap is not a bug in evaluation methodology but an inherent property of deploying models into dynamic environments where feedback loops, distribution shifts, and latency constraints interact in ways that static datasets cannot capture.

A concrete example from fraud detection: offline recall improves because the evaluation set includes confirmed fraud labels that were not available at prediction time (temporal leakage). The model learns to exploit these signals, achieving high offline recall, but in production it must predict before the fraud label exists, and recall drops sharply.
-->