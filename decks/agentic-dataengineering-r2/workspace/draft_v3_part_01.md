## The Silent Failure Problem

- ML systems fail silently: unlike traditional software that raises exceptions or dashboards that display visibly-wrong numbers, a model will continue returning predictions even when input data is incorrect or significantly shifted, producing low-quality outputs without raising any alarm. [claim:agde:001]

<!-- Speaker: Contrast this with a broken dashboard — the business at least knows something is wrong. With a silently degrading model, the damage accumulates invisibly before anyone notices. -->

<!-- Notes:
This slide sets the motivating problem for the entire lecture. The key insight is that the failure modes of ML systems are categorically different from those of traditional software. In a web service, an exception propagates and alerts an on-call engineer; in an ML system, the model simply returns a slightly worse number, and that degradation may take weeks or months to surface in business metrics. This asymmetry is what makes data engineering for ML a distinct discipline: correctness guarantees that would be implicit in software systems must be explicitly engineered into data pipelines. Students familiar with software engineering should appreciate that there is no stack trace for a model that has been trained on leaky features — only a slowly declining precision curve that is easy to miss.
-->

---

## The AI Hierarchy of Needs

- Monica Rogati's 'AI Hierarchy of Needs' (2017) frames AI as the top of a pyramid: before deploying ML, organizations must first have data literacy, collection, and infrastructure in place, just as Maslow's hierarchy requires food and shelter before self-actualization. [claim:agde:003]
- According to the CrowdFlower 2016 Data Science Survey, 80% of data scientists' work consists of data preparation: 60% of respondents spent most of their time cleaning and organizing data, and 19% spent most of their time collecting data sets. [claim:agde:004]

<!-- Speaker: The pyramid is not a metaphor — it is a budget allocation. The 80% figure from the survey makes that concrete: if your data infrastructure is broken, no amount of model sophistication will help. -->

<!-- Notes:
Monica Rogati's hierarchy of needs (published on HackerNoon in 2017) is a foundational framing for this course. The pyramid has five layers from bottom to top: data collection, data storage/flow, exploration/transformation, aggregates/features/labels, and finally AI/deep learning at the apex. The CrowdFlower statistic from 2016 remains widely cited and reinforces the same point: the bottleneck in AI projects is almost never the algorithm — it is the data pipeline underneath. For a graduate audience, it is worth noting that this survey predates the LLM era, yet the pattern persists: even organizations using GPT-4-class models spend the majority of their engineering effort on chunking, cleaning, deduplication, and feature preparation rather than on model selection. The pyramid also provides a natural structure for this lecture: sections A through E address the bottom four layers of the pyramid, and sections F through J address the transition to AI applications at the top.
-->

---

## BI vs. ML — A Different Contract on the Pipeline

- ML systems fail silently: unlike traditional software that raises exceptions or dashboards that display visibly-wrong numbers, a model will continue returning predictions even when input data is incorrect or significantly shifted, producing low-quality outputs without raising any alarm. [claim:agde:001]
- ML treats datasets as versioned, time-aware artifacts — immutable snapshots tied to a specific point in time — rather than as query targets, because ML reproducibility requires knowing exactly what data state produced a given model or index, a requirement absent in BI where the latest snapshot is always the correct answer. [claim:agde:005]

<!-- Speaker: BI asks "what is true now?"; ML asks "what was true when this label was created?" That question demands versioned, time-aware artifacts rather than a live query target. -->

<!-- Notes:
This slide draws the sharpest contrast between BI and ML data contracts. In a BI context, overwriting a dimension table with updated values is correct behavior — the dashboard should always reflect current state. In an ML context, that same overwrite is a data integrity violation: the features used to train the model no longer exist, so the experiment is not reproducible, and any point-in-time join performed after the update will silently pull in future state. Students who have worked in analytics engineering should be pushed to confront this directly: the tooling, patterns, and intuitions they bring from BI (e.g., SCD Type 1 overwrites, full table refreshes) are actively harmful in ML pipelines unless accompanied by explicit versioning discipline. The two bullets together set up both the silent failure framing and the reproducibility requirement that structures sections C and D of the lecture.
-->

---

## Data as a Versioned, Time-Aware Artifact

- ML treats datasets as versioned, time-aware artifacts — immutable snapshots tied to a specific point in time — rather than as query targets, because ML reproducibility requires knowing exactly what data state produced a given model or index, a requirement absent in BI where the latest snapshot is always the correct answer. [claim:agde:005]

<!-- Speaker: Immutability and audit trails for datasets are a first-class engineering requirement, not a nice-to-have. This framing will anchor the reproducibility section later in the lecture. -->

