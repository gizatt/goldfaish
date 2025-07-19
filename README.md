Setup:
python -m goldfaish.download_forge

# Pipeline

This tool is built around the workflow of:

### 1) Create an experiment directory with a `info.json` file (pattern match on existing files) and a decks directory with the decks of interest.
### 2) Simulate some number of matches between two decks, which produces a number of Forge game log files, one subdirectory per process. This produces a subdirectory from the matchup with many logs in it, each file pertaining to one match. This is long-running:

```
python -m goldfaish.collect_data <path to experiment directory> --games 20 --jobs 5
```

### 3) Do dataset processing on the simulated matches. This may be inefficient because there are many giant text logs to crawl.

```
python -m goldfaish.process_logs <path to experiment directory>
```

This produces a `stats.json` file which contains a structured representation of each game, intended to pare the game down to just the data needed for the actual data analysis. Each game is an entry in the top-level list, organized as:
```
{
  winner: player_name
  players: [player_name_1, player_name_2]
  turns: {
    "1": {
      "MAIN1": {
        game state dict
      }, 
      "CLEANUP": {
        game state dict
      },
    }
  }
}
```
See an existing `data.json` for the exact contents of the game state dict.

### 4) Do data analysis and plotting. This is fast.

```
python -m goldfaish.plot_stats <path to experiment directory>
```


Data directory layout:
  - `info.json` describing the matchup and the simulation parameters.
  - `decks`
    - `commander`
      - `DeckA.dck`
      - `DeckB.dck`
  - `stats.json`, processed extracted stats from the set of all matches.
  - `logs`, a directory in which all logs are found, possibly multiple folders deep.
    - `job_<timestamp>`
      - `raw_log.txt` Process output
      - `<timestamp>_game_<#>.log` Game log
      - ...
