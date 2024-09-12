"""make username and password optional fields
Revision ID: ab047a3c6ea9
Revises: 7dff2ab73d31
Create Date: 2024-08-27 14:19:02.256717
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision = 'ab047a3c6ea9'
down_revision = '7dff2ab73d31'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'username', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('users', 'salt', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('users', 'password', existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('users', 'salt', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('users', 'username', existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###