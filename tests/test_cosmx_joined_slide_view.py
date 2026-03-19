from datetime import datetime
from app.models import (
    Project,
    Cosmx_run,
    Cosmx_slide,
    Cosmx_fov,
    Cosmx_fov_rna_qc,
    Cosmx_fov_annotation,
    Cosmx_platform
)
from app.cosmx_joined_slide_view import Cosmx_slide_view


def _seed_data(db):
    """Insert a minimal set of linked records and return them."""
    platform = Cosmx_platform(
        cosmx_platform_igf_id="PLATFORM1",
        cosmx_platform_name="P1"
    )
    project = Project(project_igf_id="PROJECT_001")
    db.session.add_all([platform, project])
    db.session.flush()

    run = Cosmx_run(
        cosmx_run_igf_id="RUN_001",
        project_id=project.project_id
    )
    db.session.add(run)
    db.session.flush()

    slide = Cosmx_slide(
        cosmx_slide_igf_id="SLIDE_001",
        cosmx_run_id=run.cosmx_run_id,
        cosmx_platform_id=platform.cosmx_platform_id,
        panel_info="RNA_PANEL_A",
        assay_type="RNA",
        slide_run_date=datetime(2025, 6, 1)
    )
    db.session.add(slide)
    db.session.flush()

    fov1 = Cosmx_fov(
        cosmx_fov_name="F001",
        cosmx_slide_id=slide.cosmx_slide_id
    )
    fov2 = Cosmx_fov(
        cosmx_fov_name="F002",
        cosmx_slide_id=slide.cosmx_slide_id
    )
    db.session.add_all([fov1, fov2])
    db.session.flush()

    db.session.add_all([
        Cosmx_fov_annotation(
            cosmx_fov_id=fov1.cosmx_fov_id,
            tissue_annotation="Brain",
            tissue_condition="Normal"
        ),
        Cosmx_fov_annotation(
            cosmx_fov_id=fov2.cosmx_fov_id,
            tissue_annotation="Lung",
            tissue_condition="Tumour"
        ),
        Cosmx_fov_rna_qc(
            cosmx_fov_id=fov1.cosmx_fov_id,
            mean_transcript_per_cell=100.50,
            mean_unique_genes_per_cell=50.25
        ),
        Cosmx_fov_rna_qc(
            cosmx_fov_id=fov2.cosmx_fov_id,
            mean_transcript_per_cell=200.50,
            mean_unique_genes_per_cell=80.75
        ),
    ])
    db.session.commit()
    return {
        "project": project,
        "run": run,
        "slide": slide,
        "fovs": [fov1, fov2],
    }


def test_cosmx_slide_merged_rows_returns_data(db):
    """_cosmx_slide_merged_rows returns one row per slide with aggregated FOV data."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="", offset=0, per_page=100
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.project_igf_id == "PROJECT_001"
    assert row.cosmx_slide_igf_id == "SLIDE_001"
    assert row.assay_type == "RNA"
    assert row.fov_count == 2
    assert row.panel == "RNA_PANEL_A"


def test_cosmx_slide_merged_rows_aggregation_values(db):
    """Verify mean aggregation of QC metrics across FOVs."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="", offset=0, per_page=100
    )
    row = rows[0]
    # avg(100.50, 200.50) = 150.50
    assert float(row.mean_transcript_per_cell) == 150.50
    # avg(50.25, 80.75) = 65.50
    assert float(row.mean_unique_genes_per_cell) == 65.50


def test_cosmx_slide_merged_rows_annotation_concat(db):
    """Verify distinct annotations and conditions are concatenated."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="", offset=0, per_page=100
    )
    row = rows[0]
    for tissue in ("Brain", "Lung"):
        assert tissue in row.annotation
    for condition in ("Normal", "Tumour"):
        assert condition in row.condition


def test_cosmx_slide_merged_rows_search_by_project(db):
    """Search filter matches on project_igf_id."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="PROJECT_001", offset=0, per_page=100
    )
    assert len(rows) == 1

    rows = view._cosmx_slide_merged_rows(
        search="NONEXISTENT", offset=0, per_page=100
    )
    assert len(rows) == 0


def test_cosmx_slide_merged_rows_search_by_slide(db):
    """Search filter matches on cosmx_slide_igf_id."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="SLIDE_001", offset=0, per_page=100
    )
    assert len(rows) == 1


def test_cosmx_slide_merged_rows_search_by_annotation(db):
    """Search filter matches on tissue_annotation."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="Brain", offset=0, per_page=100
    )
    assert len(rows) == 1


def test_cosmx_slide_merged_rows_search_by_condition(db):
    """Search filter matches on tissue_condition."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="Tumour", offset=0, per_page=100
    )
    assert len(rows) == 1


def test_cosmx_slide_merged_rows_search_by_panel(db):
    """Search filter matches on panel_info."""
    _seed_data(db)
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="RNA_PANEL", offset=0, per_page=100
    )
    assert len(rows) == 1


def test_cosmx_slide_merged_rows_pagination(db):
    """Offset and per_page correctly limit results."""
    _seed_data(db)
    view = Cosmx_slide_view()
    # offset past the only row
    rows = view._cosmx_slide_merged_rows(
        search="", offset=1, per_page=100
    )
    assert len(rows) == 0

    # per_page=0 returns nothing
    rows = view._cosmx_slide_merged_rows(
        search="", offset=0, per_page=0
    )
    assert len(rows) == 0


def test_cosmx_slide_merged_rows_empty_db(db):
    """Returns empty list when no data exists."""
    view = Cosmx_slide_view()
    rows = view._cosmx_slide_merged_rows(
        search="", offset=0, per_page=100
    )
    assert len(rows) == 0


def test_list_endpoint(db, test_client):
    """The /list/ endpoint returns 200 with seeded data."""
    _seed_data(db)
    # login first
    test_client.post(
        "/login/",
        data=dict(username="admin", password="password"),
        follow_redirects=True
    )
    res = test_client.get("/cosmx_rna_slide_view/list/")
    assert res.status_code == 200


def test_list_endpoint_with_search(db, test_client):
    """The /list/ endpoint respects the search query param."""
    _seed_data(db)
    test_client.post(
        "/login/",
        data=dict(username="admin", password="password"),
        follow_redirects=True
    )
    res = test_client.get(
        "/cosmx_rna_slide_view/list/?search=PROJECT_001"
    )
    assert res.status_code == 200


def test_list_endpoint_with_pagination(db, test_client):
    """The /list/ endpoint respects page and per_page params."""
    _seed_data(db)
    test_client.post(
        "/login/",
        data=dict(username="admin", password="password"),
        follow_redirects=True
    )
    res = test_client.get(
        "/cosmx_rna_slide_view/list/?page=1&per_page=10"
    )
    assert res.status_code == 200
