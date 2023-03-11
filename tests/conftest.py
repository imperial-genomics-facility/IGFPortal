import pytest
from app import app, appbuilder

# pytest_plugins = ("celery.contrib.pytest", )

@pytest.fixture(scope="module")
def db():
    from app import db
    db.drop_all()
    db.create_all()
    yield db

@pytest.fixture(scope="module")
def test_client(db):
    db.drop_all()
    app.config.update({
        "TESTING": True,
        "CSRF_ENABLED": False,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False
    })
    db.create_all()
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
            db.init_app(app)
            yield testing_client