<!-- Notes:
This slide reinforces the versioning discipline introduced in the previous slide, giving it a standalone focus before the lecture dives into concrete mechanisms. The core principle is that every model artifact should be traceable back to a specific data snapshot: training data version → feature transformation version → model artifact. Without this chain, retraining a model is not reproducible — you may get a different model even if the algorithm and hyperparameters are identical, simply because the underlying data has changed. Treating datasets as immutable artifacts is the foundational commitment that makes the rest of the reproducibility machinery (Iceberg snapshots, DVC, lakeFS — covered in Section D) meaningful. A useful analogy for students: in software, pinning a dependency means pinning a content-addressable hash of the library; in ML, pinning a dataset means the same thing — a content-addressable pointer to an exact snapshot, not a mutable table name.
-->

---

## Feature Engineering as a Stateful Pipeline Stage

- Feature engineering is a stateful pipeline stage: transformation functions that normalize or encode features require statistics (means, standard deviations, vocabularies) computed solely on the training set ('fit-time statistics'), which must be stored and then reapplied identically during inference to prevent training-serving skew. [claim:agde:006]

<!-- Speaker: The fit-time statistics — means, vocabularies, quantile boundaries — computed during training must be stored and replayed identically at inference. This is where the state lives, and losing it is a direct path to skew. -->

<!-- Notes:
This slide introduces the concept of statefulness in feature engineering, which is subtle and often misunderstood by students coming from a pure SQL or analytics background. A StandardScaler is not a pure function: it computes μ and σ from the training data during fit(), stores them, and applies them during transform(). If you refit the scaler on new production data, you get different μ and σ, and the normalized values your model sees at inference are now on a different scale from what it was trained on — this is training-serving skew, even if the code paths are otherwise identical. The same pattern applies to one-hot encoders (vocabulary must be fixed at training time), quantile transformers (quantile boundaries must be fixed), and any other stateful transform. The stored statistics are the artifact that must be versioned alongside the model weights — they are part of the model's dependency graph. This sets up the code example on the next slide and the broader discussion of skew in Section B.
-->

---

## Stateful sklearn Pipeline — Fit vs. Transform

- Feature engineering is a stateful pipeline stage: transformation functions require fit-time statistics computed solely on training data, which must be stored and reapplied identically at inference to prevent training-serving skew. [claim:agde:006]

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib

# --- TRAINING TIME ---
X_train = np.array([[1.0, 200.0],
                     [2.0, 400.0],
                     [3.0, 600.0]])
y_train = np.array([0, 0, 1])

pipeline = Pipeline([
    ("scaler", StandardScaler()),   # fit() computes mean & std from X_train
    ("clf",    LogisticRegression()),
])
pipeline.fit(X_train, y_train)

# Inspect stored fit-time statistics
scaler = pipeline.named_steps["scaler"]
print("mean:", scaler.mean_)    # [2.0, 400.0]
print("scale:", scaler.scale_)  # [0.816, 163.3]

# Persist the entire pipeline (scaler state + model weights)
joblib.dump(pipeline, "pipeline.joblib")

# --- INFERENCE TIME (production) ---
pipeline_loaded = joblib.load("pipeline.joblib")

X_prod = np.array([[2.5, 500.0]])

# CORRECT: reuse stored mean/std from training — transform() only, no fit()
prediction = pipeline_loaded.predict(X_prod)
print("prediction:", prediction)

# BUG: calling fit() on production data recomputes mean/std from X_prod
# — the scaler now uses X_prod statistics, not X_train statistics
# — this is training-serving skew
pipeline_loaded.named_steps["scaler"].fit(X_prod)  # DO NOT DO THIS
```
<!-- EXEC_TEST -->

<!-- Speaker: Make concrete that calling fit() on inference data is the canonical stateful-transformation mistake. The pipeline.joblib file carries the mean and std computed on training data — that is the artifact that must travel to production alongside the model weights. -->

<!-- Notes:
This code example is designed to make the abstract concept of stateful transformations tangible. The key pedagogical points to emphasize: (1) joblib.dump serializes not just the LogisticRegression coefficients but also the scaler's mean_ and scale_ attributes — these are the fit-time statistics; (2) at inference time, pipeline_loaded.predict() calls transform() on the scaler using the stored statistics, so the feature scaling is consistent with training; (3) the bug at the bottom — calling scaler.fit() on X_prod — resets the scaler's statistics to those of the production batch, which may have a completely different distribution. The model then receives inputs on a different scale from what it saw during training, producing incorrect predictions with no error raised. Students should understand that the joblib file is not optional infrastructure — it is a core part of the model artifact that must be versioned, tested, and deployed alongside the weights. In a feature store context, this serialized transform state would be stored in the feature view definition and applied consistently by the serving layer.
-->
