from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import StudentOutcome, PerformanceIndicator, ProficiencyLevel, RPS, so_sort_key
from utils.decorators import kaprodi_required

bp = Blueprint('so_pi', __name__, url_prefix='/so-pi')


# ── Helper: cek apakah SO/PI dirujuk oleh RPS yang sudah ada ───────────────
def _so_referenced(so_code):
    """True jika kode SO (mis. 'SO1') muncul sebagai awalan referensi RPS."""
    prefix = f"{so_code}-"
    for rps in RPS.query.all():
        for tp in (rps.tp_data or []):
            if not isinstance(tp, dict):
                continue
            for tok in [p.strip() for p in (tp.get('sopi') or '').split(',') if p.strip()]:
                if tok.startswith(prefix):
                    return True
    return False


def _pi_referenced(pi_code):
    """True jika kode PI (mis. 'PI-01.1') muncul sebagai akhiran referensi RPS."""
    suffix = f"-{pi_code}"
    for rps in RPS.query.all():
        for tp in (rps.tp_data or []):
            if not isinstance(tp, dict):
                continue
            for tok in [p.strip() for p in (tp.get('sopi') or '').split(',') if p.strip()]:
                if tok.endswith(suffix) or tok == pi_code:
                    return True
    return False


# ── Route: Halaman manajemen SO-PI (kaprodi) ────────────────────────────────
@bp.route('/')
@login_required
@kaprodi_required
def index():
    filter_status = request.args.get('status', 'aktif')
    toggled_id = request.args.get('toggled', type=int) or 0
    if toggled_id:
        filter_status = 'semua'
    query = StudentOutcome.query
    if filter_status == 'aktif':
        query = query.filter_by(is_active=True)
    elif filter_status == 'nonaktif':
        query = query.filter_by(is_active=False)
    outcomes = sorted(query.all(), key=lambda s: so_sort_key(s.so_code))
    levels = ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all()
    return render_template('so_pi/manage.html', outcomes=outcomes, levels=levels,
                           filter_status=filter_status, toggled_id=toggled_id)


