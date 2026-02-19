FROM python:3.13.7-slim AS builder
LABEL version="v3.2.8"
LABEL description="Docker image for running IGFPortal server"
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends --fix-missing -y git tzdata curl && \
    apt-get purge -y --auto-remove && \
    apt-get clean && \
    rm -f /tmp/* && \
    rm -rf /var/lib/apt/lists/*
ENV USERNAME=portal
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -f requirements.txt
FROM python:3.13.7-slim AS runner
ENV PATH=/venv/bin:$PATH
ENV TZ=Europe/London
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY --from=builder /venv /venv
COPY --from=builder /usr/bin /usr/bin
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
WORKDIR /app
COPY . .
USER nobody
ENV PYTHONPATH=/app
EXPOSE 8080
EXPOSE 5555
