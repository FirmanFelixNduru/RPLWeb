"""Align persisted data types and enforce domain constraints."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "002_database_constraints"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table, column in (
            ("product_specs", "specifications"),
            ("review_sentiments", "pros"),
            ("review_sentiments", "cons"),
        ):
            op.alter_column(
                table,
                column,
                existing_type=sa.JSON(),
                type_=postgresql.JSONB(),
                postgresql_using=f"{column}::jsonb",
            )

    with op.batch_alter_table("brands") as batch:
        batch.create_check_constraint("ck_brand_name_nonempty", "length(trim(name)) > 0")

    with op.batch_alter_table("products") as batch:
        batch.alter_column("release_year", existing_type=sa.Integer(), nullable=False)
        for column in (
            "score_performance", "score_camera", "score_battery", "score_display",
            "score_build_quality", "score_value", "score_audio", "score_software",
        ):
            batch.alter_column(column, existing_type=sa.Integer(), nullable=False)
        batch.create_check_constraint("ck_product_name_nonempty", "length(trim(name)) > 0")
        batch.create_check_constraint(
            "ck_product_category_valid",
            "category IN ('smartphone', 'laptop', 'tablet', 'tws', 'smartwatch')",
        )

    with op.batch_alter_table("review_sentiments") as batch:
        batch.alter_column("total_reviews", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("pros", existing_type=sa.JSON(), nullable=False)
        batch.alter_column("cons", existing_type=sa.JSON(), nullable=False)
        batch.alter_column("summary", existing_type=sa.Text(), nullable=False)

    with op.batch_alter_table("warranty_infos") as batch:
        batch.alter_column("duration_months", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("coverage", existing_type=sa.Text(), nullable=False)
        batch.alter_column("claim_ease", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("official_service_centers", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("score", existing_type=sa.Float(), nullable=False)

    with op.batch_alter_table("tags") as batch:
        batch.create_check_constraint("ck_tag_name_nonempty", "length(trim(name)) > 0")

    with op.batch_alter_table("marketplaces") as batch:
        batch.create_check_constraint(
            "ck_marketplace_code_nonempty", "length(trim(code)) > 0"
        )

    with op.batch_alter_table("marketplace_links") as batch:
        batch.create_check_constraint(
            "ck_marketplace_link_http_url",
            "url LIKE 'http://%' OR url LIKE 'https://%'",
        )

    with op.batch_alter_table("marketplace_prices") as batch:
        batch.alter_column("available", existing_type=sa.Boolean(), nullable=False)
        batch.create_check_constraint(
            "ck_marketplace_price_source", "source IN ('scraped', 'fallback')"
        )
        batch.create_check_constraint(
            "ck_marketplace_price_http_url",
            "url LIKE 'http://%' OR url LIKE 'https://%'",
        )


def downgrade() -> None:
    with op.batch_alter_table("marketplace_prices") as batch:
        batch.drop_constraint("ck_marketplace_price_http_url", type_="check")
        batch.drop_constraint("ck_marketplace_price_source", type_="check")
        batch.alter_column("available", existing_type=sa.Boolean(), nullable=True)

    with op.batch_alter_table("marketplace_links") as batch:
        batch.drop_constraint("ck_marketplace_link_http_url", type_="check")

    with op.batch_alter_table("marketplaces") as batch:
        batch.drop_constraint("ck_marketplace_code_nonempty", type_="check")

    with op.batch_alter_table("tags") as batch:
        batch.drop_constraint("ck_tag_name_nonempty", type_="check")

    with op.batch_alter_table("warranty_infos") as batch:
        batch.alter_column("score", existing_type=sa.Float(), nullable=True)
        batch.alter_column("official_service_centers", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("claim_ease", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("coverage", existing_type=sa.Text(), nullable=True)
        batch.alter_column("duration_months", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("review_sentiments") as batch:
        batch.alter_column("summary", existing_type=sa.Text(), nullable=True)
        batch.alter_column("cons", existing_type=sa.JSON(), nullable=True)
        batch.alter_column("pros", existing_type=sa.JSON(), nullable=True)
        batch.alter_column("total_reviews", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("products") as batch:
        batch.drop_constraint("ck_product_category_valid", type_="check")
        batch.drop_constraint("ck_product_name_nonempty", type_="check")
        for column in (
            "score_performance", "score_camera", "score_battery", "score_display",
            "score_build_quality", "score_value", "score_audio", "score_software",
        ):
            batch.alter_column(column, existing_type=sa.Integer(), nullable=True)
        batch.alter_column("release_year", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("brands") as batch:
        batch.drop_constraint("ck_brand_name_nonempty", type_="check")

    if op.get_bind().dialect.name == "postgresql":
        for table, column in (
            ("product_specs", "specifications"),
            ("review_sentiments", "pros"),
            ("review_sentiments", "cons"),
        ):
            op.alter_column(
                table,
                column,
                existing_type=postgresql.JSONB(),
                type_=sa.JSON(),
                postgresql_using=f"{column}::json",
            )