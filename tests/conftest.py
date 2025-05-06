import pytest
from app import app, appbuilder

# pytest_plugins = ("celery.contrib.pytest", )

@pytest.fixture(scope="function")
def db():
    from app import db
    db.drop_all()
    db.create_all()
    yield db

@pytest.fixture(scope="function")
def test_client(db):
    app.config.update({
        "TESTING": True,
        "CSRF_ENABLED": False,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False
    })
    #db.create_all()
    admin_role = \
        app.appbuilder.sm.find_role("Admin")
    if admin_role is None:
        admin_role = app.appbuilder.sm.add_role("Admin")
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_show",
                "HomeView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "HomeView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_admin_home",
                "HomeView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_general",
                "HomeView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "HomeView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "IlluminaInteropDataView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "PreDeMultiplexingDataView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "RawSeqrunView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "trigger_pre_demultiplexing",
                "RawSeqrunView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "RawMetadataValidationView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "RawMetadataSubmitView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "ProjectIndexView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "SampleIndexView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "RawAnalysisView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "RDSProjectBackupView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "AnalysisView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "ProjectView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "UserView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "SeqrunView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "SampleSheetView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "SampleProjectView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "ProjectCleanupPendingView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_list",
                "ProjectCleanupFinishedView"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_get", "api"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_post", "api"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_get_project_cleanup_data", "ProjectCleanupApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_user_notified", "ProjectCleanupApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_db_cleanup_finished", "ProjectCleanupApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_add_project_cleanup_data", "ProjectCleanupApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_search_new_analysis", "RawAnalysisApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_get_raw_analysis_data", "RawAnalysisApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_analysis_synched", "RawAnalysisApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_analysis_rejected", "RawAnalysisApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_search_metadata", "RawMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_add_raw_metadata", "RawMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_download_ready_metadata", "RawMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_ready_metadata_as_synced", "RawMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_download_ready_metadata", "RawCosMxMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_mark_ready_metadata_as_synced", "RawCosMxMetadataDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_add_new_seqrun", "RawSeqrunApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_search_run_samplesheet", "RawSeqrunApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_get_run_override_cycle", "RawSeqrunApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_get_samplesheet_id", "RawSeqrunApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_update_admin_view_data", "AdminHomeApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_submit_cleanup_job", "MetadataLoadApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_add_report", "PreDeMultiplexingDataApi"))
        app.appbuilder.sm.add_permission_role(
            admin_role,
            app.appbuilder.sm.add_permission_view_menu(
                "can_add_report", "SeqrunInteropApi"))
    user = \
        app.appbuilder.sm.find_user(email="admin@fab.org")
    if user is None:
        app.appbuilder.sm.add_user(
        "admin",
        "admin",
        "user",
        "admin@fab.org",
        [admin_role],
        "password")
    with app.test_client() as testing_client:
        with app.app_context():
            # db.init_app(app)
            yield testing_client
