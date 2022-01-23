import unittest
from app import appbuilder, db
from app.apis import search_interop_for_run

class TestApiCase(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_search_interop_for_run(self):
        result = \
            search_interop_for_run(run_name='AAAA')
        self.assertTrue(result is None)

if __name__ == '__main__':
  unittest.main()