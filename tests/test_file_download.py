import os
import pytest
from app.file_download_util import prepare_file_for_download

@pytest.mark.asyncio
async def test_prepare_file_for_download():
    """Test successful file preparation"""

    # Call the async function
    file_path = await prepare_file_for_download(file_data="AAA", file_suffix=".txt")
    assert os.path.exists(file_path)
    with open(file_path, 'r') as fp:
        data = fp.read()
    assert data.strip() == "AAA"
    file_path = await prepare_file_for_download(file_data=b"AAA", file_suffix=".t")
    assert os.path.exists(file_path)
    with open(file_path, 'rb') as fp:
        data = fp.read()
    assert data.decode() == "AAA"
