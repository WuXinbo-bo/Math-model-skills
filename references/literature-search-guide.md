# Deep Literature Search Guide

In mathematical modeling competitions, literature search is a key step for model selection and method justification.
This guide defines the deep literature search process that must be executed in the S1 stage.

## Why Literature Search

1. **Methodological support**: Model selection must have academic basis; cannot be fabricated
2. **Avoid reinventing the wheel**: Proven methods already exist; citing them is more efficient than deriving from scratch
3. **Enhance paper persuasiveness**: Citing authoritative references strengthens judges' trust in the method
4. **Discover innovation space**: Understanding existing methods' limitations helps find improvement directions

## Three-Step Literature Search Method

### Step 1: Keyword Extraction

Extract core keywords from the problem description, including:
- **Problem type words**: optimization, prediction, evaluation, classification, clustering, fitting, simulation
- **Domain words**: transportation, environment, economy, biology, finance, energy
- **Method words**: linear programming, genetic algorithm, neural network, Monte Carlo, differential equation
- **Constraint words**: multi-objective, dynamic, uncertain, robust

Example: Urban traffic congestion problem:
- Problem type words: traffic flow, congestion, route planning
- Domain words: urban transportation, intelligent transportation systems
- Method words: network flow, queuing theory, graph theory, shortest path
- Constraint words: multi-objective, dynamic, real-time

### Step 2: Search Strategy

#### Search Sources (by priority)
1. **Google Scholar** (scholar.google.com) -- most comprehensive academic search engine
2. **CNKI / Wanfang** -- Chinese literature, national contest papers
3. **IEEE Xplore / arXiv** -- engineering and computer science domains
4. **Award-winning modeling paper collections** -- high-scoring papers for similar problems

#### Search Tips
- Use English keywords to search international literature
- Use Chinese keywords to search domestic literature and modeling papers
- Use `intitle:` to restrict title search
- Use `author:` to search for specific authors
- Check citation counts, prioritize highly cited papers
- Check reference lists to follow the chain

### Step 3: Literature Filtering and Organization

#### Filtering Criteria
| Dimension | Requirement |
|-----------|------------|
| Relevance | Directly related to the problem, solving similar problems |
| Timeliness | Prioritize literature from the past 5 years |
| Authority | Prioritize high-citation, high-impact-factor journals |
| Reproducibility | Clear method description and experimental results |

#### Output Format
Literature search results must be output to `outputs/literature/literature_review.md`, containing:

```markdown
# Literature Review

## 1. Problem Overview
[Brief description of the core challenge]

## 2. Existing Methods Classification
### 2.1 Method A: [Method Name]
- Representative paper: [Author, Year, Journal]
- Core idea: [1-2 sentences]
- Pros and cons: [brief description]
- Applicable scenario: [match with current problem]

### 2.2 Method B: [Method Name]
...

## 3. Method Comparison Matrix
| Method | Accuracy | Complexity | Reproducibility | Problem Match |
|--------|----------|------------|-----------------|---------------|
| A      | High     | Medium     | Good            | 5 stars       |
| B      | Medium   | Low        | Good            | 3 stars       |

## 4. Recommended Plan
Based on literature analysis, the following modeling route is recommended:
1. Primary model: [Method Name] -- Rationale: [citing literature]
2. Backup model: [Method Name] -- Rationale: [citing literature]

## 5. References
[List all cited references per academic standards]
```

## Literature Search Position in the Pipeline

```
S0 Input Registration
    |
S1 Problem Analysis
    +-- Planner: Problem analysis + Literature search
    +-- Analyst: Data availability analysis
    +-- Reviewer: Review + risk identification
    |
S2 Data Governance
    |
S3 Model Selection and Debate
    (At this point, literature support is available, making debate more grounded)
```

## Common Problem Types and Recommended Search Directions

### Optimization Problems
- Linear programming, integer programming, dynamic programming
- Multi-objective optimization: NSGA-II, MOEA/D
- Intelligent optimization: genetic algorithm, particle swarm, simulated annealing

### Prediction Problems
- Time series: ARIMA, LSTM, Prophet
- Regression analysis: multiple regression, ridge regression, random forest
- Grey prediction: GM(1,1)

### Evaluation Problems
- Analytic Hierarchy Process (AHP)
- TOPSIS
- Fuzzy Comprehensive Evaluation
- Data Envelopment Analysis (DEA)

### Classification/Clustering Problems
- K-means, DBSCAN
- Support Vector Machine (SVM)
- Neural network classification

### Graph Theory/Network Problems
- Shortest path: Dijkstra, Floyd
- Network flow: max flow, min cost flow
- Graph coloring, Traveling Salesman Problem (TSP)

## Notes

1. **Citation standards**: All cited literature must appear in the paper's reference list
2. **Avoid over-reliance**: Literature is reference, not copy; must be adapted to the current problem
3. **Balance depth and breadth**: Deeply understand core methods while also exploring related domains
4. **Record search process**: Retain search keywords and filtering rationale for traceability
