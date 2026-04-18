import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_591.client import Client591
from mcp_591.server import _filter_listing, _LISTING_KEYS, search_sale

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _mock_resp(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


class TestFilterListing:
    def test_only_keeps_allowed_keys(self):
        raw = _load("search_sale.json")
        listings = [h for h in raw["data"] if "post_id" in h]
        for h in listings:
            filtered = _filter_listing(h)
            assert set(filtered.keys()) <= _LISTING_KEYS

    def test_drops_noise_fields(self):
        raw = _load("search_sale.json")
        h = next(x for x in raw["data"] if "post_id" in x)
        filtered = _filter_listing(h)
        for dropped in ("photo_src", "video", "mvip", "isRecom", "bid_rank",
                        "adTag", "photoList", "guess_like_data", "agent_info"):
            assert dropped not in filtered

    def test_preserves_useful_fields(self):
        raw = _load("search_sale.json")
        h = next(x for x in raw["data"] if "post_id" in x)
        filtered = _filter_listing(h)
        for key in ("post_id", "title", "price", "area_str", "layout_str",
                    "area_price", "section", "region"):
            assert key in filtered


class TestSearchSaleTool:
    def test_excludes_non_listing_items(self):
        raw = _load("search_sale.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_sale("桃園市", section="中壢區")
        # community cards (no post_id) must be excluded
        for item in result["listings"]:
            assert "post_id" in item

    def test_returns_total_rows(self):
        raw = _load("search_sale.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_sale("桃園市", section="中壢區")
        assert result["total_rows"] == raw["totalRows"]

    def test_each_listing_only_has_allowed_keys(self):
        raw = _load("search_sale.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_sale("桃園市", section="中壢區")
        for item in result["listings"]:
            assert set(item.keys()) <= _LISTING_KEYS
