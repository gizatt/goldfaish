import argparse
import os
import json
import uuid
import subprocess
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from goldfaish import FORGE_BIN_DIR, FORGE_CMD
import traceback
import datetime

TIMEOUT = 100000 # Just over a day...

def run_sim(out_dir: str,
            forge_args,
            quiet,
            games,
            pbar=None):
    
    raw_log_path = os.path.join(out_dir, f"raw_log.txt")

    # Build the forge command
    cmd = [
        str(FORGE_CMD), "sim", "-n",
        str(games), "-logDir", '"' + out_dir + '"', *forge_args
    ]
    if quiet:
        cmd.append("-q")

    with open(raw_log_path, "w") as logf:
        try:
            cmd = " ".join(cmd)
            print("Launching job: ", cmd)
            proc = subprocess.Popen(cmd,
                                    stdout=logf,
                                    stderr=subprocess.STDOUT,
                                    cwd=FORGE_BIN_DIR)
            start_time = time.time()
            process_done = False
            while not process_done:
                time.sleep(1)

                proc.poll()
                process_done = proc.returncode is not None

                # Count number of files in this directory that end in `.log`.
                if pbar is not None:
                    pbar.n = len([f for f in os.listdir(out_dir) if f.endswith('.log')])
                    pbar.refresh()

                if time.time() - start_time > TIMEOUT:
                    raise TimeoutError()

            if pbar is not None:
                pbar.n = games
                pbar.refresh()
                pbar.close()
            success = proc.returncode == 0

            # After simulation, scan log for warnings the user should know about
            warnings = []
            warning_patterns = [re.compile(r"unsupported card", re.IGNORECASE)]
            try:
                with open(raw_log_path, "r", encoding="utf-8",
                          errors="ignore") as lf:
                    for line in lf:
                        if any(pat.search(line) for pat in warning_patterns):
                            warnings.append(line.rstrip())
            except Exception:
                pass

            if warnings:
                print(f"Warnings in {os.path.basename(raw_log_path)}:")
                for w in warnings:
                    print(w)
                # Write to log.txt in out_dir
                log_txt_path = os.path.join(out_dir, "log.txt")
                with open(log_txt_path, "a", encoding="utf-8") as logf:
                    logf.write(
                        f"Warnings from {os.path.basename(raw_log_path)}:\n")
                    for w in warnings:
                        logf.write(w + "\n")
            return success
        except Exception as e:
            traceback.print_exc()
            if pbar is not None:
                pbar.close()
            return  False


def main():
    parser = argparse.ArgumentParser(
        description="Parallel Forge matchup data collection.")
    parser.add_argument(
        "experiment_dir",
        help="Experiment directory.")
    parser.add_argument("--games",
                        type=int,
                        default=100,
                        help="Number of games to simulate in each job")
    parser.add_argument("--jobs",
                        type=int,
                        default=3,
                        help="Number of parallel jobs")
    parser.add_argument("--quiet",
                        action="store_true",
                        help="Pass -q to Forge for minimal output")
    parser.add_argument("--forge-args",
                        nargs=argparse.REMAINDER,
                        help="Extra args to pass to Forge after decks")
    args = parser.parse_args()

    # Open info.json
    with open(os.path.join(args.experiment_dir, "info.json"), "r") as f:
        info_dict = json.load(f)
    
    # Find decks
    deck_a = info_dict["deck_a"]
    deck_b = info_dict["deck_b"]
    format = info_dict["format"]
    decks_dir = os.path.abspath(os.path.join(args.experiment_dir, "decks"))
    for deck in deck_a, deck_b:
        deck_path = os.path.join(decks_dir, deck)
        assert os.path.exists(deck_path), "No deck found at " + deck_path
    
    log_dir = os.path.abspath(os.path.join(args.experiment_dir, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    forge_args = [
        "-d", deck_a, deck_b, "-D", '"' + decks_dir + '/"', "-f", format,
    ]
    if "forge_args" in info_dict:
        forge_args += info_dict["forge_args"]
    if args.forge_args:
        forge_args.append(args.forge_args)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
    
    results = []
    # Create a progress bar for each job
    pbars = [
        tqdm(total=args.games, desc=f"Job {i+1}", position=i, leave=True)
        for i in range(args.jobs)
    ]
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = []
        for k, pbar in enumerate(pbars):
            out_dir = os.path.join(log_dir, timestamp + "_job_" + str(k))
            os.makedirs(out_dir, exist_ok=False)
            task = (out_dir, forge_args, args.quiet, args.games)
            futures.append(executor.submit(run_sim, *task, pbar))
        for f in as_completed(futures):
            success = f.result()
            results.append((success))
    for pbar in pbars:
        pbar.close()
    print(f"\nCompleted {len(results)} simulations. {sum(results)} succeeded.")

if __name__ == "__main__":
    main()
