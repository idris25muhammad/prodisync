# ProdiSync

**ProdiSync** adalah sistem manajemen program studi berbasis web yang dirancang untuk memudahkan pengelolaan **Rencana Pembelajaran Semester (RPS)**, kurikulum, pengumuman, agenda, dan arsip dokumen secara terstruktur dan kolaboratif.

Dibangun dengan **Flask** (Python), **MySQL**, dan **Jinja2 Templates**.

---

## Fitur Utama

| Modul | Deskripsi |
|---|---|
| Autentikasi | Login aman dengan hashing password Argon2 |
| RPS | Manajemen Rencana Pembelajaran Semester per mata kuliah |
| Mata Kuliah | Katalog mata kuliah berdasarkan kurikulum |
| Kurikulum | Pengelolaan data kurikulum program studi |
| Tahun Ajaran | Pengaturan tahun ajaran aktif |
| Pengumuman | Sistem pengumuman publik/privat untuk civitas akademika |
| Agenda | Manajemen agenda dan jadwal kegiatan prodi |
| Arsip Dokumen | Pengelolaan dan unduhan arsip dokumen |
| Panduan | Halaman panduan penggunaan sistem |
| Manajemen User | Administrasi akun dosen dan kaprodi |

---

## Tech Stack

- **Backend**: Python 3.10+, Flask 3.0
- **Database**: MySQL 8.x (via SQLAlchemy + PyMySQL)
- **Auth**: Flask-Login + Argon2 Password Hashing
- **Migration**: Flask-Migrate (Alembic)
- **PDF**: xhtml2pdf
- **Template Engine**: Jinja2

---

## Persyaratan Sistem

- Python **3.10** atau lebih baru
- MySQL **8.x**
- pip (Python package manager)
- Git

---

## Panduan Deployment

### 1. Clone Repository

`ash
git clone https://github.com/<username>/prodisync.git
cd prodisync
`

### 2. Buat Virtual Environment

`ash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
`

### 3. Install Dependencies

`ash
pip install -r requirements.txt
`

### 4. Konfigurasi Environment Variables

Salin file contoh lalu isi dengan kredensial Anda:

`ash
cp .env.example .env
`

Edit file .env:

`env
# Flask
SECRET_KEY=ganti_dengan_random_string_yang_sangat_panjang_dan_aman
FLASK_DEBUG=False

# Database MySQL
DB_USER=root
DB_PASSWORD=password_database_anda
DB_HOST=localhost
DB_PORT=3306
DB_NAME=prodisync_db
`

> **Penting:** Generate `SECRET_KEY` yang kuat dengan:
> `ash
> python -c "import secrets; print(secrets.token_hex(32))"
> `

### 5. Buat Database MySQL

`sql
CREATE DATABASE prodisync_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
`

### 6. Jalankan Migrasi Database

`ash
# Jika folder migrations/ sudah ada di repo:
flask db upgrade

# Fresh setup:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
`

### 7. Seed Data Awal

`ash
flask seed-db          # User default & tahun ajaran
flask seed-matakuliah  # Katalog mata kuliah RKS
`

**Akun default setelah seed:**

| Username | Password   | Role    |
|----------|------------|---------|
| `idris`  | `idris123` | Dosen   |
| `kps`    | `kps123`   | Kaprodi |

> **Wajib ganti password** akun default setelah pertama login!

### 8. Jalankan Aplikasi

`ash
flask run
`

Aplikasi berjalan di: **http://localhost:5000**

---

## Deployment Produksi (Gunicorn + Nginx)

### Install & Jalankan Gunicorn

`ash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
`

### Konfigurasi Nginx

`
ginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \System.Management.Automation.Internal.Host.InternalHost;
        proxy_set_header X-Real-IP \;
        proxy_set_header X-Forwarded-For \;
        proxy_set_header X-Forwarded-Proto \;
    }

    location /static {
        alias /path/to/prodisync/static;
        expires 30d;
    }

    location /storage {
        alias /path/to/prodisync/storage;
    }
}
`

### Systemd Service (Linux)

Buat file `/etc/systemd/system/prodisync.service`:

`ini
[Unit]
Description=ProdiSync Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/prodisync
Environment="PATH=/path/to/prodisync/venv/bin"
ExecStart=/path/to/prodisync/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
`

`ash
sudo systemctl daemon-reload
sudo systemctl enable prodisync
sudo systemctl start prodisync
sudo systemctl status prodisync
`

---

## 🐳 Deployment dengan Docker (Direkomendasikan untuk Production)

Setup ini menggunakan **3 container** yang dikelola Docker Compose:

| Container | Image | Peran |
|-----------|-------|-------|
| `prodisync_db` | `mysql:8.0` | Database MySQL |
| `prodisync_app` | Build dari Dockerfile | Flask + Gunicorn |
| `prodisync_nginx` | `nginx:1.25-alpine` | Reverse Proxy |

