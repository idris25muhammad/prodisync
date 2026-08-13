"""Hapus kolom sks dari tabel rps

Revision ID: 0005_drop_rps_sks
Revises: 0004_rps_created_by
Create Date: 2026-08-13 15:00:00.000000

SKS tidak lagi disimpan di RPS untuk menghindari ambiguitas; nilai SKS
diambil dari tabel mata_kuliah (juga saat print/PDF). Sebelum menghapus
kolom rps.sks, nilai SKS lama di-backfill ke mata_kuliah.sks (jika masih
kosong) agar data SKS tidak hilang.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_drop_rps_sks'
down_revision = '0004_rps_created_by'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Backfill: salin SKS dari rps ke mata_kuliah yang belum punya SKS
    rows = conn.execute(
        sa.text("""
            SELECT r.matakuliah_id, r.sks
            FROM rps r
            JOIN mata_kuliah m ON m.id = r.matakuliah_id
            WHERE r.sks IS NOT NULL AND r.sks > 0
              AND (m.sks IS NULL OR m.sks = 0)
        """)
    ).fetchall()
    for mk_id, sks in rows:
        conn.execute(
            sa.text("UPDATE mata_kuliah SET sks = :sks WHERE id = :id"),
            {'sks': sks, 'id': mk_id},
        )

    op.drop_column('rps', 'sks')


def downgrade():
    op.add_column('rps', sa.Column('sks', sa.Integer(), nullable=False, server_default='3'))
