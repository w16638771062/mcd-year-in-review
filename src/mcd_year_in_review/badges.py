"""成就徽章：声明式规则引擎。

规则是"数据"而不是"代码"——新增一个徽章只需要往 ``DEFAULT_RULES`` 里加一行，
求值逻辑完全通用。这样徽章体系可以持续扩充，而不必改动引擎。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .models import Order
from .stats import Stats

TIER_LABEL = {"gold": "金", "silver": "银", "bronze": "铜"}


@dataclass(frozen=True)
class Badge:
    key: str
    name: str
    desc: str
    tier: str = "bronze"


@dataclass(frozen=True)
class BadgeRule:
    """一条徽章规则：当 ``metrics[metric] >= target`` 时解锁。"""

    badge: Badge
    metric: str
    target: float
    unit: str = ""


@dataclass
class BadgeResult:
    badge: Badge
    unlocked: bool
    current: float
    target: float
    unit: str = ""

    @property
    def pct(self) -> float:
        if self.target <= 0:
            return 100.0
        return round(min(self.current / self.target * 100, 100.0), 1)


DEFAULT_RULES: tuple[BadgeRule, ...] = (
    BadgeRule(Badge("iron", "铁杆麦门人", "一年累计下单 100 次", "gold"), "order_count", 100, "单"),
    BadgeRule(Badge("regular", "月度常客", "一年有 200 天在麦门出现", "gold"), "active_days", 200, "天"),
    BadgeRule(Badge("saved", "优惠猎手", "靠券和满减省下 200 元", "gold"), "total_discount", 200, "元"),
    BadgeRule(Badge("thousand", "千元俱乐部", "年度消费突破 3000 元", "gold"), "total_spend", 3000, "元"),
    BadgeRule(Badge("bigmac10", "巨无霸十连", "一年吃掉 10 个巨无霸", "silver"), "item:巨无霸", 10, "个"),
    BadgeRule(Badge("nights", "夜宵猎人", "夜宵时段下单 15 次", "silver"), "daypart:夜宵", 15, "次"),
    BadgeRule(Badge("breakfast", "早餐俱乐部", "早餐时段下单 20 次", "silver"), "daypart:早餐", 20, "次"),
    BadgeRule(Badge("streak", "全勤之王", "连续 7 天打卡麦门", "silver"), "longest_streak", 7, "天"),
    BadgeRule(Badge("tour", "门店巡礼", "在 6 家不同门店下过单", "silver"), "store_variety", 6, "家"),
    BadgeRule(Badge("bigbite", "大胃王", "单笔订单包含 8 件餐品", "bronze"), "max_items", 8, "件"),
    BadgeRule(Badge("sweet", "甜党认证", "一年吃掉 20 份甜品", "bronze"), "cat:甜品", 20, "份"),
    BadgeRule(Badge("caffeine", "咖啡续命", "一年喝掉 20 杯咖啡", "bronze"), "cat:咖啡", 20, "杯"),
)


def _build_metrics(stats: Stats, orders: list[Order]) -> dict[str, float]:
    """把所有徽章规则需要的口径一次性算好。"""
    item_qty: Counter[str] = Counter()
    cat_qty: Counter[str] = Counter()
    daypart_count: Counter[str] = Counter()
    stores: set[str] = set()
    max_items = 0

    for order in orders:
        daypart_count[order.daypart] += 1
        stores.add(order.store)
        max_items = max(max_items, order.item_count)
        for item in order.items:
            item_qty[item.name] += item.qty
            cat_qty[item.category] += item.qty

    metrics: dict[str, float] = {
        "order_count": stats.order_count,
        "active_days": stats.active_days,
        "total_spend": stats.total_spend,
        "total_discount": stats.total_discount,
        "longest_streak": stats.longest_streak,
        "max_items": max_items,
        "store_variety": len(stores),
    }
    for name, qty in item_qty.items():
        metrics[f"item:{name}"] = qty
    for name, qty in cat_qty.items():
        metrics[f"cat:{name}"] = qty
    for name, count in daypart_count.items():
        metrics[f"daypart:{name}"] = count
    return metrics


def evaluate(stats: Stats, orders: list[Order], rules: tuple[BadgeRule, ...] = DEFAULT_RULES) -> list[BadgeResult]:
    """按解锁优先级排序（已解锁在前，同组内按完成度倒序）。"""
    metrics = _build_metrics(stats, orders)
    results: list[BadgeResult] = []
    for rule in rules:
        current = float(metrics.get(rule.metric, 0))
        results.append(
            BadgeResult(
                badge=rule.badge,
                unlocked=current >= rule.target,
                current=round(current, 1),
                target=rule.target,
                unit=rule.unit,
            )
        )
    tier_rank = {"gold": 0, "silver": 1, "bronze": 2}
    results.sort(key=lambda r: (not r.unlocked, tier_rank.get(r.badge.tier, 3), -r.pct))
    return results


def attach(stats: Stats, orders: list[Order]) -> list[BadgeResult]:
    """计算徽章并回写到 ``stats.badges``，返回同一份结果。"""
    results = evaluate(stats, orders)
    stats.badges = results
    return results
