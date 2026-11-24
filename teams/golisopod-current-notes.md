# Poképrotocol current Mega Golisopod team (Reg M-C)

**Active set:** [golisopod-current.txt](golisopod-current.txt)  
**Version:** Rain Wings, Archaludon **Aura Sphere**.  
**Date:** 2026-11-23. **Format:** Gen 9 Champions VGC 2026 Reg M-C; 66 Stat Points per Pokémon. **M-D unverified** until the live regulation and simulator are refreshed.

## Roster and jobs
- **Mega Golisopod**: Bug/Steel Tough Claws contact attacker, Leech Life recovery, Iron Head for Fairies, Sucker Punch to bypass its slow natural speed, Protect. 2 HP / 32 Atk / 32 Spe, Adamant.
- **Mega Salamence**: alternate Mega plus Intimidate and Tailwind even when kept in its base form; Flying Hyper Voice with Aerilate after Mega, Draco Meteor for Dragons.
- **Rillaboom**: Fake Out to buy Tailwind or rain turns; Grass coverage and priority Grassy Glide into Mega Swampert; High Horsepower into Steel types.
- **Pelipper**: Drizzle weather control, Wide Guard versus Rock Slide, Heat Wave, Make It Rain, Eruption and Muddy Water, Helping Hand for bursts.
- **Archaludon**: Stamina bulk and rain Electro Shot; **Dragon Pulse remains the Dragon STAB**; Aura Sphere adds Fighting coverage versus Kingambit, opposing Archaludon, Incineroar and Tyranitar.
- **Basculegion-F**: Swift Swim and Focus Sash special attacker; rain Muddy Water; Shadow Ball pressures Mega Gengar/Gholdengo; Ice Beam pressures opposing Dragons.

## Verified speed checkpoints
- Mega Golisopod Adamant 32 Spe: **92** natural; **184 under Tailwind**. Faster than Adamant 32 Spe Sneasler (172) and Jolly max-speed Mega Raichu X (178), but slower than Jolly max-speed Sneasler (189) and Timid Mega Gengar (200).
- Mega Salamence Timid 32 Spe: **189**, tied with Jolly max-speed Sneasler and max-speed Timid Mega Salamence.
- Basculegion-F Modest 32 Spe: **130**, or **260 under Swift Swim rain**.
- Remember: only one Mega Evolution per battle. Salamence can Intimidate and Tailwind before or without Mega Evolution; Golisopod is usually brought in back, not blindly led.

## Stacked weaknesses after Mega Evolution
Attack types that strike two of six super-effectively:
- **Fire:** Golisopod 4×, Rillaboom 2×. Preserve Drizzle, and Wide Guard against spread fire moves.
- **Electric:** Pelipper 4×, Basculegion-F 2×. Rillaboom and Archaludon are Electric-resistant switch targets.
- **Ice:** Salamence 4×, Rillaboom 2×. Golisopod resists Ice.
- **Rock:** Salamence 2×, Pelipper 2×. Pelipper Wide Guard blocks Rock Slide; position carefully into Tyranitar/Excadrill.

Do not assume Grassy Terrain halves Earthquake in Champions. It does not in the pinned engine.

## Simulation evidence
- [First rebuild bracket](https://github.com/TBDProFabian/pokeprotocol-lab/issues/7): Rain Semiroom 48.5%, benchmark rain 44.0%, Sand Pivot 38.0%, Sun-Rain Flex 37.5% over 200 field games each.
- [Second rebuild bracket](https://github.com/TBDProFabian/pokeprotocol-lab/issues/8): Rain Semiroom 49.5%, Rain Wings Snarl 48.0% over 200 field games each; separate seeds and small samples.
- [Final move and flex tune](https://github.com/TBDProFabian/pokeprotocol-lab/issues/9): Rain Wings Aura Sphere **111/200 field games = 55.5%**, Snarl **91/200 = 45.5%**, Kingambit **95/200 = 47.5%**, Incineroar **82/200 = 41.0%**. Same opponent sampling seed for that comparison. Golisopod was brought in **94.5%** of Aura Sphere field simulations.
- LAIC rain championship **six-species proxy** matchup remains poor: **20/80 = 25.0%** with heuristic AI. Gdańsk sand proxy: **53/80 = 66.2%**. These are **NOT** the champions' exact registered moves, items or Stat Points.
- The simulator's heuristic AI and inferred hidden opponent spreads limit certainty; overlap in confidence intervals means one small sample cannot prove an improvement in human win rates. Only the simulator's pinned M-C rules have been validated, not M-D.

## Play modules
- Versus opposing rain featuring Mega Swampert: keep Rillaboom's Grassy Surge and Grassy Glide available and preserve Basculegion-F's Shadow Ball for Mega Gengar; consider keeping Pelipper back if the opponent will supply rain.
- Versus sand: control Rock Slide with Pelipper's Wide Guard, use Rillaboom High Horsepower/Wood Hammer and Golisopod Iron Head, avoid losing Salamence to Rock coverage.
- Versus opposing Sun: do not expose Mega Golisopod to unmitigated Fire; use Pelipper's weather reset and Protect positioning.
- Against priority spam: Rillaboom's Fake Out helps, but there is **no Armor Tail** in this final build. Priority denial and Trick Room matchup should be revisited in M-D.

The current team is a **supported choice**, not a guaranteed champion-tier result. Next scientific task: evaluate actual, verified official top team sheets and a stronger lookahead AI once accessible, then rebuild for Regulation M-D.
