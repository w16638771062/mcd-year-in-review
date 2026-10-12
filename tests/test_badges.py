"""徽章规则引擎与 MCP 解析器的单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime

from mcd_year_in_review import badges, mock_data
from mcd_year_in_review.models import Order, OrderItem
from mcd_year_in_review.source import parse_order
from mcd_year_in_review.stats import compute


class BadgeTest(unittest.TestCase):
    def test_rules_are_data_and_extensible(self) -> None:
        orders = mock_data.generate_orders()
        stats = compute(orders, mock_data.MOCK_USER)

        custom = badges.BadgeRule(badges.Badge("smoke", "测试徽章", "下单 1 次", "bronze"), "order_count", 1)
        results = badges.evaluate(stats, orders, rules=(custom,))
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].unlocked)
        self.assertEqual(results[0].pct, 100.0)

    def test_attach_sorts_unlocked_first(self) -> None:
        orders = mock_data.generate_orders()
        stats = compute(orders, mock_data.MOCK_USER)
        results = badges.attach(stats, orders)
        self.assertIs(results, stats.badges)
        unlocked = [r.unlocked for r in results]
        # 已解锁的应排在未解锁之前，不允许出现 True 在 False 之后
        self.assertEqual(unlocked, sorted(unlocked, reverse=True))

    def test_progress_is_capped(self) -> None:
        orders = mock_data.generate_orders()
        stats = compute(orders, mock_data.MOCK_USER)
        for result in badges.attach(stats, orders):
            if result.unlocked:
                self.assertEqual(result.pct, 100.0)

    def test_bigbite_unlocks_on_big_order(self) -> None:
        items = tuple(OrderItem(f"餐品{i}", "小食", 1, 10.0, 100) for i in range(9))
        order = Order("B1", datetime(2026, 6, 1, 12, 0), "dine_in", "店", "深圳", items, 90.0, 90.0)
        stats = compute([order], {"name": "T", "city": "深圳", "member_id": "X"})
        results = {r.badge.key: r for r in badges.attach(stats, [order])}
        self.assertTrue(results["bigbite"].unlocked)
        self.assertFalse(results["iron"].unlocked)


class ParseOrderTest(unittest.TestCase):
    def test_parses_common_field_names(self) -> None:
        raw = {
            "orderId": "MC20260501001",
            "orderTime": "2026-05-01 12:30:00",
            "storeName": "科技园店",
            "orderType": "外送",
            "payAmount": 42.5,
            "discountAmount": 7.5,
            "items": [
                {"productName": "麦辣鸡腿堡", "quantity": 2, "price": 23.0, "categoryName": "汉堡"},
                {"name": "薯条（中）", "qty": 1, "unitPrice": 11.0, "category": "小食"},
            ],
        }
        order = parse_order(raw, city="深圳")
        self.assertIsNotNone(order)
        assert order is not None
        self.assertEqual(order.order_id, "MC20260501001")
        self.assertEqual(order.channel, "delivery")
        self.assertEqual(order.item_count, 3)
        self.assertEqual(order.store, "科技园店")
        self.assertAlmostEqual(order.listed, 50.0, places=2)

    def test_returns_none_when_no_items(self) -> None:
        self.assertIsNone(parse_order({"orderId": "X", "orderTime": "2026-05-01 12:30:00", "items": []}))

    def test_returns_none_when_time_unparseable(self) -> None:
        raw = {"orderId": "X", "orderTime": "不是时间", "items": [{"name": "x", "price": 1}]}
        self.assertIsNone(parse_order(raw))

    def test_dine_in_channel_default(self) -> None:
        raw = {
            "orderId": "X",
            "orderTime": "2026-05-01 12:30:00",
            "orderType": "堂食",
            "items": [{"name": "巨无霸", "quantity": 1, "price": 25}],
        }
        order = parse_order(raw)
        self.assertIsNotNone(order)
        assert order is not None
        self.assertEqual(order.channel, "dine_in")


if __name__ == "__main__":
    unittest.main()
