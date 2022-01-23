import unittest, json
from app import appbuilder, db
from app.apis import search_interop_for_run
from app.apis import add_interop_data
from app.apis import edit_interop_data
from app.apis import add_or_edit_interop_data

class TestApiCase(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.json_file = "data/interop_example.json"

    def tearDown(self):
        db.drop_all()

    def test_search_interop_for_run(self):
        result = \
            search_interop_for_run(run_name='AAAA')
        self.assertTrue(result is None)

    def test_add_interop_data(self):
        with open(self.json_file, 'r') as fp:
            json_data = json.load(fp)
        run_name = json_data.get("run_name")
        result = \
            search_interop_for_run(run_name=run_name)
        self.assertTrue(result is None)
        add_interop_data(run_data=json_data)
        result = \
            search_interop_for_run(run_name=run_name)
        self.assertTrue(result is not None)

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


if __name__ == '__main__':
  unittest.main()