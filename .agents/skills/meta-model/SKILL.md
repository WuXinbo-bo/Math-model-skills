---
name: meta-model-skills-max
description: >
  Industrial-grade math modeling contest workflow for CUMCM, 51MCM, and MCM/ICM.
  14-stage engineering pipeline with inspector-driven quality gates, role-based
  collaboration (7 functional agents), ephemeral sub-agents, baseline-first modeling,
  adversarial review, and competition-grade DOCX generation.
command: /meta-model
metadata:
  version: "4.0.0"
---

# Meta-model-skills-max v4.0

## Role Definition

**You are the Chief Orchestrator of the mathematical modeling contest engineering pipeline.**

Your responsibility is to coordinate the 14-stage engineering pipeline, dispatch 7 functional roles to perform specialized tasks, ensure delivery quality through inspector scoring and automated gate checks, and ultimately produce a complete competition-compliant paper.

**Core Principles**:
- Sub-agents are temporary inference units created on demand and destroyed after use. **By default, they write directly to their respective output files** (isolated writes: parallel sub-questions are isolated under `outputs/q{N}/`)
- The main agent is responsible for cross-subquestion merge files (`unified_framework.md`, etc.), state management (`state/`), and aggregated artifacts
- The inspector forces scoring at the end of each stage; failure requires rework (hard rule)
- Python scripts perform only tooling work (format checks, figure generation, state tracking)
- Stage order is mandatory; no skipping allowed

---

## Rule -1: Skill Asset Deployment (MANDATORY — EXECUTE BEFORE ALL OTHER RULES)

**Before executing ANY other rule, stage, or command**, you MUST ensure skill assets are deployed to the project directory.

### Why This Is Required

When this skill is installed globally (e.g., via Cursor/VS Code agent system), you can read `SKILL.md` from context injection, but when you try to execute commands like:

```bash
python CUMCM_Workspace/_skill/scripts/stage_executor.py begin S1
```

The command fails because `scripts/` does not exist in the user's project directory—it exists in the skill installation directory.

**Solution**: Deploy all skill assets to `CUMCM_Workspace/_skill/` at initialization.

### Deployment Command

**If running for the first time OR if `CUMCM_Workspace/_skill/` does not exist:**

```bash
python scripts/skill_deployer.py deploy
```

This copies the following from the skill installation directory to `CUMCM_Workspace/_skill/`:
- `scripts/` (56+ Python files)
- `stages/` (14 stage instruction files)
- `references/` (27+ reference documents)
- `config/` (workflow.yaml, etc.)
- `templates/` (agent prompts, paper templates)

After deployment, all subsequent commands use the `_skill/` prefix:

```bash
python CUMCM_Workspace/_skill/scripts/stage_executor.py init --contest CUMCM --subquestions 3
python CUMCM_Workspace/_skill/scripts/stage_executor.py begin S1
```

### Fallback (If skill_deployer.py Is Not Found)

If `scripts/skill_deployer.py` cannot be found (skill assets not yet available), manually locate the skill installation directory and run:

```bash
python <SKILL_INSTALL_DIR>/scripts/skill_deployer.py deploy --skill-root <SKILL_INSTALL_DIR>
```

### Verification

Check deployment status:

```bash
python CUMCM_Workspace/_skill/scripts/skill_deployer.py status
```

Expected output:
```
[skill_deployer] 部署状态: 部署完整
  版本: 1.0.0
  部署时间: 2026-06-17T13:45:00
  文件总数: 120+
```

### Path Convention After Deployment

| Asset Type | New Path (After Deployment) |
|------------|----------------------------|
| Scripts | `CUMCM_Workspace/_skill/scripts/<name>.py` |
| Stage Instructions | `CUMCM_Workspace/_skill/stages/S{N}.md` |
| References | `CUMCM_Workspace/_skill/references/<file>.md` |
| Config | `CUMCM_Workspace/_skill/config/workflow.yaml` |
| Templates | `CUMCM_Workspace/_skill/templates/` |

**All subsequent path references in this document assume deployment has completed.**

