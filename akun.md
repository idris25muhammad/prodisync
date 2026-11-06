# 📋 Daftar Akun Uji Coba (Demo Accounts) - ProdiSync

Berikut adalah daftar akun yang telah disiapkan di database lokal untuk menguji seluruh tingkatan hak akses (**Role-Based Access Control**) dan fitur **Multi-Program Studi**:

---

## 🔑 Tabel Akun Uji Coba

| No | Nama | Username | Password | Role | Program Studi | Hak Akses Utama |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | **Ketua Jurusan** | `kajur` | `kajur123` | **Kajur / Admin** | *Seluruh Jurusan* | Kelola master Program Studi (`/prodi/`), pantau & filter dashboard semua prodi, kelola seluruh user & reset password, approval RPS semua prodi. |
| 2 | **Administrator** | `admin` | `admin123` | **Kajur / Admin** | *Seluruh Jurusan* | Hak akses setara dengan Ketua Jurusan (Super Admin). |
| 3 | **Koordinator Prodi RKS** | `kps` | `kps123` | **KPS / Kaprodi** | **RKS** (Rekayasa Keamanan Siber) | Kelola kurikulum & SO-PI RKS, penugasan Tim Kurikulum, review/approve/revisi RPS RKS, kelola dosen & reset password dosen RKS. |
| 4 | **Jajang Nurjaman** | `jajang` | `jajang123` | **KPS / Kaprodi** | **TRM** (Teknologi Rekayasa Multimedia) | Contoh pengujian isolasi multi-prodi (hanya mengelola data & kurikulum prodi TRM). |
| 5 | **Budi Tim Kurikulum** | `timkur` | `timkur123` | **Tim Kurikulum** | **RKS** (Rekayasa Keamanan Siber) | Input CPL / CLO (Tujuan Pembelajaran), pemetaan SO-PI, serta review RPS MK yang ditugaskan ke dirinya. |
| 6 | **Muhammad Idris** | `idris` | `idris123` | **Tim Kurikulum** | **RKS** (Rekayasa Keamanan Siber) | Akun alternatif Tim Kurikulum & Dosen pengampu RPS RKS. |
| 7 | **Fulan** | `fulan` | `fulan123` | **Dosen** | **RKS** (Rekayasa Keamanan Siber) | Pengampu RPS (mengisi rencana mingguan, evaluasi, kriteria penilaian), submit ke reviewer, lihat catatan revisi, dan export/cetak RPS approved. |

---

## 🧪 Skenario Pengujian yang Dapat Dicoba

### 1. Uji Kelola Program Studi & Multi-Prodi (Login sebagai `kajur`)
- Buka menu **Program Studi** (`/prodi/`) di navbar atas.
- Coba tambahkan Program Studi baru (misal: `TRPL` - *Teknologi Rekayasa Perangkat Lunak*).
- Coba filter dashboard (`/dashboard`) atau katalog mata kuliah (`/matakuliah/`) menggunakan dropdown prodi di bagian atas.
- Buka menu **Manajemen User** (`/users/`), klik ikon kunci 🔑 pada salah satu user untuk mencoba fitur **Reset Password**.

### 2. Uji Workflow RPS Lengkap (Dosen $\rightarrow$ Reviewer $\rightarrow$ Approval)
1. **Login sebagai Dosen (`fulan` / `fulan123`):**
   - Buka menu **Kurikulum $\rightarrow$ Semester Lesson Plan (RPS)** (`/rps/`).
   - Buka editor RPS mata kuliah yang diampu (misal RPS `RKS-301` atau RPS yang ditugaskan).
   - Lengkapi rencana mingguan (tab 3), evaluasi (tab 4), kriteria penilaian 100% (tab 5), lalu klik **Submit for Review**.
2. **Login sebagai KPS / Tim Kurikulum (`kps` / `kps123`):**
   - Buka `/rps/`, pilih RPS yang berstatus *Submitted*.
   - Coba lakukan **Reject** dengan memasukkan catatan revisi (akan muncul toast dan status berubah menjadi *Rejected*).
   - Atau klik **Approve** untuk menyetujui RPS.
3. **Login kembali sebagai Dosen (`fulan`):**
   - Periksa bahwa RPS yang di-approve terkunci dari edit dan tombol **Export JSON** serta **Cetak PDF** sudah aktif.

### 3. Uji Isolasi Data Antar-Prodi (Login sebagai `jajang` vs `kps`)
- Login sebagai `jajang` (Kaprodi TRM), perhatikan bahwa daftar mata kuliah, RPS, dan SO-PI yang tampil terisolasi hanya untuk prodi TRM.
- Buka `/prodi/` (akan muncul halaman 403 Forbidden karena pengelolaan master prodi khusus untuk Kajur).
