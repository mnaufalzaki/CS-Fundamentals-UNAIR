"""Antarmuka perwalian; jalankan dengan streamlit run app.py."""
from functools import partial
import html
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from academic import ROOT, RULES, load_data, semester_summary, transcript_at, max_credits
from risk import Snapshot, analyze, LEVELS
from validate_data import validate

st.set_page_config(page_title='Academic Advising DSS — UNAIR', page_icon='🎓', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
[data-testid="stSidebar"] {background:#072c55;}
[data-testid="stSidebar"] * {color:#f8fafc;}
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] .react-aria-ComboBox * {color:#142c49;-webkit-text-fill-color:#142c49;}
[data-testid="stSidebar"] label {color:#f8fafc!important;}
.block-container {padding-top:2rem;max-width:1440px;}
h1,h2,h3 {color:#073566;}
.hero {border-left:5px solid #d4aa45;background:linear-gradient(110deg,#073566,#155385);color:white;padding:25px 30px;border-radius:12px;margin-bottom:24px;}
.hero h1 {color:white;margin:7px 0 9px;font-size:2.2rem;}
.hero p {margin:0;color:#e3ecf5;}
.eyebrow {font-size:.8rem;letter-spacing:.12em;color:#eacb83;font-weight:700;}
[data-testid="stMetric"] {background:#fff;border:1px solid #dce5ee;border-top:3px solid #d4aa45;border-radius:10px;padding:16px;}
[data-testid="stMetricLabel"] {color:#42617e;min-height:38px;}
[data-testid="stMetricLabel"] p {white-space:normal!important;overflow:visible!important;text-overflow:clip!important;}
.st-key-risk_filters button {border-radius:18px;}
.hero {padding:18px 24px;margin-bottom:18px;}
.hero h1 {font-size:1.85rem;}
[data-testid="stDataFrame"] {border:1px solid #dce5ee;border-radius:12px;overflow:hidden;}

</style>''',unsafe_allow_html=True)
COLORS={LEVELS[0]:'#1b7b6c',LEVELS[1]:'#c38a18',LEVELS[2]:'#b64046'}
MENU=['Dashboard Angkatan 2024','Perwalian Mahasiswa','Cek Individu','Pedoman']
PAGE_KPS='Monitoring Program Studi'
PAGE_FAKULTAS='Administrasi Evaluasi Studi'
PAGE_DEKAN='Ringkasan Pimpinan Fakultas'
PAGE_UNIV='Rekap Universitas'
PAGE_MHS='Studi Saya'
# Peran mengikuti pembagian tugas pada pedoman FST. Pemilihan peran membatasi tampilan, bukan autentikasi.
ROLES={
    'Dosen Wali':MENU,
    'Koordinator Program Studi':[PAGE_KPS,MENU[1],MENU[2],MENU[3]],
    'Akademik Fakultas':[PAGE_FAKULTAS,MENU[3]],
    'Dekan':[PAGE_DEKAN,MENU[3]],
    'Akademik Universitas':[PAGE_UNIV,MENU[3]],
    'Mahasiswa':[PAGE_MHS,MENU[2],MENU[3]],
}
IDENTIFIED_DATA_ROLES={'Dosen Wali','Koordinator Program Studi','Akademik Fakultas'}
ROLE_SCOPE={
    'Mahasiswa':'Konsultasi dengan dosen wali sebelum mengisi KRS, lalu mengisi KRS di Cyber Campus untuk disetujui (PDF hlm. 23, 26). Hanya data diri sendiri.',
    'Dosen Wali':'Perwalian dan persetujuan KRS mahasiswa bimbingan (PDF hlm. 23, 27–28).',
    'Koordinator Program Studi':'Membantu Wakil Dekan bidang akademik memantau kegiatan akademik program studi (PDF hlm. 15).',
    'Akademik Fakultas':'Sub Bagian Akademik: transkrip, daftar perwalian, dan administrasi evaluasi studi (PDF hlm. 20, 25–26).',
    'Dekan':'Pimpinan fakultas: atas pertimbangan dosen wali mengusulkan penghentian studi kepada Rektor (PDF hlm. 29).',
    'Akademik Universitas':'Tingkat universitas: Rektor menetapkan sanksi dan penghentian studi (PDF hlm. 26, 29). Data agregat tanpa identitas.',
}
ALERT_LABELS={'IPK':'IPK di bawah 2,00','EVAL_4':'Evaluasi 4 semester belum terpenuhi',
    'EVAL_8':'Evaluasi 8 semester belum terpenuhi','D':'SKS D melebihi 20%','KRS':'Rencana KRS melebihi batas',
    'PROGRES':'Estimasi melewati 8 semester','LAJU_NOL':'Laju SKS nol',
    'MASA':'Melewati batas studi 14 semester','MASA_ESTIMASI':'Estimasi melewati 14 semester'}
# Tahap evaluasi penghentian studi tetap (PDF hlm. 28) dan kode peringatan yang memicunya.
EVALUATION_STAGES={'EVAL_4':'Evaluasi I · 4 semester','EVAL_8':'Evaluasi II · 8 semester',
    'MASA':'Evaluasi III · melewati 14 semester','MASA_ESTIMASI':'Risiko Evaluasi III · estimasi > 14 semester'}
EVALUATION_MINIMUM={'EVAL_4':'≥ 40 SKS dan IPK ≥ 2,00','EVAL_8':'≥ 80 SKS dan IPK ≥ 2,00',
    'MASA':'Maksimal 14 semester tanpa cuti','MASA_ESTIMASI':'144 SKS sebelum akhir semester 14'}
PERIODS=[2,3,4,5]

@st.cache_data
def validated_data():
    try:
        frames=load_data()
        issues=validate(*frames)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return (None, [f'Data tidak dapat dibaca: {exc}'])
    return frames,issues

(frames,errors)=validated_data()
if errors:
    st.error('Data belum lolos validasi. Analisis dihentikan agar hasil tidak menyesatkan.')
    st.write(errors)
    st.stop()
students, grades, catalog, stored=frames

def reset_menu_for_role():
    st.session_state['menu']=ROLES[st.session_state['peran']][0]


with st.sidebar:
    st.markdown('### SI · UNAIR')
    st.caption('FAKULTAS SAINS DAN TEKNOLOGI')
    role=st.selectbox('Peran pengguna',list(ROLES),key='peran',on_change=reset_menu_for_role)
    st.caption('Simulasi peran tanpa login: membatasi tampilan, bukan pengamanan data.')
    if st.session_state.get('menu') not in ROLES[role]:
        st.session_state['menu']=ROLES[role][0]
    page=st.radio('Menu',ROLES[role],key='menu')
    st.divider()
    period=st.selectbox('Perwalian awal semester',PERIODS,index=3,key='periode')
    st.caption(f'Simulasi angkatan 2024 · KHS sampai semester {period-1}.')
    st.caption('30 mahasiswa sintetis · Kurikulum 2021 · Tanpa cuti')
    st.divider()
    st.caption('Data simulasi · NIM contoh 18724001–18724030.')


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><div class="eyebrow">SISTEM INFORMASI · FST · UNIVERSITAS AIRLANGGA</div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>',unsafe_allow_html=True)
    st.caption(f'Peran: **{role}** · {ROLE_SCOPE[role]}')


def notes():
    st.info('**Catatan syarat kelulusan dari pedoman:** tidak boleh ada nilai E; SKS bernilai D maksimal **20% dari SKS yang diperoleh**; IPK akhir minimal **2,00**; kurikulum harus selesai. Skripsi harus lulus ujian dan naskah perbaikan diserahkan. Persyaratan administratif, bebas tanggungan alat/buku, serta ketentuan akademik lainnya tetap berlaku. Batas studi **14 semester**, dengan pengecualian resmi sesuai pedoman. Kehadiran kuliah minimal **75%** dan praktikum **100%**, dengan izin dan keputusan ujian mengikuti pedoman.')
    st.caption('Sumber: pedoman lampiran, PDF hlm. 16–17, 20, 22 (halaman tercetak 12–13, 16, 18). Target 144 SKS ditetapkan untuk aplikasi ini sesuai instruksi pengguna. Analisis mengasumsikan studi tanpa cuti.')


def student_snapshot(student,period,planned=None):
    summary=semester_summary(grades,catalog,student.nim,period-1)
    cap=max_credits(summary['ips'])
    if planned is None:
        planned=st.session_state.get(f'krs_{student.nim}_{period}',cap)
    return Snapshot(period,summary['ips'],summary['ipk'],summary['sks_lulus'],summary['sks_d'],int(planned),student.nama,student.nim)


def dashboard_rows():
    rows=[]
    for student in students.itertuples():
        snapshot=student_snapshot(student,period)
        result=analyze(snapshot)
        rows.append({'Nama':student.nama,'NIM':student.nim,'IPS':snapshot.ips,'IPK':snapshot.ipk,
            'SKS lulus':snapshot.sks_lulus,'SKS D':snapshot.sks_d,'Batas SKS':result['batas_sks'],
            'Status':result['kategori'],'Estimasi semester 144 SKS':result['estimasi_semester'],
            'Alasan':'; '.join(x['judul'] for x in result['peringatan']) or 'Tidak ada kondisi pemeriksaan yang terpicu.',
            '_tingkat':result['tingkat']})
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
        st.session_state['selected_student'] = nims[rows[0]]
        st.session_state['menu'] = MENU[1]


def move_list_page(delta):
    st.session_state['list_page'] = st.session_state.get('list_page', 1) + delta


def status_style(value):
    color = {'Tanpa peringatan': ('#e8f5ef', '#14634f'), 'Perhatian': ('#fff4dc', '#805717'),
             'Prioritas': ('#fbe9eb', '#9b303c')}
    background, foreground = color[value]
    return f'background-color:{background};color:{foreground};font-weight:600'


def show_result(result):
    data=result['input']
    st.subheader('Hasil analisis perwalian')
    if data['nama'] or data['nim']:
        st.write(f"**{data['nama'] or 'Mahasiswa'}** · {data['nim'] or 'NIM belum diisi'}")
    st.caption(f"Awal semester {data['semester_akan']} · hasil semester yang selesai: {data['semester_akan']-1}")
    a,b,c,d=st.columns(4)
    a.metric('IPS terakhir','—' if data['ips'] is None else f"{data['ips']:.2f}")
    b.metric('IPK','—' if data['ipk'] is None else f"{data['ipk']:.2f}")
    c.metric('SKS lulus',data['sks_lulus'])
    d.metric('Maksimum SKS berikutnya','Paket prodi' if result['batas_sks'] is None else result['batas_sks'])
    if result['tingkat']==2: st.error(result['kategori'])
    elif result['tingkat']==1: st.warning(result['kategori'])
    else: st.success(result['kategori'])
    if result['batas_sks'] is None:
        st.info('Awal semester 1 belum memiliki IPS. Jumlah SKS mengikuti paket/ketentuan prodi dan persetujuan dosen wali.')
    elif result['lebih_sks']:
        st.error(f"Rencana {data['rencana_sks']} SKS melampaui batas {result['batas_sks']} SKS sebesar {result['lebih_sks']} SKS.")
    else:
        st.success(f"Rencana {data['rencana_sks']} SKS berada dalam batas maksimum {result['batas_sks']} SKS.")
    st.caption('Maksimum SKS bukan kewajiban mengambil seluruhnya. Persetujuan KRS tetap oleh dosen wali.')
    st.progress(min(data['sks_lulus']/RULES['target_sks'],1),text=f"{data['sks_lulus']} / 144 SKS · sisa {result['sisa_sks']} SKS")
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
            st.write('Saran: '+alert['rekomendasi'])
            st.caption('Dasar: '+alert['sumber'])
    with st.container(border=True):
        st.markdown('**Belum diverifikasi**')
        for item in result['belum_diverifikasi']: st.write('• '+item)
        st.caption('Pemeriksaan minimum evaluasi menggunakan ringkasan pada periode yang dipilih. Formulir manual tidak merekonstruksi keputusan evaluasi historis. Hasil ini tidak menyatakan kelulusan resmi atau keputusan penghentian studi.')
    st.download_button('Unduh hasil individu (JSON)',json.dumps(result,ensure_ascii=False,indent=2),file_name=f"analisis_{data['nim'] or 'individu'}_semester_{data['semester_akan']}.json",mime='application/json',key='download_result')


@st.cache_data
def cohort_analysis(period):
    """Analisis seluruh angkatan untuk satu periode; rencana KRS diasumsikan sama dengan batas SKS."""
    rows=[]
    for student in students.itertuples():
        summary=semester_summary(grades,catalog,student.nim,period-1)
        cap=max_credits(summary['ips'])
        result=analyze(Snapshot(period,summary['ips'],summary['ipk'],summary['sks_lulus'],summary['sks_d'],cap,student.nama,student.nim))
        rows.append({'Nama':student.nama,'NIM':student.nim,'IPK':summary['ipk'],'SKS lulus':summary['sks_lulus'],
            'Status':result['kategori'],'Estimasi semester 144 SKS':result['estimasi_semester'],
            'Alasan':'; '.join(x['judul'] for x in result['peringatan']) or '—',
            '_tingkat':result['tingkat'],'_kode':[x['kode'] for x in result['peringatan']]})
    return pd.DataFrame(rows)


def status_counts(df):
    return {SHORT_STATUS[level]:int((df.Status==level).sum()) for level in LEVELS}


def status_metrics(df, percent=False):
    cols=st.columns(4)
    cols[0].metric('Mahasiswa',len(df))
    for col,(label,count) in zip(cols[1:],status_counts(df).items()):
        col.metric(label,f'{count} ({count/len(df):.0%})' if percent else count)


def status_trend_chart():
    trend=pd.DataFrame([{'Awal semester':p,**status_counts(cohort_analysis(p))} for p in PERIODS])
    fig=go.Figure([go.Bar(name=label,x=trend['Awal semester'],y=trend[label],marker_color=COLORS[level],
                          text=trend[label],textposition='inside')
                   for level,label in SHORT_STATUS.items()])
    fig.update_layout(barmode='stack',height=280,margin=dict(l=0,r=0,t=8,b=5),legend_title_text=None,
                      legend=dict(orientation='h',y=-0.25),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      xaxis=dict(title='Perwalian awal semester',dtick=1),yaxis=dict(title='Mahasiswa'))
    st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
    return trend


def alert_frequency(df):
    codes=df['_kode'].explode().dropna()
    freq=codes.map(ALERT_LABELS).value_counts().rename_axis('Peringatan').reset_index(name='Mahasiswa')
    return freq


def evaluation_cases(df):
    rows=[]
    for row in df.to_dict('records'):
        for code in row['_kode']:
            if code in EVALUATION_STAGES:
                rows.append({'NIM':row['NIM'],'Nama':row['Nama'],'Tahap':EVALUATION_STAGES[code],
                             'Ketentuan':EVALUATION_MINIMUM[code],'SKS lulus':row['SKS lulus'],'IPK':row['IPK'],
                             'Estimasi semester 144 SKS':row['Estimasi semester 144 SKS']})
    return pd.DataFrame(rows,columns=['NIM','Nama','Tahap','Ketentuan','SKS lulus','IPK','Estimasi semester 144 SKS'])


if page==PAGE_KPS:
    hero('Monitoring Program Studi',f'S1 Sistem Informasi · Angkatan 2024 · Awal semester {period}')
    df=cohort_analysis(period)
    status_metrics(df)
    left,right=st.columns(2)
    with left:
        st.subheader('Tren status per periode')
        status_trend_chart()
    with right:
        st.subheader(f'Jenis peringatan · awal semester {period}')
        freq=alert_frequency(df)
        if len(freq):
            fig=px.bar(freq,x='Mahasiswa',y='Peringatan',orientation='h',text='Mahasiswa',color_discrete_sequence=['#0b4f89'])
            fig.update_layout(height=280,margin=dict(l=0,r=20,t=8,b=5),yaxis=dict(title=None,categoryorder='total ascending'),
                              xaxis=dict(title='Mahasiswa',dtick=5),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
        else:
            st.info('Tidak ada peringatan pada periode ini.')
    st.subheader('Daftar tindak lanjut')
    follow=df[df._tingkat>0].sort_values(['_tingkat','Nama'],ascending=[False,True]).reset_index(drop=True)
    follow['Tindak lanjut']=follow._tingkat.map({2:'Koordinasikan dengan dosen wali; siapkan bahan evaluasi studi untuk pimpinan fakultas',
                                                 1:'Pantau melalui perwalian dosen wali'})
    st.caption(f'{len(follow)} mahasiswa dengan peringatan · Pilih baris untuk membuka detail perwalian.')
    if len(follow):
        shown=follow[['Nama','NIM','Status','Alasan','Tindak lanjut']].copy()
        shown['Status']=shown.Status.map(SHORT_STATUS)
        table_key=f'kps_table_{period}'
        st.dataframe(shown.style.map(status_style,subset=['Status']),hide_index=True,width='stretch',
                     key=table_key,on_select=partial(open_selected_student,table_key,follow.NIM.tolist()),selection_mode='single-row')
    st.download_button('Unduh daftar tindak lanjut (CSV)',follow.drop(columns=['_tingkat','_kode']).to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'tindak_lanjut_prodi_awal_semester_{period}.csv',mime='text/csv')
    st.caption('Rencana KRS diasumsikan sama dengan batas SKS; pemeriksaan KRS per mahasiswa ada di halaman Perwalian Mahasiswa.')
    notes()

elif page==PAGE_FAKULTAS:
    hero('Administrasi Evaluasi Studi',f'Daftar verifikasi evaluasi · Angkatan 2024 · Awal semester {period}')
    st.write('Pedoman menetapkan tiga tahap evaluasi penghentian studi tetap: **Evaluasi I** setelah 4 semester, '
             '**Evaluasi II** setelah 8 semester, dan **Evaluasi III** bila melampaui 14 semester (PDF hlm. 22, 28). '
             'Daftar ini menandai mahasiswa yang ringkasannya belum memenuhi ketentuan, untuk dicocokkan dengan data resmi.')
    df=cohort_analysis(period)
    cases=evaluation_cases(df)
    cols=st.columns(4)
    for col,(code,label) in zip(cols,EVALUATION_STAGES.items()):
        col.metric(label,int((cases.Tahap==label).sum()))
    if len(cases):
        st.dataframe(cases,hide_index=True,width='stretch',column_config={'IPK':st.column_config.NumberColumn('IPK',format='%.2f')})
    else:
        st.success('Tidak ada mahasiswa yang perlu diverifikasi untuk tahap evaluasi pada periode ini.')
    st.download_button('Unduh daftar verifikasi evaluasi (CSV)',cases.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'verifikasi_evaluasi_awal_semester_{period}.csv',mime='text/csv')
    st.warning('Status ini berasal dari ringkasan KHS simulasi. Keputusan evaluasi resmi memerlukan transkrip dari Sub Bagian Akademik, '
               'catatan cuti, dan pertimbangan dosen wali.')
    st.subheader('Integritas data')
    st.success(f'Validasi dataset: LULUS · {len(students)} mahasiswa · {len(stored)} ringkasan semester · {len(grades)} pengambilan mata kuliah.')
    notes()

elif page==PAGE_DEKAN:
    hero('Ringkasan Pimpinan Fakultas',f'S1 Sistem Informasi · Angkatan 2024 · Awal semester {period}')
    df=cohort_analysis(period)
    status_metrics(df,percent=True)
    st.subheader('Tren status angkatan')
    status_trend_chart()
    st.subheader('Kasus evaluasi studi untuk pertimbangan pimpinan')
    cases=evaluation_cases(df)
    if len(cases):
        st.dataframe(cases[['NIM','Nama','Tahap','SKS lulus','IPK']],hide_index=True,width='stretch',
                     column_config={'IPK':st.column_config.NumberColumn('IPK',format='%.2f')})
    else:
        st.success('Tidak ada kasus tahap evaluasi pada periode ini.')
    st.info('Usulan penghentian studi kepada Rektor diajukan Dekan **atas pertimbangan dosen wali** (PDF hlm. 29). '
            'Aplikasi ini hanya menandai kasus dari ringkasan simulasi dan tidak membuat keputusan.')
    with st.expander('Peringatan per jenis'):
        st.dataframe(alert_frequency(df),hide_index=True,width='stretch')

elif page==PAGE_UNIV:
    hero('Rekap Universitas','Ringkasan agregat tanpa identitas mahasiswa')
    records=[]
    for p in PERIODS:
        frame=cohort_analysis(p)
        cases=evaluation_cases(frame)
        records.append({'Fakultas':'FST','Program studi':'S1 Sistem Informasi','Angkatan':2024,'Awal semester':p,
                        'Mahasiswa':len(frame),**status_counts(frame),
                        **{label:int((cases.Tahap==label).sum()) for label in EVALUATION_STAGES.values()}})
    recap=pd.DataFrame(records)
    current=recap[recap['Awal semester']==period].iloc[0]
    cols=st.columns(4)
    cols[0].metric('Mahasiswa',int(current.Mahasiswa))
    for col,label in zip(cols[1:],SHORT_STATUS.values()):
        col.metric(label,int(current[label]))
    st.subheader('Rekap per periode')
    st.dataframe(recap,hide_index=True,width='stretch')
    st.download_button('Unduh rekap agregat (CSV)',recap.to_csv(index=False).encode('utf-8-sig'),
                       file_name='rekap_agregat_fst_si_2024.csv',mime='text/csv')
    st.caption('Dataset simulasi hanya mencakup satu program studi dan satu angkatan. Identitas mahasiswa tidak ditampilkan pada tingkat universitas; '
               'penetapan sanksi dan penghentian studi oleh Rektor memerlukan usulan resmi dari fakultas.')

elif page==PAGE_MHS:
    hero('Studi Saya',f'Persiapan perwalian awal semester {period} · KHS sampai semester {period-1}')
    # Identitas lewat NIM, bukan daftar pilihan, agar nama mahasiswa lain tidak terlihat.
    own_nim=st.text_input('NIM kamu',placeholder='Contoh: 18724001',key='mahasiswa_nim').strip()
    st.caption('Simulasi tanpa login. Pada sistem nyata, NIM diambil dari akun Cyber Campus.')
    match=students[students.nim==own_nim]
    if not own_nim:
        st.info('Masukkan NIM untuk melihat ringkasan studi, batas SKS, dan saran persiapan KRS.')
    elif match.empty:
        st.error('NIM tidak ditemukan pada dataset simulasi angkatan 2024.')
    else:
        me=next(match.itertuples())
        own_cap=max_credits(semester_summary(grades,catalog,me.nim,period-1)['ips'])
        planned=st.number_input('Rencana total SKS KRS',min_value=0,max_value=60,value=own_cap,step=1,key=f'mhs_krs_{me.nim}_{period}')
        show_result(analyze(student_snapshot(me,period,planned)))
        st.subheader('Langkah perwalian')
        for step in ['Konsultasikan strategi studi dan rencana KRS dengan dosen wali, termasuk peringatan di atas.',
                     'Isi KRS yang telah dikonsultasikan di Cyber Campus dengan user ID masing-masing.',
                     'Laporkan ke dosen wali untuk approval KRS. Perubahan hanya pada masa KPRS dengan persetujuan dosen wali.']:
            st.write('• '+step)
        st.caption('PDF hlm. 23 / tercetak 19 dan hlm. 26 / tercetak 22. Hasil aplikasi tidak menggantikan approval dosen wali.')
        st.subheader('Riwayat KHS')
        history=pd.DataFrame([semester_summary(grades,catalog,me.nim,s) for s in range(1,period)])
        st.dataframe(history.drop(columns='nim').rename(columns={'semester':'Semester','ips':'IPS','ipk':'IPK','sks_diambil':'SKS diambil','sks_lulus':'SKS lulus kumulatif','sks_baru_lulus':'SKS baru lulus','sks_d':'SKS D berlaku'}),hide_index=True,width='stretch')
        fig=px.line(history,x='semester',y=['ips','ipk'],markers=True,color_discrete_sequence=['#0b4f89','#bc8c2c'])
        fig.update_layout(height=260,xaxis=dict(title='Semester selesai',dtick=1),yaxis=dict(title='Indeks prestasi',range=[0,4.1]),legend_title_text=None)
        st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
    notes()

elif page==MENU[0]:
    hero('Perwalian Angkatan 2024', f'Simulasi awal semester {period} · Ringkasan KHS sampai semester {period-1}')
    df=dashboard_rows()
    cols=st.columns(4)
    cols[0].metric('Mahasiswa',len(df))
    for idx,level in enumerate(LEVELS):
        cols[idx+1].metric(['Tanpa peringatan','Perhatian','Prioritas'][idx],int((df.Status==level).sum()))

    counts=df.Status.value_counts().reindex(LEVELS,fill_value=0).reset_index()
    counts.columns=['Status','Jumlah']
    counts['Kategori']=counts.Status.map(dict(zip(LEVELS,['Tanpa peringatan','Perlu perhatian','Prioritas konsultasi'])))
    # Satu trace: indeks titik unik saat pengguna berganti kategori.
    fig=go.Figure(go.Bar(x=counts.Jumlah.tolist(),y=counts.Kategori.tolist(),orientation='h',
                         text=counts.Jumlah.tolist(),customdata=counts[['Status']].values.tolist(),
                         marker_color=[COLORS[status] for status in counts.Status]))
    fig.update_traces(textposition='outside',cliponaxis=False,
                      hovertemplate='%{y}: <b>%{x} mahasiswa</b><br>Klik untuk memfilter daftar<extra></extra>',
                      marker_line_width=0)
    fig.update_layout(showlegend=False,height=210,margin=dict(l=0,r=35,t=8,b=5),
                      paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      xaxis=dict(title=None,dtick=5,range=[0,max(5,int(counts.Jumlah.max())+3)]),
                      yaxis=dict(title=None,categoryorder='array',categoryarray=['Tanpa peringatan','Perlu perhatian','Prioritas konsultasi']),
                      clickmode='event+select',dragmode=False,font=dict(size=13))
    chart_key=f'risk_chart_{period}_{st.session_state.get("chart_epoch",0)}'
    st.plotly_chart(fig,width='stretch',key=chart_key,on_select=partial(select_risk_from_chart,chart_key),
                    selection_mode='points',config={'displayModeBar':False,'scrollZoom':False})
    st.caption('Klik batang grafik untuk memfilter daftar. Pilih Semua untuk melihat seluruh mahasiswa.')

    st.subheader('Mahasiswa')
    search=st.text_input('Cari nama atau NIM',placeholder='Naufal atau 18724001',
                         key='student_search',on_change=reset_list_page,label_visibility='collapsed')
    st.session_state.setdefault('risk_filter','Semua')
    filter_label=st.pills('Tampilkan',list(FILTER_LABELS),selection_mode='single',
                          key='risk_filter',on_change=select_risk_from_pills,label_visibility='collapsed')
    selected_status=FILTER_LABELS.get(filter_label)
    filtered=df if selected_status is None else df[df.Status==selected_status]
    if search:
        filtered=filtered[filtered.Nama.str.contains(search,case=False,regex=False)|filtered.NIM.str.contains(search,case=False,regex=False)]
    filtered=filtered.sort_values(['_tingkat','Nama'],ascending=[False,True]).reset_index(drop=True)
    total=len(filtered)
    page_size=10
    pages=max(1,(total+page_size-1)//page_size)
    current_page=min(max(1,st.session_state.get('list_page',1)),pages)
    st.session_state['list_page']=current_page
    start=(current_page-1)*page_size
    page_rows=filtered.iloc[start:start+page_size]
    st.caption(f'{total} mahasiswa' + (f' · {selected_status}' if selected_status else ' · semua status') +
               (' · hasil pencarian' if search else '') + ' · Pilih baris mahasiswa untuk membuka perwalian.')
    if total:
        compact=page_rows[['Nama','NIM','IPK','Batas SKS','Status']].copy()
        compact['Status']=compact.Status.map(SHORT_STATUS)
        styled=compact.style.map(status_style,subset=['Status'])
        table_key=f'student_table_{period}_{filter_label}_{search}_{current_page}'
        st.dataframe(styled,hide_index=True,width='stretch',height=46*len(compact)+42,row_height=46,
                     column_config={
                       'Nama':st.column_config.TextColumn('Mahasiswa',width=140),
                       'NIM':st.column_config.TextColumn('NIM',width=85),
                       'IPK':st.column_config.NumberColumn('IPK',format='%.2f',width=50),
                       'Batas SKS':st.column_config.NumberColumn('SKS maks.',format='%d',width=65,help='Maksimum SKS berikutnya dari IPS terakhir.'),
                       'Status':st.column_config.TextColumn('Status',width=90)},
                     key=table_key,on_select=partial(open_selected_student,table_key,page_rows.NIM.tolist()),
                     selection_mode='single-row')
        previous,position,next_button=st.columns([1,2,1])
        previous.button('Kembali',help='Halaman sebelumnya',disabled=current_page==1,on_click=move_list_page,args=(-1,),width='stretch')
        position.caption(f'Halaman {current_page} / {pages} · {start+1}–{start+len(page_rows)} dari {total}')
        next_button.button('Lanjut',help='Halaman berikutnya',disabled=current_page==pages,on_click=move_list_page,args=(1,),width='stretch')
    else:
        st.info('Tidak ada mahasiswa yang cocok. Ubah pencarian atau filter status.')
    export=filtered.drop(columns='_tingkat')
    download,reset=st.columns([1,1])
    download.download_button('Unduh daftar (CSV)',export.to_csv(index=False).encode('utf-8-sig'),
                             file_name=f'perwalian_2024_awal_semester_{period}.csv',mime='text/csv',width='stretch')
    reset.button('Tampilkan semua',on_click=clear_dashboard_filters,width='stretch')
    st.caption('Nama dan NIM adalah contoh sintetis. Angka risiko tidak mewakili kondisi nyata angkatan 2024.')
    notes()

elif page==MENU[1]:
    hero('Perwalian Mahasiswa',f'Riwayat KHS dan rencana total SKS · Simulasi awal semester {period}')
    nim=st.selectbox('Pilih mahasiswa',students.nim.tolist(),format_func=lambda n:f"{students.loc[students.nim==n,'nama'].iloc[0]} · {n}",key='selected_student')
    student=next(s for s in students.itertuples() if s.nim==nim)
    snap=student_snapshot(student,period)
    st.caption(f'Skenario dummy: {student.skenario}. Bukan kondisi akademik orang nyata.')
    planned=st.number_input('Total SKS rencana KRS',min_value=0,max_value=60,value=max_credits(snap.ips),step=1,key=f'krs_{nim}_{period}')
    st.caption('Masukkan total yang ingin diperiksa. Rencana yang melampaui batas tetap bisa diperiksa agar selisihnya terlihat.')
    show_result(analyze(student_snapshot(student,period,planned)))
    st.subheader('Riwayat yang sudah tersedia')
    history=pd.DataFrame([semester_summary(grades,catalog,nim,s) for s in range(1,period)])
    st.dataframe(history.drop(columns='nim').rename(columns={'semester':'Semester','ips':'IPS','ipk':'IPK','sks_diambil':'SKS diambil','sks_lulus':'SKS lulus kumulatif','sks_baru_lulus':'SKS baru lulus','sks_d':'SKS D berlaku'}),hide_index=True,width='stretch')
    fig=px.line(history,x='semester',y=['ips','ipk'],markers=True,color_discrete_sequence=['#0b4f89','#bc8c2c'])
    fig.update_layout(height=280,xaxis=dict(title='Semester selesai',dtick=1),yaxis=dict(title='Indeks prestasi',range=[0,4.1]),legend_title_text=None)
    st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
    with st.expander('Lihat pengambilan mata kuliah dan nilai'):
        available=grades[(grades.nim==nim)&(grades.semester<period)].copy()
        effective=transcript_at(grades,nim,period-1)
        available['Berlaku pada periode ini']=list(zip(available.kode,available.semester))
        pairs=set(zip(effective.kode,effective.semester))
        available['Berlaku pada periode ini']=available['Berlaku pada periode ini'].map(lambda pair:pair in pairs)
        detail=available.merge(catalog[['kode','nama','sks']],on='kode').drop(columns=['nim','berlaku_akhir_semester_4'])
        st.dataframe(detail,hide_index=True,width='stretch')
        st.caption('Pada simulasi, pengambilan terbaru menggantikan nilai sebelumnya. Ini asumsi dataset, bukan klaim aturan penggantian nilai resmi.')
    notes()

elif page==MENU[2]:
    hero('Cek Individu','Isi ringkasan KHS, periksa kapasitas KRS dan progres studi tanpa dataset.')
    st.caption('Bisa digunakan untuk angkatan lain. Hasil sementara; data formulir tidak ditambahkan ke dataset.')
    semester=st.number_input('Semester yang akan ditempuh',min_value=1,max_value=30,value=5,step=1,key='manual_semester')
    with st.form('cek_individu'):
        a,b=st.columns(2)
        nama=a.text_input('Nama (opsional)',key='manual_nama')
        nim=b.text_input('NIM (opsional)',key='manual_nim')
        a,b=st.columns(2)
        ips=a.number_input('IPS semester terakhir',min_value=0.0,max_value=4.0,value=3.2,step=0.01,format='%.2f',disabled=semester==1,key='manual_ips')
        ipk=b.number_input('IPK dari KHS',min_value=0.0,max_value=4.0,value=3.1,step=0.01,format='%.2f',disabled=semester==1,key='manual_ipk')
        a,b,c=st.columns(3)
        passed=a.number_input('SKS lulus kumulatif',min_value=0,max_value=720,value=76,step=1,disabled=semester==1,key='manual_passed')
        d=b.number_input('SKS bernilai D',min_value=0,max_value=720,value=0,step=1,disabled=semester==1,key='manual_d')
        planned=c.number_input('Total SKS rencana KRS',min_value=0,max_value=60,value=20,step=1,key='manual_planned')
        st.caption('Gunakan angka KHS resmi. SKS D termasuk SKS lulus, bukan jumlah mata kuliah. NIM diperlakukan sebagai teks agar angka nol di depan tetap tersimpan.')
        submitted=st.form_submit_button('Analisis perwalian',type='primary')
    notes()
    if submitted:
        snapshot=Snapshot(int(semester),None if semester==1 else ips,None if semester==1 else ipk,
            0 if semester==1 else int(passed),0 if semester==1 else int(d),int(planned),nama,nim)
        try:
            st.session_state['manual_result']=analyze(snapshot)
        except ValueError as exc:
            st.session_state.pop('manual_result',None)
            st.error(str(exc))
    if 'manual_result' in st.session_state:
        st.caption('Hasil dari pengiriman formulir terakhir. Setelah mengubah input, tekan Analisis perwalian untuk memperbarui hasil.')
        show_result(st.session_state['manual_result'])

else:
    hero('Pedoman dan Dasar Analisis','Aturan akademik, asal data, serta batas pemeriksaan aplikasi.')
    notes()
    st.subheader('Batas SKS dari IPS semester sebelumnya')
    st.table(pd.DataFrame({'IPS':['Kurang dari 2,00','2,00–2,50','2,51–3,00','Lebih dari 3,00'],'Maksimum SKS':[15,18,20,24]}))
    st.caption('PDF hlm. 15 / halaman tercetak 11. IPS menggunakan dua angka desimal seperti KHS; batas bukan target wajib.')
    st.subheader('Evaluasi studi')
    st.write('**Setelah 4 semester:** minimal 40 SKS dan IPK 2,00. **Setelah 8 semester:** minimal 80 SKS dan IPK 2,00. Pemeriksaan dilakukan setelah periode tersebut selesai, bukan saat baru memasuki semester 4 atau 8.')
    st.caption('PDF hlm. 22 / halaman tercetak 18. Evaluasi resmi juga mencakup ketentuan akademik dan studi tanpa izin yang tidak diinput pada aplikasi.')
    st.subheader('Cara menghitung progres')
    st.code('laju = min(SKS lulus kumulatif / semester selesai, batas SKS dari IPS)\nsisa = max(0, 144 - SKS lulus kumulatif)\nestimasi = semester selesai + ceil(sisa / laju)',language='text')
    st.write('Laju nol atau belum ada semester selesai: estimasi belum tersedia. Jika target SKS tercapai, tampilkan semester selesai; syarat kelulusan lain tetap belum diverifikasi. Kategori risiko adalah hasil aturan, bukan probabilitas kegagalan.')
    st.subheader('Asal dan asumsi dataset')
    st.write('30 mahasiswa sintetis angkatan 2024, riwayat semester 1–4, seed 2024. Mata kuliah bersumber dari kurikulum 2021; bobot SKS dikonversi dari ECTS pada handbook dengan rasio 1,6. IPS/IPK dihitung dari bobot nilai dan SKS, dibulatkan dua desimal. Nilai D lulus; E tidak disimulasikan.')
    st.write('Nilai pengambilan terbaru digunakan dalam transkrip simulasi. IPS tiap semester tetap menggunakan seluruh pengambilan pada semester tersebut; IPK dan SKS kumulatif menggunakan mata kuliah unik yang berlaku pada periode itu. Prasyarat rinci, kelas yang tersedia, jadwal, dan approval tidak disimulasikan.')
    st.markdown('[Kurikulum dan handbook 2021 — situs prodi](https://si.fst.unair.ac.id/syllabus/)')
    st.caption(RULES['sumber']['versi'])
    st.success('Validasi dataset: LULUS · 30 mahasiswa · 120 ringkasan semester · riwayat nilai konsisten.')
    # Berkas berisi nama/NIM/nilai per mahasiswa hanya untuk peran yang memang melihat data individu.
    files=['mahasiswa.csv','nilai.csv','ringkasan_semester.csv'] if role in IDENTIFIED_DATA_ROLES else []
    for filename in files+['kurikulum_2021.csv']:
        st.download_button('Unduh '+filename,(ROOT/'data'/filename).read_bytes(),file_name=filename,mime='text/csv',key='dl_'+filename)
    if not files:
        st.caption('Berkas data per mahasiswa (nama, NIM, nilai) hanya tersedia untuk Dosen Wali, Koordinator Program Studi, dan Akademik Fakultas.')
    pdf=ROOT/'docs/pedoman_fst_2024_2025.pdf'
    if pdf.exists():
        st.download_button('Unduh pedoman pendidikan sumber',pdf.read_bytes(),file_name='Pedoman-Pendidikan-FST-2024-2025-1.pdf',mime='application/pdf')
