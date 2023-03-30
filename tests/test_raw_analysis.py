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
from app.models import RawAnalysisTemplate
from app.raw_analysis.raw_analysis_util import pipeline_query
from app.raw_analysis.raw_analysis_util import project_query
from app.raw_analysis.raw_analysis_util import validate_json_schema
from app.raw_analysis.raw_analysis_util import validate_analysis_design
from app.raw_analysis.raw_analysis_util import _get_validation_status_for_analysis_design
from app.raw_analysis.raw_analysis_util import _get_project_id_for_samples
from app.raw_analysis.raw_analysis_util import _get_file_collection_for_samples
from app.raw_analysis.raw_analysis_util import _get_sample_metadata_checks_for_analysis
from app.raw_analysis.raw_analysis_util import _get_validation_errors_for_analysis_design
from app.raw_analysis.raw_analysis_util import _fetch_all_samples_for_project
from app.raw_analysis.raw_analysis_util import _get_analysis_template
from app.raw_analysis.raw_analysis_util import generate_analysis_template
from app.raw_analysis_view import async_validate_analysis_yaml
from app.raw_analysis_view import async_validate_analysis_schema

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
    assert 'sample1' in sample_with_files

def test_get_validation_status_for_analysis_design():
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    ## valid design
    design_1 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
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
    assert len(error_list) == 0
    ## invalid design
    schema_data_2 = """
    {'sample_metadata'}
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_1,
            validation_schema=schema_data_2)
    assert len(error_list) == 1
    assert 'Failed to load validation schema. Invalid format.' in error_list
    ## invalid design
    design_2 = """
    sample_metadata1:
        sample111: ""
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
            analysis_yaml=design_2,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'sample_metadata' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_3 = """
    sample_metadata:
        sample111: ""
    analysis_metadata:
        NXF_VER1: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_3,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'NXF_VER' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_4 = """
    sample_metadata:
        sample111: ""
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline1: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_4,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'nfcore_pipeline' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_5 = """
    sample_metadata:
        sample111: ""
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq1
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_5,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'nf-core/methylseq1' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_6 = """
    sample_metadata:
        sample111: ""
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params1:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    error_list = \
        _get_validation_status_for_analysis_design(
            analysis_yaml=design_6,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'nextflow_params' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_7 = """
    sample_metadata:
        IGF111:
            condition: aaa
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
            analysis_yaml=design_7,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'aaa' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_8 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: notsure
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
            analysis_yaml=design_8,
            validation_schema=schema_data)
    check_error = False
    for e in error_list:
        if 'notsure' in e:
            check_error = True
    assert check_error

def test_get_sample_metadata_checks_for_analysis(db):
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='sample1',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='sample2',
            project=project1)
    sample3 = \
        Sample(
            sample_igf_id='sample3',
            project=project2)
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
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(sample3)
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
    ## valid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample1': ''},
            project_igf_id='project1')
    assert len(error_list) == 0
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata=['sample1'],
            project_igf_id='project1')
    assert len(error_list) == 1
    assert f'sample_metadata has type {type([])}' in error_list
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={},
            project_igf_id='project1')
    assert len(error_list) == 1
    assert 'No sample ids found in sample_metadata' in error_list
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample2': ''},
            project_igf_id='project1')
    assert len(error_list) == 1
    assert 'No sample has fastq' in error_list
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample1': '', 'sample2': ''},
            project_igf_id='project1')
    assert len(error_list) == 1
    assert "Missing fastq for samples: sample2" in error_list
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample1': ''},
            project_igf_id='project2')
    assert len(error_list) == 1
    assert 'Analysis is linked to project project2 but samples are linked to project project1' in error_list
    ## invalid input
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample1': '', 'sample3': ''},
            project_igf_id='project1')
    assert len(error_list) == 2
    assert "samples are linked to multiple projects: project1, project2" in error_list
    ## missing fastq for partial sample
    error_list = \
        _get_sample_metadata_checks_for_analysis(
            sample_metadata={'sample1': '', 'sample2': ''},
            project_igf_id='project1')
    assert len(error_list) == 1
    assert "Missing fastq for samples: sample2" in error_list



def test_get_validation_errors_for_analysis_design(db):
    ## setup metadata
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    sample3 = \
        Sample(
            sample_igf_id='IGF113',
            project=project2)
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
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(sample3)
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
    ## setup design schema
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchema(
        json_schema=schema_data,
        pipeline=pipeline1,
        status="VALIDATED")
    try:
        db.session.add(pipeline1)
        db.session.add(analysis_schema1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## setup analysis design
    ## valid design
    design_1 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis1 = \
        RawAnalysis(
            analysis_name='analysis1',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_1)
    try:
        db.session.add(raw_analysis1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## valid design errors
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=raw_analysis1.raw_analysis_id)
    assert len(error_list) == 0
    ## invalid design
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=100)
    assert len(error_list) == 1
    assert "No metadata entry found for id 100" in error_list
    ## invalid design
    design_2 = None
    raw_analysis2 = \
        RawAnalysis(
            analysis_name='analysis2',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_2)
    try:
        db.session.add(raw_analysis2)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid design errors
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=raw_analysis2.raw_analysis_id)
    assert len(error_list) == 1
    assert "No analysis design found" in error_list
    ## invalid analysis
    raw_analysis3 = \
        RawAnalysis(
            analysis_name='analysis3',
            analysis_yaml=design_1)
    try:
        db.session.add(raw_analysis3)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid analysis design errors
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=raw_analysis3.raw_analysis_id)
    assert len(error_list) == 3
    assert "No pipeline info found" in error_list
    assert "No project id found" in error_list
    assert "No analysis schema found" in error_list
    ## invalid design
    design_4 = """
    sample_metadata1:
        IGF111:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis4 = \
        RawAnalysis(
            analysis_name='analysis4',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_4)
    try:
        db.session.add(raw_analysis4)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid analysis design errors
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=raw_analysis4.raw_analysis_id)
    assert len(error_list) == 1
    check_error = False
    for e in error_list:
        if 'sample_metadata' in e:
            check_error = True
    assert check_error
    ## invalid design
    design_5 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
        IGF112:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis5 = \
        RawAnalysis(
            analysis_name='analysis5',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_5)
    try:
        db.session.add(raw_analysis5)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid analysis design errors
    error_list = \
        _get_validation_errors_for_analysis_design(
            raw_analysis_id=raw_analysis5.raw_analysis_id)
    assert len(error_list) == 1
    assert "Missing fastq for samples: IGF112" in error_list


