"""drop rubric from performance_indicator

Revision ID: 40e4689f66ca
Revises: 0190eab1d9e4
Create Date: 2026-11-16 14:44:59.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40e4689f66ca'
down_revision = '0190eab1d9e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('performance_indicator', schema=None) as batch_op:
        batch_op.drop_column('rubric')


def downgrade():
    with op.batch_alter_table('performance_indicator', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rubric', sa.JSON(), nullable=True))
