"""Initial Vector schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_offer", sa.Text(), nullable=False),
        sa.Column("average_deal_size", sa.Integer(), nullable=True),
        sa.Column("sales_type", sa.String(length=32), nullable=False),
        sa.Column("usual_customers", sa.Text(), nullable=True),
        sa.Column("excluded_customers", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "searches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("okved", sa.String(length=32), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("revenue_min", sa.Integer(), nullable=True),
        sa.Column("revenue_max", sa.Integer(), nullable=True),
        sa.Column("employees_min", sa.Integer(), nullable=True),
        sa.Column("employees_max", sa.Integer(), nullable=True),
        sa.Column("company_age_min", sa.Integer(), nullable=True),
        sa.Column("active_only", sa.Boolean(), nullable=False),
        sa.Column("business_type", sa.String(length=32), nullable=False),
        sa.Column("website_requirement", sa.String(length=32), nullable=False),
        sa.Column("vacancies_requirement", sa.String(length=32), nullable=False),
        sa.Column("vacancy_categories", sa.JSON(), nullable=False),
        sa.Column("sales_department_requirement", sa.String(length=32), nullable=False),
        sa.Column("check_website", sa.Boolean(), nullable=False),
        sa.Column("exclude_ip", sa.Boolean(), nullable=False),
        sa.Column("exclude_liquidated", sa.Boolean(), nullable=False),
        sa.Column("exclude_no_revenue", sa.Boolean(), nullable=False),
        sa.Column("exclude_microbusiness", sa.Boolean(), nullable=False),
        sa.Column("exclude_government", sa.Boolean(), nullable=False),
        sa.Column("exclude_marketplace_sellers", sa.Boolean(), nullable=False),
        sa.Column("requested_companies_count", sa.Integer(), nullable=False),
        sa.Column("data_completeness", sa.String(length=64), nullable=False),
        sa.Column("export_format", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_searches_project_id"), "searches", ["project_id"], unique=False)
    op.create_index(op.f("ix_searches_status"), "searches", ["status"], unique=False)

    op.create_table(
        "company_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("search_id", sa.String(length=36), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("inn", sa.String(length=10), nullable=False),
        sa.Column("ogrn", sa.String(length=13), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("okved_main", sa.String(length=32), nullable=True),
        sa.Column("okved_description", sa.String(length=255), nullable=True),
        sa.Column("revenue", sa.Integer(), nullable=True),
        sa.Column("employees_count", sa.Integer(), nullable=True),
        sa.Column("company_age", sa.Integer(), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("has_website", sa.Boolean(), nullable=False),
        sa.Column("vacancies_total", sa.Integer(), nullable=False),
        sa.Column("sales_vacancies", sa.Integer(), nullable=False),
        sa.Column("marketing_vacancies", sa.Integer(), nullable=False),
        sa.Column("business_type", sa.String(length=32), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_company_results_company_name"), "company_results", ["company_name"], unique=False)
    op.create_index(op.f("ix_company_results_inn"), "company_results", ["inn"], unique=False)
    op.create_index(op.f("ix_company_results_search_id"), "company_results", ["search_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_company_results_search_id"), table_name="company_results")
    op.drop_index(op.f("ix_company_results_inn"), table_name="company_results")
    op.drop_index(op.f("ix_company_results_company_name"), table_name="company_results")
    op.drop_table("company_results")
    op.drop_index(op.f("ix_searches_status"), table_name="searches")
    op.drop_index(op.f("ix_searches_project_id"), table_name="searches")
    op.drop_table("searches")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
