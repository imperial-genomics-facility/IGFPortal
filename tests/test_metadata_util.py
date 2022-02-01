import os, unittest, json, tempfile
from app import appbuilder, db
from app.models import Project
from app.metadata.metadata_util import cleanup_and_load_new_data_to_metadata_tables

class TestMetadataUtil1(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_cleanup_and_load_new_data_to_metadata_tables(self):
        project = \
            Project(
                project_id=2,
                project_igf_id="test1")
        try:
            db.session.add(project)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        result = \
            db.session.\
                query(Project).\
                filter(Project.project_igf_id=="test1").\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.project_id, 2)
        json_data = {
            "project": [{
                "project_id": 1,
                "project_igf_id": "test1"}]}
        with tempfile.TemporaryDirectory() as temp_dir :
            temp_json_file = \
                os.path.join(
                    temp_dir,
                    'metadata_db.json')
            with open(temp_json_file, 'w') as fp:
                json.dump(json_data, fp)
            cleanup_and_load_new_data_to_metadata_tables(temp_json_file)
            result = \
                db.session.\
                    query(Project).\
                    filter(Project.project_igf_id=="test1").\
                    one_or_none()
            self.assertTrue(result is not None)
            self.assertEqual(result.project_id, 1)

if __name__ == '__main__':
  unittest.main()