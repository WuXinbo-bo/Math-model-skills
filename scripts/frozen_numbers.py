#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frozen Numbers Convention - Immutable Numerical Snapshots
=========================================================

Numbers flow: code -> results -> paper. Without a freeze layer,
a bug fix in code silently shifts paper numbers.

This module implements the Frozen Numbers Convention from
KyrieZhang329/MathModeling-skills:

- freeze(): Create an immutable snapshot of key numerical results
- verify(): Check that current results match the frozen snapshot
- defrost(): Mark specific numbers for revision (write intent first)
- history(): Show all freeze/defrost events

Key rule: NO numerical claim enters the paper until frozen_numbers.json
exists and is newer than all source files.

Usage:
  python frozen_numbers.py freeze --subquestion Q1 --source results/Q1/
  python frozen_numbers.py verify --subquestion Q1
  python frozen_numbers.py defrost --subquestion Q1 --fields "d,sigma"
  python frozen_numbers.py history --subquestion Q1
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()
FREEZE_DIR = WORKSPACE / "frozen"
FREEZE_FILE = "frozen_numbers.json"
FREEZE_LOG = "freeze_change_log.md"


def get_freeze_path(subquestion):
    return FREEZE_DIR / subquestion / FREEZE_FILE


def get_log_path(subquestion):
    return FREEZE_DIR / subquestion / FREEZE_LOG


def compute_file_hash(filepath):
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def compute_source_hashes(source_dir):
    hashes = {}
    if source_dir.exists():
        for f in sorted(source_dir.rglob("*")):
            if f.is_file() and f.suffix in (".py", ".m", ".json", ".csv", ".txt", ".md", ".ipynb"):
                hashes[str(f.relative_to(source_dir))] = compute_file_hash(f)
    return hashes


