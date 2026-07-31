from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import MataKuliah
from sqlalchemy import or_
from utils.decorators import kaprodi_required
from datetime import datetime
import os
import time

bp = Blueprint('matakuliah', __name__, url_prefix='/matakuliah')


PER_PAGE = 10

@bp.route('/')
@login_required
def list():
    q          = request.args.get('q',         '').strip()
    kurikulum  = request.args.get('kurikulum', '').strip()
    page       = request.args.get('page', 1, type=int)

    query = MataKuliah.query
    if q:
        query = query.filter(
            or_(
                MataKuliah.kode.ilike(f'%{q}%'),
                MataKuliah.nama.ilike(f'%{q}%'),
            )
        )
    if kurikulum:
        query = query.filter(MataKuliah.kurikulum == kurikulum)

    pagination = query.order_by(MataKuliah.kode.asc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )

    # Daftar kurikulum unik untuk dropdown filter
    kurikulum_list = [
        r[0] for r in db.session.query(MataKuliah.kurikulum)
        .filter(MataKuliah.kurikulum.isnot(None))
        .distinct()
        .order_by(MataKuliah.kurikulum.asc())
        .all()
    ]

    return render_template(
        'matakuliah/list.html',
        matkuls=pagination.items,
        pagination=pagination,
        q=q,
        kurikulum=kurikulum,
        kurikulum_list=kurikulum_list,
    )


@bp.route('/add', methods=['POST'])
@login_required
@kaprodi_required
def add():
    kode  = request.form.get('kode',      '').strip()
    nama  = request.form.get('nama',      '').strip()
    kurik = request.form.get('kurikulum', '').strip()
    desk  = request.form.get('deskripsi', '').strip()
    tipe  = request.form.get('tipe',      'wajib').strip()

    tgl_str = request.form.get('tgl_pengesahan_kaprodi', '').strip()
    tgl_kaprodi = None
    if tgl_str:
        try:
            tgl_kaprodi = datetime.strptime(tgl_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if not kode or not nama:
        flash('Kode dan Nama mata kuliah wajib diisi.', 'danger')
        return redirect(url_for('matakuliah.list'))

    if MataKuliah.query.filter_by(kode=kode, kurikulum=kurik).first():
        flash(f'Kode "{kode}" dengan kurikulum "{kurik or "-"}" sudah terdaftar.', 'danger')
        return redirect(url_for('matakuliah.list'))

    mk = MataKuliah(
        kode=kode,
        nama=nama,
        kurikulum=kurik,
        deskripsi=desk,
        tipe=tipe,
        tgl_pengesahan_kaprodi=tgl_kaprodi
    )

    qr_file = request.files.get('qr_kaprodi')
    if qr_file and qr_file.filename:
        ext = qr_file.filename.rsplit('.', 1)[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"kaprodi_qr_{int(time.time())}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            qr_file.save(filepath)
            mk.qr_kaprodi = filename

    db.session.add(mk)
    db.session.commit()
    flash('Mata kuliah berhasil ditambahkan ke katalog!', 'success')
    return redirect(url_for('matakuliah.list'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def edit(id):
    mk = MataKuliah.query.get_or_404(id)

    kode = request.form.get('kode', '').strip()
    if not kode or not request.form.get('nama', '').strip():
        flash('Kode dan Nama wajib diisi.', 'danger')
        return redirect(url_for('matakuliah.list'))

    kurik_edit = request.form.get('kurikulum', '').strip()
    existing = MataKuliah.query.filter(
        MataKuliah.kode == kode,
        MataKuliah.kurikulum == (kurik_edit or None),
        MataKuliah.id != id
    ).first()
    if existing:
        flash(f'Kode "{kode}" dengan kurikulum "{kurik_edit or "-"}" sudah dipakai MK lain.', 'danger')
        return redirect(url_for('matakuliah.list'))

    mk.kode      = kode
    mk.nama      = request.form.get('nama', '').strip()
    mk.kurikulum = kurik_edit
    mk.deskripsi = request.form.get('deskripsi', '').strip()
    mk.tipe      = request.form.get('tipe', 'wajib').strip()

    tgl_str = request.form.get('tgl_pengesahan_kaprodi', '').strip()
    if tgl_str:
        try:
            mk.tgl_pengesahan_kaprodi = datetime.strptime(tgl_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    qr_file = request.files.get('qr_kaprodi')
    if qr_file and qr_file.filename:
        ext = qr_file.filename.rsplit('.', 1)[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            upload_dir = os.path.join(current_app.root_path, 'storage', 'qr')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"kaprodi_mk_{id}_qr_{int(time.time())}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            qr_file.save(filepath)
            mk.qr_kaprodi = filename

    db.session.commit()
    flash('Mata kuliah berhasil diperbarui!', 'success')
    return redirect(url_for('matakuliah.list'))


@bp.route('/delete/<int:id>')
@login_required
@kaprodi_required
def delete(id):
    mk = MataKuliah.query.get_or_404(id)
    if mk.rps_list:
        flash('Mata kuliah ini masih memiliki RPS terkait, tidak dapat dihapus.', 'danger')
        return redirect(url_for('matakuliah.list'))
    db.session.delete(mk)
    db.session.commit()
    flash('Mata kuliah berhasil dihapus dari katalog.', 'success')
    return redirect(url_for('matakuliah.list'))


@bp.route('/search')
@login_required
def search():
    """API endpoint: cari MK untuk autocomplete di form tambah RPS."""
    from flask import jsonify
    q = request.args.get('q', '').strip()
    results = MataKuliah.query.filter(
        or_(
            MataKuliah.kode.ilike(f'%{q}%'),
            MataKuliah.nama.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    return jsonify([
        {'id': m.id, 'kode': m.kode, 'nama': m.nama, 'sks': m.sks or 3, 'kurikulum': m.kurikulum or ''}
        for m in results
    ])