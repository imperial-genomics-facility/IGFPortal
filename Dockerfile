FROM python:3.8.16-slim
LABEL version="v0.02"
LABEL description="Docker image for running IGFPortal server"
COPY requirements.txt /tmp/requirements.txt
RUN apt-get -y update && \
    apt-get install --no-install-recommends --fix-missing -y git  && \
    python -m pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    apt-get purge -y --auto-remove && \
    apt-get clean && \
    rm -f /tmp/* && \
    rm -rf /var/lib/apt/lists/*
USER nobody
WORKDIR /tmp
ENTRYPOINT ["bash","-c"]
CMD ["flask", "run"]
