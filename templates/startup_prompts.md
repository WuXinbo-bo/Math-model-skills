# Startup Prompt Templates

> Copy the template below into your chat, replace `[placeholders]`, and start immediately.

---

## 1. New Problem Solving (Standard Mode)

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Standard
Sub-questions: [N]

Problem statement:
[Paste the problem text or upload the file]

Additional info (optional):
- Data files: [path]
- References: [path]
- Other requirements: [if any]

Start from S1 and run the full pipeline.
```

---

## 2. New Problem Solving (Fast Mode)

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Fast mode (skip experiment race and multi-round adversarial review)

Problem statement:
[Paste the problem text]

Start from S1 in fast mode.
```

---

## 3. Championship Mode (Deep Review)

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Championship mode (deep review + multi-round iteration + full adversarial)

Problem statement:
[Paste the problem text]

Sub-questions: [N]

Start from S1, run all 13 stages in championship mode.
```

---

## 4. Existing Paper Revision

```
Use Meta-model-skills-max skill to revise my existing math modeling paper.

Revision type: [① General quality improvement / ② Targeted fixes]
Input file: [path to paper, .docx or .md]

Focus areas (optional):
- [① Model derivation / ② Figure narrative / ③ Abstract rewrite / ④ Sensitivity analysis / ⑤ Full revision]

Analyze the paper, output revision suggestions, then execute revisions.
```

---

## 5. Audit Only

```
Use Meta-model-skills-max skill to audit my math modeling paper.

Audit mode: [① Full audit / ② Quick check]
Input file: [path to paper]

Run the following checks:
- [ ] Gate threshold validation
- [ ] Abstract-body consistency
- [ ] Adversarial review
- [ ] Figure D-A-C narrative
- [ ] Competition scoring (100-point scale)
- [ ] Cross-subquestion consistency
- [ ] Format compliance

Output the audit report and improvement suggestions.
```

---

## 6. Continue Existing Work

```
Use Meta-model-skills-max skill to continue my previous math modeling work.

Workspace: [workspace path]
Current stage: [last completed stage, e.g., S3]

Check the pipeline status first, then continue from where we left off.
```

---

## 7. Specific Stage Execution

```
Use Meta-model-skills-max skill to execute the following specific stage:

Stage: [① S1 Problem analysis / ② S3 Algorithm selection / ③ S5 Modeling & solving / ④ S8 Paper writing / ⑤ S9 Review & revision]
Input files: [relevant file paths]

Additional requirements for this stage:
[specific instructions]

Execute the stage and output deliverables.
```

---

## 9. Standard Mode -- Full Auto

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Standard-Auto (full auto, no manual intervention)
Sub-questions: [N]

Problem statement:
[Paste the problem text]

Start from S0, run fully automatic through S10.
Auto-rework on gate failures (max 3 times).
Log all decisions to decision_log.json.
```

---

## 10. Fast Mode -- Full Auto

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Fast-Auto (skip race + multi-round review, fully automatic)

Problem statement:
[Paste the problem text]

Start from S0 in fast-auto mode.
```

---

## 11. Championship Mode -- Full Auto

```
Use Meta-model-skills-max skill to solve my math modeling contest problem.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Mode: Championship-Auto (deep review + multi-round auto iteration)

Problem statement:
[Paste the problem text]

Sub-questions: [N]

Start from S0, run all stages in championship-auto mode.
Auto 3-round adversarial review + 3-round abstract refinement.
```

---

## 12. Competition Scoring

```
Use Meta-model-skills-max skill to score my paper with competition-specific rubric.

Contest: [① CUMCM / ② 51MCM / ③ MCM/ICM]
Paper file: [path]

Run competition scoring and output:
- Official dimension scores (Model quality / Problem solving / Paper standards / Verification)
- Total score (0-100)
- Award estimate
- Improvement suggestions
```

---

## Quick Start Reference

| Scenario | Keyword | Template # |
|----------|---------|------------|
| New problem (Standard) | `new + standard` | #1 |
| New problem (Fast) | `new + fast` | #2 |
| New problem (Championship) | `new + championship` | #3 |
| Revise paper | `revise + .docx` | #4 |
| Audit paper | `audit + .md/.docx` | #5 |
| Continue work | `continue + workspace` | #6 |
| Specific stage | `stage + S-number` | #7 |
| Competition scoring | `score + contest type` | #8 |
| New problem (Standard-Auto) | `new + standard + auto` | #9 |
| New problem (Fast-Auto) | `new + fast + auto` | #10 |
| New problem (Championship-Auto) | `new + championship + auto` | #11 |

---

## Usage Tips

1. **First time**: Copy template #1, replace placeholders, paste into chat
2. **Have a draft**: Copy template #4, upload .docx file
3. **Want to check quality**: Copy template #5, select needed checks
4. **Resume after interruption**: Copy template #6, provide workspace path
5. **Not sure which to choose**: Just say `analyze this problem`, the system will enter Friendly Mode
