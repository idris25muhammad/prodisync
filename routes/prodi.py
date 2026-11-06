from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Prodi, User, MataKuliah, RPS
from utils.decorators import kajur_required

bp = Blueprint('prodi', __name__, url_prefix='/prodi')


@bp.route('/')
@login_required
@kajur_required
def list():
    prodis = Prodi.query.order_by(Prodi.kode.asc()).all()
    # Daftar dosen yang dapat dipilih sebagai Kaprodi
    dosen_list = User.query.filter(User.role.in_(['dosen', 'kaprodi'])).order_by(User.nama.asc()).all()
    return render_template('prodi/list.html', prodis=prodis, dosen_list=dosen_list)


@bp.route('/add', methods=['POST'])
@login_required
@kajur_required
def add():
    kode = request.form.get('kode', '').strip().upper()
    nama = request.form.get('nama', '').strip()
    jenjang = request.form.get('jenjang', 'D4').strip().upper()
    kaprodi_id = request.form.get('kaprodi_id', type=int)

    if not kode or not nama:
        flash('Kode dan Nama Program Studi wajib diisi.', 'danger')
        return redirect(url_for('prodi.list'))

    if Prodi.query.filter_by(kode=kode).first():
        flash(f'Program Studi dengan kode "{kode}" sudah ada.', 'danger')
        return redirect(url_for('prodi.list'))

    prodi = Prodi(
        kode=kode,
        nama=nama,
        jenjang=jenjang,
        kaprodi_id=kaprodi_id or None,
        is_aktif=True
    )
    db.session.add(prodi)
    db.session.flush()

    # Jika kaprodi ditunjuk, perbarui role user dan prodi_id-nya
    if kaprodi_id:
        user_kaprodi = User.query.get(kaprodi_id)
        if user_kaprodi:
            user_kaprodi.role = 'kaprodi'
            user_kaprodi.prodi_id = prodi.id

    db.session.commit()
    flash(f'Program Studi {kode} - {nama} berhasil ditambahkan!', 'success')
    return redirect(url_for('prodi.list'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kajur_required
def edit(id):
    prodi = Prodi.query.get_or_404(id)
    kode = request.form.get('kode', '').strip().upper()
    nama = request.form.get('nama', '').strip()
    jenjang = request.form.get('jenjang', 'D4').strip().upper()
    kaprodi_id = request.form.get('kaprodi_id', type=int)

    if not kode or not nama:
        flash('Kode dan Nama Program Studi wajib diisi.', 'danger')
        return redirect(url_for('prodi.list'))

    existing = Prodi.query.filter(Prodi.kode == kode, Prodi.id != id).first()
    if existing:
        flash(f'Kode "{kode}" sudah digunakan program studi lain.', 'danger')
        return redirect(url_for('prodi.list'))

    prodi.kode = kode
    prodi.nama = nama
    prodi.jenjang = jenjang

    old_kaprodi_id = prodi.kaprodi_id
    prodi.kaprodi_id = kaprodi_id or None

    # Update role user kaprodi baru jika ada perubahan
    if kaprodi_id and kaprodi_id != old_kaprodi_id:
        new_kaprodi = User.query.get(kaprodi_id)
        if new_kaprodi:
            new_kaprodi.role = 'kaprodi'
            new_kaprodi.prodi_id = prodi.id

    db.session.commit()
    flash(f'Program Studi {kode} berhasil diperbarui.', 'success')
    return redirect(url_for('prodi.list'))


@bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@kajur_required
def toggle(id):
    prodi = Prodi.query.get_or_404(id)
    prodi.is_aktif = not prodi.is_aktif
    db.session.commit()
    status_str = 'diaktifkan' if prodi.is_aktif else 'dinonaktifkan'
    flash(f'Program Studi {prodi.kode} berhasil {status_str}.', 'info')
    return redirect(url_for('prodi.list'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@kajur_required
def delete(id):
    prodi = Prodi.query.get_or_404(id)

    # Validasi relasi
    total_mk = MataKuliah.query.filter_by(prodi_id=id).count()
    total_rps = RPS.query.filter_by(prodi_id=id).count()
    total_dosen = User.query.filter_by(prodi_id=id).count()

    if total_mk > 0 or total_rps > 0 or total_dosen > 0:
        flash(f'Program Studi {prodi.kode} tidak dapat dihapus karena masih memiliki data terkait ({total_mk} MK, {total_rps} RPS, {total_dosen} Dosen). Silakan nonaktifkan saja.', 'danger')
        return redirect(url_for('prodi.list'))

    db.session.delete(prodi)
    db.session.commit()
    flash(f'Program Studi {prodi.kode} berhasil dihapus.', 'success')
    return redirect(url_for('prodi.list'))
