# Meta-model-skills-max -- Multi-Agent Policy

## Project Overview

Math modeling contest skill using functional role-based architecture.
The main agent is the sole LLM and orchestrator.
All reasoning happens inside the agent; Python scripts are pure tooling (file I/O, DOCX, figures, state).

## Subagent Authorization

The main agent is authorized to spawn subagents via inline role-play.
Subagents are temporary inference units that directly write their own output files.
No external agent configuration files are used.

### Parallel Spawn (spawn multiple, wait for all)

| Scenario                         | Agents                              | When                                          |
|----------------------------------|-------------------------------------|-----------------------------------------------|
| M001 Problem Consensus Meeting   | planner + analyst                   | Stage 1: parallel perspective gathering       |
| M002 Model Debate                | proposer (accuracy) + proposer (robust) | Stage 4-5: parallel model proposals        |
| Candidate model scoring          | proposer + builder                  | Stage 4: independent scoring                  |
| Multi-perspective paper review   | critic + reviewer                   | Stage 12: independent review                  |

### Sequential Spawn (spawn one, wait, then next)

| Scenario                         | Agents                              | When                                          |
|----------------------------------|-------------------------------------|-----------------------------------------------|
| M001 review                      | reviewer (after planner+analyst finish) | Stage 1: synthesis review                  |
| M002 decision                    | reviewer (after proposer finish)    | Stage 5: model selection                      |
| M004 Red-Team Review             | critic -> reviewer -> writer        | Stage 12-13: adversarial review chain         |
| Model verify                     | builder -> reviewer                 | Stage 6: code + review                        |

### Do NOT Spawn Subagents For

- Final modeling decision (main agent decides)
- Tasks requiring concurrent edits to the same file
- Vague tasks like "solve the whole problem"
- Any task where the main agent can switch roles sequentially
- Stage transitions and state updates
- Simple file operations

## File Ownership Rules

- Each subagent must be told which files it may read and which it may write
- **Sub-agents directly write their own output files** (no main-agent relay)
- No two subagents should write to the same file concurrently
- Main agent owns: `state/`, cross-subquestion merge files (`unified_framework.md`, `cross_validation_report.md`), `summary.md` aggregation
- Subagent outputs go to agent-specific files (e.g., `planner_view.md`, `analyst_view.md`, `outputs/q{N}/summary.md`)
- Parallel sub-question isolation: each sub-agent writes to `outputs/q{N}/` independently

## Python Scripts as Pure Tooling

All scripts in `scripts/` are invoked via `python scripts/<name>.py <args>`.
They perform file operations, state management, DOCX generation, figure plotting, etc.
**None of them call any LLM API.** All reasoning is done by the main agent.

### Stage Execution Protocol (v4.0)

**CRITICAL**: SKILL.md is a compact routing table. Detailed stage instructions are in `stages/S{N}.md`.

**v4.0 Execution Chain (2026-06-17)**:
- 14-stage DAG dependency: S0->S1->S2->S3->S4->S5->S5.5->S6->S7->S7.5->S8->S9->S9.5->S10
- 32 gate contracts, all implemented in gate_contracts.py
- Fast mode total calls <=20, Standard approx 40-50
- Execution protocol: after each stage completes, must run gate_check; on failure, rework until pass

```bash
# First-time: create workspace directory structure
python scripts/workspace_init.py --contest CUMCM --subquestions 3

# Initialize pipeline (with mode selection; auto-creates workspace if missing)
python scripts/stage_executor.py init --contest CUMCM --subquestions 3 --mode championship

# For each stage transition:
python scripts/stage_executor.py current              # Show current stage
python scripts/stage_executor.py begin S3             # Start stage
# Read stages/S3.md and execute all steps
python scripts/stage_executor.py validate S3          # Verify artifacts
python scripts/stage_executor.py gate_check S3        # Run gate checks (v10.0 with decision log)
python scripts/stage_executor.py complete S3          # Mark complete
python scripts/stage_executor.py rework S3 --reason "..." # Rework if gate failed (v10.0)
python scripts/stage_executor.py checklist            # View progress
```

### Script Reference

