# 使用指南 · mcd-year-in-review

面向**拿到这个仓库的其他人**。不管你是什么角色，先看下面这张表，找到自己那一行。

| 你是谁 | 你想干什么 | 跳到 |
|---|---|---|
| 路人 / 不写代码 | 就想看看它长什么样 | [第 1 步](#1-只想看看效果零门槛) |
| 开发者 | 用示例数据跑出一份年报 | [第 2 步](#2-三步跑出门自己的年报示例数据) |
| 麦当劳会员 | 用**我自己的**订单和账号出年报 | [第 3 步](#3-用你自己的真实数据) |
| WorkBuddy 用户 | 在对话里直接生成年报 | [第 4 步](#4-在-workbuddy-里当对话式-skill-用) |
| MCP 玩家 | 在别的客户端里调麦当劳 MCP | [第 5 步](#5-在其它-mcp-客户端里使用) |

**环境要求**：Python 3.9 及以上（已在 3.9.6 与 3.13.12 实测通过）。**零第三方依赖**，不需要 `pip install` 任何东西，不联网也能跑。

---

## 1. 只想看看效果（零门槛）

不用装 Python，不用敲命令：

- 直接双击打开 [`examples/year-in-review.html`](examples/year-in-review.html)，它会用浏览器渲染出一整份年度账单。
- 或者看截图 [`examples/year-in-review.html.png`](examples/year-in-review.html.png)。
- 想看终端版长啥样，看 [`examples/demo_output.md`](examples/demo_output.md)。

这一份数据是**内置的示例数据**，不是你的真实订单。

---

## 2. 三步跑出门自己的年报（示例数据）

```bash
# 1. 克隆仓库
git clone https://github.com/<仓库地址>.git
cd mcd-year-in-review

# 2. 跑一遍离线演示（不联网、不需要 Token）
PYTHONPATH=src python3 -m mcd_year_in_review demo

# 3. 生成一份可以发给朋友的 HTML 年报
PYTHONPATH=src python3 -m mcd_year_in_review --mock --html year-in-review.html
```

跑完第 3 步，当前目录下会出现 `year-in-review.html`，双击即可打开。

### 两种运行方式，挑一个

**方式 A · 零安装（推荐，改完代码立刻生效）**

```bash
PYTHONPATH=src python3 -m mcd_year_in_review demo
```

Windows 用户注意环境变量写法不同：

```powershell
# PowerShell
$env:PYTHONPATH="src"; python -m mcd_year_in_review demo

# 传统 CMD
set PYTHONPATH=src && python -m mcd_year_in_review demo
```

Windows 上更省事的做法是直接用下面的方式 B，就不需要设 `PYTHONPATH` 了。

**方式 B · 装成命令行工具（拿掉 `PYTHONPATH` 前缀）**

```bash
pip install .          # 想改代码就换成 pip install -e .
mcd-year-in-review demo
```

装完以后命令就是 `mcd-year-in-review`，所有子命令和选项都一样。

### 常用命令一览

```bash
mcd-year-in-review [report|demo|export|account] [选项]
```

| 我想…… | 命令 |
|---|---|
| 看终端年报（默认行为） | `mcd-year-in-review` |
| 一键离线演示 | `mcd-year-in-review demo` |
| 生成 HTML 年报 | `mcd-year-in-review --mock --html my-report.html` |
| 只看某几个月 | `mcd-year-in-review --mock --start 2026-07-01 --end 2026-07-31` |
| 改显示的名字/城市 | `mcd-year-in-review --mock --name 小明 --city 北京` |
| 导出订单数据 | `mcd-year-in-review export --mock --json orders.json` |
| 安静生成、不打印终端 | 加 `--quiet` |
| 真实数据 + 逐单详情 | 加 `--live --detail` |

---

## 3. 用你自己的真实数据

真实数据需要**麦当劳 MCP Token**，没有 Token 就只能看第 2 步的示例数据。

**① 申请 Token**

去 <https://open.mcd.cn/mcp> 申请（需绑定你自己的麦当劳账号），参考官方仓库 [M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)。

**② 先验证 Token 能不能用（强烈建议第一步做这个）**

```bash
PYTHONPATH=src python3 -m mcd_year_in_review account --token "你的Token"
```

- ✅ 打印出**会员卡号（已打码） / 积分** → Token 有效。
- ❌ 报 `401：MCP Token 无效或已过期` → Token 不对或已失效。

**③ 拉真实订单，生成你的年报**

```bash
# 基础模式（推荐先用这个）
PYTHONPATH=src python3 -m mcd_year_in_review --live --html 我的年度账单.html --token "你的Token"

# 逐单补渠道/优惠（更慢，但可能让「省钱合计」更准确）
PYTHONPATH=src python3 -m mcd_year_in_review --live --detail --html 我的年度账单.html --token "你的Token"
```

**用环境变量传 Token 也行**（适合反复使用，省得每次敲）：

```bash
export MCD_MCP_TOKEN="你的Token"
PYTHONPATH=src python3 -m mcd_year_in_review --live --html 我的年度账单.html
```

配置了环境变量后，其实连 `--live` 都不用写：程序检测到 Token 就会自动走真实数据，检测不到才回退到示例数据。

> 官方 `query-my-account` 不一定会返回昵称和等级。如果拿不到，程序会用「麦当劳会员」+ 打码后的会员卡号占位。你可以用 `--name 小明` 覆盖显示名称。

> ⚠️ **隐私提醒**：Token 是你的账号凭证，**不要写进任何文件、不要提交到 Git**（本仓库 `.gitignore` 已排除常见密钥文件）。会员卡号默认打码展示，但年报仍包含你的消费画像，分享前自己看一眼内容。

---

## 4. 在 WorkBuddy 里当对话式 Skill 用

本仓库自带 [`skill/SKILL.md`](skill/SKILL.md)，可以把它挂成一个「本地命令」连接器，之后在对话里说一句「帮我生成今年的麦门年报」就能出图：

1. WorkBuddy →「连接器 / 自定义连接器」→ 新增「本地命令」；
2. 工作目录指向本仓库根目录；
3. 执行命令设为：

```bash
PYTHONPATH=src python3 -m mcd_year_in_review --mock --html /tmp/mcd-year-in-review.html --name {{user_name}} --city {{city}}
```

4. 输出格式选「文件」，把 `/tmp/mcd-year-in-review.html` 返回给对话。

（接入真实数据前，先按第 3 步配好 `MCD_MCP_TOKEN`。）

---

## 5. 在其它 MCP 客户端里使用

如果你不是想用这个年报工具，而是想**自己写客户端直接调麦当劳 MCP**，本仓库的 [`mcp-config.example.json`](mcp-config.example.json) 是一份现成的脱敏配置：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}
```

把它并进你的 MCP 客户端配置，把 `${MCD_MCP_TOKEN}` 换成真实 Token 即可。具体用了哪些 Tool、调用顺序如何，见 [`MCP_INTEGRATION.md`](MCP_INTEGRATION.md)。

---

## 6. 常见问题

**`No module named mcd_year_in_review`**
说明 Python 找不到这个包。两种解法：命令前加 `PYTHONPATH=src`，或者先用 `pip install .` 装一遍。另外要确认**是在仓库根目录**下执行的命令。

**`401` / Token 无效**
Token 错了或过期了，重新去 <https://open.mcd.cn/mcp> 申请/刷新。可以用 `account --token "..."` 单独验证。

**跑出来是空的 / 报「未取到历史订单」**
可能是这个时间范围内确实没有订单，或者账号没授权订单读取。先用 `account` 确认 Token 正常，再用 `--start/--end` 收窄时间范围试试。

**Windows 上 `PYTHONPATH=src` 报错**
Windows 不支持这种前置环境变量写法，改用 PowerShell 的 `$env:PYTHONPATH="src"`，或者干脆 `pip install .` 后用 `mcd-year-in-review` 命令。

**能离线用吗？**
完全可以。`--mock` 模式内置了固定种子的一年示例数据，不联网、不需要 Token，用来演示和开发都行。

**数据会上传吗？**
不会。所有计算都在你本地完成，只有在你**主动加 `--token`/`--live`** 时才会向 `mcp.mcd.cn` 请求你自己的订单数据。

**省钱合计为什么是「—」？**
麦当劳 `order-list` 接口不一定会返回每笔订单的原价/优惠明细。程序会如实显示「—」，加 `--detail` 有机会从 `query-order` 补齐，但不保证所有订单都能拿到。

**会员卡号为什么被打码？**
年报的设计目标之一就是「方便截图分享」，所以默认对会员卡号做 `42FBD022…6000` 这种打码处理。打印终端时会提示「已打码展示」。

---

本项目为麦当劳程序员节创意开发大赛参赛作品，非麦当劳官方产品。热量 / 健康换算纯属趣味玩梗，不构成专业建议。