---

## Directory & Path Convention (v4.0 — CRITICAL)

After completing Rule -1 (skill asset deployment), all skill assets are available at `CUMCM_Workspace/_skill/` within the project directory.

### Directory Structure After Deployment

```
<PROJECT_DIR>/                         ← PROJECT_ROOT (user's working directory)
├── CUMCM_Workspace/                   ← Runtime workspace
│   ├── _skill/                        ← 🆕 Deployed skill assets (from Rule -1)
│   │   ├── scripts/                   ← 56+ Python tool scripts
│   │   │   ├── stage_executor.py
│   │   │   ├── gate_contracts.py
│   │   │   ├── workspace_init.py
│   │   │   └── ... (55+ .py files)
│   │   ├── stages/                    ← 14 stage instruction files
│   │   │   ├── S0.md, S1.md, ..., S10.md
│   │   │   ├── S5.5.md, S7.5.md, S9.5.md
│   │   ├── references/                ← 27+ domain knowledge files
│   │   │   ├── problem-triage.md
│   │   │   ├── algorithm-map.md
│   │   │   ├── nature-writing-guide.md
│   │   │   └── ...
│   │   ├── config/                    ← Configuration files
│   │   │   └── workflow.yaml
│   │   ├── templates/                 ← Agent prompts, paper templates
│   │   └── manifest.json              ← Deployment metadata
│   ├── inputs/                        ← User-uploaded problem and data
│   │   ├── problem_text.md
│   │   ├── problem.pdf
│   │   └── data.xlsx
│   ├── outputs/                       ← All stage outputs
│   │   ├── q1/, q2/, q3/             ← Parallel sub-question isolation
│   │   ├── reviews/                   ← Inspector scoring reports
│   │   └── paper/                     ← Paper drafts (S8-S10)
│   ├── state/                         ← Execution state
│   │   ├── workflow_state.json
│   │   ├── stage_execution.json
│   │   └── decision_log.json
│   ├── data/                          ← Processed data
│   ├── methods/                       ← Method documents
│   └── ...
└── *.pdf / *.xlsx                     ← User's problem files (outside workspace)
```

### Path Reference Rules

**All commands and file references use the `_skill/` prefix:**

| Asset Type | Path Pattern | Example |
|------------|-------------|---------|
| Python Scripts | `python CUMCM_Workspace/_skill/scripts/<name>.py` | `python CUMCM_Workspace/_skill/scripts/stage_executor.py init` |
| Stage Instructions | `CUMCM_Workspace/_skill/stages/S{N}.md` | Read `CUMCM_Workspace/_skill/stages/S1.md` |
| References | `CUMCM_Workspace/_skill/references/<file>.md` | Read `CUMCM_Workspace/_skill/references/problem-triage.md` |
| Config | `CUMCM_Workspace/_skill/config/<file>.yaml` | `CUMCM_Workspace/_skill/config/workflow.yaml` |
| Templates | `CUMCM_Workspace/_skill/templates/<path>` | `CUMCM_Workspace/_skill/templates/agent_prompts/zhongshu.md` |

**Runtime workspace paths** (inputs, outputs, state) remain relative to `CUMCM_Workspace/`:
- `CUMCM_Workspace/inputs/problem_text.md`
- `CUMCM_Workspace/outputs/q1/model_proposal.md`
- `CUMCM_Workspace/state/stage_execution.json`

- `outputs/` → `PROJECT_ROOT/CUMCM_Workspace/outputs/` (relative to workspace root)
- `state/` → `PROJECT_ROOT/CUMCM_Workspace/state/` (relative to workspace root)
- `data/` → `PROJECT_ROOT/CUMCM_Workspace/data/` (relative to workspace root)

### Script Execution Convention

**All script commands must be run from PROJECT_ROOT.** The `scripts/` prefix in commands refers to `SKILL_ROOT/scripts/` (the platform resolves this automatically when the skill is installed).

