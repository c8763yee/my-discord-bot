FROM python:3.10-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

ADD . /app
WORKDIR /app
CMD ["python", "app.py"]