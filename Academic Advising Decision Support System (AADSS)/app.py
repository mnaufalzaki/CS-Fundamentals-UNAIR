"""Antarmuka perwalian; jalankan dengan streamlit run app.py."""
from functools import partial
import html
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from academic import ROOT, RULES, load_data, load_faculty_data, semester_summary, transcript_at, max_credits
from risk import Snapshot, analyze, LEVELS
from validate_data import validate

st.set_page_config(page_title='AADSS - Universitas Airlangga', page_icon='🎓', layout='wide', initial_sidebar_state='auto')
st.markdown('''<style>
/* Tata letak umum */
.block-container {padding-top:3.2rem;padding-bottom:3rem;max-width:1280px;}
h1,h2,h3 {color:#0b2f57;letter-spacing:-.01em;}
h2 {font-size:1.35rem!important;margin-top:.6rem;}
h3 {font-size:1.12rem!important;}
/* Header halaman */
.hero {display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;
  background:linear-gradient(115deg,#0b2f57 0%,#134b82 100%);color:#fff;padding:20px 24px;border-radius:14px;
  margin-bottom:14px;box-shadow:0 6px 18px rgba(11,47,87,.14);}
.hero .eyebrow {font-size:.72rem;letter-spacing:.14em;color:#e3b94b;font-weight:700;text-transform:uppercase;}
.hero h1 {color:#fff;margin:6px 0 4px;font-size:1.7rem;line-height:1.2;padding:0;}
.hero p {margin:0;color:#d9e4f0;font-size:.95rem;}
.role-pill {background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);color:#fff;border-radius:999px;
  padding:5px 12px;font-size:.8rem;font-weight:600;white-space:nowrap;}
.scope {color:#5b7089;font-size:.86rem;margin:-4px 0 14px;}
/* Kartu metrik */
[data-testid="stMetric"] {background:#fff;border:1px solid #dde5ee;border-top:4px solid #c9a227;border-radius:12px;
  padding:14px 16px;box-shadow:0 1px 2px rgba(20,44,73,.05);height:100%;}
[data-testid="stMetricLabel"] p {white-space:normal!important;overflow:visible!important;text-overflow:clip!important;color:#5b7089;font-weight:600;}
[data-testid="stMetricValue"] {color:#0b2f57;font-weight:700;}
.st-key-status_metrics [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {border-top-color:#1b7b6c;}
.st-key-status_metrics [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {border-top-color:#c38a18;}
.st-key-status_metrics [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] {border-top-color:#b64046;}
/* Tabel, tombol, kartu */
[data-testid="stDataFrame"] {border:1px solid #dde5ee;border-radius:12px;overflow:hidden;background:#fff;}
.st-key-risk_filters button {border-radius:18px;}
.role-card {display:flex;flex-direction:column;justify-content:flex-start;gap:6px;padding:2px 0 6px;}
.role-badge {display:inline-block;align-self:flex-start;font-size:.66rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;color:#0b4f89;background:#edf3fa;border:1px solid #d4e2f2;border-radius:999px;
  padding:2px 9px;margin-bottom:2px;white-space:nowrap;}
.role-card h4 {margin:0;color:#0b2f57;font-size:1.05rem;font-weight:700;line-height:1.3;min-height:2.6em;}
.role-card p {margin:0;color:#5b7089;font-size:.88rem;line-height:1.45;min-height:4.4em;}
.brand {font-weight:800;font-size:1.05rem;letter-spacing:.02em;}
.brand small {display:block;font-weight:500;opacity:.75;font-size:.72rem;letter-spacing:.12em;margin-top:2px;}
/* Ponsel */
@media (max-width: 640px) {
  .block-container {padding:3rem .8rem 3rem;}
  .hero {padding:14px 16px;border-radius:12px;}
  .hero h1 {font-size:1.3rem;}
  .hero p {font-size:.85rem;}
  h2 {font-size:1.15rem!important;}
  /* Kartu metrik dua per baris, bukan satu kolom panjang */
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) {flex-direction:row!important;flex-wrap:wrap!important;gap:.6rem!important;}
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) > [data-testid="stColumn"] {flex:1 1 calc(50% - .6rem)!important;min-width:calc(50% - .6rem)!important;width:calc(50% - .6rem)!important;}
  [data-testid="stMetric"] {padding:10px 12px;}
  [data-testid="stMetricValue"] {font-size:1.45rem!important;}
  .role-card p {min-height:0;}
  /* Bilah navigasi: menu selebar layar dan boleh turun baris; semester dan Ganti peran berdampingan */
  .st-key-topbar [data-testid="stButtonGroup"] > div {flex-wrap:wrap;}
  .st-key-topbar [data-testid="stButtonGroup"] button {flex:1 1 auto;min-width:0;padding:.3rem .45rem;font-size:.82rem;}
  .st-key-topbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(n+2) {flex:1 1 calc(50% - .5rem)!important;min-width:calc(50% - .5rem)!important;width:calc(50% - .5rem)!important;}
}
.st-key-topbar {margin-bottom:.4rem;}
</style>''', unsafe_allow_html=True)

COLORS = {LEVELS[0]: '#1b7b6c', LEVELS[1]: '#c38a18', LEVELS[2]: '#b64046'}
MENU = ['Dashboard Angkatan 2024', 'Perwalian Mahasiswa', 'Cek Individu', 'Pedoman']
PAGE_KPS = 'Monitoring Program Studi'
PAGE_FAKULTAS = 'Administrasi Evaluasi Studi'
PAGE_UNIV = 'Rekap Universitas'
PAGE_MHS = 'Studi Saya'
# Peran mengikuti pembagian tugas pada pedoman FST. Pemilihan peran membatasi tampilan, bukan autentikasi.
ROLES = {
    'Dosen Wali': MENU,
    'Koordinator Program Studi': [PAGE_KPS, MENU[1], MENU[2], MENU[3]],
    'Akademik Fakultas': [PAGE_FAKULTAS, MENU[3]],
    'Akademik Universitas': [PAGE_UNIV, MENU[3]],
    'Mahasiswa': [PAGE_MHS, MENU[2], MENU[3]],
}
IDENTIFIED_DATA_ROLES = {'Dosen Wali', 'Koordinator Program Studi', 'Akademik Fakultas'}
ROLE_SCOPE = {
    'Mahasiswa': 'Konsultasi rencana studi dengan dosen wali, pemeriksaan batas SKS KRS, dan pemantauan riwayat KHS pribadi.',
    'Dosen Wali': 'Fokus pada mahasiswa wali bimbingannya: pemantauan status akademik, pemeriksaan batas SKS, dan persetujuan KRS.',
    'Koordinator Program Studi': 'Monitoring seluruh dosen wali di program studi yang mahasiswanya memiliki status Prioritas, Perhatian, dan Tanpa peringatan.',
    'Akademik Fakultas': 'Monitoring seluruh 8 Program Studi S1 dari FST beserta verifikasi Evaluasi Studi dan penentuan prodi yang naik ke tingkat universitas.',
    'Akademik Universitas': 'Monitoring tingkat Universitas Airlangga untuk program studi yang memiliki kasus Prioritas (eskalasi dari tingkat fakultas).',
}
ALERT_LABELS = {
    'IPK': 'IPK di bawah 2,00',
    'EVAL_4': 'Evaluasi 4 semester belum terpenuhi',
    'EVAL_8': 'Evaluasi 8 semester belum terpenuhi',
    'D': 'SKS D melebihi 20%',
    'KRS': 'Rencana KRS melebihi batas',
    'PROGRES': 'Estimasi melewati 8 semester',
    'LAJU_NOL': 'Laju SKS nol',
    'MASA': 'Melewati batas studi 14 semester',
    'MASA_ESTIMASI': 'Estimasi melewati 14 semester',
}
# Tahap evaluasi penghentian studi tetap (PDF hlm. 28) dan kode peringatan yang memicunya.
EVALUATION_STAGES = {
    'EVAL_4': 'Evaluasi I · 4 semester',
    'EVAL_8': 'Evaluasi II · 8 semester',
    'MASA': 'Evaluasi III · melewati 14 semester',
    'MASA_ESTIMASI': 'Risiko Evaluasi III · estimasi > 14 semester',
}
EVALUATION_MINIMUM = {
    'EVAL_4': '>= 40 SKS dan IPK >= 2,00',
    'EVAL_8': '>= 80 SKS dan IPK >= 2,00',
    'MASA': 'Maksimal 14 semester tanpa cuti',
    'MASA_ESTIMASI': '144 SKS sebelum akhir semester 14',
}
PERIODS = [2, 3, 4, 5]


