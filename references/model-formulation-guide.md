# Mathematical Model Formulation Guide

> **Applicable**: All model establishment sections of mathematical modeling papers. Agents **must** follow this guide in the `model_N_build` and `content_assembly` stages. Non-compliant model formulations will be blocked by `quality_gate.py model_formulation`.

---

## I. General Principles

### 1.1 Four Questions a Model Must Answer

| Question | Requirement | Counterexample (FAIL) |
|----------|-------------|----------------------|
| **What model is this?** | Clearly state the model type: optimization/statistics/DE/classification/prediction/evaluation/graph theory/... | "Established a mathematical model" -- no type specified |
| **What are the variables?** | List each variable: symbol, name, unit, value range | Y = -0.4953 + 0.00126W -- W is not defined |
| **How are formulas derived?** | Each formula requires a derivation process or literature reference | Formula presented directly without any explanation |
| **What are the assumptions?** | List the conditions under which the model is valid | No assumptions mentioned at all |

### 1.2 Symbol Table Standards

Every model must include a symbol description table, formatted as follows:

```
Table X  Model Symbol Description
| Symbol | Meaning | Unit | Type |
|--------|---------|------|------|
| W      | Gestational weeks | weeks | Independent variable |
| B      | Maternal BMI | kg/m^2 | Independent variable |
| Y      | Fetal Y-chromosome concentration | % | Dependent variable |
| beta_0 | Intercept term | - | Parameter to estimate |
```

### 1.3 Formula Numbering Standards

- Each formula independently numbered: (1), (2), (3)...
- In-text citation format: "as shown in Eq. (3)"
- Multi-line formulas use (3a), (3b) or alignment environments

---

## II. Model-Type-Specific Formulation Templates

### 2.1 Optimization Model

**Required Elements**:

```
1. Decision variable definitions
   - List all decision variables, describe physical meaning and units
   - Specify variable types (continuous/integer/0-1)

2. Objective function
   - Write complete mathematical expression
   - Specify optimization direction (min/max)
   - Explain the physical/economic meaning of the objective

3. Constraints
   - Each constraint written as a mathematical expression
   - Explain the real-world meaning of each constraint
   - Distinguish between hard and soft constraints

4. Model type declaration
   - e.g., Linear Programming (LP), Integer Programming (IP),
     Mixed Integer Linear Programming (MILP), Nonlinear Programming (NLP),
     Multi-objective Optimization, etc.
```

**Standard Template**:

```
X.X Model Establishment

[Problem background description, explaining why this is an optimization problem]

Decision variables:
  x_i: [physical meaning of variable], i = 1,2,...,n, [variable type, e.g., continuous/0-1]
  [If multiple variables, list one by one]

Objective function:
  min Z = sum_i c_i x_i + sum_j d_j y_j           (1)
  where: c_i represents [meaning], d_j represents [meaning]
  [Explain the business meaning of each term in the objective function]

Constraints:
  ① [Constraint name]: sum_i a_{ki} x_i >= b_k,  k = 1,...,K     (2)
     Meaning: [business interpretation of the constraint]
  ② [Constraint name]: x_i in {0,1},  i = 1,...,n              (3)
     Meaning: [explanation of variable type]
  ③ [Non-negativity]: x_i >= 0,  i = 1,...,n                  (4)

In summary, establish the following [model type]:
  min Z = sum_i c_i x_i
  s.t.  [list all constraints]
        x_i >= 0

Model assumptions:
  (1) [Assumption 1 and rationale]
  (2) [Assumption 2 and rationale]
```

### 2.2 Statistical/Regression Model

**Required Elements**:

```
1. Dependent and independent variable definitions (including units)
2. Model function form (linear/nonlinear/log/polynomial)
3. Parameter meaning explanation
4. Error term distribution assumption
5. Model selection rationale
```

### 2.3 Differential Equation Model

**Required Elements**:

```
1. State variable definitions (including units)
2. Governing equations (ODE/PDE), physical meaning of each term
3. Parameter definitions (including units and value sources)
4. Initial conditions / boundary conditions
5. Model mechanism explanation (why this equation)
```

### 2.4 Classification/Discrimination Model

**Required Elements**:

```
1. Input features and definitions
2. Output labels and definitions
3. Model function form (discriminant function / probability function)
4. Decision rule
5. Model selection rationale
```

### 2.5 Evaluation Model

**Required Elements**:

```
1. Evaluation indicator system (hierarchical structure)
2. Indicator definitions and quantification methods
3. Weight determination method (subjective/objective/combined)
4. Comprehensive evaluation function
5. Evaluation grade classification
```

### 2.6 Prediction Model

