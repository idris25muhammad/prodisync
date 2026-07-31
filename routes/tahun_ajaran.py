from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import TahunAjaran
from flask_login import login_required, current_user

# Nama blueprint ini harus sesuai dengan yang digunakan di url_for
bp = Blueprint('tahun_ajaran', __name__)

@bp.route('/add', methods=['POST'])
@login_required
def add():
    tahun = request.form.get('tahun', '').strip()
    semester = request.form.get('semester', '').strip()

    if not tahun or not semester:
        flash('Semua field data Tahun Ajaran wajib diisi!', 'danger')
        return redirect(url_for('dashboard.index'))

    existing_ta = TahunAjaran.query.filter_by(tahun=tahun, semester=semester).first()
    if existing_ta:
        flash(f'Gagal! Kombinasi Tahun Ajaran {tahun} dengan Semester {semester} sudah terdaftar di sistem.', 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        # Jika tidak ada duplikat, buat data baru
        baru_ta = TahunAjaran(
            tahun=tahun,
            semester=semester,
            is_aktif=False # Default tidak langsung aktif saat dibuat
        )
        db.session.add(baru_ta)
        db.session.commit()
        flash('Tahun Ajaran baru berhasil ditambahkan!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan internal pada sistem database.', 'danger')

    return redirect(url_for('dashboard.index'))
    

@bp.route('/tahun-ajaran/set-aktif/<int:id>', methods=['GET'])
@login_required
def set_aktif(id):
    if not current_user.is_kaprodi:
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard.index'))
    
    # Nonaktifkan semua
    TahunAjaran.query.update({'is_aktif': False})
    
    # Aktifkan yang dipilih
    ta = TahunAjaran.query.get_or_404(id)
    ta.is_aktif = True
    
    db.session.commit()
    flash(f'Tahun ajaran {ta.tahun} {ta.semester} kini aktif.', 'success')
    return redirect(url_for('dashboard.index'))

@bp.route('/tahun-ajaran/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    if not current_user.is_kaprodi:
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard.index'))
        
    ta = TahunAjaran.query.get_or_404(id)
    ta.tahun = request.form.get('tahun')
    ta.semester = request.form.get('semester')
    
    db.session.commit()
    flash('Tahun ajaran berhasil diperbarui.', 'success')
    return redirect(url_for('dashboard.index'))

@bp.route('/tahun-ajaran/<int:id>/delete', methods=['GET'])
@login_required
def delete(id):
    if not current_user.is_kaprodi:
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard.index'))
        
    ta = TahunAjaran.query.get_or_404(id)
    db.session.delete(ta)
    db.session.commit()
    
    flash('Tahun ajaran berhasil dihapus.', 'info')
    return redirect(url_for('dashboard.index'))