import logging
from app import db
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from app.models import (
    CosMxMasterTableUser,
    CosMxMasterTablePanel,
    CosMxMasterTableTissue,
    CosMxMasterTableSlide
)
log = logging.getLogger(__name__)

class CosMxMasterTableUserView(ModelView):
    datamodel = SQLAInterface(CosMxMasterTableUser)
    label_columns = {
        "name": "User name",
    }
    list_columns = [
        "name"
    ]
    show_columns = [
        "name"
    ]
    add_columns = [
        "name"
    ]
    edit_columns = [
        "name"
    ]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"
    ]
    base_order = ("user_id", "desc")

class CosMxMasterTablePanelView(ModelView):
    datamodel = SQLAInterface(CosMxMasterTablePanel)
    label_columns = {
        "panel_type": "Panel type",
    }
    list_columns = [
        "panel_type"
    ]
    show_columns = [
        "panel_type"
    ]
    add_columns = [
        "panel_type"
    ]
    edit_columns = [
        "panel_type"
    ]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"
    ]
    base_order = ("panel_id", "desc")


class CosMxMasterTableTissueView(ModelView):
    datamodel = SQLAInterface(CosMxMasterTableTissue)
    label_columns = {
        "tissue_name": "Tissue name",
        "tissue_ontology": "Tissue ontology url"
    }
    list_columns = [
        "tissue_name",
        "tissue_ontology"
    ]
    show_columns = [
        "tissue_name",
        "tissue_ontology"
    ]
    add_columns = [
        "tissue_name",
        "tissue_ontology"
    ]
    edit_columns = [
        "tissue_name",
        "tissue_ontology"
    ]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"
    ]
    base_order = ("tissue_id", "desc")

def user_query():
    try:
        results = (
            db.session
            .query(CosMxMasterTableUser)
            .order_by(
                CosMxMasterTableUser.user_id.desc()
            )
            .all()
        )
        return results
    except Exception as e:
        raise ValueError(
            "Failed to get user list, error: "
            + str(e)
        )

def panel_query():
    try:
        results = (
            db.session
            .query(CosMxMasterTablePanel)
            .order_by(
                CosMxMasterTablePanel.panel_id.desc()
            )
            .all()
        )
        return results
    except Exception as e:
        raise ValueError(
            "Failed to get panel list, error: "
            + str(e)
        )

def tissue_query():
    try:
        results = (
            db.session
            .query(CosMxMasterTableTissue)
            .order_by(
                CosMxMasterTableTissue.tissue_id.desc()
            )
            .all()
        )
        return results
    except Exception as e:
        raise ValueError(
            "Failed to get tissue list, error: "
            + str(e)
        )

class CosMxMasterTableSlideView(ModelView):
    datamodel = SQLAInterface(CosMxMasterTableSlide)
    label_columns = {
        "slide_name": "Slide name",
        "project_name": "Project name",
        "run_name": "Run name",
        "collaborator": "Collaborator name",
        "collaborator_pi": "PI name",
        "assay_type": "Assay type",
        "panel": "Panel name",
        "tissue": "Tissue name",
        "condition": "Tissue condition",
        "ffpe_ff": "FFPE or FF",
        "tissue_per_slide": "Tissue per slide",
        "true_view_applied": "True view applied",
        "pre_bleaching_profile": "Pre bleaching profile",
        "cell_segmentation_profile": "Cell segmentation profile",
        "no_fov_count": "No fov count",
        "smi": "SMI",
        "url_link": "AtoMx URL",
        "atomx_url": "AtoMx SIP",
        "scan_date": "Scan date",
        "slide_status": "Slide QC status",
        "atomx_status": "AtoMx status"
    }
    list_columns = [
        "slide_name",
        "project_name",
        "assay_type",
        "scan_date",
        "tissue",
        "slide_status",
        "atomx_status"
    ]
    show_columns = [
        "slide_name",
        "project_name",
        "run_name",
        "assay_type",
        "collaborator",
        "collaborator_pi",
        "panel",
        "tissue",
        "condition",
        "ffpe_ff",
        "tissue_per_slide",
        "true_view_applied",
        "pre_bleaching_profile",
        "cell_segmentation_profile",
        "no_fov_count",
        "smi",
        "scan_date",
        "slide_status",
        "atomx_status",
        "atomx_url"
    ]
    add_columns = [
        "slide_name",
        "project_name",
        "run_name",
        "assay_type",
        "collaborator",
        "collaborator_pi",
        "panel",
        "tissue",
        "condition",
        "ffpe_ff",
        "tissue_per_slide",
        "true_view_applied",
        "pre_bleaching_profile",
        "cell_segmentation_profile",
        "no_fov_count",
        "smi",
        "scan_date",
        "url_link"
    ]
    edit_columns = [
        "slide_name",
        "project_name",
        "run_name",
        "assay_type",
        "collaborator",
        "collaborator_pi",
        "panel",
        "tissue",
        "condition",
        "ffpe_ff",
        "tissue_per_slide",
        "true_view_applied",
        "pre_bleaching_profile",
        "cell_segmentation_profile",
        "no_fov_count",
        "smi",
        "scan_date",
        "slide_status",
        "atomx_status",
        "url_link"
    ]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"
    ]
    base_order = ("slide_id", "desc")
    add_form_extra_fields = {
        "collaborator": QuerySelectField(
            "CosMxMasterTableUser",
            query_factory=user_query,
            widget=Select2Widget()
        ),
        "collaborator_pi": QuerySelectField(
            "CosMxMasterTableUser",
            query_factory=user_query,
            widget=Select2Widget()
        ),
        "panel": QuerySelectField(
            "CosMxMasterTablePanel",
            query_factory=panel_query,
            widget=Select2Widget()
        ),
        "tissue": QuerySelectField(
            "CosMxMasterTabletissue",
            query_factory=tissue_query,
            widget=Select2Widget()
        ),
    }
    edit_form_extra_fields = {
        "collaborator": QuerySelectField(
            "CosMxMasterTableUser",
            query_factory=user_query,
            widget=Select2Widget()
        ),
        "collaborator_pi": QuerySelectField(
            "CosMxMasterTableUser",
            query_factory=user_query,
            widget=Select2Widget()
        ),
        "panel": QuerySelectField(
            "CosMxMasterTablePanel",
            query_factory=panel_query,
            widget=Select2Widget()
        ),
        "tissue": QuerySelectField(
            "CosMxMasterTabletissue",
            query_factory=tissue_query,
            widget=Select2Widget()
        ),
    }