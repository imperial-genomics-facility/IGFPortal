import unittest
from app.models import RawMetadataModel, Project, Sample
from app.raw_metadata.raw_metadata_util import _run_metadata_json_validation
from app.raw_metadata.raw_metadata_util import _validate_metadata_library_type
from app.raw_metadata.raw_metadata_util import _set_metadata_validation_status
from app.raw_metadata.raw_metadata_util import validate_raw_metadata_and_set_db_status
from app.raw_metadata.raw_metadata_util import compare_metadata_sample_with_db
from app.raw_metadata.raw_metadata_util import search_metadata_table_and_get_new_projects
from app.raw_metadata.raw_metadata_util import parse_and_add_new_raw_metadata

# class TestMetaDataValidation1(unittest.TestCase):
#     def setUp(self):
#         pass

#     def tearDown(self):
#         pass

# def test_run_metadata_json_validation(self):
def test_run_metadata_json_validation():
        errors = \
            _run_metadata_json_validation(
                metadata_file="data/metadata_file1.csv",
                schema_json="app/raw_metadata/metadata_validation.json")
        # self.assertEqual(len(errors), 5)
        # self.assertEqual(len([err for err in errors if 'sample105799' in err]), 1)
        # self.assertEqual(len([err for err in errors if 'KDSC_77' in err]), 1)
        # self.assertEqual(len([err for err in errors if 'Project_cs_23-5-2018_SC' in err]), 1)
        # self.assertEqual(len([err for err in errors if 'c.s#email.ac.uk' in err]), 1)
        # self.assertTrue(isinstance(errors[0], str))
        assert len(errors) == 5
        assert len([err for err in errors if 'sample105799' in err]) == 1
        assert len([err for err in errors if 'KDSC_77' in err]) == 1
        assert len([err for err in errors if 'Project_cs_23-5-2018_SC' in err]) == 1
        assert len([err for err in errors if 'c.s#email.ac.uk' in err]) == 1
        assert isinstance(errors[0], str)


# def test_validate_metadata_library_type(self):
def test_validate_metadata_library_type():
        err = \
            _validate_metadata_library_type(
                sample_id='test1',
                library_source='GENOMIC',
                library_strategy='CHIP-SEQ',
                experiment_type='TF')
        # self.assertTrue(err is None)
        assert err is None
        err = \
            _validate_metadata_library_type(
                sample_id='test1',
                library_source='GENOMIC',
                library_strategy='CHIP-SEQ',
                experiment_type='CHIP-Seq')
        # self.assertTrue(err is not None)
        assert err is not None


# class TestMetaDataValidation2(unittest.TestCase):
#     def setUp(self):
#         db.create_all()

#     def tearDown(self):
#         db.drop_all()

    # def test_set_metadata_validation_status(self):
def test_set_metadata_validation_status(db):
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
        # self.assertTrue(result is not None)
        # self.assertEqual(result.metadata_tag, 'test1')
        # self.assertEqual(result.status, 'UNKNOWN')
        assert result is not None
        assert result.metadata_tag == 'test1'
        assert result.status == 'UNKNOWN'
        _set_metadata_validation_status(
            raw_metadata_id=1,
            status='failed',
            report='error')
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        # self.assertTrue(result is not None)
        # self.assertEqual(result.metadata_tag, 'test1')
        # self.assertEqual(result.status, 'FAILED')
        assert result is not None
        assert result.metadata_tag, 'test1'
        assert result.status == 'FAILED'
        _set_metadata_validation_status(
            raw_metadata_id=1,
            status='validated')
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        # self.assertTrue(result is not None)
        # self.assertEqual(result.metadata_tag, 'test1')
        # self.assertEqual(result.status, 'VALIDATED')
        assert result is not None
        assert result.metadata_tag == 'test1'
        assert result.status == 'VALIDATED'

    # def test_validate_raw_metadata_and_set_db_status(self):
def test_validate_raw_metadata_and_set_db_status(db):
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
            raw_metadata_id=1,
            check_db=True)
        result = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==1).\
                one_or_none()
        # self.assertTrue(result is not None)
        # self.assertEqual(result.metadata_tag, 'test1')
        # self.assertEqual(result.status, 'FAILED')
        # self.assertTrue(result.report is not None)
        assert result is not None
        assert result.metadata_tag == 'test1'
        assert result.status == 'FAILED'
        assert result.report is not None

    # def test_compare_metadata_sample_with_db(self):
def test_compare_metadata_sample_with_db(db):
        project = \
            Project(
                project_id=1,
                project_igf_id="test1")
        sample = \
            Sample(
                sample_id=1,
                sample_igf_id='sample105799',
                project_id=1)
        try:
            db.session.add(project)
            db.session.add(sample)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        metadata_errors = \
            compare_metadata_sample_with_db(
                metadata_file="data/metadata_file1.csv")
        # self.assertTrue("Sample sample105799 is linked to project test1, not IGFQ000001_cs_23-5-2018_SC" in metadata_errors)
        assert "Sample sample105799 is linked to project test1, not IGFQ000001_cs_23-5-2018_SC" in metadata_errors


# class TestMetadataApiutil1(unittest.TestCase):
#     def setUp(self):
#         db.create_all()

#     def tearDown(self):
#         db.drop_all()

    # def test_search_metadata_table_and_get_new_projects(self):
def test_search_metadata_table_and_get_new_projects(db):
        metadata1 = \
            RawMetadataModel(
                metadata_tag='test1',
                raw_csv_data='raw',
                formatted_csv_data='formatted',
                report='')
        metadata2 = \
            RawMetadataModel(
                metadata_tag='test2',
                raw_csv_data='raw',
                formatted_csv_data='formatted',
                report='')
        try:
            db.session.add(metadata1)
            db.session.add(metadata2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        new_projects = \
            search_metadata_table_and_get_new_projects(
                data={"project_list":["test1", "test3"]})
        # self.assertTrue(isinstance(new_projects, list))
        # self.assertEqual(len(new_projects), 1)
        # self.assertTrue("test3" in new_projects)
        assert isinstance(new_projects, list)
        assert len(new_projects) == 1
        assert "test3" in new_projects
        new_projects = \
            search_metadata_table_and_get_new_projects(
                data={"project_list":["test1", "test2"]})
        # self.assertTrue(isinstance(new_projects, list))
        # self.assertEqual(len(new_projects), 0)
        assert isinstance(new_projects, list)
        assert len(new_projects) == 0

# class TestRawMetadataLoading(unittest.TestCase):
#     def setUp(self):
#         db.create_all()

#     def tearDown(self):
#         db.drop_all()

    # def test_parse_and_add_new_raw_metadata(self):
def test_parse_and_add_new_raw_metadata(db):
        metadata_list = [{
            'metadata_tag': 'test1',
            'raw_csv_data': [{'project_id','sample_id'},{'a', 'b'}],
            'formatted_csv_data': [{'project_id','sample_id'},{'a', 'b'}]},{
            'metadata_tag': 'test2',
            'raw_csv_data': [{'project_id','sample_id'},{'c', 'd'}],
            'formatted_csv_data': [{'project_id','sample_id'},{'c', 'd'}]}]
        parse_and_add_new_raw_metadata(data=metadata_list)
        results = db.session.query(RawMetadataModel.metadata_tag).all()
        results = [i[0] for i in results]
        # self.assertEqual(len(results), 2)
        # self.assertTrue('test1' in results)
        assert len(results) == 2
        assert 'test1' in results

if __name__ == '__main__':
  unittest.main()