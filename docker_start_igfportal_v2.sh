#docker compose -f docker-compose-igfportal_db.yaml -p igfportal up -d
#UID="$(id -u)" GID="$(id -g)"  docker compose -f docker-compose-igfportal.yaml -p igfportal up -d
UID="$(id -u)" GID="$(id -g)"  docker compose -f docker-compose-igfportal.yaml -p igfportal up -d