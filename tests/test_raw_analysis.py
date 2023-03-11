import unittest, json
from app import appbuilder, db
from app.models import RawAnalysis
from app.models import RawAnalysisValidationSchema
from app.models import RawAnalysis
from app.models import Sample
from app.models import Experiment
from app.models import Run
from app.models import File
from app.models import Collection
from app.models import Collection_group
from app.models import Project
from app.models import Pipeline
from app.models import RawAnalysisValidationSchema
from app.raw_analysis.raw_analysis_util import pipeline_query
from app.raw_analysis.raw_analysis_util import project_query
from app.raw_analysis.raw_analysis_util import validate_json_schema
from app.raw_analysis.raw_analysis_util import validate_analysis_design
from app.raw_analysis.raw_analysis_util import _get_validation_status_for_analysis_design
from app.raw_analysis.raw_analysis_util import _get_project_id_for_samples
from app.raw_analysis.raw_analysis_util import _get_file_collection_for_samples
from app.raw_analysis.raw_analysis_util import _get_sample_metadata_checks_for_analsis

class TestRawAnalysisUtil(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_project_query(self):
        project1 = \
            Project(
                project_id=1,
                project_igf_id="test1")
        project2 = \
            Project(
                project_id=2,
                project_igf_id="test2")
        try:
            db.session.add(project1)
            db.session.flush()
            db.session.add(project2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        projects = project_query()
        self.assertEqual(len(projects), 2)
        self.assertTrue('test2' in [p.project_igf_id for p in projects])
        self.assertTrue('test3' not in [p.project_igf_id for p in projects])

    def test_pipeline_query(self):
        pipeline1 = \
            Pipeline(
                pipeline_name='pipeline1',
                pipeline_db='test1')
        pipeline2 = \
            Pipeline(
                pipeline_name='dag_pipeline2',
                pipeline_db='test2',
                pipeline_type='AIRFLOW')
        try:
            db.session.add(pipeline1)
            db.session.flush()
            db.session.add(pipeline2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        pipelines = pipeline_query()
        self.assertEqual(len(pipelines), 1)
        self.assertTrue('dag_pipeline2' in [p.pipeline_name for p in pipelines])
        self.assertTrue('pipeline1' not in [p.pipeline_name for p in pipelines])

    def test_get_project_id_for_samples(self):
        project1 = \
            Project(project_igf_id='project1')
        project2 = \
            Project(project_igf_id='project2')
        sample1 = \
            Sample(
                sample_igf_id='sample1',
                project_id=1)
        sample2 = \
            Sample(
                sample_igf_id='sample2',
                project_id=1)
        try:
            db.session.add(project1)
            db.session.flush()
            db.session.add(project1)
            db.session.flush()
            db.session.add(sample1)
            db.session.flush()
            db.session.add(sample2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        project_list = \
            _get_project_id_for_samples(
            ['sample1', 'sample2'])
        self.assertEqual(len(project_list), 1)

    def test_get_file_collection_for_samples(self):
        pass

    def test_get_file_collection_for_samples(self):
        pass

    def test_get_sample_metadata_checks_for_analsis(self):
        pass


if __name__ == '__main__':
  unittest.main()