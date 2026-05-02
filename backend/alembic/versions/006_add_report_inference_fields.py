"""Add report inference fields

Revision ID: 006_add_report_inference_fields
Revises: 005_add_report_photos
Create Date: 2026-05-01 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_add_report_inference_fields"
down_revision: Union[str, None] = "005_add_report_photos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    report_columns = {
        "inference_summary_category": sa.String(length=50),
        "inference_summary_confidence": sa.Float(),
        "inference_summary_strategy": sa.String(length=100),
        "inference_model_version": sa.String(length=100),
    }
    for column_name, column_type in report_columns.items():
        if not _has_column(inspector, "reports", column_name):
            op.add_column("reports", sa.Column(column_name, column_type, nullable=True))

    photo_columns = [
        sa.Column("predicted_category", sa.String(length=50), nullable=False, server_default="other"),
        sa.Column("prediction_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("predicted_severity", sa.String(length=50), nullable=True),
        sa.Column("severity_confidence", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False, server_default="unknown"),
        sa.Column("model_version", sa.String(length=100), nullable=False, server_default="unknown"),
        sa.Column("inference_ran_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("inference_source", sa.String(length=20), nullable=False, server_default="mobile"),
        sa.Column("top_predictions", sa.JSON(), nullable=True),
    ]
    for column in photo_columns:
        if not _has_column(inspector, "report_photos", column.name):
            op.add_column("report_photos", column)

    op.alter_column("report_photos", "predicted_category", server_default=None)
    op.alter_column("report_photos", "prediction_confidence", server_default=None)
    op.alter_column("report_photos", "model_name", server_default=None)
    op.alter_column("report_photos", "model_version", server_default=None)
    op.alter_column("report_photos", "inference_ran_at", server_default=None)
    op.alter_column("report_photos", "inference_source", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column_name in [
        "top_predictions",
        "inference_source",
        "inference_ran_at",
        "model_version",
        "model_name",
        "severity_confidence",
        "predicted_severity",
        "prediction_confidence",
        "predicted_category",
    ]:
        if _has_column(inspector, "report_photos", column_name):
            op.drop_column("report_photos", column_name)

    for column_name in [
        "inference_model_version",
        "inference_summary_strategy",
        "inference_summary_confidence",
        "inference_summary_category",
    ]:
        if _has_column(inspector, "reports", column_name):
            op.drop_column("reports", column_name)
