from extensions import db
from datetime import datetime

class Panduan(db.Model):
    __tablename__ = 'panduan'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    tipe = db.Column(db.String(10), nullable=False) # 'file' atau 'link'
    file_path = db.Column(db.String(255), nullable=True) 
    link_url = db.Column(db.Text, nullable=True) 
    
    is_aktif = db.Column(db.Boolean, default=True, server_default='1')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Panduan {self.nama}>"