| Need                             | Command                                               |
|----------------------------------|-------------------------------------------------------|
| **Workspace initialization**     | `python scripts/workspace_init.py [--check] [--contest CUMCM] [--subquestions N]` |
| **Stage execution**              | `python scripts/stage_executor.py <command>`           |
| State machine                    | `python scripts/pipeline_manager.py <command>`         |
| Meeting minutes                  | `python scripts/meeting_protocol.py --meeting-id <id> --stage-id <stage>` |
| **Subagent scheduling**          | `python scripts/subagent_runner.py <command>`          |
| **Context management**           | `python scripts/context_bridge.py <command>`           |
| **Output validation**            | `python scripts/subagent_watchdog.py <command>`        |
| **Checkpoint/recovery**          | `python scripts/recovery_manager.py <command>`         |
| **Diagram generation**           | `python scripts/diagram_generator.py <command>`        |
| **Figure D-A-C narrative**       | `python scripts/figure_dac_generator.py <command>`     |
| **Paper assembly check**         | `python scripts/paper_assembly_checker.py <paper.md>`  |
| **Publication readiness**        | `python scripts/publication_checker.py check <paper.md> --mode <mode>` |
| DOCX generation                  | `python scripts/build_docx.py draft.md output.docx`   |
| Frozen numbers                   | `python scripts/frozen_numbers.py freeze --data <json>` |
| Math sandbox                     | `python scripts/math_sandbox.py run --code "<code>"`  |
| Metric guardian                  | `python scripts/metric_guardian.py init --subquestion Q1` |
| Experiment race                  | `python scripts/experiment_race.py init --subquestion Q1 --models "a,b,c"` |
| Evidence chain                   | `python scripts/evidence_tracer.py register --subquestion Q1 --evidence-file e.json` |
| Model evolution                  | `python scripts/model_evolver.py`                     |
| Quality gate                     | `python scripts/quality_gate.py`                      |
| Data check                       | `python scripts/check_data.py`                        |
| Figure plotting                  | `python scripts/plot_figures_nature.py`               |
| Final verification               | `python scripts/final_vfy.py --check all`             |

### Diagram Generation & Figure Narrative (v4.0)

**Paper Figure Mechanism (v4.0)**:
- `diagram_generator.py` -- automatic generation of technical roadmaps / model architecture diagrams / algorithm flowcharts (Mermaid->PNG)
- `build_docx.py` -- automatic embedding of code appendices (monospace font, light gray background, grouped by sub-question)
- `figure_dac_generator.py` -- figure D-A-C narrative template generation (batch/single/check)
- `paper_assembly_checker.py` -- paper artifact mapping validation (section-upstream product consistency)

#### Diagram Generator Usage

```bash
# 1. Generate technical roadmap (paper Figure 1, mandatory in S1)
python scripts/diagram_generator.py roadmap --stages S0,S1,S3,S5,S8,S9,S10

# 2. Generate model architecture diagram
python scripts/diagram_generator.py model-arch --type optimization --output model_arch.png

# 3. Generate algorithm flowchart (requires JSON config)
python scripts/diagram_generator.py flowchart --steps algo_steps.json --output algo_flow.png

# 4. Generate data flow diagram
python scripts/diagram_generator.py dataflow --stages "data preprocessing,feature engineering,model training,result output"

# 5. Check dependency tools
python scripts/diagram_generator.py check
```

**Dependencies**: requires `mermaid-cli` (mmdc):
```bash
npm install -g @mermaid-js/mermaid-cli
# Or use Docker: docker pull minlag/mermaid-cli
```

#### Figure D-A-C Narrative Usage

```bash
# 1. Batch generate D-A-C templates for all figures (mandatory before S8 paper writing)
python scripts/figure_dac_generator.py batch

# 2. Generate D-A-C for a single figure (with auto-prompt)
python scripts/figure_dac_generator.py single fig1_technical_roadmap.png

# 3. Generate D-A-C for a single figure (manually fill content)
python scripts/figure_dac_generator.py single fig2_convergence.png \
  --describe "Figure 2 shows the algorithm convergence curve. X-axis: iteration count (1-100), Y-axis: objective function value..." \
  --analyze "The figure shows rapid convergence in the first 20 iterations, with the objective value dropping from 1200 to 850..." \
  --conclude "Therefore, the algorithm exhibits good convergence, meeting real-time solving requirements."

# 4. Check figure D-A-C coverage
python scripts/figure_dac_generator.py check
# Output: Complete: 8 (80%), Incomplete: 2 (20%), Missing: 0 (0%)

# 5. Overwrite existing DAC files
python scripts/figure_dac_generator.py batch --overwrite
```

**Enforced Rules (S8)**:
- Directly writing figure interpretations in the paper is **prohibited**
- Must read from `*_DAC.md` files and transcribe into the paper
- Each figure must have a complete D-A-C structure (Describe -> Analyze -> Conclude)

#### Paper Assembly Checker Usage

```bash
# 1. Check paper artifact mapping (mandatory after S8 paper writing)
python scripts/paper_assembly_checker.py outputs/paper/paper.md --mode standard

# 2. Championship mode (stricter checks)
python scripts/paper_assembly_checker.py outputs/paper/paper.md --mode championship

# 3. Output JSON report
python scripts/paper_assembly_checker.py outputs/paper/paper.md --mode standard --json report.json
```

**Check Content**:
- Each section references the corresponding upstream artifact file
- Artifact files exist and are non-empty
- Section word count meets targets (Championship mode)
- Numbers are in `frozen_numbers.json`
- Referenced figure files exist

**Output Example**:
```
Paper Assembly Check Report - STANDARD Mode
Total sections: 9
  Passed: 6
  Warnings: 2
  Errors: 1

Section              Status     Issues
Problem Restatement   PASS
Problem Analysis      PASS
Model Assumptions     MISSING   Missing required artifact: outputs/model_assumptions.md
...
```

