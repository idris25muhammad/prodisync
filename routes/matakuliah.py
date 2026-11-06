from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import MataKuliah, Prodi
from sqlalchemy import or_
from utils.decorators import kaprodi_required, kurikulum_required

bp = Blueprint('matakuliah', __name__, url_prefix='/matakuliah')


PER_PAGE = 10

@bp.route('/')
@login_required
def list():
    q          = request.args.get('q',         '').strip()
    kurikulum  = request.args.get('kurikulum', '').strip()
    prodi_id   = request.args.get('prodi_id', type=int)
    page       = request.args.get('page', 1, type=int)

    query = MataKuliah.query
    if not current_user.is_kajur:
        user_prodi = getattr(current_user, 'prodi_id', None) or 1
        query = query.filter(MataKuliah.prodi_id == user_prodi)
    elif prodi_id:
        query = query.filter(MataKuliah.prodi_id == prodi_id)

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
    prodi_list = Prodi.query.filter_by(is_aktif=True).order_by(Prodi.nama.asc()).all()

    return render_template(
        'matakuliah/list.html',
        matkuls=pagination.items,
        pagination=pagination,
        q=q,
        kurikulum=kurikulum,
        kurikulum_list=kurikulum_list,
        prodi_list=prodi_list,
        prodi_id=prodi_id,
    )


@bp.route('/add', methods=['POST'])
@login_required
@kurikulum_required
def add():
    kode     = request.form.get('kode',      '').strip()
    nama     = request.form.get('nama',      '').strip()
    kurik    = request.form.get('kurikulum', '').strip()
    desk     = request.form.get('deskripsi', '').strip()
    tipe     = request.form.get('tipe',      'wajib').strip()
    sks      = request.form.get('sks', type=int) or None
    if not current_user.is_kajur:
        prodi_id = getattr(current_user, 'prodi_id', None) or 1
    else:
        prodi_id = request.form.get('prodi_id', type=int) or getattr(current_user, 'prodi_id', None) or 1

    if not kode or not nama:
        flash('Kode dan Nama mata kuliah wajib diisi.', 'danger')
        return redirect(url_for('matakuliah.list'))

    if MataKuliah.query.filter_by(prodi_id=prodi_id, kode=kode, kurikulum=kurik).first():
        flash(f'Kode "{kode}" dengan kurikulum "{kurik or "-"}" sudah terdaftar di prodi ini.', 'danger')
        return redirect(url_for('matakuliah.list'))

    mk = MataKuliah(
        prodi_id=prodi_id,
        kode=kode,
        nama=nama,
        kurikulum=kurik,
        deskripsi=desk,
        tipe=tipe,
        sks=sks,
    )

    db.session.add(mk)
    db.session.commit()
    flash('Mata kuliah berhasil ditambahkan ke katalog!', 'success')
    return redirect(url_for('matakuliah.list'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kurikulum_required
def edit(id):
    mk = MataKuliah.query.get_or_404(id)
    if not current_user.is_kajur and mk.prodi_id != getattr(current_user, 'prodi_id', None):
        flash('Anda hanya dapat mengelola mata kuliah dari program studi Anda sendiri.', 'danger')
        return redirect(url_for('matakuliah.list'))

    kode = request.form.get('kode', '').strip()
    if not kode or not request.form.get('nama', '').strip():
        flash('Kode dan Nama wajib diisi.', 'danger')
        return redirect(url_for('matakuliah.list'))

    kurik_edit = request.form.get('kurikulum', '').strip()
    existing = MataKuliah.query.filter(
        MataKuliah.prodi_id == mk.prodi_id,
        MataKuliah.kode == kode,
        MataKuliah.kurikulum == (kurik_edit or None),
        MataKuliah.id != id
    ).first()
    if existing:
        flash(f'Kode "{kode}" dengan kurikulum "{kurik_edit or "-"}" sudah dipakai MK lain di prodi ini.', 'danger')
        return redirect(url_for('matakuliah.list'))

    mk.kode      = kode
    mk.nama      = request.form.get('nama', '').strip()
    mk.kurikulum = kurik_edit
    mk.deskripsi = request.form.get('deskripsi', '').strip()
    mk.tipe      = request.form.get('tipe', 'wajib').strip()
    mk.sks       = request.form.get('sks', type=int) or None

    db.session.commit()
    flash('Mata kuliah berhasil diperbarui!', 'success')
    return redirect(url_for('matakuliah.list'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@kurikulum_required
def delete(id):
    mk = MataKuliah.query.get_or_404(id)
    if not current_user.is_kajur and mk.prodi_id != getattr(current_user, 'prodi_id', None):
        flash('Anda hanya dapat mengelola mata kuliah dari program studi Anda sendiri.', 'danger')
        return redirect(url_for('matakuliah.list'))

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
    query = MataKuliah.query
    if not current_user.is_kajur:
        user_prodi = getattr(current_user, 'prodi_id', None) or 1
        query = query.filter(MataKuliah.prodi_id == user_prodi)
    results = query.filter(
        or_(
            MataKuliah.kode.ilike(f'%{q}%'),
            MataKuliah.nama.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    return jsonify([
        {'id': m.id, 'kode': m.kode, 'nama': m.nama, 'sks': m.sks or 3, 'kurikulum': m.kurikulum or ''}
        for m in results
    ])