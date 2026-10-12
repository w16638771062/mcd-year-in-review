"""命令行入口。

用法示例::

    python -m mcd_year_in_review                    # 自动选择数据源
    python -m mcd_year_in_review --mock --html report.html
    python -m mcd_year_in_review --live --name 张三 --city 上海
    python -m mcd_year_in_review demo               # 一键演示（离线）
    python -m mcd_year_in_review export --mock --json orders.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime

from . import badges, mock_data, report, render, source
from .mcp_client import MCPClient, MCPError
from .stats import compute


def _parse_date(text: str) -> date:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:  # noqa: TRY003
        raise argparse.ArgumentTypeError(f"日期格式应为 YYYY-MM-DD，收到：{text}") from exc


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mock", action="store_true", help="强制使用离线示例数据")
    parser.add_argument("--live", action="store_true", help="强制通过麦当劳 MCP 拉取真实订单")
    parser.add_argument("--token", help="麦当劳 MCP Token（也可用环境变量 MCD_MCP_TOKEN）")
    parser.add_argument("--start", type=_parse_date, help="统计起始日期 YYYY-MM-DD")
    parser.add_argument("--end", type=_parse_date, help="统计结束日期 YYYY-MM-DD")
    parser.add_argument("--name", help="展示用的用户名（默认取账号昵称）")
    parser.add_argument("--city", help="城市（也用于真实数据源筛选）")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="真实数据模式下，额外逐单调用 query-order 补齐渠道 / 优惠明细（更准但更慢）",
    )
    parser.add_argument("--html", metavar="PATH", help="把年度账单写成一个可直接分享的 HTML 文件")
    parser.add_argument("--json", dest="json_path", metavar="PATH", help="把归一化后的订单导出为 JSON")
    parser.add_argument("--quiet", action="store_true", help="不打印终端年报")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcd-year-in-review",
        description="麦门年度账单：基于麦当劳 MCP 生成你的年度消费 / 口味 / 作息画像。",
    )
    sub = parser.add_subparsers(dest="command")

    report_parser = sub.add_parser("report", help="生成年度账单（默认行为）")
    _add_common(report_parser)

    demo_parser = sub.add_parser("demo", help="用离线示例数据一键演示")
    _add_common(demo_parser)

    export_parser = sub.add_parser("export", help="只导出归一化订单 JSON")
    _add_common(export_parser)

    account_parser = sub.add_parser("account", help="只读取并打印真实会员账号信息（用于验证 Token）")
    _add_common(account_parser)

    # 不带子命令时，等价于 report
    _add_common(parser)
    return parser


def _resolve_source(args: argparse.Namespace) -> bool:
    """决定用离线还是真实数据源：显式参数优先，否则看有没有 Token。"""
    if args.mock and args.live:
        raise SystemExit("--mock 与 --live 不能同时使用")
    if args.mock:
        return True
    if args.live or getattr(args, "token", None):
        return False
    return not (os.environ.get("MCD_MCP_TOKEN"))


def _load(args: argparse.Namespace):
    use_mock = _resolve_source(args)
    client = None
    if not use_mock:
        client = MCPClient(token=args.token) if getattr(args, "token", None) else MCPClient()
    orders, user, note, account = source.load_orders(
        mock=use_mock,
        client=client,
        start=args.start,
        end=args.end,
        city=args.city or "",
        detail=bool(getattr(args, "detail", False)) and not use_mock,
    )
    if args.name:
        user["name"] = args.name
    if args.city:
        user["city"] = args.city
    return orders, user, note, account, client


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "report"

    # account 子命令：只验证 Token 并打印真实账号，不要求必须有订单
    if command == "account":
        if _resolve_source(args):
            print("未提供 Token（--token 或 MCD_MCP_TOKEN）时无法读取真实账号。")
            print("下面展示的是离线示例账号结构：\n")
            print(render.account_card(dict(mock_data.MOCK_ACCOUNT)))
            return 0
        client = MCPClient(token=args.token) if getattr(args, "token", None) else MCPClient()
        try:
            account = source.fetch_account(client)
        except MCPError as exc:
            print(f"✗ {exc}", file=sys.stderr)
            return 2
        finally:
            client.close()
        if not account or not any(
            account.get(key)
            for key in ("name", "member_id", "level", "points_available", "points_total")
        ):
            print(
                "✗ 已连上麦当劳 MCP，但未返回可用账号字段；请确认 Token 权限与账号授权状态。",
                file=sys.stderr,
            )
            return 2
        print(render.account_card(account))
        return 0

    try:
        orders, user, note, account, client = _load(args)
    except MCPError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        print("  提示：加 --mock 可先看离线示例效果。", file=sys.stderr)
        return 2

    stats = compute(orders, user)
    badges.attach(stats, orders)

    if command == "export":
        payload = source.dumps(orders)
        if args.json_path:
            with open(args.json_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
            print(f"已导出 {len(orders)} 条订单 → {args.json_path}")
        else:
            print(payload)
        return 0

    if command == "demo":
        print("麦门年度账单 · 演示模式（离线示例数据，无需 MCP Token）")
        print()

    if not args.quiet:
        print(render.summarize(stats, source_note=note, account=account))

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            handle.write(source.dumps(orders))
        print(f"（已导出归一化订单 → {args.json_path}）")

    if args.html:
        report.write_html(stats, note, args.html, account=account)
        print(f"（已生成可分享的年度账单 → {args.html}）")

    if client is not None:
        client.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
