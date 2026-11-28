# Poképrotocol canonical Mega Golisopod team, Regulation M-C

**Current competitive team:** [golisopod-current.txt](golisopod-current.txt)  
**Published:** November 27, 2026 (America/Chicago).  
**Format:** Pokémon Champions M-C, 66 Stat Points. M-D legality and simulator support have **not** been validated.

## Why this is the active team

The initial evolutionary search and broad opponent audit favored a three-Mega-stone Tyranitar/Sand roster, but raw battle logs revealed a major theme failure: the bot usually **Mega Evolved Salamence**, even though Golisopod was frequently brought. In 25 sampled logged matches, it Mega Evolved Salamence 17 times, Golisopod four, and Tyranitar four. Bring rate must not be represented as Golisopod's Mega rate.

The [actual-use correction audit, Issue #29](https://github.com/TBDProFabian/pokeprotocol-lab/issues/29#issuecomment-7230793185), compared teams with **Golisopite as the only Mega Stone** under the pinned Champions Lab engine and versioned weather-aware preview policy. The winner is **Sand / base Salamence**.

- Selection/training: **133/240 = 55.4%** simulated field wins, Golisopod brought **95.4%**, Mega Golisopod activated **87.1%**.
- Independent holdout: **175/320 = 54.7%**, approximate 95% interval **49.2–60.1%**. Golisopod brought **93.8%** and Mega Golisopod activated **85.3%**.
- The unrestricted three-Mega reference scored **179/320 = 55.9%** on the same holdout, but did not isolate Golisopod as the Mega. The **1.2 percentage point gap** is small and not evidence of a tournament win-rate difference.
- LAIC champion published-set proxy: **65/80 = 81.2%** heuristic and **8/16 = 50.0%** lookahead. The proxy has verified public species, moves, items and natures but **inferred Stat Points**.
- Complete recent registered winner #2: **31/80 = 38.8%** heuristic and **6/16 = 37.5%** lookahead. **Important difficult matchup**. Future tuning must avoid overfitting to LAIC alone.
- Alternative single-Golisopite builds fell behind in field training: Sand/Whimsicott 46.7%, Rain/base Salamence 47.5%.
- These are AI-versus-AI **simulator** results, not estimates of a player's win rate or proof of tournament superiority.

## Six roles and play principles

1. **Mega Golisopod, the actual Mega:** Leech Life / Iron Head / Sucker Punch / Protect; Bug/Steel offensive presence with recovery and priority. 2 HP / 32 Atk / 32 Spe, Adamant. Mega activation, not roster inclusion, is our tracking priority.
2. **Base Salamence, Focus Sash:** Intimidate plus Tailwind speed control and Hyper Voice/Draco Meteor pressure. Salamence holds **no Mega Stone**. Its Focus Sash can be broken by Tyranitar's sand chip, so plan the leads and weather timing.
3. **Tyranitar, Chople Berry:** Sand Stream weather denial, Rock Slide pressure, Knock Off, Low Kick. **No Tyranitarite**. Sand can deny opposing rain and undermine immediate Electro Shot, so team preview decides whether to bring it.
4. **Physical Basculegion, Mystic Water:** Adaptability Wave Crash and Aqua Jet, plus scaling Last Respects. This is not the previous Swift Swim Basculegion-F.
5. **Archaludon, Leftovers:** Stamina and Dragon Pulse/Aura Sphere. Electro Shot is **situational** without our own Drizzle. A controlled [move audit, Issue #27](https://github.com/TBDProFabian/pokeprotocol-lab/issues/27#issuecomment-7230768339) on the preceding unrestricted sand six found Electro Shot 60.6%, Thunderbolt 60.0%, Flash Cannon 57.8%, Snarl 58.1% over 360 field games. The differences were not conclusive; leave Electro Shot unless more evidence emerges. Those move figures were **not** measured on this exact single-Mega version.
6. **Rillaboom, Miracle Seed:** Fake Out, Grassy Glide, Wood Hammer and High Horsepower to give Golisopod safe positioning, grass priority and Ground coverage.

**Play cautions:** Mega Golisopod is particularly vulnerable to Fire. Rillaboom also fears Fire; avoid exposing them together into spread Fire attacks. Tyranitar can contest Sun/Rain, Basculegion resists Fire, and Salamence provides Intimidate. This is not the former Pelipper Wide Guard team, so Rock Slide and spread-move protection require careful positioning.

## Base Salamence audit: move/item inheritance is now an advisory, not an automatic failure

The set `Focus Sash / Hyper Voice / Draco Meteor / Tailwind / Protect` was copied from a former **Mega Salamence** configuration when Salamencite was removed to enforce Mega Golisopod. The initial conversion was *not* an informed reranking of base Salamence moves. Regular Salamence has **Intimidate** rather than Aerilate, so Hyper Voice remains Normal spread damage instead of Aerilate-boosted Flying STAB. Sand Stream from our Tyranitar can break Focus Sash after the first sand-damage tick, but neither effect makes the set outright illegal or always poor.

A live [six-set corrected-preview A/B audit, Issue #32](https://github.com/TBDProFabian/pokeprotocol-lab/issues/32#issuecomment-7232057621) tested that original set, Sash+Heat Wave, and Sitrus/Haban Berries with either Heat Wave or Air Slash. All six passed the pinned M-C Showdown legality validator. The non-Sash, non-Hyper-Voice options are mechanically coherent alternatives; **none was proven better by independent holdout**.

- On one common 200-battle *training* set, the original was **105/200 = 52.5%**, Sitrus/Heat Wave **108/200 = 54.0%**, Haban/Air Slash **113/200 = 56.5%** and Sitrus/Air Slash **114/200 = 57.0%**. Targeted difficult winner matchups changed the weighted ranking, which selected Sitrus/Heat Wave before seeing holdout.
- On a different 280-battle *holdout* seed, **original Focus Sash + Hyper Voice won 176/280 = 62.9%**, while the preselected Sitrus/Heat Wave alternative won **155/280 = 55.4%**. This is a single bot-simulator holdout, **not** definitive proof Hyper Voice is optimal or human win-rate evidence.
- Original holdout bring rates: **Salamence 81.1%; Tyranitar 28.6%; Mega Golisopod activated 87.5%**. With Tyranitar omitted most games, its Sand Stream is not automatically destroying Salamence's Sash; Focus Sash may still matter before end-turn chip even when sand is present. Sitrus/Heat Wave brought Salamence 95.4% and Tyranitar 25.0%, substantially changing the preview composition.
- The three available logged matches per archetype are too few to measure actual Focus Sash activations across the field. This remains a tactical question for real-player replay validation, not a proven item-synergy benefit.

**Decision:** Retain the old set as the current, legally validated configuration for now. It was inherited inadvertently, but it may be useful in the simulator through Normal spread coverage and first-turn Focus Sash survivability. Do not silently replace it or categorically prohibit it. A new [quality-warning gate, PR #33](https://github.com/TBDProFabian/pokeprotocol-lab/pull/33) records the missing Aerilate boost and sand/Sash interaction **as advisories, not automatic rejection** during future evolution.

## Engineering status and provenance

- [Root-cause Electro Shot mutation / preview audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/13)
- [Charging move preview A/B](https://github.com/TBDProFabian/pokeprotocol-lab/issues/19): confirmed previous preview scoring bias; corrected model uses versioned `POKEPROTOCOL_WEATHER_PREVIEW_V2` weather-aware charge tempo.
- [Complete corrected-preview tournament stress audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/25): initial three-Mega reference retained strong broad results, but actual Mega Goli usage forced a true-theme revision.
- [Final Mega-only team acceptance test](https://github.com/TBDProFabian/pokeprotocol-lab/issues/29): all three eligible teams passed Showdown's M-C legality validator, complete independent field holdout finished successfully.
- Engine: `joshuamatalon/champions-lab`, pinned `09d59984631dd2a45fb21700970c65ee24cf7d0f`. Pokémon Showdown rules and battle execution unchanged; preview valuation patched only. Real opponent Stat Points may be unknown or inferred. This does not validate M-D, human decision making or human tournament performance.

**Future Poképrotocol generations must preserve Golisopod as the sole Mega option.** Legacy unrestricted three-Mega roster is an analysis benchmark, not an eligible Mega Golisopod replacement.
