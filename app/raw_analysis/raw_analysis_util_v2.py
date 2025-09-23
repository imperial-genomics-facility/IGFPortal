from app import db
import os
import json
import logging
from jinja2 import Template
from typing import Tuple, List
from app.models import (
    Sample,
    Experiment,
    Run,
    File,
    Collection,
    Collection_group,
    Project,
    RawPipeline,
    RawProject,
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)
from yaml import load, SafeLoader
from jsonschema import Draft202012Validator

log = logging.getLogger(__name__)

def raw_project_query():
    try:
        results = db.session.query(
            RawProject
        ).filter(
            RawProject.status=='ACTIVE'
        ).order_by(
            RawProject.project_id.desc()
        ).limit(100).all()
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get project list, error: {e}")


def raw_pipeline_query():
    try:
        results = db.session.query(
            RawPipeline
        ).filter(
            RawPipeline.is_active=='Y'
        ).filter(
                RawPipeline.pipeline_type=='AIRFLOW'
        ).filter(
                RawPipeline.pipeline_name.like("dag%")
        ).order_by(
                RawPipeline.pipeline_id.desc()
        ).limit(100).all()
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get pipeline list, error: {e}")


def validate_analysis_json_schema(
    raw_analysis_schema_id: int,
    validated_tag: str = 'VALIDATED',
    failed_tag: str = 'FAILED') -> str:
    try:
        status = failed_tag
        raw_analysis_schema = db.session.query(
            RawAnalysisValidationSchemaV2
        ).filter(
            RawAnalysisValidationSchemaV2.\
                raw_analysis_schema_id==raw_analysis_schema_id
        ).one_or_none()
        if raw_analysis_schema is None:
            raise ValueError(
                f"No metadata entry found for id {raw_analysis_schema_id}")
        json_schema = \
            raw_analysis_schema.json_schema
        if json_schema is not None:
            try:
                _ = json.loads(json_schema)
                status = validated_tag
            except Exception as e:
                log.error(f"Failed to run json validation, error: {e}")
                status = failed_tag
        ## update db status
        try:
            db.session.query(
                RawAnalysisValidationSchemaV2
            ).filter(
                RawAnalysisValidationSchemaV2.\
                       raw_analysis_schema_id==raw_analysis_schema_id
            ).update({'status': status})
            db.session.commit()
        except:
            db.session.rollback()
            raise
        return status
    except Exception as e:
        raise ValueError(
            f"Failed to validate json schema, error: {e}")


def _get_validation_status_for_analysis_design(
        analysis_yaml: str,
        validation_schema: str) -> list:
    try:
        error_list = list()
        # load yaml
        try:
            json_data = \
                load(analysis_yaml, Loader=SafeLoader)
        except Exception as e:
            error_list.append(
                f'Failed to load yaml data. Invalid format., error: {e}')
            return error_list
        try:
            schema = \
                json.loads(validation_schema)
        except Exception as e:
            error_list.append(
                f'Failed to load validation schema. Invalid format., error: {e}')
            return error_list
        try:
            # validation can fail if inputs are not correct
            schema_validator = \
                Draft202012Validator(schema)
            for error in sorted(schema_validator.iter_errors(json_data), key=str):
                error_list.append(error.message)
        except Exception:
            error_list.append(
                'Failed to check validation schema')
        return error_list
    except Exception as e:
        raise ValueError(
            f"Failed to get schema validation for analysis design, error: {e}")


def _get_project_id_for_samples(
        sample_igf_id_list: list) -> list:
    try:
        project_list = list()
        results = db.session.query(
            Project
        ).distinct(
            Project.project_igf_id
        ).join(
            Sample, Project.project_id==Sample.project_id
        ).filter(
            Sample.sample_igf_id.in_(sample_igf_id_list)
        ).all()
        project_list = [
            p.project_igf_id for p in list(results)
        ]
        return project_list
    except Exception as e:
        raise ValueError(
            f"Failed to get project id for sample list, error; {e}")


