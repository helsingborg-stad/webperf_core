#!/usr/bin/env python3
"""Merge completed one-test Webperf outputs into one publishable trend result."""

from __future__ import annotations

import argparse
import gettext
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helpers.models import Rating, SiteTests
from helpers.setting_helper import set_runtime_config_only
from tests.utils import calculate_rating, merge_dicts, sort_testresult_issues


def read_completed_results(folder: Path) -> dict:
    merged: dict = {}
    for file in sorted(folder.glob("*.json")):
        content = json.loads(file.read_text(encoding="utf-8"))
        for test in content.get("tests", []):
            if isinstance(test, dict) and isinstance(test.get("data"), dict):
                merged = merge_dicts(merged, test["data"], False, False)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--language", default="sv")
    args = parser.parse_args()

    set_runtime_config_only("general.language", args.language)
    set_runtime_config_only("general.review.improve-only", False)
    set_runtime_config_only("general.review.details", True)
    translation = gettext.translation(
        "webperf-core", localedir="locales", languages=[args.language]
    ).gettext

    data = read_completed_results(args.input_dir)
    sort_testresult_issues(data)
    rating = calculate_rating(translation, Rating(translation, False), data)
    result = SiteTests(0, -1, rating, datetime.now(), data).todata()[0]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"tests": [result]}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
