"""add created_by to student_outcome

Revision ID: 28ad0c41eb43
Revises: 51d036102384
Create Date: 2026-11-08 15:40:01.992580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28ad0c41eb43'
down_revision = '51d036102384'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('student_outcome')]

    with op.batch_alter_table('student_outcome', schema=None) as batch_op:
        if 'created_by' not in cols:
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_student_outcome_created_by', 'user', ['created_by'], ['id'])


def downgrade():
    with op.batch_alter_table('student_outcome', schema=None) as batch_op:
        batch_op.drop_constraint('fk_student_outcome_created_by', type_='foreignkey')
        batch_op.drop_column('created_by')
