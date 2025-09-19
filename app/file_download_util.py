import asyncio
import tempfile
from typing import Union

async def prepare_file_for_download(
    file_data: Union[str, bytes],
    file_suffix: str) -> str:
    try:
        write_mode = 'w'
        if isinstance(file_data, bytes):
            write_mode = 'wb'
        temp_file = \
            tempfile.NamedTemporaryFile(
                mode=write_mode,
                suffix=file_suffix,
                delete=False)
        temp_file.write(file_data)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise ValueError(f"Failed to dump file, error: {e}")