from extensions import db


class Prodi(db.Model):
    """Model master Program Studi untuk mendukung multi-prodi."""
    __tablename__ = 'prodi'

    id          = db.Column(db.Integer, primary_key=True)
    kode        = db.Column(db.String(20), unique=True, nullable=False)   # e.g. 'RKS'
    nama        = db.Column(db.String(100), nullable=False)               # e.g. 'Rekayasa Keamanan Siber'
    jenjang     = db.Column(db.String(10), nullable=False, default='D4')  # e.g. 'D4', 'D3'
    kaprodi_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_aktif    = db.Column(db.Boolean, nullable=False, default=True)

    created_at  = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at  = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relasi ke kaprodi penanggung jawab
    kaprodi     = db.relationship('User', foreign_keys=[kaprodi_id], backref='prodi_dipimpin', lazy=True)

    def __repr__(self):
        return f'<Prodi {self.kode} - {self.nama}>'
