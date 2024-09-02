"""Auto-generate migration

Revision ID: ebab57671f85
Revises:
Create Date: 2024-09-02 12:26:40.820735

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ebab57671f85"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "episode",
        sa.Column("episode", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("total_frame", sa.Integer(), nullable=False),
        sa.Column("frame_rate", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("episode"),
    )
    op.create_table(
        "sentence",
        sa.Column("text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("episode", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("frame_start", sa.Integer(), nullable=False),
        sa.Column("frame_end", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("segment_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("sentence")
    op.drop_table("episode")
    # ### end Alembic commands ###
