from flask import Blueprint, render_template, request
from flask_login import login_required
from extensions import db
from models import MataKuliah, TahunAjaran

bp = Blueprint('kurikulum', __name__, url_prefix='/kurikulum')

def get_matkul_queryset():
    return db.session.query(MataKuliah).join(
        TahunAjaran, MataKuliah.tahun_ajaran_id == TahunAjaran.id, isouter=True
    )

@bp.route('/matakuliah')
@login_required
def matakuliah():
    # 1. Ambil semua data Tahun Ajaran untuk dropdown filter (Terbaru di atas)
    tahun_ajaran_list = TahunAjaran.query.order_by(TahunAjaran.tahun.desc(), TahunAjaran.semester.asc()).all()

    # 2. Tentukan Default Tahun Ajaran yang sedang Aktif
    default_ta = None
    for ta in tahun_ajaran_list:
        if getattr(ta, 'is_aktif', False) == True:
            default_ta = ta.id
            break
    if not default_ta and tahun_ajaran_list:
        default_ta = tahun_ajaran_list[0].id

    # 3. Ambil parameter filter dari request query string
    # Jika user baru membuka halaman, otomatis memfilter Tahun Ajaran Aktif
    filter_tahun_id = request.args.get('tahun', default=default_ta, type=int)
    search_query = request.args.get('q', '').strip()

    # 4. Jalankan query dasar mata kuliah
    query = get_matkul_queryset()

    # 5. Terapkan Filter Tahun Ajaran (Jika memilih "Semua Tahun", nilai filter_tahun_id akan kosong/0)
    if filter_tahun_id:
        query = query.filter(MataKuliah.tahun_ajaran_id == filter_tahun_id)

    # 6. Terapkan Filter Pencarian Tekstual (By Kode atau Nama)
    if search_query:
        query = query.filter(
            (MataKuliah.kode.ilike(f"%{search_query}%")) | 
            (MataKuliah.nama.ilike(f"%{search_query}%"))
        )

    # 7. Urutkan seluruh data secara lurus: Berdasarkan Kode Matkul (Asc) kemudian Nama (Asc)
    matkuls = query.order_by(MataKuliah.kode.asc(), MataKuliah.nama.asc()).all()

    return render_template(
        'kurikulum/matakuliah.html', 
        matkuls=matkuls,
        list_tahun=tahun_ajaran_list,
        selected_tahun=filter_tahun_id,
        search_query=search_query
    )


@bp.route('/integrated')
@login_required
def integrated():
    return render_template('kurikulum/integrated.html')


@bp.route('/prasyarat')
@login_required
def prasyarat():
    return render_template('kurikulum/prasyarat.html')