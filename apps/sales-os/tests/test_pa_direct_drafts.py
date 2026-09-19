"""
Unit tests for Power Automate Direct Drafts configuration (pa_direct_drafts.py).
Tests environment variable overrides and fallback defaults.
"""
import importlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))


def test_pa_direct_drafts_defaults():
    import pa_direct_drafts

    assert pa_direct_drafts.APIHUB_RESOURCE_TOKEN == "https://apihub.azure.com"
    assert pa_direct_drafts.PPAPI_RESOURCE_TOKEN == "https://service.powerapps.com/"
    assert pa_direct_drafts.FLOW_RESOURCE_TOKEN == "https://service.flow.microsoft.com/"
    assert pa_direct_drafts.FLOW_API_BASE == "https://api.flow.microsoft.com"
    assert pa_direct_drafts.FLOW_ENV == "Default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30"
    assert (
        pa_direct_drafts.PPAPI_BASE
        == "https://default8adbbf2efd2c48578540bbcdb3a20f.30.environment.api.powerplatform.com"
    )


def test_pa_direct_drafts_env_overrides(monkeypatch):
    import pa_direct_drafts

    custom_apihub = "https://custom.apihub.azure.com"
    custom_ppapi_token = "https://custom.service.powerapps.com/"
    custom_ppapi_base = "https://custom.environment.api.powerplatform.com"
    custom_flow_base = "https://custom.api.flow.microsoft.com"
    custom_flow_env = "Custom-Env-12345"
    custom_flow_token = "https://custom.service.flow.microsoft.com/"

    monkeypatch.setenv("APIHUB_RESOURCE_TOKEN", custom_apihub)
    monkeypatch.setenv("PPAPI_RESOURCE_TOKEN", custom_ppapi_token)
    monkeypatch.setenv("PPAPI_BASE", custom_ppapi_base)
    monkeypatch.setenv("FLOW_API_BASE", custom_flow_base)
    monkeypatch.setenv("FLOW_ENV", custom_flow_env)
    monkeypatch.setenv("FLOW_RESOURCE_TOKEN", custom_flow_token)

    importlib.reload(pa_direct_drafts)

    assert pa_direct_drafts.APIHUB_RESOURCE_TOKEN == custom_apihub
    assert pa_direct_drafts.PPAPI_RESOURCE_TOKEN == custom_ppapi_token
    assert pa_direct_drafts.PPAPI_BASE == custom_ppapi_base
    assert pa_direct_drafts.FLOW_API_BASE == custom_flow_base
    assert pa_direct_drafts.FLOW_ENV == custom_flow_env
    assert pa_direct_drafts.FLOW_RESOURCE_TOKEN == custom_flow_token

    # Clean up reload back to default
    monkeypatch.delenv("APIHUB_RESOURCE_TOKEN", raising=False)
    monkeypatch.delenv("PPAPI_RESOURCE_TOKEN", raising=False)
    monkeypatch.delenv("PPAPI_BASE", raising=False)
    monkeypatch.delenv("FLOW_API_BASE", raising=False)
    monkeypatch.delenv("FLOW_ENV", raising=False)
    monkeypatch.delenv("FLOW_RESOURCE_TOKEN", raising=False)
    importlib.reload(pa_direct_drafts)
