import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL = "https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showteamfixtures?divisionid=1&teamid=48"
# URL = "https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showclubfixtures?clubid=19"
URL = input("Whats the URL of the fixture overview page?: ")
session = requests.Session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    }
)


# home_players = soup.select('td.matchplayer:nth-child(2), td.matchplayerwin:nth-child(2)')
# away_players = soup.select('td.matchplayer:nth-child(4), td.matchplayerwin:nth-child(4)')
# names = [p.get_text(strip=True) for p in home_players]                                                        ['Liam Gutcher', 'Yassin Behary', 'Joe Elliott', 'Dominic Cox', 'Will Digby']

# teams = soup.select('a[href*="showteam?teamid"]')
# home_team = teams[0].get_text(strip=True)  # 'Newcastle University 1'
# away_team = teams[1].get_text(strip=True)  # 'Northumberland 1B'

# teams = soup.select('a[href*="showteam?teamid"]')
# teams[0] = home, teams[1] = away


def make_columns(
    home_player, away_player, home_score, away_score, home_team, away_team, games
):
    row_dict["Home team"] = home_team
    row_dict["Home Player"] = home_player
    row_dict["N Games"] = home_score
    row_dict["Away team"] = away_team
    row_dict["Away Player"] = away_player
    row_dict["O games"] = away_score
    if True:
        print("Hello")

    row_dict["Games"] = games
    return row_dict
    # row_dict["Result"] = (
    # f"{cells[4].get_text(strip=True)} - {cells[5].get_text(strip=True)}"
    # )


resp = requests.get(URL, timeout=20)
resp.raise_for_status()


soup = BeautifulSoup(resp.text, "html.parser")

# Find the biggest table on the page
fixture_pages = soup.select('a[href*="fixtureid"]')
if not fixture_pages:
    raise RuntimeError("No tables found on page")


def check_walkover(home_player, away_player):
    if home_player == "(walkover)" or away_player == "(walkover)":
        return True
    return False


extracted = []

rows = []

for fixture in fixture_pages:
    yes = 2
    r = requests.get(
        urljoin(URL, fixture["href"]), timeout=20
    )  # pyright: ignore[reportArgumentType]
    r.raise_for_status()
    fixture_soup = BeautifulSoup(r.text, "html.parser")

    title = soup.select_one(".title").get_text(strip=True)
    first_part = title.split(":")[0]

    teams = fixture_soup.select('a[href*="showteam?teamid"]')
    home_team = teams[0].get_text(strip=True)
    away_team = teams[1].get_text(strip=True)

    target_data = fixture_soup.select("td.matchplayer")
    # match_rows = [row.find_parent("tr") for row in target_data]
    for row in fixture_soup.select("tr.firstRow, tr.secondRow"):
        row_dict = {}
        cells = row.find_all("td")
        if row.select("td.matchplayer"):
            games = cells[6].get_text(strip=True)
            home_player = cells[1].get_text(strip=True)
            away_player = cells[3].get_text(strip=True)
            if check_walkover(home_player, away_player):
                # row_dict = make_columns("(walkover)", "(walkover)", "0", "0", games)
                home_player = "(walkover)"
                away_player = "(walkover)"
                # row_dict["Newcastle"] = "(walkover)"
                # row_dict["Other"] = "(walkover)"
            row_dict = make_columns(
                home_player,
                away_player,
                cells[4].get_text(strip=True),
                cells[5].get_text(strip=True),
                home_team,
                away_team,
                games,
            )
            # row_dict["Newcastle"] = home_player
            # row_dict["Other"] = away_player
            # row_dict["Result"] = (
            #     f"{cells[4].get_text(strip=True)} - {cells[5].get_text(strip=True)}"
            # )
            # row_dict["Newcastle"] = away_player
            # row_dict["Other"] = home_player
            # row_dict["Result"] = (
            #     f"{cells[5].get_text(strip=True)} - {cells[4].get_text(strip=True)}"
            # )

            extracted.append(row_dict)
    # team = fixture_soup.find(name="a", string=re.compile("Newcastle University.*"))
    # team_location = team.find_parent("tr").find("th").get_text()


df = pd.DataFrame(extracted)
df.to_csv("data/fixtures.csv", index=False)

print("Saved fixtures.csv")
