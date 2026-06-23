# Competition Problem Selection: Six-Dimension Evaluation Framework

> **Source**: math-modeling-competition-workflow
> **When to Use**: At the start of the competition, when selecting among multiple problem options.

---

## I. Six Evaluation Dimensions

| Dimension | Assessment Content |
|-----------|-------------------|
| **1. Math Type** | Optimization / Prediction / Classification / Simulation / Differential Equations / Graph Theory / Statistics / Hybrid |
| **2. Data Availability & Cleaning Risk** | Is data complete? Missing rate? Heavy cleaning needed? |
| **3. Algorithm Complexity & Code Volume** | How much code needed? Existing libraries? Estimated coding time? |
| **4. Evaluation Clarity** | Are there objective evaluation metrics? Or dependent on subjective reasoning? |
| **5. Paper Writing Difficulty** | How many figures/tables? Proof burden? Interpretability requirements? |
| **6. Team Match** | Domain knowledge, programming ability, time constraints — do they match? |

## II. Recommendation Logic

Total = Dimension 1 x 0.15 + Dimension 2 x 0.20 + Dimension 3 x 0.15 + Dimension 4 x 0.20 + Dimension 5 x 0.15 + Dimension 6 x 0.15

Veto: Data dimension = 1 or Team match = 1

## III. Problem Selection Report Template

For each problem, output:

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Math Type | -- | Primary type + hybrid type |
| Data Availability | -- | Data status + cleaning risk |
| Algorithm Complexity | -- | Core algorithm + estimated code volume |
| Evaluation Clarity | -- | Metrics + subjective/objective |
| Writing Difficulty | -- | Figures/tables + proof volume + interpretability |
| Team Match | -- | Knowledge match + programming match + time |
| **Weighted Total** | **--** | |

## IV. Quick Identification of Typical Problem Types

| Problem Features | Possible Type | Recommended Method |
|-----------------|---------------|-------------------|
| Allocation/scheduling/routing | Optimization (LP/IP/NLP) | Gurobi, Genetic Algorithm, Ant Colony |
| Predict future from historical data | Prediction (time-series/regression) | ARIMA, LSTM, XGBoost, Prophet |
| Classification/recognition/diagnosis | Classification | Logistic Regression, SVM, Random Forest, CNN |
| Physical process/propagation/change | Differential Equations | ODE/PDE, SIR, Finite Element, Numerical Solution |
| Evaluation/ranking/scoring | Evaluation/Decision | AHP, TOPSIS, Entropy Weight, Fuzzy Comprehensive Evaluation |
| Network/connection/relationship | Graph Theory/Network | Shortest Path, Max Flow, Community Detection |
| Generation/synthesis/simulation | Simulation | Monte Carlo, Cellular Automata, Agent-Based Simulation |
