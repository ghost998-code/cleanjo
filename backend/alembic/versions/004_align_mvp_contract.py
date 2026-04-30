"""Align MVP backend contract

Revision ID: 004_align_mvp_contract
Revises: 003_admin_prefs
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "004_align_mvp_contract"
down_revision: Union[str, None] = "003_admin_prefs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))

    op.execute("ALTER TABLE status_history RENAME TO report_status_history")

    op.execute("ALTER TYPE reportstatus RENAME TO reportstatus_old")
    op.execute(
        "CREATE TYPE reportstatus AS ENUM ('submitted', 'under_review', 'scheduled', 'cleaned', 'rejected')"
    )

    op.execute(
        """
        ALTER TABLE reports
        ALTER COLUMN status TYPE reportstatus
        USING (
            CASE status::text
                WHEN 'pending' THEN 'submitted'
                WHEN 'in_progress' THEN 'under_review'
                WHEN 'resolved' THEN 'cleaned'
                WHEN 'rejected' THEN 'rejected'
                ELSE 'submitted'
            END
        )::reportstatus
        """
    )
    op.execute(
        """
        ALTER TABLE report_status_history
        ALTER COLUMN old_status TYPE reportstatus
        USING (
            CASE old_status::text
                WHEN 'pending' THEN 'submitted'
                WHEN 'in_progress' THEN 'under_review'
                WHEN 'resolved' THEN 'cleaned'
                WHEN 'rejected' THEN 'rejected'
                ELSE NULL
            END
        )::reportstatus
        """
    )
    op.execute(
        """
        ALTER TABLE report_status_history
        ALTER COLUMN new_status TYPE reportstatus
        USING (
            CASE new_status::text
                WHEN 'pending' THEN 'submitted'
                WHEN 'in_progress' THEN 'under_review'
                WHEN 'resolved' THEN 'cleaned'
                WHEN 'rejected' THEN 'rejected'
                ELSE 'submitted'
            END
        )::reportstatus
        """
    )
    op.execute("DROP TYPE reportstatus_old")

    op.execute(
        "CREATE TYPE reportcategory AS ENUM ('household', 'construction', 'green', 'hazardous', 'electronic', 'bulky', 'mixed', 'other')"
    )
    op.execute(
        "CREATE TYPE terraintype AS ENUM ('street', 'sidewalk', 'open_lot', 'waterway', 'residential', 'industrial', 'other')"
    )
    op.execute(
        "CREATE TYPE reachabilitytype AS ENUM ('easy', 'moderate', 'hard', 'requires_special_equipment')"
    )
    op.execute(
        "CREATE TYPE densitytype AS ENUM ('sparse', 'moderate', 'dense', 'illegal_dump')"
    )
    op.execute(
        "CREATE TYPE amountestimate AS ENUM ('1_bag', '2_5_bags', '6_15_bags', 'truckload')"
    )

    op.add_column("reports", sa.Column("locality", sa.String(length=255), nullable=True))
    op.add_column(
        "reports",
        sa.Column(
            "category",
            postgresql.ENUM(
                "household",
                "construction",
                "green",
                "hazardous",
                "electronic",
                "bulky",
                "mixed",
                "other",
                name="reportcategory",
                create_type=False,
            ),
            nullable=False,
            server_default="other",
        ),
    )
    op.add_column("reports", sa.Column("video_url", sa.String(length=500), nullable=True))
    op.add_column("reports", sa.Column("gps_accuracy", sa.Float(), nullable=True))
    op.add_column(
        "reports",
        sa.Column("reported_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        "reports",
        sa.Column(
            "terrain",
            postgresql.ENUM(
                "street",
                "sidewalk",
                "open_lot",
                "waterway",
                "residential",
                "industrial",
                "other",
                name="terraintype",
                create_type=False,
            ),
            nullable=False,
            server_default="other",
        ),
    )
    op.add_column(
        "reports",
        sa.Column(
            "reachability",
            postgresql.ENUM(
                "easy",
                "moderate",
                "hard",
                "requires_special_equipment",
                name="reachabilitytype",
                create_type=False,
            ),
            nullable=False,
            server_default="moderate",
        ),
    )
    op.add_column(
        "reports",
        sa.Column(
            "density",
            postgresql.ENUM(
                "sparse",
                "moderate",
                "dense",
                "illegal_dump",
                name="densitytype",
                create_type=False,
            ),
            nullable=False,
            server_default="moderate",
        ),
    )
    op.add_column(
        "reports",
        sa.Column(
            "amount_estimate",
            postgresql.ENUM(
                "1_bag",
                "2_5_bags",
                "6_15_bags",
                "truckload",
                name="amountestimate",
                create_type=False,
            ),
            nullable=False,
            server_default="1_bag",
        ),
    )
    op.add_column("reports", sa.Column("admin_notes", sa.Text(), nullable=True))

    op.execute(
        "UPDATE reports SET category = CASE WHEN garbage_type IN ('construction', 'hazardous', 'electronic', 'mixed', 'other') THEN garbage_type::reportcategory ELSE 'other'::reportcategory END"
    )
    op.execute("UPDATE reports SET reported_at = created_at WHERE created_at IS NOT NULL")

    op.drop_column("reports", "garbage_type")
    op.alter_column("reports", "status", server_default="submitted")

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_helpful", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("feedback")
    op.add_column("reports", sa.Column("garbage_type", sa.String(length=100), nullable=True))
    op.drop_column("reports", "admin_notes")
    op.drop_column("reports", "amount_estimate")
    op.drop_column("reports", "density")
    op.drop_column("reports", "reachability")
    op.drop_column("reports", "terrain")
    op.drop_column("reports", "reported_at")
    op.drop_column("reports", "gps_accuracy")
    op.drop_column("reports", "video_url")
    op.drop_column("reports", "category")
    op.drop_column("reports", "locality")
    op.drop_column("users", "last_login")
    op.execute("DROP TYPE IF EXISTS amountestimate")
    op.execute("DROP TYPE IF EXISTS densitytype")
    op.execute("DROP TYPE IF EXISTS reachabilitytype")
    op.execute("DROP TYPE IF EXISTS terraintype")
    op.execute("DROP TYPE IF EXISTS reportcategory")
    op.execute("ALTER TABLE report_status_history RENAME TO status_history")
