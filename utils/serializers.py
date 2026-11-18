from sqlalchemy.orm import joinedload
from models import StudentOutcome, ProficiencyLevel, so_sort_key


_COURSE_DEFAULT_STUDY_PROGRAM = 'RKS'
_COURSE_DEFAULT_TARGET = 60

_COURSE_CRITERIA_TEMPLATE = [
    (1, 'Sangat Kurang', 0,  30),
    (2, 'Kurang',        31, 55),
    (3, 'Cukup',         56, 70),
    (4, 'Baik',          71, 89),
    (5, 'Sangat Baik',   90, 100),
]

_COURSE_CRITERIA_SUBJECTS = {
    1: 'Hasil {name} sangat minim dan tidak sesuai dengan instruksi yang diberikan.',
    2: 'Hasil {name} kurang lengkap dan terdapat banyak kesalahan pada konsep utama.',
    3: 'Hasil {name} cukup baik, konsep dasar dipahami dengan benar.',
    4: 'Hasil {name} lengkap dan dikerjakan dengan baik, analisis benar dan terstruktur.',
    5: 'Hasil {name} sangat sempurna, analisis mendalam, kritis, dan kreatif.',
}


def parse_sopi_codes(raw):
    """Parse field `tp_data[].sopi` menjadi list `pi_code` unik."""
    codes = []
    for part in (raw or '').split(','):
        part = part.strip()
        if not part:
            continue
        pi_code = part.split('-', 1)[1].strip() if '-' in part else part
        if pi_code and pi_code not in codes:
            codes.append(pi_code)
    return codes


def parse_sopi_pairs(raw):
    """Parse `SO1-PI-01.1, SO1-PI-01.2` menjadi list tuple `(so_code, pi_code)`."""
    pairs = []
    for part in (raw or '').split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            so, pi = part.split('-', 1)
            so, pi = so.strip(), pi.strip()
            if so and pi:
                pairs.append((so, pi))
    return pairs


def load_so_pi_data(prodi_id=None):
    """Load master Student Outcome / Performance Indicator dari database."""
    so_map, pi_map, levels, so_pi_rows = {}, {}, {}, []
    for lvl in ProficiencyLevel.query.order_by(ProficiencyLevel.level.asc()).all():
        levels[lvl.level] = lvl.label

    query = (
        StudentOutcome.query
        .options(joinedload(StudentOutcome.indicators))
        .filter_by(is_active=True)
    )
    if prodi_id:
        query = query.filter_by(prodi_id=prodi_id)

    for so in sorted(query.all(), key=lambda s: so_sort_key(s.so_code)):
        so_map[so.so_code] = so.so_description
        for pi in sorted(so.indicators, key=lambda p: p.pi_code):
            pi_map[pi.pi_code] = {
                'description': pi.pi_description,
                'so_code'    : so.so_code,
                'level'      : pi.level,
            }
            so_pi_rows.append({
                'so_code'        : so.so_code,
                'so_description' : so.so_description,
                'pi_code'        : pi.pi_code,
                'pi_description' : pi.pi_description,
                'level'          : pi.level,
            })

    for row in so_pi_rows:
        row['level_label'] = levels.get(row['level'], '')
    return {'so_map': so_map, 'pi_map': pi_map, 'levels': levels, 'so_pi_rows': so_pi_rows}


def _course_criteria(component_name):
    """Generate rubrik 5 level per komponen dari template."""
    result = []
    for lvl, label, smin, smax in _COURSE_CRITERIA_TEMPLATE:
        label_lower = label.lower()
        result.append({
            'level'    : lvl,
            'label'    : label,
            'score_min': smin,
            'score_max': smax,
            'subjects' : [
                _COURSE_CRITERIA_SUBJECTS[lvl].format(name=component_name),
                f'Secara keseluruhan dinilai {label_lower}.',
            ],
        })
    return result


