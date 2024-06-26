from . import appbuilder
from .interop_data_api import SeqrunInteropApi
from .pre_demultiplexing_data_api import PreDeMultiplexingDataApi
from .metadata_api import MetadataLoadApi
from .raw_metadata_api import RawMetadataDataApi
from .admin_home_api import AdminHomeApi
from .raw_seqrun_api import RawSeqrunApi
from .raw_analysis_api import RawAnalysisApi
from .project_cleanup_api import ProjectCleanupApi


"""
    Api view
"""
appbuilder.add_api(SeqrunInteropApi)
appbuilder.add_api(PreDeMultiplexingDataApi)
appbuilder.add_api(MetadataLoadApi)
appbuilder.add_api(RawMetadataDataApi)
appbuilder.add_api(AdminHomeApi)
appbuilder.add_api(RawSeqrunApi)
appbuilder.add_api(RawAnalysisApi)
appbuilder.add_api(ProjectCleanupApi)