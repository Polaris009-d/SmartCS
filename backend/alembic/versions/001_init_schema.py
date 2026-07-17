"""Initial schema — all core tables + pgvector extension

Revision ID: 001
Revises:
Create Date: 2026-07-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === pgvector 扩展 ===
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # === users ===
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="agent"),
        sa.Column("availability", sa.String(20), nullable=False, server_default="offline"),
        sa.Column("max_concurrent", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("pubsub_token", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === inboxes ===
    op.create_table(
        "inboxes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("channel_type", sa.String(50), nullable=False, index=True),
        sa.Column("channel_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("auto_assignment_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("assignment_algorithm", sa.String(50), nullable=False, server_default="round_robin"),
        sa.Column("working_hours_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("greeting_message", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === contacts ===
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True, index=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("reputation_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("custom_attributes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === contact_inboxes ===
    op.create_table(
        "contact_inboxes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("inbox_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("pubsub_token", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("contact_id", "inbox_id", name="uq_contact_inbox"),
    )

    # === conversations ===
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("display_id", sa.Integer(), nullable=False),
        sa.Column("inbox_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("contact_inbox_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assigned_agent_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open", index=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("is_ai_handling", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("waiting_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_reply_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("custom_attributes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("inbox_id", "display_id", name="uq_inbox_display"),
    )
    op.create_index("ix_conversations_status_waiting", "conversations", ["status", "waiting_since"])

    # === messages ===
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("message_type", sa.String(20), nullable=False, server_default="incoming"),
        sa.Column("content_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sender_type", sa.String(50), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True, index=True),
        sa.Column("content_attributes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_messages_conv_created", "messages", ["conversation_id", "created_at"])

    # === products ===
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("sku", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True, index=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("specs", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("size_chart", postgresql.JSONB(), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("image_urls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === orders ===
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("order_no", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("payment_status", sa.String(30), nullable=False, server_default="unpaid"),
        sa.Column("shipping_address", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("logistics_no", sa.String(200), nullable=True),
        sa.Column("logistics_status", sa.String(500), nullable=True),
        sa.Column("risk_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === knowledge_chunks ===
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("source_type", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === agent_operation_logs ===
    op.create_table(
        "agent_operation_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("input_params", postgresql.JSONB(), nullable=False),
        sa.Column("validation_result", postgresql.JSONB(), nullable=False),
        sa.Column("execution_result", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("agent_operation_logs")
    op.drop_table("knowledge_chunks")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("contact_inboxes")
    op.drop_table("contacts")
    op.drop_table("inboxes")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
