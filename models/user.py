from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id                 = db.Column(db.Integer, primary_key=True)
    username           = db.Column(db.String(50), unique=True, nullable=False)
    password           = db.Column(db.String(255), nullable=False)
    nama               = db.Column(db.String(100), nullable=False)
    email              = db.Column(db.String(100))
    role               = db.Column(db.String(20), nullable=False, default='dosen')  # 'dosen' | 'kaprodi'

    nidn               = db.Column(db.String(30), unique=True, nullable=True)
    nip                = db.Column(db.String(30), unique=True, nullable=True)
    sinta_id           = db.Column(db.String(30), nullable=True)
    google_scholar_id  = db.Column(db.String(100), nullable=True)
    google_scholar_url = db.Column(db.String(255), nullable=True)
    orcid_id           = db.Column(db.String(30), nullable=True)
    scopus_id          = db.Column(db.String(50), nullable=True)
    researcher_id      = db.Column(db.String(50), nullable=True)
    garuda_id          = db.Column(db.String(50), nullable=True)

    afiliasi           = db.Column(db.String(150), nullable=True)
    prodi              = db.Column(db.String(100), nullable=True)
    jabatan_fungsional = db.Column(db.String(100), nullable=True)
    bidang_keahlian    = db.Column(db.Text, nullable=True)
    homepage_url       = db.Column(db.String(255), nullable=True)
    foto_url           = db.Column(db.String(255), nullable=True)

    created_at         = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at         = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    @property
    def is_kaprodi(self):
        return self.role == 'kaprodi'