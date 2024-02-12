import os
import time
import json
import logging
from . import db
from . import celery
from typing import Any
from .models import ProjectCleanup
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from .airflow.airflow_api_utils import get_airflow_dag_id
from datetime import datetime, timedelta
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface

log = logging.getLogger(__name__)

## TO DO: load DAG names from config file
NOTIFY_USER_DAG_TAG = 'notify_user_about_project_cleanup_dag'
DB_CLEANUP_DAG_TAG = 'cleanup_db_entry_dag_tag'

@celery.task(bind=True)
def async_trigger_airflow_cleanup_pipeline(self, dag_id, entry_list, update_trigger_date=False):
    try:
        results = list()
        run_id_list = list()
        for entry in entry_list:
            run_id_list.\
                append(entry.get('project_cleanup_id'))
            res = \
                trigger_airflow_pipeline(
                    dag_id=dag_id,
                    conf_data=entry,
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'])
            if res is not None and \
               update_trigger_date and \
               res.status_code == 200:
                update_trigger_date_for_cleanup(
                    project_cleanup_id=entry.get('project_cleanup_id'))
            time.sleep(10)
            results.append(res.status_code)
        return dict(zip(run_id_list, results))
    except Exception as e:
        raise ValueError(f"Failed to run celery job, error: {e}")

def update_status_for_project_cleanup(
        project_cleanup_id_list: list[int],
        status: str) -> None:
    try:
        if len(project_cleanup_id_list) == 0:
            raise ValueError("No id found in input list")
        for id in project_cleanup_id_list:
            try:
                db.session.\
                query(ProjectCleanup).\
                filter(ProjectCleanup.project_cleanup_id==id).\
                update({"status": status})
                db.session.commit()
            except:
                db.session.rollback()
                raise
    except Exception as e:
        raise ValueError(f"Failed to change status: {e}")


def parse_and_add_project_cleanup_data(data: Any, cutoff_weeks: int = 16) -> None:
    try:
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, list):
            raise TypeError(
                f"Expecting a list of dicts, got: {type(data)}")
        try:
            for entry in data:
                user_email = entry.get("user_email")
                user_name = entry.get("user_name")
                projects = entry.get("projects")
                if user_email is None or \
                   user_name is None or \
                   projects is None:
                    raise KeyError(f"Missing user email, name or project list")
                pc_data = \
                    ProjectCleanup(
                        user_email=user_email,
                        user_name=user_name,
                        projects=projects,
                        status='NOT_STARTED',
                        deletion_date=datetime.now()+timedelta(weeks=cutoff_weeks))
                db.session.add(pc_data)
                db.session.flush()
                db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError(f"Failed to add new data: {e}")


def update_trigger_date_for_cleanup(project_cleanup_id: int) -> None:
    try:
        try:
            db.session.\
                query(ProjectCleanup).\
                filter(ProjectCleanup.project_cleanup_id==project_cleanup_id).\
                update({"update_date": datetime.now()})
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError(f"Failed to add trigger date, error: {e}")


