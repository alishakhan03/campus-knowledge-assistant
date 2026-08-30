"""initial migration

Revision ID: db66bd3eebcd
Revises:
Create Date: 2026-08-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'db66bd3eebcd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables already exist in the database from the original migration run
    # in a different copy of this project - this file exists only so
    # Alembic's local history matches what's already stamped in MySQL.
    pass


def downgrade() -> None:
    pass
