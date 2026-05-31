import pandas as pd

df = pd.read_csv("data/fixtures.csv")

# Only count Newcastle University players, excluding walkovers
home = df[(df["Home team"].str.contains("Newcastle University", na=False)) & (df["Home Player"] != "(walkover)")]["Home Player"]
away = df[(df["Away team"].str.contains("Newcastle University", na=False)) & (df["Away Player"] != "(walkover)")]["Away Player"]

counts = pd.concat([home, away]).value_counts().reset_index()
counts.columns = ["Player", "Matches Played"]

counts.to_csv("data/match_counts.csv", index=False)
print("Saved match_counts.csv")
