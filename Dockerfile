FROM python:3.10-slim

RUN useradd user 
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt
USER user
ADD . /app
WORKDIR /app
CMD ["python", "app.py"]
