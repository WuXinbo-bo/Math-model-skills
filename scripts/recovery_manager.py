#!/usr/bin/env python3
"""
RecoveryManager v1.0 - 故障恢复与检查点管理

Architecture:
  - Per-stage checkpoint with artifact snapshot
  - Rollback to any checkpoint with hash verification
  - Resume from checkpoint after failure
  - Integrates with StateManager for workflow state sync

Design:
  - Checkpoints stored as JSON in docs/command/checkpoints/
  - Each checkpoint records: stage_id, timestamp, agent results,
    artifact hashes, and workflow state snapshot
  - Rollback verifies artifact integrity before restoring

CLI Commands:
  checkpoint  --stage-id S1 --meeting-id M001   Create checkpoint
  rollback    --stage-id S1                      Rollback to checkpoint
  resume      --stage-id S1                      Resume from checkpoint
  list                                           List all checkpoints
  verify      --stage-id S1                      Verify checkpoint integrity
  cleanup     --before S5                        Remove old checkpoints
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
CHECKPOINT_DIR = DOCS_DIR / "command" / "checkpoints"
ROLLBACK_LOG = DOCS_DIR / "command" / "rollback_log.json"


def _ensure_dirs():
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _file_hash(fpath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not fpath.exists():
        return "missing"
    return hashlib.sha256(fpath.read_bytes()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# Checkpoint
# ═══════════════════════════════════════════════════════════════

def create_checkpoint(stage_id: str, meeting_id: Optional[str] = None,
                      agent_results: Optional[Dict] = None,
                      extra: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a checkpoint for a completed stage.

    Records:
    1. Stage completion status
    2. Agent execution results (if any)
    3. Artifact file hashes (for integrity verification)
    4. Workflow state snapshot

    Args:
        stage_id: Stage identifier
        meeting_id: Optional meeting context
        agent_results: Dict of agent_id -> execution result
        extra: Additional metadata

    Returns:
        Checkpoint dict
    """
    _ensure_dirs()

    # Snapshot artifacts
    artifact_snapshot = _snapshot_artifacts()

    # Snapshot workflow state
    workflow_snapshot = _snapshot_workflow_state()

    checkpoint = {
        "stage_id": stage_id,
        "meeting_id": meeting_id,
        "created_at": _now(),
        "agent_results": agent_results or {},
        "artifact_snapshot": artifact_snapshot,
        "workflow_snapshot": workflow_snapshot,
        "extra": extra or {},
    }

    # Compute checkpoint hash (for integrity)
    checkpoint_json = json.dumps(checkpoint, sort_keys=True, ensure_ascii=False)
    checkpoint["hash"] = hashlib.sha256(checkpoint_json.encode()).hexdigest()[:16]

    # Write checkpoint file
    cp_file = CHECKPOINT_DIR / f"{stage_id}_checkpoint.json"
    cp_file.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "created",
        "stage_id": stage_id,
        "checkpoint_file": str(cp_file),
        "hash": checkpoint["hash"],
        "artifacts_count": len(artifact_snapshot),
        "agents_count": len(agent_results or {}),
    }


def _snapshot_artifacts() -> List[Dict[str, str]]:
    """Snapshot all artifact files with their hashes."""
    snapshot = []

    # Scan key directories for artifacts
    scan_dirs = [
        "outputs", "methods", "src", "paper", "figures",
        "planning", "data", "inputs", "docs/meetings",
    ]

    for dir_name in scan_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue

        for fpath in dir_path.rglob("*"):
            if not fpath.is_file():
                continue
            if fpath.suffix not in ('.md', '.json', '.csv', '.py', '.txt', '.png', '.yaml'):
                continue

            rel_path = str(fpath.relative_to(PROJECT_ROOT))
            snapshot.append({
                "path": rel_path,
                "hash": _file_hash(fpath),
                "size": fpath.stat().st_size,
                "mtime": datetime.fromtimestamp(fpath.stat().st_mtime).isoformat(),
            })

    return snapshot


