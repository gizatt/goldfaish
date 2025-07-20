import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import abc
import argparse
import io
import base64
import matplotlib.colors as mcolors


def get_players(data: dict):
    return next(iter(data.values()))["players"]


def plot_traces_with_errorbars(ax,
                               traces,
                               trace_colors: None | list | str = None):

    for k, (x, y) in enumerate(traces):
        if isinstance(trace_colors, list):
            color = trace_colors[k]
        else:
            color = trace_colors or "gray"
        # Map the color to HSV, and then apply some jitter to the hue.
        rgb_color = mcolors.to_rgb(color)
        hsv_color = mcolors.rgb_to_hsv(np.array(rgb_color))
        hsv_color[0] = (hsv_color[0] + 0.1 *
                        (float(k) / len(traces)) - 0.05) % 1.0
        ax.plot(x, y, alpha=0.2, color=mcolors.hsv_to_rgb(hsv_color))

    # Stack all data
    if len(traces) > 0:
        X = np.concatenate([x for x, y in traces])
        Y = np.concatenate([y for x, y in traces])
    else:
        return

    # Group Y by X
    y_grouped_by_x = defaultdict(list)
    for x, y in zip(X, Y):
        y_grouped_by_x[x].append(y)
    turns_sorted = sorted(y_grouped_by_x.keys())
    means = []
    lowers = []
    uppers = []
    valid_x = []
    for t in turns_sorted:
        samples = y_grouped_by_x[t]
        if len(samples) >= 3:
            mu = np.mean(samples)
            sigma = np.std(samples, ddof=1)
            means.append(mu)
            # 95% CI for normal: mu ± 1.96 * sigma
            lowers.append(mu - 1.96 * sigma)
            uppers.append(mu + 1.96 * sigma)
            valid_x.append(t)
    if valid_x:
        ax.plot(valid_x, means, color="C0", label="Mean")
        ax.fill_between(valid_x,
                        lowers,
                        uppers,
                        color="C0",
                        alpha=0.2,
                        label="95% CI")


class DataPage:
    _subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        DataPage._subclasses.append(cls)

    @classmethod
    def get_subclasses(cls):
        return list(cls._subclasses)

    @staticmethod
    @abc.abstractmethod
    def title():
        ...

    @staticmethod
    @abc.abstractmethod
    def make(data: dict):
        ...


