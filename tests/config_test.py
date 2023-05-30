import os

TESTING = True
CSRF_ENABLED = False
SECRET_KEY = "thisismyscretkey"
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = False
AUTH_ROLE_ADMIN = "Admin"
AUTH_USER_REGISTRATION_ROLE = "Admin"
REPORT_UPLOAD_PATH = "/tmp"
SQLALCHEMY_DATABASE_URI = \
    os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///" + '/tmp/app.db')
AUTH_ROLES_MAPPING = {
    "User": ["User"],
    "Admin": ["admin"],
}