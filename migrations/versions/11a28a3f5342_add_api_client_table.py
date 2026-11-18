"""add api_client table

Revision ID: 11a28a3f5342
Revises: 40e4689f66ca
Create Date: 2026-11-18 23:32:09.956548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11a28a3f5342'
down_revision = '40e4689f66ca'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('api_client'):
        op.create_table(
            'api_client',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('key_prefix', sa.String(length=20), nullable=False),
            sa.Column('key_hash', sa.String(length=64), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('last_used_at', sa.DateTime(), nullable=True),
            sa.Column('last_used_ip', sa.String(length=45), nullable=True),
            sa.Column('request_count', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['created_by'], ['user.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('api_client', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_api_client_key_prefix'), ['key_prefix'], unique=True)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('api_client'):
        with op.batch_alter_table('api_client', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_api_client_key_prefix'))
        op.drop_table('api_client')
