# Outstanding Thesis Analysis Guide

> This guide directs the Agent to systematically study award-winning papers in `modeling-paper-archives/`,
> extract reusable modeling patterns, writing techniques, and contest strategies, directly serving the current problem.

---

## 1. Analysis Timing

| Stage | Analysis Goal | Paper Type to Read |
|-------|--------------|--------------------|
| S0 Problem Registration | Understand modeling paradigms for similar problems | Award-winning papers of same problem type |
| S1 Literature Search | Supplement methodological academic basis | Method-focused papers |
| S3 Model Selection | Reference excellent papers' model architecture | Award-winning papers of same method type |
| S8 Paper Writing | Learn writing structure and expression style | High-scoring papers from same competition |
| S9 Review & Revision | Compare paper quality gaps | Benchmark papers from same competition |

---

## 2. SMAERT Six-Dimension Analysis Method

For each outstanding paper, perform structured analysis from the following 6 dimensions:

### 2.1 Structure
```markdown
## Paper Structure Analysis
- Total sections: ___
- Section arrangement:
  1. [Section name] -- [word count ratio] -- [core function]
  2. ...
- Abstract word count: ___ (Four elements present: problem/method/results/keywords)
- Logic thread: [one-sentence summary of narrative logic]
- Transition techniques: [how sections connect]
```

### 2.2 Modeling
```markdown
## Modeling Strategy Analysis
- Problem decomposition: [how the main problem is split into sub-questions]
- Model type: [optimization/prediction/evaluation/simulation/...]
- Core assumptions: [list 3-5 key assumptions]
  - Assumption rationale approach: [how assumptions are justified]
- Mathematical expression:
  - Objective function: [formula]
  - Constraints: [formula]
  - Decision variables: [list]
- Model innovation: [improvements over conventional methods]
- First-principles derivation: [whether derivation starts from first principles]
```

### 2.3 Algorithm
```markdown
## Algorithm Implementation Analysis
- Solution algorithm: [algorithm name and type]
- Algorithm selection rationale: [why this algorithm]
- Complexity: [time/space complexity]
- Implementation details: [key implementation techniques]
- Convergence/optimality: [how solution quality is proven]
- Code reproducibility: [pseudocode or detailed steps present?]
```

### 2.4 Experiment
```markdown
## Experiment Design Analysis
- Data source: [dataset description]
- Data preprocessing: [cleaning/standardization/feature engineering]
- Evaluation metrics: [list all metrics with formulas]
- Baseline comparison: [compared with simple methods?]
  - Baseline method: [description]
  - Improvement: [percentage]
- Parameter settings: [key parameters and value basis]
- Experiment groups: [control groups/ablation experiments?]
```

### 2.5 Robustness
```markdown
## Robustness Analysis
- Sensitivity analysis: [which parameters underwent sensitivity analysis]
  - Parameter variation range: [+/-10%/20%/50%]
  - Result stability: [metric variation range]
- Extreme scenario testing: [which extreme cases were tested]
- Error analysis: [error sources and quantification]
- Model limitations: [did authors voluntarily state limitations?]
```

### 2.6 Expression
```markdown
## Paper Expression Analysis
- Figure/table count: [tables __, figures __]
- Figure/table style: [three-line table / Nature style / ...]
- D-A-C narrative: [does each figure have description-analysis-conclusion?]
- Formula standards: [numbering/definition/symbol consistency]
- Language style: [academic rigor / quantitative expression ratio]
- Abstract quality: [four-element score 1-5]
- References: [quantity/quality/timeliness]
```

---

## 3. Quick Analysis Template

When time is limited (e.g., during the contest), use this streamlined version:

```markdown
# Paper Quick Analysis Card

**Paper**: [filename]
**Contest**: [CUMCM/51MCM/MCM_ICM]
**Problem**: [A/B/C/D/E/F]
**Award**: [First Prize/O奖/...]

## 30-Second Read
- Core method: [one sentence]
- Innovation: [one sentence]
- Most worth learning: [one sentence]

## Reusable Patterns
1. [Pattern 1]: [description] -> applicable to [scenario]
2. [Pattern 2]: [description] -> applicable to [scenario]

## Writing Techniques
1. [Technique 1]
2. [Technique 2]

## Relevance to Current Problem
- Methods to borrow: [description]
- Structure to borrow: [description]
- Parts needing adjustment: [description]
```

