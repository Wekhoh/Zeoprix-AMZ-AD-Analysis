"""add keyword + keyword_daily_records tables

Revision ID: 6cb038313b10
Revises: f501b86a7e39
Create Date: 2026-04-12 06:17:46.709315+00:00

Manually written (autogenerate missed new tables because create_all
had already created them in the dev database before alembic ran).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6cb038313b10"
down_revision: Union[str, None] = "f501b86a7e39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ad_group_id", sa.Integer(), nullable=False),
        sa.Column("keyword_text", sa.String(), nullable=False),
        sa.Column("match_type", sa.String(), nullable=False),
        sa.Column("bid", sa.Float(), nullable=True),
        sa.Column("state", sa.String(), nullable=False, server_default="enabled"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ad_group_id"], ["ad_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ad_group_id", "keyword_text", "match_type", name="uq_kw_group_text_match"
        ),
    )
    with op.batch_alter_table("keywords", schema=None) as batch_op:
        batch_op.create_index("ix_kw_text", ["keyword_text"], unique=False)
        batch_op.create_index("ix_kw_ad_group", ["ad_group_id"], unique=False)

    op.create_table(
        "keyword_daily_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Float(), nullable=False, server_default="0"),
        sa.Column("orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keyword_id", "date", name="uq_kw_daily"),
    )
    with op.batch_alter_table("keyword_daily_records", schema=None) as batch_op:
        batch_op.create_index("ix_kw_daily_date", ["date"], unique=False)
        batch_op.create_index("ix_kw_daily_kw", ["keyword_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("keyword_daily_records", schema=None) as batch_op:
        batch_op.drop_index("ix_kw_daily_kw")
        batch_op.drop_index("ix_kw_daily_date")
    op.drop_table("keyword_daily_records")

    with op.batch_alter_table("keywords", schema=None) as batch_op:
        batch_op.drop_index("ix_kw_ad_group")
        batch_op.drop_index("ix_kw_text")
    op.drop_table("keywords")
