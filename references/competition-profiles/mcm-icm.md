# MCM/ICM execution profile

Primary source: COMAP MCM/ICM Rules, Registration and Instructions, published contest page for 2027.

Hard requirements encoded by this profile:

- one English PDF;
- readable type of at least 12 points;
- no student, advisor, school or institution identity anywhere in the solution;
- the Control Number is the only permitted identifying value;
- a Summary Sheet is included at the front;
- the solution is at most 25 pages, including summary, solution, references, contents, notes, appendices, code and problem-specific material;
- when AI tools were used, append `Report on Use of AI Tools` after the 25-page solution; under COMAP AI policy v102025 this disclosure has no page limit and is not counted in the 25-page solution;
- outside sources are cited in the text and bibliography;
- problem selection is one of MCM A/B/C or ICM D/E/F.

COMAP changes its instructions between contests. Before submission, refresh this profile against the live official page and AI-use policy.

## Bundled project structure

- `mcmicm.cls`: Letter paper, 12pt base font, one-inch margins, Control Number/Problem headers, page numbering, equation/table/figure/code support and Summary Sheet environment.
- `main.tex`: complete English submission entry point.
- `sections/`: problem restatement, assumptions/notation, data provenance, baseline and main model, results, validation, recommendations, conclusion, reproducibility and AI disclosure.
- `LastSolutionPage`: LaTeX label placed before the AI report. The gate reads the compiled `.aux` label and applies the 25-page limit to the solution, while allowing the policy-mandated AI report to follow outside that count.

The paper must cite AI tools inline and in the reference list when used, then append the detailed report required by the current COMAP AI policy.
