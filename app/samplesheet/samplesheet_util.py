import pandas as pd
import numpy as np
import os, json, re, tempfile
from datetime import datetime
from jsonschema import Draft4Validator, ValidationError
from collections import defaultdict, deque
from .. import db
from ..models import SampleSheetModel

class SampleSheet:
    '''
        A class for processing SampleSheet files for Illumina sequencing runs

        :param infile: A samplesheet file
        :param data_header_name: name of the data section, default Data
    '''

    def __init__(self, infile, data_header_name=('Data', 'BCLConvert_Data')):
        self.infile = infile
        self.data_header_name = data_header_name
        self._sample_data = self._read_samplesheet()                            # reading samplesheet data
        self._header_data = self._load_header()                                 # loading header information
        data_header, raw_data = self._load_data()                               # loading data and data header information
        self._data_header = data_header
        self._data = raw_data

    @property
    def samplesheet_version(self):
        return self._samplesheet_version

    def _read_samplesheet(self):
        '''
            Function for reading SampleSheet.csv file
        '''
        try:
            infile = self.infile
            if os.path.exists(infile) == False:
                raise IOError('file {0} not found'.\
                        format(infile))
            sample_data = defaultdict(list)
            header = ''
            with open(infile, 'r') as f:
                for i in f:
                    row = i.rstrip('\n')
                    if row != '':
                        if row.startswith('['):
                            header = \
                                row.split(',')[0].\
                                    strip('[').\
                                    strip(']')
                        else:
                            sample_data[header].append(row)
            return sample_data
        except Exception as e:
            raise ValueError(
                    "Failed to read samplesheet, error {0}".\
                        format(e))

    def _load_data(self):
        '''
            Function for loading SampleSheet data
        '''
        try:
            sample_data = self._sample_data
            for entry in self.data_header_name:
                if entry in sample_data:
                    data = sample_data[entry]
                    if entry == 'Data':
                        self._samplesheet_version = 'v1'
                    elif entry == 'BCLConvert_Data':
                        self._samplesheet_version = 'v2'
                    else:
                        self._samplesheet_version = 'unknown'
            data = deque(data)
            data_header = data.popleft()
            data_header = data_header.split(',')
            sample_data = list()
            for row in data:
                row = row.split(',')
                row = [
                    row_val.rstrip() for row_val in row]
                row_data = \
                    dict(zip(data_header,row))
                sample_data.append(row_data)
            return data_header, sample_data
        except Exception as e:
            raise ValueError("Failed to load data, error: {0}".format(e))

    def _load_header(self):
        '''
            Function for loading SampleSheet header
            Output: 2 lists , 1st list of column headers for data section,
            2nd list of dictionaries containing data
        '''
        try:
            sample_data = self._sample_data
            header_data = dict()
            for keys in sample_data:
                if keys != self.data_header_name:
                    header_data[keys] = sample_data[keys]
            return header_data
        except Exception as e:
            raise ValueError(
                    "Failed to load header data, error: {0}".format(e))


    @staticmethod
    def _check_samplesheet_data_row(data_series, single_cell_flag='10X'):
        '''
            An internal static method for additional validation of samplesheet data

            :param data_series: A pandas data series, containing a samplesheet data row
            :param single_cell_flag: A keyword for single cell sample description, default 10X
            :returns: A string of error messages, or NAN value
        '''
        try:
            if not isinstance(data_series, pd.Series):
                raise AttributeError(type(data_series))
            single_cell_flag_pattern = \
                re.compile(
                    r'^{0}$'.format(single_cell_flag),
                    re.IGNORECASE)
            err = list()
            if ('Sample_ID' in data_series and 'Sample_Name' in data_series) and \
               data_series['Sample_ID']==data_series['Sample_Name']:
                err.append(
                    "Same sample id and sample names are not allowed, {0}".\
                        format(data_series['Sample_ID']))
            if ('I5_Index_ID' in data_series and data_series['I5_Index_ID'] != '') and \
               ('index2' not in data_series or data_series['index2'] == ''):
                err.append(
                    "Missing I_5 index sequences for {0}".\
                        format(data_series['Sample_ID']))
            single_cell_index_pattern = \
                re.compile(r'^SI-[GNT][ATN]-[A-Z][0-9]+')
            if re.search(single_cell_flag_pattern, data_series['Description']) and \
               not re.search(single_cell_index_pattern, data_series['index']):
                err.append(
                    "Required I_7 single cell indexes for 10X sample {0}".\
                        format(data_series['Sample_ID']))
            if not re.search(single_cell_flag_pattern, data_series['Description']) and \
               re.search(single_cell_index_pattern, data_series['index']):
                err.append(
                    "Found I_7 single cell indexes, missing 10X description sample {0}".\
                        format(data_series['Sample_ID']))
            if re.search(single_cell_flag_pattern, data_series['Description']) and \
               re.search(single_cell_index_pattern, data_series['index']) and \
               'index2' in data_series and data_series['index2'] !='':
                err.append(
                    "Found I_5 index(2) for single cell sample {0}".\
                        format(data_series['Sample_ID']))
            if len(err) == 0:
                err_str = np.nan
            else:
                err_str = '\n'.join(err)
            return err_str
        except Exception as e:
            raise ValueError(
                    "Failed to check samplesheet data row, error: {0}".\
                        format(e))


    def _validate_samplesheet_columns(self, schema_json):
        try:
            with open(schema_json, 'r') as jp:
                json_data = json.load(jp)
            allowed_samplesheet_fields = \
                list(json_data['items']['properties'].keys())
            errors = list()
            for header_name in self._data_header:
                if header_name not in allowed_samplesheet_fields:
                    errors.\
                        append(
                            'Header {0} is not supported. Validation incomplete.'.\
                                format(header_name))
            return errors
        except Exception as e:
            raise ValueError(
                    "Failed to validate samplesheet columns, error: {0}".\
                        format(e))


    def _get_duplicate_entries(
        self, sample_id_col='Sample_ID', sample_name_col="Sample_Name",
        lane_col='Lane', index_columns=("index", "index2")):
        try:
            errors = list()
            df = pd.DataFrame(self._data)
            df.fillna('', inplace=True)
            # get samplesheet wide duplicates
            duplicates = df[df.duplicated()]
            for entry in duplicates.to_dict(orient="records"):
                errors.\
                    append("Duplicte entry found for sample {0}".\
                        format(entry.get(sample_id_col)))
            # get duplicate indices
            index_lookup_columns = \
                [i for i in index_columns 
                    if i in df.columns]
            if len(index_lookup_columns) == 0:
                raise ValueError("No index lookup column found in samplesheet")
            if lane_col in df.columns:
                for lane, l_data in df.drop_duplicates().groupby(lane_col):
                    duplicate_entries = \
                        l_data[l_data[index_lookup_columns].duplicated()]
                    for entry in duplicate_entries.to_dict(orient="records"):
                        errors.append(
                            "Duplicate index for lane {0} sample {1}: {2}".\
                                format(
                                    lane,
                                    entry.get(sample_id_col),
                                    ', '.join([entry.get(i) for i in index_lookup_columns])) )
            else:
                duplicate_entries = \
                    df[df[index_lookup_columns].duplicated()]
                for entry in duplicate_entries.to_dict(orient="records"):
                    errors.append(
                        "Duplicate index for sample {0}: {1}".\
                            format(
                                entry.get(sample_id_col),
                                ', '.join([entry.get(i) for i in index_lookup_columns])) )
            # get duplicate samples ids and names
            if lane_col in df.columns:
                for lane, l_data in df.drop_duplicates().groupby(lane_col):
                    duplicate_ids = \
                        l_data[l_data[sample_id_col].duplicated()][sample_id_col].\
                            values.tolist()
                    if len(duplicate_ids) > 0:
                        errors.append(
                            "Duplicate sample ids present on lane {0}: {1}".\
                                format(lane, ', '.join(duplicate_ids)) )
                    duplicate_names = \
                        l_data[l_data[sample_name_col].duplicated()][sample_name_col].\
                            values.tolist()
                    if len(duplicate_names) > 0:
                        errors.append(
                            "Duplicate sample names present on lane {0}: {1}".\
                                format(lane, ', '.join(duplicate_names)) )
            else:
                duplicate_ids = \
                    df[df[sample_id_col].duplicated()][sample_id_col].\
                        values.tolist()
                if len(duplicate_ids) > 0:
                    errors.append({
                        "Duplicate sample ids present: {0}".\
                            format(', '.join(duplicate_ids)) })
                duplicate_names = \
                    df[df[sample_name_col].duplicated()][sample_name_col].\
                        values.tolist()
                if len(duplicate_names) > 0:
                    errors.append({
                        "Duplicate sample names present: {0}".\
                            format(', '.join(duplicate_names)) })
            return errors
        except Exception as e:
            raise ValueError(
                    "Failed to get duplicate entries, error: {0}".\
                        format(e))


    def validate_samplesheet_data(
        self, schema_json=os.path.join(os.path.dirname(__file__), 'samplesheet_validation.json')):
        '''
            A method for validation of samplesheet data

            :param schema: A JSON schema for validation of the samplesheet data
            :return a list of error messages or an empty list if no error found
        '''
        try:
            data = self._data
            data = pd.DataFrame(data)                                           # read data as pandas dataframe
            data = data.fillna("").applymap(lambda x: str(x))                   # replace nan with empty strings and convert all entries to string
            json_data = data.to_dict(orient='records')                          # convert dataframe to list of dictionaries
            error_list = list()                                                 # define empty error list
            if not os.path.exists(schema_json):
                raise IOError(
                        'json schema file {0} not found'.\
                            format(schema_json))
            with open(schema_json,'r') as jf:
                schema = json.load(jf)                                          # read schema from the json file
            # syntactic validation
            v_s = Draft4Validator(schema)                                       # initiate validator using schema
            error_list = \
                sorted(
                    v_s.iter_errors(json_data),
                    key=lambda e: e.path)                                       # overwrite error_list with validation error
            temp_error_list = list()
            for err in error_list:
                if isinstance(err, str):
                    temp_error_list.append(err)
                else:
                    if len(err.schema_path) > 2:
                        temp_error_list.append(
                            "{0}: {1}".format(err.schema_path[2], err.message))
                    else:
                        temp_error_list.append(
                            "{0}".format(err.message))
            error_list = temp_error_list
            # semantic validation
            column_errors = \
                self._validate_samplesheet_columns(schema_json=schema_json)
            if len(column_errors) > 0:
                error_list.extend(column_errors)
            else:
                other_errors = \
                    data.apply(
                        lambda x: \
                            self._check_samplesheet_data_row(data_series=x),
                        axis=1)                                                 # check for additional errors
                other_errors.dropna(inplace=True)
                if len(other_errors) > 0:
                    error_list.extend([
                        value for value in other_errors.to_dict().values()])    # add other errors to the list
                    duplicate_errors = \
                        self._get_duplicate_entries()
                    if len(duplicate_errors) > 0:
                        error_list.extend(duplicate_errors)
            formatted_errors = list()
            for index, entry in enumerate(error_list):
                formatted_errors.\
                    append("{0}. {1}".format(index + 1, entry))
            return formatted_errors
        except Exception as e:
            raise ValueError(
                    "Failed to validate samplesheet. Error: {0}".\
                        format(e))


