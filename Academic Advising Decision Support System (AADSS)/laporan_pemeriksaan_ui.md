# Pemeriksaan aplikasi

- Aplikasi berjalan lokal di http://127.0.0.1:8501.
- Dashboard angkatan 2024 menampilkan 30 mahasiswa; awal semester 5: 8 tanpa peringatan, 15 perlu perhatian, 7 prioritas konsultasi dengan rencana default sesuai batas.
- Nama/NIM, pencarian, filter status dan periode 2–5 diuji menggunakan Streamlit AppTest.
- Detail Naufal pada awal semester 5: 80 SKS lulus, IPS 3,62, IPK 3,56, batas 24 SKS. Rencana 25 SKS memunculkan kelebihan 1 SKS di browser.
- Cek Individu tanpa dataset di browser: IPS 2,50, IPK 3,10, 76 SKS lulus, rencana 19 SKS → batas 18 SKS, kelebihan 1 SKS, estimasi kredit semester 8.
- Formulir tidak memiliki kolom nilai E atau cuti. Catatan syarat kelulusan dan status belum diverifikasi terlihat.
- Pedoman menampilkan aturan, rumus dan unduhan data/sumber.
- Pengujian otomatis mencakup 17 skenario aturan/data dan 6 alur runtime aplikasi; semuanya lulus. Rincian tersimpan di laporan_pengujian.txt.

## Pembaruan interaktif

- Semua 30 NIM telah berganti ke 18724001–18724030, juga pada nilai dan ringkasan.
- Klik batang Prioritas konsultasi di browser menghasilkan filter Prioritas dan 7 mahasiswa, halaman 1/1.
- Tabel diperpendek menjadi Mahasiswa, NIM, IPK, SKS maks., dan Status berwarna. Tidak ada geser horizontal pada panel browser lebar 805 piksel dengan sidebar terbuka.
- Pilihan baris Bima (18724003) di browser membuka halaman Perwalian Mahasiswa dan ringkasan Bima: 37 SKS lulus, IPK 1,49, batas 15 SKS.
- AppTest memeriksa filter kategori, pencarian numerik, hasil kosong, reset semua, pergantian halaman dan pencarian yang mengembalikan halaman pertama.
- Pergantian klik batang di browser: Prioritas (7) → Perhatian (15) → Tanpa peringatan (8) → Prioritas (7); daftar mengikuti setiap pilihan.
- Pencarian 18724003 pada filter Prioritas menghasilkan satu baris Bima; Tampilkan semua memulihkan 30 mahasiswa dan menghapus pencarian.
- Tombol halaman menggunakan label Kembali/Lanjut agar tetap terbaca pada panel sempit. Pratinjau daftar terbaru tersimpan di pratinjau_daftar.png.