def _get_file_collection_for_samples(
      sample_igf_id_list: list,
      active_status: str = 'ACTIVE',
      fastq_collection_type_list: Tuple[str] = ('demultiplexed_fastq',)) -> list:
  """
  A function for fetching fastq and run_igf_id for a list od samples

  :param sample_igf_id_list: A list of sample_igf_ids for DB lookup
  :param active_status: Filter tag for active experiment, run and file status, default: active
  :param fastq_collection_type_list: Fastq collection type list, default ('demultiplexed_fastq',)
  :returns: A list of sample_igf_ids which are linked to valid file paths
  """
  try:
    sample_with_files = list()
    results = db.session.query(
        Sample.sample_igf_id
    ).distinct(
        Sample.sample_igf_id
    ).join(
        Experiment, Sample.sample_id==Experiment.sample_id
    ).join(
        Run, Experiment.experiment_id==Run.experiment_id
    ).join(
        Collection, Collection.name==Run.run_igf_id
    ).join(
        Collection_group, \
            Collection.collection_id==Collection_group.collection_id
    ).join(
        File, File.file_id==Collection_group.file_id
    ).filter(
        Run.status==active_status
    ).filter(
        Experiment.status==active_status
    ).filter(
        File.status==active_status
    ).filter(
        Collection.type.in_(fastq_collection_type_list)
    ).filter(
        Sample.sample_igf_id.in_(sample_igf_id_list)
    ).all()
    if results is not None:
        sample_with_files = [
            s.sample_igf_id
                for s in list(results)]
    return sample_with_files
  except Exception as e:
    raise ValueError(
        f'Failed to fetch fastq dir for sample id \
         {sample_igf_id_list}, error: {e}')


def _get_sample_metadata_checks_for_analysis(
        sample_metadata: dict,
        project_igf_id: str) -> list:
    try:
        error_list = list()
        if not isinstance(sample_metadata, dict):
            error_list.append(
                f'sample_metadata has type {type(sample_metadata)}')
            return error_list
        else:
            sample_ids = \
                list(sample_metadata.keys())
            if len(sample_ids) == 0:
                error_list.append(
                    'No sample ids found in sample_metadata')
                return error_list
            if len(sample_ids) > 0:
                sample_with_files = \
                    _get_file_collection_for_samples(
                        sample_igf_id_list=sample_ids)
                if len(sample_ids) != len(sample_with_files):
                    if len(sample_with_files) == 0:
                        error_list.append('No sample has fastq')
                    else:
                        missing_samples = \
                            list(set(sample_ids).difference(set(sample_with_files)))
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
                   project_list[0] != project_igf_id:
                    error_list.append(
                        f'Analysis is linked to project {project_igf_id} ' + \
                        f'but samples are linked to project {project_list[0]}')
        return error_list
    except Exception as e:
        raise ValueError(
            f"Failed to check sample metadata, error: {e}")


def _get_validation_errors_for_analysis_design(raw_analysis_id: int) -> List[str]:
    try:
        error_list = list()
        project_igf_id = ''
        deliverable = ''
        # get raw analysis design
        raw_analysis_design = db.session.query(
            RawAnalysisV2
        ).filter(
            RawAnalysisV2.raw_analysis_id==raw_analysis_id
        ).one_or_none()
        if raw_analysis_design is None:
            error_list.append(
                f"No metadata entry found for id {raw_analysis_id}")
        # no missing db record found
        if len(error_list) == 0:
            # get design yaml
            analysis_yaml = \
                raw_analysis_design.analysis_yaml
            if analysis_yaml is None:
                error_list.append(
                    "No analysis design found")
            pipeline_id = \
                raw_analysis_design.pipeline_id
            if pipeline_id is None:
                error_list.append(
                    "No pipeline info found")
            if raw_analysis_design.project is None:
                error_list.append(
                    "No project id found")
            else:
                project_igf_id = \
                    raw_analysis_design.project.project_igf_id
                deliverable = \
                    raw_analysis_design.project.deliverable
            # get validation schema
            raw_analysis_schema = db.session.query(
                RawAnalysisValidationSchemaV2
            ).filter(
                RawAnalysisValidationSchemaV2.pipeline_id==pipeline_id
            ).one_or_none()
            if raw_analysis_schema is None:
                error_list.append(
                    "No analysis schema found")
            ## no missing data, lets validate design against a schema
            if len(error_list) == 0:
                validation_schema = \
                    raw_analysis_schema.json_schema
                try:
                    # check design against schema
                    schema_validation_errors = \
                        _get_validation_status_for_analysis_design(
                            analysis_yaml=analysis_yaml,
                            validation_schema=validation_schema)
                    if len(schema_validation_errors) > 0:
                        error_list.extend(
                            schema_validation_errors)
                except Exception as e:
                    log.error(e)
                    error_list.append(
                        "Failed to inspect analysis design")
                ## valid schema, lets check sample ids
                ## only for sequencing projects, not for cosmx
                if len(error_list) == 0 and \
                   deliverable == 'FASTQ':
                    json_data = \
                        load(analysis_yaml, Loader=SafeLoader)
                    sample_metadata = \
                        json_data.get('sample_metadata')
                    if sample_metadata is None:
                        error_list.append(
                            'sample_metadata missing after validation checks ??')
                    ## no corrupted db record found
                    if len(error_list) == 0:
                        sample_metadata_errors = \
                            _get_sample_metadata_checks_for_analysis(
                                sample_metadata=sample_metadata,
                                project_igf_id=project_igf_id)
                        if len(sample_metadata_errors) > 0:
                            error_list.extend(
                                sample_metadata_errors)
        return error_list
    except Exception as e:
        raise ValueError(
            f"Failed to check analysis metadata, error: {e}")


