from app.cosmx_master_table_view import (
    user_query,
    panel_query,
    tissue_query
)
from app.models import (
    CosMxMasterTableUser,
    CosMxMasterTablePanel,
    CosMxMasterTableTissue
)

def test_user_query(db):
    user1 = CosMxMasterTableUser(
        name="AA"
    )
    user2 = CosMxMasterTableUser(
        name="BB"
    )
    try:
        db.session.add(user1)
        db.session.add(user2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    users = user_query()
    assert len(users) == 2

def test_penl_query(db):
    panel1 = CosMxMasterTablePanel(
        panel_type="AA"
    )
    panel2 = CosMxMasterTablePanel(
        panel_type="BB"
    )
    try:
        db.session.add(panel1)
        db.session.add(panel2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    panels = panel_query()
    assert len(panels) == 2

def test_tissue_query(db):
    tissue1 = CosMxMasterTableTissue(
        tissue_name="AA"
    )
    tissue2 = CosMxMasterTableTissue(
        tissue_name="BB"
    )
    try:
        db.session.add(tissue1)
        db.session.add(tissue2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    tissues = tissue_query()
    assert len(tissues) == 2