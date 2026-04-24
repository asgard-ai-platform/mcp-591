import re

from fastmcp import FastMCP

from mcp_591.client import Client591
from mcp_591.constants import (
    AGES,
    AREAS,
    KINDS,
    PATTERNS,
    REGIONS,
    RENT_KINDS,
    SECTIONS,
    SECTIONS_BY_REGION,
    SHAPES,
    TOILETS,
)

mcp = FastMCP("mcp-591")
_client = Client591()

_LISTING_KEYS = {
    "post_id", "title", "price", "area_str", "layout_str",
    "area_price", "section", "region", "community_addr",
    "feat_tag", "refreshtime", "kindStr",
}


def _filter_listing(h: dict) -> dict:
    return {k: v for k, v in h.items() if k in _LISTING_KEYS}


def _resolve(mapping: dict, name: str | None, label: str) -> int | None:
    if name is None:
        return None
    match = next((k for k, v in mapping.items() if v == name), None)
    if match is None:
        raise ValueError(f"無效的{label}：{name!r}，可用：{list(mapping.values())}")
    return match


@mcp.tool()
def search_sale(
    region: str,
    section: str | None = None,
    kind: str = "住宅",
    shape: str | None = None,
    pattern: str | None = None,
    toilet: str | None = None,
    area: str | None = None,
    age: str | None = None,
    price_str: str | None = None,
    keywords: str | None = None,
    page_size: int = 30,
    first_row: int = 0,
) -> dict:
    """搜尋 591 售屋列表。

    Args:
        region: 縣市名稱，例如「桃園市」
        section: 區域名稱，例如「中壢區」，不填則搜尋整個縣市
        kind: 物件類型，預設「住宅」，可選：住宅/店面/辦公/廠房/車位/套房/土地/住辦
        shape: 建物型態，例如「電梯大樓」，可選：公寓/電梯大樓/透天厝/別墅
        pattern: 格局，例如「3房」，可選：1房/2房/3房/4房/5房以上
        toilet: 衛浴數，例如「2衛」，可選：1衛/2衛/3衛/4衛/5衛以上
        area: 坪數區間，例如「30_40」，可選：10_20/20_30/30_40/40_50/50_60/60_100/100_150/150_200
        age: 屋齡區間，例如「_5」，可選：_5/5_10/10_20/20_30/30_40/40_
        price_str: 價格區間（萬），例如「1000_1500」
        keywords: 關鍵字搜尋，例如「捷運」「學區」
        page_size: 每頁筆數，最大 30
        first_row: 分頁 offset
    """
    region_id = _resolve(REGIONS, region, "縣市")
    if region_id is None:
        raise ValueError("縣市不可為空")

    if section:
        section_ids = [
            sid for sid, (sname, rid) in SECTIONS.items()
            if sname == section and rid == region_id
        ]
        if not section_ids:
            available = list(SECTIONS_BY_REGION[region_id].values())
            raise ValueError(f"找不到區域 {section!r}，可用：{available}")
    else:
        section_ids = list(SECTIONS_BY_REGION[region_id].keys())

    kind_id = _resolve(KINDS, kind, "物件類型")
    shape_ids = [_resolve(SHAPES, shape, "建物型態")] if shape else None
    pattern_ids = [_resolve(PATTERNS, pattern, "格局")] if pattern else None
    toilet_ids = [_resolve(TOILETS, toilet, "衛浴")] if toilet else None

    if area and area not in AREAS:
        raise ValueError(f"無效的坪數區間：{area!r}，可用：{list(AREAS.keys())}")
    if age and age not in AGES:
        raise ValueError(f"無效的屋齡區間：{age!r}，可用：{list(AGES.keys())}")

    result = _client.search_sale(
        region_id=region_id,
        section_ids=section_ids,
        kind=kind_id,
        shape_ids=shape_ids,
        pattern_ids=pattern_ids,
        toilet_ids=toilet_ids,
        area_str=area,
        age_str=age,
        price_str=price_str,
        keywords=keywords,
        page_size=page_size,
        first_row=first_row,
    )

    listings = [_filter_listing(h) for h in result.get("data", []) if "post_id" in h]
    return {
        "total_rows": result.get("totalRows"),
        "listings": listings,
    }


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.replace("&nbsp;", " ")
    return re.sub(r" {2,}", " ", text).strip()


@mcp.tool()
def get_sale_detail(post_id: str) -> dict:
    """取得 591 售屋物件的完整詳細資訊。

    Args:
        post_id: 物件 ID，來自 search_sale 結果的 post_id 欄位。
    """
    resp = _client.get_sale_detail(post_id)
    d = resp.get("data")
    if not isinstance(d, dict) or not d:
        raise ValueError(f"Listing {post_id} not found (may be delisted)")
    return {
        "title": d.get("title"),
        "price": d.get("price"),
        "unit_price": d.get("unitprice"),
        "area": d.get("area"),
        "main_area": d.get("mainarea"),
        "ratio_rate": d.get("ratioRate"),
        "layout": d.get("layout"),
        "floor": d.get("floor"),
        "age": d.get("age"),
        "shape": d.get("shape"),
        "kind": d.get("kind"),
        "region": d.get("region"),
        "section": d.get("section"),
        "street": d.get("street"),
        "community": d.get("casesname"),
        "traffic": d.get("traffic"),
        "parking": d.get("parking_new") or d.get("parking"),
        "fitment": d.get("fitment"),
        "manage_fee": d.get("manageprice"),
        "lat": d.get("lat"),
        "lng": d.get("lng"),
        "feat_tag": d.get("feat_tag"),
        "area_intro": d.get("area_intro"),
        "mortgage_info": d.get("mortgage_info"),
        "agent": d.get("linkman"),
        "agent_type": d.get("identity"),
        "phone": d.get("mobile"),
        "company": d.get("company_name"),
        "remark": _strip_html(d.get("remark", "")),
    }


