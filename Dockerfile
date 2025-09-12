FROM python:3.13.7-slim
LABEL version="v1.0"
LABEL description="Docker image for running IGFPortal server"
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends --fix-missing -y git tzdata curl && \
    apt-get purge -y --auto-remove && \
    apt-get clean && \
    rm -f /tmp/* && \
    rm -rf /var/lib/apt/lists/*
ENV TZ=Europe/London
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV USERNAME=portal
RUN adduser --disabled-password --gecos "" ${USERNAME}
USER portal
WORKDIR /home/${USERNAME}/
ENV VENV_PATH=/home/${USERNAME}/.venv
ENV PATH=${VENV_PATH}/bin:${PATH}
RUN python -m venv ${VENV_PATH}
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt
ENTRYPOINT ["bash","-c"]
CMD ["flask", "run"]
