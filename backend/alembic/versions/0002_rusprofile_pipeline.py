"""Add Rusprofile pipeline storage.

Revision ID: 0002_rusprofile_pipeline
Revises: 0001_initial
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_rusprofile_pipeline"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("searches", sa.Column("data_source", sa.String(length=32), nullable=False, server_default="mock"))
    op.add_column("searches", sa.Column("visible_browser", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("searches", sa.Column("human_mode", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        "raw_company_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("search_id", sa.String(length=36), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("raw_company_name", sa.String(length=512), nullable=True),
        sa.Column("raw_inn", sa.String(length=16), nullable=True),
        sa.Column("raw_ogrn", sa.String(length=20), nullable=True),
        sa.Column("raw_summary_text", sa.Text(), nullable=True),
        sa.Column("raw_page_text", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_raw_company_snapshots_raw_inn"), "raw_company_snapshots", ["raw_inn"], unique=False)
    op.create_index(op.f("ix_raw_company_snapshots_search_id"), "raw_company_snapshots", ["search_id"], unique=False)

    op.add_column("company_results", sa.Column("full_company_name", sa.String(length=512), nullable=True))
    op.add_column("company_results", sa.Column("kpp", sa.String(length=16), nullable=True))
    op.add_column("company_results", sa.Column("status", sa.String(length=32), nullable=True))
    op.add_column("company_results", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("company_results", sa.Column("revenue_raw", sa.String(length=128), nullable=True))
    op.add_column("company_results", sa.Column("registration_date", sa.String(length=10), nullable=True))
    op.add_column("company_results", sa.Column("phone", sa.String(length=64), nullable=True))
    op.add_column("company_results", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("company_results", sa.Column("summary_text", sa.Text(), nullable=True))
    op.add_column("company_results", sa.Column("raw_snapshot_id", sa.String(length=36), nullable=True))
    op.add_column("company_results", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.alter_column("company_results", "inn", existing_type=sa.String(length=10), type_=sa.String(length=16), nullable=True)
    op.alter_column("company_results", "ogrn", existing_type=sa.String(length=13), type_=sa.String(length=20), nullable=True)
    op.alter_column("company_results", "source_url", existing_type=sa.String(length=255), type_=sa.String(length=512), nullable=True)
    op.create_foreign_key(
        "fk_company_results_raw_snapshot_id",
        "company_results",
        "raw_company_snapshots",
        ["raw_snapshot_id"],
        ["id"],
    )

    op.alter_column("searches", "data_source", server_default=None)
    op.alter_column("searches", "visible_browser", server_default=None)
    op.alter_column("searches", "human_mode", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_company_results_raw_snapshot_id", "company_results", type_="foreignkey")
    op.alter_column("company_results", "source_url", existing_type=sa.String(length=512), type_=sa.String(length=255), nullable=True)
    op.alter_column("company_results", "ogrn", existing_type=sa.String(length=20), type_=sa.String(length=13), nullable=False)
    op.alter_column("company_results", "inn", existing_type=sa.String(length=16), type_=sa.String(length=10), nullable=False)
    for column_name in (
        "updated_at",
        "raw_snapshot_id",
        "summary_text",
        "email",
        "phone",
        "registration_date",
        "revenue_raw",
        "address",
        "status",
        "kpp",
        "full_company_name",
    ):
        op.drop_column("company_results", column_name)

    op.drop_index(op.f("ix_raw_company_snapshots_search_id"), table_name="raw_company_snapshots")
    op.drop_index(op.f("ix_raw_company_snapshots_raw_inn"), table_name="raw_company_snapshots")
    op.drop_table("raw_company_snapshots")

    op.drop_column("searches", "human_mode")
    op.drop_column("searches", "visible_browser")
    op.drop_column("searches", "data_source")