def update_samplesheet_validation_entry_in_db(samplesheet_tag, report, status=''):
    try:
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag==samplesheet_tag).\
                one_or_none()
        if entry is None:
            raise ValueError("No entr found for samplesheet tag {0}".format(samplesheet_tag))
        if status == 'pass':
            status = 'PASS'
        else:
            status='FAILED'
        samplesheeet_data = {
            'status': status,
            'report': report,
            'validation_time': datetime.now(),
            'update_time': datetime.now()}
        try:
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_tag==samplesheet_tag).\
                update(samplesheeet_data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(
                    "Failed db update for {0}, error: {1}".\
                        format(samplesheet_tag, e))
    except Exception as e:
        raise ValueError(
                "Failed to update samplesheet validation status, error: {0}".\
                    format(e))


def validate_samplesheet_data_and_update_db(samplesheet_id):
    try:
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_id==samplesheet_id).\
                one_or_none()
        if entry is not None:
            csv_data = entry.csv_data
            with tempfile.TemporaryDirectory() as temp_dir:
                csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
                with open(csv_file, 'w') as fp:
                    fp.write(csv_data)
                sa = SampleSheet(infile=csv_file)
                errors = sa.validate_samplesheet_data()
                if len(errors) > 0:
                    update_samplesheet_validation_entry_in_db(
                        samplesheet_tag=entry.samplesheet_tag,
                        report='\n'.join(errors),
                        status='failed')
                    return 'failed'
                else:
                    update_samplesheet_validation_entry_in_db(
                        samplesheet_tag=entry.samplesheet_tag,
                        report='',
                        status='pass')
                    return 'pass'
        else:
            return None
    except Exception as e:
        raise ValueError(
                "Failed samplesheet validation wrapper, error: {0}".\
                    format(e))

def compare_sample_with_metadata_db(samplesheet_id):
    try:
        entry = \
            db.session.\
                query(SampleSheetModel).\
                filter(SampleSheetModel.samplesheet_id==samplesheet_id).\
                one_or_none()
        if entry is None:
            raise ValueError(
                    "No samplesheet record found for id {0}".\
                        format(samplesheet_id))
        csv_data = entry.csv_data
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
            with open(csv_file, 'w') as fp:
                fp.write(csv_data)
            sa = SampleSheet(infile=csv_file)
            df = pd.DataFrame(sa._data)
    except Exception as e:
        raise ValueError(
                "Failed to compare samplesheet with metadata, error: {0}".\
                    format(e))