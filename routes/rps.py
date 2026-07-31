from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from extensions import db
from models import RPS, MataKuliah, User, TahunAjaran
from sqlalchemy import or_
from utils.decorators import kaprodi_required
from xhtml2pdf import pisa
from io import BytesIO
import os
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


# ── Helper: Parse form ke model RPS ──────────────────────────────────────────
def _parse_rps_form(rps):
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

    old_qr_koor = rps.rps_detail.get('qr_koor') if rps.rps_detail else None

    rps.rps_detail = {
        'rencana_mingguan'  : rencana_mingguan,
        'sarana_prasarana'  : sarana,
        'metode_evaluasi'   : request.form.get('metode_evaluasi', ''),
        'rencana_evaluasi'  : rencana_evaluasi,
        'kriteria_penilaian': kriteria,
        'kesepakatan'       : [k for k in request.form.getlist('kesepakatan[]') if k.strip()],
        'pustaka'           : [p for p in request.form.getlist('pustaka[]')     if p.strip()],
        'qr_koor'           : old_qr_koor,
        'tanggal_koor'      : request.form.get('tanggal_koor', ''),
    }


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


# ── Helper: Build data untuk PDF ──────────────────────────────────────────────
def _build_rps_data(rps, dosen):
    mk     = rps.matakuliah
    peta   = {}
    for tp in (rps.tp_data or []):
        peta.setdefault(tp.get('level', 1), []).append(tp)

    detail = rps.rps_detail or {}

    # Resolusi Tanggal
    tgl_koor_val = format_indo_date(rps.tgl_pengesahan_koor) or detail.get('tanggal_koor', '')
    tgl_kaprodi_val = format_indo_date(rps.tgl_pengesahan_kaprodi) or (format_indo_date(mk.tgl_pengesahan_kaprodi) if mk else '')

    # Resolusi QR
    qr_koor_val = rps.qr_dosen_koor or detail.get('qr_koor')
    qr_kaprodi_val = rps.qr_kaprodi or (mk.qr_kaprodi if mk else None)

    # Process Rencana Mingguan to prevent text overflow in xhtml2pdf
    rencana_mingguan_clean = []
    for item in detail.get('rencana_mingguan', []):
        m_copy = dict(item)
        for key, max_l in [
            ('minggu', 5), ('tp_ref', 8), ('kemampuan', 12),
            ('bahan_kajian', 14), ('sub_bahan', 15), ('modalitas', 12),
            ('waktu', 8), ('pengalaman', 8)
        ]:
            if key in m_copy and m_copy[key]:
                m_copy[key] = auto_wrap_text(str(m_copy[key]), max_len=max_l)
        rencana_mingguan_clean.append(m_copy)

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
    raw_kriteria = detail.get('kriteria_penilaian', [])
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

    return {
        'identitas': {
            'matkul'   : mk.nama if mk else '',
            'kode'     : mk.kode if mk else '',
            'sks'      : rps.sks,
            'semester' : rps.semester,
            'status'   : (mk.tipe.capitalize() if (mk and mk.tipe) else 'Wajib'),
            'prasyarat': prasyarat_display,
            'dosen'    : dosen.nama if dosen else '',
            'email'    : dosen.email if dosen else '',
        },
        'pengesahan': {
            'tgl_kaprodi'  : tgl_kaprodi_val,
            'tgl_koor'     : tgl_koor_val,
            'disusun_oleh' : dosen.nama if dosen else '',
        },
        'deskripsi'          : (mk.deskripsi if mk else '') or '',
        'tujuan_peta'        : {
            'tp_list'    : rps.tp_data or [],
            'peta_levels': sorted(peta.keys(), reverse=True),
            'peta_dict'  : peta,
        },
        'rencana_mingguan'   : rencana_mingguan_clean,
        'sarana_prasarana'   : detail.get('sarana_prasarana',    []),
        'metode_evaluasi'    : detail.get('metode_evaluasi',     ''),
        'rencana_evaluasi'   : detail.get('rencana_evaluasi',    []),
        'kriteria_penilaian' : kriteria_processed,
        'kesepakatan'        : detail.get('kesepakatan',         []),
        'pustaka'            : detail.get('pustaka',             []),
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
        if current_user.is_kaprodi:
            abort(403)

        rps.semester  = request.form.get('semester',  rps.semester)
        rps.prasyarat = request.form.get('prasyarat', rps.prasyarat)
        if rps.matakuliah:
            rps.matakuliah.deskripsi = request.form.get('deskripsi', rps.matakuliah.deskripsi)

        _parse_rps_form(rps)

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

                # Update json juga demi kompatibilitas
                if rps.rps_detail:
                    detail = rps.rps_detail.copy()
                    detail['qr_koor'] = filename
                    rps.rps_detail = detail

        rps.rps_status = 'submitted'
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from flask import jsonify
            return jsonify({'status': 'success', 'message': 'Draft tersimpan otomatis'})

        flash('Data RPS berhasil disimpan!', 'success')
        return redirect(url_for('rps.list'))

    return render_template('rps_editor.html', matkul=rps, readonly=current_user.is_kaprodi, hitung_progress_rps=hitung_progress_rps)


# ── Route: Download PDF ───────────────────────────────────────────────────────
@bp.route('/download/<int:id>')
@login_required
def download(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not rps.rps_detail:
        flash('Silakan isi form RPS terlebih dahulu!', 'danger')
        return redirect(url_for('rps.list'))

    dosen    = User.query.get(rps.user_id)
    rps_data = _build_rps_data(rps, dosen)

    buf = BytesIO()
    pisa.CreatePDF(render_template('rps_template.html', data=rps_data), dest=buf)
    buf.seek(0)

    resp = make_response(buf.read())
    resp.headers['Content-Type']        = 'application/pdf'
    resp.headers['Content-Disposition'] = f'inline; filename=RPS_{rps.matakuliah.kode}.pdf'
    return resp


# ── Route: Preview RPS ────────────────────────────────────────────────────────
@bp.route('/preview/<int:id>')
@login_required
def preview(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not rps.rps_detail:
        flash('RPS belum diisi.', 'warning')
        return redirect(url_for('rps.list'))

    dosen    = User.query.get(rps.user_id)
    rps_data = _build_rps_data(rps, dosen)
    return render_template('rps_template.html', data=rps_data)


# ── Route: View QR Koordinator ────────────────────────────────────────────────
@bp.route('/<int:id>/qr')
@login_required
def view_qr(id):
    if current_user.is_kaprodi:
        rps = RPS.query.get_or_404(id)
    else:
        rps = RPS.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if not rps.rps_detail or not rps.rps_detail.get('qr_koor'):
        abort(404)

    upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
    return send_from_directory(upload_dir, rps.rps_detail.get('qr_koor'))