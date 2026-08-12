from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from extensions import db
from models import RPS, MataKuliah, User, TahunAjaran
from sqlalchemy import or_
from utils.decorators import kaprodi_required
import os
import re
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from routes.dashboard import hitung_progress_rps

bp = Blueprint('rps', __name__, url_prefix='/rps')


# ── Route: Daftar RPS (Rencana Program Studi) ────────────────────────────────
@bp.route('/')
@login_required
def list():
    ta_aktif = TahunAjaran.query.filter_by(is_aktif=True).first()

    q = request.args.get('q', '').strip()
    rps_status = request.args.get('status', '').strip()
    semester = request.args.get('semester', type=int)

    if 'tahun_ajaran_id' in request.args:
        ta_arg = request.args.get('tahun_ajaran_id', '').strip()
        if ta_arg in ('all', ''):
            tahun_ajaran_id = None
        else:
            tahun_ajaran_id = int(ta_arg) if ta_arg.isdigit() else None
    else:
        tahun_ajaran_id = ta_aktif.id if ta_aktif else None

    if current_user.is_kaprodi:
        query = db.session.query(RPS, MataKuliah, User).join(
            MataKuliah, RPS.matakuliah_id == MataKuliah.id
        ).join(
            User, RPS.user_id == User.id
        )
    else:
        query = db.session.query(RPS, MataKuliah, User).join(
            MataKuliah, RPS.matakuliah_id == MataKuliah.id
        ).outerjoin(
            User, RPS.user_id == User.id
        ).filter(RPS.user_id == current_user.id)

    if q:
        query = query.filter(
            or_(
                MataKuliah.kode.ilike(f'%{q}%'),
                MataKuliah.nama.ilike(f'%{q}%'),
            )
        )

    if tahun_ajaran_id:
        query = query.filter(RPS.tahun_ajaran_id == tahun_ajaran_id)

    if rps_status:
        query = query.filter(RPS.rps_status == rps_status)

    if semester:
        query = query.filter(RPS.semester == semester)

    rps_list = query.order_by(MataKuliah.kode.asc(), MataKuliah.nama.asc()).all()

    users = User.query.order_by(User.nama.asc()).all() if current_user.is_kaprodi else []
    tahun_ajaran_list = TahunAjaran.query.order_by(TahunAjaran.tahun.desc(), TahunAjaran.semester.asc()).all()

    return render_template(
        'rps/list.html',
        rps_list=rps_list,
        users=users,
        q=q,
        tahun_ajaran_id=tahun_ajaran_id,
        rps_status=rps_status,
        semester=semester,
        ta_aktif=ta_aktif,
        tahun_ajaran_list=tahun_ajaran_list,
        hitung_progress_rps=hitung_progress_rps,
    )


