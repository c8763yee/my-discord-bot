FROM python:3.10-slim
COPY requirements.txt /tmp
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y -q \
    git libpq-dev python3-dev build-essential libsnappy-dev && \
    apt-get clean && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    useradd -m user

USER user
COPY --chown=user . /app
WORKDIR /app
CMD ["python", "app.py"]
