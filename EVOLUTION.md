# Poképrotocol Evolution Engine V1 🧬

**Status:** Experimental M-C optimizer built on the existing Champions Lab engine. It does not control the Pokémon Champions game and does not make human tournament win-rate claims.

## One-button launch from a phone

After this change is merged into `main`, go to **GitHub → pokeprotocol-lab → Actions → Poképrotocol Evolution Engine V1 → Run workflow**. Use the recommended defaults (**3 generations, 8 candidates, 40 field games per candidate**). A report artifact appears at the end containing `summary.md`, `best.txt` (Showdown paste), `baseline.txt`, `lineage.json`, `holdout.json` and each generation's scores. Alternatively, open an Issue whose title starts **`POKEPROTOCOL EVOLVE`**; only an issue authored by the repository owner can start the workflow. The workflow comments its report back on that Issue.

The simulator and tournament field run in GitHub Actions, not on your phone. Jobs have GitHub Actions compute/runtime limits. Start small. Do not assume an unfinished workflow will resume in the next run; V1 saves intermediate generation reports as artifacts but does not automatically resume timed-out runs.

## The algorithm

1. Start with `teams/golisopod-current.txt`. **Golisopod @ Golisopite is fixed as slot 1**. Its supporting five may change.
2. Load registered full sets from `data/latest-teams.json` plus the existing seed sets. Generate mutations: a different registered species and whole set, an alternative set for the same species, one registered move, an item, or a correlated nature/stat spread. Occasional crossover uses a complete set from another elite parent. These are recombinations of real components, not arbitrary new move or item inventions.
3. Require six unique species and run the pinned Showdown M-C `validate` command on **every generated candidate**. Rejected mutations are never battled. If viable mutations are scarce, the generation may have fewer than the requested number of candidates.
4. Fight each legal candidate with `heuristic` AI versus the same fixed tournament-derived field and seed (per generation). From generation 2 onward, also fight up to two successful prior-generation teams. Score **75% tournament field / 25% evolved challengers**, or 100% field when no challengers are available.
5. Keep the leading two parents and mutate/crossover their descendants. Track ancestry and fitness per generation. Repeat.
6. **Select the final champion before holdout evaluation.** Re-test the selected team, baseline, recent generational champions and finalists on a previously unused field seed. Report rate, wins, sample count and confidence interval. Do not change champion based on holdout rankings.

## Limitations

- The pinned engine covers **Regulation M-C**, not M-D. A format update requires fresh legality/mechanics verification and a new opponent field before M-D.
- The opponent field represents available open team sheets, not a census of the metagame. Stat Points absent from open sheets may be inferred.
- Evolved opposition in V1 is previous champions, **not** a full 2,048-team coevolving metagame. The champion population is a small stress layer, not a replacement for real teams.
- The mutation pool defaults to the curated recent team export, not every possible set. This limits search breadth while keeping provenance inspectable.
- Fast `heuristic` AI can be exploited. Search-AI and real-player verification remain essential. A lucky result in a 40-game sample is not proof of superiority.
- A single final holdout test checks generalization only partially. Report uncertainty, avoid claiming statistically established improvement, and use several seeds/real matches before switching a tournament team.
- Generation reports are stored in **workflow artifacts** (30-day retention). The repository's current baseline set is not automatically overwritten.

## Local testing

```sh
python -m unittest discover -s tests -p 'test_evolve.py' -v
```

The unit tests run without downloading the simulator. For actual battles, use the GitHub Actions workflow, which installs the pinned Champions Lab engine and builds its dependencies just like our existing cloud tests.

## Future improvements

- Verify simulator decision-making against human replay logs.
- Broaden the donor registry to all vetted M-C open team sheets with provenance and legality checks.
- Evaluate adversarial counter-pools and multiple AI policies rather than one heuristic policy.
- Persist champions across workflows and resume from checkpoints.
- Increase search width/battles only after establishing a reliable small-scale signal.