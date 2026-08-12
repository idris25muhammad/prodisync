# ProdiSync

**ProdiSync** adalah sistem manajemen program studi berbasis web untuk mengelola **Semester Lesson Plan (RPS)**, kurikulum, pengumuman, agenda kegiatan, serta arsip dokumen secara terstruktur, aman, dan kolaboratif.

Dibangun dengan **Flask 3.0** (Python), **MySQL 8.0**, **SQLAlchemy ORM**, dan **Jinja2 + Tailwind CSS**, serta mendukung workflow approval dosen &mdash; kaprodi / tim kurikulum.

---

## 🌟 Fitur & Modul Utama

| Modul | Deskripsi |
|---|---|
| **Autentikasi & RBAC** | Login aman (Argon2), role-based access: Kaprodi / Tim Kurikulum & Dosen. |
| **Editor RPS (Tab Wizard)** | 5-tab wizard editor: Identitas & Deskripsi, CLO & SO-PI, Weekly Course Plan (tabel 16 minggu), Sarana & Assessment Plan (multi-metode IABEE), SO Assessment Plan (kriteria PBL), Kesepakatan & Pustaka. |
| **Workflow Approval RPS** | Dosen submit &rarr; Kaprodi approve/reject (dengan alasan). Approved RPS terkunci dari edit. Kaprodi bisa revisi kembali ke draft. |
| **Progress Pengisian RPS** | Perhitungan progres proporsional: weekly plan per minggu, evaluasi per minggu, kriteria penilaian per persentase. |
| **Preview & Print PDF** | Render PDF A4 (xhtml2pdf) dengan cetak browser. Tombol hanya muncul setelah approved. |
| **Katalog Mata Kuliah** | Daftar MK lengkap dengan filter, search, prasyarat, dan integrasi RPS. |
| **Kurikulum Terintegrasi** | Peta kurikulum + aturan prasyarat mata kuliah. |
| **Dashboard Kaprodi & Dosen** | Statistik status workflow (Approved / Submitted / Assigned / Rejected), progress RPS per MK, distribusi per dosen, agenda terdekat. |
| **Pengumuman Prodi** | Publikasi pengumuman (teks + lampiran file). |
| **Agenda & Jadwal** | CRUD agenda kegiatan + tampilan kalender. |
| **Arsip Dokumen** | Unggah & kelola dokumen prodi (akses umum / terbatas per dosen). |
| **Panduan Akademik** | Publikasi panduan (file upload / link eksternal). |
| **Manajemen Pengguna** | Admin akun dosen & kaprodi. |
| **Tahun Ajaran** | CRUD tahun ajaran, set aktif/nonaktif. |
| **Dark Mode** | Tailwind dark theme, toggle, persistent via localStorage. |
| **Mobile-First Responsive** | Bottom tab bar + sheet drawer di mobile, top navbar + dropdown di desktop. |
| **Rejection Reason Display** | Alasan reject tampil di sidebar editor RPS. |

---

## 👥 Aktor & Hak Akses

| Aktor | Hak Akses |
|---|---|
| **Dosen** | Buat & edit RPS mata kuliah sendiri, submit approval, lihat pengumuman/agenda/arsip, cetak PDF (setelah approved). |
| **Kaprodi / Tim Kurikulum** | Akses semua RPS, kelola CPL & SO-PI, approve/reject/revisi RPS, kelola user, kurikulum, pengumuman, agenda, arsip, panduan, tahun ajaran. |

---

## 🏗️ Tech Stack

- **Backend**: Python 3.10+ / Flask 3.0
- **Database**: MySQL 8.0 + SQLAlchemy ORM (PyMySQL)
- **Migration**: Flask-Migrate (Alembic)
- **Auth**: Flask-Login + Argon2
- **PDF**: xhtml2pdf
- **Frontend**: Jinja2 + Tailwind CSS (CDN)
- **WSGI**: Gunicorn

---

## 📦 Petunjuk Instalasi Manual (Ubuntu 22.04 / 24.04)

### Prasyarat

- Ubuntu 22.04 atau 24.04 (fresh)
- Python 3.10+
- MySQL 8.0
- Nginx
- Git

### Step 1 — Update Sistem & Install Dependensi

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx mysql-server libmysqlclient-dev pkg-config
```

### Step 2 — Setup MySQL

```bash
sudo mysql_secure_installation
# Ikuti wizard: set root password, remove anonymous users, disallow remote root, remove test db, reload privileges