_RENT_LISTING_KEYS = {
    "post_id", "title", "price", "price_unit", "area_name",
    "layoutStr", "kind_name", "address", "tags", "refresh_time",
}


def _filter_rent_listing(item: dict) -> dict:
    result = {k: v for k, v in item.items() if k in _RENT_LISTING_KEYS}
    result["post_id"] = item.get("id")
    return result


@mcp.tool()
def search_rent(
    region: str,
    section: str | None = None,
    kind: str | None = None,
    shape: str | None = None,
    pattern: str | None = None,
    price_str: str | None = None,
    keywords: str | None = None,
    first_row: int = 0,
) -> dict:
    """搜尋 591 租屋列表。

    Args:
        region: 縣市名稱，例如「桃園市」
        section: 區域名稱，例如「中壢區」，不填則搜尋整個縣市
        kind: 物件類型，可選：整層住家/獨立套房/分租套房/雅房/車位
        shape: 建物型態，例如「電梯大樓」，可選：公寓/電梯大樓/透天厝/別墅
        pattern: 格局，例如「3房」，可選：1房/2房/3房/4房/5房以上
        price_str: 月租金區間（元），例如「10000_20000」
        keywords: 關鍵字搜尋，例如「捷運」「學區」
        first_row: 分頁 offset
    """
    region_id = _resolve(REGIONS, region, "縣市")
    if region_id is None:
        raise ValueError("縣市不可為空")

    if section:
        section_ids = [
            sid for sid, (sname, rid) in SECTIONS.items()
            if sname == section and rid == region_id
        ]
        if not section_ids:
            available = list(SECTIONS_BY_REGION[region_id].values())
            raise ValueError(f"找不到區域 {section!r}，可用：{available}")
    else:
        section_ids = list(SECTIONS_BY_REGION[region_id].keys())

    kind_id = _resolve(RENT_KINDS, kind, "物件類型") if kind else None
    shape_ids = [_resolve(SHAPES, shape, "建物型態")] if shape else None
    pattern_ids = [_resolve(PATTERNS, pattern, "格局")] if pattern else None

    result = _client.search_rent(
        region_id=region_id,
        section_ids=section_ids,
        kind=kind_id,
        shape_ids=shape_ids,
        pattern_ids=pattern_ids,
        price_str=price_str,
        keywords=keywords,
        first_row=first_row,
    )

    data = result.get("data", {})
    listings = [_filter_rent_listing(item) for item in data.get("items", [])]
    # 591 rent API returns `total` as a string; coerce to int so callers get the
    # same type as search_sale.
    total = data.get("total")
    return {
        "total_rows": int(total) if total is not None else None,
        "next_first_row": data.get("firstRow"),
        "listings": listings,
    }


@mcp.tool()
def get_rent_detail(post_id: str) -> dict:
    """取得 591 租屋物件的完整詳細資訊。

    Args:
        post_id: 物件 ID，來自 search_rent 結果的 post_id 欄位。
    """
    resp = _client.get_rent_detail(post_id)
    d = resp.get("data")
    if not isinstance(d, dict) or not d:
        raise ValueError(f"Listing {post_id} not found (may be delisted)")

    info = {item["key"]: item["value"] for item in d.get("info", [])}
    house_info = {item["key"]: item["value"] for item in d.get("houseInfo", {}).get("data", [])}
    addr = d.get("address", {})
    link = d.get("linkInfo", {})
    gtm = d.get("gtm_detail_data", {})
    remark_block = d.get("remark", {})

    return {
        "title": d.get("title"),
        "price": d.get("price"),
        "price_unit": d.get("priceUnit"),
        "deposit": d.get("deposit"),
        "kind": gtm.get("kind_name"),
        "area": info.get("area"),
        "floor": info.get("floor"),
        "shape": info.get("shape"),
        "layout": info.get("layout"),
        "region": gtm.get("region_name"),
        "section": gtm.get("section_name"),
        "address": addr.get("data"),
        "lat": addr.get("lat"),
        "lng": addr.get("lng"),
        "traffic": addr.get("traffic"),
        "lease": house_info.get("leaseTime"),
        "move_in": house_info.get("comeDate"),
        "pet": house_info.get("pet"),
        "cook": house_info.get("cook"),
        "sex": house_info.get("sex"),
        "facilities": gtm.get("facility_name"),
        "tags": d.get("tags"),
        "agent": link.get("name"),
        "agent_role": link.get("roleName"),
        "phone": link.get("mobile"),
        "remark": remark_block.get("content", ""),
    }


def main() -> None:
    mcp.run()
