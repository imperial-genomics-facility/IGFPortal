import os, unittest, json, tempfile
from app import db, app
from app.models import AdminHomeData
from app.admin_home.admin_home_utils import parse_and_add_new_admin_view_data

class TestAdminHomeUtil1(unittest.TestCase):
    def setUp(self):
        # os.environ['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/app_admin_home.db"
        app.config.update({
            "TESTING": True,
            "CSRF_ENABLED": False,
            # "SQLALCHEMY_DATABASE_URI": "sqlite:////tmp/app_admin_home.db",
        })
        db.create_all()
        self.app_context = app.app_context()
        self.app_context.push()
        print(db.get_engine().url)

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()
        db.drop_all()

    def test_parse_and_add_new_admin_view_data(self):
        json_data = {
            'admin_data_tag': 'test',
            'recent_finished_runs': 1,
            'recent_finished_analysis': 1,
            'ongoing_runs': 1,
            'ongoing_analysis': 1,
            'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
            'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}
        }
        with tempfile.TemporaryDirectory() as temp_dir :
            temp_json_file = \
                os.path.join(
                    temp_dir,
                    'admin_home.json')
            with open(temp_json_file, 'w') as fp:
                json.dump(json_data, fp)
            parse_and_add_new_admin_view_data(temp_json_file)
            results = \
                db.session.\
                    query(AdminHomeData).\
                    filter(AdminHomeData.admin_data_tag=='test').\
                    one_or_none()
            self.assertIsNotNone(results)
            self.assertEqual(results.recent_finished_runs, 1)
            self.assertTrue(isinstance(results.sequence_counts_plot, str))
            json_data = {
                'admin_data_tag': 'test',
                'recent_finished_runs': 2,
                'recent_finished_analysis': 1,
                'ongoing_runs': 1,
                'ongoing_analysis': 1,
                'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
                'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}}
            with open(temp_json_file, 'w') as fp:
                json.dump(json_data, fp)
            parse_and_add_new_admin_view_data(temp_json_file)
            results = \
                db.session.\
                    query(AdminHomeData).\
                    filter(AdminHomeData.admin_data_tag=='test').\
                    one_or_none()
            self.assertIsNotNone(results)
            self.assertEqual(results.recent_finished_runs, 2)

if __name__ == '__main__':
  unittest.main()