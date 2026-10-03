"""Perhitungan dari nilai yang tersedia pada akhir semester tertentu."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
RULES = json.loads((ROOT / 'rules.json').read_text())


def khs_round(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def max_credits(ips: float) -> int:
    if not 0 <= ips <= 4:
        raise ValueError('IPS harus berada pada rentang 0–4.')
    if khs_round(ips) != ips:
        raise ValueError('Gunakan IPS dari KHS dengan maksimal dua angka desimal.')
    return next(row['sks'] for row in RULES['batas_krs'] if ips <= row['ips_max'])


def load_data():
    return tuple(pd.read_csv(ROOT / 'data' / name, dtype={'nim': str, 'kode': str}) for name in
                 ['mahasiswa.csv', 'nilai.csv', 'kurikulum_2021.csv', 'ringkasan_semester.csv'])


def transcript_at(grades: pd.DataFrame, nim: str, finished_semester: int) -> pd.DataFrame:
    # Filter waktu lebih dahulu. Penanda akhir semester 4 tidak dipakai untuk snapshot lama.
    available = grades[(grades['nim'] == nim) & (grades['semester'] <= finished_semester)].copy()
    return available.sort_values('semester').drop_duplicates('kode', keep='last').copy()


def semester_summary(grades: pd.DataFrame, catalog: pd.DataFrame, nim: str, semester: int) -> dict:
    available = grades[(grades['nim'] == nim) & (grades['semester'] <= semester)]
    current = available[available['semester'] == semester].merge(catalog[['kode', 'sks']], on='kode', validate='many_to_one')
    effective = transcript_at(grades, nim, semester).merge(catalog[['kode', 'sks']], on='kode', validate='many_to_one')
    taken = int(current['sks'].sum())
    passed = int(effective['sks'].sum())  # A–D saja; D lulus menurut pedoman.
    ips = khs_round(float((current['nilai'].map(RULES['bobot_nilai']) * current['sks']).sum()) / taken) if taken else None
    ipk = khs_round(float((effective['nilai'].map(RULES['bobot_nilai']) * effective['sks']).sum()) / passed) if passed else None
    d = int(effective.loc[effective['nilai'] == 'D', 'sks'].sum())
    prev_passed = int(transcript_at(grades, nim, semester - 1).merge(catalog[['kode', 'sks']], on='kode')['sks'].sum())
    return {'nim': nim, 'semester': semester, 'ips': ips, 'ipk': ipk, 'sks_diambil': taken,
            'sks_lulus': passed, 'sks_baru_lulus': passed - prev_passed, 'sks_d': d}
