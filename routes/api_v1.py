from datetime import datetime
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from models import (
    Prodi, TahunAjaran, StudentOutcome, PerformanceIndicator,
    ProficiencyLevel, MataKuliah, RPS, so_sort_key,
)
from utils.api_auth import api_key_required, api_error
from utils.serializers import (
    prodi_to_dict, tahun_ajaran_to_dict, level_to_dict,
    so_to_dict, pi_to_dict, matakuliah_summary_to_dict, build_course_json,
)

bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')


def _now_iso():
    return datetime.now().astimezone().isoformat()


def _get_prodi(kode: str):
    return Prodi.query.filter(
        func.lower(Prodi.kode) == (kode or '').strip().lower(),
        Prodi.is_aktif.is_(True),
    ).first()


def _levels_map():
    return {
        lvl.level: lvl.label
        for lvl in ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all()
    }


def _resolve_tahun_ajaran(ta_param: str):
    if ta_param:
        raw = ta_param.strip()
        for ta in TahunAjaran.query.order_by(TahunAjaran.id.desc()).all():
            if f"{ta.tahun} {ta.semester}".lower() == raw.lower():
                return ta
        return None
    return TahunAjaran.query.filter_by(is_aktif=True).first()


def _find_rps_for_mk(prodi_id: int, matakuliah_id: int, ta, rps_status: str):
    query = RPS.query.filter_by(prodi_id=prodi_id, matakuliah_id=matakuliah_id)
    if ta:
        query = query.filter_by(tahun_ajaran_id=ta.id)
    if rps_status != 'all':
        query = query.filter(RPS.rps_status == rps_status)
    return query.order_by(RPS.updated_at.desc(), RPS.id.desc()).first()


@bp.route('/ping', methods=['GET'])
@api_key_required
def ping():
    return jsonify({
        'status': 'ok',
        'client': g.api_client.name,
        'api_version': 'v1',
        'server_time': _now_iso(),
    })


