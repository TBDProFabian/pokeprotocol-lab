# Poképrotocol Cloud Lab 🧪

A phone-friendly cloud runner for **Pokémon Champions Regulation M-C** simulations using the open-source [Champions Lab](https://github.com/joshuamatalon/champions-lab) simulator.

## How to run

Go to **Actions → Poképrotocol cloud simulation → Run workflow**, or ask ChatGPT to open an Issue titled `POKEPROTOCOL RUN` containing `battles=50`, `mode=both`, `player=heuristic`, and `seed=first-test`.

The workflow validates the teams, runs simulated battles, and produces an artifact with the full report. The workflow uses our validated 35-day Limitless field when available, falling back to the engine's original historical field. Simulator win rates are not equivalent to tournament results.

This is an independent fan project, not affiliated with Nintendo, Game Freak or The Pokémon Company.

## Tournament database

- **Online archive:** `data/field.json`, preserving Regulation M-C history and older carry-over teams.
- **Recent simulation opponents:** `data/field-recent.json`, a 35-day window with eligible validated public Limitless team sheets. This is the default field for new simulation runs.
- **Audit:** `data/pokeprotocol-refresh.json`, including import counts, latest source event, rejects, and skipped API calls.
- **Official tournament reference:** `data/official-meta-nov-23.md`, with LAIC and Gdańsk results from Victory Road/Pokémon Zone. These are not silently mixed into the fully specified simulation teams.

The `Refresh Poképrotocol tournament database` workflow updates the field weekly (Monday) and can be triggered by an owner-authored Issue beginning `POKEPROTOCOL REFRESH`. Its importer excludes tournaments explicitly labeled as other regulations and stops importing new M-C events once that regulation ends in December 2026. A separate simulator/mod update will be needed for M-D.

The database records **public, anonymized tournament registrations** and *inferred* Stat Point spreads when an open team sheet omits them; the data is not a census of every official event or guaranteed to represent the entire metagame.

## Current Golisopod team (November 23)

**[Mega Golisopod Rain Wings: Showdown paste](teams/golisopod-current.txt)** · **[Build rationale, matchup and speed notes](teams/golisopod-current-notes.md)**

Poképrotocol's latest verified M-C test version is **Golisopod / Mega Salamence / Rillaboom / Pelipper / Archaludon (Aura Sphere + Dragon Pulse) / Basculegion-F**. It uses one Mega Evolution per battle, with Golisopod as the principal option and Salamence as a matchup-dependent alternative.

The [final tuning test](https://github.com/TBDProFabian/pokeprotocol-lab/issues/9) recorded **111 wins in 200 heuristic field simulations (55.5%)** for the Aura Sphere version. Its Latin America International winning-six *proxy* remains a difficult matchup, so the team is not assumed universally superior. M-D legality and matchups require a new rules/data refresh.
