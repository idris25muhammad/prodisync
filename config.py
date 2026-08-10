import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY belum diset di file .env!")

    _db_user = os.environ.get('DB_USER', 'root')
    _db_pass = os.environ.get('DB_PASSWORD', '')
    _db_host = os.environ.get('DB_HOST', 'localhost')
    _db_port = os.environ.get('DB_PORT', '3306')
    _db_name = os.environ.get('DB_NAME', 'prodisync_db')

    SQLALCHEMY_DATABASE_URI     = f'mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Identitas Program Studi
    KAPRODI_NAMA = os.environ.get('KAPRODI_NAMA', 'Maidel Fani')

    # Prefix URL (untuk Nginx reverse proxy, e.g. /prodisync)
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '')