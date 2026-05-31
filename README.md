# Northumbria squash league bot

This is for team captains and league organisers so they can easily get the statistics for every player within the league. This can help collect payments and give out awards.

## What it does

I made this because when I was team captain and collecting subs from all the players I had no idea how many matches everyone played, and the committee who want to reimburse some players had the same problem. To resolve this I would have had to manually go through each fixture, and add players to a count, so this saved lots of time. This is for all team captains who are facing the same problem.  

This will accept a url from the user, which must be to a fixture page on the [Northumbria squash homepage](https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showhome?) website, such as [Fixture page link](https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe/showteamfixtures?divisionid=1&teamid=181). Then it will go through each match on that list and add the scores and players into a spreadsheet in `data/`. After this it will add a second spreadsheet, which contains every single player in the fixture page specified, and how many matches they have played.

If a user wishes to narrow the search to a single team they should provide a URL for only that team.

## Tech Stack

- **Python 3**
- **requests** for HTTP fetching
- **beautifulsoup4** for HTML parsing
- **pandas** for CSV output and aggregation

## How to run

1. Create and activate a virtual environment
    ```python3 -m venv .venv```
2. Install dependencies:
    ```bash pip install -r requirements.txt```

3. Run the scraper and paste a fixture URL when prompted:
    ```python3 main.py```
This writes data/fixtures.csv.
4. Generate match counts from the fixtures CSV:
    ```python3 countMatches.py```
This writes data/match_counts.csv.
Note: countMatches.py is currently hard‑coded to “Newcastle University”.

Design notes

- The script asks for a Northumbria Squash fixture overview URL (team or club page).
- It fetches the overview page, collects all fixtureid links, and visits each fixture.
- For each fixture it parses player names, teams, and game scores from the match rows.
- Walkovers are detected and recorded as "(walkover)".
- Output is a flat CSV in data/ so it can be opened in Excel or further processed by
pandas.
