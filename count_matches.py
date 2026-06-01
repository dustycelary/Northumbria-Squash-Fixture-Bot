import logging

import pandas as pd

logger = logging.getLogger(__name__)


def get_player_count(df: pd.DataFrame) -> pd.DataFrame:
    """Count matches played per player across home and away appearances.

    Args:
        df: DataFrame with columns 'Home Player', 'Home Team',
            'Away Player', 'Away Team'.

    Returns:
        DataFrame with columns 'Player', 'Team', 'Matches Played', sorted descending.
        Walkovers are included with an empty Team value.
    """
    logger.debug("Building player counts from %d rows", len(df))

    home = df[["Home Player", "Home Team"]].rename(
        columns={"Home Player": "Player", "Home Team": "Team"}
    )
    away = df[["Away Player", "Away Team"]].rename(
        columns={"Away Player": "Player", "Away Team": "Team"}
    )

    combined = pd.concat([home, away])
    combined.loc[combined["Player"] == "(walkover)", "Team"] = ""

    counts = (
        combined.groupby(["Player", "Team"])
        .size()
        .reset_index(name="Matches Played")
        .sort_values("Matches Played", ascending=False)
        .reset_index(drop=True)
    )
    logger.info("Player count build: %d players found", len(counts))

    return counts
