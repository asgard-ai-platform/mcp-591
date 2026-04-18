# mcp-591

An MCP server that lets AI assistants search property listings on [591.com.tw](https://house.591.com.tw), Taiwan's largest real estate platform.

> **Disclaimer**: This project scrapes data from an undocumented API. It is intended for personal research only. Do not use it for bulk or high-frequency requests.

Also available in: [繁體中文](README.zh-tw.md)

## Example

> **User:** 幫我搜尋青埔周邊 10 年內的大樓，總價控制在 1200 萬左右

Claude calls `search_sale` with the inferred parameters:

```json
{
  "region": "桃園市",
  "section": "中壢區",
  "shape": "電梯大樓",
  "age": "5_10",
  "price_str": "1000_1400",
  "keywords": "青埔"
}
```

> **Claude:** 青埔周邊 1,000~1,400 萬、10 年內電梯大樓，共找到 5年內 135 筆、5~10年 146 筆，以下整理 CP 值較高的物件：...

## Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)

## Installation

```bash
git clone <repo>
cd mcp-591
uv sync
```

## Usage

### As an MCP Server (Claude Desktop / Claude Code)

The repo ships a `.mcp.json` that Claude Code picks up automatically:

```json
{
  "mcpServers": {
    "591": {
      "command": "uv",
      "args": ["run", "mcp-591"],
      "cwd": "${PWD}"
    }
  }
}
```

Two tools are exposed:

#### `search_sale` — Search for sale listings

| Parameter | Type | Description |
|---|---|---|
| `region` | str (required) | County/city name, e.g. `桃園市` |
| `section` | str | District, e.g. `中壢區`. Omit to search the whole county. |
| `kind` | str | Property type, default `住宅`. Options: `住宅` / `店面` / `辦公` / `廠房` / `車位` / `套房` / `土地` / `住辦` |
| `shape` | str | Building type: `公寓` / `電梯大樓` / `透天厝` / `別墅` |
| `pattern` | str | Room count: `1房` / `2房` / `3房` / `4房` / `5房以上` |
| `toilet` | str | Bathroom count: `1衛` / `2衛` / `3衛` / `4衛` / `5衛以上` |
| `area` | str | Floor area range (坪): `10_20` / `20_30` / `30_40` / `40_50` / `50_60` / `60_100` / `100_150` / `150_200` |
| `age` | str | Building age: `_5` (under 5 yrs) / `5_10` / `10_20` / `20_30` / `30_40` / `40_` (40+ yrs) |
| `price_str` | str | Price range in 萬 NTD, e.g. `1000_1500` or `1000_1250,1250_1500` |
| `keywords` | str | Free-text search, e.g. `捷運` (MRT) |
| `page_size` | int | Results per page, max 30 (default 30) |
| `first_row` | int | Pagination offset (default 0) |

#### `get_sale_detail` — Fetch full listing details

| Parameter | Type | Description |
|---|---|---|
| `post_id` | str | Listing ID from a `search_sale` result |

Returns: floor area breakdown (main area / common-area ratio), floor, building age, nearby transit, parking, fitment, mortgage estimate, contact info, and description.

### Running the client directly (debugging)

```bash
# Search 桃園市中壢區
uv run python -m mcp_591.client 桃園市 中壢區

# With filters: shape pattern toilet area age
uv run python -m mcp_591.client 桃園市 中壢區 電梯大樓 3房 2衛 30_40 _5
```

Argument order: `<county> [district] [shape,...] [pattern,...] [toilet,...] [area] [age]`. Pass an empty string `""` to skip an intermediate argument.

## Development & Testing

```bash
# Install with dev dependencies
uv sync --dev

# Unit tests (no network, uses fixtures)
uv run pytest

# Integration tests (hits the real 591 API)
uv run pytest -m integration
```

### Test layout

```
tests/
├── fixtures/
│   ├── search_sale.json   # Captured search response
│   └── sale_detail.json   # Captured detail response
├── test_server.py         # Unit tests: filtering and tool logic
└── test_integration.py    # Integration tests (skipped by default)
```

To refresh fixtures (requires network):

```bash
uv run python -c "
import json
from mcp_591.client import Client591
c = Client591()
json.dump(c.search_sale(region_id=6, section_ids=[67], kind=9, page_size=5),
          open('tests/fixtures/search_sale.json', 'w'), ensure_ascii=False, indent=2)
json.dump(c.get_sale_detail(19708683),
          open('tests/fixtures/sale_detail.json', 'w'), ensure_ascii=False, indent=2)
"
```
