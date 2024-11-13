# IGFPortal

IGFPortal is a web-based data management and analysis tool created by the NIHR Imperial BRC  Genomics Facility. It facilitates tracking and managing genomic sequencing projects, integrating data pipelines, and visualizing results, particularly in genomics research.

## Key Features
- **Project Management**: Track sequencing projects, sequencing runs, samplesheets and analysis metadata, improving organization and facilitate validation.
- **Pipeline Integration**: Automates genomic data processing, enabling seamless integration with bioinformatics workflows. Provides easy to use interface for triggering data pipelines.
- **Result Visualization**: Offers an intuitive interface with graphical views for data analysis results and project status. Utilises Redis caching to minimise loading analysis reports.

## Requirements
- **Python**: Version 3.8 or higher
- **Docker**: For containerized deployments

## Installation

**1. Clone the Repository**

```bash
git clone https://github.com/imperial-genomics-facility/IGFPortal.git
```

**2. Create an environment file**

```
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

**3. Create Nginx cconfig file**

Copy the `nginx_template.conf` to `nginx.conf` and replace `server_name` value.

```json
server {
    # Redirect http to https
    listen 80 default_server;
    server_name YOUR_SERVER_NAME;
    return 301 https://$server_name$request_uri;
}
```

**4. Build docker image**

```bash
docker build -t imperialgenomicsfacility/igfportal:v0.0.2.1 .
```

**5. Update docker compose file**

Update `docker-compose.yaml` file and add correct path for following:

  * Path of the local copy of IGFPortal repo (default is /home/vmuser/github/IGFPortal)
  * Path for SSL certs (default is /home/vmuser/github/ssl)
  * Path for static directory (default is ./static)
  * Path for Airflow connection conf (default /home/vmuser/secrets/airflow_conf.json)

**6. Start the server using docker compose**

```bash
  PORTAL_UID="$(id -u)" GID="$(id -g)"  docker compose -f docker-compose.yaml -p igfportal up -d
```

**7. Access the Portal**

Open your browser at `https://SERVER_ADDRESS` to access the IGFPortal dashboard.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.