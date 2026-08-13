"""Tambah kolom created_by (pembuat RPS) pada tabel rps

Revision ID: 0004_rps_created_by
Revises: 0003_so_pi_models
Create Date: 2026-08-13 14:00:00.000000

Menambah FK pembuat RPS. Karena hanya kaprodi/tim kurikulum yang bisa
membuat RPS, data lama di-backfill ke user ber-role kaprodi pertama.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_rps_created_by'
down_revision = '0003_so_pi_models'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.add_column('rps', sa.Column('created_by', sa.Integer(), nullable=True))

    # Backfill: semua RPS lama dibuat oleh kaprodi (ambil kaprodi pertama)
    kaprodi = conn.execute(
        sa.text("SELECT id FROM user WHERE role = 'kaprodi' ORDER BY id ASC LIMIT 1")
    ).fetchone()
    if kaprodi:
        conn.execute(
            sa.text("UPDATE rps SET created_by = :uid WHERE created_by IS NULL"),
            {'uid': kaprodi[0]},
        )

    op.create_foreign_key('fk_rps_created_by', 'rps', 'user', ['created_by'], ['id'])


def downgrade():
    op.drop_constraint('fk_rps_created_by', 'rps', type_='foreignkey')
    op.drop_column('rps', 'created_by')
