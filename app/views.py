from flask import render_template
from app import appbuilder, db
from app.interop_view import IlluminaInteropDataView
from app.home_view import HomeView
from app.pre_demultiplexing_view import PreDeMultiplexingDataView
from app.samplesheet_view import SampleSheetView
from app.raw_metadata_view import (
    RawMetadataValidationView,
    RawMetadataSubmitView
)
from app.raw_seqrun_view import RawSeqrunView
from app.analysis_view import AnalysisView
from app.metadata_view import SampleProjectView, SampleView
from app.raw_analysis_view_v2 import (
    RawAnalysisV2View,
    RawAnalysisSchemaV2View,
    RawAnalysisTemplateV2View,
    RawAnalysisQueueV2View
)
from .iframe_view import IFrameView
from app.project_cleanup_view import (
    ProjectCleanupFinishedView,
    ProjectCleanupPendingView
)
from app.cosmx_raw_metadata_view import (
    RawCosMxMetadataBuilderView,
    RawCosMxMetadataModelView
)
"""
    Application wide 404 error handler
"""
@appbuilder.app.errorhandler(404)
def page_not_found_404(e):
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
def page_not_found_401(e):
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
def page_not_found_500(e):
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
# with app.app_context():
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
appbuilder.add_view(
    IlluminaInteropDataView,
    "InterOp SAV reports",
    category_icon="fa-database",
    icon="fa-bar-chart",
    category="Sequencing runs"
)
appbuilder.add_view(
    PreDeMultiplexingDataView,
    "Pre de-multiplexing reports",
    category_icon="fa-database",
    icon="fa-line-chart",
    category="Sequencing runs"
)
appbuilder.add_view(
    SampleSheetView,
    "SampleSheets",
    category_icon="fa-database",
    icon="fa-th-list",
    category="Sequencing runs"
)
appbuilder.add_view(
    RawSeqrunView,
    "Assign samplesheet to run",
    category_icon="fa-database",
    icon="fa-pencil-square-o",
    category="Sequencing runs"
)
"""
    Metadata upload
"""
appbuilder.add_view(
    RawMetadataValidationView,
    "Create metadata and validate",
    category_icon="fa-folder-open-o",
    icon="fa-th",
    category="Metadata"
)
appbuilder.add_view(
    RawMetadataSubmitView,
    "Upload metadata to pipeline",
    category_icon="fa-folder-open-o",
    icon="fa-upload",
    category="Metadata"
)
appbuilder.add_view_no_menu(
    SampleView()
)
appbuilder.add_view(
    SampleProjectView,
    "Latest projects",
    category_icon="fa-table",
    icon="fa-list-ol",
    category="Metadata"
)
appbuilder.add_view(
    RawAnalysisV2View,
    "Create new analysis design",
    category_icon="fa-flask",
    icon="fa-file-text-o",
    category="Analysis"
)
appbuilder.add_view(
    RawAnalysisQueueV2View,
    "View analysis upload queue",
    category_icon="fa-flask",
    icon="fa fa-binoculars",
    category="Analysis"
)
appbuilder.add_view(
    AnalysisView,
    "Trigger analysis pipeline",
    category_icon="fa-flask",
    icon="fa-space-shuttle",
    category="Analysis"
)
appbuilder.add_view(
    RawAnalysisSchemaV2View,
    "Validation schema",
    category_icon="fa-flask",
    icon="fa fa-check-square-o",
    category="Analysis"
)
appbuilder.add_view(
    RawAnalysisTemplateV2View,
    "Analysis template",
    category_icon="fa-flask",
    icon="fa fa-magic",
    category="Analysis"
)
"""
    CosMx view
"""
appbuilder.add_view(
    RawCosMxMetadataBuilderView,
    "Register new metadata",
    category_icon="fa-flask",
    icon="fa-file-text-o",
    category="CosMX"
)
appbuilder.add_view(
    RawCosMxMetadataModelView,
    "Metadata queue",
    category_icon="fa-flask",
    icon="fa fa-th-list",
    category="CosMX"
)
"""
    Data cleanup
"""
appbuilder.add_view(
    ProjectCleanupPendingView,
    "Cleanup old projects",
    category_icon="fa-cubes",
    icon="fa-paper-plane",
    category="Data cleanup"
)
appbuilder.add_view(
    ProjectCleanupFinishedView,
    "Removed projects",
    category_icon="fa-cubes",
    icon="fa-paper-plane",
    category="Data cleanup"
)