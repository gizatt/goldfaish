Setup:
python -m goldfaish.download_forge

Run a thing:
python -m goldfaish.collect_data --deck1 Goldfish.dck --deck2 Yuna.dck --games 5 --jobs 3  --forge-args -f commander
python -m goldfaish.process_logs .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\
python -m goldfaish.plot_stats .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\