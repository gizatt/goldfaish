Setup:
python -m goldfaish.download_forge

# Pipeline

This tool is built around the workflow of:

1) Create an experiment directory with a `info.json` file (pattern match on existing files) and a decks directory with the decks of interest.
2) Simulate some number of matches between two decks, which produces a number of Forge game log files, one subdirectory per process. This produces a subdirectory from the matchup with many logs in it, each file pertaining to one match. This is long-running.
    ```python -m goldfaish.collect_data <path to experiment directory> --games 20 --jobs 5```
2) Do dataset processing on the simulated matches. This may be inefficient because there are many giant text logs to crawl.
3) Do data analysis and plotting. This is fast.

Data directory:
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

      
 

Run a thing:
python -m goldfaish.collect_data --deck1 Yuna.dck --deck2 Goldfish.dck --games 20 --jobs 5  --forge-args -f commander  -aiTimeout 0 -gameTimeout 600
python -m goldfaish.process_logs .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\
python -m goldfaish.plot_stats .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\

python -m goldfaish.collect_data --deck1 Tidus.dck --deck2 Goldfish.dck --games 20 --jobs 5  --forge-args -f commander  -aiTimeout 0 -gameTimeout 600
python -m goldfaish.process_logs .\sandbox\logs\Tidus_v_Yuna\20250718_041515\
python -m goldfaish.plot_stats .\sandbox\logs\Tidus_v_Yuna\20250718_041515\

python -m goldfaish.collect_data --deck1 Krrik_B5.dck --deck2 Yuna.dck --games 10 --jobs 2  --forge-args -f commander -aiTimeout 0 -gameTimeout 600 -useSim
python -m goldfaish.process_logs .\sandbox\logs\Krrik_B5_v_Yuna\20250718_033123
python -m goldfaish.plot_stats .\sandbox\logs\Krrik_B5_v_Yuna\20250718_033123