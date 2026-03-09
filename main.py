import requests, re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

# URL = "https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showteamfixtures?divisionid=1&teamid=48"
# URL = "https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showclubfixtures?clubid=19"
URL = input("Whats the URL of the fixture overview page?: ")
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
})

resp = requests.get(URL, timeout=20)
resp.raise_for_status()


soup = BeautifulSoup(resp.text, "html.parser")


# Find the biggest table on the page
fixture_pages = soup.select('a[href*="fixtureid"]')
if not fixture_pages:
    raise RuntimeError("No tables found on page")

rows = []
for fixture in fixture_pages:
    r = requests.get(urljoin(URL, fixture['href']), timeout=20)
    r.raise_for_status()
    fixture_soup = BeautifulSoup(r.text, "html.parser")

    target_data = fixture_soup.select('td.matchplayer')
    match_rows = [row.find_parent('tr') for row in target_data]
    team = fixture_soup.find(name='a', string=re.compile("Newcastle University.*"))
    team_location = team.find_parent('tr').find('th').get_text()
    team_dict = {
        "rows": [],
        "team_location": team_location,
        "team_name": team.get_text()
    }
    for row in match_rows:
        if row:
            team_dict["rows"].append(row)

    rows.append(team_dict)


# print(rows)
extracted = []
headers = []

for i, team_dict in enumerate(rows):
    for row in team_dict['rows']:
        print(f"Row: {row}")
        cells = row.find_all(["th", "td"])
        values = [c.get_text(" ") for c in cells]
        values.append(team_dict['team_location'])
        values.append(team_dict['team_name'])
        if not values:
            continue

        if i == 0 and row.find_all("th"):
            headers = values
        else:
            extracted.append(values)

width = max(len(r) for r in extracted)
extracted = [r + [""] * (width - len(r)) for r in extracted]
df = pd.DataFrame(extracted, columns=[f"col_{i}" for i in range(width)])

df.to_csv("data/fixtures.csv", index=False)
# df.to_json("fixtures.json", orient="records", indent=2)

print("Saved fixtures.csv")
print(df.head())
