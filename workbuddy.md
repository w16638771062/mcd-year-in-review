# WorkBuddy 专项奖励说明

本项目在 WorkBuddy 环境中开发，使用 WorkBuddy 作为智能体协作平台完成从主题确定到代码落地的全过程。本文件说明项目的 WorkBuddy 相关上下文。

## 开发环境

- **协作平台**：腾讯 WorkBuddy
- **模型交互**：通过 WorkBuddy 对话完成需求澄清、架构设计、代码生成、测试与文档编写
- **仓库地址**（报名后创建）：`https://github.com/<你的用户名>/mcd-year-in-review`

## WorkBuddy 在项目中的作用

1. **主题决策**：在发现原「麦麦控卡助手」方向与官方示例创意重合后，由 WorkBuddy 重新给出 6 个避开红海的主题，并选定「麦门年度账单」。
2. **技术设计**：确定零第三方依赖、单文件 HTML 年报、纯内联 SVG 可视化的技术路线。
3. **代码实现**：分模块实现 `models`/`stats`/`badges`/`source`/`report`/`render`/`cli`。
4. **测试验证**：编写并运行 21 个单元测试，生成 HTML 年报后通过系统 QuickLook 截图验证渲染效果。
5. **文档交付**：生成 README、MCP_INTEGRATION、workbuddy.md 等参赛必需文件。

## 关键实现文件

| 文件 | 说明 |
|---|---|
| `src/mcd_year_in_review/mcp_client.py` | 基于 `urllib` 的 MCP Streamable HTTP 客户端，兼容 JSON/SSE 响应与 429 退避 |
| `src/mcd_year_in_review/report.py` | 单文件 HTML 年报生成器，纯内联 SVG，零外部依赖 |
| `src/mcd_year_in_review/badges.py` | 声明式成就徽章规则引擎 |
| `src/mcd_year_in_review/stats.py` | 年度消费 / 口味 / 作息 / 门店画像统计引擎 |

## 运行方式

```bash
cd /Volumes/ghn/测评文章/mcd-year-in-review
PYTHONPATH=src python3 -m mcd_year_in_review demo
PYTHONPATH=src python3 -m mcd_year_in_review --mock --html examples/year-in-review.html
```

## 备注

- 项目零第三方依赖，所有代码均可在 Python 3.10+ 标准库环境下直接运行。
- 官方 `CONTEST_DECLARATION.md` 已逐字节校验，与大赛官方仓库版本完全一致，未被改动。
