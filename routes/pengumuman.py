import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Pengumuman
from utils.decorators import kaprodi_required
from datetime import datetime, date

bp = Blueprint('pengumuman', __name__, url_prefix='/pengumuman')

ALLOWED_EXTENSIONS      = {'jpg', 'jpeg', 'png', 'docx', 'pdf'}
IMAGE_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
IMAGE_MAX_BYTES          = 3 * 1024 * 1024   # 3 MB
STORAGE_DIR_NAME         = os.path.join('storage', 'pengumuman')
IMAGE_SUBDIR             = 'images'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_ALLOWED_EXTENSIONS


def get_storage_dir(app):
    path = os.path.join(app.root_path, STORAGE_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_image_dir(app):
    path = os.path.join(app.root_path, STORAGE_DIR_NAME, IMAGE_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


# ─────────────────────────────────────────────────────────────────
#  SERVE INLINE IMAGE (disimpan di storage/pengumuman/images/)
# ─────────────────────────────────────────────────────────────────
@bp.route('/images/<path:filename>')
@login_required
def serve_image(filename):
    image_dir = get_image_dir(current_app)
    filepath  = os.path.join(image_dir, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_from_directory(image_dir, filename)


# ─────────────────────────────────────────────────────────────────
#  UPLOAD INLINE IMAGE (dipakai oleh Quill image handler)
# ─────────────────────────────────────────────────────────────────
@bp.route('/upload-image', methods=['POST'])
@login_required
@kaprodi_required
def upload_image():
    """Menerima upload gambar dari editor Quill dan mengembalikan URL-nya."""
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify({'error': 'Tidak ada file yang dikirim.'}), 400

    if not allowed_image(file.filename):
        return jsonify({'error': 'Format tidak didukung. Gunakan jpg, png, webp, atau gif.'}), 415

    # Validasi ukuran: baca dulu isi file, cek panjangnya
    file_bytes = file.read()
    if len(file_bytes) > IMAGE_MAX_BYTES:
        return jsonify({'error': f'Ukuran gambar melebihi batas {IMAGE_MAX_BYTES // (1024*1024)} MB.'}), 413

    ext             = file.filename.rsplit('.', 1)[1].lower()
    safe_name       = secure_filename(file.filename)
    unique_filename = f"{int(datetime.utcnow().timestamp())}_{safe_name}"
    image_dir       = get_image_dir(current_app)

    with open(os.path.join(image_dir, unique_filename), 'wb') as f:
        f.write(file_bytes)

    url = url_for('pengumuman.serve_image', filename=unique_filename)
    return jsonify({'url': url})


# ─────────────────────────────────────────────────────────────────
#  DOWNLOAD LAMPIRAN (semua user yg login)
# ─────────────────────────────────────────────────────────────────
@bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    storage_dir = get_storage_dir(current_app)
    filepath = os.path.join(storage_dir, filename)
    if not os.path.exists(filepath):
        flash('File tidak ditemukan atau sudah dihapus.', 'danger')
        return redirect(url_for('pengumuman.index'))
    return send_from_directory(storage_dir, filename)


# ─────────────────────────────────────────────────────────────────
#  INDEX – tampilan kartu bagi dosen / publik
# ─────────────────────────────────────────────────────────────────
@bp.route('/')
@login_required
def index():
    q = Pengumuman.query

    # Dosen hanya melihat visibility dosen & publik
    if not current_user.is_kaprodi:
        q = q.filter(Pengumuman.visibility.in_(['dosen', 'publik']))

    # Filter tanggal
    date_from = request.args.get('date_from', '').strip()
    date_to   = request.args.get('date_to',   '').strip()
    vis_filter = request.args.get('visibility', '').strip()

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            q  = q.filter(Pengumuman.created_at >= df)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            # Akhir hari
            dt = dt.replace(hour=23, minute=59, second=59)
            q  = q.filter(Pengumuman.created_at <= dt)
        except ValueError:
            pass

    if vis_filter in ('dosen', 'publik'):
        q = q.filter(Pengumuman.visibility == vis_filter)

    pengumuman_list = q.order_by(Pengumuman.created_at.desc()).all()

    return render_template(
        'pengumuman/index.html',
        pengumuman_list=pengumuman_list,
        date_from=date_from,
        date_to=date_to,
        vis_filter=vis_filter,
    )


# ─────────────────────────────────────────────────────────────────
#  DETAIL (baca satu pengumuman)
# ─────────────────────────────────────────────────────────────────
@bp.route('/<int:id>')
@login_required
def detail(id):
    p = Pengumuman.query.get_or_404(id)
    # Dosen tidak boleh melihat draft
    if not current_user.is_kaprodi and p.visibility == 'draft':
        abort(403)
    return render_template('pengumuman/detail.html', p=p)


# ─────────────────────────────────────────────────────────────────
#  KELOLA (CRUD list untuk kaprodi)
# ─────────────────────────────────────────────────────────────────
@bp.route('/kelola')
@login_required
@kaprodi_required
def kelola():
    pengumuman_list = Pengumuman.query.order_by(Pengumuman.created_at.desc()).all()
    return render_template('pengumuman/kelola.html', pengumuman_list=pengumuman_list)


# ─────────────────────────────────────────────────────────────────
#  TAMBAH (form GET + POST)
# ─────────────────────────────────────────────────────────────────
@bp.route('/tambah', methods=['GET', 'POST'])
@login_required
@kaprodi_required
def tambah():
    if request.method == 'POST':
        judul      = request.form.get('judul', '').strip()
        konten     = request.form.get('konten', '').strip()
        visibility = request.form.get('visibility', 'draft')

        if not judul or not konten:
            flash('Judul dan isi konten wajib diisi!', 'danger')
            return redirect(url_for('pengumuman.tambah'))

        # File upload (opsional)
        file_path = None
        file = request.files.get('file_lampiran')
        if file and file.filename:
            if allowed_file(file.filename):
                ext              = file.filename.rsplit('.', 1)[1].lower()
                safe_name        = secure_filename(file.filename)
                unique_filename  = f"{int(datetime.utcnow().timestamp())}_{safe_name}"
                storage_dir      = get_storage_dir(current_app)
                file.save(os.path.join(storage_dir, unique_filename))
                file_path = unique_filename
            else:
                flash('Format file tidak didukung! (jpg, png, docx, pdf)', 'danger')
                return redirect(url_for('pengumuman.tambah'))

        p = Pengumuman(
            judul=judul,
            konten=konten,
            visibility=visibility,
            file_path=file_path,
            penulis_id=current_user.id,
        )
        db.session.add(p)
        db.session.commit()
        flash('Pengumuman berhasil disimpan!', 'success')
        return redirect(url_for('pengumuman.kelola'))

    return render_template('pengumuman/form.html', action='tambah', p=None)


# ─────────────────────────────────────────────────────────────────
#  EDIT (form GET + POST)
# ─────────────────────────────────────────────────────────────────
@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@kaprodi_required
def edit(id):
    p = Pengumuman.query.get_or_404(id)

    if request.method == 'POST':
        p.judul      = request.form.get('judul', p.judul).strip()
        p.konten     = request.form.get('konten', p.konten).strip()
        p.visibility = request.form.get('visibility', p.visibility)

        file = request.files.get('file_lampiran')
        if file and file.filename:
            if allowed_file(file.filename):
                # Hapus file lama jika ada
                if p.file_path:
                    old = os.path.join(get_storage_dir(current_app), p.file_path)
                    if os.path.exists(old):
                        os.remove(old)

                safe_name       = secure_filename(file.filename)
                unique_filename = f"{int(datetime.utcnow().timestamp())}_{safe_name}"
                storage_dir     = get_storage_dir(current_app)
                file.save(os.path.join(storage_dir, unique_filename))
                p.file_path = unique_filename
            else:
                flash('Format file tidak didukung! (jpg, png, docx, pdf)', 'danger')
                return redirect(url_for('pengumuman.edit', id=id))

        # Hapus file yang sudah ada jika user mencentang hapus
        if request.form.get('hapus_file') == '1' and p.file_path:
            old = os.path.join(get_storage_dir(current_app), p.file_path)
            if os.path.exists(old):
                os.remove(old)
            p.file_path = None

        db.session.commit()
        flash('Pengumuman berhasil diperbarui!', 'success')
        return redirect(url_for('pengumuman.kelola'))

    return render_template('pengumuman/form.html', action='edit', p=p)


# ─────────────────────────────────────────────────────────────────
#  HAPUS
# ─────────────────────────────────────────────────────────────────
@bp.route('/hapus/<int:id>')
@login_required
@kaprodi_required
def hapus(id):
    p = Pengumuman.query.get_or_404(id)
    if p.file_path:
        old = os.path.join(get_storage_dir(current_app), p.file_path)
        if os.path.exists(old):
            os.remove(old)
    db.session.delete(p)
    db.session.commit()
    flash('Pengumuman berhasil dihapus!', 'success')
    return redirect(url_for('pengumuman.kelola'))
