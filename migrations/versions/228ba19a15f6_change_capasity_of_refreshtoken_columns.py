"""change capasity of RefreshToken columns

Revision ID: 228ba19a15f6
Revises: 387a2c47457f
Create Date: 2024-05-15 09:59:04.861800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '228ba19a15f6'
down_revision: Union[str, None] = '387a2c47457f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('refresh_tokens', 'refresh_token',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=350),
               existing_nullable=False)
    op.alter_column('refresh_tokens', 'session_id',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=150),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('refresh_tokens', 'session_id',
               existing_type=sa.String(length=150),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    op.alter_column('refresh_tokens', 'refresh_token',
               existing_type=sa.String(length=350),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    # ### end Alembic commands ###
