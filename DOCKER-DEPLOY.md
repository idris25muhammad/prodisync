# 🐳 Panduan Deployment Docker Container di Ubuntu Server

Dokumen ini menjelaskan tata cara deployment aplikasi **ProdiSync** di server **Ubuntu (22.04 / 24.04 LTS)** menggunakan **Docker Compose** dan **Host Nginx** sebagai Master Reverse Proxy.

---

## 🏛️ Arsitektur Deployment

Pada setup ini, container reverse proxy internal telah dihapus. Host Nginx pada OS Ubuntu bertindak langsung sebagai Master Reverse Proxy yang meneruskan trafik Web ke container aplikasi Flask (`prodisyncapp`).

```
                              [ Browser Pengguna ]
                                       │ (Port 80 / 443)
                                       ▼
                       ┌───────────────────────────────┐
                       │  Host Nginx (Ubuntu Server)   │
                       └───────────────┬───────────────┘
                                       │
                Forwarding ke http://127.0.0.1:8000 (/prodisync/)
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                            DOCKER CONTAINERS                              │
 │                                                                           │
 │  ┌─────────────────────────────────┐   ┌───────────────────────────────┐  │
 │  │   prodisyncapp (Flask/Gunicorn) │───│    prodisyncdb (MySQL 8.0)    │  │
 │  │   Port: 127.0.0.1:8000:8000     │   │    Internal Port: 3306        │  │
 │  └─────────────────────────────────┘   └───────────────────────────────┘  │
 └───────────────────────────────────────────────────────────────────────────┘
```

### Penamaan Container & Service Docker:

| Service Docker | Nama Container | Deskripsi | Port Binding |
|---|---|---|---|
| `prodisyncdb` | `prodisyncdb` | Database Engine MySQL 8.0 | `3307:3306` (Localhost) |
| `prodisyncapp` | `prodisyncapp` | Web Application (Flask + Gunicorn WSGI) | `127.0.0.1:8000:8000` |

---

## 📋 Prasyarat Server

1. **Ubuntu Server 22.04 LTS / 24.04 LTS**.
2. **Docker Engine & Docker Compose Plugin** terinstall:
   ```bash
   sudo apt update
   sudo apt install -y ca-certificates curl gnupg
   # Pastikan docker dan docker compose versi terbaru sudah aktif
   docker --version
   docker compose version
   ```
3. **Host Nginx Web Server**:
   ```bash
   sudo apt install -y nginx
   ```

---

## 🚀 Langkah-Langkah Deployment

### 1. Clone Repository ke Server

Letakkan kode aplikasi pada direktori `/opt/prodisync`:

```bash
cd /opt
sudo git clone https://github.com/idris25muhammad/prodisync.git
sudo chown -R $USER:$USER /opt/prodisync
cd /opt/prodisync
```

---

### 2. Setup Environment Variable (`.env`)

Salin berkas contoh `.env.example` ke `.env`:

```bash
cp .env.example .env
nano .env
```

Sesuaikan konfigurasi `.env` untuk lingkungan produksi:

```env
# Flask Configuration
SECRET_KEY=ganti_dengan_string_random_panjang_dan_aman_32_karakter
FLASK_DEBUG=False

# Database Configuration (Wajib DB_HOST=prodisyncdb)
DB_USER=prodisync_user
DB_PASSWORD=Password_Sangat_Kuat_123!
DB_HOST=prodisyncdb
DB_PORT=3306
DB_NAME=prodisync_db
```

> ⚠️ **Penting:** Parameter `DB_HOST` wajib diisi `prodisyncdb` agar container `prodisyncapp` dapat berkomunikasi dengan container database `prodisyncdb` di dalam jaringan internal Docker.

Untuk menghasilkan `SECRET_KEY` yang aman:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### 3. Build & Menjalankan Container

Jalankan Docker Compose dalam mode detached:

```bash
docker compose up --build -d
```

Saat container `prodisyncapp` pertama kali berjalan, entrypoint script akan secara otomatis mengeksekusi:
1. `flask db upgrade` (Menjalankan migrasi Alembic terbaru).
2. `flask seed-db` (Menyiapkan data akun default & tahun ajaran).
3. `flask seed-matakuliah` (Menyiapkan data awal katalog mata kuliah).
4. Menjalankan Gunicorn WSGI Server pada port internal `8000`.

Cek status container yang sedang berjalan:
```bash
docker compose ps
```

---

### 4. Konfigurasi Host Nginx Reverse Proxy

Buat berkas konfigurasi Nginx baru pada Host Ubuntu:

```bash
sudo nano /etc/nginx/sites-available/prodisync
```

Masukkan konfigurasi berikut (contoh routing sub-path `/prodisync/`):

```nginx
server {
    listen 80;
    server_name _; # Ganti dengan domain/IP server Anda jika ada

    client_max_body_size 20M;

    # 1. Option: Redirect root URL ke portal utama
    location = / {
        return 301 https://if.polibatam.ac.id/rekayasa-keamanan-siber/;
    }

    # 2. Forwarding /prodisync/ ke Container App (prodisyncapp)
    location /prodisync/ {
        proxy_pass http://127.0.0.1:8000/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;

        # Buffer settings
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
}
```

Aktifkan konfigurasi Nginx dan reload service:

```bash
sudo ln -s /etc/nginx/sites-available/prodisync /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Aplikasi kini dapat diakses melalui browser pada `http://<IP_SERVER>/prodisync/`.

---

## 🔄 Otomatisasi CI/CD dengan GitHub Actions

Repository ini sudah dilengkapi dengan workflow GitHub Actions pada [.github/workflows/deploy.yml](file:///.github/workflows/deploy.yml). Setiap kali ada perintah `git push` ke branch `main`, GitHub Actions akan otomatis melakukan deployment ke server.

### Langkah Inisialisasi SSH Key:

1. **Buat Key Pair SSH di Server Ubuntu:**
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-prodisync" -f ~/.ssh/deploy_key -N ""
   cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys
   ```

2. **Salin Private Key:**
   ```bash
   cat ~/.ssh/deploy_key
   ```

3. **Daftarkan Secrets pada Repository GitHub:**
   Buka **Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**:
   - `SSH_HOST`: IP Public Server Ubuntu
   - `SSH_USER`: Username pengguna SSH server (misal: `ubuntu` atau `root`)
   - `SSH_PRIVATE_KEY`: Isi konten private key ed25519 yang telah disalin

Workflow akan mengeksekusi perintah berikut di server secara otomatis:
```bash
cd /opt/prodisync
git pull origin main
docker compose up --build -d prodisyncapp
docker compose exec -T prodisyncapp flask db upgrade
```

---

## 🛠️ Perintah Maintenance Docker

Berikut daftar perintah yang sering digunakan untuk pemeliharaan container:

- **Melihat log real-time container aplikasi:**
  ```bash
  docker compose logs -f prodisyncapp
  ```
- **Melihat log container database:**
  ```bash
  docker compose logs -f prodisyncdb
  ```
- **Restart container aplikasi:**
  ```bash
  docker compose restart prodisyncapp
  ```
- **Menjalankan migrasi database secara manual di container:**
  ```bash
  docker compose exec prodisyncapp flask db upgrade
  ```
- **Menjalankan perintah CLI seed manual:**
  ```bash
  docker compose exec prodisyncapp flask seed-db
  ```
- **Menghentikan seluruh container:**
  ```bash
  docker compose down
  ```
- **Menghentikan & menghapus volume data database (HATI-HATI):**
  ```bash
  docker compose down -v
  ```
