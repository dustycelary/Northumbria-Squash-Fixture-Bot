import pandas as pd


def get_player_count(df, team="Newcastle University"):
    involved = df[
        (df["Home Team"].str.contains(team, na=False) | df["Away Team"].str.contains(team, na=False))
        & (df["Home Player"] != "(walkover)")
        & (df["Away Player"] != "(walkover)")
    ]

    home = involved[["Home Player", "Home Team"]].rename(columns={"Home Player": "Player", "Home Team": "Team"})
    away = involved[["Away Player", "Away Team"]].rename(columns={"Away Player": "Player", "Away Team": "Team"})

    counts = (
        pd.concat([home, away])
        .groupby(["Player", "Team"])
        .size()
        .reset_index(name="Matches Played")
        .sort_values("Matches Played", ascending=False)
        .reset_index(drop=True)
    )

    return counts
