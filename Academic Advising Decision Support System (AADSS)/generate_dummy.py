"""Data sintetis dari riwayat mata kuliah; ringkasan tidak dibuat secara acak."""
import json
from pathlib import Path
import random
import pandas as pd
from academic import ROOT, RULES, max_credits, semester_summary

NAMES = ['Naufal Pratama', 'Alya Rahma', 'Bima Saputra', 'Dinda Maharani', 'Rafi Aditya',
         'Salsabila Putri', 'Fajar Ramadhan', 'Nadia Azzahra', 'Arga Wijaya', 'Intan Permata',
         'Rizky Maulana', 'Citra Lestari', 'Dimas Arya', 'Zahra Amalia', 'Farhan Akbar',
         'Tiara Anindya', 'Bagas Wicaksono', 'Nabila Safira', 'Kevin Mahendra', 'Putri Larasati',
         'Ilham Fauzan', 'Vina Oktaviani', 'Reza Firmansyah', 'Sinta Dewi', 'Galih Prakoso',
         'Hana Kirana', 'Yoga Pratama', 'Amira Nadhira', 'Aditya Nugraha', 'Dea Febrianti']

FIRST_NAMES = ['Arief', 'Bella', 'Cahya', 'Danu', 'Eka', 'Faris', 'Gita', 'Hadi', 'Indah', 'Joko',
               'Kartika', 'Lutfi', 'Maya', 'Nanda', 'Oki', 'Pandu', 'Qori', 'Rangga', 'Shania', 'Tegar',
               'Ulfah', 'Vino', 'Winda', 'Yusuf', 'Zaki', 'Anisa', 'Bayu', 'Chandra', 'Dewi', 'Erlangga']
LAST_NAMES = ['Setiawan', 'Kusuma', 'Pradana', 'Wibowo', 'Lestari', 'Hidayat', 'Nugroho', 'Sari',
              'Purnama', 'Santoso', 'Wijaya', 'Permana', 'Utami', 'Hakim', 'Putra', 'Rahmawati']

PROFILES = ['Konsisten', 'IPS menurun', 'Progres tertinggal', 'Konsisten', 'Pemulihan nilai',
            'Progres lambat', 'IPK rendah', 'D berlebih']

CONSIDERATIONS = {
    'Konsisten': 'Progres studi sesuai target; KRS disetujui hingga batas maksimum SKS.',
    'IPS menurun': 'IPS menurun bertahap; disarankan pembatasan beban SKS dan evaluasi metode belajar.',
    'Progres tertinggal': 'SKS kumulatif di bawah batas Evaluasi I (40 SKS) dan estimasi > 14 semester; diusulkan evaluasi akademik fakultas.',
    'Pemulihan nilai': 'Sedang memperbaiki mata kuliah bernilai D; pantau kelulusan mata kuliah ulang.',
    'Progres lambat': 'Laju kredit di bawah 18 SKS/semester; perlu perencanaan mata kuliah wajib agar lulus tepat waktu.',
    'IPK rendah': 'IPK di bawah 2,00 pada Evaluasi I; diusulkan surat peringatan tertulis pimpinan fakultas dan pembinaan.',
    'D berlebih': 'Proporsi nilai D melebihi 20% SKS lulus; wajib mengulang mata kuliah bernilai D pada semester berikutnya.',
}

