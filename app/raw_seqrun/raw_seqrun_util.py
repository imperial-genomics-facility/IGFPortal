import typing
import logging
from typing import Tuple, Any
from .. import db
from ..models import RawSeqrun, SampleSheetModel

def fetch_samplesheet_for_seqrun(seqrun_id: str) -> Any:
    try:
        result = \
            db.session.\
                query(
                    SampleSheetModel.samplesheet_tag,
                    SampleSheetModel.csv_data).\
                join(RawSeqrun, RawSeqrun.samplesheet_id==SampleSheetModel.samplesheet_id).\
                filter(RawSeqrun.raw_seqrun_igf_id==seqrun_id).\
                filter(SampleSheetModel.status=='PASS').\
                filter(SampleSheetModel.validation_time >= SampleSheetModel.update_time).\
                one_or_none()
        return result
    except Exception as e:
        raise ValueError("Failed to fetch samplesheet for seqrun, error: {0}".format(e))

def check_and_filter_raw_seqruns_after_checking_samplesheet(
    raw_seqrun_igf_ids: list) -> \
        Tuple[list, list]:
    try:
        id_list = list()
        run_list = list()
        results = \
            db.session.\
                query(
                    RawSeqrun.raw_seqrun_id,
                    RawSeqrun.raw_seqrun_igf_id,
                    RawSeqrun.override_cycles).\
                join(SampleSheetModel, SampleSheetModel.samplesheet_id==RawSeqrun.samplesheet_id).\
                filter(SampleSheetModel.status=='PASS').\
                filter(SampleSheetModel.validation_time >= SampleSheetModel.update_time).\
                filter(RawSeqrun.raw_seqrun_igf_id.in_(raw_seqrun_igf_ids)).\
                all()
        id_list = [
            i[0] if isinstance(i, tuple) else i
                for i in results]
        run_list = [
            i[1] if isinstance(i, tuple) else i
                for i in results]
        return id_list, run_list
    except Exception as e:
        raise ValueError("Failed to filter seqruns, error: {0}".format(e))

def change_raw_run_status(
    run_list: list,
    status: str) -> None:
    try:
        db.session.\
            query(RawSeqrun).\
            filter(RawSeqrun.raw_seqrun_igf_id.in_(run_list)).\
            update({'status': status}, synchronize_session='fetch')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError("Failed to change raw run status, error: {0}".format(e))

