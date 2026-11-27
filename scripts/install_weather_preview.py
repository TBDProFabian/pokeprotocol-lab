#!/usr/bin/env python3
"""Install a versioned, fail-closed weather-aware charging preview patch.

Patch touches only the team-preview scoring policy in the pinned external
Champions Lab engine. Never modifies Showdown turn resolution or battle rules.
A pinned source anchor prevents silently patching an incompatible engine.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from evolve import ENGINE, ENGINE_SHA

SOURCE = ENGINE / "src/engine/policy/preview.ts"
MARKER = "POKEPROTOCOL_WEATHER_PREVIEW_V2"
INSERT_AFTER = "export function unitOf(dex: Dex, set: PokemonSet, oppSide: boolean): Unit {"
HIT = "function bestHit(dex: Dex, a: Unit, d: Unit): {frac: number, spread: boolean} {"
DAMAGE = "const f = (avg / r.defenderMaxHP) * acc * (mv.spread ? 1.25 : 1); // a spread hit also lands on the partner"
DUEL = "export function duel(dex: Dex, a: Unit, d: Unit, cache: Map<string, number>): number {"
KEY = "const key = a.key + '>' + d.key;"
BOTH = "const ha = bestHit(dex, a, d).frac, hd = bestHit(dex, d, a).frac;"
BRING = """function bringValue(dex: Dex, mine: Unit[], theirs: Unit[], cache: Map<string, number>): number {
\tlet s = 0;
\tfor (const a of mine) for (const d of theirs) s += duel(dex, a, d, cache);"""
LEAD = "oppWeight[j] * duel(dex, unit, t, cache)"

HELPERS = """
// POKEPROTOCOL_WEATHER_PREVIEW_V2: estimated weather for a selected four-v-four.
// Prediction, not oracle access. Weather may not activate if a setter stays on
// the bench, arrives late, or loses a weather contest. Under uncertain leads,
// we assume any brought setter has approximately a one-half opportunity to
// activate, then split control among competing setters.
export interface WeatherOdds {rain: number; sun: number}
function weatherFromAbility(ability: string): string {
    const id = toID(ability);
    if (id === 'drizzle' || id === 'primordialsea') return 'rain';
    if (id === 'drought' || id === 'desolateland') return 'sun';
    if (id === 'sandstream') return 'sand';
    if (id === 'snowwarning') return 'snow';
    return '';
}
export function estimateWeather(dex: Dex, mine: Unit[], theirs: Unit[]): WeatherOdds {
    const weight: Record<string, number> = {rain: 0, sun: 0, sand: 0, snow: 0};
    for (const mon of [...mine, ...theirs]) {
        const base = weatherFromAbility(mon.ability);
        if (base) weight[base] += 1;
        // Mega weather competes for the single Mega slot and activates only
        // when actually Mega evolved. Discount it relative to base Drizzle.
        if (mon.megaCapable) {
            const megaAbility = dex.getSpecies(mon.species)?.abilities['0'] || '';
            const megaWeather = weatherFromAbility(megaAbility);
            if (megaWeather && megaWeather !== base) weight[megaWeather] += 0.35;
        }
        for (const move of mon.moves) {
            if (move === 'raindance') weight.rain += 0.2;
            else if (move === 'sunnyday') weight.sun += 0.2;
            else if (move === 'sandstorm') weight.sand += 0.2;
            else if (move === 'snowscape') weight.snow += 0.2;
        }
    }
    const total = Object.values(weight).reduce((a, b) => a + b, 0);
    if (!total) return {rain: 0, sun: 0};
    const active = 1 - Math.pow(0.5, total);
    return {rain: active * weight.rain / total, sun: active * weight.sun / total};
}
/** Cheap tempo estimate; battle execution still uses actual weather/rules. */
export function chargeTempo(move: {id: string; flags: string[]}, item: string, w: WeatherOdds): number {
    if (!move.flags.includes('charge') || toID(item) === 'powerherb') return 1;
    let instant = 0;
    if (move.id === 'electroshot') instant = w.rain;
    else if (move.id === 'solarbeam' || move.id === 'solarblade') instant = w.sun;
    return 0.45 + 0.55 * Math.max(0, Math.min(1, instant));
}
"""

def replace_exact(text: str, old: str, new: str) -> str:
    n=text.count(old)
    if n != 1:
        raise RuntimeError(f"Expected one pinned source anchor (got {n}): {old[:65]!r}")
    return text.replace(old,new,1)

def patched(text: str) -> str:
    if MARKER in text:
        raise RuntimeError("Weather-aware preview already installed; refusing double patch")
    # Mark generated helper boundary, place just before the best-hit routine.
    text=replace_exact(text,HIT,HELPERS+"\n"+HIT.replace(
        "d: Unit):", "d: Unit, w: WeatherOdds):"))
    text=replace_exact(text,DAMAGE,
        "const f = (avg / r.defenderMaxHP) * acc * (mv.spread ? 1.25 : 1) * chargeTempo(mv, a.set.item, w); // partner hit approximated")
    text=replace_exact(text,DUEL,DUEL.replace("): number {",", w: WeatherOdds = {rain: 0, sun: 0}): number {"))
    text=replace_exact(text,KEY,
        "const key = a.key + '>' + d.key + '|rain:' + w.rain.toFixed(2) + '|sun:' + w.sun.toFixed(2);")
    text=replace_exact(text,BOTH,
        "const ha = bestHit(dex, a, d, w).frac, hd = bestHit(dex, d, a, w).frac;")
    text=replace_exact(text,BRING,
        """function bringValue(dex: Dex, mine: Unit[], theirs: Unit[], cache: Map<string, number>): number {
\tconst w = estimateWeather(dex, mine, theirs);
\tlet s = 0;
\tfor (const a of mine) for (const d of theirs) s += duel(dex, a, d, cache, w);""")
    text=replace_exact(text,LEAD,
        "oppWeight[j] * duel(dex, unit, t, cache, estimateWeather(dex, bring.map(i => mine[i]), theirs))")
    return text

def install() -> dict:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing pinned policy source {SOURCE}")
    source=SOURCE.read_text(encoding="utf8")
    output=patched(source)
    SOURCE.write_text(output,encoding="utf8")
    return {"patch":MARKER,"engine_commit":ENGINE_SHA,
            "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
            "patched_sha256":hashlib.sha256(output.encode()).hexdigest(),
            "policy_path":str(SOURCE.relative_to(ENGINE)),
            "limits":"Heuristic bring-four weather estimate; does not predict leads or order of weather activation"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path)
    args=p.parse_args()
    result=install()
    print(json.dumps(result,indent=2))
    if args.manifest:
        args.manifest.parent.mkdir(parents=True,exist_ok=True)
        args.manifest.write_text(json.dumps(result,indent=2),encoding="utf8")
