from . import appbuilder
from .interop_data_api import SeqrunInteropApi
from .pre_demultiplexing_data_api import PreDeMultiplexingDataApi


"""
    Api view
"""
appbuilder.add_api(SeqrunInteropApi)
appbuilder.add_api(PreDeMultiplexingDataApi)