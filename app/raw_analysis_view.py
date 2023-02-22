import logging, tempfile, os, json
from yaml import load, Loader
from io import BytesIO
from .models import RawAnalysis, Sample, Experiment, Seqrun, Run, File, Collection, Collection_group, Project, Pipeline, RawAnalysisValidationSchema
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
from jsonschema import Draft202012Validator

log = logging.getLogger(__name__)

def validate_json_schema(raw_analysis_schema_id):
    try:
        status = 'FAILED'
        raw_analysis_schema = \
            db.session.\
                query(RawAnalysisValidationSchema).\
                filter(RawAnalysisValidationSchema.raw_analysis_schema_id==raw_analysis_schema_id).\
                one_or_none()
        if raw_analysis_schema is None:
            raise ValueError(
                    f"No metadata entry found for id {raw_analysis_schema_id}")
        json_schema = \
            raw_analysis_schema.json_schema
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
                filter(RawAnalysisValidationSchema.raw_analysis_schema_id==raw_analysis_schema_id).\
                update({'status': status})
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except:
        raise


@celery.task(bind=True)
def async_validate_analysis_schema(self, id_list):
    try:
        results = list()
        for raw_analysis_schema_id in id_list:
            msg = \
                validate_json_schema(
                    raw_analysis_schema_id=raw_analysis_schema_id)
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

def _get_validation_status_for_analysis_design(
        analysis_yaml: str,
        validation_schema: str) -> list:
    try:
        error_list = list()
        # load yaml
        try:
            json_data = \
                load(analysis_yaml, Loader=Loader)
        except:
            error_list.append(
                'Failed to load yaml data')
        try:
            schema = \
                json.loads(validation_schema)
        except:
            error_list.append(
                'Failed to load validation schema')
        try:
            # validation can fail if inputs are not correct
            schema_validator = \
                Draft202012Validator(schema)
            for error in sorted(schema_validator.iter_errors(json_data), key=str):
                error_list.append(error)
        except:
            error_list.append(
                'Failed to check validation schema')
        return error_list
    except:
        raise

def _get_project_id_for_samples(sample_igf_id_list: list) -> list:
    try:
        project_list = list()
        results = \
            db.session.\
                query(Project).\
                distinct(Project.project_igf_id).\
                join(Sample, Project.project_id==Sample.project_id).\
                filter(Sample.sample_igf_id.in_(sample_igf_id_list)).\
                all()
        project_list = list(results)
        return project_list
    except:
        raise


def _get_file_collection_for_samples(
      sample_igf_id_list: list,
      active_status: str = 'ACTIVE',
      fastq_collection_type_list: list = ('demultiplexed_fastq',)) -> list:
  """
  A function for fetching fastq and run_igf_id for a list od samples

  :param sample_igf_id_list: A list of sample_igf_ids for DB lookup
  :param active_status: Filter tag for active experiment, run and file status, default: active
  :param fastq_collection_type_list: Fastq collection type list, default ('demultiplexed_fastq',)
  :returns: A list of sample_igf_ids which are linked to valid file paths
  """
  try:
    sample_with_files = list()
    results = \
      db.session.\
        query(Sample).\
        distinct(Sample.sample_igf_id).\
        join(Experiment, Sample.sample_id==Experiment.sample_id).\
        join(Run, Experiment.experiment_id==Run.experiment_id).\
        join(Collection, Collection.name==Run.run_igf_id).\
        join(Collection_group, Collection.collection_id==Collection_group.collection_id).\
        join(File, File.file_id==Collection_group.file_id).\
        filter(Run.status==active_status).\
        filter(Experiment.status==active_status).\
        filter(File.status==active_status).\
        filter(Collection.type.in_(fastq_collection_type_list)).\
        filter(Sample.sample_igf_id.in_(sample_igf_id_list)).\
        all()
    sample_with_files = \
        list(results)
    return sample_with_files
  except Exception as e:
    raise ValueError(
        f'Failed to fetch fastq dir for sample id {sample_igf_id_list}, error: {e}')


