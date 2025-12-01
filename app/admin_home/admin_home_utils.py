import os, json
from app import db
from app.models import AdminHomeData

def parse_and_add_new_admin_view_data(
        json_file: str,
        admin_data_tag_name: str = "admin_data_tag",
        storage_stat_plot_name: str = "storage_stat_plot",
        sequence_counts_plot_name: str = "sequence_counts_plot",
        recent_finished_runs_name: str = "recent_finished_runs",
        recent_finished_analysis_name: str = "recent_finished_analysis",
        ongoing_runs_name: str = "ongoing_runs",
        ongoing_analysis_name: str = "ongoing_analysis") -> None:
    try:
        if not os.path.exists(json_file):
            raise IOError(
                f"File {json_file} not found")
        with open(json_file, 'r') as fp:
            json_data = json.load(fp)
        if admin_data_tag_name not in json_data:
            raise KeyError("Missing admin_data_tag")
        admin_data_tag = json_data.get(admin_data_tag_name)
        storage_stat_plot = json_data.get(storage_stat_plot_name)
        if isinstance(storage_stat_plot, dict):
            storage_stat_plot = json.dumps(storage_stat_plot)
        sequence_counts_plot = json_data.get(sequence_counts_plot_name)
        if isinstance(sequence_counts_plot, dict):
            sequence_counts_plot = json.dumps(sequence_counts_plot)
        json_data.update({
            sequence_counts_plot_name: sequence_counts_plot,
            storage_stat_plot_name: storage_stat_plot})
        try:
            exists = (
                db.session
                .query(AdminHomeData)
                .filter(AdminHomeData.admin_data_tag==admin_data_tag)
                .one_or_none()
            )
            if exists is None:
                entry = AdminHomeData(
                    admin_data_tag=admin_data_tag,
                    recent_finished_runs=json_data.get(recent_finished_runs_name),
                    recent_finished_analysis=json_data.get(recent_finished_analysis_name),
                    ongoing_runs=json_data.get(ongoing_runs_name),
                    ongoing_analysis=json_data.get(ongoing_analysis_name),
                    sequence_counts_plot=sequence_counts_plot,
                    storage_stat_plot=storage_stat_plot
                )
                db.session.add(entry)
                db.session.flush()
            else:
                (db.session
                .query(AdminHomeData)
                .filter(AdminHomeData.admin_data_tag==admin_data_tag)
                .update(json_data))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(
                f"Failed to load data to db, error: {e}")
    except Exception as e:
        raise ValueError(
            f"Failed to load admin view data, error: {e}")