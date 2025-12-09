from app.cosmx_metadata.cosmx_metadata_utils import (
    check_user_data_validation,
    raw_user_query
)
from app.models import (
    RawIgfUser
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


def test_raw_user_query(db):
    user1 = \
        RawIgfUser(
            user_id=1,
            name="test1",
            email_id="test1")
    user2 = \
        RawIgfUser(
            user_id=2,
            name="test2",
            email_id="test2")
    user3 = \
        RawIgfUser(
            user_id=3,
            name="test3",
            email_id="test3",
            status="WITHDRAWN")
    try:
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = raw_user_query()
    assert records is not None
    assert len(records) == 2
    user_ids = [entry.user_id for entry in records]
    assert 3 not in user_ids
    assert 2 in user_ids