def test_validate_analysis_design(db):
    ## setup metadata
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    sample3 = \
        Sample(
            sample_igf_id='IGF113',
            project=project2)
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
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(sample3)
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
    ## setup design schema
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchema(
        json_schema=schema_data,
        pipeline=pipeline1,
        status="VALIDATED")
    try:
        db.session.add(pipeline1)
        db.session.add(analysis_schema1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## setup analysis design
    ## valid design
    design_1 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis1 = \
        RawAnalysis(
            analysis_name='analysis1',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_1)
    try:
        db.session.add(raw_analysis1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## valid design status
    status = \
        validate_analysis_design(
            raw_analysis_id=raw_analysis1.raw_analysis_id)
    assert status == 'VALIDATED'
    ## invalid design
    design_5 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
        IGF112:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis5 = \
        RawAnalysis(
            analysis_name='analysis5',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_5)
    try:
        db.session.add(raw_analysis5)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid analysis design errors
    status = \
        validate_analysis_design(
            raw_analysis_id=raw_analysis5.raw_analysis_id)
    assert status == 'FAILED'


def test_async_validate_analysis_schema(db):
    ## setup metadata
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    sample3 = \
        Sample(
            sample_igf_id='IGF113',
            project=project2)
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
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(sample3)
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
    ## setup design schema
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchema(
        json_schema=schema_data,
        pipeline=pipeline1,
        status="VALIDATED")
    try:
        db.session.add(pipeline1)
        db.session.add(analysis_schema1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## setup analysis design
    ## valid design
    design_1 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis1 = \
        RawAnalysis(
            analysis_name='analysis1',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_1)
    try:
        db.session.add(raw_analysis1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## valid design status
    status_dict = \
        async_validate_analysis_yaml(
            id_list=[raw_analysis1.raw_analysis_id])
    assert len(status_dict) == 1
    assert raw_analysis1.raw_analysis_id in status_dict
    assert status_dict.get(raw_analysis1.raw_analysis_id) == 'VALIDATED'
    ## invalid design
    design_5 = """
    sample_metadata:
        IGF111:
            condition: AAA
            strandedness: reverse
        IGF112:
            condition: AAA
            strandedness: reverse
    analysis_metadata:
        NXF_VER: x.y.z
        nfcore_pipeline: nf-core/methylseq
        nextflow_params:
            - "-profile singularity"
            - "-r a.b.c"
            - "--genome GRCh38"
    """
    raw_analysis5 = \
        RawAnalysis(
            analysis_name='analysis5',
            project=project1,
            pipeline=pipeline1,
            analysis_yaml=design_5)
    try:
        db.session.add(raw_analysis5)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## invalid analysis design errors
    status_dict = \
        async_validate_analysis_yaml(
            id_list=[raw_analysis5.raw_analysis_id])
    assert len(status_dict) == 1
    assert raw_analysis5.raw_analysis_id in status_dict
    assert status_dict.get(raw_analysis5.raw_analysis_id) == 'FAILED'


def test_validate_json_schema(db):
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    schema1 = \
        RawAnalysisValidationSchema(
            pipeline=pipeline1,
            json_schema=schema_data)
    try:
        db.session.add(pipeline1)
        db.session.add(schema1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema1.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'UNKNOWN'
    ## valid design
    validate_json_schema(schema1.raw_analysis_schema_id)
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema1.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'VALIDATED'
    ## invalid schema
    pipeline2 = \
        Pipeline(
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    schema_data = """{'a': 'b'}
    """
    schema2 = \
        RawAnalysisValidationSchema(
            pipeline=pipeline2,
            json_schema=schema_data)
    try:
        db.session.add(pipeline2)
        db.session.add(schema2)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema2.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'UNKNOWN'
    validate_json_schema(schema2.raw_analysis_schema_id)
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema2.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'FAILED'


def test_async_validate_analysis_schema(db):
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    schema_file = 'app/raw_analysis/analysis_validation_nfcore_v1.json'
    with open(schema_file, 'r') as fp:
        schema_data = fp.read()
    schema1 = \
        RawAnalysisValidationSchema(
            pipeline=pipeline1,
            json_schema=schema_data)
    try:
        db.session.add(pipeline1)
        db.session.add(schema1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema1.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'UNKNOWN'
    ## valid design
    status_dict = \
        async_validate_analysis_schema(
            id_list=[schema1.raw_analysis_schema_id])
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema1.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'VALIDATED'
    assert len(status_dict) == 1
    assert schema1.raw_analysis_schema_id in status_dict
    assert status_dict.get(schema1.raw_analysis_schema_id) == 'VALIDATED'
    ## invalid schema
    pipeline2 = \
        Pipeline(
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    schema_data = """{'a': 'b'}
    """
    schema2 = \
        RawAnalysisValidationSchema(
            pipeline=pipeline2,
            json_schema=schema_data)
    try:
        db.session.add(pipeline2)
        db.session.add(schema2)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema2.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'UNKNOWN'
    status_dict = \
        async_validate_analysis_schema(
            id_list=[schema2.raw_analysis_schema_id])
    (status,) = \
        db.session.\
            query(RawAnalysisValidationSchema.status).\
            filter(RawAnalysisValidationSchema.raw_analysis_schema_id==schema2.raw_analysis_schema_id).\
            one_or_none()
    assert status == 'FAILED'
    assert len(status_dict) == 1
    assert schema2.raw_analysis_schema_id in status_dict
    assert status_dict.get(schema2.raw_analysis_schema_id) == 'FAILED'


def test_fetch_all_samples_for_project(db):
    ## setup metadata
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
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
    sample_ids = \
        _fetch_all_samples_for_project(
            project_igf_id='project1')
    assert len(sample_ids) == 2
    assert 'IGF111' in sample_ids
    assert 'IGF112' in sample_ids
    sample_ids = \
        _fetch_all_samples_for_project(
            project_igf_id='project2')
    assert len(sample_ids) == 0

def test_get_analysis_template(db):
    template_data = \
        _get_analysis_template(template_tag='xyz')
    assert template_data is not None
    assert 'condition: CONDITION_NAME' not in [t.strip() for t in template_data.split('\n')]
    template = \
        """sample_metadata:
        {% for SAMPLE_ID in SAMPLE_ID_LIST %}
        {{ SAMPLE_ID }}:
            condition: CONDITION_NAME
            strandedness: reverse
        {% endfor %}analysis_metadata:
            pipeline_name: xyz
        """
    template1 = \
        RawAnalysisTemplate(
            template_tag="template1",
            template_data=template)
    try:
        db.session.add(template1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    template_data = \
        _get_analysis_template(template_tag='template1')
    assert template_data is not None
    assert 'condition: CONDITION_NAME' in [t.strip() for t in template_data.split('\n')]

def test_generate_analysis_template(db):
    ## setup metadata
    template = \
        """sample_metadata:
        {% for SAMPLE_ID in SAMPLE_ID_LIST %}
        {{ SAMPLE_ID }}:
            condition: CONDITION_NAME
            strandedness: reverse
        {% endfor %}analysis_metadata:
            pipeline_name: xyz"""
    project1 = \
        Project(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    template1 = \
        RawAnalysisTemplate(
            template_tag="template1",
            template_data=template)
    try:
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.add(template1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## valid project and template
    formatted_template = \
        generate_analysis_template(
            project_igf_id="project1",
            template_tag="template1")
    assert 'IGF111:' in [line.strip() for line in formatted_template.split('\n')]
    assert 'condition: CONDITION_NAME' in [line.strip() for line in formatted_template.split('\n')]
    ## invalid project valid template
    formatted_template = \
        generate_analysis_template(
            project_igf_id="project2",
            template_tag="template1")
    assert len([line.strip() for line in formatted_template.split('\n')]) == 3
    ## valid project invalid template
    formatted_template = \
        generate_analysis_template(
            project_igf_id="project1",
            template_tag="xxx")
    assert "IGF111: ''" in [line.strip() for line in formatted_template.split('\n')]
    assert 'condition: CONDITION_NAME' not in [line.strip() for line in formatted_template.split('\n')]
    ## invalid project invalid template
    formatted_template = \
        generate_analysis_template(
            project_igf_id="project2",
            template_tag="xyz")
    assert len([line.strip() for line in formatted_template.split('\n')]) == 2