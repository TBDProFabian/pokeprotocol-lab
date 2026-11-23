#!/usr/bin/env python3
"""Resolve trusted workflow_dispatch inputs or repository-owner issues to safe arguments."""
import json
import os
from pathlib import Path
import re

VALID_N = {50, 100, 300}
VALID_MODE = {"field", "headtohead", "both"}
VALID_PLAYER = {"heuristic", "search"}

def parse_config(event_name: str, event: dict, dispatch: dict) -> dict:
    cfg = {"battles": "100", "mode": "both", "player": "heuristic", "seed": "pokeprotocol-001"}
    if event_name == "workflow_dispatch":
        cfg.update({k: str(v) for k, v in dispatch.items() if k in cfg and v not in (None, "")})
    elif event_name == "issues":
        issue = event.get("issue", {})
        if not issue.get("title", "").startswith("POKEPROTOCOL RUN"):
            raise ValueError("Issue title must start with POKEPROTOCOL RUN")
        for line in str(issue.get("body") or "").splitlines():
            match = re.fullmatch(r"\s*(battles|mode|player|seed)\s*[:=]\s*(.*?)\s*", line, re.IGNORECASE)
            if match:
                cfg[match.group(1).lower()] = match.group(2)
    else:
        raise ValueError("Unsupported trigger")
    try:
        cfg["battles"] = int(cfg["battles"])
    except (ValueError, TypeError) as exc:
        raise ValueError("Battles must be an integer") from exc
    if cfg["battles"] not in VALID_N:
        raise ValueError(f"battles must be one of {sorted(VALID_N)}")
    if cfg["mode"] not in VALID_MODE:
        raise ValueError(f"mode must be one of {sorted(VALID_MODE)}")
    if cfg["player"] not in VALID_PLAYER:
        raise ValueError(f"player must be one of {sorted(VALID_PLAYER)}")
    if cfg["player"] == "search" and cfg["battles"] > 50:
        raise ValueError("Search lookahead AI is expensive; choose 50 battles")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", cfg["seed"]):
        raise ValueError("seed must be 1-48 ASCII letters/numbers/_/-")
    return cfg

def main() -> None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    event = json.loads(Path(event_path).read_text()) if event_path and Path(event_path).exists() else {}
    env_config = {k: os.environ.get("DISPATCH_" + k.upper()) for k in ("battles", "mode", "player", "seed")}
    cfg = parse_config(os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch"), event, env_config)
    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as out:
            for k, v in cfg.items():
                out.write(f"{k}={v}\n")
    print("Poképrotocol request:", json.dumps(cfg))

if __name__ == "__main__":
    main()