# ── Route: Tambah SO ────────────────────────────────────────────────────────
@bp.route('/so/add', methods=['POST'])
@login_required
@kaprodi_required
def so_add():
    so_code = request.form.get('so_code', '').strip()
    so_description = request.form.get('so_description', '').strip()

    if not so_code or not so_description:
        flash('Kode SO dan deskripsi wajib diisi.', 'danger')
        return redirect(url_for('so_pi.index'))

    if StudentOutcome.query.filter_by(so_code=so_code).first():
        flash(f'Kode SO "{so_code}" sudah terdaftar.', 'danger')
        return redirect(url_for('so_pi.index'))

    db.session.add(StudentOutcome(so_code=so_code, so_description=so_description))
    db.session.commit()
    flash(f'SO "{so_code}" berhasil ditambahkan.', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Edit SO ──────────────────────────────────────────────────────────
@bp.route('/so/<int:id>/edit', methods=['POST'])
@login_required
@kaprodi_required
def so_edit(id):
    so = StudentOutcome.query.get_or_404(id)
    so_code = request.form.get('so_code', '').strip()
    so_description = request.form.get('so_description', '').strip()

    if not so_code or not so_description:
        flash('Kode SO dan deskripsi wajib diisi.', 'danger')
        return redirect(url_for('so_pi.index'))

    if so_code != so.so_code:
        if _so_referenced(so.so_code):
            flash('Kode SO tidak bisa diubah karena sudah dipakai di RPS yang ada. Deskripsi tetap diperbarui.', 'warning')
            so.so_description = so_description
        elif StudentOutcome.query.filter_by(so_code=so_code).first():
            flash(f'Kode SO "{so_code}" sudah dipakai SO lain.', 'danger')
            return redirect(url_for('so_pi.index'))
        else:
            so.so_code = so_code
            so.so_description = so_description
    else:
        so.so_description = so_description

    db.session.commit()
    flash(f'SO "{so.so_code}" berhasil diperbarui.', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Toggle aktif/nonaktif SO ─────────────────────────────────────────
@bp.route('/so/<int:id>/toggle', methods=['POST'])
@login_required
@kaprodi_required
def so_toggle(id):
    so = StudentOutcome.query.get_or_404(id)

    so.is_active = not so.is_active
    db.session.commit()
    status = 'diaktifkan' if so.is_active else 'dinonaktifkan'
    flash(f'SO "{so.so_code}" berhasil {status}.', 'success')
    return redirect(url_for('so_pi.index', toggled=so.id))


# ── Route: Hapus SO ─────────────────────────────────────────────────────────
@bp.route('/so/<int:id>/delete', methods=['POST'])
@login_required
@kaprodi_required
def so_delete(id):
    so = StudentOutcome.query.get_or_404(id)

    if _so_referenced(so.so_code):
        flash(f'SO "{so.so_code}" tidak bisa dihapus karena masih dipakai di RPS yang ada.', 'danger')
        return redirect(url_for('so_pi.index'))

    for pi in so.indicators:
        if _pi_referenced(pi.pi_code):
            flash(f'PI "{pi.pi_code}" milik SO "{so.so_code}" masih dipakai di RPS yang ada.', 'danger')
            return redirect(url_for('so_pi.index'))

    db.session.delete(so)
    db.session.commit()
    flash(f'SO "{so.so_code}" beserta PI-nya berhasil dihapus.', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Tambah PI ────────────────────────────────────────────────────────
@bp.route('/pi/add', methods=['POST'])
@login_required
@kaprodi_required
def pi_add():
    so_id = request.form.get('student_outcome_id', type=int)
    pi_code = request.form.get('pi_code', '').strip()
    pi_description = request.form.get('pi_description', '').strip()
    level = request.form.get('level', type=int)

    so = StudentOutcome.query.get_or_404(so_id)
    if not pi_code or not pi_description:
        flash('Kode PI dan deskripsi wajib diisi.', 'danger')
        return redirect(url_for('so_pi.index'))
    if not level or level not in [1, 2, 3, 4, 5]:
        flash('Level proficiency harus antara 1-5.', 'danger')
        return redirect(url_for('so_pi.index'))

    existing = PerformanceIndicator.query.filter_by(student_outcome_id=so_id, pi_code=pi_code).first()
    if existing:
        flash(f'PI "{pi_code}" sudah terdaftar di SO "{so.so_code}".', 'danger')
        return redirect(url_for('so_pi.index'))

    db.session.add(PerformanceIndicator(
        student_outcome_id=so_id,
        pi_code=pi_code,
        pi_description=pi_description,
        level=level,
    ))
    db.session.commit()
    flash(f'PI "{pi_code}" berhasil ditambahkan ke SO "{so.so_code}".', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Edit PI ──────────────────────────────────────────────────────────
@bp.route('/pi/<int:id>/edit', methods=['POST'])
@login_required
@kaprodi_required
def pi_edit(id):
    pi = PerformanceIndicator.query.get_or_404(id)
    pi_code = request.form.get('pi_code', '').strip()
    pi_description = request.form.get('pi_description', '').strip()
    level = request.form.get('level', type=int)

    if not pi_code or not pi_description:
        flash('Kode PI dan deskripsi wajib diisi.', 'danger')
        return redirect(url_for('so_pi.index'))
    if not level or level not in [1, 2, 3, 4, 5]:
        flash('Level proficiency harus antara 1-5.', 'danger')
        return redirect(url_for('so_pi.index'))

    if pi_code != pi.pi_code:
        if _pi_referenced(pi.pi_code):
            flash('Kode PI tidak bisa diubah karena sudah dipakai di RPS yang ada. Deskripsi & level tetap diperbarui.', 'warning')
        elif PerformanceIndicator.query.filter_by(student_outcome_id=pi.student_outcome_id, pi_code=pi_code).first():
            flash(f'PI "{pi_code}" sudah terdaftar di SO yang sama.', 'danger')
            return redirect(url_for('so_pi.index'))
        else:
            pi.pi_code = pi_code

    pi.pi_description = pi_description
    pi.level = level
    db.session.commit()
    flash(f'PI "{pi.pi_code}" berhasil diperbarui.', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Hapus PI ─────────────────────────────────────────────────────────
@bp.route('/pi/<int:id>/delete', methods=['POST'])
@login_required
@kaprodi_required
def pi_delete(id):
    pi = PerformanceIndicator.query.get_or_404(id)

    if _pi_referenced(pi.pi_code):
        flash(f'PI "{pi.pi_code}" tidak bisa dihapus karena masih dipakai di RPS yang ada.', 'danger')
        return redirect(url_for('so_pi.index'))

    so_code = pi.student_outcome.so_code
    db.session.delete(pi)
    db.session.commit()
    flash(f'PI "{pi.pi_code}" berhasil dihapus dari SO "{so_code}".', 'success')
    return redirect(url_for('so_pi.index'))


# ── Route: Edit label level proficiency ─────────────────────────────────────
@bp.route('/levels/edit', methods=['POST'])
@login_required
@kaprodi_required
def levels_edit():
    levels = ProficiencyLevel.query.all()
    for lvl in levels:
        label = request.form.get(f'label_{lvl.level}', '').strip()
        if label:
            lvl.label = label
    db.session.commit()
    flash('Label level proficiency berhasil diperbarui.', 'success')
    return redirect(url_for('so_pi.index'))
