## Three Drift Types — Schema, Distribution, Concept

- Schema drift, distribution drift (covariate shift), and concept drift are three distinct failure modes: schema drift is a structural change (columns added, removed, or retyped); distribution drift means P(X) changes while P(Y|X) remains the same; concept drift means P(Y|X) changes while P(X) may remain stable [claim:agde:025]
- The joint distribution can be decomposed as P(X,Y) = P(X)·P(Y|X), making the distributional and conditional components independently driftable [claim:agde:026]

<!-- Speaker: Walk through the decomposition — schema drift is visible and breaks pipelines immediately; distribution and concept drift are silent and degrade model quality without any error. The P(X,Y) decomposition is the key framing for understanding why two silent failure modes exist independently. -->

<!-- Notes:
This slide establishes the taxonomy that underpins the rest of Section E. Schema drift is the easiest failure to detect — a missing column causes an immediate pipeline error. Distribution drift (covariate shift) is more insidious: the pipeline keeps running, and every type check passes, but P(X) has shifted from what the model was trained on; however, the trained conditional P(Y|X) still holds, so if you could retrain you would recover.

Concept drift is the hardest: P(Y|X) itself changes, meaning the relationship between features and target has fundamentally altered. No amount of data cleaning helps; the model must be retrained on fresh labels. A common student misconception is conflating distribution drift and concept drift — stress that they are independently driftable components of the joint distribution. Real production incidents often involve both simultaneously, which makes diagnosis harder.
-->

---

## Measuring Distribution Drift — PSI and KL Divergence

- PSI quantifies distributional shift by binning feature values and computing PSI = Σ(Cᵢ − Rᵢ) × ln(Cᵢ/Rᵢ), where Cᵢ and Rᵢ are current and reference bin proportions; rule-of-thumb thresholds are PSI < 0.1 (no significant change), 0.1–0.25 (moderate), > 0.25 (major shift requiring model review) [claim:agde:027]
- KL divergence measures shift as D_KL(P||Q) = Σ P(x) log[P(x)/Q(x)] and is asymmetric; PSI is a symmetric variant equivalent to D_KL(P||Q) + D_KL(Q||P), avoiding the asymmetry problem when reference and sample are interchangeable [claim:agde:028]

<!-- Speaker: Derive PSI from first principles — bin the reference and current distributions, compute the signed deviation weighted by log-ratio. Emphasize that the > 0.25 threshold is a practical engineering convention, not a statistical test. Contrast with KL divergence's asymmetry to motivate why PSI is preferred in production monitoring. -->

<!-- Notes:
PSI originated in credit scoring to monitor scorecard stability and has been widely adopted in ML monitoring because it produces an interpretable scalar per feature. The binning step (typically 10–20 equal-frequency bins on the reference distribution) is where practitioner choices matter: too few bins miss subtle shifts; too many bins produce noisy PSI values.

The asymmetry of KL divergence matters in practice: D_KL(P||Q) penalizes regions where P has mass but Q does not, while D_KL(Q||P) penalizes the reverse. In a monitoring context, P is typically the production sample and Q the training reference, so the two divergences capture different risk profiles. PSI sidesteps this by summing both directions, making it invariant to which distribution is called "reference". Students should understand that both metrics are applied per-feature in practice — an aggregate drift score across all features obscures which features are driving the shift.
-->

---

## What Data Contracts Cannot Catch

- Data contracts and schema validation tools such as Great Expectations enforce structural constraints — column presence, data types, nullability, value ranges — and reliably catch schema drift [claim:agde:029]
- A feature column can remain syntactically valid (correct type, no nulls, values in range) while its statistical distribution shifts substantially from what the model was trained on — structural validation does not detect this [claim:agde:029]

<!-- Speaker: Give a concrete example: an age column constrained to [0, 120] passes every Great Expectations check even if the distribution shifts from a 25–35 year-old population to a 55–75 year-old population. The pipeline is green; the model is silently degraded. This motivates the need for distributional monitors on top of schema contracts. -->

