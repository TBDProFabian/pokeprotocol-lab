# Poképrotocol canonical Mega Golisopod team, Regulation M-C

**Current competitive team:** [golisopod-current.txt](golisopod-current.txt)  
**Published:** November 27, 2026 (America/Chicago).  
**Format:** Pokémon Champions M-C, 66 Stat Points. M-D legality and simulator support have **not** been validated.

## Why this is the active team

The initial evolutionary search and broad opponent audit favored a three-Mega-stone Tyranitar/Sand roster, but raw battle logs revealed a major theme failure: the bot usually **Mega Evolved Salamence**, even though Golisopod was frequently brought. In 25 sampled logged matches, it Mega Evolved Salamence 17 times, Golisopod four, and Tyranitar four. Bring rate must not be represented as Golisopod's Mega rate.

**Latest canonical revision:** Salamence now holds **Sitrus Berry** based on the subsequent item-only audit (#35). The initial holdout numbers below refer to the earlier Focus Sash roster; do not treat them as measurements of the new item variant. The directly comparable 320-game Sitrus holdout scored 55.3%.

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
2. **Base Salamence, Sitrus Berry:** Intimidate plus Tailwind speed control and Hyper Voice/Draco Meteor pressure. Salamence holds **no Mega Stone**. Sitrus avoids the immediate ally Sand Stream versus Focus Sash full-health conflict; it restores health when reduced to half HP or less. Hyper Voice remains *Normal-type spread damage*, not boosted Aerilate STAB.
3. **Tyranitar, Chople Berry:** Sand Stream weather denial, Rock Slide pressure, Knock Off, Low Kick. **No Tyranitarite**. Sand can deny opposing rain and undermine immediate Electro Shot, so team preview decides whether to bring it.
4. **Physical Basculegion, Mystic Water:** Adaptability Wave Crash and Aqua Jet, plus scaling Last Respects. This is not the previous Swift Swim Basculegion-F.
5. **Archaludon, Leftovers:** Stamina and Dragon Pulse/Aura Sphere. Electro Shot is **situational** without our own Drizzle. A controlled [move audit, Issue #27](https://github.com/TBDProFabian/pokeprotocol-lab/issues/27#issuecomment-7230768339) on the preceding unrestricted sand six found Electro Shot 60.6%, Thunderbolt 60.0%, Flash Cannon 57.8%, Snarl 58.1% over 360 field games. The differences were not conclusive; leave Electro Shot unless more evidence emerges. Those move figures were **not** measured on this exact single-Mega version.
6. **Rillaboom, Miracle Seed:** Fake Out, Grassy Glide, Wood Hammer and High Horsepower to give Golisopod safe positioning, grass priority and Ground coverage.

**Play cautions:** Mega Golisopod is particularly vulnerable to Fire. Rillaboom also fears Fire; avoid exposing them together into spread Fire attacks. Tyranitar can contest Sun/Rain, Basculegion resists Fire, and Salamence provides Intimidate. This is not the former Pelipper Wide Guard team, so Rock Slide and spread-move protection require careful positioning.

## Salamence item-only sand correction: Sitrus Berry is the current item

The initial non-Mega Salamence carried both **Hyper Voice** and **Focus Sash** from the prior Mega variant. Base Salamence does not have Aerilate, so Hyper Voice is still Normal spread damage without Flying STAB or Aerilate's boost. More importantly, allied Tyranitar's Sand Stream damages Salamence at the end of turns, removing the full-HP condition that makes Focus Sash work. The Sash *can* activate before the first sand tick, but should not be assumed to protect Salamence after turn one.

Our earlier [six-set audit, Issue #32](https://github.com/TBDProFabian/pokeprotocol-lab/issues/32#issuecomment-7232057621) compared **Focus Sash + Hyper Voice** against **Sitrus Berry + Heat Wave**, changing two factors together. Its 280-battle holdout favored the old set 62.9% versus 55.4%. That comparison could NOT attribute the difference to the item and was not a valid resolution of the Sand Stream synergy question.

A new [item-only study, Issue #35](https://github.com/TBDProFabian/pokeprotocol-lab/issues/35#issuecomment-7232948152) held all six Pokémon, all 24 moves, Stat Points, natures, and abilities fixed, changing ONLY Salamence's item among Focus Sash, Sitrus Berry, Haban Berry and Yache Berry.

- Matched field training (360 battles each): **Focus Sash 183/360 = 50.8%**, **Sitrus Berry 179/360 = 49.7%**.
- LAIC champion published-set proxy, where **both Salamence and Tyranitar were selected in 100% of the battles**: Focus Sash **92.9%**; Sitrus Berry **88.6%** (140 battles per variant).
- Recent full registered winner #2, our difficult matchup: Focus Sash **43.6%**; Sitrus Berry **58.6%** (140 battles per variant).
- In the first 60 logged Focus Sash games against the LAIC proxy, Tyranitar activated sand **60/60**, Salamence took sand chip in **46/60**, and **Focus Sash activated only 2/60**. This measures *logged activations*, not proof the Sash was never potentially valuable in other games.
- On a fresh 320-battle field holdout, Focus Sash won **178/320 = 55.6%**, versus Sitrus Berry **177/320 = 55.3%**. The overall difference was effectively zero and not statistically meaningful. For both variants, the bot brought Salamence in 85.3% and Tyranitar in 24.1% of holdout battles.
- The prespecified 55% field / 30% LAIC / 15% recent winner training score narrowly favored **Sitrus 62.7%** versus **Sash 62.4%**. Small score gaps should not be oversold.

**Decision: promote Sitrus Berry with Hyper Voice still unchanged** because it avoids a known internal weather/item conflict, maintains a statistically indistinguishable overall holdout, and performed materially better against the difficult recent winner in this simulation. The changes are limited to the item. This is practical team-building judgment, **not proof** that Focus Sash is categorically inferior or that Sitrus will improve human tournament win rates.

A [synergy-warning safeguard, PR #33](https://github.com/TBDProFabian/pokeprotocol-lab/pull/33), records Mega-to-base Aerilate assumptions and ally Sand Stream/Focus Sash conflicts as advisories rather than hard bans, so future builds investigate instead of blindly copying or forbidding sets. A future **move-only** Hyper Voice vs Heat Wave/Air Slash test would be appropriate, but is distinct from the item issue fixed here.

## Engineering status and provenance

- [Root-cause Electro Shot mutation / preview audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/13)
- [Charging move preview A/B](https://github.com/TBDProFabian/pokeprotocol-lab/issues/19): confirmed previous preview scoring bias; corrected model uses versioned `POKEPROTOCOL_WEATHER_PREVIEW_V2` weather-aware charge tempo.
- [Complete corrected-preview tournament stress audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/25): initial three-Mega reference retained strong broad results, but actual Mega Goli usage forced a true-theme revision.
- [Final Mega-only team acceptance test](https://github.com/TBDProFabian/pokeprotocol-lab/issues/29): all three eligible teams passed Showdown's M-C legality validator, complete independent field holdout finished successfully.
- Engine: `joshuamatalon/champions-lab`, pinned `09d59984631dd2a45fb21700970c65ee24cf7d0f`. Pokémon Showdown rules and battle execution unchanged; preview valuation patched only. Real opponent Stat Points may be unknown or inferred. This does not validate M-D, human decision making or human tournament performance.

**Future Poképrotocol generations must preserve Golisopod as the sole Mega option.** Legacy unrestricted three-Mega roster is an analysis benchmark, not an eligible Mega Golisopod replacement.
