import os
import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict


def load_stats(stats_path):
    with open(stats_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def plot_cumulative_damage(stats, out_dir):
    files = {}
    for player in ['Ai(1)', 'Ai(2)']:
        plt.figure(figsize=(8, 5))
        for i, game in enumerate(stats):
            turns = game['turns']
            cum_damage = np.cumsum([t['damage_taken'][player] for t in turns])
            plt.plot(range(1,
                           len(turns) + 1),
                     cum_damage,
                     label=f"Game {i+1}",
                     alpha=0.5,
                     linewidth=1)
        plt.title(f'Cumulative Damage Taken by Turn ({player})')
        plt.xlabel('Turn')
        plt.ylabel('Cumulative Damage')
        out_path = os.path.join(out_dir, f'cumulative_damage_{player}.png')
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        files[player] = f'cumulative_damage_{player}.png'
    # New: plot difference in total cumulative damage taken between Ai(1) and Ai(2)
    plt.figure(figsize=(8, 5))
    for i, game in enumerate(stats):
        turns = game['turns']
        cum_damage_1 = np.cumsum([t['damage_taken']['Ai(1)'] for t in turns])
        cum_damage_2 = np.cumsum([t['damage_taken']['Ai(2)'] for t in turns])
        damage_diff = cum_damage_2 - cum_damage_1  # Positive: Ai(2) has taken more damage
        plt.plot(range(1, len(turns) + 1), damage_diff, label=f"Game {i+1}", alpha=0.5, linewidth=1)
    plt.title('Cumulative Damage Difference by Turn (Ai(2) - Ai(1))')
    plt.xlabel('Turn')
    plt.ylabel('Cumulative Damage Difference')
    plt.axhline(0, color='gray', linestyle='--', linewidth=1)
    out_path = os.path.join(out_dir, 'cumulative_damage_difference.png')
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    files['cumulative_damage_difference'] = 'cumulative_damage_difference.png'
    return files


def plot_win_rate(stats, out_dir):
    win_counts = defaultdict(int)
    total_counts = defaultdict(int)
    deck_names = {}
    for game in stats:
        for pid, deck in game['players'].items():
            deck_names[pid] = deck
        winner = game['winner']
        win_counts[winner] += 1
        for pid in ['Ai(1)', 'Ai(2)']:
            total_counts[pid] += 1
    x = [f"{pid} ({deck_names[pid]})" for pid in ['Ai(1)', 'Ai(2)']]
    y = [win_counts[pid]/total_counts[pid] if total_counts[pid] else 0 for pid in ['Ai(1)', 'Ai(2)']]
    plt.figure(figsize=(6, 4))
    plt.bar(x, y, color=['#1f77b4', '#ff7f0e'])
    plt.title('Win Rate per Player')
    plt.ylabel('Win Rate')
    plt.ylim(0, 1)
    for i, v in enumerate(y):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center')
    out_path = os.path.join(out_dir, 'win_rate.png')
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return 'win_rate.png'


def plot_win_turn_cdf(stats, out_dir):
    win_turns = defaultdict(list)
    for game in stats:
        winner = game['winner']
        win_turn = game['win_turn']
        win_turns[winner].append(win_turn)
    plt.figure(figsize=(7, 4))
    percentiles = {}
    for pid in ['Ai(1)', 'Ai(2)']:
        turns = sorted(win_turns[pid])
        if not turns:
            continue
        y = np.arange(1, len(turns)+1) / len(turns)
        plt.step(turns, y, where='post', label=pid)
        # Compute percentiles
        percentiles[pid] = {}
        for p in [10, 25, 50, 75, 90]:
            if len(turns) > 0:
                percentiles[pid][p] = np.percentile(turns, p, method='nearest')
            else:
                percentiles[pid][p] = None
    plt.title('CDF of Win Turn (by Winner)')
    plt.xlabel('Win Turn')
    plt.ylabel('CDF')
    plt.legend()
    out_path = os.path.join(out_dir, 'win_turn_cdf.png')
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return 'win_turn_cdf.png', percentiles


def write_html(stats, out_dir, plot_files, win_turn_percentiles=None):
    # Compute games won by each player
    games_won = {'Ai(1)': [], 'Ai(2)': []}
    for i, game in enumerate(stats):
        winner = game['winner']
        if winner in games_won:
            games_won[winner].append(i+1)  # 1-based game index
    # Get player and deck names for title
    if stats and 'players' in stats[0]:
        deck_names = stats[0]['players']
        player1 = f"Ai(1) ({deck_names.get('Ai(1)','')})"
        player2 = f"Ai(2) ({deck_names.get('Ai(2)','')})"
        matchup_title = f"{player1} vs {player2}"
    else:
        matchup_title = "Game Stats Dashboard"
    html_path = os.path.join(out_dir, 'stats.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'/>
            <title>{matchup_title}</title>
            <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <style>
                body {{ margin: 2em; }}
                .tab-content {{ margin-top: 1em; }}
                pre {{ background: #f8f8f8; padding: 1em; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; }}
            </style>
        </head>
        <body>
            <div class=\"container-fluid\">
                <h1 class=\"mb-4\">{matchup_title}</h1>
                <ul class=\"nav nav-tabs\" id=\"mainTab\" role=\"tablist\">
                    <li class=\"nav-item\" role=\"presentation\">
                        <button class=\"nav-link active\" id=\"tab1-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#tab1\" type=\"button\" role=\"tab\">Cumulative Damage by Turn</button>
                    </li>
                    <li class=\"nav-item\" role=\"presentation\">
                        <button class=\"nav-link\" id=\"tab1b-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#tab1b\" type=\"button\" role=\"tab\">Cumulative Damage Difference by Turn</button>
                    </li>
                    <li class=\"nav-item\" role=\"presentation\">
                        <button class=\"nav-link\" id=\"tab2-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#tab2\" type=\"button\" role=\"tab\">Win Rate per Player</button>
                    </li>
                    <li class=\"nav-item\" role=\"presentation\">
                        <button class=\"nav-link\" id=\"tab3-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#tab3\" type=\"button\" role=\"tab\">CDF of Win Turn</button>
                    </li>
                    <li class=\"nav-item\" role=\"presentation\">
                        <button class=\"nav-link\" id=\"tab4-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#tab4\" type=\"button\" role=\"tab\">Game Logs</button>
                    </li>
                </ul>
                <div class=\"tab-content\" id=\"mainTabContent\">
                    <div class=\"tab-pane fade show active\" id=\"tab1\" role=\"tabpanel\">
                        <h4>Cumulative Damage: Ai(1)</h4>
                        <img src=\"{cumulative_Ai1}\" alt=\"Cumulative Damage by Turn: Ai(1)\">
                        <h4 class=\"mt-4\">Cumulative Damage: Ai(2)</h4>
                        <img src=\"{cumulative_Ai2}\" alt=\"Cumulative Damage by Turn: Ai(2)\">
                    </div>
                    <div class=\"tab-pane fade\" id=\"tab1b\" role=\"tabpanel\">
                        <h4>Cumulative Damage Difference by Turn (Ai(2) - Ai(1))</h4>
                        <img src=\"{cumulative_damage_difference}\" alt=\"Cumulative Damage Difference by Turn\">
                    </div>
                    <div class=\"tab-pane fade\" id=\"tab2\" role=\"tabpanel\">
                        <img src=\"{winrate}\" alt=\"Win Rate per Player\">
                        <div class=\"row mt-4\">
                            <div class=\"col-md-6\">
                                <h5>Games won by Ai(1):</h5>
                                <p>{games1}</p>
                            </div>
                            <div class=\"col-md-6\">
                                <h5>Games won by Ai(2):</h5>
                                <p>{games2}</p>
                            </div>
                        </div>
                    </div>
                    <div class=\"tab-pane fade\" id=\"tab3\" role=\"tabpanel\">
                        <img src=\"{cdf}\" alt=\"CDF of Win Turn\">
        """.format(
            matchup_title=matchup_title,
            cumulative_Ai1=plot_files['cumulative_Ai(1)'],
            cumulative_Ai2=plot_files['cumulative_Ai(2)'],
            cumulative_damage_difference=plot_files['cumulative_damage_difference'],  # Add new plot
            winrate=plot_files['winrate'],
            cdf=plot_files['cdf'],
            games1=(', '.join(str(g) for g in games_won['Ai(1)'])) or 'None',
            games2=(', '.join(str(g) for g in games_won['Ai(2)'])) or 'None',
        ))
        # Add percentile summary below the CDF plot
        if win_turn_percentiles:
            f.write('<div class="mt-3">')
            for pid in ['Ai(1)', 'Ai(2)']:
                if pid in win_turn_percentiles:
                    f.write(f'<h6>{pid}:</h6><ul>')
                    for p in [10, 25, 50, 75, 90]:
                        val = win_turn_percentiles[pid].get(p)
                        if val is not None:
                            f.write(f'<li>{p}% of games finish on or before turn {val}</li>')
                    f.write('</ul>')
            f.write('</div>')
        f.write("""
                    </div>
                    <div class="tab-pane fade" id="tab4" role="tabpanel">
                        <ul class="nav nav-tabs" id="logTab" role="tablist">
        """)
        for i, game in enumerate(stats):
            f.write(f'''<li class="nav-item" role="presentation">
                <button class="nav-link{' active' if i==0 else ''}" id="logtab{i}-tab" data-bs-toggle="tab" data-bs-target="#logtab{i}" type="button" role="tab">Game {i+1}</button>
            </li>''')
        f.write("""
                        </ul>
                        <div class="tab-content" id="logTabContent">
        """)
        for i, game in enumerate(stats):
            f.write(f'''<div class="tab-pane fade{' show active' if i==0 else ''}" id="logtab{i}" role="tabpanel">
                <h5>Players: {game['players']}</h5>
                <pre style="max-height:400px;overflow-y:auto;">{game['raw_log'].replace('<','&lt;').replace('>','&gt;')}</pre>
            </div>''')
        f.write("""
                        </div>
                    </div>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """)
    print(f"Wrote dashboard to {html_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Plot stats from stats.json and create stats.html.")
    parser.add_argument('log_dir', help="Directory containing stats.json")
    args = parser.parse_args()
    stats_path = os.path.join(args.log_dir, 'stats.json')
    if not os.path.exists(stats_path):
        print(f"stats.json not found in {args.log_dir}", file=sys.stderr)
        sys.exit(1)
    stats = load_stats(stats_path)
    cumulative_files = plot_cumulative_damage(stats, args.log_dir)
    cdf_file, win_turn_percentiles = plot_win_turn_cdf(stats, args.log_dir)
    plot_files = {
        'cumulative_Ai(1)': cumulative_files['Ai(1)'],
        'cumulative_Ai(2)': cumulative_files['Ai(2)'],
        'cumulative_damage_difference': cumulative_files['cumulative_damage_difference'],  # Update key
        'winrate': plot_win_rate(stats, args.log_dir),
        'cdf': cdf_file,
    }
    write_html(stats, args.log_dir, plot_files, win_turn_percentiles=win_turn_percentiles)


if __name__ == '__main__':
    main()
