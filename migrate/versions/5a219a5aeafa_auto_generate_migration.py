"""Auto-generate migration

Revision ID: 5a219a5aeafa
Revises: d90997b91944
Create Date: 2024-09-02 12:50:58.140338

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "5a219a5aeafa"
down_revision: str | None = "d90997b91944"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
