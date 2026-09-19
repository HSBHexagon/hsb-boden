import os
import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))

from hsb_config import get_jordi_token, get_fc_refresh_token

def test_get_jordi_token_success(monkeypatch):
    monkeypatch.setenv("HSB_FC_REFRESH_TOKEN", "fake_refresh_token")

    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"access_token": "mocked_access_token_123"}).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        token = get_jordi_token()
        assert token == "mocked_access_token_123"
        assert mock_urlopen.call_count == 1

def test_get_jordi_token_retry_and_success(monkeypatch):
    monkeypatch.setenv("HSB_FC_REFRESH_TOKEN", "fake_refresh_token")

    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"access_token": "retry_success_token"}).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = None

    with patch("urllib.request.urlopen", side_effect=[Exception("Network glitch"), fake_response]) as mock_urlopen,          patch("time.sleep") as mock_sleep:
        token = get_jordi_token()
        assert token == "retry_success_token"
        assert mock_urlopen.call_count == 2
        mock_sleep.assert_called_once_with(1.5)

def test_get_jordi_token_max_retries_exceeded(monkeypatch):
    monkeypatch.setenv("HSB_FC_REFRESH_TOKEN", "fake_refresh_token")

    with patch("urllib.request.urlopen", side_effect=Exception("Persistent Error")) as mock_urlopen,          patch("time.sleep") as mock_sleep:
        with pytest.raises(Exception, match="Persistent Error"):
            get_jordi_token()
        assert mock_urlopen.call_count == 3
        assert mock_sleep.call_count == 2
