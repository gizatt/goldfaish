import argparse
import os
import uuid
import subprocess
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from goldfaish import FORGE_BIN_PATH, DEFAULT_DECK_DIR
import traceback

LOG_UPDATE_GRACE_SECONDS = 7  # Wait this long after last log update
GAME_RESULT_PREFIX = "Game Result: "  # Used to count completed games


def run_sim(deck1, deck2, deck_dir, out_dir, forge_args, quiet, games, pbar=None):
    # Generate a unique log filename
    log_id = uuid.uuid4().hex
    log_path = os.path.join(out_dir, f"match_{log_id}.log")
    
    # Build the forge command
    cmd = [
        str(FORGE_BIN_PATH),
        "sim",
        "-d",
        deck1,
        deck2,
        "-D", deck_dir,
        "-n", str(games),
        *forge_args
    ]
    if quiet:
        cmd.append("-q")
    
    # Set working directory to the directory containing FORGE_BIN_PATH
    forge_dir = os.path.dirname(str(FORGE_BIN_PATH))
    
    with open(log_path, "w") as logf:
        try:
            print("running command: ", " ".join(cmd))
            proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, cwd=forge_dir)
            proc.wait()
            # Progress tracking
            last_mtime = os.path.getmtime(log_path)
            last_count = 0
            last_update = time.time()
            while True:
                time.sleep(1)
                new_mtime = os.path.getmtime(log_path)
                if new_mtime != last_mtime:
                    last_mtime = new_mtime
                    last_update = time.time()
                # Count completed games
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        count = sum(1 for line in lf if line.startswith(GAME_RESULT_PREFIX))
                    if pbar is not None:
                        pbar.n = count
                        pbar.refresh()
                    last_count = count
                except Exception:
                    pass
                if time.time() - last_update >= LOG_UPDATE_GRACE_SECONDS:
                    break
            if pbar is not None:
                pbar.n = games
                pbar.refresh()
                pbar.close()
            success = proc.returncode == 0
            # After simulation, scan log for warnings the user should know about
            warnings = []
            warning_patterns = [re.compile(r"unsupported card", re.IGNORECASE)]
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                    for line in lf:
                        if any(pat.search(line) for pat in warning_patterns):
                            warnings.append(line.rstrip())
            except Exception:
                pass
            if warnings:
                print(f"Warnings in {os.path.basename(log_path)}:")
                for w in warnings:
                    print(w)
                # Write to log.txt in out_dir
                log_txt_path = os.path.join(out_dir, "log.txt")
                with open(log_txt_path, "a", encoding="utf-8") as logf:
                    logf.write(f"Warnings from {os.path.basename(log_path)}:\n")
                    for w in warnings:
                        logf.write(w + "\n")
            return log_path, success
        except Exception as e:
            traceback.print_exc()
            if pbar is not None:
                pbar.close()
            return log_path, False


def main():
    parser = argparse.ArgumentParser(description="Parallel Forge matchup data collection.")
    parser.add_argument("--deck1", required=True, help="Deck 1 filename (e.g. Goldfish.dck)")
    parser.add_argument("--deck2", required=True, help="Deck 2 filename (e.g. Yuna.dck)")
    # Use DEFAULT_DECK_DIR as the default, and ensure absolute path is passed to Forge
    parser.add_argument("--deck-dir", default=str(DEFAULT_DECK_DIR), help="Directory containing deck files")
    parser.add_argument("--out-dir", default=None, help="Directory to store log files (overrides default sandbox path)")
    parser.add_argument("--games", type=int, default=100, help="Number of games to simulate in each job")
    parser.add_argument("--jobs", type=int, default=4, help="Number of parallel jobs")
    parser.add_argument("--quiet", action="store_true", help="Pass -q to Forge for minimal output")
    parser.add_argument("--forge-args", nargs=argparse.REMAINDER, help="Extra args to pass to Forge after decks")
    args = parser.parse_args()

    # Compose default log directory if not provided
    if args.out_dir is None:
        deckA = os.path.splitext(os.path.basename(args.deck1))[0]
        deckB = os.path.splitext(os.path.basename(args.deck2))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.out_dir = os.path.join(
            "sandbox", "logs", f"{deckA}_v_{deckB}", timestamp
        )
    os.makedirs(args.out_dir, exist_ok=True)
    forge_args = args.forge_args if args.forge_args else []
    deck_dir_abs = os.path.abspath(args.deck_dir)
    task = (args.deck1, args.deck2, deck_dir_abs, args.out_dir, forge_args, args.quiet, args.games)
    results = []
    # Create a progress bar for each job
    pbars = [tqdm(total=args.games, desc=f"Job {i+1}", position=i, leave=True) for i in range(args.jobs)]
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(run_sim, *task, pbars[i]) for i in range(args.jobs)]
        for f in as_completed(futures):
            log_path, success = f.result()
            results.append((log_path, success))
    for pbar in pbars:
        pbar.close()
    failed = [log for log, ok in results if not ok]
    print(f"\nCompleted {len(results)} simulations. {len(failed)} failed.")
    if failed:
        print("Failed log files:")
        for log in failed:
            print(log)

if __name__ == "__main__":
    main()
