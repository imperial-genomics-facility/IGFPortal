import unittest, json
from app.models import RawAnalysis
from app.models import RawAnalysisValidationSchema
from app.models import RawAnalysis
from app.models import Sample
from app.models import Experiment
from app.models import Run
from app.models import File
from app.models import Collection
from app.models import Collection_group
from app.models import Seqrun
from app.models import Platform
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

def test_project_query(db):
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
    assert len(projects) == 2
    assert 'test2' in [p.project_igf_id for p in projects]
    assert 'test3' not in [p.project_igf_id for p in projects]


def test_pipeline_query(db):
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
    assert len(pipelines) == 1
    assert 'dag_pipeline2' in [p.pipeline_name for p in pipelines]
    assert 'pipeline1' not in [p.pipeline_name for p in pipelines]


def test_get_project_id_for_samples(db):
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
    assert len(project_list) == 1


def test_get_file_collection_for_samples(db):
    project1 = \
        Project(
            project_igf_id='project1')
    sample1 = \
        Sample(
            sample_igf_id='sample1',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='sample2',
            project=project1)
    experiment1 = \
        Experiment(
            experiment_igf_id='experiment1',
            platform_name="NEXTSEQ2000",
            status='ACTIVE',
            library_name="sample1",
            project=project1,
            sample=sample1)
    platform1 = \
        Platform(
            platform_igf_id="platform1",
            model_name="NEXTSEQ2000",
            vendor_name='ILLUMINA',
            software_name="RTA",
            software_version="x.y.z")
    seqrun1 = \
        Seqrun(
            seqrun_igf_id="seqrun1",
            flowcell_id="XXX",
            platform=platform1)
    run1 = \
        Run(
            run_igf_id="run1",
            experiment=experiment1,
            seqrun=seqrun1,
            status='ACTIVE',
            lane_number='1')
    collection1 = \
        Collection(
            name="run1",
            type="demultiplexed_fastq")
    file1 = \
        File(
            file_path="/path/file1",
            status='ACTIVE')
    collection_group1 = \
        Collection_group(
            collection=collection1,
            file=file1)
    try:
        db.session.add(project1)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(experiment1)
        db.session.add(platform1)
        db.session.add(seqrun1)
        db.session.add(run1)
        db.session.add(collection1)
        db.session.add(file1)
        db.session.add(collection_group1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    sample_with_files = \
        _get_file_collection_for_samples(
            sample_igf_id_list=['sample1', 'sample2'])
    assert len(sample_with_files) == 1

def test_get_validation_status_for_analysis_design():
    schema_file = 'app/raw_analysis/analysis_validation_nfcore.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    design_1 = """
    sample_metadata:
        IGF111: ""
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_1,
            validation_schema=schema_data)
    print(error_list)
    assert len(error_list) == 0

    # def test_get_sample_metadata_checks_for_analsis(self):
    #     pass