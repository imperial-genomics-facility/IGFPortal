import os, unittest, json, tempfile
from app import appbuilder, db
from app.models import Project, Sample, IgfUser
from app.metadata.metadata_util import cleanup_and_load_new_data_to_metadata_tables
from app.metadata.metadata_util import check_for_projects_in_metadata_db
from app.metadata.metadata_util import check_sample_and_project_ids_in_metadata_db
from app.metadata.metadata_util import check_user_name_and_email_in_metadata_db

class TestMetadataUtil1(unittest.TestCase):
    def setUp(self):
        # db.drop_all()
        # if os.path.exists('/tmp/app.db'):
        #     os.remove('/tmp/app.db')
        db.create_all()

    def tearDown(self):
        db.session.remove()
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

class TestMetadataUtil2(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_check_for_projects_in_metadata_db(self):
        project = \
            Project(
                project_id=1,
                project_igf_id="test11")
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
                filter(Project.project_igf_id=="test11").\
                one_or_none()
        self.assertTrue(result is not None)
        self.assertEqual(result.project_id, 1)
        output, errors = \
            check_for_projects_in_metadata_db(project_list=["test11", "test12"])
        self.assertTrue(output.get('test11'))
        self.assertFalse(output.get('test12'))
        self.assertEqual(len(errors), 1)

class TestMetadataUtil3(unittest.TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_check_sample_and_project_ids_in_metadata_db(self):
        project1 = \
            Project(
                project_id=1,
                project_igf_id="test1")
        project2 = \
            Project(
                project_id=2,
                project_igf_id="test2")
        sample1 = \
            Sample(
                sample_id=1,
                sample_igf_id='test_sample1',
                project_id=1)
        sample2 = \
            Sample(
                sample_id=2,
                sample_igf_id='test_sample2',
                project_id=2)
        try:
            db.session.add(project1)
            db.session.add(project2)
            db.session.add(sample1)
            db.session.add(sample2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        sample_project_list = [{
            'sample_igf_id':'test_sample1',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''},{
            'sample_igf_id':'test_sample2',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''},{
            'sample_igf_id':'test_sample3',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''}]
        errors = \
            check_sample_and_project_ids_in_metadata_db(
                sample_project_list)
        self.assertTrue('Missing metadata for sample test_sample3' in errors)
        self.assertTrue("Sample test_sample2 is linked to project test2, not test1" in errors)

    def test_check_user_name_and_email_in_metadata_db(self):
        user = \
            IgfUser(
                name='User A',
                email_id='a@g.com')
        try:
            db.session.add(user)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        data1 = [{'name':'User B', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        self.assertTrue('Missing name User B in db' in errors)
        self.assertTrue('Missing email b@g.com in db' in errors)
        data1 = [{'name':'User A', 'email_id': 'a@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        self.assertEqual(len(errors), 0)
        data1 = [{'name':'User B', 'email_id': 'a@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        self.assertTrue('Missing name User B in db' in errors)
        self.assertTrue("Email a@g.com registered with name User A, not User B" in errors)
        data1 = [{'name':'User A', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        self.assertTrue('Missing email b@g.com in db' in errors)
        self.assertTrue("User User A registered with email id a@g.com, not b@g.com" in errors)
        data1 = [{'name':'User B', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(
                name_email_list=data1,
                check_missing=False)
        self.assertEqual(len(errors), 0)

if __name__ == '__main__':
  unittest.main()