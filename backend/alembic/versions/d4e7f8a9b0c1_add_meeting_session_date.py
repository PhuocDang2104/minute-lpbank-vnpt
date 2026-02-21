"""Add session_date column to meeting

Revision ID: d4e7f8a9b0c1
Revises: c1a2b3d4e5f6
Create Date: 2026-02-21 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e7f8a9b0c1"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector: sa.inspect, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.inspect, table_name: str) -> set[str]:
    return {index.get("name") for index in inspector.get_indexes(table_name) if index.get("name")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    meeting_columns = _column_names(inspector, "meeting")
    meeting_indexes = _index_names(inspector, "meeting")

    with op.batch_alter_table("meeting") as batch:
        if "session_date" not in meeting_columns:
            batch.add_column(sa.Column("session_date", sa.Date(), nullable=True))

    if "idx_meeting_session_date" not in meeting_indexes:
        op.create_index("idx_meeting_session_date", "meeting", ["session_date"], unique=False)

    op.execute(
        """
        UPDATE meeting
        SET session_date = start_time::date
        WHERE session_date IS NULL
          AND start_time IS NOT NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    meeting_columns = _column_names(inspector, "meeting")
    meeting_indexes = _index_names(inspector, "meeting")

    if "idx_meeting_session_date" in meeting_indexes:
        op.drop_index("idx_meeting_session_date", table_name="meeting")

    if "session_date" in meeting_columns:
        with op.batch_alter_table("meeting") as batch:
            batch.drop_column("session_date")

