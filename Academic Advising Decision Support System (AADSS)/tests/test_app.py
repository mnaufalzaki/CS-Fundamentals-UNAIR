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
    def test_guidelines(self):
        self.app.radio(key='menu').set_value('Pedoman').run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('tidak boleh ada nilai E' in x.value for x in self.app.info))

if __name__=='__main__': unittest.main()