FST_STRUCTURE = {
    'fakultas': 'Fakultas Sains dan Teknologi (FST)',
    'universitas': 'Universitas Airlangga',
    'kampus': 'Kampus C UNAIR Mulyorejo, Surabaya 60115',
    'pimpinan': {
        'dekan': {
            'nama': 'Prof. Dr. Miratul Khasanah, M.Si.',
            'nip': '196703041992032001',
            'jabatan': 'Dekan Fakultas Sains dan Teknologi',
            'periode': '2025-2030 (lanjutan 2022-2025)',
            'departemen_asal': 'Departemen Kimia',
        },
        'wakil_dekan': [
            {'jabatan': 'Wakil Dekan I (Bidang Akademik dan Kemahasiswaan)', 'nama': 'Dr. Eridani, M.Si.'},
            {'jabatan': 'Wakil Dekan II (Bidang Sumber Daya dan Keuangan)', 'nama': 'Prof. Dr. Suryani Dyah Astuti, M.Si.'},
            {'jabatan': 'Wakil Dekan III (Bidang Riset, Inovasi, dan Komunitas)', 'nama': 'Prof. Dr. Fatmawati, M.Si.'},
        ],
    },
    'departemen': [
        {
            'nama': 'Departemen Matematika',
            'ketua': 'Dr. Herry Suprajitno, M.Si.',
            'prodi_s1': ['S1 Matematika', 'S1 Statistika', 'S1 Sistem Informasi'],
            'prodi_pascasarjana': ['S2 Matematika'],
        },
        {
            'nama': 'Departemen Fisika',
            'ketua': 'Herri Trilaksana, Ph.D.',
            'prodi_s1': ['S1 Fisika', 'S1 Teknik Biomedis'],
            'prodi_pascasarjana': ['S2 Teknik Biomedis'],
        },
        {
            'nama': 'Departemen Kimia',
            'ketua': 'Moh. Zakki Fahmi, Ph.D.',
            'prodi_s1': ['S1 Kimia'],
            'prodi_pascasarjana': ['S2 Kimia'],
        },
        {
            'nama': 'Departemen Biologi',
            'ketua': 'Prof. Dr. Sri Puji Astuti, M.Si.',
            'prodi_s1': ['S1 Biologi', 'S1 Teknik Lingkungan'],
            'prodi_pascasarjana': ['S2 Biologi'],
        },
    ],
    'prodi_s1': [
        {
            'prodi': 'S1 Sistem Informasi',
            'departemen': 'Departemen Matematika',
            'prefix_nim': '18724',
            'kps': 'Dr. Bambang Setiawan, S.Kom., M.Kom.',
            'dosen_wali': [
                'Dr. Hendra Kusuma, S.Kom., M.Kom.',
                'Dr. Ratna Sari, S.Si., M.T.',
                'Arif Wibowo, S.Kom., M.Sc.',
            ],
            'jumlah_mahasiswa': 30,
            'ada_prioritas': True,
        },
        {
            'prodi': 'S1 Matematika',
            'departemen': 'Departemen Matematika',
            'prefix_nim': '18124',
            'kps': 'Dr. Dian Purnamasari, S.Si., M.Si.',
            'dosen_wali': [
                'Dr. Agung Prabowo, S.Si., M.Si.',
                'Lestari Handayani, S.Si., M.Sc.',
                'Dr. Wahyu Hidayat, S.Si., M.Si.',
            ],
            'jumlah_mahasiswa': 27,
            'ada_prioritas': True,
        },
        {
            'prodi': 'S1 Statistika',
            'departemen': 'Departemen Matematika',
            'prefix_nim': '18824',
            'kps': 'Dr. Eko Tjahjono, S.Si., M.Si.',
            'dosen_wali': [
                'Dr. Nurul Hidayati, S.Si., M.Si.',
                'Bagus Santoso, S.Stat., M.Si.',
                'Dr. Rina Kusumawati, S.Si., M.Sc.',
            ],
            'jumlah_mahasiswa': 30,
            'ada_prioritas': False,
        },
        {
            'prodi': 'S1 Fisika',
            'departemen': 'Departemen Fisika',
            'prefix_nim': '18224',
            'kps': 'Dr. Andi Rahmanto, S.Si., M.Si.',
            'dosen_wali': [
                'Dr. Budi Darmawan, S.Si., M.Si.',
                'Siti Aminah, S.Si., M.Sc.',
                'Dr. Taufik Hidayat, S.Si., M.T.',
            ],
            'jumlah_mahasiswa': 24,
            'ada_prioritas': True,
        },
        {
            'prodi': 'S1 Teknik Biomedis',
            'departemen': 'Departemen Fisika',
            'prefix_nim': '18624',
            'kps': 'Dr. Rr. Retno Widyowati, S.Si., M.T.',
            'dosen_wali': [
                'Dr. Fajar Nugroho, S.T., M.T.',
                'Maya Puspita, S.T., M.Sc.',
                'Dr. Irfan Hakim, S.Si., M.T.',
            ],
            'jumlah_mahasiswa': 27,
            'ada_prioritas': False,
        },
        {
            'prodi': 'S1 Kimia',
            'departemen': 'Departemen Kimia',
            'prefix_nim': '18324',
            'kps': 'Dr. Yanuardi Raharjo, S.Si., M.Sc.',
            'dosen_wali': [
                'Dr. Dewi Kurniawati, S.Si., M.Si.',
                'Hendra Wijaya, S.Si., M.Sc.',
                'Dr. Lukman Hakim, S.Si., M.Si.',
            ],
            'jumlah_mahasiswa': 27,
            'ada_prioritas': True,
        },
        {
            'prodi': 'S1 Biologi',
            'departemen': 'Departemen Biologi',
            'prefix_nim': '18424',
            'kps': 'Dr. Dwi Winarni, S.Si., M.Si.',
            'dosen_wali': [
                'Dr. Rini Puspitasari, S.Si., M.Si.',
                'Ahmad Fauzi, S.Si., M.Sc.',
                'Dr. Kartika Sari, S.Si., M.Si.',
            ],
            'jumlah_mahasiswa': 30,
            'ada_prioritas': False,
        },
        {
            'prodi': 'S1 Teknik Lingkungan',
            'departemen': 'Departemen Biologi',
            'prefix_nim': '18524',
            'kps': 'Dr. Nur Indradewi Oktavitri, S.T., M.T.',
            'dosen_wali': [
                'Dr. Dedi Setiawan, S.T., M.T.',
                'Wulan Dari, S.T., M.Sc.',
                'Dr. Rahmat Hidayat, S.T., M.T.',
            ],
            'jumlah_mahasiswa': 27,
            'ada_prioritas': True,
        },
    ],
    'prodi_s2': ['S2 Biologi', 'S2 Teknik Biomedis', 'S2 Kimia', 'S2 Matematika'],
    'prodi_s3': ['S3 MIPA'],
    'prodi_prioritas_unair_lain': [
        {
            'fakultas': 'FTMM',
            'nama_fakultas': 'Fakultas Teknologi Maju dan Multidisiplin',
            'departemen': 'Departemen Teknik',
            'prodi': 'S1 Sains Data',
            'prefix_nim': '16224',
            'kps': 'Dr. Hendri Susilo, S.Si., M.Kom.',
            'jumlah_mahasiswa': 30,
        },
        {
            'fakultas': 'FTMM',
            'nama_fakultas': 'Fakultas Teknologi Maju dan Multidisiplin',
            'departemen': 'Departemen Teknik',
            'prodi': 'S1 Teknik Robotika dan Kecerdasan Buatan',
            'prefix_nim': '16324',
            'kps': 'Dr. Yoga Pradana, S.T., M.T.',
            'jumlah_mahasiswa': 27,
        },
        {
            'fakultas': 'FEB',
            'nama_fakultas': 'Fakultas Ekonomi dan Bisnis',
            'departemen': 'Departemen Manajemen',
            'prodi': 'S1 Manajemen',
            'prefix_nim': '14124',
            'kps': 'Dr. Rina Wijaya, S.E., M.M.',
            'jumlah_mahasiswa': 36,
        },
        {
            'fakultas': 'FEB',
            'nama_fakultas': 'Fakultas Ekonomi dan Bisnis',
            'departemen': 'Departemen Akuntansi',
            'prodi': 'S1 Akuntansi',
            'prefix_nim': '14224',
            'kps': 'Dr. Budi Santoso, S.E., M.Si., Ak.',
            'jumlah_mahasiswa': 33,
        },
        {
            'fakultas': 'FK',
            'nama_fakultas': 'Fakultas Kedokteran',
            'departemen': 'Departemen Kedokteran',
            'prodi': 'S1 Kedokteran',
            'prefix_nim': '11124',
            'kps': 'Dr. dr. Arief Hidayat, M.Kes.',
            'jumlah_mahasiswa': 36,
        },
        {
            'fakultas': 'FISIP',
            'nama_fakultas': 'Fakultas Ilmu Sosial dan Ilmu Politik',
            'departemen': 'Departemen Komunikasi',
            'prodi': 'S1 Ilmu Komunikasi',
            'prefix_nim': '17124',
            'kps': 'Dr. Maya Lestari, S.Sos., M.Si.',
            'jumlah_mahasiswa': 30,
        },
        {
            'fakultas': 'FH',
            'nama_fakultas': 'Fakultas Hukum',
            'departemen': 'Departemen Ilmu Hukum',
            'prodi': 'S1 Ilmu Hukum',
            'prefix_nim': '13124',
            'kps': 'Dr. Danu Prasetyo, S.H., M.H.',
            'jumlah_mahasiswa': 33,
        },
    ],
}


