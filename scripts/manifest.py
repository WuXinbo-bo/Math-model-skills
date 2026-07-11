from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional


SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = SKILL_ROOT / "assets" / "workflow_manifest.json"
COMPETITION_PROFILES_PATH = SKILL_ROOT / "assets" / "competition_profiles.json"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_competition_profiles() -> dict[str, Any]:
    return json.loads(COMPETITION_PROFILES_PATH.read_text(encoding="utf-8"))


def competition_profile(key: str) -> dict[str, Any]:
    profiles = load_competition_profiles()
    if key not in profiles:
        raise KeyError(f"Unknown competition profile: {key}")
    return profiles[key]


def ordered_steps() -> list[dict[str, Any]]:
    return list(load_manifest()["steps"])


def find_step(identifier: str) -> Optional[dict[str, Any]]:
    ident = identifier.strip()
    for step in ordered_steps():
        if ident in {step["stage_id"], step["skill_name"]}:
            return step
    return None


def next_step(stage_id: str) -> Optional[dict[str, Any]]:
    steps = ordered_steps()
    for index, step in enumerate(steps):
        if step["stage_id"] == stage_id:
            return steps[index + 1] if index + 1 < len(steps) else None
    return None
