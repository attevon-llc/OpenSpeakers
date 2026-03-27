"""Add cancellation, batch, and voice metadata columns.

Revision ID: 002_cancel_batch_voice
Revises: 001_initial_schema
Create Date: 2026-03-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_cancel_batch_voice"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add 'cancelled' to the jobstatus PostgreSQL enum
    op.execute("ALTER TYPE jobstatus ADD VALUE IF NOT EXISTS 'cancelled'")

    # tts_jobs: add celery_task_id and batch_id columns
    op.add_column("tts_jobs", sa.Column("celery_task_id", sa.String(256), nullable=True))
    op.add_column("tts_jobs", sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_tts_jobs_batch_id", "tts_jobs", ["batch_id"])

    # voice_profiles: add description and tags columns
    op.add_column("voice_profiles", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "voice_profiles",
        sa.Column(
            "tags",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("voice_profiles", "tags")
    op.drop_column("voice_profiles", "description")
    op.drop_index("ix_tts_jobs_batch_id", table_name="tts_jobs")
    op.drop_column("tts_jobs", "batch_id")
    op.drop_column("tts_jobs", "celery_task_id")
    # Note: PostgreSQL does not support removing enum values without recreating the type
