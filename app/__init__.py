import os
import logging
from flask import Flask, request
from flask_appbuilder import AppBuilder, SQLA
from .index import CustomIndexView
from celery import Celery
from flask_caching import Cache
from flask_migrate import Migrate

"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
migrate = Migrate(app, db)
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
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

## CACHING
cache_config = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_REDIS_URL": app.config['CACHE_REDIS_URL']
}

test_cache_config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

env_name = os.environ.get('ENV_NAME')
if 'TESTING' in app.config and \
   app.config.get('TESTING') is not None and \
   app.config.get('TESTING'):
  app.config.from_mapping(test_cache_config)
  cache = Cache(app)
else:
  app.config.from_mapping(cache_config)
  cache = Cache(app)

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
