import csv
import tempfile
import logging
from app import db
from flask import request, send_file
from sqlalchemy import select, func, or_
from app.models import (
    CosMxMasterTableUser,
    CosMxMasterTablePanel,
    CosMxMasterTableTissue,
    CosMxMasterTableSlide,
    Cosmx_platform,
    Cosmx_slide,
    Cosmx_fov_rna_qc,
    Cosmx_fov_protein_qc
)
from flask_appbuilder import BaseView, expose, has_access

log = logging.getLogger(__name__)

PAGE_SIZE = 100

class Cosmx_rna_merged_view(BaseView):
    default_view = "list"
    route_base = "/cosmx_rnaseq_merged"

    def _cosmx_rna_merged_rows(self, search: str, offset: int, per_page: int):
        stmt = (
            select(
                Cosmx_slide.cosmx_slide_igf_id.label("atomx_slide_id"),
                CosMxMasterTableSlide.slide_id.label("original_slide_id"),
            )
            .outerjoin(
                CosMxMasterTableSlide,
                CosMxMasterTableSlide.slide_id == Cosmx_slide.cosmx_slide_igf_id
            )
        )
        if search and search != "":
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Cosmx_slide.cosmx_slide_igf_id.ilike(like),
                    CosMxMasterTableSlide.slide_id.ilike(like)
                )
            )
        rows = (
            db.session.execute(
                stmt
                .order_by(CosMxMasterTableSlide.scan_date)
                .offset(offset)
                .limit(per_page))
            .all()
        )
        return rows

    @expose("/list/")
    @has_access
    def list(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", PAGE_SIZE, type=int)
        search = request.args.get("search", "").strip()
        offset = (page - 1) * per_page
        rows = self._cosmx_rna_merged_rows(search, offset, per_page)
        count_stmt = select(func.count()).select_from(
            select(Cosmx_slide.cosmx_slide_id)
            .outerjoin(
                CosMxMasterTableSlide,
                CosMxMasterTableSlide.slide_id == Cosmx_slide.cosmx_slide_igf_id
            )
            .subquery()
        )
        total = db.session.execute(count_stmt).scalar()
        total_pages = max(1, (total + per_page - 1) // per_page)
        return self.render_template(
            "cosmx_rnaseq_merged.html",
            rows=rows,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            search=search,
        )

    @expose("/export/")
    @has_access
    def export(self):
        search = request.args.get("search", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", PAGE_SIZE, type=int)
        offset = (page - 1) * per_page
        rows = self._build_query(search, offset, per_page)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            delete=False,
            delete_on_close=False,
            newline='') as tmp:
            writer = csv.writer(tmp)
            writer.writerow([
                "atomx_slide_id",
                "original_slide_id"
            ])
            for row in rows:
                writer.writerow([
                    row.atomx_slide_id,
                    row.original_slide_id
                ])
            tmp_path = tmp.name
        return send_file(
            tmp_path,
            download_name="cosmx_slides.csv",
            as_attachment=True)