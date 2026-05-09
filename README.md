# MCP 591

[![PyPI version](https://img.shields.io/pypi/v/mcp-591)](https://pypi.org/project/mcp-591/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-591)](https://pypi.org/project/mcp-591/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-591)](https://github.com/asgard-ai-platform/mcp-591/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-591)](https://github.com/asgard-ai-platform/mcp-591/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-591)](https://github.com/asgard-ai-platform/mcp-591/commits/main)
[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io/)

[繁體中文](README.zh-TW.md)

An open-source [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes [591.com.tw](https://house.591.com.tw) — Taiwan's largest real estate platform — as 4 AI-callable tools for searching sale and rental listings.

Built for [Claude Code](https://claude.ai/code), Claude Desktop, and any MCP-compatible AI client. Lets AI agents search property listings and fetch full details through natural language.

> **Disclaimer:** This project scrapes data from an undocumented API. It is intended for personal research only. Do not use it for bulk or high-frequency requests.

## What This Does

- **4 ready-to-use tools** for sale search, sale detail, rent search, rent detail
- **MCP server** (stdio) — plug into Claude Code and start asking questions immediately
- **Natural-language parameter mapping** — Chinese region/section names, human-readable filters (e.g. `電梯大樓`, `3房`, `5_10`)
- **Minimal dependencies** — `fastmcp` + `requests`

## Example

> **You:** 幫我搜尋青埔周邊 10 年內的大樓，總價控制在 1200 萬左右

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

---

## Quick Start

### Install

```bash
pip install mcp-591
```

Or use uvx (no install needed):

```bash
uvx mcp-591
```

### Use with Claude Code

Add the server via the Claude CLI:

```bash
claude mcp add --transport stdio 591 -- uvx mcp-591
```

If you clone the repo locally, the included `.mcp.json` is auto-detected by Claude Code:

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

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "591": {
      "command": "uvx",
      "args": ["mcp-591"]
    }
  }
}
```

---

## Tools (4)

### `search_sale` — Search for sale listings

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

### `get_sale_detail` — Fetch full sale listing details

| Parameter | Type | Description |
|---|---|---|
| `post_id` | str | Listing ID from a `search_sale` result |

Returns: floor area breakdown (main area / common-area ratio), floor, building age, nearby transit, parking, fitment, mortgage estimate, contact info, and description.

### `search_rent` — Search for rental listings

| Parameter | Type | Description |
|---|---|---|
| `region` | str (required) | County/city name, e.g. `桃園市` |
| `section` | str | District, e.g. `中壢區`. Omit to search the whole county. |
| `kind` | str | Room type: `整層住家` / `獨立套房` / `分租套房` / `雅房` / `車位` |
| `shape` | str | Building type: `公寓` / `電梯大樓` / `透天厝` / `別墅` |
| `pattern` | str | Room count: `1房` / `2房` / `3房` / `4房` / `5房以上` |
| `price_str` | str | Monthly rent range in NTD, e.g. `10000_20000` |
| `keywords` | str | Free-text search, e.g. `捷運` (MRT) |
| `first_row` | int | Pagination offset (default 0). Use `next_first_row` from the previous response. |

### `get_rent_detail` — Fetch full rental listing details

| Parameter | Type | Description |
|---|---|---|
| `post_id` | str | Listing ID from a `search_rent` result |

Returns: price, deposit, floor area, floor, building type, layout, address with lat/lng, lease period, move-in date, pet/cooking/gender policies, facilities, contact info, and description.

---

## Development

### Setup from Source

Requires Python 3.14+ and [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/asgard-ai-platform/mcp-591.git
cd mcp-591
uv sync --dev
```

### Run the client directly (debugging)

```bash
# Search 桃園市中壢區
uv run python -m mcp_591.client 桃園市 中壢區

# With filters: shape pattern toilet area age
uv run python -m mcp_591.client 桃園市 中壢區 電梯大樓 3房 2衛 30_40 _5
```

Argument order: `<county> [district] [shape,...] [pattern,...] [toilet,...] [area] [age]`. Pass an empty string `""` to skip an intermediate argument.

### Run Tests

```bash
# Unit tests (no network, uses fixtures)
uv run pytest

# Integration tests (hits the real 591 API)
uv run pytest -m integration
```

### Test layout

```
tests/
├── fixtures/
│   ├── search_sale.json   # Captured sale search response
│   ├── sale_detail.json   # Captured sale detail response
│   ├── search_rent.json   # Captured rent search response
│   └── rent_detail.json   # Captured rent detail response
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
json.dump(c.search_rent(region_id=6, section_ids=[67], kind=1),
          open('tests/fixtures/search_rent.json', 'w'), ensure_ascii=False, indent=2)
json.dump(c.get_rent_detail(21103645),
          open('tests/fixtures/rent_detail.json', 'w'), ensure_ascii=False, indent=2)
"
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

MIT — see [LICENSE](LICENSE).
