"""Initial schema — create all AquaMediAI tables.

Creates:
  - farmers
  - scenarios
  - agreements
  - allocation_records

Revision ID: 0001_initial
Revises: (none)
Create Date: 2026-09-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── farmers ───────────────────────────────────────────────────────────────
    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("farm_id", sa.String(length=32), nullable=False),
        sa.Column("farm_area_hectares", sa.Float(), nullable=False),
        sa.Column("crop_type", sa.String(length=64), nullable=False),
        sa.Column("soil_type", sa.String(length=64), nullable=False),
        sa.Column("growth_stage", sa.String(length=64), nullable=False),
        sa.Column("location_village", sa.String(length=128), nullable=True),
        sa.Column("canal_id", sa.String(length=32), nullable=False, server_default="CANAL_A"),
        sa.Column("preferred_irrigation_start", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("preferred_irrigation_end", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("flexibility_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farmers_id"), "farmers", ["id"], unique=False)
    op.create_index(op.f("ix_farmers_farm_id"), "farmers", ["farm_id"], unique=True)

    # ── scenarios ─────────────────────────────────────────────────────────────
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_type", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_available_water_m3", sa.Float(), nullable=False),
        sa.Column("canal_capacity_m3_per_hour", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("num_farmers", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("season", sa.String(length=32), nullable=False, server_default="kharif"),
        sa.Column("rainfall_mm", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("temperature_celsius", sa.Float(), nullable=False, server_default="28.0"),
        sa.Column("humidity_percent", sa.Float(), nullable=False, server_default="60.0"),
        sa.Column("is_synthetic", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenarios_id"), "scenarios", ["id"], unique=False)
    op.create_index(op.f("ix_scenarios_scenario_type"), "scenarios", ["scenario_type"], unique=False)

    # ── agreements ────────────────────────────────────────────────────────────
    op.create_table(
        "agreements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("total_water_available_m3", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_water_allocated_m3", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("num_conflicts_detected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("num_negotiation_rounds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_utility", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("nash_welfare", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("conflict_summary", sa.Text(), nullable=True),
        sa.Column("explanation_narrative", sa.Text(), nullable=True),
        sa.Column("is_synthetic", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("agreed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agreements_id"), "agreements", ["id"], unique=False)
    op.create_index(op.f("ix_agreements_scenario_id"), "agreements", ["scenario_id"], unique=False)
    op.create_index(op.f("ix_agreements_status"), "agreements", ["status"], unique=False)

    # ── allocation_records ────────────────────────────────────────────────────
    op.create_table(
        "allocation_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agreement_id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("predicted_demand_m3", sa.Float(), nullable=False),
        sa.Column("minimum_requirement_m3", sa.Float(), nullable=False),
        sa.Column("allocated_water_m3", sa.Float(), nullable=False),
        sa.Column("allocation_fraction", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("utility_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("negotiation_round", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "allocation_method",
            sa.String(length=64),
            nullable=False,
            server_default="milp_initial",
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agreement_id"], ["agreements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_allocation_records_id"), "allocation_records", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_allocation_records_agreement_id"),
        "allocation_records",
        ["agreement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_allocation_records_farmer_id"),
        "allocation_records",
        ["farmer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("allocation_records")
    op.drop_table("agreements")
    op.drop_table("scenarios")
    op.drop_table("farmers")
