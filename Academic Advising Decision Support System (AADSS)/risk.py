"""Mesin analisis bersama untuk dataset dan formulir manual. Tidak memprediksi probabilitas."""
from dataclasses import dataclass, asdict
import math
from numbers import Integral
from academic import RULES, max_credits, khs_round

LEVELS = ['Tidak ada peringatan terdeteksi', 'Perlu perhatian', 'Prioritas konsultasi']


@dataclass(frozen=True)
class Snapshot:
    semester_akan: int
    ips: float | None
    ipk: float | None
    sks_lulus: int
    sks_d: int
    rencana_sks: int
    nama: str = ''
    nim: str = ''


def validate_snapshot(s: Snapshot) -> list[str]:
    errors = []
    for label, value in [('Semester', s.semester_akan), ('SKS lulus', s.sks_lulus), ('SKS D', s.sks_d), ('Rencana SKS', s.rencana_sks)]:
        if isinstance(value, bool) or not isinstance(value, Integral):
            errors.append(f'{label} harus berupa bilangan bulat.')
    if errors:
        return errors
    if not 1 <= s.semester_akan <= 30:
        errors.append('Semester yang akan ditempuh harus 1–30.')
    if any(v < 0 for v in [s.sks_lulus, s.sks_d, s.rencana_sks]):
        errors.append('Jumlah SKS tidak boleh negatif.')
    if s.sks_d > s.sks_lulus:
        errors.append('SKS bernilai D tidak boleh melebihi SKS lulus kumulatif.')
    if s.semester_akan == 1:
        if s.sks_lulus or s.sks_d or s.ips is not None or s.ipk is not None:
            errors.append('Awal semester 1 belum memiliki KHS atau SKS lulus.')
    else:
        for label, value in [('IPS', s.ips), ('IPK', s.ipk)]:
            if value is None or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 4:
                errors.append(f'{label} harus diisi dari KHS pada rentang 0–4.')
            elif khs_round(value) != value:
                errors.append(f'{label} menggunakan maksimal dua angka desimal sesuai KHS.')
        if s.sks_lulus > 24 * (s.semester_akan - 1):
            errors.append('SKS lulus melampaui kapasitas maksimum 24 SKS per semester selesai dalam skenario demo.')
    return errors


def analyze(s: Snapshot) -> dict:
    errors = validate_snapshot(s)
    if errors:
        raise ValueError('\n'.join(errors))
    finished = s.semester_akan - 1
    cap = max_credits(s.ips) if finished else None
    remaining = max(0, RULES['target_sks'] - s.sks_lulus)
    proportion = s.sks_d / s.sks_lulus if s.sks_lulus else None
    pace = min(s.sks_lulus / finished, cap) if finished else 0
    estimate = finished + math.ceil(remaining / pace) if pace > 0 else None
    if remaining == 0 and finished:
        estimate = finished
    alerts = []
    def add(code, title, reason, action, page, priority=False):
        alerts.append(dict(kode=code,judul=title,alasan=reason,rekomendasi=action,
                           sumber=page,prioritas=priority))
    if finished and s.ipk < RULES['minimum_ipk']:
        add('IPK', 'IPK di bawah 2,00', f'IPK saat ini {s.ipk:.2f}.',
            'Diskusikan strategi belajar dan perbaikan nilai dengan dosen wali.', 'PDF hlm. 26 / tercetak 22')
    for checkpoint in RULES['evaluasi']:
        n, minimum = checkpoint['semester'], checkpoint['minimum_sks']
        if finished >= n and (s.sks_lulus < minimum or s.ipk < RULES['minimum_ipk']):
            add(f'EVAL_{n}', f'Minimum evaluasi {n} semester belum terpenuhi',
                f'Ringkasan yang diperiksa: {s.sks_lulus} SKS dan IPK {s.ipk:.2f}; minimum {minimum} SKS dan IPK 2,00.',
                'Prioritaskan konsultasi dan verifikasi hasil evaluasi resmi fakultas.', 'PDF hlm. 22 / tercetak 18', True)
    if proportion is not None and s.sks_d * 5 > s.sks_lulus:
        add('D', 'Proporsi SKS D melebihi 20%', f'{s.sks_d} dari {s.sks_lulus} SKS ({proportion:.1%}).',
            'Susun prioritas perbaikan nilai D agar memenuhi batas kelulusan.', 'PDF hlm. 22 / tercetak 18')
    if cap is not None and s.rencana_sks > cap:
        add('KRS', 'Rencana KRS melebihi batas', f'Rencana {s.rencana_sks} SKS; batas {cap} SKS; lebih {s.rencana_sks - cap} SKS.',
            'Kurangi total rencana SKS, lalu konsultasikan KRS dengan dosen wali.', 'PDF hlm. 15 / tercetak 11')
    if estimate is not None and estimate > RULES['semester_normal']:
        add('PROGRES', 'Progres diperkirakan melewati 8 semester',
            f'Laju efektif {pace:.2f} SKS/semester; estimasi pemenuhan 144 SKS pada akhir semester {estimate}.',
            'Diskusikan strategi pemenuhan kredit dan mata kuliah wajib; estimasi tidak menjamin waktu lulus.',
            'Asumsi estimasi; target normal: PDF hlm. 10 / tercetak 6')
    elif finished and not pace and remaining:
        add('LAJU_NOL', 'Estimasi belum tersedia', 'Belum ada SKS lulus untuk menghitung laju progres.',
            'Periksa kelengkapan KHS dan bahas pemulihan progres dengan dosen wali.', 'Asumsi estimasi')
    if s.semester_akan > RULES['semester_maksimum']:
        add('MASA', 'Periode perwalian melewati batas studi',
            f'Perwalian awal semester {s.semester_akan}; batas kesempatan studi 14 semester tanpa cuti.',
            'Verifikasi status akademik dan pengecualian resmi dengan fakultas.', 'PDF hlm. 20, 22 / tercetak 16, 18', True)
    level = 2 if any(a['prioritas'] for a in alerts) else (1 if alerts else 0)
    return {'input': asdict(s), 'kategori': LEVELS[level], 'tingkat': level, 'batas_sks': cap,
            'sisa_sks': remaining, 'proporsi_d': proportion, 'laju': pace,
            'estimasi_semester': estimate, 'peringatan': alerts,
            'lebih_sks': max(0, s.rencana_sks - cap) if cap is not None else None,
            'sisa_skenario_krs': max(0, remaining - s.rencana_sks) if cap is not None and s.rencana_sks <= cap else None,
            'belum_diverifikasi': ['Nilai E pada transkrip resmi', 'Penyelesaian kurikulum wajib/pilihan',
                'Kelulusan skripsi dan penyerahan naskah', 'Kehadiran kuliah/praktikum',
                'Persyaratan administratif dan keputusan evaluasi historis resmi']}