def data_mtime():
    return tuple((ROOT / 'data' / name).stat().st_mtime_ns for name in
                 ['mahasiswa.csv', 'ringkasan_semester.csv', 'mahasiswa_fst.csv', 'ringkasan_fst.csv', 'struktur_fst.json'])


@st.cache_data
def validated_data(_version=None):
    try:
        frames = load_data()
        faculty_frames = load_faculty_data()
        issues = validate(*frames)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return (None, None, [f'Data tidak dapat dibaca: {exc}'])
    return frames, faculty_frames, issues


DATA_VERSION = data_mtime()
frames, faculty_frames, errors = validated_data(DATA_VERSION)
if errors:
    st.error('Data belum lolos validasi. Analisis dihentikan agar hasil tidak menyesatkan.')
    st.write(errors)
    st.stop()
students, grades, catalog, stored = frames
students_fst, summaries_fst, fst_structure = faculty_frames
SI_ADVISORS = list(dict.fromkeys(students.dosen_wali.tolist()))
FST_PRODI_NAMES = [p['prodi'] for p in fst_structure['prodi_s1']]

ROLE_BADGE = {
    'Dosen Wali': 'Perwalian · Mahasiswa Wali',
    'Koordinator Program Studi': 'Prodi · Lintas Dosen Wali',
    'Akademik Fakultas': 'Fakultas · 8 Prodi S1 FST',
    'Akademik Universitas': 'Universitas · Prodi Prioritas',
    'Mahasiswa': 'Portal Mahasiswa · Studi Saya',
}
ROLE_SUMMARY = {
    'Dosen Wali': 'Pantau mahasiswa wali, periksa batas SKS, dan setujui rencana KRS.',
    'Koordinator Program Studi': 'Pantau seluruh dosen wali di prodi, status risiko, dan tindak lanjut.',
    'Akademik Fakultas': 'Pantau 8 Prodi S1 dari FST, daftar mahasiswa, dan evaluasi studi.',
    'Akademik Universitas': 'Monitoring program studi yang memiliki kasus Prioritas di tingkat universitas.',
    'Mahasiswa': 'Lihat batas SKS, peringatan akademik, riwayat KHS, dan langkah perwalian.',
}


def reset_menu_for_role():
    if st.session_state.get('peran'):
        st.session_state['menu'] = ROLES[st.session_state['peran']][0]


def choose_role(name):
    st.session_state['peran'] = name
    st.session_state['menu'] = ROLES[name][0]


def leave_role():
    st.session_state['peran'] = None


def keep_menu():
    # Kontrol segmen bisa dikosongkan dengan mengklik pilihan aktif; kembalikan ke halaman terakhir.
    if st.session_state.get('menu') is None:
        st.session_state['menu'] = st.session_state.get('last_menu') or ROLES[st.session_state['peran']][0]
    st.session_state['last_menu'] = st.session_state['menu']


MENU_LABELS = {
    MENU[0]: 'Dashboard',
    MENU[1]: 'Perwalian',
    MENU[2]: 'Cek Individu',
    MENU[3]: 'Pedoman',
    PAGE_KPS: 'Monitoring',
    PAGE_FAKULTAS: 'Evaluasi Studi',
    PAGE_UNIV: 'Rekap',
    PAGE_MHS: 'Studi Saya',
}

with st.sidebar:
    st.markdown('<div class="brand">AADSS · UNAIR<small>UNIVERSITAS AIRLANGGA</small></div>', unsafe_allow_html=True)
    role = st.selectbox('Peran pengguna', list(ROLES), index=None, placeholder='Pilih peran', key='peran', on_change=reset_menu_for_role)
    st.caption('Simulasi tanpa login: membatasi tampilan sesuai jenjang peran di AADSS.')
    st.divider()
    st.caption(f'Monitoring berjenjang AADSS UNAIR · {len(students_fst)} mahasiswa sintetis lintas 8 Prodi S1 (24 dosen wali) · Prodi Prioritas naik ke tingkat Universitas.')


