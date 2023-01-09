import pytest
from app import db, app, appbuilder

@pytest.fixture(scope="module")
def test_client():
    app.config.update({
        "TESTING": True,
        "CSRF_ENABLED": False,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "AUTH_USER_REGISTRATION_ROLE": "Admin",
    })
    db.create_all()
    all_roles = app.appbuilder.sm.get_all_roles()
    admin_role = app.appbuilder.sm.add_role("Admin")
    admin_role_2 = app.appbuilder.sm.add_role("Admin1")
    app.appbuilder.sm.add_permission_role(
        admin_role_2,
        app.appbuilder.sm.add_permission_view_menu(
            "can_show",
            "HomeView"))
    app.appbuilder.sm.add_permission_role(
        admin_role_2,
        app.appbuilder.sm.add_permission_view_menu(
            "can_list",
            "HomeView"))
    app.appbuilder.sm.add_permission_role(
        admin_role_2,
        app.appbuilder.sm.add_permission_view_menu(
            "can_admin_home",
            "HomeView"))
    app.appbuilder.sm.add_permission_role(
        admin_role_2,
        app.appbuilder.sm.add_permission_view_menu(
            "can_general",
            "HomeView"))
    app.appbuilder.sm.add_permission_role(
        admin_role_2,
        app.appbuilder.sm.add_permission_view_menu(
            "can_list",
            "HomeView"))
    role_admin = \
        app.appbuilder.sm.find_role("Admin1")
    # admin_permissions = \
    #     app.appbuilder.sm.get_role_permissions(admin_role)
    # print(admin_permissions)
    # assert role_admin is None
    user = \
        app.appbuilder.sm.find_user(email="admin1@fab.org")
    if user is None:
        app.appbuilder.sm.add_user(
        "admin1",
        "admin1",
        "use1r",
        "admin1@fab.org",
        [role_admin],
        "password")
    with app.test_client() as testing_client:
        with app.app_context():
            db.init_app(app)
            yield testing_client