sudo mysql -u root -p
```

Di dalam MySQL shell:

```sql
CREATE DATABASE prodisync CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'prodisync'@'localhost' IDENTIFIED BY 'PASSWORD_AMAN_ANDA';
GRANT ALL PRIVILEGES ON prodisync.* TO 'prodisync'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3 — Clone Repository & Setup Virtual Environment

```bash
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/idlabs-polibatam/prodisync.git
sudo chown -R $USER:$USER /var/www/prodisync
cd /var/www/prodisync

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Konfigurasi Environment

```bash
cp .env.example .env
nano .env
```

Isi `.env`:

```
SECRET_KEY=BUAT_SECRET_KEY_RANDOM_MINIMAL_32_KARAKTER
DB_USER=prodisync
DB_PASSWORD=PASSWORD_AMAN_ANDA
DB_HOST=localhost
DB_PORT=3306
DB_NAME=prodisync
KAPRODI_NAMA=Nama Kepala Program Studi
APPLICATION_ROOT=/prodisync
```

### Step 5 — Migrasi Database & Seed Data

```bash
source venv/bin/activate
flask db upgrade
flask seed
```

Akun default setelah seed:

| Username | Password | Role |
|---|---|---|
| `idris` | `idris123` | Dosen |
| `kps` | `kps123` | Kaprodi |

> Ubah password default sebelum production.

### Step 6 — Konfigurasi Gunicorn (Systemd Service)

Buat file service:

```bash
sudo nano /etc/systemd/system/prodisync.service
```

```ini
[Unit]
Description=ProdiSync Flask App (Gunicorn)
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/prodisync
Environment="PATH=/var/www/prodisync/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/var/www/prodisync/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable prodisync
sudo systemctl start prodisync
sudo systemctl status prodisync   # cek status
```

### Step 7 — Konfigurasi Nginx dengan Prefix `/prodisync`

Contoh: domain `example.com`, aplikasi diakses via `https://example.com/prodisync`.

```bash
sudo nano /etc/nginx/sites-available/prodisync
```

```nginx
server {
    listen 80;
    server_name example.com;

    # Redirect HTTP ke HTTPS (jika ada SSL)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate     /etc/ssl/certs/example.com.pem;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    # Root untuk file statis
    location /prodisync/static/ {
        alias /var/www/prodisync/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Storage files (QR, uploads)
    location /prodisync/storage/ {
        alias /var/www/prodisync/storage/;
    }

    # Proxy aplikasi Flask
    location /prodisync/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /prodisync;
        proxy_set_header X-Script-Name /prodisync;
        proxy_redirect off;
    }

    # (Opsional) Halaman statis lain di root domain
    location / {
        root /var/www/html;
        index index.html;
    }
}
```

> **Penting:** Di Flask, tambahkan di `config.py`:
> ```python
> APPLICATION_ROOT = '/prodisync'
> ```
> Atau set environment: `export APPLICATION_ROOT=/prodisync` sebelum menjalankan Gunicorn.

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/prodisync /etc/nginx/sites-enabled/
sudo nginx -t                # test konfigurasi
sudo systemctl reload nginx
```

### Step 8 — Verifikasi

Buka browser: `https://example.com/prodisync`

Login dengan akun default. Semua route otomatis bekerja di bawah prefix `/prodisync` (Flask `url_for` menghormati `APPLICATION_ROOT`).

---

## 🐳 Deployment Docker

Lihat **[DOCKER-DEPLOY.md](DOCKER-DEPLOY.md)** untuk deployment via Docker Compose + Nginx reverse proxy + CI/CD GitHub Actions.

---

## 🗄️ Migrasi Database

Lihat **[FLASK-MIGRATE.md](FLASK-MIGRATE.md)** untuk panduan pembaruan skema database di production.

---

## 🔐 Akun Default (Seed)

| Username | Password | Role |
|---|---|---|
| `idris` | `idris123` | Dosen |
| `kps` | `kps123` | Kaprodi |

> ⚠️ Ganti password default sebelum production.

---

## 🏢 Pengembang

**IDLabs** — Program Studi Rekayasa Keamanan Siber, Politeknik Negeri Batam.