### Publication Readiness Checker (v4.0 S9.5)

**Publication Readiness Check (v4.0)**:
- S9.5 stage: publication readiness check (AI traces + informal expressions + figure-text layout + formatting + academic standards + competition standards)
- P0-level checks: AI cliches >=3, generic connectors >=5, vague quantifiers >=5, first-person in abstract, anonymity violations, placeholders
- P1-level checks: excessive embellishment, colloquial language, figure-text layout, numbering consistency, terminology consistency
- P2-level checks: non-academic abbreviations, three-line tables, section hierarchy, citation format
- Rollback rule: P0 != 0 or P1 > 2 => roll back to S9, max 2 times

```bash
# 1. S9.5 full check (MANDATORY)
python scripts/publication_checker.py check outputs/paper/paper_revised.md --mode standard

# 2. Individual checks
python scripts/publication_checker.py ai-traces outputs/paper/paper_revised.md
python scripts/publication_checker.py informal outputs/paper/paper_revised.md
python scripts/publication_checker.py figure-layout outputs/paper/paper_revised.md
python scripts/publication_checker.py format outputs/paper/paper_revised.md
python scripts/publication_checker.py academic outputs/paper/paper_revised.md
python scripts/publication_checker.py competition outputs/paper/paper_revised.md --mode championship

# 3. Generate report
python scripts/publication_checker.py report outputs/paper/paper_revised.md \
  --mode standard --output outputs/paper/publication_readiness_report.md

# 4. Gate check
python scripts/gate_contracts.py publication-ready --mode standard
```

**Gate Standards**:
- P0 = 0, P1 <= 2, P2 <= 5
- Rollback count <= 2
- Championship: extra 2 cross-review rounds (language perspective + judge perspective)

### Gate Contracts Quick Reference (v4.0)

**v4.0 Gate System**:
- 32 gate contracts covering S0-S10 full pipeline
- P0 gates cannot be skipped (even with --force flag)
- 3 mode-dependent thresholds (Fast/Standard/Championship)
- gate_check automatically logs to `state/decision_log.json`

```bash
# Mode-aware gate checks (fast/standard/championship)
python scripts/gate_contracts.py model-select --mode standard
python scripts/gate_contracts.py innovation --mode championship
python scripts/gate_contracts.py paper-quality --mode standard
python scripts/gate_contracts.py abstract --mode standard
python scripts/gate_contracts.py adversarial --mode standard
python scripts/gate_contracts.py structure --mode standard
python scripts/gate_contracts.py g1 --mode standard

# P1 NEW: 4 new gate checks (injected into stage files, cannot be skipped)
python scripts/gate_contracts.py figure-narrative --mode championship  # S8: D-A-C narrative completeness
python scripts/gate_contracts.py parallel-merge --mode standard        # S5: parallel sub-question merge quality
python scripts/gate_contracts.py paper-evaluation --mode championship  # S8: 5-dimension CUMCM evaluation
python scripts/gate_contracts.py evidence-chain --mode standard        # S7/S10: evidence chain traceability

# Weight-aware thresholds (CUMCM review dimensions)
python scripts/gate_contracts.py weight-thresholds S3_model_selection --mode standard
python scripts/gate_contracts.py weight-thresholds S5_modeling_and_solve --mode championship

# General gate checking
python scripts/gate_contracts.py check G_INNOVATION_ASSESSMENT
python scripts/gate_contracts.py contracts
python scripts/gate_contracts.py thresholds --mode championship
```

### SubagentRunner Quick Reference

The SubagentRunner provides three-level fault tolerance for all subagent spawns:

```
Level 1: spawn subagent -> validate output (via Watchdog)
Level 2: retry with enriched context (max 2 retries)
Level 3: fallback to main agent role-play (BLOCKED for Inspector → human intervention required)
```

**Typical meeting workflow:**
```bash
# 1. Generate all spawn instructions for a meeting
python scripts/subagent_runner.py meeting --meeting-id M001_kickoff --stage-id S1

# 2. Spawn each subagent (read the generated spawn file)
# 3. After each subagent completes, validate:
python scripts/subagent_runner.py validate --agent-id planner --task-json '...'

# 4. If validation fails, retry with enriched context:
python scripts/subagent_runner.py enrich --agent-id planner --task-json '...' --attempt 1

# 5. If all retries fail, fallback to role-play:
# (For inspector: BLOCK instead — role-play fallback is not allowed)
python scripts/subagent_runner.py fallback --agent-id planner --task-json '...'

# 6. Check meeting execution status:
python scripts/subagent_runner.py status --meeting-id M001_kickoff
```

## Integrity Rules

Block delivery if:
- Fabricated data, references, or parameter values
- Paper numbers not traceable to code/data/derivation
- Stale results after code or data changes
- Missing explanation for major assumptions

## Content Length Rule

Hard floor: 12,000 substantive Chinese characters for Chinese contests.
Never pad with generic background or unsupported prose.
