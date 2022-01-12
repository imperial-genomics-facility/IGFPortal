from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget
from flask_appbuilder.forms import DynamicForm
from wtforms.fields import StringField,SubmitField,IntegerField,RadioField,DecimalField
from wtforms.validators import DataRequired,InputRequired,NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from . import appbuilder, db
from .models import IlluminaInteropData

def run_list_query():
  return db.session.query(IlluminaInteropData).limit(20)

class SeqrunInteropForm(DynamicForm):
	run_name = \
		QuerySelectField(
			query_factory=run_list_query,
			get_label='run_name',
			widget=Select2Widget(),
			id="run_name")