import argparse
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
parser.add_argument("--output", default="data/fixtures.csv", help="Output CSV path")
parser.add_argument(
    "--count",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Enable second file containing amount players have played",
)


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
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    with open("file.html", "w") as file:
        file.write(resp.text)
    fixture_links = soup.select('a[href*="fixtureid"]')
    if not fixture_links:
        raise RuntimeError("No fixture links found on page")

    extracted = []
    for fixture in fixture_links:
        r = session.get(urljoin(url, fixture["href"]), timeout=20)  # pyright: ignore[reportArgumentType]
        r.raise_for_status()
        fixture_soup = BeautifulSoup(r.text, "html.parser")

        teams = fixture_soup.select('a[href*="showteam?teamid"]')
        home_team = teams[0].get_text(strip=True)
        away_team = teams[1].get_text(strip=True)

        for row in fixture_soup.select("tr.firstRow, tr.secondRow"):
            cells = row.find_all("td")
            if not row.select("td.matchplayer"):
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

    return extracted


if __name__ == "__main__":
    args = parser.parse_args()
    df = pd.DataFrame(scrape_fixtures(args.url))
    df.to_csv(args.output, index=False)
    print(f"Saved {args.output}")

    if args.count:
        player_counts = count_matches.get_player_count(
            df,
        )
        player_counts.to_csv("data/match_counts.csv", index=False)
        print("Saved match_counts.csv")
