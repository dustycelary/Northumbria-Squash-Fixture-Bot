import argparse
import logging
import sys
import time
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

import count_matches
from league_searcher import get_areas

parser = argparse.ArgumentParser(description="Scrape northumbria squash fixtures")
parser.add_argument(
    "--verbose",
    "-v",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Enable debug logging",
)
parser.add_argument(
    "--test",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Enable test mode",
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


def get_competition_id(
    session: requests.Session, base_url: str, league_name: str
) -> int:
    """Look up the numeric compid for a league name string."""
    base_url = base_url.rstrip("/")
    resp = session.get(f"{base_url}/showleaguelist", timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for opt in soup.find_all("option"):
        if opt.get_text(strip=True).lower() == league_name.lower():
            return int(opt["value"])
    available = [opt.get_text(strip=True) for opt in soup.find_all("option")]
    raise ValueError(
        f"League {league_name!r} not found at {base_url}. Available: {available}"
    )


def select_competition(session: requests.Session, base_url: str, comp_id: int) -> None:
    """Select a competition by numeric ID via the changecompetition endpoint."""
    base_url = base_url.rstrip("/")
    resp = session.get(
        f"{base_url}/changecompetition",
        params={"compid": comp_id},
        timeout=20,
    )
    resp.raise_for_status()
    logger.debug("select_competition compid=%s final URL: %s", comp_id, resp.url)


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

        # Strip the host from the href and re-join with base_url so we always
        # hit the correct area's server, not whatever domain the page linked to.
        href = a["href"]
        parsed = urlparse(href)
        path_only = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        divisions.append(
            {
                "division": cells[0].get_text(strip=True),
                "fixture_url": urljoin(base_url, path_only),
            }
        )

    return divisions


def scrape_fixtures(
    session: requests.Session, url: str, area: str, division: str, league: str
) -> list[dict]:
    """url should be of the fixture page"""
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
    all_rows = []
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    for area in get_areas():
        for comp_name in area["competitions"]:
            session = requests.Session()
            try:
                comp_id = get_competition_id(session, area["url"], comp_name)
            except ValueError as e:
                logger.warning(e)
                continue
            logger.info(
                "Resolved %r -> compid=%s (%s)", comp_name, comp_id, area["name"]
            )
            select_competition(session, area["url"], comp_id)
            divisions = get_division_list(session, area["url"])
            if not divisions:
                logger.warning(
                    "No divisions found for compid=%s at %s - skipping",
                    comp_id,
                    area["url"],
                )
                continue
            for division in divisions:
                logger.info("Fetching fixture list from %s", division["fixture_url"])
                if args.test:
                    continue
                rows = scrape_fixtures(
                    session,
                    division["fixture_url"],
                    area["name"],
                    division["division"],
                    comp_name,
                )
                all_rows.extend(rows)
                time.sleep(1)

    if not args.test:
        df = pd.DataFrame(all_rows)
        df.to_csv(args.output, index=False)
        logger.info("Saved %d rows to %s", len(df), args.output)

    if args.count:
        player_counts = count_matches.get_player_count(
            df,
        )
        player_counts.to_csv("data/match_counts.csv", index=False)
        logger.info("Saved match counts to data/match_counts.csv")
