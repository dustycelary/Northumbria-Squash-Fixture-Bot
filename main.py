import argparse
import logging
import sys
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

import count_matches

parser = argparse.ArgumentParser(description="Scrape northumbria squash fixtures")
parser.add_argument(
    "--url",
    default="https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showteamfixtures?divisionid=1&teamid=48",
    help="fixture overview page url",
)
parser.add_argument(
    "--verbose",
    "-v",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Enable debug logging",
)
parser.add_argument("--output", default="data/fixtures.csv", help="Output CSV path")
parser.add_argument(
    "--count",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Enable second file containing amount players have played",
)

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


def is_walkover(home_player: str, away_player: str) -> bool:
    return home_player == "(walkover)" or away_player == "(walkover)"


def scrape_fixtures(url: str) -> list[dict]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        }
    )
    session.cookies.update(
        {
            "Competition": "332",
            "CookieID": "328645322",
            "Owner": "LeagueMaster",
        }
    )
    logger.info("Fetching fixture list from %s", url)
    try:
        resp = session.get(url, timeout=20)
    except requests.RequestException as e:
        logging.error("Request failed for %s: %s", url, e)

    resp.raise_for_status()
    logger.debug("Got %d bytes from fixture list page", len(resp.content))
    soup = BeautifulSoup(resp.text, "html.parser")

    fixture_links = soup.select('a[href*="fixtureid"]')
    if not fixture_links:
        raise RuntimeError("No fixture links found on page")

    logger.info("Found %d fixture links", len(fixture_links))

    extracted = []
    for fixture in fixture_links:
        fixture_url = urljoin(url, fixture["href"])  # pyright: ignore[reportArgumentType]
        try:
            logger.debug("Fetching fixture: %s", fixture_url)
            try:
                r = session.get(fixture_url, timeout=20)
            except requests.RequestException as e:
                logging.error("Request failed for %s: %s", fixture_url, e)
                continue

            r.raise_for_status()
            fixture_soup = BeautifulSoup(r.text, "html.parser")

            teams = fixture_soup.select('a[href*="showteam?teamid"]')
            if len(teams) < 2:
                logger.warning(
                    "Expected 2+ team links in %s, got %d — skipping", fixture_url, len(teams)
                )
                continue

            home_team = teams[0].get_text(strip=True)
            away_team = teams[1].get_text(strip=True)

            logger.debug("Processing fixture: %s vs %s", home_team, away_team)

            for row in fixture_soup.select("tr.firstRow, tr.secondRow"):
                cells = row.find_all("td")
                if not row.select("td.matchplayer"):
                    continue
                if len(cells) < 7:
                    logger.warning(
                        "Row in %s vs %s has only %d cells — skipping row",
                        home_team,
                        away_team,
                        len(cells),
                    )
                    continue

                home_player = cells[1].get_text(strip=True)
                away_player = cells[3].get_text(strip=True)
                if is_walkover(home_player, away_player):
                    home_player = "(walkover)"
                    away_player = "(walkover)"

                extracted.append(
                    {
                        "Home Team": home_team,
                        "Home Player": home_player,
                        "Home Games": cells[4].get_text(strip=True),
                        "Away Team": away_team,
                        "Away Player": away_player,
                        "Away Games": cells[5].get_text(strip=True),
                        "Games": cells[6].get_text(strip=True),
                    }
                )
        except Exception as e:
            logger.warning("Skipping fixture %s: %s", fixture_url, e)

    return extracted


if __name__ == "__main__":
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    df = pd.DataFrame(scrape_fixtures(args.url))
    df.to_csv(args.output, index=False)
    logger.info("Saved %d rows to %s", len(df), args.output)

    if args.count:
        player_counts = count_matches.get_player_count(
            df,
        )
        player_counts.to_csv("data/match_counts.csv", index=False)
        logger.info("Saved match counts to data/match_counts.csv")