<!-- Notes:
Data contracts are a necessary but not sufficient condition for ML pipeline health. The important nuance is that schema validation was designed for data warehouse correctness — ensuring ETL outputs match a structural specification — not for ML feature health. When teams adopt Great Expectations or similar tools and declare victory on data quality, they have closed only the schema drift loop.

A common real-world scenario: a marketing team changes data collection methodology mid-quarter. Column names, types, and ranges are identical. Every data contract check passes. But the behavioral distribution of users captured by the new methodology is demographically different from the training population. The model's performance degrades over weeks; the data quality dashboard stays green throughout. This is the gap that distributional monitoring (PSI per feature, rolling statistical tests) addresses. Encourage students to treat schema contracts and distributional monitors as two separate, complementary layers.
-->

---

## The Offline-Online Metrics Trap

- A well-documented failure mode in ML deployment is offline metrics improving while online metrics regress or stagnate — offline test sets are static and do not reflect production distribution shifts, user-feedback loops, or latency constraints [claim:agde:030]
- Algorithm rankings on offline benchmarks can reverse in live A/B tests, meaning a model that beats the incumbent offline may underperform it in production [claim:agde:030]

<!-- Speaker: This is not a theoretical warning — it is documented across recommender systems, ranking, and retrieval benchmarks. The reversal of algorithm rankings is the strongest argument for always running an online A/B test before decommissioning a model that "lost" on offline metrics. -->

<!-- Notes:
The offline-online gap is one of the most underappreciated failure modes in applied ML. Teams optimize test-set metrics over multiple iterations, accumulate a large improvement on held-out data, ship the model, and observe a flat or negative A/B test. Several mechanisms produce this gap: (1) the test set has been inadvertently overfit through repeated evaluation; (2) the test set was sampled from a past period and the production distribution has evolved; (3) the new model optimizes a proxy metric that correlates with the target metric offline but diverges online due to feedback loops (e.g., recommendation systems where user behavior adapts to model outputs).

The ranking reversal finding (from arXiv:2011.07931) is particularly important: it is not merely that the magnitude of improvement is overstated, but that the relative ordering of models can flip. This means teams cannot safely use offline benchmarks alone to select which model to deploy. The practical takeaway is: treat offline evaluation as a fast filter to eliminate clearly bad models, and treat online A/B testing as the definitive evaluation gate before any production deployment.
-->

---

## Observability Strategy — Layered Monitoring

- Data contracts (Great Expectations, schema validation) form layer 1 and catch schema drift reliably, but do not detect distributional shift [claim:agde:029]
- Distributional monitors computing PSI per feature form layer 2 and detect covariate shift that passes structural checks; PSI > 0.25 per feature triggers model review [claim:agde:027]
- Online model metrics evaluated via A/B test or shadow mode form layer 3 and are the definitive gate, because offline metrics can improve while online metrics regress [claim:agde:030]

<!-- Speaker: Present this as a pipeline, not a one-shot validation step. Each layer catches failures the previous layer cannot see. Layer 1 fires first and is cheapest; layer 3 fires last and is most authoritative. Budget and team maturity determine how many layers a given pipeline implements, but all three are necessary for ML pipelines in production. -->

<!-- Notes:
The layered framing is important because it clarifies what each monitoring component is responsible for and prevents teams from thinking any single tool covers all failure modes. Layer 1 (schema contracts) runs fast and cheaply at ingest time or in a CI/CD gate — fail fast on structural problems. Layer 2 (distributional monitoring) typically runs on a schedule (daily or per batch) comparing the current feature distribution against a pinned training-time reference; PSI per feature with alerting thresholds is the standard implementation.

Layer 3 (online evaluation) is the hardest to instrument because it requires an experiment infrastructure, delayed label collection, and careful split management. Shadow mode — where the new model runs alongside the production model but its outputs are not served — allows collecting online signals before any user impact. The key insight for students is that these three layers are not alternatives; they address orthogonal failure modes. A mature ML platform implements all three as a monitoring pipeline, with alerts that escalate from layer 1 through layer 3 depending on severity.
-->
