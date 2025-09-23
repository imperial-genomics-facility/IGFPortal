import os
import json
import asyncio
import pytest
from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2,
    RawProject,
    RawPipeline,
    Project,
    Experiment,
    Platform,
    Run,
    Seqrun,
    Collection,
    Collection_group,
    File,
    Sample)
from app.raw_analysis_view_v2 import (
    RawAnalysisTemplateV2View,
    RawAnalysisSchemaV2View,
    action_validate_json_analysis_schema,
    async_validate_analysis_schema,
    action_download_json_analysis_schema,
    action_reject_raw_analysis,
    action_download_raw_analysis_design,
    action_validate_and_submit_analysis,
    async_validate_analysis_yaml,
    action_download_analysis_template)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query,
    validate_analysis_json_schema,
    _get_validation_status_for_analysis_design,
    _get_project_id_for_samples,
    _get_file_collection_for_samples,
    _get_sample_metadata_checks_for_analysis,
    _get_validation_errors_for_analysis_design,
    validate_analysis_design,
    _fetch_project_igf_id_and_deliverable_for_raw_analysis_id,
    _fetch_all_samples_for_project,
    _fetch_analysis_template_for_raw_analysis_id,
    generate_analysis_template_for_analysis_id)
from unittest.mock import patch


def test_analysis_template_v2(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="test1",
            pipeline_db="test",
            pipeline_type="AIRFLOW")
    template1 = \
        RawAnalysisTemplateV2(
            template_id=1,
            pipeline_id=pipeline1.pipeline_id,
            template_data='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.flush()
        db.session.add(template1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    template = \
        db.session.\
            query(RawAnalysisTemplateV2).\
            filter(RawAnalysisTemplateV2.template_id==1).\
            one_or_none()
    assert template is not None
    assert template.pipeline_id == 1


def test_raw_pipeline_query(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name="dag_test2",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    try:
        db.session.add(pipeline1)
        db.session.flush()
        db.session.add(pipeline2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = raw_pipeline_query()
    assert records is not None
    assert len(records) == 1
    pipeline_ids = [entry.pipeline_id for entry in records]
    assert 1 not in pipeline_ids
    assert 2 in pipeline_ids


def test_raw_project_query(db):
    project1 = \
        RawProject(
            project_id=1,
            project_igf_id="test1",
            deliverable="FASTQ")
    project2 = \
        RawProject(
            project_id=2,
            project_igf_id="test2",
            deliverable="COSMX")
    project3 = \
        RawProject(
            project_id=3,
            project_igf_id="test3",
            status="WITHDRAWN",
            deliverable="FASTQ")
    try:
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(project3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = raw_project_query()
    assert records is not None
    assert len(records) == 2
    project_ids = [entry.project_id for entry in records]
    assert 3 not in project_ids
    assert 2 in project_ids

def test_validate_analysis_json_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name="dag_test2",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    status = \
        validate_analysis_json_schema(
            raw_analysis_schema_id=pipeline1.pipeline_id)
    assert status == 'VALIDATED'
    status = \
        validate_analysis_json_schema(
            raw_analysis_schema_id=pipeline2.pipeline_id)
    assert status == 'FAILED'


def test_async_validate_analysis_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name="dag_test2",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    results = \
        async_validate_analysis_schema(
            id_list=[schema1.raw_analysis_schema_id])
    assert len(results) == 1
    assert schema1.raw_analysis_schema_id in results
    assert results.get(schema1.raw_analysis_schema_id) == 'VALIDATED'
    results = \
        async_validate_analysis_schema(
            id_list=[schema2.raw_analysis_schema_id])
    assert len(results) == 1
    assert schema2.raw_analysis_schema_id in results
    assert results.get(schema2.raw_analysis_schema_id) == 'FAILED'


def test_action_validate_json_analysis_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name="dag_test2",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    with patch("app.raw_analysis_view_v2.async_validate_analysis_schema", return_values=["AAA"]):
        pipeline_list, _ = \
            action_validate_json_analysis_schema(
                item=[schema1, schema2])
        assert len(pipeline_list) == 2
        assert pipeline1.pipeline_name in pipeline_list
        assert pipeline2.pipeline_name in pipeline_list
        pipeline_list, _ = \
            action_validate_json_analysis_schema(
                item=schema1)
        assert len(pipeline_list) == 1
        assert pipeline1.pipeline_name in pipeline_list

@pytest.mark.anyio
def test_action_download_json_analysis_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(schema1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    with patch("app.raw_analysis_view_v2.prepare_file_for_download", return_values=["AAA"]):
        _, pipeline_name = \
            action_download_json_analysis_schema(schema1)
    assert pipeline_name == pipeline1.pipeline_name

def test_action_reject_raw_analysis(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    project1 = \
        RawProject(
            project_id=1,
            project_igf_id="Test")
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            project_id=project1.project_id,
            pipeline_id=pipeline1.pipeline_id,
            analysis_name="TestAnalysis1",
            status="VALIDATED",
            analysis_yaml="A: a")
    raw_analysis2 = \
        RawAnalysisV2(
            raw_analysis_id=2,
            project_id=project1.project_id,
            pipeline_id=pipeline1.pipeline_id,
            analysis_name="TestAnalysis2",
            status="VALIDATED",
            analysis_yaml="A: b")
    try:
        db.session.add(pipeline1)
        db.session.add(project1)
        db.session.add(raw_analysis1)
        db.session.add(raw_analysis2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    action_reject_raw_analysis(raw_analysis1)
    raw_analysis = \
        db.session.\
            query(RawAnalysisV2).\
            filter(RawAnalysisV2.raw_analysis_id==raw_analysis1.raw_analysis_id).\
            one_or_none()
    assert raw_analysis.status == "REJECTED"
    raw_analysis = \
        db.session.\
            query(RawAnalysisV2).\
            filter(RawAnalysisV2.raw_analysis_id==raw_analysis2.raw_analysis_id).\
            one_or_none()
    assert raw_analysis.status == "VALIDATED"


def test_action_download_raw_analysis_design(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    project1 = \
        RawProject(
            project_id=1,
            project_igf_id="Test")
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            project_id=project1.project_id,
            pipeline_id=pipeline1.pipeline_id,
            analysis_name="TestAnalysis1",
            status="VALIDATED",
            analysis_yaml="A: a")
    try:
        db.session.add(pipeline1)
        db.session.add(project1)
        db.session.add(raw_analysis1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    with patch("app.raw_analysis_view_v2.prepare_file_for_download", return_values=["AAA"]):
        _, analysis_name = \
            action_download_raw_analysis_design(raw_analysis1)
    assert analysis_name == raw_analysis1.analysis_name

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
    raw_project1 = \
        RawProject(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    raw_project2 = \
        RawProject(
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
        db.session.add(raw_project1)
        db.session.add(raw_project2)
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
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchemaV2(
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
        RawAnalysisV2(
            analysis_name='analysis1',
            project=raw_project1,
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
        RawAnalysisV2(
            analysis_name='analysis2',
            project=raw_project1,
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
        RawAnalysisV2(
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
        RawAnalysisV2(
            analysis_name='analysis4',
            project=raw_project1,
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
        RawAnalysisV2(
            analysis_name='analysis5',
            project=raw_project1,
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
    raw_project1 = \
        RawProject(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    raw_project2 = \
        RawProject(
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
        db.session.add(raw_project1)
        db.session.add(raw_project2)
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
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchemaV2(
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
        RawAnalysisV2(
            analysis_name='analysis1',
            project=raw_project1,
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
        RawAnalysisV2(
            analysis_name='analysis5',
            project=raw_project1,
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

def test_action_validate_and_submit_analysis(db):
    raw_project1 = \
        RawProject(
            project_igf_id='project1')
    raw_pipeline1 = \
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_analysis1 = \
        RawAnalysisV2(
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=raw_pipeline1,
            analysis_yaml='{"A": "B"}')
    try:
        db.session.add(raw_project1)
        db.session.add(raw_pipeline1)
        db.session.add(raw_analysis1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    with patch("app.raw_analysis_view_v2.async_validate_analysis_yaml", return_values={"AAA": "BBB"}):
        analysis_list, _ = \
            action_validate_and_submit_analysis(item=raw_analysis1)
    assert raw_analysis1.analysis_name in analysis_list


def test_async_validate_analysis_yaml(db):
    ## setup metadata
    project1 = \
        Project(
            project_igf_id='project1')
    raw_project1 = \
        RawProject(
            project_igf_id='project1')
    project2 = \
        Project(
            project_igf_id='project2')
    raw_project2 = \
        RawProject(
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
        db.session.add(raw_project1)
        db.session.add(raw_project2)
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
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis_schema1 = \
        RawAnalysisValidationSchemaV2(
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
        RawAnalysisV2(
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=pipeline1,
            analysis_yaml=design_1)
    try:
        db.session.add(raw_analysis1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    ## valid design status
    results = \
        async_validate_analysis_yaml(
            id_list=[raw_analysis1.raw_analysis_id])
    assert raw_analysis1.raw_analysis_id in results
    assert results.get(raw_analysis1.raw_analysis_id) == 'VALIDATED'


def test_fetch_project_igf_id_and_deliverable_for_raw_analysis_id(db):
    raw_project1 = \
        RawProject(
            project_igf_id='project1',
            deliverable="COSMX")
    raw_project2 = \
        RawProject(
            project_igf_id='project2',
            deliverable="FASTQ")
    pipeline1 = \
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=pipeline1,
            status="UNKNOWN",
            analysis_yaml="a: b")
    try:
        db.session.add(raw_project1)
        db.session.add(raw_project2)
        db.session.add(pipeline1)
        db.session.add(raw_analysis1)
        db.session.commit()
    except:
        db.session.rollback()
        raise
    (project_igf_id, deliverable) = \
        _fetch_project_igf_id_and_deliverable_for_raw_analysis_id(
            raw_analysis_id=raw_analysis1.raw_analysis_id)
    assert project_igf_id == raw_project1.project_igf_id
    assert deliverable == raw_project1.deliverable

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

def test_fetch_analysis_template_for_raw_analysis_id(db):
    raw_project1 = \
        RawProject(
            project_igf_id='project1',
            deliverable="COSMX")
    raw_project2 = \
        RawProject(
            project_igf_id='project2',
            deliverable="FASTQ")
    pipeline1 = \
        RawPipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    pipeline2 = \
        RawPipeline(
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=pipeline1,
            status="UNKNOWN",
            analysis_yaml="a: b")
    raw_analysis2 = \
        RawAnalysisV2(
            raw_analysis_id=2,
            analysis_name='analysis2',
            project=raw_project1,
            pipeline=pipeline2,
            status="UNKNOWN",
            analysis_yaml="a: b")
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
        RawAnalysisTemplateV2(
            template_tag="template1",
            template_data=template,
            pipeline=pipeline1)
    try:
        db.session.add(raw_project1)
        db.session.add(raw_project2)
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(raw_analysis1)
        db.session.add(raw_analysis2)
        db.session.add(template1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    template_data = \
        _fetch_analysis_template_for_raw_analysis_id(
            raw_analysis_id=raw_analysis1.raw_analysis_id)
    assert "CONDITION_NAME" in template_data
    template_data = \
        _fetch_analysis_template_for_raw_analysis_id(
            raw_analysis_id=raw_analysis2.raw_analysis_id)
    assert "CONDITION_NAME" not in template_data


def test_generate_analysis_template_for_analysis(db):
    raw_project1 = \
        RawProject(
            project_id=1,
            project_igf_id='project1',
            deliverable="FASTQ")
    raw_project2 = \
        RawProject(
            project_id=2,
            project_igf_id='project2',
            deliverable="COSMX")
    raw_pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=raw_pipeline1,
            status="UNKNOWN",
            analysis_yaml="")
    raw_analysis2 = \
        RawAnalysisV2(
            raw_analysis_id=2,
            analysis_name='analysis2',
            project=raw_project2,
            pipeline=raw_pipeline2,
            status="UNKNOWN",
            analysis_yaml="")
    template_data = \
        """sample_metadata:
        {% for SAMPLE_ID in SAMPLE_ID_LIST %}
        {{ SAMPLE_ID }}:
            condition: CONDITION_NAME
            strandedness: reverse
        {% endfor %}analysis_metadata:
            pipeline_name: xyz
        """
    raw_template1 = \
        RawAnalysisTemplateV2(
            template_data=template_data,
            pipeline=raw_pipeline1)
    project1 = \
        Project(
            project_id=1,
            project_igf_id='project1')
    project2 = \
        Project(
            project_id=2,
            project_igf_id='project2',
            deliverable="COSMX")
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    try:
        db.session.add(raw_project1)
        db.session.add(raw_project2)
        db.session.add(raw_pipeline1)
        db.session.add(raw_pipeline2)
        db.session.add(raw_analysis1)
        db.session.add(raw_analysis2)
        db.session.add(raw_template1)
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    formatted_template = \
        generate_analysis_template_for_analysis_id(
            raw_analysis_id=raw_pipeline1.pipeline_id)
    assert "CONDITION_NAME" in formatted_template
    assert "IGF111:" in formatted_template
    formatted_template = \
        generate_analysis_template_for_analysis_id(
            raw_analysis_id=raw_pipeline2.pipeline_id)
    assert "CONDITION_NAME" not in formatted_template
    assert "IGF111:" not in formatted_template
    assert "sample_metadata:\nanalysis_metadata:" in formatted_template

def test_action_download_analysis_template(db):
    raw_project1 = \
        RawProject(
            project_id=1,
            project_igf_id='project1',
            deliverable="FASTQ")
    raw_project2 = \
        RawProject(
            project_id=2,
            project_igf_id='project2',
            deliverable="COSMX")
    raw_pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    raw_analysis1 = \
        RawAnalysisV2(
            raw_analysis_id=1,
            analysis_name='analysis1',
            project=raw_project1,
            pipeline=raw_pipeline1,
            status="UNKNOWN",
            analysis_yaml="")
    raw_analysis2 = \
        RawAnalysisV2(
            raw_analysis_id=2,
            analysis_name='analysis2',
            project=raw_project2,
            pipeline=raw_pipeline2,
            status="UNKNOWN",
            analysis_yaml="")
    template_data = \
        """sample_metadata:
        {% for SAMPLE_ID in SAMPLE_ID_LIST %}
        {{ SAMPLE_ID }}:
            condition: CONDITION_NAME
            strandedness: reverse
        {% endfor %}analysis_metadata:
            pipeline_name: xyz
        """
    raw_template1 = \
        RawAnalysisTemplateV2(
            template_data=template_data,
            pipeline=raw_pipeline1)
    project1 = \
        Project(
            project_id=1,
            project_igf_id='project1')
    project2 = \
        Project(
            project_id=2,
            project_igf_id='project2',
            deliverable="COSMX")
    sample1 = \
        Sample(
            sample_igf_id='IGF111',
            project=project1)
    sample2 = \
        Sample(
            sample_igf_id='IGF112',
            project=project1)
    try:
        db.session.add(raw_project1)
        db.session.add(raw_project2)
        db.session.add(raw_pipeline1)
        db.session.add(raw_pipeline2)
        db.session.add(raw_analysis1)
        db.session.add(raw_analysis2)
        db.session.add(raw_template1)
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    with patch("app.raw_analysis_view_v2.prepare_file_for_download", return_values=["AAA"]):
        _, analysis_name = \
            action_download_analysis_template(raw_analysis1)
    assert analysis_name == raw_analysis1.analysis_name