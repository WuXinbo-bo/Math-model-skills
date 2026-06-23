#!/usr/bin/env python3
"""
setup_skills.py - Sync canonical SKILL.md to platform-specific skill directories.

This script copies the root SKILL.md (canonical source) to:
  - skills/meta-model/SKILL.md      (Claude Code entry point)
  - .agents/skills/meta-model/SKILL.md  (OpenAI Codex entry point)

Run this script whenever SKILL.md is updated to keep all platforms in sync.

Usage:
    python setup_skills.py          # Sync all platforms
    python setup_skills.py --check  # Check sync status without copying
    python setup_skills.py --clean  # Remove synced copies
"""

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Canonical source
SOURCE = PROJECT_ROOT / "SKILL.md"

# Platform targets
TARGETS = {
    "claude-code": PROJECT_ROOT / "skills" / "meta-model" / "SKILL.md",
    "codex": PROJECT_ROOT / ".agents" / "skills" / "meta-model" / "SKILL.md",
}


def check_sync():
    """Check if all targets are in sync with source."""
    if not SOURCE.exists():
        print(f"[ERROR] Source not found: {SOURCE}")
        return False

    source_content = SOURCE.read_text(encoding="utf-8")
    all_ok = True

    for platform, target in TARGETS.items():
        if not target.exists():
            print(f"[MISSING] {platform}: {target}")
            all_ok = False
        elif target.read_text(encoding="utf-8") != source_content:
            print(f"[OUTDATED] {platform}: {target}")
            all_ok = False
        else:
            print(f"[OK] {platform}: {target}")

    return all_ok


def sync_all():
    """Copy source SKILL.md to all platform targets."""
    if not SOURCE.exists():
        print(f"[ERROR] Source not found: {SOURCE}")
        sys.exit(1)

    source_content = SOURCE.read_text(encoding="utf-8")

    for platform, target in TARGETS.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source_content, encoding="utf-8")
        print(f"[SYNCED] {platform}: {target}")

    print(f"\nAll {len(TARGETS)} platform targets synced successfully.")


def clean():
    """Remove synced copies (keep reference stubs)."""
    for platform, target in TARGETS.items():
        if target.exists():
            target.unlink()
            print(f"[REMOVED] {platform}: {target}")


def main():
    if "--check" in sys.argv:
        ok = check_sync()
        sys.exit(0 if ok else 1)
    elif "--clean" in sys.argv:
        clean()
    else:
        sync_all()


if __name__ == "__main__":
    main()
