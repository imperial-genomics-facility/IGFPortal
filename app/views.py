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
    View
"""
appbuilder.\
    add_view_no_menu(HomeView())
appbuilder.\
    add_view(
        IlluminaInteropDataView,
        "InterOp data",
        category_icon="fa-database",
        icon="fa-bar-chart",
        category="Sequencing runs")
appbuilder.\
    add_view(
        PreDeMultiplexingDataView,
        "Pre de-multiplication",
        category_icon="fa-database",
        icon="fa-line-chart",
        category="Sequencing runs")
appbuilder.\
    add_view(
        SampleSheetView,
        "Samplesheet",
        category_icon="fa-database",
        icon="fa-excel",
        category="Sequencing runs")
db.create_all()
