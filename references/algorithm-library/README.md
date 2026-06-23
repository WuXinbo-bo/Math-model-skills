# Mathematical Modeling Algorithm Library

## Overview

This library contains algorithm documentation commonly used in mathematical modeling contests. It provides reference for modelers, programmers, and writers on algorithm selection, principle introductions, and code implementation.

---

## Algorithm Document Index

### Ten Core Algorithm Categories for Math Modeling

Based on practical experience in math modeling competitions, the following ten categories are essential core methods:

| # | Category | Core Algorithms | Typical Applications |
|---|----------|----------------|---------------------|
| 1 | **Monte Carlo Methods** | Random simulation, statistical experiments | Risk analysis, system simulation, model validation |
| 2 | **Data Fitting & Interpolation** | Parameter estimation, interpolation, data processing | Data preprocessing, trend analysis |
| 3 | **Programming Algorithms** | Linear programming, integer programming, multi-objective programming, quadratic programming | Resource allocation, scheduling optimization |
| 4 | **Graph Theory Algorithms** | Dijkstra, Floyd, Prim, Max Flow, Bipartite Matching | Path planning, network analysis |
| 5 | **Algorithm Design** | Dynamic programming, backtracking, divide & conquer, branch & bound | Complex problem solving |
| 6 | **Non-Classical Optimization** | Simulated Annealing (SA), Neural Networks (NN), Genetic Algorithm (GA) | Global optimization, complex search |
| 7 | **Grid Methods & Exhaustive Search** | Discretization of continuous problems, grid search | Parameter optimization, space search |
| 8 | **Continuous Problem Discretization** | Finite differences, summation integration | Numerical solution of differential equations |
| 9 | **Numerical Analysis** | Numerical approximation, numerical differentiation/integration, nonlinear equation solving | Scientific computing |
| 10 | **Image Processing** | Image display, graphics processing | Visualization, result presentation |

---

### 1. Optimization Algorithms
**File**: `01-optimization-algorithms.md`

Algorithms covered:
- Linear Programming
- Integer Programming
- Dynamic Programming
- Genetic Algorithm (GA)
- Particle Swarm Optimization (PSO)
- Simulated Annealing (SA)
- Ant Colony Optimization (ACO)
- Differential Evolution (DE)
- Tabu Search (TS)
- Grey Wolf Optimizer (GWO)
- Immune Algorithm (IA)
- Whale Optimization Algorithm (WOA)
- Sparrow Search Algorithm (SSA)
- Multi-objective Optimization (MOO)
- Robust Optimization

**Applicable Problem Types**: Resource allocation, path planning, scheduling problems, combinatorial optimization, etc.

---

### 2. Prediction Algorithms
**File**: `02-prediction-algorithms.md`

Algorithms covered:
- Grey Prediction Model (GM)
- Interpolation and Fitting
- Linear Regression
- Neural Networks (NN)
- Support Vector Machine/Regression (SVM/SVR)
- ARIMA Model
- Exponential Smoothing
- Prophet Forecasting Model
- LSTM (Long Short-Term Memory)
- XGBoost/LightGBM Prediction
- Spatiotemporal Prediction Models

**Applicable Problem Types**: Economic forecasting, population prediction, demand forecasting, time series analysis, etc.

---

### 3. Evaluation Algorithms
**File**: `03-evaluation-algorithms.md`

Algorithms covered:
- Analytic Hierarchy Process (AHP)
- Fuzzy-AHP
- Entropy Weight Method (EWM)
- TOPSIS
- Grey Relational Analysis (GRA)
- Rank Sum Ratio (RSR)
- Coefficient of Variation Method (CV)
- Subjective Weighting Methods
- Data Envelopment Analysis (DEA)
- Interval Number Evaluation
- Improved TOPSIS Methods

**Applicable Problem Types**: Plan selection, performance evaluation, quality assessment, risk evaluation, etc.

---

### 4. Graph Theory & Network Analysis
**File**: `04-graph-theory-network-analysis.md`

Algorithms covered:
- Shortest Path (Dijkstra, Bellman-Ford, Floyd-Warshall)
- Minimum Spanning Tree (Prim, Kruskal)
- Network Flow (Max Flow, Min-Cost Max Flow)
- Critical Path Method (CPM)
- Eulerian Path & Hamiltonian Path
- Matching Problems (Hungarian Algorithm)

**Applicable Problem Types**: Transportation, network routing, logistics, project management, etc.

---

### 5. Statistical Analysis & Data Processing
**File**: `05-statistical-analysis-data-processing.md`

Algorithms covered:
- Data Preprocessing (missing value handling, outlier detection, standardization)
- Cluster Analysis (K-Means, Hierarchical Clustering, DBSCAN)
- Hypothesis Testing (t-test, ANOVA, Chi-square test)
- Principal Component Analysis (PCA)
- Factor Analysis (FA)
- Canonical Correlation Analysis (CCA)
- Non-negative Matrix Factorization (NMF)

**Applicable Problem Types**: Data cleaning, pattern recognition, classification/clustering, hypothesis validation, etc.

