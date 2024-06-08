"""change in Comment table from uploaded_at to updated_at

Revision ID: 578b90e4fece
Revises: 9e16d1e8b2d9
Create Date: 2024-06-08 09:47:16.285193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '578b90e4fece'
down_revision: Union[str, None] = '9e16d1e8b2d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('comments', 'uploaded_at')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('uploaded_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.drop_column('comments', 'updated_at')
    # ### end Alembic commands ###