@bp.route('/prodi', methods=['GET'])
@api_key_required
def list_prodi():
    prodis = Prodi.query.filter_by(is_aktif=True).order_by(Prodi.kode.asc()).all()
    ta_aktif = TahunAjaran.query.filter_by(is_aktif=True).first()
    return jsonify({
        'data': [prodi_to_dict(p) for p in prodis],
        'meta': {
            'count': len(prodis),
            'tahun_ajaran_aktif': tahun_ajaran_to_dict(ta_aktif),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/proficiency-levels', methods=['GET'])
@api_key_required
def list_proficiency_levels():
    levels = ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all()
    return jsonify({
        'data': [level_to_dict(l) for l in levels],
        'meta': {
            'count': len(levels),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/so', methods=['GET'])
@api_key_required
def list_so(kode):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    status = (request.args.get('status') or 'active').strip().lower()
    include_pi = (request.args.get('include') or '').strip().lower() == 'pi'

    query = StudentOutcome.query.filter_by(prodi_id=prodi.id)
    if include_pi:
        query = query.options(joinedload(StudentOutcome.indicators))
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    outcomes = sorted(query.all(), key=lambda s: so_sort_key(s.so_code))
    lmap = _levels_map() if include_pi else None

    return jsonify({
        'data': [so_to_dict(so, include_pi=include_pi, levels_map=lmap) for so in outcomes],
        'meta': {
            'prodi': prodi.kode,
            'status': status,
            'count': len(outcomes),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/so/<string:so_code>', methods=['GET'])
@api_key_required
def detail_so(kode, so_code):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    so = (
        StudentOutcome.query
        .options(joinedload(StudentOutcome.indicators))
        .filter(
            StudentOutcome.prodi_id == prodi.id,
            func.lower(StudentOutcome.so_code) == so_code.strip().lower(),
        )
        .first()
    )
    if not so:
        return api_error(404, 'so_not_found', f"Student Outcome '{so_code}' tidak ditemukan pada prodi {prodi.kode}.")

    return jsonify({
        'data': so_to_dict(so, include_pi=True, levels_map=_levels_map()),
        'meta': {
            'prodi': prodi.kode,
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/pi', methods=['GET'])
@api_key_required
def list_pi(kode):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    so_filter = (request.args.get('so_code') or '').strip().lower()
    level_filter = request.args.get('level', type=int)

    query = (
        StudentOutcome.query
        .options(joinedload(StudentOutcome.indicators))
        .filter_by(prodi_id=prodi.id, is_active=True)
    )
    if so_filter:
        query = query.filter(func.lower(StudentOutcome.so_code) == so_filter)

    lmap = _levels_map()
    items = []
    for so in sorted(query.all(), key=lambda s: so_sort_key(s.so_code)):
        for pi in sorted(so.indicators, key=lambda p: p.pi_code):
            if level_filter is not None and pi.level != level_filter:
                continue
            items.append(pi_to_dict(pi, levels_map=lmap, so_code=so.so_code))

    return jsonify({
        'data': items,
        'meta': {
            'prodi': prodi.kode,
            'count': len(items),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/so-pi', methods=['GET'])
@api_key_required
def export_sopi(kode):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    status = (request.args.get('status') or 'active').strip().lower()
    query = (
        StudentOutcome.query
        .options(joinedload(StudentOutcome.indicators))
        .filter_by(prodi_id=prodi.id)
    )
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    lmap = _levels_map()
    outcomes = sorted(query.all(), key=lambda s: so_sort_key(s.so_code))
    levels = ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all()

    return jsonify({
        'data': {
            'prodi': prodi_to_dict(prodi),
            'proficiency_levels': [level_to_dict(l) for l in levels],
            'student_outcomes': [so_to_dict(so, include_pi=True, levels_map=lmap) for so in outcomes],
        },
        'meta': {
            'prodi': prodi.kode,
            'status': status,
            'so_count': len(outcomes),
            'pi_count': sum(len(so.indicators) for so in outcomes),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/matakuliah', methods=['GET'])
@api_key_required
def list_matakuliah(kode):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    semester = request.args.get('semester', type=int)
    kurikulum = (request.args.get('kurikulum') or '').strip()
    ta_param = (request.args.get('ta') or '').strip()
    rps_status = (request.args.get('rps_status') or 'approved').strip().lower()

    ta = _resolve_tahun_ajaran(ta_param)
    if ta_param and not ta:
        return api_error(404, 'tahun_ajaran_not_found', f"Tahun ajaran '{ta_param}' tidak ditemukan.")

    mk_query = MataKuliah.query.filter_by(prodi_id=prodi.id)
    if semester is not None:
        mk_query = mk_query.filter_by(semester=semester)
    if kurikulum:
        mk_query = mk_query.filter(func.lower(MataKuliah.kurikulum) == kurikulum.lower())

    mks = mk_query.order_by(MataKuliah.semester.asc(), MataKuliah.kode.asc()).all()

    data = []
    for mk in mks:
        rps = _find_rps_for_mk(prodi.id, mk.id, ta, rps_status)
        data.append(matakuliah_summary_to_dict(mk, rps=rps))

    return jsonify({
        'data': data,
        'meta': {
            'prodi': prodi.kode,
            'tahun_ajaran': f"{ta.tahun} {ta.semester}" if ta else None,
            'rps_status_filter': rps_status,
            'count': len(data),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/matakuliah/<string:kode_mk>/rubrik', methods=['GET'])
@api_key_required
def detail_matakuliah_rubrik(kode, kode_mk):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    mk = MataKuliah.query.filter(
        MataKuliah.prodi_id == prodi.id,
        func.lower(MataKuliah.kode) == kode_mk.strip().lower(),
    ).first()
    if not mk:
        return api_error(404, 'matakuliah_not_found', f"Mata kuliah '{kode_mk}' tidak ditemukan pada prodi {prodi.kode}.")

    ta_param = (request.args.get('ta') or '').strip()
    rps_status = (request.args.get('rps_status') or 'approved').strip().lower()
    ta = _resolve_tahun_ajaran(ta_param)
    if ta_param and not ta:
        return api_error(404, 'tahun_ajaran_not_found', f"Tahun ajaran '{ta_param}' tidak ditemukan.")

    rps = _find_rps_for_mk(prodi.id, mk.id, ta, rps_status)
    if not rps:
        return api_error(
            404,
            'rps_not_found',
            f"RPS untuk mata kuliah {mk.kode} (status={rps_status}) tidak ditemukan pada tahun ajaran yang diminta.",
        )

    return jsonify({
        'data': build_course_json(rps),
        'meta': {
            'prodi': prodi.kode,
            'tahun_ajaran': f"{rps.tahun_ajaran.tahun} {rps.tahun_ajaran.semester}" if rps.tahun_ajaran else None,
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })


@bp.route('/prodi/<string:kode>/rubrik-courses', methods=['GET'])
@api_key_required
def bulk_rubrik_courses(kode):
    prodi = _get_prodi(kode)
    if not prodi:
        return api_error(404, 'prodi_not_found', f"Program studi '{kode}' tidak ditemukan.")

    semester = request.args.get('semester', type=int)
    kurikulum = (request.args.get('kurikulum') or '').strip()
    ta_param = (request.args.get('ta') or '').strip()
    rps_status = (request.args.get('rps_status') or 'approved').strip().lower()

    ta = _resolve_tahun_ajaran(ta_param)
    if ta_param and not ta:
        return api_error(404, 'tahun_ajaran_not_found', f"Tahun ajaran '{ta_param}' tidak ditemukan.")

    mk_query = MataKuliah.query.filter_by(prodi_id=prodi.id)
    if semester is not None:
        mk_query = mk_query.filter_by(semester=semester)
    if kurikulum:
        mk_query = mk_query.filter(func.lower(MataKuliah.kurikulum) == kurikulum.lower())

    mks = mk_query.order_by(MataKuliah.semester.asc(), MataKuliah.kode.asc()).all()

    courses = []
    for mk in mks:
        rps = _find_rps_for_mk(prodi.id, mk.id, ta, rps_status)
        if rps:
            courses.append(build_course_json(rps))

    return jsonify({
        'data': courses,
        'meta': {
            'prodi': prodi.kode,
            'tahun_ajaran': f"{ta.tahun} {ta.semester}" if ta else None,
            'rps_status_filter': rps_status,
            'count': len(courses),
            'generated_at': _now_iso(),
            'api_version': 'v1',
        },
    })