def _simulate_student_semesters(rng, nim, profile, candidates):
    records, summaries = [], []
    budgets = {
        'Konsisten': [20, 20, 19, 24],
        'IPS menurun': [20, 20, 19, 18],
        'Progres tertinggal': [20, 6, 6, 5],
        'Pemulihan nilai': [20, 15, 18, 24],
        'Progres lambat': [20, 12, 12, 12],
        'IPK rendah': [20, 15, 15, 15],
        'D berlebih': [20, 18, 18, 18],
    }
    for semester in range(1, 5):
        previous = [s for s in summaries if s['nim'] == nim and s['semester'] == semester - 1]
        cap = max_credits(previous[0]['ips']) if previous else 20
        budget = min(budgets[profile][semester - 1], cap)
        historical = pd.DataFrame([r for r in records if r['nim'] == nim])
        chosen = []
        # Data pemulihan mengulang satu mata kuliah D. Berlaku hanya pada snapshot sesudahnya.
        if profile == 'Pemulihan nilai' and semester in (3, 4):
            effective = historical.sort_values('semester').drop_duplicates('kode', keep='last')
            ds = effective[effective.nilai == 'D']
            if not ds.empty:
                c = candidates[candidates.kode == ds.iloc[0]['kode']].iloc[0]
                chosen.append(c)
                budget -= int(c.sks)
        done = set(historical['kode']) if not historical.empty else set()
        available = candidates[(candidates.semester_anjuran <= semester) & ~candidates.kode.isin(done)]
        for _, course in available.iterrows():
            if int(course.sks) <= budget:
                chosen.append(course)
                budget -= int(course.sks)
        for course in chosen:
            if profile == 'Konsisten':
                grade = rng.choice(['A', 'A', 'AB', 'AB', 'B'])
            elif profile == 'IPS menurun':
                options = [['A', 'AB', 'B'], ['AB', 'B', 'BC'], ['BC', 'C', 'C'], ['C', 'D', 'D']]
                grade = rng.choice(options[semester - 1])
            elif profile in ('Progres tertinggal', 'IPK rendah'):
                grade = rng.choice(['C', 'D', 'D'])
            elif profile == 'D berlebih':
                grade = rng.choice(['A', 'AB', 'D', 'D'])
            elif profile == 'Pemulihan nilai':
                grade = rng.choice(['C', 'D', 'D']) if semester <= 2 else rng.choice(['A', 'AB', 'B'])
            else:
                grade = rng.choice(['A', 'AB', 'B', 'BC'])
            records.append(dict(nim=nim, semester=semester, kode=course.kode, nilai=grade))
        grades = pd.DataFrame(records)
        summary = semester_summary(grades, candidates, nim, semester)
        assert summary['sks_diambil'] <= cap
        summaries.append(summary)
    return records, summaries


