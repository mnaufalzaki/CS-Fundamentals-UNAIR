# Rencana implementasi yang diwujudkan

Tujuan: mendukung perwalian awal semester S1 Sistem Informasi FST UNAIR dengan batas KRS dan peringatan studi yang dapat ditelusuri.

## Cakupan

- Streamlit lokal, UI Indonesia biru–emas, kurikulum 2021, target 144 SKS.
- 30 mahasiswa sintetis angkatan 2024, nama/NIM dummy, riwayat semester 1–4.
- Dashboard dengan pilihan awal semester 2–5; analisis hanya membaca semester yang telah selesai.
- Detail perwalian dan simulasi total KRS; Cek Individu dari ringkasan KHS tanpa dataset.
- Pedoman, sumber aturan, asumsi, dan status syarat yang belum diverifikasi.
- Tanpa E sebagai input, cuti, login, backend terpisah, ML atau integrasi kampus.

## Implementasi

- Katalog dan nilai merupakan sumber perhitungan IPS/IPK, SKS lulus unik, dan proporsi D.
- Snapshot menyaring waktu sebelum memilih nilai transkrip terbaru, sehingga pengulangan tidak menghapus nilai pada periode terdahulu.
- Mesin yang sama membaca ringkasan dataset maupun input manual.
- Batas SKS berdasarkan IPS KHS; evaluasi 4/8 semester baru diperiksa setelah semester selesai.
- Kategori dari aturan dan estimasi laju kredit; tidak menghasilkan probabilitas kegagalan atau kelulusan resmi.
- Catatan kelulusan selalu terlihat, termasuk tidak boleh E dan SKS D maksimum 20%.
- File proyek, CSV, konfigurasi, sumber PDF, generator, validator dan panduan tersedia dalam folder ini.

## Penerimaan

Seluruh 23 pengujian otomatis lulus; dataset 30 mahasiswa/120 ringkasan lolos validator. Dashboard, detail, formulir manual dan pedoman diperiksa saat runtime. Pemeriksaan manual di browser membuktikan IPS 2,50 memberi batas 18 SKS dan rencana 19 SKS memunculkan kelebihan 1 SKS. Bukti visual tersedia pada pratinjau aplikasi.

## Pembaruan dashboard

NIM 18724001–18724030; grafik kategori dapat dipilih untuk memfilter daftar; satu filter status dan pencarian; tabel ringkas lima kolom dengan warna status dan maksimal 10 baris per halaman; pemilihan baris membuka perwalian; tombol Tampilkan semua menghapus filter.
