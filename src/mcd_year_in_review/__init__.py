"""麦门年度账单 · mcd-year-in-review

基于麦当劳 MCP 的年度消费 / 口味 / 作息画像生成器。
零第三方依赖，评审 clone 下来即可运行。
"""

from __future__ import annotations

from .badges import Badge, BadgeResult, BadgeRule, attach, evaluate
from .models import Order, OrderItem, classify_daypart
from .report import build_html, write_html
from .stats import Stats, compute

__version__ = "1.0.0"
__all__ = [
    "Order",
    "OrderItem",
    "Stats",
    "Badge",
    "BadgeResult",
    "BadgeRule",
    "attach",
    "build_html",
    "classify_daypart",
    "compute",
    "evaluate",
    "write_html",
    "__version__",
]
