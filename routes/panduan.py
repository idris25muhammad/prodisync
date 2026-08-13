import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Panduan
from utils.decorators import kaprodi_required
from datetime import datetime

bp = Blueprint('panduan', __name__, url_prefix='/panduan')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── ROUTE BARU: Mengunduh/Melihat File Secara Aman ──
@bp.route('/download/<filename>')
@login_required # Hanya user yang sudah login yang bisa mengakses file ini
def download_file(filename):
    # Dosen tidak boleh mengunduh panduan nonaktif
    if not current_user.is_kaprodi:
        panduan = Panduan.query.filter_by(file_path=filename).first()
        if not panduan or not panduan.is_aktif:
            abort(403)

    # Mengambil base path folder storage eksternal
    storage_dir = os.path.join(current_app.root_path, 'storage', 'dokumen_panduan')
    
    # Memastikan file ada sebelum dikirim
    if not os.path.exists(os.path.join(storage_dir, filename)):
        flash('File yang Anda cari tidak ditemukan atau sudah dihapus.', 'danger')
        return redirect(url_for('panduan.list'))
        
    return send_from_directory(storage_dir, filename)

@bp.route('/')
@login_required
def list():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Panduan.query
    if q:
        query = query.filter(Panduan.nama.ilike(f'%{q}%'))
    if not current_user.is_kaprodi:
        query = query.filter(Panduan.is_aktif == True)

    pagination = query.order_by(Panduan.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('panduan/list.html', semua_panduan=pagination.items, pagination=pagination, q=q)

@bp.route('/add', methods=['POST'])
@login_required
@kaprodi_required
def add():
    nama = request.form.get('nama', '').strip()
    tipe = request.form.get('tipe', '')
    is_aktif_form = request.form.get('is_aktif', 'true') == 'true'

    if not nama or not tipe:
        flash('Nama panduan dan Pilihan sumber wajib diisi!', 'danger')
        return redirect(url_for('panduan.list'))

    file_path = None
    link_url = None

    if tipe == 'file':
        if 'file_dokumen' not in request.files:
            flash('File dokumen tidak ditemukan!', 'danger')
            return redirect(url_for('panduan.list'))
        file = request.files['file_dokumen']
        if file.filename == '':
            flash('Silakan pilih file dokumen!', 'danger')
            return redirect(url_for('panduan.list'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
            
            # PENYIMPANAN AMAN: Disimpan ke folder storage eksternal
            storage_dir = os.path.join(current_app.root_path, 'storage', 'dokumen_panduan')
            os.makedirs(storage_dir, exist_ok=True) # Otomatis buat folder jika belum ada
            
            file.save(os.path.join(storage_dir, unique_filename))
            file_path = unique_filename
        else:
            flash('Format file tidak didukung!', 'danger')
            return redirect(url_for('panduan.list'))

    elif tipe == 'link':
        link_url = request.form.get('link_url', '').strip()
        if not link_url:
            flash('Tautan URL wajib diisi!', 'danger')
            return redirect(url_for('panduan.list'))

    try:
        baru_panduan = Panduan(nama=nama, tipe=tipe, file_path=file_path, link_url=link_url, is_aktif=is_aktif_form)
        db.session.add(baru_panduan)
        db.session.commit()
        flash('Panduan baru berhasil disimpan!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan internal database!', 'danger')

    return redirect(url_for('panduan.list'))

@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def edit(id):
    panduan = Panduan.query.get_or_404(id)
    nama = request.form.get('nama', '').strip()
    tipe = request.form.get('tipe', '')
    is_aktif_form = request.form.get('is_aktif', 'true') == 'true'

    if not nama or not tipe:
        flash('Data form tidak lengkap!', 'danger')
        return redirect(url_for('panduan.list'))

    panduan.nama = nama
    panduan.is_aktif = is_aktif_form
    storage_dir = os.path.join(current_app.root_path, 'storage', 'dokumen_panduan')
    
    if tipe == 'file':
        file = request.files.get('file_dokumen')
        if file and file.filename != '':
            if allowed_file(file.filename):
                if panduan.file_path:
                    old_path = os.path.join(storage_dir, panduan.file_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(file.filename)
                unique_filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
                file.save(os.path.join(storage_dir, unique_filename))
                panduan.file_path = unique_filename
                panduan.link_url = None
                panduan.tipe = 'file'
            else:
                flash('Format file edit tidak valid!', 'danger')
                return redirect(url_for('panduan.list'))
        else:
            if panduan.tipe != 'file':
                flash('Harap unggah berkas dokumen pendukung!', 'danger')
                return redirect(url_for('panduan.list'))

    elif tipe == 'link':
        link_url = request.form.get('link_url', '').strip()
        if not link_url:
            flash('Tautan URL wajib diisi!', 'danger')
            return redirect(url_for('panduan.list'))
        
        if panduan.file_path:
            old_path = os.path.join(storage_dir, panduan.file_path)
            if os.path.exists(old_path):
                os.remove(old_path)
            panduan.file_path = None
            
        panduan.link_url = link_url
        panduan.tipe = 'link'

    db.session.commit()
    flash('Data panduan berhasil diperbarui!', 'success')
    return redirect(url_for('panduan.list'))

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def delete(id):
    panduan = Panduan.query.get_or_404(id)
    if panduan.file_path:
        path = os.path.join(current_app.root_path, 'storage', 'dokumen_panduan', panduan.file_path)
        if os.path.exists(path):
            os.remove(path)
            
    db.session.delete(panduan)
    db.session.commit()
    flash('Panduan berhasil dihapus permanen!', 'success')
    return redirect(url_for('panduan.list'))