"""终端渲染：把年报直接打印在命令行里，方便快速查看与 CI 断言。

中文在等宽字体里占两个字符宽，所以这里自己做了一个宽度计算，
否则排版会歪。
"""

from __future__ import annotations

from .stats import Stats


def _w(text: str) -> int:
    """估算字符串在等宽终端里的显示宽度（CJK 记 2）。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(width - _w(text), 0)


def _bar(value: float, peak: float, width: int = 26) -> str:
    if peak <= 0:
        return " " * width
    filled = int(round(value / peak * width))
    return "█" * filled + " " * (width - filled)


def account_summary(account: dict | None) -> list[str]:
    """把归一化后的账号信息渲染成几行文本；没有有效字段时返回空列表。"""
    if not account:
        return []
    unit = str(account.get("points_label") or "积分")
    rows: list[tuple[str, str]] = []
    if account.get("name"):
        rows.append(("会员昵称", str(account["name"])))
    if account.get("member_id"):
        rows.append(("会员卡号", str(account["member_id"])))
    if account.get("level"):
        rows.append(("会员等级", str(account["level"])))
    if account.get("points_available") is not None:
        rows.append(("当前可用积分", f"{account['points_available']:,}"))
    if account.get("points_total") is not None:
        rows.append(("历史累计积分", f"{account['points_total']:,}"))
    if account.get("points_used") is not None:
        rows.append(("已使用积分", f"{account['points_used']:,}"))
    if account.get("points_expiring") is not None:
        rows.append(("即将过期积分", f"{account['points_expiring']:,}"))
    if unit != "积分":
        rows.append(("积分类型", unit))
    return [f"  {_pad(name, 16)}{value}" for name, value in rows]


def account_card(account: dict) -> str:
    """`account` 子命令的输出：直接把真实账号信息打出来。"""
    rows = account_summary(account)
    rule = "=" * 56
    out = [rule, "  麦当劳 MCP · 账号信息", rule, ""]
    out.extend(rows or ["  （未取到任何账号字段，请确认 Token 与授权状态）"])
    out.append("")
    out.append("  注：会员卡号默认打码展示，避免分享时泄露账号。")
    out.append("基于麦当劳 MCP 构建 · 非麦当劳官方产品")
    out.append(rule)
    return "\n".join(out)


def summarize(stats: Stats, source_note: str = "", account: dict | None = None) -> str:
    lines: list[str] = []
    rule = "=" * 56

    level = (account or {}).get("level") or getattr(stats, "level", "")
    identity_parts = [stats.user_name, stats.city, stats.member_id]
    if level:
        identity_parts.append(level)
    identity = "  " + " · ".join(part for part in identity_parts if part)

    lines.append(rule)
    lines.append(f"  麦门年度账单 · {stats.year_label}")
    lines.append(identity)
    lines.append(f"  {stats.start:%Y-%m-%d} ~ {stats.end:%Y-%m-%d}")
    lines.append(rule)
    lines.append("")

    lines.append(f"【年度关键词】{stats.headline}")
    lines.append(f"  {stats.persona_line}")
    lines.append("")

    account_lines = account_summary(account)
    if account_lines:
        lines.append("【会员账号】")
        lines.extend(account_lines)
        lines.append("")

    kcal_text = f"{stats.total_kcal:,.0f} kcal" if stats.total_kcal > 0 else "—"
    if stats.total_kcal > 0 and stats.nutrition_coverage < 100:
        kcal_text += f"（覆盖 {stats.nutrition_coverage:g}% 餐品）"
    saved_text = (
        f"¥{stats.total_discount:,.2f}（原价 {stats.saved_pct}%）"
        if stats.total_discount > 0
        else "—（官方列表接口未提供优惠明细）"
    )
    rows = [
        ("年度总消费", f"¥{stats.total_spend:,.2f}"),
        ("下单次数", f"{stats.order_count} 单"),
        ("吃掉餐品", f"{stats.item_count} 件"),
        ("摄入总热量", kcal_text),
        ("单均消费", f"¥{stats.avg_per_order:,.2f}"),
        ("省钱合计", saved_text),
        ("活跃天数", f"{stats.active_days} / {stats.span_days} 天"),
        ("最长连续打卡", f"{stats.longest_streak} 天"),
    ]
    lines.append("【年度总览】")
    for label, value in rows:
        lines.append(f"  {_pad(label, 14)}{value}")
    lines.append("")

    peak_month = max((p.spend for p in stats.monthly), default=0.0)
    lines.append("【每月消费】")
    for point in stats.monthly:
        if point.spend > 0:
            tail = f"¥{point.spend:,.0f}（{point.orders} 单）"
        elif point.orders > 0:
            tail = f"{point.orders} 单 · ¥0（用券）"
        else:
            tail = "—"
        lines.append(f"  {_pad(point.label, 6)}{_bar(point.spend, peak_month)}  {tail}")
    lines.append("")

    lines.append("【口味画像】")
    peak_cat = max((c.count for c in stats.categories), default=1)
    for item in stats.categories[:6]:
        lines.append(f"  {_pad(item.name, 8)}{_bar(item.count, peak_cat, 20)}  {item.count:>4} 件  {item.pct:>5}%")
    lines.append("")

    lines.append("【最爱单品 Top 5】")
    for index, item in enumerate(stats.top_items[:5], start=1):
        if stats.has_item_prices:
            tail = f"¥{item.spend:,.0f}"
        else:
            tail = f"{item.kcal:,.0f} kcal" if item.kcal else "—"
        lines.append(f"  {index}. {_pad(item.name, 18)}{item.qty:>3} 份   {tail}")
    lines.append("")

    lines.append("【作息画像】")
    peak_day = max((d.count for d in stats.dayparts), default=1)
    for part in stats.dayparts:
        lines.append(f"  {_pad(part.name, 8)}{_bar(part.count, peak_day, 20)}  {part.count:>3} 单  {part.pct:>5}%")
    lines.append("")

    lines.append("【门店足迹】")
    for index, store in enumerate(stats.stores[:5], start=1):
        lines.append(f"  {index}. {_pad(store.name, 16)}{store.count:>3} 单   ¥{store.spend:,.0f}")
    lines.append("")

    lines.append("【年度记录】")
    if stats.max_order is not None:
        order = stats.max_order
        names = "、".join(order.item_names[:4])
        lines.append(f"  · 最贵一单：{order.ts:%Y-%m-%d} @ {order.store}，¥{order.paid:,.2f}（{names}）")
    if stats.most_kcal_order is not None and stats.most_kcal_order.kcal > 0:
        order = stats.most_kcal_order
        lines.append(f"  · 热量最高：{order.ts:%Y-%m-%d} @ {order.store}，{order.kcal:,.0f} kcal")
    lines.append(f"  · 外送 / 到店：{stats.delivery_count} / {stats.dine_in_count} 单（外送占比 {stats.delivery_ratio}%）")
    lines.append("")

    lines.append("【成就徽章】")
    for result in stats.badges:
        mark = "[已解锁]" if result.unlocked else "[   ]"
        lines.append(f"  {mark} {_pad(result.badge.name, 14)}{result.badge.desc}")
    lines.append("")

    lines.append("【趣味换算】")
    if stats.total_kcal > 0:
        lines.append(f"  · 总热量约等于 {stats.fun['bigmac']:,.1f} 个巨无霸")
        lines.append(f"  · 约等于 {stats.fun['rice']:,.1f} 碗米饭")
        lines.append(f"  · 要慢跑 {stats.fun['run_km']:,.1f} 公里才能消耗掉")
    lines.append(f"  · 这笔钱够买 {stats.fun['milk_tea']:,.1f} 杯奶茶（按 15 元/杯）")
    lines.append("")

    if source_note:
        lines.append(f"数据来源：{source_note}")
    lines.append("基于麦当劳 MCP 构建 · 非麦当劳官方产品")
    lines.append(rule)
    return "\n".join(lines)
