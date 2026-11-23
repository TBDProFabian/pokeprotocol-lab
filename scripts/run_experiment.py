#!/usr/bin/env python3
"""Run real Champions Lab simulations; fail without reporting fabricated results."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "champions-lab"
TEAMS = {n: ROOT / "teams" / f"{n}.txt" for n in ("incineroar", "sneasler")}
OUT = ROOT / "reports"

def run_cmd(args, label: str) -> dict:
    p = subprocess.run(["node", "src/cli/lab.ts", *[str(v) for v in args]],
                       cwd=LAB, text=True, capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError(f"{label} failed (exit {p.returncode}):\n{p.stderr[-2500:]}\n{p.stdout[-2500:]}")
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{label} did not return valid JSON: {p.stdout[:900]}") from e
    if not isinstance(data, dict) or data.get("error"):
        raise RuntimeError(f"{label} returned an engine error: {data}")
    return data

def save_json(name: str, data: dict) -> None:
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def pct(value):
    return f"{float(value)*100:.1f}%" if value is not None else "n/a"

def summarize(runs: list[dict], manifest: dict, error=None) -> str:
    lines = ["## Poképrotocol cloud test", "",
             "**Source:** Champions Lab simulator, not live player matches.",
             f"**Settings:** {manifest['battles']} battles/test, `{manifest['player']}` AI, seed `{manifest['seed']}`.",
             f"**Field:** {manifest.get('field_built_at') or 'not checked'} (historical snapshot, not a live meta feed).", ""]
    if error:
        lines += ["**Result:** Simulation failed; no win rates are claimed.", "", "```", error[:2000], "```", ""]
    elif runs:
        lines += ["| Test | W | L | T | N | Win rate | 95% CI |", "|---|---:|---:|---:|---:|---:|---:|"]
        for run in runs:
            d = run["result"]
            ci = d.get("ci95", [None, None])
            lines.append(f"| {run['name']} | {d.get('wins','?')} | {d.get('losses','?')} | {d.get('ties','?')} | {d.get('n','?')} | {pct(d.get('rate'))} | {pct(ci[0])}–{pct(ci[1])} |")
        lines += ["", "Simulated outcomes depend on the engine's AI and historic opponents, not human tournament win rates.",
                  "Overlapping confidence intervals are inconclusive, and matched field seeds reduce but do not eliminate sampling noise.", ""]
    else:
        lines += ["No simulation results available.", ""]
    url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get("GITHUB_REPOSITORY","owner/repo") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID","")
    lines += [f"[Open run and downloadable JSON reports]({url})", ""]
    return "\n".join(lines)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    battles = int(os.environ.get("POKEPROTOCOL_N", "100"))
    mode = os.environ.get("POKEPROTOCOL_MODE", "both")
    player = os.environ.get("POKEPROTOCOL_PLAYER", "heuristic")
    seed = os.environ.get("POKEPROTOCOL_SEED", "pokeprotocol-001")
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(),
                "battles": battles, "mode": mode, "player": player, "seed": seed,
                "engine_git_commit": "09d59984631dd2a45fb21700970c65ee24cf7d0f",
                "team_sha256": {n: hashlib.sha256(p.read_bytes()).hexdigest() for n,p in TEAMS.items()}}
    runs = []
    try:
        if not (LAB / "src/cli/lab.ts").exists():
            raise RuntimeError("Engine not installed in champions-lab/")
        for n, path in TEAMS.items():
            result = run_cmd(["validate", path], f"validate {n}")
            save_json(f"validate_{n}.json", result)
            if result.get("ok") is not True:
                raise RuntimeError(f"Team {n} invalid: {result.get('problems',[])}")
        if mode in ("field", "both"):
            for n, path in TEAMS.items():
                result = run_cmd(["field", path, "--n", battles, "--player", player, "--seed", seed], f"field {n}")
                save_json(f"field_{n}.json", result)
                if result.get("winRate",{}).get("n") != battles:
                    raise RuntimeError(f"{n} field result count mismatch")
                manifest["field_built_at"] = result.get("provenance",{}).get("field",{}).get("builtAt")
                runs.append({"name":f"{n} vs field", "result":result["winRate"], "provenance":result.get("provenance")})
        if mode in ("headtohead", "both"):
            result = run_cmd(["sim", TEAMS["incineroar"], TEAMS["sneasler"], "--n", battles,
                              "--player", player, "--seed", seed, "--logs", 2], "head-to-head")
            save_json("headtohead.json", result)
            if result.get("winRateA",{}).get("n") != battles:
                raise RuntimeError("Head-to-head result count mismatch")
            runs.append({"name":"Incineroar vs Sneasler (Incineroar side)", "result":result["winRateA"],
                         "provenance":result.get("provenance")})
        manifest["status"] = "completed"
        save_json("manifest.json", manifest)
        save_json("summary.json", {"manifest":manifest,"tests":runs})
        (OUT / "summary.md").write_text(summarize(runs, manifest), encoding="utf-8")
        print("Completed", json.dumps({"tests": len(runs), "manifest":manifest}))
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        save_json("manifest.json", manifest)
        (OUT / "summary.md").write_text(summarize(runs, manifest, str(exc)), encoding="utf-8")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
