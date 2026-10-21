"""Add verified warranty detail columns to warranty_infos table."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "003_add_warranty_details"
down_revision: Union[str, None] = "002_database_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("warranty_infos") as batch:
        batch.add_column(sa.Column("parts_warranty_months", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("labor_warranty_months", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("warranty_type", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("battery_warranty_months", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("charger_warranty_months", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("service_type", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("warranty_source_url", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("verification_status", sa.String(length=100), nullable=True))

        batch.create_check_constraint(
            "ck_warranty_parts_months",
            "parts_warranty_months IS NULL OR parts_warranty_months >= 0"
        )
        batch.create_check_constraint(
            "ck_warranty_labor_months",
            "labor_warranty_months IS NULL OR labor_warranty_months >= 0"
        )
        batch.create_check_constraint(
            "ck_warranty_battery_months",
            "battery_warranty_months IS NULL OR battery_warranty_months >= 0"
        )
        batch.create_check_constraint(
            "ck_warranty_charger_months",
            "charger_warranty_months IS NULL OR charger_warranty_months >= 0"
        )


def downgrade() -> None:
    with op.batch_alter_table("warranty_infos") as batch:
        batch.drop_constraint("ck_warranty_charger_months", type_="check")
        batch.drop_constraint("ck_warranty_battery_months", type_="check")
        batch.drop_constraint("ck_warranty_labor_months", type_="check")
        batch.drop_constraint("ck_warranty_parts_months", type_="check")

        batch.drop_column("verification_status")
        batch.drop_column("warranty_source_url")
        batch.drop_column("service_type")
        batch.drop_column("charger_warranty_months")
        batch.drop_column("battery_warranty_months")
        batch.drop_column("warranty_type")
        batch.drop_column("labor_warranty_months")
        batch.drop_column("parts_warranty_months")
