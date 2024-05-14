FROM python:3.10-slim
COPY requirements.txt /tmp
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y -q \
    git libpq-dev python3-dev build-essential libsnappy-dev sudo && \
    apt-get clean && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    useradd -mG sudo user && \
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers


USER user
COPY --chown=user . /app
WORKDIR /app
CMD ["python", "app.py"]