---

### 6. Comprehensive Algorithms
**File**: `06-comprehensive-algorithms.md`

Algorithms covered:
- Monte Carlo Simulation
- Queuing Theory
- Game Theory
- Cellular Automata
- Markov Chain
- Differential Equation Modeling

**Applicable Problem Types**: Risk analysis, system simulation, decision analysis, complex systems, etc.

---

### 7. Machine Learning Algorithms
**File**: `07-machine-learning-algorithms.md`

Algorithms covered:
- Random Forest
- AdaBoost (Adaptive Boosting)
- Isolation Forest

**Applicable Problem Types**: Classification prediction, regression analysis, anomaly detection, etc.

---

## Each Algorithm Document Contains

### Algorithm Introduction
- Mathematical principles and formula derivations
- Algorithm steps and workflow
- Parameter descriptions

### Applicability
| Problem Type | Typical Problems | Characteristics |
|-------------|-----------------|-----------------|

### Visualization Chart Types
- Algorithm visualization recommendations
- Result presentation chart types

### Key References
| Paper Title | Author | Year | Source |

### Code Implementation Notes
- Python code examples
- Key function implementations
- Usage instructions

### Algorithm Selection Guide
- By problem type
- By data characteristics
- By scale

---

## Usage Recommendations

### For Modelers
1. Quickly locate appropriate algorithm categories based on **problem characteristics**
2. Check the algorithm's **applicability** table to confirm match
3. Reference **key literature** for theoretical support
4. Record selected algorithms and formulas for paper use

### For Programmers
1. Reference **code implementation notes** for coding
2. Plot results using recommended **visualization chart types**
3. Pay attention to parameter settings and boundary condition handling

### For Writers
1. Use **mathematical formulas** from the documents to describe models
2. Reference **key literature** for writing references
3. Explain **algorithm selection rationale** (use the applicability section)
4. Present results combining **visualization charts**

---

## Algorithm Quick Index

### Monte Carlo Methods (Essential for Competitions)

Monte Carlo methods are **almost essential** in math modeling competitions:
- Solve problems through computer simulation
- Validate model correctness through simulation
- Realistically describe system characteristics and physical processes
- Solve problems difficult for numerical methods

**Typical Applications**:
- Risk analysis and uncertainty assessment
- Complex system simulation
- Model correctness validation
- Stochastic problem solving

### By Problem Type

| Problem Type | Recommended Algorithm | Document |
|-------------|----------------------|----------|
| Resource allocation | Linear programming, Integer programming | 01-Optimization |
| Path planning | Shortest path, TSP | 01-Optimization, 04-Graph Theory |
| Plan selection | AHP, TOPSIS, Entropy Weight, DEA | 03-Evaluation |
| Time prediction | Grey prediction, ARIMA, Prophet, LSTM | 02-Prediction |
| Data clustering | K-Means, Hierarchical, DBSCAN | 05-Statistics |
| System simulation | Monte Carlo, Cellular Automata | 06-Comprehensive |
| Risk assessment | Monte Carlo, AHP | 01-Optimization, 03-Evaluation, 06-Comprehensive |
| Efficiency evaluation | Data Envelopment Analysis | 03-Evaluation |
| Anomaly detection | Isolation Forest | 07-Machine Learning |
| ML classification | Random Forest, AdaBoost | 07-Machine Learning |

### By Data Type

| Data Type | Recommended Algorithm | Document |
|-----------|----------------------|----------|
| Small sample (<20) | Grey prediction, interpolation | 02-Prediction |
| With missing values | Missing value processing, clustering | 05-Statistics |
| Network structure | Shortest path, Max flow, MST | 04-Graph Theory |
| Time series | ARIMA, Exponential Smoothing, Prophet, LSTM | 02-Prediction |
| Multi-indicator evaluation | AHP, TOPSIS, Entropy Weight | 03-Evaluation |
| Uncertain data | Interval number evaluation, Fuzzy-AHP | 03-Evaluation |
| Multi-input multi-output | Data Envelopment Analysis | 03-Evaluation |
| Spatiotemporal data | Spatiotemporal prediction models | 02-Prediction |

### By Competition Type

| Competition Type | Common Algorithms | Priority Document |
|----------------|------------------|------------------|
| CUMCM A (Continuous) | Differential equations, Neural networks, Regression, LSTM | 02-Prediction, 06-Comprehensive |
| CUMCM B (Discrete) | Integer programming, Graph theory, Evaluation | 01-Optimization, 03-Evaluation, 04-Graph Theory |
| MCM/ICM | Evaluation, Prediction, Optimization, Simulation | All |
| Graduate MCM | Deep learning, Complex optimization, ML | 01-Optimization, 02-Prediction, 07-ML |

---

## Version Info

- **Created**: 2026
- **Document Language**: English
- **Code Language**: Python
- **Applicable Contests**: CUMCM, MCM/ICM, etc.

---

## Contributions & Updates

Algorithm documents will be continuously updated based on developments in mathematical modeling. For issues or suggestions, please submit an Issue.
