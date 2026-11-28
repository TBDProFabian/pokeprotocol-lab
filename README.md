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

## Current primary Mega Golisopod team (November 28, 2026)

**[Showdown paste](teams/golisopod-current.txt)** · **[Independent holdout and matchup audit](teams/golisopod-current-notes.md)**

The primary M-C roster is **Mega Golisopod / Corviknight / Tyranitar / Basculegion / Archaludon / Rillaboom**. Golisopite is the **only Mega Stone**; Salamence is excluded from the primary evolution search.

In its reported independent 320-game *simulated* holdout the current roster achieved **184/320 (57.5%)**, with actual Mega Golisopod activation **86.9%**. These are engine policy results, not real-player win rate predictions. The team remains vulnerable to at least one fully registered Torkoal / Charizard Y / Venusaur winner (14/70 = 20% in simulation).

**Regulation boundary:** M-D starts **2026-12-02 02:00 UTC** (December 1 at 8 p.m. CST). Every existing runner and field in this repository is pinned to **M-C**, not M-D. New Pokémon, Mega Stones, moves, balance changes, legality, and the opponent dataset must be explicitly revalidated and the engine upgraded before claiming M-D support. Never silently reuse M-C simulator outcomes as M-D evidence.

**Pre-regulation maintenance:** Run the new M-C preflight before an Evolution Engine run. It fails closed on stale/mislabeled tournament data, unsupported M-D format, species/item/Stat Point roster violations, and multiple Megas. The older `Poképrotocol cloud simulation` workflow is a legacy Incineroar/Sneasler comparison, not the current Golisopod pipeline.
