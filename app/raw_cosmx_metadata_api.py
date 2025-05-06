import json, logging, gzip
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from io import BytesIO
from .models import RawCosMxMetadataModel
from .raw_metadata.raw_cosmx_metadata_util import download_ready_cosmx_metadata


log = logging.getLogger(__name__)

class RawCosMxMetadataDataApi(ModelRestApi):
    resource_name = "raw_cosmx_metadata"
    datamodel = SQLAInterface(RawCosMxMetadataModel)

    @expose('/download_ready_metadata',  methods=['GET'])
    @protect()
    def download_ready_metadata(self):
        try:
            results = \
                download_ready_cosmx_metadata()
            if len(results)==0:
                return self.response(200)
            else:
                data = dict()
                for tag, entry in results.items():
                    data.update({tag: entry})
                data = json.dumps(data)
                output = BytesIO(data.encode())
                output.seek(0)
                return send_file(output, download_name='metadata.json', as_attachment=True)
        except Exception as e:
            logging.error(e)