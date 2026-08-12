from datetime import datetime, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Agenda
from utils.decorators import kaprodi_required

bp = Blueprint('agenda', __name__, url_prefix='/agenda')


@bp.route('/')
@login_required
def index():
    semua_agenda = Agenda.query.order_by(Agenda.tanggal.asc(), Agenda.waktu_mulai.asc()).all()
    return render_template('agenda/calendar.html', semua_agenda=semua_agenda)


@bp.route('/api/events')
@login_required
def events_api():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    query = Agenda.query

    if not current_user.is_kaprodi:
        query = query.filter_by(is_aktif=True)

    events_list = query.order_by(Agenda.tanggal.asc(), Agenda.waktu_mulai.asc()).all()

    results = []
    for item in events_list:
        results.append({
            'id': item.id,
            'judul': item.judul,
            'deskripsi': item.deskripsi or '',
            'tanggal': item.tanggal.strftime('%Y-%m-%d'),
            'waktu_mulai': item.waktu_mulai.strftime('%H:%M') if item.waktu_mulai else '',
            'waktu_selesai': item.waktu_selesai.strftime('%H:%M') if item.waktu_selesai else '',
            'lokasi': item.lokasi or '',
            'kategori': item.kategori or 'Rapat Umum',
            'is_aktif': item.is_aktif,
            'created_by': item.creator.nama if item.creator else '—'
        })

    return jsonify(results)


@bp.route('/add', methods=['POST'])
@login_required
@kaprodi_required
def add():
    judul = request.form.get('judul', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    tanggal_str = request.form.get('tanggal', '').strip()
    waktu_mulai_str = request.form.get('waktu_mulai', '').strip()
    waktu_selesai_str = request.form.get('waktu_selesai', '').strip()
    lokasi = request.form.get('lokasi', '').strip()
    kategori = request.form.get('kategori', 'Rapat Umum').strip()
    is_aktif = request.form.get('is_aktif', 'true') == 'true'

    if not judul or not tanggal_str:
        flash('Judul agenda dan Tanggal wajib diisi!', 'danger')
        return redirect(url_for('agenda.index'))

    try:
        tanggal_val = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Format tanggal tidak valid!', 'danger')
        return redirect(url_for('agenda.index'))

    waktu_mulai_val = None
    if waktu_mulai_str:
        try:
            waktu_mulai_val = datetime.strptime(waktu_mulai_str, '%H:%M').time()
        except ValueError:
            pass

    waktu_selesai_val = None
    if waktu_selesai_str:
        try:
            waktu_selesai_val = datetime.strptime(waktu_selesai_str, '%H:%M').time()
        except ValueError:
            pass

    try:
        baru_agenda = Agenda(
            judul=judul,
            deskripsi=deskripsi or None,
            tanggal=tanggal_val,
            waktu_mulai=waktu_mulai_val,
            waktu_selesai=waktu_selesai_val,
            lokasi=lokasi or None,
            kategori=kategori,
            is_aktif=is_aktif,
            created_by=current_user.id
        )
        db.session.add(baru_agenda)
        db.session.commit()
        flash(f'Agenda "{judul}" berhasil ditambahkan!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan internal saat menyimpan agenda!', 'danger')

    return redirect(url_for('agenda.index'))


@bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def edit(id):
    agenda = Agenda.query.get_or_404(id)
    judul = request.form.get('judul', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    tanggal_str = request.form.get('tanggal', '').strip()
    waktu_mulai_str = request.form.get('waktu_mulai', '').strip()
    waktu_selesai_str = request.form.get('waktu_selesai', '').strip()
    lokasi = request.form.get('lokasi', '').strip()
    kategori = request.form.get('kategori', agenda.kategori).strip()
    is_aktif = request.form.get('is_aktif', 'true') == 'true'

    if not judul or not tanggal_str:
        flash('Judul agenda dan Tanggal wajib diisi!', 'danger')
        return redirect(url_for('agenda.index'))

    try:
        agenda.tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Format tanggal tidak valid!', 'danger')
        return redirect(url_for('agenda.index'))

    if waktu_mulai_str:
        try:
            agenda.waktu_mulai = datetime.strptime(waktu_mulai_str, '%H:%M').time()
        except ValueError:
            agenda.waktu_mulai = None
    else:
        agenda.waktu_mulai = None

    if waktu_selesai_str:
        try:
            agenda.waktu_selesai = datetime.strptime(waktu_selesai_str, '%H:%M').time()
        except ValueError:
            agenda.waktu_selesai = None
    else:
        agenda.waktu_selesai = None

    agenda.judul = judul
    agenda.deskripsi = deskripsi or None
    agenda.lokasi = lokasi or None
    agenda.kategori = kategori
    agenda.is_aktif = is_aktif

    try:
        db.session.commit()
        flash(f'Agenda "{judul}" berhasil diperbarui!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat memperbarui agenda!', 'danger')

    return redirect(url_for('agenda.index'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@kaprodi_required
def delete(id):
    agenda = Agenda.query.get_or_404(id)
    judul = agenda.judul
    try:
        db.session.delete(agenda)
        db.session.commit()
        flash(f'Agenda "{judul}" berhasil dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Gagal menghapus agenda.', 'danger')

    return redirect(url_for('agenda.index'))
