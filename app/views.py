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
from .metadata_view import ProjectView, UserView, SeqrunView, AnalysisView
from .raw_analysis_view import RawAnalysisView
from .rds_project_backup_view import RDSProjectBackupView


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
        category="Metadata submission")
appbuilder.\
    add_view(
        RawMetadataSubmitView,
        "Upload metadata to pipeline",
        category_icon="fa-folder-open-o",
        icon="fa-upload",
        category="Metadata submission")
"""
    Raw analysis view
"""
appbuilder.\
    add_view(
        RawAnalysisView,
        "Add and submit analysis design",
        category_icon="fa-flask",
        icon="fa-file-text-o",
        category="Analysis")
appbuilder.\
    add_view(
        AnalysisView,
        "Trigger analysis pipelines",
        category_icon="fa-flask",
        icon="fa-space-shuttle",
        category="Analysis")
"""
    Data transfer
"""
appbuilder.\
    add_view(
        RDSProjectBackupView,
        "Transfer project via RDS",
        category_icon="fa-cubes",
        icon="fa-paper-plane",
        category="Data transfer")
"""
    Metadata view
"""
appbuilder.\
    add_view(
        ProjectView,
        "Projects",
        category_icon="fa-table",
        icon="fa-home",
        category="Metadata table")
appbuilder.\
    add_view(
        UserView,
        "Users",
        category_icon="fa-table",
        icon="fa-users",
        category="Metadata table")
appbuilder.\
    add_view(
        SeqrunView,
        "Sequencing runs",
        category_icon="fa-table",
        icon="fa-paper-plane-o",
        category="Metadata table")