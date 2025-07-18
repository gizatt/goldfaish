import os
import json
import sys
import re
from typing import List, Dict, Any

class LogParseError(Exception):
    pass

class StatProcessor:
    """
    Base class for stat processors. Override process_game to extract stats from a parsed game.
    """
    def process_game(self, game_lines: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

class BasicStatsProcessor(StatProcessor):
    def process_game(self, game_lines: List[str]) -> Dict[str, Any]:
        # Extract player names
        header_pat = re.compile(r"Ai\(1\)-(\w+) vs Ai\(2\)-(\w+)")
        mulligan_pat = re.compile(r"Mulligan: Ai\((\d)\)-(\w+) has (mulliganed down to|kept a hand of) (\d+) cards")
        turn_pat = re.compile(r"Turn: Turn (\d+) \(Ai\((\d)\)-(\w+)\)")
        land_play_pat = re.compile(r"Land: Ai\((\d)\)-(\w+) played (.+) \(\d+\)")
        mana_pat = re.compile(r"Mana: .+\(\d+\) - ")
        damage_pat = re.compile(r"Damage: .+ deals (\d+) combat damage to Ai\((\d)\)-(\w+)\.")
        outcome_pat = re.compile(r"Game outcome: (.+)")
        win_pat = re.compile(r"Game outcome: (Ai\(\d\)-\w+) has won because .+")
        lose_pat = re.compile(r"Game outcome: (Ai\(\d\)-\w+) has lost because .+")
        
        # Find player names and deck names
        players = None
        deck_names = None
        for line in game_lines:
            m = header_pat.search(line)
            if m:
                players = {"Ai(1)": "Ai(1)", "Ai(2)": "Ai(2)"}
                deck_names = {"Ai(1)": m.group(1), "Ai(2)": m.group(2)}
                break
        if not players:
            raise LogParseError("Could not find player names")
        
        # Mulligan info
        mulligans = {deck_names['Ai(1)']: None, deck_names['Ai(2)']: None}
        for line in game_lines:
            m = mulligan_pat.match(line)
            if m:
                pid = f"Ai({m.group(1)})"
                pname = m.group(2)
                count = int(m.group(4))
                mulligans[pname] = count
                if all(v is not None for v in mulligans.values()):
                    break
        # Per-turn stats
        turns = []
        current_turn = None
        for line in game_lines:
            m = turn_pat.match(line)
            if m:
                if current_turn:
                    turns.append(current_turn)
                current_turn = {
                    'turn': int(m.group(1)),
                    'player': f"Ai({m.group(2)})",  # Use player name, not deck name
                    'land_plays': [],
                    'mana_taps': 0,
                    'damage_taken': {"Ai(1)": 0, "Ai(2)": 0},  # Incremental per turn
                }
            elif current_turn:
                lm = land_play_pat.match(line)
                if lm and f"Ai({lm.group(1)})" == current_turn['player']:
                    current_turn['land_plays'].append(lm.group(3))
                if mana_pat.match(line):
                    current_turn['mana_taps'] += 1
                dm = damage_pat.match(line)
                if dm:
                    dmg = int(dm.group(1))
                    pid = f"Ai({dm.group(2)})"
                    current_turn['damage_taken'][pid] += dmg  # Only this turn's damage
        if current_turn:
            turns.append(current_turn)
        # Winner and win turn
        winner = None
        win_turn = None
        for i, line in enumerate(game_lines):
            m = win_pat.match(line)
            if m:
                winner_full = m.group(1)  # e.g. 'Ai(1)-Goldfish'
                # Extract just the player (Ai(1) or Ai(2))
                winner = winner_full.split('-')[0]
                # Find previous 'Game outcome: Turn X' for win turn
                for j in range(i-1, -1, -1):
                    tm = re.match(r"Game outcome: Turn (\d+)", game_lines[j])
                    if tm:
                        win_turn = int(tm.group(1))
                        break
                break
        if not winner or not win_turn:
            raise LogParseError("Could not find winner or win turn")
        # Structure output
        return {
            'players': deck_names,  # Keep deck names for reference
            'mulligans': mulligans,
            'winner': winner,  # Now just 'Ai(1)' or 'Ai(2)'
            'win_turn': win_turn,
            'turns': turns,
            'raw_log': ''.join(game_lines),  # Add the raw log as a string
        }

def parse_log_file(filepath: str, processors: List[StatProcessor]) -> List[Dict[str, Any]]:
    games = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Split log into games (implement actual splitting logic as needed)
    # For now, treat the whole file as one game
    try:
        for processor in processors:
            game_stats = processor.process_game(lines)
            games.append(game_stats)
    except LogParseError as e:
        print(f"Malformed game in {filepath}: {e}", file=sys.stderr)
    return games

def process_log_directory(log_dir: str, output_path: str = None, processors: List[StatProcessor] = None):
    import sys
    if processors is None:
        processors = [BasicStatsProcessor()]
    all_stats = []
    log_files = [fname for fname in os.listdir(log_dir) if fname.endswith('.log')]
    total = len(log_files)
    error_count = 0
    game_count = 0
    if output_path is None:
        output_path = os.path.join(log_dir, "stats.json")
    print(f"Processing {total} log files in '{log_dir}'...")
    for idx, fname in enumerate(log_files, 1):
        fpath = os.path.join(log_dir, fname)
        try:
            game_stats = parse_log_file(fpath, processors)
            # Count games and errors
            if game_stats:
                all_stats.extend(game_stats)
                game_count += len(game_stats)
            else:
                error_count += 1
        except Exception as e:
            print(f"Error processing {fpath}: {e}", file=sys.stderr)
            error_count += 1
        # Simple progress bar
        bar_len = 40
        filled_len = int(bar_len * idx // total) if total else 0
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        print(f"[{bar}] {idx}/{total} files", end='\r', file=sys.stderr)
    print(file=sys.stderr)  # Newline after progress bar
    print(f"Writing stats to {output_path}")
    print(f"Total games processed: {game_count}")
    print(f"Total files with errors: {error_count}")
    with open(output_path, 'w', encoding='utf-8') as out:
        json.dump(all_stats, out, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process log files into structured stats.")
    parser.add_argument('log_dir', help="Directory containing .log files")
    parser.add_argument('--output', help="Output JSON file path (default: stats.json in log_dir)")
    args = parser.parse_args()
    processors = [BasicStatsProcessor()]
    process_log_directory(args.log_dir, args.output, processors)

if __name__ == '__main__':
    main()
