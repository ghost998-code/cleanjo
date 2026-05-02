"""Add report photos table

Revision ID: 005_add_report_photos
Revises: 004_align_mvp_contract
Create Date: 2026-05-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "005_add_report_photos"
down_revision: Union[str, None] = "004_align_mvp_contract"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "report_photos" not in table_names:
        op.create_table(
            "report_photos",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("image_url", sa.String(length=500), nullable=False),
            sa.Column("source_type", sa.String(length=20), nullable=False),
            sa.Column("latitude", sa.Numeric(precision=10, scale=8), nullable=False),
            sa.Column("longitude", sa.Numeric(precision=11, scale=8), nullable=False),
            sa.Column("gps_accuracy", sa.Float(), nullable=False),
            sa.Column("captured_at", sa.DateTime(), nullable=False),
            sa.Column("exif_latitude", sa.Numeric(precision=10, scale=8), nullable=True),
            sa.Column("exif_longitude", sa.Numeric(precision=11, scale=8), nullable=True),
            sa.Column("exif_accuracy", sa.Float(), nullable=True),
            sa.Column("exif_captured_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("source_type IN ('camera', 'gallery')", name="ck_report_photos_source_type"),
        )
    else:
        check_constraints = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("report_photos")
            if constraint.get("name")
        }
        if "ck_report_photos_source_type" not in check_constraints:
            op.create_check_constraint(
                "ck_report_photos_source_type",
                "report_photos",
                "source_type IN ('camera', 'gallery')",
            )

    indexes = {
        index["name"]
        for index in inspector.get_indexes("report_photos")
        if index.get("name")
    }
    if "idx_report_photos_report_id" not in indexes:
        op.create_index("idx_report_photos_report_id", "report_photos", ["report_id"], unique=False)
    if "idx_report_photos_created" not in indexes:
        op.create_index("idx_report_photos_created", "report_photos", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "report_photos" not in table_names:
        return

    check_constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("report_photos")
        if constraint.get("name")
    }
    if "ck_report_photos_source_type" in check_constraints:
        op.drop_constraint("ck_report_photos_source_type", "report_photos", type_="check")

    indexes = {
        index["name"]
        for index in inspector.get_indexes("report_photos")
        if index.get("name")
    }
    if "idx_report_photos_created" in indexes:
        op.drop_index("idx_report_photos_created", table_name="report_photos")
    if "idx_report_photos_report_id" in indexes:
        op.drop_index("idx_report_photos_report_id", table_name="report_photos")

    op.drop_table("report_photos")