```
Browser → [Nginx :80] → [Flask/Gunicorn :8000] → [MySQL :3306]
```

### Prasyarat

- Ubuntu Server 22.04 / 24.04 LTS
- Docker Engine + Docker Compose Plugin

### 1. Install Docker di Ubuntu Server

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Jalankan Docker tanpa sudo
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone Repository ke Server

```bash
cd /opt
sudo git clone https://github.com/idris25muhammad/prodisync.git
sudo chown -R $USER:$USER /opt/prodisync
cd /opt/prodisync
```

### 3. Setup File `.env`

```bash
cp .env.example .env
nano .env
```

Isi `.env` untuk production:

```env
SECRET_KEY=isi_dengan_random_string_panjang_tanpa_karakter_dolar
FLASK_DEBUG=False

DB_USER=root
DB_PASSWORD=password_kuat_anda
DB_HOST=db
DB_PORT=3306
DB_NAME=prodisync_db
```

> **Penting:** `DB_HOST` wajib diisi `db` (bukan `localhost`) agar container Flask bisa terhubung ke container MySQL.

Generate `SECRET_KEY` yang aman:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Buat Direktori Storage

```bash
mkdir -p storage && chmod 755 storage
```

### 5. Build & Jalankan Semua Container

```bash
docker compose up --build -d
```

### 6. Verifikasi

```bash
docker compose ps
```

Semua container harus berstatus `running`. Akses aplikasi di: `http://IP_SERVER_ANDA`

### Perintah Berguna

```bash
# Lihat log real-time
docker compose logs -f

# Restart container app
docker compose restart app

# Jalankan migrasi manual
docker compose exec app flask db upgrade

# Masuk ke shell container
docker compose exec app bash

# Stop semua container
docker compose down
```

---

## ⚙️ CI/CD Otomatis dengan GitHub Actions

Setiap `git push` ke branch `main` akan otomatis deploy ke server production.

### Setup (Sekali Saja)

**1. Buat SSH Key di Server**

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/deploy_key -N ""
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys

# Tampilkan private key (copy untuk disimpan di GitHub)
cat ~/.ssh/deploy_key
```

**2. Tambah Secrets di GitHub**

Buka: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `SSH_HOST` | IP server Ubuntu |
| `SSH_USER` | Username Ubuntu (misal: `ubuntu`) |
| `SSH_PRIVATE_KEY` | Isi private key dari langkah 1 |

### Alur Kerja

```
git push origin main
       ↓
GitHub Actions berjalan otomatis
       ↓
SSH ke server → git pull → docker build → flask db upgrade
       ↓
Aplikasi production terupdate! 🎉
```

Pantau status deploy di tab **Actions** pada GitHub repository.

---

## Struktur Direktori

```
prodisync/
├── app.py                  # Application factory & CLI commands
├── config.py               # Konfigurasi aplikasi
├── extensions.py           # Inisialisasi ekstensi Flask
├── requirements.txt        # Daftar dependensi Python
├── .env.example            # Template environment variables
├── Dockerfile              # Docker image untuk Flask app
├── docker-compose.yml      # Orkestrasi 3 container
├── .dockerignore           # Exclude files dari Docker build
├── nginx/
│   └── nginx.conf          # Konfigurasi Nginx reverse proxy
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions CI/CD workflow
├── migrations/             # File migrasi database (Alembic)
├── models/                 # SQLAlchemy Models
├── routes/                 # Flask Blueprints (Controllers)
├── templates/              # Jinja2 HTML Templates
├── static/                 # CSS, JS, Gambar
└── storage/                # File upload (dokumen, dll)
```

---

## CLI Commands

| Perintah | Fungsi |
|---|---|
| `flask init-db` | Membuat semua tabel database |
| `flask seed-db` | Seed data user default & tahun ajaran |
| `flask seed-matakuliah` | Seed katalog mata kuliah RKS |
| `flask db upgrade` | Menerapkan migrasi database terbaru |
| `flask db migrate -m "..."` | Membuat file migrasi baru |

---

## Peran Pengguna

| Role | Akses |
|---|---|
| **Dosen** | Membuat, mengedit, dan melihat RPS milik sendiri |
| **Kaprodi** | Akses penuh: manajemen user, kurikulum, pengumuman, semua RPS |

---

## Catatan Produksi

- Pastikan `FLASK_DEBUG=False` di environment produksi
- Gunakan HTTPS dengan SSL/TLS (disarankan Let's Encrypt)
- Backup database MySQL secara berkala
- File `.env` **jangan di-commit ke Git**
- Pastikan direktori `storage/` memiliki izin tulis:
  `ash
  chmod -R 755 storage/
  chown -R www-data:www-data storage/
  `

---

## Dikembangkan oleh

**IDLabs** — Program Studi Rekayasa Keamanan Siber, Politeknik Negeri Batam