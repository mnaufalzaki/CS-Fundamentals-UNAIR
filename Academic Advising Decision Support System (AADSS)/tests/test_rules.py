import unittest, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from academic import max_credits,load_data,semester_summary
from risk import Snapshot,analyze
from validate_data import validate
from generate_dummy import generate

class RulesTest(unittest.TestCase):
    def sample(self,**changes):
        values=dict(semester_akan=5,ips=3.2,ipk=3.2,sks_lulus=80,sks_d=0,rencana_sks=20)
        values.update(changes)
        return Snapshot(**values)
    def codes(self,**changes):
        return {x['kode'] for x in analyze(self.sample(**changes))['peringatan']}
    def test_ips_boundaries(self):
        for ips,expected in [(0,15),(1.99,15),(2,18),(2.50,18),(2.51,20),(3,20),(3.01,24),(4,24)]:
            with self.subTest(ips=ips): self.assertEqual(max_credits(ips),expected)
    def test_precision(self):
        with self.assertRaises(ValueError): max_credits(2.505)
    def test_krs_boundary(self):
        self.assertNotIn('KRS',self.codes(ips=2.5,rencana_sks=18))
        r=analyze(self.sample(ips=2.5,rencana_sks=19))
        self.assertEqual(r['lebih_sks'],1)
        self.assertIn('KRS',{a['kode'] for a in r['peringatan']})
        self.assertIsNone(r['sisa_skenario_krs'])
    def test_checkpoint4_timing(self):
        self.assertNotIn('EVAL_4',self.codes(semester_akan=4,sks_lulus=39,ipk=1.99))
        self.assertIn('EVAL_4',self.codes(sks_lulus=39))
        self.assertNotIn('EVAL_4',self.codes(sks_lulus=40,ipk=2))
        self.assertIn('EVAL_4',self.codes(sks_lulus=40,ipk=1.99))
    def test_checkpoint8_timing(self):
        self.assertNotIn('EVAL_8',self.codes(semester_akan=8,sks_lulus=79))
        self.assertIn('EVAL_8',self.codes(semester_akan=9,sks_lulus=79))
        self.assertNotIn('EVAL_8',self.codes(semester_akan=9,sks_lulus=80,ipk=2))
    def test_d_boundary(self):
        self.assertNotIn('D',self.codes(sks_lulus=80,sks_d=16))
        self.assertIn('D',self.codes(sks_lulus=80,sks_d=17))
    def test_study_limit(self):
        self.assertNotIn('MASA',self.codes(semester_akan=14,sks_lulus=140))
        self.assertIn('MASA',self.codes(semester_akan=15,sks_lulus=140))
        self.assertEqual(analyze(self.sample(semester_akan=15,sks_lulus=140))['tingkat'],2)
    def test_projection(self):
        self.assertEqual(analyze(self.sample())['estimasi_semester'],8)
        self.assertEqual(analyze(self.sample(ips=1.99))['estimasi_semester'],9)
        self.assertIn('PROGRES',self.codes(ips=1.99))
        self.assertEqual(analyze(self.sample(semester_akan=9,sks_lulus=144))['estimasi_semester'],8)
    def test_zero_and_first(self):
        self.assertIsNone(analyze(self.sample(sks_lulus=0,ipk=0,ips=0))['estimasi_semester'])
        r=analyze(Snapshot(1,None,None,0,0,20))
        self.assertIsNone(r['batas_sks']);self.assertIsNone(r['estimasi_semester'])
        self.assertEqual(r['tingkat'],0);self.assertIsNone(r['proporsi_d'])
    def test_invalid_input(self):
        for changes in [dict(sks_d=81),dict(sks_lulus=-1),dict(ips=4.1),dict(ipk=float('nan')),
                        dict(ips=None),dict(semester_akan=0),dict(rencana_sks=1.5),dict(sks_lulus=97)]:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError): analyze(self.sample(**changes))
    def test_retake_and_manual_math(self):
        catalog=pd.DataFrame([{'kode':'X','sks':3},{'kode':'Y','sks':2}])
        grades=pd.DataFrame([{'nim':'n','semester':1,'kode':'X','nilai':'D'},
            {'nim':'n','semester':1,'kode':'Y','nilai':'A'}, {'nim':'n','semester':2,'kode':'X','nilai':'A'}])
        first=semester_summary(grades,catalog,'n',1);second=semester_summary(grades,catalog,'n',2)
        self.assertEqual(first['ips'],2.2);self.assertEqual(first['sks_d'],3)
        self.assertEqual(second['sks_lulus'],5);self.assertEqual(second['sks_baru_lulus'],0)
        self.assertEqual(second['ipk'],4);self.assertEqual(second['sks_d'],0)
    def test_latest_data_not_leaked(self):
        students,grades,catalog,_=load_data()
        for nim in students.nim:
            for semester in range(1,5):
                self.assertEqual(semester_summary(grades,catalog,nim,semester),
                    semester_summary(grades[grades.semester<=semester],catalog,nim,semester))
        before=semester_summary(grades,catalog,'18724005',2)
        after=semester_summary(grades,catalog,'18724005',4)
        self.assertGreater(before['sks_d'],after['sks_d'])
    def test_dataset_validation(self): self.assertEqual(validate(*load_data()),[])
    def test_generator_reproducible(self):
        for a,b in zip(generate(),generate()): pd.testing.assert_frame_equal(a,b)
    def test_dataset_equals_manual(self):
        students,grades,catalog,summaries=load_data()
        for row in summaries.itertuples():
            c=semester_summary(grades,catalog,row.nim,row.semester)
            dataset=Snapshot(row.semester+1,c['ips'],c['ipk'],c['sks_lulus'],c['sks_d'],18)
            manual=Snapshot(row.semester+1,row.ips,row.ipk,int(row.sks_lulus),int(row.sks_d),18)
            self.assertEqual(analyze(dataset),analyze(manual))
    def test_bad_data_rejected(self):
        students,grades,catalog,summaries=load_data()
        bad=grades.copy();bad.loc[0,'nilai']='E'
        self.assertTrue(validate(students,bad,catalog,summaries))
        bad=grades.copy();bad.loc[0,'kode']='BUKAN_MK'
        self.assertTrue(validate(students,bad,catalog,summaries))
        bad=summaries.copy();bad.loc[0,'ipk']=0
        self.assertTrue(validate(students,grades,catalog,bad))
        bad=students.copy();bad.loc[1,'nim']=bad.loc[0,'nim']
        self.assertTrue(validate(bad,grades,catalog,summaries))
    def test_unverified_conditions_explicit(self):
        r=analyze(self.sample())
        self.assertTrue(any('Nilai E' in x for x in r['belum_diverifikasi']))
        self.assertFalse(any(x['kode']=='E' for x in r['peringatan']))

if __name__=='__main__': unittest.main()
