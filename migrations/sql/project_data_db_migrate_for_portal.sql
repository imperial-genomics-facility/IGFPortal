CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 78b82238be89


INSERT INTO alembic_version (version_num) VALUES ('78b82238be89');

-- Running upgrade 78b82238be89 -> a38c16db0e8d

ALTER TABLE pre_demultiplexing_data ADD COLUMN file_path VARCHAR(500);

ALTER TABLE pre_demultiplexing_data ADD COLUMN status ENUM('ACTIVE','WITHDRAWN','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN';

ALTER TABLE raw_analysis ADD COLUMN project_id INTEGER UNSIGNED;

ALTER TABLE raw_analysis ADD COLUMN pipeline_id INTEGER UNSIGNED;

ALTER TABLE raw_analysis ADD COLUMN analysis_name VARCHAR(120) NOT NULL;

ALTER TABLE raw_analysis MODIFY analysis_yaml LONGTEXT NULL;

ALTER TABLE raw_analysis MODIFY report LONGTEXT NULL;

ALTER TABLE raw_analysis ADD UNIQUE (analysis_name, project_id);

ALTER TABLE raw_analysis ADD FOREIGN KEY(pipeline_id) REFERENCES pipeline (pipeline_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE raw_analysis ADD FOREIGN KEY(project_id) REFERENCES project (project_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE raw_analysis DROP COLUMN analysis_tag;

ALTER TABLE raw_seqrun ADD COLUMN mismatches ENUM('0','1','2') DEFAULT '1';

ALTER TABLE raw_seqrun ADD COLUMN trigger_time TIMESTAMP NULL;

ALTER TABLE raw_seqrun ADD COLUMN run_config LONGTEXT;

ALTER TABLE raw_seqrun MODIFY COLUMN status ENUM("ACTIVE", "REJECTED", "PREDEMULT", "READY", "FINISHED") NOT NULL DEFAULT 'ACTIVE';

ALTER TABLE sample_index ADD FOREIGN KEY(project_index_id) REFERENCES project_index (project_index_id) ON DELETE SET NULL ON UPDATE CASCADE;

UPDATE alembic_version SET version_num='a38c16db0e8d' WHERE alembic_version.version_num = '78b82238be89';

