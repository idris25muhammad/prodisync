from flask import Flask
from config import Config
from extensions import db, login_manager, migrate
from models import User, TahunAjaran, Panduan, MataKuliah, RPS, Pengumuman, ArsipDokumen, Agenda
from werkzeug.security import generate_password_hash
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes import (
        auth_bp, dashboard_bp, matakuliah_bp, rps_bp, user_bp,
        kurikulum_bp, tahun_ajaran_bp, panduan_bp, pengumuman_bp, arsip_bp, agenda_bp
    )
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tahun_ajaran_bp)
    app.register_blueprint(matakuliah_bp)
    app.register_blueprint(rps_bp)
    app.register_blueprint(kurikulum_bp)
    app.register_blueprint(panduan_bp)
    app.register_blueprint(pengumuman_bp)
    app.register_blueprint(arsip_bp)
    app.register_blueprint(agenda_bp)

    # TA Aktif
    @app.context_processor
    def inject_ta_aktif():
        try:
            ta_aktif = TahunAjaran.query.filter_by(is_aktif=True).first()
        except Exception:
            ta_aktif = None
        return dict(ta_aktif=ta_aktif)

    # ── CLI: flask init-db ──────────────────────────────────────────────────
    @app.cli.command('init-db')
    def init_db():
        """Buat semua tabel database."""
        db.create_all()
        print('✅ Semua tabel berhasil dibuat.')

    # ── CLI: flask seed-db ──────────────────────────────────────────────────
    @app.cli.command('seed-db')
    def seed_db():
        """Seed default data (User & Tahun Ajaran)."""
        if not User.query.first():
            users = [
                User(username='idris', password=ph.hash('idris123'),
                     nama='Muhammad Idris', email='idris@polibatam.ac.id', role='dosen'),
                User(username='kps',   password=ph.hash('kps123'),
                     nama='Koordinator Prodi', email='kps-rks@polibatam.ac.id', role='kaprodi'),
            ]
            db.session.add_all(users)
            db.session.commit()
            print('✅ Data user berhasil diseed.')
        else:
            print('⚠️ Data user sudah ada, seed dilewati.')

        if not TahunAjaran.query.first():
            ta = TahunAjaran(tahun='2026/2027', semester='Ganjil', is_aktif=True)
            db.session.add(ta)
            db.session.commit()
            print('✅ Data Tahun Ajaran berhasil diseed.')
        else:
            print('⚠️ Data Tahun Ajaran sudah ada, seed dilewati.')

        if not Pengumuman.query.first():
            kaprodi = User.query.filter_by(role='kaprodi').first()
            if kaprodi:
                p = Pengumuman(
                    judul='Selamat Datang di ProdiSync!',
                    konten=(
                        '<h2>Selamat Datang di ProdiSync! 🎉</h2>'
                        '<p>Kami dengan bangga memperkenalkan <strong>ProdiSync</strong> — '
                        'sistem manajemen program studi yang dirancang untuk memudahkan pengelolaan '
                        'Rencana Pembelajaran Semester (RPS) dan kurikulum bersama.</p>'
                        '<p>Mari kita majukan prodi bersama dengan kolaborasi yang lebih terstruktur, '
                        'transparan, dan efisien! 🚀</p>'
                        '<p><em>— Tim ProdiSync</em></p>'
                    ),
                    visibility='publik',
                    penulis_id=kaprodi.id,
                )
                db.session.add(p)
                db.session.commit()
                print('✅ Seed pengumuman selamat datang berhasil ditambahkan.')
            else:
                print('⚠️ Tidak ada kaprodi, seed pengumuman dilewati.')
        else:
            print('⚠️ Data pengumuman sudah ada, seed dilewati.')

    # ── CLI: flask seed-matakuliah ───────────────────────────────────────────
    @app.cli.command('seed-matakuliah')
    def seed_matakuliah():
        """Seed katalog base mata kuliah RKS (cek by kode, aman dijalankan ulang)."""
        katalog = [
            # ── Semester 1 ──
            ('RKS-101', 'Fundamental of Cyber Security',   'v2 IABEE',
             'Konsep dasar kerahasiaan, integritas, dan ketersediaan data (CIA Triad), jenis-jenis ancaman/serangan siber umum, vektor serangan, serta arsitektur keamanan informasi dasar.'),
            ('RKS-102', 'Programming and Algorithm',       'v2 IABEE',
             'Pemahaman logika pemrograman mendasar, struktur data, pengondisian, perulangan, serta perancangan algoritma yang efisien menggunakan bahasa pemrograman dasar.'),
            ('RKS-103', 'Linux Fundamental',               'v2 IABEE',
             'Pengenalan arsitektur OS Linux, navigasi terminal/CLI, manajemen berkas dan hak akses (permissions), pengelolaan proses, serta shell scripting dasar.'),
            ('RKS-104', 'Fundamental of Physics',          'v2 IABEE',
             'Prinsip-prinsip fisika terapan yang melandasi perangkat keras komputer, teori gelombang dan sinyal listrik, serta dampaknya pada transmisi data.'),
            ('RKS-105', 'Discrete Mathematics',            'v2 IABEE',
             'Teori logika matematika, logika predikat, teori himpunan, relasi dan fungsi, kombinatorika, serta teori graf yang menjadi fondasi algoritma kriptografi.'),
            ('RKS-106', 'Pancasila Education',             'v2 IABEE',
             'Pemahaman nilai-nilai etika, kewarganegaraan, ideologi negara, dan implikasi moral serta hukum bagi profesional di bidang teknologi.'),
            # ── Semester 2 ──
            ('RKS-201', 'Computer System Administration',  'v2 IABEE',
             'Pengelolaan dan konfigurasi server (Windows/Linux), manajemen user & group, otomatisasi tugas administrasi sistem, serta instalasi infrastruktur layanan dasar.'),
            ('RKS-202', 'Computer Network',                'v2 IABEE',
             'Pemahaman model referensi OSI dan TCP/IP, pengalamatan IP (IPv4/IPv6), subnetting, analisis packet capture, serta prinsip kerja protokol komunikasi dasar.'),
            ('RKS-203', 'Windows Fundamental',             'v2 IABEE',
             'Arsitektur mendalam sistem operasi Windows, pengoperasian utilitas internal (Registry, Event Viewer, Task Manager), manajemen hak akses (ACL/icacls), dan skrip PowerShell dasar.'),
            ('RKS-204', 'Calculus',                        'v2 IABEE',
             'Konsep kalkulus diferensial dan integral terapan untuk pemodelan fungsi matematika, analisis laju perubahan data, dan optimasi algoritma.'),
            ('RKS-205', 'Applied Cryptography',            'v2 IABEE',
             'Penerapan praktis algoritma enkripsi simetris dan asimetris, pembuatan digital signature, fungsi hash, serta arsitektur Public Key Infrastructure (PKI).'),
            ('RKS-206', 'Civic Education',                 'v2 IABEE',
             'Kesadaran hukum, hak dan kewajiban warga negara, tata kelola pemerintahan, serta tanggung jawab sosial profesional IT dalam menjaga ketahanan nasional siber.'),
            # ── Semester 3 ──
            ('RKS-301', 'SOC Essential',                   'v2 IABEE',
             'Operasional dasar Security Operations Center (SOC), teknik monitoring trafik jaringan real-time, agregasi dan analisis log keamanan (SIEM), serta penanganan awal insiden siber.'),
            ('RKS-302', 'Internetworking',                 'v2 IABEE',
             'Konfigurasi dan perancangan jaringan skala menengah/luas, penerapan protokol routing dinamis (RIP, OSPF, BGP), penggunaan VLAN, dan teknik switching terapan.'),
            ('RKS-303', 'Network Defender Essentials',     'v2 IABEE',
             'Strategi pertahanan jaringan aktif dan pasif, penyusunan arsitektur perimetris, penerapan Firewall, serta konfigurasi IDS/IPS untuk pencegahan intrusi.'),
            ('RKS-304', 'Web Fundamental',                 'v2 IABEE',
             'Pengembangan aplikasi berbasis web dasar menggunakan skema client-side (HTML, CSS, JavaScript) dan penyusunan struktur aplikasi web interaktif.'),
            ('RKS-305', 'DevOps',                          'v2 IABEE',
             'Integrasi siklus pengembangan perangkat lunak (development) dan operasional (operations), otomatisasi deployment, pembuatan alur CI/CD, serta kontainerisasi (Docker/Kubernetes).'),
            ('RKS-306', 'Bahasa Indonesia',                'v2 IABEE',
             'Tata cara penyusunan karya ilmiah, penulisan laporan teknis formal, dokumentasi proyek, dan etika komunikasi akademis yang baku.'),
            ('RKS-307', 'Religious Education',             'v2 IABEE',
             'Pembentukan karakter kepemimpinan, norma moral, etika profesionalisme, dan penerapan nilai spiritual dalam kehidupan bermasyarakat dan dunia kerja.'),
            # ── Semester 4 ──
            ('RKS-401', 'Web Application Pentest',         'v2 IABEE',
             'Metodologi pengujian penetrasi pada aplikasi web, identifikasi dan eksploitasi kerentanan perangkat lunak berdasarkan standar OWASP Top 10, serta pembuatan rekomendasi perbaikannya.'),
            ('RKS-402', 'Database Security',               'v2 IABEE',
             'Pengamanan Relational & Non-Relational Database, penerapan enkripsi at-rest/in-transit, kontrol akses granular, pencegahan serangan SQL Injection, dan audit log basis data.'),
            ('RKS-403', 'DevSecOps',                       'v2 IABEE',
             'Penyisipan praktik pengujian dan otomatisasi keamanan (security testing) langsung ke dalam seluruh alur kerja CI/CD (SAST/DAST) sejak tahap awal pengembangan.'),
            ('RKS-404', 'Threat Intelligence Essential',   'v2 IABEE',
             'Pengumpulan, pengolahan, dan analisis indikator kompromi (IoC) serta taktik penyerang (TTPs) untuk memprediksi dan merespons ancaman siber secara proaktif.'),
            ('RKS-405', 'Cyber Security Risk and Management', 'v2 IABEE',
             'Kerangka kerja penilaian risiko (Risk Assessment Frameworks), penyusunan matriks dampak dan ancaman, serta analisis mitigasi risiko TI organisasi.'),
            ('RKS-406', 'General English',                 'v2 IABEE',
             'Penguatan kemampuan tata bahasa (grammar), membaca teks teknis (reading comprehension), serta kemampuan menyimak teknis dalam konteks bahasa Inggris.'),
            # ── Semester 5 ──
            ('RKS-501', 'Ethical Hacking',                 'v2 IABEE',
             'Tahapan peretasan secara etis (rekonaisans, pemindaian, gaining access, maintaining access), eksploitasi kerentanan sistem terstruktur, serta pembuatan penetration testing report.'),
            ('RKS-502', 'Mobile Security',                 'v2 IABEE',
             'Identifikasi dan pengujian keamanan pada platform mobile (Android/iOS), reverse engineering aplikasi seluler, penanganan kebocoran data, dan manipulasi runtime.'),
            ('RKS-503', 'Cloud Computing Security',        'v2 IABEE',
             'Prinsip pengamanan infrastruktur komputasi awan (AWS/Azure/GCP), konfigurasi Identity and Access Management (IAM), isolasi workload, dan pengamanan arsitektur multi-tenant.'),
            ('RKS-504', 'Digital Forensic',                'v2 IABEE',
             'Teknik akuisisi data (imaging), identifikasi bukti digital pada RAM/disk/media penyimpanan, rekonstruksi kronologi insiden, dan penyiapan barang bukti berbasis standar legal (chain of custody).'),
            ('RKS-505', 'Business Continuity Management',  'v2 IABEE',
             'Perancangan strategi Business Continuity Plan (BCP) dan Disaster Recovery Plan (DRP) untuk meminimalkan downtime operasional saat terjadi krisis siber.'),
            ('RKS-506', 'English Communication',           'v2 IABEE',
             'Pelatihan komunikasi lisan secara profesional, teknik presentasi teknis di depan pemangku kepentingan, dan simulasi diskusi interaktif dalam bahasa Inggris.'),
            ('RKS-507', 'Entrepreneurship',                'v2 IABEE',
             'Perancangan ide bisnis baru, pembentukan startup berbasis teknologi, validasi pasar, penyusunan pitch deck, dan analisis kelayakan keuangan.'),
            # ── Semester 6 ──
            ('RKS-601', 'Cyber Security Project',          'v2 IABEE',
             'Proyek berbasis tim untuk memecahkan masalah keamanan siber dunia nyata, mencakup tahap audit, perancangan arsitektur keamanan, hingga implementasi solusi.'),
            ('RKS-602', 'IoT Security',                    'v2 IABEE',
             'Keamanan ekosistem Internet of Things, ekstraksi firmware, analisis protokol komunikasi (MQTT/CoAP), mitigasi serangan tingkat hardware, dan pengamanan komunikasi sensor-cloud.'),
            ('RKS-603', 'Statistic and Probability',       'v2 IABEE',
             'Pengolahan data statistik kuantitatif, analisis teoretis peluang kejadian, pemodelan data inferensial, serta penerapannya dalam evaluasi sistem.'),
            ('RKS-604', 'Cyber Security Law and Ethics',   'v2 IABEE',
             'Pembahasan regulasi dan perundang-undangan hukum siber (seperti UU ITE, UU PDP, GDPR), etika profesi cybersecurity, serta implikasi tanggung jawab hukum.'),
            ('RKS-605', 'Research Methodology',            'v2 IABEE',
             'Penyusunan metodologi penelitian ilmiah, penentuan research gap, teknik studi literatur, serta pembuatan kerangka kerja penulisan proposal skripsi/tugas akhir.'),
            ('RKS-606', 'Cyber Security Policy and Audit', 'v2 IABEE',
             'Teknik penyusunan dokumen kebijakan keamanan organisasi, pelaksanaan audit berbasis standar ISO/IEC 27001 atau NIST, dan evaluasi tingkat kepatuhan (compliance).'),
            ('RKS-607', 'AI for Cybersecurity',            'v2 IABEE',
             'Penerapan Machine Learning dan algoritma kecerdasan buatan untuk otomatisasi deteksi anomali trafik, analisis perilaku penyerang (UEBA), dan klasifikasi malware.'),
            # ── Semester 7 ──
            ('RKS-701', 'Industrial Internship',           'v2 IABEE',
             'Pelaksanaan kerja praktik lapangan secara langsung di industri/perusahaan mitra untuk menerapkan keterampilan teknis dan profesional siber di lingkungan profesional nyata.'),
            ('RKS-702', 'Scientific Writing',              'v2 IABEE',
             'Penyusunan naskah artikel ilmiah berbasis riset, penyesuaian format publikasi jurnal/konferensi teknis, dan etika pengutipan (anti-plagiarism).'),
            ('RKS-703', 'Final Project Proposal',          'v2 IABEE',
             'Perancangan awal, penyusunan dokumen latar belakang, metodologi, dan uji sidang proposal untuk riset atau produk Tugas Akhir.'),
            # ── Semester 8 ──
            ('RKS-801', 'Final Project',                   'v2 IABEE',
             'Eksekusi penuh riset ilmiah atau pembangunan produk keamanan siber mandiri, pengujian solusi, pengolahan data hasil riset, serta pengujian pada sidang Tugas Akhir.'),
            ('RKS-802', 'English for Workspace Communication', 'v2 IABEE',
             'Persiapan bahasa Inggris untuk lingkungan kerja profesional, mencakup simulasi wawancara kerja, penulisan resume/cover letter, dan korespondensi bisnis formal.'),
            ('RKS-803', 'Internship Report',               'v2 IABEE',
             'Penyusunan dokumen pertanggungjawaban ilmiah dari hasil magang industri, presentasi laporan, serta evaluasi capaian kinerja dari penyelia kerja.'),
        ]

        inserted = 0
        skipped  = 0
        for kode, nama, kurikulum, deskripsi in katalog:
            if MataKuliah.query.filter_by(kode=kode, kurikulum=kurikulum).first():
                skipped += 1
                continue
            db.session.add(MataKuliah(kode=kode, nama=nama, kurikulum=kurikulum, deskripsi=deskripsi))
            inserted += 1

        db.session.commit()
        print(f'✅ Seed matakuliah selesai: {inserted} ditambahkan, {skipped} dilewati (sudah ada).')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)