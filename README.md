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
- **ruff** for linting and formatting (dev)

## How to run

1. Create and activate a virtual environment
    ```python3 -m venv .venv```
2. Install dependencies:
    ```pip install .```
    For development (includes ruff):
    ```pip install -e ".[dev]"```

3. Run the scraper and paste a fixture URL when prompted:
    ```python3 main.py```
This writes data/fixtures.csv.
4. Generate match counts from the fixtures CSV:
    ```python3 countMatches.py```
This writes data/match_counts.csv.
Note: countMatches.py is currently hard‑coded to "Newcastle University".

## Testing

Install dev dependencies (includes pytest and pytest-recording):

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Tests run automatically on every push and pull request via GitHub Actions. Tests use [pytest-recording](https://github.com/kiwicom/pytest-recording) (VCR.py) to replay saved HTTP responses from `tests/cassettes/` — no network access needed. If the leaguemaster site changes its HTML structure, re-record with:

```bash
pytest tests/test_main.py --record-mode=new_episodes
```

Then commit the updated cassette files.

## Linting

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
ruff check .          # lint
ruff check --fix .    # lint and auto-fix
ruff format .         # format
```

## Arguments

- `--output`: the file that you wish to output the results to.
- `--count`: determines whether to save the number of times each player has played
- `--verbose`: Enable logging for debug level messages
- `--test`: Enable test mode to not fetch each url individually

## Configuration

### target-leagues.json

This files determines what geographical area will be scraped, what and what leagues will be searched, it's structure is:

```

{
  "areas": [
    {
      "name": area name e.g. "yorkshire",
      "url": area home page link e.g. "https://yorkshiresquash.leaguemaster.co.uk/cgi-county/icounty.exe",
      "competitions": [] the name of league to search e.g. ["Winter League 2024/25"] 
    },
  ]
}
```

## Code conventions

### Naming (PEP 8)

| Thing           | Style                 | Example                  |
|-----------------|-----------------------|--------------------------|
| Variables       | `snake_case`          | `home_player`            |
| Functions       | `snake_case`          | `scrape_fixtures()`      |
| Classes         | `PascalCase`          | `Player`                 |
| Constants       | `UPPER_SNAKE_CASE`    | `MAX_RETRIES`            |
| Modules / files | `snake_case`          | `count_matches.py`       |
| Private members | `_leading_underscore` | `_internal_helper()`     |

### Git branches

| Prefix   | When to use                       |
|----------|-----------------------------------|
| `feat/`  | New feature                       |
| `fix/`   | Bug fix                           |
| `chore/` | Maintenance, dependencies, config |
| `docs/`  | Documentation only                |

Example: `feat/add-player-stats`

### Git commits

[Conventional Commits](https://www.conventionalcommits.org) style:

```
feat: add match history export
fix: handle missing player cell in fixture row
chore: add ruff to CI workflow
docs: document --count argument
```

## Design notes

- The script asks for a Northumbria Squash fixture overview URL (team or club page).
- It fetches the overview page, collects all fixtureid links, and visits each fixture.
- For each fixture it parses player names, teams, and game scores from the match rows.
- Walkovers are detected and recorded as "(walkover)".
- Output is a flat CSV in data/ so it can be opened in Excel or further processed by
pandas.
