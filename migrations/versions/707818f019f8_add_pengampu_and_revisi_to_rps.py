"""add pengampu and revisi to rps

Revision ID: 707818f019f8
Revises: 28ad0c41eb43
Create Date: 2026-11-09 15:25:59.116848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '707818f019f8'
down_revision = '28ad0c41eb43'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('rps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pengampu', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('revisi', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('rps', schema=None) as batch_op:
        batch_op.drop_column('revisi')
        batch_op.drop_column('pengampu')
