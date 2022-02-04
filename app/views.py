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