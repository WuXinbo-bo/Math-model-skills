#!/usr/bin/env python3
"""
ContextBridge v1.0 - 子 Agent 间上下文管理

Architecture:
  - File-based message passing between subagents
  - Strict file isolation: each agent reads only upstream artifacts
  - Automatic output compression for downstream consumption
  - Artifact dependency resolution via DAG

Design Principles (borrowed from old project's Role Handoff Rule):
  1. Subagent can only read upstream artifacts, not other subagents' intermediates
  2. Artifacts are compressed when passed (>2000 chars -> summary)
  3. Each subagent's output directory is strictly isolated

CLI Commands:
  build-context   --agent-id X --meeting-id M    Build context package
  compress        --file path/to/file.md          Compress file to summary
  compress-dir    --dir path/to/dir/              Compress all .md in dir
  isolation       --agent-id X --meeting-id M     Show file isolation rules
  resolve-deps    --agent-id X --stage-id S       Resolve upstream dependencies
  handoff         --from-agent A --to-agent B     Generate handoff package
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
CONTEXT_DIR = DOCS_DIR / "contexts"
SUMMARIES_DIR = DOCS_DIR / "summaries"

# Maximum characters before compression kicks in
MAX_CONTEXT_CHARS = 2000
MAX_SUMMARY_CHARS = 1500

# ═══════════════════════════════════════════════════════════════
# File Isolation Matrix
# ═══════════════════════════════════════════════════════════════

# Defines what each agent can read, write, and must not touch
ISOLATION_MATRIX = {
    "planner": {
        "read": [
            "inputs/*",
            "config/workflow.yaml",
            "references/problem-triage.md",
            "references/problem-taxonomy.md",
        ],
        "write": [
            "outputs/problem_analysis/planner_view.md",
            "outputs/problem_analysis/problem_restatement.md",
            "outputs/problem_analysis/symbol_table.md",
            "outputs/problem_analysis/tech_roadmap.md",
        ],
        "forbidden": [
            "outputs/problem_analysis/analyst_view.md",
            "outputs/problem_analysis/reviewer_review.md",
            "methods/*",
            "src/*",
            "paper.md",
        ],
    },
    "analyst": {
        "read": [
            "inputs/*",
            "data/*",
            "config/workflow.yaml",
        ],
        "write": [
            "outputs/problem_analysis/analyst_view.md",
            "outputs/data_governance/data_dictionary.md",
            "outputs/data_governance/data_profile_report.md",
        ],
        "forbidden": [
            "outputs/problem_analysis/planner_view.md",
            "outputs/problem_analysis/reviewer_review.md",
            "methods/*",
            "src/*",
            "paper.md",
        ],
    },
    "reviewer": {
        "read": [
            "outputs/problem_analysis/*.md",
            "outputs/data_governance/*.md",
            "methods/*.md",
            "paper.md",
        ],
        "write": [
            "outputs/*/reviewer_review.md",
            "outputs/*/reviewer_verdict.md",
        ],
        "forbidden": [
            "inputs/*",
            "src/*",
        ],
    },
    "proposer": {
        "read": [
            "outputs/problem_analysis/*",
            "outputs/data_governance/*",
            "planning/*",
            "references/algorithm-library.md",
            "references/model-formulation-guide.md",
        ],
        "write": [
            "methods/proposer_proposals.md",
            "src/q{N}/*.py",
            "outputs/q{N}/solution_summary.md",
        ],
        "forbidden": [
            "paper.md",
        ],
    },
    "builder": {
        "read": [
            "methods/*",
            "data/processed/*",
            "outputs/problem_analysis/*",
            "references/algorithm-library.md",
        ],
        "write": [
            "src/q{N}/*.py",
            "outputs/q{N}/*.csv",
            "outputs/q{N}/*.json",
            "outputs/q{N}/solution_summary.md",
            "figures/*.png",
        ],
        "forbidden": [
            "paper.md",
            "outputs/problem_analysis/planner_view.md",
        ],
    },
    "critic": {
        "read": [
            "paper.md",
            "outputs/**/*",
            "methods/*",
            "src/**/*.py",
        ],
        "write": [
            "outputs/*/critic_attack.md",
            "outputs/*/adversarial_review.md",
        ],
        "forbidden": [
            "inputs/*",
        ],
    },
    "writer": {
        "read": [
            "paper.md",
            "outputs/**/*",
            "references/format-spec-51mcm.md",
            "references/documents-workflow.md",
        ],
        "write": [
            "paper.md",
            "output/final.docx",
            "output/final.pdf",
            "appendix/*",
        ],
        "forbidden": [
            "src/*",
            "data/*",
        ],
    },
}

# Stage-to-agent mapping for dependency resolution
STAGE_AGENTS = {
    "S0_input_registration": ["planner"],
    "S1_problem_analysis": ["planner", "analyst", "reviewer"],
    "S2_data_governance": ["analyst"],
    "S3_model_debate": ["proposer", "critic", "reviewer"],
    "S4_experiment_design": ["builder"],
    "S5_modeling_and_solve": ["proposer", "builder"],
    "S5_5_model_evolution": ["proposer", "builder"],
    "S6_validation": ["builder", "proposer"],
    "S7_evidence_chain": ["planner"],
    "S7_5_unified_kernel": ["planner"],
    "S8_paper_write": ["writer", "planner", "proposer", "builder"],
    "S9_adversarial_review": ["critic", "reviewer", "writer"],
    "S9_5_publication_check": ["inspector"],
    "S10_final_build": ["writer", "planner"],
}

# Stage dependency DAG
STAGE_DEPS = {
    "S0_input_registration": [],
    "S1_problem_analysis": ["S0_input_registration"],
    "S2_data_governance": ["S1_problem_analysis"],
    "S3_model_debate": ["S2_data_governance"],
    "S4_experiment_design": ["S3_model_debate"],
    "S5_modeling_and_solve": ["S4_experiment_design"],
    "S5_5_model_evolution": ["S5_modeling_and_solve"],
    "S6_verification": ["S5_5_model_evolution"],
    "S7_evidence_chain": ["S6_verification"],
    "S8_paper_drafting": ["S7_evidence_chain"],
    "S9_adversarial_review": ["S8_paper_drafting"],
    "S10_final_delivery": ["S9_adversarial_review"],
}


def _ensure_dirs():
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# Context Building
# ═══════════════════════════════════════════════════════════════

def build_context(agent_id: str, meeting_id: Optional[str] = None,
                  stage_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a complete context package for a subagent.

    The context package includes:
    1. File isolation rules (what to read/write/avoid)
    2. Upstream artifact summaries (compressed)
    3. Stage dependency information
    4. Meeting context (if applicable)

    Args:
        agent_id: Agent identifier
        meeting_id: Optional meeting context
        stage_id: Optional stage context

    Returns:
        Context package dict
    """
    _ensure_dirs()

    isolation = get_isolation_rules(agent_id)
    upstream = resolve_upstream_artifacts(agent_id, stage_id)
    deps = resolve_dependencies(agent_id, stage_id)

    # Compress upstream artifacts
    compressed_upstream = []
    for artifact in upstream:
        path = Path(artifact["path"])
        if path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > MAX_CONTEXT_CHARS:
                summary = compress_text(content)
                compressed_upstream.append({
                    "path": artifact["path"],
                    "original_size": len(content),
                    "compressed_size": len(summary),
                    "summary": summary,
                    "was_compressed": True,
                })
            else:
                compressed_upstream.append({
                    "path": artifact["path"],
                    "original_size": len(content),
                    "compressed_size": len(content),
                    "summary": content,
                    "was_compressed": False,
                })

    context = {
        "agent_id": agent_id,
        "meeting_id": meeting_id,
        "stage_id": stage_id,
        "generated_at": _now(),
        "isolation": isolation,
        "upstream_artifacts": compressed_upstream,
        "dependencies": deps,
    }

    # Write context file
    ctx_file = CONTEXT_DIR / f"{agent_id}_context.json"
    ctx_file.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")

    return context


