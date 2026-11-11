"""add rubric to performance_indicator

Revision ID: 0190eab1d9e4
Revises: 707818f019f8
Create Date: 2026-11-11 10:17:37.804330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0190eab1d9e4'
down_revision = '707818f019f8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('performance_indicator', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rubric', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('performance_indicator', schema=None) as batch_op:
        batch_op.drop_column('rubric')
