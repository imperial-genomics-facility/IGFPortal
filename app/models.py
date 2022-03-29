import datetime, json
from flask import Markup, url_for
from flask_appbuilder import Model
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT
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

"""
  Admin home view
"""

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
	samplesheet_tag = Column(String(50), nullable=False)
	csv_data = Column(LONGTEXT(), nullable=False)
	status = Column(Enum("PASS", "FAILED", "UNKNOWN"), nullable=False, server_default='UNKNOWN')
	report = Column(TEXT())
	validation_time = Column(TIMESTAMP())
	update_time = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
	def __repr__(self):
		return self.samplesheet_tag

"""
  Raw metadata
"""

class RawMetadataModel(Model):
  __tablename__ = 'raw_metadata_entry'
  __table_args__ = (
    UniqueConstraint('metadata_tag'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })
  raw_metadata_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  metadata_tag = Column(String(80), nullable=False)
  raw_csv_data = Column(LONGTEXT())
  formatted_csv_data = Column(LONGTEXT(), nullable=False)
  report = Column(TEXT())
  status = Column(Enum("UNKNOWN", "FAILED", "VALIDATED", "REJECTED", "READY", "SYNCHED"), nullable=False, server_default='UNKNOWN')
  update_time = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  def __repr__(self):
    return self.metadata_tag