def get_isolation_rules(agent_id: str) -> Dict[str, List[str]]:
    """Get file isolation rules for an agent."""
    rules = ISOLATION_MATRIX.get(agent_id, {
        "read": [],
        "write": [],
        "forbidden": [],
    })
    return rules


def resolve_upstream_artifacts(agent_id: str,
                               stage_id: Optional[str] = None) -> List[Dict[str, str]]:
    """Resolve upstream artifacts that an agent should read.

    Based on the stage dependency DAG, finds all artifacts produced
    by upstream stages.
    """
    if not stage_id:
        return []

    # Find upstream stages
    upstream_stages = STAGE_DEPS.get(stage_id, [])
    if not upstream_stages:
        return []

    # Collect artifacts from upstream stages
    artifacts = []
    for up_stage in upstream_stages:
        up_agents = STAGE_AGENTS.get(up_stage, [])
        for up_agent in up_agents:
            rules = ISOLATION_MATRIX.get(up_agent, {})
            for write_pattern in rules.get("write", []):
                # Resolve glob patterns to actual files
                resolved = list(PROJECT_ROOT.glob(write_pattern.replace("{N}", "*")))
                for f in resolved:
                    if f.exists() and f.stat().st_size > 0:
                        artifacts.append({
                            "path": str(f.relative_to(PROJECT_ROOT)),
                            "created_by": up_agent,
                            "stage": up_stage,
                            "size": f.stat().st_size,
                        })

    return artifacts


