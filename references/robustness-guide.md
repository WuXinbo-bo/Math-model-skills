# Model Robustness and Sensitivity Analysis Guide (Enhanced Edition)

> **Applicable Stage**: S6 Model Verification
> **Purpose**: Agents verify the stability and reliability of model conclusions
> **Enhanced Content**: Added Sobol/Morris methods, Python code templates, SALib integration

---

## Core Principle

**Model conclusions must withstand perturbations.** If a conclusion flips with +/-10% parameter variation, the conclusion is unreliable.

---

## I. Mandatory Checks by Model Type

| Model Type | Mandatory Checks | Priority |
|-----------|-----------------|----------|
| Optimization | Baseline + parameter sensitivity + constraint perturbation + extreme scenarios | P0 |
| Prediction | Baseline + parameter sensitivity + error analysis + data perturbation + extreme scenarios | P0 |
| Statistical | Baseline + parameter sensitivity + error analysis + data perturbation | P0 |
| Evaluation | Baseline + weight sensitivity + parameter sensitivity | P0 |
| Classification | Baseline + parameter sensitivity + error analysis + data perturbation | P0 |
| Simulation | Baseline + parameter sensitivity + random stability + extreme scenarios | P0 |
| Mechanism | Baseline + parameter sensitivity + extreme scenarios | P0 |

---

## II. Eight Check Types in Detail + Code

### 2.1 Baseline Comparison

```python
def baseline_comparison(main_model_score, baseline_score):
    """Calculate primary model improvement over baseline"""
    improvement = (main_model_score - baseline_score) / baseline_score * 100
    if improvement < 0:
        print(f"WARNING: Primary model worse than baseline! Improvement: {improvement:.1f}%")
        return False
    elif improvement < 5:
        print(f"WARNING: Only {improvement:.1f}% improvement; consider if complexity is worth it")
    else:
        print(f"OK: {improvement:.1f}% improvement")
    return True
```

**Baseline Selection**:
- Prediction: mean prediction, linear regression
- Optimization: greedy algorithm, random solution
- Classification: majority class classifier
- Evaluation: equal weight average

### 2.2 Parameter Sensitivity

#### Method 1: One-At-A-Time (OAT) Perturbation

```python
import numpy as np
import pandas as pd

def sensitivity_analysis(model_func, params, base_values, perturbations=[-0.5, -0.2, -0.1, 0, 0.1, 0.2, 0.5]):
    """One-factor-at-a-time sensitivity analysis"""
    results = {}
    base_output = model_func(**base_values)
    
    for param in params:
        param_results = []
        for pct in perturbations:
            test_values = base_values.copy()
            test_values[param] = base_values[param] * (1 + pct)
            try:
                output = model_func(**test_values)
                change = (output - base_output) / abs(base_output) * 100 if base_output != 0 else 0
                param_results.append({'perturbation': pct, 'output': output, 'change_pct': change})
            except:
                param_results.append({'perturbation': pct, 'output': None, 'change_pct': None})
        results[param] = pd.DataFrame(param_results)
    
    return results
```

#### Method 2: Sobol Global Sensitivity Analysis (Recommended)

```python
from SALib.sample import saltelli
from SALib.analyze import sobol

def sobol_analysis(model_func, problem):
    """
    problem = {
        'num_vars': 3,
        'names': ['x1', 'x2', 'x3'],
        'bounds': [[0, 20], [0, 10], [0, 15]]
    }
    """
    param_values = saltelli.sample(problem, 1024)
    Y = np.array([model_func(*p) for p in param_values])
    Si = sobol.analyze(problem, Y)
    
    print("First-order sensitivity indices (S1):")
    for i, name in enumerate(problem['names']):
        print(f"  {name}: {Si['S1'][i]:.4f}")
    
    print("Total-order sensitivity indices (ST):")
    for i, name in enumerate(problem['names']):
        print(f"  {name}: {Si['ST'][i]:.4f}")
    
    return Si
```

