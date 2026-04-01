import os
import re
import time
import logging
from flask_appbuilder import ModelView
from app.models import RawExternalSeqrun, Platform
from flask import redirect, flash, url_for
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask_appbuilder.models.sqla.interface import SQLAInterface
from app import db
from app import celery
from app.airflow.airflow_api_utils import trigger_airflow_pipeline
from app.airflow.airflow_api_utils import get_airflow_dag_id


DAG_TAG = 'register_external_seqrun_dag'

log = logging.getLogger(__name__)

@celery.task(bind=True)
def async_trigger_airflow_pipeline(
    self,
    dag_id,
    run_list
) -> dict:
    try:
        results = list()
        run_id_list = list()
        for run_id in run_list:
            run_id_list.append(
                run_id
            )
            res = trigger_airflow_pipeline(
                dag_id=dag_id,
                conf_data={'external_seqrun_id': run_id},
                airflow_conf_file=os.environ['AIRFLOW_CONF_FILE']
            )
            time.sleep(2)
            results.append(res.status_code)
        return dict(zip(run_id_list, results))
    except Exception as e:
        raise ValueError(
            f"Failed to run celery job, error: {e}"
        )


def action_reject_raw_external_seqrun(
    item: RawExternalSeqrun|list[RawExternalSeqrun],
    reject_tag: str = 'REJECTED') -> None:
    try:
        if isinstance(item, list):
            try:
                for i in item:
                    (
                        db.session
                        .query(RawExternalSeqrun)
                        .filter(
                            RawExternalSeqrun.raw_external_seqrun_id==i.raw_external_seqrun_id
                        )
                        .update({'status': reject_tag})
                    )
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        else:
            try:
                (
                    db.session
                    .query(RawExternalSeqrun)
                    .filter(
                        RawExternalSeqrun.raw_external_seqrun_id==item.raw_external_seqrun_id
                    )
                    .update({'status': reject_tag})
                )
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
    except Exception as e:
        raise ValueError(
            f"Failed to reject raw external seqrun, error: {e}"
        )


def _extract_platform_name_from_seqrun_id(
    seqrun_name: str
) -> str|None:
    """
    Function to extract platform name from seqrun_name
    """
    try:
        seqrun_pattern = re.compile(
            r"\d+_(\w+)_\d+_\w+"
        )
        match = re.match(seqrun_pattern, seqrun_name)
        if not match:
            return None
        platform_name = match.group(1)
        return platform_name
    except Exception as e:
        raise ValueError(
            f"Failed to extract platform name for seqrun {seqrun_name}," +
            f" error: {e}"
        )

def _check_registered_seqrun_platform(
    platform_name: str
) -> bool:
    try:
        platform_records = (
            db.session
            .query(Platform.platform_igf_id)
            .filter(Platform.platform_igf_id==platform_name)
            .all()
        )
        if platform_records:
            return True
        else:
            return False
    except Exception as e:
        raise ValueError(
            f"Failed to check platform, error {e}"
        )


def action_add_raw_external_seqrun(
    item: RawExternalSeqrun|list[RawExternalSeqrun],
) -> list:
    try:
        airflow_dag_id = get_airflow_dag_id(
            airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
            dag_tag=DAG_TAG
        )
        if airflow_dag_id is None:
            raise ValueError(
                f"Failed to get airflow dag id for {DAG_TAG}"
            )
        errors = list()
        run_list = list()
        if isinstance(item, list):
            for i in item:
                platform_name = _extract_platform_name_from_seqrun_id(
                    seqrun_name=i.raw_external_seqrun_igf_id
                )
                if platform_name is None:
                    errors.append(
                        f'Unknown run id {i.raw_external_seqrun_igf_id}'
                    )
                    continue
                registered_platform = _check_registered_seqrun_platform(
                    platform_name=platform_name
                )
                if not registered_platform:
                    errors.append(
                        f'Unknown platform {platform_name}'
                    )
                    continue
                run_list.append(i.raw_external_seqrun_igf_id)
        elif isinstance(item, RawExternalSeqrun):
            platform_name = _extract_platform_name_from_seqrun_id(
                seqrun_name=item.raw_external_seqrun_igf_id
            )
            if platform_name is None:
                errors.append(
                    f'Unknown run id {item.raw_external_seqrun_igf_id}'
                )
                return run_list, errors
            registered_platform = _check_registered_seqrun_platform(
                platform_name=platform_name
            )
            if not registered_platform:
                errors.append(
                    f'Unknown platform {platform_name}'
                )
                return run_list, errors
            run_list.append(
                item.raw_external_seqrun_igf_id
            )
        else:
            raise TypeError(
                f"Wrong data type, {type}"
            )
        if len(run_list) > 0:
            _ = (
                async_trigger_airflow_pipeline
                .apply_async(args=[airflow_dag_id, run_list])
            )
        return run_list, errors
    except Exception as e:
        raise ValueError(
            f"Failed to add raw seqrun, error: {e}"
        )


class RawExternalSeqrunView(ModelView):
    datamodel = SQLAInterface(RawExternalSeqrun)
    list_columns = [
        "raw_external_seqrun_igf_id",
        "status",
        "date_stamp"
    ]
    label_columns = {
        "raw_external_seqrun_igf_id": "Run id",
        "status": "Status",
        "date_stamp": "Date"
    }
    add_columns = [
        "raw_external_seqrun_igf_id"
    ]
    edit_columns = [
        "raw_external_seqrun_igf_id"
    ]
    base_permissions = [
        "can_add",
        "can_list",
        "can_edit"
    ]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "CHECKING"]]]
    base_order = ("raw_external_seqrun_igf_id", "desc")

    @action(
        "reject_raw_seqrun",
        "Reject run",
        confirmation="Reject?",
        multiple=False,
        single=True,
        icon="fa-exclamation"
    )
    def reject_raw_external_seqrun(self, item):
        try:
            action_reject_raw_external_seqrun(item)
            return redirect(url_for('RawAnalysisV2View.list'))
        except Exception as e:
            log.error(e)
            flash(
                'Failed to reject analysis design',
                'danger')
            return redirect(url_for('RawAnalysisV2View.list'))

    @action(
        "add_raw_seqrun",
        "Add external run",
        confirmation="Add?",
        multiple=True,
        single=False,
        icon="fa-exclamation"
    )
    def add_raw_external_seqrun(self, item):
        try:
            run_list, errors = action_add_raw_external_seqrun(
                item=item
            )
            if len(errors) > 0:
                log.error(errors)
                flash(f"Errors: {', '.join(errors)}", "danger")
            if len(run_list) > 0:
                flash(f"Registering run {', '.join(run_list)}", "info")
            self.update_redirect()
            return redirect(url_for('RawExternalSeqrunView.list'))
        except Exception as e:
            log.error(e)
            flash("Failed to register external runs", "danger")
            return redirect(url_for('RawExternalSeqrunView.list'))