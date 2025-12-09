from app.cosmx_metadata.cosmx_metadata_utils import (
    check_user_data_validation
)

def test_check_user_data_validation():
    user_data1 = {
        "name": "Bob Jones",
        "email": "bob@example.com",
        "username": "bob123"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data1
    )
    assert len(err_list) == 0
    user_data2 = {
        "name": "Bob",
        "email": "bob@example.com",
        "username": "bob123"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data2
    )
    assert len(err_list) == 1
    user_data3 = {
        "name": "Bob Jones",
        "email": "bob@example.com",
        "username": "bob"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data3
    )
    assert len(err_list) == 1
    user_data4 = {
        "name": "Bob Jones",
        "email": "bob@example.com"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data4
    )
    assert len(err_list) == 0