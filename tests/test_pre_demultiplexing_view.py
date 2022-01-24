import unittest, json
from app import appbuilder, db
from app.apis import search_predemultiplexing_data
from app.apis import add_predemultiplexing_data
from app.pre_demultiplexing_view import get_pre_demultiplexing_data

class TestPreDemultView(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.demult_file = "data/demultiplexing_example.json"

    def tearDown(self):
        db.drop_all()

    def test_get_pre_demultiplexing_data(self):
        with open(self.demult_file, 'r') as fp:
            json_data = json.load(fp)
        add_predemultiplexing_data(data=json_data)
        result = \
            search_predemultiplexing_data(
                run_name="AAAA",
                samplesheet_tag="BBBB")
        self.assertTrue(result is not None)
        (run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,\
         sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp) = \
             get_pre_demultiplexing_data(demult_id=1)
        self.assertEqual(run_name,"AAAA")
        self.assertTrue("plot1" in flowcell_cluster_plot)
        self.assertEqual(flowcell_cluster_plot.get("plot1"), "data1")

if __name__ == '__main__':
  unittest.main()