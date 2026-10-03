"""Validasi data utama; tidak memperbaiki atau mengisi nol pada data rusak."""
import json
import math
from datetime import datetime, timezone
from academic import ROOT, RULES, load_data, max_credits, semester_summary
from risk import Snapshot, analyze


def validate(students,grades,catalog,summaries):
    errors=[]
    expected_columns=[(students,{'nim','nama','angkatan','kurikulum'},'mahasiswa'),
                      (grades,{'nim','kode','semester','nilai','berlaku_akhir_semester_4'},'nilai'),
                      (catalog,{'kode','sks','semester_anjuran'},'katalog'),
                      (summaries,{'nim','semester','ips','ipk','sks_diambil','sks_lulus','sks_baru_lulus','sks_d'},'ringkasan')]
    for frame, required, label in expected_columns:
        missing=required-set(frame.columns)
        if missing: errors.append(f'Kolom {label} tidak lengkap: {sorted(missing)}')
    if errors: return errors
    def check(condition,message):
        if not condition: errors.append(message)
    check(len(students)==30,'Dataset harus berisi 30 mahasiswa.')
    check(students.nim.is_unique,'NIM mahasiswa duplikat.')
    check(set(students.nim)=={f'18724{i:03d}' for i in range(1,31)},'Rentang NIM contoh tidak lengkap.')
    check(students.nama.notna().all(),'Nama mahasiswa kosong.')
    check(students.nim.str.match(r'^18724(?:00[1-9]|0[12][0-9]|030)$').all(),'NIM contoh harus berurutan 18724001–18724030.')
    check((students.angkatan==2024).all() and (students.kurikulum==2021).all(),'Angkatan/kurikulum tidak sesuai.')
    check(catalog.kode.is_unique,'Kode katalog duplikat.')
    check(catalog.sks.notna().all() and (catalog.sks>0).all() and (catalog.sks%1==0).all(),'SKS katalog tidak valid.')
    check(set(grades.nim)<=set(students.nim),'Riwayat nilai memiliki NIM yang tidak dikenal.')
    check(set(grades.kode)<=set(catalog.kode),'Riwayat nilai memiliki kode yang tidak dikenal.')
    check(grades.nilai.isin(RULES['bobot_nilai']).all(),'Nilai harus A, AB, B, BC, C, atau D; E tidak disimulasikan.')
    check(grades.semester.isin([1,2,3,4]).all(),'Semester nilai harus 1–4.')
    check(grades[['nim','kode','semester','nilai']].notna().all().all(),'Ada data nilai yang kosong.')
    check(summaries.notna().all().all(),'Ada ringkasan semester yang kosong.')
    check(not grades.duplicated(['nim','kode','semester']).any(),'Mata kuliah ganda pada semester yang sama.')
    check(not summaries.duplicated(['nim','semester']).any(),'Ringkasan semester duplikat.')
    check(set(summaries.nim)==set(students.nim),'NIM ringkasan tidak cocok dengan mahasiswa.')
    check(summaries.semester.isin([1,2,3,4]).all(),'Semester ringkasan harus 1–4.')
    check(len(summaries)==120,'Harus ada empat ringkasan per mahasiswa.')
    expected=~grades.duplicated(['nim','kode'],keep='last')
    check((grades.berlaku_akhir_semester_4.astype(str).str.lower().to_numpy()==expected.astype(str).str.lower().to_numpy()).all(),'Penanda nilai akhir tidak konsisten.')
    if errors: return errors
    for nim in students.nim:
        prev_ips=None
        for semester in range(1,5):
            stored=summaries[(summaries.nim==nim)&(summaries.semester==semester)]
            if len(stored)!=1:
                errors.append(f'{nim}: ringkasan semester {semester} tidak lengkap.');continue
            recomputed=semester_summary(grades,catalog,nim,semester)
            for field in ['ips','ipk','sks_diambil','sks_lulus','sks_baru_lulus','sks_d']:
                value=stored.iloc[0][field]
                if recomputed[field] is None or not math.isclose(float(value),float(recomputed[field]),abs_tol=1e-9):
                    errors.append(f'{nim} semester {semester}: {field} tidak sesuai riwayat nilai.')
            cap=max_credits(prev_ips) if prev_ips is not None else 20
            check(recomputed['sks_diambil']<=cap,f'{nim}: KRS semester {semester} melampaui kapasitas.')
            course_rows=grades[(grades.nim==nim)&(grades.semester==semester)].merge(catalog,on='kode')
            check((course_rows.semester_anjuran<=semester).all(),f'{nim}: mata kuliah mendahului semester anjuran.')
            prev_ips=recomputed['ips']
            if prev_ips is not None:
                analyze(Snapshot(semester+1,prev_ips,recomputed['ipk'],recomputed['sks_lulus'],recomputed['sks_d'],max_credits(prev_ips)))
    return errors


def main():
    data=load_data()
    errors=validate(*data)
    report={'status':'LULUS' if not errors else 'GAGAL','seed':2024,
            'mahasiswa':len(data[0]),'pengambilan_mata_kuliah':len(data[1]),'ringkasan':len(data[3]),
            'kesalahan':errors,'asumsi':['Seluruh mahasiswa tanpa cuti','NIM/nama sintetis',
            'Nilai pengulangan terbaru digunakan sebagai transkrip simulasi; bukan klaim kebijakan resmi',
            'Komposisi skenario bukan prevalensi nyata','Katalog mendokumentasikan ECTS dan konversi SKS',
            'Ketersediaan kelas, prasyarat rinci, jadwal dan approval dosen wali tidak disimulasikan']}
    (ROOT/'laporan_validasi.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
