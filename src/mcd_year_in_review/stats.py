"""统计引擎：把一堆订单折算成一份"拿得出手"的年度画像。

所有口径集中在这里，模型层只负责表达事实，渲染层只负责排版。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

from .models import Order

# 趣味换算用的常量（均为公开常识值，仅用于玩梗，不代表营养建议）
BIGMAC_KCAL = 550.0
RICE_BOWL_KCAL = 230.0
RUN_KCAL_PER_KM = 60.0
MILK_TEA_PRICE = 15.0

DAYPART_ORDER = ("早餐", "午餐", "下午茶", "晚餐", "夜宵")


@dataclass
class MonthlyPoint:
    label: str
    spend: float
    orders: int
    kcal: float


@dataclass
class CategorySlice:
    name: str
    count: int
    spend: float
    pct: float
    kcal: float = 0.0


@dataclass
class ItemRank:
    name: str
    qty: int
    spend: float
    kcal: float = 0.0


@dataclass
class DaypartSlice:
    name: str
    count: int
    pct: float


@dataclass
class StoreRank:
    name: str
    count: int
    spend: float


@dataclass
class Stats:
    user_name: str
    city: str
    member_id: str
    start: date
    end: date

    total_spend: float
    total_listed: float
    total_discount: float
    order_count: int
    item_count: int
    total_kcal: float
    avg_per_order: float
    active_days: int
    span_days: int
    longest_streak: int

    monthly: list[MonthlyPoint]
    categories: list[CategorySlice]
    top_items: list[ItemRank]
    dayparts: list[DaypartSlice]
    stores: list[StoreRank]

    delivery_count: int
    dine_in_count: int
    max_order: Order | None
    most_kcal_order: Order | None

    fav_item: str
    fav_category: str
    fav_daypart: str
    fav_store: str

    persona_tag: str
    persona_line: str
    headline: str
    has_item_prices: bool = True
    nutrition_coverage: float = 100.0
    fun: dict[str, float] = field(default_factory=dict)
    badges: list = field(default_factory=list)

    @property
    def saved_pct(self) -> float:
        if self.total_listed <= 0:
            return 0.0
        return round(self.total_discount / self.total_listed * 100, 1)

    @property
    def delivery_ratio(self) -> float:
        if self.order_count <= 0:
            return 0.0
        return round(self.delivery_count / self.order_count * 100, 1)

    @property
    def year_label(self) -> str:
        """年份标签：跨年时显示 ``2025–2026``，同年只显示一个年份。"""
        if self.start.year == self.end.year:
            return str(self.start.year)
        return f"{self.start.year}–{self.end.year}"


def _month_axis(start: date, end: date) -> list[tuple[int, int]]:
    """列出 start ~ end 之间连续的 ``(年, 月)``，跨年时不会补出多余的空月份。"""
    months: list[tuple[int, int]] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _longest_streak(days: list[date]) -> int:
    """最长连续下单天数。"""
    if not days:
        return 0
    unique = sorted(set(days))
    best = current = 1
    for prev, cur in zip(unique, unique[1:]):
        if cur - prev == timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def _persona(fav_daypart: str, fav_category: str, order_count: int, saved: float) -> tuple[str, str]:
    """根据作息与口味给一个"人设标签 + 一句话"。"""
    tag = {
        "夜宵": "夜宵行动派",
        "早餐": "早八早餐官",
        "下午茶": "办公室续命家",
        "午餐": "午饭搭子",
        "晚餐": "准点干饭人",
    }.get(fav_daypart, "麦门常客")

    flavor = {
        "汉堡": "扎实管饱的汉堡才是正经饭",
        "小食": "薯条和鸡块永远是你的开场白",
        "饮料": "一杯冰可乐就能救你一整天",
        "甜品": "甜党本色，先上甜品再谈正事",
        "咖啡": "咖啡因才是你真正的续命燃料",
        "早餐": "一天从一份热腾腾的早餐开始",
    }.get(fav_category, "菜单上就没有你不爱的")

    line = (
        f"一年 {order_count} 单，{fav_daypart}时段是你出现最频繁的战场——"
        f"{flavor}。"
    )
    if saved >= 200:
        line += f"顺带一提，你靠优惠券和满减硬生生省下了 {saved:.0f} 元，是会过日子的人。"
    return tag, line


def compute(orders: list[Order], user: dict[str, str] | None = None) -> Stats:
    """把订单列表折算成一份完整的年度画像。"""
    user = user or {"name": "麦门信徒", "city": "深圳", "member_id": "M****1024"}
    if not orders:
        raise ValueError("没有可用于统计的订单数据")

    orders = sorted(orders, key=lambda order: order.ts)
    start, end = orders[0].ts.date(), orders[-1].ts.date()

    total_spend = round(sum(order.paid for order in orders), 2)
    total_listed = round(sum(order.listed for order in orders), 2)
    total_kcal = round(sum(order.kcal for order in orders), 1)
    item_count = sum(order.item_count for order in orders)
    order_count = len(orders)

    # ---- 月度分布（跨年时沿时间轴连续展开，只画真实覆盖到的月份）----
    month_bucket: dict[tuple[int, int], dict[str, float]] = {}
    for order in orders:
        bucket = month_bucket.setdefault((order.ts.year, order.ts.month), {"spend": 0.0, "orders": 0, "kcal": 0.0})
        bucket["spend"] += order.paid
        bucket["orders"] += 1
        bucket["kcal"] += order.kcal
    same_year = start.year == end.year
    monthly: list[MonthlyPoint] = []
    for year, month in _month_axis(start, end):
        bucket = month_bucket.get((year, month), {})
        monthly.append(
            MonthlyPoint(
                label=f"{month}月" if same_year else f"{year % 100}/{month}",
                spend=round(bucket.get("spend", 0.0), 2),
                orders=int(bucket.get("orders", 0)),
                kcal=round(bucket.get("kcal", 0.0), 1),
            )
        )

    # ---- 类目画像 ----
    cat_count: Counter[str] = Counter()
    cat_spend: Counter[str] = Counter()
    cat_kcal: Counter[str] = Counter()
    item_count_map: Counter[str] = Counter()
    item_spend: Counter[str] = Counter()
    item_kcal: Counter[str] = Counter()
    qty_total = qty_known = 0
    has_item_prices = False
    for order in orders:
        for item in order.items:
            cat_count[item.category] += item.qty
            cat_spend[item.category] += item.subtotal
            cat_kcal[item.category] += item.kcal
            item_count_map[item.name] += item.qty
            item_spend[item.name] += item.subtotal
            item_kcal[item.name] += item.kcal
            qty_total += item.qty
            if item.kcal_per_unit > 0:
                qty_known += item.qty
            if item.unit_price > 0:
                has_item_prices = True
    total_items = sum(cat_count.values()) or 1
    categories = [
        CategorySlice(
            name=name,
            count=count,
            spend=round(cat_spend[name], 2),
            pct=round(count / total_items * 100, 1),
            kcal=round(cat_kcal[name], 1),
        )
        for name, count in cat_count.most_common()
    ]
    top_items = [
        ItemRank(name=name, qty=qty, spend=round(item_spend[name], 2), kcal=round(item_kcal[name], 1))
        for name, qty in item_count_map.most_common(8)
    ]
    nutrition_coverage = round(qty_known / qty_total * 100, 1) if qty_total else 100.0

    # ---- 时段与渠道 ----
    daypart_count: Counter[str] = Counter(order.daypart for order in orders)
    dayparts = [
        DaypartSlice(name=name, count=daypart_count.get(name, 0), pct=round(daypart_count.get(name, 0) / order_count * 100, 1))
        for name in DAYPART_ORDER
    ]
    delivery_count = sum(1 for order in orders if order.is_delivery)

    # ---- 门店偏好 ----
    store_count: Counter[str] = Counter(order.store for order in orders)
    store_spend: Counter[str] = Counter()
    for order in orders:
        store_spend[order.store] += order.paid
    stores = [
        StoreRank(name=name, count=count, spend=round(store_spend[name], 2))
        for name, count in store_count.most_common(6)
    ]

    # ---- 记录 ----
    dates = [order.ts.date() for order in orders]
    max_order = max(orders, key=lambda order: order.paid)
    most_kcal_order = max(orders, key=lambda order: order.kcal)

    fav_item = top_items[0].name if top_items else "—"
    fav_category = categories[0].name if categories else "—"
    fav_daypart = max(DAYPART_ORDER, key=lambda name: daypart_count.get(name, 0))
    fav_store = stores[0].name if stores else "—"

    total_discount = round(total_listed - total_spend, 2)
    tag, line = _persona(fav_daypart, fav_category, order_count, total_discount)
    year_label = f"{start.year}–{end.year}" if start.year != end.year else str(start.year)

    fun = {
        "bigmac": round(total_kcal / BIGMAC_KCAL, 1),
        "run_km": round(total_kcal / RUN_KCAL_PER_KM, 1),
        "rice": round(total_kcal / RICE_BOWL_KCAL, 1),
        "milk_tea": round(total_spend / MILK_TEA_PRICE, 1),
    }

    return Stats(
        user_name=user.get("name", "麦门信徒"),
        city=user.get("city", "深圳"),
        member_id=user.get("member_id", "M****1024"),
        start=start,
        end=end,
        total_spend=total_spend,
        total_listed=total_listed,
        total_discount=total_discount,
        order_count=order_count,
        item_count=item_count,
        total_kcal=total_kcal,
        avg_per_order=round(total_spend / order_count, 2),
        active_days=len(set(dates)),
        span_days=(end - start).days + 1,
        longest_streak=_longest_streak(dates),
        monthly=monthly,
        categories=categories,
        top_items=top_items,
        dayparts=dayparts,
        stores=stores,
        delivery_count=delivery_count,
        dine_in_count=order_count - delivery_count,
        max_order=max_order,
        most_kcal_order=most_kcal_order,
        fav_item=fav_item,
        fav_category=fav_category,
        fav_daypart=fav_daypart,
        fav_store=fav_store,
        persona_tag=tag,
        persona_line=line,
        headline=f"{year_label} 麦门年度关键词：「{tag}」",
        has_item_prices=has_item_prices,
        nutrition_coverage=nutrition_coverage,
        fun=fun,
    )
