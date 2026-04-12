"""initial baseline — marks schema as of 2026-04-11

Revision ID: 0001_initial_baseline
Revises:
Create Date: 2026-04-11

Existing databases should be stamped at this revision without running
the migration (all tables already exist via Base.metadata.create_all):

    alembic stamp 0001_initial_baseline

New databases can also use create_all + stamp, or alembic upgrade head
once future migrations (B2, B3, etc.) add incremental schema changes.
"""

revision = "0001_initial_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: current schema was created via Base.metadata.create_all
    # in backend/database.py. This revision exists solely as a baseline
    # anchor for future autogenerate migrations.
    pass


def downgrade() -> None:
    # No-op: dropping all tables is too destructive for a baseline.
    pass
