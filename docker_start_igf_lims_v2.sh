#docker-compose -f docker-compose-igf-lims_v2.yaml -p igfportal_v2 up -d
UID="$(id -u)" GID="$(id -g)"  docker-compose -f docker-compose-igf-lims_v2_db.yaml -p igfportal_v2 up -d