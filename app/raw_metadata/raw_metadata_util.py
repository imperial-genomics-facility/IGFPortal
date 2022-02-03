from multiprocessing.sharedctypes import Value
from numpy import isin
import pandas as pd
import os, json, re, tempfile, logging
from jsonschema import Draft4Validator, ValidationError
from .. import db
from ..models import RawMetadataModel
from ..metadata.metadata_util import check_for_projects_in_metadata_db
from ..metadata.metadata_util import check_sample_and_project_ids_in_metadata_db

EXPERIMENT_TYPE_LOOKUP = \
[{'library_preparation': 'WHOLE GENOME SEQUENCING - SAMPLE', 'library_type': 'WHOLE GENOME',
  'library_strategy': 'WGS', 'experiment_type': 'WGS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WHOLE GENOME SEQUENCING HUMAN - SAMPLE', 'library_type': 'WHOLE GENOME',
  'library_strategy': 'WGS', 'experiment_type': 'WGS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WHOLE GENOME SEQUENCING - BACTERIA', 'library_type': 'WHOLE GENOME',
  'library_strategy': 'WGS', 'experiment_type': 'WGS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WGA', 'library_type': 'WGA',
  'library_strategy': 'WGA', 'experiment_type': 'WGA', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WHOLE EXOME CAPTURE - EXONS - SAMPLE', 'library_type': 'HYBRID CAPTURE - EXOME',
  'library_strategy': 'WXS', 'experiment_type': 'WXS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WHOLE EXOME CAPTURE - EXONS + UTR - SAMPLE', 'library_type': 'HYBRID CAPTURE - EXOME',
  'library_strategy': 'WXS', 'experiment_type': 'WXS-UTR', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - RIBOSOME PROFILING - SAMPLE', 'library_type': 'TOTAL RNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'RIBOSOME-PROFILING', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - TOTAL RNA', 'library_type': 'TOTAL RNA',
  'library_strategy': 'RNA-SEQ','experiment_type': 'TOTAL-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - MRNA', 'library_type': 'MRNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'POLYA-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - MRNA STRANDED - SAMPLE', 'library_type': 'RNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'POLYA-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - TOTAL RNA WITH RRNA DEPLETION - SAMPLE', 'library_type': 'RNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TOTAL-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - LOW INPUT WITH RIBODEPLETION', 'library_type': 'MRNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'RIBODEPLETION', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - TOTAL RNA WITH GLOBIN DEPLETION', 'library_type': 'TOTAL RNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TOTAL-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - MRNA RNA WITH GLOBIN DEPLETION', 'library_type': 'MRNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'POLYA-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': "RNA SEQUENCING - 3' END RNA-SEQ", 'library_type': 'MRNA',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'POLYA-RNA-3P', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': "SINGLE CELL -3' RNASEQ- SAMPLE", 'library_type': "SINGLE CELL-3' RNA",
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TENX-TRANSCRIPTOME-3P', 'library_source': 'TRANSCRIPTOMIC_SINGLE_CELL','biomaterial_type':'UNKNOWN'},
 {'library_preparation': "SINGLE CELL -3' RNASEQ- SAMPLE NUCLEI", 'library_type': "SINGLE CELL-3' RNA (NUCLEI)",
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TENX-TRANSCRIPTOME-3P', 'library_source': 'TRANSCRIPTOMIC_SINGLE_CELL','biomaterial_type':'SINGLE_NUCLEI'},
 {'library_preparation': "SINGLE CELL -5' RNASEQ- SAMPLE", 'library_type': "SINGLE CELL-5' RNA",
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TENX-TRANSCRIPTOME-5P', 'library_source': 'TRANSCRIPTOMIC_SINGLE_CELL','biomaterial_type':'UNKNOWN'},
 {'library_preparation': "SINGLE CELL -5' RNASEQ- SAMPLE NUCLEI", 'library_type': "SINGLE CELL-5' RNA (NUCLEI)",
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'TENX-TRANSCRIPTOME-5P', 'library_source': 'TRANSCRIPTOMIC_SINGLE_CELL','biomaterial_type':'SINGLE_NUCLEI'},
 {'library_preparation': 'METAGENOMIC PROFILING - 16S RRNA SEQUENCING - SAMPLE', 'library_type': '16S',
  'library_strategy': 'RNA-SEQ', 'experiment_type': '16S', 'library_source': 'METAGENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RNA SEQUENCING - SMALL RNA - SAMPLE', 'library_type': 'SMALL RNA',
  'library_strategy': 'MIRNA-SEQ', 'experiment_type': 'SMALL-RNA', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'NCRNA-SEQ', 'library_type': 'NCRNA-SEQ',
  'library_strategy': 'NCRNA-SEQ', 'experiment_type': 'NCRNA-SEQ', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'FL-CDNA', 'library_type': 'FL-CDNA',
  'library_strategy': 'FL-CDNA', 'experiment_type': 'FL-CDNA', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'EST', 'library_type': 'EST',
  'library_strategy': 'EST', 'experiment_type': 'EST', 'library_source': 'TRANSCRIPTOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'HI-C SEQ', 'library_type': 'HI-C SEQ',
  'library_strategy': 'HI-C', 'experiment_type': 'HI-C', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'ATAC SEQ', 'library_type': 'ATAC SEQ',
  'library_strategy': 'ATAC-SEQ', 'experiment_type': 'ATAC-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'DNASE-SEQ', 'library_type': 'DNASE-SEQ',
  'library_strategy': 'DNASE-SEQ', 'experiment_type': 'DNASE-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'WCS', 'library_type': 'WCS',
  'library_strategy': 'WCS', 'experiment_type': 'WCS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RAD-SEQ', 'library_type': 'RAD-SEQ',
  'library_strategy': 'RAD-SEQ', 'experiment_type': 'RAD-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CLONE', 'library_type': 'CLONE',
  'library_strategy': 'CLONE', 'experiment_type': 'CLONE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'POOLCLONE', 'library_type': 'POOLCLONE',
  'library_strategy': 'POOLCLONE', 'experiment_type': 'POOLCLONE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'AMPLICON SEQUENCING - ILLUMINA TRUSEQ CUSTOM AMPLICON', 'library_type': 'AMPLICON SEQ',
  'library_strategy': 'AMPLICON', 'experiment_type': 'AMPLICON', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CLONEEND', 'library_type': 'CLONEEND',
  'library_strategy': 'CLONEEND', 'experiment_type': 'CLONEEND', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'FINISHING', 'library_type': 'FINISHING',
  'library_strategy': 'FINISHING', 'experiment_type': 'FINISHING', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - SAMPLE', 'library_type': 'CHIP SEQ',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'CHIP-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - INPUT', 'library_type': 'CHIP SEQ - INPUT',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'CHIP-INPUT', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - TF', 'library_type': 'CHIP SEQ - TF',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'TF', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - BROAD PEAK', 'library_type': 'CHIP SEQ - BROAD PEAK',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'HISTONE-BROAD', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - NARROW PEAK', 'library_type': 'CHIP SEQ - NARROW PEAK',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'HISTONE-NARROW', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'MNASE-SEQ', 'library_type': 'MNASE-SEQ',
  'library_strategy': 'MNASE-SEQ', 'experiment_type': 'MNASE-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'DNASE-HYPERSENSITIVITY', 'library_type': 'DNASE-HYPERSENSITIVITY',
  'library_strategy': 'DNASE-HYPERSENSITIVITY', 'experiment_type': 'DNASE-HYPERSENSITIVITY', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'METHYLATION PROFILING - RRBS-SEQ - SAMPLE', 'library_type': 'RRBS-SEQ',
  'library_strategy': 'BISULFITE-SEQ', 'experiment_type': 'RRBS-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'METHYLATION PROFILING - WHOLE GENOME BISULFITE SEQUENCING - SAMPLE', 'library_type': 'BISULFITE SEQ',
  'library_strategy': 'BISULFITE-SEQ', 'experiment_type': 'WGBS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CTS', 'library_type': 'CTS',
  'library_strategy': 'CTS', 'experiment_type': 'CTS', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'MRE-SEQ', 'library_type': 'MRE-SEQ',
  'library_strategy': 'MRE-SEQ', 'experiment_type': 'MRE-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'METHYLATION PROFILING - MEDIP-SEQ - SAMPLE', 'library_type': 'MEDIP-SEQ',
  'library_strategy': 'MEDIP-SEQ', 'experiment_type': 'MEDIP-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'METHYLATION PROFILING - MBD-SEQ - SAMPLE', 'library_type': 'MBD-SEQ',
  'library_strategy': 'MBD-SEQ', 'experiment_type': 'MBD-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'TN-SEQ', 'library_type': 'TN-SEQ',
  'library_strategy': 'TN-SEQ', 'experiment_type': 'TN-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'VALIDATION', 'library_type': 'VALIDATION',
  'library_strategy': 'VALIDATION', 'experiment_type': 'VALIDATION', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'FAIRE-SEQ', 'library_type': 'FAIRE-SEQ',
  'library_strategy': 'FAIRE-SEQ', 'experiment_type': 'FAIRE-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'SELEX', 'library_type': 'SELEX',
  'library_strategy': 'SELEX', 'experiment_type': 'SELEX', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'RIP-SEQ', 'library_type': 'RIP-SEQ',
  'library_strategy': 'RIP-SEQ', 'experiment_type': 'RIP-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIA-PET', 'library_type': 'CHIA-PET',
  'library_strategy': 'CHIA-PET', 'experiment_type': 'CHIA-PET', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'SYNTHETIC-LONG-READ', 'library_type': 'SYNTHETIC-LONG-READ',
  'library_strategy': 'SYNTHETIC-LONG-READ', 'experiment_type': 'SYNTHETIC-LONG-READ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'TARGETED CAPTURE AGILENT (PROBES PROVIDED BY COLL.) - SAMPLE', 'library_type': 'HYBRID CAPTURE - PANEL',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE: 1 TO 499KB - SAMPLE', 'library_type': 'HYBRID CAPTURE - CUSTOM',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE: 0.5 TO 2.9MB - SAMPLE', 'library_type': 'HYBRID CAPTURE - CUSTOM',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE: 3 TO 5.9MB - SAMPLE', 'library_type': 'HYBRID CAPTURE - CUSTOM',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE: 6 TO 11.9MB - SAMPLE', 'library_type': 'HYBRID CAPTURE - CUSTOM',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE: 12 TO 24MB - SAMPLE', 'library_type': 'HYBRID CAPTURE - CUSTOM',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CUSTOM TARGET CAPTURE - TRUSIGHT CARDIO - SAMPLE', 'library_type': 'HYBRID CAPTURE - PANEL',
  'library_strategy': 'TARGETED-CAPTURE', 'experiment_type': 'TARGETED-CAPTURE', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'TETHERED', 'library_type': 'TETHERED',
  'library_strategy': 'TETHERED', 'experiment_type': 'TETHERED', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'NOME-SEQ', 'library_type': 'NOME-SEQ',
  'library_strategy': 'NOME-SEQ', 'experiment_type': 'NOME-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'OTHER-SPECIFY IN COMMENT BOX', 'library_type': 'OTHER',
  'library_strategy': 'UNKNOWN', 'experiment_type': 'UNKNOWN', 'library_source': 'UNKNOWN','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIRP SEQ', 'library_type': 'CHIRP SEQ',
  'library_strategy': 'CHIRP SEQ', 'experiment_type': 'CHIRP SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': '4-C SEQ', 'library_type': '4-C SEQ',
  'library_strategy': '4-C-SEQ', 'experiment_type': '4-C-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': '5-C SEQ', 'library_type': '5-C SEQ',
  'library_strategy': '5-C-SEQ', 'experiment_type': '5-C-SEQ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'METAGENOMICS - OTHER', 'library_type': 'METAGENOMICS - OTHER',
  'library_strategy': 'WGS', 'experiment_type': 'METAGENOMIC', 'library_source': 'METAGENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'DROP-SEQ-TRANSCRIPTOME', 'library_type': 'DROP-SEQ-TRANSCRIPTOME',
  'library_strategy': 'RNA-SEQ', 'experiment_type': 'DROP-SEQ-TRANSCRIPTOME', 'library_source': 'TRANSCRIPTOMIC SINGLE CELL','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K27ME3', 'library_type': 'CHIP SEQ - H3K27ME3',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K27ME3', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K27AC', 'library_type': 'CHIP SEQ - H3K27AC',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K27AC', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K9ME3', 'library_type': 'CHIP SEQ - H3K9ME3',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K9ME3', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K36ME3', 'library_type': 'CHIP SEQ - H3K36ME3',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K36ME3', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3F3A', 'library_type': 'CHIP SEQ - H3F3A',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3F3A', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K4ME1', 'library_type': 'CHIP SEQ - H3K4ME1',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K4ME1', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K79ME2', 'library_type': 'CHIP SEQ - H3K79ME2',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K79ME2', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K79ME3', 'library_type': 'CHIP SEQ - H3K79ME3',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K79ME3', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K9ME1', 'library_type': 'CHIP SEQ - H3K9ME1',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K9ME1', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K9ME2', 'library_type': 'CHIP SEQ - H3K9ME2',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K9ME2', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H4K20ME1', 'library_type': 'CHIP SEQ - H4K20ME1',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H4K20ME1', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H2AFZ', 'library_type': 'CHIP SEQ - H2AFZ',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H2AFZ', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3AC', 'library_type': 'CHIP SEQ - H3AC',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3AC', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K4ME2', 'library_type': 'CHIP SEQ - H3K4ME2',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K4ME2', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K4ME3', 'library_type': 'CHIP SEQ - H3K4ME3',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K4ME3', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'},
 {'library_preparation': 'CHIP SEQUENCING - H3K9AC', 'library_type': 'CHIP SEQ - H3K9AC',
  'library_strategy': 'CHIP-SEQ', 'experiment_type': 'H3K9AC', 'library_source': 'GENOMIC','biomaterial_type':'UNKNOWN'}]


def _run_metadata_json_validation(
    metadata_file, schema_json):
    try:
        if not os.path.exists(metadata_file) or \
           not os.path.exists(schema_json):
           raise IOError("Input file error")
        error_list = list()
        with open(schema_json,'r') as jf:
            schema = json.load(jf)
        metadata_validator = Draft4Validator(schema)
        metadata_json_fields = list(schema['items']['properties'].keys())
        metadata_df = pd.read_csv(metadata_file)
        metadata_df.fillna('', inplace=True)
        metadata_df['taxon_id'] = \
            metadata_df['taxon_id'].\
                astype(str)
        for header_name in metadata_df.columns:
            if header_name not in metadata_json_fields:
                error_list.append("Unexpected column {0} found")
        duplicates = \
            metadata_df[metadata_df.duplicated()]
        for entry in duplicates.to_dict(orient="records"):
            error_list.append(
                "Duplicate entry found for sample {0}".\
                    format(entry.get("sample_igf_id")))
        json_data = \
            metadata_df.\
                to_dict(orient='records')
        validation_errors = \
            sorted(
                metadata_validator.iter_errors(json_data),
                key=lambda e: e.path)
        for err in validation_errors:
            if isinstance(err, str):
                error_list.append(err)
            else:
                if len(err.schema_path) > 2:
                    error_list.append(
                        "{0}: {1}".format(err.schema_path[2], err.message))
                else:
                    error_list.append(
                        "{0}".format(err.message))
        return error_list
    except Exception as e:
        raise ValueError(
                "Failed to run json validation, error: {0}".\
                    format(e))


def _set_metadata_validation_status(raw_metadata_id, status, report=''):
    try:
        if status.upper() == 'VALIDATED':
            try:
                db.session.\
                    query(RawMetadataModel).\
                    filter(RawMetadataModel.raw_metadata_id==raw_metadata_id).\
                    update({
                        'status': 'VALIDATED',
                        'report': ''})
                db.session.commit()
            except:
                db.session.rollback()
                raise
        elif status.upper() == 'FAILED':
            try:
                db.session.\
                    query(RawMetadataModel).\
                    filter(RawMetadataModel.raw_metadata_id==raw_metadata_id).\
                    update({
                        'status': 'FAILED',
                        'report': report})
                db.session.commit()
            except:
                db.session.rollback()
                raise
        else:
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==raw_metadata_id).\
                update({
                    'status': 'UNKNOWN'})
    except Exception as e:
        raise ValueError(
                "Failed to set metadata status for id {0}, error: {1}".\
                    format(raw_metadata_id, e))


def validate_raw_metadata_and_set_db_status(
    raw_metadata_id,
    check_db=True,
    schema_json=os.path.join(os.path.dirname(__file__), 'metadata_validation.json')):
    try:
        error_list = list()
        raw_metadata = \
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id==raw_metadata_id).\
                one_or_none()
        if raw_metadata is None:
            raise ValueError(
                    "No metadata entry found for id {0}".\
                        format(raw_metadata_id))
        csv_data = raw_metadata.formatted_csv_data
        if csv_data is None:
            raise ValueError(
                    "No formatted csv error found for id {0}".\
                        format(raw_metadata_id))
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = os.path.join(temp_dir, 'metadata.csv')
            with open(metadata_file, 'w') as fp:
                fp.write(csv_data)
            validation_errors = \
                _run_metadata_json_validation(
                    metadata_file=metadata_file,
                    schema_json=schema_json)
            if len(validation_errors) > 0:
                error_list.\
                    extend(validation_errors)
            metadata_df = pd.read_csv(metadata_file)
            for entry in metadata_df.to_dict(orient="records"):
                sample_id = entry.get('sample_igf_id'),
                library_source = entry.get('library_source'),
                library_strategy = entry.get('library_strategy'),
                experiment_type = entry.get('experiment_type')
                err = \
                    _validate_metadata_library_type(
                        sample_id=sample_id,
                        library_source=library_source,
                        library_strategy=library_strategy,
                        experiment_type=experiment_type)
                if err is not None:
                    error_list.append(
                        "Metadata error: {0}, {1}".\
                            format(sample_id, err))
            if check_db:
                existing_metadata_errors = \
                    compare_metadata_sample_with_db(
                        metadata_file=metadata_file)
                if len(existing_metadata_errors) > 0:
                    error_list.extend(existing_metadata_errors)
        if len(error_list) > 0:
            error_list = \
                ["{0}, {1}".format(i+1, e)
                    for i,e in enumerate(error_list)]
            _set_metadata_validation_status(
                raw_metadata_id=raw_metadata_id,
                status='FAILED',
                report='\n'.join(error_list))
            return 'FAILED'
        else:
            _set_metadata_validation_status(
                raw_metadata_id=raw_metadata_id,
                status='PASS')
            return 'PASS'
    except Exception as e:
        raise ValueError(
                "Failed to get metadata for id {0}, error: {1}".\
                    format(raw_metadata_id, e))


def compare_metadata_sample_with_db(
    metadata_file: str, project_column: str ='project_igf_id', sample_column: str ='sample_igf_id',
    name_column: str ='name', email_column: str ='email_id') -> list:
    try:
        errors = list()
        df = pd.read_csv(metadata_file)
        project_list = \
            df[project_column].\
                drop_duplicates().\
                values.\
                tolist()
        sample_projects_df = \
            df[[sample_column, project_column, name_column, email_column]].\
                drop_duplicates()
        sample_project_list = \
            sample_projects_df.\
                to_dict(orient='records')
        sample_project_errors = \
            check_sample_and_project_ids_in_metadata_db(
                sample_project_list=sample_project_list,
                check_missing=False)
        if len(sample_project_errors) > 0:
            errors.extend(sample_project_errors)
        return errors
    except Exception as e:
        raise ValueError(
                "Failed to compare metadata with db, error: {0}".\
                    format(e))


def _validate_metadata_library_type(
    sample_id, library_source, library_strategy, experiment_type):
    '''
    A staticmethod for validating library metadata information for sample

    :param sample_id: Sample name
    :param library_source: Library source information
    :param library_strategy: Library strategy information
    :param experiment_type: Experiment type information
    :returns: A error message string or None
    '''
    try:
      error_msg = None
      exp_lookup_data = pd.DataFrame(EXPERIMENT_TYPE_LOOKUP)
      if library_source == 'GENOMIC':
        library_strategy_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='GENOMIC']['library_strategy'].values)
        library_strategy_list.append('UNKNOWN')
        experiment_type_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='GENOMIC']['experiment_type'].values)
        experiment_type_list.append('UNKNOWN')
        if library_strategy not in library_strategy_list or \
            experiment_type not in experiment_type_list:
          error_msg = \
            '{0}: library_strategy {1} or experiment_type {2} is not compatible with library_source {3}'.\
            format(sample_id,
                   library_strategy,
                   experiment_type,
                   library_source)
      elif library_source == 'TRANSCRIPTOMIC':
        library_strategy_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='TRANSCRIPTOMIC']['library_strategy'].values)
        library_strategy_list.append('UNKNOWN')
        experiment_type_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='TRANSCRIPTOMIC']['experiment_type'].values)
        experiment_type_list.append('UNKNOWN')
        if library_strategy not in library_strategy_list or \
           experiment_type not in experiment_type_list:
          error_msg = \
            '{0}: library_strategy {1} or experiment_type {2} is not compatible with library_source {3}'.\
            format(sample_id,
                   library_strategy,
                   experiment_type,
                   library_source)
      elif library_source == 'GENOMIC_SINGLE_CELL':
        library_strategy_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='GENOMIC_SINGLE_CELL']['library_strategy'].values)
        library_strategy_list.append('UNKNOWN')
        experiment_type_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='GENOMIC_SINGLE_CELL']['experiment_type'].values)
        experiment_type_list.append('UNKNOWN')
        if library_strategy not in library_strategy_list or \
           experiment_type not in experiment_type_list:
          error_msg = \
            '{0}: library_strategy {1} or experiment_type {2} is not compatible with library_source {3}'.\
            format(sample_id,
                   library_strategy,
                   experiment_type,
                   library_source)
      elif library_source == 'TRANSCRIPTOMIC_SINGLE_CELL':
        library_strategy_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='TRANSCRIPTOMIC_SINGLE_CELL']['library_strategy'].values)
        library_strategy_list.append('UNKNOWN')
        experiment_type_list = \
          list(exp_lookup_data[exp_lookup_data['library_source']=='TRANSCRIPTOMIC_SINGLE_CELL']['experiment_type'].values)
        experiment_type_list.append('UNKNOWN')
        if library_strategy not in library_strategy_list or \
           experiment_type not in experiment_type_list:
          error_msg = \
            '{0}: library_strategy {1} or experiment_type {2} is not compatible with library_source {3}'.\
            format(sample_id,
                   library_strategy,
                   experiment_type,
                   library_source)

      return error_msg
    except Exception as e:
      raise ValueError(
                "Failed to validate library type, error: {0}".\
                    format(e))

def mark_raw_metadata_as_ready(id_list):
    try:
        try:
            db.session.\
                query(RawMetadataModel).\
                filter(RawMetadataModel.raw_metadata_id.in_(id_list)).\
                filter(RawMetadataModel.status=="VALIDATED").\
                update({'status': 'READY'}, synchronize_session='fetch')
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError("Failed to mark metadata as ready, error: {0}".format(e))