def cmd_freeze(args):
    subquestion = args.subquestion
    source_dir = Path(args.source) if args.source else Path("results") / subquestion
    numbers = {}

    result_json = source_dir / "reports" / "run_summary.json"
    if result_json.exists():
        with open(result_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        numbers["results"] = data

    source_hashes = compute_source_hashes(source_dir)

    freeze_record = {
        "subquestion": subquestion,
        "frozen_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_dir": str(source_dir),
        "source_hashes": source_hashes,
        "numbers": numbers,
        "defrosts": [],
        "version": 1,
    }

    freeze_dir = FREEZE_DIR / subquestion
    freeze_dir.mkdir(parents=True, exist_ok=True)

    freeze_path = freeze_dir / FREEZE_FILE
    with open(freeze_path, "w", encoding="utf-8") as f:
        json.dump(freeze_record, f, indent=2, ensure_ascii=False)

    log_path = freeze_dir / FREEZE_LOG
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n## Freeze v{} - {}\n".format(freeze_record["version"], freeze_record["frozen_at"]))
        f.write("- Source: {}\n".format(source_dir))
        f.write("- Hashes: {} files\n".format(len(source_hashes)))
        if numbers:
            f.write("- Numbers frozen: {}\n".format(json.dumps(list(numbers.keys()))))

    print("[FROZEN] {}: {}".format(subquestion, freeze_path))
    print("  Source hashes: {} files".format(len(source_hashes)))
    print("  [RULE] No numerical claim enters paper before frozen_numbers.json exists.")


def cmd_verify(args):
    subquestion = args.subquestion
    freeze_path = get_freeze_path(subquestion)

    if not freeze_path.exists():
        print("[VERIFY] {}: NO FREEZE - run freeze first".format(subquestion))
        sys.exit(1)

    with open(freeze_path, "r", encoding="utf-8") as f:
        frozen = json.load(f)

    source_dir = Path(frozen["source_dir"])
    current_hashes = compute_source_hashes(source_dir)
    frozen_hashes = frozen.get("source_hashes", {})

    changed = []
    missing = []
    for fpath, fhash in frozen_hashes.items():
        if fpath not in current_hashes:
            missing.append(fpath)
        elif current_hashes[fpath] != fhash:
            changed.append((fpath, fhash, current_hashes[fpath]))

    is_consistent = not (changed or missing)

    print("[VERIFY] {}: {}".format(subquestion, "CONSISTENT" if is_consistent else "DRIFT"))
    if changed:
        print("  CHANGED ({}):".format(len(changed)))
        for fpath, oh, nh in changed:
            print("    - {}: {} -> {}".format(fpath, oh, nh))
    if missing:
        print("  MISSING ({}):".format(len(missing)))
        for fpath in missing:
            print("    - {}".format(fpath))

    if not is_consistent and args.strict:
        print("\n  [BLOCKED] Paper numbers may be stale.")
        sys.exit(1)

    sys.exit(0)


def cmd_defrost(args):
    subquestion = args.subquestion
    freeze_path = get_freeze_path(subquestion)

    if not freeze_path.exists():
        print("[DEFROST] {}: No freeze exists.".format(subquestion))
        sys.exit(1)

    with open(freeze_path, "r", encoding="utf-8") as f:
        frozen = json.load(f)

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else ["all"]
    reason = args.reason or "Manual defrost"

    defrost_entry = {
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fields": fields,
        "reason": reason,
        "previous_version": frozen["version"],
    }
    frozen.setdefault("defrosts", []).append(defrost_entry)
    frozen["version"] += 1
    frozen["status"] = "defrosted"

    with open(freeze_path, "w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2, ensure_ascii=False)

    log_path = get_log_path(subquestion)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n## Defrost v{} - {}\n".format(frozen["version"], defrost_entry["at"]))
        f.write("- Fields: {}\n".format(fields))
        f.write("- Reason: {}\n".format(reason))
        f.write("- [NEXT] Re-freeze after changes.\n")

    print("[DEFROSTED] {} v{}: {}".format(subquestion, frozen["version"], fields))


def cmd_refreeze(args):
    """Re-freeze after changes: clear STALE status, bump version, write log."""
    subquestion = args.subquestion
    freeze_path = get_freeze_path(subquestion)

    if not freeze_path.exists():
        print("[RE-FREEZE] {}: No freeze exists. Run freeze first.".format(subquestion))
        sys.exit(1)

    with open(freeze_path, "r", encoding="utf-8") as f:
        frozen = json.load(f)

    source_dir = args.source or frozen.get("source_dir", "")
    source_dir = Path(source_dir)

    # Re-compute hashes
    new_hashes = compute_source_hashes(source_dir)
    frozen["source_hashes"] = new_hashes
    frozen["frozen_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frozen["version"] = frozen.get("version", 0) + 1
    frozen["status"] = "frozen"
    frozen.pop("stale_detected_at", None)
    frozen.pop("stale_reason", None)

    with open(freeze_path, "w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2, ensure_ascii=False)

    # Log the re-freeze
    log_path = get_log_path(subquestion)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n## Re-Freeze v{} - {}\n".format(frozen["version"], frozen["frozen_at"]))
        f.write("- Source: {}\n".format(source_dir))
        f.write("- Hashes: {} files\n".format(len(new_hashes)))
        f.write("- [OK] Frozen snapshot updated. Paper numbers can be trusted again.\n")

    print("[RE-FROZEN] {} v{}: {}".format(subquestion, frozen["version"], freeze_path))
    print("  Source hashes: {} files".format(len(new_hashes)))
    print("  [OK] Snapshot is now CURRENT. Paper numbers trusted.")


def cmd_history(args):
    subquestion = args.subquestion
    log_path = get_log_path(subquestion)
    if not log_path.exists():
        print("[HISTORY] {}: No history.".format(subquestion))
        sys.exit(1)
    print("[HISTORY] {}".format(subquestion))
    print(log_path.read_text(encoding="utf-8"))


def cmd_status(args):
    if not FREEZE_DIR.exists():
        print("[FREEZE] No frozen numbers.")
        sys.exit(0)
    for qdir in sorted(FREEZE_DIR.iterdir()):
        if qdir.is_dir():
            fp = qdir / FREEZE_FILE
            if fp.exists():
                with open(fp, "r", encoding="utf-8") as f:
                    frozen = json.load(f)
                st = frozen.get("status", "frozen")
                if st == "stale":
                    icon = "[STALE]"
                    detail = frozen.get("stale_reason", "unknown cause")
                    print("  {} {} v{} ({}) - {}".format(icon, qdir.name, frozen["version"], frozen["frozen_at"], detail))
                elif st == "defrosted":
                    icon = "[THAWED]"
                    print("  {} {} v{} ({})".format(icon, qdir.name, frozen["version"], frozen["frozen_at"]))
                else:
                    icon = "[FROZEN]"
                    print("  {} {} v{} ({})".format(icon, qdir.name, frozen["version"], frozen["frozen_at"]))
            else:
                print("  [EMPTY] {}".format(qdir.name))


def main():
    parser = argparse.ArgumentParser(description="Frozen Numbers Manager")
    sub = parser.add_subparsers(dest="command")

    pf = sub.add_parser("freeze")
    pf.add_argument("--subquestion", "-q", required=True)
    pf.add_argument("--source", "-s")

    pv = sub.add_parser("verify")
    pv.add_argument("--subquestion", "-q", required=True)
    pv.add_argument("--strict", action="store_true")

    pd = sub.add_parser("defrost")
    pd.add_argument("--subquestion", "-q", required=True)
    pd.add_argument("--fields")
    pd.add_argument("--reason")

    ph = sub.add_parser("history")
    ph.add_argument("--subquestion", "-q", required=True)

    prf = sub.add_parser("re-freeze", help="Re-freeze after changes (clear STALE, update hashes)")
    prf.add_argument("--subquestion", "-q", required=True)
    prf.add_argument("--source", "-s")

    ps = sub.add_parser("status")

    args = parser.parse_args()
    if args.command == "freeze":
        cmd_freeze(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "defrost":
        cmd_defrost(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "re-freeze":
        cmd_refreeze(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()