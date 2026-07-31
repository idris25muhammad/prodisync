from extensions import db

class TahunAjaran(db.Model):
    __tablename__ = 'tahun_ajaran'

    id        = db.Column(db.Integer, primary_key=True)
    tahun     = db.Column(db.String(20), nullable=False)   # "2025/2026"
    semester  = db.Column(db.String(10), nullable=False)  # "Ganjil" / "Genap"
    is_aktif     = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    def __repr__(self):
        return f"{self.tahun} {self.semester}"