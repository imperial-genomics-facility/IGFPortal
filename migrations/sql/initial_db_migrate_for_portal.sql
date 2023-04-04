CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 78b82238be89


INSERT INTO alembic_version (version_num) VALUES ('78b82238be89');

