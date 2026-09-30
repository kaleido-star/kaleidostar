#!/usr/bin/env python3
"""Validate the public quote data without third-party dependencies."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"anime_official", "anime_episode_checked", "radio_segment", "fan_name"}
REQUIRED = {"id", "text", "speaker", "category", "source"}
OPTIONAL = {"lines", "episode", "context"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    data = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
    check(isinstance(data, list) and len(data) > 0, "quotes.json must be a nonempty array")
    ids, texts = set(), set()
    for index, item in enumerate(data):
        prefix = f"quotes[{index}]"
        check(isinstance(item, dict), f"{prefix} must be an object")
        check(REQUIRED <= item.keys() and item.keys() <= REQUIRED | OPTIONAL, f"{prefix}: unexpected or missing fields")
        for field in ("id", "text", "speaker"):
            value = item[field]
            check(isinstance(value, str) and value.strip() == value and value, f"{prefix}.{field}: invalid string")
            check(not any(ord(char) < 32 for char in value), f"{prefix}.{field}: control character")
        check(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["id"]) is not None, f"{prefix}.id: invalid format")
        check(len(item["text"]) <= 200, f"{prefix}.text: too long")
        check(item["id"] not in ids and item["text"] not in texts, f"{prefix}: duplicate ID or text")
        ids.add(item["id"])
        texts.add(item["text"])
        check(item["category"] in CATEGORIES, f"{prefix}.category: unknown value")
        if "lines" in item:
            lines = item["lines"]
            check(isinstance(lines, list) and len(lines) > 1 and all(isinstance(line, str) and line for line in lines), f"{prefix}.lines: invalid lines")
            check("".join(lines) == item["text"], f"{prefix}.lines: must join to text")
        if item["category"] == "anime_episode_checked":
            check(type(item.get("episode")) is int and 1 <= item["episode"] <= 51, f"{prefix}.episode: required episode number")
        else:
            check("episode" not in item, f"{prefix}.episode: only for episode-checked dialogue")
        if "context" in item:
            check(isinstance(item["context"], str) and 0 < len(item["context"]) <= 200, f"{prefix}.context: invalid string")
        source = item["source"]
        check(isinstance(source, dict) and set(source) == {"label", "url"}, f"{prefix}.source: invalid fields")
        check(isinstance(source["label"], str) and bool(source["label"].strip()), f"{prefix}.source.label: invalid string")
        check(isinstance(source["url"], str), f"{prefix}.source.url: invalid string")
        url = urlsplit(source["url"])
        check(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password, f"{prefix}.source.url: HTTPS URL required")
    print(f"Validated {len(data)} quotes")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