# ── Route: Tambah RPS ─────────────────────────────────────────────────────────
@bp.route('/add', methods=['POST'])
@login_required
@kaprodi_required
def add():
    matakuliah_id   = request.form.get('matakuliah_id',   type=int)
    user_id         = request.form.get('assigned_to',     type=int)
    tahun_ajaran_id = request.form.get('tahun_ajaran_id', type=int)
    semester        = request.form.get('semester',        type=int)
    prasyarat       = request.form.get('prasyarat',       '').strip()

    if not matakuliah_id:
        flash('Mata kuliah wajib dipilih dari katalog.', 'danger')
        return redirect(url_for('rps.list'))
    if not user_id:
        flash('Dosen koordinator wajib dipilih.', 'danger')
        return redirect(url_for('rps.list'))
    if not tahun_ajaran_id:
        flash('Tahun ajaran wajib dipilih.', 'danger')
        return redirect(url_for('rps.list'))

    mk = MataKuliah.query.get(matakuliah_id)
    sks = mk.sks if (mk and mk.sks) else (request.form.get('sks', type=int) or 3)

    # Cek duplikat (MK + TA yang sama)
    existing = RPS.query.filter_by(matakuliah_id=matakuliah_id, tahun_ajaran_id=tahun_ajaran_id).first()
    if existing:
        flash('RPS untuk mata kuliah dan tahun ajaran ini sudah ada.', 'danger')
        return redirect(url_for('rps.list'))

    # Handle Pengesahan & QR Kaprodi saat buat RPS
    tgl_kaprodi_str = request.form.get('tgl_pengesahan_kaprodi', '').strip()
    tgl_kaprodi = None
    if tgl_kaprodi_str:
        try:
            tgl_kaprodi = datetime.strptime(tgl_kaprodi_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if not tgl_kaprodi and mk and mk.tgl_pengesahan_kaprodi:
        tgl_kaprodi = mk.tgl_pengesahan_kaprodi

    qr_kaprodi_file = request.files.get('qr_kaprodi')
    filename_qr = None
    if qr_kaprodi_file and qr_kaprodi_file.filename:
        ext = qr_kaprodi_file.filename.rsplit('.', 1)[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
            os.makedirs(upload_dir, exist_ok=True)
            filename_qr = f"kaprodi_rps_{int(time.time())}.{ext}"
            filepath = os.path.join(upload_dir, filename_qr)
            qr_kaprodi_file.save(filepath)
    if not filename_qr and mk and mk.qr_kaprodi:
        filename_qr = mk.qr_kaprodi

    db.session.add(RPS(
        matakuliah_id=matakuliah_id,
        tahun_ajaran_id=tahun_ajaran_id,
        user_id=user_id,
        sks=sks,
        semester=semester,
        prasyarat=prasyarat or None,
        qr_kaprodi=filename_qr,
        tgl_pengesahan_kaprodi=tgl_kaprodi,
        rps_status='assigned',
    ))
    db.session.commit()
    flash('RPS berhasil ditambahkan!', 'success')
    return redirect(url_for('rps.list'))


# ── Route: Edit RPS (metadata) ────────────────────────────────────────────────
@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_meta(id):
    rps = RPS.query.get_or_404(id)

    if not current_user.is_kaprodi and rps.user_id != current_user.id:
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('rps.list'))

    if rps.matakuliah and rps.matakuliah.sks:
        rps.sks = rps.matakuliah.sks
    else:
        rps.sks = request.form.get('sks', type=int) or rps.sks

    rps.semester  = request.form.get('semester',  type=int) or rps.semester
    rps.prasyarat = request.form.get('prasyarat', '').strip() or None

    if current_user.is_kaprodi:
        rps.user_id         = request.form.get('assigned_to',     type=int) or rps.user_id
        rps.tahun_ajaran_id = request.form.get('tahun_ajaran_id', type=int) or rps.tahun_ajaran_id

        tgl_kaprodi_str = request.form.get('tgl_pengesahan_kaprodi', '').strip()
        if tgl_kaprodi_str:
            try:
                rps.tgl_pengesahan_kaprodi = datetime.strptime(tgl_kaprodi_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        qr_kaprodi_file = request.files.get('qr_kaprodi')
        if qr_kaprodi_file and qr_kaprodi_file.filename:
            ext = qr_kaprodi_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg']:
                upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
                os.makedirs(upload_dir, exist_ok=True)
                filename_qr = f"kaprodi_rps_{rps.id}_qr_{int(time.time())}.{ext}"
                filepath = os.path.join(upload_dir, filename_qr)
                qr_kaprodi_file.save(filepath)
                rps.qr_kaprodi = filename_qr

    db.session.commit()
    flash('RPS berhasil diperbarui!', 'success')
    return redirect(url_for('rps.list'))


# ── Route: Hapus RPS ──────────────────────────────────────────────────────────
@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(rps)
    db.session.commit()
    flash('RPS berhasil dihapus!', 'success')
    return redirect(url_for('rps.list'))


# ── Route: Approve RPS ────────────────────────────────────────────────────────
@bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@kaprodi_required
def approve(id):
    rps = RPS.query.get_or_404(id)
    rps.rps_status = 'approved'
    rps.reason = None
    db.session.commit()
    flash('RPS berhasil di-approve.', 'success')
    return redirect(url_for('rps.list'))


# ── Route: Reject RPS ─────────────────────────────────────────────────────────
@bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@kaprodi_required
def reject(id):
    rps = RPS.query.get_or_404(id)
    reason = request.form.get('reason', '').strip()

    if not reason:
        flash('Alasan reject wajib diisi.', 'danger')
        return redirect(url_for('rps.list'))

    rps.rps_status = 'rejected'
    rps.reason = reason
    db.session.commit()
    flash('RPS berhasil di-reject.', 'warning')
    return redirect(url_for('rps.list'))


@bp.route('/<int:id>/revisi', methods=['POST'])
@login_required
@kaprodi_required
def revisi(id):
    rps = RPS.query.get_or_404(id)
    if rps.rps_status != 'approved':
        flash('Hanya RPS yang sudah di-approve yang dapat direvisi.', 'warning')
        return redirect(url_for('rps.list'))
    rps.rps_status = 'assigned'
    db.session.commit()
    flash('RPS dikembalikan ke draft untuk direvisi.', 'success')
    return redirect(url_for('rps.editor', id=id))


# ── Helper: Parse form ke model RPS ──────────────────────────────────────────
def _parse_tp_form(rps):
    """Bagian Tim Kurikulum: Tujuan Pembelajaran (CPL)."""
    tp_teks = request.form.getlist('tp_teks[]')
    so_pi   = request.form.getlist('so_pi[]')
    levels  = request.form.getlist('tp_level[]')
    rps.tp_data = [
        {
            'no'   : i + 1,
            'teks' : tp_teks[i],
            'sopi' : so_pi[i],
            'level': int(levels[i]) if levels[i].isdigit() else 1
        }
        for i in range(len(tp_teks)) if tp_teks[i].strip()
    ]


def _parse_detail_form(rps):
    """Bagian Dosen Koordinator: rencana mingguan, sarana, evaluasi, penilaian, dll."""
    minggu_ke  = request.form.getlist('minggu_ke[]')
    tp_ref     = request.form.getlist('tp_ref[]')
    kemampuan  = request.form.getlist('kemampuan[]')
    bahan      = request.form.getlist('bahan_kajian[]')
    sub_bahan  = request.form.getlist('sub_bahan[]')
    modalitas  = request.form.getlist('modalitas[]')
    waktu      = request.form.getlist('waktu[]')
    pengalaman = request.form.getlist('pengalaman[]')

    rencana_mingguan = [
        {
            'minggu'      : minggu_ke[i],
            'tp_ref'      : tp_ref[i],
            'kemampuan'   : kemampuan[i],
            'bahan_kajian': bahan[i],
            'sub_bahan'   : sub_bahan[i],
            'modalitas'   : modalitas[i],
            'waktu'       : waktu[i],
            'pengalaman'  : pengalaman[i]
        }
        for i in range(len(minggu_ke))
        if bahan[i].strip() or kemampuan[i].strip()
    ]

    sarana = [
        {'no': i + 1, 'nama': n, 'jumlah': j}
        for i, (n, j) in enumerate(zip(
            request.form.getlist('sarana_nama[]'),
            request.form.getlist('sarana_jumlah[]')
        )) if n.strip()
    ]

    eval_minggu     = request.form.getlist('eval_minggu[]')
    eval_tp         = request.form.getlist('eval_tp[]')
    eval_metode     = request.form.getlist('eval_metode[]')
    eval_keterangan = request.form.getlist('eval_keterangan[]')

    rencana_evaluasi = [
        {
            'minggu'    : eval_minggu[i],
            'tp'        : eval_tp[i],
            'metode'    : eval_metode[i],
            'keterangan': eval_keterangan[i]
        }
        for i in range(len(eval_minggu))
        if eval_tp[i].strip() or eval_metode[i].strip() or eval_keterangan[i].strip()
    ]

    kriteria = [
        {'komponen': k, 'sub_komponen': s, 'persentase': p}
        for k, s, p in zip(
            request.form.getlist('komponen_nilai[]'),
            request.form.getlist('sub_komponen[]'),
            request.form.getlist('persentase[]')
        )
    ]

    rps.rencana_mingguan    = rencana_mingguan or None
    rps.sarana_prasarana    = sarana or None
    rps.metode_evaluasi     = request.form.get('metode_evaluasi', '') or None
    rps.rencana_evaluasi    = rencana_evaluasi or None
    rps.kriteria_penilaian  = kriteria or None
    rps.kesepakatan         = [k for k in request.form.getlist('kesepakatan[]') if k.strip()] or None
    rps.pustaka             = [p for p in request.form.getlist('pustaka[]')     if p.strip()] or None


def format_indo_date(dt):
    if not dt:
        return ''
    if hasattr(dt, 'strftime'):
        bulan = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return f"{dt.day:02d} {bulan[dt.month]} {dt.year}"
    return str(dt)


def auto_wrap_text(text, max_len=16):
    if not text or not isinstance(text, str):
        return text
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        words = line.split(' ')
        new_words = []
        for word in words:
            if len(word) > max_len:
                chunks = [word[i:i+max_len] for i in range(0, len(word), max_len)]
                new_words.append(' '.join(chunks))
            else:
                new_words.append(word)
        processed_lines.append(' '.join(new_words))
    return '\n'.join(processed_lines)


# ── Helper: Load SO-PI master data dari database ────────────────────────────
def _load_so_pi_data():
    """
    Load master Student Outcome / Performance Indicator dari tabel database
    (StudentOutcome, PerformanceIndicator, ProficiencyLevel).
    Return dict dengan kontrak yang sama seperti versi lama yang membaca
    static/data/so-pi.json:
      - so_map    : {so_code: so_description}
      - pi_map    : {pi_code: {'description': ..., 'so_code': ..., 'level': int}}
      - levels    : {level_int: label}
      - so_pi_rows: list baris SO-PI urut (untuk Section IV, semua PI aktif)
    """
    from models import StudentOutcome, ProficiencyLevel, so_sort_key

    so_map, pi_map, levels, so_pi_rows = {}, {}, {}, []
    for lvl in ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all():
        levels[lvl.level] = lvl.label

    for so in sorted(
            StudentOutcome.query.filter_by(is_active=True).all(),
            key=lambda s: so_sort_key(s.so_code)):
        so_map[so.so_code] = so.so_description
        for pi in sorted(so.indicators, key=lambda p: p.pi_code):
            pi_map[pi.pi_code] = {
                'description': pi.pi_description,
                'so_code'    : so.so_code,
                'level'      : pi.level,
            }
            so_pi_rows.append({
                'so_code'        : so.so_code,
                'so_description' : so.so_description,
                'pi_code'        : pi.pi_code,
                'pi_description' : pi.pi_description,
                'level'          : pi.level,
            })

    for row in so_pi_rows:
        row['level_label'] = levels.get(row['level'], '')
    return {'so_map': so_map, 'pi_map': pi_map, 'levels': levels, 'so_pi_rows': so_pi_rows}


# ── Route: API SO-PI (untuk modal pemilih SO-PI di editor RPS) ─────────────
@bp.route('/api/so-pi')
@login_required
def api_so_pi():
    """
    Sumber data dinamis pengganti static/data/so-pi.json untuk modal
    pemilih SO-PI. Bentuk JSON persis seperti file lama:
      {student_outcome: [{so_code, so_description, performance_indicator: [...]}],
       proficiency_levels: [{level, label}]}
    """
    from flask import jsonify
    from models import StudentOutcome, ProficiencyLevel, so_sort_key

    student_outcome = []
    for so in sorted(
            StudentOutcome.query.filter_by(is_active=True).all(),
            key=lambda s: so_sort_key(s.so_code)):
        student_outcome.append({
            'so_code'             : so.so_code,
            'so_description'      : so.so_description,
            'performance_indicator': [
                {
                    'pi_code'       : pi.pi_code,
                    'pi_description': pi.pi_description,
                    'level'         : pi.level,
                }
                for pi in sorted(so.indicators, key=lambda p: p.pi_code)
            ],
        })
    proficiency_levels = [
        {'level': lvl.level, 'label': lvl.label}
        for lvl in ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all()
    ]
    return jsonify({'student_outcome': student_outcome, 'proficiency_levels': proficiency_levels})



# ── Helper: Kode metode asesmen (A/Q/MSE/FSE/P/PP) untuk Section X ────────────
# Pemetaan label baru (IABEE-style) ke kode lama tersimpan:
#   A = Assignment (dulu T), Q = Quiz (dulu K), MSE = Mid-Semester Exam (dulu ATS),
#   FSE = Final-Semester Exam (dulu AAS), P = Practice/Project (tetap P),
#   PP = Project Presentation, Demo or Team meeting (tetap PP)
_VALID_ASSESSMENT_CODES = {'A', 'Q', 'MSE', 'FSE', 'P', 'PP'}
_LEGACY_ASSESSMENT_MAP = {'T': 'A', 'K': 'Q', 'ATS': 'MSE', 'AAS': 'FSE'}


def _split_multi(raw):
    """Pecah value gabungan koma (mis. "A, P, Q" atau "TP1, TP2") jadi list token bersih."""
    if not raw:
        return []
    return [p.strip() for p in str(raw).split(',') if p.strip()]


def _normalize_assessment_code(token):
    """
    Normalisasi satu token metode ke kode baku (A/Q/MSE/FSE/P/PP) sesuai
    pilihan di UI. Kode lama (T/K/ATS/AAS) ikut dipetakan untuk kompatibilitas
    data tersimpan. Fallback deteksi dari teks deskriptif tetap dipertahankan
    untuk kompatibilitas data lama yang menyimpan teks penuh (mis. "Tugas").
    """
    t = (token or '').strip()
    if not t:
        return ''
    upper = t.upper()
    if upper in _VALID_ASSESSMENT_CODES:
        return upper
    if upper in _LEGACY_ASSESSMENT_MAP:
        return _LEGACY_ASSESSMENT_MAP[upper]
    low = t.lower()
    if 'tengah semester' in low or 'uts' in low or 'mid' in low:
        return 'MSE'
    if 'akhir semester' in low or 'uas' in low or 'final' in low:
        return 'FSE'
    if 'kuis' in low or 'quiz' in low:
        return 'Q'
    if 'presentasi' in low or 'progres' in low or 'progress' in low or 'demo' in low:
        return 'PP'
    if 'praktikum' in low or 'lab' in low or 'proyek' in low or 'project' in low:
        return 'P'
    if 'tugas' in low or 'assignment' in low:
        return 'A'
    return upper[:3]


def _assessment_codes(metode_text):
    """
    Field 'metode' bisa berisi lebih dari satu kode sekaligus, dipisah koma
    (mis. "T, P, K"). Return list kode baku UNIK, urut sesuai kemunculan.
    """
    codes = []
    for token in _split_multi(metode_text):
        code = _normalize_assessment_code(token)
        if code and code not in codes:
            codes.append(code)
    return codes


# ── Helper: parse kode SO-PI dari field tp_data[].sopi ───────────────────────
def _parse_sopi_codes(raw):
    """
    tp_data[].sopi bisa berisi:
      - kode gabungan tunggal   : "SO1-1a"
      - kode gabungan multi     : "SO1-1a, SO2-2b"
      - kode legacy tanpa prefix SO (data lama): "1a"
      - variasi spasi di sekitar tanda hubung  : "SO1 - 1a"
    Return list pi_code MURNI, mis. ['1a', '2b'], sesuai key di ref['pi_map'].
    """
    codes = []
    for part in (raw or '').split(','):
        part = part.strip()
        if not part:
            continue
        # Kode gabungan "SO1-1a" -> ambil bagian setelah tanda "-" pertama.
        # PENTING: strip lagi setelah split, karena format "SO1 - 1a" (dengan
        # spasi di sekitar tanda hubung) akan menyisakan spasi di depan pi_code
        # (mis. " 1a") kalau tidak di-strip ulang, sehingga tidak match dengan
        # key di ref['pi_map'] (yang persis "1a") dan baris SO-PI tsb hilang
        # diam-diam dari Section IV & Section X.
        pi_code = part.split('-', 1)[1].strip() if '-' in part else part
        if pi_code and pi_code not in codes:
            codes.append(pi_code)
    return codes


# ── Helper: ekstrak angka dari string referensi TP/minggu sembarang format ──
def _extract_ref_number(raw):
    """
    Field seperti eval_tp[] / eval_minggu[] adalah free-text, sehingga bisa
    diisi dengan berbagai format: "1", " 1 ", "TP-1", "CLO-1", "Minggu 5", dsb.
    Ambil angka pertama yang ditemukan agar pemetaan ke tp_data[].no / minggu
    tidak gagal hanya karena ada prefix teks atau spasi.
    Return int atau None kalau tidak ada angka sama sekali.
    """
    if raw is None:
        return None
    match = re.search(r'\d+', str(raw))
    return int(match.group()) if match else None


def _parse_tp_refs(raw):
    """
    Field eval_tp[] bisa berisi satu atau LEBIH referensi TP sekaligus,
    dipisah koma, mis. "TP1", "TP1, TP2", "1, 2". Return list nomor TP unik
    (int), sesuai key di tp_by_no.
    """
    refs = []
    for token in _split_multi(raw):
        n = _extract_ref_number(token)
        if n is not None and n not in refs:
            refs.append(n)
    return refs


def _normalize_week_key(raw):
    """
    Field minggu bisa berupa angka murni ("1".."14") ATAU label teks untuk
    masa asesmen tengah/akhir semester ("ATS"/"AAS"). Normalisasi supaya key
    yang dipakai di header & dict cells konsisten (mis. "01" -> "1",
    "ats" -> "ATS", "Minggu 5" -> "5").
    Return string key, atau None kalau tidak ada nilai valid sama sekali.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s.isdigit():
        return str(int(s))
    upper = s.upper()
    if upper in ('ATS', 'AAS'):
        return upper
    n = _extract_ref_number(s)
    return str(n) if n is not None else upper


def _week_sort_key(key):
    """Urutan kolom Section X: angka naik dulu, lalu ATS, lalu AAS, lalu sisanya."""
    if str(key).isdigit():
        return (0, int(key), '')
    upper = str(key).upper()
    if upper == 'ATS':
        return (1, 0, '')
    if upper == 'AAS':
        return (2, 0, '')
    return (3, 0, upper)


# ── Helper: Section IV (SO-PI table) & Section V (CLO table) ────────────────
def _build_so_pi_and_clo(rps):
    """
    Section IV & Section X: hanya SO-PI yang benar-benar dipakai di RPS ini
    (dirujuk lewat tp_data[].sopi). Deskripsi & Level PI diambil dari
    master data database (levelnya sudah fix per PI di master data, bukan
    input manual per RPS).

    Section V (CLO): dari rps.tp_data, tiap TP jadi 1 baris CLO.
      tp_data: [{'no': 1, 'teks': '...', 'sopi': 'SO1-PI-01.1'}, ...]
      'sopi' bisa berisi 1 atau beberapa kode gabungan (comma-separated),
      di-parse via _parse_sopi_codes() menjadi pi_code murni untuk lookup
      ke master data (mis. 'PI-01.1' -> SO1 / PI 01.1).
    """
    ref = _load_so_pi_data()
    tp_list = rps.tp_data or []

    # PI unik yang benar-benar dipakai di RPS ini, urut kemunculan pertama
    used_pi_codes = []
    for tp in tp_list:
        for code in _parse_sopi_codes(tp.get('sopi')):
            if code not in used_pi_codes:
                used_pi_codes.append(code)

    # Section IV - hanya baris SO-PI yang dipakai, level dari master data
    so_pi_list = []
    for pi_code in used_pi_codes:
        pi_info = ref['pi_map'].get(pi_code)
        if not pi_info:
            continue
        so_pi_list.append({
            'so_code'        : pi_info['so_code'],
            'so_description' : ref['so_map'].get(pi_info['so_code'], ''),
            'pi_code'        : pi_code,
            'pi_description' : pi_info['description'],
            'level'          : pi_info['level'],
            'level_label'    : ref['levels'].get(pi_info['level'], ''),
        })
    so_pi_list.sort(key=lambda r: (r['so_code'], r['pi_code']))

    # Section V - CLO list, urut sesuai input dosen
    # Satu TP bisa merujuk ke lebih dari satu PI, jadi related_sopi/so_code
    # dsb disimpan sebagai list; field tunggal (so_code, pi_description,
    # level) diisi dari PI pertama untuk kompatibilitas tampilan lama.
    # 'pi_details' menyimpan SEMUA PI beserta description & level MASING-
    # MASING (dipakai Section IX supaya tiap PI dapat baris & centang level
    # proficiency sendiri, bukan cuma level PI pertama).
    clo_list = []
    for i, tp in enumerate(tp_list):
        pi_codes = _parse_sopi_codes(tp.get('sopi'))
        pi_infos = [ref['pi_map'][c] for c in pi_codes if c in ref['pi_map']]
        first = pi_infos[0] if pi_infos else {}
        clo_list.append({
            'code'             : f"CLO-{tp.get('no', i + 1)}",
            'description'      : tp.get('teks', ''),
            'related_sopi'     : ', '.join(pi_codes),
            'related_sopi_list': pi_codes,
            'so_code'          : first.get('so_code', ''),
            'so_code_list'     : [pi['so_code'] for pi in pi_infos],
            'pi_description'   : first.get('description', ''),
            'level'            : first.get('level', 1),
            'pi_details'       : [
                {
                    'pi_code'   : c,
                    'so_code'   : ref['pi_map'][c]['so_code'],
                    'description': ref['pi_map'][c]['description'],
                    'level'     : ref['pi_map'][c]['level'],
                }
                for c in pi_codes if c in ref['pi_map']
            ],
        })

    proficiency_levels = [
        {'level': lvl, 'label': label}
        for lvl, label in sorted(ref['levels'].items())
    ]

    # Section IX (Assessment Rubric) - 1 baris per PI (bukan per CLO), supaya
    # CLO yang merujuk 2+ PI dengan level proficiency berbeda tetap tercentang
    # sesuai levelnya masing-masing, tidak numpuk jadi 1 baris/level.
    rubric_rows = []
    for clo in clo_list:
        details = clo['pi_details'] or [{
            'pi_code'    : clo.get('related_sopi', ''),
            'so_code'    : clo.get('so_code', ''),
            'description': clo.get('pi_description', ''),
            'level'      : clo.get('level', 1),
        }]
        for idx, d in enumerate(details):
            rubric_rows.append({
                'clo_code'      : clo['code'],
                'show_clo'      : idx == 0,
                'rowspan'       : len(details),
                'so_code'       : d['so_code'],
                'pi_code'       : d['pi_code'],
                'pi_description': d['description'],
                'level'         : d['level'],
            })

    return so_pi_list, clo_list, proficiency_levels, rubric_rows


# ── Helper: Section X - Student Outcomes Assessment Plan (matrix) ───────────
def _build_so_pi_matrix(rps, so_pi_list):
    """
    Bangun grid SO-PI (baris) x Minggu (kolom) berisi kode asesmen
    (A/Q/MSE/FSE/P/PP) berdasarkan rencana_evaluasi (minggu, tp, metode)
    yang tp-nya merujuk ke tp_data dengan pi_code (sopi) yang sama dengan
    baris SO-PI.

    Catatan penting:
      - 'tp' & 'metode' bisa berisi LEBIH DARI SATU nilai sekaligus, dipisah
        koma (mis. tp="TP1, TP2", metode="A, P, Q") -> harus dipecah semua,
        bukan cuma diambil satu. Kode lama (T/K/ATS/AAS) dipetakan otomatis
        ke label baru oleh _normalize_assessment_code.
      - 'minggu' bisa berupa angka ("1".."14") ATAU label teks masa asesmen
        ("ATS"/"AAS") -> kolomnya tetap harus muncul, bukan cuma yang angka.
    """
    rencana_evaluasi = rps.rencana_evaluasi or []
    tp_by_no = {tp.get('no'): tp for tp in (rps.tp_data or [])}

    week_keys = []
    for ev in rencana_evaluasi:
        key = _normalize_week_key(ev.get('minggu'))
        if key is not None and key not in week_keys:
            week_keys.append(key)
    weeks = sorted(week_keys, key=_week_sort_key)
    if not weeks:
        weeks = [str(w) for w in range(1, 15)]  # hindari list() yang ke-shadow oleh route function `list`

    rows = []
    for so_pi in so_pi_list:
        cells = {w: [] for w in weeks}
        for ev in rencana_evaluasi:
            # eval_tp[] bisa berisi beberapa referensi TP sekaligus ("TP1, TP2")
            tp_refs = _parse_tp_refs(ev.get('tp'))
            matched = any(
                so_pi['pi_code'] in _parse_sopi_codes(tp_by_no[n].get('sopi'))
                for n in tp_refs if n in tp_by_no
            )
            if not matched:
                continue
            wk = _normalize_week_key(ev.get('minggu'))
            if wk not in cells:
                continue
            # eval_metode[] bisa berisi beberapa kode sekaligus ("T, P, K")
            for code in _assessment_codes(ev.get('metode', '')):
                if code not in cells[wk]:
                    cells[wk].append(code)
        rows.append({
            'so_code' : so_pi['so_code'],
            'pi_code' : so_pi['pi_code'],
            'cells'   : {w: ', '.join(codes) for w, codes in cells.items()},
        })

    return {'weeks': weeks, 'rows': rows}


# ── Helper: Export JSON Course (format mengikuti static/data/course_dummy.json) ─
# Field yang belum tersimpan di DB diisi dengan default/template sesuai keputusan:
#   - is_pbl            : default False (tidak pernah disimpan ke DB)
#   - target_attainment : hardcode 60
#   - study_program     : constanta default "RKS"
#   - criteria          : generate 5 level rubrik (score + subjects) dari template
#   - cpl_pis           : kosong (pemetaan sub-komponen -> CPL/SO/PI belum ada di DB)
# Kode PI memakai format proyek (mis. "PI-01.1"), bukan format course_dummy ("1a").
_COURSE_DEFAULT_STUDY_PROGRAM = 'RKS'
_COURSE_DEFAULT_TARGET = 60

# Template rubrik 5 level: (level, label, score_min, score_max)
_COURSE_CRITERIA_TEMPLATE = [
    (1, 'Sangat Kurang',  0,  30),
    (2, 'Kurang',         31, 55),
    (3, 'Cukup',          56, 70),
    (4, 'Baik',           71, 89),
    (5, 'Sangat Baik',    90, 100),
]

_COURSE_CRITERIA_SUBJECTS = {
    1: 'Hasil {name} sangat minim dan tidak sesuai dengan instruksi yang diberikan.',
    2: 'Hasil {name} kurang lengkap dan terdapat banyak kesalahan pada konsep utama.',
    3: 'Hasil {name} cukup baik, konsep dasar dipahami dengan benar.',
    4: 'Hasil {name} lengkap dan dikerjakan dengan baik, analisis benar dan terstruktur.',
    5: 'Hasil {name} sangat sempurna, analisis mendalam, kritis, dan kreatif.',
}


def _parse_sopi_pairs(raw):
    """
    Parse field sopi ("SO1-PI-01.1, SO1-PI-01.2") menjadi pasangan (so_code, pi_code).
    Return list tuple, mis. [('SO1', 'PI-01.1'), ('SO1', 'PI-01.2')].
    """
    pairs = []
    for part in (raw or '').split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            so, pi = part.split('-', 1)
            so, pi = so.strip(), pi.strip()
            if so and pi:
                pairs.append((so, pi))
    return pairs


def _course_criteria(component_name):
    """Generate rubrik 5 level per komponen dari template (data tidak tersimpan)."""
    result = []
    for lvl, label, smin, smax in _COURSE_CRITERIA_TEMPLATE:
        label_lower = label.lower()
        result.append({
            'level'    : lvl,
            'label'    : label,
            'score_min': smin,
            'score_max': smax,
            'subjects' : [
                _COURSE_CRITERIA_SUBJECTS[lvl].format(name=component_name),
                f'Secara keseluruhan dinilai {label_lower}.',
            ],
        })
    return result


def _build_course_json(rps):
    """Bangun dict course JSON mengikuti format static/data/course_dummy.json."""
    mk = rps.matakuliah
    ta = rps.tahun_ajaran

    tp_data = rps.tp_data or []
    kriteria = rps.kriteria_penilaian or []

    # CPL list (dari Tujuan Pembelajaran / CLO)
    cpls = []
    for tp in tp_data:
        so_codes = [so for so, _ in _parse_sopi_pairs(tp.get('sopi'))]
        cpls.append({
            'code'            : f"CPL{tp.get('no')}",
            'description'     : tp.get('teks', ''),
            'proficiency_level': tp.get('level', 1),
            'so_codes'        : sorted(set(so_codes)),
        })

    # Kelompokkan sub-komponen per komponen (urut kemunculan pertama)
    kategori_order = []
    komponen_groups = {}
    for k in kriteria:
        komponen = (k.get('komponen') or '').strip()
        if not komponen:
            continue
        if komponen not in komponen_groups:
            komponen_groups[komponen] = []
            kategori_order.append(komponen)
        komponen_groups[komponen].append(k)

    key_map = {
        'Partisipatif': 'partisipatif',
        'Tugas'       : 'tugas',
        'Kuis'        : 'kuis',
        'ATS'         : 'ats',
        'AAS'         : 'aas',
        'Proyek'      : 'proyek',
    }

    categories = []
    for komponen in kategori_order:
        category_key = key_map.get(komponen, komponen.lower())
        components = []
        for sub in komponen_groups[komponen]:
            name = (sub.get('sub_komponen') or '').strip()
            if not name:
                continue
            try:
                weight = int(float(sub.get('persentase', 0) or 0))
            except (ValueError, TypeError):
                weight = 0
            components.append({
                'name'   : name,
                'weight' : weight,
                'cpl_pis': [],
                'criteria': _course_criteria(name),
            })
        categories.append({
            'key'       : category_key,
            'label'     : komponen,
            'components': components,
        })

    return {
        'course_code'     : mk.kode if mk else '',
        'course_name'     : mk.nama if mk else '',
        'sks'             : rps.sks,
        'semester'        : f"{ta.tahun} {ta.semester}" if ta else '',
        'study_program'   : _COURSE_DEFAULT_STUDY_PROGRAM,
        'is_pbl'          : False,
        'target_attainment': _COURSE_DEFAULT_TARGET,
        'categories'      : categories,
        'cpls'            : cpls,
    }


# ── Helper: Build data untuk PDF ──────────────────────────────────────────────
def _build_rps_data(rps, dosen):
    mk     = rps.matakuliah
    peta   = {}
    for tp in (rps.tp_data or []):
        peta.setdefault(tp.get('level', 1), []).append(tp)

    # Resolusi Tanggal
    tgl_koor_val = format_indo_date(rps.tgl_pengesahan_koor)
    tgl_kaprodi_val = format_indo_date(rps.tgl_pengesahan_kaprodi) or (format_indo_date(mk.tgl_pengesahan_kaprodi) if mk else '')

    # Resolusi QR
    qr_koor_val = rps.qr_dosen_koor
    qr_kaprodi_val = rps.qr_kaprodi or (mk.qr_kaprodi if mk else None)

    # Rencana Mingguan apa adanya — wrapping teks diserahkan ke CSS
    # (table-layout: fixed + word-wrap: break-word) di rps_template.html,
    # bukan manual char-wrap seperti waktu masih pakai xhtml2pdf.
    # NB: pakai list comprehension, bukan list(...), karena ada route
    # function bernama `list` di module ini yang nge-shadow builtin.
    rencana_mingguan_clean = [dict(item) for item in (rps.rencana_mingguan or [])]

    # Format prasyarat dengan nama mata kuliah jika hanya berisi kode
    prasyarat_val = rps.prasyarat or ''
    if prasyarat_val and prasyarat_val != '-':
        items = [x.strip() for x in prasyarat_val.split(',') if x.strip()]
        formatted_prasyarat = []
        for item in items:
            mk_pr = MataKuliah.query.filter((MataKuliah.kode == item) | (MataKuliah.nama == item)).first()
            if mk_pr and mk_pr.nama not in item:
                formatted_prasyarat.append(f"{mk_pr.kode} {mk_pr.nama}")
            else:
                formatted_prasyarat.append(item)
        prasyarat_display = ', '.join(formatted_prasyarat)
    else:
        prasyarat_display = '-'

    # Process Kriteria Penilaian for rowspan merge
    raw_kriteria = rps.kriteria_penilaian or []
    kriteria_processed = []
    i = 0
    while i < len(raw_kriteria):
        item = dict(raw_kriteria[i])
        komponen = item.get('komponen', '')
        count = 1
        j = i + 1
        while j < len(raw_kriteria) and raw_kriteria[j].get('komponen') == komponen:
            count += 1
            j += 1
        
        item['rowspan'] = count
        item['show_komponen'] = True
        kriteria_processed.append(item)

        for k in range(i + 1, j):
            sub_item = dict(raw_kriteria[k])
            sub_item['show_komponen'] = False
            sub_item['rowspan'] = 0
            kriteria_processed.append(sub_item)
        
        i = j

    # Section IV (SO-PI table), Section V (CLO table), footnote proficiency level,
    # Section IX (Assessment Rubric - 1 baris per PI)
    so_pi_list, clo_list, proficiency_levels, rubric_rows = _build_so_pi_and_clo(rps)

    # Section X (Student Outcomes Assessment Plan grid)
    so_pi_matrix = _build_so_pi_matrix(rps, so_pi_list)

    # Section co-requisite: belum ada kolom di model, default '-' sesuai template
    co_requisite = getattr(mk, 'co_requisite', None) or '-'

    return {
        'identitas': {
            'matkul'       : mk.nama if mk else '',
            'kode'         : mk.kode if mk else '',
            'sks'          : rps.sks,
            'semester'     : rps.semester,
            'status'       : (mk.tipe.capitalize() if (mk and mk.tipe) else 'Wajib'),
            'prasyarat'    : prasyarat_display,
            'co_requisite' : co_requisite,
            'dosen'        : dosen.nama if dosen else '',
            'email'        : dosen.email if dosen else '',
        },
        'pengesahan': {
            'tgl_kaprodi'  : tgl_kaprodi_val,
            'tgl_koor'     : tgl_koor_val,
            'disusun_oleh' : dosen.nama if dosen else '',
            'disetujui_oleh': current_app.config.get('KAPRODI_NAMA', 'Maidel Fani'),
        },
        'deskripsi'          : (mk.deskripsi if mk else '') or '',
        'tujuan_peta'        : {
            'tp_list'    : rps.tp_data or [],
            'peta_levels': sorted(peta.keys(), reverse=True),
            'peta_dict'  : peta,
        },
        'so_pi_list'         : so_pi_list,          # Section IV
        'clo_list'           : clo_list,            # Section V
        'proficiency_levels' : proficiency_levels,  # Footnote Section IV/IX
        'rubric_rows'        : rubric_rows,          # Section IX (1 baris per PI)
        'so_pi_matrix'       : so_pi_matrix,         # Section X
        'rencana_mingguan'   : rencana_mingguan_clean,
        'sarana_prasarana'   : rps.sarana_prasarana or [],
        'metode_evaluasi'    : rps.metode_evaluasi or '',
        'rencana_evaluasi'   : rps.rencana_evaluasi or [],
        'kriteria_penilaian' : kriteria_processed,
        'kesepakatan'        : rps.kesepakatan or [],
        'pustaka'            : rps.pustaka or [],
        'qr_dosen_koor'      : qr_koor_val,
        'qr_kaprodi'         : qr_kaprodi_val,
        'tanggal_koor'       : tgl_koor_val,
    }


# ── Route: Editor RPS (Tab-based form) ───────────────────────────────────────
@bp.route('/editor/<int:id>', methods=['GET', 'POST'])
@login_required
def editor(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        if rps.rps_status == 'approved':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from flask import jsonify
                return jsonify({'status': 'error', 'message': 'RPS sudah di-approve, tidak dapat diedit.'}), 403
            flash('RPS sudah di-approve, tidak dapat diedit.', 'warning')
            return redirect(url_for('rps.list'))

        if not current_user.is_kaprodi:
            # Dosen koordinator: hanya boleh mengisi sisanya (tab 3-5).
            # Identitas, Deskripsi, dan Tujuan Pembelajaran (CPL) hanya bisa diisi tim kurikulum.
            cpl_defined = bool(
                rps.tp_data
                and any(tp.get('sopi', '').strip() for tp in rps.tp_data if isinstance(tp, dict))
            )
            if not cpl_defined:
                flash('CPL belum didefinisikan. Kontak tim kurikulum.', 'danger')
                return redirect(url_for('rps.list'))

            rps.semester  = request.form.get('semester',  rps.semester)
            rps.prasyarat = request.form.get('prasyarat', rps.prasyarat)
            _parse_detail_form(rps)
        else:
            # Tim Kurikulum: bisa update SEMUA bagian
            if rps.matakuliah:
                rps.matakuliah.deskripsi = request.form.get('deskripsi', rps.matakuliah.deskripsi)
            _parse_tp_form(rps)
            _parse_detail_form(rps)
            rps.semester  = request.form.get('semester',  rps.semester)
            rps.prasyarat = request.form.get('prasyarat', rps.prasyarat)

        # Handle Tanggal Pengesahan Koordinator (Save directly to DB Column)
        tgl_koor_str = request.form.get('tanggal_koor', '').strip()
        if tgl_koor_str:
            try:
                rps.tgl_pengesahan_koor = datetime.strptime(tgl_koor_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Handle QR Koordinator Upload (Save directly to DB Column)
        qr_file = request.files.get('qr_koor')
        if qr_file and qr_file.filename:
            ext = qr_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg']:
                upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"rps_{rps.id}_qr_{int(time.time())}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                qr_file.save(filepath)
                
                # Simpan ke kolom DB
                rps.qr_dosen_koor = filename

        rps.rps_status = 'submitted'
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from flask import jsonify
            return jsonify({'status': 'success', 'message': 'Draft tersimpan otomatis'})

        if current_user.is_kaprodi:
            flash('Data RPS berhasil disimpan!', 'success')
        else:
            flash('RPS berhasil disimpan dan telah dikirim untuk review. Menunggu approval dari Kaprodi/Tim Kurikulum.', 'success')
        return redirect(url_for('rps.list'))

    cpl_defined = bool(
        rps.tp_data
        and any(tp.get('sopi', '').strip() for tp in rps.tp_data if isinstance(tp, dict))
    )

    return render_template(
        'rps_editor.html',
        matkul=rps,
        readonly=current_user.is_kaprodi,
        hitung_progress_rps=hitung_progress_rps,
        cpl_defined=cpl_defined,
        is_approved=(rps.rps_status == 'approved'),
    )





# ── Route: Preview RPS ────────────────────────────────────────────────────────
@bp.route('/preview/<int:id>')
@login_required
def preview(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not (rps.rencana_mingguan or rps.sarana_prasarana or rps.rencana_evaluasi
            or rps.kriteria_penilaian or rps.kesepakatan or rps.pustaka or rps.tp_data):
        flash('RPS belum diisi.', 'warning')
        return redirect(url_for('rps.list'))

    dosen    = User.query.get(rps.user_id)
    rps_data = _build_rps_data(rps, dosen)
    return render_template('rps_template.html', data=rps_data)


# ── Route: Export RPS Approved ke JSON (format course_dummy.json) ────────────
@bp.route('/<int:id>/export-json')
@login_required
def export_json(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if rps.rps_status != 'approved':
        flash('Export JSON hanya tersedia untuk RPS yang sudah di-approve.', 'warning')
        return redirect(url_for('rps.list'))

    from flask import jsonify
    data = _build_course_json(rps)

    mk = rps.matakuliah
    filename = secure_filename(f"{mk.kode if mk else rps.id}_{rps.id}.json")
    response = jsonify(data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


# ── Route: View QR Koordinator ────────────────────────────────────────────────
@bp.route('/<int:id>/qr')
@login_required
def view_qr(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not rps.qr_dosen_koor:
        abort(404)

    upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
    return send_from_directory(upload_dir, rps.qr_dosen_koor)


# ── Route: Serve file QR generik (dipakai rps_template.html: qr_dosen_koor & qr_kaprodi) ──
@bp.route('/qr-file/<path:filename>')
@login_required
def qr_file(filename):
    qr_dir = os.path.join(current_app.root_path, 'storage', 'qr')
    return send_from_directory(qr_dir, filename)