def validate_analysis_design(
        raw_analysis_id: int) -> str:
    try:
        status = 'FAILED'
        error_list = list()
        error_list = \
            _get_validation_errors_for_analysis_design(
                raw_analysis_id=raw_analysis_id)
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
            db.session.query(
                RawAnalysisV2
            ).filter(
                RawAnalysisV2.raw_analysis_id==raw_analysis_id
            ).update({
                'status': status,
                'report': errors
            })
            db.session.commit()
        except:
            db.session.rollback()
            raise
        return status
    except Exception as e:
        raise ValueError(
            f"Failed to validate analysis design, error; {e}")


def _fetch_project_igf_id_and_deliverable_for_raw_analysis_id(
    raw_analysis_id: int) -> \
        Tuple[str, str]:
    try:
        project_records = db.session.query(
            RawProject.project_igf_id,
            RawProject.deliverable
        ).join(
            RawAnalysisV2, \
                RawProject.project_id==RawAnalysisV2.project_id
        ).filter(
            RawAnalysisV2.raw_analysis_id==raw_analysis_id
        ).one_or_none()
        if project_records is None:
            raise ValueError(
                f"No project entry found for raw analysis {raw_analysis_id}")
        (project_igf_id, deliverable) = project_records
        return (project_igf_id, deliverable)
    except Exception as e:
        raise ValueError(
            f"No project_igf_id for raw analysis {raw_analysis_id}, error: {e}")


def _fetch_all_samples_for_project(project_igf_id: str) -> list:
    try:
        sample_ids = list()
        samples = db.session.query(
            Sample.sample_igf_id
        ).join(
            Project, Project.project_id==Sample.project_id
        ).filter(
            Project.project_igf_id==project_igf_id
        ).all()
        sample_ids = [
            sample_id for (sample_id,) in samples
        ]
        return sample_ids
    except Exception as e:
        raise ValueError(
            f"Failed to get sample list for project {project_igf_id}, error; {e}")


def _fetch_analysis_template_for_raw_analysis_id(
        raw_analysis_id: int,
        default_template_path: str = os.path.join(os.path.dirname(__file__), 'default_analysis_template.txt')) \
            -> str:
    try:
        pipeline_records = db.session.query(
            RawPipeline.pipeline_id
        ).join(
            RawAnalysisV2, \
                RawPipeline.pipeline_id==RawAnalysisV2.pipeline_id
        ).filter(
            RawAnalysisV2.raw_analysis_id==raw_analysis_id
        ).one_or_none()
        if pipeline_records is None or pipeline_records == '':
            raise ValueError(
                f"No pipeline entry found for raw analysis {raw_analysis_id}")
        (pipeline_id,) = pipeline_records
        with open(default_template_path, 'r') as fp:
            default_template = fp.read()
        template_records = db.session.query(
            RawAnalysisTemplateV2.template_data
        ).filter(
            RawAnalysisTemplateV2.pipeline_id==pipeline_id
        ).one_or_none()
        if template_records is None:
            return default_template
        else:
            (template_data,) = template_records
            return template_data
    except Exception as e:
        raise ValueError(
            f"Failed to get template for analysis id {raw_analysis_id}, error; {e}")


def generate_analysis_template_for_analysis_id(raw_analysis_id: int) -> str:
    try:
        (project_igf_id, deliverable) = \
            _fetch_project_igf_id_and_deliverable_for_raw_analysis_id(
                raw_analysis_id)
        template_data = \
            _fetch_analysis_template_for_raw_analysis_id(
                raw_analysis_id)
        if deliverable == 'COSMX':
            sample_id_list = []
        else:
            sample_id_list = \
                _fetch_all_samples_for_project(
                    project_igf_id=project_igf_id)
        template = \
            Template(template_data, keep_trailing_newline=True)
        ## cosmx export will work with this function
        formatted_template = \
            template.render(SAMPLE_ID_LIST=sample_id_list)
        return formatted_template
    except Exception as e:
        raise ValueError(
            f"Failed to generate template for analysis {raw_analysis_id}, error; {e}")