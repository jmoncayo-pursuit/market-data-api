"""Initial database migration.

Revision ID: 05c2c5f44812
Revises:
Create Date: 2024-03-19 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "05c2c5f44812"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Create market_data table
    op.create_table(
        "market_data",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_market_data_symbol"),
        "market_data",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_data_timestamp"),
        "market_data",
        ["timestamp"],
        unique=False,
    )

    # Create raw_market_data table
    op.create_table(
        "raw_market_data",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False),
    )
    op.create_index(
        op.f("ix_raw_market_data_symbol"),
        "raw_market_data",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_raw_market_data_timestamp"),
        "raw_market_data",
        ["timestamp"],
        unique=False,
    )

    # Create processed_prices table
    op.create_table(
        "processed_prices",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("raw_data_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["raw_data_id"],
            ["raw_market_data.id"],
        ),
    )
    op.create_index(
        op.f("ix_processed_prices_symbol"),
        "processed_prices",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_processed_prices_timestamp"),
        "processed_prices",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(
        op.f("ix_processed_prices_timestamp"),
        table_name="processed_prices",
    )
    op.drop_index(
        op.f("ix_processed_prices_symbol"),
        table_name="processed_prices",
    )
    op.drop_table("processed_prices")
    op.drop_index(
        op.f("ix_raw_market_data_timestamp"),
        table_name="raw_market_data",
    )
    op.drop_index(
        op.f("ix_raw_market_data_symbol"),
        table_name="raw_market_data",
    )
    op.drop_table("raw_market_data")
    op.drop_index(
        op.f("ix_market_data_timestamp"),
        table_name="market_data",
    )
    op.drop_index(
        op.f("ix_market_data_symbol"),
        table_name="market_data",
    )
    op.drop_table("market_data")