def _snapshot_workflow_state() -> Dict[str, Any]:
    """Snapshot current workflow state from StateManager."""
    try:
        from state_manager import StateManager
        sm = StateManager()
        return sm.get_workflow_state()
    except ImportError:
        return {"error": "StateManager not available"}


# ═══════════════════════════════════════════════════════════════
# Rollback
# ═══════════════════════════════════════════════════════════════

def rollback_to_checkpoint(stage_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """Rollback to a specific checkpoint.

    Steps:
    1. Load checkpoint
    2. Verify checkpoint integrity
    3. Identify artifacts that changed after checkpoint
    4. If dry_run: report what would change
    5. If not dry_run: restore workflow state, flag stale artifacts

    Args:
        stage_id: Stage to rollback to
        dry_run: If True, only report what would change

    Returns:
        Rollback result dict
    """
    cp_file = CHECKPOINT_DIR / f"{stage_id}_checkpoint.json"
    if not cp_file.exists():
        return {"status": "error", "msg": f"No checkpoint found for {stage_id}"}

    checkpoint = json.loads(cp_file.read_text(encoding="utf-8"))

    # Verify checkpoint integrity
    stored_hash = checkpoint.get("hash", "")
    verify_cp = dict(checkpoint)
    del verify_cp["hash"]
    computed_hash = hashlib.sha256(
        json.dumps(verify_cp, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]

    if stored_hash and stored_hash != computed_hash:
        return {
            "status": "error",
            "msg": f"Checkpoint integrity check failed (stored={stored_hash}, computed={computed_hash})",
        }

    # Identify changed artifacts
    current_artifacts = _snapshot_artifacts()
    checkpoint_artifacts = {a["path"]: a for a in checkpoint.get("artifact_snapshot", [])}

    changed = []
    new_files = []
    deleted = []

    for artifact in current_artifacts:
        path = artifact["path"]
        if path in checkpoint_artifacts:
            if artifact["hash"] != checkpoint_artifacts[path]["hash"]:
                changed.append({
                    "path": path,
                    "checkpoint_hash": checkpoint_artifacts[path]["hash"],
                    "current_hash": artifact["hash"],
                })
        else:
            new_files.append(path)

    for path in checkpoint_artifacts:
        if not any(a["path"] == path for a in current_artifacts):
            deleted.append(path)

    # Identify stages to re-run
    stages_to_redo = _get_downstream_stages(stage_id)

    result = {
        "status": "dry_run" if dry_run else "rolled_back",
        "stage_id": stage_id,
        "checkpoint_created_at": checkpoint.get("created_at"),
        "changed_artifacts": changed,
        "new_files_since_checkpoint": new_files,
        "deleted_files_since_checkpoint": deleted,
        "stages_to_redo": stages_to_redo,
    }

    if not dry_run:
        # Restore workflow state
        workflow_snapshot = checkpoint.get("workflow_snapshot", {})
        if workflow_snapshot and "error" not in workflow_snapshot:
            try:
                from state_manager import StateManager
                sm = StateManager()
                sm.update_workflow_state(workflow_snapshot)
                result["workflow_restored"] = True
            except ImportError:
                result["workflow_restored"] = False
                result["workflow_error"] = "StateManager not available"

        # Mark downstream stages as needs_redo
        try:
            from state_manager import StateManager
            sm = StateManager()
            for sid in stages_to_redo:
                sm.set_stage_status(sid, "needs_redo")
            result["stages_marked_redo"] = stages_to_redo
        except ImportError:
            pass

        # Log rollback
        _log_rollback(stage_id, result)

    return result


def _get_downstream_stages(stage_id: str) -> List[str]:
    """Get all stages downstream of a given stage."""
    from context_bridge import STAGE_DEPS

    downstream = []
    for sid, deps in STAGE_DEPS.items():
        if stage_id in deps:
            downstream.append(sid)
            # Recursively get downstream of downstream
            downstream.extend(_get_downstream_stages(sid))

    return list(set(downstream))


def _log_rollback(stage_id: str, result: Dict[str, Any]):
    """Log rollback event."""
    log = {}
    if ROLLBACK_LOG.exists():
        try:
            log = json.loads(ROLLBACK_LOG.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log = {"rollbacks": []}

    if "rollbacks" not in log:
        log["rollbacks"] = []

    log["rollbacks"].append({
        "stage_id": stage_id,
        "timestamp": _now(),
        "changed_artifacts": len(result.get("changed_artifacts", [])),
        "stages_to_redo": result.get("stages_to_redo", []),
    })

    ROLLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    ROLLBACK_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════
# Resume
# ═══════════════════════════════════════════════════════════════

def resume_from_checkpoint(stage_id: str) -> Dict[str, Any]:
    """Resume execution from a checkpoint.

    Determines what needs to be re-done based on the checkpoint
    and current state.

    Args:
        stage_id: Stage to resume from

    Returns:
        Resume plan dict
    """
    cp_file = CHECKPOINT_DIR / f"{stage_id}_checkpoint.json"
    if not cp_file.exists():
        return {"status": "error", "msg": f"No checkpoint found for {stage_id}"}

    checkpoint = json.loads(cp_file.read_text(encoding="utf-8"))

    # Check which artifacts are still valid
    artifact_snapshot = checkpoint.get("artifact_snapshot", [])
    valid_artifacts = []
    invalid_artifacts = []

    for artifact in artifact_snapshot:
        path = PROJECT_ROOT / artifact["path"]
        if path.exists():
            current_hash = _file_hash(path)
            if current_hash == artifact["hash"]:
                valid_artifacts.append(artifact["path"])
            else:
                invalid_artifacts.append({
                    "path": artifact["path"],
                    "reason": "hash_changed",
                })
        else:
            invalid_artifacts.append({
                "path": artifact["path"],
                "reason": "file_missing",
            })

    return {
        "status": "resume_plan",
        "stage_id": stage_id,
        "checkpoint_created_at": checkpoint.get("created_at"),
        "valid_artifacts": len(valid_artifacts),
        "invalid_artifacts": invalid_artifacts,
        "agent_results": checkpoint.get("agent_results", {}),
        "instruction": (
            f"Resume from {stage_id} checkpoint ({checkpoint.get('created_at')}). "
            f"{len(valid_artifacts)} artifacts still valid, "
            f"{len(invalid_artifacts)} need regeneration. "
            f"Re-execute agents whose outputs are invalid."
        ),
    }


# ═══════════════════════════════════════════════════════════════
# List & Verify
# ═══════════════════════════════════════════════════════════════

def list_checkpoints() -> Dict[str, Any]:
    """List all available checkpoints."""
    _ensure_dirs()

    checkpoints = []
    for cp_file in sorted(CHECKPOINT_DIR.glob("*_checkpoint.json")):
        try:
            cp = json.loads(cp_file.read_text(encoding="utf-8"))
            checkpoints.append({
                "stage_id": cp.get("stage_id"),
                "meeting_id": cp.get("meeting_id"),
                "created_at": cp.get("created_at"),
                "hash": cp.get("hash"),
                "artifacts": len(cp.get("artifact_snapshot", [])),
                "agents": len(cp.get("agent_results", {})),
            })
        except (json.JSONDecodeError, OSError):
            checkpoints.append({
                "stage_id": cp_file.stem.replace("_checkpoint", ""),
                "error": "corrupted",
            })

    return {
        "total": len(checkpoints),
        "checkpoints": checkpoints,
    }


def verify_checkpoint(stage_id: str) -> Dict[str, Any]:
    """Verify checkpoint integrity and artifact availability."""
    cp_file = CHECKPOINT_DIR / f"{stage_id}_checkpoint.json"
    if not cp_file.exists():
        return {"status": "error", "msg": f"No checkpoint found for {stage_id}"}

    checkpoint = json.loads(cp_file.read_text(encoding="utf-8"))

    # Verify hash
    stored_hash = checkpoint.get("hash", "")
    verify_cp = dict(checkpoint)
    if "hash" in verify_cp:
        del verify_cp["hash"]
    computed_hash = hashlib.sha256(
        json.dumps(verify_cp, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]

    hash_ok = stored_hash == computed_hash if stored_hash else None

    # Verify artifacts
    missing = []
    changed = []
    ok = []

    for artifact in checkpoint.get("artifact_snapshot", []):
        path = PROJECT_ROOT / artifact["path"]
        if not path.exists():
            missing.append(artifact["path"])
        elif _file_hash(path) != artifact["hash"]:
            changed.append(artifact["path"])
        else:
            ok.append(artifact["path"])

    return {
        "status": "verified",
        "stage_id": stage_id,
        "hash_integrity": "ok" if hash_ok else ("failed" if hash_ok is False else "no_hash"),
        "artifacts_total": len(checkpoint.get("artifact_snapshot", [])),
        "artifacts_ok": len(ok),
        "artifacts_changed": len(changed),
        "artifacts_missing": len(missing),
        "changed_files": changed[:20],
        "missing_files": missing[:20],
    }


def cleanup_checkpoints(before_stage: Optional[str] = None) -> Dict[str, Any]:
    """Remove old checkpoints.

    Args:
        before_stage: Remove checkpoints for stages before this one

    Returns:
        Cleanup result
    """
    _ensure_dirs()

    removed = []
    kept = []

    for cp_file in CHECKPOINT_DIR.glob("*_checkpoint.json"):
        if before_stage:
            # Parse stage order from context_bridge
            try:
                from context_bridge import STAGE_DEPS
                stage_order = list(STAGE_DEPS.keys())
                cp_stage = cp_file.stem.replace("_checkpoint", "")
                if cp_stage in stage_order and before_stage in stage_order:
                    if stage_order.index(cp_stage) < stage_order.index(before_stage):
                        cp_file.unlink()
                        removed.append(cp_file.name)
                        continue
            except ImportError:
                pass

        kept.append(cp_file.name)

    return {
        "status": "completed",
        "removed": removed,
        "kept": kept,
    }


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="RecoveryManager v1.0 - 故障恢复与检查点管理"
    )
    sub = p.add_subparsers(dest="command")

    # checkpoint
    pcp = sub.add_parser("checkpoint", help="Create checkpoint")
    pcp.add_argument("--stage-id", required=True)
    pcp.add_argument("--meeting-id", default=None)

    # rollback
    prb = sub.add_parser("rollback", help="Rollback to checkpoint")
    prb.add_argument("--stage-id", required=True)
    prb.add_argument("--dry-run", action="store_true")

    # resume
    prs = sub.add_parser("resume", help="Resume from checkpoint")
    prs.add_argument("--stage-id", required=True)

    # list
    sub.add_parser("list", help="List all checkpoints")

    # verify
    pv = sub.add_parser("verify", help="Verify checkpoint integrity")
    pv.add_argument("--stage-id", required=True)

    # cleanup
    pcl = sub.add_parser("cleanup", help="Remove old checkpoints")
    pcl.add_argument("--before", default=None)

    args = p.parse_args()

    if args.command == "checkpoint":
        result = create_checkpoint(args.stage_id, args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "rollback":
        result = rollback_to_checkpoint(args.stage_id, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "resume":
        result = resume_from_checkpoint(args.stage_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "list":
        result = list_checkpoints()
        print(f"\n{'=' * 60}")
        print(f"  Checkpoints ({result['total']} total)")
        print(f"{'=' * 60}")
        for cp in result["checkpoints"]:
            if "error" in cp:
                print(f"  ✘ {cp['stage_id']:<25s} CORRUPTED")
            else:
                print(f"  ✔ {cp['stage_id']:<25s} {cp['created_at']}  "
                      f"({cp['artifacts']} artifacts, {cp['agents']} agents)")
        print(f"{'=' * 60}\n")

    elif args.command == "verify":
        result = verify_checkpoint(args.stage_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "cleanup":
        result = cleanup_checkpoints(args.before)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
