"""Initial complete database schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-01 05:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. User
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='dosen'),
        sa.Column('nidn', sa.String(length=30), nullable=True),
        sa.Column('nip', sa.String(length=30), nullable=True),
        sa.Column('sinta_id', sa.String(length=30), nullable=True),
        sa.Column('google_scholar_id', sa.String(length=100), nullable=True),
        sa.Column('google_scholar_url', sa.String(length=255), nullable=True),
        sa.Column('orcid_id', sa.String(length=30), nullable=True),
        sa.Column('scopus_id', sa.String(length=50), nullable=True),
        sa.Column('researcher_id', sa.String(length=50), nullable=True),
        sa.Column('garuda_id', sa.String(length=50), nullable=True),
        sa.Column('afiliasi', sa.String(length=150), nullable=True),
        sa.Column('prodi', sa.String(length=100), nullable=True),
        sa.Column('jabatan_fungsional', sa.String(length=100), nullable=True),
        sa.Column('bidang_keahlian', sa.Text(), nullable=True),
        sa.Column('homepage_url', sa.String(length=255), nullable=True),
        sa.Column('foto_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('nidn'),
        sa.UniqueConstraint('nip')
    )

    # 2. Tahun Ajaran
    op.create_table('tahun_ajaran',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tahun', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.String(length=10), nullable=False),
        sa.Column('is_aktif', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Mata Kuliah
    op.create_table('mata_kuliah',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kode', sa.String(length=20), nullable=False),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('sks', sa.Integer(), nullable=True),
        sa.Column('kurikulum', sa.String(length=50), nullable=True),
        sa.Column('deskripsi', sa.Text(), nullable=True),
        sa.Column('tipe', sa.String(length=20), nullable=True, server_default='wajib'),
        sa.Column('qr_kaprodi', sa.String(length=200), nullable=True),
        sa.Column('tgl_pengesahan_kaprodi', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kode', 'kurikulum', name='uq_matakuliah_kode_kurikulum')
    )

    # 4. RPS
    op.create_table('rps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matakuliah_id', sa.Integer(), nullable=False),
        sa.Column('tahun_ajaran_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sks', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('semester', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('prasyarat', sa.String(length=100), nullable=True),
        sa.Column('qr_kaprodi', sa.String(length=200), nullable=True),
        sa.Column('tgl_pengesahan_kaprodi', sa.Date(), nullable=True),
        sa.Column('qr_dosen_koor', sa.String(length=200), nullable=True),
        sa.Column('tgl_pengesahan_koor', sa.Date(), nullable=True),
        sa.Column('tp_data', sa.JSON(), nullable=True),
        sa.Column('rps_detail', sa.JSON(), nullable=True),
        sa.Column('rps_status', sa.String(length=20), nullable=False, server_default='assigned'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['matakuliah_id'], ['mata_kuliah.id']),
        sa.ForeignKeyConstraint(['tahun_ajaran_id'], ['tahun_ajaran.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Panduan
    op.create_table('panduan',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nama', sa.String(length=255), nullable=False),
        sa.Column('tipe', sa.String(length=10), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('link_url', sa.Text(), nullable=True),
        sa.Column('is_aktif', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Pengumuman
    op.create_table('pengumuman',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judul', sa.String(length=255), nullable=False),
        sa.Column('konten', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('penulis_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['penulis_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Arsip Dokumen
    op.create_table('arsip_dokumen',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nama', sa.String(length=255), nullable=False),
        sa.Column('link_url', sa.Text(), nullable=False),
        sa.Column('akses_tipe', sa.String(length=20), nullable=False, server_default='semua'),
        sa.Column('is_aktif', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('uploader_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['uploader_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('arsip_dokumen_allowed_users',
        sa.Column('arsip_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['arsip_id'], ['arsip_dokumen.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('arsip_id', 'user_id')
    )

    # 8. Agenda
    op.create_table('agenda',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judul', sa.String(length=255), nullable=False),
        sa.Column('deskripsi', sa.Text(), nullable=True),
        sa.Column('tanggal', sa.Date(), nullable=False),
        sa.Column('waktu_mulai', sa.Time(), nullable=True),
        sa.Column('waktu_selesai', sa.Time(), nullable=True),
        sa.Column('lokasi', sa.String(length=255), nullable=True),
        sa.Column('kategori', sa.String(length=50), nullable=True, server_default='Rapat Umum'),
        sa.Column('is_aktif', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('agenda')
    op.drop_table('arsip_dokumen_allowed_users')
    op.drop_table('arsip_dokumen')
    op.drop_table('pengumuman')
    op.drop_table('panduan')
    op.drop_table('rps')
    op.drop_table('mata_kuliah')
    op.drop_table('tahun_ajaran')
    op.drop_table('user')
