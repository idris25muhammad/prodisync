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
    prodi_id           = db.Column(db.Integer, db.ForeignKey('prodi.id'), nullable=True)
    prodi              = db.Column(db.String(100), nullable=True)  # string cadangan / legacy
    jabatan_fungsional = db.Column(db.String(100), nullable=True)
    bidang_keahlian    = db.Column(db.Text, nullable=True)
    homepage_url       = db.Column(db.String(255), nullable=True)
    foto_url           = db.Column(db.String(255), nullable=True)

    created_at         = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at         = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relasi ke Prodi
    prodi_rel          = db.relationship('Prodi', foreign_keys=[prodi_id], backref='dosen_list', lazy=True)

    @property
    def is_kaprodi(self):
        return self.role in ('kps', 'kaprodi')

    @property
    def is_kps(self):
        return self.role in ('kps', 'kaprodi')

    @property
    def is_timkur(self):
        return self.role == 'timkur'

    @property
    def is_kajur(self):
        return self.role in ('kajur', 'admin')

    @property
    def can_manage_prodi(self):
        return self.role in ('kajur', 'admin')

    @property
    def can_manage_kurikulum(self):
        return self.role in ('kajur', 'admin', 'kps', 'kaprodi', 'timkur')

    @property
    def role_label(self):
        labels = {
            'kajur': 'Kajur / Admin',
            'admin': 'Kajur / Admin',
            'kps': 'KPS',
            'kaprodi': 'KPS',
            'timkur': 'Tim Kurikulum',
            'dosen': 'Dosen'
        }
        return labels.get(self.role, self.role.capitalize())

    def can_review_rps(self, rps):
        """
        Kajur/Admin: bisa review semua RPS.
        KPS/Kaprodi: bisa review RPS di prodinya.
        Tim Kurikulum: bisa review jika ditugaskan sebagai reviewer MK (created_by) di RPS tersebut.
        """
        if self.is_kajur:
            return True
        if self.is_kaprodi and (rps.prodi_id == self.prodi_id or not self.prodi_id):
            return True
        if self.is_timkur and rps.created_by == self.id:
            return True
        return False

    def can_edit_rps(self, rps):
        if self.is_kajur:
            return True
        if self.is_kaprodi and (rps.prodi_id == self.prodi_id or not self.prodi_id):
            return True
        if self.is_timkur and rps.created_by == self.id:
            return True
        if rps.user_id == self.id:
            return True
    def can_manage_so(self, so):
        """
        Kajur/Admin: bisa kelola semua SO & PI di semua prodi.
        KPS: hanya bisa kelola SO & PI prodi masing-masing, atau jika dia pembuat SO tersebut.
        Bisa melihat SO-PI prodi lain tapi tidak bisa edit dan hapus kecuali pembuatnya.
        """
        if self.is_kajur:
            return True
        prodi_id = getattr(so, 'prodi_id', None)
        created_by = getattr(so, 'created_by', None)
        if created_by and created_by == self.id:
            return True
        if self.prodi_id and prodi_id == self.prodi_id:
            if self.is_kaprodi:
                return True
            if self.is_timkur and (created_by == self.id or created_by is None):
                return True
        return False

    @property
    def prodi_nama(self):
        if self.prodi_rel:
            return self.prodi_rel.nama
        return self.prodi or ''