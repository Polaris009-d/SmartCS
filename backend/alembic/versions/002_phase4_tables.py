"""Phase 4 tables — refund_records, sentiment_alerts, tickets

Revision ID: 002
Revises: 001
Create Date: 2026-07-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # refund_records
    op.create_table(
        "refund_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("processed_by", sa.String(100), nullable=True),
        sa.Column("approval_rule", sa.String(200), nullable=True),
        sa.Column("external_refund_id", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # sentiment_alerts
    op.create_table(
        "sentiment_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("sentiment_label", sa.String(20), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("alert_level", sa.String(20), server_default="warning"),
        sa.Column("is_escalated", sa.Boolean(), server_default="false"),
        sa.Column("escalation_ticket_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("handled_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # tickets
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("ticket_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tickets")
    op.drop_table("sentiment_alerts")
    op.drop_table("refund_records")