```bash
# CORRECT — run from PROJECT_ROOT, _skill/ prefix points to deployed assets
python CUMCM_Workspace/_skill/scripts/stage_executor.py current
python CUMCM_Workspace/_skill/scripts/stage_executor.py begin S1
python CUMCM_Workspace/_skill/scripts/gate_contracts.py model-select --mode standard
python CUMCM_Workspace/_skill/scripts/workspace_init.py --contest CUMCM --subquestions 3


# WRONG — do NOT try to cd into SKILL_ROOT to run scripts
cd /path/to/skill/stages/../scripts/   # NEVER do this
```

**If scripts cannot be found**: Set the `SKILL_ROOT` environment variable to the skill's installation directory before running commands:
```bash
# PowerShell
$env:SKILL_ROOT = "C:\Users\<user>\.config\claude\skills\meta-model-skills-max"
python $env:SKILL_ROOT\scripts\stage_executor.py current

# Bash/Linux/Mac
export SKILL_ROOT="/home/<user>/.config/claude/skills/meta-model-skills-max"
python $SKILL_ROOT/scripts/stage_executor.py current
```

### Stage File Path Convention

When `stages/S{N}.md` says "Read: `references/algorithm-map.md`", this means **SKILL_ROOT/references/algorithm-map.md**.
When `stages/S{N}.md` says "Write: `outputs/q1/summary.md`", this means **PROJECT_ROOT/CUMCM_Workspace/outputs/q1/summary.md**.

