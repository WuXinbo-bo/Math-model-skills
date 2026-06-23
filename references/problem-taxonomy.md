# Mathematical Modeling Contest Problem Taxonomy v4.0

> **Source**: KyrieZhang329/MathModeling-skills problem-classifier + customized for this skill
> **Purpose**: In the problem_analysis stage, map each sub-question to a standard modeling type
> **Principle**: Classify by objective, output, and constraints, not by model name

---

## I. Eight Standard Problem Types

| # | Type | Typical Keywords | Expected Output | Corresponding Model Template |
|---|------|-----------------|----------------|------------------------------|
| 1 | **Evaluation** | assess, rank, compare, score, quality evaluation, risk assessment | Score/rank/grade | model-formulation-guide.md 2.5 |
| 2 | **Prediction** | predict, estimate, infer, trend, future value | Value/trend/interval | model-formulation-guide.md 2.6 |
| 3 | **Optimization** | select, allocate, schedule, route, maximize, minimize, design | Optimal solution/plan | model-formulation-guide.md 2.1 |
| 4 | **Mechanism/Physics** | explain, mechanism, equation, dynamics, causality, physical process | Equation/relation/parameter | model-formulation-guide.md 2.3 + 2.7 |
| 5 | **Classification/Clustering** | group, label, identify, segment, anomaly detection | Category/label/cluster | model-formulation-guide.md 2.4 |
| 6 | **Graph Theory/Network** | node, edge, path, network, flow, connectivity, matching | Path/flow/match | algorithm-library/04 |
| 7 | **Statistics/Regression** | relationship, correlation, influencing factor, significance, distribution | Regression equation/coefficient/p-value | model-formulation-guide.md 2.2 |
| 8 | **Hybrid** | multiple type combination | Decompose by sub-question | Combined use of above templates |

---

## II. Classification Decision Tree

```
What type of output does the problem require?
|
+-- Numerical rank/score/grade -> Evaluation (Type 1)
|   +-- Indicators independent? -> TOPSIS/Entropy Weight
|   +-- Indicators correlated? -> AHP + Fuzzy Comprehensive Evaluation
|
+-- Future value/trend -> Prediction (Type 2)
|   +-- Sufficient data (>=30 points)? -> ARIMA/Time Series
|   +-- Sparse data? -> Grey Prediction GM(1,1)
|
+-- Optimal plan/configuration -> Optimization (Type 3)
|   +-- Linear relationship? -> Linear Programming/Integer Programming
|   +-- Nonlinear? -> Nonlinear Programming / Intelligent Optimization
|
+-- Physical law/dynamic process -> Mechanism/Physics (Type 4)
|   +-- Interference/diffraction? -> Optical interference model (2.7A)
|   +-- Heat/diffusion? -> Heat conduction model (2.7B)
|   +-- Wave/vibration? -> Wave equation model (2.7C)
|   +-- General dynamics? -> Differential equation model (2.3)
|
+-- Category/label -> Classification (Type 5)
|   +-- Linearly separable? -> Logistic Regression / SVM
|   +-- Nonlinear? -> Random Forest / Neural Network
|   +-- Unlabeled? -> Clustering (K-means/DBSCAN)
|
+-- Path/flow/connection -> Graph Theory (Type 6)
|   +-- Shortest path? -> Dijkstra/Floyd
|   +-- Max flow? -> Ford-Fulkerson
|   +-- Matching? -> Hungarian Algorithm
|
+-- Variable relationship/influence -> Statistics/Regression (Type 7)
    +-- Single dependent variable? -> Linear/Nonlinear Regression
    +-- Multiple dependent variables? -> Multiple Regression / Structural Equation
    +-- Distribution characteristics? -> Hypothesis Testing / ANOVA
```

---

## III. Sub-Question Decomposition Principles

1. **Split by output**: Each sub-question produces a different type of output -> different type
2. **Split by variables**: Different sub-questions involve different variable sets -> may require different types
3. **Split by stage**: Previous sub-question's output is the next sub-question's input -> modeling dependency chain

---

## IV. Common Misclassification Traps

| Trap | Example | Correction |
|------|---------|------------|
| Evaluation mistaken for prediction | "Predict which plan is better" | Actually evaluation: indicator data exists, just needs ranking |
| Optimization mistaken for evaluation | "Select the optimal plan" | May have continuous decision variables, requires optimization model |
| Statistics mistaken for mechanism | Using regression to fit physical data | If physical law exists, build mechanism model rather than pure statistics |
| Classification mistaken for clustering | "Divide samples into 3 categories" | If category meaning known -> classification; unknown -> clustering |
| Single type applied globally | Labeling entire problem "optimization" | Decompose by sub-question; Q1 may be evaluation, Q2 optimization, Q3 prediction |

---

## V. Classification Artifact Format

For each sub-question, output:

```json
{
  "subquestion": "Q1",
  "primary_type": "Mechanism/Physics",
  "primary_subtype": "Optical Interference",
  "secondary_type": null,
  "required_output": "Epitaxial layer thickness d (nm)",
  "classification_reason": "The problem requires calculating film thickness based on spectral interference fringes; the core is physical mechanism modeling",
  "candidate_method_families": ["Fabry-Perot interference model", "Two-beam interference model"],
  "unsuitable_methods": ["Pure statistical regression (no physical basis)", "Deep learning (insufficient data)"],
  "data_dependency": "Q1 results used by Q2",
  "risk_flags": ["Refractive index dispersion may affect accuracy", "Multi-beam interference may require correction"]
}
```

---

## VI. Algorithm Selection Mapping

After classification, use `references/problem-algorithm-map.json` to match specific algorithms:

| Problem Type | Primary Algorithm | Backup Algorithm |
|-------------|------------------|------------------|
| Evaluation | TOPSIS, AHP | Entropy Weight, Fuzzy Comprehensive Evaluation |
| Prediction | ARIMA, Grey Prediction | LSTM, Prophet |
| Optimization | Linear Programming, Integer Programming | Genetic Algorithm, Particle Swarm |
| Mechanism | Differential Equations, Physical Formula Derivation | Numerical Simulation |
| Classification | Logistic Regression, SVM | Random Forest, XGBoost |
| Graph Theory | Dijkstra, Floyd | Ford-Fulkerson, Hungarian |
| Statistics | OLS Regression, Hypothesis Testing | Ridge Regression, LASSO |