class ProjectCleanupPendingView(ModelView):
    datamodel = SQLAInterface(ProjectCleanup)
    list_columns = [
        "user_name",
        "user_email",
        "status",
        "deletion_date",
        "update_date"]
    show_columns = [
        "user_name",
        "user_email",
        "projects",
        "status",
        "deletion_date",
        "update_date"]
    add_columns = [
        "user_email",
        "user_name",
        "projects",
        "deletion_date"]
    edit_columns = [
        "user_email",
        "user_name"]
    label_columns = {
        "user_email": "User email",
        "user_name": "User name",
        "projects": "List of Projects",
        "status": "Status",
        "deletion_date": "Deletion date",
        "update_date": "Updated on"}
    base_permissions = [
        "can_list",
        "can_show",
        "can_edit"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["NOT_STARTED", "PROCESSING", "USER_NOTIFIED", "DB_CLEANUP_FINISHED"]]]
    base_order = ("project_cleanup_id", "desc")

    @action("notify_user_about_cleanup", "Notify user about cleanup", confirmation="Confirm?", multiple=True, single=True, icon="fa-exclamation")
    def notify_user_about_cleanup(self, item):
        try:
            entry_list = list()
            failed_list = list()
            if isinstance(item, list):
                for i in item:
                    if i.status == "NOT_STARTED" and \
                       datetime.now() < i.deletion_date:
                        entry_list.append(i.project_cleanup_id)
                    else:
                        failed_list.append(i.project_cleanup_id)
            else:
                if item.status == "NOT_STARTED" and \
                   datetime.now() < item.deletion_date:
                    entry_list.append(item.project_cleanup_id)
                else:
                    failed_list.append(item.project_cleanup_id)
            if len(entry_list) > 0:
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=NOTIFY_USER_DAG_TAG)
                if airflow_dag_id is None:
                    raise ValueError(
                        f"Failed to get airflow dag id for {NOTIFY_USER_DAG_TAG}")
                _ = \
                    async_trigger_airflow_cleanup_pipeline.\
                        apply_async(args=[airflow_dag_id, entry_list, True])
                flash("Submitted notify cleanup task for {0}".format(', '.join(entry_list)), "info")
            if len(failed_list) > 0:
                flash("Failed to sent email to {0}".format(', '.join(failed_list)), "danger")
            self.update_redirect()
            return redirect(url_for('ProjectCleanup.list'))
        except Exception as e:
            log.error(e)
            flash('Failed to mark projects deleted in DB', 'danger')
            return redirect(url_for('ProjectCleanup.list'))

    @action("cleanup_db_entry", "Cleanup DB entry", confirmation="Confirm?", multiple=True, single=True, icon="fa-exclamation")
    def cleanup_db_entry(self, item):
        try:
            entry_list = list()
            failed_list = list()
            if isinstance(item, list):
                for i in item:
                    if i.status == "USER_NOTIFIED" and \
                       datetime.now() >= i.deletion_date:
                        entry_list.append(i.project_cleanup_id)
                    else:
                        failed_list.append(i.project_cleanup_id)
            else:
                if item.status == "USER_NOTIFIED" and \
                   datetime.now() >= item.deletion_date:
                    entry_list.append(item.project_cleanup_id)
                else:
                    failed_list.append(item.project_cleanup_id)
            if len(entry_list) > 0:
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=DB_CLEANUP_DAG_TAG)
                if airflow_dag_id is None:
                    raise ValueError(
                        f"Failed to get airflow dag id for {DB_CLEANUP_DAG_TAG}")
                _ = \
                    async_trigger_airflow_cleanup_pipeline.\
                        apply_async(args=[airflow_dag_id, entry_list, True])
                ## mark entries as PROCESSING to prevent repeat runs
                update_status_for_project_cleanup(
                    project_cleanup_id_list=entry_list,
                    status='PROCESSING')
                flash("Submitted DB cleanup for {0}".format(', '.join(entry_list)), "info")
            if len(failed_list) > 0:
                flash("Failed DB cleanup for user {0}".format(', '.join(failed_list)), "danger")
            self.update_redirect()
            return redirect(url_for('ProjectCleanup.list'))
        except Exception as e:
            log.error(e)
            flash('Failed to mark projects deleted in DB', 'danger')
            return redirect(url_for('ProjectCleanup.list'))


    @action("mark_cleanup_finished", "Mark cleanup finished", confirmation="Confirm?", multiple=True, single=True, icon="fa-exclamation")
    def mark_cleanup_finished(self, item):
        try:
            if isinstance(item, list):
                try:
                    for i in item:
                        db.session.\
                            query(ProjectCleanup).\
                            filter(ProjectCleanup.project_cleanup_id==i.project_cleanup_id).\
                            filter(ProjectCleanup.status=='DB_CLEANUP_FINISHED').\
                            filter(datetime.now() >= ProjectCleanup.deletion_date).\
                            update({'status': 'FILES_DELETED'})
                    db.session.commit()
                except:
                    db.session.rollback()
                    raise
            else:
                try:
                    db.session.\
                        query(ProjectCleanup).\
                        filter(ProjectCleanup.project_cleanup_id==item.project_cleanup_id).\
                        filter(ProjectCleanup.status=='DB_CLEANUP_FINISHED').\
                        filter(datetime.now() >= ProjectCleanup.deletion_date).\
                        update({'status': 'FILES_DELETED'})
                    db.session.commit()
                except:
                    db.session.rollback()
                    raise
            return redirect(url_for('ProjectCleanup.list'))
        except Exception as e:
            log.error(e)
            flash('Failed to mark projects deleted', 'danger')
            return redirect(url_for('ProjectCleanup.list'))


class ProjectCleanupFinishedView(ModelView):
    datamodel = SQLAInterface(ProjectCleanup)
    list_columns = [
        "user_name",
        "user_email",
        "status",
        "deletion_date",
        "update_date"]
    show_columns = [
        "user_name",
        "user_email",
        "projects",
        "status",
        "deletion_date",
        "update_date"]
    label_columns = {
        "user_email": "User email",
        "user_name": "User name",
        "projects": "List of Projects",
        "status": "Status",
        "deletion_date": "Deletion date",
        "update_date": "Updated on"}
    base_permissions = [
        "can_list",
        "can_show"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["FILES_DELETED"]]]
    base_order = ("project_cleanup_id", "desc")