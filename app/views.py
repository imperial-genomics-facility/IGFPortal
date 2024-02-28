import json
import logging
from flask_appbuilder import has_access
from flask import render_template, redirect, flash, url_for, send_file, abort
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, SimpleFormView
from flask_appbuilder.baseviews import BaseView, expose
from . import appbuilder, db
from .models import IlluminaInteropData, PreDeMultiplexingData
from .forms import SeqrunInteropForm
from .models import AdminHomeData
from .interop_view import IlluminaInteropDataView
from .home_view import HomeView
from .pre_demultiplexing_view import PreDeMultiplexingDataView
from .samplesheet_view import SampleSheetView
from .raw_metadata_view import RawMetadataValidationView, RawMetadataSubmitView
from .raw_seqrun_view import RawSeqrunView
from .analysis_view import AnalysisView
from .metadata_view import ProjectView, UserView, SeqrunView, SampleProjectView, SampleView
from .raw_analysis_view import RawAnalysisView, RawAnalysisSchemaView, RawAnalysisQueueView, RawAnalysisTemplateView
from .rds_project_backup_view import RDSProjectBackupView
from .pipeline_trigger_view import PipelineTriggerView
from .index_table_view import ProjectIndexView, SampleIndexView
from .iframe_view import IFrameView
from .project_cleanup_view import ProjectCleanupFinishedView, ProjectCleanupPendingView

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html",
            base_template=appbuilder.base_template,
            appbuilder=appbuilder
        ),
        404,
    )

"""
    Application wide 401 error handler
"""


@appbuilder.app.errorhandler(401)
def page_not_found(e):
    return (
        render_template(
            "401.html",
            base_template=appbuilder.base_template,
            appbuilder=appbuilder
        ),
        401,
    )

"""
    Application wide 500 error handler
"""


@appbuilder.app.errorhandler(500)
def page_not_found(e):
    return (
        render_template(
            "500.html",
            base_template=appbuilder.base_template,
            appbuilder=appbuilder
        ),
        500,
    )

"""
    Create DB
"""
db.create_all()

"""
    Home view
"""
appbuilder.\
    add_view_no_menu(HomeView())

"""
IFrame view
"""

appbuilder.\
    add_view_no_menu(IFrameView())

"""
    Seqrun view
"""
appbuilder.\
    add_view(
        IlluminaInteropDataView,
        "InterOp SAV reports",
        category_icon="fa-database",
        icon="fa-bar-chart",
        category="Sequencing runs")
appbuilder.\
    add_view(
        PreDeMultiplexingDataView,
        "Pre de-multiplexing reports",
        category_icon="fa-database",
        icon="fa-line-chart",
        category="Sequencing runs")
appbuilder.\
    add_view(
        SampleSheetView,
        "SampleSheets",
        category_icon="fa-database",
        icon="fa-th-list",
        category="Sequencing runs")
appbuilder.\
    add_view(
        RawSeqrunView,
        "Assign samplesheet to run",
        category_icon="fa-database",
        icon="fa-pencil-square-o",
        category="Sequencing runs")
"""
    Metadata upload
"""
appbuilder.\
    add_view(
        RawMetadataValidationView,
        "Create metadata and validate",
        category_icon="fa-folder-open-o",
        icon="fa-th",
        category="Metadata")
appbuilder.\
    add_view(
        RawMetadataSubmitView,
        "Upload metadata to pipeline",
        category_icon="fa-folder-open-o",
        icon="fa-upload",
        category="Metadata")
appbuilder.\
    add_view_no_menu(SampleView())
appbuilder.\
    add_view(
        SampleProjectView,
        "Latest projects",
        category_icon="fa-table",
        icon="fa-list-ol",
        category="Metadata")
"""
    Raw analysis view
"""
#appbuilder.\
#    add_view(
#        PipelineTriggerView(),
#        "Trigger pipelines",
#        href="/trigger_page",
#        category_icon="fa-flask",
#        icon="fa-rocket",
#        category="Analysis")
appbuilder.\
    add_view(
        RawAnalysisView,
        "Create new analysis design",
        category_icon="fa-flask",
        icon="fa-file-text-o",
        category="Analysis")
appbuilder.\
    add_view(
        RawAnalysisQueueView,
        "View analysis upload queue",
        category_icon="fa-flask",
        icon="fa fa-binoculars",
        category="Analysis")
appbuilder.\
    add_view(
        AnalysisView,
        "Trigger analysis pipeline",
        category_icon="fa-flask",
        icon="fa-space-shuttle",
        category="Analysis")
appbuilder.\
    add_view(
        RawAnalysisSchemaView,
        "Validation schema",
        category_icon="fa-flask",
        icon="fa fa-check-square-o",
        category="Analysis")
appbuilder.\
    add_view(
        RawAnalysisTemplateView,
        "Analysis template",
        category_icon="fa-flask",
        icon="fa fa-magic",
        category="Analysis")


"""
    Data cleanup
"""
appbuilder.\
    add_view(
        ProjectCleanupPendingView,
        "Cleanup old projects",
        category_icon="fa-cubes",
        icon="fa-paper-plane",
        category="Data cleanup")

appbuilder.\
    add_view(
        ProjectCleanupFinishedView,
        "Removed projects",
        category_icon="fa-cubes",
        icon="fa-paper-plane",
        category="Data cleanup")
"""
    Metadata view
"""
# appbuilder.\
#     add_view(
#         ProjectView,
#         "Projects",
#         category_icon="fa-table",
#         icon="fa-home",
#         category="Metadata table")
# appbuilder.\
#     add_view(
#         SampleProjectView,
#         "Samples",
#         category_icon="fa-table",
#         icon="fa-list-ol",
#         category="Metadata table")
# appbuilder.\
#     add_view(
#         UserView,
#         "Users",
#         category_icon="fa-table",
#         icon="fa-users",
#         category="Metadata table")
# appbuilder.\
#     add_view(
#         SeqrunView,
#         "Sequencing runs",
#         category_icon="fa-table",
#         icon="fa-paper-plane-o",
#         category="Metadata table")

"""
    Index table view
"""
# appbuilder.\
#     add_view(
#         ProjectIndexView,
#         "Project index",
#         category_icon="fa-folder-open-o",
#         icon="fa-table",
#         category="Metadata")
# appbuilder.\
#     add_view(
#         SampleIndexView,
#         "Sample index",
#         category_icon="fa-folder-open-o",
#         icon="fa-table",
#         category="Metadata")