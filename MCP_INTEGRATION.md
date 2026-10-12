# MCP 集成说明 · mcd-year-in-review

本文件说明项目如何使用麦当劳 MCP Server（`M-China/mcd-mcp-server`）以及每一笔数据的调用链路。

## 使用的 MCP Server

- **Server 名称**：麦当劳 MCP Server
- **接入地址**：`https://mcp.mcd.cn`
- **传输协议**：Streamable HTTP（含 SSE 兼容）
- **鉴权方式**：请求头 `Authorization: Bearer <MCP_TOKEN>`
- **协议版本**：`2025-06-18`

## 使用的 Tool 清单

| Tool | 官方名称 | 在本项目中的用途 |
|---|---|---|
| `order-list` | 查询历史订单 | 拉取近期到店/外送订单列表，作为年报主数据源 |
| `query-order` | 查询订单详情 | 可选补充：餐品明细、外带/堂食、优惠明细 |
| `list-nutrition-foods` | 营养信息查询 | 拉取 160 款餐品的热量 / 蛋白 / 脂肪 / 碳水 / 钠 / 钙，用于计算「摄入总热量」 |
| `query-my-account` | 我的积分查询 | 读取会员卡号、可用积分、累计积分、即将过期积分（官方不返回昵称/等级） |
| `now-time-info` | 获取当前时间信息 | 辅助判断年报统计区间 |

> 注：`mall-order-list` / `mall-order-detail` 目前未接入（账号样本中未产生商城订单），但 `fetch_orders` 与 `source.py` 的抽象已经为后续接入预留了扩展点。

## 调用流程

```text
┌──────────────┐
│ 用户运行 CLI │
└──────┬───────┘
       │
       v
┌──────────────────────┐     initialize     ┌──────────────────┐
│  MCPClient           │ -----------------> │ 麦当劳 MCP Server│
│  (Streamable HTTP)   │                    └────────┬─────────┘
└──────┬───────────────┘                             │
       │                                             │
       │  1. tools/call order-list                   │
       │     分页拉取历史订单（默认 50 条/页，最多 20 页）│
       │-------------------------------------------->│
       │                                             │
       │  2. （可选）tools/call query-order          │
       │     加 --detail 才触发：逐单补渠道/优惠     │
       │                                             │
       │  3. tools/call list-nutrition-foods         │
       │     拉取官方营养表，给餐品补热量              │
       │                                             │
       │  4. tools/call query-my-account             │
       │     读取会员卡号、积分                       │
       │                                             │
       v                                             v
┌──────────────────────────────────────────────────────────┐
│  source.parse_order() 对字段做容错解析                    │
│  兼容多种字段命名：orderId/orderNo/orderTime/createTime   │
│  realTotalAmount/payAmount/amount                         │
│  orderProductList/items/products                          │
│  comboItemList（套餐子项）                                │
└──────────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────┐
│  stats.compute() + badges.evaluate()                      │
│  生成：总览、月度、类目、单品、时段、门店、徽章、趣味换算  │
└──────────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────┐
│  report.build_html() 输出单文件 HTML 年报                  │
│  纯内联 SVG，零外部依赖                                    │
└──────────────────────────────────────────────────────────┘
```

## 配置示例

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer ${MCD_MCP_TOKEN}"
      }
    }
  }
}
```

环境变量写法：

```bash
export MCD_MCP_TOKEN="your_token"
export MCD_MCP_ENDPOINT="https://mcp.mcd.cn"
```

## 数据解析的兼容性

官方 MCP 工具返回的字段命名没有公开 JSON Schema，因此 `source.py` 的解析器采用了**最宽容**的策略。

### 响应形态

麦当劳 MCP Server v1.0 的真实响应在 `content[].text` 里夹带了一段 Markdown 说明 + JSON，
**真正的结构化数据放在 `structuredContent` 里**。`mcp_client.ToolResult.json()` 已优先读取 `structuredContent`，
没有时才退回到文本里抠 JSON，因此解析稳定可靠。

### 订单字段容错映射

| 业务 | 实际见过的字段名（任一即可） |
|---|---|
| 订单 ID | `orderId` / `orderNo` / `id` |
| 下单时间 | `createTime` / `orderTime` / `time` / `createdAt` / 时间戳 |
| 实付金额 | `realTotalAmount` / `payAmount` / `actualAmount` / `totalAmount` / `amount` |
| 商品列表 | `orderProductList` / `items` / `products` / `orderItems` / `mealList` / `details` |
| 商品名 | `productName` / `name` / `mealName` / `itemName` / `skuName` |
| 套餐子项 | `comboItemList[].name` / `comboItemList[].itemName` |
| 子项数量 | `quantity` / `itemQuantity` / `qty` / `num` / `count` |
| 门店名 | `storeName` / `store` / `restaurantName` |
| 渠道 | `takeWay`（外带/外送） / `deliveryPrice` / `orderType` |

任何解析失败的订单会被跳过并计数，不会导致整批失败。这也意味着：**强烈建议先用 `--mock` 验证年报形态，再用 `--live` 接入真实数据。**

## 数据隐私

- 项目代码与配置文件中**不包含任何真实 Token**；
- Token 仅通过环境变量或 `--token` 注入；
- **会员卡号默认打码展示**（前 8 位 + 省略号 + 后 4 位），避免截图分享时泄露账号；
- 年报 HTML 默认生成在本地，由用户自行决定是否分享。

## 离线数据

为了方便评审与演示，仓库内置了 2026-01-01 至 2026-10-11 的示例订单数据（`src/mcd_year_in_review/mock_data.py`），固定随机种子，保证任何环境生成的结果一致。
