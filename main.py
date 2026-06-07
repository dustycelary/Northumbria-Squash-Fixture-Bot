import argparse
import logging
import sys
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

import count_matches
from league_searcher import get_target_areas, get_target_leagues

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


def select_league(session: requests.Session, base_url: str, league_id: str) -> None:
    """Setting session cookie so it gets data from the correct league"""

    base_url = base_url.rstrip("/")
    resp = session.post(
        f"{base_url}/selectleague",
        data={"leagueid": league_id},
        allow_redirects=True,
    )
    resp.raise_for_status()
    return resp


def get_division_list(session: requests.Session, league_url: str) -> list[dict]:
    base_url = league_url.rstrip("/")
    team_list_url = f"{base_url}/showdivlist"
    resp = session.get(team_list_url)

    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    divisions = []

    for a in soup.find_all("a", href=True):
        if "showdivfixtures" not in a["href"]:
            continue
        tr = a.find_parent("tr")
        if not tr:
            continue

        cells = tr.find_all("td")
        if len(cells) < 3:
            continue

        divisions.append(
            {
                "division": cells[0].get_text(strip=True),
                "fixture_url": urljoin(base_url, a["href"]),
            }
        )

    return divisions


def scrape_fixtures(
    session: requests.Session, url: str, area: str, division: str, league: str
) -> list[dict]:
    """url should be of the fixture page"""
    logger.info("Fetching fixture list from %s", url)
    try:
        resp = session.get(url, timeout=20)
    except requests.RequestException as e:
        logging.error("Request failed for %s: %s", url, e)

    resp.raise_for_status()
    logger.debug("Got %d bytes from fixture list page", len(resp.content))
    soup = BeautifulSoup(resp.text, "html.parser")

    fixture_links = soup.select(
        'a[href*="fixtureid"]'
    )  # returns all the links to individual fixtures
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
                    "Expected 2+ team links in %s, got %d — skipping",
                    fixture_url,
                    len(teams),
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
                        "Area": area,
                        "Division": division,
                        "League": league,
                    }
                )
        except Exception as e:
            logger.warning("Skipping fixture %s: %s", fixture_url, e)

    return extracted


if __name__ == "__main__":
    session = requests.Session()
    all_rows = []
    args = parser.parse_args()
    for league in get_target_leagues():
        for area in get_target_areas():
            resp = select_league(session, area, league)
            divisions = get_division_list(session, area)
            if not divisions:
                logger.warning(
                    "No divisions found for league %s at %s - skipping", league, area
                )
                continue
            for division in divisions:
                rows = scrape_fixtures(
                    session,
                    division["fixture_url"],
                    area,
                    division["division"],
                    league,
                )

                all_rows.extend(rows)
                # for result in scrape_fixtures(team["ixture_url"]):
                # results["area"] = area
                # results["league"] = league

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    df = pd.DataFrame(all_rows)
    df.to_csv(args.output, index=False)
    logger.info("Saved %d rows to %s", len(df), args.output)

    if args.count:
        player_counts = count_matches.get_player_count(
            df,
        )
        player_counts.to_csv("data/match_counts.csv", index=False)
        logger.info("Saved match counts to data/match_counts.csv")
