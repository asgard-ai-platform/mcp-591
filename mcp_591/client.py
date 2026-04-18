import time
import uuid
import warnings

import requests
from urllib3.exceptions import InsecureRequestWarning

_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Mobile Safari/537.36"
)


class Client591:
    _SALE_URL = "https://bff-house.591.com.tw/v1/touch/sale/list"

    def __init__(self, device_id: str | None = None) -> None:
        self._device_id = device_id or uuid.uuid4().hex
        self._session = requests.Session()
        self._session.headers.update(
            {
                "user-agent": _MOBILE_UA,
                "device": "touch",
                "deviceid": self._device_id,
                "origin": "https://m.591.com.tw",
                "referer": "https://m.591.com.tw/",
            }
        )
        self._session.cookies.set("T591_TOKEN", self._device_id)
        # 591's cert is missing Subject Key Identifier; suppress the noise
        self._session.verify = False
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    def search_sale(
        self,
        region_id: int,
        section_ids: list[int],
        *,
        first_row: int = 0,
        page_size: int = 30,
        price_str: str | None = None,
        kind: int | None = None,
        shape_ids: list[int] | None = None,
        pattern_ids: list[int] | None = None,
        toilet_ids: list[int] | None = None,
        area_str: str | None = None,
    ) -> dict:
        """Search for sale listings.

        Args:
            region_id: County ID. e.g. 6 = 桃園市
            section_ids: District IDs. e.g. [67] = 中壢區
            first_row: Pagination offset.
            page_size: Results per page (max 30).
            price_str: Price range in 萬. e.g. "1000_1500" or "1000_1250,1250_1500"
            kind: Property type. e.g. 9 = 住宅 (see KINDS in constants)
            shape_ids: Building shape. e.g. [2] = 電梯大樓 (see SHAPES in constants)
            pattern_ids: Room count. e.g. [3] = 3房, [5] = 5房以上 (see PATTERNS in constants)
            toilet_ids: Bathroom count. e.g. [2] = 2衛 (see TOILETS in constants)
            area_str: Area range key from AREAS. e.g. "30_40" = 30~40坪
        """
        params: dict = {
            "type": "sale",
            "version": 2017,
            "regionid": region_id,
            "sectionidStr": ",".join(str(i) for i in section_ids),
            "firstRow": first_row,
            "newPageSize": page_size,
            "device": "touch",
            "device_id": self._device_id,
            "timestamp": int(time.time() * 1000),
        }
        if price_str is not None:
            params["price_str"] = price_str
        if kind is not None:
            params["kind"] = kind
        if shape_ids is not None:
            params["shape_str"] = ",".join(str(i) for i in shape_ids)
        if pattern_ids is not None:
            params["pattern_str"] = ",".join(str(i) for i in pattern_ids)
        if toilet_ids is not None:
            params["toilet_str"] = ",".join(str(i) for i in toilet_ids)
        if area_str is not None:
            params["area_str"] = area_str

        resp = self._session.get(self._SALE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    import sys
    from mcp_591.constants import REGIONS, SECTIONS, SECTIONS_BY_REGION, SHAPES, PATTERNS, TOILETS, AREAS

    # Usage: client.py <縣市> [區域] [型態,...] [格局,...] [衛浴,...] [坪數]
    # e.g.  client.py 桃園市 中壢區 電梯大樓 3房 2衛 30_40
    region_name = sys.argv[1] if len(sys.argv) > 1 else "桃園市"
    section_name = sys.argv[2] if len(sys.argv) > 2 else None
    shape_names = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
    pattern_names = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []
    toilet_names = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] else []
    area_arg = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] else None

    region_id = next((rid for rid, name in REGIONS.items() if name == region_name), None)
    if region_id is None:
        print(f"找不到縣市：{region_name}")
        print("可用：", list(REGIONS.values()))
        sys.exit(1)

    if section_name:
        section_ids = [
            sid for sid, (sname, rid) in SECTIONS.items()
            if sname == section_name and rid == region_id
        ]
        if not section_ids:
            print(f"找不到區域：{section_name}（{region_name}）")
            print("可用：", list(SECTIONS_BY_REGION[region_id].values()))
            sys.exit(1)
    else:
        section_ids = list(SECTIONS_BY_REGION[region_id].keys())

    shape_ids = None
    if shape_names:
        shape_ids = [sid for sid, name in SHAPES.items() if name in shape_names]
        if not shape_ids:
            print(f"找不到型態：{shape_names}")
            print("可用：", list(SHAPES.values()))
            sys.exit(1)

    pattern_ids = None
    if pattern_names:
        pattern_ids = [pid for pid, name in PATTERNS.items() if name in pattern_names]
        if not pattern_ids:
            print(f"找不到格局：{pattern_names}")
            print("可用：", list(PATTERNS.values()))
            sys.exit(1)

    toilet_ids = None
    if toilet_names:
        toilet_ids = [tid for tid, name in TOILETS.items() if name in toilet_names]
        if not toilet_ids:
            print(f"找不到衛浴：{toilet_names}")
            print("可用：", list(TOILETS.values()))
            sys.exit(1)

    area_str = None
    if area_arg:
        if area_arg not in AREAS:
            print(f"找不到坪數區間：{area_arg}")
            print("可用：", list(AREAS.keys()))
            sys.exit(1)
        area_str = area_arg

    client = Client591()
    result = client.search_sale(
        region_id=region_id, section_ids=section_ids, kind=9,
        shape_ids=shape_ids, pattern_ids=pattern_ids, toilet_ids=toilet_ids,
        area_str=area_str, page_size=5,
    )
    listings = [x for x in result.get("data", []) if "post_id" in x]
    filters = ",".join(filter(None, [",".join(shape_names), ",".join(pattern_names), ",".join(toilet_names), AREAS.get(area_str, "") if area_str else ""]))
    label = f" [{filters}]" if filters else ""
    print(f"{region_name}{section_name or '全區'}{label}  totalRows: {result.get('totalRows')}")
    for h in listings:
        print(f"  [{h['post_id']}] {h['price']:>10}  {h['title'][:30]}")
