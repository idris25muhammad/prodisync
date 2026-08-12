from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import ArsipDokumen, User
from utils.decorators import kaprodi_required

bp = Blueprint('arsip', __name__, url_prefix='/arsip')


@bp.route('/')
@login_required
def list():
    q = request.args.get('q', '').strip()

    query = ArsipDokumen.query

    if q:
        query = query.filter(ArsipDokumen.nama.ilike(f'%{q}%'))

    semua_arsip_raw = query.order_by(ArsipDokumen.updated_at.desc()).all()

    # Filter visible items based on permissions
    semua_arsip = []
    for item in semua_arsip_raw:
        if current_user.is_kaprodi or item.uploader_id == current_user.id:
            semua_arsip.append(item)
        elif item.is_aktif:
            if item.akses_tipe == 'semua':
                semua_arsip.append(item)
            elif item.akses_tipe == 'custom':
                if current_user in item.allowed_users:
                    semua_arsip.append(item)

    all_users = User.query.order_by(User.nama.asc()).all()

    return render_template(
        'arsip/list.html',
        semua_arsip=semua_arsip,
        all_users=all_users,
        q=q
    )


@bp.route('/index')
@login_required
def index():
    return redirect(url_for('arsip.list'))


@bp.route('/add', methods=['POST'])
@login_required
@kaprodi_required
def add():
    nama       = request.form.get('nama', '').strip()
    link_url   = request.form.get('link_url', '').strip()
    akses_tipe = request.form.get('akses_tipe', 'semua').strip()
    is_aktif   = request.form.get('is_aktif', 'true') == 'true'
    user_ids   = request.form.getlist('allowed_user_ids')

    if not nama or not link_url:
        flash('Nama dokumen dan Link Tautan URL wajib diisi!', 'danger')
        return redirect(url_for('arsip.list'))

    try:
        baru_arsip = ArsipDokumen(
            nama=nama,
            link_url=link_url,
            akses_tipe=akses_tipe,
            is_aktif=is_aktif,
            uploader_id=current_user.id
        )

        if akses_tipe == 'custom' and user_ids:
            valid_users = User.query.filter(User.id.in_([int(uid) for uid in user_ids if uid.isdigit()])).all()
            baru_arsip.allowed_users.extend(valid_users)

        db.session.add(baru_arsip)
        db.session.commit()
        flash('Arsip dokumen baru berhasil disimpan!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan internal saat menyimpan arsip!', 'danger')

    return redirect(url_for('arsip.list'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def edit(id):
    arsip      = ArsipDokumen.query.get_or_404(id)
    nama       = request.form.get('nama', '').strip()
    link_url   = request.form.get('link_url', '').strip()
    akses_tipe = request.form.get('akses_tipe', 'semua').strip()
    is_aktif   = request.form.get('is_aktif', 'true') == 'true'
    user_ids   = request.form.getlist('allowed_user_ids')

    if not nama or not link_url:
        flash('Nama dokumen dan Link Tautan URL wajib diisi!', 'danger')
        return redirect(url_for('arsip.list'))

    arsip.nama       = nama
    arsip.link_url   = link_url
    arsip.akses_tipe = akses_tipe
    arsip.is_aktif   = is_aktif

    arsip.allowed_users.clear()
    if akses_tipe == 'custom' and user_ids:
        valid_users = User.query.filter(User.id.in_([int(uid) for uid in user_ids if uid.isdigit()])).all()
        arsip.allowed_users.extend(valid_users)

    try:
        db.session.commit()
        flash('Data arsip dokumen berhasil diperbarui!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat memperbarui arsip!', 'danger')

    return redirect(url_for('arsip.list'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def delete(id):
    arsip = ArsipDokumen.query.get_or_404(id)
    try:
        db.session.delete(arsip)
        db.session.commit()
        flash('Arsip dokumen berhasil dihapus permanen!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Gagal menghapus arsip dokumen.', 'danger')

    return redirect(url_for('arsip.list'))
