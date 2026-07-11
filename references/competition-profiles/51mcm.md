# 51MCM execution profile

- Use the bundled `51mcmthesis` template and start electronic submission from `withoutpreface`.
- Keep the registration number and problem/group fields; remove school, member, email and telephone fields from the submitted paper body.
- The bundled class is derived from the public 2025 `PPKunOfficial/51MCMThesis` implementation and retains its CC BY-NC 4.0 notice.
- Because the official site may change or be unavailable, the team must compare the generated paper against the current-year official Word template and submission notice before final submission.
- Chinese abstract, keywords, references, reproducibility notes and anonymous body are hard gates.

## Bundled project structure

- `51mcmthesis.cls`: page geometry, Chinese heading hierarchy, captions, abstract/keyword environment, theorem and code styles.
- `main.tex`: anonymous electronic-submission entry point with `withoutpreface`.
- `simkai.ttf` and `simsun.ttc`: bundled Chinese fonts used by the class to avoid machine-dependent SimKai/SimSun lookup failures.
- `sections/`: problem restatement, analysis, assumptions, notation, per-question modeling, validation, evaluation, conclusions and appendices.

Compile with XeLaTeX. Do not restore `schoolname`, `membera/memberb/memberc`, `email`, or `phone` commands in the electronic paper.
