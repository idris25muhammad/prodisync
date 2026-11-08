from collections import Counter

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import MataKuliah, TahunAjaran, Prodi

bp = Blueprint('kurikulum', __name__, url_prefix='/kurikulum')


@bp.route('/matakuliah')
@login_required
def matakuliah():
    return redirect(url_for('matakuliah.list'))


CDIO_SKILLS = ('pd', 'wc', 'st', 'tw', 'ce', 'ps')


@bp.route('/integrated')
@login_required
def integrated():
    prodi_list = Prodi.query.filter_by(is_aktif=True).order_by(Prodi.nama.asc()).all()

    if not current_user.is_kajur:
        prodi_id = getattr(current_user, 'prodi_id', None) or 1
    else:
        prodi_id = request.args.get('prodi_id', type=int) or getattr(current_user, 'prodi_id', None) or (prodi_list[0].id if prodi_list else 1)

    kurikulum_list = [
        r[0] for r in db.session.query(MataKuliah.kurikulum)
        .filter(MataKuliah.prodi_id == prodi_id, MataKuliah.kurikulum.isnot(None))
        .distinct()
        .order_by(MataKuliah.kurikulum.asc())
        .all()
    ]

    # Fallback ke kurikulum pertama jika kosong / tidak ada di prodi terpilih (mis. setelah ganti prodi)
    selected_kurikulum = request.args.get('kurikulum', '').strip()
    if selected_kurikulum not in kurikulum_list:
        selected_kurikulum = kurikulum_list[0] if kurikulum_list else ''

    query = MataKuliah.query.filter_by(prodi_id=prodi_id)
    if selected_kurikulum:
        query = query.filter_by(kurikulum=selected_kurikulum)

    all_mk = query.order_by(MataKuliah.semester.asc(), MataKuliah.kode.asc()).all()

    mk_by_semester = {sem: [] for sem in range(1, 9)}
    for mk in all_mk:
        sem = mk.semester or 1
        mk_by_semester[min(max(sem, 1), 8)].append(mk)

    year_config = [
        {'year': 1, 'label': 'CDIO skills are introduced',   'project': 'Project Foundation',     'semesters': [1, 2]},
        {'year': 2, 'label': 'CDIO skills are reinforced',   'project': 'Project Cornerstone #1', 'semesters': [3, 4]},
        {'year': 3, 'label': 'CDIO skills are strengthened', 'project': 'Project Cornerstone #2', 'semesters': [5, 6]},
        {'year': 4, 'label': 'CDIO skills are proficient',   'project': 'Project Capstone',       'semesters': [7, 8]},
    ]

    def normalize_skill(mk):
        skill = (mk.cdio_skill or '').strip().lower()
        return skill if skill in CDIO_SKILLS else 'pd'

    cdio_map = {mk.id: normalize_skill(mk) for mk in all_mk}
    cdio_counts = Counter(cdio_map.values())

    return render_template(
        'kurikulum/integrated.html',
        prodi_list=prodi_list,
        selected_prodi_id=prodi_id,
        kurikulum_list=kurikulum_list,
        selected_kurikulum=selected_kurikulum,
        mk_by_semester=mk_by_semester,
        year_config=year_config,
        cdio_map=cdio_map,
        cdio_counts=cdio_counts,
        total_mk=len(all_mk),
    )


@bp.route('/prasyarat')
@login_required
def prasyarat():
    prodi_list = Prodi.query.filter_by(is_aktif=True).order_by(Prodi.nama.asc()).all()

    # Tentukan prodi_id
    if not current_user.is_kajur:
        prodi_id = getattr(current_user, 'prodi_id', None) or 1
    else:
        prodi_id = request.args.get('prodi_id', type=int) or getattr(current_user, 'prodi_id', None) or (prodi_list[0].id if prodi_list else 1)

    # Ambil kurikulum yang ada di prodi ini
    kurikulum_list = [
        r[0] for r in db.session.query(MataKuliah.kurikulum)
        .filter(MataKuliah.prodi_id == prodi_id, MataKuliah.kurikulum.isnot(None))
        .distinct()
        .order_by(MataKuliah.kurikulum.asc())
        .all()
    ]

    selected_kurikulum = request.args.get('kurikulum', '').strip()
    if not selected_kurikulum and kurikulum_list:
        selected_kurikulum = kurikulum_list[0]

    # Query mata kuliah
    query = MataKuliah.query.filter_by(prodi_id=prodi_id)
    if selected_kurikulum:
        query = query.filter_by(kurikulum=selected_kurikulum)

    all_mk = query.order_by(MataKuliah.semester.asc(), MataKuliah.kode.asc()).all()

    # Kelompokkan mata kuliah per semester (1 s.d. 8)
    mk_by_semester = {sem: [] for sem in range(1, 9)}
    mk_map = {}
    for mk in all_mk:
        mk_map[mk.kode.strip()] = mk
        sem = mk.semester or 1
        if 1 <= sem <= 8:
            mk_by_semester[sem].append(mk)
        else:
            mk_by_semester[1].append(mk)

    category_colors = {
        'math': '#9333ea',
        'system': '#ea580c',
        'network': '#0ea5e9',
        'devops': '#ca8a04',
        'appsec': '#16a34a',
        'grc': '#475569',
        'research': '#0d9488',
        'general': '#64748b'
    }

    # Buat relasi garis penghubung (connections)
    connections = []
    for mk in all_mk:
        if mk.prasyarat:
            items = [x.strip() for x in mk.prasyarat.split(',') if x.strip()]
            for item in items:
                # Periksa apakah mata kuliah prasyarat ada dalam katalog
                prereq_mk = mk_map.get(item)
                cat = (mk.kategori or (prereq_mk.kategori if prereq_mk else None) or 'appsec').lower()
                if cat not in category_colors:
                    cat = 'appsec'
                connections.append({
                    'ids': [f'mk-{item}', f'mk-{mk.kode}'],
                    'cat': cat,
                    'prereq_code': item,
                    'target_code': mk.kode,
                })

    return render_template(
        'kurikulum/prasyarat.html',
        prodi_list=prodi_list,
        selected_prodi_id=prodi_id,
        kurikulum_list=kurikulum_list,
        selected_kurikulum=selected_kurikulum,
        mk_by_semester=mk_by_semester,
        connections=connections,
        category_colors=category_colors,
        total_mk=len(all_mk),
    )