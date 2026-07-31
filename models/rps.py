from extensions import db


class RPS(db.Model):
    """Rencana Pembelajaran Semester — satu per mata kuliah per tahun ajaran."""
    __tablename__ = 'rps'

    id = db.Column(db.Integer, primary_key=True)

    # FK ke katalog base mata kuliah
    matakuliah_id = db.Column(
        db.Integer,
        db.ForeignKey('mata_kuliah.id'),
        nullable=False
    )

    # FK ke tahun ajaran
    tahun_ajaran_id = db.Column(
        db.Integer,
        db.ForeignKey('tahun_ajaran.id'),
        nullable=False
    )

    # FK ke dosen koordinator
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    sks      = db.Column(db.Integer, nullable=False, default=3)
    semester = db.Column(db.Integer, nullable=True,  default=1)
    prasyarat = db.Column(db.String(100), nullable=True)

    # Penandatangan
    qr_kaprodi             = db.Column(db.String(200), nullable=True)
    tgl_pengesahan_kaprodi = db.Column(db.Date,        nullable=True)

    qr_dosen_koor          = db.Column(db.String(200), nullable=True)
    tgl_pengesahan_koor    = db.Column(db.Date,        nullable=True)

    # Data RPS (JSON)
    tp_data    = db.Column(db.JSON, nullable=True)
    rps_detail = db.Column(db.JSON, nullable=True)

    # Workflow
    rps_status = db.Column(
        db.String(20),
        nullable=False,
        default='assigned',
        server_default='assigned'
    )
    reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relasi
    tahun_ajaran = db.relationship('TahunAjaran', backref='rps_list',     lazy=True)
    dosen_koor   = db.relationship('User',        backref='rps_list',     lazy=True)
    # (relasi ke MataKuliah lewat backref 'matakuliah' di models/matakuliah.py)

    def __repr__(self):
        return f'<RPS matakuliah_id={self.matakuliah_id} TA={self.tahun_ajaran_id}>'
