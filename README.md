Setup:
python -m goldfaish.download_forge

Run a thing:
python -m goldfaish.collect_data --deck1 Yuna.dck --deck2 Goldfish.dck --games 20 --jobs 2  --forge-args -f commander  -aiTimeout 0 -gameTimeout 600
python -m goldfaish.process_logs .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\
python -m goldfaish.plot_stats .\sandbox\logs\Goldfish_v_Yuna\20250718_025507\

python -m goldfaish.collect_data --deck1 Tidus.dck --deck2 Goldfish.dck --games 20 --jobs 2  --forge-args -f commander  -aiTimeout 0 -gameTimeout 600 -useSim
python -m goldfaish.process_logs .\sandbox\logs\Tidus_v_Yuna\20250718_041515\
python -m goldfaish.plot_stats .\sandbox\logs\Tidus_v_Yuna\20250718_041515\

python -m goldfaish.collect_data --deck1 Krrik_B5.dck --deck2 Yuna.dck --games 10 --jobs 2  --forge-args -f commander -aiTimeout 0 -gameTimeout 600 -useSim
python -m goldfaish.process_logs .\sandbox\logs\Krrik_B5_v_Yuna\20250718_033123
python -m goldfaish.plot_stats .\sandbox\logs\Krrik_B5_v_Yuna\20250718_033123