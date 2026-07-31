from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from extensions import db
from models import User
from utils.decorators import role_required


bp = Blueprint('user', __name__, url_prefix='/users')
ph = PasswordHasher()


@bp.route('/')
@login_required
@role_required('kaprodi')
def list():
    users = User.query.order_by(User.role.asc(), User.nama.asc()).all()
    return render_template('users.html', users=users)


@bp.route('/add', methods=['POST'])
@login_required
@role_required('kaprodi')
def add():
    nama = request.form.get('nama', '').strip()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'dosen').strip()

    nidn = request.form.get('nidn', '').strip()
    nip = request.form.get('nip', '').strip()
    sinta_id = request.form.get('sinta_id', '').strip()
    google_scholar_id = request.form.get('google_scholar_id', '').strip()
    google_scholar_url = request.form.get('google_scholar_url', '').strip()
    orcid_id = request.form.get('orcid_id', '').strip()
    scopus_id = request.form.get('scopus_id', '').strip()
    researcher_id = request.form.get('researcher_id', '').strip()
    garuda_id = request.form.get('garuda_id', '').strip()
    afiliasi = request.form.get('afiliasi', '').strip()
    prodi = request.form.get('prodi', '').strip()
    jabatan_fungsional = request.form.get('jabatan_fungsional', '').strip()
    bidang_keahlian = request.form.get('bidang_keahlian', '').strip()
    homepage_url = request.form.get('homepage_url', '').strip()
    foto_url = request.form.get('foto_url', '').strip()

    if not nama or not username or not password:
        flash('Nama, username, dan password wajib diisi.', 'danger')
        return redirect(url_for('user.list'))

    if role not in ['dosen', 'kaprodi']:
        flash('Role tidak valid.', 'danger')
        return redirect(url_for('user.list'))

    if User.query.filter_by(username=username).first():
        flash('Username sudah digunakan.', 'danger')
        return redirect(url_for('user.list'))

    if email and User.query.filter_by(email=email).first():
        flash('Email sudah digunakan.', 'danger')
        return redirect(url_for('user.list'))

    if nidn and User.query.filter_by(nidn=nidn).first():
        flash('NIDN sudah digunakan.', 'danger')
        return redirect(url_for('user.list'))

    if nip and User.query.filter_by(nip=nip).first():
        flash('NIP sudah digunakan.', 'danger')
        return redirect(url_for('user.list'))

    user = User(
        nama=nama,
        username=username,
        email=email or None,
        password=ph.hash(password),
        role=role,
        nidn=nidn or None,
        nip=nip or None,
        sinta_id=sinta_id or None,
        google_scholar_id=google_scholar_id or None,
        google_scholar_url=google_scholar_url or None,
        orcid_id=orcid_id or None,
        scopus_id=scopus_id or None,
        researcher_id=researcher_id or None,
        garuda_id=garuda_id or None,
        afiliasi=afiliasi or None,
        prodi=prodi or None,
        jabatan_fungsional=jabatan_fungsional or None,
        bidang_keahlian=bidang_keahlian or None,
        homepage_url=homepage_url or None,
        foto_url=foto_url or None,
    )

    db.session.add(user)
    db.session.commit()

    flash(f'Akun {nama} berhasil ditambahkan.', 'success')
    return redirect(url_for('user.list'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@role_required('kaprodi')
def edit(id):
    user = User.query.get_or_404(id)

    nama = request.form.get('nama', '').strip()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'dosen').strip()

    nidn = request.form.get('nidn', '').strip()
    nip = request.form.get('nip', '').strip()
    sinta_id = request.form.get('sinta_id', '').strip()
    google_scholar_id = request.form.get('google_scholar_id', '').strip()
    google_scholar_url = request.form.get('google_scholar_url', '').strip()
    orcid_id = request.form.get('orcid_id', '').strip()
    scopus_id = request.form.get('scopus_id', '').strip()
    researcher_id = request.form.get('researcher_id', '').strip()
    garuda_id = request.form.get('garuda_id', '').strip()
    afiliasi = request.form.get('afiliasi', '').strip()
    prodi = request.form.get('prodi', '').strip()
    jabatan_fungsional = request.form.get('jabatan_fungsional', '').strip()
    bidang_keahlian = request.form.get('bidang_keahlian', '').strip()
    homepage_url = request.form.get('homepage_url', '').strip()
    foto_url = request.form.get('foto_url', '').strip()

    if not nama or not username:
        flash('Nama dan username wajib diisi.', 'danger')
        return redirect(url_for('user.list'))

    if role not in ['dosen', 'kaprodi']:
        flash('Role tidak valid.', 'danger')
        return redirect(url_for('user.list'))

    username_owner = User.query.filter(User.username == username, User.id != id).first()
    if username_owner:
        flash('Username sudah digunakan user lain.', 'danger')
        return redirect(url_for('user.list'))

    if email:
        email_owner = User.query.filter(User.email == email, User.id != id).first()
        if email_owner:
            flash('Email sudah digunakan user lain.', 'danger')
            return redirect(url_for('user.list'))

    if nidn:
        nidn_owner = User.query.filter(User.nidn == nidn, User.id != id).first()
        if nidn_owner:
            flash('NIDN sudah digunakan user lain.', 'danger')
            return redirect(url_for('user.list'))

    if nip:
        nip_owner = User.query.filter(User.nip == nip, User.id != id).first()
        if nip_owner:
            flash('NIP sudah digunakan user lain.', 'danger')
            return redirect(url_for('user.list'))

    if current_user.id == user.id and role != 'kaprodi':
        flash('Anda tidak bisa menurunkan role akun sendiri.', 'danger')
        return redirect(url_for('user.list'))

    user.nama = nama
    user.username = username
    user.email = email or None
    user.role = role
    user.nidn = nidn or None
    user.nip = nip or None
    user.sinta_id = sinta_id or None
    user.google_scholar_id = google_scholar_id or None
    user.google_scholar_url = google_scholar_url or None
    user.orcid_id = orcid_id or None
    user.scopus_id = scopus_id or None
    user.researcher_id = researcher_id or None
    user.garuda_id = garuda_id or None
    user.afiliasi = afiliasi or None
    user.prodi = prodi or None
    user.jabatan_fungsional = jabatan_fungsional or None
    user.bidang_keahlian = bidang_keahlian or None
    user.homepage_url = homepage_url or None
    user.foto_url = foto_url or None

    db.session.commit()
    flash(f'Data user {user.nama} berhasil diperbarui.', 'success')
    return redirect(url_for('user.list'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required('kaprodi')
def delete(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Anda tidak bisa menghapus akun sendiri.', 'danger')
        return redirect(url_for('user.list'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Akun {user.nama} berhasil dihapus.', 'success')
    return redirect(url_for('user.list'))


@bp.route('/reset-password/<int:id>', methods=['POST'])
@login_required
@role_required('kaprodi')
def reset_password(id):
    user = User.query.get_or_404(id)
    new_password = request.form.get('password', '').strip()

    if not new_password or len(new_password) < 6:
        flash('Password baru minimal 6 karakter.', 'danger')
        return redirect(url_for('user.list'))

    user.password = ph.hash(new_password)
    db.session.commit()

    flash(f'Password untuk {user.nama} berhasil direset.', 'success')
    return redirect(url_for('user.list'))


@bp.route('/ganti-password', methods=['GET', 'POST'])
@login_required
def ganti_password():
    if request.method == 'POST':
        password_lama = request.form.get('password_lama', '').strip()
        password_baru = request.form.get('password_baru', '').strip()
        konfirmasi_password = request.form.get('konfirmasi_password', '').strip()

        if not password_lama or not password_baru or not konfirmasi_password:
            flash('Semua field wajib diisi.', 'danger')
            return redirect(url_for('user.ganti_password'))

        try:
            ph.verify(current_user.password, password_lama)
        except VerifyMismatchError:
            flash('Password lama salah.', 'danger')
            return redirect(url_for('user.ganti_password'))

        if password_baru != konfirmasi_password:
            flash('Password baru dan konfirmasi tidak cocok.', 'danger')
            return redirect(url_for('user.ganti_password'))

        if len(password_baru) < 6:
            flash('Password baru minimal 6 karakter.', 'danger')
            return redirect(url_for('user.ganti_password'))

        current_user.password = ph.hash(password_baru)
        db.session.commit()

        flash('Password berhasil diubah.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('ganti_password.html')


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Data Pribadi
        current_user.nama = request.form.get('nama', '').strip()
        current_user.email = request.form.get('email', '').strip() or None
        current_user.foto_url = request.form.get('foto_url', '').strip() or None
        
        # Identitas Akademik
        current_user.nidn = request.form.get('nidn', '').strip() or None
        current_user.nip = request.form.get('nip', '').strip() or None
        current_user.afiliasi = request.form.get('afiliasi', '').strip() or None
        current_user.prodi = request.form.get('prodi', '').strip() or None
        current_user.jabatan_fungsional = request.form.get('jabatan_fungsional', '').strip() or None
        current_user.bidang_keahlian = request.form.get('bidang_keahlian', '').strip() or None
        
        # Publikasi & ID
        current_user.sinta_id = request.form.get('sinta_id', '').strip() or None
        current_user.google_scholar_id = request.form.get('google_scholar_id', '').strip() or None
        current_user.google_scholar_url = request.form.get('google_scholar_url', '').strip() or None
        current_user.orcid_id = request.form.get('orcid_id', '').strip() or None
        current_user.scopus_id = request.form.get('scopus_id', '').strip() or None
        current_user.researcher_id = request.form.get('researcher_id', '').strip() or None
        current_user.garuda_id = request.form.get('garuda_id', '').strip() or None
        current_user.homepage_url = request.form.get('homepage_url', '').strip() or None

        db.session.commit()
        flash('Profil berhasil diperbarui.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('profile.html')