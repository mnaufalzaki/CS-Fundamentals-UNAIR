"""Validasi data utama; tidak memperbaiki atau mengisi nol pada data rusak."""
import json
import math
from academic import ROOT, RULES, load_data, load_faculty_data, max_credits, semester_summary
from risk import Snapshot, analyze, LEVELS


def validate_faculty(students_fst, summaries_fst, structure):
    errors = []
    req_stu = {'nim', 'nama', 'angkatan', 'kurikulum', 'skenario', 'departemen', 'prodi', 'kps', 'dosen_wali', 'pertimbangan_dosen_wali'}
    req_sum = {'nim', 'semester', 'ips', 'ipk', 'sks_diambil', 'sks_lulus', 'sks_baru_lulus', 'sks_d'}
    if req_stu - set(students_fst.columns):
        errors.append(f'Kolom mahasiswa_fst tidak lengkap: {sorted(req_stu - set(students_fst.columns))}')
    if req_sum - set(summaries_fst.columns):
        errors.append(f'Kolom ringkasan_fst tidak lengkap: {sorted(req_sum - set(summaries_fst.columns))}')
    if errors:
        return errors

    prodi_list = [p['prodi'] for p in structure.get('prodi_s1', [])]
    if len(prodi_list) != 8:
        errors.append('Struktur FST harus mencakup 8 program studi S1.')
    if set(students_fst.prodi) != set(prodi_list):
        errors.append('Daftar program studi pada mahasiswa_fst tidak sesuai dengan 8 prodi S1 FST.')
    if not students_fst.nim.is_unique:
        errors.append('NIM pada mahasiswa_fst duplikat.')
    if set(summaries_fst.nim) != set(students_fst.nim):
        errors.append('NIM pada ringkasan_fst tidak cocok dengan mahasiswa_fst.')
    if len(summaries_fst) != len(students_fst) * 4:
        errors.append('Jumlah ringkasan_fst harus 4 semester per mahasiswa.')
    if not structure.get('pimpinan', {}).get('dekan', {}).get('nama'):
        errors.append('Data Dekan FST belum tersedia pada struktur_fst.json.')

    # Pastikan sebagian prodi FST memiliki kasus Prioritas (untuk dinaikkan ke Akademik Universitas)
    # dan sebagian prodi tanpa kasus Prioritas (hanya Tanpa peringatan dan Perhatian).
    sem4 = summaries_fst[summaries_fst.semester == 4].set_index('nim')
    priority_prodi_count = 0
    non_priority_prodi_count = 0
    for prodi_meta in structure.get('prodi_s1', []):
        p_name = prodi_meta['prodi']
        has_priority = prodi_meta.get('ada_prioritas', True)
        if has_priority:
            priority_prodi_count += 1
        else:
            non_priority_prodi_count += 1
        p_stu = students_fst[students_fst.prodi == p_name]
        if len(p_stu) != prodi_meta['jumlah_mahasiswa']:
            errors.append(f'{p_name}: jumlah mahasiswa tidak sesuai konfigurasi.')
        expected_levels = set(LEVELS) if has_priority else {LEVELS[0], LEVELS[1]}
        for adv in prodi_meta['dosen_wali']:
            a_stu = p_stu[p_stu.dosen_wali == adv]
            if a_stu.empty:
                errors.append(f'{p_name}: dosen wali {adv} tidak memiliki mahasiswa wali.')
                continue
            levels_found = set()
            for s in a_stu.itertuples():
                if s.nim not in sem4.index:
                    errors.append(f'{s.nim}: ringkasan semester 4 tidak ditemukan.')
                    continue
                row = sem4.loc[s.nim]
                res = analyze(Snapshot(5, float(row.ips), float(row.ipk), int(row.sks_lulus), int(row.sks_d), max_credits(float(row.ips)), s.nama, s.nim))
                levels_found.add(res['kategori'])
            if levels_found != expected_levels:
                errors.append(f'{p_name} ({adv}): status mahasiswa wali tidak sesuai skenario prodi, ditemukan {sorted(levels_found)}.')
    if not (priority_prodi_count > 0 and non_priority_prodi_count > 0):
        errors.append('Dataset FST harus mencakup prodi dengan Prioritas dan prodi tanpa Prioritas.')
    return errors