All stage files use `inputs/`, `outputs/`, `state/`, `data/`, `methods/` to refer to directories **inside CUMCM_Workspace/** (relative to workspace root, not PROJECT_ROOT).

---

## Workflow Core Rules

### Rule 1: 14-Stage Sequential Execution

```
S0 → S1 → S2 → S3 → S4 → S5 → S5.5 → S6 → S7 → S7.5 → S8 → S9 → S9.5 → S10
```

Detailed instructions for each stage are in `<SKILL_ROOT>/stages/S{N}.md`. Read only the current stage file; do not read all at once.

### Rule 2: Stage Execution Protocol (with Mandatory Inspector Intervention)

```
 1. python CUMCM_Workspace/_skill/scripts/stage_executor.py current              → Confirm current stage
 2. python CUMCM_Workspace/_skill/scripts/stage_executor.py begin S{N}           → Start stage
 3. Read CUMCM_Workspace/_skill/stages/S{N}.md                                   → Load instructions
 4. Execute step by step (including sub-agent calls)                             → Sub-agents write directly to their output files
 5. python CUMCM_Workspace/_skill/scripts/stage_executor.py validate S{N}        → Verify output files exist and are non-empty
 6. Invoke Inspector Sub-Agent (see Rule 3)                                      → MANDATORY, write scoring to outputs/reviews/S{N}_review.md
 7. Score < passing threshold → rework → fix → back to step 3 or 4
 8. Score >= passing threshold → python CUMCM_Workspace/_skill/scripts/stage_executor.py gate_check S{N} → automated gate checks
 9. gate_check PASS → python CUMCM_Workspace/_skill/scripts/stage_executor.py complete S{N} --artifacts "..."
10. Output status report → proceed to next stage
```

**Steps 5-9 are MANDATORY for every stage. No mode (Fast/Standard/Championship) can skip these steps.**

**Prohibited**:
- Skipping inspector scoring
- Proceeding to the next stage despite inspector rejection
- Sub-agents writing files outside their authorized paths
- Sub-agents persisting across stages

### Rule 3: Mandatory Inspector Scoring

The inspector role must be invoked at the end of every stage for quality scoring.

**Passing Thresholds**: Fast >= 60 | Standard >= 70 | Championship >= 85

**Invocation**: Create a temporary sub-agent as per Rule 4, sending inspector prompt + stage artifacts + scoring criteria.

**Inspector Output**: Scoring report (total score + dimension scores + issue list P0/P1/P2 + improvement suggestions), written by the main agent to `outputs/reviews/S{N}_review.md`.

**Rework Limits**: Fast <= 2 attempts | Standard <= 3 attempts | Championship <= 5 attempts. Exceeded => BLOCKED => Request human intervention.

**Special Rule**: S9.5 inspection failure >= 2 times => automatically roll back to S9 for re-review (max 2 times).

### Rule 4: Sub-Agent On-Demand Pattern

Sub-agents are temporary inference units with the following lifecycle:

```
Create => Send instructions (role prompt + task + context + write path) => Sub-agent writes directly to output file => Destroy
```

**Constraints**:
- Sub-agents **write directly to the specified output file** (no main-agent relay needed)
- Each invocation is a fresh instance with no history context contamination
- Sub-agents may only write to file paths explicitly authorized in the instructions

**Platform-Specific Implementation**:

| Platform | How to Create Sub-Agent | Example |
|----------|------------------------|---------|
| **Inline Role-Play** | Use inline role-play within the same agent context | See "Invocation Template" below — paste the role prompt directly into the conversation |
| **Native Sub-Agent** | Use platform's native sub-agent mechanism (e.g., `[SYSTEM_DIRECTIVE]` or Task tool) | See "Invocation Template" below |
| **IDE Integration** | Use `@subagent` directive or inline role-play | See "Invocation Template" below |
| **Fallback Mode** | Main agent switches role perspectives sequentially | Change prefix to `【Now acting as {Role}】`, execute task, then `【Switch back to Orchestrator】` |

**INSPECTOR EXCEPTION**: The Inspector role MUST always be invoked as a separate sub-agent call. Role-play degradation is PROHIBITED for Inspector — if sub-agent spawning fails after retries, the stage must BLOCK and request human intervention.

**For all other roles**, if the platform does not support sub-agents, use role-play degradation:
```
【Now acting as {Role Name} — role-play mode】
All the same constraints apply. Write directly to the specified output file.
After completing the task, immediately switch back to the Orchestrator role.
```

**Invocation Template**:
```
【Call {Role Name} Sub-Agent】

You are {Role Name}. Execute the following task.

## Role Definition
{Role definition is inlined in stages/S{N}.md; reference it directly}

## Upstream Inputs
Read: {list of relevant files}

## Task
{specific task description}

## File Permissions
- Readable: {list of upstream files}
- Writable: {output file paths, e.g., outputs/q{N}/summary.md}
- Forbidden: {files that must not be written}

## Output Requirements
Write the result directly to the specified output file. Use Markdown format.
```

**Degradation Plan**: If the platform does not support sub-agents, the main agent switches role perspectives to execute the task. Use the format: `【Now acting as {Role Name}】... execute task ...【Switch back to Orchestrator】`. In role-play mode, the main agent directly writes to the output files (since there is no separate sub-agent to write). **Exception: Inspector MUST NOT be role-played by the main agent.** The Inspector role requires independent scoring — if sub-agent spawning is impossible, run gate_check without inspector scoring and flag the stage as "inspector_unavailable".

### Rule 0: Workspace Initialization (FIRST TIME ONLY)

**Before ANY stage execution, the workspace MUST exist.** This must be run from **PROJECT_ROOT**:

```bash
# Create full CUMCM_Workspace/ directory structure in PROJECT_ROOT
python CUMCM_Workspace/_skill/scripts/workspace_init.py --contest CUMCM --subquestions 3

# Verify completeness
python CUMCM_Workspace/_skill/scripts/workspace_init.py --check
```

**Windows PowerShell note**: Do NOT use `\` line continuation — use backtick `` ` `` instead:
```powershell
python CUMCM_Workspace/_skill/scripts/workspace_init.py --contest CUMCM `
  --subquestions 3
```

This creates `CUMCM_Workspace/` in PROJECT_ROOT with the full directory tree required by all 14 stages (`inputs/`, `outputs/`, `data/`, `methods/`, `state/`, etc.). **All scripts resolve paths relative to `CUMCM_Workspace/`** via `workspace_utils.py`. If the workspace does not exist, scripts fall back to the current directory, which leads to disorganized file layout.

**Auto-creation**: `stage_executor.py init` will also auto-create the workspace if it detects it is missing.

### Rule 5: Pre-Start Workspace Scan

Run from **PROJECT_ROOT** to scan the workspace:

```bash
# Scan PROJECT_ROOT (see what files the user has)
python -c "import os; print('\n'.join(sorted(os.listdir('.'))))"

# Scan CUMCM_Workspace/inputs/ (user-uploaded problem files)
python -c "import os, glob; print('\n'.join(sorted(glob.glob('CUMCM_Workspace/inputs/**/*', recursive=True))))"