def generate(seed=2024):
    rng = random.Random(seed)
    catalog = pd.read_csv(ROOT / 'data/kurikulum_2021.csv')
    candidates = catalog[catalog.semester_anjuran <= 4].copy()
    candidates = candidates[~candidates.kode.str.startswith('AG') | (candidates.kode == 'AGI101')]
    si_meta = FST_STRUCTURE['prodi_s1'][0]
    advisors = si_meta['dosen_wali']
    students, records, summaries = [], [], []
    for index, name in enumerate(NAMES):
        nim = f'18724{index + 1:03d}'
        profile = PROFILES[index % len(PROFILES)]
        advisor = advisors[min(index // 10, len(advisors) - 1)]
        students.append(dict(
            nim=nim,
            nama=name,
            angkatan=2024,
            kurikulum=2021,
            skenario=profile,
            departemen=si_meta['departemen'],
            prodi=si_meta['prodi'],
            kps=si_meta['kps'],
            dosen_wali=advisor,
            pertimbangan_dosen_wali=CONSIDERATIONS[profile],
        ))
        stu_records, stu_summaries = _simulate_student_semesters(rng, nim, profile, candidates)
        records.extend(stu_records)
        summaries.extend(stu_summaries)
    grades = pd.DataFrame(records)
    grades['berlaku_akhir_semester_4'] = ~grades.duplicated(['nim', 'kode'], keep='last')
    return pd.DataFrame(students), grades, catalog, pd.DataFrame(summaries)


def generate_faculty(seed=2024):
    si_students, _, catalog, si_summaries = generate(seed=seed)
    candidates = catalog[catalog.semester_anjuran <= 4].copy()
    candidates = candidates[~candidates.kode.str.startswith('AG') | (candidates.kode == 'AGI101')]

    all_students = si_students.to_dict('records')
    all_summaries = si_summaries.to_dict('records')

    # Pola profil untuk prodi yang memiliki kasus Prioritas vs prodi tanpa kasus Prioritas (hanya Tanpa peringatan & Perhatian).
    priority_templates = [
        ['Konsisten', 'Konsisten', 'Konsisten', 'IPS menurun', 'Pemulihan nilai', 'Progres lambat', 'D berlebih', 'Progres tertinggal', 'Konsisten', 'IPK rendah'],
        ['Konsisten', 'Konsisten', 'IPS menurun', 'Pemulihan nilai', 'Progres lambat', 'D berlebih', 'Progres tertinggal', 'IPK rendah', 'Konsisten', 'Progres lambat'],
        ['Konsisten', 'Konsisten', 'Konsisten', 'Konsisten', 'IPS menurun', 'Pemulihan nilai', 'Progres lambat', 'Progres tertinggal', 'D berlebih', 'IPK rendah'],
    ]
    non_priority_templates = [
        ['Konsisten', 'Konsisten', 'Konsisten', 'Konsisten', 'IPS menurun', 'Pemulihan nilai', 'Progres lambat', 'D berlebih', 'Konsisten', 'Progres lambat'],
        ['Konsisten', 'Konsisten', 'Konsisten', 'IPS menurun', 'Pemulihan nilai', 'Progres lambat', 'Konsisten', 'D berlebih', 'Konsisten', 'IPS menurun'],
        ['Konsisten', 'Konsisten', 'Konsisten', 'Konsisten', 'Konsisten', 'Pemulihan nilai', 'Progres lambat', 'IPS menurun', 'D berlebih', 'Konsisten'],
    ]

    for prodi_idx, meta in enumerate(FST_STRUCTURE['prodi_s1'][1:], start=1):
        rng = random.Random(seed + prodi_idx * 101)
        total = meta['jumlah_mahasiswa']
        advisors = meta['dosen_wali']
        per_advisor = total // len(advisors)
        templates = priority_templates if meta.get('ada_prioritas', True) else non_priority_templates
        for index in range(total):
            adv_idx = min(index // per_advisor, len(advisors) - 1)
            pos_in_adv = index - adv_idx * per_advisor
            template = templates[(prodi_idx + adv_idx) % len(templates)]
            profile = template[pos_in_adv % len(template)]
            nim = f"{meta['prefix_nim']}{index + 1:03d}"
            first = FIRST_NAMES[(prodi_idx * 7 + index) % len(FIRST_NAMES)]
            last = LAST_NAMES[(prodi_idx * 5 + index * 3) % len(LAST_NAMES)]
            name = f'{first} {last}'
            all_students.append(dict(
                nim=nim,
                nama=name,
                angkatan=2024,
                kurikulum=2021,
                skenario=profile,
                departemen=meta['departemen'],
                prodi=meta['prodi'],
                kps=meta['kps'],
                dosen_wali=advisors[adv_idx],
                pertimbangan_dosen_wali=CONSIDERATIONS[profile],
            ))
            _, stu_summaries = _simulate_student_semesters(rng, nim, profile, candidates)
            all_summaries.extend(stu_summaries)

    return pd.DataFrame(all_students), pd.DataFrame(all_summaries), FST_STRUCTURE


def main():
    students, grades, _, summaries = generate()
    for data, name in [(students, 'mahasiswa.csv'), (grades, 'nilai.csv'), (summaries, 'ringkasan_semester.csv')]:
        data.to_csv(ROOT / 'data' / name, index=False)
    students_fst, summaries_fst, structure = generate_faculty()
    students_fst.to_csv(ROOT / 'data' / 'mahasiswa_fst.csv', index=False)
    summaries_fst.to_csv(ROOT / 'data' / 'ringkasan_fst.csv', index=False)
    (ROOT / 'data' / 'struktur_fst.json').write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Dibuat {len(students)} mahasiswa SI ({len(grades)} nilai, {len(summaries)} ringkasan) '
          f'dan {len(students_fst)} mahasiswa FST lintas {len(structure["prodi_s1"])} prodi S1 ({len(summaries_fst)} ringkasan).')


if __name__ == '__main__':
    main()
