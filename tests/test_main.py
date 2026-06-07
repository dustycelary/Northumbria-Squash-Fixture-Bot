import pytest
import requests

from main import get_competition_id, get_division_list

BASE_URL = "https://northumbriasquash.leaguemaster.co.uk/cgi-county/icounty.exe"


# ---------------------------------------------------------------------------
# get_competition_id
# ---------------------------------------------------------------------------


@pytest.mark.vcr
def test_get_competition_id_resolves_name():
    session = requests.Session()
    comp_id = get_competition_id(session, BASE_URL, "Men's Winter 2025/26")
    assert comp_id == 332


@pytest.mark.vcr("test_get_competition_id_resolves_name.yaml")
def test_get_competition_id_case_insensitive():
    session = requests.Session()
    comp_id = get_competition_id(session, BASE_URL, "men's winter 2025/26")
    assert comp_id == 332


@pytest.mark.vcr("test_get_competition_id_resolves_name.yaml")
def test_get_competition_id_not_found():
    session = requests.Session()
    with pytest.raises(ValueError, match="not found"):
        get_competition_id(session, BASE_URL, "Nonexistent League")


# ---------------------------------------------------------------------------
# get_division_list
# ---------------------------------------------------------------------------


@pytest.mark.vcr
def test_get_division_list_returns_correct_domains():
    """All fixture_urls must use the northumbria base, not yorkshiresquash (bug fix)."""
    session = requests.Session()
    divisions = get_division_list(session, BASE_URL)

    assert len(divisions) > 0
    for div in divisions:
        assert div["fixture_url"].startswith("https://northumbriasquash"), (
            f"Expected northumbriasquash domain, got: {div['fixture_url']}"
        )
        assert "yorkshiresquash" not in div["fixture_url"]


@pytest.mark.vcr("test_get_division_list_returns_correct_domains.yaml")
def test_get_division_list_parses_names():
    session = requests.Session()
    divisions = get_division_list(session, BASE_URL)

    for div in divisions:
        assert isinstance(div["division"], str)
        assert len(div["division"]) > 0


def test_get_division_list_no_divisions():
    """No network needed — just pass HTML with no showdivfixtures links."""
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.text = "<html><body><p>Nothing here</p></body></html>"
    resp.raise_for_status = MagicMock()

    session = MagicMock(spec=requests.Session)
    session.get.return_value = resp

    divisions = get_division_list(session, BASE_URL)
    assert divisions == []
