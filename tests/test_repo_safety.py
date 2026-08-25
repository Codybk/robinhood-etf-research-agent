import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_configuration_is_unambiguously_paper_only():
    config = json.loads((ROOT / "config" / "settings.json").read_text())
    assert config["mode"] == "PAPER_RESEARCH_ONLY"
    assert config["paper_only"] is True
    assert config["live_trading_enabled"] is False


def test_runtime_contains_no_robinhood_connection_or_mcp_endpoint():
    runtime = "\n".join(
        path.read_text().lower()
        for folder in ("src", "scripts")
        for path in (ROOT / folder).glob("*.py")
    )
    assert "agent.robinhood.com" not in runtime
    assert "robinhood.com/mcp" not in runtime
    assert "place_order" not in runtime
    assert "submit_order" not in runtime
