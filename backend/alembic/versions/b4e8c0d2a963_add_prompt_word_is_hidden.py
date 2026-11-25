"""add prompt word is_hidden

Revision ID: b4e8c0d2a963
Revises: c7a91b3e5d24
Create Date: 2026-11-25 09:40:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b4e8c0d2a963'
down_revision: Union[str, None] = 'c7a91b3e5d24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'prompt_words',
        sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('prompt_words', 'is_hidden')
