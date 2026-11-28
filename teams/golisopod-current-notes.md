# Poképrotocol canonical Mega Golisopod team, Regulation M-C

**Current competitive team:** [golisopod-current.txt](golisopod-current.txt)  
**Published:** November 27, 2026 (America/Chicago).  
**Format:** Pokémon Champions M-C, 66 Stat Points. M-D legality and simulator support have **not** been validated.

## Why this is the active team

**Current canonical six, November 27, 2026:** Mega Golisopod / Corviknight / Tyranitar / Basculegion / Archaludon / Rillaboom. The user explicitly does **not** want ordinary Salamence without its Mega Stone; carrying Salamencite would compete with the team's primary Mega Golisopod strategy. This team uses **only Golisopite**, so the simulator's Mega activation rate measures actual Mega Golisopod usage.

The [nine-team replacement evaluation, Issue #39](https://github.com/TBDProFabian/pokeprotocol-lab/issues/39#issuecomment-7233393139) included legal Staraptor (both Tailwind and Scarf), Incineroar, Whimsicott, Talonflame, Corviknight and Farigiraf sets; the old non-Mega Salamence and true Salamencite variants were reference-only. The predefined training selection chose **Corviknight**, with Farigiraf showing better Mega Golisopod activation and an initially better holdout. That prompted a *new, separately prespecified* [Fire/Sun safety gate, Issue #42](https://github.com/TBDProFabian/pokeprotocol-lab/issues/42#issuecomment-7233555813) against two complete registered Sun-team winners.

The Sun safety gate compared Corviknight, Farigiraf, Incineroar and Staraptor, checking each full six with the pinned Showdown Regulation M-C validator and versioned weather-aware Champions Lab preview. Winner chosen **before** a new independent holdout using: 35% field, 20% Nov 18 Torkoal/Charizard Y registered Sun winner, 15% Oct 26 Charizard Y/Venusaur registered winner, 10% LAIC published-set proxy, 10% difficult fully registered winner #2, and 10% actual Mega Golisopod activation, with an 80% Mega activation floor. **Corviknight narrowly won the composite, 52.9% versus Farigiraf's 52.6%.** This is a noisy close result, not strong proof of superiority.

- **Independent new holdout:** Corviknight **184/320 = 57.5%**, Golisopod brought **95.3%**, and actually Mega Evolved **86.9%**. Farigiraf scored **140/320 = 43.8%**, Golisopod Mega Evolved **94.1%**. A previous holdout seed (#39) had favored Farigiraf, so the reversal shows major simulator/sample uncertainty.
- **First registered Sun opponent:** Corviknight **14/70 = 20.0%**, Farigiraf **21/70 = 30.0%**, Incineroar **23/70 = 32.9%**. Against that complete Torkoal/Charizard Y/Venusaur six, our current team is **very vulnerable**.
- **Second registered Sun opponent:** Corviknight **53/70 = 75.7%**, Farigiraf **43/70 = 61.4%**. Sun is not one homogeneous matchup.
- **Other matchup checks:** Corviknight versus LAIC champion published-set proxy **39/70 = 55.7%** (published moves, item and nature but inferred Stat Points); versus hard recent 11–0 registered winner #2 **24/70 = 34.3%**. These remain concerning.
- **Lookahead diagnostic (12 games per pairing, extremely uncertain):** Corviknight against first Torkoal Sun opponent **2/12 = 16.7%** and second Sun **10/12 = 83.3%**; these confirm a possible sharp matchup distinction rather than an overall win-rate estimate.
- All results are **AI-vs-AI simulations under one pinned M-C engine**, not estimates of human tournament performance, and M-D legality has not been checked.

This is the best current **no-base-Salamence**, Mega Golisopod-centered configuration from the constrained experiments. The next meaningful engineering/teambuilding work is **remedying the full Torkoal Sun and recent 11–0 team matchups**, rather than rebuilding Salamence again.

## Six roles and play principles

1. **Mega Golisopod, the actual Mega:** Leech Life / Iron Head / Sucker Punch / Protect; Bug/Steel offensive presence with recovery and priority. 2 HP / 32 Atk / 32 Spe, Adamant. Mega activation, not roster inclusion, is our tracking priority.
2. **Corviknight, Sitrus Berry:** Mirror Armor, Brave Bird, Roost, Tailwind and Protect. Unlike non-Mega Salamence, it is immune to Tyranitar's sandstorm chip, retains Tailwind support and can heal with Roost. **It does not supply Intimidate** and adds a third Steel-type slot, worsening stacked Fire exposure. 32 HP / 1 Atk / 1 Def / 15 SpD / 17 Spe, Careful.
3. **Tyranitar, Chople Berry:** Sand Stream weather denial, Rock Slide pressure, Knock Off, Low Kick. **No Tyranitarite**. Sand can deny opposing rain and undermine immediate Electro Shot, so team preview decides whether to bring it.
4. **Physical Basculegion, Mystic Water:** Adaptability Wave Crash and Aqua Jet, plus scaling Last Respects. This is not the previous Swift Swim Basculegion-F.
5. **Archaludon, Leftovers:** Stamina and Dragon Pulse/Aura Sphere. Electro Shot is **situational** without our own Drizzle. A controlled [move audit, Issue #27](https://github.com/TBDProFabian/pokeprotocol-lab/issues/27#issuecomment-7230768339) on the preceding unrestricted sand six found Electro Shot 60.6%, Thunderbolt 60.0%, Flash Cannon 57.8%, Snarl 58.1% over 360 field games. The differences were not conclusive; leave Electro Shot unless more evidence emerges. Those move figures were **not** measured on this exact single-Mega version.
6. **Rillaboom, Miracle Seed:** Fake Out, Grassy Glide, Wood Hammer and High Horsepower to give Golisopod safe positioning, grass priority and Ground coverage.

**Play cautions:** Mega Golisopod (Bug/Steel) is 4× weak to Fire; Corviknight and Rillaboom are also Fire-weak. **This is a serious shared Fire vulnerability and Corviknight creates three Steel types on the roster.** Tyranitar's sand can contest Sun, and Basculegion resists Fire, but neither guarantees a solution. The complete registered Torkoal/Charizard Y/Venusaur winner demolished our fast AI (20% wins), and lookahead only went 2/12. This is not a Pelipper Wide Guard team; manage spread attacks, speed and lead positioning carefully. Corviknight is not an Intimidate user.

## Archived Salamence item/move experiments (not the current team)

The following tests explain why the earlier regular Salamence roster was abandoned and preserved as a reproducible historical benchmark. **No Salamence is present in the current six.** The Focus Sash / Sitrus Berry comparison below is historical; the current Sitrus holder is Corviknight.

The initial non-Mega Salamence carried both **Hyper Voice** and **Focus Sash** from the prior Mega variant. Base Salamence does not have Aerilate, so Hyper Voice is still Normal spread damage without Flying STAB or Aerilate's boost. More importantly, allied Tyranitar's Sand Stream damages Salamence at the end of turns, removing the full-HP condition that makes Focus Sash work. The Sash *can* activate before the first sand tick, but should not be assumed to protect Salamence after turn one.

Our earlier [six-set audit, Issue #32](https://github.com/TBDProFabian/pokeprotocol-lab/issues/32#issuecomment-7232057621) compared **Focus Sash + Hyper Voice** against **Sitrus Berry + Heat Wave**, changing two factors together. Its 280-battle holdout favored the old set 62.9% versus 55.4%. That comparison could NOT attribute the difference to the item and was not a valid resolution of the Sand Stream synergy question.

A new [item-only study, Issue #35](https://github.com/TBDProFabian/pokeprotocol-lab/issues/35#issuecomment-7232948152) held all six Pokémon, all 24 moves, Stat Points, natures, and abilities fixed, changing ONLY Salamence's item among Focus Sash, Sitrus Berry, Haban Berry and Yache Berry.

- Matched field training (360 battles each): **Focus Sash 183/360 = 50.8%**, **Sitrus Berry 179/360 = 49.7%**.
- LAIC champion published-set proxy, where **both Salamence and Tyranitar were selected in 100% of the battles**: Focus Sash **92.9%**; Sitrus Berry **88.6%** (140 battles per variant).
- Recent full registered winner #2, our difficult matchup: Focus Sash **43.6%**; Sitrus Berry **58.6%** (140 battles per variant).
- In the first 60 logged Focus Sash games against the LAIC proxy, Tyranitar activated sand **60/60**, Salamence took sand chip in **46/60**, and **Focus Sash activated only 2/60**. This measures *logged activations*, not proof the Sash was never potentially valuable in other games.
- On a fresh 320-battle field holdout, Focus Sash won **178/320 = 55.6%**, versus Sitrus Berry **177/320 = 55.3%**. The overall difference was effectively zero and not statistically meaningful. For both variants, the bot brought Salamence in 85.3% and Tyranitar in 24.1% of holdout battles.
- The prespecified 55% field / 30% LAIC / 15% recent winner training score narrowly favored **Sitrus 62.7%** versus **Sash 62.4%**. Small score gaps should not be oversold.

**Historical decision at the time:** We promoted Sitrus Berry with Hyper Voice still unchanged on Salamence. That historical set has since been **replaced entirely by Corviknight** in the current team. That choice avoided a known internal sand/item conflict and preserved a statistically similar overall holdout. The changes are limited to the item. This is practical team-building judgment, **not proof** that Focus Sash is categorically inferior or that Sitrus will improve human tournament win rates.

A [synergy-warning safeguard, PR #33](https://github.com/TBDProFabian/pokeprotocol-lab/pull/33), records Mega-to-base Aerilate assumptions and ally Sand Stream/Focus Sash conflicts as advisories rather than hard bans, so future builds investigate instead of blindly copying or forbidding sets. A future **move-only** Hyper Voice vs Heat Wave/Air Slash test would be appropriate, but is distinct from the item issue fixed here.

## Engineering status and provenance

- [No-base-Salamence replacement study, Issue #39](https://github.com/TBDProFabian/pokeprotocol-lab/issues/39#issuecomment-7233393139): nine legal configurations, selected Corviknight from the initial training composite; old Salamence retained as historical reference only.
- [Final full-OTS Sun safety validation, Issue #42](https://github.com/TBDProFabian/pokeprotocol-lab/issues/42#issuecomment-7233555813): Corviknight won newly prespecified Sun-focused selection and a separate 320-battle holdout. Results warn of very poor Torkoal Sun matchup.
- [Future no-Salamence exclusion PR #40](https://github.com/TBDProFabian/pokeprotocol-lab/pull/40): enforce user preference during future Mega Golisopod evolution.


- [Root-cause Electro Shot mutation / preview audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/13)
- [Charging move preview A/B](https://github.com/TBDProFabian/pokeprotocol-lab/issues/19): confirmed previous preview scoring bias; corrected model uses versioned `POKEPROTOCOL_WEATHER_PREVIEW_V2` weather-aware charge tempo.
- [Complete corrected-preview tournament stress audit](https://github.com/TBDProFabian/pokeprotocol-lab/issues/25): initial three-Mega reference retained strong broad results, but actual Mega Goli usage forced a true-theme revision.
- [Final Mega-only team acceptance test](https://github.com/TBDProFabian/pokeprotocol-lab/issues/29): all three eligible teams passed Showdown's M-C legality validator, complete independent field holdout finished successfully.
- Engine: `joshuamatalon/champions-lab`, pinned `09d59984631dd2a45fb21700970c65ee24cf7d0f`. Pokémon Showdown rules and battle execution unchanged; preview valuation patched only. Real opponent Stat Points may be unknown or inferred. This does not validate M-D, human decision making or human tournament performance.

**Future Poképrotocol generations must preserve Golisopod as the sole Mega option.** Legacy unrestricted three-Mega roster is an analysis benchmark, not an eligible Mega Golisopod replacement.
