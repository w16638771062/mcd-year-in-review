# WorkBuddy 专项奖励说明

本项目全程在 **腾讯 WorkBuddy** 中开发完成——从主题决策、架构设计、编码实现、真实数据联调到最终提交，均由 WorkBuddy 作为智能体协作平台驱动。本文件记录开发过程中的 WorkBuddy 对话上下文，供核验联动活动（WorkBuddy 专项奖励）条件使用。

## 开发环境

- **协作平台**：腾讯 WorkBuddy
- **交互方式**：通过 WorkBuddy 对话完成需求澄清、创意筛选、架构设计、代码生成、测试编写、真实数据联调与文档交付
- **作品仓库**：https://github.com/w16638771062/mcd-year-in-review
- **参赛报名 Issue**：https://github.com/M-China/mcd-developer-innovation-challenge/issues/540
- **开发日期**：2026-10-12

## WorkBuddy 在项目中的实际作用

1. **规则解析**：解析大赛活动页与官方仓库规则，梳理出必需文件清单、报名 Issue 格式、时间窗口与 Star 排名机制。
2. **创意筛选**：首版选题「麦麦控卡助手」经比对发现与官方示例方向重合，由 WorkBuddy 重新给出 6 个避开红海的主题并做「传播力 × 实用价值」定位，最终选定「麦门年度账单」。
3. **技术路线**：确定「零第三方依赖（仅 Python 标准库）+ 单文件内联 SVG HTML + 声明式徽章规则引擎」的技术方案。
4. **代码实现**：分模块实现 `models` / `source` / `mcp_client` / `nutrition` / `stats` / `badges` / `report` / `render` / `cli` 共九个模块。
5. **真实数据联调**：接入麦当劳官方 MCP，实测中发现并修复关键缺陷——真实响应的结构化数据位于 `structuredContent` 而非 `content[].text`，据此重写 `ToolResult.json()`；并扩展订单/账号解析以兼容真实字段。
6. **测试验证**：编写并运行 **51 个单元测试**（覆盖 MCP 客户端、数据源、营养解析、统计、徽章），全部通过；HTML 年报经系统 QuickLook 截图验证渲染效果。
7. **文档交付**：生成 `README.md`、`USAGE.md`、`MCP_INTEGRATION.md`、`mcp-config.example.json`、`workbuddy.md` 等参赛文件，并逐字节校验官方 `CONTEST_DECLARATION.md` 未被改动。
8. **提交上线**：完成 git 初始化与提交、经 GitHub API 创建公开仓库、推送全部文件，并按官方格式提交报名 Issue。

## 关键实现文件

| 文件 | 说明 |
|---|---|
| `src/mcd_year_in_review/mcp_client.py` | 基于 `urllib` 的 MCP Streamable HTTP 客户端，兼容 JSON/SSE 响应、`structuredContent` 结构化返回与 429 退避 |
| `src/mcd_year_in_review/source.py` | 数据源层：订单/账号归一化，兼容真实字段（`orderProductList` / `createTime` / `realTotalAmount` / `comboItemList` 等），套餐自动展开，会员卡号打码 |
| `src/mcd_year_in_review/nutrition.py` | 解析官方 `list-nutrition-foods` 紧凑文本表，按关键字归类餐品并回填套餐子项热量 |
| `src/mcd_year_in_review/stats.py` | 年度消费 / 口味 / 作息 / 门店 / 渠道画像统计引擎 |
| `src/mcd_year_in_review/badges.py` | 声明式成就徽章规则引擎 |
| `src/mcd_year_in_review/report.py` | 单文件 HTML 年报生成器，纯内联 SVG，零外部依赖 |

## 运行方式

```bash
# 零安装体验（离线示例数据）
cd mcd-year-in-review
PYTHONPATH=src python3 -m mcd_year_in_review demo

# 使用真实麦当劳 MCP Token 生成个人年报
mcd-year-in-review --live --token <你的 MCP Token>
```

## 备注

- 项目零第三方依赖，仅使用 Python 标准库，**Python 3.9+** 即可运行（已在 3.9.6 与 3.13.12 上实测通过全部测试）。
- 隐私优先：会员卡号默认打码，真实数据默认输出到仓库外目录，不会误提交。
- 官方 `CONTEST_DECLARATION.md` 已逐字节校验，与大赛官方仓库版本完全一致，未被改动。
