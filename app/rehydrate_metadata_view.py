import os
import time
import logging
from app import (
    celery
)
from app.models import Project
from flask_appbuilder import ModelView
from flask import (
    redirect,
    flash,
    url_for
)
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask_appbuilder.models.sqla.interface import SQLAInterface
from app.airflow.airflow_api_utils import (
    trigger_airflow_pipeline,
    get_airflow_dag_id
)

log = logging.getLogger(__name__)

DAG_TAG = 'rehydrate_metadata_dag'

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
                conf_data={'project_id': run_id},
                airflow_conf_file=os.environ['AIRFLOW_CONF_FILE']
            )
            time.sleep(2)
            results.append(res.status_code)
        return dict(zip(run_id_list, results))
    except Exception as e:
        raise ValueError(
            f"Failed to run celery job, error: {e}"
        )


def action_fetch_metadata(
    item: Project|list[Project]
) -> list:
    try:
        project_id_list = list()
        airflow_dag_id = get_airflow_dag_id(
            airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
            dag_tag=DAG_TAG
        )
        if isinstance(item, list):
            for i in item:
                if i.deliverable != 'COSMX':
                    project_id_list.append(
                        i.project_id
                    )
        else:
            if item.deliverable != 'COSMX':
                project_id_list.append(
                    item.project_id
                )
        if len(project_id_list) > 0:
            _ = (
                async_trigger_airflow_pipeline
                .apply_async(
                    args=[airflow_dag_id, project_id_list, True]
                )
            )
        return project_id_list
    except Exception as e:
        raise ValueError(
            f"Failed to fetch metadata, error: {e}"
        )


class RehydrateProjectMetadataView(ModelView):
    datamodel = SQLAInterface(Project)
    list_columns = [
        "project_igf_id"
    ]
    label_columns = {
        "project_igf_id": "Project name"
    }
    base_permissions = [
        "can_list"
    ]
    base_filters = [
        ["deliverable", FilterInFunction, lambda: ["FASTQ", "ALIGNMENT", "ANALYSIS"]]
    ]
    base_order = ("project_id", "desc")

    @action(
        "fetch_metadata",
        "Fetch metadata",
        confirmation="Run?",
        multiple=False,
        icon="fa-plane"
    )
    def fetch_metadata(self, item):
        try:
            action_fetch_metadata(item)
            self.update_redirect()
            return redirect(
                url_for('RehydrateProjectMetadataView.list')
            )
        except Exception as e:
            log.error(e)
            flash(
                "Failed to fetch metadata",
                "danger"
            )
            return redirect(
                url_for('RehydrateProjectMetadataView.list')
            )