### 2.3 Weight Sensitivity (Evaluation Models Only)

```python
def weight_sensitivity(model_func, base_weights, n_iterations=100, perturbation=0.2):
    """Perturb evaluation indicator weights, check ranking stability"""
    rankings = []
    for _ in range(n_iterations):
        perturbed = base_weights * (1 + np.random.uniform(-perturbation, perturbation, len(base_weights)))
        perturbed /= perturbed.sum()
        ranking = model_func(perturbed)
        rankings.append(ranking)
    
    from collections import Counter
    rank1_counts = Counter([r[0] for r in rankings])
    print("Frequency of ranking 1st under weight perturbation:")
    for item, count in sorted(rank1_counts.items(), key=lambda x: -x[1]):
        print(f"  Plan {item}: {count/n_iterations*100:.1f}%")
```

### 2.4 Data Perturbation

```python
def data_perturbation_test(model_func, X, y, n_bootstrap=50, noise_level=0.1):
    """Bootstrap + noise perturbation test"""
    results = []
    for i in range(n_bootstrap):
        idx = np.random.choice(len(X), len(X), replace=True)
        X_boot, y_boot = X[idx], y[idx]
        noise = np.random.normal(0, noise_level, X_boot.shape)
        X_noisy = X_boot + noise
        score = model_func(X_noisy, y_boot)
        results.append(score)
    
    print(f"Bootstrap results: {np.mean(results):.4f} +/- {np.std(results):.4f}")
    print(f"95% CI: [{np.percentile(results, 2.5):.4f}, {np.percentile(results, 97.5):.4f}]")
```

### 2.5 Error Analysis

```python
def error_analysis(y_true, y_pred):
    """Residual analysis"""
    residuals = y_true - y_pred
    
    print(f"Residual mean: {np.mean(residuals):.4f}")
    print(f"Residual std: {np.std(residuals):.4f}")
    
    from scipy import stats
    stat, p_value = stats.shapiro(residuals[:500])
    print(f"Normality test p-value: {p_value:.4f} {'PASS' if p_value > 0.05 else 'FAIL'}")
    
    from sklearn.linear_model import LinearRegression
    reg = LinearRegression().fit(y_pred.reshape(-1, 1), residuals**2)
    r2 = reg.score(y_pred.reshape(-1, 1), residuals**2)
    print(f"Heteroscedasticity R-squared: {r2:.4f} {'WARNING' if r2 > 0.1 else 'OK'}")
    
    return residuals
```

### 2.6 Random Stability

```python
def stability_test(model_func, X, y, n_seeds=10):
    """Multi-seed stability test"""
    scores = []
    for seed in range(n_seeds):
        np.random.seed(seed)
        score = model_func(X, y, random_state=seed)
        scores.append(score)
    
    print(f"Mean: {np.mean(scores):.4f}")
    print(f"Std: {np.std(scores):.4f}")
    print(f"CV: {np.std(scores)/np.mean(scores)*100:.2f}%")
    if np.std(scores)/np.mean(scores) < 0.05:
        print("OK: Good random stability")
    else:
        print("WARNING: Insufficient random stability")
```

### 2.7 Extreme Scenarios

```python
def extreme_scenario_test(model_func, base_values, bounds):
    """Test boundary conditions"""
    scenarios = {
        'base': base_values,
        'all_min': {k: bounds[k][0] for k in bounds},
        'all_max': {k: bounds[k][1] for k in bounds},
    }
    
    for param in bounds:
        scenarios[f'{param}_min'] = {**base_values, param: bounds[param][0]}
        scenarios[f'{param}_max'] = {**base_values, param: bounds[param][1]}
    
    results = {}
    for name, values in scenarios.items():
        try:
            results[name] = model_func(**values)
        except Exception as e:
            results[name] = f"ERROR: {e}"
    
    for name, result in results.items():
        print(f"  {name}: {result}")
    return results
```

---

## III. Sensitivity Judgment Standards

