import pandas as pd


def get_player_count(df):
    home = df[["Home Player", "Home Team"]].rename(
        columns={"Home Player": "Player", "Home Team": "Team"}
    )
    away = df[["Away Player", "Away Team"]].rename(
        columns={"Away Player": "Player", "Away Team": "Team"}
    )

    combined = pd.concat([home, away])
    combined.loc[combined["Player"] == "(walkover)", "Team"] = ""

    counts = (
        combined
        .groupby(["Player", "Team"])
        .size()
        .reset_index(name="Matches Played")
        .sort_values("Matches Played", ascending=False)
        .reset_index(drop=True)
    )

    return counts
