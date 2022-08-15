import unittest, json
from app import appbuilder, db
from app.raw_analysis.raw_analysis_util import validate_analysis_json

class TestRawAnalysisUtil(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.schema_file = 'app/raw_analysis/analysis_validation.json'

    def tearDown(self):
        db.drop_all()
        pass

    def test_validate_analysis_json(self):
        with open(self.schema_file, 'r') as fp:
            json_data = json.load(fp)

if __name__ == '__main__':
  unittest.main()