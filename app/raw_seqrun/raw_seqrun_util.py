from typing import (
    Tuple,
    Any,
    Optional)
from app import db
from app.models import (
    RawSeqrun,
    SampleSheetModel)

def check_and_add_new_raw_seqrun(
    seqrun_id_list: list,
    run_config_list: Optional[list] = None
    ) -> bool:
    try:
        for seqrun_list_index, seqrun_id in enumerate(seqrun_id_list):
            seqrun_id = (
                seqrun_id
                .strip()
                .replace(' ', '_')
            )
            result = (
                db.session
                .query(RawSeqrun)
                .filter(RawSeqrun.raw_seqrun_igf_id==seqrun_id)
                .one_or_none()
            )
            if result is None:
                ## try to get run config from the json data or set it to ''
                run_config = None
                if (
                    run_config_list is not None
                    and len(run_config_list)+1 >= seqrun_list_index
                ):
                    run_config = run_config_list[seqrun_list_index]
                if run_config is None:
                    run_config = ''
                (
                    db.session
                    .add(
                        RawSeqrun(
                            raw_seqrun_igf_id=seqrun_id,
                            run_config=run_config)
                        )
                )
                db.session.flush()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(
            f"Failed to check and add new raw seqrun, error: {e}")


def fetch_samplesheet_id_for_seqrun(
    seqrun_id: str
    ) -> Any:
    try:
        result = (
            db.session
            .query(
                RawSeqrun.samplesheet_id
            )
            .filter(
                RawSeqrun.raw_seqrun_igf_id==seqrun_id
            )
            .one_or_none()
        )
        if result is None:
            return None
        else:
            (samplesheet_id, ) = result
            return samplesheet_id
    except Exception as e:
        raise ValueError(
            f"Failed to fetch samplesheet id for seqrun, error: {e}")


def fetch_override_cycle_for_seqrun(
    seqrun_id: str
    ) -> Any:
    try:
        records = (
            db.session
            .query(
                RawSeqrun.override_cycles
            )
            .filter(
                RawSeqrun.raw_seqrun_igf_id==seqrun_id
            )
            .one_or_none()
        )
        if records is None:
            return None
        else:
            (override_cycle, ) = records
            return override_cycle
    except Exception as e:
        raise ValueError(
            f"Failed to fetch override cycle for seqrun, error: {e}")

def fetch_samplesheet_for_seqrun(
    seqrun_id: str
    ) -> Any:
    try:
        result = (
            db.session
            .query(
                SampleSheetModel.samplesheet_tag,
                SampleSheetModel.csv_data
            )
            .join(
                RawSeqrun,
                RawSeqrun.samplesheet_id==SampleSheetModel.samplesheet_id
            )
            .filter(
                RawSeqrun.raw_seqrun_igf_id==seqrun_id
            )
            .filter(
                SampleSheetModel.status=='PASS'
            )
            .filter(
                SampleSheetModel.validation_time >= SampleSheetModel.update_time
            )
            .one_or_none()
        )
        return result
    except Exception as e:
        raise ValueError(
            f"Failed to fetch samplesheet for seqrun, error: {e}")

def check_and_filter_raw_seqruns_after_checking_samplesheet(
    raw_seqrun_igf_ids: list
    ) -> Tuple[list, list]:
    try:
        id_list = list()
        run_list = list()
        results = (
            db.session
            .query(
                RawSeqrun.raw_seqrun_id,
                RawSeqrun.raw_seqrun_igf_id
            )
            .join(
                SampleSheetModel,
                SampleSheetModel.samplesheet_id==RawSeqrun.samplesheet_id
            )
            .filter(
                SampleSheetModel.status=='PASS'
            )
            .filter(
                SampleSheetModel.validation_time >= SampleSheetModel.update_time
            )
            .filter(
                RawSeqrun.raw_seqrun_igf_id.in_(raw_seqrun_igf_ids)
            )
            .all()
        )
        id_list = [
            i[0] if isinstance(i, tuple) else i
            for i in results]
        run_list = [
            i[1] if isinstance(i, tuple) else i
            for i in results]
        return id_list, run_list
    except Exception as e:
        raise ValueError(
            f"Failed to filter seqruns, error: {e}")

def change_raw_run_status(
    run_list: list,
    status: str
    ) -> None:
    try:
        (
            db.session
            .query(RawSeqrun)
            .filter(
                RawSeqrun.raw_seqrun_igf_id.in_(run_list)
            )
            .update({
                'status': status
            },
            synchronize_session='fetch'
            )
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(
            f"Failed to change raw run status, error: {e}")