def hero(title, subtitle, eyebrow='Academic Advising Decision Support System · Universitas Airlangga'):
    pill = f'<div class="role-pill">{html.escape(role)}</div>' if role else ''
    st.markdown(f'<div class="hero"><div><div class="eyebrow">{html.escape(eyebrow)}</div>'
                f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>{pill}</div>', unsafe_allow_html=True)
    if role:
        st.markdown(f'<div class="scope">{html.escape(ROLE_SCOPE[role])}</div>', unsafe_allow_html=True)


def notes(expanded=False):
    with st.expander('Catatan syarat kelulusan dan sumber aturan', expanded=expanded):
        notes_body()


def notes_body():
    st.info('**Catatan syarat kelulusan dari pedoman:** tidak boleh ada nilai E; SKS bernilai D maksimal **20% dari SKS yang diperoleh**; IPK akhir minimal **2,00**; kurikulum harus selesai. Skripsi harus lulus ujian dan naskah perbaikan diserahkan. Persyaratan administratif, bebas tanggungan alat/buku, serta ketentuan akademik lainnya tetap berlaku. Batas studi **14 semester**, dengan pengecualian resmi sesuai pedoman. Kehadiran kuliah minimal **75%** dan praktikum **100%**, dengan izin dan keputusan ujian mengikuti pedoman.')
    st.caption('Sumber: pedoman lampiran, PDF hlm. 16-17, 20, 22 (halaman tercetak 12-13, 16, 18). Target 144 SKS ditetapkan untuk aplikasi ini sesuai instruksi pengguna. Analisis mengasumsikan studi tanpa cuti.')


def student_snapshot(student, period, planned=None):
    summary = semester_summary(grades, catalog, student.nim, period - 1)
    cap = max_credits(summary['ips'])
    if planned is None:
        planned = st.session_state.get(f'krs_{student.nim}_{period}', cap)
    return Snapshot(period, summary['ips'], summary['ipk'], summary['sks_lulus'], summary['sks_d'], int(planned), student.nama, student.nim)


def dashboard_rows(student_frame=None):
    target_students = students if student_frame is None else student_frame
    rows = []
    for student in target_students.itertuples():
        snapshot = student_snapshot(student, period)
        result = analyze(snapshot)
        rows.append({
            'Nama': student.nama,
            'NIM': student.nim,
            'Program studi': student.prodi,
            'Dosen Wali': student.dosen_wali,
            'IPS': snapshot.ips,
            'IPK': snapshot.ipk,
            'SKS lulus': snapshot.sks_lulus,
            'SKS D': snapshot.sks_d,
            'Batas SKS': result['batas_sks'],
            'Status': result['kategori'],
            'Estimasi semester 144 SKS': result['estimasi_semester'],
            'Alasan': '; '.join(x['judul'] for x in result['peringatan']) or 'Tidak ada kondisi pemeriksaan yang terpicu.',
            '_tingkat': result['tingkat'],
            '_kode': [x['kode'] for x in result['peringatan']],
        })
    return pd.DataFrame(rows)


SHORT_STATUS = dict(zip(LEVELS, ['Tanpa peringatan', 'Perhatian', 'Prioritas']))
FILTER_LABELS = {'Semua': None, **{short: full for full, short in SHORT_STATUS.items()}}


def reset_list_page():
    st.session_state['list_page'] = 1


def select_risk_from_chart(chart_key):
    points = st.session_state[chart_key]['selection']['points']
    if points:
        status = points[-1].get('customdata', [None])[0]
        if status in SHORT_STATUS:
            st.session_state['risk_filter'] = SHORT_STATUS[status]
    else:
        st.session_state['risk_filter'] = 'Semua'
    reset_list_page()


def select_risk_from_pills():
    st.session_state['chart_epoch'] = st.session_state.get('chart_epoch', 0) + 1
    reset_list_page()


def clear_dashboard_filters():
    st.session_state['risk_filter'] = 'Semua'
    st.session_state['student_search'] = ''
    select_risk_from_pills()


def open_selected_student(table_key, nims):
    rows = st.session_state[table_key]['selection']['rows']
    if rows and 0 <= rows[0] < len(nims):
        chosen_nim = nims[rows[0]]
        if chosen_nim in set(students.nim):
            st.session_state['selected_student'] = chosen_nim
            if MENU[1] in ROLES[role]:
                st.session_state['menu'] = MENU[1]


def move_list_page(delta):
    st.session_state['list_page'] = st.session_state.get('list_page', 1) + delta


def status_style(value):
    color = {
        'Tanpa peringatan': ('#e8f5ef', '#14634f'),
        'Perhatian': ('#fff4dc', '#805717'),
        'Prioritas': ('#fbe9eb', '#9b303c'),
    }
    background, foreground = color[value]
    return f'background-color:{background};color:{foreground};font-weight:600'


def show_result(result, advisor_name=None, advisor_note=None):
    data = result['input']
    st.subheader('Hasil analisis perwalian')
    if data['nama'] or data['nim']:
        info_line = f"**{data['nama'] or 'Mahasiswa'}** · {data['nim'] or 'NIM belum diisi'}"
        if advisor_name:
            info_line += f' · Dosen Wali: **{advisor_name}**'
        st.write(info_line)
    st.caption(f"Awal semester {data['semester_akan']} · hasil semester yang selesai: {data['semester_akan'] - 1}")
    if advisor_note:
        st.info(f'**Catatan / Pertimbangan Dosen Wali:** {advisor_note}')
    a, b, c, d = st.columns(4)
    a.metric('IPS terakhir', '-' if data['ips'] is None else f"{data['ips']:.2f}")
    b.metric('IPK', '-' if data['ipk'] is None else f"{data['ipk']:.2f}")
    c.metric('SKS lulus', data['sks_lulus'])
    d.metric('Maksimum SKS berikutnya', 'Paket prodi' if result['batas_sks'] is None else result['batas_sks'])
    if result['tingkat'] == 2:
        st.error(result['kategori'])
    elif result['tingkat'] == 1:
        st.warning(result['kategori'])
    else:
        st.success(result['kategori'])
    if result['batas_sks'] is None:
        st.info('Awal semester 1 belum memiliki IPS. Jumlah SKS mengikuti paket/ketentuan prodi dan persetujuan dosen wali.')
    elif result['lebih_sks']:
        st.error(f"Rencana {data['rencana_sks']} SKS melampaui batas {result['batas_sks']} SKS sebesar {result['lebih_sks']} SKS.")
    else:
        st.success(f"Rencana {data['rencana_sks']} SKS berada dalam batas maksimum {result['batas_sks']} SKS.")
    st.caption('Maksimum SKS bukan kewajiban mengambil seluruhnya. Persetujuan KRS tetap oleh dosen wali.')
    st.progress(min(data['sks_lulus'] / RULES['target_sks'], 1), text=f"{data['sks_lulus']} / 144 SKS · sisa {result['sisa_sks']} SKS")
    if result['estimasi_semester'] is not None:
        st.write(f"**Estimasi pemenuhan 144 SKS:** akhir semester {result['estimasi_semester']} · laju efektif {result['laju']:.2f} SKS/semester.")
    else:
        st.write('**Estimasi pemenuhan 144 SKS:** belum tersedia karena belum ada laju SKS lulus.')
    st.caption('Estimasi menggunakan rata-rata SKS lulus kumulatif per semester selesai, dibatasi kapasitas KRS dari IPS terakhir. Estimasi kredit tidak menjamin waktu kelulusan atau ketersediaan mata kuliah.')
    if result['sisa_skenario_krs'] is not None:
        st.write(f"**Skenario KRS:** sisa {result['sisa_skenario_krs']} SKS jika seluruh {data['rencana_sks']} SKS rencana merupakan kredit baru dan berhasil lulus. Pengulangan tidak menambah kredit baru.")
    st.write('**Alasan dan saran tindak lanjut**')
    if not result['peringatan']:
        st.write('Tidak ada kondisi pemeriksaan yang terpicu dari ringkasan ini.')
    for alert in result['peringatan']:
        with st.container(border=True):
            st.markdown(f"**{alert['judul']}**")
            st.write(alert['alasan'])
            st.write('Saran: ' + alert['rekomendasi'])
            st.caption('Dasar: ' + alert['sumber'])
    with st.container(border=True):
        st.markdown('**Belum diverifikasi**')
        for item in result['belum_diverifikasi']:
            st.write('• ' + item)
        st.caption('Pemeriksaan minimum evaluasi menggunakan ringkasan pada periode yang dipilih. Formulir manual tidak merekonstruksi keputusan evaluasi historis. Hasil ini tidak menyatakan kelulusan resmi atau keputusan penghentian studi.')
    st.download_button(
        'Unduh hasil individu (JSON)',
        json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"analisis_{data['nim'] or 'individu'}_semester_{data['semester_akan']}.json",
        mime='application/json',
        key='download_result',
    )


@st.cache_data
def cohort_analysis(period, advisor=None, _version=DATA_VERSION):
    """Analisis angkatan S1 Sistem Informasi untuk satu periode (seluruh prodi atau per dosen wali)."""
    target = students if advisor in (None, 'Semua Dosen Wali') else students[students.dosen_wali == advisor]
    rows = []
    for student in target.itertuples():
        summary = semester_summary(grades, catalog, student.nim, period - 1)
        cap = max_credits(summary['ips'])
        result = analyze(Snapshot(period, summary['ips'], summary['ipk'], summary['sks_lulus'], summary['sks_d'], cap, student.nama, student.nim))
        rows.append({
            'Nama': student.nama,
            'NIM': student.nim,
            'Program studi': student.prodi,
            'Departemen': student.departemen,
            'Dosen Wali': student.dosen_wali,
            'Pertimbangan Dosen Wali': student.pertimbangan_dosen_wali,
            'IPS': summary['ips'],
            'IPK': summary['ipk'],
            'SKS lulus': summary['sks_lulus'],
            'SKS D': summary['sks_d'],
            'Batas SKS': result['batas_sks'],
            'Status': result['kategori'],
            'Estimasi semester 144 SKS': result['estimasi_semester'],
            'Alasan': '; '.join(x['judul'] for x in result['peringatan']) or '-',
            '_tingkat': result['tingkat'],
            '_kode': [x['kode'] for x in result['peringatan']],
        })
    return pd.DataFrame(rows)


@st.cache_data
def faculty_analysis(period, prodi_filter=None, _version=DATA_VERSION):
    """Analisis seluruh 8 Program Studi S1 di FST UNAIR pada periode tertentu."""
    target_students = students_fst if prodi_filter in (None, 'Semua Program Studi S1 FST (8 Prodi)') else students_fst[students_fst.prodi == prodi_filter]
    sem_summaries = summaries_fst[summaries_fst.semester == period - 1].set_index('nim')
    rows = []
    for student in target_students.itertuples():
        summary = sem_summaries.loc[student.nim]
        ips = float(summary['ips'])
        ipk = float(summary['ipk'])
        sks_lulus = int(summary['sks_lulus'])
        sks_d = int(summary['sks_d'])
        cap = max_credits(ips)
        result = analyze(Snapshot(period, ips, ipk, sks_lulus, sks_d, cap, student.nama, student.nim))
        rows.append({
            'Departemen': student.departemen,
            'Program studi': student.prodi,
            'KPS': student.kps,
            'Dosen Wali': student.dosen_wali,
            'Nama': student.nama,
            'NIM': student.nim,
            'IPS': ips,
            'IPK': ipk,
            'SKS lulus': sks_lulus,
            'SKS D': sks_d,
            'Batas SKS': result['batas_sks'],
            'Status': result['kategori'],
            'Estimasi semester 144 SKS': result['estimasi_semester'],
            'Pertimbangan Dosen Wali': student.pertimbangan_dosen_wali,
            'Alasan': '; '.join(x['judul'] for x in result['peringatan']) or '-',
            '_tingkat': result['tingkat'],
            '_kode': [x['kode'] for x in result['peringatan']],
        })
    return pd.DataFrame(rows)


def priority_prodi_names(period):
    """Daftar program studi S1 FST yang memiliki mahasiswa berstatus Prioritas."""
    # Prodi yang memiliki kasus prioritas di tingkat fakultas (atau pada periode berjalan) masuk ke Akademik Universitas.
    full = faculty_analysis(period)
    active_priority = set(full.loc[full.Status == LEVELS[2], 'Program studi'])
    configured_priority = {p['prodi'] for p in fst_structure['prodi_s1'] if p.get('ada_prioritas', True)}
    names = active_priority or configured_priority
    return [p for p in FST_PRODI_NAMES if p in names]


def status_counts(df):
    return {SHORT_STATUS[level]: int((df.Status == level).sum()) for level in LEVELS}


def status_metrics(df, percent=False):
    cols = st.container(key='status_metrics').columns(4)
    cols[0].metric('Mahasiswa', len(df))
    for col, (label, count) in zip(cols[1:], status_counts(df).items()):
        col.metric(label, f'{count} ({count / len(df):.0%})' if (percent and len(df)) else count)


def status_trend_chart(analysis_fn):
    trend = pd.DataFrame([{'Awal semester': p, **status_counts(analysis_fn(p))} for p in PERIODS])
    fig = go.Figure([
        go.Bar(name=label, x=trend['Awal semester'], y=trend[label], marker_color=COLORS[level],
               text=trend[label], textposition='inside')
        for level, label in SHORT_STATUS.items()
    ])
    fig.update_layout(
        barmode='stack', height=280, margin=dict(l=0, r=0, t=8, b=5), legend_title_text=None,
        legend=dict(orientation='h', y=-0.25), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title='Perwalian awal semester', dtick=1), yaxis=dict(title='Mahasiswa'),
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    return trend


def alert_frequency(df):
    codes = df['_kode'].explode().dropna()
    freq = codes.map(ALERT_LABELS).value_counts().rename_axis('Peringatan').reset_index(name='Mahasiswa')
    return freq


def evaluation_cases(df):
    rows = []
    for row in df.to_dict('records'):
        for code in row['_kode']:
            if code in EVALUATION_STAGES:
                rows.append({
                    'Program studi': row.get('Program studi', 'S1 Sistem Informasi'),
                    'NIM': row['NIM'],
                    'Nama': row['Nama'],
                    'Dosen Wali': row.get('Dosen Wali', '-'),
                    'Tahap': EVALUATION_STAGES[code],
                    'Ketentuan': EVALUATION_MINIMUM[code],
                    'SKS lulus': row['SKS lulus'],
                    'IPK': row['IPK'],
                    'Estimasi semester 144 SKS': row['Estimasi semester 144 SKS'],
                    'Pertimbangan Dosen Wali': row.get('Pertimbangan Dosen Wali', '-'),
                })
    cols = ['Program studi', 'NIM', 'Nama', 'Dosen Wali', 'Tahap', 'Ketentuan',
            'SKS lulus', 'IPK', 'Estimasi semester 144 SKS', 'Pertimbangan Dosen Wali']
    return pd.DataFrame(rows, columns=cols)


def advisor_summary_table(df):
    rows = []
    for advisor in dict.fromkeys(df['Dosen Wali'].tolist()):
        sub = df[df['Dosen Wali'] == advisor]
        counts = status_counts(sub)
        rows.append({
            'Dosen Wali': advisor,
            'Mahasiswa Wali': len(sub),
            'Tanpa peringatan': counts['Tanpa peringatan'],
            'Perhatian': counts['Perhatian'],
            'Prioritas': counts['Prioritas'],
        })
    return pd.DataFrame(rows)


def prodi_summary_table(df, cases):
    rows = []
    for meta in fst_structure['prodi_s1']:
        p_name = meta['prodi']
        sub = df[df['Program studi'] == p_name]
        if sub.empty:
            continue
        counts = status_counts(sub)
        p_cases = cases[cases['Program studi'] == p_name] if len(cases) else pd.DataFrame()
        n_eval_mhs = int(p_cases['NIM'].nunique()) if len(p_cases) else 0
        eskalasi = 'Masuk Akademik Universitas' if counts['Prioritas'] > 0 else 'Selesai di Fakultas (0 Prioritas)'
        rows.append({
            'Departemen': meta['departemen'],
            'Program studi': p_name,
            'Koordinator Program Studi': meta['kps'],
            'Dosen Wali': len(meta['dosen_wali']),
            'Mahasiswa': len(sub),
            'Tanpa peringatan': counts['Tanpa peringatan'],
            'Perhatian': counts['Perhatian'],
            'Prioritas': counts['Prioritas'],
            'Mahasiswa Evaluasi': n_eval_mhs,
            'Status Eskalasi': eskalasi,
        })
    return pd.DataFrame(rows)


def render_risk_chart_and_roster(df, show_advisor_col=False, show_prodi_col=False, file_prefix='perwalian_2024'):
    counts = df.Status.value_counts().reindex(LEVELS, fill_value=0).reset_index()
    counts.columns = ['Status', 'Jumlah']
    counts['Kategori'] = counts.Status.map(dict(zip(LEVELS, ['Tanpa peringatan', 'Perlu perhatian', 'Prioritas konsultasi'])))
    fig = go.Figure(go.Bar(
        x=counts.Jumlah.tolist(), y=counts.Kategori.tolist(), orientation='h',
        text=counts.Jumlah.tolist(), customdata=counts[['Status']].values.tolist(),
        marker_color=[COLORS[status] for status in counts.Status],
    ))
    fig.update_traces(
        textposition='outside', cliponaxis=False,
        hovertemplate='%{y}: <b>%{x} mahasiswa</b><br>Klik untuk memfilter daftar<extra></extra>',
        marker_line_width=0,
    )
    fig.update_layout(
        showlegend=False, height=210, margin=dict(l=0, r=35, t=8, b=5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title=None, dtick=5, range=[0, max(5, int(counts.Jumlah.max()) + 3)]),
        yaxis=dict(title=None, categoryorder='array', categoryarray=['Tanpa peringatan', 'Perlu perhatian', 'Prioritas konsultasi']),
        clickmode='event+select', dragmode=False, font=dict(size=13),
    )
    chart_key = f'risk_chart_{period}_{st.session_state.get("chart_epoch", 0)}'
    st.plotly_chart(fig, width='stretch', key=chart_key, on_select=partial(select_risk_from_chart, chart_key),
                    selection_mode='points', config={'displayModeBar': False, 'scrollZoom': False})
    st.caption('Klik batang grafik untuk memfilter daftar. Pilih Semua untuk melihat seluruh mahasiswa pada cakupan ini.')

    st.subheader('Daftar Mahasiswa')
    search = st.text_input('Cari nama atau NIM', placeholder='Naufal atau 18724001',
                           key='student_search', on_change=reset_list_page, label_visibility='collapsed')
    st.session_state.setdefault('risk_filter', 'Semua')
    filter_label = st.pills('Tampilkan', list(FILTER_LABELS), selection_mode='single',
                            key='risk_filter', on_change=select_risk_from_pills, label_visibility='collapsed')
    selected_status = FILTER_LABELS.get(filter_label)
    filtered = df if selected_status is None else df[df.Status == selected_status]
    if search:
        mask = (
            filtered.Nama.str.contains(search, case=False, regex=False)
            | filtered.NIM.str.contains(search, case=False, regex=False)
        )
        if show_advisor_col and 'Dosen Wali' in filtered.columns:
            mask = mask | filtered['Dosen Wali'].str.contains(search, case=False, regex=False)
        if show_prodi_col and 'Program studi' in filtered.columns:
            mask = mask | filtered['Program studi'].str.contains(search, case=False, regex=False)
        filtered = filtered[mask]
    filtered = filtered.sort_values(['_tingkat', 'Nama'], ascending=[False, True]).reset_index(drop=True)
    total = len(filtered)
    page_size = 10
    pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, st.session_state.get('list_page', 1)), pages)
    st.session_state['list_page'] = current_page
    start = (current_page - 1) * page_size
    page_rows = filtered.iloc[start:start + page_size]
    st.caption(f'{total} mahasiswa' + (f' · {selected_status}' if selected_status else ' · semua status') +
               (' · hasil pencarian' if search else '') + ' · Pilih baris mahasiswa untuk membuka perwalian.')
    if total:
        cols_to_show = ['Nama', 'NIM']
        if show_prodi_col:
            cols_to_show.append('Program studi')
        if show_advisor_col:
            cols_to_show.append('Dosen Wali')
        cols_to_show.extend(['IPK', 'Batas SKS', 'Status'])
        compact = page_rows[cols_to_show].copy()
        compact['Status'] = compact.Status.map(SHORT_STATUS)
        styled = compact.style.map(status_style, subset=['Status'])
        table_key = f'student_table_{period}_{filter_label}_{search}_{current_page}'
        col_cfg = {
            'Nama': st.column_config.TextColumn('Mahasiswa', width=140),
            'NIM': st.column_config.TextColumn('NIM', width=85),
            'IPK': st.column_config.NumberColumn('IPK', format='%.2f', width=50),
            'Batas SKS': st.column_config.NumberColumn('SKS maks.', format='%d', width=65, help='Maksimum SKS berikutnya dari IPS terakhir.'),
            'Status': st.column_config.TextColumn('Status', width=90),
        }
        if show_prodi_col:
            col_cfg['Program studi'] = st.column_config.TextColumn('Program studi', width=140)
        if show_advisor_col:
            col_cfg['Dosen Wali'] = st.column_config.TextColumn('Dosen Wali', width=170)
        st.dataframe(
            styled, hide_index=True, width='stretch', height=46 * len(compact) + 42, row_height=46,
            column_config=col_cfg, key=table_key,
            on_select=partial(open_selected_student, table_key, page_rows.NIM.tolist()),
            selection_mode='single-row',
        )
        previous, position, next_button = st.columns([1, 2, 1])
        previous.button('Kembali', help='Halaman sebelumnya', disabled=current_page == 1, on_click=move_list_page, args=(-1,), width='stretch')
        position.caption(f'Halaman {current_page} / {pages} · {start + 1}-{start + len(page_rows)} dari {total}')
        next_button.button('Lanjut', help='Halaman berikutnya', disabled=current_page == pages, on_click=move_list_page, args=(1,), width='stretch')
    else:
        st.info('Tidak ada mahasiswa yang cocok. Ubah pencarian atau filter status.')
    export = filtered.drop(columns=[c for c in ['_tingkat', '_kode'] if c in filtered.columns])
    download, reset = st.columns([1, 1])
    download.download_button(
        'Unduh daftar (CSV)', export.to_csv(index=False).encode('utf-8-sig'),
        file_name=f'{file_prefix}_awal_semester_{period}.csv', mime='text/csv', width='stretch',
    )
    reset.button('Tampilkan semua', on_click=clear_dashboard_filters, width='stretch')