def validate(students, grades, catalog, summaries):
    errors = []
    expected_columns = [
        (students, {'nim', 'nama', 'angkatan', 'kurikulum', 'departemen', 'prodi', 'kps', 'dosen_wali', 'pertimbangan_dosen_wali'}, 'mahasiswa'),
        (grades, {'nim', 'kode', 'semester', 'nilai', 'berlaku_akhir_semester_4'}, 'nilai'),
        (catalog, {'kode', 'sks', 'semester_anjuran'}, 'katalog'),
        (summaries, {'nim', 'semester', 'ips', 'ipk', 'sks_diambil', 'sks_lulus', 'sks_baru_lulus', 'sks_d'}, 'ringkasan'),
    ]
    for frame, required, label in expected_columns:
        missing = required - set(frame.columns)
        if missing:
            errors.append(f'Kolom {label} tidak lengkap: {sorted(missing)}')
    if errors:
        return errors

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(len(students) == 30, 'Dataset harus berisi 30 mahasiswa.')
    check(students.nim.is_unique, 'NIM mahasiswa duplikat.')
    check(set(students.nim) == {f'18724{i:03d}' for i in range(1, 31)}, 'Rentang NIM contoh tidak lengkap.')
    check(students.nama.notna().all(), 'Nama mahasiswa kosong.')
    check(students.dosen_wali.notna().all() and (students.dosen_wali.str.strip() != '').all(), 'Dosen wali kosong.')
    check(students.dosen_wali.nunique() >= 2, 'Program studi harus mencakup beberapa dosen wali.')
    check(students.nim.str.match(r'^18724(?:00[1-9]|0[12][0-9]|030)$').all(), 'NIM contoh harus berurutan 18724001–18724030.')
    check((students.angkatan == 2024).all() and (students.kurikulum == 2021).all(), 'Angkatan/kurikulum tidak sesuai.')
    check(catalog.kode.is_unique, 'Kode katalog duplikat.')
    check(catalog.sks.notna().all() and (catalog.sks > 0).all() and (catalog.sks % 1 == 0).all(), 'SKS katalog tidak valid.')
    check(set(grades.nim) <= set(students.nim), 'Riwayat nilai memiliki NIM yang tidak dikenal.')
    check(set(grades.kode) <= set(catalog.kode), 'Riwayat nilai memiliki kode yang tidak dikenal.')
    check(grades.nilai.isin(RULES['bobot_nilai']).all(), 'Nilai harus A, AB, B, BC, C, atau D; E tidak disimulasikan.')
    check(grades.semester.isin([1, 2, 3, 4]).all(), 'Semester nilai harus 1–4.')
    check(grades[['nim', 'kode', 'semester', 'nilai']].notna().all().all(), 'Ada data nilai yang kosong.')
    check(summaries.notna().all().all(), 'Ada ringkasan semester yang kosong.')
    check(not grades.duplicated(['nim', 'kode', 'semester']).any(), 'Mata kuliah ganda pada semester yang sama.')
    check(not summaries.duplicated(['nim', 'semester']).any(), 'Ringkasan semester duplikat.')
    check(set(summaries.nim) == set(students.nim), 'NIM ringkasan tidak cocok dengan mahasiswa.')
    check(summaries.semester.isin([1, 2, 3, 4]).all(), 'Semester ringkasan harus 1–4.')
    check(len(summaries) == 120, 'Harus ada empat ringkasan per mahasiswa.')
    expected = ~grades.duplicated(['nim', 'kode'], keep='last')
    check((grades.berlaku_akhir_semester_4.astype(str).str.lower().to_numpy() == expected.astype(str).str.lower().to_numpy()).all(), 'Penanda nilai akhir tidak konsisten.')
    if errors:
        return errors

    for nim in students.nim:
        prev_ips = None
        for semester in range(1, 5):
            stored = summaries[(summaries.nim == nim) & (summaries.semester == semester)]
            if len(stored) != 1:
                errors.append(f'{nim}: ringkasan semester {semester} tidak lengkap.')
                continue
            recomputed = semester_summary(grades, catalog, nim, semester)
            for field in ['ips', 'ipk', 'sks_diambil', 'sks_lulus', 'sks_baru_lulus', 'sks_d']:
                value = stored.iloc[0][field]
                if recomputed[field] is None or not math.isclose(float(value), float(recomputed[field]), abs_tol=1e-9):
                    errors.append(f'{nim} semester {semester}: {field} tidak sesuai riwayat nilai.')
            cap = max_credits(prev_ips) if prev_ips is not None else 20
            check(recomputed['sks_diambil'] <= cap, f'{nim}: KRS semester {semester} melampaui kapasitas.')
            course_rows = grades[(grades.nim == nim) & (grades.semester == semester)].merge(catalog, on='kode')
            check((course_rows.semester_anjuran <= semester).all(), f'{nim}: mata kuliah mendahului semester anjuran.')
            prev_ips = recomputed['ips']
            if prev_ips is not None:
                analyze(Snapshot(semester + 1, prev_ips, recomputed['ipk'], recomputed['sks_lulus'], recomputed['sks_d'], max_credits(prev_ips)))

    students_fst, summaries_fst, structure = load_faculty_data()
    errors.extend(validate_faculty(students_fst, summaries_fst, structure))
    return errors


def main():
    data = load_data()
    students_fst, summaries_fst, structure = load_faculty_data()
    errors = validate(*data)
    report = {
        'status': 'LULUS' if not errors else 'GAGAL',
        'seed': 2024,
        'mahasiswa_prodi_si': len(data[0]),
        'pengambilan_mata_kuliah_si': len(data[1]),
        'ringkasan_si': len(data[3]),
        'prodi_s1_fst': len(structure['prodi_s1']),
        'dosen_wali_fst': sum(len(p['dosen_wali']) for p in structure['prodi_s1']),
        'mahasiswa_fst': len(students_fst),
        'ringkasan_fst': len(summaries_fst),
        'kesalahan': errors,
        'asumsi': [
            'Seluruh mahasiswa tanpa cuti',
            'NIM/nama mahasiswa dan dosen wali adalah data sintetis; pimpinan fakultas mengacu pada Pedoman Pendidikan FST',
            'Setiap dosen wali membimbing mahasiswa dengan variasi status Tanpa peringatan, Perhatian, dan Prioritas',
            'Cakupan fakultas meliputi seluruh 8 Program Studi S1 di FST UNAIR',
            'Nilai pengulangan terbaru digunakan sebagai transkrip simulasi; bukan klaim kebijakan resmi',
            'Katalog mendokumentasikan ECTS dan konversi SKS',
        ],
    }
    (ROOT / 'laporan_validasi.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
