# Experiment Design Framework

> **Position**: Pipeline stage `experiment_design`, located after `data_preprocessing` and before `model_N_build`.
> **Purpose**: Before starting modeling, systematically plan the experiment plan for each sub-question, avoiding blind algorithm trial-and-error.

---

## Experiment Design Template

Each sub-question `model_N` must fill out the following experiment design card:

```yaml
model_id: model_1
problem_description: "Brief description of sub-question 1"
depends_on: []  # Dependent model IDs, e.g., ["model_2"] means results of model_2 are needed

## 1. Model Selection Justification
candidate_models:
  - name: "Linear Programming (LP)"
    rationale: "Objective function and constraints are linear; problem scale is moderate"
    complexity: "O(n)"
    pros: ["Fast solution", "Guaranteed global optimum"]
    cons: ["Cannot handle nonlinear relationships"]
  - name: "Genetic Algorithm (GA)"
    rationale: "Comparison method"
    complexity: "O(g.p.n)"
    pros: ["Global search", "No differentiability requirement"]
    cons: ["Slow convergence", "Unstable results"]

selected_model: "Linear Programming (LP)"
selection_reason: "Problem has strong linear characteristics; prioritize interpretable, stable methods"

## 2. Validation Strategy
validation_method: "cross_validation"  # or holdout / bootstrap / sensitivity
metrics:
  - name: "R-squared"
    threshold: 0.7
    interpretation: "Proportion of variance explained by the model"
  - name: "MAE"
    threshold: 0.1
    interpretation: "Mean Absolute Error"
baseline: "Mean prediction"  # Simplest baseline method

## 3. Data Requirements
required_data:
  - variable: "X1"
    description: "Description of independent variable 1"
    source: "Problem attachment / public data / simulated generation"
    expected_range: [0, 100]
  - variable: "Y"
    description: "Description of dependent variable"
    source: "Problem attachment"

## 4. Failure Contingency
if_model_fails:
  primary_fallback: "Try log transformation and re-regress"
  secondary_fallback: "Switch to Random Forest regression"
  give_up_condition: "R-squared < 0.05 and all transformations ineffective"
  honest_report: "Honestly report limited predictive ability; switch to grouping strategy"

## 5. Reproducibility Requirements
reproducibility:
  seed: 42
  environment: "Python 3.11 + scikit-learn 1.3"
  data_version: "v1.0 (original attachment)"
```

---

## Dependency Graph

Model dependencies are declared through the `depends_on` field, forming a DAG:

```
Example DAG:
  model_1 (independent) ---------------+
                                       +--> model_4 (comprehensive model)
  model_2 (independent) --> model_3 ---+
```

Rules:
- `depends_on: []` indicates an independent model, can be built in parallel
- `depends_on: ["model_2"]` indicates must wait for model_2 to complete
- Circular dependencies are not allowed (automatically detected by pipeline_manager)

---

## Score Trajectory Tracking

After each stage completes, record the quality score into the `score_trajectory` array in `pipeline.json`:

```json
{
  "stage": "model_1_verify",
  "timestamp": "2026-05-24 10:30:00",
  "metrics": {
    "R-squared": 0.85,
    "MAE": 0.072,
    "formulation_score": 90,
    "code_quality_score": 85
  },
  "passed": true,
  "reworks": 0
}
```

Purpose: Track quality changes across the full pipeline, identify weak spots.