def resolve_dependencies(agent_id: str,
                         stage_id: Optional[str] = None) -> Dict[str, Any]:
    """Resolve stage-level dependencies for an agent."""
    if not stage_id:
        return {"upstream_stages": [], "downstream_stages": []}

    upstream = STAGE_DEPS.get(stage_id, [])
    downstream = [s for s, deps in STAGE_DEPS.items() if stage_id in deps]

    return {
        "current_stage": stage_id,
        "upstream_stages": upstream,
        "downstream_stages": downstream,
        "stage_agents": STAGE_AGENTS.get(stage_id, []),
    }


# ═══════════════════════════════════════════════════════════════
# Compression
# ═══════════════════════════════════════════════════════════════

def compress_text(text: str, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Compress text to a summary by extracting key lines.

    Strategy:
    1. Extract lines with conclusion/result keywords
    2. Extract lines with numerical data
    3. Extract section headers
    4. Fill remaining space with first N lines

    Args:
        text: Original text
        max_chars: Maximum output characters

    Returns:
        Compressed summary text
    """
    lines = text.split('\n')

    # Priority 1: Section headers
    headers = [l for l in lines if l.strip().startswith('#')]

    # Priority 2: Conclusion/result lines
    conclusion_keywords = [
        '结论', '结果', '发现', '核心', '关键', '建议', '风险',
        '总结', '评价', '优势', '劣势', '改进', '验证', '通过', '失败',
        'conclusion', 'result', 'finding', 'recommendation', 'risk',
    ]
    conclusions = [
        l for l in lines
        if any(kw in l.lower() for kw in conclusion_keywords)
        and l.strip() and not l.strip().startswith('#')
    ]

    # Priority 3: Numerical data lines
    number_pattern = re.compile(r'\d+\.?\d*\s*[%％℃m]|RMSE|MAE|R²|accuracy|精度|误差')
    numbers = [
        l for l in lines
        if number_pattern.search(l)
        and l.strip() and not l.strip().startswith('#')
        and l not in conclusions
    ]

    # Priority 4: First few content lines
    content_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')][:5]

    # Assemble summary
    summary_parts = []

    if headers:
        summary_parts.append("## Structure")
        summary_parts.extend(headers[:15])
        summary_parts.append("")

    if conclusions:
        summary_parts.append("## Key Conclusions")
        summary_parts.extend(conclusions[:10])
        summary_parts.append("")

    if numbers:
        summary_parts.append("## Key Numbers")
        summary_parts.extend(numbers[:8])
        summary_parts.append("")

    if not conclusions and not numbers:
        summary_parts.append("## Content Preview")
        summary_parts.extend(content_lines)

    summary = '\n'.join(summary_parts)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n...[truncated]"

    return summary


def compress_file(file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Compress a single file to summary.

    Args:
        file_path: Path to the file to compress
        output_path: Optional output path for summary

    Returns:
        Compression result dict
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "msg": f"File not found: {file_path}"}

    content = path.read_text(encoding="utf-8", errors="replace")
    original_size = len(content)

    if original_size <= MAX_CONTEXT_CHARS:
        return {
            "status": "skipped",
            "msg": f"File already small ({original_size} chars)",
            "original_size": original_size,
        }

    summary = compress_text(content)

    if output_path:
        out = Path(output_path)
    else:
        _ensure_dirs()
        out = SUMMARIES_DIR / f"{path.stem}_summary.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")

    return {
        "status": "compressed",
        "original_size": original_size,
        "compressed_size": len(summary),
        "ratio": f"{len(summary) / original_size:.1%}",
        "output": str(out),
    }


def compress_directory(dir_path: str) -> Dict[str, Any]:
    """Compress all .md files in a directory.

    Args:
        dir_path: Directory path

    Returns:
        Batch compression result
    """
    dir_p = Path(dir_path)
    if not dir_p.exists():
        return {"status": "error", "msg": f"Directory not found: {dir_path}"}

    results = []
    for md_file in dir_p.glob("*.md"):
        result = compress_file(str(md_file))
        results.append({"file": md_file.name, **result})

    return {
        "status": "completed",
        "total_files": len(results),
        "compressed": sum(1 for r in results if r.get("status") == "compressed"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════
# Handoff Package
# ═══════════════════════════════════════════════════════════════

def generate_handoff(from_agent: str, to_agent: str,
                     meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a handoff package from one agent to another.

    Creates a structured document that passes the from-agent's
    output (compressed) to the to-agent as input context.

    Args:
        from_agent: Source agent ID
        to_agent: Target agent ID
        meeting_id: Optional meeting context

    Returns:
        Handoff package dict
    """
    _ensure_dirs()

    from_rules = ISOLATION_MATRIX.get(from_agent, {})
    to_rules = ISOLATION_MATRIX.get(to_agent, {})

    # Find from-agent's output files
    from_outputs = []
    for pattern in from_rules.get("write", []):
        resolved = list(PROJECT_ROOT.glob(pattern.replace("{N}", "*")))
        for f in resolved:
            if f.exists() and f.stat().st_size > 0:
                from_outputs.append(f)

    # Compress each output
    compressed = []
    for f in from_outputs:
        content = f.read_text(encoding="utf-8", errors="replace")
        if len(content) > MAX_CONTEXT_CHARS:
            summary = compress_text(content)
            compressed.append({
                "file": str(f.relative_to(PROJECT_ROOT)),
                "summary": summary,
                "was_compressed": True,
            })
        else:
            compressed.append({
                "file": str(f.relative_to(PROJECT_ROOT)),
                "summary": content,
                "was_compressed": False,
            })

    # Write handoff document
    handoff_id = f"{from_agent}_to_{to_agent}"
    handoff_file = CONTEXT_DIR / f"{handoff_id}_handoff.md"

    lines = [
        f"# Handoff: {from_agent} -> {to_agent}",
        "",
        f"**Generated**: {_now()}",
        f"**Meeting**: {meeting_id or 'N/A'}",
        "",
        "---",
        "",
    ]

    for item in compressed:
        lines.append(f"## {item['file']}")
        if item["was_compressed"]:
            lines.append(f"*Compressed from original (see full file for details)*")
        lines.append("")
        lines.append(item["summary"])
        lines.append("")

    handoff_file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "status": "completed",
        "handoff_file": str(handoff_file),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "artifacts_passed": len(compressed),
        "compressed_count": sum(1 for c in compressed if c["was_compressed"]),
    }


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="ContextBridge v1.0 - 子 Agent 间上下文管理"
    )
    sub = p.add_subparsers(dest="command")

    # build-context
    pbc = sub.add_parser("build-context", help="Build context package")
    pbc.add_argument("--agent-id", required=True)
    pbc.add_argument("--meeting-id", default=None)
    pbc.add_argument("--stage-id", default=None)

    # compress
    pc = sub.add_parser("compress", help="Compress file to summary")
    pc.add_argument("--file", required=True)
    pc.add_argument("--output", default=None)

    # compress-dir
    pcd = sub.add_parser("compress-dir", help="Compress all .md in dir")
    pcd.add_argument("--dir", required=True)

    # isolation
    pi = sub.add_parser("isolation", help="Show file isolation rules")
    pi.add_argument("--agent-id", required=True)

    # resolve-deps
    prd = sub.add_parser("resolve-deps", help="Resolve upstream dependencies")
    prd.add_argument("--agent-id", required=True)
    prd.add_argument("--stage-id", required=True)

    # handoff
    ph = sub.add_parser("handoff", help="Generate handoff package")
    ph.add_argument("--from-agent", required=True)
    ph.add_argument("--to-agent", required=True)
    ph.add_argument("--meeting-id", default=None)

    args = p.parse_args()

    if args.command == "build-context":
        result = build_context(args.agent_id, args.meeting_id, args.stage_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "compress":
        result = compress_file(args.file, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "compress-dir":
        result = compress_directory(args.dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "isolation":
        rules = get_isolation_rules(args.agent_id)
        print(f"\n{'=' * 60}")
        print(f"  File Isolation Rules: {args.agent_id}")
        print(f"{'=' * 60}")
        print(f"\n  Read (allowed):")
        for r in rules.get("read", []):
            print(f"    + {r}")
        print(f"\n  Write (output):")
        for w in rules.get("write", []):
            print(f"    > {w}")
        print(f"\n  Forbidden (do NOT touch):")
        for f in rules.get("forbidden", []):
            print(f"    x {f}")
        print(f"{'=' * 60}\n")

    elif args.command == "resolve-deps":
        deps = resolve_dependencies(args.agent_id, args.stage_id)
        print(json.dumps(deps, ensure_ascii=False, indent=2))

    elif args.command == "handoff":
        result = generate_handoff(args.from_agent, args.to_agent, args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