**Required Elements**:

```
1. Prediction target (single-step/multi-step, short-term/long-term)
2. Model type (time series / grey prediction / machine learning)
3. Model order and parameters
4. Prediction formula (explicit)
5. Data preprocessing description
```

### 2.7 Physical Models (Interference/Diffraction/Wave/Heat Conduction/Diffusion)

**Applicable Scenarios**:
- Optical interference and diffraction problems (thin-film interference, Fabry-Perot interference, two-beam interference, grating diffraction)
- Wave propagation problems (acoustic, electromagnetic, elastic waves)
- Heat conduction and diffusion problems (Fourier's law, Fick's law)
- Electromagnetic field problems (Maxwell's equations, electrostatic/magnetostatic fields)
- Mechanical systems (Newtonian mechanics, Lagrangian/Hamiltonian mechanics)
- Fluid mechanics problems (Navier-Stokes equations, Bernoulli's equation)

**Required Elements**:

```
1. Physical quantity definitions
   - List all physical quantities: symbol, name, unit, physical meaning
   - Distinguish known quantities (parameters) from unknown quantities (variables to solve)
   - Mark vector/scalar/tensor type

2. Governing equations / physical laws
   - Write complete governing equations (interference conditions / wave equation / diffusion equation / ...)
   - Note the physical meaning and unit of each term
   - Explain the theoretical source of the equation (Fresnel formula / Snell's law / Airy formula / ...)

3. Parameter definitions and value sources
   - Each parameter: symbol, physical meaning, unit, value, value source
   - Distinguish: known parameters (from literature/manual), unknown parameters (model solution target), assumed parameters

4. Boundary conditions / initial conditions
   - Write complete initial conditions and boundary conditions
   - Explain the physical basis for condition selection

5. Model assumptions and applicable scope
   - List all assumptions, explain their physical reasonableness and limitations
   - Judge whether they match the actual physical scenario
```

### 2.8 Physical Model Derivation Path Requirements

When the model is based on known physical laws, **must** write the complete derivation chain:

```
Example -- Derivation path from physical law to model formula:

Optical interference model:
  Maxwell's equations -> Plane wave solution -> Boundary condition matching ->
  Fresnel formulas (amplitude reflection/transmission coefficients) ->
  Optical path difference (OPD) calculation -> Phase difference calculation ->
  Interference superposition (intensity superposition formula) -> Interference intensity formula ->
  Extrema conditions -> Measurement formula (d = 1/(2*n_e*Delta_nu))

Heat conduction model:
  Fourier's law -> Energy conservation ->
  Heat conduction equation (PDE) -> Separation of variables / Green's function method ->
  Analytical/numerical solution -> Temperature distribution
```

**During derivation process, must**:
- Each step: "From [physical law] we obtain" or "Substituting into [formula] gives"
- Key approximation steps require special explanation: e.g., small-angle approximation sin(theta) ~ theta
- Dimensional analysis: the final formula's dimensionality must be correct

### 2.9 Physical Model Common Errors

| Error | Example | Correction |
|-------|---------|------------|
| Only final formula without derivation | Directly given d=1/(2n_e*Delta_nu) | Write: OPD -> Interference condition -> Wavenumber conversion -> Thickness formula |
| Physical quantity undefined | n, d, theta appear without definition | Each symbol: name/unit/meaning |
| Vague physical law name | "According to optical principles" | Write: "According to Snell's law of refraction" |
| Missing approximation conditions | Directly use 2nd = m*lambda | Note: only valid at normal incidence (cos(theta_t)=1) |
| No dimensional check | Give d = lambda/(2n) | Check: d[nm]=lambda[nm]/(2*dimensionless) OK |
| Parameters without sources | "Let n = 3.5" | Supplement: refractive index of Si in infrared band, from reference [XX] |

---

## VI. Common Errors and Corrections

| Error | Example | Correction |
|-------|---------|------------|
| Variable undefined | "Y = beta_0 + beta_1 X + epsilon" | Supplement: Y is..., X is..., beta_1 represents... |
| Formula without derivation | Directly listing complex formula | Explain derivation steps or cite literature |
| No model type declaration | "Establish a mathematical model as follows" | Change to "Establish a linear programming model" |
| No assumption explanation | Using OLS but not mentioning assumptions | Supplement linearity/independence/normality assumptions |
| Parameters without sources | "Let alpha = 0.3" | Explain: alpha estimated by [method] / taken from [literature] recommended value |
| Optimization model missing constraints | Only objective function | Supplement all constraint conditions |
| Optimization model missing variable ranges | x_i has no domain | Supplement x_i >= 0 or x_i in {0,1} |
| Formula-text disconnect | Formula directly followed by results | Each formula must have text explanation |

---

## VII. Self-Check Checklist

After completing the model establishment section, check item by item:

- [ ] Model type explicitly declared (optimization/statistics/DE/classification/...)
- [ ] All variables defined (symbol, meaning, unit, type)
- [ ] Model formulas completely written (not oral descriptions)
- [ ] Each formula numbered
- [ ] Each term on the right side of each formula explained
- [ ] Formula derivation process explained (or literature reference given)
- [ ] Model assumptions listed (at least 3)
- [ ] Parameter values justified (data estimation/literature/experience)
- [ ] Optimization model: objective function + all constraints
- [ ] Statistical model: dependent variable + independent variables + error assumptions
- [ ] Differential equation model: state variables + governing equations + initial/boundary conditions
- [ ] Classification model: features + labels + decision function + decision rule

---

## VIII. Model Assumption Classification Standards (v4.0 New)

### 8.1 Assumption Classification Dimensions

Each model assumption must be classified along two dimensions:

**Dimension 1: Necessity**
| Type | Definition | Indicator |
|------|------------|-----------|
| **Hard Assumption** | Violation invalidates the model | "If not true, the model breaks" |
| **Soft Assumption (Simplification)** | Violation reduces accuracy but model remains usable | "To simplify computation, approximately..." |

**Dimension 2: Scope**
| Type | Definition | Indicator |
|------|------------|-----------|
| **Global Assumption** | Applies to all sub-questions | "Assume all data is accurate and reliable" |
| **Sub-question Assumption** | Applies only to a specific sub-question | "Q1 assumes normal incidence conditions" |

### 8.2 Assumption Writing Standard Template

```
X.X Model Assumptions

[Global hard assumption]
(1) [Assumption name]: [Assumption content].
    Necessity: Hard -- If not true, [describe consequences].
    Rationale: [Why the assumption is reasonable].

[Global soft assumption]
(2) [Assumption name]: [Assumption content].
    Necessity: Soft -- Relaxing this assumption would [describe impact].
    Rationale: [Why this simplification is acceptable].

[Q1 sub-question assumption]
(3) [Q1-specific assumption name]: [Assumption content].
    Scope: Q1 only.
    Necessity: [Hard/Soft].
    Rationale: [Rationale explanation].
```

### 8.3 Counterexample: Bad vs Good Assumptions

```
BAD:
  Assumption 1: All data is accurate and reliable.
  -> Problem: Too general, no necessity stated, no rationale for why this can be assumed

GOOD:
  Assumption 1: Data accuracy assumption (Global/Soft)
  The problem does not provide independent measurement error information, so recorded values
  are treated as the best available observations. The impact of outliers was verified through
  data auditing and sensitivity analysis (see Section X).
  -> Necessity and scope clarified, alternative provided (sensitivity analysis verification)
```

---

## IX. Model Establishment Expansion Checklist (v5.1 -- Check When Model is Too Thin)

> **Source**: math-modeling-competition-workflow -- When the model establishment section is less than 2,000 words,
> check and expand from the following 6 dimensions. **Do not pad; each expansion must have mathematical substance.**

### 9.1 Six Expansion Dimensions

| Dimension | Specific Operation | Example |
|-----------|--------------------|---------|
| **1. Data-to-Model Mapping** | Explain how raw data is transformed into model input, draw a data flow -> model flow composite diagram | "The original scoring matrix S_{ij} is Z-score standardized to serve as model input X_{ij}" |
| **2. Loss Function & Optimization Objective** | Clearly write the mathematical form of the loss/objective function, explain why this form (not another) | "Reason for choosing MAE over MSE: MSE is overly sensitive to outliers, inconsistent with MAD detection logic" |
| **3. Regularization & Constraints** | Explain the meaning and value basis of regularization terms (L1/L2/Elastic Net) or constraints (hard/soft) | "Avoiding one's own school in the greedy algorithm is a hard constraint; load balancing is a soft constraint (objective term)" |
| **4. Robust Statistical Methods** | If data contains noise, explain the robust methods used: Hampel filter, MAD, Huber loss, quantile regression, residual correction, etc. | "Using MAD(1.4826) instead of standard deviation for outlier detection, because standard deviation is inflated by contaminated data in small samples" |
| **5. Feature Engineering Definitions** | If feature construction is involved, list: lag terms, rolling windows, event indicators, stage labels, etc., with precise definitions | "Rolling window width w=5, covering 2 responses before and after, used to calculate local mean and variance of scores" |
| **6. Algorithm Pseudocode Tables** | Provide structured pseudocode for core algorithms: input, steps, output | "Algorithm A.3: Three-Step Score Adjustment. Input: scoring matrix S, judge set J, answer set P. Output: final score Final_i" |

### 9.2 Expansion Priorities

Expand level by level in the following order; proceed to next level only when current level passes:

```
Level 1: Are variable definitions complete? -> Supplement missing symbols, meanings, units, types
Level 2: Are formulas derived? -> Supplement the derivation chain from principle to formula (at least 2 steps)
Level 3: Is the loss function explained? -> Explain why this function was chosen (compare at least 1 alternative)
Level 4: Are constraints classified? -> Distinguish hard/soft constraints, note real-world meaning for each
Level 5: Is there pseudocode? -> Add structured pseudocode (input/steps/output) for core algorithms
Level 6: Are parameters justified? -> Each parameter noted with source (data estimation / literature / experience / sensitivity analysis)
```

### 9.3 Model Establishment vs Model Solving: Strict Separation

**Model Establishment Section (prohibited content):**
- Numerical results (R^2, MAE, AUC, etc.)
- Verification metrics
- Code implementation details (unless pseudocode-level algorithm description)
- "As shown in Table X" table references (result tables belong to solution section)

**Model Establishment Section (required content):**
- Model type declaration
- All variable symbols / meanings / units / types
- Complete mathematical expressions (objective function + constraints / governing equations + boundary/initial conditions)
- Derivation process or literature basis
- Parameter meaning explanation
- Model assumptions and rationale justification

**Model Solution Section (corresponding to each sub-question):**
- Implementation source and reproducibility path
- Solution steps (described in order)
- Key figures (placed immediately after the results they support)
- Three-part analysis for each figure (Description -> Analysis -> Conclusion)
- Direct answer to the sub-question

### 9.4 Figure Three-Part Rule (Mandatory for Each Figure/Table)

```
Description: What the figure/table shows
Analysis: What patterns/comparisons/trends are observed
Conclusion: What decision or answer follows from this

Counterexample:
  "Figure 3 shows the MAE variation at different L values." -- Only description, no analysis or conclusion

Good Example:
  "Figure 3 shows the MAE trend for L=2 through L=7 (description).
   As L increases, MAE shows a decreasing trend but marginal improvement diminishes,
   with MAE decreasing 12.8% from L=3 to L=4, but only 7.4% from L=6 to L=7 (analysis).
   Considering both cost and accuracy, L=4 is selected as the optimal review count (conclusion)."
```

---

## X. Model Derivation Depth Standards (v5.2)

### 10.1 Four-Level Derivation Depth

| Level | Name | Requirements | Judgment |
|-------|------|--------------|----------|
| **L1** | Formula listing | Formulas only, no explanation | FAIL |
| **L2** | Symbol definition | Formulas + symbol table + one-sentence explanation | MINIMAL |
| **L3** | Derivation expansion | Formulas + derivation steps + text explanation per step | PASS |
| **L4** | Deep derivation | L3 + alternative comparison + selection rationale + parameter sources | EXCELLENT |

**Goal**: Each model reaches at least L3; core model reaches L4.

### 10.2 Derivation Expansion Six-Step Template

Each model must be expanded according to the following structure:

1. **Problem formalization**: Restate in mathematical language: what is known? what is required? what are the constraints?
2. **Modeling approach**: Why choose this type of model? Were alternatives considered? One-sentence summary of the core idea
3. **Variable and parameter definitions**: Symbol table (meaning + unit + type + range), distinguish decision variables / state variables / parameters
4. **Objective function / governing equation derivation**: Starting from first principles, at least 2 derivation steps, each with text explanation
5. **Constraints / boundary conditions**: Each constraint: mathematical expression + real-world meaning + classification (hard/soft) + source
6. **Model assumption justification**: Each assumption: conditions + rationale + violation consequences + relaxation plan

### 10.3 Derivation Depth Self-Check Checklist

After writing each model, self-check item by item:

- [ ] Does it start with what is known / what is required?
- [ ] Does each variable have a symbol + meaning + unit + type?
- [ ] Is each formula accompanied by at least 2 sentences of explanation?
- [ ] Does the objective function have at least 1 step of derivation (not written directly)?
- [ ] Does each constraint have a real-world meaning explanation?
- [ ] Are key parameters sourced?
- [ ] Do model assumptions include "if relaxed, then..." explanations?
- [ ] Is it clear why this model type was chosen?
- [ ] Is the complete model summarized together?
- [ ] Are there logical connectors between derivation steps?

**Failing 5 or more items => model is insufficient, must be rewritten and expanded**