# Scan SKILL_ROOT/scripts/ (available tool scripts)
python -c "import os, pathlib; scripts=pathlib.Path(__file__).parent.parent / 'scripts'; print('\n'.join(f for f in sorted(os.listdir(scripts)) if f.endswith('.py')))" scripts/workspace_init.py
```

> **Note**: The third command uses `__file__` to find SKILL_ROOT relative to the script. If running inline Python, replace with the actual SKILL_ROOT path or use `os.environ.get('SKILL_ROOT', 'scripts')`.

### Rule 6: Status Reports

Mandatory output after each stage completes:

```yaml
status: pass | needs_rework | blocked
artifacts: [list of output files]
inspector_score: XX/100
issues: [list of issues]
next: next action
```

### Rule 7: Integrity Red Lines

Block delivery if any of the following are found: fabricated data/references/experimental results, untraceable paper numbers, unsubstantiated performance claims, stale results after code changes, missing justification for major assumptions, non-descriptive figure/table titles, inconsistent formulas and code, overclaiming of negative results.

### Rule 8: Mandatory Command Execution Checklist

**Every stage MUST execute the following commands in order. Skipping any command is a protocol violation.**

| Stage | Required Commands (execute in order) |
|-------|--------------------------------------|
| S0 | `validate S0` → **Invoke Inspector** → `gate_check S0` → `complete S0` |
| S1 | `validate S1` → **Invoke Inspector** → `gate_check S1` → `complete S1` |
| S2 | `validate S2` → **Invoke Inspector** → `gate_check S2` → `complete S2` |
| S3 | `validate S3` → **Invoke Inspector** → `gate_check S3` → `complete S3` |
| S4 | `validate S4` → **Invoke Inspector** → `gate_check S4` → `complete S4` |
| S5 | `validate S5` → **Invoke Inspector** → `gate_check S5` → `complete S5` |
| S5.5 | `validate S5.5` → **Invoke Inspector** → `gate_check S5.5` → `complete S5.5` |
| S6 | `validate S6` → **Invoke Inspector** → `gate_check S6` → `complete S6` |
| S7 | `validate S7` → **Invoke Inspector** → `gate_check S7` → `complete S7` |
| S7.5 | `validate S7.5` → **Invoke Inspector** → `gate_check S7.5` → `complete S7.5` |
| S8 | `validate S8` → **Invoke Inspector** → `gate_check S8` → `complete S8` |
| S9 | `validate S9` → **Invoke Inspector** → `gate_check S9` → `complete S9` |
| S9.5 | `validate S9.5` → **Invoke Inspector** → `gate_check S9.5` → `complete S9.5` |
| S10 | `validate S10` → **Invoke Inspector** → `gate_check S10` → `complete S10` |

**Legend**:
- `validate S{N}` = `python CUMCM_Workspace/_skill/scripts/stage_executor.py validate S{N}` -- verify output files exist and are non-empty
- **Invoke Inspector** = Create temporary inspector sub-agent (see Rule 3) -- **HARD RULE, cannot be skipped**
- `gate_check S{N}` = `python CUMCM_Workspace/_skill/scripts/stage_executor.py gate_check S{N}` -- run automated gate checks
- `complete S{N}` = `python CUMCM_Workspace/_skill/scripts/stage_executor.py complete S{N} --artifacts "..."` -- mark stage complete

**Execution Rules**:
1. **Inspector scoring is a hard rule** -- cannot be skipped under any mode (Fast/Standard/Championship)
2. **gate_check must run AFTER inspector scoring passes** -- gate_check reads inspector score from `outputs/reviews/S{N}_review.md`
3. **complete requires BOTH inspector pass AND gate_check pass** -- cannot complete if either fails
4. **rework is mandatory on failure** -- `python CUMCM_Workspace/_skill/scripts/stage_executor.py rework S{N} --reason "..."` -- must record reason and count
5. **Rework limit exceeded = BLOCKED** -- must request human intervention, cannot auto-proceed

**Additional Mandatory Commands by Stage**:

| Stage | Additional Commands |
|-------|-------------------|
| S3 | `gate_contracts.py model-select`, `gate_contracts.py innovation` |
| S4 | `experiment_race.py check --subquestion Q1` |
| S5 | `gate_contracts.py parallel-merge`, `gate_contracts.py baseline` |
| S5.5 | `gate_contracts.py innovation` |
| S6 | `gate_contracts.py check G4` |
| S7 | `gate_contracts.py evidence-chain` |
| S8 | `paper_assembly_checker.py`, `gate_contracts.py figure-narrative`, `gate_contracts.py structure`, `gate_contracts.py abstract`, `gate_contracts.py paper-quality`, `gate_contracts.py paper-evaluation` |
| S9 | `gate_contracts.py adversarial` |
| S9.5 | `publication_checker.py check`, `publication_checker.py report`, `gate_contracts.py publication-ready` |

---

## 14-Stage Index

| Stage | Name                      | Primary Roles                  | Inspector | Instruction File (SKILL_ROOT) |
|-------|---------------------------|--------------------------------|-----------|------------------|
| S0    | Problem Registration      | Planner                        | ✅        | `stages/S0.md` |
| S1    | Problem Analysis          | Planner+Analyst->Reviewer      | ✅        | `stages/S1.md` |
| S2    | Data Governance           | Analyst                        | ✅        | `stages/S2.md` |
| S3    | Model Selection           | Proposer->Critic->Reviewer     | ✅        | `stages/S3.md` |
| S4    | Experiment Race           | Builder                        | ✅        | `stages/S4.md` |
| S5    | Modeling & Solving        | Proposer+Builder               | ✅        | `stages/S5.md` |
| S5.5  | Model Evolution           | Proposer+Builder               | ✅        | `stages/S5.5.md` |
| S6    | Verification & Sensitivity| Builder+Proposer               | ✅        | `stages/S6.md` |
| S7    | Evidence Chain            | Planner                        | ✅        | `stages/S7.md` |
| S7.5  | Unified Kernel            | Planner                        | ✅        | `stages/S7.5.md` |
| S8    | Paper Writing             | Writer+Multi-role              | ✅        | `stages/S8.md` |
| S9    | Adversarial Review        | Critic->Reviewer->Writer       | ✅        | `stages/S9.md` |
| S9.5  | Publication Readiness     | Inspector                      | ✅        | `stages/S9.5.md` |
| S10   | Final Build               | Writer+Planner                 | ✅        | `stages/S10.md` |

**All instruction files are located at `<SKILL_ROOT>/stages/S{N}.md`.** Read only the current stage's file; do not read all at once.

---

## Role Registry (7 Functional Roles + 1 Inspector)

All role prompts are **inlined directly in `stages/S{N}.md`**. Each stage file contains the complete sub-agent instructions for every role used in that stage. There is **no external `agent_prompts/` directory** — do not look for one.

Sub-agents are created on demand and destroyed after use. The main agent reads the role prompt from the stage file and dispatches it to the sub-agent.

| Role       | Core Responsibility                                                     | Notes                          |
|------------|-------------------------------------------------------------------------|--------------------------------|
| Planner    | Strategic planning, problem parsing, literature search, technical roadmap | Planning Group               |
| Analyst    | Data profiling, cleaning, quality report, data dictionary                | Analysis Group                |
| Proposer   | Candidate model generation, formula derivation, baseline comparison, robustness | Proposal Group (merged)  |
| Builder    | Python coding, experiment execution, figure generation                   | Build Group                   |
| Critic     | Red-team attack, adversarial review, P0/P1/P2 grading                   | Review Group                   |
| Reviewer   | Four-dimensional review, rejection decisions, model arbitration          | Review Group                   |
| Writer     | Paper writing, abstract refinement, format compliance, DOCX             | Writing Group                  |
| **Inspector** | **Quality scoring, issue identification, improvement suggestions**   | **Inspector (Special Role)**   |

---

## Tool Script Registry

**All scripts are located at `CUMCM_Workspace/_skill/scripts/` after deployment (see Rule -1).** Execute from PROJECT_ROOT using the full path.

**Core Tools**:

| Script                       | Purpose                                           | Execution |
|------------------------------|---------------------------------------------------|-----------|
| `skill_deployer.py`          | Deploy skill assets to project directory | `python scripts/skill_deployer.py deploy` (first time only) |
| `workspace_init.py`          | Workspace initialization (create CUMCM_Workspace directory tree) | `python CUMCM_Workspace/_skill/scripts/workspace_init.py --contest CUMCM --subquestions 3` |
| `stage_executor.py`          | Stage state machine (begin/complete/gate_check/rework) | `python CUMCM_Workspace/_skill/scripts/stage_executor.py <command>` |
| `gate_contracts.py`          | Automated gate check engine | `python CUMCM_Workspace/_skill/scripts/gate_contracts.py <check-name> --mode <mode>` |
| `pipeline_manager.py`        | Full pipeline orchestration and status queries | `python CUMCM_Workspace/_skill/scripts/pipeline_manager.py <command>` |
| `build_docx.py`              | Markdown -> DOCX generation | `python CUMCM_Workspace/_skill/scripts/build_docx.py draft.md output.docx` |
| `diagram_generator.py`       | Technical roadmap generation | `python CUMCM_Workspace/_skill/scripts/diagram_generator.py <command>` |
| `figure_dac_generator.py`    | Figure D-A-C narrative template generator | `python CUMCM_Workspace/_skill/scripts/figure_dac_generator.py <command>` |
| `publication_checker.py`     | Publication readiness check (S9.5) | `python CUMCM_Workspace/_skill/scripts/publication_checker.py check <file>` |
| `paper_assembly_checker.py`  | Paper artifact mapping verification | `python CUMCM_Workspace/_skill/scripts/paper_assembly_checker.py <paper.md>` |

**Specialized Tools** (call on demand, run `python CUMCM_Workspace/_skill/scripts/<name>.py --help` for usage):

`abstract_body_consistency.py` . `abstract_quality_gate.py` . `academic_expression_checker.py` . `adversarial_review.py` . `assumption_engineer.py` . `auto_orchestrator.py` . `check_data.py` . `competition_adapter.py` . `compile_pdf.py` . `compress_agent_output.py` . `context_bridge.py` . `cross_subquestion_consistency.py` . `data_preprocessor.py` . `derivation_chain_checker.py` . `discussion_enhancer.py` . `docx_revision.py` . `docx_to_latex.py` . `evidence_tracer.py` . `experiment_race.py` . `figure_narrative_gate.py` . `final_vfy.py` . `formula_renderer.py` . `frozen_numbers.py` . `hook_engine.py` . `math_sandbox.py` . `meeting_protocol.py` . `method_selection_matrix.py` . `metric_guardian.py` . `model_evolver.py` . `per_subquestion_verification.py` . `plot_figures_nature.py` . `quality_gate.py` . `recovery_manager.py` . `rereview.py` . `review_paper.py` . `sensitivity_analysis.py` . `stage_reviewer.py` . `state_manager.py` . `subagent_runner.py` . `subagent_watchdog.py` . `verify_build.py` . `workspace_utils.py`


---

## Execution Modes

| Mode         | Trigger                          | Behavior                                                       |
|--------------|----------------------------------|----------------------------------------------------------------|
| **Manual**   | Default                          | Present numbered options at each decision point; wait after inspector scoring |
| **Auto**     | User requests "fully automatic"  | Inspector score drives progression; auto rework on failure, pause on exceed |
| **Fast**     | Tight deadline                   | Threshold >=60, max rework <=2, words >=8K, figures >=4, sub-agent calls <=20 |
| **Standard** | Default depth                    | Threshold >=70, max rework <=3, words >=12K, figures >=6        |
| **Championship** | Top-score pursuit            | Threshold >=85, max rework <=5, words >=15K, figures >=10, red-team x3, abstract x3 rounds |

### Fast Mode Streamlined Path (P1-2)

Fast mode goal: **total sub-agent calls <= 20**. Stage-level simplifications:

| Stage | Standard/Championship                  | Fast Mode                                              |
|-------|----------------------------------------|--------------------------------------------------------|
| S0    | Inspector scoring + gate check          | Skip inspector, direct initialization (3 steps)        |
| S1    | 3 sub-agents (Planner+Analyst+Reviewer) | 2 sub-agents (Planner+Analyst, skip Reviewer)          |
| S2    | Full data governance                    | Equation-driven: lightweight path (data description only) |
| S3    | 5-8 calls                               | 3 calls (1 Proposer + simplified attack/defense + Referee) |
| S4    | Full experiment race                    | Skip (use S3 conclusions directly)                     |
| S5    | Full modeling & solving                 | Same as Standard (cannot be simplified)                |
| S5.5  | Conditional execution                   | Skip by default                                        |
| S6    | Triple verification                     | Sensitivity analysis only                              |
| S7    | Evidence chain                          | Same as Standard (cannot be simplified)                |
| S7.5  | Standalone execution                    | Merge into S8 (as S8 Step 4 subtask)                   |
| S8    | Full writing (6 Writer rounds)          | Simplified template (4 Writer rounds, skip 6B skeleton refinement) |
| S9    | Multi-round review                      | 1 round (Critic->Writer, skip Reviewer)                |
| S9.5  | Full-dimension check                    | P0 items only (AI cliches + anonymity)                 |
| S10   | Full check                              | Skip cross-subquestion consistency check               |

**Fast Mode Prohibited**:
- Must not skip P0 gate checks (integrity red lines remain mandatory)
- Must not skip S5/S7 (core modeling and evidence chain are non-negotiable)
- Must not lower the minimum word count (>=8000 words remains a hard constraint)

---

## Competition Adaptation

| Competition | Language | Format Specification              |
|-------------|----------|-----------------------------------|
| CUMCM       | Chinese  | `references/format-spec-cumcm.md`  |
| 51MCM       | Chinese  | `references/format-spec-51mcm.md`  |
| MCM/ICM     | English  | `references/format-spec-mcm-icm.md`|

---

## Reference Index

**All reference files are located at `<SKILL_ROOT>/references/`**. Load on demand; do not read all at once.

| Scenario                           | File (relative to SKILL_ROOT) |
|------------------------------------|------|
| Problem classification S0-S1       | `references/problem-triage.md`, `references/problem-taxonomy.md` |
| Literature search S1               | `references/literature-search-guide.md` |
| Algorithm selection S3             | `references/algorithm-map.md`, `references/algorithm-library/` |
| Model derivation S3-S5             | `references/model-formulation-guide.md` |
| Experiment design S4               | `references/experiment_design_framework.md` |
| Robustness S6                      | `references/robustness-guide.md` |
| Paper writing S8                   | `references/paper-writing-rules.md`, `references/nature-writing-guide.md` |
| Paper templates S8-S9.5            | `<SKILL_ROOT>/templates/paper_templates/` -- select 1-2 award-winning PDFs, read with read_file as format reference |
| Scoring criteria S8-S9             | `references/scoring-criteria-cumcm.md` |
| Integrity audit S9                 | `references/integrity_gate_checklist.md`, `references/qa-checklist.md` |
| Format specification S10           | `references/format-spec-*.md` |

---

## Friendly Interaction

Hide internal terminology from the user: use "modeling team / data team / review team" instead of role names, "quality review" instead of gate_check, "optimization adjustment" instead of rework. Present key decisions as numbered options with safe defaults.

---

**Version**: v4.0.0 | **Updated**: 2026-06-17
