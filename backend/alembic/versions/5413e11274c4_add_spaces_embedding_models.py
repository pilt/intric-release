"""add spaces_embedding_models
Revision ID: 5413e11274c4
Revises: c8a82a470a8c
Create Date: 2024-07-31 07:46:17.622036
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision = '5413e11274c4'
down_revision = 'c8a82a470a8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'spaces_embedding_models',
        sa.Column('space_id', sa.UUID(), nullable=False),
        sa.Column('embedding_model_id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['embedding_model_id'], ['embedding_models.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('space_id', 'embedding_model_id'),
    )
    op.drop_constraint('spaces_embedding_model_id_fkey', 'spaces', type_='foreignkey')
    op.drop_column('spaces', 'embedding_model_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'spaces',
        sa.Column('embedding_model_id', sa.UUID(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        'spaces_embedding_model_id_fkey',
        'spaces',
        'embedding_models',
        ['embedding_model_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_table('spaces_embedding_models')
    # ### end Alembic commands ###