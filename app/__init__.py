import logging

from flask import Flask, request
from flask_appbuilder import AppBuilder, SQLA
from .index import CustomIndexView
from celery import Celery

"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
appbuilder = AppBuilder(app, db.session, indexview=CustomIndexView)


"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""
## CELERY
celery = \
    Celery(
        app.name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

## GDPR
@app.context_processor
def inject_template_scope():
  injections = dict()

  def cookies_check():
    value = request.cookies.get('cookie_consent')
    return value == 'true'
  injections.update(cookies_check=cookies_check)
  return injections


from . import views
from . import apis
