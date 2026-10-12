"""统计引擎与数据模型的单元测试。"""

from __future__ import annotations

import unittest
from datetime import date, datetime

from mcd_year_in_review import mock_data
from mcd_year_in_review.models import Order, OrderItem, classify_daypart, mask_account
from mcd_year_in_review.stats import compute


class MaskAccountTest(unittest.TestCase):
    def test_short_id_preserved(self) -> None:
        self.assertEqual(mask_account("M123"), "M123")

    def test_long_id_masked(self) -> None:
        self.assertEqual(mask_account("42FBD022-35A7-7E0A-B728-FF1B0ED66000"), "42FBD022…6000")

    def test_empty_safe(self) -> None:
        self.assertEqual(mask_account(""), "")


def _order(ts: datetime, paid: float, kcal: float = 500.0, name: str = "巨无霸") -> Order:
    item = OrderItem(name=name, category="汉堡", qty=1, unit_price=paid, kcal_per_unit=kcal)
    return Order(
        order_id=f"T{ts:%Y%m%d%H%M}",
        ts=ts,
        channel="delivery",
        store="测试店",
        city="深圳",
        items=(item,),
        paid=paid,
        listed=paid,
    )


class DaypartTest(unittest.TestCase):
    def test_boundaries(self) -> None:
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 7, 30)), "早餐")
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 12, 0)), "午餐")
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 15, 0)), "下午茶")
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 19, 0)), "晚餐")
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 22, 30)), "夜宵")

    def test_late_night_crosses_midnight(self) -> None:
        # 凌晨 1 点应归入夜宵，而不是"其他"
        self.assertEqual(classify_daypart(datetime(2026, 3, 1, 1, 0)), "夜宵")


class OrderModelTest(unittest.TestCase):
    def test_discount_and_totals(self) -> None:
        item = OrderItem("薯条（大）", "小食", qty=2, unit_price=13.0, kcal_per_unit=460)
        order = Order("A1", datetime(2026, 5, 1, 12, 0), "dine_in", "店A", "深圳", (item,), paid=20.0, listed=26.0)
        self.assertEqual(order.item_count, 2)
        self.assertEqual(order.discount, 6.0)
        self.assertEqual(order.kcal, 920.0)

    def test_negative_discount_is_clamped(self) -> None:
        item = OrderItem("玉米杯", "小食", qty=1, unit_price=9.0)
        order = Order("A2", datetime(2026, 5, 1, 12, 0), "dine_in", "店A", "深圳", (item,), paid=10.0, listed=9.0)
        self.assertEqual(order.discount, 0.0)


class MockDataTest(unittest.TestCase):
    def test_deterministic(self) -> None:
        first = mock_data.generate_orders()
        second = mock_data.generate_orders()
        self.assertEqual(len(first), len(second))
        self.assertEqual(first[0].order_id, second[0].order_id)
        self.assertEqual(first[-1].paid, second[-1].paid)

    def test_generates_reasonable_volume(self) -> None:
        orders = mock_data.generate_orders()
        self.assertGreater(len(orders), 100, "一年的示例数据应该足够撑起一份年报")
        self.assertTrue(all(order.items for order in orders), "每一单都应有餐品")


class ComputeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.orders = mock_data.generate_orders()
        self.stats = compute(self.orders, mock_data.MOCK_USER)

    def test_totals_match_raw_orders(self) -> None:
        self.assertAlmostEqual(self.stats.total_spend, round(sum(o.paid for o in self.orders), 2), places=2)
        self.assertEqual(self.stats.order_count, len(self.orders))
        self.assertEqual(self.stats.item_count, sum(o.item_count for o in self.orders))

    def test_monthly_covers_only_real_range(self) -> None:
        self.assertEqual(len(self.stats.monthly), 10, "2026-01 ~ 2026-10，只应出现 10 个月")
        self.assertEqual(self.stats.monthly[0].label, "1月")
        self.assertEqual(self.stats.monthly[-1].label, "10月")
        self.assertAlmostEqual(
            sum(point.spend for point in self.stats.monthly), self.stats.total_spend, places=1
        )

    def test_monthly_spans_cross_year(self) -> None:
        orders = [
            _order(datetime(2025, 12, 5, 12, 0), 30.0),
            _order(datetime(2026, 8, 27, 12, 0), 20.0),
        ]
        stats = compute(orders, {"name": "T", "city": "深圳", "member_id": "X"})
        self.assertEqual(stats.year_label, "2025–2026")
        labels = [p.label for p in stats.monthly]
        self.assertEqual(labels[0], "25/12")
        self.assertEqual(labels[-1], "26/8")
        # 中间空月份不应出现
        self.assertNotIn("25/11", labels)
        self.assertNotIn("26/9", labels)

    def test_has_item_prices_detected(self) -> None:
        # mock 数据里每个单品都有 unit_price
        self.assertTrue(self.stats.has_item_prices)
        # 构造一个 unit_price 全为 0 的场景
        zero_item = OrderItem(name="中薯条", category="小食", qty=1, unit_price=0.0, kcal_per_unit=289)
        zero_order = Order(
            "Z1", datetime(2026, 5, 1, 12, 0), "dine_in", "店", "深圳", (zero_item,), paid=10.0, listed=10.0
        )
        stats = compute([zero_order], {"name": "T", "city": "深圳", "member_id": "X"})
        self.assertFalse(stats.has_item_prices)

    def test_category_percentage_sums_to_100(self) -> None:
        self.assertAlmostEqual(sum(c.pct for c in self.stats.categories), 100.0, delta=0.6)

    def test_dayparts_cover_all_orders(self) -> None:
        self.assertEqual(sum(d.count for d in self.stats.dayparts), self.stats.order_count)

    def test_fun_conversions_positive(self) -> None:
        self.assertGreater(self.stats.fun["bigmac"], 0)
        self.assertGreater(self.stats.fun["run_km"], 0)

    def test_streak_detects_consecutive_days(self) -> None:
        orders = [
            _order(datetime(2026, 4, 1, 12, 0), 30.0),
            _order(datetime(2026, 4, 2, 12, 0), 30.0),
            _order(datetime(2026, 4, 3, 12, 0), 30.0),
            _order(datetime(2026, 4, 9, 12, 0), 30.0),
        ]
        stats = compute(orders, {"name": "T", "city": "深圳", "member_id": "X"})
        self.assertEqual(stats.longest_streak, 3)
        self.assertEqual(stats.active_days, 4)
        self.assertEqual(stats.start, date(2026, 4, 1))

    def test_empty_orders_raises(self) -> None:
        with self.assertRaises(ValueError):
            compute([], {"name": "T", "city": "深圳", "member_id": "X"})


if __name__ == "__main__":
    unittest.main()
