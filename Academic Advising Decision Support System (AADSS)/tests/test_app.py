"""Uji runtime Streamlit tanpa memerlukan browser eksternal."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
APP=Path(__file__).resolve().parents[1]/'app.py'

class AppTestCase(unittest.TestCase):
    def setUp(self): self.app=AppTest.from_file(str(APP),default_timeout=30).run()
    def test_dashboard_and_periods(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value,'30')
        self.app.text_input(key='student_search').set_value('18724001').run()
        self.assertEqual(len(self.app.dataframe[0].value),1)
        self.assertEqual(self.app.dataframe[0].value.iloc[0]['Nama'],'Naufal Pratama')
        self.app.text_input(key='student_search').set_value('').run()
        self.app.button[1].click().run()
        self.assertEqual(self.app.session_state['list_page'],2)
        for semester in [2,3,4,5]:
            self.app.selectbox(key='periode').set_value(semester).run()
            self.assertFalse(self.app.exception)
            self.assertEqual(len(self.app.dataframe[0].value),10)
    def test_perwalian_and_invalid_krs(self):
        self.app.radio(key='menu').set_value('Perwalian Mahasiswa').run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[2].value,'80')
        self.app.number_input(key='krs_18724001_5').set_value(25).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('melampaui' in error.value for error in self.app.error))
        self.app.selectbox(key='periode').set_value(4).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[2].value,'59')
        self.assertEqual(len(self.app.dataframe[0].value),3)
    def test_manual_valid_invalid_first_and_cross_cohort(self):
        self.app.radio(key='menu').set_value('Cek Individu').run()
        self.assertFalse(self.app.exception)
        self.app.text_input(key='manual_nim').set_value('001234')
        self.app.text_input(key='manual_nama').set_value('Mahasiswa lain')
        self.app.number_input(key='manual_ips').set_value(2.5)
        self.app.number_input(key='manual_planned').set_value(19)
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[3].value,'18')
        self.assertTrue(any('melampaui' in error.value for error in self.app.error))
        self.app.number_input(key='manual_d').set_value(77)
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('tidak boleh melebihi' in error.value for error in self.app.error))
        self.assertNotIn('manual_result',self.app.session_state)
        self.app.number_input(key='manual_semester').set_value(1).run()
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[3].value,'Paket prodi')
    def test_status_filters_and_search(self):
        self.app.get('button_group')[0].set_value('Prioritas').run()
        self.assertFalse(self.app.exception)
        table=self.app.dataframe[0].value
        self.assertEqual(len(table),7)
        self.assertEqual(set(table.Status),{'Prioritas'})
        self.assertEqual(list(table.columns),['Nama','NIM','IPK','Batas SKS','Status'])
        self.app.text_input(key='student_search').set_value('18724003').run()
        self.assertEqual(self.app.dataframe[0].value.iloc[0]['Nama'],'Bima Saputra')
        self.app.text_input(key='student_search').set_value('18724001').run()
        self.assertEqual(len(self.app.dataframe),0)
        self.assertTrue(any('Tidak ada mahasiswa' in x.value for x in self.app.info))
        self.app.button[-1].click().run()
        self.assertEqual(self.app.get('button_group')[0].value,'Semua')
        self.assertEqual(self.app.text_input(key='student_search').value,'')
        self.assertEqual(len(self.app.dataframe[0].value),10)
    def test_search_resets_page(self):
        self.app.button[1].click().run()
        self.assertEqual(self.app.session_state['list_page'],2)
        self.app.text_input(key='student_search').set_value('18724001').run()
        self.assertEqual(self.app.session_state['list_page'],1)
        self.assertEqual(self.app.dataframe[0].value.iloc[0]['NIM'],'18724001')
    def set_role(self,role):
        self.app.selectbox(key='peran').set_value(role).run()
        self.assertFalse(self.app.exception)
    def test_role_menus(self):
        # Dosen Wali terakhir agar setiap langkah benar-benar mengganti peran.
        expected={'Koordinator Program Studi':['Monitoring Program Studi','Perwalian Mahasiswa','Cek Individu','Pedoman'],
                  'Akademik Fakultas':['Administrasi Evaluasi Studi','Pedoman'],
                  'Dekan':['Ringkasan Pimpinan Fakultas','Pedoman'],
                  'Akademik Universitas':['Rekap Universitas','Pedoman'],
                  'Mahasiswa':['Studi Saya','Cek Individu','Pedoman'],
                  'Dosen Wali':['Dashboard Angkatan 2024','Perwalian Mahasiswa','Cek Individu','Pedoman']}
        self.app.radio(key='menu').set_value('Cek Individu').run()
        for role,menu in expected.items():
            self.app.radio(key='menu').set_value('Pedoman').run()
            with self.subTest(role=role):
                self.set_role(role)
                self.assertEqual(list(self.app.radio(key='menu').options),menu)
                self.assertEqual(self.app.radio(key='menu').value,menu[0])
    def test_coordinator_follow_up(self):
        self.set_role('Koordinator Program Studi')
        self.assertEqual([m.value for m in self.app.metric],['30','8','15','7'])
        table=self.app.dataframe[0].value
        self.assertEqual(len(table),22)
        self.assertNotIn('Tanpa peringatan',set(table.Status))
    def test_faculty_evaluation_list(self):
        self.set_role('Akademik Fakultas')
        self.assertEqual([m.value for m in self.app.metric],['7','0','0','4'])
        self.assertEqual(len(self.app.dataframe[0].value),11)
        self.app.selectbox(key='periode').set_value(2).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value,'0')
    def test_dean_summary(self):
        self.set_role('Dekan')
        self.assertEqual(self.app.metric[3].value,'7 (23%)')
        self.assertEqual(list(self.app.dataframe[0].value.columns),['NIM','Nama','Tahap','SKS lulus','IPK'])
        self.assertTrue(any('pertimbangan dosen wali' in x.value for x in self.app.info))
    def test_university_recap_has_no_identity(self):
        self.set_role('Akademik Universitas')
        recap=self.app.dataframe[0].value
        self.assertEqual(list(recap['Awal semester']),[2,3,4,5])
        self.assertFalse({'NIM','Nama'} & set(recap.columns))
        self.assertEqual(int(recap.loc[recap['Awal semester']==5,'Prioritas'].iloc[0]),7)
    def test_student_sees_only_own_data(self):
        self.set_role('Mahasiswa')
        self.assertEqual(len(self.app.selectbox),2)  # hanya peran dan periode; tanpa daftar nama mahasiswa
        self.assertEqual(len(self.app.dataframe),0)
        self.assertTrue(any('Masukkan NIM' in x.value for x in self.app.info))
        self.app.text_input(key='mahasiswa_nim').set_value('99999999').run()
        self.assertTrue(any('tidak ditemukan' in x.value for x in self.app.error))
        self.app.text_input(key='mahasiswa_nim').set_value('18724001').run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[2].value,'80')
        history=self.app.dataframe[0].value
        self.assertEqual(list(history.Semester),[1,2,3,4])
        self.assertNotIn('Nama',history.columns)
        self.app.number_input(key='mhs_krs_18724001_5').set_value(25).run()
        self.assertTrue(any('melampaui' in error.value for error in self.app.error))
    def test_dataset_downloads_follow_role(self):
        personal={'Unduh mahasiswa.csv','Unduh nilai.csv','Unduh ringkasan_semester.csv'}
        expected={'Koordinator Program Studi':True,'Akademik Fakultas':True,'Dekan':False,
                  'Akademik Universitas':False,'Mahasiswa':False,'Dosen Wali':True}
        for role,allowed in expected.items():
            with self.subTest(role=role):
                self.set_role(role)
                self.app.radio(key='menu').set_value('Pedoman').run()
                self.assertFalse(self.app.exception)
                labels={b.proto.label for b in self.app.get('download_button')}
                self.assertIn('Unduh kurikulum_2021.csv',labels)
                self.assertEqual(personal<=labels,allowed)
                if not allowed: self.assertFalse(personal&labels)
    def test_guidelines(self):
        self.app.radio(key='menu').set_value('Pedoman').run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('tidak boleh ada nilai E' in x.value for x in self.app.info))

if __name__=='__main__': unittest.main()
