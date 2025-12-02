# IGFPortal

IGFPortal is a web-based data management and analysis tool created by the NIHR Imperial BRC Genomics Facility. It facilitates tracking and managing genomic sequencing projects, integrates with data pipelines, and provides tools for visualizing results.

## Key features
* Project management: track sequencing projects, runs, samplesheets, and analysis metadata.
* Pipeline integration: automates genomic data processing and integrates with bioinformatics workflows.
* Result visualization: offers an intuitive interface with graphical views for results and project status. Uses Redis caching to reduce load times.

## Requirements
* Docker (for containerized deployments)
* Optional: Docker Compose

## Installation

1. Clone the repository:

  ```bash
  git clone https://github.com/imperial-genomics-facility/IGFPortal.git
  cd IGFPortal
  ```

2. Create an environment file

  Create a new file named `env` and add:

  ```bash
  PYTHONPATH=/container_path/IGFPortal
  FLASK_APP=/container_path/IGFPortal/app/__init__.py
  SQLALCHEMY_DATABASE_URI=mysql+pymysql://DBUSER:DBPASS@DB/MYSQL_DATABASE
  MYSQL_ROOT_PASSWORD=MYSQL_ROOT_PASSWORD
  MYSQL_DATABASE=MYSQL_DATABASE
  MYSQL_USER=DBUSER
  MYSQL_PASSWORD=DBPASS
  BASIC_AUTH=FlowerUser:FlowerUserPass
  CELERY_BROKER_URL=redis://redis_db/0
  CELERY_RESULT_BACKEND=redis://redis_db/1
  CACHE_REDIS_URL=redis://redis_db/2
  CELERY_WORK_DIR=/TMP_WORK_DIR_FOR_CELERY_WORKER
  AIRFLOW_CONF_FILE=/container_path/secret/airflow_conf.json
  ```

3. Create nginx configuration

  Copy `nginx_template.conf` to `nginx.conf` and update the `server_name`:

  ```bash
  cp nginx_template.conf nginx.conf
  # Edit nginx.conf and replace SERVER_ADDRESS
  ```

  Example (for HTTP -> HTTPS redirect):

  ```nginx
  server {
      listen 80 default_server;
      server_name SERVER_ADDRESS;
      return 301 https://$server_name$request_uri;
  }
  ```

4. Build the Docker image:

  ```bash
  docker build -t imperialgenomicsfacility/igfportal:v3.0.0 .
  ```

5. Update `docker-compose.yaml`

  Update paths in `docker-compose.yaml` to match your environment:

  - Path for SSL certs (default: `../ssl_cert`)
  - Path for static directory (`../static`)
  - Path for Airflow connection conf (default: `../secret/airflow_conf.json`)

6. Start the server using Docker Compose:

  ```bash
  PORTAL_UID="$(id -u)" GID="$(id -g)" docker compose -f docker-compose-prod.yaml -p igfportal up -d
  ```

7. Access the portal

  Open your browser at `https://SERVER_ADDRESS`.

## License

  This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.