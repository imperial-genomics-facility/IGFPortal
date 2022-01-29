import unittest
from app import db
from app.models import SampleSheetModel
from app.samplesheet.samplesheet_util import SampleSheet
from app.samplesheet.samplesheet_util import update_samplesheet_validation_entry_in_db
from app.samplesheet.samplesheet_util import validate_samplesheet_data_and_update_db

class TestSampleSheetUtil(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_validate_samplesheet_data1(self):
        sa = SampleSheet(infile="data/SampleSheet_v1.csv")
        self.assertEqual(len(sa._data), 8)
        errors = sa.validate_samplesheet_data()
        self.assertEqual(len(errors), 10)
        self.assertEqual(len([e for e in errors if "s4" in e]), 1)
        self.assertEqual(len([e for e in errors if "IGF0001" in e]), 1)
        self.assertEqual(len([e for e in errors if "TCCGGAGA, GTCAGTAC" in e]), 1)

    def test_validate_samplesheet_data2(self):
        sa = SampleSheet(infile="data/SampleSheet_v2.csv")
        self.assertEqual(len(sa._data), 16)
        errors = sa.validate_samplesheet_data()
        self.assertEqual(len(errors), 2)

class TestSampleSheetDbUpdate(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_update_samplesheet_validation_entry_in_db(self):
        samplesheet = \
            SampleSheetModel(
                samplesheet_tag='test1',
                csv_data='data')
        try:
            db.session.add(samplesheet)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag=='test1').\
                one_or_none()
        self.assertTrue(entry is not None)
        self.assertEqual(entry.status, 'UNKNOWN')
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag=='test2').\
                one_or_none()
        self.assertTrue(entry is None)
        update_samplesheet_validation_entry_in_db(
            samplesheet_tag='test1',
            report='FAILED',
            status='failed')
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag=='test1').\
                one_or_none()
        self.assertTrue(entry is not None)
        self.assertEqual(entry.status, 'FAILED')
        self.assertEqual(entry.report, 'FAILED')
        update_samplesheet_validation_entry_in_db(
            samplesheet_tag='test1',
            report='PASS',
            status='pass')
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag=='test1').\
                one_or_none()
        self.assertTrue(entry is not None)
        self.assertEqual(entry.status, 'PASS')
        self.assertEqual(entry.report, 'PASS')


    def test_validate_samplesheet_data_and_update_db(self):
        with open("data/SampleSheet_v1.csv", 'r') as fp:
            csv_data = fp.readlines()
            csv_data = '\n'.join(csv_data)
        samplesheet = \
            SampleSheetModel(
                samplesheet_tag='test1',
                csv_data=csv_data)
        try:
            db.session.add(samplesheet)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        validate_samplesheet_data_and_update_db(
            samplesheet_id=1)
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag=='test1').\
                one_or_none()
        self.assertTrue(entry is not None)
        self.assertEqual(entry.status, 'FAILED')

if __name__ == '__main__':
  unittest.main()