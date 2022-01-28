import datetime, json
from flask import Markup, url_for
from flask_appbuilder import Model
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, Enum, TIMESTAMP, TEXT, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy import UnicodeText
from sqlalchemy.types import TypeDecorator


"""
Custom JSON data type for DB
"""
class JSONType(TypeDecorator):
  '''
  JSON datatype class for assigning dialect specific datatype
  It will assign JSON datatype for mysql tables and unicodetext for sqlite
  '''
  impl = UnicodeText

  def load_dialect_impl(self, dialect):
    if dialect.name == 'mysql':
      from sqlalchemy.dialects.mysql import JSON
      return dialect.type_descriptor(JSON())
    elif dialect.name == 'postgresql':
      from sqlalchemy.dialects.postgresql import JSON
      return dialect.type_descriptor(JSON())
    else:
      return dialect.type_descriptor(self.impl)

  def process_bind_param(self, value, dialect):
    if dialect.name == 'mysql' or \
       dialect.name == 'postgresql':
      return value
    if value is not None:
      value = json.dumps(value)
      return value

  def process_result_value(self, value, dialect):
    if dialect.name == 'mysql' or \
       dialect.name == 'postgresql':
      return value
    if value is not None:
      value = json.loads(value)
      return value



"""
InterOp data
"""
class IlluminaInteropData(Model):
    __tablename__ = 'illumina_interop_data'
    __table_args__ = (
        UniqueConstraint('run_name'),
        { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
    run_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
    run_name = Column(String(50), nullable=False)
    table_data = Column(TEXT())
    flowcell_data = Column(TEXT())
    intensity_data = Column(TEXT())
    cluster_count_data = Column(TEXT())
    density_data = Column(TEXT())
    qscore_bins_data = Column(TEXT())
    qscore_cycles_data = Column(TEXT())
    occupied_pass_filter = Column(TEXT())
    date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
    def __repr__(self):
        return self.run_name

    def seqrun(self):
        return Markup('<a href="'+url_for('IlluminaInteropDataView.get_seqrun',id=self.run_id)+'">'+self.run_name+'</a>')

"""
Pre de-multiplexing data
"""

class PreDeMultiplexingData(Model):
    __tablename__ = 'pre_demultiplexing_data'
    __table_args__ = (
        UniqueConstraint('run_name', 'samplesheet_tag'),
        { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
    demult_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
    run_name = Column(String(50), nullable=False)
    samplesheet_tag = Column(String(50), nullable=False)
    flowcell_cluster_plot = Column(TEXT())
    project_summary_table = Column(TEXT())
    project_summary_plot = Column(TEXT())
    sample_table = Column(TEXT())
    sample_plot= Column(TEXT())
    undetermined_table = Column(TEXT())
    undetermined_plot = Column(TEXT())
    date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
    def __repr__(self):
        return self.run_name
    def report(self):
        return Markup('<a href="'+url_for('PreDeMultiplexingDataView.get_report', id=self.demult_id)+'">report</a>')

class AdminHomeData(Model):
	__tablename__ = 'admin_home_data'
	__table_args__ = (
    UniqueConstraint('admin_data_id'),
    UniqueConstraint('admin_data_tag'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })
	admin_data_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
	admin_data_tag = Column(String(50), nullable=False)
	recent_finished_runs = Column(INTEGER, nullable=False)
	recent_finished_analysis = Column(INTEGER, nullable=False)
	ongoing_runs = Column(INTEGER, nullable=False)
	ongoing_analysis = Column(INTEGER, nullable=False)
	sequence_bases_plot = Column(TEXT())
	sequence_counts_plot = Column(TEXT())
	storage_stat_plot = Column(TEXT())
	def __repr__(self):
		return self.admin_data_tag

"""
  SampleSheet
"""
class SampleSheetModel(Model):
	__tablename__ = 'samplesheet'
	__table_args__ = (
		UniqueConstraint('samplesheet_tag'),
		{ 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
	samplesheet_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
	samplesheet_tag = Column(String(20), nullable=False)
	csv_data = Column(TEXT(), nullable=False)
	status = Column(Enum("PASS", "FAILED", "UNKNOWN"), nullable=False, server_default='UNKNOWN')
	report = Column(TEXT())
	validation_time = Column(TIMESTAMP())
	update_time = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
	def __repr__(self):
		return self.samplesheet_tag