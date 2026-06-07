import json


def get_areas() -> list[dict]:
    """Return list of area dicts with keys: name, url, competitions."""
    try:
        with open("./data/target-leagues.json") as f:
            data = json.loads(f.read())
    except FileNotFoundError as e:
        print(e)
        raise
    return data["areas"]
