import unittest
from app import db
from app.models import RawMetadataModel
from app.raw_metadata.raw_metadata_util import _run_metadata_json_validation
from app.raw_metadata.raw_metadata_util import _validate_metadata_library_type
from app.raw_metadata.raw_metadata_util import _set_metadata_validation_status
from app.raw_metadata.raw_metadata_util import validate_raw_metadata_and_set_db_status

class TestMetaDataValidation1(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_run_metadata_json_validation(self):
        errors = \
            _run_metadata_json_validation(
                metadata_file="data/metadata_file1.csv",
                schema_json="app/raw_metadata/metadata_validation.json")
        self.assertEqual(len(errors), 5)
        self.assertEqual(len([err for err in errors if 'sample105799' in err]), 1)
        self.assertEqual(len([err for err in errors if 'KDSC_77' in err]), 1)
        self.assertEqual(len([err for err in errors if 'Project_cs_23-5-2018_SC' in err]), 1)
        self.assertEqual(len([err for err in errors if 'c.s#email.ac.uk' in err]), 1)
        self.assertTrue(isinstance(errors[0], str))

    def test_validate_metadata_library_type(self):
        err = \
            _validate_metadata_library_type(
                sample_id='test1',
                library_source='GENOMIC',
                library_strategy='CHIP-SEQ',
                experiment_type='TF')
        self.assertTrue(err is None)
        err = \
            _validate_metadata_library_type(
                sample_id='test1',
                library_source='GENOMIC',
                library_strategy='CHIP-SEQ',
                experiment_type='CHIP-Seq')
        self.assertTrue(err is not None)


class TestMetaDataValidation2(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_set_metadata_validation_status(self):
        metadata = \
            RawMetadataModel(
                raw_metadata_id=1,
                metadata_tag='test1',
                raw_csv_data='raw',
                formatted_csv_data='formatted',
                report='')
        try:
            db.session.add(metadata)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.metadata_tag, 'test1')
        self.assertEqual(result.status, 'UNKNOWN')
        _set_metadata_validation_status(
            raw_metadata_id=1,
            status='failed',
            report='error')
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.metadata_tag, 'test1')
        self.assertEqual(result.status, 'FAILED')
        _set_metadata_validation_status(
            raw_metadata_id=1,
            status='validated')
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.metadata_tag, 'test1')
        self.assertEqual(result.status, 'VALIDATED')

    def test_validate_raw_metadata_and_set_db_status(self):
        with open("data/metadata_file1.csv", "r") as fp:
            lines = fp.readlines()
            metadata = \
                RawMetadataModel(
                    raw_metadata_id=1,
                    metadata_tag='test1',
                    raw_csv_data='raw',
                    formatted_csv_data='\n'.join(lines),
                    report='')
            try:
                db.session.add(metadata)
                db.session.flush()
                db.session.commit()
            except:
                db.session.rollback()
                raise
        validate_raw_metadata_and_set_db_status(
            raw_metadata_id=1)
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.metadata_tag, 'test1')
        self.assertEqual(result.status, 'FAILED')
        self.assertTrue(result.report is not None)

if __name__ == '__main__':
  unittest.main()