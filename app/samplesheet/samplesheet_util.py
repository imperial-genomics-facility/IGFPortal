import os, json, re
import pandas as pd
import numpy as np
from jsonschema import Draft4Validator
from collections import defaultdict, deque

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
        self.columns = ("Lane", "Sample_ID", "Sample_Name", "Sample_Plate",
                        "Sample_Well", "I7_Index_ID", "index", "I5_Index_ID",
                        "index2", "Sample_Project", "Description")

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


    def validate_samplesheet_data(self, schema_json=os.path.join(os.path.dirname(__file__), 'samplesheet_validation.json')):
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
            # semantic validation
            other_errors = \
                data.apply(
                    lambda x: \
                        self._check_samplesheet_data_row(data_series=x),
                    axis=1)                                                     # check for additional errors
            other_errors.dropna(inplace=True)
            if len(other_errors) > 0:
                error_list.extend([
                    value for value in other_errors.to_dict().values()])        # add other errors to the list
            for c in data.columns.tolist():
                if c not in self.columns:
                    error_list.\
                        append('Unknown column {0} found on samplesheet'.\
                                 format(c))
            return error_list
        except Exception as e:
            raise ValueError(
                    "Failed to validate samplesheet. Error: {0}".\
                        format(e))