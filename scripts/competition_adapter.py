#!/usr/bin/env python3
"""竞赛适配器 - Competition Adapter"""

import json
from pathlib import Path

PROFILES = {
    "CUMCM": {"lang": "zh", "pages": 20, "abs_words": (400,550), "refs": 6, "table": "三线表"},
    "51MCM": {"lang": "zh", "pages": 15, "abs_words": (300,450), "refs": 5, "table": "简化三线表"},
    "MCM": {"lang": "en", "pages": 25, "abs_words": (300,400), "refs": 8, "table": "APA"},
    "ICM": {"lang": "en", "pages": 25, "abs_words": (300,400), "refs": 8, "table": "APA"}
}

def get_profile(comp):
    return PROFILES.get(comp, PROFILES["CUMCM"])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition", default="CUMCM")
    args = parser.parse_args()
    print(json.dumps(get_profile(args.competition), ensure_ascii=False, indent=2))
