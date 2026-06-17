## Three Kinds of Drift

- **Schema drift** — a structural change such as a missing column or type mismatch; breaks pipelines visibly [claim:agentic-de:024]
- **Distribution drift (covariate shift)** — P(X) changes but P(Y|X) stays the same; degrades models silently [claim:agentic-de:024]
- **Concept drift** — P(Y|X) changes but P(X) stays the same; the learned relationship between inputs and outputs shifts [claim:agentic-de:024]

<!-- Speaker: Walk through each drift type with a concrete example — schema drift is the easy one (a column disappears), distribution drift is subtle (feature values shift), concept drift is the hardest (the world changes). Stress that only schema drift raises visible errors. -->

<!-- Notes:
Students already know data-quality contracts from earlier in the course, so the key
insight here is that contracts catch only the first category. Distribution and concept
drift are silent — no schema rule fires, no pipeline fails, yet model quality erodes.

Covariate shift example: during COVID-19, the distribution of housing features
(location preferences, price ranges) changed dramatically while the underlying
pricing model relationship did not. Concept drift example: the *same* 3-bedroom
apartment in San Francisco dropped from $2M to $1.5M — same inputs, different
correct output. Each type demands a different detection and remediation strategy:
schema drift is caught by contracts, distribution drift by statistical monitors
(next slide), and concept drift by tracking prediction-outcome correlations over time.
-->

---

## Distributional Validation — PSI and KL Divergence

- PSI quantifies distributional shift: PSI(P,Q) = D_KL(P||Q) + D_KL(Q||P) = sum of (p_i - q_i) * ln(p_i / q_i) [claim:agentic-de:025]
- Industry thresholds: PSI < 0.1 no significant change; 0.1 <= PSI < 0.25 minor shift; PSI >= 0.25 major shift [claim:agentic-de:025]
- PSI is preferred over raw KL divergence because PSI is symmetric — swapping baseline p(x) and sample q(x) yields the same value, whereas KL divergence is asymmetric [claim:agentic-de:026]

<!-- Speaker: Show the formula, then focus on the thresholds — these are the numbers teams actually use in production alerting. Emphasize symmetry as the practical reason PSI wins over raw KL. -->

<!-- Notes:
PSI is computed by binning both the reference (training-time) and current
(serving-time) distributions, then summing the per-bin divergence term.
The symmetry property is crucial for production use: with raw KL divergence,
D_KL(P||Q) != D_KL(Q||P), so the alert threshold would depend on which
distribution you designate as reference. PSI eliminates that ambiguity.

The threshold values (0.1 and 0.25) are widely adopted conventions rather than
theoretically derived cutoffs. A PSI below 0.1 means the distributions are
essentially stable. A PSI between 0.1 and 0.25 signals a minor shift that
warrants investigation — perhaps a seasonal pattern or a data-source change.
A PSI at or above 0.25 signals a major shift that likely requires model
retraining or at minimum a root-cause analysis of the upstream data.

Students should note that PSI works best on continuous features after binning;
for categorical features, chi-squared tests or direct proportion comparisons
may be more appropriate.
-->

---

## When Contracts Are Not Enough

- Data contracts catch structural breaks (missing columns, type mismatches, null violations) but cannot detect silent distributional shift in feature values [claim:agentic-de:027]
- Detecting distributional drift requires statistical monitoring (PSI, KL divergence, KS test) layered on top of contract enforcement [claim:agentic-de:027]
- Offline metric improvements show diminishing returns in online performance — the ranking of models can change depending on available offline data, so offline improvements do not reliably predict proportional online gains [claim:agentic-de:028]
- The offline-online metric gap arises when a model overfits to historical patterns and offline datasets that underrepresent edge cases — e.g., temporal leakage in offline features or latency regressions invisible to accuracy metrics [claim:agentic-de:029]

<!-- Speaker: This is the punchline of the quality section — contracts are necessary but insufficient. Connect back to the PSI thresholds from the previous slide as the tool that fills the gap. Then highlight the offline-online disconnect as a concrete failure mode students should watch for. -->

<!-- Notes:
This slide ties together the preceding material. Data contracts, which students
learned about earlier in the course, are excellent at preventing schema-level
breakage. But a feature column can pass every contract while its distribution
shifts enough to invalidate model assumptions. The solution is layered
monitoring: contracts for structure, statistical tests for distribution, and
online metric tracking for concept drift.

The offline-online gap is a subtler problem. Research on recommender systems
shows that improvements in offline metrics lead to diminishing returns in
online performance — not necessarily regression, but smaller and smaller
online gains for each offline improvement. Moreover, the relative ranking of
candidate models can change depending on how much initial offline data is
available, which means offline A/B comparisons may not predict production
winners.

The offline-online metric gap can also stem from offline datasets that
underrepresent edge cases or reflect shifted historical patterns. For
instance, in fraud detection, offline recall can look strong when confirmed
fraud labels are available at evaluation time, but in production the model
must predict before those labels exist. Latency regressions — invisible to
accuracy metrics — can further erode real-world performance.
-->
