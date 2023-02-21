import logging, tempfile, os, json
from io import BytesIO
from .models import RawAnalysis, RawMetadataModel, Project, Pipeline, RawAnalysisValidationSchema
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask import redirect, flash, url_for, send_file, abort
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from . import db
from . import celery
from .raw_analysis.raw_analysis_util import validate_analysis_json

log = logging.getLogger(__name__)

def validate_json_schema(id):
    try:
        status = 'FAILED'
        raw_metadata_schema = \
            db.session.\
                query(RawAnalysisValidationSchema).\
                filter(RawAnalysisValidationSchema.raw_analysis_schema_id==id).\
                one_or_none()
        if raw_metadata_schema is None:
            raise ValueError(
                    f"No metadata entry found for id {id}")
        json_schema = \
            raw_metadata_schema.json_schema
        if json_schema is not None:
            json_schema = \
                json_schema.encode('utf-8')
        try:
            _ = json.loads(json_schema)
            status = 'VALIDATED'
        except:
            status = 'FAILED'
        try:
            db.session.\
                query(RawAnalysisValidationSchema).\
                filter(RawAnalysisValidationSchema.raw_analysis_schema_id==id).\
                update({'status': status})
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except:
        raise


@celery.task(bind=True)
def async_validate_analysis_yaml(self, id_list):
    try:
        pass
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


@celery.task(bind=True)
def async_validate_analysis_schema(self, id_list):
    try:
        results = list()
        for raw_analysis_schema_id in id_list:
            msg = \
                validate_json_schema(id=raw_analysis_schema_id)
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


def project_query():
    results = \
        db.session.\
            query(Project).\
            filter(Project.status=='ACTIVE').\
            order_by(Project.project_id.desc()).\
            limit(100).\
            all()
    return results

def pipeline_query():
    results = \
        db.session.\
            query(Pipeline).\
            filter(Pipeline.is_active=='Y').\
            filter(Pipeline.pipeline_type=='AIRFLOW').\
            filter(Pipeline.pipeline_name.like("dag%")).\
            order_by(Pipeline.pipeline_id.desc()).\
            limit(100).\
            all()
    return results


class RawAnalysisSchemaView(ModelView):
    datamodel = SQLAInterface(RawAnalysisValidationSchema)
    label_columns = {
        "pipeline.pipeline_name": "Pipeline name",
        "status": "Status",
        "json_schema": "Schema"
    }
    list_columns = ["pipeline.pipeline_name", "status", "date_stamp"]
    show_columns = ["pipeline.pipeline_name", "status", "date_stamp", "json_schema"]
    add_columns = ["pipeline", "json_schema"]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_delete"]
    base_order = ("raw_analysis_schema_id", "desc")

    add_form_extra_fields = {
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=pipeline_query,
            widget=Select2Widget()
        ),
    }
    edit_form_extra_fields = {
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=pipeline_query,
            widget=Select2Widget()
        )
    }

    @action("validate_json_analysis_schema", "Validate JSON", confirmation="Run validate?", multiple=True, single=False, icon="fa-rocket")
    def validate_json_analysis_schema(self, item):
        id_list = list()
        pipeline_list = list()
        if isinstance(item, list):
            id_list = [i.raw_analysis_schema_id for i in item]
            pipeline_list = [i.pipeline.pipeline_name for i in item]
        else:
            id_list = [item.raw_analysis_schema_id]
            pipeline_list = [item.pipeline.pipeline_name]
        _ = \
            async_validate_analysis_schema.\
                apply_async(args=[id_list])
        flash("Submitted jobs for {0}".format(', '.join(pipeline_list)), "info")
        self.update_redirect()
        return redirect(url_for('RawAnalysisSchemaView.list'))

    @action("download_json_analysis_schema", "Download JSON schema", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_json_analysis_schema(self, item):
        try:
            json_schema = item.json_schema
            if json_schema is None:
                json_schema = '{}'
            output = BytesIO(json_schema.encode('utf-8'))
            pipeline_name = item.pipeline.pipeline_name.encode('utf-8').decode()
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=f'{pipeline_name}_schema.json', as_attachment=True)
        except:
            flash('Failed to download analysis schema', 'danger')
            return redirect(url_for('RawAnalysisSchemaView.list'))




class RawAnalysisView(ModelView):
    datamodel = SQLAInterface(RawAnalysis)
    label_columns = {
        "analysis_name": "Analysis name",
        "project.project_igf_id": "Project name",
        "pipeline.pipeline_name": "Pipeline name",
        "status": "Status",
        "date_stamp": "Updated on",
        "analysis_yaml": "Yaml",
        "report": "Report"
    }
    list_columns = ["analysis_name", "project.project_igf_id", "pipeline.pipeline_name", "status", "date_stamp"]
    show_columns = ["analysis_name", "project.project_igf_id", "pipeline.pipeline_name", "status", "date_stamp", "analysis_yaml",  "report"]
    add_columns = ["analysis_name", "project", "pipeline", "analysis_yaml"]
    edit_columns = ["analysis_name", "project", "pipeline", "analysis_yaml"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]]
    base_order = ("raw_analysis_id", "desc")
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"]

    add_form_extra_fields = {
        "project": QuerySelectField(
            "Project",
            query_factory=project_query,
            widget=Select2Widget()
        ),
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=pipeline_query,
            widget=Select2Widget()
        ),
    }
    edit_form_extra_fields = {
        "project": QuerySelectField(
            "Project",
            query_factory=project_query,
            widget=Select2Widget()
        ),
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=pipeline_query,
            widget=Select2Widget()
        )
    }


    @action("validate_and_submit_analysis", "Validate and upload analysis", confirmation="Validate analysis design?", multiple=True, single=False, icon="fa-rocket")
    def validate_and_submit_analysis(self, item):
        analysis_list = list()
        id_list = list()
        if isinstance(item, list):
            analysis_list = [i.analysis_tag for i in item]
            id_list = [i.raw_analysis_id for i in item]
        else:
            analysis_list = [item.analysis_tag]
            id_list = [item.raw_analysis_id]
        flash("Submitted jobs for {0}".format(', '.join(analysis_list)), "info")
        self.update_redirect()
        return redirect(url_for('RawAnalysisView.list'))


    @action("download_raw_analysis_damp", "Download analysis yaml", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_raw_analysis_damp(self, item):
        try:
            analysis_yaml = item.analysis_yaml
            if analysis_yaml is None:
                analysis_yaml = ''
            output = BytesIO(analysis_yaml.encode('utf-8'))
            analysis_name = item.analysis_name.encode('utf-8').decode()
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=f'{analysis_name}_analysis.yaml', as_attachment=True)
        except:
            flash('Failed to download raw analysis', 'danger')
            return redirect(url_for('RawAnalysisView.list'))

    @action("template_nf_rna", "Template NF RNA", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_rna(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_sm_rna", "Template Snakemake RNA", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_sm_rna(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_chip", "Template NF ChIP", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_chip(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_atac", "Template NF ATAC", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_atac(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_sarek", "Template NF Sarek", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_sarek(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_ampliseq", "Template NF Ampliseq", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_ampliseq(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_ampliseq", "Template NF Ampliseq", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_ampliseq(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_cutandrun", "Template NF CutAndRun", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_cutandrun(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_nf_bactmap", "Template NF BactMap", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_nf_bactmap(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)

    @action("template_custom", "Template Custom", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def template_custom(self, item):
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        output = BytesIO(analysis_yaml.encode('utf-8'))
        analysis_name = item.analysis_name.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name='{0}_analysis.yaml'.format(analysis_name), as_attachment=True)