---

## 4. Analysis Focus by Competition Type

### CUMCM (100-point scale)
| Dimension | Weight | Analysis Focus |
|-----------|--------|----------------|
| Model quality | 55% | Mathematical derivation completeness, assumption reasonableness, solution correctness |
| Problem solving | 25% | Complete answer to all sub-questions, result accuracy |
| Paper standards | 12% | Abstract quality, format compliance, figure clarity |
| Verification | 8% | Sensitivity analysis, error analysis, robustness |

### 51MCM (100-point scale)
| Dimension | Weight | Analysis Focus |
|-----------|--------|----------------|
| Model quality | 50% | Model selection reasonableness, mathematical expression standards |
| Problem solving | 25% | Practical problem-solving effectiveness, result credibility |
| Paper standards | 15% | Paper structure completeness, strict format compliance |
| Verification | 10% | Sufficient robustness and sensitivity checks |

### MCM/ICM (100-point scale)
| Dimension | Weight | Analysis Focus |
|-----------|--------|----------------|
| Modeling | 50% | Model development process, assumption declaration, validation |
| Analysis | 25% | Analysis depth, sensitivity, multi-plan comparison |
| Paper | 15% | Summary sheet quality, organizational structure |
| Robustness | 10% | Strengths/Weaknesses discussion |

---

## 5. Paper Comparison Matrix

When analyzing multiple papers, use this matrix for cross-comparison:

```markdown
| Dimension | Paper A | Paper B | Paper C | Best Practice |
|-----------|---------|---------|---------|---------------|
| Abstract style | | | | |
| Modeling method | | | | |
| Solution algorithm | | | | |
| Figure/table count | | | | |
| Sensitivity analysis | | | | |
| Baseline comparison | | | | |
| Writing quality | | | | |
| Learnings | | | | |
```

---

## 6. Paper-to-Practice Translation Checklist

After analyzing papers, output the following translation content:

```markdown
# Paper Analysis Translation Report

## Directly Reusable
- [ ] Modeling framework: [extracted from paper] -> write to model_spec.md
- [ ] Writing template: [abstract/conclusion template] -> write to paper_template.md
- [ ] Figure style: [figure design pattern] -> write to figure_style.md

## Needs Adaptation
- [ ] Algorithm implementation: [paper algorithm] -> needs modification [specific modification points]
- [ ] Data processing: [paper method] -> needs adaptation to [current data characteristics]

## Cannot Copy Directly
- [ ] [Reason]: [why it cannot be used directly]

## Innovation Inspiration
- [ ] [Innovation inspiration gained from paper]
```

---

## 7. Common Excellent Paper Pattern Library

### 7.1 Abstract Pattern
```
[Problem background 1 sentence] -> [Core method 1 sentence] -> [Key results 2-3 sentences (with values)] -> [Model evaluation 1 sentence]
Keywords: [method name]; [algorithm name]; [core metric]; [application scenario]
```

### 7.2 Model Establishment Pattern
```
Problem analysis -> Assumption declaration (with rationale) -> Symbol description ->
Objective function -> Constraints -> Solution algorithm -> Result analysis
```

### 7.3 Sensitivity Analysis Pattern
```
Select key parameters -> Set variation range (+/-10%/20%/50%) ->
Vary one at a time, record metrics -> Plot sensitivity curves -> Conclusion (robust/sensitive)
```

### 7.4 Model Evaluation Pattern
```
3 advantages (specific, quantified) -> 2 limitations (honest, with improvement directions) ->
Applicable scenarios -> Extension prospects
```

---

## 8. Usage Notes

1. **Don't copy directly**: Learn the approach and express in your own way
2. **Focus on methodology**: Understand "why this approach" not just "what was done"
3. **Cross-validate**: Compare multiple papers to avoid being misled by one
4. **Timeliness**: Prioritize papers from the last 3 years; format specifications may change
5. **Contest match**: Prioritize papers from the same contest type
6. **Problem match**: Prioritize papers of the same problem type (optimization/prediction/evaluation)
