import os
from collections import defaultdict
import json
import sys
import re
from typing import List, Dict, Any
import tqdm
import glob

def parse_card_info(data: str ) -> dict:
    '''
        Example: 
        Diamond Weapon|Set:FIN|Art:1|Type:Legendary Artifact Creature - Elemental|Power:8|Toughness:8|ManaCost:{7}{G}{G}|Tapped|Counters:Indestructible=1,P1P1=1|Attacking
    '''
    info = data.split("|")
    out = {
        "name": "NONE",
        "type": "NONE",
        "power": "NONE",
        "toughness": "NONE",
        "manacost": "NONE",
        "counters": {}
    }

    out["name"] = info[0]
    for subinfo in info[1:]:
        if ":" not in subinfo:
            continue
        try:
            field_name, field_data = subinfo.split(":")
        except ValueError:
            print("Trouble parsing ", subinfo)
            continue
        
        match field_name.lower():
            case "type":
                out["type"] = field_data
            case "power":
                out["power"] = int(field_data)
            case "toughness":
                out["toughness"] = int(field_data)
            case "manacost":
                out["manacost"] = field_data
            case "counters":
                counter_info = {}
                for counter_data in field_data.split(","):
                    counter_name, counter_count = counter_data.split("=")
                    counter_info[counter_name] = int(counter_count)
            case _:
                pass
    return out

def parse_card_list(data: str) -> dict:
    return [
        parse_card_info(x) for x in data.split(";")
    ]
def parse_game_state(data: str, player_names_in_order: list[str]) -> dict:
    out = {}

    data_as_dict = {}
    for row in data.split("\n"):
        try:
            field_name, field_data = row.split("=")
        except ValueError:
            continue
        data_as_dict[field_name] = field_data
    
    out["turn"] = int(data_as_dict["turn"])
    player_index = int(data_as_dict["activeplayer"][1]) #p0 or p1 -> 0 or 1
    assert player_index == 0 or player_index == 1, player_index
    out["activeplayer"] = player_names_in_order[player_index] 
    out["activephase"] = data_as_dict["activephase"]
    
    for k, player_name in enumerate(player_names_in_order):
        player_state = {}
        out[player_name] = player_state
        basename = f"p{k}"
        player_state["life"] = data_as_dict[f"{basename}life"]
        player_state["hand"] = parse_card_list(data_as_dict[f"{basename}hand"])
        
        for field_name in ["battlefield", "graveyard"]:
            combined_name = f"{basename}{field_name}"
            if combined_name in data_as_dict:
                player_state[field_name] = parse_card_list(data_as_dict[combined_name])

    return out

def parse_game_log_file(log_file) -> dict:
    current_event = None
    current_block = []

    first_line = log_file.readline().strip()
    assert first_line == "=== Players ===", f"Malformed first line: {first_line}"
    p1_name = log_file.readline().split(" - ")[0]
    p2_name = log_file.readline().split(" - ")[0]
    player_names = [p1_name, p2_name]

    out = {
        "turns": defaultdict(dict),
        "players": player_names,
        "winner": "NONE",
    }

    import traceback
    
    def handle_event_block(event: str, data: str):
        match event:
            case "forge.game.event.GameEventTurnPhase":
                if ("Main phase, precombat phase" in data or "Cleanup step phase" in data) and "Board state" in data:
                    try:
                        game_state = parse_game_state(data, player_names_in_order=player_names)
                        out["turns"][game_state["turn"]][game_state["activephase"]] = game_state
                    except Exception as e:
                        print("Error parsing block:")
                        print(data)
                        traceback.print_exc()
            case "forge.game.event.GameEventGameOutcome":
                assert data[:7] == "result=", f"Malformed result block data {data}"
                winners = re.findall(r"(.+) has won", data[7:])
                if len(winners) == 1:
                    out["winner"] = winners[0]
                else:
                    print(f"Warning: Expected exactly one winner, found {len(winners)}: {winners}")
            case _:
                pass

    for line in log_file:
        line = line.rstrip('\n')
        match = re.match(r"== GameEvent: (.+) ===", line)
        if match:
            if current_event:
                handle_event_block(current_event, "\n".join(current_block))
            current_event = match.group(1)
            current_block = []
        else:
            if current_event:
                current_block.append(line)
    if current_event:
        handle_event_block(current_event, "\n".join(current_block))

    return out



def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process log files into structured stats.")
    parser.add_argument(
        "experiment_dir",
        help="Experiment directory.")
    parser.add_argument("--f", help="Overwrite existing data.json", action="store_true")
    args = parser.parse_args()

    # Open info.json
    with open(os.path.join(args.experiment_dir, "info.json"), "r") as f:
        info_dict = json.load(f)

    output_file = os.path.join(args.experiment_dir, "data.json")
    if os.path.exists(output_file):
        if args.f:
            os.remove(output_file)
        else:
            raise FileExistsError(output_file)
    
    logs_dir = os.path.join(args.experiment_dir, "logs")

    logs_to_read = glob.glob("**/*.log", root_dir=logs_dir)
    all_data = {}
    for log_k, log_subpath in enumerate(logs_to_read):
        log_path = os.path.join(logs_dir, log_subpath)
        print("Parsing ", log_path)
        
        with open(log_path, "r") as f:
            all_data[f"game_{log_k:03d}"] = parse_game_log_file(f)

    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"Saved data to {output_file}")

if __name__ == '__main__':
    main()
