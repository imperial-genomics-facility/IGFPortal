import logging
import os
from app import db
from .models import Analysis
from .models import Pipeline_seed
from .models import Pipeline
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from flask_appbuilder import ModelView
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import celery

log = logging.getLogger(__name__)

def get_analysis_pipeline_seed_status(analysis_id: int) -> str:
    try:
        result = \
            db.session.\
                query(
                    Analysis.analysis_name,
                    Pipeline.pipeline_name,
                    Pipeline_seed.status).\
                join(Pipeline, Pipeline.pipeline_name==Analysis.analysis_type).\
                join(Pipeline_seed, Pipeline_seed.seed_id==Analysis.analysis_id).\
                filter(Pipeline_seed.pipeline_id==Pipeline.pipeline_id).\
                filter(Pipeline_seed.seed_table=='analysis').\
                filter(Pipeline_seed.status=='SEEDED').\
                filter(Pipeline.pipeline_type=='AIRFLOW').\
                filter(Analysis.analysis_id==analysis_id).\
                one_or_none()
        if result is None:
            return 'INVALID'
        else:
            return 'VALID'
    except Exception as e:
        log.error(e)
        raise ValueError(
            f"Failed to get analysis pipeline seed status, error: {e}")


@celery.task(bind=True)
def async_submit_analysis_pipeline(self, id_list):
    try:
        results = list()
        for analysis_id in id_list:
            ## get dag id
            dag_name = \
                db.session.\
                    query(Analysis.analysis_type).\
                    filter(Analysis.analysis_id==analysis_id).\
                    one_or_none()
            if dag_name is not None and \
               isinstance(dag_name, list):
                dag_name = dag_name[0]
            res = \
                trigger_airflow_pipeline(
                    dag_id=dag_name,
                    conf_data={"analysis_id": analysis_id},
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'])
            results.append(res.status_code)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


class AnalysisView(ModelView):
    datamodel = \
        SQLAInterface(Analysis)
    list_columns = [
        "analysis_name",
        "analysis_type",
        "project.project_igf_id"]
    base_permissions = [
        "can_list",
        "can_show"]
    base_order = ("analysis_id", "desc")

    @action("trigger_analysis_pipeline", "Trigger analysis pipeline", confirmation="confirm pipeline run?", icon="fa-rocket")
    def trigger_analysis_pipeline(self, item):
        try:
            id_list = list()
            analysis_list = list()
            if isinstance(item, list):
                id_list = [i.analysis_id for i in item]
                analysis_list = [i.analysis_name for i in item]
            else:
                id_list = [item.analysis_id]
                analysis_list = [item.analysis_name]
            analysis_dict = \
                dict(zip(id_list, analysis_list))
            invalid_id_list = list()
            valid_id_list = list()
            invalid_name_list = list()
            valid_name_list = list()
            for analysis_id in id_list:
                status = \
                    get_analysis_pipeline_seed_status(
                        analysis_id=analysis_id)
                if status == 'VALID':
                    valid_id_list.\
                        append(analysis_id)
                    valid_name_list.\
                        append(analysis_dict.get(analysis_id))
                if status == 'INVALID':
                    invalid_id_list.\
                        append(analysis_id)
                    invalid_name_list.\
                        append(analysis_dict.get(analysis_id))
            if len(valid_name_list) > 0:
                _ = \
                    async_submit_analysis_pipeline.\
                        apply_async(args=[valid_id_list])
                flash(f"Submitted jobs for {', '.join(valid_name_list)}", "info")
            if len(invalid_name_list) > 0:
                flash(f"Skipped old analysis {', '.join(invalid_name_list)}", "danger")
            self.update_redirect()
            return redirect(url_for('AnalysisView.list'))
        except:
            flash('Failed to submit analysis', 'danger')
            return redirect(url_for('AnalysisView.list'))