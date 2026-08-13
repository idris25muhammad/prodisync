"""Hapus kolom sks dari tabel rps

Revision ID: 0005_drop_rps_sks
Revises: 0004_rps_created_by
Create Date: 2026-08-13 15:00:00.000000

SKS tidak lagi disimpan di RPS untuk menghindari ambiguitas; nilai SKS
diambil dari tabel mata_kuliah (juga saat print/PDF).
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0005_drop_rps_sks'
down_revision = '0004_rps_created_by'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('rps', 'sks')


def downgrade():
    import sqlalchemy as sa
    op.add_column('rps', sa.Column('sks', sa.Integer(), nullable=False, server_default='3'))
