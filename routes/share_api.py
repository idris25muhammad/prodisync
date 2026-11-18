from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models import ApiClient, Prodi
from utils.decorators import kajur_required

bp = Blueprint('share_api', __name__, url_prefix='/share-api')


@bp.route('/')
@login_required
@kajur_required
def index():
    clients = ApiClient.query.order_by(ApiClient.created_at.desc()).all()
    new_api_key = session.pop('new_api_key', None)
    sample_prodi = Prodi.query.filter_by(is_aktif=True).order_by(Prodi.kode.asc()).first()
    sample_kode = sample_prodi.kode if sample_prodi else 'RKS'
    base_api_url = request.url_root.rstrip('/') + url_for('api_v1.ping').rsplit('/ping', 1)[0]

    return render_template(
        'share_api/index.html',
        clients=clients,
        new_api_key=new_api_key,
        sample_kode=sample_kode,
        base_api_url=base_api_url,
    )


@bp.route('/create', methods=['POST'])
@login_required
@kajur_required
def create():
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip() or None

    if not name:
        flash('Nama aplikasi konsumen wajib diisi.', 'danger')
        return redirect(url_for('share_api.index'))

    raw_key, key_prefix, key_hash = ApiClient.generate_key()
    client = ApiClient(
        name=name,
        description=description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
        created_by=current_user.id,
    )
    db.session.add(client)
    db.session.commit()

    session['new_api_key'] = {
        'name': client.name,
        'key': raw_key,
        'action': 'dibuat',
    }
    flash(f'API key untuk "{client.name}" berhasil dibuat.', 'success')
    return redirect(url_for('share_api.index'))


@bp.route('/<int:id>/edit', methods=['POST'])
@login_required
@kajur_required
def edit(id):
    client = ApiClient.query.get_or_404(id)
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip() or None

    if not name:
        flash('Nama aplikasi tidak boleh kosong.', 'danger')
        return redirect(url_for('share_api.index'))

    client.name = name
    client.description = description
    db.session.commit()

    flash(f'Informasi "{client.name}" berhasil diperbarui.', 'success')
    return redirect(url_for('share_api.index'))


@bp.route('/<int:id>/regenerate', methods=['POST'])
@login_required
@kajur_required
def regenerate(id):
    client = ApiClient.query.get_or_404(id)
    raw_key, key_prefix, key_hash = ApiClient.generate_key()
    client.key_prefix = key_prefix
    client.key_hash = key_hash
    client.is_active = True
    db.session.commit()

    session['new_api_key'] = {
        'name': client.name,
        'key': raw_key,
        'action': 'di-regenerate',
    }
    flash(f'API key baru untuk "{client.name}" berhasil diterbitkan. Key lama sudah tidak berlaku.', 'success')
    return redirect(url_for('share_api.index'))


@bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
@kajur_required
def toggle(id):
    client = ApiClient.query.get_or_404(id)
    client.is_active = not client.is_active
    db.session.commit()

    status_txt = 'diaktifkan' if client.is_active else 'dinonaktifkan'
    flash(f'Akses API "{client.name}" berhasil {status_txt}.', 'success')
    return redirect(url_for('share_api.index'))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@kajur_required
def delete(id):
    client = ApiClient.query.get_or_404(id)
    name = client.name
    db.session.delete(client)
    db.session.commit()

    flash(f'API client "{name}" berhasil dihapus.', 'success')
    return redirect(url_for('share_api.index'))
