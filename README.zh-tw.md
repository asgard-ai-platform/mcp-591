# mcp-591

MCP server 讓 AI 助理能搜尋 [591 售屋網](https://house.591.com.tw) 的物件資訊。

> **注意**：本專案透過非公開的 API 抓取資料，屬個人研究用途。請勿大量或高頻率呼叫，以免對服務造成負擔。

## 使用範例

> **使用者：** 幫我搜尋青埔周邊 10 年內的大樓，總價控制在 1200 萬左右

Claude 自動推導參數並呼叫 `search_sale`：

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

> **Claude：** 青埔周邊 1,000~1,400 萬、10 年內電梯大樓，共找到 5年內 135 筆、5~10年 146 筆，以下整理 CP 值較高的物件：...

## 相依

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)

## 安裝

```bash
git clone <repo>
cd mcp-591
uv sync
```

## 如何使用

### 作為 MCP Server（搭配 Claude Desktop / Claude Code）

專案根目錄已附 `.mcp.json`，Claude Code 會自動偵測：

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

啟動後可使用四個 tool：

#### `search_sale` — 搜尋售屋列表

| 參數 | 型別 | 說明 |
|---|---|---|
| `region` | str（必填） | 縣市，例如 `桃園市` |
| `section` | str | 區域，例如 `中壢區`，省略則搜尋整個縣市 |
| `kind` | str | 物件類型，預設 `住宅`，可選：`住宅` / `店面` / `辦公` / `廠房` / `車位` / `套房` / `土地` / `住辦` |
| `shape` | str | 建物型態：`公寓` / `電梯大樓` / `透天厝` / `別墅` |
| `pattern` | str | 格局：`1房` / `2房` / `3房` / `4房` / `5房以上` |
| `toilet` | str | 衛浴數：`1衛` / `2衛` / `3衛` / `4衛` / `5衛以上` |
| `area` | str | 坪數區間：`10_20` / `20_30` / `30_40` / `40_50` / `50_60` / `60_100` / `100_150` / `150_200` |
| `age` | str | 屋齡：`_5`（5年內）/ `5_10` / `10_20` / `20_30` / `30_40` / `40_`（40年以上） |
| `price_str` | str | 價格區間（萬），例如 `1000_1500` 或 `1000_1250,1250_1500` |
| `keywords` | str | 關鍵字，例如 `捷運` |
| `page_size` | int | 每頁筆數，最大 30（預設 30） |
| `first_row` | int | 分頁 offset（預設 0） |

#### `get_sale_detail` — 取得物件詳情

| 參數 | 型別 | 說明 |
|---|---|---|
| `post_id` | str | 物件 ID，來自 `search_sale` 結果的 `post_id` 欄位 |

回傳包含：坪數細項（主建物 / 公設比）、樓層、屋齡、交通、停車、裝潢、貸款試算、聯絡資訊、備註等。

#### `search_rent` — 搜尋租屋列表

| 參數 | 型別 | 說明 |
|---|---|---|
| `region` | str（必填） | 縣市，例如 `桃園市` |
| `section` | str | 區域，例如 `中壢區`，省略則搜尋整個縣市 |
| `kind` | str | 物件類型：`整層住家` / `獨立套房` / `分租套房` / `雅房` / `車位` |
| `shape` | str | 建物型態：`公寓` / `電梯大樓` / `透天厝` / `別墅` |
| `pattern` | str | 格局：`1房` / `2房` / `3房` / `4房` / `5房以上` |
| `price_str` | str | 月租金區間（元），例如 `10000_20000` |
| `keywords` | str | 關鍵字，例如 `捷運` |
| `first_row` | int | 分頁 offset（預設 0），使用上一頁回傳的 `next_first_row` |

#### `get_rent_detail` — 取得租屋物件詳情

| 參數 | 型別 | 說明 |
|---|---|---|
| `post_id` | str | 物件 ID，來自 `search_rent` 結果的 `post_id` 欄位 |

回傳包含：租金、押金、坪數、樓層、建物型態、格局、地址與座標、租期、入住時間、寵物 / 開伙 / 性別限制、提供設備、聯絡資訊、備註等。

### 直接執行 client（除錯用）

```bash
# 搜尋桃園市中壢區
uv run python -m mcp_591.client 桃園市 中壢區

# 加入篩選：型態 格局 衛浴 坪數 屋齡
uv run python -m mcp_591.client 桃園市 中壢區 電梯大樓 3房 2衛 30_40 _5
```

參數順序：`<縣市> [區域] [型態,...] [格局,...] [衛浴,...] [坪數] [屋齡]`，空字串 `""` 可跳過中間參數。

## 開發與測試

```bash
# 安裝含開發相依
uv sync --dev

# 單元測試（不打 API，使用 fixture）
uv run pytest

# 整合測試（打真實 591 API）
uv run pytest -m integration
```

### 測試結構

```
tests/
├── fixtures/
│   ├── search_sale.json   # 售屋搜尋結果 fixture
│   ├── sale_detail.json   # 售屋詳情 fixture
│   ├── search_rent.json   # 租屋搜尋結果 fixture
│   └── rent_detail.json   # 租屋詳情 fixture
├── test_server.py         # 單元測試：filter / tool 邏輯
└── test_integration.py    # 整合測試（default 跳過）
```

更新 fixture（需要網路）：

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
