"""Add LLM ICP scoring fields.

Revision ID: 0003_llm_icp_scoring
Revises: 0002_rusprofile_pipeline
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_llm_icp_scoring"
down_revision = "0002_rusprofile_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("searches", sa.Column("llm_scoring_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("searches", sa.Column("llm_scoring_threshold", sa.Integer(), nullable=True))

    op.add_column("company_results", sa.Column("icp_score", sa.Integer(), nullable=True))
    op.add_column("company_results", sa.Column("icp_is_match", sa.Boolean(), nullable=True))
    op.add_column("company_results", sa.Column("icp_confidence", sa.String(length=16), nullable=True))
    op.add_column("company_results", sa.Column("icp_fit_reason", sa.Text(), nullable=True))
    op.add_column("company_results", sa.Column("icp_mismatch_reason", sa.Text(), nullable=True))
    op.add_column("company_results", sa.Column("icp_matched_criteria", sa.JSON(), nullable=True))
    op.add_column("company_results", sa.Column("icp_failed_criteria", sa.JSON(), nullable=True))
    op.add_column("company_results", sa.Column("icp_recommended_action", sa.String(length=32), nullable=True))
    op.add_column("company_results", sa.Column("llm_model", sa.String(length=128), nullable=True))
    op.add_column("company_results", sa.Column("llm_scored_at", sa.DateTime(), nullable=True))

    op.alter_column("searches", "llm_scoring_enabled", server_default=None)


def downgrade() -> None:
    for column_name in (
        "llm_scored_at",
        "llm_model",
        "icp_recommended_action",
        "icp_failed_criteria",
        "icp_matched_criteria",
        "icp_mismatch_reason",
        "icp_fit_reason",
        "icp_confidence",
        "icp_is_match",
        "icp_score",
    ):
        op.drop_column("company_results", column_name)

    op.drop_column("searches", "llm_scoring_threshold")
    op.drop_column("searches", "llm_scoring_enabled")
