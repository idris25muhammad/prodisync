from extensions import db


class MataKuliah(db.Model):
    """Katalog base mata kuliah — master data per program studi."""
    __tablename__ = 'mata_kuliah'
    __table_args__ = (
        db.UniqueConstraint('prodi_id', 'kode', 'kurikulum', name='uq_matakuliah_prodi_kode_kurikulum'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    prodi_id   = db.Column(db.Integer, db.ForeignKey('prodi.id'), nullable=False)
    kode       = db.Column(db.String(20),  nullable=False)
    nama       = db.Column(db.String(100), nullable=False)
    sks        = db.Column(db.Integer,     nullable=True)   # SKS bawaan kurikulum
    kurikulum  = db.Column(db.String(50),  nullable=True)   # e.g. "v2 IABEE"
    deskripsi  = db.Column(db.Text,        nullable=True)
    tipe       = db.Column(db.String(20),  nullable=True, default='wajib') # 'wajib' / 'pilihan'

    # Penandatangan Kaprodi
    qr_kaprodi             = db.Column(db.String(200), nullable=True)
    tgl_pengesahan_kaprodi = db.Column(db.Date,        nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relasi
    prodi      = db.relationship('Prodi', backref='mata_kuliah_list', lazy=True)
    rps_list   = db.relationship('RPS', backref='matakuliah', lazy=True)

    def __repr__(self):
        return f'<MataKuliah {self.kode} [{self.kurikulum}] - {self.nama}>'