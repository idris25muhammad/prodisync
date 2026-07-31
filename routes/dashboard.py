from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import RPS, MataKuliah, User, TahunAjaran, Panduan, Agenda

bp = Blueprint('dashboard', __name__)


def hitung_progress_rps(rps):
    """Hitung persentase kelengkapan pengisian RPS (0-100)."""
    score = 0
    total = 6

    if rps.matakuliah and rps.matakuliah.deskripsi:
        score += 1
    if rps.tp_data and len(rps.tp_data) > 0:
        score += 1
    if rps.rps_detail and rps.rps_detail.get('rencana_mingguan'):
        score += 1
    if rps.rps_detail and rps.rps_detail.get('rencana_evaluasi'):
        score += 1
    if rps.rps_detail and rps.rps_detail.get('kriteria_penilaian'):
        score += 1
    if rps.rps_detail and rps.rps_detail.get('pustaka'):
        score += 1

    return round((score / total) * 100)


@bp.route('/dashboard')
@login_required
def index():
    semua_ta = TahunAjaran.query.all()
    ta_aktif = TahunAjaran.query.filter_by(is_aktif=True).first()

    today = date.today()
    agenda_terdekat = Agenda.query.filter(
        Agenda.tanggal >= today,
        Agenda.is_aktif == True
    ).order_by(Agenda.tanggal.asc(), Agenda.waktu_mulai.asc()).first()

    if current_user.is_kaprodi:
        if ta_aktif:
            rps_list = RPS.query.filter_by(tahun_ajaran_id=ta_aktif.id).all()
        else:
            rps_list = RPS.query.all()

        dosens = User.query.filter_by(role='dosen').all()

        rps_selesai = 0
        rps_draft   = 0
        rps_belum   = 0
        per_dosen     = []
        progress_items = []

        for rps in rps_list:
            nama = rps.matakuliah.nama if rps.matakuliah else '—'
            progress = hitung_progress_rps(rps)
            progress_items.append({
                'label'   : nama if len(nama) <= 28 else nama[:28] + '...',
                'progress': progress
            })

            if progress >= 100:
                rps_selesai += 1
            elif progress > 0:
                rps_draft += 1
            else:
                rps_belum += 1

        for d in dosens:
            jumlah = RPS.query.filter_by(
                user_id=d.id,
                tahun_ajaran_id=ta_aktif.id if ta_aktif else None
            ).count()
            per_dosen.append({
                'nama'  : d.nama if len(d.nama) <= 20 else d.nama[:20] + '...',
                'jumlah': jumlah
            })

        progress_items = sorted(progress_items, key=lambda x: x['progress'])[:5]
        per_dosen      = sorted(per_dosen,      key=lambda x: x['jumlah'], reverse=True)[:5]

        return render_template(
            'dashboard/kaprodi.html',
            semua_ta=semua_ta,
            agenda_terdekat=agenda_terdekat,
            total_dosen=len(dosens),
            total_mk=len(rps_list),
            rps_selesai=rps_selesai,
            rps_draft=rps_draft,
            rps_belum=rps_belum,
            progress_labels=[x['label']    for x in progress_items],
            progress_values=[x['progress'] for x in progress_items],
            dosen_labels=[x['nama']   for x in per_dosen],
            dosen_values=[x['jumlah'] for x in per_dosen]
        )

    # ── Logika Dosen ──────────────────────────────────────────────────────────
    if ta_aktif:
        rps_list = RPS.query.filter_by(user_id=current_user.id, tahun_ajaran_id=ta_aktif.id).all()
    else:
        rps_list = RPS.query.filter_by(user_id=current_user.id).all()

    rps_selesai    = 0
    rps_draft      = 0
    rps_belum      = 0
    progress_items = []
    daftar_panduan = Panduan.query.filter_by(is_aktif=True).order_by(Panduan.updated_at.desc()).all()

    for rps in rps_list:
        nama = rps.matakuliah.nama if rps.matakuliah else '—'
        progress = hitung_progress_rps(rps)
        progress_items.append({
            'label'   : nama if len(nama) <= 28 else nama[:28] + '...',
            'progress': progress
        })

        if progress >= 100:
            rps_selesai += 1
        elif progress > 0:
            rps_draft += 1
        else:
            rps_belum += 1

    progress_items = sorted(progress_items, key=lambda x: x['progress'])[:5]

    return render_template(
        'dashboard/dosen.html',
        semua_ta=semua_ta,
        agenda_terdekat=agenda_terdekat,
        semua_panduan=daftar_panduan,
        total_mk=len(rps_list),
        rps_selesai=rps_selesai,
        rps_draft=rps_draft,
        rps_belum=rps_belum,
        progress_labels=[x['label']    for x in progress_items],
        progress_values=[x['progress'] for x in progress_items]
    )