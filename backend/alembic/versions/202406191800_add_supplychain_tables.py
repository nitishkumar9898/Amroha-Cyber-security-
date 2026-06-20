# backend/alembic/versions/202406191800_add_supplychain_tables.py

"""Add supply chain tables.

Revision ID: 202406191800
Revises: None
Create Date: 2026-06-19 22:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202406191800"
Down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create supply_chain_entities table
    op.create_table(
        "supply_chain_entities",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("version", sa.String, nullable=True),
        sa.Column("provenance_hash", sa.String, nullable=False, unique=True),
        sa.Column("metadata", sa.JSON, nullable=True),
    )
    # Create risk_events table
    op.create_table(
        "risk_events",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("supply_chain_entities.id"), nullable=False),
        sa.Column("severity", sa.Float, nullable=False),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now()),
    )
    # Create anomalies table
    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("supply_chain_entities.id"), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    # Create simulation_scenarios table
    op.create_table(
        "simulation_scenarios",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("generated_plan", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("simulation_scenarios")
    op.drop_table("anomalies")
    op.drop_table("risk_events")
    op.drop_table("supply_chain_entities")