def build_course_json(rps):
    """Bangun dict course JSON untuk Aplikasi Rubrik Asesmen / export-json."""
    mk = rps.matakuliah
    ta = rps.tahun_ajaran
    prodi = rps.prodi or (mk.prodi if mk else None)

    tp_data = rps.tp_data or []
    kriteria = rps.kriteria_penilaian or []

    ref = load_so_pi_data(prodi_id=rps.prodi_id)

    cpls = []
    for tp in tp_data:
        if not isinstance(tp, dict):
            continue
        pairs = parse_sopi_pairs(tp.get('sopi'))
        so_codes = sorted({so for so, _ in pairs})
        pi_codes = []
        so_pi_pairs = []
        for so_code, pi_code in pairs:
            if pi_code not in pi_codes:
                pi_codes.append(pi_code)
            pi_info = ref['pi_map'].get(pi_code)
            so_pi_pairs.append({
                'so_code': so_code,
                'pi_code': pi_code,
                'level'  : pi_info['level'] if pi_info else None,
            })

        tp_rubric = tp.get('rubric') if isinstance(tp.get('rubric'), dict) else {}
        rubric_out = None
        if tp_rubric:
            rubric_map = {}
            for _, pi_code in pairs:
                pi_info = ref['pi_map'].get(pi_code)
                pi_level = pi_info['level'] if pi_info else 1
                pi_rub = tp_rubric.get(pi_code) if isinstance(tp_rubric.get(pi_code), dict) else {}
                if pi_rub:
                    rubric_map[pi_code] = {
                        str(lvl): (pi_rub.get(str(lvl)) or pi_rub.get(lvl) or None)
                        for lvl in range(1, pi_level + 1)
                    }
                else:
                    rubric_map[pi_code] = None
            if any(v is not None for v in rubric_map.values()):
                rubric_out = rubric_map

        cpls.append({
            'code'             : f"CPL{tp.get('no')}",
            'description'      : tp.get('teks', ''),
            'proficiency_level': tp.get('level', 1),
            'so_codes'         : so_codes,
            'pi_codes'         : pi_codes,
            'so_pi_pairs'      : so_pi_pairs,
            'assessment_rubric': rubric_out,
        })

    kategori_order = []
    komponen_groups = {}
    for k in kriteria:
        komponen = (k.get('komponen') or '').strip()
        if not komponen:
            continue
        if komponen not in komponen_groups:
            komponen_groups[komponen] = []
            kategori_order.append(komponen)
        komponen_groups[komponen].append(k)

    key_map = {
        'Partisipatif': 'partisipatif',
        'Tugas'       : 'tugas',
        'Kuis'        : 'kuis',
        'ATS'         : 'ats',
        'AAS'         : 'aas',
        'Proyek'      : 'proyek',
    }

    categories = []
    for komponen in kategori_order:
        category_key = key_map.get(komponen, komponen.lower())
        components = []
        for sub in komponen_groups[komponen]:
            name = (sub.get('sub_komponen') or '').strip()
            try:
                weight = int(float(sub.get('persentase', 0) or 0))
            except (ValueError, TypeError):
                weight = 0
            if not name:
                name = '-'
                weight = 0
            components.append({
                'name'    : name,
                'weight'  : weight,
                'cpl_pis' : [],
                'criteria': _course_criteria(name),
            })
        categories.append({
            'key'       : category_key,
            'label'     : komponen,
            'components': components,
        })

    return {
        'course_code'      : mk.kode if mk else '',
        'course_name'      : mk.nama if mk else '',
        'sks'              : (mk.sks or 0) if mk else 0,
        'semester_ke'      : rps.semester or (mk.semester if mk else None),
        'semester'         : f"{ta.tahun} {ta.semester}" if ta else '',
        'study_program'    : prodi.kode if prodi else _COURSE_DEFAULT_STUDY_PROGRAM,
        'rps_status'       : rps.rps_status,
        'is_pbl'           : False,
        'target_attainment': _COURSE_DEFAULT_TARGET,
        'categories'       : categories,
        'cpls'             : cpls,
    }


def _iso(dt):
    return dt.isoformat() if dt else None


def prodi_to_dict(prodi):
    return {
        'kode'   : prodi.kode,
        'nama'   : prodi.nama,
        'jenjang': prodi.jenjang,
    }


def tahun_ajaran_to_dict(ta):
    if not ta:
        return None
    return {
        'tahun'   : ta.tahun,
        'semester': ta.semester,
        'label'   : f"{ta.tahun} {ta.semester}",
        'is_aktif': bool(ta.is_aktif),
    }


def level_to_dict(lvl):
    return {
        'level': lvl.level,
        'label': lvl.label,
    }


def pi_to_dict(pi, levels_map=None, so_code=None):
    data = {
        'pi_code'    : pi.pi_code,
        'description': pi.pi_description,
        'level'      : pi.level,
        'level_label': (levels_map or {}).get(pi.level, ''),
        'updated_at' : _iso(pi.updated_at),
    }
    if so_code is not None:
        data['so_code'] = so_code
    return data


def so_to_dict(so, include_pi=False, levels_map=None):
    data = {
        'so_code'    : so.so_code,
        'description': so.so_description,
        'is_active'  : bool(so.is_active),
        'updated_at' : _iso(so.updated_at),
    }
    if include_pi:
        pis = sorted(so.indicators, key=lambda p: p.pi_code)
        data['performance_indicators'] = [pi_to_dict(p, levels_map=levels_map) for p in pis]
    return data


def matakuliah_summary_to_dict(mk, rps=None):
    prasyarat_list = [p.strip() for p in (mk.prasyarat or '').split(',') if p.strip()]
    rps_summary = None
    if rps:
        so_codes = []
        pi_codes = []
        tp_list = [tp for tp in (rps.tp_data or []) if isinstance(tp, dict)]
        for tp in tp_list:
            for so_c, pi_c in parse_sopi_pairs(tp.get('sopi')):
                if so_c not in so_codes:
                    so_codes.append(so_c)
                if pi_c not in pi_codes:
                    pi_codes.append(pi_c)
        ta = rps.tahun_ajaran
        rps_summary = {
            'tahun_ajaran': f"{ta.tahun} {ta.semester}" if ta else None,
            'status'      : rps.rps_status,
            'updated_at'  : _iso(rps.updated_at),
            'so_codes'    : sorted(so_codes, key=so_sort_key),
            'pi_codes'    : pi_codes,
            'clo_count'   : len(tp_list),
        }

    return {
        'kode'      : mk.kode,
        'nama'      : mk.nama,
        'sks'       : mk.sks,
        'semester'  : mk.semester,
        'tipe'      : mk.tipe,
        'kurikulum' : mk.kurikulum,
        'kategori'  : mk.kategori,
        'cdio_skill': mk.cdio_skill,
        'prasyarat' : prasyarat_list,
        'rps'       : rps_summary,
    }
