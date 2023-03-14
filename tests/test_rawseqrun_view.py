import os
import requests
from unittest.mock import MagicMock
from unittest.mock import patch
from datetime import datetime
from app.raw_seqrun_view import samplesheet_query
from app.models import RawSeqrun, SampleSheetModel
from app.raw_seqrun_view import update_trigger_date_for_seqrun
from app.raw_seqrun_view import async_trigger_airflow_pipeline

def test_samplesheet_query(db):
        samplesheets = samplesheet_query()
        assert len(samplesheets) == 0
        try:
            sa1 = \
                SampleSheetModel(
                    samplesheet_tag='test1',
                    csv_data='test data',
                    status='PASS',
                    validation_time=datetime.now(),
                    update_time=datetime.now())
            db.session.add(sa1)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        samplesheets = samplesheet_query()
        assert len(samplesheets) == 1
        assert samplesheets[0].samplesheet_tag == 'test1'
        assert samplesheets[0].status == 'PASS'


def test_update_trigger_date_for_seqrun(db):
        try:
            seqrun = \
                RawSeqrun(raw_seqrun_igf_id='seqrun2')
            db.session.add(seqrun)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        seqrun = \
            db.session.\
                query(RawSeqrun).\
                filter(RawSeqrun.raw_seqrun_igf_id=='seqrun2').\
                one_or_none()
        assert seqrun.raw_seqrun_igf_id == 'seqrun2'
        assert seqrun.trigger_time is None
        update_trigger_date_for_seqrun(seqrun_id='seqrun2')
        seqrun = \
            db.session.\
                query(RawSeqrun).\
                filter(RawSeqrun.raw_seqrun_igf_id=='seqrun2').\
                one_or_none()
        assert seqrun.raw_seqrun_igf_id == 'seqrun2'
        assert seqrun.trigger_time is not None

@patch('app.raw_seqrun_view.trigger_airflow_pipeline', return_value=requests.patch('https://httpbin.org/patch', data ={'key': 'value'}, headers={'Content-Type': 'application/json'}))
def test_async_trigger_airflow_pipeline(mock_object, db):
        try:
            seqrun = \
                RawSeqrun(raw_seqrun_igf_id='seqrun1')
            db.session.add(seqrun)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        os.environ['AIRFLOW_CONF_FILE'] = '/tmp/'
        result = async_trigger_airflow_pipeline('test_dag', [{'seqrun_id':'seqrun1'}], True)
        assert 'seqrun1' in result