if role is None:
    hero('AADSS Universitas Airlangga', 'Academic Advising Decision Support System · Monitoring Perwalian dan Evaluasi Studi Berjenjang.')
    st.markdown('<div class="scope">Pilih peran pengguna untuk membuka dashboard monitoring sesuai jenjang kewenangan akademik, dari mahasiswa wali, program studi, fakultas, hingga universitas.</div>', unsafe_allow_html=True)
    names = list(ROLES)
    top_cols = st.columns(3)
    bottom_cols = st.columns(2)
    card_cols = [top_cols[0], top_cols[1], top_cols[2], bottom_cols[0], bottom_cols[1]]
    for index, (name, col) in enumerate(zip(names, card_cols)):
        with col.container(border=True):
            st.markdown(
                f'<div class="role-card"><span class="role-badge">{html.escape(ROLE_BADGE[name])}</span>'
                f'<h4>{html.escape(name)}</h4><p>{html.escape(ROLE_SUMMARY[name])}</p></div>',
                unsafe_allow_html=True,
            )
            st.button('Masuk', key=f'masuk_{index}', on_click=choose_role, args=(name,), width='stretch', type='primary')
    st.caption(f'AADSS Universitas Airlangga · Cakupan berjenjang: Mahasiswa Wali, Program Studi, Akademik Fakultas (8 Prodi S1 FST), hingga Akademik Universitas (Prodi Prioritas).')
    st.stop()

