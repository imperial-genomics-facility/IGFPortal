import os
import tempfile
import pandas as pd
from app.models import SampleSheetModel, Project, Sample
from app.samplesheet.samplesheet_util import SampleSheet
from app.samplesheet.samplesheet_util import update_samplesheet_validation_entry_in_db
from app.samplesheet.samplesheet_util import validate_samplesheet_data_and_update_db
from app.samplesheet.samplesheet_util import compare_sample_with_metadata_db



def test_validate_samplesheet_data1():
    sa = SampleSheet(infile="data/SampleSheet_v1.csv")
    assert len(sa._data) == 8
    errors = sa.validate_samplesheet_data()
    assert len(errors) == 10
    assert len([e for e in errors if "s4" in e]) == 1
    assert len([e for e in errors if "IGF0001" in e]) == 1
    assert len([e for e in errors if "TCCGGAGA, GTCAGTAC" in e]) == 1

def test_validate_samplesheet_data2():
    sa = SampleSheet(infile="data/SampleSheet_v2.csv")
    assert len(sa._data) == 16
    errors = sa.validate_samplesheet_data()
    assert len(errors) == 2



def test_update_samplesheet_validation_entry_in_db(db):
    samplesheet = SampleSheetModel(
        samplesheet_tag='test1',
        csv_data='data'
    )
    try:
        db.session.add(samplesheet)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    entry = (
        db.session
        .query(SampleSheetModel)
        .filter(SampleSheetModel.samplesheet_tag=='test1')
        .one_or_none()
    )
    assert entry is not None
    assert entry.status == 'UNKNOWN'
    entry = (
        db.session
        .query(SampleSheetModel)
        .filter(SampleSheetModel.samplesheet_tag=='test2')
        .one_or_none()
    )
    assert entry is None
    update_samplesheet_validation_entry_in_db(
        samplesheet_tag='test1',
        report='FAILED',
        status='failed'
    )
    entry = (
        db.session
        .query(SampleSheetModel)
        .filter(SampleSheetModel.samplesheet_tag=='test1')
        .one_or_none()
    )
    assert entry is not None
    assert entry.status == 'FAILED'
    assert entry.report == 'FAILED'
    update_samplesheet_validation_entry_in_db(
        samplesheet_tag='test1',
        report='PASS',
        status='pass'
    )
    entry = (
        db.session
        .query(SampleSheetModel)
        .filter(SampleSheetModel.samplesheet_tag=='test1')
        .one_or_none()
    )
    assert entry is not None
    assert entry.status == 'PASS'
    assert entry.report == 'PASS'

def test_get_samplesheet_with_reverse_complement_index():
    sa = SampleSheet(infile="data/SampleSheet_v1.csv")
    sa._data_header = [
        "Sample_ID",
        "Sample_Name",
        "Sample_Plate",
        "Sample_Well",
        "I7_Index_ID",
        "index",
        "I5_Index_ID",
        "index2",
        "Sample_Project",
        "Description"]
    sa._data = [{
        "Sample_ID": "IGF0001",
        "Sample_Name": "IGF0001",
        "Sample_Plate": "",
        "Sample_Well": "",
        "I7_Index_ID": "",
        "index": "AAAAAA",
        "I5_Index_ID": "",
        "index2": "TTTTTA",
        "Sample_Project": "IGFQ_project_1",
        "Description": ""
    },{
        "Sample_ID": "IGF0002",
        "Sample_Name": "IGF0002",
        "Sample_Plate": "",
        "Sample_Well": "",
        "I7_Index_ID": "",
        "index": "AAAAAAAA",
        "I5_Index_ID": "",
        "index2": "",
        "Sample_Project": "IGFQ_project_1",
        "Description": ""
    },{
        "Sample_ID": "IGF0003",
        "Sample_Name": "IGF0003",
        "Sample_Plate": "",
        "Sample_Well": "",
        "I7_Index_ID": "",
        "index": "SI-NN-A10",
        "I5_Index_ID": "",
        "index2": "",
        "Sample_Project": "IGFQ_project_1",
        "Description": "10X"
    }]
    i5_rc_data = (
        sa.get_samplesheet_with_reverse_complement_index()
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
        with open(csv_file, 'w') as fp:
            fp.write(i5_rc_data)
        sa = SampleSheet(infile=csv_file)
        df = pd.DataFrame(sa._data)
        assert df[df['Sample_ID']=="IGF0001"]['index'].values.tolist()[0] == 'AAAAAA'
        assert df[df['Sample_ID']=="IGF0001"]['index2'].values.tolist()[0] == 'TAAAAA'
        assert df[df['Sample_ID']=="IGF0002"]['index'].values.tolist()[0] == 'AAAAAAAA'
        assert df[df['Sample_ID']=="IGF0002"]['index2'].values.tolist()[0] == ''
        assert df[df['Sample_ID']=="IGF0003"]['index'].values.tolist()[0] == 'SI-NN-A10'

def test_samplesheet_v2():
    sa = SampleSheet(infile="data/SampleSheet_v1.csv")
    assert sa._samplesheet_version == 'v1'
    v2_data = sa.get_v2_samplesheet_data()
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
        with open(csv_file, 'w') as fp:
            fp.write(v2_data)
        sa = SampleSheet(infile=csv_file)
        assert sa._samplesheet_version == 'v2'
        sa = SampleSheet(infile="data/SampleSheet_v2.csv")
        assert sa._samplesheet_version == 'v2'
        v2_data = sa.get_v2_samplesheet_data()
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
        with open(csv_file, 'w') as fp:
            fp.write(v2_data)
        sa = SampleSheet(infile=csv_file)
        assert sa._samplesheet_version == 'v2'


def test_validate_samplesheet_data_and_update_db(db):
    with open("data/SampleSheet_v1.csv", 'r') as fp:
        csv_data = fp.readlines()
        csv_data = '\n'.join(csv_data)
    samplesheet = SampleSheetModel(
        samplesheet_tag='test1',
        csv_data=csv_data
    )
    try:
        db.session.add(samplesheet)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    validate_samplesheet_data_and_update_db(
        samplesheet_id=1,
        check_metadata=False)
    entry = (
        db.session
        .query(SampleSheetModel)
        .filter(SampleSheetModel.samplesheet_tag=='test1')
        .one_or_none()
    )
    assert entry is not None
    assert entry.status == 'FAILED'

def test_compare_sample_with_metadata_db(db):
    samplesheet_file = "data/SampleSheet_v3.csv"
    project1 = Project(
        project_id=1,
        project_igf_id="test1"
    )
    project2 = Project(
        project_id=2,
        project_igf_id="test2"
    )
    sample1 = Sample(
        sample_id=1,
        sample_igf_id='test_sample1',
        project_id=1
    )
    sample2 = Sample(
        sample_id=2,
        sample_igf_id='test_sample2',
        project_id=2
    )
    try:
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(sample1)
        db.session.add(sample2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    metadata_errors = compare_sample_with_metadata_db(
        samplesheet_file=samplesheet_file)
    assert 'Missing metadata for sample test_sample3' in metadata_errors
    assert "Sample test_sample2 is linked to project test2, not test1" in metadata_errors

