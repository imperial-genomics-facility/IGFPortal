import os
import time
import logging
from flask import request
from typing import Any
from app import (
    db,
    celery
)
from sqlalchemy import (
    select,
    func,
    desc
)
from app.models import (
    Project,
    Sample,
    Experiment,
    Run,
    Run_attribute
)
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
from flask_appbuilder.baseviews import expose
from flask_appbuilder.security.decorators import has_access

log = logging.getLogger(__name__)

DAG_TAG = 'rehydrate_metadata_dag'

PAGE_SIZE = 100

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
                    args=[airflow_dag_id, project_id_list]
                )
            )
        return project_id_list
    except Exception as e:
        raise ValueError(
            f"Failed to fetch metadata, error: {e}"
        )

def get_sample_for_project(
    project_id: int,
    offset: int,
    per_page: int
) -> Any:
    try:
        results = (
            db.session.query(
                Project.project_igf_id,
                Sample.sample_igf_id,
                Sample.sample_submitter_id,
                func.format(
                    func.coalesce(func.sum(Run_attribute.attribute_value), 0), 0
                ).label("total_read_count")
            )
            .join(Sample, Project.project_id == Sample.project_id)
            .outerjoin(Experiment, Sample.sample_id == Experiment.sample_id)
            .outerjoin(Run, Experiment.experiment_id == Run.experiment_id)
            .outerjoin(
                Run_attribute,
                (Run_attribute.run_id == Run.run_id) &
                (Run_attribute.attribute_name == "R1_READ_COUNT")
            )
            .filter(
                Project.project_id == project_id,
                Sample.sample_igf_id.isnot(None)
            )
            .group_by(Sample.sample_igf_id)
            .order_by(
                desc(
                    Sample.sample_igf_id
                )
            )
            .offset(offset)
            .limit(per_page)
            .all()
        )
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get sample records, error: {e}"
        )


class RehydrateProjectMetadataView(ModelView):
    datamodel = SQLAInterface(Project)
    list_columns = [
        "project_igf_id",
        "project_data",
        "start_timestamp"
    ]
    label_columns = {
        "project_igf_id": "Project name",
        "project_data": "Samples",
        "start_timestamp": "Date"
    }
    base_permissions = [
        "can_list",
        "can_get_samples_for_project"
    ]
    base_filters = [
        ["deliverable", FilterInFunction, lambda: ["FASTQ", "ALIGNMENT", "ANALYSIS"]],
        ["status", FilterInFunction, lambda: ["ACTIVE"]]
    ]
    base_order = ("project_id", "desc")

    @expose('/project_samples/<int:project_id>')
    @has_access
    def get_samples_for_project(self, project_id):
        try:
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", PAGE_SIZE, type=int)
            offset = (page - 1) * per_page
            count_stmt = select(func.count()).select_from(
                select(Sample.sample_igf_id)
                .filter(
                    Sample.project_id == project_id,
                    Sample.sample_igf_id.isnot(None)
                )
                .subquery()
            )
            total = db.session.execute(count_stmt).scalar()
            total_pages = max(1, (total + per_page - 1) // per_page)
            rows = get_sample_for_project(
                project_id=project_id,
                per_page=per_page,
                offset=offset
            )
            return self.render_template(
                "project_sample_view.html",
                rows=rows,
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            )
        except Exception as e:
            log.error(e)
            flash("Failed to fetch samples", 'danger')
            return redirect(
                url_for('RehydrateProjectMetadataView.list')
            )

    @action(
        "fetch_metadata",
        "Fetch metadata",
        confirmation="Run?",
        multiple=True,
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