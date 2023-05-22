#docker compose -f docker-compose-igfportal_db.yaml -p igfportal up -d
# docker exec -i portal_db mysql --host=portal_db  --user=root --password igfportaldb < backup.sql
docker compose -f docker-compose-igfportal.yaml -p igfportal up -d