# Bilah navigasi di area utama agar tetap terlihat di ponsel, saat sidebar tertutup.
if st.session_state.get('menu') not in ROLES[role]:
    st.session_state['menu'] = ROLES[role][0]
with st.container(key='topbar'):
    nav, choose_period, switch = st.columns([6, 2, 1.6], vertical_alignment='center')
    page = nav.segmented_control('Menu', ROLES[role], format_func=MENU_LABELS.get, key='menu',
                                 on_change=keep_menu, label_visibility='collapsed') or ROLES[role][0]
    period = choose_period.selectbox('Perwalian awal semester', PERIODS, index=3, key='periode',
                                     format_func=lambda p: f'Awal semester {p}', label_visibility='collapsed')
    switch.button('Ganti peran', on_click=leave_role, width='stretch', icon=':material/swap_horiz:')

if page == PAGE_KPS:
    si_meta = fst_structure['prodi_s1'][0]
    hero('Monitoring Program Studi', f"{si_meta['prodi']} · KPS: {si_meta['kps']} · Awal semester {period}",
         eyebrow=f"AADSS · {si_meta['departemen']} · FST Universitas Airlangga")
    advisor_options = ['Semua Dosen Wali'] + SI_ADVISORS
    chosen_advisor = st.selectbox(
        'Filter Dosen Wali di Program Studi',
        advisor_options,
        key='kps_dosen_wali',
        on_change=reset_list_page,
        help='KPS memantau seluruh dosen wali di program studi; pilih Semua Dosen Wali atau filter ke salah satu dosen wali.',
    )
    full_prodi_df = cohort_analysis(period)
    df = full_prodi_df if chosen_advisor == 'Semua Dosen Wali' else full_prodi_df[full_prodi_df['Dosen Wali'] == chosen_advisor].reset_index(drop=True)
    status_metrics(df)

    # Struktur perwalian interaktif yang sama dengan Dosen Wali, namun mencakup seluruh dosen wali di prodi.
    render_risk_chart_and_roster(df, show_advisor_col=True, file_prefix='monitoring_kps_si_2024')

    st.subheader('Distribusi Status per Dosen Wali')
    st.caption('Setiap dosen wali di program studi membimbing mahasiswa dengan variasi status Tanpa peringatan, Perhatian, dan Prioritas.')
    st.dataframe(advisor_summary_table(full_prodi_df), hide_index=True, width='stretch')

    left, right = st.columns(2)
    with left:
        st.subheader('Tren status per periode')
        status_trend_chart(partial(cohort_analysis, advisor=chosen_advisor))
    with right:
        st.subheader(f'Jenis peringatan · awal semester {period}')
        freq = alert_frequency(df)
        if len(freq):
            fig = px.bar(freq, x='Mahasiswa', y='Peringatan', orientation='h', text='Mahasiswa', color_discrete_sequence=['#0b4f89'])
            fig.update_layout(height=280, margin=dict(l=0, r=20, t=8, b=5), yaxis=dict(title=None, categoryorder='total ascending'),
                              xaxis=dict(title='Mahasiswa', dtick=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info('Tidak ada peringatan pada periode ini.')

    st.subheader('Daftar tindak lanjut')
    follow = df[df._tingkat > 0].sort_values(['_tingkat', 'Nama'], ascending=[False, True]).reset_index(drop=True)
    follow['Peringatan'] = follow._kode.map(lambda codes: [ALERT_LABELS[c] for c in codes])
    follow['Tindak lanjut'] = follow._tingkat.map({2: 'Koordinasi dosen wali + bahan evaluasi', 1: 'Pantau lewat perwalian'})
    st.caption(f'{len(follow)} mahasiswa dengan peringatan · Pilih baris untuk membuka detail perwalian.')
    if len(follow):
        shown = follow[['Nama', 'NIM', 'Dosen Wali', 'Status', 'Peringatan', 'Tindak lanjut']].copy()
        shown['Status'] = shown.Status.map(SHORT_STATUS)
        table_key = f'kps_table_{period}'
        st.dataframe(
            shown.style.map(status_style, subset=['Status']), hide_index=True, width='stretch',
            column_config={'Peringatan': st.column_config.ListColumn('Peringatan', width='large')},
            key=table_key, on_select=partial(open_selected_student, table_key, follow.NIM.tolist()), selection_mode='single-row',
        )
    st.download_button(
        'Unduh daftar tindak lanjut (CSV)',
        follow.drop(columns=['_tingkat', '_kode', 'Peringatan']).to_csv(index=False).encode('utf-8-sig'),
        file_name=f'tindak_lanjut_prodi_awal_semester_{period}.csv', mime='text/csv',
    )
    st.caption('Rencana KRS diasumsikan sama dengan batas SKS; pemeriksaan KRS per mahasiswa ada di halaman Perwalian Mahasiswa.')
    notes()

elif page == PAGE_FAKULTAS:
    hero('Monitoring Akademik Fakultas', f'Fakultas Sains dan Teknologi (8 Program Studi S1) · Awal semester {period}',
         eyebrow='AADSS · Tingkat Fakultas · Universitas Airlangga')
    st.write('Akademik Fakultas memantau seluruh **8 Program Studi S1 di FST UNAIR** (S1 Sistem Informasi, S1 Matematika, S1 Statistika, '
             'S1 Fisika, S1 Teknik Biomedis, S1 Kimia, S1 Biologi, dan S1 Teknik Lingkungan). '
             'Program studi yang memiliki mahasiswa berstatus **Prioritas / Evaluasi Studi** akan dinaikkan (dieskalasi) ke **Akademik Universitas**, '
             'sedangkan program studi tanpa kasus Prioritas cukup dituntaskan pemantauannya di tingkat fakultas.')
    prodi_options = ['Semua Program Studi S1 FST (8 Prodi)'] + FST_PRODI_NAMES
    selected_prodi = st.selectbox('Filter Program Studi S1 FST', prodi_options, key='fakultas_prodi', on_change=reset_list_page)
    full_fst_df = faculty_analysis(period)
    df_fst = full_fst_df if selected_prodi == 'Semua Program Studi S1 FST (8 Prodi)' else full_fst_df[full_fst_df['Program studi'] == selected_prodi].reset_index(drop=True)

    # Struktur seragam dengan KPS dan Dosen Wali: metrik status, grafik filter, dan daftar mahasiswa.
    status_metrics(df_fst)
    render_risk_chart_and_roster(df_fst, show_advisor_col=True, show_prodi_col=True, file_prefix='monitoring_fakultas_fst_2024')

    st.subheader('Distribusi Status per Program Studi S1 FST (8 Prodi)')
    full_fst_cases = evaluation_cases(full_fst_df)
    prodi_table = prodi_summary_table(full_fst_df, full_fst_cases)
    n_priority_prodi = int((prodi_table['Prioritas'] > 0).sum())
    st.caption(f'Dari 8 Program Studi S1 di FST, terdapat {n_priority_prodi} prodi yang memiliki mahasiswa Prioritas (masuk ke Akademik Universitas) '
               f'dan {8 - n_priority_prodi} prodi tanpa kasus Prioritas.')
    st.dataframe(prodi_table, hide_index=True, width='stretch')

    left, right = st.columns(2)
    with left:
        st.subheader('Tren status fakultas per periode')
        status_trend_chart(partial(faculty_analysis, prodi_filter=selected_prodi))
    with right:
        st.subheader(f'Jenis peringatan · awal semester {period}')
        freq = alert_frequency(df_fst)
        if len(freq):
            fig = px.bar(freq, x='Mahasiswa', y='Peringatan', orientation='h', text='Mahasiswa', color_discrete_sequence=['#0b4f89'])
            fig.update_layout(height=280, margin=dict(l=0, r=20, t=8, b=5), yaxis=dict(title=None, categoryorder='total ascending'),
                              xaxis=dict(title='Mahasiswa', dtick=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info('Tidak ada peringatan pada periode ini.')

    st.subheader('Daftar Verifikasi Evaluasi Studi (Evaluasi I-III)')
    cases = evaluation_cases(df_fst)
    eval_cols = st.columns(4)
    for col, (code, label) in zip(eval_cols, EVALUATION_STAGES.items()):
        col.metric(label, int((cases.Tahap == label).sum()))
    if len(cases):
        shown_cases = cases[['Program studi', 'NIM', 'Nama', 'Dosen Wali', 'Tahap', 'Ketentuan', 'SKS lulus', 'IPK', 'Estimasi semester 144 SKS']]
        st.dataframe(shown_cases, hide_index=True, width='stretch',
                     column_config={'IPK': st.column_config.NumberColumn('IPK', format='%.2f')})
    else:
        st.success('Tidak ada mahasiswa yang perlu diverifikasi untuk tahap evaluasi pada cakupan dan periode ini.')
    st.download_button('Unduh daftar verifikasi evaluasi (CSV)', cases.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'verifikasi_evaluasi_fst_awal_semester_{period}.csv', mime='text/csv')
    st.warning('Status ini berasal dari ringkasan KHS simulasi. Keputusan evaluasi resmi memerlukan transkrip dari Sub Bagian Akademik, '
               'catatan cuti, dan pertimbangan dosen wali.')
    st.subheader('Integritas data')
    st.success(f'Validasi dataset: LULUS · 8 Prodi S1 FST · {len(students_fst)} mahasiswa · 24 dosen wali · {len(summaries_fst)} ringkasan semester.')
    notes()

elif page == PAGE_UNIV:
    hero('Monitoring Akademik Universitas', 'Program Studi dengan Kasus Prioritas di Tingkat Universitas (Tanpa identitas mahasiswa)',
         eyebrow='AADSS · Tingkat Universitas · Universitas Airlangga')
    escalated_prodi = priority_prodi_names(5)
    non_escalated_prodi = [p for p in FST_PRODI_NAMES if p not in escalated_prodi]
    st.info(f'**Mekanisme Eskalasi Fakultas ke Universitas:** Dari **8 Program Studi S1 di FST**, hanya **{len(escalated_prodi)} program studi yang memiliki mahasiswa berstatus Prioritas** '
            f'({", ".join(escalated_prodi)}) yang dimasukkan ke monitoring **Akademik Universitas**. '
            f'Sementara **{len(non_escalated_prodi)} program studi tanpa kasus Prioritas** ({", ".join(non_escalated_prodi)}) selesai dipantau di tingkat **Akademik Fakultas**.')

    period_records = []
    prodi_period_records = []
    for p in PERIODS:
        full_frame = faculty_analysis(p)
        frame = full_frame[full_frame['Program studi'].isin(escalated_prodi)]
        cases = evaluation_cases(frame)
        period_records.append({
            'Awal semester': p,
            'Prodi Prioritas': len(escalated_prodi),
            'Mahasiswa': len(frame),
            **status_counts(frame),
            **{label: int((cases.Tahap == label).sum()) for label in EVALUATION_STAGES.values()},
        })
        for meta in fst_structure['prodi_s1']:
            p_name = meta['prodi']
            if p_name not in escalated_prodi:
                continue
            sub = frame[frame['Program studi'] == p_name]
            sub_cases = cases[cases['Program studi'] == p_name] if len(cases) else pd.DataFrame()
            prodi_period_records.append({
                'Fakultas': 'FST',
                'Departemen': meta['departemen'],
                'Program studi': p_name,
                'Angkatan': 2024,
                'Awal semester': p,
                'Mahasiswa': len(sub),
                **status_counts(sub),
                **{label: int((sub_cases.Tahap == label).sum()) if len(sub_cases) else 0 for label in EVALUATION_STAGES.values()},
            })
    recap = pd.DataFrame(period_records)
    prodi_recap = pd.DataFrame(prodi_period_records)
    current = recap[recap['Awal semester'] == period].iloc[0]
    cols = st.container(key='status_metrics').columns(4)
    cols[0].metric('Mahasiswa (5 Prodi Prioritas)', int(current.Mahasiswa))
    for col, label in zip(cols[1:], SHORT_STATUS.values()):
        col.metric(label, int(current[label]))

    current_prodi = prodi_recap[prodi_recap['Awal semester'] == period].drop(columns=['Fakultas', 'Angkatan', 'Awal semester'])
    left, right = st.columns(2)
    with left:
        st.subheader('Distribusi Status per Prodi Prioritas')
        fig_prodi = go.Figure([
            go.Bar(name=label, y=current_prodi['Program studi'], x=current_prodi[label], orientation='h',
                   marker_color=COLORS[level], text=current_prodi[label], textposition='inside')
            for level, label in SHORT_STATUS.items()
        ])
        fig_prodi.update_layout(
            barmode='stack', height=280, margin=dict(l=0, r=10, t=8, b=5), legend_title_text=None,
            legend=dict(orientation='h', y=-0.25), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='Mahasiswa', dtick=5), yaxis=dict(title=None, autorange='reversed'),
        )
        st.plotly_chart(fig_prodi, width='stretch', config={'displayModeBar': False})
    with right:
        st.subheader('Tren status prodi prioritas per periode')
        fig_trend = go.Figure([
            go.Bar(name=label, x=recap['Awal semester'], y=recap[label], marker_color=COLORS[level],
                   text=recap[label], textposition='inside')
            for level, label in SHORT_STATUS.items()
        ])
        fig_trend.update_layout(
            barmode='stack', height=280, margin=dict(l=0, r=0, t=8, b=5), legend_title_text=None,
            legend=dict(orientation='h', y=-0.25), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='Perwalian awal semester', dtick=1), yaxis=dict(title='Mahasiswa'),
        )
        st.plotly_chart(fig_trend, width='stretch', config={'displayModeBar': False})

    st.subheader(f'Program Studi dengan Kasus Prioritas di Akademik Universitas · Awal semester {period}')
    st.caption(f'Menampilkan {len(escalated_prodi)} dari 8 Program Studi S1 FST yang memiliki mahasiswa berstatus Prioritas (tanpa identitas Nama/NIM).')
    st.dataframe(current_prodi, hide_index=True, width='stretch')

    st.subheader('Rekap per periode (Program Studi Prioritas)')
    st.caption(f'AADSS Universitas Airlangga · {len(escalated_prodi)} Program Studi S1 Prioritas · Angkatan 2024')
    st.dataframe(recap, hide_index=True, width='stretch')

    st.download_button('Unduh rekap agregat prodi prioritas (CSV)', prodi_recap.to_csv(index=False).encode('utf-8-sig'),
                       file_name='rekap_agregat_univ_prodi_prioritas_2024.csv', mime='text/csv')
    st.caption('Identitas mahasiswa tidak ditampilkan pada tingkat universitas; '
               'penetapan sanksi dan penghentian studi oleh Rektor didasarkan pada usulan evaluasi resmi dari fakultas.')

elif page == PAGE_MHS:
    hero('Studi Saya', f'Persiapan perwalian awal semester {period} · KHS sampai semester {period - 1}')
    # Identitas lewat NIM, bukan daftar pilihan, agar nama mahasiswa lain tidak terlihat.
    own_nim = st.text_input('NIM kamu', placeholder='Contoh: 18724001', key='mahasiswa_nim').strip()
    st.caption('Simulasi tanpa login. Pada sistem nyata, NIM diambil dari akun Cyber Campus.')
    match = students[students.nim == own_nim]
    if not own_nim:
        st.info('Masukkan NIM untuk melihat ringkasan studi, batas SKS, dan saran persiapan KRS.')
    elif match.empty:
        st.error('NIM tidak ditemukan pada dataset simulasi S1 Sistem Informasi angkatan 2024.')
    else:
        me = next(match.itertuples())
        own_cap = max_credits(semester_summary(grades, catalog, me.nim, period - 1)['ips'])
        planned = st.number_input('Rencana total SKS KRS', min_value=0, max_value=60, value=own_cap, step=1, key=f'mhs_krs_{me.nim}_{period}')
        with st.container(border=True):
            st.markdown('**Langkah perwalian**')
            st.markdown(f'1. Konsultasikan strategi studi dan rencana KRS dengan dosen wali (**{me.dosen_wali}**), termasuk peringatan di bawah.\n'
                        '2. Isi KRS yang telah dikonsultasikan di Cyber Campus dengan user ID masing-masing.\n'
                        '3. Laporkan ke dosen wali untuk approval KRS. Perubahan hanya pada masa KPRS dengan persetujuan dosen wali.')
            st.caption('PDF hlm. 23 / tercetak 19 dan hlm. 26 / tercetak 22. Hasil aplikasi tidak menggantikan approval dosen wali.')
        show_result(analyze(student_snapshot(me, period, planned)), advisor_name=me.dosen_wali, advisor_note=me.pertimbangan_dosen_wali)
        st.subheader('Riwayat KHS')
        history = pd.DataFrame([semester_summary(grades, catalog, me.nim, s) for s in range(1, period)])
        st.dataframe(history.drop(columns='nim').rename(columns={
            'semester': 'Semester', 'ips': 'IPS', 'ipk': 'IPK', 'sks_diambil': 'SKS diambil',
            'sks_lulus': 'SKS lulus kumulatif', 'sks_baru_lulus': 'SKS baru lulus', 'sks_d': 'SKS D berlaku',
        }), hide_index=True, width='stretch')
        fig = px.line(history.rename(columns={'ips': 'IPS', 'ipk': 'IPK'}), x='semester', y=['IPS', 'IPK'], markers=True, color_discrete_sequence=['#0b4f89', '#bc8c2c'])
        fig.update_layout(height=260, xaxis=dict(title='Semester selesai', dtick=1), yaxis=dict(title='Indeks prestasi', range=[0, 4.1]), legend_title_text=None)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    notes()

elif page == MENU[0]:
    active_advisor = st.selectbox(
        'Dosen Wali Aktif (S1 Sistem Informasi)',
        SI_ADVISORS,
        key='dosen_wali_aktif',
        on_change=reset_list_page,
        help='Dosen wali berfokus pada mahasiswa walinya sendiri.',
    )
    adv_students = students[students.dosen_wali == active_advisor].reset_index(drop=True)
    hero('Dashboard Mahasiswa Wali', f'Dosen Wali: {active_advisor} · {len(adv_students)} Mahasiswa Bimbingan · Awal semester {period}',
         eyebrow='S1 Sistem Informasi · FST · Universitas Airlangga')
    df = dashboard_rows(adv_students)
    cols = st.container(key='status_metrics').columns(4)
    cols[0].metric('Mahasiswa', len(df))
    for idx, level in enumerate(LEVELS):
        cols[idx + 1].metric(['Tanpa peringatan', 'Perhatian', 'Prioritas'][idx], int((df.Status == level).sum()))

    render_risk_chart_and_roster(df, show_advisor_col=False, file_prefix='perwalian_mahasiswa_wali_2024')
    st.caption('Dosen wali hanya menampilkan daftar mahasiswa walinya sendiri. Nama dan NIM adalah contoh sintetis.')
    notes()

elif page == MENU[1]:
    hero('Perwalian Mahasiswa', f'Riwayat KHS dan rencana total SKS · Simulasi awal semester {period}',
         eyebrow='S1 Sistem Informasi · FST · Universitas Airlangga')
    if role == 'Dosen Wali':
        active_advisor = st.selectbox(
            'Dosen Wali Aktif (S1 Sistem Informasi)',
            SI_ADVISORS,
            key='dosen_wali_aktif',
            help='Menampilkan mahasiswa bimbingan dari dosen wali yang dipilih.',
        )
        available_students = students[students.dosen_wali == active_advisor].reset_index(drop=True)
    else:
        available_students = students

    valid_nims = available_students.nim.tolist()
    if st.session_state.get('selected_student') not in valid_nims:
        st.session_state['selected_student'] = valid_nims[0]
    nim = st.selectbox(
        'Pilih mahasiswa wali' if role == 'Dosen Wali' else 'Pilih mahasiswa program studi',
        valid_nims,
        format_func=lambda n: f"{available_students.loc[available_students.nim == n, 'nama'].iloc[0]} · {n} ({available_students.loc[available_students.nim == n, 'dosen_wali'].iloc[0]})",
        key='selected_student',
    )
    student = next(s for s in available_students.itertuples() if s.nim == nim)
    snap = student_snapshot(student, period)
    st.caption(f'Dosen Wali: {student.dosen_wali} · Skenario dummy: {student.skenario}. Bukan kondisi akademik orang nyata.')
    planned = st.number_input('Total SKS rencana KRS', min_value=0, max_value=60, value=max_credits(snap.ips), step=1, key=f'krs_{nim}_{period}')
    st.caption('Masukkan total yang ingin diperiksa. Rencana yang melampaui batas tetap bisa diperiksa agar selisihnya terlihat.')
    show_result(analyze(student_snapshot(student, period, planned)), advisor_name=student.dosen_wali, advisor_note=student.pertimbangan_dosen_wali)
    st.subheader('Riwayat yang sudah tersedia')
    history = pd.DataFrame([semester_summary(grades, catalog, nim, s) for s in range(1, period)])
    st.dataframe(history.drop(columns='nim').rename(columns={
        'semester': 'Semester', 'ips': 'IPS', 'ipk': 'IPK', 'sks_diambil': 'SKS diambil',
        'sks_lulus': 'SKS lulus kumulatif', 'sks_baru_lulus': 'SKS baru lulus', 'sks_d': 'SKS D berlaku',
    }), hide_index=True, width='stretch')
    fig = px.line(history.rename(columns={'ips': 'IPS', 'ipk': 'IPK'}), x='semester', y=['IPS', 'IPK'], markers=True, color_discrete_sequence=['#0b4f89', '#bc8c2c'])
    fig.update_layout(height=280, xaxis=dict(title='Semester selesai', dtick=1), yaxis=dict(title='Indeks prestasi', range=[0, 4.1]), legend_title_text=None)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    with st.expander('Lihat pengambilan mata kuliah dan nilai'):
        available = grades[(grades.nim == nim) & (grades.semester < period)].copy()
        effective = transcript_at(grades, nim, period - 1)
        available['Berlaku pada periode ini'] = list(zip(available.kode, available.semester))
        pairs = set(zip(effective.kode, effective.semester))
        available['Berlaku pada periode ini'] = available['Berlaku pada periode ini'].map(lambda pair: pair in pairs)
        detail = available.merge(catalog[['kode', 'nama', 'sks']], on='kode').drop(columns=['nim', 'berlaku_akhir_semester_4'])
        st.dataframe(detail, hide_index=True, width='stretch')
        st.caption('Pada simulasi, pengambilan terbaru menggantikan nilai sebelumnya. Ini asumsi dataset, bukan klaim aturan penggantian nilai resmi.')
    notes()

elif page == MENU[2]:
    hero('Cek Individu', 'Isi ringkasan KHS, periksa kapasitas KRS dan progres studi tanpa dataset.')
    st.caption('Bisa digunakan untuk angkatan lain. Hasil sementara; data formulir tidak ditambahkan ke dataset.')
    semester = st.number_input('Semester yang akan ditempuh', min_value=1, max_value=30, value=5, step=1, key='manual_semester')
    with st.form('cek_individu'):
        a, b = st.columns(2)
        nama = a.text_input('Nama (opsional)', key='manual_nama')
        nim = b.text_input('NIM (opsional)', key='manual_nim')
        a, b = st.columns(2)
        ips = a.number_input('IPS semester terakhir', min_value=0.0, max_value=4.0, value=3.2, step=0.01, format='%.2f', disabled=semester == 1, key='manual_ips')
        ipk = b.number_input('IPK dari KHS', min_value=0.0, max_value=4.0, value=3.1, step=0.01, format='%.2f', disabled=semester == 1, key='manual_ipk')
        a, b, c = st.columns(3)
        passed = a.number_input('SKS lulus kumulatif', min_value=0, max_value=720, value=76, step=1, disabled=semester == 1, key='manual_passed')
        d = b.number_input('SKS bernilai D', min_value=0, max_value=720, value=0, step=1, disabled=semester == 1, key='manual_d')
        planned = c.number_input('Total SKS rencana KRS', min_value=0, max_value=60, value=20, step=1, key='manual_planned')
        st.caption('Gunakan angka KHS resmi. SKS D termasuk SKS lulus, bukan jumlah mata kuliah. NIM diperlakukan sebagai teks agar angka nol di depan tetap tersimpan.')
        submitted = st.form_submit_button('Analisis perwalian', type='primary')
    if submitted:
        snapshot = Snapshot(int(semester), None if semester == 1 else ips, None if semester == 1 else ipk,
                            0 if semester == 1 else int(passed), 0 if semester == 1 else int(d), int(planned), nama, nim)
        try:
            st.session_state['manual_result'] = analyze(snapshot)
        except ValueError as exc:
            st.session_state.pop('manual_result', None)
            st.error(str(exc))
    if 'manual_result' in st.session_state:
        st.caption('Hasil dari pengiriman formulir terakhir. Setelah mengubah input, tekan Analisis perwalian untuk memperbarui hasil.')
        show_result(st.session_state['manual_result'])
    notes()

else:
    hero('Pedoman dan Dasar Analisis', 'Aturan akademik, struktur FST UNAIR, asal data, serta batas pemeriksaan aplikasi.')
    notes(expanded=True)
    st.subheader('Struktur Program Studi FST UNAIR & Eskalasi ke Universitas')
    st.write('Berdasarkan **Panduan Pendidikan FST UNAIR 2024-2025** (PDF hlm. 2, 6-8), Fakultas Sains dan Teknologi mengelola '
             '**4 Departemen** serta **8 Program Studi S1** (dan 4 Prodi S2 serta 1 Prodi S3 MIPA). '
             'Seluruh 8 Program Studi S1 dipantau pada **Akademik Fakultas**, dan program studi yang memiliki kasus **Prioritas** '
             'dimasukkan ke monitoring **Akademik Universitas**:')
    st.dataframe(pd.DataFrame([
        {'Departemen': p['departemen'], 'Program Studi S1': p['prodi'], 'Koordinator Program Studi (Dummy)': p['kps'],
         'Jumlah Dosen Wali': len(p['dosen_wali']), 'Mahasiswa Simulasi': p['jumlah_mahasiswa'],
         'Cakupan Eskalasi': 'Akademik Fakultas & Akademik Universitas (Ada Prioritas)' if p.get('ada_prioritas', True) else 'Akademik Fakultas saja (0 Prioritas)'}
        for p in fst_structure['prodi_s1']
    ]), hide_index=True, width='stretch')

    st.subheader('Batas SKS dari IPS semester sebelumnya')
    st.table(pd.DataFrame({'IPS': ['Kurang dari 2,00', '2,00-2,50', '2,51-3,00', 'Lebih dari 3,00'], 'Maksimum SKS': [15, 18, 20, 24]}))
    st.caption('PDF hlm. 15 / halaman tercetak 11. IPS menggunakan dua angka desimal seperti KHS; batas bukan target wajib.')
    st.subheader('Evaluasi studi')
    st.write('**Setelah 4 semester:** minimal 40 SKS dan IPK 2,00. **Setelah 8 semester:** minimal 80 SKS dan IPK 2,00. Pemeriksaan dilakukan setelah periode tersebut selesai, bukan saat baru memasuki semester 4 atau 8.')
    st.caption('PDF hlm. 22 / halaman tercetak 18. Evaluasi resmi juga mencakup ketentuan akademik dan studi tanpa izin yang tidak diinput pada aplikasi.')
    st.subheader('Cara menghitung progres')
    st.code('laju = min(SKS lulus kumulatif / semester selesai, batas SKS dari IPS)\nsisa = max(0, 144 - SKS lulus kumulatif)\nestimasi = semester selesai + ceil(sisa / laju)', language='text', wrap_lines=True)
    st.write('Laju nol atau belum ada semester selesai: estimasi belum tersedia. Jika target SKS tercapai, tampilkan semester selesai; syarat kelulusan lain tetap belum diverifikasi. Kategori risiko adalah hasil aturan, bukan probabilitas kegagalan.')
    st.subheader('Asal dan asumsi dataset')
    st.write(f'{len(students_fst)} mahasiswa sintetis angkatan 2024 lintas 8 Program Studi S1 FST (24 dosen wali, {len(summaries_fst)} ringkasan semester 1-4), termasuk 30 mahasiswa S1 Sistem Informasi dengan riwayat 998 pengambilan mata kuliah kurikulum 2021. IPS/IPK dihitung dari bobot nilai dan SKS, dibulatkan dua desimal. Nilai D lulus; E tidak disimulasikan.')
    st.write('Nilai pengambilan terbaru digunakan dalam transkrip simulasi. IPS tiap semester tetap menggunakan seluruh pengambilan pada semester tersebut; IPK dan SKS kumulatif menggunakan mata kuliah unik yang berlaku pada periode itu. Prasyarat rinci, kelas yang tersedia, jadwal, dan approval tidak disimulasikan.')
    st.markdown('[Kurikulum dan handbook 2021 - situs prodi](https://si.fst.unair.ac.id/syllabus/)')
    st.caption(RULES['sumber']['versi'])
    st.success(f'Validasi dataset: LULUS · 8 Prodi S1 FST ({len(students_fst)} mahasiswa · {len(summaries_fst)} ringkasan) · Detail SI (30 mahasiswa · 120 ringkasan · 998 nilai).')
    # Berkas berisi nama/NIM/nilai per mahasiswa hanya untuk peran yang memang melihat data individu.
    files = ['mahasiswa.csv', 'nilai.csv', 'ringkasan_semester.csv', 'mahasiswa_fst.csv', 'ringkasan_fst.csv'] if role in IDENTIFIED_DATA_ROLES else []
    for filename in files + ['kurikulum_2021.csv']:
        st.download_button('Unduh ' + filename, (ROOT / 'data' / filename).read_bytes(), file_name=filename, mime='text/csv', key='dl_' + filename)
    if not files:
        st.caption('Berkas data per mahasiswa (nama, NIM, nilai) hanya tersedia untuk Dosen Wali, Koordinator Program Studi, dan Akademik Fakultas.')
    pdf = ROOT / 'docs/pedoman_fst_2024_2025.pdf'
    if pdf.exists():
        st.download_button('Unduh pedoman pendidikan sumber', pdf.read_bytes(), file_name='Pedoman-Pendidikan-FST-2024-2025-1.pdf', mime='application/pdf')
