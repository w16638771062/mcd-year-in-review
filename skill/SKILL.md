# WorkBuddy Skill 集成说明

如果你是在 WorkBuddy 中使用本项目，可以把它配置成一个对话式 Skill：

1. 在 WorkBuddy 的「连接器 / 自定义连接器」中新增一个「本地命令」连接器；
2. 工作目录指向本仓库根目录；
3. 执行命令设为：

```bash
PYTHONPATH=src python3 -m mcd_year_in_review --mock --html /tmp/mcd-year-in-review.html --name {{user_name}} --city {{city}}
```

4. 输出格式：把生成的 `/tmp/mcd-year-in-review.html` 作为文件附件返回给对话。

## 对话示例

> 用户：帮我生成今年的麦门年报

> WorkBuddy：好，我先用你的历史订单生成一下……这是你的 2026 麦门年度账单，
> 你最常吃的是「麦乐鸡（5块）」，累计消费 ¥6,077，最长连续打卡 8 天。
> [year-in-review.html]

## 注意事项

- 真实数据接入需要配置环境变量 `MCD_MCP_TOKEN`；
- `--mock` 模式使用固定示例数据，仅用于体验形态；
- 热量 / 健康相关换算纯属趣味，不构成专业建议。
