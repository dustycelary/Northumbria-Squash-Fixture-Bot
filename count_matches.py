import pandas as pd


# Only count Newcastle University players, excluding walkovers
def get_newcastle_university_player_count(df):

    home = df[
        (df["Home Team"].str.contains("Newcastle University", na=False))
        & (df["Home Player"] != "(walkover)")
    ]["Home Player"]
    away = df[
        (df["Away Team"].str.contains("Newcastle University", na=False))
        & (df["Away Player"] != "(walkover)")
    ]["Away Player"]

    counts = pd.concat([home, away]).value_counts().reset_index()
    counts.columns = ["Player", "Matches Played"]

    return counts
