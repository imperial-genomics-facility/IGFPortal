import json
import logging
from flask_appbuilder import ModelRestApi
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from flask import send_file
from io import BytesIO
from app import db
from app.models import RawCosMxMetadataModel

log = logging.getLogger(__name__)

class RawCosMxMetadataApi(ModelRestApi):
    resource_name = "raw_cosmx_metadata"
    datamodel = SQLAInterface(RawCosMxMetadataModel)

    @expose(
        '/get_raw_metadata/<raw_cosmx_metadata_id>', 
        methods=['GET']
    )
    @protect()
    def get_raw_metadata(self, raw_cosmx_metadata_id: int):
        try:
            result = (
                db.session
                .query(
                    RawCosMxMetadataModel.cosmx_metadata_tag,
                    RawCosMxMetadataModel.formatted_csv_data
                )
                .filter(RawCosMxMetadataModel.status=='READY')
                .filter(
                    RawCosMxMetadataModel.raw_cosmx_metadata_id
                    == raw_cosmx_metadata_id
                )
                .one_or_none()
            )
            if result is None:
                entry = {'': ''}
            else:
                entry = {result[0]: result[1]}
            data = json.dumps(entry)
            output = BytesIO(data.encode())
            output.seek(0)
            return send_file(
                output,
                download_name='metadata.json',
                as_attachment=True
            )
        except Exception as e:
            log.error(e)

    @expose(
        '/mark_ready_metadata_as_synced/<raw_cosmx_metadata_id>', 
        methods=['GET']
    )
    @protect()
    def mark_raw_metadata_as_synced(self, raw_cosmx_metadata_id: int):
        try:
            try:
                (
                    db.session
                    .query(RawCosMxMetadataModel)
                    .filter(RawCosMxMetadataModel.status=='READY')
                    .filter(
                        RawCosMxMetadataModel.raw_cosmx_metadata_id
                        == raw_cosmx_metadata_id
                    )
                    .update({'status':'SYNCHED'})
                )
                db.session.commit()
                return self.response(200, message='metadata synced')
            except:
                db.session.rollback()
                raise
        except Exception as e:
            log.error(e)