"""
  List of raw seqrun
"""
class RawSeqrun(Model):
  __tablename__ = 'raw_seqrun'
  __table_args__ = (
    UniqueConstraint('raw_seqrun_igf_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })
  raw_seqrun_id =  Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  raw_seqrun_igf_id = Column(String(80), nullable=False)
  status = Column(Enum("ACTIVE", "REJECTED", "PREDEMULT", "READY", "FINISHED"), nullable=False, server_default='ACTIVE')
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  samplesheet_id = Column(INTEGER(unsigned=True), ForeignKey("samplesheet.samplesheet_id", onupdate="NO ACTION", ondelete="NO ACTION"), nullable=True)
  samplesheet = relationship('SampleSheetModel')
  def __repr__(self):
    return self.raw_seqrun_igf_id

"""
  Raw analysis
"""

class RawAnalysis(Model):
  __tablename__ = 'raw_analysis'
  __table_args__ = (
    UniqueConstraint('analysis_tag'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
  raw_analysis_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  analysis_tag = Column(String(50), nullable=False)
  analysis_yaml = Column(TEXT(), nullable=False)
  status = Column(Enum("VALIDATED", "FAILED", "SYNCHED", "UNKNOWN"), nullable=False, server_default='UNKNOWN')
  report = Column(TEXT())
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  def __repr__(self):
    return self.analysis_tag
"""
  RDS project backup
"""
class RDSProject_backup(Model):
  __tablename__ = 'rds_project_backup'
  __table_args__ = (
    UniqueConstraint('project_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
  rds_backup_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  project_id =  Column(INTEGER(unsigned=True), ForeignKey("project.project_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
  project = relationship('Project')
  status = Column(Enum("PENDING", "FAILED", "FINISHED"), nullable=False, server_default='PENDING')
  rds_path = Column(TEXT(), nullable=False)
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  def __repr__(self):
    return self.project.project_igf_id

"""
  Metadata db
"""

class Project(Model):

  '''
  A table for loading project information

  :param project_id: An integer id for project table
  :param project_igf_id: A required string as project id specific to IGF team, allowed length 50
  :param project_name: An optional string as project name
  :param start_timestamp: An optional timestamp for project creation, default current timestamp
  :param description: An optional text column to document project description
  :param deliverable: An enum list to document project deliverable, default FASTQ,allowed entries are

    * FASTQ
    * ALIGNMENT
    * ANALYSIS

  :param status: An enum list for project status, default ACTIVE, allowed entries are

    * ACTIVE
    * FINISHED
    * WITHDRAWN
  '''
  __tablename__ = 'project'
  __table_args__ = (
     UniqueConstraint('project_igf_id'),
     { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  project_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  project_igf_id = Column(String(70), nullable=False)
  project_name = Column(String(40))
  start_timestamp = Column(TIMESTAMP(), nullable=True, server_default=current_timestamp())
  description = Column(TEXT())
  status = Column(Enum('ACTIVE', 'FINISHED', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  deliverable = Column(Enum('FASTQ', 'ALIGNMENT', 'ANALYSIS'), server_default='FASTQ')

  def __repr__(self):
    '''
    Display Project entry
    '''
    return  self.project_igf_id

class IgfUser(Model):

  '''
  A table for loading user information

  :param user_id: An integer id for user table
  :param user_igf_id: An optional string as user id specific to IGF team, allowed length 10
  :param name: A required string as user name, allowed length 30
  :param email_id: A required string as email id, allowed length 40
  :param username: A required string as IGF username, allowed length 20
  :param hpc_username: An optional string as Imperial College's HPC login name, allowed length 20
  :param twitter_user: An optional string as twitter user name, allowed length 20
  :param category: An optional enum list as user category, default NON_HPC_USER, allowed values are

    * HPC_USER
    * NON_HPC_USER
    * EXTERNAL

  :param status: An optional enum list as user status, default is ACTIVE, allowed values are

    * ACTIVE
    * BLOCKED
    * WITHDRAWN

  :param date_created: An optional timestamp, default current timestamp
  :param password: An optional string field to store encrypted password
  :param encryption_salt: An optional string field to store encryption salt
  :param ht_password: An optional field to store password for htaccess
  '''
  __tablename__ = 'user'
  __table_args__ = (
    UniqueConstraint('name'),
    UniqueConstraint('username'),
    UniqueConstraint('email_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  user_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  user_igf_id = Column(String(10))
  name = Column(String(30), nullable=False)
  email_id = Column(String(40), nullable=False)
  username = Column(String(20))
  hpc_username = Column(String(20))
  twitter_user = Column(String(20))
  orcid_id = Column(String(50))
  category = Column(Enum('HPC_USER','NON_HPC_USER','EXTERNAL'), nullable=False, server_default='NON_HPC_USER')
  status = Column(Enum('ACTIVE', 'BLOCKED', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  password = Column(String(129))
  encryption_salt = Column(String(129))
  ht_password = Column(String(40))

  def __repr__(self):
    '''
    Display User entry
    '''
    return self.name


class ProjectUser(Model):

  '''
  A table for linking users to the projects

  :param project_user_id: An integer id for project_user table
  :param project_id: An integer id for project table (foreign key)
  :param user_id: An integer id for user table (foreign key)
  :param data_authority: An optional enum value to denote primary user for the project,
                          allowed value T
  '''
  __tablename__ = 'project_user'
  __table_args__ = (
    UniqueConstraint('project_id','data_authority'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  project_user_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  project_id = Column(INTEGER(unsigned=True), ForeignKey("project.project_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  project = relationship('Project')
  user_id = Column(INTEGER(unsigned=True), ForeignKey("user.user_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  user = relationship('IgfUser')
  data_authority = Column(Enum('T'))

  def __repr__(self):
    '''
    Display ProjectUser entry
    '''
    return self.project_user_id

class Sample(Model):

  '''
  A table for loading sample information

  :param sample_id: An integer id for sample table
  :param sample_igf_id: A required string as sample id specific to IGF team, allowed length 20
  :param sample_submitter_id: An optional string as sample name from user, allowed value 40
  :param taxon_id: An optional integer NCBI taxonomy information for sample
  :param scientific_name: An optional string as scientific name of the species
  :param species_name: An optional string as the species name (genome build code) information
  :param donor_anonymized_id: An optional string as anonymous donor name
  :param description: An optional string as sample description
  :param phenotype: An optional string as sample phenotype information
  :param sex: An optional enum list to specify sample sex, default UNKNOWN, allowed values are

    * FEMALE
    * MALE
    * MIXED
    * UNKNOWN

  :param status: An optional enum list to specify sample status, default ACTIVE, allowed values are

    * ACTIVE
    * FAILED
    * WITHDRAWS

  :param biomaterial_type: An optional enum list as sample biomaterial type, default UNKNOWN, allowed values are

    * PRIMARY_TISSUE
    * PRIMARY_CELL
    * PRIMARY_CELL_CULTURE
    * CELL_LINE
    * SINGLE_NUCLEI
    * UNKNOWN

  :param cell_type: An optional string to specify sample cell_type information, if biomaterial_type is PRIMARY_CELL or PRIMARY_CELL_CULTURE
  :param tissue_type: An optional string to specify sample tissue information, if biomaterial_type is PRIMARY_TISSUE
  :param cell_line: An optional string to specify cell line information ,if biomaterial_type is CELL_LINE
  :param date_created: An optional timestamp column to specify entry creation date, default current timestamp
  :param project_id:  An integer id for project table (foreign key)
  '''
  __tablename__ = 'sample'
  __table_args__ = (
    UniqueConstraint('sample_igf_id'),
    { 'mysql_engine':'InnoDB','mysql_charset':'utf8' })

  sample_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  sample_igf_id = Column(String(20), nullable=False)
  sample_submitter_id = Column(String(40))
  taxon_id = Column(INTEGER(unsigned=True))
  scientific_name = Column(String(50))
  species_name = Column(String(50))
  donor_anonymized_id = Column(String(10))
  description = Column(String(50))
  phenotype = Column(String(45))
  sex = Column(Enum('FEMALE', 'MALE', 'MIXED', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  status = Column(Enum('ACTIVE', 'FAILED', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  biomaterial_type = Column(Enum('PRIMARY_TISSUE', 'PRIMARY_CELL', 'PRIMARY_CELL_CULTURE', 'CELL_LINE', 'SINGLE_NUCLEI', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  cell_type = Column(String(50))
  tissue_type = Column(String(50))
  cell_line = Column(String(50))
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp())
  project_id = Column(INTEGER(unsigned=True), ForeignKey('project.project_id', onupdate="CASCADE", ondelete="SET NULL"))
  project = relationship('Project')

  def __repr__(self):
    '''
    Display Sample entry
    '''
    return self.sample_igf_id


class Platform(Model):

  '''
  A table for loading sequencing platform information

  :param platform_id: An integer id for platform table
  :param platform_igf_id: A required string as platform id specific to IGF team, allowed length 10
  :param model_name: A required enum list to specify platform model, allowed values are

    * HISEQ2500
    * HISEQ4000
    * MISEQ
    * NEXTSEQ
    * NOVASEQ6000
    * NANOPORE_MINION
    * DNBSEQ-G400
    * DNBSEQ-G50
    * DNBSEQ-T7

  :param vendor_name: A required enum list to specify vendor's name, allowed values are

    * ILLUMINA
    * NANOPORE
    * MGI

  :param software_name: A required enum list for specifying platform software, allowed values are

    * RTA
    * UNKNOWN

  :param software_version: A optional software version number, default is UNKNOWN
  :param date_created: An optional timestamp column to record entry creation time, default current timestamp
  '''
  __tablename__ = 'platform'
  __table_args__ = (
    UniqueConstraint('platform_igf_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })

  platform_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  platform_igf_id = Column(String(10), nullable=False)
  model_name = Column(Enum('HISEQ2500','HISEQ4000','MISEQ','NEXTSEQ','NOVASEQ6000','NANOPORE_MINION','DNBSEQ-G400', 'DNBSEQ-G50', 'DNBSEQ-T7'), nullable=False)
  vendor_name = Column(Enum('ILLUMINA','NANOPORE', 'MGI'), nullable=False)
  software_name = Column(Enum('RTA','UNKNOWN'), nullable=False)
  software_version = Column(String(20), nullable=False, server_default='UNKNOWN')
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now )

  def __repr__(self):
    '''
    Display Platform entry
    '''
    return self.platform_igf_id


class Flowcell_barcode_rule(Model):

  '''
  A table for loading flowcell specific barcode rules information

  :param flowcell_rule_id: An integer id for flowcell_barcode_rule table
  :param platform_id: An integer id for platform table (foreign key)
  :param flowcell_type: A required string as flowcell type name, allowed length 50
  :param index_1: An optional enum list as index_1 specific rule, default UNKNOWN, allowed values are

    * NO_CHANGE
    * REVCOMP
    * UNKNOWN

  :param index_2: An optional enum list as index_2 specific rule, default UNKNOWN, allowed values are

    * NO_CHANGE
    * REVCOMP
    * UNKNOWN
  '''
  __tablename__ = 'flowcell_barcode_rule'
  __table_args__ = (
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })

  flowcell_rule_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  platform_id = Column(INTEGER(unsigned=True), ForeignKey('platform.platform_id', onupdate="CASCADE", ondelete="SET NULL"))
  platform = relationship('Platform')
  flowcell_type = Column(String(50), nullable=False)
  index_1 = Column(Enum('NO_CHANGE','REVCOMP','UNKNOWN'), nullable=False, server_default='UNKNOWN')
  index_2 = Column(Enum('NO_CHANGE','REVCOMP','UNKNOWN'), nullable=False, server_default='UNKNOWN')

  def __repr__(self):
    '''
    Display Flowcell_barcode_rule entry
    '''
    return self.flowcell_rule_id

class Seqrun(Model):

  '''
  A table for loading sequencing run information

  :param seqrun_id: An integer id for seqrun table
  :param seqrun_igf_id: A required string as seqrun id specific to IGF team, allowed length 50
  :param reject_run: An optional enum list to specify rejected run information ,default N,
                      allowed values Y and N
  :param date_created: An optional timestamp column to record entry creation time, default current timestamp
  :param flowcell_id: A required string column for storing flowcell_id information, allowed length 20
  :param platform_id: An integer platform id (foreign key)
  '''
  __tablename__ = 'seqrun'
  __table_args__ = (
    UniqueConstraint('seqrun_igf_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  seqrun_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  seqrun_igf_id = Column(String(50), nullable=False)
  reject_run = Column(Enum('Y','N'), nullable=False, server_default='N')
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  flowcell_id = Column(String(20), nullable=False)
  platform_id = Column(INTEGER(unsigned=True), ForeignKey('platform.platform_id', onupdate="CASCADE", ondelete="SET NULL"))
  platform = relationship('Platform')

  def __repr__(self):
    '''
    Display Seqrun entry
    '''
    return self.seqrun_id

class Seqrun_stats(Model):

  '''
  A table for loading sequencing stats information

  :param seqrun_stats_id: An integer id for seqrun_stats table
  :param seqrun_id: An integer seqrun id (foreign key)
  :param lane_number: A required enum list for specifying lane information,
                       allowed values are 1, 2, 3, 4, 5, 6, 7 and 8
  :param bases_mask: An optional string field for storing bases mask information
  :param undetermined_barcodes: An optional json field to store barcode info for undetermined samples
  :param known_barcodes: An optional json field to store barcode info for known samples
  :param undetermined_fastqc: An optional json field to store qc info for undetermined samples
  '''
  __tablename__  = 'seqrun_stats'
  __table_args__ = (
    UniqueConstraint('seqrun_id', 'lane_number'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  seqrun_stats_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  seqrun_id = Column(INTEGER(unsigned=True), ForeignKey('seqrun.seqrun_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  seqrun = relationship('Seqrun')
  lane_number = Column(Enum('1', '2', '3', '4', '5', '6', '7', '8'), nullable=False)
  bases_mask = Column(String(20))
  undetermined_barcodes = Column(JSONType)
  known_barcodes = Column(JSONType)
  undetermined_fastqc = Column(JSONType)

  def __repr__(self):
    '''
    Display Seqrun_stats entry
    '''
    return self.seqrun_stats_id

class Experiment(Model):

  '''
  A table for loading experiment (unique combination of sample, library and platform) information.

  :param experiment_id: An integer id for experiment table
  :param experiment_igf_id: A required string as experiment id specific to IGF team, allowed length 40
  :param project_id: A required integer id from project table (foreign key)
  :param sample_id: A required integer id from sample table (foreign key)
  :param library_name: A required string to specify library name, allowed length 50
  :param library_source: An optional enum list to specify library source information, default is UNKNOWN, allowed values are

    * GENOMIC
    * TRANSCRIPTOMIC
    * GENOMIC_SINGLE_CELL
    * TRANSCRIPTOMIC_SINGLE_CELL
    * METAGENOMIC
    * METATRANSCRIPTOMIC
    * SYNTHETIC
    * VIRAL_RNA
    * UNKNOWN

  :param library_strategy: An optional enum list to specify library strategy information, default is UNKNOWN, allowed values are

    * WGS
    * WXS
    * WGA
    * RNA-SEQ
    * CHIP-SEQ
    * ATAC-SEQ
    * MIRNA-SEQ
    * NCRNA-SEQ
    * FL-CDNA
    * EST
    * HI-C
    * DNASE-SEQ
    * WCS
    * RAD-SEQ
    * CLONE
    * POOLCLONE
    * AMPLICON
    * CLONEEND
    * FINISHING
    * MNASE-SEQ
    * DNASE-HYPERSENSITIVITY
    * BISULFITE-SEQ
    * CTS
    * MRE-SEQ
    * MEDIP-SEQ
    * MBD-SEQ
    * TN-SEQ
    * VALIDATION
    * FAIRE-SEQ
    * SELEX
    * RIP-SEQ
    * CHIA-PET
    * SYNTHETIC-LONG-READ
    * TARGETED-CAPTURE
    * TETHERED
    * NOME-SEQ
    * CHIRP SEQ
    * 4-C-SEQ
    * 5-C-SEQ
    * UNKNOWN

  :param experiment_type: An optional enum list as experiment type information, default is UNKNOWN, allowed values are

    * POLYA-RNA
    * POLYA-RNA-3P
    * TOTAL-RNA
    * SMALL-RNA
    * WGS
    * WGA
    * WXS
    * WXS-UTR
    * RIBOSOME-PROFILING
    * RIBODEPLETION
    * 16S
    * NCRNA-SEQ
    * FL-CDNA
    * EST
    * HI-C
    * DNASE-SEQ
    * WCS
    * RAD-SEQ
    * CLONE
    * POOLCLONE
    * AMPLICON
    * CLONEEND
    * FINISHING
    * DNASE-HYPERSENSITIVITY
    * RRBS-SEQ
    * WGBS
    * CTS
    * MRE-SEQ
    * MEDIP-SEQ
    * MBD-SEQ
    * TN-SEQ
    * VALIDATION
    * FAIRE-SEQ
    * SELEX
    * RIP-SEQ
    * CHIA-PET
    * SYNTHETIC-LONG-READ
    * TARGETED-CAPTURE
    * TETHERED
    * NOME-SEQ
    * CHIRP-SEQ
    * 4-C-SEQ
    * 5-C-SEQ
    * METAGENOMIC
    * METATRANSCRIPTOMIC
    * TF
    * H3K27ME3
    * H3K27AC
    * H3K9ME3
    * H3K36ME3
    * H3F3A
    * H3K4ME1
    * H3K79ME2
    * H3K79ME3
    * H3K9ME1
    * H3K9ME2
    * H4K20ME1
    * H2AFZ
    * H3AC
    * H3K4ME2
    * H3K4ME3
    * H3K9AC
    * HISTONE-NARROW
    * HISTONE-BROAD
    * CHIP-INPUT
    * ATAC-SEQ
    * TENX-TRANSCRIPTOME-3P
    * TENX-TRANSCRIPTOME-5P
    * DROP-SEQ-TRANSCRIPTOME
    * UNKNOWN

  :param library_layout: An optional enum list to specify library layout, default is UNONWN, allowed values are

    * SINGLE
    * PAIRED
    * UNKNOWN

  :param status: An optional enum list to specify experiment status, default is ACTIVE, allowed values are

    * ACTIVE
    * FAILED
    * WITHDRAWN

  :param date_created: An optional timestamp column to record entry creation or modification time, default current timestamp
  :param platform_name: An optional enum list to specify platform model, default is UNKNOWN, allowed values are

    * HISEQ250
    * HISEQ4000
    * MISEQ
    * NEXTSEQ
    * NOVASEQ6000
    * NANOPORE_MINION
    * DNBSEQ-G400
    * DNBSEQ-G50
    * DNBSEQ-T7
    * UNKNOWN
  '''
  __tablename__ = 'experiment'
  __table_args__ = (
    UniqueConstraint('sample_id', 'library_name', 'platform_name'),
    UniqueConstraint('experiment_igf_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  experiment_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  experiment_igf_id = Column(String(40), nullable=False)
  project_id = Column(INTEGER(unsigned=True), ForeignKey('project.project_id', onupdate="CASCADE", ondelete="SET NULL"))
  project = relationship('Project')
  sample_id = Column(INTEGER(unsigned=True), ForeignKey('sample.sample_id', onupdate="CASCADE", ondelete="SET NULL"))
  sample = relationship('Sample')
  library_name = Column(String(50), nullable=False)
  library_source = Column(Enum('GENOMIC', 'TRANSCRIPTOMIC' ,'GENOMIC_SINGLE_CELL', 'METAGENOMIC', 'METATRANSCRIPTOMIC',
                               'TRANSCRIPTOMIC_SINGLE_CELL', 'SYNTHETIC', 'VIRAL_RNA', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  library_strategy = Column(Enum('WGS', 'WXS', 'WGA', 'RNA-SEQ', 'CHIP-SEQ', 'ATAC-SEQ', 'MIRNA-SEQ', 'NCRNA-SEQ',
                                 'FL-CDNA', 'EST', 'HI-C', 'DNASE-SEQ', 'WCS', 'RAD-SEQ', 'CLONE', 'POOLCLONE',
                                 'AMPLICON', 'CLONEEND', 'FINISHING', 'MNASE-SEQ', 'DNASE-HYPERSENSITIVITY', 'BISULFITE-SEQ',
                                 'CTS', 'MRE-SEQ', 'MEDIP-SEQ', 'MBD-SEQ', 'TN-SEQ', 'VALIDATION', 'FAIRE-SEQ', 'SELEX',
                                 'RIP-SEQ', 'CHIA-PET', 'SYNTHETIC-LONG-READ', 'TARGETED-CAPTURE', 'TETHERED', 'NOME-SEQ',
                                 'CHIRP SEQ', '4-C-SEQ', '5-C-SEQ', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  experiment_type = Column(Enum('POLYA-RNA', 'POLYA-RNA-3P', 'TOTAL-RNA', 'SMALL-RNA', 'WGS', 'WGA', 'WXS', 'WXS-UTR',
                                'RIBOSOME-PROFILING', 'RIBODEPLETION', '16S', 'NCRNA-SEQ', 'FL-CDNA', 'EST', 'HI-C',
                                'DNASE-SEQ', 'WCS', 'RAD-SEQ', 'CLONE', 'POOLCLONE', 'AMPLICON', 'CLONEEND', 'FINISHING',
                                'DNASE-HYPERSENSITIVITY', 'RRBS-SEQ', 'WGBS', 'CTS', 'MRE-SEQ', 'MEDIP-SEQ', 'MBD-SEQ',
                                'TN-SEQ', 'VALIDATION', 'FAIRE-SEQ', 'SELEX', 'RIP-SEQ', 'CHIA-PET', 'SYNTHETIC-LONG-READ',
                                'TARGETED-CAPTURE', 'TETHERED', 'NOME-SEQ', 'CHIRP-SEQ', '4-C-SEQ', '5-C-SEQ',
                                'METAGENOMIC', 'METATRANSCRIPTOMIC', 'TF', 'H3K27ME3', 'H3K27AC', 'H3K9ME3',
                                'H3K36ME3', 'H3F3A', 'H3K4ME1', 'H3K79ME2', 'H3K79ME3', 'H3K9ME1', 'H3K9ME2',
                                'H4K20ME1', 'H2AFZ', 'H3AC', 'H3K4ME2', 'H3K4ME3', 'H3K9AC', 'HISTONE-NARROW',
                                'HISTONE-BROAD', 'CHIP-INPUT', 'ATAC-SEQ', 'TENX-TRANSCRIPTOME-3P', 'TENX-TRANSCRIPTOME-5P',
                                'DROP-SEQ-TRANSCRIPTOME', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  library_layout = Column(Enum('SINGLE', 'PAIRED', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  status = Column(Enum('ACTIVE', 'FAILED', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  platform_name = Column(Enum('HISEQ2500', 'HISEQ4000', 'MISEQ', 'NEXTSEQ', 'NANOPORE_MINION', 'NOVASEQ6000',
                              'DNBSEQ-G400', 'DNBSEQ-G50', 'DNBSEQ-T7',
                              'UNKNOWN'), nullable=False, server_default='UNKNOWN')

  def __repr__(self):
    '''
    Display Experiment entry
    '''
    return self.experiment_igf_id

class Run(Model):

  '''
  A table for loading run (unique combination of experiment, sequencing flowcell and lane) information

  :param run_id: An integer id for run table
  :param run_igf_id: A required string as run id specific to IGF team, allowed length 70
  :param experiment_id: A required integer id from experiment table (foreign key)
  :param seqrun_id: A required integer id from seqrun table (foreign key)
  :param status: An optional enum list to specify experiment status, default is ACTIVE, allowed values are 

    * ACTIVE
    * FAILED
    * WITHDRAWN

  :param lane_number: A required enum list for specifying lane information,
                       allowed values 1, 2, 3, 4, 5, 6, 7 and 8
  :param date_created: An optional timestamp column to record entry creation time, default current timestamp
  '''
  __tablename__ = 'run'
  __table_args__ = (
    UniqueConstraint('run_igf_id'),
    UniqueConstraint('experiment_id','seqrun_id','lane_number'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  run_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  run_igf_id = Column(String(70), nullable=False)
  experiment_id = Column(INTEGER(unsigned=True), ForeignKey('experiment.experiment_id', onupdate="CASCADE", ondelete="SET NULL"))
  experiment = relationship('Experiment')
  seqrun_id = Column(INTEGER(unsigned=True), ForeignKey('seqrun.seqrun_id', onupdate="CASCADE", ondelete="SET NULL"))
  seqrun = relationship('Seqrun')
  status = Column(Enum('ACTIVE', 'FAILED', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  lane_number = Column(Enum('1', '2', '3', '4', '5', '6', '7', '8'), nullable=False)
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp())

  def __repr__(self):
    '''
    Display Run entry
    '''
    return self.run_igf_id

class Analysis(Model):

  '''
  A table for loading analysis design information

  :param analysis_id: An integer id for analysis table
  :param project_id: A required integer id from project table (foreign key)
  :param analysis_type: An optional string field of 120chrs to specify analysis type
  :param analysis_description: An optional json description for analysis
  '''
  __tablename__ = 'analysis'
  __table_args__ = (
    UniqueConstraint('analysis_name','project_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  analysis_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  project_id = Column(INTEGER(unsigned=True), ForeignKey('project.project_id', onupdate="CASCADE", ondelete="SET NULL"))
  project = relationship('Project')
  analysis_name = Column(String(120), nullable=False)
  analysis_type = Column(String(120), nullable=False)
  analysis_description = Column(JSONType)

  def __repr__(self):
    '''
    Display Analysis entry
    '''
    return self.analysis_name


class Collection(Model):

  '''
  A table for loading collection information

  :param collection_id: An integer id for collection table
  :param name: A required string to specify collection name, allowed length 70
  :param type: A required string to specify collection type, allowed length 50
  :param table: An optional enum list to specify collection table information, default unknown,
                 allowed values are sample, experiment, run, file, project, seqrun and unknown
  :param date_stamp: An optional timestamp column to record entry creation or modification time, default current timestamp
  '''
  __tablename__ = 'collection'
  __table_args__ = (
    UniqueConstraint('name','type'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  collection_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  name = Column(String(70), nullable=False)
  type = Column(String(50), nullable=False)
  table = Column(Enum('sample', 'experiment', 'run', 'file', 'project', 'seqrun', 'analysis', 'unknown'), nullable=False, server_default='unknown')
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)

  def __repr__(self):
    '''
    Display Collection entry
    '''
    return "{0}, {1}".format(self.name, self.type)


class File(Model):

  '''
  A table for loading file information

  :param file_id: An integer id for file table
  :param file_path: A required string to specify file path information, allowed length 500
  :param location: An optional enum list to specify storage location, default UNKNOWN, allowed values are

    * ORWELL
    * HPC_PROJECT
    * ELIOT
    * IRODS
    * UNKNOWN

  :param status: An optional enum list to specify experiment status, default is ACTIVE, allowed values are

    * ACTIVE
    * FAILED
    * WITHDRAWN

  :param md5: An optional string to specify file md5 value, allowed length 33
  :param size: An optional string to specify file size, allowed value 15
  :param date_created: An optional timestamp column to record file creation time, default current timestamp
  :param date_updated: An optional timestamp column to record file modification time, default current timestamp
  '''
  __tablename__ = 'file'
  __table_args__ = (
    UniqueConstraint('file_path'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  file_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  file_path = Column(String(500), nullable=False)
  location = Column(Enum('ORWELL', 'HPC_PROJECT', 'ELIOT', 'IRODS', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  status = Column(Enum('ACTIVE', 'WITHDRAWN'), nullable=False, server_default='ACTIVE')
  md5 = Column(String(33))
  size = Column(String(15))
  date_created = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp())
  date_updated = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now )

  def __repr__(self):
    '''
    Display File entry
    '''
    return self.file_path


class Collection_group(Model):

  '''
  A table for linking files to the collection entries

  :param collection_group_id: An integer id for collection_group table
  :param collection_id: A required integer id from collection table (foreign key)
  :param file_id: A required integer id from file table (foreign key)
  '''
  __tablename__ = 'collection_group'
  __table_args__ = (
    UniqueConstraint('collection_id','file_id'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  collection_group_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  collection_id = Column(INTEGER(unsigned=True), ForeignKey('collection.collection_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  collection = relationship('Collection')
  file_id = Column(INTEGER(unsigned=True), ForeignKey('file.file_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  file = relationship('File')

  def __repr__(self):
    '''
    Display Collection_group entry
    '''
    return self.collection_group_id


class Pipeline(Model):

  '''
  A table for loading pipeline information

  :param pipeline_id: An integer id for pipeline table
  :param pipeline_name: A required string to specify pipeline name, allowed length 50
  :param pipeline_db: A required string to specify pipeline database url, allowed length 200
  :param pipeline_init_conf: An optional json field to specify initial pipeline configuration
  :param pipeline_run_conf: An optional json field to specify modified pipeline configuration
  :param pipeline_type: An optional enum list to specify pipeline type, default EHIVE, allowed values are

    * EHIVE
    * UNKNOWN
    * AIRFLOW
    * NEXTFLOW

  :param is_active: An optional enum list to specify the status of pipeline, default Y
                    allowed values are Y and N
  :param date_stamp: An optional timestamp column to record file creation or modification time, default current timestamp
  '''
  __tablename__ = 'pipeline'
  __table_args__ = (
    UniqueConstraint('pipeline_name'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  pipeline_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  pipeline_name = Column(String(120), nullable=False)
  pipeline_db = Column(String(200), nullable=False)
  pipeline_init_conf = Column(JSONType)
  pipeline_run_conf = Column(JSONType)
  pipeline_type = Column(Enum('EHIVE', 'AIRFLOW', 'NEXTFLOW', 'UNKNOWN'), nullable=False, server_default='EHIVE')
  is_active = Column(Enum('Y', 'N'), nullable=False, server_default='Y')
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)
  #pipeline_seed = relationship('Pipeline_seed', backref='pipeline')

  def __repr__(self):
    '''
    Display Pipeline entry
    '''
    return self.pipeline_name


class Pipeline_seed(Model):

  '''
  A table for loading pipeline seed information

  :param pipeline_seed_id: An integer id for pipeline_seed table
  :param seed_id: A required integer id
  :param seed_table: An optional enum list to specify seed table information, default unknown,
                      allowed values project, sample, experiment, run, file, seqrun, collection and unknown
  :param pipeline_id: An integer id from pipeline table (foreign key)
  :param status: An optional enum list to specify the status of pipeline, default UNKNOWN,
                  allowed values are

    * SEEDED
    * RUNNING
    * FINISHED
    * FAILED
    * UNKNOWN

  :param date_stamp: An optional timestamp column to record file creation or modification time, default current timestamp
  '''
  __tablename__ = 'pipeline_seed'
  __table_args__ = (
    UniqueConstraint('pipeline_id','seed_id','seed_table'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })

  pipeline_seed_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  seed_id = Column(INTEGER(unsigned=True), nullable=False)
  seed_table = Column(Enum('project','sample','experiment','run','file','seqrun','analysis','collection','unknown'), nullable=False, server_default='unknown')
  pipeline_id = Column(INTEGER(unsigned=True), ForeignKey('pipeline.pipeline_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  pipeline = relationship('Pipeline')
  status = Column(Enum('SEEDED', 'RUNNING', 'FINISHED', 'FAILED', 'UNKNOWN'), nullable=False, server_default='UNKNOWN')
  date_stamp = Column(TIMESTAMP(), nullable=False, server_default=current_timestamp(), onupdate=datetime.datetime.now)

  def __repr__(self):
    '''
    Display Pipeline_seed entry
    '''
    return self.pipeline_seed_id


class Project_attribute(Model):

  '''
  A table for loading project attributes

  :param project_attribute_id: An integer id for project_attribute table
  :param attribute_name: An optional string attribute name, allowed length 50
  :param attribute_value: An optional string attribute value, allowed length 50
  :param project_id: An integer id from project table (foreign key)
  '''
  __tablename__ = 'project_attribute'
  __table_args__ = (
    UniqueConstraint('project_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  project_attribute_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(50))
  attribute_value = Column(String(50))
  project_id = Column(INTEGER(unsigned=True), ForeignKey('project.project_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  project =relationship('Project')

  def __repr__(self):
    '''
    Display Project_attribute entry
    '''
    return self.project_attribute_id

class Experiment_attribute(Model):

  '''
  A table for loading experiment attributes

  :param experiment_attribute_id: An integer id for experiment_attribute table
  :param attribute_name: An optional string attribute name, allowed length 30
  :param attribute_value: An optional string attribute value, allowed length 50
  :param experiment_id: An integer id from experiment table (foreign key)
  '''
  __tablename__ = 'experiment_attribute'
  __table_args__ = (
    UniqueConstraint('experiment_id', 'attribute_name', 'attribute_value'),
    {  'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  experiment_attribute_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(30))
  attribute_value = Column(String(50))
  experiment_id = Column(INTEGER(unsigned=True), ForeignKey('experiment.experiment_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  experiment = relationship('Experiment')

  def __repr__(self):
    '''
    Display Experiment_attribute entry
    '''
    return self.experiment_attribute_id

class Collection_attribute(Model):

  '''
  A table for loading collection attributes

  :param collection_attribute_id: An integer id for collection_attribute table
  :param attribute_name: An optional string attribute name, allowed length 200
  :param attribute_value: An optional string attribute value, allowed length 200
  :param collection_id: An integer id from collection table (foreign key)
  '''
  __tablename__ = 'collection_attribute'
  __table_args__ = (
    UniqueConstraint('collection_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  collection_attribute_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(200))
  attribute_value = Column(String(200))
  collection_id = Column(INTEGER(unsigned=True), ForeignKey('collection.collection_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  collection = relationship('Collection')

  def __repr__(self):
    '''
    Display Collection_attribute entry
    '''
    return self.collection_attribute_ids

class Sample_attribute(Model):

  '''
  A table for loading sample attributes

  :param sample_attribute_id: An integer id for sample_attribute table
  :param attribute_name: An optional string attribute name, allowed length 50
  :param attribute_value: An optional string attribute value, allowed length 50
  :param sample_id: An integer id from sample table (foreign key)
  '''
  __tablename__ = 'sample_attribute'
  __table_args__ = (
    UniqueConstraint('sample_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  sample_attribute_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(50))
  attribute_value = Column(String(50))
  sample_id = Column(INTEGER(unsigned=True), ForeignKey('sample.sample_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  sample = relationship('Sample')

  def __repr__(self):
    '''
    Display Sample_attribute entry
    '''
    return self.sample_attribute_id


class Seqrun_attribute(Model):

  '''
  A table for loading seqrun attributes

  :param seqrun_attribute_id: An integer id for seqrun_attribute table
  :param attribute_name: An optional string attribute name, allowed length 50
  :param attribute_value: An optional string attribute value, allowed length 100
  :param seqrun_id: An integer id from seqrun table (foreign key)
  '''
  __tablename__ = 'seqrun_attribute'
  __table_args__ = (
    UniqueConstraint('seqrun_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })
  seqrun_attribute_id  = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(50))
  attribute_value = Column(String(100))
  seqrun_id = Column(INTEGER(unsigned=True), ForeignKey('seqrun.seqrun_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  seqrun = relationship('Seqrun')

class Run_attribute(Model):

  '''
  A table for loading run attributes

  :param run_attribute_id: An integer id for run_attribute table
  :param attribute_name: An optional string attribute name, allowed length 30
  :param attribute_value: An optional string attribute value, allowed length 50
  :param run_id: An integer id from run table (foreign key)
  '''
  __tablename__ = 'run_attribute'
  __table_args__ = (
    UniqueConstraint('run_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8' })

  run_attribute_id  = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(30))
  attribute_value = Column(String(50))
  run_id = Column(INTEGER(unsigned=True), ForeignKey('run.run_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  run = relationship('Run')

  def __repr__(self):
    '''
    Display Run_attribute entry
    '''
    return self.run_attribute_id

class File_attribute(Model):

  '''
  A table for loading file attributes

  :param file_attribute_id: An integer id for file_attribute table
  :param attribute_name: An optional string attribute name, allowed length 30
  :param attribute_value: An optional string attribute value, allowed length 50
  :param file_id: An integer id from file table (foreign key)
  '''
  __tablename__ = 'file_attribute'
  __table_args__ = (
    UniqueConstraint('file_id', 'attribute_name', 'attribute_value'),
    { 'mysql_engine':'InnoDB', 'mysql_charset':'utf8'  })

  file_attribute_id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False)
  attribute_name = Column(String(30))
  attribute_value = Column(String(50))
  file_id = Column(INTEGER(unsigned=True), ForeignKey('file.file_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
  file = relationship('File')

  def __repr__(self):
    '''
    Display File_attribute entry
    '''
    return self.file_attribute_id
