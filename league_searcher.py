import json


def get_target_areas():
    try:
        with open("./data/target-leagues.json") as league_file:
            league_area = json.loads(league_file.read())
    except FileNotFoundError as e:
        print(e)
        raise
    return league_area["league-link"]


def get_target_leagues():
    try:
        with open("./data/target-leagues.json") as league_file:
            leagues = json.loads(league_file.read())
    except FileNotFoundError as e:
        print(e)
        raise
    return leagues["target-leagues"]
