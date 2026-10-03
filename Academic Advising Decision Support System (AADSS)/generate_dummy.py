"""Data sintetis dari riwayat mata kuliah; ringkasan tidak dibuat secara acak."""
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
PROFILES = ['Konsisten', 'IPS menurun', 'Progres tertinggal', 'Konsisten', 'Pemulihan nilai',
            'Progres lambat', 'IPK rendah', 'D berlebih']


def generate(seed=2024):
    rng = random.Random(seed)
    catalog = pd.read_csv(ROOT / 'data/kurikulum_2021.csv')
    candidates = catalog[catalog.semester_anjuran <= 4].copy()
    candidates = candidates[~candidates.kode.str.startswith('AG') | (candidates.kode == 'AGI101')]
    students, records, summaries = [], [], []
    for index, name in enumerate(NAMES):
        nim = f'18724{index + 1:03d}'
        profile = PROFILES[index % len(PROFILES)]
        students.append(dict(nim=nim,nama=name,angkatan=2024,kurikulum=2021,skenario=profile))
        for semester in range(1,5):
            previous = [s for s in summaries if s['nim']==nim and s['semester']==semester-1]
            cap = max_credits(previous[0]['ips']) if previous else 20
            budgets = {'Konsisten': [20,20,19,24], 'IPS menurun': [20,20,19,18],
                       'Progres tertinggal': [20,6,6,5], 'Pemulihan nilai': [20,15,18,24],
                       'Progres lambat': [20,12,12,12], 'IPK rendah': [20,15,15,15],
                       'D berlebih': [20,18,18,18]}
            budget = min(budgets[profile][semester-1],cap)
            historical = pd.DataFrame([r for r in records if r['nim']==nim])
            chosen=[]
            # Data pemulihan mengulang satu mata kuliah D. Berlaku hanya pada snapshot sesudahnya.
            if profile=='Pemulihan nilai' and semester in (3,4):
                effective=historical.sort_values('semester').drop_duplicates('kode',keep='last')
                ds=effective[effective.nilai=='D']
                if not ds.empty:
                    c=candidates[candidates.kode==ds.iloc[0]['kode']].iloc[0]
                    chosen.append(c)
                    budget-=int(c.sks)
            done=set(historical['kode']) if not historical.empty else set()
            available=candidates[(candidates.semester_anjuran<=semester)&~candidates.kode.isin(done)]
            for _,course in available.iterrows():
                if int(course.sks)<=budget:
                    chosen.append(course)
                    budget-=int(course.sks)
            for course in chosen:
                if profile=='Konsisten':
                    grade=rng.choice(['A','A','AB','AB','B'])
                elif profile=='IPS menurun':
                    options=[['A','AB','B'],['AB','B','BC'],['BC','C','C'],['C','D','D']]
                    grade=rng.choice(options[semester-1])
                elif profile in ('Progres tertinggal','IPK rendah'):
                    grade=rng.choice(['C','D','D'])
                elif profile=='D berlebih':
                    grade=rng.choice(['A','AB','D','D'])
                elif profile=='Pemulihan nilai':
                    grade=rng.choice(['C','D','D']) if semester<=2 else rng.choice(['A','AB','B'])
                else:
                    grade=rng.choice(['A','AB','B','BC'])
                records.append(dict(nim=nim,semester=semester,kode=course.kode,nilai=grade))
            grades=pd.DataFrame(records)
            summary=semester_summary(grades,catalog,nim,semester)
            assert summary['sks_diambil']<=cap
            summaries.append(summary)
    grades=pd.DataFrame(records)
    grades['berlaku_akhir_semester_4']=~grades.duplicated(['nim','kode'],keep='last')
    return pd.DataFrame(students), grades, catalog, pd.DataFrame(summaries)


def main():
    students, grades, _, summaries=generate()
    for data,name in [(students,'mahasiswa.csv'),(grades,'nilai.csv'),(summaries,'ringkasan_semester.csv')]:
        data.to_csv(ROOT / 'data' / name,index=False)
    print(f'Dibuat {len(students)} mahasiswa, {len(grades)} pengambilan mata kuliah, {len(summaries)} ringkasan semester.')

if __name__=='__main__': main()
