"""add word source and danbooru fields

Revision ID: c7a91b3e5d24
Revises: ff35bdd86813
Create Date: 2026-11-25 09:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c7a91b3e5d24'
down_revision: Union[str, None] = 'ff35bdd86813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Independent words (e.g. Danbooru tags) do not belong to a statement/prompt.
    op.alter_column('prompt_words', 'prompt_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('prompt_words', 'statement_id', existing_type=sa.Integer(), nullable=True)

    op.add_column(
        'prompt_words',
        sa.Column('source', sa.String(length=20), nullable=False, server_default='statement'),
    )
    op.add_column('prompt_words', sa.Column('category', sa.Integer(), nullable=True))
    op.add_column('prompt_words', sa.Column('post_count', sa.BigInteger(), nullable=True))

    op.create_index('ix_prompt_words_word_en', 'prompt_words', ['word_en'])
    op.create_index('ix_prompt_words_prompt_id', 'prompt_words', ['prompt_id'])
    op.create_index('ix_prompt_words_statement_id', 'prompt_words', ['statement_id'])
    # One row per Danbooru tag; statement words may legitimately repeat.
    op.create_index(
        'uq_prompt_words_danbooru_word_en',
        'prompt_words',
        ['word_en'],
        unique=True,
        postgresql_where=sa.text("source = 'danbooru'"),
    )


def downgrade() -> None:
    op.execute("DELETE FROM prompt_words WHERE source = 'danbooru'")
    op.drop_index('uq_prompt_words_danbooru_word_en', table_name='prompt_words')
    op.drop_index('ix_prompt_words_statement_id', table_name='prompt_words')
    op.drop_index('ix_prompt_words_prompt_id', table_name='prompt_words')
    op.drop_index('ix_prompt_words_word_en', table_name='prompt_words')
    op.drop_column('prompt_words', 'post_count')
    op.drop_column('prompt_words', 'category')
    op.drop_column('prompt_words', 'source')
    op.alter_column('prompt_words', 'statement_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('prompt_words', 'prompt_id', existing_type=sa.Integer(), nullable=False)
