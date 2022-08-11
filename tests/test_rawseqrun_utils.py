import os, unittest, tempfile
from app import db
from datetime import datetime
from app.models import SampleSheetModel, RawSeqrun
from app.raw_seqrun.raw_seqrun_util import fetch_samplesheet_id_for_seqrun
from app.raw_seqrun.raw_seqrun_util import fetch_override_cycle_for_seqrun
from app.raw_seqrun.raw_seqrun_util import fetch_samplesheet_for_seqrun
from app.raw_seqrun.raw_seqrun_util import change_raw_run_status
from app.raw_seqrun.raw_seqrun_util import check_and_filter_raw_seqruns_after_checking_samplesheet
from app.raw_seqrun.raw_seqrun_util import check_and_add_new_raw_seqrun

class TestRawSeqrunA(unittest.TestCase):
    def setUp(self):
        db.create_all()
        try:
            samplesheet1 = \
                SampleSheetModel(
                    samplesheet_tag='samplesheet1',
                    csv_data='data',
                    status='PASS',
                    update_time=datetime.now(),
                    validation_time=datetime.now())
            db.session.add(samplesheet1)
            db.session.flush()
            samplesheet2 = \
                SampleSheetModel(
                    samplesheet_tag='samplesheet2',
                    csv_data='data',
                    status='PASS',
                    update_time=datetime.now(),
                    validation_time=datetime.now(),)
            db.session.add(samplesheet2)
            db.session.flush()
            raw_seqrun1 = \
                RawSeqrun(
                    raw_seqrun_igf_id='run1',
                    samplesheet_id=samplesheet2.samplesheet_id,
                    override_cycles='Y100;I8;I8;Y100')
            db.session.add(raw_seqrun1)
            db.session.flush()
            raw_seqrun2 = \
                RawSeqrun(
                    raw_seqrun_igf_id='run2')
            db.session.add(raw_seqrun2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise

    def tearDown(self):
        db.drop_all()

    def test_fetch_samplesheet_id_for_seqrun(self):
        result = \
            fetch_samplesheet_id_for_seqrun('run1')
        self.assertEqual(result, 2)
        result = \
            fetch_samplesheet_id_for_seqrun('run2')
        self.assertIsNone(result)

    def test_fetch_override_cycle_for_seqrun(self):
        result = \
            fetch_override_cycle_for_seqrun('run1')
        self.assertEqual(result, 'Y100;I8;I8;Y100')
        result = \
            fetch_override_cycle_for_seqrun('run2')
        self.assertIsNone(result)

    def test_fetch_samplesheet_for_seqrun(self):
        result = \
            fetch_samplesheet_for_seqrun('run1')
        #print(db.session.query(SampleSheetModel.validation_time, SampleSheetModel.update_time).filter(SampleSheetModel.samplesheet_tag=='samplesheet2').all())
        self.assertEqual(result.samplesheet_tag, 'samplesheet2')
        self.assertEqual(result.csv_data, 'data')
        result = \
            fetch_samplesheet_for_seqrun('run2')
        self.assertIsNone(result)

    def test_check_and_add_new_raw_seqrun(self):
        seqrun_id_list = ['run1', 'run2', 'run 3']
        check_and_add_new_raw_seqrun(
            seqrun_id_list=seqrun_id_list)
        results = \
            db.session.\
                query(RawSeqrun.raw_seqrun_igf_id).\
                all()
        self.assertEqual(len(results), 3)
        results = [s[0] for s in results]
        self.assertIn('run1', results)
        self.assertIn('run_3', results)

if __name__ == '__main__':
  unittest.main()