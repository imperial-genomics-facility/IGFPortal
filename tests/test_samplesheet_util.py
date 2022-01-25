import unittest
from app.samplesheet.samplesheet_util import SampleSheet

class TestSampleSheetUtil(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_validate_samplesheet_data(self):
        sa = SampleSheet(infile="data/SampleSheet_v1.csv")
        self.assertEqual(len(sa._data), 8)
        errors = sa.validate_samplesheet_data()
        self.assertEqual(len(errors), 10)
        self.assertEqual(len([e for e in errors if "s4" in e]), 1)
        self.assertEqual(len([e for e in errors if "IGF0001" in e]), 1)
        self.assertEqual(len([e for e in errors if "TCCGGAGA, GTCAGTAC" in e]), 1)

if __name__ == '__main__':
  unittest.main()