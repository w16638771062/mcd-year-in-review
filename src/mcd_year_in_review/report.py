"""年报渲染：生成一个**单文件、零外部依赖、离线可看**的 HTML 年度账单。

为什么坚持不用图表库 / CDN：
- 评审 clone 下来双击就能打开，不需要联网、不需要构建；
- 所有图形用内联 SVG 现算，任何环境渲染一致；
- 单文件方便截图、转发、发朋友圈——这正是 Star 增长的关键动作。
"""

from __future__ import annotations

import html
from datetime import datetime

from .badges import TIER_LABEL
from .stats import Stats

RED = "#DA291C"
RED_DARK = "#A31E14"
YELLOW = "#FFC72C"
INK = "#1B1B1B"
MUTED = "#7A736C"
CREAM = "#FFF8F0"
LINE = "#EBE2D8"

# 类目配色（与麦当劳红黄主色协调）
CAT_COLORS = ("#DA291C", "#F4A01C", "#FFC72C", "#7A9A4A", "#3E7CB1", "#8E6BAF", "#C96A8A", "#6B6B6B")

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #F2EDE7;
  color: #1B1B1B;
  font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  padding: 28px 16px 48px;
}
.page { max-width: 760px; margin: 0 auto; }
.card {
  background: #FFFFFF;
  border-radius: 18px;
  padding: 26px 26px 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.03);
}
.hero {
  background: #DA291C;
  border-radius: 18px;
  padding: 30px 28px 28px;
  margin-bottom: 16px;
  color: #FFFFFF;
  position: relative;
  overflow: hidden;
}
.hero:after {
  content: "";
  position: absolute;
  right: -46px; bottom: -70px;
  width: 190px; height: 190px;
  border-radius: 50%;
  background: #FFC72C;
  opacity: 0.92;
}
.hero .kicker { font-size: 12px; letter-spacing: 2px; opacity: 0.85; }
.hero h1 { font-size: 30px; font-weight: 500; margin: 10px 0 6px; letter-spacing: 0.5px; }
.hero .sub { font-size: 13px; opacity: 0.9; }
.hero .persona { font-size: 15px; margin-top: 16px; max-width: 460px; line-height: 1.65; position: relative; z-index: 1; }
h2 { font-size: 15px; font-weight: 500; margin-bottom: 4px; }
.hint { font-size: 12px; color: #7A736C; margin-bottom: 18px; }
.numbers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.num { background: #FFF8F0; border-radius: 12px; padding: 16px 14px; }
.num .v { font-size: 24px; font-weight: 500; color: #DA291C; line-height: 1.15; }
.num .v small { font-size: 12px; font-weight: 400; color: #7A736C; margin-left: 2px; }
.num .k { font-size: 12px; color: #7A736C; margin-top: 6px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; align-items: center; }
.legend { font-size: 13px; }
.legend .row { display: flex; align-items: center; gap: 8px; padding: 5px 0; }
.legend .dot { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.legend .nm { flex: 1; }
.legend .pc { color: #7A736C; font-variant-numeric: tabular-nums; }
.badges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.badge { border: 1px solid #EBE2D8; border-radius: 12px; padding: 14px; }
.badge.on { border-color: #DA291C; background: #FFF8F0; }
.badge .t { font-size: 13px; font-weight: 500; }
.badge .d { font-size: 11px; color: #7A736C; margin-top: 5px; line-height: 1.5; }
.badge .bar { height: 4px; background: #EBE2D8; border-radius: 2px; margin-top: 10px; overflow: hidden; }
.badge .bar i { display: block; height: 100%; background: #D9CFC4; }
.badge.on .bar i { background: #DA291C; }
.badge .pg { font-size: 10px; color: #7A736C; margin-top: 4px; font-variant-numeric: tabular-nums; }
.tier { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 6px; margin-left: 6px; vertical-align: 1px; }
.tier.gold { background: #FFC72C; color: #4A3600; }
.tier.silver { background: #E3E3E3; color: #454545; }
.tier.bronze { background: #F0DCC8; color: #6B4A28; }
.fun { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.fun .f { background: #FFF8F0; border-radius: 12px; padding: 16px; }
.fun .f .v { font-size: 20px; font-weight: 500; }
.fun .f .k { font-size: 12px; color: #7A736C; margin-top: 4px; line-height: 1.5; }
.rec { display: flex; gap: 14px; padding: 12px 0; border-bottom: 1px dashed #EBE2D8; font-size: 13px; }
.rec:last-child { border-bottom: none; }
.rec .lb { color: #7A736C; width: 96px; flex: none; }
.rec .vl { flex: 1; }
.rec .vl b { color: #DA291C; font-weight: 500; }
footer { text-align: center; font-size: 12px; color: #9A928A; margin-top: 22px; line-height: 1.8; }
@media (max-width: 620px) {
  .numbers { grid-template-columns: repeat(2, 1fr); }
  .two { grid-template-columns: 1fr; }
  .badges { grid-template-columns: 1fr 1fr; }
  .hero h1 { font-size: 24px; }
}
"""


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _money(value: float) -> str:
    return f"{value:,.0f}"


# ------------------------------------------------------------------ SVG 组件
def _peak_month_index(stats: Stats) -> int:
    if not stats.monthly:
        return 0
    return max(range(len(stats.monthly)), key=lambda index: stats.monthly[index].spend)


def _svg_monthly(stats: Stats) -> str:
    """按月消费柱状图（只画真实覆盖到的月份）。"""
    months = stats.monthly
    width, height = 700, 236
    left, right, top, base = 34, 34, 34, 176
    chart_w = width - left - right
    slot = chart_w / max(len(months), 1)
    bar_w = slot * 0.56
    peak = max((p.spend for p in months), default=0.0) or 1.0
    best = _peak_month_index(stats)

    bars = []
    for index, point in enumerate(months):
        ratio = point.spend / peak
        bar_h = max(ratio * (base - top), 3 if point.spend > 0 else 0)
        x = left + index * slot + (slot - bar_w) / 2
        y = base - bar_h
        is_peak = index == best and point.spend > 0
        fill = RED if is_peak else "#F3C9C4"
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{fill}"/>')
        label_fill = RED if is_peak else MUTED
        weight = "500" if is_peak else "400"
        if point.spend > 0:
            bars.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" '
                f'font-size="10.5" fill="{label_fill}" font-weight="{weight}">{_money(point.spend)}</text>'
            )
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{base + 20:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{MUTED}">{point.label}</text>'
        )
    axis = f'<line x1="{left}" y1="{base}" x2="{width - right}" y2="{base}" stroke="{LINE}" stroke-width="1"/>'
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="按月消费分布柱状图">{"".join(bars)}{axis}</svg>'
    )


def _svg_donut(stats: Stats) -> str:
    """类目占比环形图。"""
    size, radius, stroke = 220, 74, 26
    center = size / 2
    circumference = 2 * 3.141592653589793 * radius
    slices = stats.categories[:8]
    offset = 0.0
    arcs = []
    for index, item in enumerate(slices):
        length = max(item.pct / 100 * circumference, 0)
        color = CAT_COLORS[index % len(CAT_COLORS)]
        arcs.append(
            f'<circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-dasharray="{length:.2f} {circumference - length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}"/>'
        )
        offset += length
    total = f'<text x="{center}" y="{center - 4}" text-anchor="middle" font-size="24" font-weight="500" fill="{INK}">{stats.item_count}</text>'
    total2 = f'<text x="{center}" y="{center + 18}" text-anchor="middle" font-size="11" fill="{MUTED}">件餐品</text>'
    return (
        f'<svg viewBox="0 0 {size} {size}" width="100%" style="max-width:220px" role="img" '
        f'aria-label="类目占比环形图"><g transform="rotate(-90 {center} {center})">'
        f'{"".join(arcs)}</g>{total}{total2}</svg>'
    )


def _svg_hbars(rows: list[tuple[str, float, str]], width: int = 640) -> str:
    """通用横向条形图：rows = [(标签, 数值, 右侧说明), ...]"""
    row_h, gap, label_w = 30, 12, 118
    height = len(rows) * (row_h + gap) + 10
    track_x = label_w + 10
    track_w = width - track_x - 74
    peak = max((value for _, value, _ in rows), default=1.0) or 1.0

    parts = []
    for index, (name, value, note) in enumerate(rows):
        y = index * (row_h + gap) + 6
        bar_w = max(value / peak * track_w, 2)
        parts.append(
            f'<text x="0" y="{y + 20}" font-size="12.5" fill="{INK}">{_esc(name)}</text>'
        )
        parts.append(
            f'<rect x="{track_x}" y="{y + 7}" width="{track_w}" height="18" rx="5" fill="#F5EFE8"/>'
        )
        parts.append(
            f'<rect x="{track_x}" y="{y + 7}" width="{bar_w:.1f}" height="18" rx="5" fill="{RED}"/>'
        )
        parts.append(
            f'<text x="{width}" y="{y + 20}" text-anchor="end" font-size="12" fill="{MUTED}">{_esc(note)}</text>'
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="横向条形图">{"".join(parts)}</svg>'
    )


# ------------------------------------------------------------------ 组装
def build_html(
    stats: Stats,
    source_note: str,
    account: dict | None = None,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()
    account = account or {}

    legend_rows = []
    for index, item in enumerate(stats.categories[:8]):
        color = CAT_COLORS[index % len(CAT_COLORS)]
        legend_rows.append(
            f'<div class="row"><span class="dot" style="background:{color}"></span>'
            f'<span class="nm">{_esc(item.name)}</span>'
            f'<span class="pc">{item.pct}% · {item.count} 件</span></div>'
        )

    if stats.has_item_prices:
        top_rows = [
            (item.name, float(item.qty), f"{item.qty} 份 · ¥{_money(item.spend)}")
            for item in stats.top_items[:6]
        ]
        top_hint = "按一年内点过的份数排序"
    else:
        # 真实订单里官方只给「整单金额」，套餐展开后拿不到单品价，因此改展示热量
        top_rows = [
            (item.name, float(item.qty), f"{item.qty} 份 · {item.kcal:,.0f} kcal" if item.kcal else f"{item.qty} 份")
            for item in stats.top_items[:6]
        ]
        top_hint = "按一年内点过的份数排序（真实订单的套餐已展开为单品，热量来自官方营养表）"
    daypart_rows = [(p.name, float(p.count), f"{p.count} 单 · {p.pct}%") for p in stats.dayparts]
    store_rows = [(s.name, float(s.count), f"{s.count} 单 · ¥{_money(s.spend)}") for s in stats.stores[:5]]

    badge_cards = []
    for result in stats.badges:
        badge = result.badge
        cls = "badge on" if result.unlocked else "badge"
        tier_cls = badge.tier
        progress = (
            f'<div class="bar"><i style="width:{result.pct:.0f}%"></i></div>'
            f'<div class="pg">{result.pct:.0f}% · {result.current:g}/{result.target:g}{_esc(result.unit)}</div>'
        )
        badge_cards.append(
            f'<div class="{cls}"><div class="t">{_esc(badge.name)}'
            f'<span class="tier {tier_cls}">{TIER_LABEL[badge.tier]}</span></div>'
            f'<div class="d">{_esc(badge.desc)}</div>{progress}</div>'
        )

    fun_cards = []
    if stats.total_kcal > 0:
        fun_cards += [
            (f'{stats.fun["bigmac"]:,.1f} 个', "热量相当于这么多巨无霸"),
            (f'{stats.fun["rice"]:,.1f} 碗', "相当于这么多碗米饭（约 230 kcal/碗）"),
            (f'{stats.fun["run_km"]:,.1f} km', "要慢跑这么远才能消耗掉（约 60 kcal/km）"),
        ]
    fun_cards.append((f'{stats.fun["milk_tea"]:,.1f} 杯', "这笔钱够买这么多杯奶茶（按 15 元/杯）"))
    fun_html = "".join(
        f'<div class="f"><div class="v">{_esc(value)}</div><div class="k">{_esc(label)}</div></div>'
        for value, label in fun_cards
    )

    max_order = stats.max_order
    max_kcal_order = stats.most_kcal_order
    records = []
    if max_order is not None:
        records.append(
            ("最贵的一单", f"{max_order.ts:%Y-%m-%d} 在 {_esc(max_order.store)} 花了 <b>¥{_money(max_order.paid)}</b>，"
                           f"点了 {max_order.item_count} 件：{'、'.join(_esc(name) for name in max_order.item_names[:4])}")
        )
    if max_kcal_order is not None and max_kcal_order.kcal > 0:
        records.append(
            ("热量最高一单", f"{max_kcal_order.ts:%Y-%m-%d} 的 {_esc(max_kcal_order.store)} 一单干掉了 "
                             f"<b>{max_kcal_order.kcal:,.0f} kcal</b>")
        )
    records.append(("最长连续打卡", f"连着 <b>{stats.longest_streak}</b> 天没有断过麦门"))
    records.append(("外送 vs 到店", f"外送 {stats.delivery_count} 单（{stats.delivery_ratio}%），"
                                   f"到店 {stats.dine_in_count} 单，{_esc(stats.fav_store)} 是出现最多的门店"))
    records_html = "".join(
        f'<div class="rec"><div class="lb">{_esc(label)}</div><div class="vl">{value}</div></div>'
        for label, value in records
    )

    account_rows: list[tuple[str, str]] = []
    if account:
        points_label = account.get("points_label") or "积分"
        if account.get("name"):
            account_rows.append(("会员昵称", f"<b>{_esc(account['name'])}</b>"))
        if account.get("member_id"):
            account_rows.append(("会员卡号", f"<b>{_esc(account['member_id'])}</b>"))
        if account.get("level"):
            account_rows.append(("会员等级", f"<b>{_esc(account['level'])}</b>"))
        available = account.get("points_available")
        total_points = account.get("points_total")
        if available is not None or total_points is not None:
            account_rows.append(
                (points_label, f"当前可用 <b>{_esc(available if available is not None else 0)}</b>，"
                               f"历史累计 <b>{_esc(total_points if total_points is not None else 0)}</b>")
            )
        if account.get("points_used"):
            account_rows.append(("已使用", f"<b>{_esc(account['points_used'])}</b> {_esc(points_label)}"))
        if account.get("points_expiring") not in (None, 0):
            account_rows.append(("即将过期", f"<b>{_esc(account['points_expiring'])}</b> {_esc(points_label)}，记得用掉"))
    points_line = "".join(
        f'<div class="rec"><div class="lb">{_esc(label)}</div><div class="vl">{value}</div></div>'
        for label, value in account_rows
    )
    account_section = (
        f'<section class="card">\n    <h2>会员账号</h2>\n    {points_line}\n  </section>'
        if points_line
        else ""
    )
    hero_level = f" · {_esc(account['level'])}" if account and account.get("level") else ""
    hero_meta = " · ".join(
        part
        for part in (
            f"{stats.start:%Y.%m.%d} - {stats.end:%Y.%m.%d}",
            stats.city,
            stats.member_id,
        )
        if part
    )
    kcal_value = f"{stats.total_kcal / 1000:,.1f}" if stats.total_kcal > 0 else "—"
    coverage_hint = (
        f"　热量数据覆盖 {stats.nutrition_coverage:g}% 的餐品（来自官方营养表）"
        if stats.total_kcal > 0 and stats.nutrition_coverage < 100
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(stats.user_name)} 的 {stats.year_label} 麦门年度账单</title>
<style>{_CSS}</style>
</head>
<body>
<div class="page">

  <header class="hero">
    <div class="kicker">MCDONALD'S YEAR IN REVIEW · {stats.year_label}</div>
    <h1>{_esc(stats.user_name)} 的麦门年度账单</h1>
    <div class="sub">{_esc(hero_meta)}{hero_level}</div>
    <div class="persona">{_esc(stats.headline)}<br>{_esc(stats.persona_line)}</div>
  </header>

  <section class="card">
    <h2>年度总览</h2>
    <div class="hint">数据来源：{_esc(source_note)}</div>
    <div class="numbers">
      <div class="num"><div class="v">¥{_money(stats.total_spend)}</div><div class="k">年度总消费</div></div>
      <div class="num"><div class="v">{stats.order_count}<small>单</small></div><div class="k">下单次数</div></div>
      <div class="num"><div class="v">{kcal_value}<small>千千卡</small></div><div class="k">摄入总热量</div></div>
      <div class="num"><div class="v">¥{_money(stats.total_discount)}</div><div class="k">省下的钱（{stats.saved_pct}%）</div></div>
    </div>
  </section>

  <section class="card">
    <h2>每月消费分布</h2>
    <div class="hint">红色柱子是你全年最上头的一个月：{stats.monthly[_peak_month_index(stats)].label}</div>
    {_svg_monthly(stats)}
  </section>

  <section class="card">
    <h2>口味画像</h2>
    <div class="hint">吃得最多的是「{_esc(stats.fav_category)}」，单品冠军是「{_esc(stats.fav_item)}」{coverage_hint}</div>
    <div class="two">
      <div>{_svg_donut(stats)}</div>
      <div class="legend">{"".join(legend_rows)}</div>
    </div>
  </section>

  <section class="card">
    <h2>你最爱的单品</h2>
    <div class="hint">{_esc(top_hint)}</div>
    {_svg_hbars(top_rows)}
  </section>

  <section class="card">
    <h2>作息画像</h2>
    <div class="hint">你最常在「{_esc(stats.fav_daypart)}」时段出现</div>
    {_svg_hbars(daypart_rows)}
  </section>

  <section class="card">
    <h2>门店足迹</h2>
    <div class="hint">一年里你在 {len(stats.stores)} 家门店打过卡（列出前 5）</div>
    {_svg_hbars(store_rows)}
  </section>

  <section class="card">
    <h2>年度记录</h2>
    {records_html}
  </section>

  {account_section}

  <section class="card">
    <h2>成就徽章</h2>
    <div class="hint">已解锁 {sum(1 for r in stats.badges if r.unlocked)} / {len(stats.badges)} 枚</div>
    <div class="badges">{"".join(badge_cards)}</div>
  </section>

  <section class="card">
    <h2>趣味换算</h2>
    <div class="hint">纯属玩梗，不构成任何营养或健康建议</div>
    <div class="fun">{fun_html}</div>
  </section>

  <footer>
    由「麦门年度账单 · mcd-year-in-review」生成 · {generated_at:%Y-%m-%d %H:%M}<br>
    基于麦当劳 MCP 构建 · 非麦当劳官方产品 · 餐品与价格以官方渠道实时结果为准
  </footer>

</div>
</body>
</html>
"""


def write_html(stats: Stats, source_note: str, path: str, account: dict | None = None) -> str:
    content = build_html(stats, source_note, account=account)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path