class FieldSizeByTurn(DataPage):

    @staticmethod
    def title():
        return "Hand/Field/GY Size"

    def make(data: dict):
        players = get_players(data)
        fields = ["hand", "battlefield", "graveyard", "exile", "library"]
        fig, axes = plt.subplots(
            nrows=len(fields),
            ncols=len(players),
            figsize=(4 * len(players), 3 * len(fields)),
            dpi=300,
            sharex='all',
            sharey='row',
        )
        phase = "MAIN1"

        for i, player in enumerate(players):
            for j, field in enumerate(fields):
                ax = axes[j, i]
                all_traces = []
                trace_colors = []
                # Collect all traces for this player
                for game in data.values():
                    if game["winner"] not in players:
                        continue
                    turns = []
                    field_sizes = []
                    for turn_index, turn in game["turns"].items():
                        if turn[phase]["activeplayer"] != player:
                            continue
                        turns.append(int(turn_index) // 2)
                        field_sizes.append(
                            turn[phase][player]["field_sizes"][field])
                    if turns:
                        all_traces.append(
                            (np.array(turns), np.array(field_sizes)))
                        trace_colors.append("green" if game["winner"] ==
                                            player else "red")

                plot_traces_with_errorbars(ax, all_traces, trace_colors)
                ax.set_title(player)
                ax.set_xlabel("Turn")
                ax.set_ylabel(f"Size of {field} at start of {phase}")
                ax.tick_params(
                    axis='x',
                    labelbottom=True)  # Ensure tick labels are visible
                ax.tick_params(
                    axis='y', labelleft=True)  # Ensure tick labels are visible
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        img_html = f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>'
        return img_html


class LandsAndCreaturesOnBoard(DataPage):

    @staticmethod
    def title():
        return "Board Presence"

    @staticmethod
    def make(data: dict):
        players = get_players(data)
        categories = [
            ("Lands", lambda card: "land" in card["type"].lower()),
            ("Mana production", lambda card: card["maxmanaproduced"]),
            ("Creatures", lambda card: "creature" in card["type"].lower()),
            ("Nonland Permanents",
             lambda card: "land" not in card["type"].lower()),
            ("Total Power", lambda card: card["power"]
             if card["power"] != "NONE" else 0),
            ("Total Toughness", lambda card: card["toughness"]
             if card["toughness"] != "NONE" else 0),
        ]

        fig, axes = plt.subplots(
            nrows=len(categories),
            ncols=len(players),
            figsize=(4 * len(players), 3 * len(categories)),
            dpi=300,
            sharex='all',
            sharey='row',
        )
        if len(players) == 1 and len(categories) == 1:
            axes = np.array([[axes]])
        elif len(players) == 1:
            axes = axes[:, np.newaxis]
        elif len(categories) == 1:
            axes = axes[np.newaxis, :]

        for col, player in enumerate(players):
            for row, (cat_name, cat_fn) in enumerate(categories):
                traces = []
                trace_colors = []
                for game in data.values():
                    if game["winner"] not in players:
                        continue
                    turns = []
                    counts = []
                    for turn_index, turn in game["turns"].items():
                        if "battlefield" in turn["MAIN1"][player]:
                            battlefield = turn["MAIN1"][player]["battlefield"]
                            count = sum(
                                cat_fn(card) for card in battlefield
                                if card["type"] != "NONE")
                        else:
                            count = 0
                        turns.append(float(turn_index) / 2.)
                        counts.append(count)
                    if turns:
                        traces.append((np.array(turns), np.array(counts)))
                        trace_colors.append("green" if game["winner"] ==
                                            player else "red")
                ax = axes[row, col]
                plot_traces_with_errorbars(ax, traces, trace_colors)
                if row == 0:
                    ax.set_title(player)
                if col == 0:
                    ax.set_ylabel(cat_name)
                ax.set_xlabel("Turn")
                ax.tick_params(
                    axis='x',
                    labelbottom=True)  # Ensure tick labels are visible
                ax.tick_params(
                    axis='y', labelleft=True)  # Ensure tick labels are visible
                ax.legend(fontsize=8, loc="upper left")
                if cat_name in ("Lands", "Mana production"):
                    one_drop_per_turn = np.linspace(0, 100, num=10)
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    ax.plot(one_drop_per_turn,
                            one_drop_per_turn,
                            linestyle="--",
                            alpha=0.5,
                            color="orange")
                    ax.set_xlim(xlim)
                    ax.set_ylim(ylim)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        img_html = f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>'
        return img_html


class Life(DataPage):

    @staticmethod
    def title():
        return "Life"

    @staticmethod
    def make(data: dict):
        players = get_players(data)
        plt.figure(dpi=300).set_size_inches(12, 6)

        fig, axes = plt.subplots(
            nrows=3,
            ncols=len(players),
            figsize=(6 * len(players), 3 * 6),
            dpi=300,
            sharex='all',
            sharey='row',
        )

        for i, player in enumerate(players):
            all_traces = []
            won_traces = []
            lost_traces = []
            trace_colors = []
            # Collect all traces for this player
            for game in data.values():
                if game["winner"] not in players:
                    continue
                turns = []
                life_totals = []
                for turn_index, turn in game["turns"].items():
                    turns.append(float(turn_index) / 2.)
                    life_totals.append(int(turn["MAIN1"][player]["life"]))
                if turns:
                    all_traces.append((np.array(turns), np.array(life_totals)))
                    won = game["winner"] == player
                    if won:
                        won_traces.append(all_traces[-1])
                    else:
                        lost_traces.append(all_traces[-1])
                    trace_colors.append("green" if won else "red")

            # Combined plot
            ax = axes[0, i]
            plot_traces_with_errorbars(ax, all_traces, trace_colors)
            ax.set_title(player)
            ax.set_xlabel("Turn")
            ax.set_ylabel("Life")
            ax.tick_params(axis='x',
                           labelbottom=True)  # Ensure tick labels are visible
            ax.tick_params(axis='y',
                           labelleft=True)  # Ensure tick labels are visible

            ax = axes[1, i]
            plot_traces_with_errorbars(ax, won_traces, "green")
            ax.set_title("Only winning games")
            ax.set_xlabel("Turn")
            ax.set_ylabel("Life")
            ax.tick_params(axis='x',
                           labelbottom=True)  # Ensure tick labels are visible
            ax.tick_params(axis='y',
                           labelleft=True)  # Ensure tick labels are visible

            ax = axes[2, i]
            plot_traces_with_errorbars(ax, lost_traces, "red")
            ax.set_title("Only losing games")
            ax.set_xlabel("Turn")
            ax.set_ylabel("Life")
            ax.tick_params(axis='x',
                           labelbottom=True)  # Ensure tick labels are visible
            ax.tick_params(axis='y',
                           labelleft=True)  # Ensure tick labels are visible

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        img_html = f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>'
        return img_html


class Winning(DataPage):

    @staticmethod
    def title():
        return "Win Rate and Speed"

    @staticmethod
    def make(data: dict):
        players = get_players(data)
        plt.figure(dpi=300).set_size_inches(6, 12)

        games_won = {player: 0 for player in players}
        games_won_by_reason = {player: defaultdict(int) for player in players}
        won_durations = {player: [] for player in players}
        all_wincons = set()
        for game in data.values():
            winner = game["winner"]
            if winner not in players:
                continue
            loss_reason = game.get("loss_reason",
                                   "unknown wincon, reprocess logs")
            all_wincons.add(loss_reason)
            games_won[game["winner"]] += 1
            games_won_by_reason[game["winner"]][loss_reason] += 1
            won_durations[game["winner"]].append(len(game["turns"]) / 2.)

        ax = plt.subplot(2, 1, 1)
        total_games = sum(list(games_won.values()))
        bottom = np.zeros(len(players))
        for wincon in all_wincons:
            heights = np.array([
                games_won_by_reason[player][wincon] for player in players
            ])  # / total_games
            ax.bar(players, heights, bottom=bottom, label=wincon)
            bottom += heights
        plt.legend()
        plt.title("Games Won (N=%d)" % total_games)

        plt.subplot(2, 1, 2)
        for k, player in enumerate(players):
            turns = sorted(won_durations[player])
            if not turns:
                continue
            y = np.arange(1, len(turns) + 1) / len(turns)
            plt.step(turns, y, where='post', label=player)
        plt.title('CDF of Win Turn')
        plt.xlabel('Win Turn')
        plt.ylabel('CDF')
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        img_html = f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>'
        return img_html


def make_html(data: dict, title):
    # Generate HTML tabs for each DataPage subclass
    subclasses = DataPage.get_subclasses()
    tab_headers = []
    tab_contents = []

    for i, cls in enumerate(subclasses):
        print("Adding tab for ", cls.title())
        tab_id = f"tab{i}"
        tab_headers.append(
            f'<button class="tablinks" onclick="openTab(event, \'{tab_id}\')">{cls.title()}</button>'
        )
        try:
            content = cls.make(data)
        except NotImplementedError:
            content = "<em>Not implemented</em>"
        tab_contents.append(
            f'<div id="{tab_id}" class="tabcontent" style="display:none">{content}</div>'
        )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <style>
    .tab {{
      overflow: hidden;
      border-bottom: 1px solid #ccc;
    }}
    .tab button {{
      background-color: inherit;
      border: none;
      outline: none;
      cursor: pointer;
      padding: 14px 16px;
      transition: 0.3s;
      font-size: 17px;
    }}
    .tab button:hover {{
      background-color: #ddd;
    }}
    .tabcontent {{
      display: none;
      padding: 6px 12px;
      border-top: none;
    }}
    </style>
    </head>
    <body>

    <div class="tab">
      {''.join(tab_headers)}
    </div>
    {''.join(tab_contents)}

    <script>
    function openTab(evt, tabName) {{
      var i, tabcontent, tablinks;
      tabcontent = document.getElementsByClassName("tabcontent");
      for (i = 0; i < tabcontent.length; i++) {{
        tabcontent[i].style.display = "none";
      }}
      tablinks = document.getElementsByClassName("tablinks");
      for (i = 0; i < tablinks.length; i++) {{
        tablinks[i].className = tablinks[i].className.replace(" active", "");
      }}
      document.getElementById(tabName).style.display = "block";
      evt.currentTarget.className += " active";
    }}
    // Open first tab by default
    document.addEventListener("DOMContentLoaded", function() {{
        document.querySelector(".tablinks").click();
    }});
    </script>

    </body>
    </html>
    """
    return html


def main():
    parser = argparse.ArgumentParser(
        description="Process log files into structured stats.")
    parser.add_argument("experiment_dir", help="Experiment directory.")
    args = parser.parse_args()

    data_json = os.path.join(args.experiment_dir, "data.json")
    assert os.path.exists(data_json), data_json

    with open(data_json, "r") as f:
        data = json.load(f)

    html = make_html(data, args.experiment_dir)
    with open(os.path.join(args.experiment_dir, "index.html"),
              "w",
              encoding="utf-8") as f:
        f.write(html)


if __name__ == '__main__':
    main()
