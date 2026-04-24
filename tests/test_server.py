import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_591.client import Client591
from mcp_591.server import (
    _LISTING_KEYS,
    _RENT_LISTING_KEYS,
    _filter_listing,
    _filter_rent_listing,
    _strip_html,
    get_rent_detail,
    get_sale_detail,
    search_rent,
    search_sale,
)

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


class TestStripHtml:
    def test_removes_tags(self):
        assert _strip_html("<p>hello <b>world</b></p>") == "hello world"

    def test_replaces_nbsp(self):
        assert _strip_html("foo&nbsp;bar") == "foo bar"

    def test_collapses_spaces(self):
        assert _strip_html("a&nbsp;&nbsp;&nbsp;b") == "a b"

    def test_empty_string(self):
        assert _strip_html("") == ""


class TestGetSaleDetailTool:
    def test_returns_expected_fields(self):
        raw = _load("sale_detail.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = get_sale_detail("19708683")
        for key in ("title", "price", "area", "layout", "floor", "age",
                    "region", "section", "lat", "lng"):
            assert key in result

    def test_remark_has_no_html_tags(self):
        raw = _load("sale_detail.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = get_sale_detail("19708683")
        assert "<" not in result["remark"]
        assert ">" not in result["remark"]
        assert "&nbsp;" not in result["remark"]

    def test_maps_fixture_values(self):
        raw = _load("sale_detail.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = get_sale_detail("19708683")
        assert result["price"] == "1,688萬元"
        assert result["layout"] == "3房2廳2衛"
        assert result["community"] == "麗江星漾"
        assert result["agent_type"] == "仲介"


class TestFilterRentListing:
    def test_injects_post_id_from_id(self):
        raw = _load("search_rent.json")
        item = raw["data"]["items"][0]
        filtered = _filter_rent_listing(item)
        assert filtered["post_id"] == item["id"]

    def test_only_keeps_allowed_keys(self):
        raw = _load("search_rent.json")
        for item in raw["data"]["items"]:
            filtered = _filter_rent_listing(item)
            allowed = _RENT_LISTING_KEYS | {"post_id"}
            assert set(filtered.keys()) <= allowed

    def test_preserves_useful_fields(self):
        raw = _load("search_rent.json")
        item = raw["data"]["items"][0]
        filtered = _filter_rent_listing(item)
        for key in ("post_id", "title", "price", "price_unit", "area_name", "kind_name", "address"):
            assert key in filtered


class TestSearchRentTool:
    def test_returns_total_rows_and_next_offset(self):
        raw = _load("search_rent.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_rent("桃園市", section="中壢區")
        assert result["total_rows"] == raw["data"]["total"]
        assert "next_first_row" in result

    def test_each_listing_has_post_id(self):
        raw = _load("search_rent.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_rent("桃園市", section="中壢區")
        for item in result["listings"]:
            assert "post_id" in item
            assert item["post_id"] is not None

    def test_each_listing_only_has_allowed_keys(self):
        raw = _load("search_rent.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = search_rent("桃園市", section="中壢區")
        allowed = _RENT_LISTING_KEYS | {"post_id"}
        for item in result["listings"]:
            assert set(item.keys()) <= allowed


class TestGetRentDetailTool:
    def test_returns_expected_fields(self):
        raw = _load("rent_detail.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = get_rent_detail("21103645")
        for key in ("title", "price", "price_unit", "kind", "area", "floor",
                    "region", "section", "address", "lat", "lng", "lease", "facilities"):
            assert key in result

    def test_maps_fixture_values(self):
        raw = _load("rent_detail.json")
        client = Client591(device_id="test")
        with patch.object(client._session, "get", return_value=_mock_resp(raw)):
            with patch("mcp_591.server._client", client):
                result = get_rent_detail("21103645")
        assert result["price"] == "32,000"
        assert result["price_unit"] == "元/月"
        assert result["kind"] == "整層住家"
        assert result["region"] == "桃園市"
        assert result["section"] == "中壢區"
        assert result["lat"] == "25.0160495"