| Output Change | Judgment | Action |
|--------------|----------|--------|
| < 10% | Stable | Report normally |
| 10-30% | Moderately sensitive | Discuss in paper |
| > 30% | Highly sensitive / fragile | Must note limiting conditions |

---

## IV. Report Template

Each sub-question generates `robustness/Qx/qx_robustness_report.md`:

```markdown
# Qx Robustness Report

## Supported Conclusions
| Conclusion | Supporting Evidence | Confidence |
|------------|-------------------|------------|

## Fragile Conclusions
| Conclusion | Vulnerability Reason | Limiting Condition |
|------------|--------------------|-------------------|

## Conclusion Boundaries
| Conclusion | Valid Conditions | Possible Failure Conditions |
|------------|-----------------|---------------------------|

## Sensitivity Summary
| Parameter | Perturbation Range | Output Change | Judgment |
|-----------|-------------------|---------------|----------|
```

---

## V. S6 Sensitivity Analysis Figure Selection Guide

**Figure types are determined by research content**, not fixed to one type. Choose the most appropriate figure based on the analysis scenario:

| Analysis Scenario | Preferred Figure | Alternative | Applicable Condition |
|------------------|-----------------|-------------|---------------------|
| Single/multi-parameter comparison | Sensitivity line chart | Area chart | Parameters <= 8 |
| Parameter importance ranking | Tornado plot | Horizontal bar chart | Need ranking by impact |
| Parameter interaction effects | Heatmap | 3D surface plot | Need to show two-parameter interaction |
| Weight sensitivity | Radar chart | Grouped bar chart | Multi-dimension evaluation |
| Multi-model robustness comparison | Forest plot | Box plot | Need to show confidence intervals |
| Data perturbation distribution | Box plot | Violin plot | Bootstrap resampling results |
| Convergence process | Convergence curve | Semi-log curve | Iterative algorithms |
| Global sensitivity | Scatter plot (mu* vs sigma) | Pareto chart | Morris/Sobol analysis |

---

## VI. Constraint Self-Check Report Template

Each sub-question must generate `constraint_verification.md` in S6:

```markdown
# Q{N} Constraint Self-Check Report

## Conservation Verification
| Constraint | Theoretical Value | Actual Value | Error | Judgment |
|------------|------------------|--------------|-------|----------|
| Rod length conservation | 0 m | 6.46E-12 m | 6.46E-12 | PASS |
| Mass conservation | 1.000 kg | 1.000 kg | < 1E-12 | PASS |

## Consistency Verification
| Check Item | Expected | Actual | Judgment |
|------------|----------|--------|----------|
| Unit consistency | Unified throughout | SI units throughout | PASS |
| Symbol consistency | Matches symbol table | Consistent | PASS |

## Boundary Condition Verification
| Boundary Condition | Expected Behavior | Actual Behavior | Judgment |
|-------------------|------------------|----------------|----------|
| As lambda -> 0 | Degrades to unconstrained solution | Consistent with independent optimization | PASS |
| As lambda -> infinity | Solution approaches constraint boundary | Deviation < 0.1% | PASS |

## Sensitivity Summary
| Parameter | Perturbation Range | Output Change | Judgment |
|-----------|-------------------|---------------|----------|
| lambda | +/-50% | +3.2%/-2.8% | Stable |
| mu | +/-50% | +8.1%/-7.5% | Stable |
```

**Judgment Criteria**:
- Error < 1E-8 -> PASS (numerical precision level)
- Error 1E-8 ~ 1E-4 -> WARN (acceptable but needs attention)
- Error > 1E-4 -> FAIL (must investigate)

---

## VII. CLI Integration

```bash
# Generate robustness report
python scripts/sensitivity_analysis.py --question Q1 --model-type prediction

# Check model derivation depth
python scripts/verify_solution.py --depth-check "model description text"

# Generate sensitivity figures
python scripts/sensitivity_analysis.py --question Q2 --plot
```
