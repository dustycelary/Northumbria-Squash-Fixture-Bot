import json
from unittest.mock import mock_open, patch

import pytest

from league_searcher import get_areas

VALID_JSON = json.dumps(
    {
        "areas": [
            {
                "name": "Northumbria",
                "url": "https://example.com",
                "competitions": ["Winter 2025/26"],
            },
        ]
    }
)


def test_get_areas_returns_list():
    with patch("builtins.open", mock_open(read_data=VALID_JSON)):
        result = get_areas()

    assert isinstance(result, list)
    assert len(result) == 1
    area = result[0]
    assert "name" in area
    assert "url" in area
    assert "competitions" in area


def test_get_areas_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError("no such file")):
        with pytest.raises(FileNotFoundError):
            get_areas()


def test_get_areas_missing_key():
    bad_json = json.dumps({"not_areas": []})
    with patch("builtins.open", mock_open(read_data=bad_json)):
        with pytest.raises(KeyError):
            get_areas()
