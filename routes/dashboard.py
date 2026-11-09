from datetime import date
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import RPS, MataKuliah, User, TahunAjaran, Panduan, Agenda, ArsipDokumen, Prodi
from sqlalchemy import or_

bp = Blueprint('dashboard', __name__)


def hitung_progress_rps(rps):
    """Hitung persentase kelengkapan pengisian RPS (0-100).

    Hanya mengukur bagian yang menjadi tanggung jawab dosen (bukan kaprodi).
    Bobot disesuaikan dengan kompleksitas pengisian tiap bagian:
      - rencana_mingguan   : 3 poin  (tab-3, 16 minggu — paling berat)
      - rencana_evaluasi   : 2 poin  (tab-4 Assessment Plan, 16 minggu)
      - kriteria_penilaian : 2 poin  (tab-5 Grading Criteria)
      - sarana_prasarana   : 1 poin  (tab-4 Facilities)
      - kesepakatan        : 1 poin  (tab-5 Course Policies)
      - pustaka            : 1 poin  (tab-5 References)
    Total: 10 poin

    Perhitungan proporsional per item agar 1 minggu saja tidak langsung 100%.
    """
    score = 0.0
    total = 10
    total_minggu = 16

    # tab-3: Weekly Course Plan (bobot 3, 16 minggu)
    if rps.rencana_mingguan and len(rps.rencana_mingguan) > 0:
        filled = 0
        for m in rps.rencana_mingguan:
            bahan = (m.get('bahan_kajian') or '').strip()
            modalitas = (m.get('modalitas') or '').strip()
            waktu = (m.get('waktu') or '').strip()
            tp_ref = (m.get('tp_ref') or '').strip()
            if bahan and modalitas and waktu and tp_ref:
                filled += 1
        score += (filled / total_minggu) * 3

    # tab-4: Assessment Plan (bobot 2, 16 minggu)
    if rps.rencana_evaluasi and len(rps.rencana_evaluasi) > 0:
        filled = 0
        for r in rps.rencana_evaluasi:
            tp = (r.get('tp') or '').strip()
            metode = (r.get('metode') or '').strip()
            if tp and metode:
                filled += 1
        score += (filled / total_minggu) * 2

    # tab-5: Kriteria Penilaian (bobot 2, proporsional terhadap total 100%)
    if rps.kriteria_penilaian and len(rps.kriteria_penilaian) > 0:
        total_persen = 0.0
        for k in rps.kriteria_penilaian:
            try:
                p = float(k.get('persentase', 0) or 0)
            except (ValueError, TypeError):
                p = 0.0
            total_persen += p
        if total_persen >= 100:
            score += 2
        else:
            has_filled = any(
                (k.get('sub_komponen') or '').strip()
                for k in rps.kriteria_penilaian
            )
            if has_filled:
                score += max(0.4, (total_persen / 100) * 2)

    # tab-4: Sarana & Prasarana
    if rps.sarana_prasarana and len(rps.sarana_prasarana) > 0:
        score += 1

    # tab-5: Kesepakatan (Course Policies)
    if rps.kesepakatan and len(rps.kesepakatan) > 0:
        score += 1

    # tab-5: Pustaka (References)
    if rps.pustaka and len(rps.pustaka) > 0:
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

    user_prodi_id = getattr(current_user, 'prodi_id', None)
    prodi_filter_id = request.args.get('prodi_id', type=int) if current_user.is_kajur else None

    if current_user.can_manage_kurikulum:
        query_rps = RPS.query
        if user_prodi_id and not current_user.is_kajur:
            query_rps = query_rps.filter_by(prodi_id=user_prodi_id)
        elif prodi_filter_id:
            query_rps = query_rps.filter_by(prodi_id=prodi_filter_id)

        if ta_aktif:
            rps_list = query_rps.filter_by(tahun_ajaran_id=ta_aktif.id).all()
        else:
            rps_list = query_rps.all()

        query_dosen = User.query.filter(User.role.in_(['dosen', 'timkur']))
        if user_prodi_id and not current_user.is_kajur:
            query_dosen = query_dosen.filter_by(prodi_id=user_prodi_id)
        elif prodi_filter_id:
            query_dosen = query_dosen.filter_by(prodi_id=prodi_filter_id)
        dosens = query_dosen.all()

        rps_selesai = 0  # approved
        rps_draft   = 0  # submitted
        rps_belum   = 0  # assigned
        rps_reject  = 0  # rejected
        per_dosen     = []
        progress_items = []

        for rps in rps_list:
            nama = rps.matakuliah.nama if rps.matakuliah else '—'
            progress = hitung_progress_rps(rps)
            progress_items.append({
                'label'   : nama if len(nama) <= 28 else nama[:28] + '...',
                'progress': progress
            })

            if rps.rps_status == 'approved':
                rps_selesai += 1
            elif rps.rps_status == 'submitted':
                rps_draft += 1
            elif rps.rps_status == 'rejected':
                rps_reject += 1
            else:
                rps_belum += 1

        for d in dosens:
            q_d = RPS.query.filter_by(user_id=d.id)
            if ta_aktif:
                q_d = q_d.filter_by(tahun_ajaran_id=ta_aktif.id)
            jumlah = q_d.count()
            per_dosen.append({
                'nama'  : d.nama if len(d.nama) <= 20 else d.nama[:20] + '...',
                'jumlah': jumlah
            })

        progress_items = sorted(progress_items, key=lambda x: x['progress'])[:5]
        per_dosen      = sorted(per_dosen,      key=lambda x: x['jumlah'], reverse=True)[:5]

        total_slp = query_rps.count()
        total_prodi = Prodi.query.count()
        total_users = User.query.filter_by(prodi_id=prodi_filter_id).count() if prodi_filter_id else User.query.count()
        daftar_prodi = Prodi.query.order_by(Prodi.kode.asc()).all()

        return render_template(
            'dashboard/kaprodi.html',
            semua_ta=semua_ta,
            agenda_terdekat=agenda_terdekat,
            prodi_id=prodi_filter_id,
            daftar_prodi=daftar_prodi,
            total_slp=total_slp,
            total_prodi=total_prodi,
            total_users=total_users,
            total_dosen=len(dosens),
            total_mk=len(rps_list),
            rps_selesai=rps_selesai,
            rps_draft=rps_draft,
            rps_belum=rps_belum,
            rps_reject=rps_reject,
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

    # Arsip dokumen yang dapat diakses dosen: tipe 'semua' atau di-tag ke user ini.
    arsip_docs = ArsipDokumen.query.filter(
        ArsipDokumen.is_aktif == True,
        or_(
            ArsipDokumen.akses_tipe == 'semua',
            ArsipDokumen.allowed_users.any(id=current_user.id)
        )
    ).order_by(ArsipDokumen.updated_at.desc()).limit(5).all()

    return render_template(
        'dashboard/dosen.html',
        semua_ta=semua_ta,
        agenda_terdekat=agenda_terdekat,
        arsip_docs=arsip_docs,
        total_mk=len(rps_list),
        rps_selesai=rps_selesai,
        rps_draft=rps_draft,
        rps_belum=rps_belum,
        progress_labels=[x['label']    for x in progress_items],
        progress_values=[x['progress'] for x in progress_items]
    )