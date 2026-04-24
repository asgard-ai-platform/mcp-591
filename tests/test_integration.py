"""Integration tests — hit the real 591 API.

Run with:  pytest -m integration
Excluded from default test runs.
"""
import pytest

from mcp_591.client import Client591
from mcp_591.server import get_sale_detail, search_sale

# 桃園市中壢區, 3房, 電梯大樓
_REGION = "桃園市"
_SECTION = "中壢區"


@pytest.fixture(scope="module")
def client():
    return Client591()


@pytest.fixture(scope="module")
def live_post_id(client):
    """Fetch a currently-live sale post_id. Hardcoding IDs is fragile — 591
    listings get delisted and the detail API returns {status: 1, data: ""} for
    stale IDs, which looks like success but crashes downstream parsing."""
    result = client.search_sale(region_id=6, section_ids=[67], kind=9, page_size=5)
    listings = [x for x in result["data"] if "post_id" in x]
    assert listings, "no live listings found for fixture"
    return str(listings[0]["post_id"])


# ── Client ────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestClientSearchSale:
    def test_schema(self, client):
        result = client.search_sale(region_id=6, section_ids=[67], kind=9, page_size=5)
        assert isinstance(result.get("totalRows"), int)
        assert result["totalRows"] > 0

        listings = [x for x in result["data"] if "post_id" in x]
        assert len(listings) > 0

        h = listings[0]
        assert isinstance(h["post_id"], (str, int))
        assert isinstance(h["price"], str)
        assert isinstance(h["area_str"], str)
        assert isinstance(h["layout_str"], str)
        assert isinstance(h["section"], str)
        assert isinstance(h["region"], str)

    def test_region_filter_works(self, client):
        result = client.search_sale(region_id=6, section_ids=[67], kind=9, page_size=10)
        listings = [x for x in result["data"] if "post_id" in x]
        for h in listings:
            assert h["region"] == "桃園市"
            assert h["section"] == "中壢區"


@pytest.mark.integration
class TestClientGetSaleDetail:
    def test_schema(self, client, live_post_id):
        result = client.get_sale_detail(live_post_id)
        assert result["status"] == 1
        d = result["data"]
        assert isinstance(d["title"], str)
        assert isinstance(d["price"], str)
        assert isinstance(d["layout"], str)
        assert isinstance(d["area"], str)
        assert isinstance(d["floor"], str)
        assert isinstance(d["section"], str)
        assert isinstance(d["region"], str)
        assert isinstance(d["lat"], str)
        assert isinstance(d["lng"], str)


# ── Server tools ──────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestToolSearchSale:
    def test_schema(self):
        result = search_sale(_REGION, section=_SECTION, page_size=5)
        assert isinstance(result["total_rows"], int)
        assert result["total_rows"] > 0
        assert len(result["listings"]) > 0

    def test_listing_fields(self):
        result = search_sale(_REGION, section=_SECTION, page_size=5)
        h = result["listings"][0]
        for key in ("post_id", "title", "price", "area_str", "layout_str",
                    "area_price", "section", "region"):
            assert key in h, f"missing key: {key}"

    def test_no_noise_fields(self):
        result = search_sale(_REGION, section=_SECTION, page_size=5)
        for h in result["listings"]:
            for noise in ("photo_src", "video", "bid_rank", "adTag"):
                assert noise not in h


@pytest.mark.integration
class TestToolGetSaleDetail:
    def test_schema(self, live_post_id):
        result = get_sale_detail(live_post_id)
        for key in ("title", "price", "area", "layout", "floor",
                    "region", "section", "lat", "lng"):
            assert key in result, f"missing key: {key}"

    def test_remark_is_plain_text(self, live_post_id):
        result = get_sale_detail(live_post_id)
        remark = result.get("remark", "")
        assert "<" not in remark
        assert "&nbsp;" not in remark
