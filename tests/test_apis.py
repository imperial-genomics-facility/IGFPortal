import os, unittest, json
from app import db
from app.interop_data_api import search_interop_for_run
from app.interop_data_api import add_interop_data
from app.interop_data_api import edit_interop_data
from app.interop_data_api import add_or_edit_interop_data
# from app.pre_demultiplexing_data_api import search_predemultiplexing_data
# from app.pre_demultiplexing_data_api import add_predemultiplexing_data
# from app.pre_demultiplexing_data_api import edit_predemultiplexing_data
# from app.pre_demultiplexing_data_api import add_or_edit_predemultiplexing_data

class TestApiCase(unittest.TestCase):
    def setUp(self):
        # os.environ['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/app_api.db"
        # from app import app
        # app.config.update({
        #     "TESTING": True,
        #     "CSRF_ENABLED": False,
        #     # "SQLALCHEMY_DATABASE_URI": "sqlite:////tmp/app_api.db",
        # })
        # self.app_context = app.app_context()
        # self.app_context.push()
        db.create_all()
        print(db.get_engine().url)
        self.json_file = "data/interop_example.json"
        self.demult_file = "data/demultiplexing_example.json",


    def tearDown(self):
        db.session.remove()
        # self.app_context.pop()
        db.drop_all()

    def test_search_interop_for_run(self):
        result = \
            search_interop_for_run(run_name='AAAA')
        self.assertTrue(result is None)

    # def test_add_interop_data(self):
    #     with open(self.json_file, 'r') as fp:
    #         json_data = json.load(fp)
    #     run_name = json_data.get("run_name")
    #     result = \
    #         search_interop_for_run(run_name=run_name)
    #     self.assertTrue(result is None)
    #     add_interop_data(run_data=json_data)
    #     result = \
    #         search_interop_for_run(run_name=run_name)
    #     self.assertTrue(result is not None)

    def test_edit_interop_data(self):
        with open(self.json_file, 'r') as fp:
            json_data = json.load(fp)
        run_name = json_data.get("run_name")
        add_interop_data(run_data=json_data)
        json_data['table_data'] = "AAAAA"
        edit_interop_data(run_data=json_data)
        result = \
            search_interop_for_run(run_name=run_name)
        self.assertEqual(result.table_data, "AAAAA")

    def test_add_or_edit_interop_data(self):
        with open(self.json_file, 'r') as fp:
            json_data = json.load(fp)
        run_name = json_data.get("run_name")
        add_or_edit_interop_data(run_data=json_data)
        result = \
            search_interop_for_run(run_name=run_name)
        self.assertTrue(result is not None)
        json_data['table_data'] = "AAAAA"
        add_or_edit_interop_data(run_data=json_data)
        result = \
            search_interop_for_run(run_name=run_name)
        self.assertEqual(result.table_data, "AAAAA")

    # def test_search_predemultiplexing_data(self):
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is None)

    # def test_add_predemultiplexing_data(self):
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is None)
    #     with open(self.demult_file, 'r') as fp:
    #         json_data = json.load(fp)
    #     add_predemultiplexing_data(data=json_data)
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is not None)

    # def test_edit_predemultiplexing_data(self):
    #     with open(self.demult_file, 'r') as fp:
    #         json_data = json.load(fp)
    #     add_predemultiplexing_data(data=json_data)
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is not None)
    #     json_data["flowcell_cluster_plot"] = "CCCC"
    #     edit_predemultiplexing_data(data=json_data)
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertEqual(result.flowcell_cluster_plot, "CCCC")

    # def test_add_or_edit_predemultiplexing_data(self):
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is None)
    #     with open(self.demult_file, 'r') as fp:
    #         json_data = json.load(fp)
    #     add_or_edit_predemultiplexing_data(data=json_data)
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertTrue(result is not None)
    #     json_data["flowcell_cluster_plot"] = "CCCC"
    #     add_or_edit_predemultiplexing_data(data=json_data)
    #     result = \
    #         search_predemultiplexing_data(
    #             run_name="AAAA",
    #             samplesheet_tag="BBBB")
    #     self.assertEqual(result.flowcell_cluster_plot, "CCCC")

if __name__ == '__main__':
  unittest.main()