def _get_sample_metadata_checks_for_analsis(
        sample_metadata: dict,
        project_igf_id: str) -> list:
    try:
        error_list = list()
        if not isinstance(sample_metadata, dict):
            error_list.append(
                f'sample_metadata has type {type(sample_metadata)}')
        else:
            sample_ids = \
                list(sample_metadata.keys())
            if len(sample_ids) == 0:
                error_list.append('No sample ids found in sample_metadata')
            if len(sample_ids) > 0:
                sample_with_files = \
                    _get_file_collection_for_samples(
                        sample_igf_id_list=sample_ids)
                if len(sample_ids) != len(sample_with_files):
                    missing_samples = \
                        list(set(sample_with_files).difference(set(sample_ids)))
                    error_list.append(
                        f"Missing fastq for samples: {', '.join(missing_samples)}")
                project_list = \
                    _get_project_id_for_samples(sample_igf_id_list=sample_ids)
                if len(project_list) == 0 :
                    error_list.append('No project info found')
                if len(project_list) > 1:
                    error_list.append(
                        f"samples are linked to multiple projects: {', '.join(project_list)}")
                if len(project_list) == 1 and \
                   project_list[0].project_igf_id != project_igf_id:
                    error_list.append(
                        f'Analysis is linked to project {project_igf_id} but samples are linked to project {project_list[0].project_igf_id}')
        return error_list
    except:
        raise

def validate_analysis_design(
        raw_analysis_id: int) -> str:
    try:
        status = 'FAILED'
        validation_schema = None
        error_list = list()
        raw_analysis_design = \
            db.session.\
                query(RawAnalysis).\
                filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                one_or_none()
        if raw_analysis_design is None:
            raise ValueError(
                    f"No metadata entry found for id {raw_analysis_id}")
        analysis_yaml = \
            raw_analysis_design.analysis_yaml
        analysis_yaml = \
            analysis_yaml
        pipeline_id = \
            raw_analysis_design.pipeline_id
        if pipeline_id is None:
            error_list.append("No pipeline info found")
        project_igf_id = \
            raw_analysis_design.project.project_igf_id
        if project_igf_id is None:
            error_list.append("No project id found")
        else:
            raw_analysis_schema = \
                db.session.\
                    query(RawAnalysisValidationSchema).\
                    filter(RawAnalysisValidationSchema.pipeline_id==pipeline_id).\
                    one_or_none()
            if raw_analysis_schema is None:
                error_list.append("No analysis schema found")
            else:
                validation_schema = \
                    raw_analysis_schema.json_schema
        if validation_schema is not None:
            try:
                # check against schema
                schema_validation_errors = \
                    _get_validation_status_for_analysis_design(
                        analysis_yaml=analysis_yaml,
                        validation_schema=validation_schema)
                if len(schema_validation_errors) > 0:
                    error_list.extend(schema_validation_errors)
            except Exception as e:
                error_list.append("Failed to inspect design")
        if len(error_list) == 0:
            # its time to check igf ids
            # assuming it has sample_metadata as its passed validation checks
            json_data = \
                load(analysis_yaml, Loader=Loader)
            sample_metadata = \
                json_data.get('sample_metadata')
            if sample_metadata is None:
                error_list.append(
                    'sample_metadata missing after validation checks ??')
            else:
                sample_metadata_errors = \
                    _get_sample_metadata_checks_for_analsis(
                        sample_metadata=sample_metadata,
                        project_igf_id=project_igf_id)
                if len(sample_metadata_errors) > 0:
                    error_list.extend(sample_metadata_errors)
        if len(error_list) == 0:
            status = 'VALIDATED'
            errors = ''
        else:
            status = 'FAILED'
            formatted_errors = list()
            for i, e in enumerate(error_list):
                formatted_errors.append(f"{i+1}. {e}")
            errors = '\n'.join(formatted_errors)
        try:
            db.session.\
                query(RawAnalysis).\
                filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                update({'status': status, 'report': errors})
            db.session.commit()
        except:
            db.session.rollback()
            raise
        return status
    except:
        raise

@celery.task(bind=True)
def async_validate_analysis_yaml(self, id_list):
    try:
        results = list()
        for raw_analysis_id in id_list:
            msg = \
                validate_analysis_design(
                    raw_analysis_id=raw_analysis_id)
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


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
            analysis_list = [i.analysis_name for i in item]
            id_list = [i.raw_analysis_id for i in item]
        else:
            analysis_list = [item.analysis_name]
            id_list = [item.raw_analysis_id]
        _ = \
            async_validate_analysis_yaml.\
                apply_async(args=[id_list])
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

class RawAnalysisQueueView(ModelView):
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
    base_filters = [
        ["status", FilterInFunction, lambda: ["VALIDATED",]]]
    base_order = ("raw_analysis_id", "desc")
    base_permissions = [
        "can_list",
        "can_show"]