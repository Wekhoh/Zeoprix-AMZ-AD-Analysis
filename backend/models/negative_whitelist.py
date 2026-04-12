"""Never-Negative 白名单 — 运营标记为"绝不否定"的搜索词。

即使这些搜索词出现在 Money Pits 桶（高点击零订单），系统也不会建议
将其加入否定关键词列表。常见用途：

- 品牌词（自家品牌名称，否定后会丢失品牌流量）
- 长期转化词（季节性波动导致短期数据差，但历史上是高价值词）
- 竞品词（运营故意投放竞品词抢流量，接受高 ACOS）
"""

from sqlalchemy import Column, Index, Integer, String

from backend.models.base import Base, TimestampMixin


class NegativeWhitelist(Base, TimestampMixin):
    __tablename__ = "negative_whitelist"
    __table_args__ = (Index("ix_neg_wl_term", "search_term"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_term = Column(String, nullable=False, unique=True)
    reason = Column(String)  # 运营备注：为什么保护这个词
