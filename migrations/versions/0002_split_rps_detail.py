"""Split rps_detail JSON menjadi satu kolom per section

Revision ID: 0002_split_rps_detail
Revises: 0001_initial_schema
Create Date: 2026-08-11 10:00:00.000000

"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_split_rps_detail'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Tambah kolom baru
    op.add_column('rps', sa.Column('rencana_mingguan', sa.JSON(), nullable=True))
    op.add_column('rps', sa.Column('sarana_prasarana', sa.JSON(), nullable=True))
    op.add_column('rps', sa.Column('metode_evaluasi', sa.Text(), nullable=True))
    op.add_column('rps', sa.Column('rencana_evaluasi', sa.JSON(), nullable=True))
    op.add_column('rps', sa.Column('kriteria_penilaian', sa.JSON(), nullable=True))
    op.add_column('rps', sa.Column('kesepakatan', sa.JSON(), nullable=True))
    op.add_column('rps', sa.Column('pustaka', sa.JSON(), nullable=True))

    # 2. Migrasi data dari rps_detail JSON ke kolom per-section
    rows = conn.execute(
        sa.text("SELECT id, rps_detail FROM rps WHERE rps_detail IS NOT NULL")
    ).fetchall()

    for rps_id, detail_raw in rows:
        if not detail_raw:
            continue
        detail = detail_raw if isinstance(detail_raw, dict) else json.loads(detail_raw)
        conn.execute(
            sa.text("""
                UPDATE rps SET
                    rencana_mingguan   = :rm,
                    sarana_prasarana   = :sp,
                    metode_evaluasi    = :me,
                    rencana_evaluasi   = :re,
                    kriteria_penilaian = :kp,
                    kesepakatan        = :ks,
                    pustaka            = :pu
                WHERE id = :id
            """),
            {
                'id': rps_id,
                'rm': json.dumps(detail.get('rencana_mingguan') or [], ensure_ascii=False) if detail.get('rencana_mingguan') else None,
                'sp': json.dumps(detail.get('sarana_prasarana') or [], ensure_ascii=False) if detail.get('sarana_prasarana') else None,
                'me': detail.get('metode_evaluasi'),
                're': json.dumps(detail.get('rencana_evaluasi') or [], ensure_ascii=False) if detail.get('rencana_evaluasi') else None,
                'kp': json.dumps(detail.get('kriteria_penilaian') or [], ensure_ascii=False) if detail.get('kriteria_penilaian') else None,
                'ks': json.dumps(detail.get('kesepakatan') or [], ensure_ascii=False) if detail.get('kesepakatan') else None,
                'pu': json.dumps(detail.get('pustaka') or [], ensure_ascii=False) if detail.get('pustaka') else None,
            },
        )

    # 3. Hapus kolom lama
    op.drop_column('rps', 'rps_detail')


def downgrade():
    conn = op.get_bind()

    op.add_column('rps', sa.Column('rps_detail', sa.JSON(), nullable=True))

    rows = conn.execute(
        sa.text("SELECT id, rencana_mingguan, sarana_prasarana, metode_evaluasi, rencana_evaluasi, kriteria_penilaian, kesepakatan, pustaka FROM rps")
    ).fetchall()

    for (rps_id, rm, sp, me, re, kp, ks, pu) in rows:
        detail = {}
        if rm: detail['rencana_mingguan'] = rm if isinstance(rm, list) else json.loads(rm)
        if sp: detail['sarana_prasarana'] = sp if isinstance(sp, list) else json.loads(sp)
        if me: detail['metode_evaluasi'] = me
        if re: detail['rencana_evaluasi'] = re if isinstance(re, list) else json.loads(re)
        if kp: detail['kriteria_penilaian'] = kp if isinstance(kp, list) else json.loads(kp)
        if ks: detail['kesepakatan'] = ks if isinstance(ks, list) else json.loads(ks)
        if pu: detail['pustaka'] = pu if isinstance(pu, list) else json.loads(pu)
        detail_json = json.dumps(detail, ensure_ascii=False) if detail else None
        conn.execute(
            sa.text("UPDATE rps SET rps_detail = :d WHERE id = :id"),
            {'d': detail_json, 'id': rps_id},
        )

    op.drop_column('rps', 'rencana_mingguan')
    op.drop_column('rps', 'sarana_prasarana')
    op.drop_column('rps', 'metode_evaluasi')
    op.drop_column('rps', 'rencana_evaluasi')
    op.drop_column('rps', 'kriteria_penilaian')
    op.drop_column('rps', 'kesepakatan')
    op.drop_column('rps', 'pustaka')
