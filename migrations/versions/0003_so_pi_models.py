"""SO-PI master data pindah ke tabel database

Revision ID: 0003_so_pi_models
Revises: 0002_split_rps_detail
Create Date: 2026-08-12 09:00:00.000000

Membuat tabel student_outcome, performance_indicator, dan proficiency_level,
lalu meng-seed dari static/data/so-pi.json (data yang sama persis dengan
sebelumnya, sehingga kode referensi di RPS yang lama tetap cocok).
"""
import json
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_so_pi_models'
down_revision = '0002_split_rps_detail'
branch_labels = None
depends_on = None


def _load_seed():
    """Baca static/data/so-pi.json relatif dari root proyek."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base, 'static', 'data', 'so-pi.json')
    if not os.path.exists(path):
        return [], []
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return raw.get('student_outcome', []), raw.get('proficiency_levels', [])


def upgrade():
    conn = op.get_bind()

    # 1. Tabel baru
    op.create_table('student_outcome',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('so_code', sa.String(length=20), nullable=False),
        sa.Column('so_description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('so_code')
    )
    op.create_table('performance_indicator',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_outcome_id', sa.Integer(), nullable=False),
        sa.Column('pi_code', sa.String(length=50), nullable=False),
        sa.Column('pi_description', sa.Text(), nullable=False),
        sa.Column('level', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['student_outcome_id'], ['student_outcome.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_outcome_id', 'pi_code', name='uq_pi_outcome_code')
    )
    op.create_table('proficiency_level',
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('level')
    )

    # 2. Seed dari so-pi.json
    student_outcome, proficiency_levels = _load_seed()

    for lvl in proficiency_levels:
        conn.execute(
            sa.text("INSERT INTO proficiency_level (level, label) VALUES (:lvl, :label)"),
            {'lvl': lvl.get('level'), 'label': lvl.get('label', '')},
        )

    for so in student_outcome:
        row = conn.execute(
            sa.text("SELECT id FROM student_outcome WHERE so_code = :code"),
            {'code': so.get('so_code')},
        ).fetchone()
        if not row:
            conn.execute(
                sa.text("INSERT INTO student_outcome (so_code, so_description, is_active) VALUES (:code, :desc, 1)"),
                {'code': so.get('so_code'), 'desc': so.get('so_description', '')},
            )
            row = conn.execute(
                sa.text("SELECT id FROM student_outcome WHERE so_code = :code"),
                {'code': so.get('so_code')},
            ).fetchone()
        so_id = row[0]
        for pi in so.get('performance_indicator', []):
            conn.execute(
                sa.text("""
                    INSERT INTO performance_indicator (student_outcome_id, pi_code, pi_description, level)
                    VALUES (:so_id, :code, :desc, :lvl)
                """),
                {
                    'so_id' : so_id,
                    'code'  : pi.get('pi_code'),
                    'desc'  : pi.get('pi_description', ''),
                    'lvl'   : pi.get('level', 1),
                },
            )


def downgrade():
    op.drop_table('performance_indicator')
    op.drop_table('student_outcome')
    op.drop_table('proficiency_level')
