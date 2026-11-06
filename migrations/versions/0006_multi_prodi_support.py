"""Multi-prodi support dengan default ke Prodi 1 (Rekayasa Keamanan Siber)

Revision ID: 0006_multi_prodi_support
Revises: 0005_drop_rps_sks
Create Date: 2026-10-28 05:45:00.000000

Menerapkan multi-prodi:
1. Membuat tabel master `prodi`.
2. Menambahkan baris default id=1: 'RKS' - 'Rekayasa Keamanan Siber'.
3. Menambahkan kolom `prodi_id` ke user, mata_kuliah, student_outcome, rps,
   agenda, pengumuman, arsip_dokumen, dan panduan.
4. Melakukan backfill semua data lama ke prodi_id = 1.
5. Memperbarui constraint unique pada mata_kuliah (prodi_id, kode, kurikulum)
   dan student_outcome (prodi_id, so_code).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_multi_prodi_support'
down_revision = '0005_drop_rps_sks'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Buat tabel prodi
    op.create_table(
        'prodi',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('kode', sa.String(length=20), nullable=False),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('jenjang', sa.String(length=10), nullable=False, server_default='D4'),
        sa.Column('kaprodi_id', sa.Integer(), nullable=True),
        sa.Column('is_aktif', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kode', name='uq_prodi_kode'),
    )

    # 2. Seed baris default prodi 1 (RKS)
    conn.execute(sa.text("""
        INSERT INTO prodi (id, kode, nama, jenjang, kaprodi_id, is_aktif)
        VALUES (1, 'RKS', 'Rekayasa Keamanan Siber', 'D4', 1, 1)
        ON DUPLICATE KEY UPDATE nama = VALUES(nama)
    """))

    # Relasi kaprodi_id di prodi ke user.id
    op.create_foreign_key('fk_prodi_kaprodi_id_user', 'prodi', 'user', ['kaprodi_id'], ['id'])

    # 3. User: tambah prodi_id
    op.add_column('user', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE user SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.create_foreign_key('fk_user_prodi_id', 'user', 'prodi', ['prodi_id'], ['id'])

    # 4. MataKuliah: tambah prodi_id & sesuaikan constraint
    op.add_column('mata_kuliah', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE mata_kuliah SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.drop_constraint('uq_matakuliah_kode_kurikulum', 'mata_kuliah', type_='unique')
    op.alter_column('mata_kuliah', 'prodi_id', existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint('uq_matakuliah_prodi_kode_kurikulum', 'mata_kuliah', ['prodi_id', 'kode', 'kurikulum'])
    op.create_foreign_key('fk_matakuliah_prodi_id', 'mata_kuliah', 'prodi', ['prodi_id'], ['id'])

    # 5. StudentOutcome: tambah prodi_id & ubah constraint unik
    op.add_column('student_outcome', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE student_outcome SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.drop_index('so_code', table_name='student_outcome')
    op.alter_column('student_outcome', 'prodi_id', existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint('uq_prodi_so_code', 'student_outcome', ['prodi_id', 'so_code'])
    op.create_foreign_key('fk_student_outcome_prodi_id', 'student_outcome', 'prodi', ['prodi_id'], ['id'])

    # 6. RPS: tambah prodi_id
    op.add_column('rps', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE rps SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.alter_column('rps', 'prodi_id', existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key('fk_rps_prodi_id', 'rps', 'prodi', ['prodi_id'], ['id'])

    # 7. Agenda: tambah prodi_id
    op.add_column('agenda', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE agenda SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.create_foreign_key('fk_agenda_prodi_id', 'agenda', 'prodi', ['prodi_id'], ['id'])

    # 8. Pengumuman: tambah prodi_id
    op.add_column('pengumuman', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE pengumuman SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.create_foreign_key('fk_pengumuman_prodi_id', 'pengumuman', 'prodi', ['prodi_id'], ['id'])

    # 9. ArsipDokumen: tambah prodi_id
    op.add_column('arsip_dokumen', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE arsip_dokumen SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.create_foreign_key('fk_arsip_dokumen_prodi_id', 'arsip_dokumen', 'prodi', ['prodi_id'], ['id'])

    # 10. Panduan: tambah prodi_id
    op.add_column('panduan', sa.Column('prodi_id', sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE panduan SET prodi_id = 1 WHERE prodi_id IS NULL"))
    op.create_foreign_key('fk_panduan_prodi_id', 'panduan', 'prodi', ['prodi_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_panduan_prodi_id', 'panduan', type_='foreignkey')
    op.drop_column('panduan', 'prodi_id')

    op.drop_constraint('fk_arsip_dokumen_prodi_id', 'arsip_dokumen', type_='foreignkey')
    op.drop_column('arsip_dokumen', 'prodi_id')

    op.drop_constraint('fk_pengumuman_prodi_id', 'pengumuman', type_='foreignkey')
    op.drop_column('pengumuman', 'prodi_id')

    op.drop_constraint('fk_agenda_prodi_id', 'agenda', type_='foreignkey')
    op.drop_column('agenda', 'prodi_id')

    op.drop_constraint('fk_rps_prodi_id', 'rps', type_='foreignkey')
    op.drop_column('rps', 'prodi_id')

    op.drop_constraint('fk_student_outcome_prodi_id', 'student_outcome', type_='foreignkey')
    op.drop_constraint('uq_prodi_so_code', 'student_outcome', type_='unique')
    op.create_index('so_code', 'student_outcome', ['so_code'], unique=True)
    op.drop_column('student_outcome', 'prodi_id')

    op.drop_constraint('fk_matakuliah_prodi_id', 'mata_kuliah', type_='foreignkey')
    op.drop_constraint('uq_matakuliah_prodi_kode_kurikulum', 'mata_kuliah', type_='unique')
    op.create_unique_constraint('uq_matakuliah_kode_kurikulum', 'mata_kuliah', ['kode', 'kurikulum'])
    op.drop_column('mata_kuliah', 'prodi_id')

    op.drop_constraint('fk_user_prodi_id', 'user', type_='foreignkey')
    op.drop_column('user', 'prodi_id')

    op.drop_constraint('fk_prodi_kaprodi_id_user', 'prodi', type_='foreignkey')
    op.drop_table('prodi')
