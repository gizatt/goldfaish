import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "experiment_dir",
        help="Top-level of experiment directorys.")
    parser.add_argument("--games",
                        type=int,
                        default=40,
                        help="Number of games to simulate in each job")
    parser.add_argument("--jobs",
                        type=int,
                        default=3,
                        help="Number of parallel jobs")
    parser.add_argument("--recollect_data",
                        action="store_true")
    args = parser.parse_args()

    for subdir in os.listdir(args.experiment_dir):
        full_subdir = os.path.join(args.experiment_dir, subdir)
        if not os.path.isdir(full_subdir):
            continue
        if os.path.exists(os.path.join(full_subdir, "info.json")):
            print(f"Updating {full_subdir}")
            if not os.path.exists(os.path.join(full_subdir, "data.json")) or args.recollect_data:
                os.system(f"python -m goldfaish.collect_data {full_subdir} --games {args.games} --jobs {args.jobs}")
            os.system(f"python -m goldfaish.process_logs {full_subdir}")
            os.system(f"python -m goldfaish.plot_stats {full_subdir}")
            
